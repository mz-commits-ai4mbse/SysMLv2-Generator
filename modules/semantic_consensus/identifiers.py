"""Result-local identifiers for semantic consensus candidates."""

from __future__ import annotations

from collections.abc import Iterable
import re

from .errors import (
    SemanticConsensusCandidateIdAllocationError,
    SemanticConsensusValidationError,
)


SEMANTIC_CONSENSUS_CANDIDATE_ID_PATTERN = re.compile(
    r"^SCC-([0-9]{6})$"
)

MIN_SEMANTIC_CONSENSUS_CANDIDATE_SEQUENCE = 1
MAX_SEMANTIC_CONSENSUS_CANDIDATE_SEQUENCE = 999_999


def is_valid_semantic_consensus_candidate_id(
    value: object,
) -> bool:
    """Return whether a value is a valid consensus-candidate ID."""

    return (
        isinstance(value, str)
        and SEMANTIC_CONSENSUS_CANDIDATE_ID_PATTERN.fullmatch(
            value
        )
        is not None
        and value != "SCC-000000"
    )


def validate_semantic_consensus_candidate_id(
    value: object,
) -> str:
    """Validate and return a result-local consensus-candidate ID."""

    if not isinstance(value, str):
        raise SemanticConsensusValidationError(
            "consensus_candidate_id must be a string."
        )

    match = (
        SEMANTIC_CONSENSUS_CANDIDATE_ID_PATTERN.fullmatch(
            value
        )
    )

    if match is None:
        raise SemanticConsensusValidationError(
            "consensus_candidate_id must match "
            "^SCC-[0-9]{6}$."
        )

    sequence = int(match.group(1))

    if sequence < MIN_SEMANTIC_CONSENSUS_CANDIDATE_SEQUENCE:
        raise SemanticConsensusValidationError(
            "consensus_candidate_id sequence must be between "
            "000001 and 999999."
        )

    return value


def semantic_consensus_candidate_id_sequence(
    value: object,
) -> int:
    """Return the sequence represented by a consensus-candidate ID."""

    validated_id = (
        validate_semantic_consensus_candidate_id(value)
    )
    return int(validated_id.removeprefix("SCC-"))


def format_semantic_consensus_candidate_id(
    sequence: object,
) -> str:
    """Format a sequence as a valid consensus-candidate ID."""

    if isinstance(sequence, bool) or not isinstance(
        sequence,
        int,
    ):
        raise SemanticConsensusValidationError(
            "Semantic Consensus Candidate ID sequence "
            "must be an integer."
        )

    if not (
        MIN_SEMANTIC_CONSENSUS_CANDIDATE_SEQUENCE
        <= sequence
        <= MAX_SEMANTIC_CONSENSUS_CANDIDATE_SEQUENCE
    ):
        raise SemanticConsensusValidationError(
            "Semantic Consensus Candidate ID sequence "
            "must be between 1 and 999999."
        )

    return f"SCC-{sequence:06d}"


def next_semantic_consensus_candidate_id(
    occupied_candidate_ids: Iterable[str],
) -> str:
    """Return the next sequential ID without reusing gaps."""

    if isinstance(occupied_candidate_ids, (str, bytes)):
        raise SemanticConsensusCandidateIdAllocationError(
            "occupied_candidate_ids must be an iterable of "
            "Semantic Consensus Candidate IDs."
        )

    try:
        identifiers = tuple(occupied_candidate_ids)
    except TypeError as exc:
        raise SemanticConsensusCandidateIdAllocationError(
            "occupied_candidate_ids must be iterable."
        ) from exc

    for candidate_id in identifiers:
        if not is_valid_semantic_consensus_candidate_id(
            candidate_id
        ):
            raise SemanticConsensusCandidateIdAllocationError(
                "Invalid occupied Semantic Consensus Candidate "
                f"ID: {candidate_id!r}."
            )

    if len(identifiers) != len(set(identifiers)):
        raise SemanticConsensusCandidateIdAllocationError(
            "Duplicate occupied Semantic Consensus Candidate "
            "IDs are not allowed."
        )

    highest_sequence = max(
        (
            semantic_consensus_candidate_id_sequence(
                identifier
            )
            for identifier in identifiers
        ),
        default=0,
    )

    if (
        highest_sequence
        >= MAX_SEMANTIC_CONSENSUS_CANDIDATE_SEQUENCE
    ):
        raise SemanticConsensusCandidateIdAllocationError(
            "Semantic Consensus Candidate ID range is "
            "exhausted at SCC-999999."
        )

    return format_semantic_consensus_candidate_id(
        highest_sequence + 1
    )