"""Canonical project-local paths for immutable Internal Engineering Models."""

from __future__ import annotations

from pathlib import Path

from modules.project_workspace.identifiers import is_valid_project_id

from .errors import InternalModelValidationError
from .identifiers import (
    validate_internal_engineering_model_id,
    validate_internal_model_element_id,
    validate_internal_model_relationship_id,
)


INTERNAL_MODELS_DIRECTORY_NAME = "internal_models"
INTERNAL_MODEL_MANIFEST_FILENAME = "manifest.json"
INTERNAL_MODEL_STRUCTURE_FILENAME = "structure.json"
INTERNAL_MODEL_ELEMENTS_DIRECTORY_NAME = "elements"
INTERNAL_MODEL_RELATIONSHIPS_DIRECTORY_NAME = "relationships"


def project_path(root: Path | str, project_id: object) -> Path:
    if not is_valid_project_id(project_id):
        raise InternalModelValidationError(
            "project_id must be a string containing exactly six digits."
        )
    return Path(root) / project_id


def internal_models_path(
    root: Path | str,
    project_id: object,
) -> Path:
    return project_path(root, project_id) / INTERNAL_MODELS_DIRECTORY_NAME


def internal_engineering_model_path(
    root: Path | str,
    project_id: object,
    internal_engineering_model_id: object,
) -> Path:
    validated = validate_internal_engineering_model_id(
        internal_engineering_model_id
    )
    return internal_models_path(root, project_id) / validated


def internal_model_manifest_path(
    root: Path | str,
    project_id: object,
    internal_engineering_model_id: object,
) -> Path:
    return (
        internal_engineering_model_path(
            root,
            project_id,
            internal_engineering_model_id,
        )
        / INTERNAL_MODEL_MANIFEST_FILENAME
    )


def internal_model_structure_path(
    root: Path | str,
    project_id: object,
    internal_engineering_model_id: object,
) -> Path:
    return (
        internal_engineering_model_path(
            root,
            project_id,
            internal_engineering_model_id,
        )
        / INTERNAL_MODEL_STRUCTURE_FILENAME
    )


def internal_model_elements_path(
    root: Path | str,
    project_id: object,
    internal_engineering_model_id: object,
) -> Path:
    return (
        internal_engineering_model_path(
            root,
            project_id,
            internal_engineering_model_id,
        )
        / INTERNAL_MODEL_ELEMENTS_DIRECTORY_NAME
    )


def internal_model_relationships_path(
    root: Path | str,
    project_id: object,
    internal_engineering_model_id: object,
) -> Path:
    return (
        internal_engineering_model_path(
            root,
            project_id,
            internal_engineering_model_id,
        )
        / INTERNAL_MODEL_RELATIONSHIPS_DIRECTORY_NAME
    )


def internal_model_element_filename(
    internal_model_element_id: object,
) -> str:
    validated = validate_internal_model_element_id(
        internal_model_element_id
    )
    return f"{validated}.json"


def internal_model_relationship_filename(
    internal_model_relationship_id: object,
) -> str:
    validated = validate_internal_model_relationship_id(
        internal_model_relationship_id
    )
    return f"{validated}.json"
