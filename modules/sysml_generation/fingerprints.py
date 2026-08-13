"""Canonical SHA-256 helpers for deterministic Phase-J generation."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from .errors import SysMLGenerationValidationError


SHA256_HEX_PATTERN = re.compile(r"^[0-9a-f]{64}$")


def validate_sha256_fingerprint(value: object, *, label: str) -> str:
    """Validate one lowercase SHA-256 hexadecimal fingerprint."""

    if not isinstance(value, str) or SHA256_HEX_PATTERN.fullmatch(value) is None:
        raise SysMLGenerationValidationError(
            f"{label} must be a 64-character lowercase SHA-256 hex string."
        )
    return value


def canonical_json_bytes(payload: Any) -> bytes:
    """Serialize one JSON-compatible value using canonical project ordering."""

    try:
        text = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    except (TypeError, ValueError) as exc:
        raise SysMLGenerationValidationError(
            "fingerprint payload must be JSON serializable."
        ) from exc
    return text.encode("utf-8")


def calculate_json_fingerprint(payload: Any) -> str:
    """Return a canonical SHA-256 fingerprint for JSON-compatible data."""

    return hashlib.sha256(canonical_json_bytes(payload)).hexdigest()


def calculate_text_fingerprint(content: object) -> str:
    """Return the exact-byte SHA-256 fingerprint for generated text."""

    if not isinstance(content, str):
        raise SysMLGenerationValidationError(
            "generated text content must be a string."
        )
    return hashlib.sha256(content.encode("utf-8")).hexdigest()
