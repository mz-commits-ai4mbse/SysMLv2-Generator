"""Stable project-local IDs for Phase-H Candidate Review Decisions."""

from __future__ import annotations

from collections.abc import Iterable
import re

from .errors import (
    ModelCandidateReviewDecisionIdAllocationError,
    ModelCandidateValidationError,
)


MODEL_CANDIDATE_REVIEW_DECISION_ID_PATTERN = re.compile(
    r"^MCD-([0-9]{6})$"
)
MIN_MODEL_CANDIDATE_REVIEW_DECISION_SEQUENCE = 1
MAX_MODEL_CANDIDATE_REVIEW_DECISION_SEQUENCE = 999_999


def is_valid_model_candidate_review_decision_id(value: object) -> bool:
    return (
        isinstance(value, str)
        and MODEL_CANDIDATE_REVIEW_DECISION_ID_PATTERN.fullmatch(value)
        is not None
        and value != "MCD-000000"
    )


def validate_model_candidate_review_decision_id(value: object) -> str:
    if not is_valid_model_candidate_review_decision_id(value):
        raise ModelCandidateValidationError(
            "model_candidate_review_decision_id must match "
            "^MCD-[0-9]{6}$ with sequence 000001..999999."
        )
    return value


def model_candidate_review_decision_id_sequence(value: object) -> int:
    validated = validate_model_candidate_review_decision_id(value)
    return int(validated.removeprefix("MCD-"))


def format_model_candidate_review_decision_id(sequence: object) -> str:
    if isinstance(sequence, bool) or not isinstance(sequence, int):
        raise ModelCandidateValidationError(
            "Model Candidate Review Decision sequence must be an integer."
        )
    if not (
        MIN_MODEL_CANDIDATE_REVIEW_DECISION_SEQUENCE
        <= sequence
        <= MAX_MODEL_CANDIDATE_REVIEW_DECISION_SEQUENCE
    ):
        raise ModelCandidateValidationError(
            "Model Candidate Review Decision sequence must be between "
            "1 and 999999."
        )
    return f"MCD-{sequence:06d}"


def next_model_candidate_review_decision_id(
    occupied_decision_ids: Iterable[str],
) -> str:
    if isinstance(occupied_decision_ids, (str, bytes)):
        raise ModelCandidateReviewDecisionIdAllocationError(
            "occupied_decision_ids must be an iterable of MCD IDs."
        )
    try:
        identifiers = tuple(occupied_decision_ids)
    except TypeError as exc:
        raise ModelCandidateReviewDecisionIdAllocationError(
            "occupied_decision_ids must be iterable."
        ) from exc
    try:
        sequences = tuple(
            model_candidate_review_decision_id_sequence(item)
            for item in identifiers
        )
    except ModelCandidateValidationError as exc:
        raise ModelCandidateReviewDecisionIdAllocationError(
            "occupied_decision_ids contains an invalid MCD ID."
        ) from exc
    if len(identifiers) != len(set(identifiers)):
        raise ModelCandidateReviewDecisionIdAllocationError(
            "Duplicate occupied MCD IDs are not allowed."
        )
    highest = max(sequences, default=0)
    if highest >= MAX_MODEL_CANDIDATE_REVIEW_DECISION_SEQUENCE:
        raise ModelCandidateReviewDecisionIdAllocationError(
            "Model Candidate Review Decision ID range is exhausted."
        )
    return format_model_candidate_review_decision_id(highest + 1)
