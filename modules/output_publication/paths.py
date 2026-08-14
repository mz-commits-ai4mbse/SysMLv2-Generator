"""Canonical paths for authoritative final published outputs."""

from __future__ import annotations

from pathlib import Path

from modules.project_workspace.identifiers import is_valid_project_id

from .errors import OutputPublicationValidationError
from .identifiers import validate_output_package_id


DEFAULT_OUTPUT_ROOT = Path("data/output")


def output_project_path(
    output_root: Path | str,
    project_id: object,
) -> Path:
    if not is_valid_project_id(project_id):
        raise OutputPublicationValidationError(
            "project_id must be a valid six-digit Project ID."
        )
    return Path(output_root) / project_id


def output_package_path(
    output_root: Path | str,
    project_id: object,
    output_package_id: object,
) -> Path:
    return output_project_path(output_root, project_id) / (
        validate_output_package_id(output_package_id)
    )


def output_manifest_path(
    output_root: Path | str,
    project_id: object,
    output_package_id: object,
) -> Path:
    return output_package_path(
        output_root, project_id, output_package_id
    ) / "manifest.json"
