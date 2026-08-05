"""Tests for deterministic Reviewed Report rendering."""

from __future__ import annotations

from dataclasses import replace

import pytest

from modules.review_workspace.errors import (
    ReviewIntegrityError,
    ReviewValidationError,
)
from modules.review_workspace.reviewed_report_renderer import (
    REVIEWED_REPORT_SCHEMA_VERSION,
    RenderedReviewedReport,
    calculate_reviewed_report_fingerprint,
    create_rendered_reviewed_report,
    reviewed_report_to_markdown,
    validate_rendered_reviewed_report,
    validate_reviewed_report_source_binding,
)

from tests.test_effective_review_decisions_manifest import (
    _decision_set,
)
from tests.test_review_workspace_finalization_validation import (
    _element_item,
    _open_question_item,
    _relationship_item,
)


def _report(*items):
    reviewed_document, revision, decision_set = (
        _decision_set(*items)
    )

    report = create_rendered_reviewed_report(
        reviewed_document,
        decision_set,
    )

    return (
        reviewed_document,
        revision,
        decision_set,
        report,
    )


def test_schema_constant() -> None:
    assert REVIEWED_REPORT_SCHEMA_VERSION == "1.0.0"


def test_create_binds_exact_finalized_artifacts() -> None:
    (
        reviewed_document,
        _,
        decision_set,
        report,
    ) = _report()

    assert report.project_id == reviewed_document.project_id
    assert (
        report.review_document_id
        == reviewed_document.review_document_id
    )
    assert (
        report.review_document_version_id
        == reviewed_document
        .review_document_version_id
    )
    assert (
        report.review_revision_id
        == reviewed_document.review_revision_id
    )
    assert (
        report.finalized_reviewed_document_fingerprint
        == reviewed_document.content_fingerprint
    )
    assert (
        report.effective_decision_set_fingerprint
        == decision_set.content_fingerprint
    )


def test_markdown_ends_with_newline_and_is_fingerprinted() -> None:
    *_, report = _report()

    markdown = reviewed_report_to_markdown(report)

    assert markdown.endswith("\n")
    assert (
        calculate_reviewed_report_fingerprint(markdown)
        == report.content_fingerprint
    )


def test_rendering_is_deterministic() -> None:
    *_, first = _report()
    *_, second = _report()

    assert first.markdown == second.markdown
    assert (
        first.content_fingerprint
        == second.content_fingerprint
    )


def test_summary_contains_exact_outcome_counts() -> None:
    *_, report = _report(
        _element_item(
            review_item_id="RIT-000001",
        ),
        _open_question_item(
            review_item_id="RIT-000002",
        ),
        _element_item(
            review_item_id="RIT-000003",
            outcome="rejected",
        ),
    )

    assert "| `accepted_with_modification` | 1 |" in (
        report.markdown
    )
    assert "| `rejected` | 1 |" in report.markdown
    assert "| `deferred` | 1 |" in report.markdown
    assert "| **Total** | **3** |" in report.markdown


def test_primary_sections_are_rendered() -> None:
    *_, report = _report()

    assert "## Elements\n" in report.markdown
    assert "## Relationships\n" in report.markdown
    assert "## Open Questions\n" in report.markdown
    assert "## Rejected Content\n" in report.markdown


def test_reviewed_item_content_is_rendered() -> None:
    *_, report = _report()

    assert (
        "### RIT-000001 — Preserve traceability"
        in report.markdown
    )
    assert (
        "> The system shall preserve source "
        "traceability."
        in report.markdown
    )
    assert (
        "- Review Outcome: "
        "`accepted_with_modification`"
        in report.markdown
    )


def test_relationship_representation_is_rendered() -> None:
    *_, report = _report(
        _relationship_item(
            review_item_id="RIT-000003",
            outcome="deferred",
        )
    )

    assert "**Relationship Representation**" in (
        report.markdown
    )
    assert "- Semantic Intent: `depends_on`" in (
        report.markdown
    )
    assert "- Validation Status: `unresolved`" in (
        report.markdown
    )


def test_rejected_content_is_derived_from_outcome() -> None:
    *_, report = _report(
        _element_item(
            outcome="rejected",
        )
    )

    rejected_section = report.markdown.split(
        "## Rejected Content",
        1,
    )[1]

    assert "### RIT-000001" in rejected_section
    assert "Rejection Rationale" in rejected_section


def test_empty_rejected_content_is_explicit() -> None:
    *_, report = _report()

    assert "_No rejected Review Items._" in (
        report.markdown
    )


def test_items_are_rendered_in_identifier_order() -> None:
    *_, report = _report(
        _element_item(
            review_item_id="RIT-000002",
        ),
        _element_item(
            review_item_id="RIT-000001",
        ),
    )

    first_position = report.markdown.index(
        "### RIT-000001"
    )
    second_position = report.markdown.index(
        "### RIT-000002"
    )

    assert first_position < second_position


def test_exact_source_binding_is_valid() -> None:
    reviewed_document, _, decision_set, _ = (
        _report()
    )

    validate_reviewed_report_source_binding(
        reviewed_document,
        decision_set,
    )


def test_foreign_decision_set_is_rejected() -> None:
    reviewed_document, _, _, _ = _report(
        _element_item(
            review_item_id="RIT-000001",
        )
    )

    _, _, foreign_decision_set, _ = _report(
        _element_item(
            review_item_id="RIT-000002",
        )
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="exact Finalized Reviewed Document",
    ):
        validate_reviewed_report_source_binding(
            reviewed_document,
            foreign_decision_set,
        )


def test_tampered_markdown_is_rejected() -> None:
    *_, report = _report()

    tampered = replace(
        report,
        markdown=report.markdown + "tampered\n",
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="fingerprint",
    ):
        validate_rendered_reviewed_report(tampered)


def test_missing_final_newline_is_rejected() -> None:
    *_, report = _report()

    markdown = report.markdown.rstrip("\n")
    tampered = replace(
        report,
        markdown=markdown,
        content_fingerprint=(
            calculate_reviewed_report_fingerprint(
                markdown
            )
        ),
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="newline",
    ):
        validate_rendered_reviewed_report(tampered)


def test_fingerprint_argument_is_strict() -> None:
    with pytest.raises(
        ReviewValidationError,
        match="must be a string",
    ):
        calculate_reviewed_report_fingerprint(
            object()
        )


def test_report_argument_is_strict() -> None:
    with pytest.raises(
        ReviewValidationError,
        match="RenderedReviewedReport",
    ):
        validate_rendered_reviewed_report(
            object()
        )


def test_report_type_is_immutable() -> None:
    *_, report = _report()

    assert isinstance(report, RenderedReviewedReport)

    with pytest.raises(AttributeError):
        report.project_id = "000002"
