"""Regression coverage for corrected shared-Evidence Human Review usability."""

from modules.review_workspace.shared_evidence_review_adapter import (
    _shared_review_item_kind,
)


def _subject(*information_types):
    return {
        "persona_interpretations": [
            {"information_type": value}
            for value in information_types
        ]
    }


def test_unclassified_consensus_is_not_automatically_an_open_question():
    assert _shared_review_item_kind(
        information_type="unclassified",
        subject=_subject("function", "function", "capability"),
    ) == "element"


def test_unclassified_consensus_preserves_genuine_open_question_majority():
    assert _shared_review_item_kind(
        information_type="unclassified",
        subject=_subject("gap", "ambiguity", "open_question"),
    ) == "open_question"


def test_explicit_open_question_type_remains_open_question():
    assert _shared_review_item_kind(
        information_type="open_question",
        subject=_subject("function", "function", "function"),
    ) == "open_question"


def test_unclassified_without_interpretation_types_fails_to_element_not_question():
    assert _shared_review_item_kind(
        information_type="unclassified",
        subject={"persona_interpretations": []},
    ) == "element"
