"""Deterministic JSON Source Projection adapter."""

from __future__ import annotations

import json
from typing import Any

from .errors import (
    DuplicateJsonKeyError,
    SourceAdapterError,
    UnsupportedTextEncodingError,
)
from .types import (
    ProjectionSegmentDraft,
    SourceLocator,
    SourceProjectionDraft,
)


JSON_ADAPTER_ID = "json"
JSON_ADAPTER_VERSION = "1.0.0"

_UTF8_BOM = b"\xef\xbb\xbf"


def project_json(content: bytes) -> SourceProjectionDraft:
    """Project strict UTF-8 JSON into source-located segments."""

    if not isinstance(content, bytes):
        raise SourceAdapterError(
            "JSON adapter content must be bytes."
        )

    has_utf8_bom = content.startswith(_UTF8_BOM)

    try:
        decoded_text = content.decode(
            "utf-8-sig" if has_utf8_bom else "utf-8"
        )
    except UnicodeDecodeError as exc:
        raise UnsupportedTextEncodingError(
            "JSON source must use UTF-8 or UTF-8 with BOM."
        ) from exc

    parsed = _parse_strict_json(decoded_text)

    segments: list[ProjectionSegmentDraft] = []
    _append_json_segments(
        value=parsed,
        pointer="",
        segments=segments,
    )

    return SourceProjectionDraft(
        adapter_id=JSON_ADAPTER_ID,
        adapter_version=JSON_ADAPTER_VERSION,
        adapter_configuration=(
            ("encoding", "utf-8"),
            (
                "leading_utf8_bom",
                "removed" if has_utf8_bom else "absent",
            ),
            ("parser", "strict_json"),
            ("member_order", "source_order"),
            (
                "segmentation",
                "scalar_leaves_and_empty_containers",
            ),
            ("rendering", "compact_json"),
        ),
        projection_result="complete",
        segments=tuple(segments),
    )


def _parse_strict_json(text: str) -> Any:
    """Parse JSON while rejecting duplicate keys and constants."""

    try:
        return json.loads(
            text,
            object_pairs_hook=_object_without_duplicate_keys,
            parse_constant=_reject_nonstandard_constant,
        )
    except DuplicateJsonKeyError:
        raise
    except (json.JSONDecodeError, ValueError) as exc:
        raise SourceAdapterError(
            f"JSON source contains invalid strict JSON: {exc}."
        ) from exc


def _object_without_duplicate_keys(
    pairs: list[tuple[str, Any]],
) -> dict[str, Any]:
    """Build an object while rejecting duplicate member names."""

    result: dict[str, Any] = {}

    for key, value in pairs:
        if key in result:
            raise DuplicateJsonKeyError(
                "JSON object contains duplicate member name: "
                f"{key!r}."
            )

        result[key] = value

    return result


def _reject_nonstandard_constant(value: str) -> None:
    """Reject NaN and infinity extensions accepted by Python."""

    raise ValueError(
        f"Non-standard JSON constant is not permitted: {value}."
    )


def _append_json_segments(
    *,
    value: Any,
    pointer: str,
    segments: list[ProjectionSegmentDraft],
) -> None:
    """Append scalar leaves and empty containers in source order."""

    if isinstance(value, dict):
        if not value:
            segments.append(
                _create_json_segment(
                    pointer=pointer,
                    value=value,
                    segment_type="json_empty_object",
                )
            )
            return

        for key, child_value in value.items():
            child_pointer = (
                f"{pointer}/{_escape_json_pointer_token(key)}"
            )
            _append_json_segments(
                value=child_value,
                pointer=child_pointer,
                segments=segments,
            )

        return

    if isinstance(value, list):
        if not value:
            segments.append(
                _create_json_segment(
                    pointer=pointer,
                    value=value,
                    segment_type="json_empty_array",
                )
            )
            return

        for index, child_value in enumerate(value):
            child_pointer = f"{pointer}/{index}"
            _append_json_segments(
                value=child_value,
                pointer=child_pointer,
                segments=segments,
            )

        return

    segments.append(
        _create_json_segment(
            pointer=pointer,
            value=value,
            segment_type="json_value",
        )
    )


def _create_json_segment(
    *,
    pointer: str,
    value: Any,
    segment_type: str,
) -> ProjectionSegmentDraft:
    """Create one canonical, JSON-Pointer-located segment."""

    display_pointer = pointer if pointer else "<root>"
    rendered_value = json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
    )

    locator = SourceLocator(
        locator_type="json_pointer",
        coordinates=(
            ("pointer", pointer),
        ),
    )

    return ProjectionSegmentDraft(
        segment_type=segment_type,
        text=f"{display_pointer} = {rendered_value}",
        source_locators=(locator,),
    )


def _escape_json_pointer_token(token: str) -> str:
    """Escape one JSON Pointer reference token per RFC 6901."""

    return token.replace("~", "~0").replace("/", "~1")