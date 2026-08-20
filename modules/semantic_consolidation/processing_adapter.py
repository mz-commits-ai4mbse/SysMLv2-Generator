"""Project-Processing adapter for element semantic consolidation.

The adapter consumes exact derivation Agent outputs from one Phase-F execution,
uses the existing LLM provider boundary for one compact semantic partition call,
and persists both raw comparator trace and the validated immutable C2 artifact
inside the Phase-F work tree before publication / ``awaiting_review``.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from modules.llm.factory import create_llm_client
from modules.llm.types import LLMRequest
from modules.source_analysis_units.identifiers import (
    validate_source_analysis_unit_id,
)

from .artifact import (
    semantic_consolidation_artifact_from_dict,
    semantic_consolidation_artifact_to_dict,
)
from .cross_unit_synthesis import (
    LocalElementSubject,
    LocalRelationshipSubject,
    CrossUnitSemanticSynthesisArtifact,
    cross_unit_semantic_synthesis_artifact_to_dict,
    synthesize_cross_unit_semantics,
)
from .element_clustering import (
    ElementSemanticProposal,
    SemanticEvidenceStatement,
    consolidate_element_proposals,
)
from .relationship_clustering import (
    RelationshipSemanticProposal,
    consolidate_relationship_proposals,
)
from .errors import (
    SemanticConsolidationIntegrityError,
    SemanticConsolidationValidationError,
)
from .types import SemanticUpstreamArtifactBinding


DERIVATION_STAGE_DIRECTORY = "03_derivation_assessment"
SEMANTIC_CONSOLIDATION_STAGE_DIRECTORY = "05_semantic_consolidation"
SEMANTIC_CONSOLIDATION_ARTIFACT_FILENAME = (
    "semantic_element_consolidation.json"
)
SEMANTIC_COMPARATOR_TRACE_FILENAME = "semantic_element_comparator_run_01.json"

RELATIONSHIP_SEMANTIC_CONSOLIDATION_ARTIFACT_FILENAME = (
    "semantic_relationship_consolidation.json"
)
RELATIONSHIP_SEMANTIC_COMPARATOR_TRACE_FILENAME = (
    "semantic_relationship_comparator_run_01.json"
)


CROSS_UNIT_SYNTHESIS_STAGE_DIRECTORY = "06_cross_unit_synthesis"
CROSS_UNIT_SYNTHESIS_ARTIFACT_FILENAME = "cross_unit_semantic_synthesis.json"
CROSS_UNIT_ELEMENT_COMPARATOR_TRACE_FILENAME = (
    "cross_unit_element_comparator_run_01.json"
)
CROSS_UNIT_RELATIONSHIP_COMPARATOR_TRACE_FILENAME = (
    "cross_unit_relationship_comparator_run_01.json"
)


_RELATIONSHIP_ENDPOINT_UNRESOLVED_WARNING = (
    "relationship_endpoint_unresolved_human_review_required"
)
_RELATIONSHIP_ENDPOINT_AMBIGUOUS_WARNING = (
    "relationship_endpoint_ambiguous_human_review_required"
)


@dataclass(frozen=True, slots=True)
class PhaseFElementSemanticInput:
    """Exact C2 input reconstructed from one completed Phase-F execution."""

    proposals: tuple[ElementSemanticProposal, ...]
    evidence: tuple[SemanticEvidenceStatement, ...]
    upstream_artifacts: tuple[SemanticUpstreamArtifactBinding, ...]
    expected_persona_ids: tuple[str, ...]
    source_analysis_unit_id: str | None = None


@dataclass(frozen=True, slots=True)
class PhaseFElementSemanticResult:
    """Persisted semantic-consolidation execution summary."""

    artifact_path: Path
    comparator_trace_path: Path | None
    degraded_to_singletons: bool
    warning_codes: tuple[str, ...]
    proposal_count: int
    semantic_subject_count: int
    source_analysis_unit_id: str | None = None

    relationship_artifact_path: Path | None = None
    relationship_comparator_trace_path: Path | None = None
    relationship_degraded_to_singletons: bool = False
    relationship_warning_codes: tuple[str, ...] = ()
    relationship_proposal_count: int = 0
    relationship_semantic_subject_count: int = 0


@dataclass(frozen=True, slots=True)
class RelationshipEndpointResolutionFinding:
    """Recoverable endpoint-resolution issue requiring Human Review."""

    relationship_proposal_ref: str
    endpoint_role: str
    endpoint_token: str
    resolution_status: str
    candidate_proposal_refs: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RelationshipEndpointResolution:
    """Authority-safe endpoint binding used by C3."""

    proposal_ref: str
    semantic_subject_id: str
    warning_code: str | None = None
    finding: RelationshipEndpointResolutionFinding | None = None


@dataclass(frozen=True, slots=True)
class PhaseFRelationshipSemanticInput:
    """Exact C3 relationship input bound to semantic element endpoints."""

    proposals: tuple[RelationshipSemanticProposal, ...]
    evidence: tuple[SemanticEvidenceStatement, ...]
    upstream_artifacts: tuple[SemanticUpstreamArtifactBinding, ...]
    expected_persona_ids: tuple[str, ...]
    warning_codes: tuple[str, ...] = ()
    endpoint_resolution_findings: tuple[
        RelationshipEndpointResolutionFinding, ...
    ] = ()
    source_analysis_unit_id: str | None = None


@dataclass(frozen=True, slots=True)
class PhaseFSourceAnchoredSemanticResult:
    """Local C2/C3 results for every canonical Source Analysis Unit."""

    unit_results: tuple[PhaseFElementSemanticResult, ...]
    source_analysis_unit_ids: tuple[str, ...]
    element_proposal_count: int
    element_semantic_subject_count: int
    relationship_proposal_count: int
    relationship_semantic_subject_count: int


@dataclass(frozen=True, slots=True)
class PhaseFCrossUnitSemanticInput:
    """Exact D4 input reconstructed from persisted D3 local artifacts."""

    source_analysis_unit_ids: tuple[str, ...]
    local_element_subjects: tuple[LocalElementSubject, ...]
    local_relationship_subjects: tuple[LocalRelationshipSubject, ...]


@dataclass(frozen=True, slots=True)
class PhaseFCrossUnitSemanticResult:
    """Persisted D4 cross-unit synthesis execution summary."""

    artifact_path: Path
    element_comparator_trace_path: Path | None
    relationship_comparator_trace_path: Path | None
    element_degraded_to_singletons: bool
    element_warning_codes: tuple[str, ...]
    relationship_degraded_to_singletons: bool
    relationship_warning_codes: tuple[str, ...]
    local_element_subject_count: int
    synthesized_element_subject_count: int
    local_relationship_subject_count: int
    synthesized_relationship_subject_count: int
    relationship_rebinding_finding_count: int


@dataclass(frozen=True, slots=True)
class PhaseFSourceAnchoredSemanticPipelineResult:
    """Compiled D3+D4 result used by the project-bound Processing bridge."""

    source_anchored_result: PhaseFSourceAnchoredSemanticResult
    cross_unit_result: PhaseFCrossUnitSemanticResult


def _strict_json_loads(text: str, *, label: str) -> object:
    if not isinstance(text, str):
        raise SemanticConsolidationValidationError(
            f"{label} must be JSON text."
        )

    def no_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise SemanticConsolidationIntegrityError(
                    f"{label} contains duplicate JSON key {key!r}."
                )
            result[key] = value
        return result

    try:
        return json.loads(text, object_pairs_hook=no_duplicates)
    except SemanticConsolidationIntegrityError:
        raise
    except json.JSONDecodeError as exc:
        raise SemanticConsolidationValidationError(
            f"{label} is not valid JSON."
        ) from exc


def _exact_text(value: object, *, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SemanticConsolidationValidationError(
            f"{label} must be a non-empty string."
        )
    return value.strip()


def _repository_relative(path: Path, *, repository_root: Path) -> str:
    resolved_root = repository_root.resolve()
    resolved_path = path.resolve()
    try:
        relative = resolved_path.relative_to(resolved_root)
    except ValueError as exc:
        raise SemanticConsolidationIntegrityError(
            "Semantic consolidation input escaped repository_root."
        ) from exc
    return relative.as_posix()


def _semantic_source_evidence_ref(
    *,
    artifact_ref: str,
    source_info_id: str,
    statement: str,
) -> str:
    """Build deterministic identity for one exact source-evidence statement."""

    statement_fingerprint = hashlib.sha256(
        statement.encode("utf-8")
    ).hexdigest()
    return (
        f"{artifact_ref}#source-info:{source_info_id}"
        f":statement-sha256:{statement_fingerprint}"
    )


def _validated_optional_source_analysis_unit_id(
    value: object,
) -> str | None:
    if value is None:
        return None
    try:
        return validate_source_analysis_unit_id(value)
    except Exception as exc:
        raise SemanticConsolidationValidationError(
            "source_analysis_unit_id is invalid."
        ) from exc


def _derivation_source_analysis_unit_id(
    *,
    result: object,
    wrapper: dict[str, object],
) -> str | None:
    """Validate the D2 binding duplicated in result and persisted wrapper."""

    result_value = _validated_optional_source_analysis_unit_id(
        getattr(result, "source_analysis_unit_id", None)
    )
    wrapper_value = _validated_optional_source_analysis_unit_id(
        wrapper.get("source_analysis_unit_id")
    )

    if result_value is None and wrapper_value is None:
        return None
    if result_value is None or wrapper_value is None:
        raise SemanticConsolidationIntegrityError(
            "Derivation Agent Source Analysis Unit binding is incomplete."
        )
    if result_value != wrapper_value:
        raise SemanticConsolidationIntegrityError(
            "Derivation Agent Source Analysis Unit binding conflicts "
            "between execution result and persisted wrapper."
        )
    return result_value


def _source_anchored_semantic_paths(
    *,
    phase_root: Path,
    source_analysis_unit_id: str | None,
    artifact_filename: str,
    trace_filename: str,
) -> tuple[Path, Path]:
    if source_analysis_unit_id is None:
        return (
            phase_root / "consensus_reports" / artifact_filename,
            phase_root
            / "agent_outputs"
            / SEMANTIC_CONSOLIDATION_STAGE_DIRECTORY
            / trace_filename,
        )

    validated_id = _validated_optional_source_analysis_unit_id(
        source_analysis_unit_id
    )
    assert validated_id is not None
    return (
        phase_root
        / "consensus_reports"
        / SEMANTIC_CONSOLIDATION_STAGE_DIRECTORY
        / validated_id
        / artifact_filename,
        phase_root
        / "agent_outputs"
        / SEMANTIC_CONSOLIDATION_STAGE_DIRECTORY
        / validated_id
        / trace_filename,
    )


def build_phase_f_element_semantic_input(
    *,
    phase_f_result: object,
    repository_root: Path | str,
    source_analysis_unit_id: str | None = None,
    allow_empty_proposals: bool = False,
) -> PhaseFElementSemanticInput:
    """Reconstruct exact semantic element inputs from derivation Agent outputs."""

    root = Path(repository_root)
    requested_source_analysis_unit_id = (
        _validated_optional_source_analysis_unit_id(
            source_analysis_unit_id
        )
    )
    results = getattr(phase_f_result, "agent_results", None)
    if not isinstance(results, list):
        raise SemanticConsolidationIntegrityError(
            "Phase-F result does not expose agent_results."
        )

    proposals: list[ElementSemanticProposal] = []
    evidence_by_ref: dict[str, str] = {}
    upstream: dict[str, SemanticUpstreamArtifactBinding] = {}
    expected_personas: set[str] = set()
    derivation_count = 0

    for result in results:
        output_path = getattr(result, "output_path", None)
        if not isinstance(output_path, Path):
            output_path = Path(output_path) if output_path is not None else None
        if output_path is None or DERIVATION_STAGE_DIRECTORY not in output_path.parts:
            continue

        if not output_path.exists() or not output_path.is_file():
            raise SemanticConsolidationIntegrityError(
                "Derivation Agent output artifact is unavailable."
            )

        wrapper_bytes = output_path.read_bytes()
        wrapper = _strict_json_loads(
            wrapper_bytes.decode("utf-8"),
            label="derivation Agent wrapper",
        )
        if not isinstance(wrapper, dict):
            raise SemanticConsolidationValidationError(
                "Derivation Agent wrapper must be a JSON object."
            )

        bound_source_analysis_unit_id = (
            _derivation_source_analysis_unit_id(
                result=result,
                wrapper=wrapper,
            )
        )
        if requested_source_analysis_unit_id is not None:
            if bound_source_analysis_unit_id is None:
                raise SemanticConsolidationIntegrityError(
                    "Source-anchored semantic consolidation received an "
                    "unbound derivation Agent result."
                )
            if (
                bound_source_analysis_unit_id
                != requested_source_analysis_unit_id
            ):
                continue

        derivation_count += 1
        agent_id = _exact_text(wrapper.get("agent_id"), label="agent_id")
        persona_id = _exact_text(
            wrapper.get("persona_id"),
            label="persona_id",
        )
        run_index = wrapper.get("run_index")
        if isinstance(run_index, bool) or not isinstance(run_index, int) or run_index < 1:
            raise SemanticConsolidationValidationError(
                "run_index must be an integer >= 1."
            )
        expected_personas.add(persona_id)

        output_text = _exact_text(
            wrapper.get("output_text"),
            label="output_text",
        )
        output = _strict_json_loads(
            output_text,
            label="derivation output",
        )
        if not isinstance(output, dict):
            raise SemanticConsolidationValidationError(
                "Derivation output must be a JSON object."
            )
        raw_elements = output.get("candidate_model_elements")
        if not isinstance(raw_elements, list):
            raise SemanticConsolidationValidationError(
                "candidate_model_elements must be a JSON array."
            )

        artifact_ref = _repository_relative(output_path, repository_root=root)
        fingerprint = hashlib.sha256(wrapper_bytes).hexdigest()
        previous = upstream.get(artifact_ref)
        binding = SemanticUpstreamArtifactBinding(
            artifact_ref=artifact_ref,
            artifact_fingerprint=fingerprint,
        )
        if previous is not None and previous != binding:
            raise SemanticConsolidationIntegrityError(
                "One upstream artifact reference has conflicting content."
            )
        upstream[artifact_ref] = binding

        seen_candidate_ids: set[str] = set()
        for raw in raw_elements:
            if not isinstance(raw, dict):
                raise SemanticConsolidationValidationError(
                    "candidate_model_elements contains a non-object entry."
                )
            candidate_id = _exact_text(
                raw.get("candidate_id"),
                label="candidate_id",
            )
            if candidate_id in seen_candidate_ids:
                raise SemanticConsolidationIntegrityError(
                    "Candidate IDs repeat within one derivation Agent output."
                )
            seen_candidate_ids.add(candidate_id)

            candidate_name = _exact_text(
                raw.get("candidate_name"),
                label="candidate_name",
            )
            element_type = _exact_text(
                raw.get("element_type"),
                label="element_type",
            )
            description = _exact_text(
                raw.get("description"),
                label="description",
            )
            assignments = raw.get("assigned_source_information")
            if not isinstance(assignments, list) or not assignments:
                raise SemanticConsolidationIntegrityError(
                    "Element proposal requires exact source assignments."
                )

            evidence_refs: list[str] = []
            for assignment in assignments:
                if not isinstance(assignment, dict):
                    raise SemanticConsolidationValidationError(
                        "assigned_source_information contains a non-object entry."
                    )
                source_info_id = _exact_text(
                    assignment.get("source_info_id"),
                    label="source_info_id",
                )
                statement = _exact_text(
                    assignment.get("source_statement"),
                    label="source_statement",
                )
                evidence_ref = _semantic_source_evidence_ref(
                    artifact_ref=artifact_ref,
                    source_info_id=source_info_id,
                    statement=statement,
                )
                previous_statement = evidence_by_ref.get(evidence_ref)
                if previous_statement is not None and previous_statement != statement:
                    raise SemanticConsolidationIntegrityError(
                        "One exact evidence reference has conflicting statements."
                    )
                evidence_by_ref[evidence_ref] = statement
                evidence_refs.append(evidence_ref)

            proposal_ref = (
                f"{artifact_ref}#element:{candidate_id}"
            )
            proposals.append(
                ElementSemanticProposal(
                    proposal_ref=proposal_ref,
                    candidate_name=candidate_name,
                    proposed_element_type=element_type,
                    concise_description=description,
                    agent_id=agent_id,
                    persona_id=persona_id,
                    run_index=run_index,
                    upstream_artifact_ref=artifact_ref,
                    evidence_refs=tuple(sorted(set(evidence_refs))),
                )
            )

    if derivation_count == 0:
        suffix = (
            f" for {requested_source_analysis_unit_id}"
            if requested_source_analysis_unit_id is not None
            else ""
        )
        raise SemanticConsolidationIntegrityError(
            "Phase-F result contains no derivation Agent outputs"
            f"{suffix}."
        )
    if not proposals and not allow_empty_proposals:
        raise SemanticConsolidationIntegrityError(
            "Derivation Agent outputs contain no element proposals."
        )

    proposal_refs = tuple(item.proposal_ref for item in proposals)
    if len(proposal_refs) != len(set(proposal_refs)):
        raise SemanticConsolidationIntegrityError(
            "Exact semantic proposal references are not unique."
        )

    return PhaseFElementSemanticInput(
        proposals=tuple(sorted(proposals, key=lambda item: item.proposal_ref)),
        evidence=tuple(
            SemanticEvidenceStatement(evidence_ref=ref, statement=statement)
            for ref, statement in sorted(evidence_by_ref.items())
        ),
        upstream_artifacts=tuple(
            upstream[key] for key in sorted(upstream)
        ),
        expected_persona_ids=tuple(sorted(expected_personas)),
        source_analysis_unit_id=(
            requested_source_analysis_unit_id
        ),
    )



def _normalize_endpoint_token(value: str) -> str:
    return " ".join(value.casefold().split())


def _element_subject_by_proposal_ref(
    artifact: object,
) -> dict[str, str]:
    subjects = getattr(artifact, "subjects", None)
    if not isinstance(subjects, tuple):
        raise SemanticConsolidationIntegrityError(
            "Element semantic artifact does not expose immutable subjects."
        )

    result: dict[str, str] = {}
    for subject in subjects:
        if getattr(subject, "proposal_kind", None) != "element":
            continue
        subject_id = _exact_text(
            getattr(subject, "semantic_subject_id", None),
            label="semantic_subject_id",
        )
        member_refs = getattr(subject, "member_proposal_refs", None)
        if not isinstance(member_refs, tuple) or not member_refs:
            raise SemanticConsolidationIntegrityError(
                "Element semantic subject has invalid member proposal refs."
            )
        for proposal_ref in member_refs:
            checked = _exact_text(
                proposal_ref,
                label="element member proposal_ref",
            )
            if checked in result:
                raise SemanticConsolidationIntegrityError(
                    "One element proposal belongs to multiple semantic subjects."
                )
            result[checked] = subject_id
    return result


def _unresolved_endpoint_binding(
    *,
    artifact_ref: str,
    relationship_proposal_ref: str,
    link_id: str,
    endpoint_role: str,
    endpoint_token: str,
    resolution_status: str,
    candidate_proposal_refs: tuple[str, ...],
) -> RelationshipEndpointResolution:
    if endpoint_role not in {"source", "target"}:
        raise SemanticConsolidationIntegrityError(
            "Relationship endpoint role must be source or target."
        )
    if resolution_status not in {"unresolved", "ambiguous"}:
        raise SemanticConsolidationIntegrityError(
            "Recoverable relationship endpoint status is invalid."
        )

    identity_payload = {
        "artifact_ref": artifact_ref,
        "relationship_proposal_ref": relationship_proposal_ref,
        "link_id": link_id,
        "endpoint_role": endpoint_role,
        "endpoint_token": endpoint_token,
        "resolution_status": resolution_status,
        "candidate_proposal_refs": list(candidate_proposal_refs),
    }
    fingerprint = hashlib.sha256(
        json.dumps(
            identity_payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()

    warning_code = (
        _RELATIONSHIP_ENDPOINT_AMBIGUOUS_WARNING
        if resolution_status == "ambiguous"
        else _RELATIONSHIP_ENDPOINT_UNRESOLVED_WARNING
    )

    return RelationshipEndpointResolution(
        proposal_ref=(
            f"{artifact_ref}#relationship-endpoint:{link_id}:"
            f"{endpoint_role}:{resolution_status}:{fingerprint}"
        ),
        semantic_subject_id=(
            f"semantic:unresolved-element-endpoint:{fingerprint}"
        ),
        warning_code=warning_code,
        finding=RelationshipEndpointResolutionFinding(
            relationship_proposal_ref=relationship_proposal_ref,
            endpoint_role=endpoint_role,
            endpoint_token=endpoint_token,
            resolution_status=resolution_status,
            candidate_proposal_refs=candidate_proposal_refs,
        ),
    )


def _resolve_element_endpoint(
    value: object,
    *,
    artifact_ref: str,
    relationship_proposal_ref: str,
    link_id: str,
    endpoint_role: str,
    candidate_ids: dict[str, str],
    candidate_names: dict[str, list[str]],
    element_subject_by_ref: dict[str, str],
) -> RelationshipEndpointResolution:
    token = _exact_text(value, label="relationship element endpoint")

    if token in candidate_ids:
        proposal_ref = candidate_ids[token]
        try:
            semantic_subject_id = element_subject_by_ref[proposal_ref]
        except KeyError as exc:
            raise SemanticConsolidationIntegrityError(
                "Resolved relationship endpoint proposal is unavailable "
                "from the exact C2 semantic element artifact."
            ) from exc
        return RelationshipEndpointResolution(
            proposal_ref=proposal_ref,
            semantic_subject_id=semantic_subject_id,
        )

    matches = tuple(
        sorted(
            candidate_names.get(
                _normalize_endpoint_token(token),
                [],
            )
        )
    )
    if len(matches) == 1:
        proposal_ref = matches[0]
        try:
            semantic_subject_id = element_subject_by_ref[proposal_ref]
        except KeyError as exc:
            raise SemanticConsolidationIntegrityError(
                "Resolved relationship endpoint proposal is unavailable "
                "from the exact C2 semantic element artifact."
            ) from exc
        return RelationshipEndpointResolution(
            proposal_ref=proposal_ref,
            semantic_subject_id=semantic_subject_id,
        )

    return _unresolved_endpoint_binding(
        artifact_ref=artifact_ref,
        relationship_proposal_ref=relationship_proposal_ref,
        link_id=link_id,
        endpoint_role=endpoint_role,
        endpoint_token=token,
        resolution_status=(
            "unresolved"
            if not matches
            else "ambiguous"
        ),
        candidate_proposal_refs=matches,
    )


def build_phase_f_relationship_semantic_input(
    *,
    phase_f_result: object,
    repository_root: Path | str,
    element_artifact: object,
    source_analysis_unit_id: str | None = None,
) -> PhaseFRelationshipSemanticInput:
    """Reconstruct exact relationships and bind them to C2 element subjects."""

    root = Path(repository_root)
    requested_source_analysis_unit_id = (
        _validated_optional_source_analysis_unit_id(
            source_analysis_unit_id
        )
    )
    results = getattr(phase_f_result, "agent_results", None)
    if not isinstance(results, list):
        raise SemanticConsolidationIntegrityError(
            "Phase-F result does not expose agent_results."
        )

    element_subject_by_ref = _element_subject_by_proposal_ref(
        element_artifact
    )
    proposals: list[RelationshipSemanticProposal] = []
    evidence_by_ref: dict[str, str] = {}
    upstream: dict[str, SemanticUpstreamArtifactBinding] = {}
    expected_personas: set[str] = set()
    warning_codes: set[str] = set()
    endpoint_findings: list[RelationshipEndpointResolutionFinding] = []

    for result in results:
        output_path = getattr(result, "output_path", None)
        if not isinstance(output_path, Path):
            output_path = (
                Path(output_path)
                if output_path is not None
                else None
            )
        if (
            output_path is None
            or DERIVATION_STAGE_DIRECTORY not in output_path.parts
        ):
            continue

        wrapper_bytes = output_path.read_bytes()
        wrapper = _strict_json_loads(
            wrapper_bytes.decode("utf-8"),
            label="derivation Agent wrapper",
        )
        if not isinstance(wrapper, dict):
            raise SemanticConsolidationValidationError(
                "Derivation Agent wrapper must be a JSON object."
            )

        bound_source_analysis_unit_id = (
            _derivation_source_analysis_unit_id(
                result=result,
                wrapper=wrapper,
            )
        )
        if requested_source_analysis_unit_id is not None:
            if bound_source_analysis_unit_id is None:
                raise SemanticConsolidationIntegrityError(
                    "Source-anchored relationship consolidation received "
                    "an unbound derivation Agent result."
                )
            if (
                bound_source_analysis_unit_id
                != requested_source_analysis_unit_id
            ):
                continue

        agent_id = _exact_text(
            wrapper.get("agent_id"),
            label="agent_id",
        )
        persona_id = _exact_text(
            wrapper.get("persona_id"),
            label="persona_id",
        )
        run_index = wrapper.get("run_index")
        if (
            isinstance(run_index, bool)
            or not isinstance(run_index, int)
            or run_index < 1
        ):
            raise SemanticConsolidationValidationError(
                "run_index must be an integer >= 1."
            )
        expected_personas.add(persona_id)

        output_text = _exact_text(
            wrapper.get("output_text"),
            label="output_text",
        )
        output = _strict_json_loads(
            output_text,
            label="derivation output",
        )
        if not isinstance(output, dict):
            raise SemanticConsolidationValidationError(
                "Derivation output must be a JSON object."
            )

        raw_elements = output.get("candidate_model_elements")
        if not isinstance(raw_elements, list):
            raise SemanticConsolidationValidationError(
                "candidate_model_elements must be a JSON array."
            )
        raw_links = output.get("explicit_source_links", [])
        if not isinstance(raw_links, list):
            raise SemanticConsolidationValidationError(
                "explicit_source_links must be a JSON array."
            )

        artifact_ref = _repository_relative(
            output_path,
            repository_root=root,
        )
        fingerprint = hashlib.sha256(wrapper_bytes).hexdigest()
        binding = SemanticUpstreamArtifactBinding(
            artifact_ref=artifact_ref,
            artifact_fingerprint=fingerprint,
        )
        previous = upstream.get(artifact_ref)
        if previous is not None and previous != binding:
            raise SemanticConsolidationIntegrityError(
                "One upstream artifact reference has conflicting content."
            )
        upstream[artifact_ref] = binding

        candidate_ids: dict[str, str] = {}
        candidate_names: dict[str, list[str]] = {}
        for raw_element in raw_elements:
            if not isinstance(raw_element, dict):
                raise SemanticConsolidationValidationError(
                    "candidate_model_elements contains a non-object entry."
                )
            candidate_id = _exact_text(
                raw_element.get("candidate_id"),
                label="candidate_id",
            )
            candidate_name = _exact_text(
                raw_element.get("candidate_name"),
                label="candidate_name",
            )
            proposal_ref = (
                f"{artifact_ref}#element:{candidate_id}"
            )
            if proposal_ref not in element_subject_by_ref:
                raise SemanticConsolidationIntegrityError(
                    "Relationship endpoint element proposal is unavailable "
                    "from the C2 semantic element artifact."
                )
            if candidate_id in candidate_ids:
                raise SemanticConsolidationIntegrityError(
                    "Candidate IDs repeat within one derivation Agent output."
                )
            candidate_ids[candidate_id] = proposal_ref
            candidate_names.setdefault(
                _normalize_endpoint_token(candidate_name),
                [],
            ).append(proposal_ref)

        seen_link_ids: set[str] = set()
        for raw_link in raw_links:
            if not isinstance(raw_link, dict):
                raise SemanticConsolidationValidationError(
                    "explicit_source_links contains a non-object entry."
                )
            link_id = _exact_text(
                raw_link.get("link_id"),
                label="link_id",
            )
            if link_id in seen_link_ids:
                raise SemanticConsolidationIntegrityError(
                    "Link IDs repeat within one derivation Agent output."
                )
            seen_link_ids.add(link_id)

            relationship_proposal_ref = (
                f"{artifact_ref}#relationship:{link_id}"
            )

            source_resolution = _resolve_element_endpoint(
                raw_link.get("source_element_candidate"),
                artifact_ref=artifact_ref,
                relationship_proposal_ref=relationship_proposal_ref,
                link_id=link_id,
                endpoint_role="source",
                candidate_ids=candidate_ids,
                candidate_names=candidate_names,
                element_subject_by_ref=element_subject_by_ref,
            )
            target_resolution = _resolve_element_endpoint(
                raw_link.get("target_element_candidate"),
                artifact_ref=artifact_ref,
                relationship_proposal_ref=relationship_proposal_ref,
                link_id=link_id,
                endpoint_role="target",
                candidate_ids=candidate_ids,
                candidate_names=candidate_names,
                element_subject_by_ref=element_subject_by_ref,
            )

            for resolution in (source_resolution, target_resolution):
                if resolution.warning_code is not None:
                    warning_codes.add(resolution.warning_code)
                if resolution.finding is not None:
                    endpoint_findings.append(resolution.finding)

            relationship_type = _exact_text(
                raw_link.get("link_type"),
                label="link_type",
            )
            source_statement = _exact_text(
                raw_link.get("source_statement"),
                label="source_statement",
            )

            evidence_ref = (
                f"{artifact_ref}#relationship-source:{link_id}"
            )
            previous_statement = evidence_by_ref.get(evidence_ref)
            if (
                previous_statement is not None
                and previous_statement != source_statement
            ):
                raise SemanticConsolidationIntegrityError(
                    "One relationship evidence reference has conflicting "
                    "source statements."
                )
            evidence_by_ref[evidence_ref] = source_statement

            proposals.append(
                RelationshipSemanticProposal(
                    proposal_ref=relationship_proposal_ref,
                    source_element_proposal_ref=(
                        source_resolution.proposal_ref
                    ),
                    source_semantic_subject_id=(
                        source_resolution.semantic_subject_id
                    ),
                    proposed_relationship_type=relationship_type,
                    target_element_proposal_ref=(
                        target_resolution.proposal_ref
                    ),
                    target_semantic_subject_id=(
                        target_resolution.semantic_subject_id
                    ),
                    semantic_statement=source_statement,
                    agent_id=agent_id,
                    persona_id=persona_id,
                    run_index=run_index,
                    upstream_artifact_ref=artifact_ref,
                    evidence_refs=(evidence_ref,),
                )
            )

    proposal_refs = tuple(
        proposal.proposal_ref for proposal in proposals
    )
    if len(proposal_refs) != len(set(proposal_refs)):
        raise SemanticConsolidationIntegrityError(
            "Exact relationship proposal references are not unique."
        )

    return PhaseFRelationshipSemanticInput(
        proposals=tuple(
            sorted(proposals, key=lambda item: item.proposal_ref)
        ),
        evidence=tuple(
            SemanticEvidenceStatement(
                evidence_ref=ref,
                statement=statement,
            )
            for ref, statement in sorted(evidence_by_ref.items())
        ),
        upstream_artifacts=tuple(
            upstream[key] for key in sorted(upstream)
        ),
        expected_persona_ids=tuple(sorted(expected_personas)),
        warning_codes=tuple(sorted(warning_codes)),
        endpoint_resolution_findings=tuple(
            sorted(
                endpoint_findings,
                key=lambda item: (
                    item.relationship_proposal_ref,
                    item.endpoint_role,
                ),
            )
        ),
        source_analysis_unit_id=(
            requested_source_analysis_unit_id
        ),
    )


def _semantic_comparator_instructions() -> str:
    return """
