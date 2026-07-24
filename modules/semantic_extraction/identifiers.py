"""Result-local identifiers for Information Unit Candidates."""

from __future__ import annotations

from collections.abc import Iterable
import re

from .errors import (
    InformationUnitCandidateIdAllocationError,
    SemanticExtractionValidationError,
)


INFORMATION_UNIT_CANDIDATE_ID_PATTERN = re.compile(
    r"^IUC-([0-9]{6})$"
)

MIN_INFORMATION_UNIT_CANDIDATE_SEQUENCE = 1
MAX_INFORMATION_UNIT_CANDIDATE_SEQUENCE = 999_999


def is_valid_information_unit_candidate_id(
    value: object,
) -> bool:
    """Return whether a value is a valid candidate ID."""

    return (
        isinstance(value, str)
        and INFORMATION_UNIT_CANDIDATE_ID_PATTERN.fullmatch(
            value
        )
        is not None
        and value != "IUC-000000"
    )


def validate_information_unit_candidate_id(
    value: object,
) -> str:
    """Validate and return a result-local candidate ID."""

    if not isinstance(value, str):
        raise SemanticExtractionValidationError(
            "candidate_id must be a string."
        )

    match = (
        INFORMATION_UNIT_CANDIDATE_ID_PATTERN.fullmatch(
            value
        )
    )

    if match is None:
        raise SemanticExtractionValidationError(
            "candidate_id must match ^IUC-[0-9]{6}$."
        )

    sequence = int(match.group(1))

    if sequence < MIN_INFORMATION_UNIT_CANDIDATE_SEQUENCE:
        raise SemanticExtractionValidationError(
            "candidate_id sequence must be between "
            "000001 and 999999."
        )

    return value


def information_unit_candidate_id_sequence(
    value: object,
) -> int:
    """Return the sequence represented by a candidate ID."""

    validated_id = (
        validate_information_unit_candidate_id(value)
    )
    return int(validated_id.removeprefix("IUC-"))


def format_information_unit_candidate_id(
    sequence: object,
) -> str:
    """Format a sequence as a valid candidate ID."""

    if isinstance(sequence, bool) or not isinstance(
        sequence,
        int,
    ):
        raise SemanticExtractionValidationError(
            "Information Unit Candidate ID sequence "
            "must be an integer."
        )

    if not (
        MIN_INFORMATION_UNIT_CANDIDATE_SEQUENCE
        <= sequence
        <= MAX_INFORMATION_UNIT_CANDIDATE_SEQUENCE
    ):
        raise SemanticExtractionValidationError(
            "Information Unit Candidate ID sequence "
            "must be between 1 and 999999."
        )

    return f"IUC-{sequence:06d}"


def next_information_unit_candidate_id(
    occupied_candidate_ids: Iterable[str],
) -> str:
    """Return the next sequential ID without reusing gaps."""

    if isinstance(occupied_candidate_ids, (str, bytes)):
        raise InformationUnitCandidateIdAllocationError(
            "occupied_candidate_ids must be an iterable "
            "of Information Unit Candidate IDs."
        )

    try:
        identifiers = tuple(occupied_candidate_ids)
    except TypeError as exc:
        raise InformationUnitCandidateIdAllocationError(
            "occupied_candidate_ids must be iterable."
        ) from exc

    for candidate_id in identifiers:
        if not is_valid_information_unit_candidate_id(
            candidate_id
        ):
            raise InformationUnitCandidateIdAllocationError(
                "Invalid occupied Information Unit "
                f"Candidate ID: {candidate_id!r}."
            )

    if len(identifiers) != len(set(identifiers)):
        raise InformationUnitCandidateIdAllocationError(
            "Duplicate occupied Information Unit "
            "Candidate IDs are not allowed."
        )

    highest_sequence = max(
        (
            information_unit_candidate_id_sequence(
                identifier
            )
            for identifier in identifiers
        ),
        default=0,
    )

    if (
        highest_sequence
        >= MAX_INFORMATION_UNIT_CANDIDATE_SEQUENCE
    ):
        raise InformationUnitCandidateIdAllocationError(
            "Information Unit Candidate ID range is "
            "exhausted at IUC-999999."
        )

    return format_information_unit_candidate_id(
        highest_sequence + 1
    )