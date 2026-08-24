"""Advisory derivation-mode and Human-review escalation contract."""

from __future__ import annotations

from dataclasses import dataclass

from .errors import (
    ModelCandidateReferenceError,
    ModelCandidateValidationError,
)
from .types import (
    ModelCandidateProjectionCoverage,
    ModelCandidateReviewDecision,
    ModelCandidateSetSnapshot,
)


ECO_DETERMINISTIC_MODE = "eco_deterministic"
LLM_ASSISTED_MODE = "llm_assisted"

MODEL_DERIVATION_MODES = frozenset(
    {
        ECO_DETERMINISTIC_MODE,
        LLM_ASSISTED_MODE,
    }
)

RECOMMENDATION_ECO_COVERAGE = "eco_coverage_complete"
RECOMMENDATION_LLM_UNRESOLVED = "llm_unresolved_projection"
RECOMMENDATION_LLM_REVIEW_ESCALATION = "llm_review_rejection_escalation"


@dataclass(frozen=True, slots=True)
class ModelDerivationStrategyAssessment:
    """Advisory mode recommendation for one Approved-Input snapshot."""

    project_id: str
    recommended_mode: str
    recommendation_reason_code: str
    eco_feasible: bool
    mapped_count: int
    ambiguous_count: int
    unmapped_count: int
    intentionally_not_projected_count: int
    unresolved_approved_input_ids: tuple[str, ...]
    predecessor_candidate_set_id: str | None
    rejected_predecessor_candidate_ids: tuple[str, ...]
    escalated_approved_input_ids: tuple[str, ...]
    rationale: str
    approved_subject_count: int = 0
    approved_subject_mapped_count: int = 0
    approved_subject_ambiguous_count: int = 0
    approved_subject_unmapped_count: int = 0
    approved_subject_intentionally_not_projected_count: int = 0
    semantic_relationship_count: int = 0
    semantic_relationship_mapped_count: int = 0
    semantic_relationship_ambiguous_count: int = 0
    semantic_relationship_unmapped_count: int = 0
    semantic_relationship_intentionally_not_projected_count: int = 0


