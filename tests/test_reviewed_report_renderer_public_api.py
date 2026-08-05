"""Public API tests for Reviewed Report rendering."""

from __future__ import annotations

import modules.review_workspace as review_workspace


def test_rendered_reviewed_report_type_is_public() -> None:
    assert (
        review_workspace.RenderedReviewedReport
        is not None
    )


def test_reviewed_report_contract_is_public() -> None:
    assert (
        review_workspace.REVIEWED_REPORT_SCHEMA_VERSION
        == "1.0.0"
    )

    functions = (
        review_workspace
        .calculate_reviewed_report_fingerprint,
        review_workspace.create_rendered_reviewed_report,
        review_workspace.reviewed_report_to_markdown,
        review_workspace
        .validate_rendered_reviewed_report,
        review_workspace
        .validate_reviewed_report_source_binding,
    )

    assert all(callable(value) for value in functions)


def test_reviewed_report_exports_are_declared() -> None:
    required_exports = {
        "REVIEWED_REPORT_SCHEMA_VERSION",
        "RenderedReviewedReport",
        "calculate_reviewed_report_fingerprint",
        "create_rendered_reviewed_report",
        "reviewed_report_to_markdown",
        "validate_rendered_reviewed_report",
        "validate_reviewed_report_source_binding",
    }

    assert required_exports <= set(
        review_workspace.__all__
    )
