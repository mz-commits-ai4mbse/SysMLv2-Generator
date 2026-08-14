"""Canonical project-local paths for Phase-L Final Model Review."""

from __future__ import annotations

from pathlib import Path
from modules.project_workspace.identifiers import is_valid_project_id

from .errors import FinalModelReviewValidationError
from .identifiers import (
    validate_final_model_review_change_proposal_id,
    validate_final_model_review_decision_id,
    validate_final_model_review_id,
    validate_final_model_review_item_id,
    validate_final_model_review_revision_id,
)

ROOT_NAME = "final_model_reviews"


def _project(project_id: object) -> str:
    if not is_valid_project_id(project_id):
        raise FinalModelReviewValidationError(
            "project_id must be a valid six-digit Project ID."
        )
    return project_id


def final_model_reviews_path(root: Path | str, project_id: object) -> Path:
    return Path(root) / _project(project_id) / ROOT_NAME


def final_model_review_path(root, project_id, review_id) -> Path:
    return final_model_reviews_path(root, project_id) / validate_final_model_review_id(review_id)


def final_model_review_manifest_path(root, project_id, review_id) -> Path:
    return final_model_review_path(root, project_id, review_id) / "manifest.json"


def final_model_review_revisions_path(root, project_id, review_id) -> Path:
    return final_model_review_path(root, project_id, review_id) / "revisions"


def final_model_review_revision_path(root, project_id, review_id, revision_id) -> Path:
    return final_model_review_revisions_path(root, project_id, review_id) / validate_final_model_review_revision_id(revision_id)


def final_model_review_revision_items_path(root, project_id, review_id, revision_id) -> Path:
    return final_model_review_revision_path(root, project_id, review_id, revision_id) / "items"


def final_model_review_item_path(root, project_id, review_id, revision_id, item_id) -> Path:
    return final_model_review_revision_items_path(root, project_id, review_id, revision_id) / f"{validate_final_model_review_item_id(item_id)}.json"


def final_model_review_decisions_path(root, project_id, review_id) -> Path:
    return final_model_review_path(root, project_id, review_id) / "decisions"


def final_model_review_decision_path(root, project_id, review_id, decision_id) -> Path:
    return final_model_review_decisions_path(root, project_id, review_id) / f"{validate_final_model_review_decision_id(decision_id)}.json"


def final_model_review_change_proposals_path(
    root: Path | str,
    project_id: object,
    review_id: object,
) -> Path:
    return final_model_review_path(
        root, project_id, review_id
    ) / "change_proposals"


def final_model_review_change_proposal_path(
    root: Path | str,
    project_id: object,
    review_id: object,
    change_proposal_id: object,
) -> Path:
    return final_model_review_change_proposals_path(
        root, project_id, review_id
    ) / f"{validate_final_model_review_change_proposal_id(change_proposal_id)}.json"
