"""Stable project-local identifiers for Phase-H Model Candidates."""

from __future__ import annotations

from collections.abc import Callable, Iterable
import re

from .errors import (
    ModelCandidateError,
    ModelCandidateSetIdAllocationError,
    ModelCandidateValidationError,
    ModelElementCandidateIdAllocationError,
    ModelRelationshipCandidateIdAllocationError,
)


MODEL_CANDIDATE_SET_ID_PATTERN = re.compile(r"^MCS-([0-9]{6})$")
MODEL_ELEMENT_CANDIDATE_ID_PATTERN = re.compile(r"^MCE-([0-9]{6})$")
MODEL_RELATIONSHIP_CANDIDATE_ID_PATTERN = re.compile(r"^MCR-([0-9]{6})$")

MIN_MODEL_CANDIDATE_SEQUENCE = 1
MAX_MODEL_CANDIDATE_SEQUENCE = 999_999


def is_valid_model_candidate_set_id(value: object) -> bool:
    """Return whether value is a valid Model Candidate Set ID."""

    return _is_valid_identifier(
        value,
        MODEL_CANDIDATE_SET_ID_PATTERN,
        "MCS-000000",
    )


def validate_model_candidate_set_id(value: object) -> str:
    """Validate and return one Model Candidate Set ID."""

    return _validate_identifier(
        value,
        pattern=MODEL_CANDIDATE_SET_ID_PATTERN,
        zero_value="MCS-000000",
        label="model_candidate_set_id",
        prefix="MCS",
    )


def model_candidate_set_id_sequence(value: object) -> int:
    """Return the sequence represented by a Model Candidate Set ID."""

    validated = validate_model_candidate_set_id(value)
    return int(validated.removeprefix("MCS-"))


def format_model_candidate_set_id(sequence: object) -> str:
    """Format one positive sequence as a Model Candidate Set ID."""

    return _format_identifier(
        sequence,
        prefix="MCS",
        label="Model Candidate Set ID",
    )


def next_model_candidate_set_id(
    occupied_candidate_set_ids: Iterable[str],
) -> str:
    """Return the next Set ID after the highest occupied sequence."""

    return _next_identifier(
        occupied_candidate_set_ids,
        validator=validate_model_candidate_set_id,
        sequence_reader=model_candidate_set_id_sequence,
        formatter=format_model_candidate_set_id,
        error_type=ModelCandidateSetIdAllocationError,
        label="Model Candidate Set ID",
    )


def is_valid_model_element_candidate_id(value: object) -> bool:
    """Return whether value is a valid Model Element Candidate ID."""

    return _is_valid_identifier(
        value,
        MODEL_ELEMENT_CANDIDATE_ID_PATTERN,
        "MCE-000000",
    )


def validate_model_element_candidate_id(value: object) -> str:
    """Validate and return one Model Element Candidate ID."""

    return _validate_identifier(
        value,
        pattern=MODEL_ELEMENT_CANDIDATE_ID_PATTERN,
        zero_value="MCE-000000",
        label="model_element_candidate_id",
        prefix="MCE",
    )


def model_element_candidate_id_sequence(value: object) -> int:
    """Return the sequence represented by a Model Element Candidate ID."""

    validated = validate_model_element_candidate_id(value)
    return int(validated.removeprefix("MCE-"))


def format_model_element_candidate_id(sequence: object) -> str:
    """Format one positive sequence as a Model Element Candidate ID."""

    return _format_identifier(
        sequence,
        prefix="MCE",
        label="Model Element Candidate ID",
    )


def next_model_element_candidate_id(
    occupied_element_candidate_ids: Iterable[str],
) -> str:
    """Return the next Element ID after the highest occupied sequence."""

    return _next_identifier(
        occupied_element_candidate_ids,
        validator=validate_model_element_candidate_id,
        sequence_reader=model_element_candidate_id_sequence,
        formatter=format_model_element_candidate_id,
        error_type=ModelElementCandidateIdAllocationError,
        label="Model Element Candidate ID",
    )


