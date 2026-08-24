"""Validate and serialize immutable source-grounded Evidence."""

from __future__ import annotations

from datetime import datetime
from hashlib import sha256
import json
import re
from typing import Any

from modules.project_sources.identifiers import validate_source_id
from modules.project_workspace.identifiers import is_valid_project_id
from modules.source_projection.identifiers import (
    segment_id_sequence,
    validate_segment_id,
    validate_source_projection_id,
)

from .errors import (
    SourceEvidenceAnchorError,
    SourceEvidenceValidationError,
)
from .identifiers import validate_source_evidence_id
from .types import SourceEvidence, SourceEvidenceAnchor


SOURCE_EVIDENCE_SCHEMA_VERSION = "1.0.0"

_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_UTC_TIMESTAMP_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T"
    r"\d{2}:\d{2}:\d{2}"
    r"(?:\.\d+)?Z$"
)

_SOURCE_EVIDENCE_FIELDS = frozenset(
    {
        "schema_version",
        "project_id",
        "source_id",
        "source_projection_id",
        "source_evidence_id",
        "source_projection_fingerprint",
        "source_anchors",
        "source_excerpt",
        "content_fingerprint",
        "created_at",
    }
)
_SOURCE_ANCHOR_FIELDS = frozenset(
    {
        "segment_id",
        "start_offset",
        "end_offset",
    }
)


def create_source_evidence(
    *,
    project_id: str,
    source_id: str,
    source_projection_id: str,
    source_evidence_id: str,
    source_projection_fingerprint: str,
    source_anchors: tuple[SourceEvidenceAnchor, ...],
    source_excerpt: str,
    timestamp: str,
) -> SourceEvidence:
    """Create one validated immutable Source Evidence object."""

    content_fingerprint = calculate_source_evidence_content_fingerprint(
        project_id=project_id,
        source_id=source_id,
        source_projection_id=source_projection_id,
        source_projection_fingerprint=source_projection_fingerprint,
        source_anchors=source_anchors,
        source_excerpt=source_excerpt,
    )

    return parse_source_evidence(
        {
            "schema_version": SOURCE_EVIDENCE_SCHEMA_VERSION,
            "project_id": project_id,
            "source_id": source_id,
            "source_projection_id": source_projection_id,
            "source_evidence_id": source_evidence_id,
            "source_projection_fingerprint": (
                source_projection_fingerprint
            ),
            "source_anchors": [
                _source_anchor_payload(anchor)
                for anchor in source_anchors
            ],
            "source_excerpt": source_excerpt,
            "content_fingerprint": content_fingerprint,
            "created_at": timestamp,
        },
        expected_project_id=project_id,
        expected_source_id=source_id,
        expected_source_projection_id=source_projection_id,
        expected_source_evidence_id=source_evidence_id,
    )


def parse_source_evidence(
    payload: Any,
    *,
    expected_project_id: str | None = None,
    expected_source_id: str | None = None,
    expected_source_projection_id: str | None = None,
    expected_source_evidence_id: str | None = None,
) -> SourceEvidence:
    """Parse and validate one Source Evidence payload."""

    item = _require_exact_object(
        payload,
        _SOURCE_EVIDENCE_FIELDS,
        "Source Evidence",
    )

    schema_version = item["schema_version"]
    if schema_version != SOURCE_EVIDENCE_SCHEMA_VERSION:
        raise SourceEvidenceValidationError(
            "Unsupported Source Evidence schema_version: "
            f"{schema_version!r}."
        )

    project_id = _require_project_id(item["project_id"])
    source_id = _require_source_id(item["source_id"])
    source_projection_id = _require_source_projection_id(
        item["source_projection_id"]
    )
    source_evidence_id = validate_source_evidence_id(
        item["source_evidence_id"]
    )

    _require_expected(project_id, expected_project_id, "project_id")
    _require_expected(source_id, expected_source_id, "source_id")
    _require_expected(
        source_projection_id,
        expected_source_projection_id,
        "source_projection_id",
    )
    _require_expected(
        source_evidence_id,
        expected_source_evidence_id,
        "source_evidence_id",
    )

    source_projection_fingerprint = _require_sha256(
        item["source_projection_fingerprint"],
        "source_projection_fingerprint",
    )
    source_anchors = _parse_source_anchors(item["source_anchors"])
    source_excerpt = _require_source_excerpt(item["source_excerpt"])
    content_fingerprint = _require_sha256(
        item["content_fingerprint"],
        "content_fingerprint",
    )
    created_at = _require_utc_timestamp(
        item["created_at"],
        "created_at",
    )

    expected_fingerprint = calculate_source_evidence_content_fingerprint(
        project_id=project_id,
        source_id=source_id,
        source_projection_id=source_projection_id,
        source_projection_fingerprint=source_projection_fingerprint,
        source_anchors=source_anchors,
        source_excerpt=source_excerpt,
    )
    if content_fingerprint != expected_fingerprint:
        raise SourceEvidenceValidationError(
            "content_fingerprint does not match Source Evidence content."
        )

    return SourceEvidence(
        schema_version=schema_version,
        project_id=project_id,
        source_id=source_id,
        source_projection_id=source_projection_id,
        source_evidence_id=source_evidence_id,
        source_projection_fingerprint=source_projection_fingerprint,
        source_anchors=source_anchors,
        source_excerpt=source_excerpt,
        content_fingerprint=content_fingerprint,
        created_at=created_at,
    )


