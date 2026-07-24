"""Stable six-digit Human Review Decision identifiers."""

from __future__ import annotations

from collections.abc import Iterable
import re

from .errors import (
    HumanReviewDecisionIdAllocationError,
    HumanReviewValidationError,
)


HUMAN_REVIEW_DECISION_ID_PATTERN = re.compile(
    r"^HRD-([0-9]{6})$"
)
MIN_HUMAN_REVIEW_DECISION_SEQUENCE = 1
MAX_HUMAN_REVIEW_DECISION_SEQUENCE = 999_999


def is_valid_human_review_decision_id(value: object) -> bool:
    """Return whether value is a valid Human Review Decision ID."""

    return (
        isinstance(value, str)
        and HUMAN_REVIEW_DECISION_ID_PATTERN.fullmatch(value)
        is not None
        and value != "HRD-000000"
    )


def validate_human_review_decision_id(value: object) -> str:
    """Validate and return one Human Review Decision ID."""

    if not isinstance(value, str):
        raise HumanReviewValidationError(
            "human_review_decision_id must be a string."
        )
    if HUMAN_REVIEW_DECISION_ID_PATTERN.fullmatch(value) is None:
        raise HumanReviewValidationError(
            "human_review_decision_id must match "
            "^HRD-[0-9]{6}$."
        )
    if value == "HRD-000000":
        raise HumanReviewValidationError(
            "human_review_decision_id sequence must be between "
            "000001 and 999999."
        )
    return value


def human_review_decision_id_sequence(value: object) -> int:
    """Return the sequence represented by a decision ID."""

    validated = validate_human_review_decision_id(value)
    return int(validated.removeprefix("HRD-"))


def format_human_review_decision_id(sequence: object) -> str:
    """Format one positive sequence as a decision ID."""

    if isinstance(sequence, bool) or not isinstance(sequence, int):
        raise HumanReviewValidationError(
            "Human Review Decision ID sequence must be an integer."
        )
    if not (
        MIN_HUMAN_REVIEW_DECISION_SEQUENCE
        <= sequence
        <= MAX_HUMAN_REVIEW_DECISION_SEQUENCE
    ):
        raise HumanReviewValidationError(
            "Human Review Decision ID sequence must be between "
            "1 and 999999."
        )
    return f"HRD-{sequence:06d}"


def next_human_review_decision_id(
    occupied_decision_ids: Iterable[str],
) -> str:
    """Return the next ID after the highest occupied sequence."""

    if isinstance(occupied_decision_ids, (str, bytes)):
        raise HumanReviewDecisionIdAllocationError(
            "occupied_decision_ids must be an iterable of IDs."
        )
    try:
        identifiers = tuple(occupied_decision_ids)
    except TypeError as exc:
        raise HumanReviewDecisionIdAllocationError(
            "occupied_decision_ids must be iterable."
        ) from exc
    try:
        for identifier in identifiers:
            validate_human_review_decision_id(identifier)
    except HumanReviewValidationError as exc:
        raise HumanReviewDecisionIdAllocationError(
            f"Invalid occupied Human Review Decision ID: "
            f"{identifier!r}."
        ) from exc
    if len(identifiers) != len(set(identifiers)):
        raise HumanReviewDecisionIdAllocationError(
            "Duplicate occupied Human Review Decision IDs are not "
            "allowed."
        )
    highest = max(
        (
            human_review_decision_id_sequence(identifier)
            for identifier in identifiers
        ),
        default=0,
    )
    if highest >= MAX_HUMAN_REVIEW_DECISION_SEQUENCE:
        raise HumanReviewDecisionIdAllocationError(
            "Human Review Decision ID range is exhausted at "
            "HRD-999999."
        )
    return format_human_review_decision_id(highest + 1)