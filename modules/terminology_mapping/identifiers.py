"""Identifiers for terminology and ontology mapping candidates."""

from __future__ import annotations

from collections.abc import Iterable
import re

from .errors import (
    TerminologyMappingError,
    TerminologyMappingAgentCandidateIdAllocationError,
    TerminologyMappingCandidateIdAllocationError,
    TerminologyMappingValidationError,
)


TERMINOLOGY_MAPPING_AGENT_CANDIDATE_ID_PATTERN = re.compile(
    r"^TMAC-([0-9]{6})$"
)
TERMINOLOGY_MAPPING_CANDIDATE_ID_PATTERN = re.compile(
    r"^TMC-([0-9]{6})$"
)

MIN_TERMINOLOGY_MAPPING_SEQUENCE = 1
MAX_TERMINOLOGY_MAPPING_SEQUENCE = 999_999


def is_valid_terminology_mapping_agent_candidate_id(
    value: object,
) -> bool:
    """Return whether value is a valid result-local agent candidate ID."""

    return _is_valid_identifier(
        value,
        TERMINOLOGY_MAPPING_AGENT_CANDIDATE_ID_PATTERN,
        "TMAC-000000",
    )


def validate_terminology_mapping_agent_candidate_id(
    value: object,
) -> str:
    """Validate and return one result-local agent candidate ID."""

    return _validate_identifier(
        value,
        pattern=(
            TERMINOLOGY_MAPPING_AGENT_CANDIDATE_ID_PATTERN
        ),
        zero_value="TMAC-000000",
        label="terminology_mapping_agent_candidate_id",
        prefix="TMAC",
    )


def terminology_mapping_agent_candidate_id_sequence(
    value: object,
) -> int:
    """Return the sequence represented by an agent candidate ID."""

    validated = (
        validate_terminology_mapping_agent_candidate_id(value)
    )
    return int(validated.removeprefix("TMAC-"))


def format_terminology_mapping_agent_candidate_id(
    sequence: object,
) -> str:
    """Format a sequence as a result-local agent candidate ID."""

    return _format_identifier(
        sequence,
        prefix="TMAC",
        label="Terminology Mapping Agent Candidate ID",
    )


def next_terminology_mapping_agent_candidate_id(
    occupied_candidate_ids: Iterable[str],
) -> str:
    """Return the next result-local ID without reusing gaps."""

    return _next_identifier(
        occupied_candidate_ids,
        validator=(
            validate_terminology_mapping_agent_candidate_id
        ),
        sequence_reader=(
            terminology_mapping_agent_candidate_id_sequence
        ),
        formatter=(
            format_terminology_mapping_agent_candidate_id
        ),
        error_type=(
            TerminologyMappingAgentCandidateIdAllocationError
        ),
        label="Terminology Mapping Agent Candidate ID",
    )


def is_valid_terminology_mapping_candidate_id(
    value: object,
) -> bool:
    """Return whether value is a valid persistent mapping candidate ID."""

    return _is_valid_identifier(
        value,
        TERMINOLOGY_MAPPING_CANDIDATE_ID_PATTERN,
        "TMC-000000",
    )


def validate_terminology_mapping_candidate_id(
    value: object,
) -> str:
    """Validate and return one persistent mapping candidate ID."""

    return _validate_identifier(
        value,
        pattern=TERMINOLOGY_MAPPING_CANDIDATE_ID_PATTERN,
        zero_value="TMC-000000",
        label="terminology_mapping_candidate_id",
        prefix="TMC",
    )


def terminology_mapping_candidate_id_sequence(
    value: object,
) -> int:
    """Return the sequence represented by a mapping candidate ID."""

    validated = validate_terminology_mapping_candidate_id(
        value
    )
    return int(validated.removeprefix("TMC-"))


def format_terminology_mapping_candidate_id(
    sequence: object,
) -> str:
    """Format a sequence as a persistent mapping candidate ID."""

    return _format_identifier(
        sequence,
        prefix="TMC",
        label="Terminology Mapping Candidate ID",
    )


def next_terminology_mapping_candidate_id(
    occupied_candidate_ids: Iterable[str],
) -> str:
    """Return the next persistent ID without reusing gaps."""

    return _next_identifier(
        occupied_candidate_ids,
        validator=validate_terminology_mapping_candidate_id,
        sequence_reader=(
            terminology_mapping_candidate_id_sequence
        ),
        formatter=format_terminology_mapping_candidate_id,
        error_type=TerminologyMappingCandidateIdAllocationError,
        label="Terminology Mapping Candidate ID",
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
        raise TerminologyMappingValidationError(
            f"{label} must be a string."
        )
    if pattern.fullmatch(value) is None:
        raise TerminologyMappingValidationError(
            f"{label} must match ^{prefix}-[0-9]{{6}}$."
        )
    if value == zero_value:
        raise TerminologyMappingValidationError(
            f"{label} sequence must be between 000001 and "
            "999999."
        )
    return value


def _format_identifier(
    sequence: object,
    *,
    prefix: str,
    label: str,
) -> str:
    if isinstance(sequence, bool) or not isinstance(
        sequence,
        int,
    ):
        raise TerminologyMappingValidationError(
            f"{label} sequence must be an integer."
        )
    if not (
        MIN_TERMINOLOGY_MAPPING_SEQUENCE
        <= sequence
        <= MAX_TERMINOLOGY_MAPPING_SEQUENCE
    ):
        raise TerminologyMappingValidationError(
            f"{label} sequence must be between 1 and 999999."
        )
    return f"{prefix}-{sequence:06d}"


def _next_identifier(
    occupied_candidate_ids: Iterable[str],
    *,
    validator: object,
    sequence_reader: object,
    formatter: object,
    error_type: type[TerminologyMappingError],
    label: str,
) -> str:
    if isinstance(occupied_candidate_ids, (str, bytes)):
        raise error_type(
            f"occupied_candidate_ids must be an iterable of "
            f"{label} values."
        )

    try:
        identifiers = tuple(occupied_candidate_ids)
    except TypeError as exc:
        raise error_type(
            "occupied_candidate_ids must be iterable."
        ) from exc

    try:
        for identifier in identifiers:
            validator(identifier)
    except TerminologyMappingValidationError as exc:
        raise error_type(
            f"Invalid occupied {label}: {identifier!r}."
        ) from exc

    if len(identifiers) != len(set(identifiers)):
        raise error_type(
            f"Duplicate occupied {label} values are not "
            "allowed."
        )

    highest_sequence = max(
        (
            sequence_reader(identifier)
            for identifier in identifiers
        ),
        default=0,
    )
    if highest_sequence >= MAX_TERMINOLOGY_MAPPING_SEQUENCE:
        raise error_type(
            f"{label} range is exhausted at "
            f"{formatter(MAX_TERMINOLOGY_MAPPING_SEQUENCE)}."
        )
    return formatter(highest_sequence + 1)