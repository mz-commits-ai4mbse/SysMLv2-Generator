"""Stable project-local identities for published output packages."""

from __future__ import annotations

from collections.abc import Iterable
import re

from .errors import (
    OutputPublicationIntegrityError,
    OutputPublicationValidationError,
)


OUTPUT_PACKAGE_ID_PATTERN = re.compile(r"^OUT-([0-9]{6})$")
MIN_OUTPUT_PACKAGE_SEQUENCE = 1
MAX_OUTPUT_PACKAGE_SEQUENCE = 999_999


def validate_output_package_id(value: object) -> str:
    if (
        not isinstance(value, str)
        or OUTPUT_PACKAGE_ID_PATTERN.fullmatch(value) is None
        or value == "OUT-000000"
    ):
        raise OutputPublicationValidationError(
            "output_package_id must match ^OUT-[0-9]{6}$ with sequence "
            "000001..999999."
        )
    return value


def output_package_id_sequence(value: object) -> int:
    validated = validate_output_package_id(value)
    return int(validated.removeprefix("OUT-"))


def format_output_package_id(sequence: object) -> str:
    if isinstance(sequence, bool) or not isinstance(sequence, int):
        raise OutputPublicationValidationError(
            "Published Output sequence must be an integer."
        )
    if not MIN_OUTPUT_PACKAGE_SEQUENCE <= sequence <= MAX_OUTPUT_PACKAGE_SEQUENCE:
        raise OutputPublicationValidationError(
            "Published Output sequence must be between 1 and 999999."
        )
    return f"OUT-{sequence:06d}"


def next_output_package_id(occupied_ids: Iterable[str]) -> str:
    if isinstance(occupied_ids, (str, bytes)):
        raise OutputPublicationIntegrityError(
            "occupied output IDs must be an iterable of OUT IDs."
        )
    try:
        identifiers = tuple(occupied_ids)
    except TypeError as exc:
        raise OutputPublicationIntegrityError(
            "occupied output IDs must be iterable."
        ) from exc
    if len(identifiers) != len(set(identifiers)):
        raise OutputPublicationIntegrityError(
            "duplicate occupied OUT IDs are not allowed."
        )
    try:
        sequences = tuple(output_package_id_sequence(item) for item in identifiers)
    except OutputPublicationValidationError as exc:
        raise OutputPublicationIntegrityError(
            "occupied output IDs contain an invalid OUT ID."
        ) from exc
    highest = max(sequences, default=0)
    if highest >= MAX_OUTPUT_PACKAGE_SEQUENCE:
        raise OutputPublicationIntegrityError(
            "Published Output ID range is exhausted."
        )
    return format_output_package_id(highest + 1)
