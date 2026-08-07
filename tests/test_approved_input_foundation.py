"""Tests for Approved Input foundation contracts."""

from __future__ import annotations

from typing import Callable

import pytest

from modules.approved_input.errors import (
    ApprovedInputError,
    ApprovedInputEventIdAllocationError,
    ApprovedInputEventNotFoundError,
    ApprovedInputIdAllocationError,
    ApprovedInputIdentifierAllocationError,
    ApprovedInputIntegrityError,
    ApprovedInputNotFoundError,
    ApprovedInputPersistenceError,
    ApprovedInputRecoveryRequiredError,
    ApprovedInputReferenceError,
    ApprovedInputValidationError,
    UnsafeApprovedInputPathError,
)
from modules.approved_input.identifiers import (
    MAX_APPROVED_INPUT_IDENTIFIER_SEQUENCE,
    MIN_APPROVED_INPUT_IDENTIFIER_SEQUENCE,
    approved_input_event_id_sequence,
    approved_input_id_sequence,
    format_approved_input_event_id,
    format_approved_input_id,
    is_valid_approved_input_event_id,
    is_valid_approved_input_id,
    next_approved_input_event_id,
    next_approved_input_id,
    validate_approved_input_event_id,
    validate_approved_input_id,
)
from modules.approved_input.types import (
    APPROVED_INPUT_AUTHORITY_STATES,
    APPROVED_INPUT_KINDS,
    INITIAL_APPROVED_INPUT_AUTHORITY_STATE,
)


Validator = Callable[[object], str]
ValidityChecker = Callable[[object], bool]
Formatter = Callable[[object], str]
SequenceReader = Callable[[object], int]
Allocator = Callable[[object], str]


_IDENTIFIER_CASES = (
    (
        "AIN",
        is_valid_approved_input_id,
        validate_approved_input_id,
        format_approved_input_id,
        approved_input_id_sequence,
        next_approved_input_id,
        ApprovedInputIdAllocationError,
    ),
    (
        "AIE",
        is_valid_approved_input_event_id,
        validate_approved_input_event_id,
        format_approved_input_event_id,
        approved_input_event_id_sequence,
        next_approved_input_event_id,
        ApprovedInputEventIdAllocationError,
    ),
)


def test_error_hierarchy_is_explicit() -> None:
    direct_errors = (
        ApprovedInputValidationError,
        ApprovedInputIntegrityError,
        ApprovedInputReferenceError,
        ApprovedInputPersistenceError,
        ApprovedInputIdentifierAllocationError,
        UnsafeApprovedInputPathError,
    )

    assert all(
        issubclass(error, ApprovedInputError)
        for error in direct_errors
    )

    assert issubclass(
        ApprovedInputNotFoundError,
        ApprovedInputReferenceError,
    )
    assert issubclass(
        ApprovedInputEventNotFoundError,
        ApprovedInputReferenceError,
    )

    assert issubclass(
        ApprovedInputIdAllocationError,
        ApprovedInputIdentifierAllocationError,
    )
    assert issubclass(
        ApprovedInputEventIdAllocationError,
        ApprovedInputIdentifierAllocationError,
    )

    assert issubclass(
        ApprovedInputRecoveryRequiredError,
        ApprovedInputIntegrityError,
    )


@pytest.mark.parametrize(
    (
        "prefix",
        "is_valid",
        "validator",
        "formatter",
        "sequence_reader",
        "allocator",
        "allocation_error",
    ),
    _IDENTIFIER_CASES,
)
def test_valid_identifiers(
    prefix: str,
    is_valid: ValidityChecker,
    validator: Validator,
    formatter: Formatter,
    sequence_reader: SequenceReader,
    allocator: Allocator,
    allocation_error: type[Exception],
) -> None:
    del allocator
    del allocation_error

    values = (
        f"{prefix}-000001",
        f"{prefix}-123456",
        f"{prefix}-999999",
    )

    for value in values:
        assert is_valid(value)
        assert validator(value) == value

    assert formatter(42) == f"{prefix}-000042"

    assert sequence_reader(
        f"{prefix}-654321"
    ) == 654_321


