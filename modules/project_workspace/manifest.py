"""Validate, parse and serialize Project Workspace manifests.

This module owns only the manifest contract. Filesystem discovery and
persistence belong to ``workspace.py``.
"""

from __future__ import annotations

from datetime import datetime
import json
import re
from typing import Any

from modules.framework import (
    FrameworkTemplateError,
    load_framework_template,
)
from modules.project_workspace.errors import ProjectManifestError
from modules.project_workspace.identifiers import is_valid_project_id
from modules.project_workspace.types import (
    FrameworkTemplateReference,
    ProjectManifest,
)


PROJECT_MANIFEST_SCHEMA_VERSION = "1.0.0"
PROJECT_MANIFEST_FILENAME = "project_manifest.json"

DISPLAY_NAME_MAX_LENGTH = 120
DESCRIPTION_MAX_LENGTH = 2000

_MANIFEST_FIELDS = frozenset(
    {
        "schema_version",
        "project_id",
        "display_name",
        "description",
        "framework_template",
        "created_at",
        "updated_at",
    }
)

_FRAMEWORK_REFERENCE_FIELDS = frozenset(
    {
        "template_id",
        "template_version",
    }
)

_UTC_TIMESTAMP_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T"
    r"\d{2}:\d{2}:\d{2}"
    r"(?:\.\d+)?Z$"
)


def create_project_manifest(
    project_id: str,
    display_name: str,
    *,
    timestamp: str,
    description: str = "",
) -> ProjectManifest:
    """Create and validate the initial manifest for one project."""

    stored_display_name: Any = display_name

    if isinstance(display_name, str):
        stored_display_name = display_name.strip()

    framework_reference = _expected_framework_reference()

    payload = {
        "schema_version": PROJECT_MANIFEST_SCHEMA_VERSION,
        "project_id": project_id,
        "display_name": stored_display_name,
        "description": description,
        "framework_template": {
            "template_id": framework_reference.template_id,
            "template_version": framework_reference.template_version,
        },
        "created_at": timestamp,
        "updated_at": timestamp,
    }

    return parse_project_manifest(
        payload,
        expected_project_id=project_id,
    )


def parse_project_manifest(
    payload: Any,
    *,
    expected_project_id: str | None = None,
) -> ProjectManifest:
    """Parse and validate a manifest payload."""

    if not isinstance(payload, dict):
        raise ProjectManifestError(
            "Project manifest must be a JSON object."
        )

    _require_exact_fields(
        payload,
        _MANIFEST_FIELDS,
        "Project manifest",
    )

    schema_version = payload["schema_version"]

    if schema_version != PROJECT_MANIFEST_SCHEMA_VERSION:
        raise ProjectManifestError(
            "Unsupported project manifest schema_version: "
            f"{schema_version!r}."
        )

    project_id = payload["project_id"]

    if not is_valid_project_id(project_id):
        raise ProjectManifestError(
            "project_id must be a string containing exactly six digits."
        )

    if expected_project_id is not None:
        if not is_valid_project_id(expected_project_id):
            raise ProjectManifestError(
                "expected_project_id must contain exactly six digits."
            )

        if project_id != expected_project_id:
            raise ProjectManifestError(
                "Manifest project_id does not match its project directory: "
                f"{project_id!r} != {expected_project_id!r}."
            )

    display_name = _validate_display_name(payload["display_name"])
    description = _validate_description(payload["description"])

    framework_reference = _parse_framework_reference(
        payload["framework_template"]
    )

    created_at = payload["created_at"]
    updated_at = payload["updated_at"]

    created_datetime = _parse_utc_timestamp(
        created_at,
        "created_at",
    )
    updated_datetime = _parse_utc_timestamp(
        updated_at,
        "updated_at",
    )

    if updated_datetime < created_datetime:
        raise ProjectManifestError(
            "updated_at must not be earlier than created_at."
        )

    return ProjectManifest(
        schema_version=schema_version,
        project_id=project_id,
        display_name=display_name,
        description=description,
        framework_template=framework_reference,
        created_at=created_at,
        updated_at=updated_at,
    )


def project_manifest_from_json(
    text: str,
    *,
    expected_project_id: str | None = None,
) -> ProjectManifest:
    """Parse and validate a project manifest from JSON text."""

    if not isinstance(text, str):
        raise ProjectManifestError(
            "Project manifest JSON input must be a string."
        )

    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ProjectManifestError(
            f"Project manifest contains invalid JSON: {exc}."
        ) from exc

    return parse_project_manifest(
        payload,
        expected_project_id=expected_project_id,
    )


