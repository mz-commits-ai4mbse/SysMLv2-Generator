"""R4c.5b.3 Subject-centric UI helper tests."""

from types import SimpleNamespace

import pytest

from app.human_subject_review_ui import (
    build_subject_review_item_request,
    canonical_subject_id_from_item,
    subject_review_cards_by_id,
)
from modules.review_workspace.types import ReviewItemContent


def _item():
    return SimpleNamespace(
        review_document_version_id="RVV-000001",
        item_content_fingerprint="a" * 64,
        original_report_locator="subject_review:SUBJ-000001",
        current_content=ReviewItemContent(
            title="Operator",
            primary_text="Operator statement.",
            description=None,
            information_type="actor",
            modality="descriptive",
            epistemic_status="explicit",
            human_rationale=None,
            human_confidence=None,
            relationship_representation=None,
        ),
    )


def test_exact_subject_id_is_recovered_from_review_locator():
    assert canonical_subject_id_from_item(_item()) == "SUBJ-000001"


def test_card_population_must_match_exact_authority_order():
    payload = {
        "canonical_subject_ids": ["SUBJ-000001"],
        "cards": [
            {
                "canonical_subject_id": "SUBJ-000001",
            }
        ],
    }
    assert tuple(subject_review_cards_by_id(payload)) == (
        "SUBJ-000001",
    )

    payload["canonical_subject_ids"] = ["SUBJ-000002"]
    with pytest.raises(ValueError):
        subject_review_cards_by_id(payload)


def test_unchanged_explicit_accept_maps_to_plain_g6_acceptance():
    item = _item()
    request = build_subject_review_item_request(
        item,
        action="accept",
        statement="Operator statement.",
        information_type="actor",
        statement_modality="descriptive",
        epistemic_class="explicit",
        rationale=None,
    )

    assert request.review_outcome == "accepted_as_generated"
    assert request.selected_proposal_keys == ()
    assert request.updated_content == item.current_content


def test_modified_accept_requires_rationale():
    with pytest.raises(ValueError):
        build_subject_review_item_request(
            _item(),
            action="accept",
            statement="Human edited statement.",
            information_type="actor",
            statement_modality="descriptive",
            epistemic_class="explicit",
            rationale=None,
        )


def test_reject_requires_rationale():
    with pytest.raises(ValueError):
        build_subject_review_item_request(
            _item(),
            action="reject",
            rationale=None,
        )
