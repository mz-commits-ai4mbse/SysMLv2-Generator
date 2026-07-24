"""Deterministic comparison rules for Project Glossary labels."""

from __future__ import annotations

import re
import unicodedata

from modules.project_glossary.errors import (
    ProjectGlossaryValidationError,
)


_LANGUAGE_CODE_PATTERN = re.compile(r"^[a-z]{2}$")


def is_valid_language_code(value: object) -> bool:
    """Return whether a value is a supported P4 language code."""

    return (
        isinstance(value, str)
        and _LANGUAGE_CODE_PATTERN.fullmatch(value)
        is not None
    )


def require_language_code(
    value: object,
    label: str = "language",
) -> str:
    """Require a lowercase two-letter language code."""

    if not is_valid_language_code(value):
        raise ProjectGlossaryValidationError(
            f"{label} must contain exactly two lowercase "
            "ASCII letters."
        )

    return value


def require_stored_glossary_text(
    value: object,
    label: str,
) -> str:
    """Require non-empty stored text without outer whitespace."""

    if not isinstance(value, str) or not value.strip():
        raise ProjectGlossaryValidationError(
            f"{label} must be a non-empty string."
        )

    if value != value.strip():
        raise ProjectGlossaryValidationError(
            f"{label} must not contain surrounding whitespace."
        )

    return value


def normalize_label_for_comparison(
    value: object,
    label: str = "label",
) -> str:
    """Create the accepted NFKC, trim and casefold key."""

    if not isinstance(value, str):
        raise ProjectGlossaryValidationError(
            f"{label} must be a string."
        )

    normalized = unicodedata.normalize("NFKC", value)
    normalized = normalized.strip()
    normalized = normalized.casefold()

    if not normalized:
        raise ProjectGlossaryValidationError(
            f"{label} must not normalize to an empty value."
        )

    return normalized


def localized_label_comparison_key(
    language: object,
    text: object,
    *,
    label: str = "localized label",
) -> tuple[str, str]:
    """Return the project-language and normalized-label key."""

    validated_language = require_language_code(
        language,
        f"{label}.language",
    )
    normalized_text = normalize_label_for_comparison(
        text,
        f"{label}.text",
    )

    return validated_language, normalized_text