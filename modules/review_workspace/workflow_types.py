"""Read models for the G6 Human Review and Approval workflow."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from .types import (
    ReviewDocument,
    ReviewDocumentVersion,
    ReviewRevision,
    ScopedReviewAction,
)

if TYPE_CHECKING:
    from modules.approved_input.eligibility import (
        ApprovedInputPromotionEligibilityAssessment,
    )
    from modules.approved_input.types import (
        ApprovedInputAuthoritySnapshot,
    )
    from modules.human_review.types import HumanReviewDecision

    from .finalization_authorization import (
        ReviewFinalizationAuthorization,
    )
    from .finalization_validation import (
        ReviewFinalizationValidationAssessment,
    )
    from .finalization_workflow import (
        ReviewFinalizationWorkflowPreview,
    )
    from .finalized_artifact_set import (
        FinalizedReviewArtifactSet,
    )


REVIEW_APPROVAL_WORKFLOW_STATUSES = frozenset(
    {
        "awaiting_workspace",
        "draft_review",
        "ready_to_finalize",
        "ready_to_promote",
        "approved_input_available",
        "promotion_blocked",
        "attention_required",
    }
)

REVIEW_APPROVAL_ISSUE_LEVELS = frozenset(
    {
        "warning",
        "blocking",
    }
)


@dataclass(frozen=True, slots=True)
class ReviewApprovalIssue:
    """One safe UI-facing issue without repository filesystem paths."""

    project_id: str
    code: str
    issue_level: str
    source_domain: str
    message: str
    source_id: str | None = None
    processing_run_id: str | None = None
    review_document_id: str | None = None
    review_document_version_id: str | None = None
    approved_input_id: str | None = None


@dataclass(frozen=True, slots=True)
class ReviewApprovalQueueItem:
    """One project-local review workflow entry for the G6 queue."""

    project_id: str
    source_id: str
    original_filename: str
    processing_run_id: str
    attempt_id: str | None
    run_state: str | None
    pending_review: bool
    is_current_processing_run: bool
    review_document_ids: tuple[str, ...]
    review_document_id: str | None
    review_document_version_id: str | None
    version_number: int | None
    version_state: str | None
    head_revision_id: str | None
    review_item_count: int
    review_outcome_counts: tuple[tuple[str, int], ...]
    finalization_eligible: bool | None
    finalization_blocking_issue_codes: tuple[str, ...]
    promotion_eligible: bool | None
    promotion_blocking_issue_codes: tuple[str, ...]
    promotable_review_item_ids: tuple[str, ...]
    active_approved_input_ids: tuple[str, ...]
    inactive_approved_input_ids: tuple[str, ...]
    workflow_status: str
    issue_codes: tuple[str, ...]

    def review_outcome_count(self, outcome: str) -> int:
        """Return the count for one review outcome."""

        return dict(self.review_outcome_counts).get(outcome, 0)


@dataclass(frozen=True, slots=True)
class ReviewApprovalProjectView:
    """Complete deterministic G6 review queue for one Project."""

    project_id: str
    items: tuple[ReviewApprovalQueueItem, ...]
    issues: tuple[ReviewApprovalIssue, ...]

    @property
    def blocking_issue_codes(self) -> tuple[str, ...]:
        """Return deterministic project-level blocking issue codes."""

        return tuple(
            issue.code
            for issue in self.issues
            if issue.issue_level == "blocking"
        )

    @property
    def has_blocking_issues(self) -> bool:
        """Return whether any read-side integrity issue blocks trust."""

        return bool(self.blocking_issue_codes)


@dataclass(frozen=True, slots=True)
class ReviewApprovalWorkspaceView:
    """One exact Review Version plus its G6 authority projections."""

    project_id: str
    document: ReviewDocument
    version: ReviewDocumentVersion
    revision: ReviewRevision
    scoped_actions: tuple[ScopedReviewAction, ...]
    finalization_assessment: (
        ReviewFinalizationValidationAssessment | None
    )
    promotion_assessment: (
        ApprovedInputPromotionEligibilityAssessment | None
    )
    finalization_decisions: tuple[HumanReviewDecision, ...]
    approved_input_authority: tuple[
        ApprovedInputAuthoritySnapshot,
        ...,
    ]
    issues: tuple[ReviewApprovalIssue, ...]

    @property
    def blocking_issue_codes(self) -> tuple[str, ...]:
        """Return blocking issue codes relevant to this workspace."""

        return tuple(
            issue.code
            for issue in self.issues
            if issue.issue_level == "blocking"
        )

    @property
    def has_blocking_issues(self) -> bool:
        """Return whether this workspace has blocking read-side issues."""

        return bool(self.blocking_issue_codes)

    @property
    def can_finalize(self) -> bool:
        """Return whether the exact current draft may enter finalization."""

        return bool(
            self.version.version_state == "draft"
            and self.finalization_assessment is not None
            and self.finalization_assessment.eligible_for_finalization
            and not self.has_blocking_issues
        )

    @property
    def can_promote(self) -> bool:
        """Return whether exact finalized authority is promotable."""

        return bool(
            self.version.version_state == "finalized"
            and self.promotion_assessment is not None
            and self.promotion_assessment.eligible_for_promotion
            and not self.has_blocking_issues
        )

    @property
    def active_approved_input_ids(self) -> tuple[str, ...]:
        """Return active Approved Input IDs for this Review Document."""

        return tuple(
            snapshot.manifest.approved_input_id
            for snapshot in self.approved_input_authority
            if snapshot.authority_state == "active"
        )

@dataclass(frozen=True, slots=True)
class ReviewApprovalWorkspaceOpenResult:
    """Result of opening an existing or creating an initial workspace."""

    created: bool
    workspace: ReviewApprovalWorkspaceView

    @property
    def review_document_id(self) -> str:
        """Return the stable Review Document identity."""

        return self.workspace.document.review_document_id

    @property
    def review_document_version_id(self) -> str:
        """Return the selected Review Document Version identity."""

        return self.workspace.version.review_document_version_id



@dataclass(frozen=True, slots=True)
class ReviewApprovalFinalizationResult:
    """Successful exact G6 finalization and persisted artifact result."""

    workspace: ReviewApprovalWorkspaceView
    preview: ReviewFinalizationWorkflowPreview
    authorization: ReviewFinalizationAuthorization
    artifact_set: FinalizedReviewArtifactSet

    @property
    def finalization_decision_id(self) -> str:
        return self.authorization.human_review_decision_id

    @property
    def artifact_filenames(self) -> tuple[str, ...]:
        return tuple(
            artifact.filename
            for artifact in self.artifact_set.artifacts
        )
