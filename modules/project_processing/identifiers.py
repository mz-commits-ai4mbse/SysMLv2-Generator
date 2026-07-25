"""Identifiers for project-oriented processing artifacts."""

from __future__ import annotations

from collections.abc import Iterable
import re
from typing import Callable, Pattern

from .errors import (
    ProcessingAttemptIdAllocationError,
    ProcessingDecisionIdAllocationError,
    ProcessingEventIdAllocationError,
    ProcessingIdentifierAllocationError,
    ProcessingRunIdAllocationError,
    ProcessingValidationError,
)


PROCESSING_RUN_ID_PATTERN = re.compile(
    r"^RUN-([0-9]{6})$"
)
PROCESSING_EVENT_ID_PATTERN = re.compile(
    r"^EVT-([0-9]{6})$"
)
PROCESSING_ATTEMPT_ID_PATTERN = re.compile(
    r"^ATT-([0-9]{6})$"
)
PROCESSING_DECISION_ID_PATTERN = re.compile(
    r"^PD-([0-9]{6})$"
)

MIN_PROCESSING_IDENTIFIER_SEQUENCE = 1
MAX_PROCESSING_IDENTIFIER_SEQUENCE = 999_999


def is_valid_processing_run_id(value: object) -> bool:
    """Return whether value is a valid Processing Run ID."""

    return _is_valid_identifier(
        value,
        pattern=PROCESSING_RUN_ID_PATTERN,
    )


def validate_processing_run_id(value: object) -> str:
    """Validate and return a Processing Run ID."""

    return _validate_identifier(
        value,
        pattern=PROCESSING_RUN_ID_PATTERN,
        label="processing_run_id",
        prefix="RUN",
    )


def processing_run_id_sequence(value: object) -> int:
    """Return the sequence represented by a Processing Run ID."""

    return _identifier_sequence(
        value,
        validator=validate_processing_run_id,
        prefix="RUN",
    )


def format_processing_run_id(sequence: object) -> str:
    """Format a sequence as a Processing Run ID."""

    return _format_identifier(
        sequence,
        prefix="RUN",
        label="Processing Run ID",
    )


def next_processing_run_id(
    occupied_identifiers: Iterable[str],
) -> str:
    """Return the next Processing Run ID without reusing gaps."""

    return _next_identifier(
        occupied_identifiers,
        sequence_reader=processing_run_id_sequence,
        formatter=format_processing_run_id,
        allocation_error=ProcessingRunIdAllocationError,
        label="Processing Run",
    )


def is_valid_processing_event_id(value: object) -> bool:
    """Return whether value is a valid Processing Event ID."""

    return _is_valid_identifier(
        value,
        pattern=PROCESSING_EVENT_ID_PATTERN,
    )


def validate_processing_event_id(value: object) -> str:
    """Validate and return a Processing Event ID."""

    return _validate_identifier(
        value,
        pattern=PROCESSING_EVENT_ID_PATTERN,
        label="event_id",
        prefix="EVT",
    )


def processing_event_id_sequence(value: object) -> int:
    """Return the sequence represented by a Processing Event ID."""

    return _identifier_sequence(
        value,
        validator=validate_processing_event_id,
        prefix="EVT",
    )


def format_processing_event_id(sequence: object) -> str:
    """Format a sequence as a Processing Event ID."""

    return _format_identifier(
        sequence,
        prefix="EVT",
        label="Processing Event ID",
    )


def next_processing_event_id(
    occupied_identifiers: Iterable[str],
) -> str:
    """Return the next Processing Event ID without reusing gaps."""

    return _next_identifier(
        occupied_identifiers,
        sequence_reader=processing_event_id_sequence,
        formatter=format_processing_event_id,
        allocation_error=ProcessingEventIdAllocationError,
        label="Processing Event",
    )


def is_valid_processing_attempt_id(value: object) -> bool:
    """Return whether value is a valid Processing Attempt ID."""

    return _is_valid_identifier(
        value,
        pattern=PROCESSING_ATTEMPT_ID_PATTERN,
    )


def validate_processing_attempt_id(value: object) -> str:
    """Validate and return a Processing Attempt ID."""

    return _validate_identifier(
        value,
        pattern=PROCESSING_ATTEMPT_ID_PATTERN,
        label="attempt_id",
        prefix="ATT",
    )


def processing_attempt_id_sequence(value: object) -> int:
    """Return the sequence represented by an Attempt ID."""

    return _identifier_sequence(
        value,
        validator=validate_processing_attempt_id,
        prefix="ATT",
    )


