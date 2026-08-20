"""Stable project-local identifiers for Source Analysis Units."""

from __future__ import annotations

from collections.abc import Iterable
import re

from .errors import (
    SourceAnalysisUnitIdAllocationError,
    SourceAnalysisUnitValidationError,
)


SOURCE_ANALYSIS_UNIT_ID_PATTERN = re.compile(
    r"^SAU-([0-9]{6})$"
)

MIN_SOURCE_ANALYSIS_UNIT_SEQUENCE = 1
MAX_SOURCE_ANALYSIS_UNIT_SEQUENCE = 999_999


def is_valid_source_analysis_unit_id(value: object) -> bool:
    """Return whether a value is a valid Source Analysis Unit ID."""

    return (
        isinstance(value, str)
        and SOURCE_ANALYSIS_UNIT_ID_PATTERN.fullmatch(value)
        is not None
        and value != "SAU-000000"
    )


def validate_source_analysis_unit_id(value: object) -> str:
    """Validate and return a project-local Source Analysis Unit ID."""

    if not isinstance(value, str):
        raise SourceAnalysisUnitValidationError(
            "source_analysis_unit_id must be a string."
        )

    match = SOURCE_ANALYSIS_UNIT_ID_PATTERN.fullmatch(value)

    if match is None:
        raise SourceAnalysisUnitValidationError(
            "source_analysis_unit_id must match ^SAU-[0-9]{6}$."
        )

    sequence = int(match.group(1))

    if sequence < MIN_SOURCE_ANALYSIS_UNIT_SEQUENCE:
        raise SourceAnalysisUnitValidationError(
            "source_analysis_unit_id sequence must be between "
            "000001 and 999999."
        )

    return value


def source_analysis_unit_id_sequence(value: object) -> int:
    """Return the sequence represented by a Source Analysis Unit ID."""

    validated_id = validate_source_analysis_unit_id(value)
    return int(validated_id.removeprefix("SAU-"))


def format_source_analysis_unit_id(sequence: object) -> str:
    """Format a sequence as a valid Source Analysis Unit ID."""

    if isinstance(sequence, bool) or not isinstance(sequence, int):
        raise SourceAnalysisUnitValidationError(
            "Source Analysis Unit ID sequence must be an integer."
        )

    if not (
        MIN_SOURCE_ANALYSIS_UNIT_SEQUENCE
        <= sequence
        <= MAX_SOURCE_ANALYSIS_UNIT_SEQUENCE
    ):
        raise SourceAnalysisUnitValidationError(
            "Source Analysis Unit ID sequence must be between "
            "1 and 999999."
        )

    return f"SAU-{sequence:06d}"


def next_source_analysis_unit_id(
    occupied_source_analysis_unit_ids: Iterable[str],
) -> str:
    """Return the next sequential ID without reusing gaps."""

    if isinstance(
        occupied_source_analysis_unit_ids,
        (str, bytes),
    ):
        raise SourceAnalysisUnitIdAllocationError(
            "occupied_source_analysis_unit_ids must be an "
            "iterable of Source Analysis Unit IDs."
        )

    try:
        identifiers = tuple(
            occupied_source_analysis_unit_ids
        )
    except TypeError as exc:
        raise SourceAnalysisUnitIdAllocationError(
            "occupied_source_analysis_unit_ids must be iterable."
        ) from exc

    for source_analysis_unit_id in identifiers:
        if not is_valid_source_analysis_unit_id(
            source_analysis_unit_id
        ):
            raise SourceAnalysisUnitIdAllocationError(
                "Invalid occupied Source Analysis Unit ID: "
                f"{source_analysis_unit_id!r}."
            )

    if len(identifiers) != len(set(identifiers)):
        raise SourceAnalysisUnitIdAllocationError(
            "Duplicate occupied Source Analysis Unit IDs "
            "are not allowed."
        )

    highest_sequence = max(
        (
            source_analysis_unit_id_sequence(identifier)
            for identifier in identifiers
        ),
        default=0,
    )

    if highest_sequence >= MAX_SOURCE_ANALYSIS_UNIT_SEQUENCE:
        raise SourceAnalysisUnitIdAllocationError(
            "Source Analysis Unit ID range is exhausted "
            "at SAU-999999."
        )

    return format_source_analysis_unit_id(
        highest_sequence + 1
    )
