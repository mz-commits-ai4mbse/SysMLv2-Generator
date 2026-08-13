"""Stable identifiers and generated symbols for Phase-J SysML v2 generation."""

from __future__ import annotations

import re

from modules.internal_model.identifiers import (
    validate_internal_model_element_id,
    validate_internal_model_relationship_id,
)

from .errors import SysMLGenerationValidationError


GENERATED_SYSML_UNIT_ID_PATTERN = re.compile(r"^GSU-([0-9]{6})$")
GENERATED_SYSML_SYMBOL_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

MIN_GENERATED_SYSML_UNIT_SEQUENCE = 1
MAX_GENERATED_SYSML_UNIT_SEQUENCE = 999_999


def validate_generated_sysml_unit_id(value: object) -> str:
    """Validate and return one generated SysML unit ID."""

    if not isinstance(value, str):
        raise SysMLGenerationValidationError(
            "generated_sysml_unit_id must be a string."
        )
    if GENERATED_SYSML_UNIT_ID_PATTERN.fullmatch(value) is None:
        raise SysMLGenerationValidationError(
            "generated_sysml_unit_id must match ^GSU-[0-9]{6}$."
        )
    if value == "GSU-000000":
        raise SysMLGenerationValidationError(
            "generated_sysml_unit_id sequence must be between 000001 and 999999."
        )
    return value


def format_generated_sysml_unit_id(sequence: object) -> str:
    """Format a positive sequence as a generated SysML unit ID."""

    if isinstance(sequence, bool) or not isinstance(sequence, int):
        raise SysMLGenerationValidationError(
            "Generated SysML unit sequence must be an integer."
        )
    if not (
        MIN_GENERATED_SYSML_UNIT_SEQUENCE
        <= sequence
        <= MAX_GENERATED_SYSML_UNIT_SEQUENCE
    ):
        raise SysMLGenerationValidationError(
            "Generated SysML unit sequence must be between 1 and 999999."
        )
    return f"GSU-{sequence:06d}"


def validate_generated_sysml_symbol(value: object) -> str:
    """Validate a machine-safe symbol from the deliberately small J1 subset."""

    if not isinstance(value, str):
        raise SysMLGenerationValidationError(
            "generated SysML symbol must be a string."
        )
    if GENERATED_SYSML_SYMBOL_PATTERN.fullmatch(value) is None:
        raise SysMLGenerationValidationError(
            "generated SysML symbol must match "
            "^[A-Za-z_][A-Za-z0-9_]*$."
        )
    return value


def generated_element_symbol(
    internal_model_element_id: object,
) -> str:
    """Return the stable generated symbol for one IME identity."""

    try:
        validated = validate_internal_model_element_id(
            internal_model_element_id
        )
    except Exception as exc:
        raise SysMLGenerationValidationError(
            "internal_model_element_id is invalid for symbol generation."
        ) from exc
    return validate_generated_sysml_symbol(validated.replace("-", "_"))


def generated_relationship_symbol(
    internal_model_relationship_id: object,
) -> str:
    """Return the stable trace symbol for one IMR identity."""

    try:
        validated = validate_internal_model_relationship_id(
            internal_model_relationship_id
        )
    except Exception as exc:
        raise SysMLGenerationValidationError(
            "internal_model_relationship_id is invalid for symbol generation."
        ) from exc
    return validate_generated_sysml_symbol(validated.replace("-", "_"))
