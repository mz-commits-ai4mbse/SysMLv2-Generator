"""Tests for exact Review Document finalization decisions."""

from __future__ import annotations

import pytest

import modules.human_review as human_review
from modules.human_review.errors import (
    HumanReviewIntegrityError,
    HumanReviewValidationError,
)
from modules.human_review.manifest import (
    create_human_review_decision,
    create_human_review_target_snapshot,
    human_review_decision_from_json,
    human_review_decision_to_json,
)


PROJECT_ID = "318604"
DECISION_ID = "HRD-000001"
VERSION_ID = "RVV-000001"
TIMESTAMP = "2026-08-05T18:45:00Z"
CONTENT_FINGERPRINT = "a" * 64
VALIDATION_FINGERPRINT = "b" * 64


def _target(**overrides):
    values = {
        "target_type": (
            "review_document_finalization"
        ),
        "target_id": VERSION_ID,
        "target_content_fingerprint": (
            CONTENT_FINGERPRINT
        ),
        "recommended_review_mode": (
            "detailed_review"
        ),
        "confirmation_required": True,
        "reference_validation_status": "valid",
        "reference_validation_fingerprint": (
            VALIDATION_FINGERPRINT
        ),
    }
    values.update(overrides)

    return create_human_review_target_snapshot(
        **values
    )


def _decision(**overrides):
    values = {
        "project_id": PROJECT_ID,
        "human_review_decision_id": DECISION_ID,
        "target": _target(),
        "review_mode": "detailed_review",
        "decision": "confirm",
        "reviewer_identity": "moritz",
        "rationale": None,
        "timestamp": TIMESTAMP,
    }
    values.update(overrides)

    return create_human_review_decision(
        **values
    )


def test_finalization_target_type_is_public() -> None:
    assert (
        "review_document_finalization"
        in human_review.HUMAN_REVIEW_TARGET_TYPES
    )


def test_creates_exact_finalization_target() -> None:
    target = _target()

    assert (
        target.target_type
        == "review_document_finalization"
    )
    assert target.target_id == VERSION_ID
    assert (
        target.target_content_fingerprint
        == CONTENT_FINGERPRINT
    )
    assert (
        target.reference_validation_fingerprint
        == VALIDATION_FINGERPRINT
    )


def test_creates_confirmed_detailed_decision() -> None:
    decision = _decision()

    assert decision.review_mode == "detailed_review"
    assert decision.decision == "confirm"
    assert (
        decision.target.target_id
        == VERSION_ID
    )


@pytest.mark.parametrize(
    "target_id",
    (
        "RVD-000001",
        "RVR-000001",
        "RVV-1",
    ),
)
def test_finalization_requires_version_id(
    target_id: str,
) -> None:
    with pytest.raises(
        HumanReviewValidationError
    ):
        _target(target_id=target_id)


def test_finalization_must_recommend_detailed_review() -> None:
    with pytest.raises(
        HumanReviewIntegrityError,
        match="recommend detailed_review",
    ):
        _target(
            recommended_review_mode=(
                "quick_confirmation"
            )
        )


def test_finalization_requires_detailed_review() -> None:
    with pytest.raises(
        HumanReviewIntegrityError,
        match="requires detailed_review",
    ):
        _decision(
            review_mode="quick_confirmation"
        )


def test_finalization_requires_validation_fingerprint() -> None:
    with pytest.raises(
        HumanReviewIntegrityError,
        match="validation",
    ):
        _target(
            reference_validation_fingerprint=None
        )


def test_invalid_finalization_cannot_be_confirmed() -> None:
    with pytest.raises(
        HumanReviewIntegrityError,
        match="must not be confirmed",
    ):
        _decision(
            target=_target(
                reference_validation_status=(
                    "invalid"
                )
            )
        )


def test_invalid_finalization_may_request_changes() -> None:
    decision = _decision(
        target=_target(
            reference_validation_status="invalid"
        ),
        decision="request_changes",
        rationale=(
            "Blocking finalization findings remain."
        ),
    )

    assert decision.decision == "request_changes"


def test_finalization_decision_round_trip() -> None:
    decision = _decision()
    serialized = human_review_decision_to_json(
        decision
    )

    assert (
        human_review_decision_from_json(
            serialized
        )
        == decision
    )


@pytest.mark.parametrize(
    "changed_target",
    (
        _target(
            target_content_fingerprint="c" * 64
        ),
        _target(
            reference_validation_fingerprint=(
                "d" * 64
            )
        ),
    ),
)
def test_decision_fingerprint_binds_exact_target(
    changed_target,
) -> None:
    original = _decision()
    changed = _decision(
        target=changed_target
    )

    assert (
        original.decision_fingerprint
        != changed.decision_fingerprint
    )
