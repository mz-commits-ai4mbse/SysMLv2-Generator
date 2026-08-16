"""Deterministic Processing and Human Review presentation adapters for WP-10."""

from __future__ import annotations

from dataclasses import dataclass

from .errors import GuidedWorkflowValidationError
from .presentation import create_engineering_content_view, create_proposal_view
from .types import (
    GUIDED_PRESENTATION_SEMANTICS,
    GuidedEngineeringContentView,
    GuidedProposalView,
)

_REVIEW_ATTENTION_OUTCOMES = frozenset({"open", "deferred", "unresolved"})

_PROCESSING_STATUS = {
    None: ("Ready to process", "neutral", "Run processing"),
    "created": ("Processing prepared", "informational", None),
    "running": ("Processing in progress", "informational", None),
    "awaiting_review": (
        "Ready for Human Review",
        "attention",
        "Continue to Human Review",
    ),
    "blocked": ("Processing blocked", "blocking", "Resolve processing issue"),
    "failed": ("Processing failed", "blocking", "Retry processing"),
    "completed": ("Processing complete", "positive", None),
    "superseded": ("Superseded processing result", "neutral", None),
}

_REVIEW_WORKFLOW_STATUS = {
    "awaiting_workspace": (
        "Ready to start review",
        "attention",
        "Start Human Review",
    ),
    "draft_review": (
        "Human Review in progress",
        "attention",
        "Continue review",
    ),
    "ready_to_finalize": (
        "Ready to finalize",
        "attention",
        "Finalize reviewed content",
    ),
    "ready_to_promote": (
        "Ready to promote",
        "attention",
        "Promote Approved Input",
    ),
    "approved_input_available": (
        "Approved Input available",
        "positive",
        None,
    ),
    "promotion_blocked": (
        "Promotion blocked",
        "blocking",
        "Resolve promotion blocker",
    ),
    "attention_required": (
        "Attention required",
        "blocking",
        "Inspect review issue",
    ),
}

_CONSENSUS_PRESENTATION = {
    "full_agreement": ("unanimous", "low", "positive", "Unanimous"),
    "majority_agreement": (
        "majority",
        "medium",
        "attention",
        "Majority agreement",
    ),
    "majority_with_disagreement": (
        "majority",
        "medium",
        "attention",
        "Majority with disagreement",
    ),
    "minority_interpretation": (
        "none",
        "high",
        "blocking",
        "Minority interpretation",
    ),
    "conflict": (
        "none",
        "high",
        "blocking",
        "Conflicting interpretations",
    ),
    "not_available": (
        "incomplete",
        "high",
        "neutral",
        "Consensus not available",
    ),
}


@dataclass(frozen=True, slots=True)
class GuidedProcessingSourceView:
    source_id: str
    filename: str
    source_role: str
    role_label: str
    status_label: str
    semantic: str
    pending_review: bool
    can_start_new: bool
    can_retry: bool
    recovery_required: bool
    next_action: str | None
    processing_run_id: str | None
    attempt_id: str | None
    run_state: str | None
    media_type: str
    size_bytes: int
    sha256: str
    failure_reason: str | None
    blocked_reason: str | None


@dataclass(frozen=True, slots=True)
class GuidedReviewQueueItemView:
    source_filename: str
    status_label: str
    semantic: str
    decisions_required: int
    review_item_count: int
    active_approved_input_count: int
    next_action: str | None
    source_id: str
    processing_run_id: str
    run_state: str | None
    review_document_id: str | None
    review_document_version_id: str | None
    workflow_status: str
    issue_codes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class GuidedReviewPersonaColumn:
    persona_id: str
    persona_label: str
    agent_ids: tuple[str, ...]
    proposals: tuple[GuidedProposalView, ...]


@dataclass(frozen=True, slots=True)
class GuidedReviewVarianceSummary:
    consensus_level: str
    variance_level: str
    semantic: str
    label: str
    consensus_states: tuple[str, ...]
    persona_count: int
    disagreement_state: str


