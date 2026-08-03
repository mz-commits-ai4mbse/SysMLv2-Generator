"""Stable identifiers for the Human Review Workspace."""

from __future__ import annotations

from collections.abc import Iterable
import re
from typing import Callable, Pattern

from .errors import (
    ReviewDocumentIdAllocationError,
    ReviewDocumentVersionIdAllocationError,
    ReviewIdentifierAllocationError,
    ReviewItemIdAllocationError,
    ReviewRevisionIdAllocationError,
    ReviewValidationError,
    ScopedReviewActionIdAllocationError,
)


REVIEW_DOCUMENT_ID_PATTERN = re.compile(
    r"^RVD-([0-9]{6})$"
)
REVIEW_DOCUMENT_VERSION_ID_PATTERN = re.compile(
    r"^RVV-([0-9]{6})$"
)
REVIEW_REVISION_ID_PATTERN = re.compile(
    r"^RVR-([0-9]{6})$"
)
REVIEW_ITEM_ID_PATTERN = re.compile(
    r"^RIT-([0-9]{6})$"
)
SCOPED_REVIEW_ACTION_ID_PATTERN = re.compile(
    r"^SRA-([0-9]{6})$"
)

MIN_REVIEW_IDENTIFIER_SEQUENCE = 1
MAX_REVIEW_IDENTIFIER_SEQUENCE = 999_999


def is_valid_review_document_id(value: object) -> bool:
    """Return whether value is a valid Review Document ID."""

    return _is_valid_identifier(
        value,
        pattern=REVIEW_DOCUMENT_ID_PATTERN,
    )


def validate_review_document_id(value: object) -> str:
    """Validate and return one Review Document ID."""

    return _validate_identifier(
        value,
        pattern=REVIEW_DOCUMENT_ID_PATTERN,
        label="review_document_id",
        prefix="RVD",
    )


def review_document_id_sequence(value: object) -> int:
    """Return the sequence represented by a Review Document ID."""

    return _identifier_sequence(
        value,
        validator=validate_review_document_id,
        prefix="RVD",
    )


def format_review_document_id(sequence: object) -> str:
    """Format one sequence as a Review Document ID."""

    return _format_identifier(
        sequence,
        prefix="RVD",
        label="Review Document ID",
    )


def next_review_document_id(
    occupied_identifiers: Iterable[str],
) -> str:
    """Return the next Review Document ID without reusing gaps."""

    return _next_identifier(
        occupied_identifiers,
        sequence_reader=review_document_id_sequence,
        formatter=format_review_document_id,
        allocation_error=ReviewDocumentIdAllocationError,
        label="Review Document",
    )


def is_valid_review_document_version_id(
    value: object,
) -> bool:
    """Return whether value is a valid Review Document Version ID."""

    return _is_valid_identifier(
        value,
        pattern=REVIEW_DOCUMENT_VERSION_ID_PATTERN,
    )


def validate_review_document_version_id(
    value: object,
) -> str:
    """Validate and return one Review Document Version ID."""

    return _validate_identifier(
        value,
        pattern=REVIEW_DOCUMENT_VERSION_ID_PATTERN,
        label="review_document_version_id",
        prefix="RVV",
    )


def review_document_version_id_sequence(
    value: object,
) -> int:
    """Return the sequence represented by a version ID."""

    return _identifier_sequence(
        value,
        validator=validate_review_document_version_id,
        prefix="RVV",
    )


def format_review_document_version_id(
    sequence: object,
) -> str:
    """Format one sequence as a Review Document Version ID."""

    return _format_identifier(
        sequence,
        prefix="RVV",
        label="Review Document Version ID",
    )


def next_review_document_version_id(
    occupied_identifiers: Iterable[str],
) -> str:
    """Return the next version ID without reusing gaps."""

    return _next_identifier(
        occupied_identifiers,
        sequence_reader=review_document_version_id_sequence,
        formatter=format_review_document_version_id,
        allocation_error=(
            ReviewDocumentVersionIdAllocationError
        ),
        label="Review Document Version",
    )


def is_valid_review_revision_id(value: object) -> bool:
    """Return whether value is a valid Review Revision ID."""

    return _is_valid_identifier(
        value,
        pattern=REVIEW_REVISION_ID_PATTERN,
    )


def validate_review_revision_id(value: object) -> str:
    """Validate and return one Review Revision ID."""

    return _validate_identifier(
        value,
        pattern=REVIEW_REVISION_ID_PATTERN,
        label="review_revision_id",
        prefix="RVR",
    )


def review_revision_id_sequence(value: object) -> int:
    """Return the sequence represented by a Review Revision ID."""

    return _identifier_sequence(
        value,
        validator=validate_review_revision_id,
        prefix="RVR",
    )


def format_review_revision_id(sequence: object) -> str:
    """Format one sequence as a Review Revision ID."""

    return _format_identifier(
        sequence,
        prefix="RVR",
        label="Review Revision ID",
    )


def next_review_revision_id(
    occupied_identifiers: Iterable[str],
) -> str:
    """Return the next Review Revision ID without reusing gaps."""

    return _next_identifier(
        occupied_identifiers,
        sequence_reader=review_revision_id_sequence,
        formatter=format_review_revision_id,
        allocation_error=ReviewRevisionIdAllocationError,
        label="Review Revision",
    )


def is_valid_review_item_id(value: object) -> bool:
    """Return whether value is a valid Review Item ID."""

    return _is_valid_identifier(
        value,
        pattern=REVIEW_ITEM_ID_PATTERN,
    )


