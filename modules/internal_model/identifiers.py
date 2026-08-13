"""Stable project-local identifiers for Phase-I Internal Engineering Models."""

from __future__ import annotations

from collections.abc import Callable, Iterable
import re

from .errors import (
    InternalEngineeringModelIdAllocationError,
    InternalModelElementIdAllocationError,
    InternalModelError,
    InternalModelRelationshipIdAllocationError,
    InternalModelValidationError,
)


INTERNAL_ENGINEERING_MODEL_ID_PATTERN = re.compile(r"^IEM-([0-9]{6})$")
INTERNAL_MODEL_ELEMENT_ID_PATTERN = re.compile(r"^IME-([0-9]{6})$")
INTERNAL_MODEL_RELATIONSHIP_ID_PATTERN = re.compile(r"^IMR-([0-9]{6})$")

MIN_INTERNAL_MODEL_SEQUENCE = 1
MAX_INTERNAL_MODEL_SEQUENCE = 999_999


def is_valid_internal_engineering_model_id(value: object) -> bool:
    """Return whether value is a valid Internal Engineering Model ID."""

    return _is_valid_identifier(
        value,
        INTERNAL_ENGINEERING_MODEL_ID_PATTERN,
        "IEM-000000",
    )


def validate_internal_engineering_model_id(value: object) -> str:
    """Validate and return one Internal Engineering Model ID."""

    return _validate_identifier(
        value,
        pattern=INTERNAL_ENGINEERING_MODEL_ID_PATTERN,
        zero_value="IEM-000000",
        label="internal_engineering_model_id",
        prefix="IEM",
    )


def internal_engineering_model_id_sequence(value: object) -> int:
    """Return the sequence represented by an Internal Engineering Model ID."""

    validated = validate_internal_engineering_model_id(value)
    return int(validated.removeprefix("IEM-"))


def format_internal_engineering_model_id(sequence: object) -> str:
    """Format one positive sequence as an Internal Engineering Model ID."""

    return _format_identifier(
        sequence,
        prefix="IEM",
        label="Internal Engineering Model ID",
    )


def next_internal_engineering_model_id(
    occupied_internal_engineering_model_ids: Iterable[str],
) -> str:
    """Return the next IEM ID after the highest occupied sequence."""

    return _next_identifier(
        occupied_internal_engineering_model_ids,
        validator=validate_internal_engineering_model_id,
        sequence_reader=internal_engineering_model_id_sequence,
        formatter=format_internal_engineering_model_id,
        error_type=InternalEngineeringModelIdAllocationError,
        label="Internal Engineering Model ID",
    )


def is_valid_internal_model_element_id(value: object) -> bool:
    """Return whether value is a valid Internal Model Element ID."""

    return _is_valid_identifier(
        value,
        INTERNAL_MODEL_ELEMENT_ID_PATTERN,
        "IME-000000",
    )


def validate_internal_model_element_id(value: object) -> str:
    """Validate and return one Internal Model Element ID."""

    return _validate_identifier(
        value,
        pattern=INTERNAL_MODEL_ELEMENT_ID_PATTERN,
        zero_value="IME-000000",
        label="internal_model_element_id",
        prefix="IME",
    )


def internal_model_element_id_sequence(value: object) -> int:
    """Return the sequence represented by an Internal Model Element ID."""

    validated = validate_internal_model_element_id(value)
    return int(validated.removeprefix("IME-"))


def format_internal_model_element_id(sequence: object) -> str:
    """Format one positive sequence as an Internal Model Element ID."""

    return _format_identifier(
        sequence,
        prefix="IME",
        label="Internal Model Element ID",
    )


def next_internal_model_element_id(
    occupied_internal_model_element_ids: Iterable[str],
) -> str:
    """Return the next IME ID after the highest occupied sequence."""

    return _next_identifier(
        occupied_internal_model_element_ids,
        validator=validate_internal_model_element_id,
        sequence_reader=internal_model_element_id_sequence,
        formatter=format_internal_model_element_id,
        error_type=InternalModelElementIdAllocationError,
        label="Internal Model Element ID",
    )


def is_valid_internal_model_relationship_id(value: object) -> bool:
    """Return whether value is a valid Internal Model Relationship ID."""

    return _is_valid_identifier(
        value,
        INTERNAL_MODEL_RELATIONSHIP_ID_PATTERN,
        "IMR-000000",
    )


def validate_internal_model_relationship_id(value: object) -> str:
    """Validate and return one Internal Model Relationship ID."""

    return _validate_identifier(
        value,
        pattern=INTERNAL_MODEL_RELATIONSHIP_ID_PATTERN,
        zero_value="IMR-000000",
        label="internal_model_relationship_id",
        prefix="IMR",
    )


def internal_model_relationship_id_sequence(value: object) -> int:
    """Return the sequence represented by an Internal Model Relationship ID."""

    validated = validate_internal_model_relationship_id(value)
    return int(validated.removeprefix("IMR-"))


def format_internal_model_relationship_id(sequence: object) -> str:
    """Format one positive sequence as an Internal Model Relationship ID."""

    return _format_identifier(
        sequence,
        prefix="IMR",
        label="Internal Model Relationship ID",
    )


def next_internal_model_relationship_id(
    occupied_internal_model_relationship_ids: Iterable[str],
) -> str:
    """Return the next IMR ID after the highest occupied sequence."""

    return _next_identifier(
        occupied_internal_model_relationship_ids,
        validator=validate_internal_model_relationship_id,
        sequence_reader=internal_model_relationship_id_sequence,
        formatter=format_internal_model_relationship_id,
        error_type=InternalModelRelationshipIdAllocationError,
        label="Internal Model Relationship ID",
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
        raise InternalModelValidationError(
            f"{label} must be a string."
        )
    if pattern.fullmatch(value) is None:
        raise InternalModelValidationError(
            f"{label} must match ^{prefix}-[0-9]{{6}}$."
        )
    if value == zero_value:
        raise InternalModelValidationError(
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
        raise InternalModelValidationError(
            f"{label} sequence must be an integer."
        )
    if not (
        MIN_INTERNAL_MODEL_SEQUENCE
        <= sequence
        <= MAX_INTERNAL_MODEL_SEQUENCE
    ):
        raise InternalModelValidationError(
            f"{label} sequence must be between 1 and 999999."
        )
    return f"{prefix}-{sequence:06d}"


def _next_identifier(
    occupied_ids: Iterable[str],
    *,
    validator: Callable[[object], str],
    sequence_reader: Callable[[object], int],
    formatter: Callable[[object], str],
    error_type: type[InternalModelError],
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
    except InternalModelValidationError as exc:
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
    if highest_sequence >= MAX_INTERNAL_MODEL_SEQUENCE:
        raise error_type(
            f"{label} range is exhausted at "
            f"{formatter(MAX_INTERNAL_MODEL_SEQUENCE)}."
        )
    return formatter(highest_sequence + 1)
