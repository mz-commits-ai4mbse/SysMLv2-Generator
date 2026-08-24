"""R4c.5c relationship finalization governance tests."""

from types import SimpleNamespace

from modules.subject_review.governance import (
    subject_relationship_finalization_issue_codes,
)


def _payload():
    return {
        "canonical_subject_ids": [
            "SUBJ-000001",
            "SUBJ-000002",
        ],
        "cards": [
            {
                "canonical_subject_id": "SUBJ-000001",
                "content_fingerprint": "a" * 64,
                "relationships": [
                    {
                        "direction": "outgoing",
                        "source_subject_id": "SUBJ-000001",
                        "relationship_kind": "uses",
                        "target_subject_id": "SUBJ-000002",
                    }
                ],
            },
            {
                "canonical_subject_id": "SUBJ-000002",
                "content_fingerprint": "b" * 64,
                "relationships": [
                    {
                        "direction": "incoming",
                        "source_subject_id": "SUBJ-000001",
                        "relationship_kind": "uses",
                        "target_subject_id": "SUBJ-000002",
                    }
                ],
            },
        ],
    }


def _items(target_outcome="accepted_with_modification"):
    return (
        SimpleNamespace(
            original_report_locator="subject_review:SUBJ-000001",
            effective_review_outcome="accepted_with_modification",
        ),
        SimpleNamespace(
            original_report_locator="subject_review:SUBJ-000002",
            effective_review_outcome=target_outcome,
        ),
    )


def _decision(outcome="accepted"):
    return SimpleNamespace(
        decision_id="SRD-000001",
        predecessor_decision_id=None,
        subject_review_card_fingerprint="a" * 64,
        source_subject_id="SUBJ-000001",
        relationship_kind="uses",
        target_subject_id="SUBJ-000002",
        outcome=outcome,
        rationale=None,
        content_fingerprint="c" * 64,
    )


def test_missing_relationship_decision_blocks_finalization():
    issues = subject_relationship_finalization_issue_codes(
        subject_review_payload=_payload(),
        review_items=_items(),
        relationship_decisions=(),
    )
    assert len(issues) == 1
    assert issues[0].startswith(
        "subject_relationship_decision_missing:"
    )


def test_explicit_decision_clears_missing_guard():
    assert subject_relationship_finalization_issue_codes(
        subject_review_payload=_payload(),
        review_items=_items(),
        relationship_decisions=(_decision("deferred"),),
    ) == ()


def test_accepted_relation_requires_approved_endpoints():
    issues = subject_relationship_finalization_issue_codes(
        subject_review_payload=_payload(),
        review_items=_items(target_outcome="rejected"),
        relationship_decisions=(_decision("accepted"),),
    )
    assert len(issues) == 1
    assert issues[0].startswith(
        "subject_relationship_endpoint_not_approved:"
    )