def assess_model_derivation_strategy(
    *,
    coverage: ModelCandidateProjectionCoverage,
    predecessor_candidate_set: ModelCandidateSetSnapshot | None = None,
    predecessor_review_decisions: tuple[
        ModelCandidateReviewDecision,
        ...,
    ] = (),
) -> ModelDerivationStrategyAssessment:
    """Recommend Eco or LLM-assisted without making the Human decision."""

    _validate_coverage(coverage)
    rejected_candidate_ids: tuple[str, ...] = ()
    escalated_approved_input_ids: tuple[str, ...] = ()
    predecessor_candidate_set_id = None

    if predecessor_candidate_set is None:
        if predecessor_review_decisions:
            raise ModelCandidateValidationError(
                "predecessor_review_decisions require a predecessor "
                "Candidate Set."
            )
    else:
        _validate_predecessor(
            coverage=coverage,
            predecessor=predecessor_candidate_set,
        )
        predecessor_candidate_set_id = (
            predecessor_candidate_set.manifest.candidate_set_id
        )
        (
            rejected_candidate_ids,
            escalated_approved_input_ids,
        ) = _review_escalation_targets(
            predecessor=predecessor_candidate_set,
            review_decisions=predecessor_review_decisions,
        )

    unresolved_ids = tuple(
        sorted(coverage.unresolved_approved_input_ids)
    )
    eco_feasible = not unresolved_ids

    if rejected_candidate_ids:
        recommended_mode = LLM_ASSISTED_MODE
        reason_code = RECOMMENDATION_LLM_REVIEW_ESCALATION
        rationale = (
            "Human Model Review rejected predecessor Candidate content. "
            "LLM-assisted regeneration is recommended for the exact "
            "Approved Inputs supporting the rejected Candidate targets."
        )
    elif unresolved_ids:
        recommended_mode = LLM_ASSISTED_MODE
        reason_code = RECOMMENDATION_LLM_UNRESOLVED
        rationale = (
            "Deterministic projection coverage contains unresolved target "
            "mappings across approved engineering information. LLM-assisted derivation is "
            "recommended; Eco remains fail-closed rather than forcing "
            "a target mapping."
        )
    else:
        recommended_mode = ECO_DETERMINISTIC_MODE
        reason_code = RECOMMENDATION_ECO_COVERAGE
        rationale = (
            "All projectable approved engineering information is deterministically ""mapped. "
            "Eco / deterministic derivation is recommended and requires "
            "no LLM call; Model Candidate Review remains mandatory."
        )

    subject_entries = tuple(
        item
        for item in coverage.entries
        if item.approved_input_kind != "semantic_relationship"
    )
    semantic_relationship_entries = tuple(
        item
        for item in coverage.entries
        if item.approved_input_kind == "semantic_relationship"
    )

    def _population_count(entries, disposition):
        return sum(
            1
            for item in entries
            if item.disposition == disposition
        )

    return ModelDerivationStrategyAssessment(
        project_id=coverage.project_id,
        recommended_mode=recommended_mode,
        recommendation_reason_code=reason_code,
        eco_feasible=eco_feasible,
        mapped_count=coverage.mapped_count,
        ambiguous_count=coverage.ambiguous_count,
        unmapped_count=coverage.unmapped_count,
        intentionally_not_projected_count=(
            coverage.intentionally_not_projected_count
        ),
        unresolved_approved_input_ids=unresolved_ids,
        predecessor_candidate_set_id=predecessor_candidate_set_id,
        rejected_predecessor_candidate_ids=(
            rejected_candidate_ids
        ),
        escalated_approved_input_ids=escalated_approved_input_ids,
        rationale=rationale,
        approved_subject_count=len(subject_entries),
        approved_subject_mapped_count=_population_count(
            subject_entries,
            "mapped",
        ),
        approved_subject_ambiguous_count=_population_count(
            subject_entries,
            "ambiguous",
        ),
        approved_subject_unmapped_count=_population_count(
            subject_entries,
            "unmapped",
        ),
        approved_subject_intentionally_not_projected_count=(
            _population_count(
                subject_entries,
                "intentionally_not_projected",
            )
        ),
        semantic_relationship_count=len(
            semantic_relationship_entries
        ),
        semantic_relationship_mapped_count=_population_count(
            semantic_relationship_entries,
            "mapped",
        ),
        semantic_relationship_ambiguous_count=_population_count(
            semantic_relationship_entries,
            "ambiguous",
        ),
        semantic_relationship_unmapped_count=_population_count(
            semantic_relationship_entries,
            "unmapped",
        ),
        semantic_relationship_intentionally_not_projected_count=(
            _population_count(
                semantic_relationship_entries,
                "intentionally_not_projected",
            )
        ),
    )


def validate_model_derivation_mode(
    mode: str,
) -> str:
    """Validate one explicit Human-selected mode without applying advice."""

    if mode not in MODEL_DERIVATION_MODES:
        raise ModelCandidateValidationError(
            "model derivation mode must be one of "
            f"{sorted(MODEL_DERIVATION_MODES)!r}."
        )
    return mode


def build_review_escalation_reason(
    *,
    assessment: ModelDerivationStrategyAssessment,
    human_reason: str,
) -> str:
    """Create a non-empty traceable successor-Candidate regeneration reason."""

    if not isinstance(
        assessment,
        ModelDerivationStrategyAssessment,
    ):
        raise ModelCandidateValidationError(
            "assessment must be ModelDerivationStrategyAssessment."
        )
    if not assessment.rejected_predecessor_candidate_ids:
        raise ModelCandidateValidationError(
            "Review escalation reason requires rejected predecessor "
            "Candidate targets."
        )
    if (
        not isinstance(human_reason, str)
        or not human_reason.strip()
        or human_reason != human_reason.strip()
    ):
        raise ModelCandidateValidationError(
            "human_reason must be non-empty trimmed text."
        )

    targets = ",".join(
        assessment.rejected_predecessor_candidate_ids
    )
    return (
        "Human Model Review escalation from "
        f"{assessment.predecessor_candidate_set_id}; "
        f"rejected_candidates={targets}; reason={human_reason}"
    )


