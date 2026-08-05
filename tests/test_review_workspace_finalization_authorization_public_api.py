"""Public API tests for Review finalization authorization."""

from __future__ import annotations

import modules.review_workspace as review_workspace


def test_finalization_authorization_is_publicly_importable() -> None:
    assert (
        review_workspace
        .ReviewFinalizationAuthorization
        is not None
    )
    assert (
        review_workspace
        .AuthorizedReviewDocumentFinalization
        is not None
    )

    assert callable(
        review_workspace
        .authorize_review_document_finalization
    )
    assert callable(
        review_workspace
        .authorize_persisted_review_document_finalization
    )
    assert callable(
        review_workspace
        .calculate_review_finalization_authorization_fingerprint
    )
    assert callable(
        review_workspace
        .validate_review_finalization_authorization
    )


def test_finalization_authorization_schema_is_public() -> None:
    assert (
        review_workspace
        .REVIEW_FINALIZATION_AUTHORIZATION_SCHEMA_VERSION
        == "1.0.0"
    )


def test_finalization_authorization_exports_are_declared() -> None:
    required_exports = {
        "REVIEW_FINALIZATION_AUTHORIZATION_SCHEMA_VERSION",
        "AuthorizedReviewDocumentFinalization",
        "ReviewFinalizationAuthorization",
        "authorize_persisted_review_document_finalization",
        "authorize_review_document_finalization",
        "calculate_review_finalization_authorization_fingerprint",
        "validate_review_finalization_authorization",
    }

    assert required_exports <= set(
        review_workspace.__all__
    )
