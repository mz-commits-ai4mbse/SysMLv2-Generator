"""Stable project-local identifiers for Phase-L Final Model Review."""

from __future__ import annotations

from collections.abc import Iterable
import re

from .errors import (
    FinalModelReviewIdAllocationError,
    FinalModelReviewValidationError,
)


MIN_SEQUENCE = 1
MAX_SEQUENCE = 999_999

_PREFIXES = {
    "final_model_review_id": "FMR",
    "final_model_review_revision_id": "FRV",
    "final_model_review_item_id": "FRI",
    "final_model_review_decision_id": "FRD",
    "final_model_review_change_proposal_id": "FCP",
}

_PATTERNS = {
    label: re.compile(rf"^{prefix}-([0-9]{{6}})$")
    for label, prefix in _PREFIXES.items()
}


def _validate(value: object, *, label: str) -> str:
    prefix = _PREFIXES[label]
    pattern = _PATTERNS[label]
    if not isinstance(value, str) or pattern.fullmatch(value) is None:
        raise FinalModelReviewValidationError(
            f"{label} must match ^{prefix}-[0-9]{{6}}$."
        )
    if value == f"{prefix}-000000":
        raise FinalModelReviewValidationError(
            f"{label} sequence must be between 000001 and 999999."
        )
    return value


def _sequence(value: object, *, label: str) -> int:
    validated = _validate(value, label=label)
    return int(validated.rsplit("-", 1)[1])


def _format(sequence: object, *, label: str) -> str:
    if isinstance(sequence, bool) or not isinstance(sequence, int):
        raise FinalModelReviewValidationError(
            f"{label} sequence must be an integer."
        )
    if not MIN_SEQUENCE <= sequence <= MAX_SEQUENCE:
        raise FinalModelReviewValidationError(
            f"{label} sequence must be between 1 and 999999."
        )
    return f"{_PREFIXES[label]}-{sequence:06d}"


def _next(occupied_ids: Iterable[str], *, label: str) -> str:
    if isinstance(occupied_ids, (str, bytes)):
        raise FinalModelReviewIdAllocationError(
            f"occupied {label} values must be an iterable of IDs."
        )
    try:
        identifiers = tuple(occupied_ids)
    except TypeError as exc:
        raise FinalModelReviewIdAllocationError(
            f"occupied {label} values must be iterable."
        ) from exc
    if len(identifiers) != len(set(identifiers)):
        raise FinalModelReviewIdAllocationError(
            f"duplicate occupied {label} values are not allowed."
        )
    try:
        sequences = tuple(
            _sequence(item, label=label)
            for item in identifiers
        )
    except FinalModelReviewValidationError as exc:
        raise FinalModelReviewIdAllocationError(
            f"occupied {label} values contain an invalid ID."
        ) from exc
    highest = max(sequences, default=0)
    if highest >= MAX_SEQUENCE:
        raise FinalModelReviewIdAllocationError(
            f"{label} range is exhausted."
        )
    return _format(highest + 1, label=label)


def validate_final_model_review_id(value: object) -> str:
    return _validate(value, label="final_model_review_id")


def final_model_review_id_sequence(value: object) -> int:
    return _sequence(value, label="final_model_review_id")


def format_final_model_review_id(sequence: object) -> str:
    return _format(sequence, label="final_model_review_id")


def next_final_model_review_id(occupied_ids: Iterable[str]) -> str:
    return _next(occupied_ids, label="final_model_review_id")


def validate_final_model_review_revision_id(value: object) -> str:
    return _validate(value, label="final_model_review_revision_id")


def final_model_review_revision_id_sequence(value: object) -> int:
    return _sequence(value, label="final_model_review_revision_id")


def format_final_model_review_revision_id(sequence: object) -> str:
    return _format(sequence, label="final_model_review_revision_id")


def next_final_model_review_revision_id(
    occupied_ids: Iterable[str],
) -> str:
    return _next(
        occupied_ids,
        label="final_model_review_revision_id",
    )


def validate_final_model_review_item_id(value: object) -> str:
    return _validate(value, label="final_model_review_item_id")


def final_model_review_item_id_sequence(value: object) -> int:
    return _sequence(value, label="final_model_review_item_id")


def format_final_model_review_item_id(sequence: object) -> str:
    return _format(sequence, label="final_model_review_item_id")


def next_final_model_review_item_id(occupied_ids: Iterable[str]) -> str:
    return _next(occupied_ids, label="final_model_review_item_id")


def validate_final_model_review_decision_id(value: object) -> str:
    return _validate(value, label="final_model_review_decision_id")


def final_model_review_decision_id_sequence(value: object) -> int:
    return _sequence(value, label="final_model_review_decision_id")


def format_final_model_review_decision_id(sequence: object) -> str:
    return _format(sequence, label="final_model_review_decision_id")


def next_final_model_review_decision_id(
    occupied_ids: Iterable[str],
) -> str:
    return _next(
        occupied_ids,
        label="final_model_review_decision_id",
    )


def validate_final_model_review_change_proposal_id(value: object) -> str:
    return _validate(value, label="final_model_review_change_proposal_id")


def final_model_review_change_proposal_id_sequence(value: object) -> int:
    return _sequence(value, label="final_model_review_change_proposal_id")


def format_final_model_review_change_proposal_id(sequence: object) -> str:
    return _format(sequence, label="final_model_review_change_proposal_id")


def next_final_model_review_change_proposal_id(
    occupied_ids: Iterable[str],
) -> str:
    return _next(
        occupied_ids,
        label="final_model_review_change_proposal_id",
    )