Return only one JSON object matching required_result in the input payload.

Your only responsibility is semantic identity comparison of existing element
proposals. Group proposals that express the same engineering concept even when
wording differs, for example grammatical variants, synonyms, or nominalized
phrases. Element classification is NOT semantic identity: two proposals may
belong to one semantic group while proposing different element types.

Authority constraints:
- Never invent, remove, rewrite, or approve an engineering proposal.
- Every provided proposal_ref must occur in exactly one group.
- Use only proposal content and exact evidence supplied in the payload.
- A multi-proposal group requires explicit equivalent comparisons connecting
  all members into one equivalence graph.
- If semantic equivalence is doubtful, do not merge; keep separate groups and
  use outcome uncertain for the relevant comparison.
- distinct and uncertain never authorize a merge.
- Keep rationales concise and semantic; do not expose chain-of-thought.
- Set method to semantic_model.
- Set trace_ref to pending; the runtime replaces it with the exact response
  trace after execution.
""".strip()


def _run_live_comparator(
    *,
    payload: dict[str, object],
    provider: str,
    model: str,
    api_key: str | None,
    trace_path: Path,
) -> dict[str, object]:
    client = create_llm_client(provider)
    result = client.generate(
        LLMRequest(
            provider=provider,
            model=model,
            api_key=api_key,
            instructions=_semantic_comparator_instructions(),
            input_text=json.dumps(
                payload,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ),
            metadata={
                "task_name": "semantic_element_consolidation",
                "semantic_consolidation": True,
            },
        )
    )

    trace_path.parent.mkdir(parents=True, exist_ok=True)
    trace_payload = {
        "task_name": "semantic_element_consolidation",
        "provider": result.provider,
        "model": result.model,
        "response_id": result.response_id,
        "status": result.raw_status,
        "usage": result.usage,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "output_text": result.text,
    }
    trace_path.write_text(
        json.dumps(trace_payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    raw = _strict_json_loads(
        result.text,
        label="semantic comparator output",
    )
    if not isinstance(raw, dict):
        raise SemanticConsolidationValidationError(
            "Semantic comparator output must be a JSON object."
        )
    raw = dict(raw)
    raw["method"] = "semantic_model"
    response_id = result.response_id
    if isinstance(response_id, str) and response_id.strip():
        trace_ref = f"llm-response:{response_id.strip()}"
    else:
        trace_ref = "llm-output-sha256:" + hashlib.sha256(
            result.text.encode("utf-8")
        ).hexdigest()
    raw["trace_ref"] = trace_ref
    return raw



def _relationship_semantic_comparator_instructions() -> str:
    return """
