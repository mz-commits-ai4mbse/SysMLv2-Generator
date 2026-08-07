"""Tests for the Approved Input foundation public API."""

import modules.approved_input as approved_input


def test_foundation_symbols_are_public() -> None:
    expected = {
        "APPROVED_INPUT_AUTHORITY_STATES",
        "APPROVED_INPUT_KINDS",
        "ApprovedInputError",
        "ApprovedInputEventIdAllocationError",
        "ApprovedInputIdAllocationError",
        "ApprovedInputValidationError",
        "INITIAL_APPROVED_INPUT_AUTHORITY_STATE",
        "next_approved_input_event_id",
        "next_approved_input_id",
        "validate_approved_input_event_id",
        "validate_approved_input_id",
    }

    assert expected.issubset(
        set(approved_input.__all__)
    )


def test_public_identifier_contracts_work() -> None:
    assert (
        approved_input.validate_approved_input_id(
            "AIN-000001"
        )
        == "AIN-000001"
    )

    assert (
        approved_input.validate_approved_input_event_id(
            "AIE-000001"
        )
        == "AIE-000001"
    )

    assert (
        approved_input.next_approved_input_id(())
        == "AIN-000001"
    )

    assert (
        approved_input.next_approved_input_event_id(())
        == "AIE-000001"
    )
