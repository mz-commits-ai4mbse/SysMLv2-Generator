"""R4c.5b.2 Subject Review filter-fact tests."""

from types import SimpleNamespace

from modules.review_workspace.subject_review_artifact_adapter import (
    _subject_review_draft_statement,
)


def test_subject_review_draft_preserves_persona_statement_without_synthesis():
    card = {
        "canonical_label": "Operator",
        "persona_interpretations": [
            {
                "persona_id": "P1",
                "interpreted_statements": [
                    "First exact Persona statement."
                ],
            },
            {
                "persona_id": "P2",
                "interpreted_statements": [
                    "Second exact Persona statement."
                ],
            },
        ],
        "mentions": [],
    }

    assert (
        _subject_review_draft_statement(card)
        == "First exact Persona statement."
    )


def test_subject_review_draft_falls_back_to_exact_mention():
    card = {
        "canonical_label": "Operator",
        "persona_interpretations": [],
        "mentions": [
            {
                "exact_text": "the operator",
            }
        ],
    }

    assert _subject_review_draft_statement(card) == "the operator"
