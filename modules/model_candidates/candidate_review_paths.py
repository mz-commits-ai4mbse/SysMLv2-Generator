"""Canonical project-local paths for Phase-H Candidate Review Decisions."""

from __future__ import annotations

from pathlib import Path

from modules.project_workspace.identifiers import is_valid_project_id

from .candidate_review_identifiers import (
    validate_model_candidate_review_decision_id,
)
from .errors import ModelCandidateValidationError


SEMANTICS_DIRECTORY_NAME = "semantics"
MODEL_CANDIDATE_REVIEWS_DIRECTORY_NAME = "model_candidate_reviews"


def model_candidate_reviews_path(
    root: Path | str,
    project_id: object,
) -> Path:
    if not is_valid_project_id(project_id):
        raise ModelCandidateValidationError(
            "project_id must be a valid six-digit Project ID."
        )
    return (
        Path(root)
        / project_id
        / SEMANTICS_DIRECTORY_NAME
        / MODEL_CANDIDATE_REVIEWS_DIRECTORY_NAME
    )


def model_candidate_review_decision_path(
    root: Path | str,
    project_id: object,
    decision_id: object,
) -> Path:
    validated = validate_model_candidate_review_decision_id(decision_id)
    return model_candidate_reviews_path(root, project_id) / f"{validated}.json"
