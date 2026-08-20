"""Focused presentation contract tests for BLK-001 B.1c."""

from types import SimpleNamespace

from app.human_review_item_editor_ui import (
    _items_for_section,
    _resolution_candidate_button_key,
)


def _item(item_id, section, outcome):
    return SimpleNamespace(
        review_item_id=item_id,
        section=section,
        effective_review_outcome=outcome,
    )


def test_resolved_open_questions_leave_primary_open_question_queue():
    items = (
        _item("RIT-000001", "open_questions", "open"),
        _item("RIT-000002", "open_questions", "unresolved"),
        _item("RIT-000003", "open_questions", "deferred"),
        _item(
            "RIT-000004",
            "open_questions",
            "accepted_with_modification",
        ),
        _item("RIT-000005", "open_questions", "out_of_scope"),
    )

    visible = _items_for_section(
        items,
        "open_questions",
    )

    assert tuple(
        item.review_item_id
        for item in visible
    ) == (
        "RIT-000001",
        "RIT-000002",
        "RIT-000003",
    )


def test_resolution_candidate_button_keys_are_scoped_by_open_question():
    first = _resolution_candidate_button_key(
        selection_key=(
            "human_review_item_editor.endpoint.target.RIT-000010"
        ),
        endpoint_role="target",
        review_item_id="RIT-000003",
    )
    second = _resolution_candidate_button_key(
        selection_key=(
            "human_review_item_editor.endpoint.target.RIT-000011"
        ),
        endpoint_role="target",
        review_item_id="RIT-000003",
    )
    repeat = _resolution_candidate_button_key(
        selection_key=(
            "human_review_item_editor.endpoint.target.RIT-000010"
        ),
        endpoint_role="target",
        review_item_id="RIT-000003",
    )

    assert first != second
    assert first == repeat
