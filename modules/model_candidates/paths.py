"""Canonical project-local paths for Phase-H Model Candidates."""

from __future__ import annotations

from pathlib import Path

from modules.project_workspace.identifiers import is_valid_project_id

from .errors import ModelCandidateValidationError
from .identifiers import (
    validate_model_candidate_set_id,
    validate_model_element_candidate_id,
    validate_model_relationship_candidate_id,
)


MODEL_CANDIDATES_DIRECTORY_NAME = "model_candidates"
MODEL_CANDIDATE_SETS_DIRECTORY_NAME = "sets"
MODEL_CANDIDATE_SET_MANIFEST_FILENAME = "manifest.json"
MODEL_CANDIDATE_ELEMENTS_DIRECTORY_NAME = "elements"
MODEL_CANDIDATE_RELATIONSHIPS_DIRECTORY_NAME = "relationships"


def project_path(root: Path | str, project_id: object) -> Path:
    """Return the canonical directory of one Project."""

    if not is_valid_project_id(project_id):
        raise ModelCandidateValidationError(
            "project_id must be a string containing exactly six digits."
        )
    return Path(root) / project_id


def model_candidates_path(
    root: Path | str,
    project_id: object,
) -> Path:
    """Return the Model Candidate repository root."""

    return (
        project_path(root, project_id)
        / MODEL_CANDIDATES_DIRECTORY_NAME
    )


def model_candidate_sets_path(
    root: Path | str,
    project_id: object,
) -> Path:
    """Return the immutable Candidate Set root."""

    return (
        model_candidates_path(root, project_id)
        / MODEL_CANDIDATE_SETS_DIRECTORY_NAME
    )


def model_candidate_set_path(
    root: Path | str,
    project_id: object,
    candidate_set_id: object,
) -> Path:
    """Return one immutable Candidate Set directory."""

    validated_id = validate_model_candidate_set_id(candidate_set_id)
    return model_candidate_sets_path(root, project_id) / validated_id


def model_candidate_set_manifest_path(
    root: Path | str,
    project_id: object,
    candidate_set_id: object,
) -> Path:
    """Return the manifest path of one Candidate Set."""

    return (
        model_candidate_set_path(root, project_id, candidate_set_id)
        / MODEL_CANDIDATE_SET_MANIFEST_FILENAME
    )


def model_candidate_elements_path(
    root: Path | str,
    project_id: object,
    candidate_set_id: object,
) -> Path:
    """Return the Element Candidate directory of one Candidate Set."""

    return (
        model_candidate_set_path(root, project_id, candidate_set_id)
        / MODEL_CANDIDATE_ELEMENTS_DIRECTORY_NAME
    )


def model_element_candidate_filename(
    model_element_candidate_id: object,
) -> str:
    """Return the canonical Element Candidate filename."""

    validated_id = validate_model_element_candidate_id(
        model_element_candidate_id
    )
    return f"{validated_id}.json"


def model_element_candidate_path(
    root: Path | str,
    project_id: object,
    candidate_set_id: object,
    model_element_candidate_id: object,
) -> Path:
    """Return one Element Candidate path."""

    return (
        model_candidate_elements_path(
            root,
            project_id,
            candidate_set_id,
        )
        / model_element_candidate_filename(
            model_element_candidate_id
        )
    )


def model_candidate_relationships_path(
    root: Path | str,
    project_id: object,
    candidate_set_id: object,
) -> Path:
    """Return the Relationship Candidate directory of one Candidate Set."""

    return (
        model_candidate_set_path(root, project_id, candidate_set_id)
        / MODEL_CANDIDATE_RELATIONSHIPS_DIRECTORY_NAME
    )


def model_relationship_candidate_filename(
    model_relationship_candidate_id: object,
) -> str:
    """Return the canonical Relationship Candidate filename."""

    validated_id = validate_model_relationship_candidate_id(
        model_relationship_candidate_id
    )
    return f"{validated_id}.json"


def model_relationship_candidate_path(
    root: Path | str,
    project_id: object,
    candidate_set_id: object,
    model_relationship_candidate_id: object,
) -> Path:
    """Return one Relationship Candidate path."""

    return (
        model_candidate_relationships_path(
            root,
            project_id,
            candidate_set_id,
        )
        / model_relationship_candidate_filename(
            model_relationship_candidate_id
        )
    )
