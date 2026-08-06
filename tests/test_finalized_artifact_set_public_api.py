"""Public API tests for finalized Review Artifact Sets."""

from __future__ import annotations

import modules.review_workspace as review_workspace


def test_finalized_artifact_set_types_are_public() -> None:
    assert (
        review_workspace.FinalizedReviewArtifact
        is not None
    )
    assert (
        review_workspace.FinalizedReviewArtifactSet
        is not None
    )


def test_finalized_artifact_set_contract_is_public() -> None:
    assert (
        review_workspace
        .FINALIZED_REVIEW_ARTIFACT_SET_SCHEMA_VERSION
        == "1.0.0"
    )
    assert (
        review_workspace.FINALIZED_REVIEW_ARTIFACT_ORDER
        == (
            "reviewed_document.json",
            "effective_decisions.json",
            "reviewed_report.md",
        )
    )

    functions = (
        review_workspace
        .calculate_finalized_review_artifact_fingerprint,
        review_workspace
        .calculate_finalized_review_artifact_set_fingerprint,
        review_workspace
        .create_finalized_review_artifact_set,
        review_workspace
        .validate_finalized_review_artifact_set,
    )

    assert all(callable(value) for value in functions)


def test_finalized_artifact_set_exports_are_declared() -> None:
    required_exports = {
        "FINALIZED_REVIEW_ARTIFACT_ORDER",
        "FINALIZED_REVIEW_ARTIFACT_SET_SCHEMA_VERSION",
        "FinalizedReviewArtifact",
        "FinalizedReviewArtifactSet",
        "calculate_finalized_review_artifact_fingerprint",
        "calculate_finalized_review_artifact_set_fingerprint",
        "create_finalized_review_artifact_set",
        "validate_finalized_review_artifact_set",
    }

    assert required_exports <= set(
        review_workspace.__all__
    )
