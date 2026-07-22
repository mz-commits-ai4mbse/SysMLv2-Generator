"""Project-local Source ID validation and allocation."""

from __future__ import annotations

import re
from collections.abc import Iterable

from .errors import SourceIdExhaustedError, SourceManifestError


SOURCE_ID_PATTERN = re.compile(r"^SRC-([0-9]{6})$")
MIN_SOURCE_SEQUENCE = 1
MAX_SOURCE_SEQUENCE = 999_999


def validate_source_id(source_id: object) -> str:
    """Validate and return a project-local Source ID."""

    if not isinstance(source_id, str):
        raise SourceManifestError("source_id must be a string.")

    match = SOURCE_ID_PATTERN.fullmatch(source_id)

    if match is None:
        raise SourceManifestError(
            "source_id must match ^SRC-[0-9]{6}$."
        )

    sequence = int(match.group(1))

    if sequence < MIN_SOURCE_SEQUENCE:
        raise SourceManifestError(
            "source_id sequence must be between 000001 and 999999."
        )

    return source_id


def source_id_sequence(source_id: object) -> int:
    """Return the numeric sequence represented by a valid Source ID."""

    validated_source_id = validate_source_id(source_id)
    return int(validated_source_id.removeprefix("SRC-"))


def format_source_id(sequence: object) -> str:
    """Format a numeric sequence as a valid Source ID."""

    if isinstance(sequence, bool) or not isinstance(sequence, int):
        raise SourceManifestError(
            "Source ID sequence must be an integer."
        )

    if not MIN_SOURCE_SEQUENCE <= sequence <= MAX_SOURCE_SEQUENCE:
        raise SourceManifestError(
            "Source ID sequence must be between 1 and 999999."
        )

    return f"SRC-{sequence:06d}"


def next_source_id(occupied_source_ids: Iterable[str]) -> str:
    """Return the next sequential Source ID without reusing gaps."""

    if isinstance(occupied_source_ids, (str, bytes)):
        raise SourceManifestError(
            "occupied_source_ids must be an iterable of Source IDs."
        )

    highest_sequence = 0

    for source_id in occupied_source_ids:
        sequence = source_id_sequence(source_id)
        highest_sequence = max(highest_sequence, sequence)

    if highest_sequence >= MAX_SOURCE_SEQUENCE:
        raise SourceIdExhaustedError(
            "Source ID range is exhausted at SRC-999999."
        )

    return format_source_id(highest_sequence + 1)