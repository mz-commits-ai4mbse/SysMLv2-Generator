"""G6 Approved Input promotion and lifecycle traceability read models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from modules.approved_input.promotion_service import (
        ApprovedInputPromotionResult,
    )

    from .workflow_types import ReviewApprovalWorkspaceView


@dataclass(frozen=True, slots=True)
class ReviewApprovedInputEventTrace:
    """One immutable lifecycle event projected for G6 traceability."""

    approved_input_event_id: str
    approved_input_id: str
    event_type: str
    previous_authority_state: str
    next_authority_state: str
    reason_code: str
    rationale: str | None
    actor_identity: str
    successor_approved_input_id: str | None
    causal_review_document_id: str | None
    causal_review_document_version_id: str | None
    causal_review_revision_id: str | None
    causal_finalization_decision_id: str | None
    causal_finalization_decision_fingerprint: str | None
    occurred_at: str
    previous_event_fingerprint: str | None
    event_fingerprint: str


@dataclass(frozen=True, slots=True)
class ReviewApprovedInputTrace:
    """One immutable AIN plus its derived current authority and lineage."""

    approved_input_id: str
    authority_state: str
    approved_input_kind: str
    stable_subject_key: str
    canonical_title: str
    canonical_primary_text: str
    review_document_id: str
    review_document_version_id: str
    review_revision_id: str
    review_item_id: str
    review_item_kind: str
    review_item_fingerprint: str
    finalized_artifact_set_fingerprint: str
    finalization_decision_id: str
    finalization_decision_fingerprint: str
    finalization_validation_fingerprint: str
    source_id: str
    source_sha256: str
    processing_run_id: str
    attempt_id: str
    primary_artifact_id: str
    supporting_artifact_ids: tuple[str, ...]
    proposal_references: tuple[str, ...]
    created_at: str
    manifest_content_fingerprint: str
    latest_event_fingerprint: str | None
    lifecycle_events: tuple[
        ReviewApprovedInputEventTrace,
        ...,
    ]

    @property
    def is_active(self) -> bool:
        return self.authority_state == "active"


@dataclass(frozen=True, slots=True)
class ReviewApprovalPromotionResult:
    """Completed G6 promotion plus freshly reloaded authority traceability."""

    workspace: ReviewApprovalWorkspaceView
    promotion: ApprovedInputPromotionResult
    traceability: tuple[
        ReviewApprovedInputTrace,
        ...,
    ]

    @property
    def created_approved_input_ids(self) -> tuple[str, ...]:
        return self.promotion.created_approved_input_ids

    @property
    def reused_approved_input_ids(self) -> tuple[str, ...]:
        return self.promotion.reused_approved_input_ids

    @property
    def skipped_review_item_ids(self) -> tuple[str, ...]:
        return self.promotion.skipped_review_item_ids

    @property
    def lifecycle_event_ids(self) -> tuple[str, ...]:
        return self.promotion.lifecycle_event_ids
