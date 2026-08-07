"""Tests for immutable Approved Input lifecycle event manifests."""

from dataclasses import FrozenInstanceError, replace

import pytest

from modules.approved_input.event_manifest import (
    APPROVED_INPUT_EVENT_SCHEMA_VERSION,
    approved_input_event_from_json,
    approved_input_event_to_json,
    calculate_approved_input_event_fingerprint,
    create_approved_input_event,
    validate_approved_input_event,
)
from modules.approved_input.errors import (
    ApprovedInputIntegrityError,
    ApprovedInputValidationError,
)
from modules.approved_input.types import (
    APPROVED_INPUT_EVENT_TYPES,
    ApprovedInputEvent,
)


SHA_A = "a" * 64


def _event(event_type="invalidated"):
    causal = event_type in {"revoked", "superseded"}
    return create_approved_input_event(
        project_id="000001",
        approved_input_event_id="AIE-000001",
        approved_input_id="AIN-000001",
        event_type=event_type,
        reason_code="test_reason",
        rationale=(
            "Human withdrawal rationale."
            if event_type == "revoked"
            else None
        ),
        actor_identity="reviewer@example.com",
        successor_approved_input_id=(
            "AIN-000002" if event_type == "superseded" else None
        ),
        causal_review_document_id=(
            "RVD-000001" if causal else None
        ),
        causal_review_document_version_id=(
            "RVV-000002" if causal else None
        ),
        causal_review_revision_id=(
            "RVR-000002" if causal else None
        ),
        causal_finalization_decision_id=(
            "HRD-000002" if causal else None
        ),
        causal_finalization_decision_fingerprint=(
            SHA_A if causal else None
        ),
        occurred_at="2026-08-07T11:00:00Z",
    )


def test_event_contract_is_frozen_and_closed() -> None:
    event = _event()

    assert APPROVED_INPUT_EVENT_SCHEMA_VERSION == "1.0.0"
    assert APPROVED_INPUT_EVENT_TYPES == frozenset(
        {"invalidated", "revoked", "superseded"}
    )
    assert event.__dataclass_params__.frozen
    assert event.__slots__

    with pytest.raises(FrozenInstanceError):
        event.event_type = "revoked"  # type: ignore[misc]


def test_all_terminal_event_types_validate() -> None:
    for event_type in APPROVED_INPUT_EVENT_TYPES:
        validate_approved_input_event(_event(event_type))


def test_json_round_trip_and_fingerprint_are_exact() -> None:
    event = _event("superseded")
    text = approved_input_event_to_json(event)

    assert text.endswith("\n")
    assert approved_input_event_from_json(text) == event
    assert (
        calculate_approved_input_event_fingerprint(event)
        == event.event_fingerprint
    )


def test_lifecycle_event_must_start_from_active() -> None:
    event = replace(
        _event(),
        previous_authority_state="revoked",
    )

    with pytest.raises(ApprovedInputIntegrityError):
        validate_approved_input_event(event)


def test_revocation_requires_human_rationale() -> None:
    with pytest.raises(ApprovedInputValidationError):
        create_approved_input_event(
            project_id="000001",
            approved_input_event_id="AIE-000001",
            approved_input_id="AIN-000001",
            event_type="revoked",
            reason_code="withdrawn",
            rationale=None,
            actor_identity="reviewer@example.com",
            successor_approved_input_id=None,
            causal_review_document_id="RVD-000001",
            causal_review_document_version_id="RVV-000002",
            causal_review_revision_id="RVR-000002",
            causal_finalization_decision_id="HRD-000002",
            causal_finalization_decision_fingerprint=SHA_A,
            occurred_at="2026-08-07T11:00:00Z",
        )


def test_invalidation_rejects_human_review_causal_binding() -> None:
    event = replace(
        _event(),
        causal_review_document_id="RVD-000001",
    )

    with pytest.raises(ApprovedInputIntegrityError):
        validate_approved_input_event(event)


def test_supersession_requires_distinct_successor() -> None:
    event = replace(
        _event("superseded"),
        successor_approved_input_id="AIN-000001",
    )

    with pytest.raises(ApprovedInputIntegrityError):
        validate_approved_input_event(event)


def test_tampered_event_fingerprint_is_rejected() -> None:
    event = replace(
        _event(),
        reason_code="changed_reason",
    )

    with pytest.raises(ApprovedInputIntegrityError):
        validate_approved_input_event(event)


def test_parser_rejects_unknown_field() -> None:
    text = approved_input_event_to_json(_event())
    tampered = text.replace(
        '  "event_fingerprint":',
        '  "unexpected": true,\n  "event_fingerprint":',
    )

    with pytest.raises(ApprovedInputValidationError):
        approved_input_event_from_json(tampered)
