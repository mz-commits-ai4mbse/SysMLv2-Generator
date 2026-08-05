"""Public API tests for initial Review Document assembly."""

from __future__ import annotations

import modules.review_workspace as review_workspace


def test_review_document_assembly_is_publicly_importable() -> None:
    assert (
        review_workspace
        .InitialReviewDocumentAssembly
        is not None
    )
    assert (
        review_workspace
        .ReviewDocumentEligibilityAssessment
        is not None
    )
    assert callable(
        review_workspace
        .assemble_initial_review_document
    )


def test_review_document_assembly_types_are_distinct() -> None:
    assert (
        review_workspace
        .InitialReviewDocumentAssembly
        is not review_workspace
        .ReviewDocumentEligibilityAssessment
    )


def test_review_document_assembly_exports_are_declared() -> None:
    required_exports = {
        "InitialReviewDocumentAssembly",
        "ReviewDocumentEligibilityAssessment",
        "assemble_initial_review_document",
    }

    assert required_exports <= set(
        review_workspace.__all__
    )