@dataclass(frozen=True, slots=True)
class GuidedReviewItemView:
    subject: GuidedEngineeringContentView
    persona_columns: tuple[GuidedReviewPersonaColumn, ...]
    variance: GuidedReviewVarianceSummary
    decision_required: bool
    decision_label: str
    review_item_id: str
    review_item_kind: str
    review_outcome: str
    lineage_operation: str
    item_content_fingerprint: str
    source_evidence_count: int
    consensus_evidence_count: int
    human_modification_state: str
    evidence_sufficiency_state: str
    relationship_validation_status: str


def build_processing_source_view(source, execution_state) -> GuidedProcessingSourceView:
    source_id = _text(source.source_id, "source.source_id")
    filename = _text(source.original_filename, "source.original_filename")
    source_role = _text(source.source_role, "source.source_role")

    if execution_state is None:
        run_state = None
        processing_run_id = None
        attempt_id = None
        pending_review = False
        can_start_new = True
        can_retry = False
        recovery_required = False
        failure_reason = None
        blocked_reason = None
    else:
        if execution_state.source_id != source_id:
            raise GuidedWorkflowValidationError(
                "Processing state belongs to a different Source."
            )
        run_state = execution_state.run_state
        processing_run_id = execution_state.processing_run_id
        attempt_id = execution_state.attempt_id
        pending_review = bool(execution_state.pending_review)
        can_start_new = bool(execution_state.can_start_new)
        can_retry = bool(execution_state.can_retry)
        recovery_required = bool(execution_state.recovery_required)
        failure_reason = execution_state.failure_reason
        blocked_reason = execution_state.blocked_reason

    if run_state not in _PROCESSING_STATUS:
        raise GuidedWorkflowValidationError(
            f"Unsupported Processing run state: {run_state!r}."
        )

    status_label, semantic, default_action = _PROCESSING_STATUS[run_state]

    if recovery_required:
        status_label = "Recovery required"
        semantic = "blocking"
        next_action = "Resolve recovery issue"
    elif pending_review:
        status_label = "Ready for Human Review"
        semantic = "attention"
        next_action = "Continue to Human Review"
    elif run_state == "failed" and not can_retry:
        next_action = "Inspect processing failure"
    elif run_state is None and not can_start_new:
        status_label = "Processing unavailable"
        semantic = "blocking"
        next_action = None
    else:
        next_action = default_action

    _semantic(semantic)

    return GuidedProcessingSourceView(
        source_id=source_id,
        filename=filename,
        source_role=source_role,
        role_label=_role_label(source_role),
        status_label=status_label,
        semantic=semantic,
        pending_review=pending_review,
        can_start_new=can_start_new,
        can_retry=can_retry,
        recovery_required=recovery_required,
        next_action=next_action,
        processing_run_id=_optional_text(
            processing_run_id,
            "execution_state.processing_run_id",
        ),
        attempt_id=_optional_text(
            attempt_id,
            "execution_state.attempt_id",
        ),
        run_state=run_state,
        media_type=_text(source.media_type, "source.media_type"),
        size_bytes=_nonnegative_int(source.size_bytes, "source.size_bytes"),
        sha256=_text(source.sha256, "source.sha256"),
        failure_reason=_optional_text(
            failure_reason,
            "execution_state.failure_reason",
        ),
        blocked_reason=_optional_text(
            blocked_reason,
            "execution_state.blocked_reason",
        ),
    )


