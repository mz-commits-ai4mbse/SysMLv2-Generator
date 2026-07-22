"""Validate, parse and serialize Project Source Manifests.

This module owns only the Source Manifest contract. Filesystem discovery,
integrity checks and persistence belong to ``registry.py``.
"""

from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
import re
from typing import Any

from modules.project_workspace.identifiers import is_valid_project_id

from .errors import SourceManifestError, UnsupportedSourceRoleError
from .identifiers import validate_source_id
from .types import SourceManifest


SOURCE_MANIFEST_SCHEMA_VERSION = "1.0.0"
SOURCE_MANIFEST_FILENAME = "source_manifest.json"

ENGINEERING_SOURCE_ROLE = "engineering_source"
CONTEXT_ONLY_SOURCE_ROLE = "context_only"

SOURCE_ROLES = frozenset(
    {
        ENGINEERING_SOURCE_ROLE,
        CONTEXT_ONLY_SOURCE_ROLE,
    }
)

_MANIFEST_FIELDS = frozenset(
    {
        "schema_version",
        "project_id",
        "source_id",
        "source_role",
        "original_filename",
        "stored_filename",
        "media_type",
        "size_bytes",
        "sha256",
        "registered_at",
        "updated_at",
    }
)

_MEDIA_TYPE_BY_SUFFIX = {
    ".bin": "application/octet-stream",
    ".csv": "text/csv",
    ".doc": "application/msword",
    ".docx": (
        "application/vnd.openxmlformats-officedocument."
        "wordprocessingml.document"
    ),
    ".html": "text/html",
    ".json": "application/json",
    ".md": "text/markdown",
    ".odt": "application/vnd.oasis.opendocument.text",
    ".pdf": "application/pdf",
    ".ppt": "application/vnd.ms-powerpoint",
    ".pptx": (
        "application/vnd.openxmlformats-officedocument."
        "presentationml.presentation"
    ),
    ".rtf": "application/rtf",
    ".tsv": "text/tab-separated-values",
    ".txt": "text/plain",
    ".xls": "application/vnd.ms-excel",
    ".xlsx": (
        "application/vnd.openxmlformats-officedocument."
        "spreadsheetml.sheet"
    ),
    ".xml": "application/xml",
}

_UTC_TIMESTAMP_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T"
    r"\d{2}:\d{2}:\d{2}"
    r"(?:\.\d+)?Z$"
)

_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_STORED_FILENAME_PATTERN = re.compile(
    r"^content\.[a-z0-9]{1,10}$"
)


def create_source_manifest(
    project_id: str,
    source_id: str,
    source_role: str,
    original_filename: str,
    *,
    size_bytes: int,
    sha256: str,
    timestamp: str,
) -> SourceManifest:
    """Create and validate the initial manifest for one source."""

    stored_filename, media_type = source_storage_metadata(
        original_filename
    )

    payload = {
        "schema_version": SOURCE_MANIFEST_SCHEMA_VERSION,
        "project_id": project_id,
        "source_id": source_id,
        "source_role": source_role,
        "original_filename": original_filename,
        "stored_filename": stored_filename,
        "media_type": media_type,
        "size_bytes": size_bytes,
        "sha256": sha256,
        "registered_at": timestamp,
        "updated_at": timestamp,
    }

    return parse_source_manifest(
        payload,
        expected_project_id=project_id,
        expected_source_id=source_id,
    )


def update_source_role_manifest(
    manifest: SourceManifest,
    source_role: str,
    *,
    timestamp: str,
) -> SourceManifest:
    """Return a validated manifest with an updated source role."""

    payload = source_manifest_to_dict(manifest)
    payload["source_role"] = source_role
    payload["updated_at"] = timestamp

    return parse_source_manifest(
        payload,
        expected_project_id=manifest.project_id,
        expected_source_id=manifest.source_id,
    )


