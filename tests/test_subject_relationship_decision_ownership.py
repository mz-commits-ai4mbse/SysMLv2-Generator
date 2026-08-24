"""R4c.5b.4 relationship decision ownership test."""

from modules.review_workspace.workflow_service import (
    _subject_review_has_outgoing_relationship,
)


def test_only_source_card_owns_relationship_decision():
    card = {
        "relationships": [
            {
                "direction": "outgoing",
                "source_subject_id": "SUBJ-000002",
                "relationship_kind": "uses",
                "target_subject_id": "SUBJ-000006",
            },
            {
                "direction": "incoming",
                "source_subject_id": "SUBJ-000004",
                "relationship_kind": "observes",
                "target_subject_id": "SUBJ-000002",
            },
        ]
    }

    assert _subject_review_has_outgoing_relationship(
        card,
        source_subject_id="SUBJ-000002",
        relationship_kind="uses",
        target_subject_id="SUBJ-000006",
    )
    assert not _subject_review_has_outgoing_relationship(
        card,
        source_subject_id="SUBJ-000004",
        relationship_kind="observes",
        target_subject_id="SUBJ-000002",
    )
