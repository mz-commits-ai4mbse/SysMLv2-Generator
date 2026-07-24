"""Identifiers for framework-assignment candidates."""

from __future__ import annotations

from collections.abc import Callable, Iterable
import re

from .errors import (
    FrameworkAssignmentAgentCandidateIdAllocationError,
    FrameworkAssignmentCandidateIdAllocationError,
    FrameworkAssignmentError,
    FrameworkAssignmentValidationError,
)


FRAMEWORK_ASSIGNMENT_AGENT_CANDIDATE_ID_PATTERN = re.compile(
    r"^FAAC-([0-9]{6})$"
)
FRAMEWORK_ASSIGNMENT_CANDIDATE_ID_PATTERN = re.compile(
    r"^FAC-([0-9]{6})$"
)

MIN_FRAMEWORK_ASSIGNMENT_SEQUENCE = 1
MAX_FRAMEWORK_ASSIGNMENT_SEQUENCE = 999_999


def is_valid_framework_assignment_agent_candidate_id(
    value: object,
) -> bool:
    """Return whether value is a valid result-local candidate ID."""

    return _is_valid_identifier(
        value,
        FRAMEWORK_ASSIGNMENT_AGENT_CANDIDATE_ID_PATTERN,
        "FAAC-000000",
    )


def validate_framework_assignment_agent_candidate_id(
    value: object,
) -> str:
    """Validate and return one result-local candidate ID."""

    return _validate_identifier(
        value,
        pattern=(
            FRAMEWORK_ASSIGNMENT_AGENT_CANDIDATE_ID_PATTERN
        ),
        zero_value="FAAC-000000",
        label="framework_assignment_agent_candidate_id",
        prefix="FAAC",
    )


def framework_assignment_agent_candidate_id_sequence(
    value: object,
) -> int:
    """Return the sequence represented by an agent candidate ID."""

    validated = (
        validate_framework_assignment_agent_candidate_id(value)
    )
    return int(validated.removeprefix("FAAC-"))


def format_framework_assignment_agent_candidate_id(
    sequence: object,
) -> str:
    """Format a sequence as a result-local candidate ID."""

    return _format_identifier(
        sequence,
        prefix="FAAC",
        label="Framework Assignment Agent Candidate ID",
    )


def next_framework_assignment_agent_candidate_id(
    occupied_candidate_ids: Iterable[str],
) -> str:
    """Return the next result-local ID without reusing gaps."""

    return _next_identifier(
        occupied_candidate_ids,
        validator=(
            validate_framework_assignment_agent_candidate_id
        ),
        sequence_reader=(
            framework_assignment_agent_candidate_id_sequence
        ),
        formatter=(
            format_framework_assignment_agent_candidate_id
        ),
        error_type=(
            FrameworkAssignmentAgentCandidateIdAllocationError
        ),
        label="Framework Assignment Agent Candidate ID",
    )


def is_valid_framework_assignment_candidate_id(
    value: object,
) -> bool:
    """Return whether value is a valid persistent candidate ID."""

    return _is_valid_identifier(
        value,
        FRAMEWORK_ASSIGNMENT_CANDIDATE_ID_PATTERN,
        "FAC-000000",
    )


def validate_framework_assignment_candidate_id(
    value: object,
) -> str:
    """Validate and return one persistent candidate ID."""

    return _validate_identifier(
        value,
        pattern=FRAMEWORK_ASSIGNMENT_CANDIDATE_ID_PATTERN,
        zero_value="FAC-000000",
        label="framework_assignment_candidate_id",
        prefix="FAC",
    )


def framework_assignment_candidate_id_sequence(
    value: object,
) -> int:
    """Return the sequence represented by a persistent candidate ID."""

    validated = validate_framework_assignment_candidate_id(
        value
    )
    return int(validated.removeprefix("FAC-"))


def format_framework_assignment_candidate_id(
    sequence: object,
) -> str:
    """Format a sequence as a persistent candidate ID."""

    return _format_identifier(
        sequence,
        prefix="FAC",
        label="Framework Assignment Candidate ID",
    )


def next_framework_assignment_candidate_id(
    occupied_candidate_ids: Iterable[str],
) -> str:
    """Return the next persistent ID without reusing gaps."""

    return _next_identifier(
        occupied_candidate_ids,
        validator=validate_framework_assignment_candidate_id,
        sequence_reader=(
            framework_assignment_candidate_id_sequence
        ),
        formatter=format_framework_assignment_candidate_id,
        error_type=FrameworkAssignmentCandidateIdAllocationError,
        label="Framework Assignment Candidate ID",
    )


def _is_valid_identifier(
    value: object,
    pattern: re.Pattern[str],
    zero_value: str,
) -> bool:
    return (
        isinstance(value, str)
        and pattern.fullmatch(value) is not None
        and value != zero_value
    )


def _validate_identifier(
    value: object,
    *,
    pattern: re.Pattern[str],
    zero_value: str,
    label: str,
    prefix: str,
) -> str:
    if not isinstance(value, str):
        raise FrameworkAssignmentValidationError(
            f"{label} must be a string."
        )
    if pattern.fullmatch(value) is None:
        raise FrameworkAssignmentValidationError(
            f"{label} must match ^{prefix}-[0-9]{{6}}$."
        )
    if value == zero_value:
        raise FrameworkAssignmentValidationError(
            f"{label} sequence must be between 000001 and "
            "999999."
        )
    return value


def _format_identifier(
    sequence: object,
    *,
    prefix: str,
    label: str,
) -> str:
    if isinstance(sequence, bool) or not isinstance(
        sequence,
        int,
    ):
        raise FrameworkAssignmentValidationError(
            f"{label} sequence must be an integer."
        )
    if not (
        MIN_FRAMEWORK_ASSIGNMENT_SEQUENCE
        <= sequence
        <= MAX_FRAMEWORK_ASSIGNMENT_SEQUENCE
    ):
        raise FrameworkAssignmentValidationError(
            f"{label} sequence must be between 1 and 999999."
        )
    return f"{prefix}-{sequence:06d}"


def _next_identifier(
    occupied_candidate_ids: Iterable[str],
    *,
    validator: Callable[[object], str],
    sequence_reader: Callable[[object], int],
    formatter: Callable[[object], str],
    error_type: type[FrameworkAssignmentError],
    label: str,
) -> str:
    if isinstance(occupied_candidate_ids, (str, bytes)):
        raise error_type(
            "occupied_candidate_ids must be an iterable of "
            f"{label} values."
        )

    try:
        identifiers = tuple(occupied_candidate_ids)
    except TypeError as exc:
        raise error_type(
            "occupied_candidate_ids must be iterable."
        ) from exc

    try:
        for identifier in identifiers:
            validator(identifier)
    except FrameworkAssignmentValidationError as exc:
        raise error_type(
            f"Invalid occupied {label}: {identifier!r}."
        ) from exc

    if len(identifiers) != len(set(identifiers)):
        raise error_type(
            f"Duplicate occupied {label} values are not allowed."
        )

    highest_sequence = max(
        (
            sequence_reader(identifier)
            for identifier in identifiers
        ),
        default=0,
    )
    if highest_sequence >= MAX_FRAMEWORK_ASSIGNMENT_SEQUENCE:
        raise error_type(
            f"{label} range is exhausted at "
            f"{formatter(MAX_FRAMEWORK_ASSIGNMENT_SEQUENCE)}."
        )
    return formatter(highest_sequence + 1)