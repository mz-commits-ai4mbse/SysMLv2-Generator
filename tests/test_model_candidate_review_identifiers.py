"""Tests for Phase-H Candidate Review Decision identifiers."""

import pytest

from modules.model_candidates import (
    ModelCandidateReviewDecisionIdAllocationError,
    ModelCandidateValidationError,
    format_model_candidate_review_decision_id,
    is_valid_model_candidate_review_decision_id,
    model_candidate_review_decision_id_sequence,
    next_model_candidate_review_decision_id,
    validate_model_candidate_review_decision_id,
)


def test_mcd_identifier_contract():
    assert is_valid_model_candidate_review_decision_id("MCD-000001")
    assert not is_valid_model_candidate_review_decision_id("MCD-000000")
    assert validate_model_candidate_review_decision_id(
        "MCD-999999"
    ) == "MCD-999999"
    assert model_candidate_review_decision_id_sequence(
        "MCD-000042"
    ) == 42
    assert format_model_candidate_review_decision_id(42) == "MCD-000042"


def test_mcd_allocation_uses_highest_and_never_reuses_gap():
    assert next_model_candidate_review_decision_id(
        ("MCD-000001", "MCD-000003")
    ) == "MCD-000004"


def test_mcd_invalid_and_duplicate_occupied_ids_fail():
    with pytest.raises(ModelCandidateReviewDecisionIdAllocationError):
        next_model_candidate_review_decision_id(
            ("MCD-000001", "MCD-000001")
        )
    with pytest.raises(ModelCandidateReviewDecisionIdAllocationError):
        next_model_candidate_review_decision_id(
            ("bad",)
        )


def test_mcd_format_rejects_out_of_range():
    with pytest.raises(ModelCandidateValidationError):
        format_model_candidate_review_decision_id(0)