def format_processing_attempt_id(sequence: object) -> str:
    """Format a sequence as a Processing Attempt ID."""

    return _format_identifier(
        sequence,
        prefix="ATT",
        label="Processing Attempt ID",
    )


def next_processing_attempt_id(
    occupied_identifiers: Iterable[str],
) -> str:
    """Return the next Attempt ID without reusing gaps."""

    return _next_identifier(
        occupied_identifiers,
        sequence_reader=processing_attempt_id_sequence,
        formatter=format_processing_attempt_id,
        allocation_error=ProcessingAttemptIdAllocationError,
        label="Processing Attempt",
    )


def is_valid_processing_decision_id(value: object) -> bool:
    """Return whether value is a valid Processing Decision ID."""

    return _is_valid_identifier(
        value,
        pattern=PROCESSING_DECISION_ID_PATTERN,
    )


def validate_processing_decision_id(value: object) -> str:
    """Validate and return a Processing Decision ID."""

    return _validate_identifier(
        value,
        pattern=PROCESSING_DECISION_ID_PATTERN,
        label="processing_decision_id",
        prefix="PD",
    )


def processing_decision_id_sequence(value: object) -> int:
    """Return the sequence represented by a Processing Decision ID."""

    return _identifier_sequence(
        value,
        validator=validate_processing_decision_id,
        prefix="PD",
    )


def format_processing_decision_id(sequence: object) -> str:
    """Format a sequence as a Processing Decision ID."""

    return _format_identifier(
        sequence,
        prefix="PD",
        label="Processing Decision ID",
    )


def next_processing_decision_id(
    occupied_identifiers: Iterable[str],
) -> str:
    """Return the next Processing Decision ID without reusing gaps."""

    return _next_identifier(
        occupied_identifiers,
        sequence_reader=processing_decision_id_sequence,
        formatter=format_processing_decision_id,
        allocation_error=ProcessingDecisionIdAllocationError,
        label="Processing Decision",
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
        MIN_PROCESSING_IDENTIFIER_SEQUENCE
        <= sequence
        <= MAX_PROCESSING_IDENTIFIER_SEQUENCE
    )


def _validate_identifier(
    value: object,
    *,
    pattern: Pattern[str],
    label: str,
    prefix: str,
) -> str:
    """Validate one processing identifier."""

    if not isinstance(value, str):
        raise ProcessingValidationError(
            f"{label} must be a string."
        )

    match = pattern.fullmatch(value)

    if match is None:
        raise ProcessingValidationError(
            f"{label} must match "
            f"^{prefix}-[0-9]{{6}}$."
        )

    sequence = int(match.group(1))

    if not (
        MIN_PROCESSING_IDENTIFIER_SEQUENCE
        <= sequence
        <= MAX_PROCESSING_IDENTIFIER_SEQUENCE
    ):
        raise ProcessingValidationError(
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
    """Format one processing identifier sequence."""

    if isinstance(sequence, bool) or not isinstance(
        sequence,
        int,
    ):
        raise ProcessingValidationError(
            f"{label} sequence must be an integer."
        )

    if not (
        MIN_PROCESSING_IDENTIFIER_SEQUENCE
        <= sequence
        <= MAX_PROCESSING_IDENTIFIER_SEQUENCE
    ):
        raise ProcessingValidationError(
            f"{label} sequence must be between "
            "1 and 999999."
        )

    return f"{prefix}-{sequence:06d}"


def _next_identifier(
    occupied_identifiers: Iterable[str],
    *,
    sequence_reader: Callable[[object], int],
    formatter: Callable[[object], str],
    allocation_error: type[ProcessingIdentifierAllocationError],
    label: str,
) -> str:
    """Allocate the next sequential identifier."""

    if isinstance(occupied_identifiers, (str, bytes)):
        raise allocation_error(
            f"occupied identifiers for {label} must be an iterable "
            "of identifiers."
        )

    try:
        identifiers = tuple(occupied_identifiers)
    except TypeError as exc:
        raise allocation_error(
            f"occupied identifiers for {label} must be iterable."
        ) from exc

    if len(identifiers) != len(set(identifiers)):
        raise allocation_error(
            f"occupied identifiers for {label} must be unique."
        )

    highest_sequence = 0

    for identifier in identifiers:
        try:
            sequence = sequence_reader(identifier)
        except ProcessingValidationError as exc:
            raise allocation_error(
                f"occupied identifiers for {label} contain an "
                "invalid identifier."
            ) from exc

        highest_sequence = max(
            highest_sequence,
            sequence,
        )

    if highest_sequence >= MAX_PROCESSING_IDENTIFIER_SEQUENCE:
        raise allocation_error(
            f"{label} identifier range is exhausted."
        )

    return formatter(highest_sequence + 1)