def build_review_queue_item_view(item) -> GuidedReviewQueueItemView:
    workflow_status = _text(item.workflow_status, "item.workflow_status")
    try:
        status_label, semantic, next_action = _REVIEW_WORKFLOW_STATUS[
            workflow_status
        ]
    except KeyError as exc:
        raise GuidedWorkflowValidationError(
            f"Unsupported Human Review workflow status: {workflow_status!r}."
        ) from exc

    counts = dict(item.review_outcome_counts)
    decisions_required = sum(
        _nonnegative_int(counts.get(outcome, 0), f"outcome.{outcome}")
        for outcome in _REVIEW_ATTENTION_OUTCOMES
    )

    if workflow_status == "draft_review" and decisions_required == 0:
        status_label = "Review ready for completion"
        semantic = "positive"
        next_action = "Continue review"

    _semantic(semantic)

    return GuidedReviewQueueItemView(
        source_filename=_text(
            item.original_filename,
            "item.original_filename",
        ),
        status_label=status_label,
        semantic=semantic,
        decisions_required=decisions_required,
        review_item_count=_nonnegative_int(
            item.review_item_count,
            "item.review_item_count",
        ),
        active_approved_input_count=len(
            tuple(item.active_approved_input_ids)
        ),
        next_action=next_action,
        source_id=_text(item.source_id, "item.source_id"),
        processing_run_id=_text(
            item.processing_run_id,
            "item.processing_run_id",
        ),
        run_state=_optional_text(item.run_state, "item.run_state"),
        review_document_id=_optional_text(
            item.review_document_id,
            "item.review_document_id",
        ),
        review_document_version_id=_optional_text(
            item.review_document_version_id,
            "item.review_document_version_id",
        ),
        workflow_status=workflow_status,
        issue_codes=tuple(item.issue_codes),
    )


def build_review_item_view(
    item,
    *,
    proposal_details,
    filter_fact,
) -> GuidedReviewItemView:
    if filter_fact.review_item_id != item.review_item_id:
        raise GuidedWorkflowValidationError(
            "Review filter facts belong to a different Review Item."
        )
    if filter_fact.item_content_fingerprint != item.item_content_fingerprint:
        raise GuidedWorkflowValidationError(
            "Review filter facts do not bind the current Review Item content."
        )

    details = tuple(proposal_details)
    for detail in details:
        if detail.review_item_id != item.review_item_id:
            raise GuidedWorkflowValidationError(
                "A proposal detail belongs to a different Review Item."
            )

    subject = create_engineering_content_view(
        entity_id=item.review_item_id,
        content_kind=item.review_item_kind,
        title=_text(item.current_content.title, "item.current_content.title"),
        primary_text=_text(
            item.current_content.primary_text,
            "item.current_content.primary_text",
        ),
        secondary_text=_optional_text(
            item.current_content.description,
            "item.current_content.description",
        ),
        source_label=None,
        traceability_available=bool(
            item.source_evidence_references
            or item.consensus_evidence_references
        ),
    )

    persona_columns = _persona_columns(details)
    variance = _review_variance(
        filter_fact,
        persona_count=len(persona_columns),
    )
    decision_required = (
        item.effective_review_outcome in _REVIEW_ATTENTION_OUTCOMES
    )

    return GuidedReviewItemView(
        subject=subject,
        persona_columns=persona_columns,
        variance=variance,
        decision_required=decision_required,
        decision_label=(
            "Human decision required"
            if decision_required
            else "Human decision recorded"
        ),
        review_item_id=item.review_item_id,
        review_item_kind=item.review_item_kind,
        review_outcome=item.effective_review_outcome,
        lineage_operation=item.lineage_operation,
        item_content_fingerprint=item.item_content_fingerprint,
        source_evidence_count=len(item.source_evidence_references),
        consensus_evidence_count=len(item.consensus_evidence_references),
        human_modification_state=filter_fact.human_modification_state,
        evidence_sufficiency_state=filter_fact.evidence_sufficiency_state,
        relationship_validation_status=filter_fact.relationship_validation_status,
    )


