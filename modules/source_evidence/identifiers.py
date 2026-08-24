"""Stable project-local identifiers for Source Evidence."""

from __future__ import annotations

from collections.abc import Iterable
import re

from .errors import (
    SourceEvidenceIdAllocationError,
    SourceEvidenceValidationError,
)


SOURCE_EVIDENCE_ID_PATTERN = re.compile(r"^EVD-([0-9]{6})$")

MIN_SOURCE_EVIDENCE_SEQUENCE = 1
MAX_SOURCE_EVIDENCE_SEQUENCE = 999_999


def is_valid_source_evidence_id(value: object) -> bool:
    """Return whether a value is a valid Source Evidence ID."""

    return (
        isinstance(value, str)
        and SOURCE_EVIDENCE_ID_PATTERN.fullmatch(value) is not None
        and value != "EVD-000000"
    )


def validate_source_evidence_id(value: object) -> str:
    """Validate and return a project-local Source Evidence ID."""

    if not isinstance(value, str):
        raise SourceEvidenceValidationError(
            "source_evidence_id must be a string."
        )

    match = SOURCE_EVIDENCE_ID_PATTERN.fullmatch(value)
    if match is None:
        raise SourceEvidenceValidationError(
            "source_evidence_id must match ^EVD-[0-9]{6}$."
        )

    sequence = int(match.group(1))
    if sequence < MIN_SOURCE_EVIDENCE_SEQUENCE:
        raise SourceEvidenceValidationError(
            "source_evidence_id sequence must be between "
            "000001 and 999999."
        )

    return value


def source_evidence_id_sequence(value: object) -> int:
    """Return the sequence represented by a Source Evidence ID."""

    return int(
        validate_source_evidence_id(value).removeprefix("EVD-")
    )


def format_source_evidence_id(sequence: object) -> str:
    """Format one sequence as a valid Source Evidence ID."""

    if isinstance(sequence, bool) or not isinstance(sequence, int):
        raise SourceEvidenceValidationError(
            "Source Evidence ID sequence must be an integer."
        )

    if not (
        MIN_SOURCE_EVIDENCE_SEQUENCE
        <= sequence
        <= MAX_SOURCE_EVIDENCE_SEQUENCE
    ):
        raise SourceEvidenceValidationError(
            "Source Evidence ID sequence must be between "
            "1 and 999999."
        )

    return f"EVD-{sequence:06d}"


def next_source_evidence_id(
    occupied_source_evidence_ids: Iterable[str],
) -> str:
    """Return the next sequential ID without reusing gaps."""

    if isinstance(
        occupied_source_evidence_ids,
        (str, bytes),
    ):
        raise SourceEvidenceIdAllocationError(
            "occupied_source_evidence_ids must be an iterable "
            "of Source Evidence IDs."
        )

    try:
        identifiers = tuple(occupied_source_evidence_ids)
    except TypeError as exc:
        raise SourceEvidenceIdAllocationError(
            "occupied_source_evidence_ids must be iterable."
        ) from exc

    for source_evidence_id in identifiers:
        if not is_valid_source_evidence_id(source_evidence_id):
            raise SourceEvidenceIdAllocationError(
                "Invalid occupied Source Evidence ID: "
                f"{source_evidence_id!r}."
            )

    if len(identifiers) != len(set(identifiers)):
        raise SourceEvidenceIdAllocationError(
            "Duplicate occupied Source Evidence IDs are not allowed."
        )

    highest_sequence = max(
        (
            source_evidence_id_sequence(identifier)
            for identifier in identifiers
        ),
        default=0,
    )

    if highest_sequence >= MAX_SOURCE_EVIDENCE_SEQUENCE:
        raise SourceEvidenceIdAllocationError(
            "Source Evidence ID range is exhausted at EVD-999999."
        )

    return format_source_evidence_id(highest_sequence + 1)
