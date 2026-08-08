"""Public API tests for the G6.1 Review Approval workflow."""

from modules.review_workspace import (
    REVIEW_APPROVAL_ISSUE_LEVELS,
    REVIEW_APPROVAL_WORKFLOW_STATUSES,
    ReviewApprovalIssue,
    ReviewApprovalProjectView,
    ReviewApprovalQueueItem,
    ReviewApprovalWorkflowService,
    ReviewApprovalWorkspaceView,
)


def test_g6_1_review_approval_public_api_is_available():
    assert "awaiting_workspace" in REVIEW_APPROVAL_WORKFLOW_STATUSES
    assert "ready_to_finalize" in REVIEW_APPROVAL_WORKFLOW_STATUSES
    assert "ready_to_promote" in REVIEW_APPROVAL_WORKFLOW_STATUSES
    assert "attention_required" in REVIEW_APPROVAL_WORKFLOW_STATUSES
    assert REVIEW_APPROVAL_ISSUE_LEVELS == frozenset({"warning", "blocking"})
    assert ReviewApprovalIssue.__name__ == "ReviewApprovalIssue"
    assert ReviewApprovalQueueItem.__name__ == "ReviewApprovalQueueItem"
    assert ReviewApprovalProjectView.__name__ == "ReviewApprovalProjectView"
    assert ReviewApprovalWorkspaceView.__name__ == "ReviewApprovalWorkspaceView"
    assert ReviewApprovalWorkflowService.__name__ == "ReviewApprovalWorkflowService"
