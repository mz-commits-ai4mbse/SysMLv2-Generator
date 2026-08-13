"""Shared strict JSON-profile support for Phase-J generation policy artifacts."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .errors import SysMLGenerationProfileError


SEMVER_PATTERN = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
UPPER_ID_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]*$")
RULE_ID_PATTERN = re.compile(r"^[A-Z0-9_]+$")


def load_json_without_duplicate_keys(path: Path | str) -> dict[str, Any]:
    target = Path(path)
    try:
        raw = target.read_text(encoding="utf-8")
    except OSError as exc:
        raise SysMLGenerationProfileError(
            f"Unable to read Phase-J profile: {target}."
        ) from exc
    try:
        value = json.loads(raw, object_pairs_hook=_without_duplicate_keys)
    except SysMLGenerationProfileError:
        raise
    except json.JSONDecodeError as exc:
        raise SysMLGenerationProfileError(
            f"Phase-J profile is not valid JSON: {target}."
        ) from exc
    if not isinstance(value, dict):
        raise SysMLGenerationProfileError(
            f"Phase-J profile must be a JSON object: {target}."
        )
    return value


def exact_object(
    value: object,
    *,
    expected: frozenset[str],
    label: str,
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise SysMLGenerationProfileError(f"{label} must be a JSON object.")
    actual = frozenset(value)
    if actual != expected:
        raise SysMLGenerationProfileError(
            f"{label} has invalid fields; "
            f"missing={sorted(expected - actual)}, "
            f"unknown={sorted(actual - expected)}."
        )
    return value


def require_semver(value: object, label: str) -> str:
    if not isinstance(value, str) or SEMVER_PATTERN.fullmatch(value) is None:
        raise SysMLGenerationProfileError(
            f"{label} must be a semantic version."
        )
    return value


def require_upper_id(value: object, label: str) -> str:
    if not isinstance(value, str) or UPPER_ID_PATTERN.fullmatch(value) is None:
        raise SysMLGenerationProfileError(
            f"{label} must be an uppercase identifier."
        )
    return value


def require_rule_id(value: object, label: str) -> str:
    if not isinstance(value, str) or RULE_ID_PATTERN.fullmatch(value) is None:
        raise SysMLGenerationProfileError(
            f"{label} must be an uppercase rule identifier."
        )
    return value


def require_nonempty_string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SysMLGenerationProfileError(
            f"{label} must be a non-empty string."
        )
    return value


def _without_duplicate_keys(
    pairs: list[tuple[str, object]],
) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise SysMLGenerationProfileError(
                f"Duplicate JSON key is not allowed: {key!r}."
            )
        result[key] = value
    return result
