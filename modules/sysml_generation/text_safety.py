"""Deterministic safe-text rules used before Phase-J rendering."""

from __future__ import annotations

from .errors import SysMLGenerationValidationError


_BLOCK_COMMENT_DELIMITERS = ("/*", "*/")


def normalize_engineering_text(
    value: object,
    *,
    label: str,
    allow_empty: bool,
) -> str:
    """Return canonical safe text for later SysML documentation rendering.

    Engineering names remain separate from stable machine symbols.

    Human-readable engineering text is projected only into controlled SysML
    documentation blocks in the J4 MVP renderer. Raw block-comment delimiters
    are therefore rejected rather than rewritten, because rewriting accepted
    engineering text would silently change source content.
    """

    if not isinstance(value, str):
        raise SysMLGenerationValidationError(
            f"{label} must be a string."
        )

    normalized = value.replace("\r\n", "\n").replace("\r", "\n")

    if not allow_empty and not normalized.strip():
        raise SysMLGenerationValidationError(
            f"{label} must not be empty."
        )
    if "\x00" in normalized:
        raise SysMLGenerationValidationError(
            f"{label} must not contain NUL characters."
        )

    for delimiter in _BLOCK_COMMENT_DELIMITERS:
        if delimiter in normalized:
            raise SysMLGenerationValidationError(
                f"{label} contains the SysML documentation block delimiter "
                f"{delimiter!r}."
            )

    try:
        normalized.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise SysMLGenerationValidationError(
            f"{label} must be valid UTF-8 encodable text."
        ) from exc

    return normalized


def normalize_optional_engineering_text(
    value: object,
    *,
    label: str,
) -> str | None:
    """Normalize optional human-readable engineering text."""

    if value is None:
        return None
    return normalize_engineering_text(
        value,
        label=label,
        allow_empty=True,
    )