def _persona_columns(details) -> tuple[GuidedReviewPersonaColumn, ...]:
    grouped = {}

    for detail in details:
        persona_id = _text(detail.persona_id, "detail.persona_id")
        grouped.setdefault(persona_id, []).append(detail)

    columns = []
    for persona_id in sorted(grouped):
        persona_details = grouped[persona_id]
        proposals = tuple(
            create_proposal_view(
                proposal_id=_text(
                    detail.proposal_id,
                    "detail.proposal_id",
                ),
                title=_text(
                    detail.proposed_title,
                    "detail.proposed_title",
                ),
                primary_text=_text(
                    detail.proposed_primary_text,
                    "detail.proposed_primary_text",
                ),
                secondary_text=_optional_text(
                    detail.proposed_description,
                    "detail.proposed_description",
                ),
                confidence=_optional_text(
                    detail.confidence,
                    "detail.confidence",
                ),
                rationale=_optional_text(
                    detail.rationale,
                    "detail.rationale",
                ),
                supporting_evidence_count=len(
                    tuple(detail.supporting_evidence)
                ),
                missing_evidence_count=len(
                    tuple(detail.missing_evidence)
                ),
            )
            for detail in sorted(
                persona_details,
                key=lambda value: (
                    value.proposal_id,
                    value.proposal_key,
                ),
            )
        )
        agent_ids = tuple(
            sorted(
                {
                    _text(detail.agent_id, "detail.agent_id")
                    for detail in persona_details
                }
            )
        )
        columns.append(
            GuidedReviewPersonaColumn(
                persona_id=persona_id,
                persona_label=_humanize_identifier(persona_id),
                agent_ids=agent_ids,
                proposals=proposals,
            )
        )

    return tuple(columns)


def _review_variance(
    filter_fact,
    *,
    persona_count: int,
) -> GuidedReviewVarianceSummary:
    states = tuple(filter_fact.consensus_states)
    if not states:
        states = ("not_available",)

    unsupported = tuple(
        sorted(set(states) - set(_CONSENSUS_PRESENTATION))
    )
    if unsupported:
        raise GuidedWorkflowValidationError(
            "Unsupported Consensus state(s): " + ", ".join(unsupported)
        )

    state = _strongest_consensus_state(states)
    consensus_level, variance_level, semantic, base_label = (
        _CONSENSUS_PRESENTATION[state]
    )

    if state == "full_agreement" and persona_count == 1:
        consensus_level = "incomplete"
        variance_level = "not_assessable"
        semantic = "neutral"
        label = "Single Persona result · agreement cannot be assessed"
    elif state == "full_agreement" and persona_count > 1:
        label = f"Unanimous · {persona_count} Personas agree"
    elif state == "not_available":
        label = base_label
    elif persona_count:
        label = f"{base_label} · {persona_count} Personas compared"
    else:
        label = base_label

    _semantic(semantic)

    return GuidedReviewVarianceSummary(
        consensus_level=consensus_level,
        variance_level=variance_level,
        semantic=semantic,
        label=label,
        consensus_states=states,
        persona_count=persona_count,
        disagreement_state=filter_fact.agent_disagreement_state,
    )


def _strongest_consensus_state(states: tuple[str, ...]) -> str:
    priority = (
        "conflict",
        "minority_interpretation",
        "majority_with_disagreement",
        "majority_agreement",
        "full_agreement",
        "not_available",
    )
    state_set = set(states)
    for candidate in priority:
        if candidate in state_set:
            return candidate
    raise GuidedWorkflowValidationError(
        "No supported Consensus state is available."
    )


def _role_label(source_role: str) -> str:
    if source_role == "engineering_source":
        return "Engineering source"
    if source_role == "context_only":
        return "Context only"
    return _humanize_identifier(source_role)


def _humanize_identifier(value: str) -> str:
    return value.replace("_", " ").replace("-", " ").strip().title()


def _semantic(value: str) -> str:
    if value not in GUIDED_PRESENTATION_SEMANTICS:
        raise GuidedWorkflowValidationError(
            f"Unsupported presentation semantic: {value!r}."
        )
    return value


def _text(value, field: str) -> str:
    if not isinstance(value, str):
        raise GuidedWorkflowValidationError(f"{field} must be a string.")
    normalized = value.strip()
    if not normalized:
        raise GuidedWorkflowValidationError(f"{field} must not be empty.")
    return normalized


def _optional_text(value, field: str) -> str | None:
    if value is None:
        return None
    return _text(value, field)


def _nonnegative_int(value, field: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise GuidedWorkflowValidationError(
            f"{field} must be a non-negative integer."
        )
    return value