def validate_review_item_id(value: object) -> str:
    """Validate and return one Review Item ID."""

    return _validate_identifier(
        value,
        pattern=REVIEW_ITEM_ID_PATTERN,
        label="review_item_id",
        prefix="RIT",
    )


def review_item_id_sequence(value: object) -> int:
    """Return the sequence represented by a Review Item ID."""

    return _identifier_sequence(
        value,
        validator=validate_review_item_id,
        prefix="RIT",
    )


def format_review_item_id(sequence: object) -> str:
    """Format one sequence as a Review Item ID."""

    return _format_identifier(
        sequence,
        prefix="RIT",
        label="Review Item ID",
    )


def next_review_item_id(
    occupied_identifiers: Iterable[str],
) -> str:
    """Return the next Review Item ID without reusing gaps."""

    return _next_identifier(
        occupied_identifiers,
        sequence_reader=review_item_id_sequence,
        formatter=format_review_item_id,
        allocation_error=ReviewItemIdAllocationError,
        label="Review Item",
    )


def is_valid_scoped_review_action_id(
    value: object,
) -> bool:
    """Return whether value is a valid Scoped Review Action ID."""

    return _is_valid_identifier(
        value,
        pattern=SCOPED_REVIEW_ACTION_ID_PATTERN,
    )


def validate_scoped_review_action_id(
    value: object,
) -> str:
    """Validate and return one Scoped Review Action ID."""

    return _validate_identifier(
        value,
        pattern=SCOPED_REVIEW_ACTION_ID_PATTERN,
        label="scoped_review_action_id",
        prefix="SRA",
    )


def scoped_review_action_id_sequence(
    value: object,
) -> int:
    """Return the sequence represented by a scoped action ID."""

    return _identifier_sequence(
        value,
        validator=validate_scoped_review_action_id,
        prefix="SRA",
    )


def format_scoped_review_action_id(
    sequence: object,
) -> str:
    """Format one sequence as a Scoped Review Action ID."""

    return _format_identifier(
        sequence,
        prefix="SRA",
        label="Scoped Review Action ID",
    )


def next_scoped_review_action_id(
    occupied_identifiers: Iterable[str],
) -> str:
    """Return the next Scoped Review Action ID without reusing gaps."""

    return _next_identifier(
        occupied_identifiers,
        sequence_reader=scoped_review_action_id_sequence,
        formatter=format_scoped_review_action_id,
        allocation_error=ScopedReviewActionIdAllocationError,
        label="Scoped Review Action",
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
        MIN_REVIEW_IDENTIFIER_SEQUENCE
        <= sequence
        <= MAX_REVIEW_IDENTIFIER_SEQUENCE
    )


def _validate_identifier(
    value: object,
    *,
    pattern: Pattern[str],
    label: str,
    prefix: str,
) -> str:
    """Validate one Review Workspace identifier."""

    if not isinstance(value, str):
        raise ReviewValidationError(
            f"{label} must be a string."
        )

    match = pattern.fullmatch(value)

    if match is None:
        raise ReviewValidationError(
            f"{label} must match "
            f"^{prefix}-[0-9]{{6}}$."
        )

    sequence = int(match.group(1))

    if not (
        MIN_REVIEW_IDENTIFIER_SEQUENCE
        <= sequence
        <= MAX_REVIEW_IDENTIFIER_SEQUENCE
    ):
        raise ReviewValidationError(
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
    """Format one Review Workspace identifier sequence."""

    if isinstance(sequence, bool) or not isinstance(
        sequence,
        int,
    ):
        raise ReviewValidationError(
            f"{label} sequence must be an integer."
        )

    if not (
        MIN_REVIEW_IDENTIFIER_SEQUENCE
        <= sequence
        <= MAX_REVIEW_IDENTIFIER_SEQUENCE
    ):
        raise ReviewValidationError(
            f"{label} sequence must be between "
            "1 and 999999."
        )

    return f"{prefix}-{sequence:06d}"


def _next_identifier(
    occupied_identifiers: Iterable[str],
    *,
    sequence_reader: Callable[[object], int],
    formatter: Callable[[object], str],
    allocation_error: type[ReviewIdentifierAllocationError],
    label: str,
) -> str:
    """Allocate the next sequential identifier."""

    if isinstance(occupied_identifiers, (str, bytes)):
        raise allocation_error(
            f"occupied identifiers for {label} must be an "
            "iterable of identifiers."
        )

    try:
        identifiers = tuple(occupied_identifiers)
    except TypeError as exc:
        raise allocation_error(
            f"occupied identifiers for {label} must be iterable."
        ) from exc

    highest_sequence = 0
    seen_identifiers: set[str] = set()

    for identifier in identifiers:
        try:
            sequence = sequence_reader(identifier)
        except ReviewValidationError as exc:
            raise allocation_error(
                f"occupied identifiers for {label} contain an "
                "invalid identifier."
            ) from exc

        if identifier in seen_identifiers:
            raise allocation_error(
                f"occupied identifiers for {label} must be unique."
            )

        seen_identifiers.add(identifier)
        highest_sequence = max(
            highest_sequence,
            sequence,
        )

    if highest_sequence >= MAX_REVIEW_IDENTIFIER_SEQUENCE:
        raise allocation_error(
            f"{label} identifier range is exhausted."
        )

    return formatter(highest_sequence + 1)
