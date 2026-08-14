"""Canonical SHA-256 helpers for deterministic Final Model Review artifacts."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from .errors import FinalModelReviewValidationError


SHA256_HEX_PATTERN = re.compile(r"^[0-9a-f]{64}$")


def validate_sha256_fingerprint(value: object, *, label: str) -> str:
    if (
        not isinstance(value, str)
        or SHA256_HEX_PATTERN.fullmatch(value) is None
    ):
        raise FinalModelReviewValidationError(
            f"{label} must be a 64-character lowercase SHA-256 hex string."
        )
    return value


def canonical_json_bytes(payload: Any) -> bytes:
    try:
        text = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    except (TypeError, ValueError) as exc:
        raise FinalModelReviewValidationError(
            "fingerprint payload must be JSON serializable."
        ) from exc
    return text.encode("utf-8")


def calculate_json_fingerprint(payload: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(payload)).hexdigest()
