"""Deterministic presentation builders for the Guided Engineering Workflow."""

from __future__ import annotations

import re
from collections.abc import Iterable

from modules.project_workspace.identifiers import is_valid_project_id

from .errors import GuidedWorkflowValidationError
from .types import (
    GUIDED_CONSENSUS_LEVELS,
    GUIDED_DECISION_PRESENTATION_STATES,
    GUIDED_PERSONA_STABILITY_LEVELS,
    GUIDED_PRESENTATION_SEMANTICS,
    GUIDED_VARIANCE_LEVELS,
    GUIDED_WORKFLOW_PRESENTATION_STATUSES,
    GUIDED_WORKFLOW_STAGE_IDS,
    GUIDED_WORKFLOW_STAGE_LABELS,
    EngineerWorkSummary,
    GuidedComparisonView,
    GuidedDecisionAlternativeView,
    GuidedDecisionView,
    GuidedEngineeringContentView,
    GuidedPersonaResultView,
    GuidedProposalView,
    GuidedVarianceView,
    GuidedWorkflowStageView,
    GuidedWorkflowView,
)


_ENTITY_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,159}$")


def create_engineering_content_view(
    *,
    entity_id: str,
    content_kind: str,
    title: str,
    primary_text: str,
    secondary_text: str | None = None,
    source_label: str | None = None,
    traceability_available: bool = True,
) -> GuidedEngineeringContentView:
    """Create one content-first engineering presentation."""

    return GuidedEngineeringContentView(
        entity_id=_stable_entity_id(entity_id, "entity_id"),
        content_kind=_text(content_kind, "content_kind"),
        title=_text(title, "title"),
        primary_text=_text(primary_text, "primary_text"),
        secondary_text=_optional_text(secondary_text, "secondary_text"),
        source_label=_optional_text(source_label, "source_label"),
        traceability_available=_boolean(
            traceability_available,
            "traceability_available",
        ),
    )


def create_proposal_view(
    *,
    proposal_id: str,
    title: str,
    primary_text: str,
    secondary_text: str | None = None,
    confidence: str | None = None,
    rationale: str | None = None,
    supporting_evidence_count: int = 0,
    missing_evidence_count: int = 0,
) -> GuidedProposalView:
    """Create one exact proposal without creating approval semantics."""

    return GuidedProposalView(
        proposal_id=_stable_entity_id(proposal_id, "proposal_id"),
        title=_text(title, "title"),
        primary_text=_text(primary_text, "primary_text"),
        secondary_text=_optional_text(secondary_text, "secondary_text"),
        confidence=_optional_text(confidence, "confidence"),
        rationale=_optional_text(rationale, "rationale"),
        supporting_evidence_count=_nonnegative_int(
            supporting_evidence_count,
            "supporting_evidence_count",
        ),
        missing_evidence_count=_nonnegative_int(
            missing_evidence_count,
            "missing_evidence_count",
        ),
    )


def create_persona_result_view(
    *,
    persona_id: str,
    persona_label: str,
    stability_level: str,
    run_count: int,
    proposals: Iterable[GuidedProposalView],
) -> GuidedPersonaResultView:
    """Group repeated runs beneath one Persona so they never become extra votes."""

    if stability_level not in GUIDED_PERSONA_STABILITY_LEVELS:
        raise GuidedWorkflowValidationError(
            "stability_level is not supported."
        )
    if not isinstance(run_count, int) or isinstance(run_count, bool):
        raise GuidedWorkflowValidationError(
            "run_count must be an integer."
        )
    if run_count < 1:
        raise GuidedWorkflowValidationError(
            "run_count must be at least one."
        )

    proposal_tuple = tuple(proposals)
    if not proposal_tuple:
        raise GuidedWorkflowValidationError(
            "A Persona result must expose at least one proposal."
        )
    if any(not isinstance(item, GuidedProposalView) for item in proposal_tuple):
        raise GuidedWorkflowValidationError(
            "proposals must contain GuidedProposalView values."
        )
    _require_unique(
        (item.proposal_id for item in proposal_tuple),
        "proposal_id",
    )

    return GuidedPersonaResultView(
        persona_id=_stable_entity_id(persona_id, "persona_id"),
        persona_label=_text(persona_label, "persona_label"),
        stability_level=stability_level,
        run_count=run_count,
        proposals=proposal_tuple,
    )


