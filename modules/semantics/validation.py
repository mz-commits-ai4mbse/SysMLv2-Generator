"""Strict validation helpers for semantic-reference artifacts."""

from __future__ import annotations

from collections.abc import Iterable
from hashlib import sha256
from pathlib import Path, PurePosixPath
import re
from typing import Any
from urllib.parse import urlparse

from modules.semantics.errors import (
    OntologyRegistryError,
    UnsafeOntologyPathError,
)


_SEMANTIC_VERSION_PATTERN = re.compile(
    r"^\d+\.\d+\.\d+$"
)
_IDENTIFIER_PATTERN = re.compile(
    r"^[A-Z][A-Z0-9_]*$"
)
_GIT_SHA_PATTERN = re.compile(
    r"^[0-9a-f]{40}$"
)
_SHA256_PATTERN = re.compile(
    r"^[0-9a-f]{64}$"
)


def require_exact_object(
    payload: Any,
    required_fields: frozenset[str],
    label: str,
    *,
    optional_fields: frozenset[str] = frozenset(),
) -> dict[str, Any]:
    """Require one object with no missing or unknown fields."""

    if not isinstance(payload, dict):
        raise OntologyRegistryError(
            f"{label} must be a JSON object."
        )

    actual_fields = set(payload)
    missing = required_fields - actual_fields
    unexpected = (
        actual_fields
        - required_fields
        - optional_fields
    )

    if missing:
        raise OntologyRegistryError(
            f"{label} is missing fields: "
            f"{', '.join(sorted(missing))}."
        )

    if unexpected:
        raise OntologyRegistryError(
            f"{label} contains unknown fields: "
            f"{', '.join(sorted(unexpected))}."
        )

    return payload


def object_without_duplicate_keys(
    pairs: list[tuple[str, Any]],
) -> dict[str, Any]:
    """Construct an object while rejecting duplicate JSON keys."""

    result: dict[str, Any] = {}

    for key, value in pairs:
        if key in result:
            raise OntologyRegistryError(
                f"Duplicate JSON field: {key!r}."
            )

        result[key] = value

    return result


def require_string(
    value: Any,
    label: str,
) -> str:
    """Require a non-empty string without outer whitespace."""

    if not isinstance(value, str) or not value.strip():
        raise OntologyRegistryError(
            f"{label} must be a non-empty string."
        )

    if value != value.strip():
        raise OntologyRegistryError(
            f"{label} must not contain surrounding whitespace."
        )

    return value


def require_boolean(
    value: Any,
    label: str,
) -> bool:
    """Require an actual JSON boolean."""

    if not isinstance(value, bool):
        raise OntologyRegistryError(
            f"{label} must be a boolean."
        )

    return value


def require_list(
    value: Any,
    label: str,
) -> list[Any]:
    """Require a JSON list."""

    if not isinstance(value, list):
        raise OntologyRegistryError(
            f"{label} must be a list."
        )

    return value


def require_positive_integer(
    value: Any,
    label: str,
) -> int:
    """Require a positive integer and reject booleans."""

    if (
        not isinstance(value, int)
        or isinstance(value, bool)
        or value <= 0
    ):
        raise OntologyRegistryError(
            f"{label} must be a positive integer."
        )

    return value


def require_semantic_version(
    value: Any,
    label: str,
) -> str:
    """Require MAJOR.MINOR.PATCH version syntax."""

    version = require_string(value, label)

    if not _SEMANTIC_VERSION_PATTERN.fullmatch(
        version
    ):
        raise OntologyRegistryError(
            f"{label} must use MAJOR.MINOR.PATCH "
            "versioning."
        )

    return version


def require_identifier(
    value: Any,
    label: str,
) -> str:
    """Require a stable uppercase identifier."""

    identifier = require_string(value, label)

    if not _IDENTIFIER_PATTERN.fullmatch(identifier):
        raise OntologyRegistryError(
            f"{label} must be a stable uppercase "
            "identifier."
        )

    return identifier


def require_git_sha(
    value: Any,
    label: str,
) -> str:
    """Require a full lowercase hexadecimal Git SHA."""

    git_sha = require_string(value, label)

    if not _GIT_SHA_PATTERN.fullmatch(git_sha):
        raise OntologyRegistryError(
            f"{label} must contain 40 lowercase "
            "hexadecimal characters."
        )

    return git_sha


def require_sha256(
    value: Any,
    label: str,
) -> str:
    """Require a lowercase hexadecimal SHA-256 value."""

    checksum = require_string(value, label)

    if not _SHA256_PATTERN.fullmatch(checksum):
        raise OntologyRegistryError(
            f"{label} must contain 64 lowercase "
            "hexadecimal characters."
        )

    return checksum


def require_http_url(
    value: Any,
    label: str,
) -> str:
    """Require an absolute HTTP or HTTPS URL."""

    url = require_string(value, label)
    parsed = urlparse(url)

    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.netloc
    ):
        raise OntologyRegistryError(
            f"{label} must be an absolute HTTP(S) URL."
        )

    return url


def require_repository_path(
    value: Any,
    label: str,
    *,
    required_prefix: tuple[str, ...],
) -> Path:
    """Require a normalized repository-relative path."""

    text = require_string(value, label)

    if "\\" in text:
        raise OntologyRegistryError(
            f"{label} must use forward slashes."
        )

    path = PurePosixPath(text)

    if (
        path.is_absolute()
        or ".." in path.parts
        or "." in path.parts
        or path.parts[: len(required_prefix)]
        != required_prefix
        or path.as_posix() != text
    ):
        raise OntologyRegistryError(
            f"{label} violates its repository-relative "
            "path boundary."
        )

    return Path(*path.parts)


def require_source_path(
    value: Any,
    label: str,
) -> str:
    """Require a normalized relative upstream path."""

    text = require_string(value, label)

    if "\\" in text:
        raise OntologyRegistryError(
            f"{label} must use forward slashes."
        )

    path = PurePosixPath(text)

    if (
        path.is_absolute()
        or ".." in path.parts
        or "." in path.parts
        or path.as_posix() != text
    ):
        raise OntologyRegistryError(
            f"{label} must be a safe relative "
            "upstream path."
        )

    return path.as_posix()


def require_unique(
    values: Iterable[str],
    label: str,
) -> None:
    """Reject duplicate string values."""

    seen: set[str] = set()

    for value in values:
        if value in seen:
            raise OntologyRegistryError(
                f"Duplicate {label}: {value!r}."
            )

        seen.add(value)


def resolve_repository_path(
    repository_root: Path,
    path: Path,
    label: str,
) -> Path:
    """Resolve a path without permitting root escape."""

    root = repository_root.resolve()
    candidate = (
        path.resolve()
        if path.is_absolute()
        else (root / path).resolve()
    )

    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise UnsafeOntologyPathError(
            f"{label} escapes repository root: "
            f"{candidate}."
        ) from exc

    return candidate


def calculate_file_sha256(path: Path) -> str:
    """Calculate one file checksum without loading it at once."""

    digest = sha256()

    with path.open("rb") as handle:
        for chunk in iter(
            lambda: handle.read(1024 * 1024),
            b"",
        ):
            digest.update(chunk)

    return digest.hexdigest()