"""Public API tests for Review Document Version reopening."""

from __future__ import annotations

from modules.review_workspace import (
    ReopenedReviewVersionBundle,
    ReviewWorkspaceRepository,
    create_reopened_review_version_bundle,
    validate_reopened_review_version_bundle,
)


def test_review_reopening_api_is_public() -> None:
    assert ReopenedReviewVersionBundle is not None
    assert callable(
        create_reopened_review_version_bundle
    )
    assert callable(
        validate_reopened_review_version_bundle
    )
    assert callable(
        ReviewWorkspaceRepository
        .reopen_finalized_version
    )