def _validate_coverage(
    coverage: ModelCandidateProjectionCoverage,
) -> None:
    if not isinstance(
        coverage,
        ModelCandidateProjectionCoverage,
    ):
        raise ModelCandidateValidationError(
            "coverage must be ModelCandidateProjectionCoverage."
        )
    if not coverage.is_complete:
        raise ModelCandidateValidationError(
            "projection coverage must account for the complete "
            "Approved-Input snapshot."
        )


def _validate_predecessor(
    *,
    coverage: ModelCandidateProjectionCoverage,
    predecessor: ModelCandidateSetSnapshot,
) -> None:
    if not isinstance(predecessor, ModelCandidateSetSnapshot):
        raise ModelCandidateValidationError(
            "predecessor_candidate_set must be ModelCandidateSetSnapshot."
        )
    if predecessor.manifest.project_id != coverage.project_id:
        raise ModelCandidateReferenceError(
            "Predecessor Candidate Set belongs to another project."
        )


def _review_escalation_targets(
    *,
    predecessor: ModelCandidateSetSnapshot,
    review_decisions: tuple[ModelCandidateReviewDecision, ...],
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    if not isinstance(review_decisions, tuple):
        raise ModelCandidateValidationError(
            "predecessor_review_decisions must be a tuple."
        )

    candidate_set_id = predecessor.manifest.candidate_set_id
    candidate_by_target = _candidate_index(predecessor)

    latest_by_target: dict[
        tuple[str, str],
        ModelCandidateReviewDecision,
    ] = {}

    for decision in review_decisions:
        if not isinstance(decision, ModelCandidateReviewDecision):
            raise ModelCandidateValidationError(
                "predecessor_review_decisions contains an invalid type."
            )
        if decision.project_id != predecessor.manifest.project_id:
            raise ModelCandidateReferenceError(
                "Candidate Review Decision belongs to another project."
            )
        if decision.target.candidate_set_id != candidate_set_id:
            raise ModelCandidateReferenceError(
                "Candidate Review Decision does not bind the selected "
                "predecessor Candidate Set."
            )

        target_key = (
            decision.target.target_type,
            decision.target.candidate_id,
        )
        if target_key not in candidate_by_target:
            raise ModelCandidateReferenceError(
                "Candidate Review Decision references a target outside "
                "the selected predecessor Candidate Set."
            )

        previous = latest_by_target.get(target_key)
        if previous is None or _decision_order_key(
            decision
        ) > _decision_order_key(previous):
            latest_by_target[target_key] = decision

    rejected_targets = tuple(
        sorted(
            target_key
            for target_key, decision in latest_by_target.items()
            if decision.decision == "rejected"
        )
    )

    rejected_candidate_ids = tuple(
        candidate_id
        for _target_type, candidate_id in rejected_targets
    )

    approved_input_ids = set()
    for target_key in rejected_targets:
        candidate = candidate_by_target[target_key]
        for reference in candidate.approved_input_references:
            approved_input_ids.add(reference.approved_input_id)

    return (
        rejected_candidate_ids,
        tuple(sorted(approved_input_ids)),
    )


def _candidate_index(
    predecessor: ModelCandidateSetSnapshot,
):
    result = {}

    for item in predecessor.element_candidates:
        key = (
            "element_candidate",
            item.model_element_candidate_id,
        )
        result[key] = item

    for item in predecessor.relationship_candidates:
        key = (
            "relationship_candidate",
            item.model_relationship_candidate_id,
        )
        result[key] = item

    return result


def _decision_order_key(
    decision: ModelCandidateReviewDecision,
) -> tuple[str, str]:
    return (
        decision.reviewed_at,
        decision.model_candidate_review_decision_id,
    )
