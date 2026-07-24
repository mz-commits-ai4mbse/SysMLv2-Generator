"""Stable project-local identifiers for Information Units."""

from __future__ import annotations

from collections.abc import Iterable
import re

from .errors import (
    InformationUnitIdAllocationError,
    InformationUnitValidationError,
)


INFORMATION_UNIT_ID_PATTERN = re.compile(
    r"^IU-([0-9]{6})$"
)

MIN_INFORMATION_UNIT_SEQUENCE = 1
MAX_INFORMATION_UNIT_SEQUENCE = 999_999


def is_valid_information_unit_id(value: object) -> bool:
    """Return whether a value is a valid Information Unit ID."""

    return (
        isinstance(value, str)
        and INFORMATION_UNIT_ID_PATTERN.fullmatch(value)
        is not None
        and value != "IU-000000"
    )


def validate_information_unit_id(value: object) -> str:
    """Validate and return a project-local Information Unit ID."""

    if not isinstance(value, str):
        raise InformationUnitValidationError(
            "information_unit_id must be a string."
        )

    match = INFORMATION_UNIT_ID_PATTERN.fullmatch(value)

    if match is None:
        raise InformationUnitValidationError(
            "information_unit_id must match ^IU-[0-9]{6}$."
        )

    sequence = int(match.group(1))

    if sequence < MIN_INFORMATION_UNIT_SEQUENCE:
        raise InformationUnitValidationError(
            "information_unit_id sequence must be between "
            "000001 and 999999."
        )

    return value


def information_unit_id_sequence(value: object) -> int:
    """Return the sequence represented by an Information Unit ID."""

    validated_id = validate_information_unit_id(value)
    return int(validated_id.removeprefix("IU-"))


def format_information_unit_id(sequence: object) -> str:
    """Format a sequence as a valid Information Unit ID."""

    if isinstance(sequence, bool) or not isinstance(sequence, int):
        raise InformationUnitValidationError(
            "Information Unit ID sequence must be an integer."
        )

    if not (
        MIN_INFORMATION_UNIT_SEQUENCE
        <= sequence
        <= MAX_INFORMATION_UNIT_SEQUENCE
    ):
        raise InformationUnitValidationError(
            "Information Unit ID sequence must be between "
            "1 and 999999."
        )

    return f"IU-{sequence:06d}"


def next_information_unit_id(
    occupied_information_unit_ids: Iterable[str],
) -> str:
    """Return the next sequential ID without reusing gaps."""

    if isinstance(
        occupied_information_unit_ids,
        (str, bytes),
    ):
        raise InformationUnitIdAllocationError(
            "occupied_information_unit_ids must be an "
            "iterable of Information Unit IDs."
        )

    try:
        identifiers = tuple(occupied_information_unit_ids)
    except TypeError as exc:
        raise InformationUnitIdAllocationError(
            "occupied_information_unit_ids must be iterable."
        ) from exc

    for information_unit_id in identifiers:
        if not is_valid_information_unit_id(
            information_unit_id
        ):
            raise InformationUnitIdAllocationError(
                "Invalid occupied Information Unit ID: "
                f"{information_unit_id!r}."
            )

    if len(identifiers) != len(set(identifiers)):
        raise InformationUnitIdAllocationError(
            "Duplicate occupied Information Unit IDs "
            "are not allowed."
        )

    highest_sequence = max(
        (
            information_unit_id_sequence(identifier)
            for identifier in identifiers
        ),
        default=0,
    )

    if highest_sequence >= MAX_INFORMATION_UNIT_SEQUENCE:
        raise InformationUnitIdAllocationError(
            "Information Unit ID range is exhausted "
            "at IU-999999."
        )

    return format_information_unit_id(
        highest_sequence + 1
    )