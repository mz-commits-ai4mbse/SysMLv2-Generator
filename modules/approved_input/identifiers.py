"""Stable project-local identifiers for Approved Input."""

from __future__ import annotations

from collections.abc import Iterable
import re
from typing import Callable, Pattern

from .errors import (
    ApprovedInputEventIdAllocationError,
    ApprovedInputIdAllocationError,
    ApprovedInputIdentifierAllocationError,
    ApprovedInputValidationError,
)


APPROVED_INPUT_ID_PATTERN = re.compile(
    r"^AIN-([0-9]{6})$"
)
APPROVED_INPUT_EVENT_ID_PATTERN = re.compile(
    r"^AIE-([0-9]{6})$"
)

MIN_APPROVED_INPUT_IDENTIFIER_SEQUENCE = 1
MAX_APPROVED_INPUT_IDENTIFIER_SEQUENCE = 999_999


def is_valid_approved_input_id(value: object) -> bool:
    """Return whether value is a valid Approved Input ID."""

    return _is_valid_identifier(
        value,
        pattern=APPROVED_INPUT_ID_PATTERN,
    )


def validate_approved_input_id(value: object) -> str:
    """Validate and return one Approved Input ID."""

    return _validate_identifier(
        value,
        pattern=APPROVED_INPUT_ID_PATTERN,
        label="approved_input_id",
        prefix="AIN",
    )


def approved_input_id_sequence(value: object) -> int:
    """Return the sequence represented by an Approved Input ID."""

    return _identifier_sequence(
        value,
        validator=validate_approved_input_id,
        prefix="AIN",
    )


def format_approved_input_id(sequence: object) -> str:
    """Format one sequence as an Approved Input ID."""

    return _format_identifier(
        sequence,
        prefix="AIN",
        label="Approved Input ID",
    )


def next_approved_input_id(
    occupied_identifiers: Iterable[str],
) -> str:
    """Return the next Approved Input ID without reusing gaps."""

    return _next_identifier(
        occupied_identifiers,
        sequence_reader=approved_input_id_sequence,
        formatter=format_approved_input_id,
        allocation_error=ApprovedInputIdAllocationError,
        label="Approved Input",
    )


def is_valid_approved_input_event_id(
    value: object,
) -> bool:
    """Return whether value is a valid Approved Input Event ID."""

    return _is_valid_identifier(
        value,
        pattern=APPROVED_INPUT_EVENT_ID_PATTERN,
    )


def validate_approved_input_event_id(
    value: object,
) -> str:
    """Validate and return one Approved Input Event ID."""

    return _validate_identifier(
        value,
        pattern=APPROVED_INPUT_EVENT_ID_PATTERN,
        label="approved_input_event_id",
        prefix="AIE",
    )


def approved_input_event_id_sequence(
    value: object,
) -> int:
    """Return the sequence represented by an Approved Input Event ID."""

    return _identifier_sequence(
        value,
        validator=validate_approved_input_event_id,
        prefix="AIE",
    )


def format_approved_input_event_id(
    sequence: object,
) -> str:
    """Format one sequence as an Approved Input Event ID."""

    return _format_identifier(
        sequence,
        prefix="AIE",
        label="Approved Input Event ID",
    )


def next_approved_input_event_id(
    occupied_identifiers: Iterable[str],
) -> str:
    """Return the next Approved Input Event ID without reusing gaps."""

    return _next_identifier(
        occupied_identifiers,
        sequence_reader=approved_input_event_id_sequence,
        formatter=format_approved_input_event_id,
        allocation_error=(
            ApprovedInputEventIdAllocationError
        ),
        label="Approved Input Event",
    )


def _is_valid_identifier(
    value: object,
    *,
    pattern: Pattern[str],
) -> bool:
    """Return whether value matches one non-zero identifier."""

    if not isinstance(value, str):
        return False

    match = pattern.fullmatch(value)

    if match is None:
        return False

    sequence = int(match.group(1))

    return (
        MIN_APPROVED_INPUT_IDENTIFIER_SEQUENCE
        <= sequence
        <= MAX_APPROVED_INPUT_IDENTIFIER_SEQUENCE
    )


def _validate_identifier(
    value: object,
    *,
    pattern: Pattern[str],
    label: str,
    prefix: str,
) -> str:
    """Validate one Approved Input identifier."""

    if not isinstance(value, str):
        raise ApprovedInputValidationError(
            f"{label} must be a string."
        )

    match = pattern.fullmatch(value)

    if match is None:
        raise ApprovedInputValidationError(
            f"{label} must match "
            f"^{prefix}-[0-9]{{6}}$."
        )

    sequence = int(match.group(1))

    if not (
        MIN_APPROVED_INPUT_IDENTIFIER_SEQUENCE
        <= sequence
        <= MAX_APPROVED_INPUT_IDENTIFIER_SEQUENCE
    ):
        raise ApprovedInputValidationError(
            f"{label} sequence must be between "
            "000001 and 999999."
        )

    return value


def _identifier_sequence(
    value: object,
    *,
    validator: Callable[[object], str],
    prefix: str,
) -> int:
    """Return the numeric sequence from one valid identifier."""

    validated_identifier = validator(value)

    return int(
        validated_identifier.removeprefix(f"{prefix}-")
    )


def _format_identifier(
    sequence: object,
    *,
    prefix: str,
    label: str,
) -> str:
    """Format one Approved Input identifier sequence."""

    if isinstance(sequence, bool) or not isinstance(
        sequence,
        int,
    ):
        raise ApprovedInputValidationError(
            f"{label} sequence must be an integer."
        )

    if not (
        MIN_APPROVED_INPUT_IDENTIFIER_SEQUENCE
        <= sequence
        <= MAX_APPROVED_INPUT_IDENTIFIER_SEQUENCE
    ):
        raise ApprovedInputValidationError(
            f"{label} sequence must be between "
            "1 and 999999."
        )

    return f"{prefix}-{sequence:06d}"


def _next_identifier(
    occupied_identifiers: Iterable[str],
    *,
    sequence_reader: Callable[[object], int],
    formatter: Callable[[object], str],
    allocation_error: type[
        ApprovedInputIdentifierAllocationError
    ],
    label: str,
) -> str:
    """Allocate the next sequential identifier."""

    if isinstance(occupied_identifiers, (str, bytes)):
        raise allocation_error(
            f"occupied identifiers for {label} must be an "
            "iterable of identifiers."
        )

    try:
        identifiers = tuple(occupied_identifiers)
    except TypeError as exc:
        raise allocation_error(
            f"occupied identifiers for {label} must be iterable."
        ) from exc

    highest_sequence = 0
    seen_identifiers: set[str] = set()

    for identifier in identifiers:
        try:
            sequence = sequence_reader(identifier)
        except ApprovedInputValidationError as exc:
            raise allocation_error(
                f"occupied identifiers for {label} contain an "
                "invalid identifier."
            ) from exc

        if identifier in seen_identifiers:
            raise allocation_error(
                f"occupied identifiers for {label} must be unique."
            )

        seen_identifiers.add(identifier)
        highest_sequence = max(
            highest_sequence,
            sequence,
        )

    if highest_sequence >= MAX_APPROVED_INPUT_IDENTIFIER_SEQUENCE:
        raise allocation_error(
            f"{label} identifier range is exhausted."
        )

    return formatter(highest_sequence + 1)
