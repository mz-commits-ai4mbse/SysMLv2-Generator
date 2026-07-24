"""Source Projection and Segment identifier validation and allocation."""

from __future__ import annotations

from collections.abc import Iterable
import re

from .errors import (
    SegmentIdExhaustedError,
    SourceProjectionIdExhaustedError,
    SourceProjectionManifestError,
)


SOURCE_PROJECTION_ID_PATTERN = re.compile(
    r"^SP-([0-9]{6})$"
)
SEGMENT_ID_PATTERN = re.compile(
    r"^SEG-([0-9]{6})$"
)

MIN_SOURCE_PROJECTION_SEQUENCE = 1
MAX_SOURCE_PROJECTION_SEQUENCE = 999_999

MIN_SEGMENT_SEQUENCE = 1
MAX_SEGMENT_SEQUENCE = 999_999


def validate_source_projection_id(
    source_projection_id: object,
) -> str:
    """Validate and return a project-local Source Projection ID."""

    if not isinstance(source_projection_id, str):
        raise SourceProjectionManifestError(
            "source_projection_id must be a string."
        )

    match = SOURCE_PROJECTION_ID_PATTERN.fullmatch(
        source_projection_id
    )

    if match is None:
        raise SourceProjectionManifestError(
            "source_projection_id must match ^SP-[0-9]{6}$."
        )

    sequence = int(match.group(1))

    if sequence < MIN_SOURCE_PROJECTION_SEQUENCE:
        raise SourceProjectionManifestError(
            "source_projection_id sequence must be between "
            "000001 and 999999."
        )

    return source_projection_id


def source_projection_id_sequence(
    source_projection_id: object,
) -> int:
    """Return the sequence represented by a Source Projection ID."""

    validated_id = validate_source_projection_id(
        source_projection_id
    )
    return int(validated_id.removeprefix("SP-"))


def format_source_projection_id(sequence: object) -> str:
    """Format a sequence as a valid Source Projection ID."""

    if isinstance(sequence, bool) or not isinstance(sequence, int):
        raise SourceProjectionManifestError(
            "Source Projection ID sequence must be an integer."
        )

    if not (
        MIN_SOURCE_PROJECTION_SEQUENCE
        <= sequence
        <= MAX_SOURCE_PROJECTION_SEQUENCE
    ):
        raise SourceProjectionManifestError(
            "Source Projection ID sequence must be between "
            "1 and 999999."
        )

    return f"SP-{sequence:06d}"


def next_source_projection_id(
    occupied_source_projection_ids: Iterable[str],
) -> str:
    """Return the next sequential ID without reusing gaps."""

    if isinstance(
        occupied_source_projection_ids,
        (str, bytes),
    ):
        raise SourceProjectionManifestError(
            "occupied_source_projection_ids must be an "
            "iterable of Source Projection IDs."
        )

    highest_sequence = 0

    for source_projection_id in (
        occupied_source_projection_ids
    ):
        sequence = source_projection_id_sequence(
            source_projection_id
        )
        highest_sequence = max(
            highest_sequence,
            sequence,
        )

    if highest_sequence >= MAX_SOURCE_PROJECTION_SEQUENCE:
        raise SourceProjectionIdExhaustedError(
            "Source Projection ID range is exhausted "
            "at SP-999999."
        )

    return format_source_projection_id(
        highest_sequence + 1
    )


def validate_segment_id(segment_id: object) -> str:
    """Validate and return a projection-local Segment ID."""

    if not isinstance(segment_id, str):
        raise SourceProjectionManifestError(
            "segment_id must be a string."
        )

    match = SEGMENT_ID_PATTERN.fullmatch(segment_id)

    if match is None:
        raise SourceProjectionManifestError(
            "segment_id must match ^SEG-[0-9]{6}$."
        )

    sequence = int(match.group(1))

    if sequence < MIN_SEGMENT_SEQUENCE:
        raise SourceProjectionManifestError(
            "segment_id sequence must be between "
            "000001 and 999999."
        )

    return segment_id


def segment_id_sequence(segment_id: object) -> int:
    """Return the sequence represented by a Segment ID."""

    validated_id = validate_segment_id(segment_id)
    return int(validated_id.removeprefix("SEG-"))


def format_segment_id(sequence: object) -> str:
    """Format a sequence as a valid Segment ID."""

    if isinstance(sequence, bool) or not isinstance(sequence, int):
        raise SourceProjectionManifestError(
            "Segment ID sequence must be an integer."
        )

    if not MIN_SEGMENT_SEQUENCE <= sequence <= MAX_SEGMENT_SEQUENCE:
        raise SourceProjectionManifestError(
            "Segment ID sequence must be between 1 and 999999."
        )

    return f"SEG-{sequence:06d}"


def next_segment_id(
    occupied_segment_ids: Iterable[str],
) -> str:
    """Return the next sequential Segment ID without reusing gaps."""

    if isinstance(occupied_segment_ids, (str, bytes)):
        raise SourceProjectionManifestError(
            "occupied_segment_ids must be an iterable "
            "of Segment IDs."
        )

    highest_sequence = 0

    for segment_id in occupied_segment_ids:
        sequence = segment_id_sequence(segment_id)
        highest_sequence = max(
            highest_sequence,
            sequence,
        )

    if highest_sequence >= MAX_SEGMENT_SEQUENCE:
        raise SegmentIdExhaustedError(
            "Segment ID range is exhausted at SEG-999999."
        )

    return format_segment_id(highest_sequence + 1)