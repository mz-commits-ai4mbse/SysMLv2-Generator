"""Project exact P9 proposals onto persisted semantic review subjects.

C4 keeps raw Agent proposals immutable and uses C2/C3 semantic artifacts only
as grouping/reference authority for Human Review. Historical Processing Runs
without semantic artifacts retain their legacy stable-subject projection.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import Iterable

from modules.source_analysis_units.identifiers import (
    validate_source_analysis_unit_id,
)
from modules.semantic_consolidation.artifact import (
    semantic_consolidation_artifact_from_dict,
)
from modules.semantic_consolidation.types import (
    SemanticConsolidationArtifact,
)

from .errors import (
    ReviewIntegrityError,
    ReviewReferenceError,
    ReviewValidationError,
)
from .evidence_adapter import P9ReviewEvidenceSet
from .p9_evidence_reference_adapter import (
    CONSENSUS_EVIDENCE_ROLE,
    P9ConsensusEvidenceFact,
    P9StructuredEvidenceSet,
    P9SubjectEvidence,
)
from .p9_proposal_adapter import (
    P9ElementProposal,
    P9RelationshipProposal,
    P9StructuredProposalSet,
)
from .types import ReviewEvidenceReference


SEMANTIC_ELEMENT_ARTIFACT_FILENAME = (
    "semantic_element_consolidation.json"
)
SEMANTIC_RELATIONSHIP_ARTIFACT_FILENAME = (
    "semantic_relationship_consolidation.json"
)

CROSS_UNIT_SEMANTIC_SYNTHESIS_ARTIFACT_FILENAME = (
    "cross_unit_semantic_synthesis.json"
)
_DERIVATION_STAGE_DIRECTORY = "03_derivation_assessment"
_CROSS_UNIT_SCHEMA_VERSION = "1.0.0"
_CROSS_UNIT_ARTIFACT_KIND = "cross_unit_semantic_synthesis"


@dataclass(frozen=True, slots=True)
class SemanticReviewProjectionResult:
    """Projected P9 review inputs plus explicit migration-mode evidence."""

    proposals: P9StructuredProposalSet
    evidence: P9StructuredEvidenceSet
    used_semantic_projection: bool
    element_semantic_subject_count: int
    relationship_semantic_subject_count: int


@dataclass(frozen=True, slots=True)
class _SemanticProjectionIndex:
    """Exact lookup from published P9 proposal identity to semantic subject."""

    element_subject_by_key: dict[tuple[str, str, str, str], str]
    relationship_subject_by_key: dict[tuple[str, str, str, str], str]
    semantic_evidence_by_subject: dict[
        str,
        ReviewEvidenceReference,
    ]
    element_subject_count: int
    relationship_subject_count: int
    projection_authority: str


def _strict_json_loads(text: str, *, label: str) -> object:
    if not isinstance(text, str):
        raise ReviewValidationError(
            f"{label} must be JSON text."
        )

    def no_duplicates(
        pairs: list[tuple[str, object]],
    ) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise ReviewIntegrityError(
                    f"{label} contains duplicate JSON key {key!r}."
                )
            result[key] = value
        return result

    try:
        return json.loads(
            text,
            object_pairs_hook=no_duplicates,
        )
    except ReviewIntegrityError:
        raise
    except json.JSONDecodeError as exc:
        raise ReviewReferenceError(
            f"{label} is not valid JSON."
        ) from exc


def _validated_root(value: Path | str) -> Path:
    root = Path(value).resolve()
    if not root.exists() or not root.is_dir():
        raise ReviewReferenceError(
            "repository_root must reference an existing directory."
        )
    return root


def _artifact_reference_for_filename(
    p9_evidence: P9ReviewEvidenceSet,
    filename: str,
):
    matches = tuple(
        reference
        for reference in p9_evidence.consensus_report_references
        if PurePosixPath(
            reference.repository_relative_path
        ).name == filename
    )
    if len(matches) > 1:
        raise ReviewIntegrityError(
            "P9 evidence contains duplicate semantic consolidation "
            f"artifacts named {filename!r}."
        )
    return matches[0] if matches else None


def _load_semantic_artifact(
    p9_evidence: P9ReviewEvidenceSet,
    *,
    filename: str,
    proposal_kind: str,
    repository_root: Path,
) -> SemanticConsolidationArtifact | None:
    reference = _artifact_reference_for_filename(
        p9_evidence,
        filename,
    )
    if reference is None:
        return None

    path = (
        repository_root
        / PurePosixPath(
            reference.repository_relative_path
        )
    ).resolve()
    try:
        path.relative_to(repository_root)
    except ValueError as exc:
        raise ReviewReferenceError(
            "Semantic consolidation artifact escaped repository_root."
        ) from exc

    if not path.is_file():
        raise ReviewReferenceError(
            "Published semantic consolidation artifact is unavailable."
        )

    content = path.read_bytes()
    if hashlib.sha256(content).hexdigest() != (
        reference.content_fingerprint
    ):
        raise ReviewIntegrityError(
            "Published semantic consolidation artifact fingerprint "
            "does not match Processing authority."
        )

    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ReviewReferenceError(
            "Semantic consolidation artifact is not valid UTF-8."
        ) from exc

    wrapper = _strict_json_loads(
        text,
        label="semantic consolidation artifact wrapper",
    )
    if not isinstance(wrapper, dict):
        raise ReviewValidationError(
            "Semantic consolidation wrapper must be a JSON object."
        )
    payload = wrapper.get("semantic_consolidation")
    if not isinstance(payload, dict):
        raise ReviewValidationError(
            "Semantic consolidation wrapper is missing "
            "semantic_consolidation."
        )

    try:
        artifact = semantic_consolidation_artifact_from_dict(
            payload
        )
    except Exception as exc:
        raise ReviewIntegrityError(
            "Published semantic consolidation artifact failed "
            "authority validation."
        ) from exc

    if (
        artifact.project_id != p9_evidence.project_id
        or artifact.processing_run_id
        != p9_evidence.processing_run_id
    ):
        raise ReviewIntegrityError(
            "Semantic consolidation artifact does not belong to the "
            "selected P9 Project/Processing Run."
        )

    if any(
        binding.proposal_kind != proposal_kind
        for binding in artifact.proposals
    ):
        raise ReviewIntegrityError(
            "Semantic consolidation artifact contains an unexpected "
            "proposal kind."
        )
    if any(
        subject.proposal_kind != proposal_kind
        for subject in artifact.subjects
    ):
        raise ReviewIntegrityError(
            "Semantic consolidation artifact contains an unexpected "
            "subject kind."
        )

    expected_prefix = f"semantic:{proposal_kind}:"
    if any(
        not subject.semantic_subject_id.startswith(
            expected_prefix
        )
        for subject in artifact.subjects
    ):
        raise ReviewIntegrityError(
            "Semantic subject identity does not use the expected "
            f"{proposal_kind!r} namespace."
        )

    return artifact


def _semantic_proposal_id(
    proposal_ref: str,
    *,
    proposal_kind: str,
) -> str:
    marker = f"#{proposal_kind}:"
    if proposal_ref.count(marker) != 1:
        raise ReviewIntegrityError(
            "Semantic proposal_ref does not expose one exact "
            f"{proposal_kind} proposal ID."
        )
    value = proposal_ref.split(marker, 1)[1]
    if not value or "#" in value:
        raise ReviewIntegrityError(
            "Semantic proposal_ref contains an invalid proposal ID."
        )
    return value


def _semantic_subject_index(
    artifact: SemanticConsolidationArtifact,
    *,
    proposal_kind: str,
) -> dict[tuple[str, str, str, str], str]:
    upstream = {
        item.artifact_ref: item.artifact_fingerprint
        for item in artifact.upstream_artifacts
    }

    subject_by_ref: dict[str, str] = {}
    for subject in artifact.subjects:
        for proposal_ref in subject.member_proposal_refs:
            if proposal_ref in subject_by_ref:
                raise ReviewIntegrityError(
                    "One semantic proposal belongs to multiple subjects."
                )
            subject_by_ref[proposal_ref] = (
                subject.semantic_subject_id
            )

    result: dict[
        tuple[str, str, str, str],
        str,
    ] = {}
    for binding in artifact.proposals:
        fingerprint = upstream.get(
            binding.upstream_artifact_ref
        )
        if fingerprint is None:
            raise ReviewIntegrityError(
                "Semantic proposal references an unavailable upstream "
                "artifact binding."
            )
        subject_id = subject_by_ref.get(
            binding.proposal_ref
        )
        if subject_id is None:
            raise ReviewIntegrityError(
                "Semantic proposal is not assigned to a semantic subject."
            )
        proposal_id = _semantic_proposal_id(
            binding.proposal_ref,
            proposal_kind=proposal_kind,
        )
        key = (
            fingerprint,
            binding.agent_id,
            binding.persona_id,
            proposal_id,
        )
        if key in result:
            raise ReviewIntegrityError(
                "Semantic proposal projection identity is not unique."
            )
        result[key] = subject_id

    return result


def _p9_proposal_key(
    proposal: P9ElementProposal | P9RelationshipProposal,
) -> tuple[str, str, str, str]:
    reference = proposal.proposal_reference
    return (
        reference.artifact_reference.content_fingerprint,
        reference.agent_id,
        reference.persona_id,
        reference.proposal_id,
    )


def _semantic_subject_evidence_reference(
    *,
    artifact: SemanticConsolidationArtifact,
    artifact_reference,
    semantic_subject_id: str,
) -> ReviewEvidenceReference:
    subject_matches = tuple(
        subject
        for subject in artifact.subjects
        if subject.semantic_subject_id
        == semantic_subject_id
    )
    if len(subject_matches) != 1:
        raise ReviewIntegrityError(
            "Semantic Review subject cannot be reconstructed uniquely "
            "from its consolidation artifact."
        )
    subject = subject_matches[0]
    members = set(subject.member_proposal_refs)
    comparisons = tuple(
        comparison
        for comparison in artifact.comparisons
        if (
            comparison.left_proposal_ref in members
            and comparison.right_proposal_ref in members
        )
    )

    fragment = {
        "semantic_subject_id": (
            subject.semantic_subject_id
        ),
        "proposal_kind": subject.proposal_kind,
        "member_proposal_refs": list(
            subject.member_proposal_refs
        ),
        "comparisons": [
            {
                "left_proposal_ref": (
                    comparison.left_proposal_ref
                ),
                "right_proposal_ref": (
                    comparison.right_proposal_ref
                ),
                "outcome": comparison.outcome,
                "method": comparison.method,
                "trace_ref": comparison.trace_ref,
                "rationale": comparison.rationale,
            }
            for comparison in comparisons
        ],
        "artifact_fingerprint": (
            artifact.artifact_fingerprint
        ),
    }
    canonical = json.dumps(
        fragment,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )

    return ReviewEvidenceReference(
        artifact_reference=artifact_reference,
        evidence_role=CONSENSUS_EVIDENCE_ROLE,
        evidence_locator=(
            "semantic_consolidation:/subjects/"
            f"{semantic_subject_id}"
        ),
        evidence_content_fingerprint=hashlib.sha256(
            canonical.encode("utf-8")
        ).hexdigest(),
    )


def _semantic_subject_evidence_catalog(
    *,
    artifact: SemanticConsolidationArtifact,
    artifact_reference,
) -> dict[str, ReviewEvidenceReference]:
    result = {}
    for subject in artifact.subjects:
        if subject.semantic_subject_id in result:
            raise ReviewIntegrityError(
                "Semantic consolidation repeats a semantic subject ID."
            )
        result[subject.semantic_subject_id] = (
            _semantic_subject_evidence_reference(
                artifact=artifact,
                artifact_reference=artifact_reference,
                semantic_subject_id=(
                    subject.semantic_subject_id
                ),
            )
        )
    return result



def _derivation_artifact_suffix(value: str) -> str:
    """Return the stable derivation-stage suffix shared by work and published paths."""

    if not isinstance(value, str) or not value:
        raise ReviewIntegrityError(
            "Semantic proposal artifact reference must be a non-empty string."
        )
    path = PurePosixPath(value)
    parts = path.parts
    try:
        index = parts.index(_DERIVATION_STAGE_DIRECTORY)
    except ValueError as exc:
        raise ReviewIntegrityError(
            "Semantic proposal artifact reference does not contain the "
            "derivation-stage boundary."
        ) from exc
    suffix = PurePosixPath(*parts[index:]).as_posix()
    if not suffix:
        raise ReviewIntegrityError(
            "Semantic proposal artifact suffix is unavailable."
        )
    return suffix


def _cross_unit_proposal_identity(
    proposal_ref: str,
    *,
    proposal_kind: str,
) -> tuple[str, str]:
    marker = f"#{proposal_kind}:"
    if not isinstance(proposal_ref, str) or proposal_ref.count(marker) != 1:
        raise ReviewIntegrityError(
            "Cross-unit synthesis proposal reference does not expose "
            f"one exact {proposal_kind} proposal ID."
        )
    artifact_ref, proposal_id = proposal_ref.split(marker, 1)
    if not proposal_id or "#" in proposal_id:
        raise ReviewIntegrityError(
            "Cross-unit synthesis proposal ID is invalid."
        )
    return (
        _derivation_artifact_suffix(artifact_ref),
        proposal_id,
    )


def _p9_derivation_proposal_identity(
    proposal: P9ElementProposal | P9RelationshipProposal,
    *,
    proposal_kind: str,
) -> tuple[str, str]:
    reference = proposal.proposal_reference
    proposal_id = (
        proposal.candidate_id
        if isinstance(proposal, P9ElementProposal)
        else proposal.link_id
    )
    return (
        _derivation_artifact_suffix(
            reference.artifact_reference.repository_relative_path
        ),
        proposal_id,
    )


def _cross_unit_artifact_payload(
    p9_evidence: P9ReviewEvidenceSet,
    *,
    repository_root: Path,
) -> tuple[dict[str, object], dict[str, object], object] | None:
    """Load and authority-check the published D4 synthesis wrapper."""

    reference = _artifact_reference_for_filename(
        p9_evidence,
        CROSS_UNIT_SEMANTIC_SYNTHESIS_ARTIFACT_FILENAME,
    )
    if reference is None:
        return None

    path = (
        repository_root
        / PurePosixPath(reference.repository_relative_path)
    ).resolve()
    try:
        path.relative_to(repository_root)
    except ValueError as exc:
        raise ReviewReferenceError(
            "Cross-unit semantic synthesis artifact escaped repository_root."
        ) from exc

    if not path.is_file():
        raise ReviewReferenceError(
            "Published cross-unit semantic synthesis artifact is unavailable."
        )

    content = path.read_bytes()
    if hashlib.sha256(content).hexdigest() != reference.content_fingerprint:
        raise ReviewIntegrityError(
            "Published cross-unit semantic synthesis artifact fingerprint "
            "does not match Processing authority."
        )

    try:
        wrapper = _strict_json_loads(
            content.decode("utf-8"),
            label="cross-unit semantic synthesis artifact wrapper",
        )
    except UnicodeDecodeError as exc:
        raise ReviewReferenceError(
            "Cross-unit semantic synthesis artifact is not valid UTF-8."
        ) from exc

    if not isinstance(wrapper, dict):
        raise ReviewValidationError(
            "Cross-unit semantic synthesis wrapper must be a JSON object."
        )
    payload = wrapper.get("cross_unit_semantic_synthesis")
    if not isinstance(payload, dict):
        raise ReviewValidationError(
            "Cross-unit semantic synthesis wrapper is missing "
            "cross_unit_semantic_synthesis."
        )
    execution = wrapper.get("execution")
    if not isinstance(execution, dict):
        raise ReviewValidationError(
            "Cross-unit semantic synthesis wrapper is missing "
            "execution quality evidence."
        )

    expected_fields = frozenset(
        {
            "schema_version",
            "artifact_kind",
            "project_id",
            "processing_run_id",
            "created_at_utc",
            "source_analysis_unit_ids",
            "local_element_subjects",
            "synthesized_element_subjects",
            "element_comparisons",
            "local_relationship_subjects",
            "synthesized_relationship_subjects",
            "relationship_comparisons",
            "relationship_rebinding_findings",
            "artifact_fingerprint",
        }
    )
    if frozenset(payload) != expected_fields:
        raise ReviewIntegrityError(
            "Cross-unit semantic synthesis artifact fields do not match "
            "the accepted D4 contract."
        )
    if payload["schema_version"] != _CROSS_UNIT_SCHEMA_VERSION:
        raise ReviewIntegrityError(
            "Cross-unit semantic synthesis schema version is unsupported."
        )
    if payload["artifact_kind"] != _CROSS_UNIT_ARTIFACT_KIND:
        raise ReviewIntegrityError(
            "Cross-unit semantic synthesis artifact kind is invalid."
        )
    if (
        payload["project_id"] != p9_evidence.project_id
        or payload["processing_run_id"]
        != p9_evidence.processing_run_id
    ):
        raise ReviewIntegrityError(
            "Cross-unit semantic synthesis artifact does not belong to "
            "the selected P9 Project/Processing Run."
        )

    fingerprint = payload["artifact_fingerprint"]
    if (
        not isinstance(fingerprint, str)
        or len(fingerprint) != 64
        or any(character not in "0123456789abcdef" for character in fingerprint)
    ):
        raise ReviewIntegrityError(
            "Cross-unit semantic synthesis artifact fingerprint is invalid."
        )
    without_fingerprint = dict(payload)
    without_fingerprint.pop("artifact_fingerprint")
    expected_fingerprint = hashlib.sha256(
        json.dumps(
            without_fingerprint,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    if fingerprint != expected_fingerprint:
        raise ReviewIntegrityError(
            "Cross-unit semantic synthesis internal fingerprint is invalid."
        )

    raw_unit_ids = payload["source_analysis_unit_ids"]
    if not isinstance(raw_unit_ids, list) or not raw_unit_ids:
        raise ReviewIntegrityError(
            "Cross-unit semantic synthesis must bind at least one "
            "Source Analysis Unit."
        )
    try:
        unit_ids = tuple(
            validate_source_analysis_unit_id(value)
            for value in raw_unit_ids
        )
    except Exception as exc:
        raise ReviewIntegrityError(
            "Cross-unit semantic synthesis contains an invalid "
            "Source Analysis Unit ID."
        ) from exc
    if unit_ids != tuple(sorted(set(unit_ids))):
        raise ReviewIntegrityError(
            "Cross-unit Source Analysis Unit IDs must be sorted and unique."
        )

    for field_name in (
        "local_element_subjects",
        "synthesized_element_subjects",
        "element_comparisons",
        "local_relationship_subjects",
        "synthesized_relationship_subjects",
        "relationship_comparisons",
        "relationship_rebinding_findings",
    ):
        if not isinstance(payload[field_name], list):
            raise ReviewIntegrityError(
                f"Cross-unit semantic synthesis {field_name} must be an array."
            )

    return payload, execution, reference


def _cross_unit_subject_evidence_reference(
    *,
    payload: dict[str, object],
    execution: dict[str, object],
    artifact_reference,
    proposal_kind: str,
    subject_payload: dict[str, object],
) -> ReviewEvidenceReference:
    subject_id = subject_payload.get("synthesized_subject_id")
    local_field = (
        "local_element_subjects"
        if proposal_kind == "element"
        else "local_relationship_subjects"
    )
    comparison_field = (
        "element_comparisons"
        if proposal_kind == "element"
        else "relationship_comparisons"
    )
    local_refs = subject_payload.get("member_local_subject_refs")
    if not isinstance(local_refs, list):
        raise ReviewIntegrityError(
            "Synthesized semantic subject has invalid local-subject references."
        )
    local_ref_set = set(local_refs)

    local_subjects = [
        item
        for item in payload[local_field]
        if (
            isinstance(item, dict)
            and item.get("local_subject_ref") in local_ref_set
        )
    ]
    if len(local_subjects) != len(local_ref_set):
        raise ReviewIntegrityError(
            "Synthesized semantic subject references an unavailable "
            "local semantic subject."
        )

    comparisons = [
        item
        for item in payload[comparison_field]
        if (
            isinstance(item, dict)
            and item.get("left_local_subject_ref") in local_ref_set
            and item.get("right_local_subject_ref") in local_ref_set
        )
    ]

    fragment: dict[str, object] = {
        "proposal_kind": proposal_kind,
        "synthesized_subject": subject_payload,
        "local_subjects": local_subjects,
        "comparisons": comparisons,
        "execution_quality": execution,
        "artifact_fingerprint": payload["artifact_fingerprint"],
    }

    if proposal_kind == "relationship":
        fragment["rebinding_findings"] = [
            item
            for item in payload["relationship_rebinding_findings"]
            if (
                isinstance(item, dict)
                and item.get("local_relationship_subject_ref")
                in local_ref_set
            )
        ]

    canonical = json.dumps(
        fragment,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return ReviewEvidenceReference(
        artifact_reference=artifact_reference,
        evidence_role=CONSENSUS_EVIDENCE_ROLE,
        evidence_locator=(
            "cross_unit_semantic_synthesis:/"
            f"synthesized_{proposal_kind}_subjects/"
            f"{subject_id}"
        ),
        evidence_content_fingerprint=hashlib.sha256(
            canonical.encode("utf-8")
        ).hexdigest(),
    )


def _cross_unit_review_subject_key(
    *,
    proposal_kind: str,
    synthesized_subject_id: str,
) -> str:
    """Map D4 authority IDs to canonical Review stable-subject keys.

    Synthesized Engineering Subject IDs remain explicit D4 domain
    identities. Review and Approved Input stable-subject keys are a
    separate, lower-case namespaced identity contract.
    """

    if proposal_kind == "element":
        expected_prefix = "SES-"
        review_prefix = "semantic:element:"
    elif proposal_kind == "relationship":
        expected_prefix = "SRS-"
        review_prefix = "semantic:relationship:"
    else:
        raise ReviewIntegrityError(
            "Cross-unit Review subject kind is unsupported."
        )

    if not synthesized_subject_id.startswith(expected_prefix):
        raise ReviewIntegrityError(
            "Cross-unit synthesized subject ID does not match "
            "its Review subject kind."
        )

    return review_prefix + synthesized_subject_id.lower()


def _cross_unit_projection_index(
    p9_evidence: P9ReviewEvidenceSet,
    structured_proposals: P9StructuredProposalSet,
    *,
    repository_root: Path,
) -> _SemanticProjectionIndex | None:
    loaded = _cross_unit_artifact_payload(
        p9_evidence,
        repository_root=repository_root,
    )
    if loaded is None:
        return None

    payload, execution, artifact_reference = loaded
    unit_ids = set(payload["source_analysis_unit_ids"])

    raw_elements = {
        _p9_derivation_proposal_identity(
            proposal,
            proposal_kind="element",
        ): proposal
        for proposal in structured_proposals.element_proposals
    }
    if len(raw_elements) != len(
        structured_proposals.element_proposals
    ):
        raise ReviewIntegrityError(
            "P9 element proposal derivation identity is not unique."
        )
    raw_relationships = {
        _p9_derivation_proposal_identity(
            proposal,
            proposal_kind="relationship",
        ): proposal
        for proposal in structured_proposals.relationship_proposals
    }
    if len(raw_relationships) != len(
        structured_proposals.relationship_proposals
    ):
        raise ReviewIntegrityError(
            "P9 relationship proposal derivation identity is not unique."
        )

    element_index: dict[tuple[str, str, str, str], str] = {}
    relationship_index: dict[tuple[str, str, str, str], str] = {}
    semantic_evidence: dict[str, ReviewEvidenceReference] = {}
    consumed_element_identities: set[tuple[str, str]] = set()
    consumed_relationship_identities: set[tuple[str, str]] = set()

    synthesized_elements = payload["synthesized_element_subjects"]
    element_subject_ids: set[str] = set()
    for subject in synthesized_elements:
        if not isinstance(subject, dict):
            raise ReviewIntegrityError(
                "Synthesized element subject must be a JSON object."
            )
        subject_id = subject.get("synthesized_subject_id")
        if (
            not isinstance(subject_id, str)
            or not subject_id.startswith("SES-")
            or len(subject_id) != 10
            or not subject_id[4:].isdigit()
            or subject_id == "SES-000000"
        ):
            raise ReviewIntegrityError(
                "Synthesized element subject ID is invalid."
            )
        if subject_id in element_subject_ids:
            raise ReviewIntegrityError(
                "Synthesized element subject IDs must be unique."
            )
        element_subject_ids.add(subject_id)

        subject_units = subject.get("source_analysis_unit_ids")
        if (
            not isinstance(subject_units, list)
            or not subject_units
            or not set(subject_units).issubset(unit_ids)
        ):
            raise ReviewIntegrityError(
                "Synthesized element subject has invalid "
                "Source Analysis Unit membership."
            )

        member_refs = subject.get("member_proposal_refs")
        if not isinstance(member_refs, list) or not member_refs:
            raise ReviewIntegrityError(
                "Synthesized element subject must contain proposal references."
            )
        for proposal_ref in member_refs:
            identity = _cross_unit_proposal_identity(
                proposal_ref,
                proposal_kind="element",
            )
            if identity in consumed_element_identities:
                raise ReviewIntegrityError(
                    "One P9 element proposal belongs to multiple "
                    "synthesized subjects."
                )
            proposal = raw_elements.get(identity)
            if proposal is None:
                raise ReviewIntegrityError(
                    "Cross-unit element synthesis references a proposal "
                    "outside the selected P9 proposal set."
                )
            consumed_element_identities.add(identity)
            review_subject_key = _cross_unit_review_subject_key(
                proposal_kind="element",
                synthesized_subject_id=subject_id,
            )
            element_index[_p9_proposal_key(proposal)] = (
                review_subject_key
            )

        semantic_evidence[review_subject_key] = (
            _cross_unit_subject_evidence_reference(
                payload=payload,
                execution=execution,
                artifact_reference=artifact_reference,
                proposal_kind="element",
                subject_payload=subject,
            )
        )

    synthesized_relationships = payload[
        "synthesized_relationship_subjects"
    ]
    relationship_subject_ids: set[str] = set()
    for subject in synthesized_relationships:
        if not isinstance(subject, dict):
            raise ReviewIntegrityError(
                "Synthesized relationship subject must be a JSON object."
            )
        subject_id = subject.get("synthesized_subject_id")
        if (
            not isinstance(subject_id, str)
            or not subject_id.startswith("SRS-")
            or len(subject_id) != 10
            or not subject_id[4:].isdigit()
            or subject_id == "SRS-000000"
        ):
            raise ReviewIntegrityError(
                "Synthesized relationship subject ID is invalid."
            )
        if subject_id in relationship_subject_ids:
            raise ReviewIntegrityError(
                "Synthesized relationship subject IDs must be unique."
            )
        relationship_subject_ids.add(subject_id)

        subject_units = subject.get("source_analysis_unit_ids")
        if (
            not isinstance(subject_units, list)
            or not subject_units
            or not set(subject_units).issubset(unit_ids)
        ):
            raise ReviewIntegrityError(
                "Synthesized relationship subject has invalid "
                "Source Analysis Unit membership."
            )

        for endpoint_field in (
            "source_synthesized_element_subject_id",
            "target_synthesized_element_subject_id",
        ):
            endpoint = subject.get(endpoint_field)
            if (
                endpoint is not None
                and endpoint not in element_subject_ids
            ):
                raise ReviewIntegrityError(
                    "Synthesized relationship endpoint references an "
                    "unavailable synthesized element subject."
                )

        requires_human_review = subject.get(
            "requires_human_review"
        )
        if not isinstance(requires_human_review, bool):
            raise ReviewIntegrityError(
                "Synthesized relationship requires_human_review "
                "must be boolean."
            )

        member_refs = subject.get("member_proposal_refs")
        if not isinstance(member_refs, list) or not member_refs:
            raise ReviewIntegrityError(
                "Synthesized relationship subject must contain "
                "proposal references."
            )
        for proposal_ref in member_refs:
            identity = _cross_unit_proposal_identity(
                proposal_ref,
                proposal_kind="relationship",
            )
            if identity in consumed_relationship_identities:
                raise ReviewIntegrityError(
                    "One P9 relationship proposal belongs to multiple "
                    "synthesized subjects."
                )
            proposal = raw_relationships.get(identity)
            if proposal is None:
                raise ReviewIntegrityError(
                    "Cross-unit relationship synthesis references a proposal "
                    "outside the selected P9 proposal set."
                )
            consumed_relationship_identities.add(identity)
            review_subject_key = _cross_unit_review_subject_key(
                proposal_kind="relationship",
                synthesized_subject_id=subject_id,
            )
            relationship_index[_p9_proposal_key(proposal)] = (
                review_subject_key
            )

        if review_subject_key in semantic_evidence:
            raise ReviewIntegrityError(
                "Element and relationship synthesized Review subjects "
                "must not share one stable key."
            )
        semantic_evidence[review_subject_key] = (
            _cross_unit_subject_evidence_reference(
                payload=payload,
                execution=execution,
                artifact_reference=artifact_reference,
                proposal_kind="relationship",
                subject_payload=subject,
            )
        )

    if consumed_element_identities != set(raw_elements):
        raise ReviewIntegrityError(
            "Cross-unit element synthesis does not partition the exact "
            "selected P9 element proposal set."
        )
    if consumed_relationship_identities != set(raw_relationships):
        raise ReviewIntegrityError(
            "Cross-unit relationship synthesis does not partition the exact "
            "selected P9 relationship proposal set."
        )

    return _SemanticProjectionIndex(
        element_subject_by_key=element_index,
        relationship_subject_by_key=relationship_index,
        semantic_evidence_by_subject=semantic_evidence,
        element_subject_count=len(element_subject_ids),
        relationship_subject_count=len(relationship_subject_ids),
        projection_authority="cross_unit_semantic_synthesis",
    )


def _projection_index(
    p9_evidence: P9ReviewEvidenceSet,
    structured_proposals: P9StructuredProposalSet,
    *,
    repository_root: Path,
) -> _SemanticProjectionIndex | None:
    cross_unit_index = _cross_unit_projection_index(
        p9_evidence,
        structured_proposals,
        repository_root=repository_root,
    )
    if cross_unit_index is not None:
        return cross_unit_index

    element_artifact = _load_semantic_artifact(
        p9_evidence,
        filename=SEMANTIC_ELEMENT_ARTIFACT_FILENAME,
        proposal_kind="element",
        repository_root=repository_root,
    )
    relationship_artifact = _load_semantic_artifact(
        p9_evidence,
        filename=SEMANTIC_RELATIONSHIP_ARTIFACT_FILENAME,
        proposal_kind="relationship",
        repository_root=repository_root,
    )

    if element_artifact is None:
        if relationship_artifact is not None:
            raise ReviewIntegrityError(
                "Relationship semantic consolidation exists without "
                "its authoritative element semantic consolidation."
            )
        return None

    if (
        structured_proposals.relationship_proposals
        and relationship_artifact is None
    ):
        raise ReviewReferenceError(
            "P9 contains relationship proposals but the published "
            "relationship semantic consolidation artifact is unavailable."
        )
    if (
        not structured_proposals.relationship_proposals
        and relationship_artifact is not None
        and relationship_artifact.proposals
    ):
        raise ReviewIntegrityError(
            "Relationship semantic consolidation contains proposals "
            "that are absent from the selected P9 proposal set."
        )

    element_index = _semantic_subject_index(
        element_artifact,
        proposal_kind="element",
    )
    relationship_index = (
        {}
        if relationship_artifact is None
        else _semantic_subject_index(
            relationship_artifact,
            proposal_kind="relationship",
        )
    )

    element_reference = _artifact_reference_for_filename(
        p9_evidence,
        SEMANTIC_ELEMENT_ARTIFACT_FILENAME,
    )
    if element_reference is None:
        raise ReviewReferenceError(
            "Published element semantic consolidation reference "
            "became unavailable during Review projection."
        )
    semantic_evidence = (
        _semantic_subject_evidence_catalog(
            artifact=element_artifact,
            artifact_reference=element_reference,
        )
    )

    if relationship_artifact is not None:
        relationship_reference = (
            _artifact_reference_for_filename(
                p9_evidence,
                SEMANTIC_RELATIONSHIP_ARTIFACT_FILENAME,
            )
        )
        if relationship_reference is None:
            raise ReviewReferenceError(
                "Published relationship semantic consolidation "
                "reference became unavailable during Review projection."
            )
        for subject_id, reference in (
            _semantic_subject_evidence_catalog(
                artifact=relationship_artifact,
                artifact_reference=relationship_reference,
            ).items()
        ):
            if subject_id in semantic_evidence:
                raise ReviewIntegrityError(
                    "Element and relationship semantic subjects "
                    "must not share one identity."
                )
            semantic_evidence[subject_id] = reference

    p9_element_keys = {
        _p9_proposal_key(proposal)
        for proposal in structured_proposals.element_proposals
    }
    p9_relationship_keys = {
        _p9_proposal_key(proposal)
        for proposal in structured_proposals.relationship_proposals
    }
    if p9_element_keys != set(element_index):
        raise ReviewIntegrityError(
            "Element semantic consolidation does not partition the "
            "exact selected P9 proposal set."
        )
    if p9_relationship_keys != set(relationship_index):
        raise ReviewIntegrityError(
            "Relationship semantic consolidation does not partition "
            "the exact selected P9 proposal set."
        )

    return _SemanticProjectionIndex(
        element_subject_by_key=element_index,
        relationship_subject_by_key=relationship_index,
        semantic_evidence_by_subject=semantic_evidence,
        element_subject_count=len(element_artifact.subjects),
        relationship_subject_count=(
            0
            if relationship_artifact is None
            else len(relationship_artifact.subjects)
        ),
        projection_authority="semantic_consolidation",
    )


def _project_proposals(
    structured_proposals: P9StructuredProposalSet,
    index: _SemanticProjectionIndex,
) -> P9StructuredProposalSet:
    projected_elements: list[P9ElementProposal] = []
    endpoint_subject_by_context: dict[
        tuple[str, str, str, str],
        str,
    ] = {}

    for proposal in structured_proposals.element_proposals:
        semantic_subject_id = (
            index.element_subject_by_key[
                _p9_proposal_key(proposal)
            ]
        )
        projected = replace(
            proposal,
            stable_subject_key=semantic_subject_id,
        )
        projected_elements.append(projected)

        reference = proposal.proposal_reference
        context_key = (
            reference.artifact_reference.content_fingerprint,
            reference.agent_id,
            reference.persona_id,
            proposal.stable_subject_key,
        )
        if context_key in endpoint_subject_by_context:
            raise ReviewIntegrityError(
                "One derivation execution contains ambiguous legacy "
                "element endpoint identity."
            )
        endpoint_subject_by_context[
            context_key
        ] = semantic_subject_id

    projected_relationships: list[
        P9RelationshipProposal
    ] = []
    for proposal in structured_proposals.relationship_proposals:
        reference = proposal.proposal_reference
        context = (
            reference.artifact_reference.content_fingerprint,
            reference.agent_id,
            reference.persona_id,
        )
        source_key = (
            *context,
            proposal.source_subject_key,
        )
        target_key = (
            *context,
            proposal.target_subject_key,
        )
        source_subject = endpoint_subject_by_context.get(
            source_key
        )
        target_subject = endpoint_subject_by_context.get(
            target_key
        )
        if source_subject is None or target_subject is None:
            raise ReviewReferenceError(
                "Relationship proposal endpoints cannot be mapped "
                "to exact semantic element subjects."
            )

        semantic_subject_id = (
            index.relationship_subject_by_key[
                _p9_proposal_key(proposal)
            ]
        )
        projected_relationships.append(
            replace(
                proposal,
                stable_subject_key=semantic_subject_id,
                source_subject_key=source_subject,
                target_subject_key=target_subject,
            )
        )

    return P9StructuredProposalSet(
        project_id=structured_proposals.project_id,
        source_id=structured_proposals.source_id,
        processing_run_id=(
            structured_proposals.processing_run_id
        ),
        attempt_id=structured_proposals.attempt_id,
        element_proposals=tuple(
            sorted(
                projected_elements,
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
                projected_relationships,
                key=lambda item: (
                    item.stable_subject_key,
                    item.proposal_reference
                    .artifact_reference.artifact_id,
                    item.link_id,
                ),
            )
        ),
        review_question_proposals=(
            structured_proposals.review_question_proposals
        ),
    )


def _evidence_reference_sort_key(reference) -> tuple[str, ...]:
    artifact = reference.artifact_reference
    return (
        artifact.artifact_type,
        artifact.artifact_id,
        artifact.content_fingerprint,
        artifact.repository_relative_path,
        reference.evidence_role,
        reference.evidence_locator,
        reference.evidence_content_fingerprint,
    )


def _source_locator(
    proposal: P9ElementProposal | P9RelationshipProposal,
) -> str:
    if isinstance(proposal, P9ElementProposal):
        return (
            "output_text:/candidate_model_elements/"
            f"{proposal.candidate_id}/source_evidence"
        )
    return (
        "output_text:/explicit_source_links/"
        f"{proposal.link_id}/source_evidence"
    )


def _project_evidence(
    raw_proposals: P9StructuredProposalSet,
    projected_proposals: P9StructuredProposalSet,
    structured_evidence: P9StructuredEvidenceSet,
    *,
    semantic_evidence_by_subject: dict[
        str,
        ReviewEvidenceReference,
    ],
) -> P9StructuredEvidenceSet:
    raw_candidates = (
        *raw_proposals.element_proposals,
        *raw_proposals.relationship_proposals,
    )
    projected_candidates = (
        *projected_proposals.element_proposals,
        *projected_proposals.relationship_proposals,
    )
    if len(raw_candidates) != len(projected_candidates):
        raise ReviewIntegrityError(
            "Semantic Review projection changed P9 proposal cardinality."
        )

    projected_by_key = {
        _p9_proposal_key(proposal): proposal
        for proposal in projected_candidates
    }
    raw_by_key = {
        _p9_proposal_key(proposal): proposal
        for proposal in raw_candidates
    }
    if set(projected_by_key) != set(raw_by_key):
        raise ReviewIntegrityError(
            "Semantic Review projection changed exact P9 proposal identity."
        )

    evidence_by_raw_subject = {
        item.stable_subject_key: item
        for item in structured_evidence.subject_evidence
    }
    if len(evidence_by_raw_subject) != len(
        structured_evidence.subject_evidence
    ):
        raise ReviewIntegrityError(
            "P9 evidence subjects must be unique before semantic projection."
        )

    raw_subject_to_semantic: dict[str, set[str]] = {}
    groups: dict[
        tuple[str, str],
        list[
            tuple[
                P9ElementProposal | P9RelationshipProposal,
                P9ElementProposal | P9RelationshipProposal,
            ]
        ],
    ] = {}

    for key, raw in raw_by_key.items():
        projected = projected_by_key[key]
        kind = (
            "element"
            if isinstance(raw, P9ElementProposal)
            else "relationship"
        )
        raw_subject_to_semantic.setdefault(
            raw.stable_subject_key,
            set(),
        ).add(projected.stable_subject_key)
        groups.setdefault(
            (kind, projected.stable_subject_key),
            [],
        ).append((raw, projected))

    projected_evidence: list[P9SubjectEvidence] = []
    consumed_raw_subjects: set[str] = set()

    for (kind, semantic_subject_id), pairs in sorted(
        groups.items()
    ):
        source_refs = {}

        for raw, _ in pairs:
            record = evidence_by_raw_subject.get(
                raw.stable_subject_key
            )
            if record is None:
                raise ReviewReferenceError(
                    "Exact P9 evidence is unavailable for one proposal "
                    "being projected to a semantic Review subject."
                )
            if record.review_item_kind != kind:
                raise ReviewIntegrityError(
                    "P9 evidence kind does not match semantic Review "
                    "proposal kind."
                )
            consumed_raw_subjects.add(
                raw.stable_subject_key
            )

            expected_locator = _source_locator(raw)
            matching = tuple(
                reference
                for reference in record.source_evidence_references
                if (
                    reference.artifact_reference
                    == raw.proposal_reference.artifact_reference
                    and reference.evidence_locator
                    == expected_locator
                )
            )
            if len(matching) != 1:
                raise ReviewReferenceError(
                    "Exact source evidence for a projected semantic "
                    "proposal cannot be identified uniquely."
                )
            reference = matching[0]
            source_refs[
                _evidence_reference_sort_key(reference)
            ] = reference

            # Legacy Consensus Evidence remains exact Processing
            # evidence, but semantic Review grouping authority comes from
            # the persisted C2/C3 semantic subject artifact. Never copy a
            # string-key Consensus group as authority for a new semantic
            # subject.

        semantic_consensus = (
            semantic_evidence_by_subject.get(
                semantic_subject_id
            )
        )
        if semantic_consensus is None:
            raise ReviewReferenceError(
                "Semantic Review subject has no exact C2/C3 "
                "grouping evidence reference."
            )

        projected_evidence.append(
            P9SubjectEvidence(
                stable_subject_key=semantic_subject_id,
                review_item_kind=kind,
                source_evidence_references=tuple(
                    source_refs[key]
                    for key in sorted(source_refs)
                ),
                consensus_evidence_references=(
                    semantic_consensus,
                ),
            )
        )

    # Preserve Open Questions and any other non-element/non-relationship
    # review subjects exactly. C4 changes semantic grouping only for the
    # C2/C3 proposal kinds.
    raw_candidate_subjects = {
        proposal.stable_subject_key
        for proposal in raw_candidates
    }
    for record in structured_evidence.subject_evidence:
        if record.stable_subject_key in raw_candidate_subjects:
            continue
        projected_evidence.append(record)

    return P9StructuredEvidenceSet(
        project_id=structured_evidence.project_id,
        source_id=structured_evidence.source_id,
        processing_run_id=(
            structured_evidence.processing_run_id
        ),
        attempt_id=structured_evidence.attempt_id,
        subject_evidence=tuple(
            sorted(
                projected_evidence,
                key=lambda item: (
                    item.stable_subject_key,
                    item.review_item_kind,
                ),
            )
        ),
    )


def _validate_input_identity(
    p9_evidence: P9ReviewEvidenceSet,
    proposals: P9StructuredProposalSet,
    evidence: P9StructuredEvidenceSet | None = None,
) -> None:
    expected = (
        p9_evidence.project_id,
        p9_evidence.source_id,
        p9_evidence.processing_run_id,
        p9_evidence.attempt_id,
    )
    proposal_identity = (
        proposals.project_id,
        proposals.source_id,
        proposals.processing_run_id,
        proposals.attempt_id,
    )
    if proposal_identity != expected:
        raise ReviewIntegrityError(
            "P9 proposal identity does not match selected P9 evidence."
        )
    if evidence is not None:
        evidence_identity = (
            evidence.project_id,
            evidence.source_id,
            evidence.processing_run_id,
            evidence.attempt_id,
        )
        if evidence_identity != expected:
            raise ReviewIntegrityError(
                "P9 structured evidence identity does not match "
                "selected P9 evidence."
            )


def load_semantic_review_consensus_evidence_facts(
    p9_evidence: object,
    structured_proposals: object,
    *,
    repository_root: Path | str,
) -> tuple[P9ConsensusEvidenceFact, ...]:
    """Reconstruct semantic-subject facts from D4 or legacy C2/C3 authority."""

    if not isinstance(p9_evidence, P9ReviewEvidenceSet):
        raise ReviewValidationError(
            "p9_evidence must be a P9ReviewEvidenceSet."
        )
    if not isinstance(
        structured_proposals,
        P9StructuredProposalSet,
    ):
        raise ReviewValidationError(
            "structured_proposals must be a P9StructuredProposalSet."
        )

    _validate_input_identity(
        p9_evidence,
        structured_proposals,
    )
    root = _validated_root(repository_root)
    index = _projection_index(
        p9_evidence,
        structured_proposals,
        repository_root=root,
    )
    if index is None:
        return ()

    expected_personas = tuple(
        sorted(
            {
                proposal.proposal_reference.persona_id
                for proposal in (
                    *structured_proposals.element_proposals,
                    *structured_proposals.relationship_proposals,
                )
            }
        )
    )
    if not expected_personas:
        raise ReviewIntegrityError(
            "Semantic Review consensus cannot determine any expected Persona."
        )
    expected_set = set(expected_personas)

    if (
        index.projection_authority
        == "cross_unit_semantic_synthesis"
    ):
        recognized_by_subject: dict[
            tuple[str, str],
            set[str],
        ] = {}
        for proposal in (
            *structured_proposals.element_proposals,
            *structured_proposals.relationship_proposals,
        ):
            if isinstance(proposal, P9ElementProposal):
                kind = "element"
                subject_id = index.element_subject_by_key[
                    _p9_proposal_key(proposal)
                ]
            else:
                kind = "relationship"
                subject_id = index.relationship_subject_by_key[
                    _p9_proposal_key(proposal)
                ]
            recognized_by_subject.setdefault(
                (kind, subject_id),
                set(),
            ).add(
                proposal.proposal_reference.persona_id
            )

        facts: list[P9ConsensusEvidenceFact] = []
        seen_keys: set[tuple[str, str, str]] = set()
        for (_, subject_id), recognized in sorted(
            recognized_by_subject.items()
        ):
            if not recognized.issubset(expected_set):
                raise ReviewIntegrityError(
                    "Cross-unit synthesized subject contains a Persona "
                    "outside the selected P9 proposal set."
                )
            if recognized == expected_set:
                agreement_level = "full_agreement"
            elif len(recognized) * 2 > len(expected_set):
                agreement_level = "majority_agreement"
            else:
                agreement_level = "minority_interpretation"

            evidence_reference = (
                index.semantic_evidence_by_subject.get(
                    subject_id
                )
            )
            if evidence_reference is None:
                raise ReviewReferenceError(
                    "Cross-unit synthesized subject has no exact "
                    "Review evidence reference."
                )
            artifact_reference = (
                evidence_reference.artifact_reference
            )
            key = (
                artifact_reference.artifact_id,
                evidence_reference.evidence_locator,
                evidence_reference.evidence_content_fingerprint,
            )
            if key in seen_keys:
                raise ReviewIntegrityError(
                    "Cross-unit Review consensus facts must be unique."
                )
            seen_keys.add(key)
            facts.append(
                P9ConsensusEvidenceFact(
                    artifact_id=artifact_reference.artifact_id,
                    evidence_locator=(
                        evidence_reference.evidence_locator
                    ),
                    evidence_content_fingerprint=(
                        evidence_reference
                        .evidence_content_fingerprint
                    ),
                    agreement_level=agreement_level,
                    review_required=True,
                )
            )

        return tuple(
            sorted(
                facts,
                key=lambda item: (
                    item.artifact_id,
                    item.evidence_locator,
                    item.evidence_content_fingerprint,
                ),
            )
        )

    facts: list[P9ConsensusEvidenceFact] = []
    seen_keys: set[tuple[str, str, str]] = set()

    for filename, kind in (
        (
            SEMANTIC_ELEMENT_ARTIFACT_FILENAME,
            "element",
        ),
        (
            SEMANTIC_RELATIONSHIP_ARTIFACT_FILENAME,
            "relationship",
        ),
    ):
        artifact_reference = _artifact_reference_for_filename(
            p9_evidence,
            filename,
        )
        if artifact_reference is None:
            if kind == "relationship":
                continue
            raise ReviewReferenceError(
                "Element semantic consolidation reference is unavailable."
            )

        artifact = _load_semantic_artifact(
            p9_evidence,
            filename=filename,
            proposal_kind=kind,
            repository_root=root,
        )
        if artifact is None:
            raise ReviewReferenceError(
                "Published semantic consolidation artifact is unavailable."
            )

        binding_by_ref = {
            binding.proposal_ref: binding
            for binding in artifact.proposals
        }

        for subject in artifact.subjects:
            recognized = {
                binding_by_ref[proposal_ref].persona_id
                for proposal_ref in subject.member_proposal_refs
            }
            if not recognized.issubset(expected_set):
                raise ReviewIntegrityError(
                    "Semantic subject contains a Persona outside the exact "
                    "selected P9 proposal set."
                )

            if recognized == expected_set:
                agreement_level = "full_agreement"
            elif len(recognized) * 2 > len(expected_set):
                agreement_level = "majority_agreement"
            else:
                agreement_level = "minority_interpretation"

            evidence_reference = (
                index.semantic_evidence_by_subject.get(
                    subject.semantic_subject_id
                )
            )
            if evidence_reference is None:
                raise ReviewReferenceError(
                    "Semantic subject has no exact Review evidence reference."
                )

            key = (
                artifact_reference.artifact_id,
                evidence_reference.evidence_locator,
                evidence_reference.evidence_content_fingerprint,
            )
            if key in seen_keys:
                raise ReviewIntegrityError(
                    "Semantic Review consensus facts must be unique."
                )
            seen_keys.add(key)

            facts.append(
                P9ConsensusEvidenceFact(
                    artifact_id=artifact_reference.artifact_id,
                    evidence_locator=(
                        evidence_reference.evidence_locator
                    ),
                    evidence_content_fingerprint=(
                        evidence_reference
                        .evidence_content_fingerprint
                    ),
                    agreement_level=agreement_level,
                    review_required=True,
                )
            )

    return tuple(
        sorted(
            facts,
            key=lambda item: (
                item.artifact_id,
                item.evidence_locator,
                item.evidence_content_fingerprint,
            ),
        )
    )


def project_p9_proposals_to_semantic_subjects(
    p9_evidence: object,
    structured_proposals: object,
    *,
    repository_root: Path | str,
) -> P9StructuredProposalSet:
    """Project exact P9 proposals to D4 or legacy C2/C3 subject identities."""

    if not isinstance(p9_evidence, P9ReviewEvidenceSet):
        raise ReviewValidationError(
            "p9_evidence must be a P9ReviewEvidenceSet."
        )
    if not isinstance(
        structured_proposals,
        P9StructuredProposalSet,
    ):
        raise ReviewValidationError(
            "structured_proposals must be a P9StructuredProposalSet."
        )

    _validate_input_identity(
        p9_evidence,
        structured_proposals,
    )
    root = _validated_root(repository_root)
    index = _projection_index(
        p9_evidence,
        structured_proposals,
        repository_root=root,
    )
    if index is None:
        return structured_proposals
    return _project_proposals(
        structured_proposals,
        index,
    )


def project_p9_review_inputs_to_semantic_subjects(
    p9_evidence: object,
    structured_proposals: object,
    structured_evidence: object,
    *,
    repository_root: Path | str,
) -> SemanticReviewProjectionResult:
    """Project exact P9 proposals/evidence for initial Human Review."""

    if not isinstance(p9_evidence, P9ReviewEvidenceSet):
        raise ReviewValidationError(
            "p9_evidence must be a P9ReviewEvidenceSet."
        )
    if not isinstance(
        structured_proposals,
        P9StructuredProposalSet,
    ):
        raise ReviewValidationError(
            "structured_proposals must be a P9StructuredProposalSet."
        )
    if not isinstance(
        structured_evidence,
        P9StructuredEvidenceSet,
    ):
        raise ReviewValidationError(
            "structured_evidence must be a P9StructuredEvidenceSet."
        )

    _validate_input_identity(
        p9_evidence,
        structured_proposals,
        structured_evidence,
    )
    root = _validated_root(repository_root)
    index = _projection_index(
        p9_evidence,
        structured_proposals,
        repository_root=root,
    )
    if index is None:
        return SemanticReviewProjectionResult(
            proposals=structured_proposals,
            evidence=structured_evidence,
            used_semantic_projection=False,
            element_semantic_subject_count=len(
                {
                    item.stable_subject_key
                    for item in structured_proposals.element_proposals
                }
            ),
            relationship_semantic_subject_count=len(
                {
                    item.stable_subject_key
                    for item
                    in structured_proposals.relationship_proposals
                }
            ),
        )

    projected_proposals = _project_proposals(
        structured_proposals,
        index,
    )
    projected_evidence = _project_evidence(
        structured_proposals,
        projected_proposals,
        structured_evidence,
        semantic_evidence_by_subject=(
            index.semantic_evidence_by_subject
        ),
    )

    return SemanticReviewProjectionResult(
        proposals=projected_proposals,
        evidence=projected_evidence,
        used_semantic_projection=True,
        element_semantic_subject_count=(
            index.element_subject_count
        ),
        relationship_semantic_subject_count=(
            index.relationship_subject_count
        ),
    )
