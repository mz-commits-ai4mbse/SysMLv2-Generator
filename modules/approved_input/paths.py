"""Canonical project-local paths for Approved Input persistence."""

from __future__ import annotations

from pathlib import Path

from modules.project_workspace.identifiers import is_valid_project_id

from .errors import ApprovedInputValidationError
from .identifiers import (
    validate_approved_input_event_id,
    validate_approved_input_id,
)


APPROVED_INPUTS_DIRECTORY_NAME = "approved_inputs"
APPROVED_INPUT_MANIFESTS_DIRECTORY_NAME = "manifests"
APPROVED_INPUT_EVENTS_DIRECTORY_NAME = "events"


def project_path(
    root: Path | str,
    project_id: object,
) -> Path:
    """Return the canonical directory of one Project."""

    if not is_valid_project_id(project_id):
        raise ApprovedInputValidationError(
            "project_id must be a string containing exactly six digits."
        )

    return Path(root) / project_id


def approved_inputs_path(
    root: Path | str,
    project_id: object,
) -> Path:
    """Return the Approved Input repository root of one Project."""

    return (
        project_path(root, project_id)
        / APPROVED_INPUTS_DIRECTORY_NAME
    )


def approved_input_manifests_path(
    root: Path | str,
    project_id: object,
) -> Path:
    """Return the immutable Approved Input Manifest root."""

    return (
        approved_inputs_path(root, project_id)
        / APPROVED_INPUT_MANIFESTS_DIRECTORY_NAME
    )


def approved_input_events_path(
    root: Path | str,
    project_id: object,
) -> Path:
    """Return the reserved Approved Input Event root."""

    return (
        approved_inputs_path(root, project_id)
        / APPROVED_INPUT_EVENTS_DIRECTORY_NAME
    )


def approved_input_manifest_filename(
    approved_input_id: object,
) -> str:
    """Return the canonical filename of one Approved Input Manifest."""

    validated_id = validate_approved_input_id(approved_input_id)
    return f"{validated_id}.json"


def approved_input_manifest_path(
    root: Path | str,
    project_id: object,
    approved_input_id: object,
) -> Path:
    """Return the canonical path of one Approved Input Manifest."""

    return (
        approved_input_manifests_path(root, project_id)
        / approved_input_manifest_filename(approved_input_id)
    )


def approved_input_event_directory_path(
    root: Path | str,
    project_id: object,
    approved_input_id: object,
) -> Path:
    """Return the reserved event directory of one Approved Input."""

    validated_id = validate_approved_input_id(approved_input_id)

    return (
        approved_input_events_path(root, project_id)
        / validated_id
    )


def approved_input_event_filename(
    approved_input_event_id: object,
) -> str:
    """Return the canonical filename of one Approved Input Event."""

    validated_id = validate_approved_input_event_id(
        approved_input_event_id
    )
    return f"{validated_id}.json"


def approved_input_event_path(
    root: Path | str,
    project_id: object,
    approved_input_id: object,
    approved_input_event_id: object,
) -> Path:
    """Return the canonical path of one immutable lifecycle event."""

    return (
        approved_input_event_directory_path(
            root,
            project_id,
            approved_input_id,
        )
        / approved_input_event_filename(approved_input_event_id)
    )
