"""Authority-safe cross-unit semantic synthesis for ADR-026 D4.

D4 consumes already-localized semantic subjects from canonical Source Analysis
Units. It never compares the global pool of raw Agent proposals. Comparator
output is advisory: malformed, incomplete or unavailable output cannot authorize
an unsafe merge and degrades conservatively to singleton synthesized subjects.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
import json
import re
from typing import Callable

from modules.source_analysis_units.identifiers import (
    validate_source_analysis_unit_id,
)

from .errors import (
    SemanticConsolidationIntegrityError,
    SemanticConsolidationValidationError,
)


CrossUnitComparator = Callable[[dict[str, object]], object]

_CROSS_UNIT_SCHEMA_VERSION = "1.0.0"
_SYNTHESIZED_ELEMENT_ID_PATTERN = re.compile(r"^SES-[0-9]{6}$")
_SYNTHESIZED_RELATIONSHIP_ID_PATTERN = re.compile(r"^SRS-[0-9]{6}$")
_PROJECT_ID_PATTERN = re.compile(r"^[0-9]{6}$")
_TIMESTAMP_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$"
)
_COMPARISON_OUTCOMES = frozenset({"equivalent", "distinct", "uncertain"})

_ELEMENT_UNAVAILABLE_WARNING = "cross_unit_element_comparator_unavailable"
_ELEMENT_INVALID_WARNING = "cross_unit_element_comparator_invalid"
_RELATIONSHIP_UNAVAILABLE_WARNING = (
    "cross_unit_relationship_comparator_unavailable"
)
_RELATIONSHIP_INVALID_WARNING = "cross_unit_relationship_comparator_invalid"
_RELATIONSHIP_ENDPOINT_WARNING = (
    "cross_unit_relationship_endpoint_human_review_required"
)


@dataclass(frozen=True, slots=True)
class LocalElementSubject:
    """One D3 element subject bound to one canonical Source Analysis Unit."""

    local_subject_ref: str
    source_analysis_unit_id: str
    local_semantic_subject_id: str
    member_proposal_refs: tuple[str, ...]
    candidate_names: tuple[str, ...]
    proposed_element_types: tuple[str, ...]
    concise_descriptions: tuple[str, ...]
    evidence_refs: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class LocalRelationshipSubject:
    """One D3 relationship subject with local element endpoint bindings."""

    local_subject_ref: str
    source_analysis_unit_id: str
    local_semantic_subject_id: str
    member_proposal_refs: tuple[str, ...]
    source_local_element_subject_ref: str | None
    source_unresolved_endpoint_ref: str | None
    target_local_element_subject_ref: str | None
    target_unresolved_endpoint_ref: str | None
    proposed_relationship_types: tuple[str, ...]
    semantic_statements: tuple[str, ...]
    evidence_refs: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CrossUnitSemanticComparison:
    """Validated comparator evidence between two local semantic subjects."""

    proposal_kind: str
    left_local_subject_ref: str
    right_local_subject_ref: str
    outcome: str
    method: str
    trace_ref: str
    rationale: str


@dataclass(frozen=True, slots=True)
class SynthesizedElementSubject:
    """One engineering subject synthesized across Source Analysis Units."""

    synthesized_subject_id: str
    member_local_subject_refs: tuple[str, ...]
    source_analysis_unit_ids: tuple[str, ...]
    member_proposal_refs: tuple[str, ...]
    evidence_refs: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RelationshipRebindingFinding:
    """Endpoint that cannot be rebound without Human Review."""

    local_relationship_subject_ref: str
    endpoint_role: str
    unresolved_endpoint_ref: str
    finding_code: str


@dataclass(frozen=True, slots=True)
class SynthesizedRelationshipSubject:
    """One relationship subject after endpoint rebinding and synthesis."""

    synthesized_subject_id: str
    member_local_subject_refs: tuple[str, ...]
    source_analysis_unit_ids: tuple[str, ...]
    member_proposal_refs: tuple[str, ...]
    source_synthesized_element_subject_id: str | None
    target_synthesized_element_subject_id: str | None
    proposed_relationship_types: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    requires_human_review: bool


@dataclass(frozen=True, slots=True)
class CrossUnitSemanticSynthesisArtifact:
    """Immutable D4 synthesis artifact spanning all Source Analysis Units."""

    schema_version: str
    artifact_kind: str
    project_id: str
    processing_run_id: str
    created_at_utc: str
    source_analysis_unit_ids: tuple[str, ...]
    local_element_subjects: tuple[LocalElementSubject, ...]
    synthesized_element_subjects: tuple[SynthesizedElementSubject, ...]
    element_comparisons: tuple[CrossUnitSemanticComparison, ...]
    local_relationship_subjects: tuple[LocalRelationshipSubject, ...]
    synthesized_relationship_subjects: tuple[
        SynthesizedRelationshipSubject, ...
    ]
    relationship_comparisons: tuple[CrossUnitSemanticComparison, ...]
    relationship_rebinding_findings: tuple[RelationshipRebindingFinding, ...]
    artifact_fingerprint: str


@dataclass(frozen=True, slots=True)
class CrossUnitSemanticSynthesisResult:
    """D4 artifact plus explicit safe-degradation evidence."""

    artifact: CrossUnitSemanticSynthesisArtifact
    element_degraded_to_singletons: bool
    element_warning_codes: tuple[str, ...]
    relationship_degraded_to_singletons: bool
    relationship_warning_codes: tuple[str, ...]


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


def _sorted_unique_texts(
    values: object,
    *,
    label: str,
    require_nonempty: bool,
) -> tuple[str, ...]:
    if not isinstance(values, (tuple, list)):
        raise SemanticConsolidationValidationError(
            f"{label} must be a tuple or JSON array."
        )
    checked = tuple(_text(value, label=label) for value in values)
    if require_nonempty and not checked:
        raise SemanticConsolidationIntegrityError(
            f"{label} must not be empty."
        )
    normalized = tuple(sorted(set(checked)))
    return normalized


def _project_id(value: object) -> str:
    value = _text(value, label="project_id")
    if _PROJECT_ID_PATTERN.fullmatch(value) is None:
        raise SemanticConsolidationValidationError(
            "project_id must be a six-digit Project ID."
        )
    return value


def _timestamp(value: object) -> str:
    value = _text(value, label="created_at_utc")
    if _TIMESTAMP_PATTERN.fullmatch(value) is None:
        raise SemanticConsolidationValidationError(
            "created_at_utc must be an ISO-8601 UTC timestamp ending in Z."
        )
    return value


def _normalize_local_elements(
    values: tuple[LocalElementSubject, ...],
) -> tuple[LocalElementSubject, ...]:
    if not isinstance(values, tuple):
        raise SemanticConsolidationValidationError(
            "local_element_subjects must be a tuple."
        )
    normalized: list[LocalElementSubject] = []
    for value in values:
        if not isinstance(value, LocalElementSubject):
            raise SemanticConsolidationValidationError(
                "local_element_subjects contains an invalid item."
            )
        try:
            unit_id = validate_source_analysis_unit_id(
                value.source_analysis_unit_id
            )
        except Exception as exc:
            raise SemanticConsolidationValidationError(
                "Local element source_analysis_unit_id is invalid."
            ) from exc
        normalized.append(
            LocalElementSubject(
                local_subject_ref=_text(
                    value.local_subject_ref,
                    label="local_subject_ref",
                ),
                source_analysis_unit_id=unit_id,
                local_semantic_subject_id=_text(
                    value.local_semantic_subject_id,
                    label="local_semantic_subject_id",
                ),
                member_proposal_refs=_sorted_unique_texts(
                    value.member_proposal_refs,
                    label="member_proposal_refs",
                    require_nonempty=True,
                ),
                candidate_names=_sorted_unique_texts(
                    value.candidate_names,
                    label="candidate_names",
                    require_nonempty=True,
                ),
                proposed_element_types=_sorted_unique_texts(
                    value.proposed_element_types,
                    label="proposed_element_types",
                    require_nonempty=True,
                ),
                concise_descriptions=_sorted_unique_texts(
                    value.concise_descriptions,
                    label="concise_descriptions",
                    require_nonempty=True,
                ),
                evidence_refs=_sorted_unique_texts(
                    value.evidence_refs,
                    label="evidence_refs",
                    require_nonempty=True,
                ),
            )
        )
    result = tuple(sorted(normalized, key=lambda item: item.local_subject_ref))
    refs = tuple(item.local_subject_ref for item in result)
    if len(refs) != len(set(refs)):
        raise SemanticConsolidationIntegrityError(
            "Local element subject references must be unique."
        )
    local_ids = tuple(
        (item.source_analysis_unit_id, item.local_semantic_subject_id)
        for item in result
    )
    if len(local_ids) != len(set(local_ids)):
        raise SemanticConsolidationIntegrityError(
            "Local element semantic subject identity must be unique per SAU."
        )
    return result


def _endpoint_pair(
    local_ref: str | None,
    unresolved_ref: str | None,
    *,
    label: str,
) -> tuple[str | None, str | None]:
    if local_ref is not None:
        local_ref = _text(local_ref, label=f"{label}_local_subject_ref")
    if unresolved_ref is not None:
        unresolved_ref = _text(
            unresolved_ref,
            label=f"{label}_unresolved_endpoint_ref",
        )
    if (local_ref is None) == (unresolved_ref is None):
        raise SemanticConsolidationIntegrityError(
            f"{label} endpoint must contain exactly one local or unresolved binding."
        )
    return local_ref, unresolved_ref


def _normalize_local_relationships(
    values: tuple[LocalRelationshipSubject, ...],
) -> tuple[LocalRelationshipSubject, ...]:
    if not isinstance(values, tuple):
        raise SemanticConsolidationValidationError(
            "local_relationship_subjects must be a tuple."
        )
    normalized: list[LocalRelationshipSubject] = []
    for value in values:
        if not isinstance(value, LocalRelationshipSubject):
            raise SemanticConsolidationValidationError(
                "local_relationship_subjects contains an invalid item."
            )
        try:
            unit_id = validate_source_analysis_unit_id(
                value.source_analysis_unit_id
            )
        except Exception as exc:
            raise SemanticConsolidationValidationError(
                "Local relationship source_analysis_unit_id is invalid."
            ) from exc
        source_local, source_unresolved = _endpoint_pair(
            value.source_local_element_subject_ref,
            value.source_unresolved_endpoint_ref,
            label="source",
        )
        target_local, target_unresolved = _endpoint_pair(
            value.target_local_element_subject_ref,
            value.target_unresolved_endpoint_ref,
            label="target",
        )
        normalized.append(
            LocalRelationshipSubject(
                local_subject_ref=_text(
                    value.local_subject_ref,
                    label="local_relationship_subject_ref",
                ),
                source_analysis_unit_id=unit_id,
                local_semantic_subject_id=_text(
                    value.local_semantic_subject_id,
                    label="local_relationship_semantic_subject_id",
                ),
                member_proposal_refs=_sorted_unique_texts(
                    value.member_proposal_refs,
                    label="relationship member_proposal_refs",
                    require_nonempty=True,
                ),
                source_local_element_subject_ref=source_local,
                source_unresolved_endpoint_ref=source_unresolved,
                target_local_element_subject_ref=target_local,
                target_unresolved_endpoint_ref=target_unresolved,
                proposed_relationship_types=_sorted_unique_texts(
                    value.proposed_relationship_types,
                    label="proposed_relationship_types",
                    require_nonempty=True,
                ),
                semantic_statements=_sorted_unique_texts(
                    value.semantic_statements,
                    label="semantic_statements",
                    require_nonempty=True,
                ),
                evidence_refs=_sorted_unique_texts(
                    value.evidence_refs,
                    label="relationship evidence_refs",
                    require_nonempty=True,
                ),
            )
        )
    result = tuple(sorted(normalized, key=lambda item: item.local_subject_ref))
    refs = tuple(item.local_subject_ref for item in result)
    if len(refs) != len(set(refs)):
        raise SemanticConsolidationIntegrityError(
            "Local relationship subject references must be unique."
        )
    return result


def build_cross_unit_element_comparator_payload(
    local_subjects: tuple[LocalElementSubject, ...],
) -> dict[str, object]:
    """Build compact D4 element-comparison input from local subjects only."""

    subjects = _normalize_local_elements(local_subjects)
    return {
        "schema_version": _CROSS_UNIT_SCHEMA_VERSION,
        "task": "cross_unit_element_semantic_synthesis",
        "local_subjects": [
            {
                "local_subject_ref": item.local_subject_ref,
                "source_analysis_unit_id": item.source_analysis_unit_id,
                "candidate_names": list(item.candidate_names),
                "proposed_element_types": list(item.proposed_element_types),
                "concise_descriptions": list(item.concise_descriptions),
                "evidence_refs": list(item.evidence_refs),
            }
            for item in subjects
        ],
        "required_result": {
            "schema_version": _CROSS_UNIT_SCHEMA_VERSION,
            "method": "semantic_model",
            "trace_ref": "pending",
            "groups": [
                {"member_refs": ["<local_subject_ref>"]}
            ],
            "comparisons": [
                {
                    "left_ref": "<local_subject_ref>",
                    "right_ref": "<local_subject_ref>",
                    "outcome": "equivalent|distinct|uncertain",
                    "rationale": "<concise semantic rationale>",
                }
            ],
        },
    }


def build_cross_unit_relationship_comparator_payload(
    local_subjects: tuple[LocalRelationshipSubject, ...],
    *,
    rebound_endpoints: dict[str, tuple[str, str]],
) -> dict[str, object]:
    """Build D4 relationship input after exact element endpoint rebinding."""

    subjects = _normalize_local_relationships(local_subjects)
    eligible = tuple(
        item for item in subjects if item.local_subject_ref in rebound_endpoints
    )
    return {
        "schema_version": _CROSS_UNIT_SCHEMA_VERSION,
        "task": "cross_unit_relationship_semantic_synthesis",
        "local_subjects": [
            {
                "local_subject_ref": item.local_subject_ref,
                "source_analysis_unit_id": item.source_analysis_unit_id,
                "source_synthesized_element_subject_id": rebound_endpoints[
                    item.local_subject_ref
                ][0],
                "target_synthesized_element_subject_id": rebound_endpoints[
                    item.local_subject_ref
                ][1],
                "proposed_relationship_types": list(
                    item.proposed_relationship_types
                ),
                "semantic_statements": list(item.semantic_statements),
                "evidence_refs": list(item.evidence_refs),
            }
            for item in eligible
        ],
        "required_result": {
            "schema_version": _CROSS_UNIT_SCHEMA_VERSION,
            "method": "semantic_model",
            "trace_ref": "pending",
            "groups": [
                {"member_refs": ["<local_subject_ref>"]}
            ],
            "comparisons": [
                {
                    "left_ref": "<local_subject_ref>",
                    "right_ref": "<local_subject_ref>",
                    "outcome": "equivalent|distinct|uncertain",
                    "rationale": "<concise semantic rationale>",
                }
            ],
        },
    }


def _fallback_groups(refs: tuple[str, ...]) -> tuple[tuple[str, ...], ...]:
    return tuple((ref,) for ref in sorted(refs))


def _normalize_comparator_result(
    raw: object,
    *,
    known_refs: tuple[str, ...],
    proposal_kind: str,
    endpoint_by_ref: dict[str, tuple[str, str]] | None = None,
) -> tuple[tuple[tuple[str, ...], ...], tuple[CrossUnitSemanticComparison, ...]]:
    if not isinstance(raw, dict):
        raise SemanticConsolidationValidationError(
            "Cross-unit comparator output must be a JSON object."
        )
    expected = frozenset(
        {"schema_version", "method", "trace_ref", "groups", "comparisons"}
    )
    if frozenset(raw) != expected:
        raise SemanticConsolidationValidationError(
            "Cross-unit comparator output fields do not match the contract."
        )
    if raw["schema_version"] != _CROSS_UNIT_SCHEMA_VERSION:
        raise SemanticConsolidationValidationError(
            "Cross-unit comparator schema_version is unsupported."
        )
    method = _text(raw["method"], label="comparator method")
    if method != "semantic_model":
        raise SemanticConsolidationValidationError(
            "Cross-unit comparator method must be semantic_model."
        )
    trace_ref = _text(raw["trace_ref"], label="comparator trace_ref")

    raw_groups = raw["groups"]
    if not isinstance(raw_groups, list) or not raw_groups:
        raise SemanticConsolidationIntegrityError(
            "Cross-unit comparator groups must be a non-empty JSON array."
        )
    groups: list[tuple[str, ...]] = []
    flattened: list[str] = []
    for group in raw_groups:
        if not isinstance(group, dict) or frozenset(group) != {"member_refs"}:
            raise SemanticConsolidationValidationError(
                "Cross-unit comparator group has invalid fields."
            )
        members = _sorted_unique_texts(
            group["member_refs"],
            label="group member_refs",
            require_nonempty=True,
        )
        groups.append(members)
        flattened.extend(members)

    known = tuple(sorted(known_refs))
    if tuple(sorted(flattened)) != known:
        raise SemanticConsolidationIntegrityError(
            "Cross-unit comparator groups must form one complete non-overlapping partition."
        )
    if len(flattened) != len(set(flattened)):
        raise SemanticConsolidationIntegrityError(
            "Cross-unit comparator groups contain duplicate subject references."
        )

    raw_comparisons = raw["comparisons"]
    if not isinstance(raw_comparisons, list):
        raise SemanticConsolidationValidationError(
            "Cross-unit comparator comparisons must be a JSON array."
        )
    comparisons: list[CrossUnitSemanticComparison] = []
    seen_pairs: set[tuple[str, str]] = set()
    known_set = set(known)
    equivalent_pairs: set[tuple[str, str]] = set()
    for item in raw_comparisons:
        if not isinstance(item, dict) or frozenset(item) != {
            "left_ref", "right_ref", "outcome", "rationale"
        }:
            raise SemanticConsolidationValidationError(
                "Cross-unit comparator comparison has invalid fields."
            )
        left = _text(item["left_ref"], label="left_ref")
        right = _text(item["right_ref"], label="right_ref")
        if left == right or left not in known_set or right not in known_set:
            raise SemanticConsolidationIntegrityError(
                "Cross-unit comparator comparison references are invalid."
            )
        pair = tuple(sorted((left, right)))
        if pair in seen_pairs:
            raise SemanticConsolidationIntegrityError(
                "Cross-unit comparator repeats one unordered comparison pair."
            )
        seen_pairs.add(pair)
        outcome = _text(item["outcome"], label="comparison outcome")
        if outcome not in _COMPARISON_OUTCOMES:
            raise SemanticConsolidationValidationError(
                "Cross-unit comparator comparison outcome is invalid."
            )
        if outcome == "equivalent":
            equivalent_pairs.add(pair)
        comparisons.append(
            CrossUnitSemanticComparison(
                proposal_kind=proposal_kind,
                left_local_subject_ref=pair[0],
                right_local_subject_ref=pair[1],
                outcome=outcome,
                method=method,
                trace_ref=trace_ref,
                rationale=_text(item["rationale"], label="comparison rationale"),
            )
        )

    group_by_ref = {
        ref: index for index, group in enumerate(groups) for ref in group
    }
    for left, right in equivalent_pairs:
        if group_by_ref[left] != group_by_ref[right]:
            raise SemanticConsolidationIntegrityError(
                "Equivalent comparison crosses comparator groups."
            )

    for group in groups:
        if len(group) < 2:
            continue
        connected = {group[0]}
        changed = True
        while changed:
            changed = False
            for left, right in equivalent_pairs:
                if left not in group or right not in group:
                    continue
                if left in connected and right not in connected:
                    connected.add(right)
                    changed = True
                elif right in connected and left not in connected:
                    connected.add(left)
                    changed = True
        if connected != set(group):
            raise SemanticConsolidationIntegrityError(
                "Every multi-subject group requires a connected graph of equivalent comparisons."
            )

        if endpoint_by_ref is not None:
            endpoints = {endpoint_by_ref[ref] for ref in group}
            if len(endpoints) != 1:
                raise SemanticConsolidationIntegrityError(
                    "Relationship synthesis may not merge different rebound endpoint pairs."
                )

    ordered_groups = tuple(
        sorted((tuple(sorted(group)) for group in groups), key=lambda group: group[0])
    )
    return ordered_groups, tuple(
        sorted(
            comparisons,
            key=lambda item: (
                item.left_local_subject_ref,
                item.right_local_subject_ref,
            ),
        )
    )


def _resolve_groups(
    *,
    refs: tuple[str, ...],
    payload: dict[str, object],
    comparator: CrossUnitComparator | None,
    proposal_kind: str,
    unavailable_warning: str,
    invalid_warning: str,
    endpoint_by_ref: dict[str, tuple[str, str]] | None = None,
) -> tuple[
    tuple[tuple[str, ...], ...],
    tuple[CrossUnitSemanticComparison, ...],
    bool,
    tuple[str, ...],
]:
    if len(refs) <= 1:
        return _fallback_groups(refs), (), False, ()
    if comparator is None:
        return _fallback_groups(refs), (), True, (unavailable_warning,)
    try:
        raw = comparator(payload)
    except Exception:
        return _fallback_groups(refs), (), True, (unavailable_warning,)
    try:
        groups, comparisons = _normalize_comparator_result(
            raw,
            known_refs=refs,
            proposal_kind=proposal_kind,
            endpoint_by_ref=endpoint_by_ref,
        )
    except Exception:
        return _fallback_groups(refs), (), True, (invalid_warning,)
    return groups, comparisons, False, ()


def _element_subject_payload(value: LocalElementSubject) -> dict[str, object]:
    return {
        "local_subject_ref": value.local_subject_ref,
        "source_analysis_unit_id": value.source_analysis_unit_id,
        "local_semantic_subject_id": value.local_semantic_subject_id,
        "member_proposal_refs": list(value.member_proposal_refs),
        "candidate_names": list(value.candidate_names),
        "proposed_element_types": list(value.proposed_element_types),
        "concise_descriptions": list(value.concise_descriptions),
        "evidence_refs": list(value.evidence_refs),
    }


def _relationship_subject_payload(
    value: LocalRelationshipSubject,
) -> dict[str, object]:
    return {
        "local_subject_ref": value.local_subject_ref,
        "source_analysis_unit_id": value.source_analysis_unit_id,
        "local_semantic_subject_id": value.local_semantic_subject_id,
        "member_proposal_refs": list(value.member_proposal_refs),
        "source_local_element_subject_ref": value.source_local_element_subject_ref,
        "source_unresolved_endpoint_ref": value.source_unresolved_endpoint_ref,
        "target_local_element_subject_ref": value.target_local_element_subject_ref,
        "target_unresolved_endpoint_ref": value.target_unresolved_endpoint_ref,
        "proposed_relationship_types": list(value.proposed_relationship_types),
        "semantic_statements": list(value.semantic_statements),
        "evidence_refs": list(value.evidence_refs),
    }


def _comparison_payload(value: CrossUnitSemanticComparison) -> dict[str, object]:
    return {
        "proposal_kind": value.proposal_kind,
        "left_local_subject_ref": value.left_local_subject_ref,
        "right_local_subject_ref": value.right_local_subject_ref,
        "outcome": value.outcome,
        "method": value.method,
        "trace_ref": value.trace_ref,
        "rationale": value.rationale,
    }


def _artifact_payload_without_fingerprint(
    artifact: CrossUnitSemanticSynthesisArtifact,
) -> dict[str, object]:
    return {
        "schema_version": artifact.schema_version,
        "artifact_kind": artifact.artifact_kind,
        "project_id": artifact.project_id,
        "processing_run_id": artifact.processing_run_id,
        "created_at_utc": artifact.created_at_utc,
        "source_analysis_unit_ids": list(artifact.source_analysis_unit_ids),
        "local_element_subjects": [
            _element_subject_payload(item) for item in artifact.local_element_subjects
        ],
        "synthesized_element_subjects": [
            {
                "synthesized_subject_id": item.synthesized_subject_id,
                "member_local_subject_refs": list(item.member_local_subject_refs),
                "source_analysis_unit_ids": list(item.source_analysis_unit_ids),
                "member_proposal_refs": list(item.member_proposal_refs),
                "evidence_refs": list(item.evidence_refs),
            }
            for item in artifact.synthesized_element_subjects
        ],
        "element_comparisons": [
            _comparison_payload(item) for item in artifact.element_comparisons
        ],
        "local_relationship_subjects": [
            _relationship_subject_payload(item)
            for item in artifact.local_relationship_subjects
        ],
        "synthesized_relationship_subjects": [
            {
                "synthesized_subject_id": item.synthesized_subject_id,
                "member_local_subject_refs": list(item.member_local_subject_refs),
                "source_analysis_unit_ids": list(item.source_analysis_unit_ids),
                "member_proposal_refs": list(item.member_proposal_refs),
                "source_synthesized_element_subject_id": (
                    item.source_synthesized_element_subject_id
                ),
                "target_synthesized_element_subject_id": (
                    item.target_synthesized_element_subject_id
                ),
                "proposed_relationship_types": list(
                    item.proposed_relationship_types
                ),
                "evidence_refs": list(item.evidence_refs),
                "requires_human_review": item.requires_human_review,
            }
            for item in artifact.synthesized_relationship_subjects
        ],
        "relationship_comparisons": [
            _comparison_payload(item) for item in artifact.relationship_comparisons
        ],
        "relationship_rebinding_findings": [
            {
                "local_relationship_subject_ref": item.local_relationship_subject_ref,
                "endpoint_role": item.endpoint_role,
                "unresolved_endpoint_ref": item.unresolved_endpoint_ref,
                "finding_code": item.finding_code,
            }
            for item in artifact.relationship_rebinding_findings
        ],
    }


def cross_unit_semantic_synthesis_artifact_to_dict(
    artifact: CrossUnitSemanticSynthesisArtifact,
) -> dict[str, object]:
    """Serialize a D4 artifact deterministically."""

    payload = _artifact_payload_without_fingerprint(artifact)
    expected = hashlib.sha256(
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    if artifact.artifact_fingerprint != expected:
        raise SemanticConsolidationIntegrityError(
            "Cross-unit synthesis artifact fingerprint is invalid."
        )
    return {**payload, "artifact_fingerprint": artifact.artifact_fingerprint}


def synthesize_cross_unit_semantics(
    *,
    project_id: str,
    processing_run_id: str,
    created_at_utc: str,
    source_analysis_unit_ids: tuple[str, ...],
    local_element_subjects: tuple[LocalElementSubject, ...],
    local_relationship_subjects: tuple[LocalRelationshipSubject, ...],
    element_comparator: CrossUnitComparator | None,
    relationship_comparator: CrossUnitComparator | None,
) -> CrossUnitSemanticSynthesisResult:
    """Synthesize D3 local subjects and conservatively rebind relationships."""

    project_id = _project_id(project_id)
    processing_run_id = _text(processing_run_id, label="processing_run_id")
    created_at_utc = _timestamp(created_at_utc)
    unit_ids = tuple(
        validate_source_analysis_unit_id(value)
        for value in source_analysis_unit_ids
    )
    if not unit_ids or unit_ids != tuple(sorted(set(unit_ids))):
        raise SemanticConsolidationIntegrityError(
            "source_analysis_unit_ids must be a non-empty sorted unique tuple."
        )

    elements = _normalize_local_elements(local_element_subjects)
    relationships = _normalize_local_relationships(local_relationship_subjects)
    known_units = set(unit_ids)
    if any(item.source_analysis_unit_id not in known_units for item in elements):
        raise SemanticConsolidationIntegrityError(
            "Local element subject references an unknown Source Analysis Unit."
        )
    if any(
        item.source_analysis_unit_id not in known_units for item in relationships
    ):
        raise SemanticConsolidationIntegrityError(
            "Local relationship subject references an unknown Source Analysis Unit."
        )

    element_refs = tuple(item.local_subject_ref for item in elements)
    element_groups, element_comparisons, element_degraded, element_warnings = (
        _resolve_groups(
            refs=element_refs,
            payload=build_cross_unit_element_comparator_payload(elements),
            comparator=element_comparator,
            proposal_kind="element",
            unavailable_warning=_ELEMENT_UNAVAILABLE_WARNING,
            invalid_warning=_ELEMENT_INVALID_WARNING,
        )
    )
    element_by_ref = {item.local_subject_ref: item for item in elements}
    synthesized_elements: list[SynthesizedElementSubject] = []
    synthesized_id_by_local_ref: dict[str, str] = {}
    for index, group in enumerate(element_groups, start=1):
        synthesized_id = f"SES-{index:06d}"
        if _SYNTHESIZED_ELEMENT_ID_PATTERN.fullmatch(synthesized_id) is None:
            raise AssertionError("Invalid synthesized element ID.")
        group_items = tuple(element_by_ref[ref] for ref in group)
        subject = SynthesizedElementSubject(
            synthesized_subject_id=synthesized_id,
            member_local_subject_refs=group,
            source_analysis_unit_ids=tuple(
                sorted({item.source_analysis_unit_id for item in group_items})
            ),
            member_proposal_refs=tuple(
                sorted(
                    {
                        ref
                        for item in group_items
                        for ref in item.member_proposal_refs
                    }
                )
            ),
            evidence_refs=tuple(
                sorted(
                    {
                        ref
                        for item in group_items
                        for ref in item.evidence_refs
                    }
                )
            ),
        )
        synthesized_elements.append(subject)
        for local_ref in group:
            synthesized_id_by_local_ref[local_ref] = synthesized_id

    rebound_endpoints: dict[str, tuple[str, str]] = {}
    rebinding_findings: list[RelationshipRebindingFinding] = []
    eligible_relationships: list[LocalRelationshipSubject] = []
    unresolved_relationships: list[LocalRelationshipSubject] = []

    for relationship in relationships:
        if relationship.source_local_element_subject_ref is not None:
            source_id = synthesized_id_by_local_ref.get(
                relationship.source_local_element_subject_ref
            )
            if source_id is None:
                raise SemanticConsolidationIntegrityError(
                    "Local relationship source endpoint references an unavailable local element subject."
                )
        else:
            source_id = None
            rebinding_findings.append(
                RelationshipRebindingFinding(
                    local_relationship_subject_ref=relationship.local_subject_ref,
                    endpoint_role="source",
                    unresolved_endpoint_ref=relationship.source_unresolved_endpoint_ref or "",
                    finding_code=_RELATIONSHIP_ENDPOINT_WARNING,
                )
            )

        if relationship.target_local_element_subject_ref is not None:
            target_id = synthesized_id_by_local_ref.get(
                relationship.target_local_element_subject_ref
            )
            if target_id is None:
                raise SemanticConsolidationIntegrityError(
                    "Local relationship target endpoint references an unavailable local element subject."
                )
        else:
            target_id = None
            rebinding_findings.append(
                RelationshipRebindingFinding(
                    local_relationship_subject_ref=relationship.local_subject_ref,
                    endpoint_role="target",
                    unresolved_endpoint_ref=relationship.target_unresolved_endpoint_ref or "",
                    finding_code=_RELATIONSHIP_ENDPOINT_WARNING,
                )
            )

        if source_id is None or target_id is None:
            unresolved_relationships.append(relationship)
        else:
            rebound_endpoints[relationship.local_subject_ref] = (
                source_id,
                target_id,
            )
            eligible_relationships.append(relationship)

    eligible_refs = tuple(
        item.local_subject_ref for item in eligible_relationships
    )
    relationship_groups, relationship_comparisons, relationship_degraded, relationship_warnings = (
        _resolve_groups(
            refs=eligible_refs,
            payload=build_cross_unit_relationship_comparator_payload(
                tuple(eligible_relationships),
                rebound_endpoints=rebound_endpoints,
            ),
            comparator=relationship_comparator,
            proposal_kind="relationship",
            unavailable_warning=_RELATIONSHIP_UNAVAILABLE_WARNING,
            invalid_warning=_RELATIONSHIP_INVALID_WARNING,
            endpoint_by_ref=rebound_endpoints,
        )
    )
    if rebinding_findings:
        relationship_warnings = tuple(
            dict.fromkeys((*relationship_warnings, _RELATIONSHIP_ENDPOINT_WARNING))
        )

    relationship_by_ref = {
        item.local_subject_ref: item for item in relationships
    }
    all_relationship_groups = list(relationship_groups)
    all_relationship_groups.extend(
        (item.local_subject_ref,) for item in unresolved_relationships
    )
    all_relationship_groups = sorted(
        all_relationship_groups,
        key=lambda group: group[0],
    )

    synthesized_relationships: list[SynthesizedRelationshipSubject] = []
    for index, group in enumerate(all_relationship_groups, start=1):
        synthesized_id = f"SRS-{index:06d}"
        if _SYNTHESIZED_RELATIONSHIP_ID_PATTERN.fullmatch(synthesized_id) is None:
            raise AssertionError("Invalid synthesized relationship ID.")
        group_items = tuple(relationship_by_ref[ref] for ref in group)
        endpoints = {
            rebound_endpoints[ref]
            for ref in group
            if ref in rebound_endpoints
        }
        if len(endpoints) > 1:
            raise SemanticConsolidationIntegrityError(
                "Synthesized relationship group contains conflicting endpoints."
            )
        if endpoints:
            endpoint = next(iter(endpoints))
        elif len(group_items) == 1:
            item = group_items[0]
            endpoint = (
                synthesized_id_by_local_ref.get(
                    item.source_local_element_subject_ref
                )
                if item.source_local_element_subject_ref is not None
                else None,
                synthesized_id_by_local_ref.get(
                    item.target_local_element_subject_ref
                )
                if item.target_local_element_subject_ref is not None
                else None,
            )
        else:
            endpoint = (None, None)
        requires_review = any(
            ref not in rebound_endpoints for ref in group
        )
        synthesized_relationships.append(
            SynthesizedRelationshipSubject(
                synthesized_subject_id=synthesized_id,
                member_local_subject_refs=tuple(group),
                source_analysis_unit_ids=tuple(
                    sorted({item.source_analysis_unit_id for item in group_items})
                ),
                member_proposal_refs=tuple(
                    sorted(
                        {
                            ref
                            for item in group_items
                            for ref in item.member_proposal_refs
                        }
                    )
                ),
                source_synthesized_element_subject_id=endpoint[0],
                target_synthesized_element_subject_id=endpoint[1],
                proposed_relationship_types=tuple(
                    sorted(
                        {
                            value
                            for item in group_items
                            for value in item.proposed_relationship_types
                        }
                    )
                ),
                evidence_refs=tuple(
                    sorted(
                        {
                            ref
                            for item in group_items
                            for ref in item.evidence_refs
                        }
                    )
                ),
                requires_human_review=requires_review,
            )
        )

    provisional = CrossUnitSemanticSynthesisArtifact(
        schema_version=_CROSS_UNIT_SCHEMA_VERSION,
        artifact_kind="cross_unit_semantic_synthesis",
        project_id=project_id,
        processing_run_id=processing_run_id,
        created_at_utc=created_at_utc,
        source_analysis_unit_ids=unit_ids,
        local_element_subjects=elements,
        synthesized_element_subjects=tuple(synthesized_elements),
        element_comparisons=element_comparisons,
        local_relationship_subjects=relationships,
        synthesized_relationship_subjects=tuple(synthesized_relationships),
        relationship_comparisons=relationship_comparisons,
        relationship_rebinding_findings=tuple(
            sorted(
                rebinding_findings,
                key=lambda item: (
                    item.local_relationship_subject_ref,
                    item.endpoint_role,
                ),
            )
        ),
        artifact_fingerprint="0" * 64,
    )
    payload = _artifact_payload_without_fingerprint(provisional)
    fingerprint = hashlib.sha256(
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    artifact = replace(
        provisional,
        artifact_fingerprint=fingerprint,
    )

    return CrossUnitSemanticSynthesisResult(
        artifact=artifact,
        element_degraded_to_singletons=element_degraded,
        element_warning_codes=element_warnings,
        relationship_degraded_to_singletons=relationship_degraded,
        relationship_warning_codes=relationship_warnings,
    )