def parse_source_manifest(
    payload: Any,
    *,
    expected_project_id: str | None = None,
    expected_source_id: str | None = None,
) -> SourceManifest:
    """Parse and validate a Source Manifest payload."""

    if not isinstance(payload, dict):
        raise SourceManifestError(
            "Source Manifest must be a JSON object."
        )

    _require_exact_fields(
        payload,
        _MANIFEST_FIELDS,
        "Source Manifest",
    )

    schema_version = payload["schema_version"]

    if schema_version != SOURCE_MANIFEST_SCHEMA_VERSION:
        raise SourceManifestError(
            "Unsupported Source Manifest schema_version: "
            f"{schema_version!r}."
        )

    project_id = _validate_project_id(payload["project_id"])

    if expected_project_id is not None:
        validated_expected_project_id = _validate_project_id(
            expected_project_id,
            field_name="expected_project_id",
        )

        if project_id != validated_expected_project_id:
            raise SourceManifestError(
                "Manifest project_id does not match its project directory: "
                f"{project_id!r} != "
                f"{validated_expected_project_id!r}."
            )

    source_id = validate_source_id(payload["source_id"])

    if expected_source_id is not None:
        validated_expected_source_id = validate_source_id(
            expected_source_id
        )

        if source_id != validated_expected_source_id:
            raise SourceManifestError(
                "Manifest source_id does not match its source directory: "
                f"{source_id!r} != "
                f"{validated_expected_source_id!r}."
            )

    source_role = validate_source_role(payload["source_role"])

    original_filename = _validate_original_filename(
        payload["original_filename"]
    )
    stored_filename = _validate_stored_filename(
        payload["stored_filename"]
    )
    media_type = _validate_media_type(payload["media_type"])

    expected_stored_filename, expected_media_type = (
        source_storage_metadata(original_filename)
    )

    if stored_filename != expected_stored_filename:
        raise SourceManifestError(
            "stored_filename does not match original_filename: "
            f"{stored_filename!r} != "
            f"{expected_stored_filename!r}."
        )

    if media_type != expected_media_type:
        raise SourceManifestError(
            "media_type does not match stored_filename: "
            f"{media_type!r} != {expected_media_type!r}."
        )

    size_bytes = _validate_size_bytes(payload["size_bytes"])
    sha256 = _validate_sha256(payload["sha256"])

    registered_at = payload["registered_at"]
    updated_at = payload["updated_at"]

    registered_datetime = _parse_utc_timestamp(
        registered_at,
        "registered_at",
    )
    updated_datetime = _parse_utc_timestamp(
        updated_at,
        "updated_at",
    )

    if updated_datetime < registered_datetime:
        raise SourceManifestError(
            "updated_at must not be earlier than registered_at."
        )

    return SourceManifest(
        schema_version=schema_version,
        project_id=project_id,
        source_id=source_id,
        source_role=source_role,
        original_filename=original_filename,
        stored_filename=stored_filename,
        media_type=media_type,
        size_bytes=size_bytes,
        sha256=sha256,
        registered_at=registered_at,
        updated_at=updated_at,
    )


def source_manifest_from_json(
    text: str,
    *,
    expected_project_id: str | None = None,
    expected_source_id: str | None = None,
) -> SourceManifest:
    """Parse and validate a Source Manifest from JSON text."""

    if not isinstance(text, str):
        raise SourceManifestError(
            "Source Manifest JSON input must be a string."
        )

    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise SourceManifestError(
            f"Source Manifest contains invalid JSON: {exc}."
        ) from exc

    return parse_source_manifest(
        payload,
        expected_project_id=expected_project_id,
        expected_source_id=expected_source_id,
    )


def validate_source_manifest(
    manifest: SourceManifest,
    *,
    expected_project_id: str | None = None,
    expected_source_id: str | None = None,
) -> None:
    """Validate an immutable SourceManifest instance."""

    payload = _source_manifest_payload(manifest)

    parse_source_manifest(
        payload,
        expected_project_id=expected_project_id,
        expected_source_id=expected_source_id,
    )


def source_manifest_to_dict(
    manifest: SourceManifest,
) -> dict[str, Any]:
    """Return a validated JSON-compatible manifest dictionary."""

    payload = _source_manifest_payload(manifest)
    validate_source_manifest(manifest)

    return payload


def source_manifest_to_json(
    manifest: SourceManifest,
) -> str:
    """Serialize a validated Source Manifest deterministically."""

    payload = source_manifest_to_dict(manifest)

    return json.dumps(
        payload,
        ensure_ascii=False,
        indent=2,
    ) + "\n"


def source_storage_metadata(
    original_filename: str,
) -> tuple[str, str]:
    """Return the generated stored filename and deterministic media type."""

    validated_original_filename = _validate_original_filename(
        original_filename
    )
    suffix = Path(validated_original_filename).suffix.lower()

    if suffix not in _MEDIA_TYPE_BY_SUFFIX:
        suffix = ".bin"

    return (
        f"content{suffix}",
        _MEDIA_TYPE_BY_SUFFIX[suffix],
    )