def is_valid_model_relationship_candidate_id(value: object) -> bool:
    """Return whether value is a valid Model Relationship Candidate ID."""

    return _is_valid_identifier(
        value,
        MODEL_RELATIONSHIP_CANDIDATE_ID_PATTERN,
        "MCR-000000",
    )


def validate_model_relationship_candidate_id(value: object) -> str:
    """Validate and return one Model Relationship Candidate ID."""

    return _validate_identifier(
        value,
        pattern=MODEL_RELATIONSHIP_CANDIDATE_ID_PATTERN,
        zero_value="MCR-000000",
        label="model_relationship_candidate_id",
        prefix="MCR",
    )


def model_relationship_candidate_id_sequence(value: object) -> int:
    """Return the sequence represented by a Relationship Candidate ID."""

    validated = validate_model_relationship_candidate_id(value)
    return int(validated.removeprefix("MCR-"))


def format_model_relationship_candidate_id(sequence: object) -> str:
    """Format one positive sequence as a Relationship Candidate ID."""

    return _format_identifier(
        sequence,
        prefix="MCR",
        label="Model Relationship Candidate ID",
    )


def next_model_relationship_candidate_id(
    occupied_relationship_candidate_ids: Iterable[str],
) -> str:
    """Return the next Relationship ID after the highest occupied sequence."""

    return _next_identifier(
        occupied_relationship_candidate_ids,
        validator=validate_model_relationship_candidate_id,
        sequence_reader=model_relationship_candidate_id_sequence,
        formatter=format_model_relationship_candidate_id,
        error_type=ModelRelationshipCandidateIdAllocationError,
        label="Model Relationship Candidate ID",
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
        raise ModelCandidateValidationError(
            f"{label} must be a string."
        )
    if pattern.fullmatch(value) is None:
        raise ModelCandidateValidationError(
            f"{label} must match ^{prefix}-[0-9]{{6}}$."
        )
    if value == zero_value:
        raise ModelCandidateValidationError(
            f"{label} sequence must be between 000001 and 999999."
        )
    return value


def _format_identifier(
    sequence: object,
    *,
    prefix: str,
    label: str,
) -> str:
    if isinstance(sequence, bool) or not isinstance(sequence, int):
        raise ModelCandidateValidationError(
            f"{label} sequence must be an integer."
        )
    if not (
        MIN_MODEL_CANDIDATE_SEQUENCE
        <= sequence
        <= MAX_MODEL_CANDIDATE_SEQUENCE
    ):
        raise ModelCandidateValidationError(
            f"{label} sequence must be between 1 and 999999."
        )
    return f"{prefix}-{sequence:06d}"


def _next_identifier(
    occupied_ids: Iterable[str],
    *,
    validator: Callable[[object], str],
    sequence_reader: Callable[[object], int],
    formatter: Callable[[object], str],
    error_type: type[ModelCandidateError],
    label: str,
) -> str:
    if isinstance(occupied_ids, (str, bytes)):
        raise error_type(
            f"occupied_ids must be an iterable of {label} values."
        )

    try:
        identifiers = tuple(occupied_ids)
    except TypeError as exc:
        raise error_type(
            f"occupied_ids must be iterable for {label} allocation."
        ) from exc

    try:
        for identifier in identifiers:
            validator(identifier)
    except ModelCandidateValidationError as exc:
        raise error_type(
            f"Invalid occupied {label}: {identifier!r}."
        ) from exc

    if len(identifiers) != len(set(identifiers)):
        raise error_type(
            f"Duplicate occupied {label} values are not allowed."
        )

    highest_sequence = max(
        (sequence_reader(identifier) for identifier in identifiers),
        default=0,
    )
    if highest_sequence >= MAX_MODEL_CANDIDATE_SEQUENCE:
        raise error_type(
            f"{label} range is exhausted at "
            f"{formatter(MAX_MODEL_CANDIDATE_SEQUENCE)}."
        )
    return formatter(highest_sequence + 1)