def create_variance_view(
    *,
    consensus_level: str,
    variance_level: str,
    total_personas: int,
    supporting_personas: Iterable[str] = (),
    dissenting_personas: Iterable[str] = (),
    omitting_personas: Iterable[str] = (),
    review_required: bool,
) -> GuidedVarianceView:
    """Create an accessible consensus indicator without implying approval."""

    if consensus_level not in GUIDED_CONSENSUS_LEVELS:
        raise GuidedWorkflowValidationError(
            "consensus_level is not supported."
        )
    if variance_level not in GUIDED_VARIANCE_LEVELS:
        raise GuidedWorkflowValidationError(
            "variance_level is not supported."
        )
    if not isinstance(total_personas, int) or isinstance(
        total_personas,
        bool,
    ):
        raise GuidedWorkflowValidationError(
            "total_personas must be an integer."
        )
    if total_personas < 1:
        raise GuidedWorkflowValidationError(
            "total_personas must be at least one."
        )
    review_required = _boolean(review_required, "review_required")

    supporting = _persona_tuple(
        supporting_personas,
        "supporting_personas",
    )
    dissenting = _persona_tuple(
        dissenting_personas,
        "dissenting_personas",
    )
    omitting = _persona_tuple(
        omitting_personas,
        "omitting_personas",
    )

    sets = (set(supporting), set(dissenting), set(omitting))
    if sets[0] & sets[1] or sets[0] & sets[2] or sets[1] & sets[2]:
        raise GuidedWorkflowValidationError(
            "Persona support, dissent and omission sets must be disjoint."
        )

    represented = sets[0] | sets[1] | sets[2]
    if len(represented) > total_personas:
        raise GuidedWorkflowValidationError(
            "Persona distribution exceeds total_personas."
        )

    if consensus_level == "unanimous":
        if (
            len(supporting) != total_personas
            or dissenting
            or omitting
        ):
            raise GuidedWorkflowValidationError(
                "unanimous consensus requires support from every Persona."
            )

    semantic = _variance_semantic(
        consensus_level=consensus_level,
        variance_level=variance_level,
    )
    label = _variance_label(
        consensus_level=consensus_level,
        supporting_count=len(supporting),
        total_personas=total_personas,
    )
    explanation = _variance_explanation(
        consensus_level=consensus_level,
        variance_level=variance_level,
        review_required=review_required,
    )

    return GuidedVarianceView(
        consensus_level=consensus_level,
        variance_level=variance_level,
        semantic=semantic,
        label=label,
        explanation=explanation,
        total_personas=total_personas,
        supporting_personas=supporting,
        dissenting_personas=dissenting,
        omitting_personas=omitting,
        review_required=review_required,
    )


def create_decision_alternative_view(
    *,
    alternative_key: str,
    label: str,
    summary: str | None = None,
    source_entity_id: str | None = None,
) -> GuidedDecisionAlternativeView:
    """Create one visible alternative without persisting a Human decision."""

    return GuidedDecisionAlternativeView(
        alternative_key=_stable_entity_id(
            alternative_key,
            "alternative_key",
        ),
        label=_text(label, "label"),
        summary=_optional_text(summary, "summary"),
        source_entity_id=(
            None
            if source_entity_id is None
            else _stable_entity_id(
                source_entity_id,
                "source_entity_id",
            )
        ),
    )


def create_decision_view(
    *,
    decision_key: str,
    subject: str,
    prompt: str,
    presentation_state: str,
    authority_domain: str,
    target_entity_id: str,
    alternatives: Iterable[GuidedDecisionAlternativeView] = (),
) -> GuidedDecisionView:
    """Create one decision surface bound to an existing authority domain."""

    if presentation_state not in GUIDED_DECISION_PRESENTATION_STATES:
        raise GuidedWorkflowValidationError(
            "presentation_state is not supported."
        )
    alternative_tuple = tuple(alternatives)
    if any(
        not isinstance(item, GuidedDecisionAlternativeView)
        for item in alternative_tuple
    ):
        raise GuidedWorkflowValidationError(
            "alternatives must contain GuidedDecisionAlternativeView values."
        )
    _require_unique(
        (item.alternative_key for item in alternative_tuple),
        "alternative_key",
    )

    if presentation_state == "required" and not alternative_tuple:
        raise GuidedWorkflowValidationError(
            "A required decision must expose at least one alternative."
        )

    return GuidedDecisionView(
        decision_key=_stable_entity_id(decision_key, "decision_key"),
        subject=_text(subject, "subject"),
        prompt=_text(prompt, "prompt"),
        presentation_state=presentation_state,
        authority_domain=_text(authority_domain, "authority_domain"),
        target_entity_id=_stable_entity_id(
            target_entity_id,
            "target_entity_id",
        ),
        alternatives=alternative_tuple,
    )