def validate_source_role(value: Any) -> str:
    """Validate and return one explicit source role."""

    if not isinstance(value, str):
        raise UnsupportedSourceRoleError(
            "source_role must be a string."
        )

    if value not in SOURCE_ROLES:
        allowed_roles = ", ".join(sorted(SOURCE_ROLES))

        raise UnsupportedSourceRoleError(
            "Unsupported source_role: "
            f"{value!r}. Expected one of: {allowed_roles}."
        )

    return value


def _source_manifest_payload(
    manifest: SourceManifest,
) -> dict[str, Any]:
    if not isinstance(manifest, SourceManifest):
        raise SourceManifestError(
            "manifest must be a SourceManifest instance."
        )

    return {
        "schema_version": manifest.schema_version,
        "project_id": manifest.project_id,
        "source_id": manifest.source_id,
        "source_role": manifest.source_role,
        "original_filename": manifest.original_filename,
        "stored_filename": manifest.stored_filename,
        "media_type": manifest.media_type,
        "size_bytes": manifest.size_bytes,
        "sha256": manifest.sha256,
        "registered_at": manifest.registered_at,
        "updated_at": manifest.updated_at,
    }


def _validate_project_id(
    value: Any,
    *,
    field_name: str = "project_id",
) -> str:
    if not is_valid_project_id(value):
        raise SourceManifestError(
            f"{field_name} must be a string containing exactly six digits."
        )

    return value


def _validate_original_filename(value: Any) -> str:
    if not isinstance(value, str):
        raise SourceManifestError(
            "original_filename must be a string."
        )

    if not value.strip():
        raise SourceManifestError(
            "original_filename must not be empty."
        )

    if value in {".", ".."}:
        raise SourceManifestError(
            "original_filename must be a file basename."
        )

    if any(character in value for character in ("/", "\\", "\x00")):
        raise SourceManifestError(
            "original_filename must not contain path separators."
        )

    if any(ord(character) < 32 for character in value):
        raise SourceManifestError(
            "original_filename must not contain control characters."
        )

    return value


def _validate_stored_filename(value: Any) -> str:
    if (
        not isinstance(value, str)
        or _STORED_FILENAME_PATTERN.fullmatch(value) is None
    ):
        raise SourceManifestError(
            "stored_filename must match "
            "^content\\.[a-z0-9]{1,10}$."
        )

    if Path(value).name != value:
        raise SourceManifestError(
            "stored_filename must be a file basename."
        )

    return value


def _validate_media_type(value: Any) -> str:
    if not isinstance(value, str):
        raise SourceManifestError(
            "media_type must be a string."
        )

    if not value or value != value.strip():
        raise SourceManifestError(
            "media_type must be a non-empty trimmed string."
        )

    return value


def _validate_size_bytes(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise SourceManifestError(
            "size_bytes must be an integer."
        )

    if value <= 0:
        raise SourceManifestError(
            "size_bytes must be greater than zero."
        )

    return value


def _validate_sha256(value: Any) -> str:
    if (
        not isinstance(value, str)
        or _SHA256_PATTERN.fullmatch(value) is None
    ):
        raise SourceManifestError(
            "sha256 must be a lowercase 64-character "
            "hexadecimal value."
        )

    return value


def _parse_utc_timestamp(
    value: Any,
    field_name: str,
) -> datetime:
    if (
        not isinstance(value, str)
        or _UTC_TIMESTAMP_PATTERN.fullmatch(value) is None
    ):
        raise SourceManifestError(
            f"{field_name} must be an ISO-8601 UTC "
            "timestamp ending in Z."
        )

    try:
        return datetime.fromisoformat(
            value.removesuffix("Z") + "+00:00"
        )
    except ValueError as exc:
        raise SourceManifestError(
            f"{field_name} is not a valid UTC timestamp."
        ) from exc


def _require_exact_fields(
    value: dict[str, Any],
    expected_fields: frozenset[str],
    label: str,
) -> None:
    actual_fields = set(value)
    missing_fields = sorted(expected_fields - actual_fields)
    unknown_fields = sorted(actual_fields - expected_fields)

    problems: list[str] = []

    if missing_fields:
        problems.append(
            "missing " + ", ".join(missing_fields)
        )

    if unknown_fields:
        problems.append(
            "unknown " + ", ".join(unknown_fields)
        )

    if problems:
        raise SourceManifestError(
            f"{label} fields are invalid: {'; '.join(problems)}."
        )