def source_evidence_from_json(
    text: str,
    **expected: Any,
) -> SourceEvidence:
    """Parse one Source Evidence JSON string."""

    if not isinstance(text, str):
        raise SourceEvidenceValidationError(
            "Source Evidence JSON input must be a string."
        )

    try:
        payload = json.loads(
            text,
            object_pairs_hook=_object_without_duplicate_keys,
        )
    except SourceEvidenceValidationError:
        raise
    except json.JSONDecodeError as exc:
        raise SourceEvidenceValidationError(
            f"Source Evidence contains invalid JSON: {exc}."
        ) from exc

    return parse_source_evidence(payload, **expected)


def source_evidence_to_dict(
    evidence: SourceEvidence,
) -> dict[str, Any]:
    """Return the canonical JSON-compatible representation."""

    if not isinstance(evidence, SourceEvidence):
        raise SourceEvidenceValidationError(
            "evidence must be a SourceEvidence instance."
        )

    payload = _source_evidence_payload(evidence)
    validated = parse_source_evidence(payload)
    return _source_evidence_payload(validated)


def source_evidence_to_json(
    evidence: SourceEvidence,
) -> str:
    """Serialize one Source Evidence object deterministically."""

    return (
        json.dumps(
            source_evidence_to_dict(evidence),
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )


def calculate_source_evidence_content_fingerprint(
    *,
    project_id: str,
    source_id: str,
    source_projection_id: str,
    source_projection_fingerprint: str,
    source_anchors: tuple[SourceEvidenceAnchor, ...],
    source_excerpt: str,
) -> str:
    """Hash stable source identity, excluding Evidence ID and time."""

    validated_project_id = _require_project_id(project_id)
    validated_source_id = _require_source_id(source_id)
    validated_projection_id = _require_source_projection_id(
        source_projection_id
    )
    validated_projection_fingerprint = _require_sha256(
        source_projection_fingerprint,
        "source_projection_fingerprint",
    )
    validated_anchors = _parse_source_anchors(
        [
            _source_anchor_payload(anchor)
            for anchor in source_anchors
        ]
    )
    validated_excerpt = _require_source_excerpt(source_excerpt)

    payload = {
        "project_id": validated_project_id,
        "source_id": validated_source_id,
        "source_projection_id": validated_projection_id,
        "source_projection_fingerprint": validated_projection_fingerprint,
        "source_anchors": [
            _source_anchor_payload(anchor)
            for anchor in validated_anchors
        ],
        "source_excerpt": validated_excerpt,
    }
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(canonical.encode("utf-8")).hexdigest()


def _source_evidence_payload(
    evidence: SourceEvidence,
) -> dict[str, Any]:
    return {
        "schema_version": evidence.schema_version,
        "project_id": evidence.project_id,
        "source_id": evidence.source_id,
        "source_projection_id": evidence.source_projection_id,
        "source_evidence_id": evidence.source_evidence_id,
        "source_projection_fingerprint": (
            evidence.source_projection_fingerprint
        ),
        "source_anchors": [
            _source_anchor_payload(anchor)
            for anchor in evidence.source_anchors
        ],
        "source_excerpt": evidence.source_excerpt,
        "content_fingerprint": evidence.content_fingerprint,
        "created_at": evidence.created_at,
    }


def _source_anchor_payload(
    anchor: SourceEvidenceAnchor,
) -> dict[str, Any]:
    if not isinstance(anchor, SourceEvidenceAnchor):
        raise SourceEvidenceAnchorError(
            "source_anchors must contain SourceEvidenceAnchor instances."
        )

    return {
        "segment_id": anchor.segment_id,
        "start_offset": anchor.start_offset,
        "end_offset": anchor.end_offset,
    }


def _parse_source_anchors(
    value: Any,
) -> tuple[SourceEvidenceAnchor, ...]:
    if not isinstance(value, list):
        raise SourceEvidenceAnchorError(
            "source_anchors must be a JSON array."
        )
    if not value:
        raise SourceEvidenceAnchorError(
            "source_anchors must contain at least one anchor."
        )

    anchors: list[SourceEvidenceAnchor] = []
    previous_key: tuple[int, int, int] | None = None

    for raw_anchor in value:
        item = _require_exact_object(
            raw_anchor,
            _SOURCE_ANCHOR_FIELDS,
            "Source Evidence source anchor",
        )

        try:
            segment_id = validate_segment_id(item["segment_id"])
        except Exception as exc:
            raise SourceEvidenceAnchorError(
                "Source Evidence anchor contains an invalid segment_id."
            ) from exc

        try:
            start_offset = _require_nonnegative_integer(
                item["start_offset"],
                "source anchor start_offset",
            )
            end_offset = _require_positive_integer(
                item["end_offset"],
                "source anchor end_offset",
            )
        except SourceEvidenceValidationError as exc:
            raise SourceEvidenceAnchorError(str(exc)) from exc

        if end_offset <= start_offset:
            raise SourceEvidenceAnchorError(
                "Source anchor end_offset must be greater than start_offset."
            )

        key = (
            segment_id_sequence(segment_id),
            start_offset,
            end_offset,
        )
        if previous_key is not None and key <= previous_key:
            raise SourceEvidenceAnchorError(
                "source_anchors must use strict canonical "
                "source order without duplicates."
            )
        previous_key = key

        anchors.append(
            SourceEvidenceAnchor(
                segment_id=segment_id,
                start_offset=start_offset,
                end_offset=end_offset,
            )
        )

    return tuple(anchors)


def _require_exact_object(
    value: Any,
    expected_fields: frozenset[str],
    label: str,
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise SourceEvidenceValidationError(
            f"{label} must be a JSON object."
        )

    actual_fields = frozenset(value)
    if actual_fields != expected_fields:
        missing = sorted(expected_fields - actual_fields)
        unexpected = sorted(actual_fields - expected_fields)
        raise SourceEvidenceValidationError(
            f"{label} fields do not match the schema. "
            f"Missing: {missing}; unexpected: {unexpected}."
        )

    return value


def _require_project_id(value: Any) -> str:
    if not is_valid_project_id(value):
        raise SourceEvidenceValidationError(
            "project_id must be a valid six-digit project ID."
        )
    return value


def _require_source_id(value: Any) -> str:
    try:
        return validate_source_id(value)
    except Exception as exc:
        raise SourceEvidenceValidationError("source_id is invalid.") from exc


def _require_source_projection_id(value: Any) -> str:
    try:
        return validate_source_projection_id(value)
    except Exception as exc:
        raise SourceEvidenceValidationError(
            "source_projection_id is invalid."
        ) from exc


def _require_sha256(
    value: Any,
    field_name: str,
) -> str:
    if (
        not isinstance(value, str)
        or _SHA256_PATTERN.fullmatch(value) is None
    ):
        raise SourceEvidenceValidationError(
            f"{field_name} must be a lowercase SHA-256 hex string."
        )
    return value


def _require_source_excerpt(value: Any) -> str:
    if not isinstance(value, str):
        raise SourceEvidenceValidationError(
            "source_excerpt must be a string."
        )
    if not value:
        raise SourceEvidenceValidationError(
            "source_excerpt must not be empty."
        )
    return value


def _require_nonnegative_integer(
    value: Any,
    field_name: str,
) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value < 0
    ):
        raise SourceEvidenceValidationError(
            f"{field_name} must be a non-negative integer."
        )
    return value


def _require_positive_integer(
    value: Any,
    field_name: str,
) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value <= 0
    ):
        raise SourceEvidenceValidationError(
            f"{field_name} must be a positive integer."
        )
    return value


def _require_utc_timestamp(
    value: Any,
    field_name: str,
) -> str:
    if (
        not isinstance(value, str)
        or _UTC_TIMESTAMP_PATTERN.fullmatch(value) is None
    ):
        raise SourceEvidenceValidationError(
            f"{field_name} must be a canonical UTC timestamp ending in Z."
        )

    try:
        parsed = datetime.fromisoformat(
            value.removesuffix("Z") + "+00:00"
        )
    except ValueError as exc:
        raise SourceEvidenceValidationError(
            f"{field_name} is not a valid timestamp."
        ) from exc

    if parsed.utcoffset() is None:
        raise SourceEvidenceValidationError(
            f"{field_name} must include UTC timezone information."
        )

    return value


def _require_expected(
    actual: str,
    expected: str | None,
    field_name: str,
) -> None:
    if expected is not None and actual != expected:
        raise SourceEvidenceValidationError(
            f"{field_name} does not match the expected value."
        )


def _object_without_duplicate_keys(
    pairs: list[tuple[str, Any]],
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise SourceEvidenceValidationError(
                f"Duplicate JSON field is not allowed: {key!r}."
            )
        result[key] = value
    return result
