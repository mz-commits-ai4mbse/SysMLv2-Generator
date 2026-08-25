import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pytest

from modules.target_model_formulation.authority import (
    create_formulation_authority_set,
    create_formulation_decision,
)
from modules.target_model_formulation.errors import TargetModelFormulationError
from modules.target_model_formulation.contract import (
    create_formulation_review,
    create_review_item,
)
from target_model_formulation_authority_helpers import (
    review_four,
    unresolved_candidate,
)


def decision(review, number, subject, candidate, supersedes=None):
    return create_formulation_decision(
        review=review,
        decision_id=f"TFD-{number:06d}",
        authority_subject_id=subject,
        selected_candidate_id=candidate,
        reviewer_identity="MZ",
        rationale="Human-reviewed Target-Model Formulation decision.",
        decided_at="2026-08-25T14:00:00Z",
        supersedes_decision_id=supersedes,
    )


def test_decision_binds_exact_review_item_and_candidate():
    review = review_four()
    value = decision(review, 1, "IME-000001", "TFC-000001")
    assert value.review_id == "TFR-000001"
    assert value.review_fingerprint == review.content_fingerprint
    assert value.review_item_fingerprint == review.items[0].content_fingerprint
    assert value.selected_candidate_fingerprint == review.items[0].candidates[0].content_fingerprint
    assert value.selected_relevance_outcome == "materialize_formally"
    assert value.selected_target_notation_construct_id == "TN_003"


def test_candidate_must_belong_to_exact_review_item():
    review = review_four()
    with pytest.raises(TargetModelFormulationError, match="not uniquely present"):
        decision(review, 1, "IME-000001", "TFC-000003")


def test_unresolved_candidate_cannot_be_final_human_authority():
    base = review_four()
    item = create_review_item(
        subject_kind="element",
        authority_subject_id="IME-000099",
        current_engineering_type="stakeholder",
        current_target_representation="stakeholder",
        candidates=(unresolved_candidate("TFC-000099"),),
    )
    review = create_formulation_review(
        project_id=base.project_id,
        review_id="TFR-000002",
        source_internal_engineering_model_id=base.source_internal_engineering_model_id,
        source_internal_engineering_model_fingerprint=base.source_internal_engineering_model_fingerprint,
        final_model_review_decision_id=base.final_model_review_decision_id,
        final_model_review_decision_fingerprint=base.final_model_review_decision_fingerprint,
        target_model_profile_id=base.target_model_profile_id,
        target_model_profile_version=base.target_model_profile_version,
        target_model_profile_fingerprint=base.target_model_profile_fingerprint,
        target_notation_fingerprint=base.target_notation_fingerprint,
        items=(item,),
        created_at="2026-08-25T13:55:00Z",
    )
    with pytest.raises(TargetModelFormulationError, match="cannot be Human-authorized"):
        decision(review, 1, "IME-000099", "TFC-000099")


def test_authority_set_requires_every_review_item_exactly_once():
    review = review_four()
    values = (
        decision(review, 1, "IME-000001", "TFC-000001"),
        decision(review, 2, "IME-000003", "TFC-000002"),
        decision(review, 3, "IMR-000001", "TFC-000003"),
    )
    with pytest.raises(TargetModelFormulationError, match="cover every review item"):
        create_formulation_authority_set(
            review=review,
            authority_set_id="TFA-000001",
            effective_decisions=values,
            created_at="2026-08-25T14:05:00Z",
        )


def test_complete_authority_set_preserves_formal_and_nonmaterialized_outcomes():
    review = review_four()
    values = (
        decision(review, 1, "IME-000001", "TFC-000001"),
        decision(review, 2, "IME-000003", "TFC-000002"),
        decision(review, 3, "IMR-000001", "TFC-000003"),
        decision(review, 4, "IMR-000003", "TFC-000004"),
    )
    authority = create_formulation_authority_set(
        review=review,
        authority_set_id="TFA-000001",
        effective_decisions=values,
        created_at="2026-08-25T14:05:00Z",
    )
    assert authority.source_internal_engineering_model_id == "IEM-000001"
    assert authority.final_model_review_decision_id == "FAD-000001"
    assert [d.selected_relevance_outcome for d in authority.effective_decisions] == [
        "materialize_formally",
        "materialize_formally",
        "intentionally_not_materialized",
        "intentionally_not_materialized",
    ]
