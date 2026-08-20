"""Authority-safe semantic clustering for element proposals.

C2 deliberately separates three concerns:

1. build a compact comparator payload from exact immutable proposal content;
2. validate an externally produced semantic comparison result;
3. materialize a C1 SemanticConsolidationArtifact or degrade safely to
   singleton subjects when comparator output is missing or malformed.

Comparator output never becomes engineering authority by itself. Only explicit
``equivalent`` comparison evidence may authorize a merge.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Callable, Mapping

from .artifact import build_semantic_consolidation_artifact
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
class ElementSemanticProposal:
    """Exact element proposal content required for semantic comparison."""

    proposal_ref: str
    candidate_name: str
    proposed_element_type: str
    concise_description: str
    agent_id: str
    persona_id: str
    run_index: int
    upstream_artifact_ref: str
    evidence_refs: tuple[str, ...]


@dataclass(frozen=True)
class SemanticEvidenceStatement:
    """Exact source statement catalog entry referenced by proposals."""

    evidence_ref: str
    statement: str


@dataclass(frozen=True)
class ElementSemanticGroupSuggestion:
    """Comparator-declared semantic group; not authoritative by itself."""

    member_proposal_refs: tuple[str, ...]


@dataclass(frozen=True)
class ElementSemanticPairDecision:
    """Comparator evidence for one unordered proposal pair."""

    left_proposal_ref: str
    right_proposal_ref: str
    outcome: str
    rationale: str


@dataclass(frozen=True)
class ElementSemanticComparatorResult:
    """Strict model-independent semantic comparator output."""

    method: str
    trace_ref: str
    groups: tuple[ElementSemanticGroupSuggestion, ...]
    comparisons: tuple[ElementSemanticPairDecision, ...]


@dataclass(frozen=True)
class ElementSemanticConsolidationResult:
    """C2 result plus explicit safe-degradation evidence."""

    artifact: SemanticConsolidationArtifact
    degraded_to_singletons: bool
    warning_codes: tuple[str, ...]


ComparatorCallable = Callable[[dict[str, object]], object]


_COMPARATOR_SCHEMA_VERSION = "1.0.0"
_UNAVAILABLE_WARNING = "semantic_comparator_unavailable"
_INVALID_WARNING = "semantic_comparator_invalid"


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


def _normalize_element_proposals(
    proposals: tuple[ElementSemanticProposal, ...],
) -> tuple[ElementSemanticProposal, ...]:
    if not isinstance(proposals, tuple) or not proposals:
        raise SemanticConsolidationIntegrityError(
            "Element semantic consolidation requires at least one proposal."
        )
    normalized: list[ElementSemanticProposal] = []
    for proposal in proposals:
        if not isinstance(proposal, ElementSemanticProposal):
            raise SemanticConsolidationValidationError(
                "proposals contains an invalid element proposal."
            )
        normalized.append(
            ElementSemanticProposal(
                proposal_ref=_text(
                    proposal.proposal_ref,
                    label="proposal_ref",
                ),
                candidate_name=_text(
                    proposal.candidate_name,
                    label="candidate_name",
                ),
                proposed_element_type=_text(
                    proposal.proposed_element_type,
                    label="proposed_element_type",
                ),
                concise_description=_text(
                    proposal.concise_description,
                    label="concise_description",
                ),
                agent_id=_text(proposal.agent_id, label="agent_id"),
                persona_id=_text(
                    proposal.persona_id,
                    label="persona_id",
                ),
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
            "Element semantic proposals must not repeat a proposal_ref."
        )
    return result


def _normalize_evidence_catalog(
    evidence: tuple[SemanticEvidenceStatement, ...],
) -> tuple[SemanticEvidenceStatement, ...]:
    if not isinstance(evidence, tuple) or not evidence:
        raise SemanticConsolidationIntegrityError(
            "Semantic comparison requires an evidence catalog."
        )
    normalized: list[SemanticEvidenceStatement] = []
    for item in evidence:
        if not isinstance(item, SemanticEvidenceStatement):
            raise SemanticConsolidationValidationError(
                "evidence contains an invalid item."
            )
        normalized.append(
            SemanticEvidenceStatement(
                evidence_ref=_text(
                    item.evidence_ref,
                    label="evidence_ref",
                ),
                statement=_text(item.statement, label="evidence statement"),
            )
        )
    result = tuple(sorted(normalized, key=lambda item: item.evidence_ref))
    refs = tuple(item.evidence_ref for item in result)
    if len(refs) != len(set(refs)):
        raise SemanticConsolidationIntegrityError(
            "Evidence catalog must not repeat an evidence_ref."
        )
    return result


def build_element_semantic_comparator_payload(
    *,
    proposals: tuple[ElementSemanticProposal, ...],
    evidence: tuple[SemanticEvidenceStatement, ...],
) -> dict[str, object]:
    """Build a compact deterministic comparator payload.

    Repeated source statements are stored once in ``evidence_catalog`` and are
    referenced by proposal. The payload intentionally excludes whole documents,
    unrelated rationale, and project-wide context.
    """

    normalized_proposals = _normalize_element_proposals(proposals)
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
            "Proposal evidence references are unavailable from the exact "
            f"evidence catalog: {missing}."
        )

    return {
        "schema_version": _COMPARATOR_SCHEMA_VERSION,
        "task": "group_semantically_equivalent_element_proposals",
        "authority_constraints": {
            "may_create_engineering_claims": False,
            "may_select_element_classification": False,
            "uncertain_authorizes_merge": False,
            "all_proposal_refs_must_be_partitioned_exactly_once": True,
        },
        "proposals": [
            {
                "proposal_ref": proposal.proposal_ref,
                "candidate_name": proposal.candidate_name,
                "proposed_element_type": proposal.proposed_element_type,
                "concise_description": proposal.concise_description,
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


def _parse_comparator_result(value: object) -> ElementSemanticComparatorResult:
    if not isinstance(value, Mapping):
        raise SemanticConsolidationValidationError(
            "Semantic comparator result must be a JSON object."
        )
    expected = {"method", "trace_ref", "groups", "comparisons"}
    if set(value) != expected:
        raise SemanticConsolidationValidationError(
            "Semantic comparator result has invalid fields."
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
    groups: list[ElementSemanticGroupSuggestion] = []
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
        checked_members = tuple(
            _text(item, label="group member_proposal_refs")
            for item in members
        )
        if len(checked_members) != len(set(checked_members)):
            raise SemanticConsolidationIntegrityError(
                "Comparator group must not repeat a proposal_ref."
            )
        groups.append(
            ElementSemanticGroupSuggestion(
                member_proposal_refs=tuple(sorted(checked_members))
            )
        )

    raw_comparisons = value["comparisons"]
    if not isinstance(raw_comparisons, list):
        raise SemanticConsolidationValidationError(
            "Comparator comparisons must be a JSON array."
        )
    comparisons: list[ElementSemanticPairDecision] = []
    for raw in raw_comparisons:
        expected_fields = {
            "left_proposal_ref",
            "right_proposal_ref",
            "outcome",
            "rationale",
        }
        if not isinstance(raw, Mapping) or set(raw) != expected_fields:
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
            ElementSemanticPairDecision(
                left_proposal_ref=left,
                right_proposal_ref=right,
                outcome=outcome,
                rationale=_text(raw["rationale"], label="comparison rationale"),
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
    return ElementSemanticComparatorResult(
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
    return f"semantic:element:{digest}"


def _singleton_subjects(
    proposals: tuple[ElementSemanticProposal, ...],
) -> tuple[SemanticSubject, ...]:
    return tuple(
        SemanticSubject(
            semantic_subject_id=_semantic_subject_id((proposal.proposal_ref,)),
            proposal_kind="element",
            member_proposal_refs=(proposal.proposal_ref,),
        )
        for proposal in proposals
    )


def _proposal_bindings(
    proposals: tuple[ElementSemanticProposal, ...],
) -> tuple[SemanticProposalBinding, ...]:
    return tuple(
        SemanticProposalBinding(
            proposal_ref=proposal.proposal_ref,
            proposal_kind="element",
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
    proposals: tuple[ElementSemanticProposal, ...],
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
    proposals: tuple[ElementSemanticProposal, ...],
    comparator_result: ElementSemanticComparatorResult,
) -> SemanticConsolidationArtifact:
    known_refs = {proposal.proposal_ref for proposal in proposals}

    flattened = tuple(
        proposal_ref
        for group in comparator_result.groups
        for proposal_ref in group.member_proposal_refs
    )
    if set(flattened) != known_refs or len(flattened) != len(known_refs):
        raise SemanticConsolidationIntegrityError(
            "Comparator groups must partition every exact proposal exactly once."
        )

    subjects = tuple(
        SemanticSubject(
            semantic_subject_id=_semantic_subject_id(group.member_proposal_refs),
            proposal_kind="element",
            member_proposal_refs=group.member_proposal_refs,
        )
        for group in comparator_result.groups
    )
    subjects = tuple(sorted(subjects, key=lambda item: item.semantic_subject_id))

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
        subjects=subjects,
        comparisons=tuple(comparisons),
    )


def consolidate_element_proposals(
    *,
    project_id: str,
    processing_run_id: str,
    created_at_utc: str,
    upstream_artifacts: tuple[SemanticUpstreamArtifactBinding, ...],
    proposals: tuple[ElementSemanticProposal, ...],
    evidence: tuple[SemanticEvidenceStatement, ...],
    comparator: ComparatorCallable | None,
) -> ElementSemanticConsolidationResult:
    """Run C2 element consolidation with safe singleton degradation.

    Exact input/provenance failures are allowed to propagate as hard failures.
    Comparator unavailability, exceptions, malformed output, or unauthorized
    merge suggestions are degraded to singleton subjects so no semantic merge is
    silently authorized.
    """

    normalized_proposals = _normalize_element_proposals(proposals)
    payload = build_element_semantic_comparator_payload(
        proposals=normalized_proposals,
        evidence=evidence,
    )

    # Build the singleton artifact first. This validates exact project/run,
    # upstream bindings, proposal provenance, evidence refs, and fingerprints.
    # Those failures are authority/integrity failures and must not be hidden by
    # semantic-comparator fallback behavior.
    fallback = _build_fallback_artifact(
        project_id=project_id,
        processing_run_id=processing_run_id,
        created_at_utc=created_at_utc,
        upstream_artifacts=upstream_artifacts,
        proposals=normalized_proposals,
    )

    if comparator is None:
        return ElementSemanticConsolidationResult(
            artifact=fallback,
            degraded_to_singletons=True,
            warning_codes=(_UNAVAILABLE_WARNING,),
        )

    try:
        raw_result = comparator(payload)
    except Exception:
        return ElementSemanticConsolidationResult(
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
        return ElementSemanticConsolidationResult(
            artifact=fallback,
            degraded_to_singletons=True,
            warning_codes=(_INVALID_WARNING,),
        )

    return ElementSemanticConsolidationResult(
        artifact=artifact,
        degraded_to_singletons=False,
        warning_codes=(),
    )
