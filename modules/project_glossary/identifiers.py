"""Stable project-local identifiers for glossary artifacts."""

from __future__ import annotations

from collections.abc import Callable, Iterable
import re

from modules.project_glossary.errors import (
    AmbiguityGroupIdAllocationError,
    ProjectConceptIdAllocationError,
    ProjectGlossaryError,
    TerminologyDecisionError,
)


PROJECT_CONCEPT_ID_PATTERN = re.compile(
    r"^PC-[0-9]{6}$"
)
AMBIGUITY_GROUP_ID_PATTERN = re.compile(
    r"^AG-[0-9]{6}$"
)
TERMINOLOGY_DECISION_ID_PATTERN = re.compile(
    r"^TD-[0-9]{6}$"
)

MAX_GLOSSARY_IDENTIFIER_NUMBER = 999_999


def is_valid_project_concept_id(value: object) -> bool:
    """Return whether a value is a valid Project Concept ID."""

    return (
        isinstance(value, str)
        and PROJECT_CONCEPT_ID_PATTERN.fullmatch(value)
        is not None
        and value != "PC-000000"
    )


def is_valid_ambiguity_group_id(value: object) -> bool:
    """Return whether a value is a valid Ambiguity Group ID."""

    return (
        isinstance(value, str)
        and AMBIGUITY_GROUP_ID_PATTERN.fullmatch(value)
        is not None
        and value != "AG-000000"
    )


def is_valid_terminology_decision_id(
    value: object,
) -> bool:
    """Return whether a value is a valid Terminology Decision ID."""

    return (
        isinstance(value, str)
        and TERMINOLOGY_DECISION_ID_PATTERN.fullmatch(value)
        is not None
        and value != "TD-000000"
    )


def format_project_concept_id(number: int) -> str:
    """Format one positive Project Concept sequence number."""

    return _format_identifier(
        number,
        prefix="PC",
        label="Project Concept",
        error_type=ProjectConceptIdAllocationError,
    )


def format_ambiguity_group_id(number: int) -> str:
    """Format one positive Ambiguity Group sequence number."""

    return _format_identifier(
        number,
        prefix="AG",
        label="Ambiguity Group",
        error_type=AmbiguityGroupIdAllocationError,
    )


def format_terminology_decision_id(number: int) -> str:
    """Format one positive Terminology Decision sequence number."""

    return _format_identifier(
        number,
        prefix="TD",
        label="Terminology Decision",
        error_type=TerminologyDecisionError,
    )


def allocate_next_project_concept_id(
    existing_ids: Iterable[str],
) -> str:
    """Allocate the next Project Concept ID above the maximum."""

    return _allocate_next_identifier(
        existing_ids,
        validator=is_valid_project_concept_id,
        formatter=format_project_concept_id,
        label="Project Concept",
        error_type=ProjectConceptIdAllocationError,
    )


def allocate_next_ambiguity_group_id(
    existing_ids: Iterable[str],
) -> str:
    """Allocate the next Ambiguity Group ID above the maximum."""

    return _allocate_next_identifier(
        existing_ids,
        validator=is_valid_ambiguity_group_id,
        formatter=format_ambiguity_group_id,
        label="Ambiguity Group",
        error_type=AmbiguityGroupIdAllocationError,
    )


def allocate_next_terminology_decision_id(
    existing_ids: Iterable[str],
) -> str:
    """Allocate the next Terminology Decision ID above the maximum."""

    return _allocate_next_identifier(
        existing_ids,
        validator=is_valid_terminology_decision_id,
        formatter=format_terminology_decision_id,
        label="Terminology Decision",
        error_type=TerminologyDecisionError,
    )


def _format_identifier(
    number: int,
    *,
    prefix: str,
    label: str,
    error_type: type[ProjectGlossaryError],
) -> str:
    if (
        not isinstance(number, int)
        or isinstance(number, bool)
        or number < 1
        or number > MAX_GLOSSARY_IDENTIFIER_NUMBER
    ):
        raise error_type(
            f"{label} number must be an integer from 1 to "
            f"{MAX_GLOSSARY_IDENTIFIER_NUMBER}."
        )

    return f"{prefix}-{number:06d}"


def _allocate_next_identifier(
    existing_ids: Iterable[str],
    *,
    validator: Callable[[object], bool],
    formatter: Callable[[int], str],
    label: str,
    error_type: type[ProjectGlossaryError],
) -> str:
    if isinstance(existing_ids, (str, bytes)):
        raise error_type(
            f"{label} existing IDs must be an iterable of IDs."
        )

    try:
        identifiers = tuple(existing_ids)
    except TypeError as exc:
        raise error_type(
            f"{label} existing IDs must be iterable."
        ) from exc

    for identifier in identifiers:
        if not validator(identifier):
            raise error_type(
                f"Invalid existing {label} ID: {identifier!r}."
            )

    if len(identifiers) != len(set(identifiers)):
        raise error_type(
            f"Duplicate existing {label} IDs are not allowed."
        )

    highest_number = max(
        (
            int(identifier.rsplit("-", 1)[1])
            for identifier in identifiers
        ),
        default=0,
    )

    if highest_number >= MAX_GLOSSARY_IDENTIFIER_NUMBER:
        raise error_type(
            f"No {label} identifiers remain available."
        )

    return formatter(highest_number + 1)