def create_comparison_view(
    *,
    subject: GuidedEngineeringContentView,
    persona_results: Iterable[GuidedPersonaResultView],
    variance: GuidedVarianceView,
    decision: GuidedDecisionView | None = None,
) -> GuidedComparisonView:
    """Create one side-by-side comparison with one vote per Persona."""

    if not isinstance(subject, GuidedEngineeringContentView):
        raise GuidedWorkflowValidationError(
            "subject must be GuidedEngineeringContentView."
        )
    if not isinstance(variance, GuidedVarianceView):
        raise GuidedWorkflowValidationError(
            "variance must be GuidedVarianceView."
        )
    if decision is not None and not isinstance(decision, GuidedDecisionView):
        raise GuidedWorkflowValidationError(
            "decision must be GuidedDecisionView or None."
        )

    persona_tuple = tuple(persona_results)
    if not persona_tuple:
        raise GuidedWorkflowValidationError(
            "A comparison requires at least one Persona result."
        )
    if any(
        not isinstance(item, GuidedPersonaResultView)
        for item in persona_tuple
    ):
        raise GuidedWorkflowValidationError(
            "persona_results must contain GuidedPersonaResultView values."
        )

    _require_unique(
        (item.persona_id for item in persona_tuple),
        "persona_id",
    )

    if variance.total_personas != len(persona_tuple):
        raise GuidedWorkflowValidationError(
            "variance.total_personas must equal the number of distinct Persona columns."
        )

    persona_ids = {item.persona_id for item in persona_tuple}
    represented = (
        set(variance.supporting_personas)
        | set(variance.dissenting_personas)
        | set(variance.omitting_personas)
    )
    if not represented.issubset(persona_ids):
        raise GuidedWorkflowValidationError(
            "Variance references a Persona not present in the comparison."
        )

    return GuidedComparisonView(
        subject=subject,
        persona_results=persona_tuple,
        variance=variance,
        decision=decision,
    )


def create_stage_view(
    *,
    stage_id: str,
    presentation_status: str,
    semantic: str,
    summary: str,
    decision_count: int = 0,
    variance_attention_count: int = 0,
    blocking_issue_count: int = 0,
    action_label: str | None = None,
    target_entity_id: str | None = None,
) -> GuidedWorkflowStageView:
    """Create one presentation-only workflow stage."""

    if stage_id not in GUIDED_WORKFLOW_STAGE_IDS:
        raise GuidedWorkflowValidationError(
            "stage_id is not supported."
        )
    if presentation_status not in GUIDED_WORKFLOW_PRESENTATION_STATUSES:
        raise GuidedWorkflowValidationError(
            "presentation_status is not supported."
        )
    if semantic not in GUIDED_PRESENTATION_SEMANTICS:
        raise GuidedWorkflowValidationError(
            "semantic is not supported."
        )

    return GuidedWorkflowStageView(
        stage_id=stage_id,
        label=GUIDED_WORKFLOW_STAGE_LABELS[stage_id],
        presentation_status=presentation_status,
        semantic=semantic,
        summary=_text(summary, "summary"),
        decision_count=_nonnegative_int(
            decision_count,
            "decision_count",
        ),
        variance_attention_count=_nonnegative_int(
            variance_attention_count,
            "variance_attention_count",
        ),
        blocking_issue_count=_nonnegative_int(
            blocking_issue_count,
            "blocking_issue_count",
        ),
        action_label=_optional_text(action_label, "action_label"),
        target_entity_id=(
            None
            if target_entity_id is None
            else _stable_entity_id(
                target_entity_id,
                "target_entity_id",
            )
        ),
    )


