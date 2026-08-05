"""Public API tests for Finalized Reviewed Documents."""

from __future__ import annotations

import modules.review_workspace as review_workspace


def test_finalized_reviewed_document_types_are_public() -> None:
    assert (
        review_workspace.FinalizedReviewedDocument
        is not None
    )
    assert (
        review_workspace.FinalizedReviewItemReference
        is not None
    )


def test_finalized_reviewed_document_contract_is_public() -> None:
    assert (
        review_workspace
        .FINALIZED_REVIEWED_DOCUMENT_SCHEMA_VERSION
        == "1.0.0"
    )

    assert (
        review_workspace.FINALIZED_REVIEW_ITEM_OUTCOMES
        == frozenset(
            {
                "accepted_as_generated",
                "accepted_with_modification",
                "combined",
                "rejected",
                "deferred",
                "out_of_scope",
            }
        )
    )

    functions = (
        review_workspace
        .calculate_finalized_reviewed_document_fingerprint,
        review_workspace.create_finalized_reviewed_document,
        review_workspace
        .finalized_reviewed_document_from_json,
        review_workspace
        .finalized_reviewed_document_to_dict,
        review_workspace
        .finalized_reviewed_document_to_json,
        review_workspace.parse_finalized_reviewed_document,
        review_workspace
        .validate_finalized_reviewed_document,
    )

    assert all(callable(value) for value in functions)


def test_finalized_reviewed_document_exports_are_declared() -> None:
    required_exports = {
        "FINALIZED_REVIEWED_DOCUMENT_SCHEMA_VERSION",
        "FINALIZED_REVIEW_ITEM_OUTCOMES",
        "FinalizedReviewItemReference",
        "FinalizedReviewedDocument",
        "calculate_finalized_reviewed_document_fingerprint",
        "create_finalized_reviewed_document",
        "finalized_reviewed_document_from_json",
        "finalized_reviewed_document_to_dict",
        "finalized_reviewed_document_to_json",
        "parse_finalized_reviewed_document",
        "validate_finalized_reviewed_document",
    }

    assert required_exports <= set(
        review_workspace.__all__
    )