def validate_project_manifest(
    manifest: ProjectManifest,
    *,
    expected_project_id: str | None = None,
) -> None:
    """Validate an immutable ProjectManifest instance."""

    payload = _project_manifest_payload(manifest)

    parse_project_manifest(
        payload,
        expected_project_id=expected_project_id,
    )


def project_manifest_to_dict(
    manifest: ProjectManifest,
) -> dict[str, Any]:
    """Return a validated JSON-compatible manifest dictionary."""

    payload = _project_manifest_payload(manifest)
    validate_project_manifest(manifest)

    return payload


def project_manifest_to_json(
    manifest: ProjectManifest,
) -> str:
    """Serialize a validated project manifest deterministically."""

    payload = project_manifest_to_dict(manifest)

    return json.dumps(
        payload,
        ensure_ascii=False,
        indent=2,
    ) + "\n"


def _project_manifest_payload(
    manifest: ProjectManifest,
) -> dict[str, Any]:
    if not isinstance(manifest, ProjectManifest):
        raise ProjectManifestError(
            "manifest must be a ProjectManifest instance."
        )

    framework_reference = manifest.framework_template

    if not isinstance(
        framework_reference,
        FrameworkTemplateReference,
    ):
        raise ProjectManifestError(
            "framework_template must be a "
            "FrameworkTemplateReference instance."
        )

    return {
        "schema_version": manifest.schema_version,
        "project_id": manifest.project_id,
        "display_name": manifest.display_name,
        "description": manifest.description,
        "framework_template": {
            "template_id": framework_reference.template_id,
            "template_version": framework_reference.template_version,
        },
        "created_at": manifest.created_at,
        "updated_at": manifest.updated_at,
    }


def _validate_display_name(value: Any) -> str:
    if not isinstance(value, str):
        raise ProjectManifestError(
            "display_name must be a string."
        )

    trimmed = value.strip()

    if not trimmed:
        raise ProjectManifestError(
            "display_name must not be empty."
        )

    if value != trimmed:
        raise ProjectManifestError(
            "display_name must not contain leading or trailing whitespace."
        )

    if len(trimmed) > DISPLAY_NAME_MAX_LENGTH:
        raise ProjectManifestError(
            "display_name must contain at most "
            f"{DISPLAY_NAME_MAX_LENGTH} characters."
        )

    return value


def _validate_description(value: Any) -> str:
    if not isinstance(value, str):
        raise ProjectManifestError(
            "description must be a string."
        )

    if len(value) > DESCRIPTION_MAX_LENGTH:
        raise ProjectManifestError(
            "description must contain at most "
            f"{DESCRIPTION_MAX_LENGTH} characters."
        )

    return value


def _parse_framework_reference(
    value: Any,
) -> FrameworkTemplateReference:
    if not isinstance(value, dict):
        raise ProjectManifestError(
            "framework_template must be an object."
        )

    _require_exact_fields(
        value,
        _FRAMEWORK_REFERENCE_FIELDS,
        "framework_template",
    )

    template_id = value["template_id"]
    template_version = value["template_version"]

    if not isinstance(template_id, str):
        raise ProjectManifestError(
            "framework_template.template_id must be a string."
        )

    if not isinstance(template_version, str):
        raise ProjectManifestError(
            "framework_template.template_version must be a string."
        )

    actual_reference = FrameworkTemplateReference(
        template_id=template_id,
        template_version=template_version,
    )
    expected_reference = _expected_framework_reference()

    if actual_reference != expected_reference:
        raise ProjectManifestError(
            "Unsupported framework template reference: "
            f"{template_id!r} version {template_version!r}. "
            "Expected "
            f"{expected_reference.template_id!r} version "
            f"{expected_reference.template_version!r}."
        )

    return actual_reference


def _expected_framework_reference() -> FrameworkTemplateReference:
    try:
        template = load_framework_template()
    except FrameworkTemplateError as exc:
        raise ProjectManifestError(
            f"Unable to validate the framework template: {exc}"
        ) from exc

    return FrameworkTemplateReference(
        template_id=template["template_id"],
        template_version=template["template_version"],
    )


def _parse_utc_timestamp(
    value: Any,
    field_name: str,
) -> datetime:
    if (
        not isinstance(value, str)
        or _UTC_TIMESTAMP_PATTERN.fullmatch(value) is None
    ):
        raise ProjectManifestError(
            f"{field_name} must be an ISO-8601 UTC timestamp ending in Z."
        )

    try:
        return datetime.fromisoformat(
            value.removesuffix("Z") + "+00:00"
        )
    except ValueError as exc:
        raise ProjectManifestError(
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
        raise ProjectManifestError(
            f"{label} fields are invalid: {'; '.join(problems)}."
        )