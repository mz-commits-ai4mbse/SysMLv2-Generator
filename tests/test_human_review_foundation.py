"""Tests for Human Review identifiers and immutable foundation types."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, fields

import pytest

from modules.human_review.errors import (
    HumanReviewDecisionIdAllocationError,
    HumanReviewError,
    HumanReviewIntegrityError,
    HumanReviewPersistenceError,
    HumanReviewReferenceError,
    HumanReviewValidationError,
    TokenBudgetError,
    TokenBudgetExceededError,
    TokenBudgetValidationError,
    TokenEstimationError,
)
from modules.human_review.identifiers import (
    MAX_HUMAN_REVIEW_DECISION_SEQUENCE,
    MIN_HUMAN_REVIEW_DECISION_SEQUENCE,
    format_human_review_decision_id,
    human_review_decision_id_sequence,
    is_valid_human_review_decision_id,
    next_human_review_decision_id,
    validate_human_review_decision_id,
)
from modules.human_review.types import (
    HUMAN_REVIEW_DECISIONS,
    HUMAN_REVIEW_MODES,
    HUMAN_REVIEW_TARGET_TYPES,
    REFERENCE_VALIDATION_STATUSES,
    TOKEN_BUDGET_CATEGORIES,
    HumanReviewDecision,
    HumanReviewIssue,
    HumanReviewScanResult,
    HumanReviewTargetSnapshot,
    TokenBudgetAllocation,
    TokenBudgetAssessment,
    TokenBudgetContextItem,
    TokenBudgetPolicy,
)


def test_error_hierarchy_is_explicit() -> None:
    review_errors = (
        HumanReviewValidationError,
        HumanReviewIntegrityError,
        HumanReviewReferenceError,
        HumanReviewPersistenceError,
        HumanReviewDecisionIdAllocationError,
        TokenBudgetError,
    )
    budget_errors = (
        TokenBudgetValidationError,
        TokenBudgetExceededError,
        TokenEstimationError,
    )

    assert all(
        issubclass(error, HumanReviewError)
        for error in review_errors
    )
    assert all(
        issubclass(error, TokenBudgetError)
        for error in budget_errors
    )


@pytest.mark.parametrize(
    "value",
    (
        "HRD-000001",
        "HRD-123456",
        "HRD-999999",
    ),
)
def test_valid_decision_ids(value: str) -> None:
    assert is_valid_human_review_decision_id(value)
    assert validate_human_review_decision_id(value) == value


@pytest.mark.parametrize(
    "value",
    (
        None,
        1,
        True,
        "",
        "HRD-000000",
        "HRD-00001",
        "HRD-1000000",
        "hrd-000001",
        "HRD_000001",
        " HRD-000001",
        "TMC-000001",
    ),
)
def test_invalid_decision_ids(value: object) -> None:
    assert not is_valid_human_review_decision_id(value)
    with pytest.raises(HumanReviewValidationError):
        validate_human_review_decision_id(value)


@pytest.mark.parametrize(
    ("sequence", "expected"),
    (
        (1, "HRD-000001"),
        (42, "HRD-000042"),
        (999_999, "HRD-999999"),
    ),
)
def test_format_decision_id(
    sequence: int,
    expected: str,
) -> None:
    assert format_human_review_decision_id(sequence) == expected


@pytest.mark.parametrize(
    "sequence",
    (
        None,
        True,
        1.0,
        "1",
        0,
        -1,
        1_000_000,
    ),
)
def test_invalid_decision_sequences(sequence: object) -> None:
    with pytest.raises(HumanReviewValidationError):
        format_human_review_decision_id(sequence)


def test_decision_sequence_reader() -> None:
    assert human_review_decision_id_sequence("HRD-654321") == (
        654_321
    )


def test_sequence_bounds_are_explicit() -> None:
    assert MIN_HUMAN_REVIEW_DECISION_SEQUENCE == 1
    assert MAX_HUMAN_REVIEW_DECISION_SEQUENCE == 999_999


def test_next_id_starts_at_one_and_does_not_reuse_gaps() -> None:
    assert next_human_review_decision_id(()) == "HRD-000001"
    assert next_human_review_decision_id(
        ("HRD-000001", "HRD-000003")
    ) == "HRD-000004"


@pytest.mark.parametrize(
    "occupied",
    (
        "HRD-000001",
        42,
        None,
        ("HRD-000001", "HRD-000001"),
        ("wrong",),
        ("HRD-999999",),
    ),
)
def test_invalid_occupied_ids_are_rejected(
    occupied: object,
) -> None:
    with pytest.raises(HumanReviewDecisionIdAllocationError):
        next_human_review_decision_id(occupied)


def test_review_vocabularies_are_closed() -> None:
    assert HUMAN_REVIEW_TARGET_TYPES == frozenset(
        {
            "information_unit_publication",
            "terminology_mapping_candidate",
            "framework_assignment_candidate",
        }
    )
    assert HUMAN_REVIEW_DECISIONS == frozenset(
        {"confirm", "reject", "request_changes"}
    )
    assert HUMAN_REVIEW_MODES == frozenset(
        {"quick_confirmation", "detailed_review"}
    )
    assert REFERENCE_VALIDATION_STATUSES == frozenset(
        {"valid", "invalid", "not_applicable"}
    )


def test_token_category_priority_is_complete_and_unique() -> None:
    assert TOKEN_BUDGET_CATEGORIES == (
        "instruction_and_schema",
        "information_unit",
        "project_terminology",
        "turing_core",
        "external_reference_concepts",
        "framework_targets",
        "supplementary_context",
    )
    assert len(TOKEN_BUDGET_CATEGORIES) == len(
        set(TOKEN_BUDGET_CATEGORIES)
    )


def test_all_public_data_types_are_frozen_and_slotted() -> None:
    data_types = (
        HumanReviewTargetSnapshot,
        HumanReviewDecision,
        HumanReviewIssue,
        HumanReviewScanResult,
        TokenBudgetPolicy,
        TokenBudgetContextItem,
        TokenBudgetAllocation,
        TokenBudgetAssessment,
    )

    for data_type in data_types:
        assert data_type.__dataclass_params__.frozen
        assert data_type.__slots__


def test_review_target_binds_exact_content_snapshot() -> None:
    names = {
        field.name
        for field in fields(HumanReviewTargetSnapshot)
    }

    assert {
        "target_type",
        "target_id",
        "target_content_fingerprint",
        "reference_validation_status",
        "reference_validation_fingerprint",
    }.issubset(names)


def test_review_decision_contains_no_mutation_result() -> None:
    names = {
        field.name
        for field in fields(HumanReviewDecision)
    }

    assert "decision" in names
    assert "reviewer_identity" in names
    assert "approved_model_id" not in names
    assert "mutated_target" not in names
    assert "published" not in names


def test_token_policy_forbids_silent_required_truncation() -> None:
    names = {
        field.name
        for field in fields(TokenBudgetPolicy)
    }

    assert "block_on_required_context_overflow" in names
    assert (
        "silent_required_context_truncation_allowed"
        in names
    )


def test_context_items_are_traceable_and_content_addressed() -> None:
    names = {
        field.name
        for field in fields(TokenBudgetContextItem)
    }

    assert {
        "category",
        "reference_id",
        "reference_version",
        "content_sha256",
        "required",
        "estimated_tokens",
    }.issubset(names)


def test_assessment_can_block_without_deciding_review() -> None:
    names = {
        field.name
        for field in fields(TokenBudgetAssessment)
    }

    assert {"blocked", "blocked_reason", "context_fits"}.issubset(
        names
    )
    assert "decision" not in names
    assert "confirmed" not in names


def test_frozen_instance_rejects_mutation() -> None:
    target = HumanReviewTargetSnapshot(
        target_type="framework_assignment_candidate",
        target_id="FAC-000001",
        target_content_fingerprint="a" * 64,
        recommended_review_mode="quick_confirmation",
        confirmation_required=True,
        reference_validation_status="valid",
        reference_validation_fingerprint="b" * 64,
    )

    with pytest.raises(FrozenInstanceError):
        target.target_id = "FAC-000002"