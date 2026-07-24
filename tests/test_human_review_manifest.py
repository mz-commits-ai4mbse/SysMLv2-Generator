"""Tests for the strict Human Review Decision Manifest."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
import json

import pytest

from modules.human_review.errors import (
    HumanReviewIntegrityError,
    HumanReviewReferenceError,
    HumanReviewValidationError,
)
from modules.human_review.manifest import (
    HUMAN_REVIEW_DECISION_SCHEMA_VERSION,
    calculate_human_review_decision_fingerprint,
    create_human_review_decision,
    create_human_review_target_snapshot,
    human_review_decision_from_json,
    human_review_decision_to_dict,
    human_review_decision_to_json,
    parse_human_review_decision,
    validate_human_review_decision,
)


PROJECT_ID = "318604"
DECISION_ID = "HRD-000001"
TIMESTAMP = "2026-07-24T18:00:00Z"
CONTENT_HASH = "a" * 64
VALIDATION_HASH = "b" * 64


def target(
    *,
    target_type: str = "framework_assignment_candidate",
    target_id: str = "FAC-000001",
    recommended_review_mode: str = "quick_confirmation",
    confirmation_required: bool = True,
    validation_status: str = "valid",
    validation_fingerprint: str | None = VALIDATION_HASH,
):
    return create_human_review_target_snapshot(
        target_type=target_type,
        target_id=target_id,
        target_content_fingerprint=CONTENT_HASH,
        recommended_review_mode=recommended_review_mode,
        confirmation_required=confirmation_required,
        reference_validation_status=validation_status,
        reference_validation_fingerprint=validation_fingerprint,
    )


def decision(**overrides):
    values = {
        "project_id": PROJECT_ID,
        "human_review_decision_id": DECISION_ID,
        "target": target(),
        "review_mode": "quick_confirmation",
        "decision": "confirm",
        "reviewer_identity": "moritz",
        "rationale": None,
        "timestamp": TIMESTAMP,
    }
    values.update(overrides)
    return create_human_review_decision(**values)


def payload(**overrides):
    result = human_review_decision_to_dict(decision())
    result.update(overrides)
    if overrides:
        provisional = dict(result)
        provisional["decision_fingerprint"] = "0" * 64
        from modules.human_review.types import HumanReviewDecision

        if set(provisional) == set(result):
            try:
                parsed_target = create_human_review_target_snapshot(
                    **{
                        "target_type": provisional["target"]["target_type"],
                        "target_id": provisional["target"]["target_id"],
                        "target_content_fingerprint": provisional["target"][
                            "target_content_fingerprint"
                        ],
                        "recommended_review_mode": provisional["target"][
                            "recommended_review_mode"
                        ],
                        "confirmation_required": provisional["target"][
                            "confirmation_required"
                        ],
                        "reference_validation_status": provisional["target"][
                            "reference_validation_status"
                        ],
                        "reference_validation_fingerprint": provisional[
                            "target"
                        ]["reference_validation_fingerprint"],
                    }
                )
                candidate = HumanReviewDecision(
                    schema_version=provisional["schema_version"],
                    project_id=provisional["project_id"],
                    human_review_decision_id=provisional[
                        "human_review_decision_id"
                    ],
                    target=parsed_target,
                    review_mode=provisional["review_mode"],
                    decision=provisional["decision"],
                    reviewer_identity=provisional["reviewer_identity"],
                    rationale=provisional["rationale"],
                    decided_at=provisional["decided_at"],
                    decision_fingerprint="0" * 64,
                )
                result["decision_fingerprint"] = (
                    calculate_human_review_decision_fingerprint(candidate)
                )
            except (KeyError, HumanReviewValidationError):
                pass
    return result


def test_schema_version() -> None:
    assert HUMAN_REVIEW_DECISION_SCHEMA_VERSION == "1.0.0"


def test_create_confirmed_quick_decision() -> None:
    item = decision()
    assert item.project_id == PROJECT_ID
    assert item.target.target_content_fingerprint == CONTENT_HASH
    assert item.decision == "confirm"


def test_types_are_immutable() -> None:
    item = decision()
    with pytest.raises(FrozenInstanceError):
        item.decision = "reject"
    with pytest.raises(FrozenInstanceError):
        item.target.target_id = "FAC-000002"


def test_round_trip_is_deterministic() -> None:
    item = decision()
    text = human_review_decision_to_json(item)
    assert text == human_review_decision_to_json(item)
    assert human_review_decision_from_json(text) == item
    assert text.endswith("\n")


def test_validate_accepts_created_decision() -> None:
    assert validate_human_review_decision(decision()) is None


def test_fingerprint_ignores_record_identity_and_time() -> None:
    first = decision()
    second = replace(
        first,
        human_review_decision_id="HRD-999999",
        decided_at="2026-07-24T19:00:00Z",
    )
    assert calculate_human_review_decision_fingerprint(first) == (
        calculate_human_review_decision_fingerprint(second)
    )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("project_id", "654321"),
        ("review_mode", "detailed_review"),
        ("decision", "reject"),
        ("reviewer_identity", "reviewer-two"),
        ("rationale", "Changed rationale."),
    ],
)
def test_fingerprint_covers_decision_content(field, value) -> None:
    first = decision()
    second = replace(first, **{field: value})
    assert calculate_human_review_decision_fingerprint(first) != (
        calculate_human_review_decision_fingerprint(second)
    )


@pytest.mark.parametrize(
    ("target_type", "target_id"),
    [
        ("information_unit_publication", "IU-000001"),
        ("terminology_mapping_candidate", "TMC-000001"),
        ("framework_assignment_candidate", "FAC-000001"),
    ],
)
def test_supported_target_id_namespaces(target_type, target_id) -> None:
    status = (
        "not_applicable"
        if target_type == "information_unit_publication"
        else "valid"
    )
    fingerprint = None if status == "not_applicable" else VALIDATION_HASH
    item = target(
        target_type=target_type,
        target_id=target_id,
        validation_status=status,
        validation_fingerprint=fingerprint,
    )
    assert item.target_id == target_id


@pytest.mark.parametrize(
    ("target_type", "target_id"),
    [
        ("information_unit_publication", "FAC-000001"),
        ("terminology_mapping_candidate", "IU-000001"),
        ("framework_assignment_candidate", "TMC-000001"),
        ("framework_assignment_candidate", "FAC-1"),
    ],
)
def test_target_id_must_match_target_type(target_type, target_id) -> None:
    with pytest.raises(HumanReviewValidationError):
        target(target_type=target_type, target_id=target_id)


def test_every_target_requires_confirmation() -> None:
    with pytest.raises(HumanReviewIntegrityError):
        target(confirmation_required=False)


@pytest.mark.parametrize(
    "target_type",
    [
        "terminology_mapping_candidate",
        "framework_assignment_candidate",
    ],
)
def test_candidate_requires_validation_fingerprint(target_type) -> None:
    target_id = (
        "TMC-000001"
        if target_type == "terminology_mapping_candidate"
        else "FAC-000001"
    )
    with pytest.raises(HumanReviewIntegrityError):
        target(
            target_type=target_type,
            target_id=target_id,
            validation_fingerprint=None,
        )


def test_not_applicable_is_only_for_information_unit() -> None:
    with pytest.raises(HumanReviewIntegrityError):
        target(
            validation_status="not_applicable",
            validation_fingerprint=None,
        )


def test_information_unit_not_applicable_rejects_fingerprint() -> None:
    with pytest.raises(HumanReviewIntegrityError):
        target(
            target_type="information_unit_publication",
            target_id="IU-000001",
            validation_status="not_applicable",
            validation_fingerprint=VALIDATION_HASH,
        )


def test_detailed_review_is_always_available() -> None:
    item = decision(review_mode="detailed_review")
    assert item.review_mode == "detailed_review"


def test_quick_mode_requires_quick_recommendation() -> None:
    with pytest.raises(HumanReviewIntegrityError):
        decision(
            target=target(
                recommended_review_mode="detailed_review"
            )
        )


def test_quick_mode_rejects_invalid_reference() -> None:
    with pytest.raises(HumanReviewIntegrityError):
        decision(
            target=target(validation_status="invalid")
        )


def test_confirm_rejects_invalid_reference_even_detailed() -> None:
    with pytest.raises(HumanReviewIntegrityError):
        decision(
            target=target(
                recommended_review_mode="detailed_review",
                validation_status="invalid",
            ),
            review_mode="detailed_review",
        )


@pytest.mark.parametrize("selected", ["reject", "request_changes"])
def test_non_confirming_decisions_require_rationale(selected) -> None:
    with pytest.raises(HumanReviewIntegrityError):
        decision(
            decision=selected,
            review_mode="detailed_review",
        )


@pytest.mark.parametrize("selected", ["reject", "request_changes"])
def test_non_confirming_decisions_accept_rationale(selected) -> None:
    item = decision(
        decision=selected,
        review_mode="detailed_review",
        rationale="The target needs human correction.",
    )
    assert item.decision == selected


def test_confirm_may_record_rationale() -> None:
    assert decision(rationale="Reviewed.").rationale == "Reviewed."


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("schema_version", "2.0.0"),
        ("project_id", ""),
        ("human_review_decision_id", "HRD-1"),
        ("review_mode", "automatic"),
        ("decision", "publish"),
        ("reviewer_identity", " "),
        ("rationale", ""),
        ("decided_at", "2026-07-24"),
    ],
)
def test_invalid_top_level_values_are_rejected(field, value) -> None:
    with pytest.raises(
        (HumanReviewValidationError, HumanReviewIntegrityError)
    ):
        parse_human_review_decision(payload(**{field: value}))


def test_invalid_decision_fingerprint_syntax_is_rejected() -> None:
    data = payload()
    data["decision_fingerprint"] = "f" * 63
    with pytest.raises(HumanReviewValidationError):
        parse_human_review_decision(data)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("target_type", "other"),
        ("target_content_fingerprint", "a" * 63),
        ("recommended_review_mode", "automatic"),
        ("confirmation_required", 1),
        ("reference_validation_status", "unknown"),
        ("reference_validation_fingerprint", "b" * 63),
    ],
)
def test_invalid_target_values_are_rejected(field, value) -> None:
    data = payload()
    data["target"][field] = value
    with pytest.raises(
        (HumanReviewValidationError, HumanReviewIntegrityError)
    ):
        parse_human_review_decision(data)


@pytest.mark.parametrize("field", sorted({
    "schema_version",
    "project_id",
    "human_review_decision_id",
    "target",
    "review_mode",
    "decision",
    "reviewer_identity",
    "rationale",
    "decided_at",
    "decision_fingerprint",
}))
def test_missing_top_level_field_is_rejected(field) -> None:
    data = payload()
    del data[field]
    with pytest.raises(HumanReviewValidationError):
        parse_human_review_decision(data)


def test_unknown_top_level_field_is_rejected() -> None:
    data = payload()
    data["automatic_release"] = True
    with pytest.raises(HumanReviewValidationError):
        parse_human_review_decision(data)


def test_unknown_target_field_is_rejected() -> None:
    data = payload()
    data["target"]["automatic_release"] = True
    with pytest.raises(HumanReviewValidationError):
        parse_human_review_decision(data)


def test_non_object_payload_is_rejected() -> None:
    with pytest.raises(HumanReviewValidationError):
        parse_human_review_decision([])


def test_invalid_json_is_rejected() -> None:
    with pytest.raises(HumanReviewValidationError):
        human_review_decision_from_json("{invalid")


def test_non_string_json_is_rejected() -> None:
    with pytest.raises(HumanReviewValidationError):
        human_review_decision_from_json(None)


def test_duplicate_json_key_is_rejected() -> None:
    text = human_review_decision_to_json(decision())
    text = text.replace(
        '"project_id": "318604",',
        '"project_id": "318604",\n  "project_id": "318604",',
    )
    with pytest.raises(HumanReviewValidationError):
        human_review_decision_from_json(text)


def test_tampered_content_fingerprint_is_rejected() -> None:
    data = payload()
    data["target"]["target_content_fingerprint"] = "c" * 64
    with pytest.raises(HumanReviewIntegrityError):
        parse_human_review_decision(data)


def test_expected_project_binding_is_enforced() -> None:
    with pytest.raises(HumanReviewReferenceError):
        human_review_decision_from_json(
            human_review_decision_to_json(decision()),
            expected_project_id="654321",
        )


def test_expected_decision_binding_is_enforced() -> None:
    with pytest.raises(HumanReviewReferenceError):
        human_review_decision_from_json(
            human_review_decision_to_json(decision()),
            expected_human_review_decision_id="HRD-000002",
        )


def test_matching_expected_bindings_are_accepted() -> None:
    item = human_review_decision_from_json(
        human_review_decision_to_json(decision()),
        expected_project_id=PROJECT_ID,
        expected_human_review_decision_id=DECISION_ID,
    )
    assert item.human_review_decision_id == DECISION_ID


def test_serializer_rejects_wrong_type() -> None:
    with pytest.raises(HumanReviewValidationError):
        human_review_decision_to_dict(object())


def test_serializer_revalidates_dataclass() -> None:
    item = replace(decision(), decision_fingerprint="f" * 64)
    with pytest.raises(HumanReviewIntegrityError):
        human_review_decision_to_json(item)


def test_json_is_valid_and_exactly_round_trippable() -> None:
    item = decision()
    raw = json.loads(human_review_decision_to_json(item))
    assert raw == human_review_decision_to_dict(item)