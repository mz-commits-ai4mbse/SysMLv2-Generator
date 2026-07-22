"""Project identity generation, validation and name normalization."""

from __future__ import annotations

import re
import secrets
import unicodedata
from typing import Any


PROJECT_ID_LENGTH = 6
PROJECT_ID_SPACE_SIZE = 1_000_000

_PROJECT_ID_PATTERN = re.compile(r"^[0-9]{6}$")


def generate_project_id() -> str:
    """Generate one six-digit project-ID candidate.

    Workspace-level collision detection is intentionally handled by
    ``ProjectWorkspace``.
    """

    return f"{secrets.randbelow(PROJECT_ID_SPACE_SIZE):0{PROJECT_ID_LENGTH}d}"


def is_valid_project_id(value: Any) -> bool:
    """Return whether a value is a valid six-digit project identifier."""

    return (
        isinstance(value, str)
        and _PROJECT_ID_PATTERN.fullmatch(value) is not None
    )


def normalize_display_name(value: str) -> str:
    """Return the deterministic comparison form of a project display name."""

    if not isinstance(value, str):
        raise TypeError("display_name must be a string.")

    trimmed = value.strip()
    collapsed = " ".join(trimmed.split())
    normalized = unicodedata.normalize("NFKC", collapsed)

    return normalized.casefold()