@pytest.mark.parametrize(
    (
        "prefix",
        "is_valid",
        "validator",
        "formatter",
        "sequence_reader",
        "allocator",
        "allocation_error",
    ),
    _IDENTIFIER_CASES,
)
def test_invalid_identifiers(
    prefix: str,
    is_valid: ValidityChecker,
    validator: Validator,
    formatter: Formatter,
    sequence_reader: SequenceReader,
    allocator: Allocator,
    allocation_error: type[Exception],
) -> None:
    del formatter
    del sequence_reader
    del allocator
    del allocation_error

    invalid_values = (
        None,
        1,
        True,
        "",
        "XXX-000001",
        f"{prefix}-000000",
        f"{prefix}-00001",
        f"{prefix}-1000000",
        f"{prefix.lower()}-000001",
        f"{prefix}_000001",
        f" {prefix}-000001",
    )

    for value in invalid_values:
        assert not is_valid(value)

        with pytest.raises(
            ApprovedInputValidationError
        ):
            validator(value)


@pytest.mark.parametrize(
    (
        "prefix",
        "is_valid",
        "validator",
        "formatter",
        "sequence_reader",
        "allocator",
        "allocation_error",
    ),
    _IDENTIFIER_CASES,
)
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
def test_invalid_identifier_sequences(
    prefix: str,
    is_valid: ValidityChecker,
    validator: Validator,
    formatter: Formatter,
    sequence_reader: SequenceReader,
    allocator: Allocator,
    allocation_error: type[Exception],
    sequence: object,
) -> None:
    del prefix
    del is_valid
    del validator
    del sequence_reader
    del allocator
    del allocation_error

    with pytest.raises(
        ApprovedInputValidationError
    ):
        formatter(sequence)


@pytest.mark.parametrize(
    (
        "prefix",
        "is_valid",
        "validator",
        "formatter",
        "sequence_reader",
        "allocator",
        "allocation_error",
    ),
    _IDENTIFIER_CASES,
)
def test_next_identifier_does_not_reuse_gaps(
    prefix: str,
    is_valid: ValidityChecker,
    validator: Validator,
    formatter: Formatter,
    sequence_reader: SequenceReader,
    allocator: Allocator,
    allocation_error: type[Exception],
) -> None:
    del is_valid
    del validator
    del formatter
    del sequence_reader
    del allocation_error

    assert allocator(()) == f"{prefix}-000001"

    assert allocator(
        (
            f"{prefix}-000001",
            f"{prefix}-000003",
        )
    ) == f"{prefix}-000004"


@pytest.mark.parametrize(
    (
        "prefix",
        "is_valid",
        "validator",
        "formatter",
        "sequence_reader",
        "allocator",
        "allocation_error",
    ),
    _IDENTIFIER_CASES,
)
def test_invalid_occupied_identifiers_are_rejected(
    prefix: str,
    is_valid: ValidityChecker,
    validator: Validator,
    formatter: Formatter,
    sequence_reader: SequenceReader,
    allocator: Allocator,
    allocation_error: type[Exception],
) -> None:
    del is_valid
    del validator
    del formatter
    del sequence_reader

    invalid_inputs = (
        f"{prefix}-000001",
        42,
        None,
        (
            f"{prefix}-000001",
            f"{prefix}-000001",
        ),
        ("wrong",),
        (f"{prefix}-999999",),
    )

    for invalid_input in invalid_inputs:
        with pytest.raises(allocation_error):
            allocator(invalid_input)


def test_identifier_bounds_are_explicit() -> None:
    assert MIN_APPROVED_INPUT_IDENTIFIER_SEQUENCE == 1
    assert (
        MAX_APPROVED_INPUT_IDENTIFIER_SEQUENCE
        == 999_999
    )


def test_approved_input_vocabularies_are_explicit() -> None:
    assert APPROVED_INPUT_KINDS == frozenset(
        {
            "element_statement",
            "relationship_statement",
            "human_clarification",
        }
    )

    assert APPROVED_INPUT_AUTHORITY_STATES == frozenset(
        {
            "active",
            "invalidated",
            "revoked",
            "superseded",
        }
    )

    assert (
        INITIAL_APPROVED_INPUT_AUTHORITY_STATE
        == "active"
    )
