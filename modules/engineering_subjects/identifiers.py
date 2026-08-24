"""Identifiers for canonical engineering-subject discovery."""

from __future__ import annotations

import re

from .errors import EngineeringSubjectValidationError


_SPAN_PATTERN = re.compile(r"^SPAN-([0-9]{6})$")
_TOKEN_PATTERN = re.compile(r"^TOK-([0-9]{6})$")
_MENTION_PATTERN = re.compile(r"^MNT-([0-9]{6})$")
_SUBJECT_PATTERN = re.compile(r"^SUBJ-([0-9]{6})$")


def _format(prefix: str, sequence: object) -> str:
    if isinstance(sequence, bool) or not isinstance(sequence, int):
        raise EngineeringSubjectValidationError(
            f"{prefix} sequence must be an integer."
        )
    if not 1 <= sequence <= 999_999:
        raise EngineeringSubjectValidationError(
            f"{prefix} sequence must be between 1 and 999999."
        )
    return f"{prefix}-{sequence:06d}"


def _validate(value: object, pattern: re.Pattern[str], label: str) -> str:
    if not isinstance(value, str) or pattern.fullmatch(value) is None:
        raise EngineeringSubjectValidationError(
            f"{label} has an invalid identifier."
        )
    if int(value.rsplit("-", 1)[1]) < 1:
        raise EngineeringSubjectValidationError(
            f"{label} sequence must be at least 000001."
        )
    return value


def format_source_span_id(sequence: object) -> str:
    return _format("SPAN", sequence)


def format_source_token_id(sequence: object) -> str:
    return _format("TOK", sequence)


def format_engineering_mention_id(sequence: object) -> str:
    return _format("MNT", sequence)


def format_canonical_subject_id(sequence: object) -> str:
    return _format("SUBJ", sequence)


def validate_source_span_id(value: object) -> str:
    return _validate(value, _SPAN_PATTERN, "source_span_id")


def validate_source_token_id(value: object) -> str:
    return _validate(value, _TOKEN_PATTERN, "source_token_id")


def validate_engineering_mention_id(value: object) -> str:
    return _validate(value, _MENTION_PATTERN, "mention_id")


def validate_canonical_subject_id(value: object) -> str:
    return _validate(value, _SUBJECT_PATTERN, "canonical_subject_id")