def build_guided_workflow_view(
    *,
    project_id: str,
    stages: Iterable[GuidedWorkflowStageView],
    confirmed_result_count: int = 0,
) -> GuidedWorkflowView:
    """Build the complete non-authoritative workflow projection."""

    if not is_valid_project_id(project_id):
        raise GuidedWorkflowValidationError(
            "project_id must contain exactly six digits."
        )

    stage_tuple = tuple(stages)
    if any(
        not isinstance(item, GuidedWorkflowStageView)
        for item in stage_tuple
    ):
        raise GuidedWorkflowValidationError(
            "stages must contain GuidedWorkflowStageView values."
        )

    actual_ids = tuple(item.stage_id for item in stage_tuple)
    if actual_ids != GUIDED_WORKFLOW_STAGE_IDS:
        raise GuidedWorkflowValidationError(
            "stages must contain all Guided Workflow stages exactly once and in canonical order."
        )

    confirmed_result_count = _nonnegative_int(
        confirmed_result_count,
        "confirmed_result_count",
    )

    work_summary = EngineerWorkSummary(
        decisions_required=sum(
            item.decision_count for item in stage_tuple
        ),
        variance_attention_count=sum(
            item.variance_attention_count for item in stage_tuple
        ),
        blocking_issue_count=sum(
            item.blocking_issue_count for item in stage_tuple
        ),
        confirmed_result_count=confirmed_result_count,
        completed_stage_count=sum(
            1
            for item in stage_tuple
            if item.presentation_status == "complete"
        ),
    )

    next_stage = _next_stage(stage_tuple)

    return GuidedWorkflowView(
        project_id=project_id,
        work_summary=work_summary,
        stages=stage_tuple,
        next_stage_id=(
            None if next_stage is None else next_stage.stage_id
        ),
        next_action=(
            None
            if next_stage is None
            else (
                next_stage.action_label
                or f"Open {next_stage.label}"
            )
        ),
    )


def _next_stage(
    stages: tuple[GuidedWorkflowStageView, ...],
) -> GuidedWorkflowStageView | None:
    """Select presentation priority without creating workflow authority."""

    with_decision = next(
        (item for item in stages if item.decision_count > 0),
        None,
    )
    if with_decision is not None:
        return with_decision

    with_blocker = next(
        (item for item in stages if item.blocking_issue_count > 0),
        None,
    )
    if with_blocker is not None:
        return with_blocker

    for status in (
        "action_required",
        "in_progress",
        "ready",
        "not_started",
    ):
        candidate = next(
            (
                item
                for item in stages
                if item.presentation_status == status
            ),
            None,
        )
        if candidate is not None:
            return candidate

    return None


def _variance_semantic(
    *,
    consensus_level: str,
    variance_level: str,
) -> str:
    if consensus_level in {"incomplete", "incomparable"}:
        return "neutral"
    if consensus_level == "unanimous" and variance_level == "low":
        return "positive"
    if variance_level == "high" or consensus_level == "none":
        return "blocking"
    if consensus_level in {"majority", "single"}:
        return "attention"
    if variance_level == "medium":
        return "attention"
    return "informational"


def _variance_label(
    *,
    consensus_level: str,
    supporting_count: int,
    total_personas: int,
) -> str:
    title = {
        "unanimous": "Unanimous",
        "majority": "Majority",
        "single": "Single perspective",
        "none": "No consensus",
        "incomparable": "Incomparable",
        "incomplete": "Incomplete",
    }[consensus_level]

    if consensus_level in {"unanimous", "majority", "single"}:
        return (
            f"{title} · {supporting_count} / "
            f"{total_personas} Personas agree"
        )

    return title


def _variance_explanation(
    *,
    consensus_level: str,
    variance_level: str,
    review_required: bool,
) -> str:
    base = (
        f"Consensus: {consensus_level}. "
        f"Variance: {variance_level}."
    )
    if review_required:
        return base + " Human review is required."
    return base + " No additional review is indicated by this presentation."


def _persona_tuple(
    values: Iterable[str],
    field_name: str,
) -> tuple[str, ...]:
    result = tuple(
        _stable_entity_id(item, field_name)
        for item in values
    )
    _require_unique(result, field_name)
    return result


def _stable_entity_id(value: str, field_name: str) -> str:
    if (
        not isinstance(value, str)
        or _ENTITY_ID_PATTERN.fullmatch(value) is None
    ):
        raise GuidedWorkflowValidationError(
            f"{field_name} must be a stable identifier and must not contain a filesystem path."
        )
    return value


def _text(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise GuidedWorkflowValidationError(
            f"{field_name} must be a non-empty string."
        )
    return value


def _optional_text(
    value: str | None,
    field_name: str,
) -> str | None:
    if value is None:
        return None
    return _text(value, field_name)


def _boolean(value: bool, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise GuidedWorkflowValidationError(
            f"{field_name} must be boolean."
        )
    return value


def _nonnegative_int(value: int, field_name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise GuidedWorkflowValidationError(
            f"{field_name} must be an integer."
        )
    if value < 0:
        raise GuidedWorkflowValidationError(
            f"{field_name} must not be negative."
        )
    return value


def _require_unique(
    values: Iterable[str],
    field_name: str,
) -> None:
    items = tuple(values)
    if len(set(items)) != len(items):
        raise GuidedWorkflowValidationError(
            f"{field_name} values must be unique."
        )
