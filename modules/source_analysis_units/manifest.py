"""Validate and serialize immutable Source Analysis Units."""

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
    SourceAnalysisUnitAnchorError,
    SourceAnalysisUnitValidationError,
)
from .identifiers import validate_source_analysis_unit_id
from .types import (
    SourceAnalysisUnit,
    SourceAnalysisUnitAnchor,
)


SOURCE_ANALYSIS_UNIT_SCHEMA_VERSION = "1.0.0"

_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_LOWER_IDENTIFIER_PATTERN = re.compile(
    r"^[a-z][a-z0-9_]*$"
)
_SEMANTIC_VERSION_PATTERN = re.compile(
    r"^[0-9]+\.[0-9]+\.[0-9]+$"
)
_UTC_TIMESTAMP_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T"
    r"\d{2}:\d{2}:\d{2}"
    r"(?:\.\d+)?Z$"
)

_SOURCE_ANALYSIS_UNIT_FIELDS = frozenset(
    {
        "schema_version",
        "project_id",
        "source_id",
        "source_projection_id",
        "source_analysis_unit_id",
        "source_projection_fingerprint",
        "source_anchors",
        "source_excerpt",
        "source_order_index",
        "segmentation_profile_id",
        "segmentation_profile_version",
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


def create_source_analysis_unit(
    *,
    project_id: str,
    source_id: str,
    source_projection_id: str,
    source_analysis_unit_id: str,
    source_projection_fingerprint: str,
    source_anchors: tuple[SourceAnalysisUnitAnchor, ...],
    source_excerpt: str,
    source_order_index: int,
    segmentation_profile_id: str,
    segmentation_profile_version: str,
    timestamp: str,
) -> SourceAnalysisUnit:
    """Create one validated immutable Source Analysis Unit."""

    content_fingerprint = (
        calculate_source_analysis_unit_content_fingerprint(
            project_id=project_id,
            source_id=source_id,
            source_projection_id=source_projection_id,
            source_projection_fingerprint=(
                source_projection_fingerprint
            ),
            source_anchors=source_anchors,
            source_excerpt=source_excerpt,
            source_order_index=source_order_index,
            segmentation_profile_id=segmentation_profile_id,
            segmentation_profile_version=(
                segmentation_profile_version
            ),
        )
    )

    return parse_source_analysis_unit(
        {
            "schema_version": (
                SOURCE_ANALYSIS_UNIT_SCHEMA_VERSION
            ),
            "project_id": project_id,
            "source_id": source_id,
            "source_projection_id": source_projection_id,
            "source_analysis_unit_id": source_analysis_unit_id,
            "source_projection_fingerprint": (
                source_projection_fingerprint
            ),
            "source_anchors": [
                _source_anchor_payload(anchor)
                for anchor in source_anchors
            ],
            "source_excerpt": source_excerpt,
            "source_order_index": source_order_index,
            "segmentation_profile_id": (
                segmentation_profile_id
            ),
            "segmentation_profile_version": (
                segmentation_profile_version
            ),
            "content_fingerprint": content_fingerprint,
            "created_at": timestamp,
        },
        expected_project_id=project_id,
        expected_source_analysis_unit_id=(
            source_analysis_unit_id
        ),
        expected_source_id=source_id,
        expected_source_projection_id=source_projection_id,
    )


def parse_source_analysis_unit(
    payload: Any,
    *,
    expected_project_id: str | None = None,
    expected_source_analysis_unit_id: str | None = None,
    expected_source_id: str | None = None,
    expected_source_projection_id: str | None = None,
) -> SourceAnalysisUnit:
    """Parse and validate one Source Analysis Unit payload."""

    item = _require_exact_object(
        payload,
        _SOURCE_ANALYSIS_UNIT_FIELDS,
        "Source Analysis Unit",
    )

    schema_version = item["schema_version"]
    if schema_version != SOURCE_ANALYSIS_UNIT_SCHEMA_VERSION:
        raise SourceAnalysisUnitValidationError(
            "Unsupported Source Analysis Unit schema_version: "
            f"{schema_version!r}."
        )

    project_id = _require_project_id(item["project_id"])
    source_id = _require_source_id(item["source_id"])
    source_projection_id = _require_source_projection_id(
        item["source_projection_id"]
    )
    source_analysis_unit_id = (
        validate_source_analysis_unit_id(
            item["source_analysis_unit_id"]
        )
    )

    _require_expected(
        project_id,
        expected_project_id,
        "project_id",
    )
    _require_expected(
        source_id,
        expected_source_id,
        "source_id",
    )
    _require_expected(
        source_projection_id,
        expected_source_projection_id,
        "source_projection_id",
    )
    _require_expected(
        source_analysis_unit_id,
        expected_source_analysis_unit_id,
        "source_analysis_unit_id",
    )

    source_projection_fingerprint = _require_sha256(
        item["source_projection_fingerprint"],
        "source_projection_fingerprint",
    )
    source_anchors = _parse_source_anchors(
        item["source_anchors"]
    )
    source_excerpt = _require_source_excerpt(
        item["source_excerpt"]
    )
    source_order_index = _require_positive_integer(
        item["source_order_index"],
        "source_order_index",
    )
    segmentation_profile_id = _require_lower_identifier(
        item["segmentation_profile_id"],
        "segmentation_profile_id",
    )
    segmentation_profile_version = _require_semantic_version(
        item["segmentation_profile_version"],
        "segmentation_profile_version",
    )
    content_fingerprint = _require_sha256(
        item["content_fingerprint"],
        "content_fingerprint",
    )
    created_at = _require_utc_timestamp(
        item["created_at"],
        "created_at",
    )

    expected_fingerprint = (
        calculate_source_analysis_unit_content_fingerprint(
            project_id=project_id,
            source_id=source_id,
            source_projection_id=source_projection_id,
            source_projection_fingerprint=(
                source_projection_fingerprint
            ),
            source_anchors=source_anchors,
            source_excerpt=source_excerpt,
            source_order_index=source_order_index,
            segmentation_profile_id=(
                segmentation_profile_id
            ),
            segmentation_profile_version=(
                segmentation_profile_version
            ),
        )
    )

    if content_fingerprint != expected_fingerprint:
        raise SourceAnalysisUnitValidationError(
            "content_fingerprint does not match the "
            "Source Analysis Unit content."
        )

    return SourceAnalysisUnit(
        schema_version=schema_version,
        project_id=project_id,
        source_id=source_id,
        source_projection_id=source_projection_id,
        source_analysis_unit_id=source_analysis_unit_id,
        source_projection_fingerprint=(
            source_projection_fingerprint
        ),
        source_anchors=source_anchors,
        source_excerpt=source_excerpt,
        source_order_index=source_order_index,
        segmentation_profile_id=segmentation_profile_id,
        segmentation_profile_version=(
            segmentation_profile_version
        ),
        content_fingerprint=content_fingerprint,
        created_at=created_at,
    )


def source_analysis_unit_from_json(
    text: str,
    **expected: Any,
) -> SourceAnalysisUnit:
    """Parse one Source Analysis Unit JSON string."""

    if not isinstance(text, str):
        raise SourceAnalysisUnitValidationError(
            "Source Analysis Unit JSON input must be a string."
        )

    try:
        payload = json.loads(
            text,
            object_pairs_hook=_object_without_duplicate_keys,
        )
    except SourceAnalysisUnitValidationError:
        raise
    except json.JSONDecodeError as exc:
        raise SourceAnalysisUnitValidationError(
            "Source Analysis Unit contains invalid JSON: "
            f"{exc}."
        ) from exc

    return parse_source_analysis_unit(payload, **expected)


def source_analysis_unit_to_dict(
    unit: SourceAnalysisUnit,
) -> dict[str, Any]:
    """Return the canonical JSON-compatible representation."""

    if not isinstance(unit, SourceAnalysisUnit):
        raise SourceAnalysisUnitValidationError(
            "unit must be a SourceAnalysisUnit instance."
        )

    payload = _source_analysis_unit_payload(unit)
    validated = parse_source_analysis_unit(payload)
    return _source_analysis_unit_payload(validated)


def source_analysis_unit_to_json(
    unit: SourceAnalysisUnit,
) -> str:
    """Serialize one Source Analysis Unit deterministically."""

    return (
        json.dumps(
            source_analysis_unit_to_dict(unit),
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )


def calculate_source_analysis_unit_content_fingerprint(
    *,
    project_id: str,
    source_id: str,
    source_projection_id: str,
    source_projection_fingerprint: str,
    source_anchors: tuple[SourceAnalysisUnitAnchor, ...],
    source_excerpt: str,
    source_order_index: int,
    segmentation_profile_id: str,
    segmentation_profile_version: str,
) -> str:
    """Hash stable source-analysis content, excluding ID and time."""

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
    validated_excerpt = _require_source_excerpt(
        source_excerpt
    )
    validated_order = _require_positive_integer(
        source_order_index,
        "source_order_index",
    )
    validated_profile_id = _require_lower_identifier(
        segmentation_profile_id,
        "segmentation_profile_id",
    )
    validated_profile_version = _require_semantic_version(
        segmentation_profile_version,
        "segmentation_profile_version",
    )

    payload = {
        "project_id": validated_project_id,
        "source_id": validated_source_id,
        "source_projection_id": validated_projection_id,
        "source_projection_fingerprint": (
            validated_projection_fingerprint
        ),
        "source_anchors": [
            _source_anchor_payload(anchor)
            for anchor in validated_anchors
        ],
        "source_excerpt": validated_excerpt,
        "source_order_index": validated_order,
        "segmentation_profile_id": validated_profile_id,
        "segmentation_profile_version": (
            validated_profile_version
        ),
    }
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(canonical.encode("utf-8")).hexdigest()


def _source_analysis_unit_payload(
    unit: SourceAnalysisUnit,
) -> dict[str, Any]:
    return {
        "schema_version": unit.schema_version,
        "project_id": unit.project_id,
        "source_id": unit.source_id,
        "source_projection_id": unit.source_projection_id,
        "source_analysis_unit_id": (
            unit.source_analysis_unit_id
        ),
        "source_projection_fingerprint": (
            unit.source_projection_fingerprint
        ),
        "source_anchors": [
            _source_anchor_payload(anchor)
            for anchor in unit.source_anchors
        ],
        "source_excerpt": unit.source_excerpt,
        "source_order_index": unit.source_order_index,
        "segmentation_profile_id": (
            unit.segmentation_profile_id
        ),
        "segmentation_profile_version": (
            unit.segmentation_profile_version
        ),
        "content_fingerprint": unit.content_fingerprint,
        "created_at": unit.created_at,
    }


def _source_anchor_payload(
    anchor: SourceAnalysisUnitAnchor,
) -> dict[str, Any]:
    if not isinstance(anchor, SourceAnalysisUnitAnchor):
        raise SourceAnalysisUnitAnchorError(
            "source_anchors must contain "
            "SourceAnalysisUnitAnchor instances."
        )

    return {
        "segment_id": anchor.segment_id,
        "start_offset": anchor.start_offset,
        "end_offset": anchor.end_offset,
    }


def _parse_source_anchors(
    value: Any,
) -> tuple[SourceAnalysisUnitAnchor, ...]:
    if not isinstance(value, list):
        raise SourceAnalysisUnitAnchorError(
            "source_anchors must be a JSON array."
        )
    if not value:
        raise SourceAnalysisUnitAnchorError(
            "source_anchors must contain at least one anchor."
        )

    anchors: list[SourceAnalysisUnitAnchor] = []
    previous_key: tuple[int, int, int] | None = None

    for raw_anchor in value:
        item = _require_exact_object(
            raw_anchor,
            _SOURCE_ANCHOR_FIELDS,
            "Source Analysis Unit source anchor",
        )
        try:
            segment_id = validate_segment_id(
                item["segment_id"]
            )
        except Exception as exc:
            raise SourceAnalysisUnitAnchorError(
                "Source Analysis Unit anchor contains an "
                "invalid segment_id."
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
        except SourceAnalysisUnitValidationError as exc:
            raise SourceAnalysisUnitAnchorError(
                str(exc)
            ) from exc

        if end_offset <= start_offset:
            raise SourceAnalysisUnitAnchorError(
                "Source anchor end_offset must be greater "
                "than start_offset."
            )

        key = (
            segment_id_sequence(segment_id),
            start_offset,
            end_offset,
        )
        if previous_key is not None and key <= previous_key:
            raise SourceAnalysisUnitAnchorError(
                "source_anchors must use strict canonical "
                "source order without duplicates."
            )
        previous_key = key

        anchors.append(
            SourceAnalysisUnitAnchor(
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
        raise SourceAnalysisUnitValidationError(
            f"{label} must be a JSON object."
        )

    actual_fields = frozenset(value)
    if actual_fields != expected_fields:
        missing = sorted(expected_fields - actual_fields)
        unexpected = sorted(actual_fields - expected_fields)
        raise SourceAnalysisUnitValidationError(
            f"{label} fields do not match the schema. "
            f"Missing: {missing}; unexpected: {unexpected}."
        )

    return value


def _require_project_id(value: Any) -> str:
    if not is_valid_project_id(value):
        raise SourceAnalysisUnitValidationError(
            "project_id must be a valid six-digit project ID."
        )
    return value


def _require_source_id(value: Any) -> str:
    try:
        return validate_source_id(value)
    except Exception as exc:
        raise SourceAnalysisUnitValidationError(
            "source_id is invalid."
        ) from exc


def _require_source_projection_id(value: Any) -> str:
    try:
        return validate_source_projection_id(value)
    except Exception as exc:
        raise SourceAnalysisUnitValidationError(
            "source_projection_id is invalid."
        ) from exc


def _require_source_excerpt(value: Any) -> str:
    if not isinstance(value, str) or value == "":
        raise SourceAnalysisUnitValidationError(
            "source_excerpt must be a non-empty string."
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
        raise SourceAnalysisUnitValidationError(
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
        or value < 1
    ):
        raise SourceAnalysisUnitValidationError(
            f"{field_name} must be a positive integer."
        )
    return value


def _require_lower_identifier(
    value: Any,
    field_name: str,
) -> str:
    if (
        not isinstance(value, str)
        or _LOWER_IDENTIFIER_PATTERN.fullmatch(value) is None
    ):
        raise SourceAnalysisUnitValidationError(
            f"{field_name} must be a lower-case identifier."
        )
    return value


def _require_semantic_version(
    value: Any,
    field_name: str,
) -> str:
    if (
        not isinstance(value, str)
        or _SEMANTIC_VERSION_PATTERN.fullmatch(value) is None
    ):
        raise SourceAnalysisUnitValidationError(
            f"{field_name} must use semantic version form X.Y.Z."
        )
    return value


def _require_sha256(
    value: Any,
    field_name: str,
) -> str:
    if (
        not isinstance(value, str)
        or _SHA256_PATTERN.fullmatch(value) is None
    ):
        raise SourceAnalysisUnitValidationError(
            f"{field_name} must be a lower-case SHA-256 hex string."
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
        raise SourceAnalysisUnitValidationError(
            f"{field_name} must be an ISO-8601 UTC timestamp ending in Z."
        )

    try:
        parsed = datetime.fromisoformat(
            value.removesuffix("Z") + "+00:00"
        )
    except ValueError as exc:
        raise SourceAnalysisUnitValidationError(
            f"{field_name} is not a valid timestamp."
        ) from exc

    if parsed.utcoffset() is None or parsed.utcoffset().total_seconds() != 0:
        raise SourceAnalysisUnitValidationError(
            f"{field_name} must be UTC."
        )

    return value


def _require_expected(
    actual: str,
    expected: str | None,
    field_name: str,
) -> None:
    if expected is not None and actual != expected:
        raise SourceAnalysisUnitValidationError(
            f"{field_name} does not match the expected value."
        )


def _object_without_duplicate_keys(
    pairs: list[tuple[str, Any]],
) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise SourceAnalysisUnitValidationError(
                f"Duplicate JSON object key: {key!r}."
            )
        value[key] = item
    return value
