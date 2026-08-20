"""Strict immutable artifact contract for semantic proposal consolidation."""

from __future__ import annotations

from dataclasses import fields
import hashlib
import json
import re
from typing import Any, Iterable

from .errors import (
    SemanticConsolidationIntegrityError,
    SemanticConsolidationValidationError,
)
from .types import (
    PROPOSAL_KINDS,
    SEMANTIC_COMPARISON_METHODS,
    SEMANTIC_COMPARISON_OUTCOMES,
    SemanticComparison,
    SemanticConsolidationArtifact,
    SemanticProposalBinding,
    SemanticSubject,
    SemanticUpstreamArtifactBinding,
)


SEMANTIC_CONSOLIDATION_SCHEMA_VERSION = "1.0.0"
SEMANTIC_CONSOLIDATION_ARTIFACT_KIND = "semantic_consolidation"

_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_PROJECT_ID_PATTERN = re.compile(r"^[0-9]{6}$")
_UTC_TIMESTAMP_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T"
    r"\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$"
)


def _text(value: object, *, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SemanticConsolidationValidationError(
            f"{label} must be a non-empty string."
        )
    if value != value.strip():
        raise SemanticConsolidationValidationError(
            f"{label} must not contain surrounding whitespace."
        )
    return value


def _sha256(value: object, *, label: str) -> str:
    value = _text(value, label=label)
    if _SHA256_PATTERN.fullmatch(value) is None:
        raise SemanticConsolidationValidationError(
            f"{label} must be a lowercase SHA-256 value."
        )
    return value


def _project_id(value: object) -> str:
    value = _text(value, label="project_id")
    if _PROJECT_ID_PATTERN.fullmatch(value) is None:
        raise SemanticConsolidationValidationError(
            "project_id must be a six-digit Project ID."
        )
    return value


def _timestamp(value: object) -> str:
    value = _text(value, label="created_at_utc")
    if _UTC_TIMESTAMP_PATTERN.fullmatch(value) is None:
        raise SemanticConsolidationValidationError(
            "created_at_utc must be an ISO-8601 UTC timestamp ending in Z."
        )
    return value


def _exact_object(
    value: object,
    *,
    expected_fields: frozenset[str],
    label: str,
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise SemanticConsolidationValidationError(
            f"{label} must be a JSON object."
        )
    actual = frozenset(value)
    if actual != expected_fields:
        raise SemanticConsolidationValidationError(
            f"{label} has invalid fields; "
            f"missing={sorted(expected_fields - actual)}, "
            f"unknown={sorted(actual - expected_fields)}."
        )
    return value


def _exact_fields(dataclass_type: type[object]) -> frozenset[str]:
    return frozenset(field.name for field in fields(dataclass_type))


def _string_tuple(
    value: object,
    *,
    label: str,
    require_nonempty: bool,
) -> tuple[str, ...]:
    if not isinstance(value, (tuple, list)):
        raise SemanticConsolidationValidationError(
            f"{label} must be a tuple or JSON array."
        )
    checked = tuple(_text(item, label=label) for item in value)
    if require_nonempty and not checked:
        raise SemanticConsolidationIntegrityError(
            f"{label} must not be empty."
        )
    if checked != tuple(sorted(checked)):
        raise SemanticConsolidationValidationError(
            f"{label} must use deterministic sorted order."
        )
    if len(checked) != len(set(checked)):
        raise SemanticConsolidationIntegrityError(
            f"{label} must contain unique values."
        )
    return checked


def _canonical_fingerprint(payload: object) -> str:
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _upstream_payload(
    binding: SemanticUpstreamArtifactBinding,
) -> dict[str, object]:
    return {
        "artifact_ref": binding.artifact_ref,
        "artifact_fingerprint": binding.artifact_fingerprint,
    }


def _proposal_payload(binding: SemanticProposalBinding) -> dict[str, object]:
    return {
        "proposal_ref": binding.proposal_ref,
        "proposal_kind": binding.proposal_kind,
        "agent_id": binding.agent_id,
        "persona_id": binding.persona_id,
        "run_index": binding.run_index,
        "upstream_artifact_ref": binding.upstream_artifact_ref,
        "evidence_refs": list(binding.evidence_refs),
    }


def _subject_payload(subject: SemanticSubject) -> dict[str, object]:
    return {
        "semantic_subject_id": subject.semantic_subject_id,
        "proposal_kind": subject.proposal_kind,
        "member_proposal_refs": list(subject.member_proposal_refs),
    }


def _comparison_payload(
    comparison: SemanticComparison,
) -> dict[str, object]:
    return {
        "left_proposal_ref": comparison.left_proposal_ref,
        "right_proposal_ref": comparison.right_proposal_ref,
        "outcome": comparison.outcome,
        "method": comparison.method,
        "trace_ref": comparison.trace_ref,
        "rationale": comparison.rationale,
    }


def _artifact_payload_without_fingerprint(
    artifact: SemanticConsolidationArtifact,
) -> dict[str, object]:
    return {
        "schema_version": artifact.schema_version,
        "artifact_kind": artifact.artifact_kind,
        "project_id": artifact.project_id,
        "processing_run_id": artifact.processing_run_id,
        "created_at_utc": artifact.created_at_utc,
        "upstream_artifacts": [
            _upstream_payload(item) for item in artifact.upstream_artifacts
        ],
        "input_set_fingerprint": artifact.input_set_fingerprint,
        "proposals": [
            _proposal_payload(item) for item in artifact.proposals
        ],
        "subjects": [_subject_payload(item) for item in artifact.subjects],
        "comparisons": [
            _comparison_payload(item) for item in artifact.comparisons
        ],
    }


def semantic_consolidation_artifact_to_dict(
    artifact: SemanticConsolidationArtifact,
) -> dict[str, object]:
    """Serialize an already-valid artifact using its canonical field model."""

    validate_semantic_consolidation_artifact(artifact)
    payload = _artifact_payload_without_fingerprint(artifact)
    return {
        **payload,
        "artifact_fingerprint": artifact.artifact_fingerprint,
    }


def calculate_input_set_fingerprint(
    upstream_artifacts: Iterable[SemanticUpstreamArtifactBinding],
) -> str:
    """Fingerprint the exact sorted upstream artifact set."""

    normalized = _normalize_upstream_artifacts(tuple(upstream_artifacts))
    return _canonical_fingerprint(
        [_upstream_payload(item) for item in normalized]
    )


def calculate_artifact_fingerprint(
    artifact: SemanticConsolidationArtifact,
) -> str:
    """Calculate the artifact fingerprint excluding its own fingerprint."""

    return _canonical_fingerprint(
        _artifact_payload_without_fingerprint(artifact)
    )


def _validate_kind(value: object, *, label: str) -> str:
    value = _text(value, label=label)
    if value not in PROPOSAL_KINDS:
        raise SemanticConsolidationValidationError(
            f"{label} must be one of {sorted(PROPOSAL_KINDS)}."
        )
    return value


def _validate_outcome(value: object) -> str:
    value = _text(value, label="comparison outcome")
    if value not in SEMANTIC_COMPARISON_OUTCOMES:
        raise SemanticConsolidationValidationError(
            "comparison outcome must be one of "
            f"{sorted(SEMANTIC_COMPARISON_OUTCOMES)}."
        )
    return value


def _validate_method(value: object) -> str:
    value = _text(value, label="comparison method")
    if value not in SEMANTIC_COMPARISON_METHODS:
        raise SemanticConsolidationValidationError(
            "comparison method must be one of "
            f"{sorted(SEMANTIC_COMPARISON_METHODS)}."
        )
    return value


def _normalize_upstream_artifacts(
    values: tuple[SemanticUpstreamArtifactBinding, ...],
) -> tuple[SemanticUpstreamArtifactBinding, ...]:
    if not isinstance(values, tuple):
        raise SemanticConsolidationValidationError(
            "upstream_artifacts must be a tuple."
        )
    if not values:
        raise SemanticConsolidationIntegrityError(
            "Semantic consolidation requires at least one upstream artifact."
        )

    normalized: list[SemanticUpstreamArtifactBinding] = []
    for value in values:
        if not isinstance(value, SemanticUpstreamArtifactBinding):
            raise SemanticConsolidationValidationError(
                "upstream_artifacts contains an invalid item."
            )
        normalized.append(
            SemanticUpstreamArtifactBinding(
                artifact_ref=_text(
                    value.artifact_ref,
                    label="upstream artifact_ref",
                ),
                artifact_fingerprint=_sha256(
                    value.artifact_fingerprint,
                    label="upstream artifact_fingerprint",
                ),
            )
        )

    result = tuple(sorted(normalized, key=lambda item: item.artifact_ref))
    refs = tuple(item.artifact_ref for item in result)
    if len(refs) != len(set(refs)):
        raise SemanticConsolidationIntegrityError(
            "upstream_artifacts must not repeat an artifact_ref."
        )
    return result


def _normalize_proposals(
    values: tuple[SemanticProposalBinding, ...],
) -> tuple[SemanticProposalBinding, ...]:
    if not isinstance(values, tuple):
        raise SemanticConsolidationValidationError(
            "proposals must be a tuple."
        )

    normalized: list[SemanticProposalBinding] = []
    for value in values:
        if not isinstance(value, SemanticProposalBinding):
            raise SemanticConsolidationValidationError(
                "proposals contains an invalid item."
            )
        if isinstance(value.run_index, bool) or not isinstance(
            value.run_index, int
        ):
            raise SemanticConsolidationValidationError(
                "proposal run_index must be an integer."
            )
        if value.run_index < 1:
            raise SemanticConsolidationValidationError(
                "proposal run_index must be at least 1."
            )
        normalized.append(
            SemanticProposalBinding(
                proposal_ref=_text(
                    value.proposal_ref,
                    label="proposal_ref",
                ),
                proposal_kind=_validate_kind(
                    value.proposal_kind,
                    label="proposal_kind",
                ),
                agent_id=_text(value.agent_id, label="agent_id"),
                persona_id=_text(value.persona_id, label="persona_id"),
                run_index=value.run_index,
                upstream_artifact_ref=_text(
                    value.upstream_artifact_ref,
                    label="proposal upstream_artifact_ref",
                ),
                evidence_refs=_string_tuple(
                    value.evidence_refs,
                    label="proposal evidence_refs",
                    require_nonempty=True,
                ),
            )
        )

    result = tuple(sorted(normalized, key=lambda item: item.proposal_ref))
    refs = tuple(item.proposal_ref for item in result)
    if len(refs) != len(set(refs)):
        raise SemanticConsolidationIntegrityError(
            "proposals must not repeat a proposal_ref."
        )
    return result


def _normalize_subjects(
    values: tuple[SemanticSubject, ...],
) -> tuple[SemanticSubject, ...]:
    if not isinstance(values, tuple):
        raise SemanticConsolidationValidationError(
            "subjects must be a tuple."
        )

    normalized: list[SemanticSubject] = []
    for value in values:
        if not isinstance(value, SemanticSubject):
            raise SemanticConsolidationValidationError(
                "subjects contains an invalid item."
            )
        normalized.append(
            SemanticSubject(
                semantic_subject_id=_text(
                    value.semantic_subject_id,
                    label="semantic_subject_id",
                ),
                proposal_kind=_validate_kind(
                    value.proposal_kind,
                    label="subject proposal_kind",
                ),
                member_proposal_refs=_string_tuple(
                    value.member_proposal_refs,
                    label="member_proposal_refs",
                    require_nonempty=True,
                ),
            )
        )

    result = tuple(
        sorted(normalized, key=lambda item: item.semantic_subject_id)
    )
    ids = tuple(item.semantic_subject_id for item in result)
    if len(ids) != len(set(ids)):
        raise SemanticConsolidationIntegrityError(
            "subjects must not repeat a semantic_subject_id."
        )
    return result


def _comparison_pair(
    comparison: SemanticComparison,
) -> tuple[str, str]:
    return tuple(
        sorted(
            (
                comparison.left_proposal_ref,
                comparison.right_proposal_ref,
            )
        )
    )


def _normalize_comparisons(
    values: tuple[SemanticComparison, ...],
) -> tuple[SemanticComparison, ...]:
    if not isinstance(values, tuple):
        raise SemanticConsolidationValidationError(
            "comparisons must be a tuple."
        )

    normalized: list[SemanticComparison] = []
    for value in values:
        if not isinstance(value, SemanticComparison):
            raise SemanticConsolidationValidationError(
                "comparisons contains an invalid item."
            )
        left = _text(
            value.left_proposal_ref,
            label="left_proposal_ref",
        )
        right = _text(
            value.right_proposal_ref,
            label="right_proposal_ref",
        )
        if left == right:
            raise SemanticConsolidationIntegrityError(
                "A semantic comparison must not compare a proposal to itself."
            )
        left, right = sorted((left, right))
        normalized.append(
            SemanticComparison(
                left_proposal_ref=left,
                right_proposal_ref=right,
                outcome=_validate_outcome(value.outcome),
                method=_validate_method(value.method),
                trace_ref=_text(
                    value.trace_ref,
                    label="comparison trace_ref",
                ),
                rationale=_text(
                    value.rationale,
                    label="comparison rationale",
                ),
            )
        )

    result = tuple(
        sorted(
            normalized,
            key=lambda item: (
                item.left_proposal_ref,
                item.right_proposal_ref,
            ),
        )
    )
    pairs = tuple(_comparison_pair(item) for item in result)
    if len(pairs) != len(set(pairs)):
        raise SemanticConsolidationIntegrityError(
            "comparisons must not repeat an unordered proposal pair."
        )
    return result


def _assert_deterministic_order(
    *,
    original: tuple[object, ...],
    normalized: tuple[object, ...],
    label: str,
) -> None:
    if original != normalized:
        raise SemanticConsolidationValidationError(
            f"{label} must use deterministic canonical order."
        )


def _validate_graph_integrity(
    proposals: tuple[SemanticProposalBinding, ...],
    subjects: tuple[SemanticSubject, ...],
    comparisons: tuple[SemanticComparison, ...],
) -> None:
    proposal_by_ref = {
        proposal.proposal_ref: proposal for proposal in proposals
    }

    memberships: dict[str, str] = {}
    for subject in subjects:
        for proposal_ref in subject.member_proposal_refs:
            proposal = proposal_by_ref.get(proposal_ref)
            if proposal is None:
                raise SemanticConsolidationIntegrityError(
                    "Semantic subject references an unknown proposal: "
                    f"{proposal_ref!r}."
                )
            if proposal_ref in memberships:
                raise SemanticConsolidationIntegrityError(
                    "A proposal must belong to exactly one semantic subject: "
                    f"{proposal_ref!r}."
                )
            if proposal.proposal_kind != subject.proposal_kind:
                raise SemanticConsolidationIntegrityError(
                    "Semantic subject kind does not match member proposal kind: "
                    f"{proposal_ref!r}."
                )
            memberships[proposal_ref] = subject.semantic_subject_id

    proposal_refs = set(proposal_by_ref)
    member_refs = set(memberships)
    if proposal_refs != member_refs:
        missing = sorted(proposal_refs - member_refs)
        extra = sorted(member_refs - proposal_refs)
        raise SemanticConsolidationIntegrityError(
            "Semantic subjects must cover every proposal exactly once; "
            f"missing={missing}, extra={extra}."
        )

    equivalent_edges: set[tuple[str, str]] = set()
    for comparison in comparisons:
        left = proposal_by_ref.get(comparison.left_proposal_ref)
        right = proposal_by_ref.get(comparison.right_proposal_ref)
        if left is None or right is None:
            missing_ref = (
                comparison.left_proposal_ref
                if left is None
                else comparison.right_proposal_ref
            )
            raise SemanticConsolidationIntegrityError(
                "Semantic comparison references an unknown proposal: "
                f"{missing_ref!r}."
            )
        if left.proposal_kind != right.proposal_kind:
            raise SemanticConsolidationIntegrityError(
                "Semantic comparison proposals must have the same kind."
            )

        same_subject = (
            memberships[left.proposal_ref]
            == memberships[right.proposal_ref]
        )
        if comparison.outcome == "equivalent":
            equivalent_edges.add(_comparison_pair(comparison))
            if not same_subject:
                raise SemanticConsolidationIntegrityError(
                    "Equivalent proposals must belong to the same semantic "
                    "subject."
                )
        elif same_subject:
            raise SemanticConsolidationIntegrityError(
                f"{comparison.outcome!r} proposals must not belong to the "
                "same semantic subject."
            )

    adjacency: dict[str, set[str]] = {
        proposal_ref: set() for proposal_ref in proposal_by_ref
    }
    for left, right in equivalent_edges:
        adjacency[left].add(right)
        adjacency[right].add(left)

    for subject in subjects:
        members = set(subject.member_proposal_refs)
        if len(members) < 2:
            continue
        start = next(iter(members))
        visited: set[str] = set()
        pending = [start]
        while pending:
            current = pending.pop()
            if current in visited:
                continue
            visited.add(current)
            pending.extend(
                neighbor
                for neighbor in adjacency[current]
                if neighbor in members and neighbor not in visited
            )
        if visited != members:
            raise SemanticConsolidationIntegrityError(
                "Every multi-proposal semantic subject must be connected by "
                "explicit equivalent comparison evidence."
            )


def validate_semantic_consolidation_artifact(
    artifact: SemanticConsolidationArtifact,
) -> None:
    """Validate structure, provenance binding, merge authority, and fingerprints."""

    if not isinstance(artifact, SemanticConsolidationArtifact):
        raise SemanticConsolidationValidationError(
            "artifact has invalid type."
        )
    if artifact.schema_version != SEMANTIC_CONSOLIDATION_SCHEMA_VERSION:
        raise SemanticConsolidationValidationError(
            "Unsupported semantic consolidation schema_version."
        )
    if artifact.artifact_kind != SEMANTIC_CONSOLIDATION_ARTIFACT_KIND:
        raise SemanticConsolidationValidationError(
            "Invalid semantic consolidation artifact_kind."
        )

    _project_id(artifact.project_id)
    _text(artifact.processing_run_id, label="processing_run_id")
    _timestamp(artifact.created_at_utc)
    _sha256(
        artifact.input_set_fingerprint,
        label="input_set_fingerprint",
    )
    _sha256(
        artifact.artifact_fingerprint,
        label="artifact_fingerprint",
    )

    upstream_artifacts = _normalize_upstream_artifacts(
        artifact.upstream_artifacts
    )
    proposals = _normalize_proposals(artifact.proposals)
    subjects = _normalize_subjects(artifact.subjects)
    comparisons = _normalize_comparisons(artifact.comparisons)

    _assert_deterministic_order(
        original=artifact.upstream_artifacts,
        normalized=upstream_artifacts,
        label="upstream_artifacts",
    )
    _assert_deterministic_order(
        original=artifact.proposals,
        normalized=proposals,
        label="proposals",
    )
    _assert_deterministic_order(
        original=artifact.subjects,
        normalized=subjects,
        label="subjects",
    )
    _assert_deterministic_order(
        original=artifact.comparisons,
        normalized=comparisons,
        label="comparisons",
    )

    upstream_refs = {item.artifact_ref for item in upstream_artifacts}
    for proposal in proposals:
        if proposal.upstream_artifact_ref not in upstream_refs:
            raise SemanticConsolidationIntegrityError(
                "Proposal references an unavailable upstream artifact: "
                f"{proposal.upstream_artifact_ref!r}."
            )

    expected_input_fingerprint = calculate_input_set_fingerprint(
        upstream_artifacts
    )
    if artifact.input_set_fingerprint != expected_input_fingerprint:
        raise SemanticConsolidationIntegrityError(
            "input_set_fingerprint does not match the exact upstream set."
        )

    _validate_graph_integrity(proposals, subjects, comparisons)

    expected_artifact_fingerprint = calculate_artifact_fingerprint(artifact)
    if artifact.artifact_fingerprint != expected_artifact_fingerprint:
        raise SemanticConsolidationIntegrityError(
            "artifact_fingerprint does not match artifact content."
        )


def build_semantic_consolidation_artifact(
    *,
    project_id: str,
    processing_run_id: str,
    created_at_utc: str,
    upstream_artifacts: tuple[SemanticUpstreamArtifactBinding, ...],
    proposals: tuple[SemanticProposalBinding, ...],
    subjects: tuple[SemanticSubject, ...],
    comparisons: tuple[SemanticComparison, ...],
) -> SemanticConsolidationArtifact:
    """Build one canonical artifact and calculate its exact fingerprints."""

    normalized_upstream = _normalize_upstream_artifacts(
        tuple(upstream_artifacts)
    )
    normalized_proposals = _normalize_proposals(tuple(proposals))
    normalized_subjects = _normalize_subjects(tuple(subjects))
    normalized_comparisons = _normalize_comparisons(tuple(comparisons))

    base = SemanticConsolidationArtifact(
        schema_version=SEMANTIC_CONSOLIDATION_SCHEMA_VERSION,
        artifact_kind=SEMANTIC_CONSOLIDATION_ARTIFACT_KIND,
        project_id=_project_id(project_id),
        processing_run_id=_text(
            processing_run_id,
            label="processing_run_id",
        ),
        created_at_utc=_timestamp(created_at_utc),
        upstream_artifacts=normalized_upstream,
        input_set_fingerprint=calculate_input_set_fingerprint(
            normalized_upstream
        ),
        proposals=normalized_proposals,
        subjects=normalized_subjects,
        comparisons=normalized_comparisons,
        artifact_fingerprint="0" * 64,
    )

    _validate_graph_integrity(
        base.proposals,
        base.subjects,
        base.comparisons,
    )

    artifact = SemanticConsolidationArtifact(
        schema_version=base.schema_version,
        artifact_kind=base.artifact_kind,
        project_id=base.project_id,
        processing_run_id=base.processing_run_id,
        created_at_utc=base.created_at_utc,
        upstream_artifacts=base.upstream_artifacts,
        input_set_fingerprint=base.input_set_fingerprint,
        proposals=base.proposals,
        subjects=base.subjects,
        comparisons=base.comparisons,
        artifact_fingerprint=calculate_artifact_fingerprint(base),
    )
    validate_semantic_consolidation_artifact(artifact)
    return artifact


def _parse_upstream(value: object) -> SemanticUpstreamArtifactBinding:
    data = _exact_object(
        value,
        expected_fields=_exact_fields(SemanticUpstreamArtifactBinding),
        label="Semantic Upstream Artifact Binding",
    )
    return SemanticUpstreamArtifactBinding(
        artifact_ref=_text(
            data["artifact_ref"],
            label="upstream artifact_ref",
        ),
        artifact_fingerprint=_sha256(
            data["artifact_fingerprint"],
            label="upstream artifact_fingerprint",
        ),
    )


def _parse_proposal(value: object) -> SemanticProposalBinding:
    data = _exact_object(
        value,
        expected_fields=_exact_fields(SemanticProposalBinding),
        label="Semantic Proposal Binding",
    )
    run_index = data["run_index"]
    if isinstance(run_index, bool) or not isinstance(run_index, int):
        raise SemanticConsolidationValidationError(
            "proposal run_index must be an integer."
        )
    return SemanticProposalBinding(
        proposal_ref=_text(data["proposal_ref"], label="proposal_ref"),
        proposal_kind=_validate_kind(
            data["proposal_kind"],
            label="proposal_kind",
        ),
        agent_id=_text(data["agent_id"], label="agent_id"),
        persona_id=_text(data["persona_id"], label="persona_id"),
        run_index=run_index,
        upstream_artifact_ref=_text(
            data["upstream_artifact_ref"],
            label="proposal upstream_artifact_ref",
        ),
        evidence_refs=_string_tuple(
            data["evidence_refs"],
            label="proposal evidence_refs",
            require_nonempty=True,
        ),
    )


def _parse_subject(value: object) -> SemanticSubject:
    data = _exact_object(
        value,
        expected_fields=_exact_fields(SemanticSubject),
        label="Semantic Subject",
    )
    return SemanticSubject(
        semantic_subject_id=_text(
            data["semantic_subject_id"],
            label="semantic_subject_id",
        ),
        proposal_kind=_validate_kind(
            data["proposal_kind"],
            label="subject proposal_kind",
        ),
        member_proposal_refs=_string_tuple(
            data["member_proposal_refs"],
            label="member_proposal_refs",
            require_nonempty=True,
        ),
    )


def _parse_comparison(value: object) -> SemanticComparison:
    data = _exact_object(
        value,
        expected_fields=_exact_fields(SemanticComparison),
        label="Semantic Comparison",
    )
    return SemanticComparison(
        left_proposal_ref=_text(
            data["left_proposal_ref"],
            label="left_proposal_ref",
        ),
        right_proposal_ref=_text(
            data["right_proposal_ref"],
            label="right_proposal_ref",
        ),
        outcome=_validate_outcome(data["outcome"]),
        method=_validate_method(data["method"]),
        trace_ref=_text(
            data["trace_ref"],
            label="comparison trace_ref",
        ),
        rationale=_text(
            data["rationale"],
            label="comparison rationale",
        ),
    )


def semantic_consolidation_artifact_from_dict(
    value: object,
) -> SemanticConsolidationArtifact:
    """Parse exact JSON-shaped data and fail closed on any mismatch."""

    data = _exact_object(
        value,
        expected_fields=_exact_fields(SemanticConsolidationArtifact),
        label="Semantic Consolidation Artifact",
    )

    def _array(name: str) -> list[object]:
        raw = data[name]
        if not isinstance(raw, list):
            raise SemanticConsolidationValidationError(
                f"{name} must be a JSON array."
            )
        return raw

    artifact = SemanticConsolidationArtifact(
        schema_version=_text(
            data["schema_version"],
            label="schema_version",
        ),
        artifact_kind=_text(
            data["artifact_kind"],
            label="artifact_kind",
        ),
        project_id=_project_id(data["project_id"]),
        processing_run_id=_text(
            data["processing_run_id"],
            label="processing_run_id",
        ),
        created_at_utc=_timestamp(data["created_at_utc"]),
        upstream_artifacts=tuple(
            _parse_upstream(item)
            for item in _array("upstream_artifacts")
        ),
        input_set_fingerprint=_sha256(
            data["input_set_fingerprint"],
            label="input_set_fingerprint",
        ),
        proposals=tuple(
            _parse_proposal(item) for item in _array("proposals")
        ),
        subjects=tuple(
            _parse_subject(item) for item in _array("subjects")
        ),
        comparisons=tuple(
            _parse_comparison(item) for item in _array("comparisons")
        ),
        artifact_fingerprint=_sha256(
            data["artifact_fingerprint"],
            label="artifact_fingerprint",
        ),
    )
    validate_semantic_consolidation_artifact(artifact)
    return artifact
