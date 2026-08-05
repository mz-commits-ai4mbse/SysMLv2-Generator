"""Adapt structured P9 Agent Outputs into immutable review proposals."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import unicodedata
from typing import Any

from modules.project_processing import (
    ProcessingArtifactReference,
    ProcessingValidationError,
    validate_processing_artifact_reference,
)

from .errors import (
    ReviewIntegrityError,
    ReviewReferenceError,
    ReviewValidationError,
)
from .evidence_adapter import (
    AGENTIC_INGESTION_STAGE,
    P9ReviewEvidenceSet,
)
from .types import ReviewProposalReference


DERIVATION_STAGE_DIRECTORY = "03_derivation_assessment"
DERIVATION_TEAM_ID = "TEAM_DERIVATION_ASSESSMENT"

P9_ELEMENT_TYPES = frozenset(
    {
        "actor",
        "stakeholder",
        "system",
        "subsystem",
        "requirement",
        "use_case",
        "function",
        "item",
        "interface",
        "constraint",
        "risk",
        "verification_case",
        "data_object",
        "package",
        "other",
    }
)

P9_CONFIDENCE_LEVELS = frozenset(
    {
        "high",
        "medium",
        "low",
    }
)

P9_GENERATION_READINESS_LEVELS = frozenset(
    {
        "ready",
        "partial",
        "blocked",
    }
)

P9_SOURCE_ASSIGNMENT_TYPES = frozenset(
    {
        "defines_element",
        "names_element",
        "describes_behavior",
        "describes_property",
        "states_requirement",
        "states_constraint",
        "describes_input",
        "describes_output",
        "mentions_interface",
        "describes_risk",
        "unclear_assignment",
    }
)

_DERIVATION_OUTPUT_FIELDS = frozenset(
    {
        "candidate_model_elements",
        "explicit_source_links",
        "sysml_model_buildability",
        "missing_information_for_model_building",
        "possible_but_unsupported_interpretations",
        "model_artifact_assessments",
        "cross_artifact_observations",
        "blocked_generation_tasks",
    }
)

_ELEMENT_FIELDS = frozenset(
    {
        "candidate_id",
        "element_type",
        "candidate_name",
        "description",
        "source_basis",
        "assigned_source_information",
        "confidence",
        "generation_readiness",
        "missing_information",
        "rationale_summary",
    }
)

_SOURCE_ASSIGNMENT_FIELDS = frozenset(
    {
        "source_info_id",
        "source_statement",
        "assignment_type",
        "confidence",
    }
)

_LINK_FIELDS = frozenset(
    {
        "link_id",
        "source_element_candidate",
        "link_type",
        "target_element_candidate",
        "source_basis",
        "source_statement",
        "confidence",
        "rationale_summary",
    }
)

_GENERIC_IDENTIFIER_PATTERN = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,239}$"
)


@dataclass(frozen=True, slots=True)
class P9SourceAssignment:
    """One exact source assignment contained in an Agent proposal."""

    source_info_id: str
    source_statement: str
    assignment_type: str
    confidence: str


@dataclass(frozen=True, slots=True)
class P9ElementProposal:
    """One structured element proposal from one P9 Agent Output."""

    stable_subject_key: str
    candidate_id: str
    element_type: str
    candidate_name: str
    description: str
    source_basis: tuple[str, ...]
    source_assignments: tuple[P9SourceAssignment, ...]
    confidence: str
    generation_readiness: str
    missing_information: tuple[str, ...]
    rationale_summary: str
    proposal_reference: ReviewProposalReference


@dataclass(frozen=True, slots=True)
class P9RelationshipProposal:
    """One explicit source-supported relationship proposal."""

    stable_subject_key: str
    link_id: str
    source_element_candidate: str
    source_subject_key: str
    link_type: str
    target_element_candidate: str
    target_subject_key: str
    source_basis: tuple[str, ...]
    source_statement: str
    confidence: str
    rationale_summary: str
    proposal_reference: ReviewProposalReference


@dataclass(frozen=True, slots=True)
class P9StructuredProposalSet:
    """All structured element and relationship proposals for one P9 set."""

    project_id: str
    source_id: str
    processing_run_id: str
    attempt_id: str
    element_proposals: tuple[P9ElementProposal, ...]
    relationship_proposals: tuple[
        P9RelationshipProposal,
        ...,
    ]

    @property
    def proposal_count(self) -> int:
        """Return the total number of exact Agent proposals."""

        return (
            len(self.element_proposals)
            + len(self.relationship_proposals)
        )


def adapt_p9_agent_proposals(
    p9_evidence: object,
    *,
    repository_root: Path | str,
) -> P9StructuredProposalSet:
    """Adapt exact structured derivation outputs into review proposals.

    The operation is deterministic and read-only. Markdown is not parsed.
    """

    if not isinstance(p9_evidence, P9ReviewEvidenceSet):
        raise ReviewValidationError(
            "p9_evidence must be a P9ReviewEvidenceSet."
        )

    root = _validated_repository_root(repository_root)

    derivation_references = tuple(
        reference
        for reference in p9_evidence.agent_output_references
        if _is_derivation_reference(reference)
    )

    if not derivation_references:
        raise ReviewReferenceError(
            "P9 Review Evidence contains no structured "
            "derivation-assessment Agent Outputs."
        )

    execution_keys: set[
        tuple[str, str, int]
    ] = set()

    element_proposals: list[P9ElementProposal] = []
    relationship_proposals: list[
        P9RelationshipProposal
    ] = []

    for reference in sorted(
        derivation_references,
        key=_reference_key,
    ):
        wrapper = _load_agent_wrapper(
            reference,
            repository_root=root,
            p9_evidence=p9_evidence,
        )

        execution_key = (
            wrapper["agent_id"],
            wrapper["persona_id"],
            wrapper["run_index"],
        )

        if execution_key in execution_keys:
            raise ReviewIntegrityError(
                "P9 contains duplicate derivation Agent "
                "execution identity."
            )

        execution_keys.add(execution_key)

        output = _parse_derivation_output(
            wrapper["output_text"]
        )

        artifact_elements = _adapt_element_proposals(
            output["candidate_model_elements"],
            reference=reference,
            agent_id=wrapper["agent_id"],
            persona_id=wrapper["persona_id"],
        )

        element_proposals.extend(artifact_elements)

        relationship_proposals.extend(
            _adapt_relationship_proposals(
                output["explicit_source_links"],
                reference=reference,
                agent_id=wrapper["agent_id"],
                persona_id=wrapper["persona_id"],
                element_proposals=artifact_elements,
            )
        )

    if not element_proposals:
        raise ReviewIntegrityError(
            "Structured P9 derivation evidence contains "
            "no candidate model elements."
        )

    return P9StructuredProposalSet(
        project_id=p9_evidence.project_id,
        source_id=p9_evidence.source_id,
        processing_run_id=(
            p9_evidence.processing_run_id
        ),
        attempt_id=p9_evidence.attempt_id,
        element_proposals=tuple(
            sorted(
                element_proposals,
                key=lambda item: (
                    item.stable_subject_key,
                    item.proposal_reference
                    .artifact_reference.artifact_id,
                    item.candidate_id,
                ),
            )
        ),
        relationship_proposals=tuple(
            sorted(
                relationship_proposals,
                key=lambda item: (
                    item.stable_subject_key,
                    item.proposal_reference
                    .artifact_reference.artifact_id,
                    item.link_id,
                ),
            )
        ),
    )


def _adapt_element_proposals(
    values: object,
    *,
    reference: ProcessingArtifactReference,
    agent_id: str,
    persona_id: str,
) -> tuple[P9ElementProposal, ...]:
    if not isinstance(values, list):
        raise ReviewValidationError(
            "candidate_model_elements must be a JSON array."
        )

    proposals: list[P9ElementProposal] = []
    candidate_ids: set[str] = set()
    subject_keys: set[str] = set()

    for value in values:
        data = _exact_object(
            value,
            expected_fields=_ELEMENT_FIELDS,
            label="candidate model element",
        )

        candidate_id = _identifier(
            data["candidate_id"],
            "candidate_id",
        )
        element_type = _enum_value(
            data["element_type"],
            P9_ELEMENT_TYPES,
            "element_type",
        )
        candidate_name = _text(
            data["candidate_name"],
            "candidate_name",
        )
        description = _text(
            data["description"],
            "description",
        )
        source_basis = _string_tuple(
            data["source_basis"],
            label="source_basis",
            require_nonempty=True,
            identifiers=True,
        )
        source_assignments = (
            _parse_source_assignments(
                data["assigned_source_information"]
            )
        )
        confidence = _enum_value(
            data["confidence"],
            P9_CONFIDENCE_LEVELS,
            "confidence",
        )
        generation_readiness = _enum_value(
            data["generation_readiness"],
            P9_GENERATION_READINESS_LEVELS,
            "generation_readiness",
        )
        missing_information = _string_tuple(
            data["missing_information"],
            label="missing_information",
            require_nonempty=False,
            identifiers=False,
        )
        rationale_summary = _text(
            data["rationale_summary"],
            "rationale_summary",
        )

        if candidate_id in candidate_ids:
            raise ReviewIntegrityError(
                "Candidate IDs must be unique within one "
                "derivation Agent Output."
            )

        candidate_ids.add(candidate_id)

        stable_subject_key = (
            create_element_stable_subject_key(
                element_type=element_type,
                candidate_name=candidate_name,
            )
        )

        if stable_subject_key in subject_keys:
            raise ReviewIntegrityError(
                "One derivation Agent Output contains "
                "multiple element candidates for the same "
                "normalized subject."
            )

        subject_keys.add(stable_subject_key)

        professional_content = {
            key: data[key]
            for key in sorted(_ELEMENT_FIELDS)
            if key != "candidate_id"
        }

        content_fingerprint = (
            _canonical_fingerprint(
                professional_content
            )
        )

        proposal_reference = ReviewProposalReference(
            artifact_reference=reference,
            agent_id=agent_id,
            persona_id=persona_id,
            proposal_id=candidate_id,
            proposal_content_fingerprint=(
                content_fingerprint
            ),
            original_report_locator=(
                "report:recognized_elements/"
                f"{stable_subject_key}"
            ),
            review_state="available",
        )

        proposals.append(
            P9ElementProposal(
                stable_subject_key=stable_subject_key,
                candidate_id=candidate_id,
                element_type=element_type,
                candidate_name=candidate_name,
                description=description,
                source_basis=source_basis,
                source_assignments=source_assignments,
                confidence=confidence,
                generation_readiness=(
                    generation_readiness
                ),
                missing_information=(
                    missing_information
                ),
                rationale_summary=rationale_summary,
                proposal_reference=proposal_reference,
            )
        )

    return tuple(proposals)


def _adapt_relationship_proposals(
    values: object,
    *,
    reference: ProcessingArtifactReference,
    agent_id: str,
    persona_id: str,
    element_proposals: tuple[
        P9ElementProposal,
        ...,
    ],
) -> tuple[P9RelationshipProposal, ...]:
    if not isinstance(values, list):
        raise ReviewValidationError(
            "explicit_source_links must be a JSON array."
        )

    by_candidate_id = {
        proposal.candidate_id: proposal
        for proposal in element_proposals
    }

    by_normalized_name: dict[
        str,
        list[P9ElementProposal],
    ] = {}

    for proposal in element_proposals:
        by_normalized_name.setdefault(
            _normalize_subject_text(
                proposal.candidate_name
            ),
            [],
        ).append(proposal)

    proposals: list[P9RelationshipProposal] = []
    link_ids: set[str] = set()

    for value in values:
        data = _exact_object(
            value,
            expected_fields=_LINK_FIELDS,
            label="explicit source link",
        )

        link_id = _identifier(
            data["link_id"],
            "link_id",
        )
        source_element_candidate = _text(
            data["source_element_candidate"],
            "source_element_candidate",
        )
        link_type = _text(
            data["link_type"],
            "link_type",
        )
        target_element_candidate = _text(
            data["target_element_candidate"],
            "target_element_candidate",
        )
        source_basis = _string_tuple(
            data["source_basis"],
            label="relationship source_basis",
            require_nonempty=True,
            identifiers=True,
        )
        source_statement = _text(
            data["source_statement"],
            "source_statement",
        )
        confidence = _enum_value(
            data["confidence"],
            P9_CONFIDENCE_LEVELS,
            "relationship confidence",
        )
        rationale_summary = _text(
            data["rationale_summary"],
            "relationship rationale_summary",
        )

        if link_id in link_ids:
            raise ReviewIntegrityError(
                "Link IDs must be unique within one "
                "derivation Agent Output."
            )

        link_ids.add(link_id)

        source_proposal = _resolve_element_candidate(
            source_element_candidate,
            by_candidate_id=by_candidate_id,
            by_normalized_name=by_normalized_name,
        )
        target_proposal = _resolve_element_candidate(
            target_element_candidate,
            by_candidate_id=by_candidate_id,
            by_normalized_name=by_normalized_name,
        )

        stable_subject_key = (
            create_relationship_stable_subject_key(
                source_subject_key=(
                    source_proposal.stable_subject_key
                ),
                link_type=link_type,
                target_subject_key=(
                    target_proposal.stable_subject_key
                ),
            )
        )

        professional_content = {
            "source_subject_key": (
                source_proposal.stable_subject_key
            ),
            "link_type": link_type,
            "target_subject_key": (
                target_proposal.stable_subject_key
            ),
            "source_basis": list(source_basis),
            "source_statement": source_statement,
            "confidence": confidence,
            "rationale_summary": rationale_summary,
        }

        proposal_reference = ReviewProposalReference(
            artifact_reference=reference,
            agent_id=agent_id,
            persona_id=persona_id,
            proposal_id=link_id,
            proposal_content_fingerprint=(
                _canonical_fingerprint(
                    professional_content
                )
            ),
            original_report_locator=(
                "report:explicit_source_links/"
                f"{stable_subject_key}"
            ),
            review_state="available",
        )

        proposals.append(
            P9RelationshipProposal(
                stable_subject_key=stable_subject_key,
                link_id=link_id,
                source_element_candidate=(
                    source_element_candidate
                ),
                source_subject_key=(
                    source_proposal.stable_subject_key
                ),
                link_type=link_type,
                target_element_candidate=(
                    target_element_candidate
                ),
                target_subject_key=(
                    target_proposal.stable_subject_key
                ),
                source_basis=source_basis,
                source_statement=source_statement,
                confidence=confidence,
                rationale_summary=rationale_summary,
                proposal_reference=proposal_reference,
            )
        )

    return tuple(proposals)


def create_element_stable_subject_key(
    *,
    element_type: str,
    candidate_name: str,
) -> str:
    """Create a stable key independent of Agent and candidate IDs."""

    normalized_type = _normalize_subject_text(
        element_type
    )
    normalized_name = _normalize_subject_text(
        candidate_name
    )

    if not normalized_type or not normalized_name:
        raise ReviewValidationError(
            "Element subject content cannot be normalized."
        )

    semantic_identity = (
        f"{normalized_type}|{normalized_name}"
    )
    digest = hashlib.sha256(
        semantic_identity.encode("utf-8")
    ).hexdigest()[:20]

    name_fragment = normalized_name[:100]

    return (
        f"element:{normalized_type}:"
        f"{name_fragment}:{digest}"
    )


def create_relationship_stable_subject_key(
    *,
    source_subject_key: str,
    link_type: str,
    target_subject_key: str,
) -> str:
    """Create a stable key for one explicit semantic relationship."""

    normalized_link_type = _normalize_subject_text(
        link_type
    )

    if not normalized_link_type:
        raise ReviewValidationError(
            "Relationship intent cannot be normalized."
        )

    semantic_identity = "|".join(
        (
            source_subject_key,
            normalized_link_type,
            target_subject_key,
        )
    )
    digest = hashlib.sha256(
        semantic_identity.encode("utf-8")
    ).hexdigest()[:24]

    return (
        "relationship:"
        f"{normalized_link_type[:80]}:"
        f"{digest}"
    )


def _load_agent_wrapper(
    reference: ProcessingArtifactReference,
    *,
    repository_root: Path,
    p9_evidence: P9ReviewEvidenceSet,
) -> dict[str, Any]:
    content = _read_verified_agent_artifact(
        reference,
        repository_root=repository_root,
        p9_evidence=p9_evidence,
    )

    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ReviewReferenceError(
            "P9 Agent Output is not valid UTF-8."
        ) from exc

    wrapper = _parse_json_object(
        text,
        label="P9 Agent Output wrapper",
    )

    required_fields = {
        "team_id",
        "agent_id",
        "persona_id",
        "run_index",
        "status",
        "output_text",
    }

    missing = required_fields - set(wrapper)

    if missing:
        raise ReviewValidationError(
            "P9 Agent Output wrapper is missing "
            f"required fields: {sorted(missing)!r}."
        )

    if wrapper["team_id"] != DERIVATION_TEAM_ID:
        raise ReviewIntegrityError(
            "Derivation artifact does not identify the "
            "Derivation Assessment Team."
        )

    agent_id = _identifier(
        wrapper["agent_id"],
        "wrapper agent_id",
    )
    persona_id = _identifier(
        wrapper["persona_id"],
        "wrapper persona_id",
    )

    run_index = wrapper["run_index"]

    if (
        isinstance(run_index, bool)
        or not isinstance(run_index, int)
        or run_index < 1
        or run_index > 999_999
    ):
        raise ReviewValidationError(
            "wrapper run_index must be an integer "
            "between 1 and 999999."
        )

    if wrapper["status"] != "completed":
        raise ReviewIntegrityError(
            "Only completed derivation Agent Outputs may "
            "create structured review proposals."
        )

    output_text = wrapper["output_text"]

    if (
        not isinstance(output_text, str)
        or not output_text.strip()
    ):
        raise ReviewValidationError(
            "wrapper output_text must be a non-empty string."
        )

    return {
        "agent_id": agent_id,
        "persona_id": persona_id,
        "run_index": run_index,
        "output_text": output_text,
    }


def _parse_derivation_output(
    text: str,
) -> dict[str, Any]:
    if text.lstrip().startswith("```"):
        raise ReviewValidationError(
            "Structured derivation output must be raw JSON "
            "and must not use Markdown fences."
        )

    output = _parse_json_object(
        text,
        label="structured derivation output",
    )

    if set(output) != _DERIVATION_OUTPUT_FIELDS:
        missing = sorted(
            _DERIVATION_OUTPUT_FIELDS - set(output)
        )
        unknown = sorted(
            set(output) - _DERIVATION_OUTPUT_FIELDS
        )

        raise ReviewValidationError(
            "Structured derivation output fields do not "
            f"match the contract; missing={missing!r}, "
            f"unknown={unknown!r}."
        )

    for field_name in _DERIVATION_OUTPUT_FIELDS:
        if not isinstance(output[field_name], list):
            raise ReviewValidationError(
                f"{field_name} must be a JSON array."
            )

    return output


def _parse_source_assignments(
    values: object,
) -> tuple[P9SourceAssignment, ...]:
    if not isinstance(values, list):
        raise ReviewValidationError(
            "assigned_source_information must be "
            "a JSON array."
        )

    assignments: list[P9SourceAssignment] = []
    keys: set[tuple[str, str, str, str]] = set()

    for value in values:
        data = _exact_object(
            value,
            expected_fields=(
                _SOURCE_ASSIGNMENT_FIELDS
            ),
            label="assigned source information",
        )

        assignment = P9SourceAssignment(
            source_info_id=_identifier(
                data["source_info_id"],
                "source_info_id",
            ),
            source_statement=_text(
                data["source_statement"],
                "source_statement",
            ),
            assignment_type=_enum_value(
                data["assignment_type"],
                P9_SOURCE_ASSIGNMENT_TYPES,
                "assignment_type",
            ),
            confidence=_enum_value(
                data["confidence"],
                P9_CONFIDENCE_LEVELS,
                "source assignment confidence",
            ),
        )

        key = (
            assignment.source_info_id,
            assignment.source_statement,
            assignment.assignment_type,
            assignment.confidence,
        )

        if key in keys:
            raise ReviewIntegrityError(
                "assigned_source_information must "
                "not contain duplicates."
            )

        keys.add(key)
        assignments.append(assignment)

    return tuple(assignments)


def _resolve_element_candidate(
    value: str,
    *,
    by_candidate_id: dict[str, P9ElementProposal],
    by_normalized_name: dict[
        str,
        list[P9ElementProposal],
    ],
) -> P9ElementProposal:
    direct = by_candidate_id.get(value)

    if direct is not None:
        return direct

    normalized = _normalize_subject_text(value)
    matches = by_normalized_name.get(
        normalized,
        [],
    )

    if not matches:
        raise ReviewReferenceError(
            "Explicit source link references an "
            f"unavailable element candidate: {value!r}."
        )

    if len(matches) != 1:
        raise ReviewIntegrityError(
            "Explicit source link candidate name is "
            f"ambiguous: {value!r}."
        )

    return matches[0]


def _read_verified_agent_artifact(
    reference: ProcessingArtifactReference,
    *,
    repository_root: Path,
    p9_evidence: P9ReviewEvidenceSet,
) -> bytes:
    try:
        validate_processing_artifact_reference(
            reference
        )
    except ProcessingValidationError as exc:
        raise ReviewValidationError(
            "P9 contains an invalid Agent Output "
            "artifact reference."
        ) from exc

    if reference.artifact_type != "agent_outputs":
        raise ReviewIntegrityError(
            "Proposal adapter accepts only "
            "agent_outputs references."
        )

    relative_path = PurePosixPath(
        reference.repository_relative_path
    )

    expected_prefix = (
        "data",
        "projects",
        p9_evidence.project_id,
        "runs",
        p9_evidence.processing_run_id,
        "artifacts",
        "agent_outputs",
        AGENTIC_INGESTION_STAGE,
        p9_evidence.attempt_id,
    )

    if (
        relative_path.parts[: len(expected_prefix)]
        != expected_prefix
    ):
        raise ReviewIntegrityError(
            "Agent Output path does not match the "
            "selected Project, Run and Attempt."
        )

    if (
        DERIVATION_STAGE_DIRECTORY
        not in relative_path.parts[
            len(expected_prefix) :
        ]
    ):
        raise ReviewIntegrityError(
            "Selected proposal artifact is not a "
            "derivation-assessment output."
        )

    target = repository_root.joinpath(
        *relative_path.parts
    )

    current = repository_root

    for part in relative_path.parts:
        current = current / part

        if current.is_symlink():
            raise ReviewReferenceError(
                "P9 Agent Output path must not contain "
                "symbolic links."
            )

    try:
        resolved_root = repository_root.resolve(
            strict=True
        )
        resolved_target = target.resolve(
            strict=True
        )
        resolved_target.relative_to(resolved_root)
    except FileNotFoundError as exc:
        raise ReviewReferenceError(
            "Referenced P9 Agent Output does not exist."
        ) from exc
    except ValueError as exc:
        raise ReviewReferenceError(
            "Referenced P9 Agent Output escapes "
            "repository_root."
        ) from exc
    except OSError as exc:
        raise ReviewReferenceError(
            "Referenced P9 Agent Output cannot "
            "be resolved."
        ) from exc

    if not target.is_file():
        raise ReviewReferenceError(
            "Referenced P9 Agent Output is not "
            "a regular file."
        )

    try:
        content = target.read_bytes()
    except OSError as exc:
        raise ReviewReferenceError(
            "Referenced P9 Agent Output cannot be read."
        ) from exc

    if not content:
        raise ReviewIntegrityError(
            "Referenced P9 Agent Output must not be empty."
        )

    actual_fingerprint = hashlib.sha256(
        content
    ).hexdigest()

    if (
        actual_fingerprint
        != reference.content_fingerprint
    ):
        raise ReviewIntegrityError(
            "P9 Agent Output fingerprint does not "
            "match persisted content."
        )

    return content


def _is_derivation_reference(
    reference: ProcessingArtifactReference,
) -> bool:
    return (
        reference.artifact_type == "agent_outputs"
        and DERIVATION_STAGE_DIRECTORY
        in PurePosixPath(
            reference.repository_relative_path
        ).parts
    )


def _validated_repository_root(
    repository_root: Path | str,
) -> Path:
    try:
        root = Path(repository_root)
    except TypeError as exc:
        raise ReviewValidationError(
            "repository_root must be a filesystem path."
        ) from exc

    if root.is_symlink():
        raise ReviewReferenceError(
            "repository_root must not be a symbolic link."
        )

    if not root.exists() or not root.is_dir():
        raise ReviewReferenceError(
            "repository_root must be an existing directory."
        )

    return root


def _parse_json_object(
    text: str,
    *,
    label: str,
) -> dict[str, Any]:
    try:
        value = json.loads(
            text,
            object_pairs_hook=(
                _object_without_duplicate_keys
            ),
        )
    except ReviewIntegrityError:
        raise
    except json.JSONDecodeError as exc:
        raise ReviewValidationError(
            f"{label} is not valid JSON."
        ) from exc

    if not isinstance(value, dict):
        raise ReviewValidationError(
            f"{label} must be a JSON object."
        )

    return value


def _object_without_duplicate_keys(
    pairs: list[tuple[str, Any]],
) -> dict[str, Any]:
    result: dict[str, Any] = {}

    for key, value in pairs:
        if key in result:
            raise ReviewIntegrityError(
                f"Duplicate JSON key is not permitted: {key!r}."
            )

        result[key] = value

    return result


def _exact_object(
    value: object,
    *,
    expected_fields: frozenset[str],
    label: str,
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ReviewValidationError(
            f"{label} must be a JSON object."
        )

    if set(value) != expected_fields:
        missing = sorted(
            expected_fields - set(value)
        )
        unknown = sorted(
            set(value) - expected_fields
        )

        raise ReviewValidationError(
            f"{label} fields do not match the "
            f"contract; missing={missing!r}, "
            f"unknown={unknown!r}."
        )

    return value


def _identifier(
    value: object,
    label: str,
) -> str:
    if (
        not isinstance(value, str)
        or _GENERIC_IDENTIFIER_PATTERN.fullmatch(
            value
        )
        is None
    ):
        raise ReviewValidationError(
            f"{label} must be a supported identifier."
        )

    return value


def _text(
    value: object,
    label: str,
) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or "\x00" in value
        or "\r" in value
    ):
        raise ReviewValidationError(
            f"{label} must be non-empty normalized text."
        )

    return value


def _enum_value(
    value: object,
    allowed: frozenset[str],
    label: str,
) -> str:
    if value not in allowed:
        raise ReviewValidationError(
            f"{label} must be one of "
            f"{sorted(allowed)!r}."
        )

    return value


def _string_tuple(
    value: object,
    *,
    label: str,
    require_nonempty: bool,
    identifiers: bool,
) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ReviewValidationError(
            f"{label} must be a JSON array."
        )

    if require_nonempty and not value:
        raise ReviewIntegrityError(
            f"{label} must not be empty."
        )

    result = tuple(
        (
            _identifier(item, label)
            if identifiers
            else _text(item, label)
        )
        for item in value
    )

    if len(result) != len(set(result)):
        raise ReviewIntegrityError(
            f"{label} must not contain duplicates."
        )

    return result


def _normalize_subject_text(
    value: str,
) -> str:
    normalized = unicodedata.normalize(
        "NFKD",
        value.casefold(),
    )

    ascii_text = "".join(
        character
        for character in normalized
        if not unicodedata.combining(character)
    )

    tokens = re.findall(
        r"[a-z0-9]+",
        ascii_text,
    )

    return "_".join(tokens)


def _canonical_fingerprint(
    value: object,
) -> str:
    canonical = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )

    return hashlib.sha256(
        canonical.encode("utf-8")
    ).hexdigest()


def _reference_key(
    reference: ProcessingArtifactReference,
) -> tuple[str, str, str, str]:
    return (
        reference.artifact_type,
        reference.artifact_id,
        reference.content_fingerprint,
        reference.repository_relative_path,
    )