Return only one JSON object matching required_result in the input payload.

Your only responsibility is semantic identity comparison of existing directed
relationship proposals. Element endpoints are already consolidated engineering
subjects and are authoritative comparison guards.

Relationship classification is NOT semantic identity: proposals may belong to
one semantic relationship subject while using different relationship types.

Authority constraints:
- Never invent, remove, rewrite, or approve an engineering proposal.
- Every provided proposal_ref must occur in exactly one group.
- Never merge proposals with different source_semantic_subject_id values.
- Never merge proposals with different target_semantic_subject_id values.
- A multi-proposal group requires explicit equivalent comparisons connecting
  all members into one equivalence graph.
- If semantic equivalence is doubtful, do not merge; use uncertain.
- distinct and uncertain never authorize a merge.
- Keep rationales concise and semantic; do not expose chain-of-thought.
- Set method to semantic_model.
- Set trace_ref to pending; runtime replaces it with the exact response trace.
""".strip()


def _run_live_relationship_comparator(
    *,
    payload: dict[str, object],
    provider: str,
    model: str,
    api_key: str | None,
    trace_path: Path,
) -> dict[str, object]:
    client = create_llm_client(provider)
    result = client.generate(
        LLMRequest(
            provider=provider,
            model=model,
            api_key=api_key,
            instructions=_relationship_semantic_comparator_instructions(),
            input_text=json.dumps(
                payload,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ),
            metadata={
                "task_name": "semantic_relationship_consolidation",
                "semantic_consolidation": True,
            },
        )
    )

    trace_path.parent.mkdir(parents=True, exist_ok=True)
    trace_payload = {
        "task_name": "semantic_relationship_consolidation",
        "provider": result.provider,
        "model": result.model,
        "response_id": result.response_id,
        "status": result.raw_status,
        "usage": result.usage,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "output_text": result.text,
    }
    trace_path.write_text(
        json.dumps(
            trace_payload,
            indent=2,
            ensure_ascii=False,
        ) + "\n",
        encoding="utf-8",
    )

    raw = _strict_json_loads(
        result.text,
        label="relationship semantic comparator output",
    )
    if not isinstance(raw, dict):
        raise SemanticConsolidationValidationError(
            "Relationship semantic comparator output must be a JSON object."
        )
    raw = dict(raw)
    raw["method"] = "semantic_model"
    response_id = result.response_id
    if isinstance(response_id, str) and response_id.strip():
        trace_ref = f"llm-response:{response_id.strip()}"
    else:
        trace_ref = "llm-output-sha256:" + hashlib.sha256(
            result.text.encode("utf-8")
        ).hexdigest()
    raw["trace_ref"] = trace_ref
    return raw


def consolidate_phase_f_element_proposals(
    *,
    project_id: str,
    processing_run_id: str,
    created_at_utc: str,
    phase_f_result: object,
    phase_f_root: Path | str,
    repository_root: Path | str,
    provider: str,
    model: str,
    api_key: str | None,
    dry_run: bool,
    source_analysis_unit_id: str | None = None,
) -> PhaseFElementSemanticResult:
    """Consolidate and persist element semantics before review publication."""

    requested_source_analysis_unit_id = (
        _validated_optional_source_analysis_unit_id(
            source_analysis_unit_id
        )
    )
    inputs = build_phase_f_element_semantic_input(
        phase_f_result=phase_f_result,
        repository_root=repository_root,
        source_analysis_unit_id=(
            requested_source_analysis_unit_id
        ),
        allow_empty_proposals=(
            requested_source_analysis_unit_id is not None
        ),
    )
    phase_root = Path(phase_f_root)
    artifact_path, trace_path = _source_anchored_semantic_paths(
        phase_root=phase_root,
        source_analysis_unit_id=(
            requested_source_analysis_unit_id
        ),
        artifact_filename=(
            SEMANTIC_CONSOLIDATION_ARTIFACT_FILENAME
        ),
        trace_filename=SEMANTIC_COMPARATOR_TRACE_FILENAME,
    )

    if not inputs.proposals:
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_path.write_text(
            json.dumps(
                {
                    "semantic_consolidation": None,
                    "execution": {
                        "source_analysis_unit_id": (
                            requested_source_analysis_unit_id
                        ),
                        "degraded_to_singletons": False,
                        "warning_codes": [],
                        "expected_persona_ids": list(
                            inputs.expected_persona_ids
                        ),
                        "proposal_count": 0,
                        "semantic_subject_count": 0,
                        "no_element_proposals": True,
                    },
                },
                indent=2,
                ensure_ascii=False,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        return PhaseFElementSemanticResult(
            artifact_path=artifact_path,
            comparator_trace_path=None,
            degraded_to_singletons=False,
            warning_codes=(),
            proposal_count=0,
            semantic_subject_count=0,
            source_analysis_unit_id=(
                requested_source_analysis_unit_id
            ),
        )

    comparator = None
    if not dry_run:
        comparator = lambda payload: _run_live_comparator(
            payload=payload,
            provider=provider,
            model=model,
            api_key=api_key,
            trace_path=trace_path,
        )

    result = consolidate_element_proposals(
        project_id=project_id,
        processing_run_id=processing_run_id,
        created_at_utc=created_at_utc,
        upstream_artifacts=inputs.upstream_artifacts,
        proposals=inputs.proposals,
        evidence=inputs.evidence,
        comparator=comparator,
    )

    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "semantic_consolidation": semantic_consolidation_artifact_to_dict(
            result.artifact
        ),
        "execution": {
            "source_analysis_unit_id": (
                requested_source_analysis_unit_id
            ),
            "degraded_to_singletons": result.degraded_to_singletons,
            "warning_codes": list(result.warning_codes),
            "expected_persona_ids": list(inputs.expected_persona_ids),
            "proposal_count": len(inputs.proposals),
            "semantic_subject_count": len(result.artifact.subjects),
        },
    }
    artifact_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    relationship_inputs = build_phase_f_relationship_semantic_input(
        phase_f_result=phase_f_result,
        repository_root=repository_root,
        element_artifact=result.artifact,
        source_analysis_unit_id=(
            requested_source_analysis_unit_id
        ),
    )
    relationship_artifact_path = None
    relationship_trace_path = None
    relationship_degraded = False
    relationship_warnings: tuple[str, ...] = ()
    relationship_subject_count = 0

    if relationship_inputs.proposals:
        (
            relationship_artifact_path,
            relationship_trace_path,
        ) = _source_anchored_semantic_paths(
            phase_root=phase_root,
            source_analysis_unit_id=(
                requested_source_analysis_unit_id
            ),
            artifact_filename=(
                RELATIONSHIP_SEMANTIC_CONSOLIDATION_ARTIFACT_FILENAME
            ),
            trace_filename=(
                RELATIONSHIP_SEMANTIC_COMPARATOR_TRACE_FILENAME
            ),
        )

        relationship_comparator = None
        if not dry_run:
            relationship_comparator = lambda comparator_payload: (
                _run_live_relationship_comparator(
                    payload=comparator_payload,
                    provider=provider,
                    model=model,
                    api_key=api_key,
                    trace_path=relationship_trace_path,
                )
            )

        relationship_result = consolidate_relationship_proposals(
            project_id=project_id,
            processing_run_id=processing_run_id,
            created_at_utc=created_at_utc,
            upstream_artifacts=(
                relationship_inputs.upstream_artifacts
            ),
            proposals=relationship_inputs.proposals,
            evidence=relationship_inputs.evidence,
            comparator=relationship_comparator,
        )

        relationship_artifact_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        relationship_payload = {
            "semantic_consolidation": (
                semantic_consolidation_artifact_to_dict(
                    relationship_result.artifact
                )
            ),
            "execution": {
                "source_analysis_unit_id": (
                    requested_source_analysis_unit_id
                ),
                "degraded_to_singletons": (
                    relationship_result.degraded_to_singletons
                ),
                "warning_codes": list(
                    dict.fromkeys(
                        (
                            *relationship_inputs.warning_codes,
                            *relationship_result.warning_codes,
                        )
                    )
                ),
                "endpoint_resolution_findings": [
                    {
                        "relationship_proposal_ref": (
                            finding.relationship_proposal_ref
                        ),
                        "endpoint_role": finding.endpoint_role,
                        "endpoint_token": finding.endpoint_token,
                        "resolution_status": finding.resolution_status,
                        "candidate_proposal_refs": list(
                            finding.candidate_proposal_refs
                        ),
                    }
                    for finding in (
                        relationship_inputs.endpoint_resolution_findings
                    )
                ],
                "expected_persona_ids": list(
                    relationship_inputs.expected_persona_ids
                ),
                "proposal_count": len(
                    relationship_inputs.proposals
                ),
                "semantic_subject_count": len(
                    relationship_result.artifact.subjects
                ),
                "element_semantic_artifact_fingerprint": (
                    result.artifact.artifact_fingerprint
                ),
            },
        }
        relationship_artifact_path.write_text(
            json.dumps(
                relationship_payload,
                indent=2,
                ensure_ascii=False,
                sort_keys=True,
            ) + "\n",
            encoding="utf-8",
        )
        relationship_degraded = (
            relationship_result.degraded_to_singletons
        )
        relationship_warnings = tuple(
            dict.fromkeys(
                (
                    *relationship_inputs.warning_codes,
                    *relationship_result.warning_codes,
                )
            )
        )
        relationship_subject_count = len(
            relationship_result.artifact.subjects
        )

    return PhaseFElementSemanticResult(
        artifact_path=artifact_path,
        comparator_trace_path=(trace_path if trace_path.exists() else None),
        degraded_to_singletons=result.degraded_to_singletons,
        warning_codes=result.warning_codes,
        proposal_count=len(inputs.proposals),
        semantic_subject_count=len(result.artifact.subjects),
        source_analysis_unit_id=(
            requested_source_analysis_unit_id
        ),
        relationship_artifact_path=relationship_artifact_path,
        relationship_comparator_trace_path=(
            relationship_trace_path
            if (
                relationship_trace_path is not None
                and relationship_trace_path.exists()
            )
            else None
        ),
        relationship_degraded_to_singletons=relationship_degraded,
        relationship_warning_codes=relationship_warnings,
        relationship_proposal_count=len(
            relationship_inputs.proposals
        ),
        relationship_semantic_subject_count=(
            relationship_subject_count
        ),
    )


def consolidate_phase_f_source_analysis_unit_proposals(
    *,
    project_id: str,
    processing_run_id: str,
    created_at_utc: str,
    phase_f_result: object,
    phase_f_root: Path | str,
    repository_root: Path | str,
    provider: str,
    model: str,
    api_key: str | None,
    dry_run: bool,
) -> PhaseFSourceAnchoredSemanticResult:
    """Run local C2/C3 independently for every D2 Source Analysis Unit.

    This D3 boundary deliberately does not perform cross-unit semantic
    synthesis. D4 consumes these local artifacts.
    """

    raw_ids = getattr(
        phase_f_result,
        "source_analysis_unit_ids",
        None,
    )
    if not isinstance(raw_ids, tuple) or not raw_ids:
        raise SemanticConsolidationIntegrityError(
            "Source-anchored semantic consolidation requires the "
            "Phase-F source_analysis_unit_ids tuple."
        )

    unit_ids = tuple(
        validate_source_analysis_unit_id(value)
        for value in raw_ids
    )
    if len(unit_ids) != len(set(unit_ids)):
        raise SemanticConsolidationIntegrityError(
            "Phase-F source_analysis_unit_ids contains duplicates."
        )

    unit_results = tuple(
        consolidate_phase_f_element_proposals(
            project_id=project_id,
            processing_run_id=processing_run_id,
            created_at_utc=created_at_utc,
            phase_f_result=phase_f_result,
            phase_f_root=phase_f_root,
            repository_root=repository_root,
            provider=provider,
            model=model,
            api_key=api_key,
            dry_run=dry_run,
            source_analysis_unit_id=unit_id,
        )
        for unit_id in unit_ids
    )

    return PhaseFSourceAnchoredSemanticResult(
        unit_results=unit_results,
        source_analysis_unit_ids=unit_ids,
        element_proposal_count=sum(
            result.proposal_count
            for result in unit_results
        ),
        element_semantic_subject_count=sum(
            result.semantic_subject_count
            for result in unit_results
        ),
        relationship_proposal_count=sum(
            result.relationship_proposal_count
            for result in unit_results
        ),
        relationship_semantic_subject_count=sum(
            result.relationship_semantic_subject_count
            for result in unit_results
        ),
    )



def _load_local_semantic_artifact(
    path: Path,
    *,
    label: str,
) -> object | None:
    raw = _strict_json_loads(
        path.read_text(encoding="utf-8"),
        label=label,
    )
    if not isinstance(raw, dict):
        raise SemanticConsolidationValidationError(
            f"{label} must be a JSON object."
        )
    if "semantic_consolidation" not in raw:
        raise SemanticConsolidationValidationError(
            f"{label} is missing semantic_consolidation."
        )
    semantic = raw["semantic_consolidation"]
    if semantic is None:
        return None
    return semantic_consolidation_artifact_from_dict(semantic)


def build_phase_f_cross_unit_semantic_input(
    *,
    phase_f_result: object,
    source_anchored_result: PhaseFSourceAnchoredSemanticResult,
    repository_root: Path | str,
) -> PhaseFCrossUnitSemanticInput:
    """Reconstruct D4 inputs from exact D3 local subjects and proposals."""

    if not isinstance(
        source_anchored_result,
        PhaseFSourceAnchoredSemanticResult,
    ):
        raise SemanticConsolidationValidationError(
            "source_anchored_result must be a PhaseFSourceAnchoredSemanticResult."
        )
    unit_ids = source_anchored_result.source_analysis_unit_ids
    if not unit_ids or len(unit_ids) != len(
        source_anchored_result.unit_results
    ):
        raise SemanticConsolidationIntegrityError(
            "D3 source analysis unit result cardinality is inconsistent."
        )

    local_elements: list[LocalElementSubject] = []
    local_relationships: list[LocalRelationshipSubject] = []
    local_element_ref_by_identity: dict[tuple[str, str], str] = {}

    for expected_unit_id, unit_result in zip(
        unit_ids,
        source_anchored_result.unit_results,
        strict=True,
    ):
        if unit_result.source_analysis_unit_id != expected_unit_id:
            raise SemanticConsolidationIntegrityError(
                "D3 unit result order does not match source_analysis_unit_ids."
            )

        element_inputs = build_phase_f_element_semantic_input(
            phase_f_result=phase_f_result,
            repository_root=repository_root,
            source_analysis_unit_id=expected_unit_id,
            allow_empty_proposals=True,
        )
        element_artifact = _load_local_semantic_artifact(
            unit_result.artifact_path,
            label=(
                f"D3 element artifact for {expected_unit_id}"
            ),
        )
        if element_artifact is None:
            if element_inputs.proposals:
                raise SemanticConsolidationIntegrityError(
                    "D3 element artifact is empty despite available proposals."
                )
            continue

        proposal_by_ref = {
            proposal.proposal_ref: proposal
            for proposal in element_inputs.proposals
        }
        for subject in element_artifact.subjects:
            members = tuple(subject.member_proposal_refs)
            try:
                member_proposals = tuple(
                    proposal_by_ref[ref] for ref in members
                )
            except KeyError as exc:
                raise SemanticConsolidationIntegrityError(
                    "D3 element subject references an unavailable exact proposal."
                ) from exc

            local_ref = (
                f"{expected_unit_id}#element-subject:"
                f"{subject.semantic_subject_id}"
            )
            local_elements.append(
                LocalElementSubject(
                    local_subject_ref=local_ref,
                    source_analysis_unit_id=expected_unit_id,
                    local_semantic_subject_id=(
                        subject.semantic_subject_id
                    ),
                    member_proposal_refs=tuple(sorted(members)),
                    candidate_names=tuple(
                        sorted(
                            {
                                proposal.candidate_name
                                for proposal in member_proposals
                            }
                        )
                    ),
                    proposed_element_types=tuple(
                        sorted(
                            {
                                proposal.proposed_element_type
                                for proposal in member_proposals
                            }
                        )
                    ),
                    concise_descriptions=tuple(
                        sorted(
                            {
                                proposal.concise_description
                                for proposal in member_proposals
                            }
                        )
                    ),
                    evidence_refs=tuple(
                        sorted(
                            {
                                ref
                                for proposal in member_proposals
                                for ref in proposal.evidence_refs
                            }
                        )
                    ),
                )
            )
            key = (
                expected_unit_id,
                subject.semantic_subject_id,
            )
            if key in local_element_ref_by_identity:
                raise SemanticConsolidationIntegrityError(
                    "D3 repeats one local element semantic subject identity."
                )
            local_element_ref_by_identity[key] = local_ref

        relationship_path = unit_result.relationship_artifact_path
        if relationship_path is None:
            continue

        relationship_artifact = _load_local_semantic_artifact(
            relationship_path,
            label=(
                f"D3 relationship artifact for {expected_unit_id}"
            ),
        )
        if relationship_artifact is None:
            continue

        relationship_inputs = build_phase_f_relationship_semantic_input(
            phase_f_result=phase_f_result,
            repository_root=repository_root,
            element_artifact=element_artifact,
            source_analysis_unit_id=expected_unit_id,
        )
        relationship_proposal_by_ref = {
            proposal.proposal_ref: proposal
            for proposal in relationship_inputs.proposals
        }

        for subject in relationship_artifact.subjects:
            members = tuple(subject.member_proposal_refs)
            try:
                member_proposals = tuple(
                    relationship_proposal_by_ref[ref]
                    for ref in members
                )
            except KeyError as exc:
                raise SemanticConsolidationIntegrityError(
                    "D3 relationship subject references an unavailable exact proposal."
                ) from exc

            source_ids = {
                proposal.source_semantic_subject_id
                for proposal in member_proposals
            }
            target_ids = {
                proposal.target_semantic_subject_id
                for proposal in member_proposals
            }
            if len(source_ids) != 1 or len(target_ids) != 1:
                raise SemanticConsolidationIntegrityError(
                    "One D3 relationship subject contains conflicting local endpoints."
                )
            source_local_id = next(iter(source_ids))
            target_local_id = next(iter(target_ids))

            source_local_ref = local_element_ref_by_identity.get(
                (expected_unit_id, source_local_id)
            )
            target_local_ref = local_element_ref_by_identity.get(
                (expected_unit_id, target_local_id)
            )

            source_unresolved = None
            if source_local_ref is None:
                if not source_local_id.startswith(
                    "semantic:unresolved-element-endpoint:"
                ):
                    raise SemanticConsolidationIntegrityError(
                        "D3 relationship source endpoint is neither a local element subject nor an explicit unresolved endpoint."
                    )
                source_unresolved = source_local_id

            target_unresolved = None
            if target_local_ref is None:
                if not target_local_id.startswith(
                    "semantic:unresolved-element-endpoint:"
                ):
                    raise SemanticConsolidationIntegrityError(
                        "D3 relationship target endpoint is neither a local element subject nor an explicit unresolved endpoint."
                    )
                target_unresolved = target_local_id

            local_relationships.append(
                LocalRelationshipSubject(
                    local_subject_ref=(
                        f"{expected_unit_id}#relationship-subject:"
                        f"{subject.semantic_subject_id}"
                    ),
                    source_analysis_unit_id=expected_unit_id,
                    local_semantic_subject_id=(
                        subject.semantic_subject_id
                    ),
                    member_proposal_refs=tuple(sorted(members)),
                    source_local_element_subject_ref=(
                        source_local_ref
                    ),
                    source_unresolved_endpoint_ref=(
                        source_unresolved
                    ),
                    target_local_element_subject_ref=(
                        target_local_ref
                    ),
                    target_unresolved_endpoint_ref=(
                        target_unresolved
                    ),
                    proposed_relationship_types=tuple(
                        sorted(
                            {
                                proposal.proposed_relationship_type
                                for proposal in member_proposals
                            }
                        )
                    ),
                    semantic_statements=tuple(
                        sorted(
                            {
                                proposal.semantic_statement
                                for proposal in member_proposals
                            }
                        )
                    ),
                    evidence_refs=tuple(
                        sorted(
                            {
                                ref
                                for proposal in member_proposals
                                for ref in proposal.evidence_refs
                            }
                        )
                    ),
                )
            )

    return PhaseFCrossUnitSemanticInput(
        source_analysis_unit_ids=unit_ids,
        local_element_subjects=tuple(
            sorted(
                local_elements,
                key=lambda item: item.local_subject_ref,
            )
        ),
        local_relationship_subjects=tuple(
            sorted(
                local_relationships,
                key=lambda item: item.local_subject_ref,
            )
        ),
    )


def _cross_unit_comparator_instructions(*, proposal_kind: str) -> str:
    endpoint_guard = (
        "Never merge relationship subjects with different source or target "
        "synthesized element subject IDs.\n"
        if proposal_kind == "relationship"
        else ""
    )
    return (
        "Return only one JSON object matching required_result in the input payload.\n\n"
        "Compare only the provided already-localized semantic subjects. "
        "They originate from different canonical Source Analysis Units; raw "
        "Agent proposals have already been consolidated locally.\n\n"
        "Authority constraints:\n"
        "- Never invent, remove, rewrite, or approve an engineering subject.\n"
        "- Every provided local_subject_ref must occur in exactly one group.\n"
        "- A multi-subject group requires explicit equivalent comparisons "
        "connecting all members into one equivalence graph.\n"
        "- If equivalence is doubtful, keep subjects separate and use uncertain.\n"
        "- distinct and uncertain never authorize a merge.\n"
        + endpoint_guard
        + "- Keep rationales concise and semantic; do not expose chain-of-thought.\n"
        "- Set method to semantic_model.\n"
        "- Set trace_ref to pending; runtime replaces it with the exact response trace."
    )


def _run_live_cross_unit_comparator(
    *,
    payload: dict[str, object],
    provider: str,
    model: str,
    api_key: str | None,
    trace_path: Path,
    proposal_kind: str,
) -> dict[str, object]:
    client = create_llm_client(provider)
    task_name = f"cross_unit_{proposal_kind}_semantic_synthesis"
    result = client.generate(
        LLMRequest(
            provider=provider,
            model=model,
            api_key=api_key,
            instructions=_cross_unit_comparator_instructions(
                proposal_kind=proposal_kind
            ),
            input_text=json.dumps(
                payload,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ),
            metadata={
                "task_name": task_name,
                "semantic_consolidation": True,
                "cross_unit_synthesis": True,
            },
        )
    )

    trace_path.parent.mkdir(parents=True, exist_ok=True)
    trace_path.write_text(
        json.dumps(
            {
                "task_name": task_name,
                "provider": result.provider,
                "model": result.model,
                "response_id": result.response_id,
                "status": result.raw_status,
                "usage": result.usage,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "output_text": result.text,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    raw = _strict_json_loads(
        result.text,
        label=f"cross-unit {proposal_kind} comparator output",
    )
    if not isinstance(raw, dict):
        raise SemanticConsolidationValidationError(
            "Cross-unit comparator output must be a JSON object."
        )
    raw = dict(raw)
    raw["method"] = "semantic_model"
    response_id = result.response_id
    if isinstance(response_id, str) and response_id.strip():
        raw["trace_ref"] = f"llm-response:{response_id.strip()}"
    else:
        raw["trace_ref"] = "llm-output-sha256:" + hashlib.sha256(
            result.text.encode("utf-8")
        ).hexdigest()
    return raw


def synthesize_phase_f_source_analysis_units(
    *,
    project_id: str,
    processing_run_id: str,
    created_at_utc: str,
    phase_f_result: object,
    source_anchored_result: PhaseFSourceAnchoredSemanticResult,
    phase_f_root: Path | str,
    repository_root: Path | str,
    provider: str,
    model: str,
    api_key: str | None,
    dry_run: bool,
) -> PhaseFCrossUnitSemanticResult:
    """Persist D4 synthesis after all D3 Source Analysis Units are complete."""

    inputs = build_phase_f_cross_unit_semantic_input(
        phase_f_result=phase_f_result,
        source_anchored_result=source_anchored_result,
        repository_root=repository_root,
    )
    phase_root = Path(phase_f_root)
    artifact_path = (
        phase_root
        / "consensus_reports"
        / CROSS_UNIT_SYNTHESIS_STAGE_DIRECTORY
        / CROSS_UNIT_SYNTHESIS_ARTIFACT_FILENAME
    )
    element_trace_path = (
        phase_root
        / "agent_outputs"
        / CROSS_UNIT_SYNTHESIS_STAGE_DIRECTORY
        / CROSS_UNIT_ELEMENT_COMPARATOR_TRACE_FILENAME
    )
    relationship_trace_path = (
        phase_root
        / "agent_outputs"
        / CROSS_UNIT_SYNTHESIS_STAGE_DIRECTORY
        / CROSS_UNIT_RELATIONSHIP_COMPARATOR_TRACE_FILENAME
    )

    element_comparator = None
    relationship_comparator = None
    if not dry_run:
        element_comparator = lambda payload: _run_live_cross_unit_comparator(
            payload=payload,
            provider=provider,
            model=model,
            api_key=api_key,
            trace_path=element_trace_path,
            proposal_kind="element",
        )
        relationship_comparator = lambda payload: _run_live_cross_unit_comparator(
            payload=payload,
            provider=provider,
            model=model,
            api_key=api_key,
            trace_path=relationship_trace_path,
            proposal_kind="relationship",
        )

    result = synthesize_cross_unit_semantics(
        project_id=project_id,
        processing_run_id=processing_run_id,
        created_at_utc=created_at_utc,
        source_analysis_unit_ids=inputs.source_analysis_unit_ids,
        local_element_subjects=inputs.local_element_subjects,
        local_relationship_subjects=inputs.local_relationship_subjects,
        element_comparator=element_comparator,
        relationship_comparator=relationship_comparator,
    )

    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text(
        json.dumps(
            {
                "cross_unit_semantic_synthesis": (
                    cross_unit_semantic_synthesis_artifact_to_dict(
                        result.artifact
                    )
                ),
                "execution": {
                    "element_degraded_to_singletons": (
                        result.element_degraded_to_singletons
                    ),
                    "element_warning_codes": list(
                        result.element_warning_codes
                    ),
                    "relationship_degraded_to_singletons": (
                        result.relationship_degraded_to_singletons
                    ),
                    "relationship_warning_codes": list(
                        result.relationship_warning_codes
                    ),
                    "local_element_subject_count": len(
                        inputs.local_element_subjects
                    ),
                    "synthesized_element_subject_count": len(
                        result.artifact.synthesized_element_subjects
                    ),
                    "local_relationship_subject_count": len(
                        inputs.local_relationship_subjects
                    ),
                    "synthesized_relationship_subject_count": len(
                        result.artifact.synthesized_relationship_subjects
                    ),
                    "relationship_rebinding_finding_count": len(
                        result.artifact.relationship_rebinding_findings
                    ),
                },
            },
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    return PhaseFCrossUnitSemanticResult(
        artifact_path=artifact_path,
        element_comparator_trace_path=(
            element_trace_path if element_trace_path.exists() else None
        ),
        relationship_comparator_trace_path=(
            relationship_trace_path
            if relationship_trace_path.exists()
            else None
        ),
        element_degraded_to_singletons=(
            result.element_degraded_to_singletons
        ),
        element_warning_codes=result.element_warning_codes,
        relationship_degraded_to_singletons=(
            result.relationship_degraded_to_singletons
        ),
        relationship_warning_codes=result.relationship_warning_codes,
        local_element_subject_count=len(inputs.local_element_subjects),
        synthesized_element_subject_count=len(
            result.artifact.synthesized_element_subjects
        ),
        local_relationship_subject_count=len(
            inputs.local_relationship_subjects
        ),
        synthesized_relationship_subject_count=len(
            result.artifact.synthesized_relationship_subjects
        ),
        relationship_rebinding_finding_count=len(
            result.artifact.relationship_rebinding_findings
        ),
    )


def consolidate_phase_f_source_anchored_pipeline(
    *,
    project_id: str,
    processing_run_id: str,
    created_at_utc: str,
    phase_f_result: object,
    phase_f_root: Path | str,
    repository_root: Path | str,
    provider: str,
    model: str,
    api_key: str | None,
    dry_run: bool,
) -> PhaseFSourceAnchoredSemanticPipelineResult:
    """Run ADR-026 D3 local consolidation followed by D4 cross-unit synthesis.

    The project-bound Processing bridge calls this compiled boundary only after
    D2 has completed all canonical Source Analysis Units. Human Review remains
    downstream; this function creates semantic authority evidence but performs
    no engineering approval.
    """

    source_anchored_result = (
        consolidate_phase_f_source_analysis_unit_proposals(
            project_id=project_id,
            processing_run_id=processing_run_id,
            created_at_utc=created_at_utc,
            phase_f_result=phase_f_result,
            phase_f_root=phase_f_root,
            repository_root=repository_root,
            provider=provider,
            model=model,
            api_key=api_key,
            dry_run=dry_run,
        )
    )

    cross_unit_result = synthesize_phase_f_source_analysis_units(
        project_id=project_id,
        processing_run_id=processing_run_id,
        created_at_utc=created_at_utc,
        phase_f_result=phase_f_result,
        source_anchored_result=source_anchored_result,
        phase_f_root=phase_f_root,
        repository_root=repository_root,
        provider=provider,
        model=model,
        api_key=api_key,
        dry_run=dry_run,
    )

    return PhaseFSourceAnchoredSemanticPipelineResult(
        source_anchored_result=source_anchored_result,
        cross_unit_result=cross_unit_result,
    )
