"""Public API tests for Review finalization validation."""

from __future__ import annotations

import modules.review_workspace as review_workspace


def test_finalization_validation_is_publicly_importable() -> None:
    assert (
        review_workspace
        .ReviewFinalizationItemSnapshot
        is not None
    )
    assert (
        review_workspace
        .ReviewFinalizationValidationAssessment
        is not None
    )

    assert callable(
        review_workspace
        .assess_review_document_finalization
    )
    assert callable(
        review_workspace
        .create_review_document_finalization_target
    )
    assert callable(
        review_workspace
        .calculate_review_finalization_validation_fingerprint
    )
    assert callable(
        review_workspace
        .validate_review_finalization_assessment
    )


def test_finalization_validation_constants_are_public() -> None:
    assert (
        review_workspace
        .REVIEW_FINALIZATION_VALIDATION_SCHEMA_VERSION
        == "1.0.0"
    )
    assert (
        review_workspace
        .FINALIZATION_BLOCKING_OUTCOMES
        == frozenset(
            {
                "open",
                "unresolved",
            }
        )
    )


def test_finalization_validation_exports_are_declared() -> None:
    required_exports = {
        "FINALIZATION_BLOCKING_OUTCOMES",
        "REVIEW_FINALIZATION_VALIDATION_SCHEMA_VERSION",
        "ReviewFinalizationItemSnapshot",
        "ReviewFinalizationValidationAssessment",
        "assess_review_document_finalization",
        "calculate_review_finalization_validation_fingerprint",
        "create_review_document_finalization_target",
        "validate_review_finalization_assessment",
    }

    assert required_exports <= set(
        review_workspace.__all__
    )
