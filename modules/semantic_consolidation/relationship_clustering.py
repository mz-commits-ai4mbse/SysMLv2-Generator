"""Authority-safe semantic clustering for relationship proposals.

C3 reuses the generic C1 SemanticConsolidationArtifact while adding one
relationship-specific authority rule: semantic equivalence may never merge
proposals whose already-consolidated source or target element subjects differ.

Relationship classification is evidence about a semantic relationship subject;
it is not semantic identity by itself.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Callable, Mapping

from .artifact import build_semantic_consolidation_artifact
from .element_clustering import SemanticEvidenceStatement
from .errors import (
    SemanticConsolidationError,
    SemanticConsolidationIntegrityError,
    SemanticConsolidationValidationError,
)
from .types import (
    SEMANTIC_COMPARISON_METHODS,
    SEMANTIC_COMPARISON_OUTCOMES,
    SemanticComparison,
    SemanticConsolidationArtifact,
    SemanticProposalBinding,
    SemanticSubject,
    SemanticUpstreamArtifactBinding,
)


@dataclass(frozen=True)
class RelationshipSemanticProposal:
    """Exact relationship proposal bound to semantic element endpoints."""

    proposal_ref: str
    source_element_proposal_ref: str
    source_semantic_subject_id: str
    proposed_relationship_type: str
    target_element_proposal_ref: str
    target_semantic_subject_id: str
    semantic_statement: str
    agent_id: str
    persona_id: str
    run_index: int
    upstream_artifact_ref: str
    evidence_refs: tuple[str, ...]


@dataclass(frozen=True)
class RelationshipSemanticGroupSuggestion:
    """Comparator-declared relationship group; not authority by itself."""

    member_proposal_refs: tuple[str, ...]


@dataclass(frozen=True)
class RelationshipSemanticPairDecision:
    """Comparator evidence for one unordered relationship proposal pair."""

    left_proposal_ref: str
    right_proposal_ref: str
    outcome: str
    rationale: str


@dataclass(frozen=True)
class RelationshipSemanticComparatorResult:
    """Strict model-independent relationship comparator output."""

    method: str
    trace_ref: str
    groups: tuple[RelationshipSemanticGroupSuggestion, ...]
    comparisons: tuple[RelationshipSemanticPairDecision, ...]


@dataclass(frozen=True)
class RelationshipSemanticConsolidationResult:
    """C3 result plus explicit safe-degradation evidence."""

    artifact: SemanticConsolidationArtifact
    degraded_to_singletons: bool
    warning_codes: tuple[str, ...]


ComparatorCallable = Callable[[dict[str, object]], object]

_COMPARATOR_SCHEMA_VERSION = "1.0.0"
_UNAVAILABLE_WARNING = "relationship_semantic_comparator_unavailable"
_INVALID_WARNING = "relationship_semantic_comparator_invalid"


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


def _run_index(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise SemanticConsolidationValidationError(
            "run_index must be an integer >= 1."
        )
    return value


def _sorted_unique_text_tuple(
    values: object,
    *,
    label: str,
    require_nonempty: bool,
) -> tuple[str, ...]:
    if not isinstance(values, (tuple, list)):
        raise SemanticConsolidationValidationError(
            f"{label} must be a tuple or JSON array."
        )
    checked = tuple(_text(item, label=label) for item in values)
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


def _normalize_proposals(
    proposals: tuple[RelationshipSemanticProposal, ...],
) -> tuple[RelationshipSemanticProposal, ...]:
    if not isinstance(proposals, tuple) or not proposals:
        raise SemanticConsolidationIntegrityError(
            "Relationship semantic consolidation requires at least one proposal."
        )

    normalized: list[RelationshipSemanticProposal] = []
    for proposal in proposals:
        if not isinstance(proposal, RelationshipSemanticProposal):
            raise SemanticConsolidationValidationError(
                "proposals contains an invalid relationship proposal."
            )
        normalized.append(
            RelationshipSemanticProposal(
                proposal_ref=_text(proposal.proposal_ref, label="proposal_ref"),
                source_element_proposal_ref=_text(
                    proposal.source_element_proposal_ref,
                    label="source_element_proposal_ref",
                ),
                source_semantic_subject_id=_text(
                    proposal.source_semantic_subject_id,
                    label="source_semantic_subject_id",
                ),
                proposed_relationship_type=_text(
                    proposal.proposed_relationship_type,
                    label="proposed_relationship_type",
                ),
                target_element_proposal_ref=_text(
                    proposal.target_element_proposal_ref,
                    label="target_element_proposal_ref",
                ),
                target_semantic_subject_id=_text(
                    proposal.target_semantic_subject_id,
                    label="target_semantic_subject_id",
                ),
                semantic_statement=_text(
                    proposal.semantic_statement,
                    label="semantic_statement",
                ),
                agent_id=_text(proposal.agent_id, label="agent_id"),
                persona_id=_text(proposal.persona_id, label="persona_id"),
                run_index=_run_index(proposal.run_index),
                upstream_artifact_ref=_text(
                    proposal.upstream_artifact_ref,
                    label="upstream_artifact_ref",
                ),
                evidence_refs=_sorted_unique_text_tuple(
                    proposal.evidence_refs,
                    label="evidence_refs",
                    require_nonempty=True,
                ),
            )
        )

    result = tuple(sorted(normalized, key=lambda item: item.proposal_ref))
    refs = tuple(item.proposal_ref for item in result)
    if len(refs) != len(set(refs)):
        raise SemanticConsolidationIntegrityError(
            "Relationship semantic proposals must not repeat a proposal_ref."
        )
    return result


def _normalize_evidence_catalog(
    evidence: tuple[SemanticEvidenceStatement, ...],
) -> tuple[SemanticEvidenceStatement, ...]:
    if not isinstance(evidence, tuple) or not evidence:
        raise SemanticConsolidationIntegrityError(
            "Relationship semantic comparison requires an evidence catalog."
        )

    normalized = tuple(
        sorted(
            (
                SemanticEvidenceStatement(
                    evidence_ref=_text(item.evidence_ref, label="evidence_ref"),
                    statement=_text(item.statement, label="evidence statement"),
                )
                for item in evidence
                if isinstance(item, SemanticEvidenceStatement)
            ),
            key=lambda item: item.evidence_ref,
        )
    )
    if len(normalized) != len(evidence):
        raise SemanticConsolidationValidationError(
            "evidence contains an invalid item."
        )
    refs = tuple(item.evidence_ref for item in normalized)
    if len(refs) != len(set(refs)):
        raise SemanticConsolidationIntegrityError(
            "Evidence catalog must not repeat an evidence_ref."
        )
    return normalized


def build_relationship_semantic_comparator_payload(
    *,
    proposals: tuple[RelationshipSemanticProposal, ...],
    evidence: tuple[SemanticEvidenceStatement, ...],
) -> dict[str, object]:
    """Build one compact deterministic relationship comparator payload."""

    normalized_proposals = _normalize_proposals(proposals)
    normalized_evidence = _normalize_evidence_catalog(evidence)
    evidence_by_ref = {
        item.evidence_ref: item.statement for item in normalized_evidence
    }
    referenced = {
        ref
        for proposal in normalized_proposals
        for ref in proposal.evidence_refs
    }
    missing = sorted(referenced - set(evidence_by_ref))
    if missing:
        raise SemanticConsolidationIntegrityError(
            "Relationship proposal evidence references are unavailable: "
            f"{missing}."
        )

    return {
        "schema_version": _COMPARATOR_SCHEMA_VERSION,
        "task": "group_semantically_equivalent_relationship_proposals",
        "authority_constraints": {
            "may_create_engineering_claims": False,
            "may_select_relationship_classification": False,
            "uncertain_authorizes_merge": False,
            "all_proposal_refs_must_be_partitioned_exactly_once": True,
            "different_semantic_endpoints_may_merge": False,
        },
        "proposals": [
            {
                "proposal_ref": proposal.proposal_ref,
                "source_semantic_subject_id": (
                    proposal.source_semantic_subject_id
                ),
                "proposed_relationship_type": (
                    proposal.proposed_relationship_type
                ),
                "target_semantic_subject_id": (
                    proposal.target_semantic_subject_id
                ),
                "semantic_statement": proposal.semantic_statement,
                "evidence_refs": list(proposal.evidence_refs),
            }
            for proposal in normalized_proposals
        ],
        "evidence_catalog": [
            {
                "evidence_ref": item.evidence_ref,
                "statement": item.statement,
            }
            for item in normalized_evidence
            if item.evidence_ref in referenced
        ],
        "required_result": {
            "method": "semantic_model|deterministic_rule",
            "trace_ref": "non-empty comparator trace reference",
            "groups": [
                {"member_proposal_refs": ["proposal refs"]}
            ],
            "comparisons": [
                {
                    "left_proposal_ref": "proposal ref",
                    "right_proposal_ref": "proposal ref",
                    "outcome": "equivalent|distinct|uncertain",
                    "rationale": "brief semantic rationale",
                }
            ],
        },
    }


def _parse_comparator_result(
    value: object,
) -> RelationshipSemanticComparatorResult:
    if not isinstance(value, Mapping):
        raise SemanticConsolidationValidationError(
            "Relationship semantic comparator result must be a JSON object."
        )
    expected = {"method", "trace_ref", "groups", "comparisons"}
    if set(value) != expected:
        raise SemanticConsolidationValidationError(
            "Relationship comparator result has invalid fields."
        )

    method = _text(value["method"], label="comparator method")
    if method not in SEMANTIC_COMPARISON_METHODS:
        raise SemanticConsolidationValidationError(
            "Comparator method is unsupported."
        )
    trace_ref = _text(value["trace_ref"], label="comparator trace_ref")

    raw_groups = value["groups"]
    if not isinstance(raw_groups, list):
        raise SemanticConsolidationValidationError(
            "Comparator groups must be a JSON array."
        )
    groups: list[RelationshipSemanticGroupSuggestion] = []
    for raw in raw_groups:
        if not isinstance(raw, Mapping) or set(raw) != {"member_proposal_refs"}:
            raise SemanticConsolidationValidationError(
                "Comparator group has invalid fields."
            )
        members = raw["member_proposal_refs"]
        if not isinstance(members, list) or not members:
            raise SemanticConsolidationIntegrityError(
                "Comparator group member_proposal_refs must not be empty."
            )
        checked = tuple(
            _text(item, label="group member_proposal_refs")
            for item in members
        )
        if len(checked) != len(set(checked)):
            raise SemanticConsolidationIntegrityError(
                "Comparator group must not repeat a proposal_ref."
            )
        groups.append(
            RelationshipSemanticGroupSuggestion(
                member_proposal_refs=tuple(sorted(checked))
            )
        )

    raw_comparisons = value["comparisons"]
    if not isinstance(raw_comparisons, list):
        raise SemanticConsolidationValidationError(
            "Comparator comparisons must be a JSON array."
        )
    comparisons: list[RelationshipSemanticPairDecision] = []
    for raw in raw_comparisons:
        fields = {
            "left_proposal_ref",
            "right_proposal_ref",
            "outcome",
            "rationale",
        }
        if not isinstance(raw, Mapping) or set(raw) != fields:
            raise SemanticConsolidationValidationError(
                "Comparator comparison has invalid fields."
            )
        left = _text(raw["left_proposal_ref"], label="left_proposal_ref")
        right = _text(raw["right_proposal_ref"], label="right_proposal_ref")
        if left == right:
            raise SemanticConsolidationIntegrityError(
                "Comparator must not self-compare a proposal."
            )
        left, right = sorted((left, right))
        outcome = _text(raw["outcome"], label="comparison outcome")
        if outcome not in SEMANTIC_COMPARISON_OUTCOMES:
            raise SemanticConsolidationValidationError(
                "Comparator comparison outcome is unsupported."
            )
        comparisons.append(
            RelationshipSemanticPairDecision(
                left_proposal_ref=left,
                right_proposal_ref=right,
                outcome=outcome,
                rationale=_text(
                    raw["rationale"],
                    label="comparison rationale",
                ),
            )
        )

    normalized_groups = tuple(
        sorted(groups, key=lambda item: item.member_proposal_refs)
    )
    normalized_comparisons = tuple(
        sorted(
            comparisons,
            key=lambda item: (
                item.left_proposal_ref,
                item.right_proposal_ref,
            ),
        )
    )
    pairs = tuple(
        (item.left_proposal_ref, item.right_proposal_ref)
        for item in normalized_comparisons
    )
    if len(pairs) != len(set(pairs)):
        raise SemanticConsolidationIntegrityError(
            "Comparator must not repeat an unordered proposal pair."
        )

    return RelationshipSemanticComparatorResult(
        method=method,
        trace_ref=trace_ref,
        groups=normalized_groups,
        comparisons=normalized_comparisons,
    )


def _semantic_subject_id(member_refs: tuple[str, ...]) -> str:
    canonical = json.dumps(
        list(member_refs),
        ensure_ascii=False,
        separators=(",", ":"),
    )
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:24]
    return f"semantic:relationship:{digest}"


def _singleton_subjects(
    proposals: tuple[RelationshipSemanticProposal, ...],
) -> tuple[SemanticSubject, ...]:
    return tuple(
        SemanticSubject(
            semantic_subject_id=_semantic_subject_id(
                (proposal.proposal_ref,)
            ),
            proposal_kind="relationship",
            member_proposal_refs=(proposal.proposal_ref,),
        )
        for proposal in proposals
    )


def _proposal_bindings(
    proposals: tuple[RelationshipSemanticProposal, ...],
) -> tuple[SemanticProposalBinding, ...]:
    return tuple(
        SemanticProposalBinding(
            proposal_ref=proposal.proposal_ref,
            proposal_kind="relationship",
            agent_id=proposal.agent_id,
            persona_id=proposal.persona_id,
            run_index=proposal.run_index,
            upstream_artifact_ref=proposal.upstream_artifact_ref,
            evidence_refs=proposal.evidence_refs,
        )
        for proposal in proposals
    )


def _build_fallback_artifact(
    *,
    project_id: str,
    processing_run_id: str,
    created_at_utc: str,
    upstream_artifacts: tuple[SemanticUpstreamArtifactBinding, ...],
    proposals: tuple[RelationshipSemanticProposal, ...],
) -> SemanticConsolidationArtifact:
    return build_semantic_consolidation_artifact(
        project_id=project_id,
        processing_run_id=processing_run_id,
        created_at_utc=created_at_utc,
        upstream_artifacts=upstream_artifacts,
        proposals=_proposal_bindings(proposals),
        subjects=_singleton_subjects(proposals),
        comparisons=(),
    )


def _materialize_comparator_artifact(
    *,
    project_id: str,
    processing_run_id: str,
    created_at_utc: str,
    upstream_artifacts: tuple[SemanticUpstreamArtifactBinding, ...],
    proposals: tuple[RelationshipSemanticProposal, ...],
    comparator_result: RelationshipSemanticComparatorResult,
) -> SemanticConsolidationArtifact:
    proposal_by_ref = {
        proposal.proposal_ref: proposal for proposal in proposals
    }
    known_refs = set(proposal_by_ref)

    flattened = tuple(
        proposal_ref
        for group in comparator_result.groups
        for proposal_ref in group.member_proposal_refs
    )
    if set(flattened) != known_refs or len(flattened) != len(known_refs):
        raise SemanticConsolidationIntegrityError(
            "Comparator groups must partition every exact relationship "
            "proposal exactly once."
        )

    subjects: list[SemanticSubject] = []
    for group in comparator_result.groups:
        members = tuple(
            proposal_by_ref[ref]
            for ref in group.member_proposal_refs
            if ref in proposal_by_ref
        )
        if len(members) != len(group.member_proposal_refs):
            raise SemanticConsolidationIntegrityError(
                "Comparator group references an unknown relationship proposal."
            )

        endpoint_pairs = {
            (
                proposal.source_semantic_subject_id,
                proposal.target_semantic_subject_id,
            )
            for proposal in members
        }
        if len(endpoint_pairs) != 1:
            raise SemanticConsolidationIntegrityError(
                "Relationship proposals with different semantic endpoints "
                "must not share one semantic subject."
            )

        subjects.append(
            SemanticSubject(
                semantic_subject_id=_semantic_subject_id(
                    group.member_proposal_refs
                ),
                proposal_kind="relationship",
                member_proposal_refs=group.member_proposal_refs,
            )
        )

    comparisons: list[SemanticComparison] = []
    for decision in comparator_result.comparisons:
        if (
            decision.left_proposal_ref not in known_refs
            or decision.right_proposal_ref not in known_refs
        ):
            raise SemanticConsolidationIntegrityError(
                "Comparator comparison references an unknown proposal."
            )
        comparisons.append(
            SemanticComparison(
                left_proposal_ref=decision.left_proposal_ref,
                right_proposal_ref=decision.right_proposal_ref,
                outcome=decision.outcome,
                method=comparator_result.method,
                trace_ref=comparator_result.trace_ref,
                rationale=decision.rationale,
            )
        )

    return build_semantic_consolidation_artifact(
        project_id=project_id,
        processing_run_id=processing_run_id,
        created_at_utc=created_at_utc,
        upstream_artifacts=upstream_artifacts,
        proposals=_proposal_bindings(proposals),
        subjects=tuple(
            sorted(subjects, key=lambda item: item.semantic_subject_id)
        ),
        comparisons=tuple(comparisons),
    )


def consolidate_relationship_proposals(
    *,
    project_id: str,
    processing_run_id: str,
    created_at_utc: str,
    upstream_artifacts: tuple[SemanticUpstreamArtifactBinding, ...],
    proposals: tuple[RelationshipSemanticProposal, ...],
    evidence: tuple[SemanticEvidenceStatement, ...],
    comparator: ComparatorCallable | None,
) -> RelationshipSemanticConsolidationResult:
    """Run C3 relationship consolidation with safe singleton degradation."""

    normalized_proposals = _normalize_proposals(proposals)
    payload = build_relationship_semantic_comparator_payload(
        proposals=normalized_proposals,
        evidence=evidence,
    )

    fallback = _build_fallback_artifact(
        project_id=project_id,
        processing_run_id=processing_run_id,
        created_at_utc=created_at_utc,
        upstream_artifacts=upstream_artifacts,
        proposals=normalized_proposals,
    )

    if comparator is None:
        return RelationshipSemanticConsolidationResult(
            artifact=fallback,
            degraded_to_singletons=True,
            warning_codes=(_UNAVAILABLE_WARNING,),
        )

    try:
        raw_result = comparator(payload)
    except Exception:
        return RelationshipSemanticConsolidationResult(
            artifact=fallback,
            degraded_to_singletons=True,
            warning_codes=(_UNAVAILABLE_WARNING,),
        )

    try:
        parsed = _parse_comparator_result(raw_result)
        artifact = _materialize_comparator_artifact(
            project_id=project_id,
            processing_run_id=processing_run_id,
            created_at_utc=created_at_utc,
            upstream_artifacts=upstream_artifacts,
            proposals=normalized_proposals,
            comparator_result=parsed,
        )
    except SemanticConsolidationError:
        return RelationshipSemanticConsolidationResult(
            artifact=fallback,
            degraded_to_singletons=True,
            warning_codes=(_INVALID_WARNING,),
        )

    return RelationshipSemanticConsolidationResult(
        artifact=artifact,
        degraded_to_singletons=False,
        warning_codes=(),
    )
