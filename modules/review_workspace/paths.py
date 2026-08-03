"""Canonical project-local paths for Review Workspace persistence."""

from __future__ import annotations

from pathlib import Path

from modules.project_workspace.identifiers import (
    is_valid_project_id,
)

from .document_manifest import (
    REVIEW_DOCUMENT_MANIFEST_FILENAME,
)
from .errors import ReviewValidationError
from .identifiers import (
    validate_review_document_id,
    validate_review_document_version_id,
    validate_review_revision_id,
    validate_scoped_review_action_id,
)
from .revision_manifest import (
    review_revision_filename,
)
from .scoped_action_manifest import (
    scoped_review_action_filename,
)
from .version_manifest import (
    REVIEW_DOCUMENT_VERSION_MANIFEST_FILENAME,
)


REVIEWS_DIRECTORY_NAME = "reviews"
VERSIONS_DIRECTORY_NAME = "versions"
REVISIONS_DIRECTORY_NAME = "revisions"
SCOPED_ACTIONS_DIRECTORY_NAME = "scoped_actions"
FINALIZED_DIRECTORY_NAME = "finalized"

REVIEWED_DOCUMENT_FILENAME = "reviewed_document.json"
EFFECTIVE_DECISIONS_FILENAME = "effective_decisions.json"
REVIEWED_REPORT_FILENAME = "reviewed_report.md"


def project_path(
    root: Path | str,
    project_id: object,
) -> Path:
    """Return the canonical directory of one Project."""

    if not is_valid_project_id(project_id):
        raise ReviewValidationError(
            "project_id must be a string containing "
            "exactly six digits."
        )

    return Path(root) / project_id


def reviews_path(
    root: Path | str,
    project_id: object,
) -> Path:
    """Return the Review Workspace root of one Project."""

    return (
        project_path(root, project_id)
        / REVIEWS_DIRECTORY_NAME
    )


def review_document_path(
    root: Path | str,
    project_id: object,
    review_document_id: object,
) -> Path:
    """Return the directory of one Review Document."""

    validated_document_id = validate_review_document_id(
        review_document_id
    )

    return (
        reviews_path(root, project_id)
        / validated_document_id
    )


def review_document_manifest_path(
    root: Path | str,
    project_id: object,
    review_document_id: object,
) -> Path:
    """Return one Review Document Manifest path."""

    return (
        review_document_path(
            root,
            project_id,
            review_document_id,
        )
        / REVIEW_DOCUMENT_MANIFEST_FILENAME
    )


def review_versions_path(
    root: Path | str,
    project_id: object,
    review_document_id: object,
) -> Path:
    """Return the version root of one Review Document."""

    return (
        review_document_path(
            root,
            project_id,
            review_document_id,
        )
        / VERSIONS_DIRECTORY_NAME
    )


def review_document_version_path(
    root: Path | str,
    project_id: object,
    review_document_id: object,
    review_document_version_id: object,
) -> Path:
    """Return the directory of one Review Document Version."""

    validated_version_id = (
        validate_review_document_version_id(
            review_document_version_id
        )
    )

    return (
        review_versions_path(
            root,
            project_id,
            review_document_id,
        )
        / validated_version_id
    )


def review_document_version_manifest_path(
    root: Path | str,
    project_id: object,
    review_document_id: object,
    review_document_version_id: object,
) -> Path:
    """Return one Review Document Version Manifest path."""

    return (
        review_document_version_path(
            root,
            project_id,
            review_document_id,
            review_document_version_id,
        )
        / REVIEW_DOCUMENT_VERSION_MANIFEST_FILENAME
    )


def review_revisions_path(
    root: Path | str,
    project_id: object,
    review_document_id: object,
    review_document_version_id: object,
) -> Path:
    """Return the immutable revision root of one version."""

    return (
        review_document_version_path(
            root,
            project_id,
            review_document_id,
            review_document_version_id,
        )
        / REVISIONS_DIRECTORY_NAME
    )


def review_revision_path(
    root: Path | str,
    project_id: object,
    review_document_id: object,
    review_document_version_id: object,
    review_revision_id: object,
) -> Path:
    """Return one immutable Review Revision path."""

    validated_revision_id = validate_review_revision_id(
        review_revision_id
    )

    return (
        review_revisions_path(
            root,
            project_id,
            review_document_id,
            review_document_version_id,
        )
        / review_revision_filename(validated_revision_id)
    )


def scoped_review_actions_path(
    root: Path | str,
    project_id: object,
    review_document_id: object,
    review_document_version_id: object,
) -> Path:
    """Return the Scoped Review Action root of one version."""

    return (
        review_document_version_path(
            root,
            project_id,
            review_document_id,
            review_document_version_id,
        )
        / SCOPED_ACTIONS_DIRECTORY_NAME
    )


def scoped_review_action_path(
    root: Path | str,
    project_id: object,
    review_document_id: object,
    review_document_version_id: object,
    scoped_review_action_id: object,
) -> Path:
    """Return one immutable Scoped Review Action path."""

    validated_action_id = (
        validate_scoped_review_action_id(
            scoped_review_action_id
        )
    )

    return (
        scoped_review_actions_path(
            root,
            project_id,
            review_document_id,
            review_document_version_id,
        )
        / scoped_review_action_filename(
            validated_action_id
        )
    )


def finalized_review_path(
    root: Path | str,
    project_id: object,
    review_document_id: object,
    review_document_version_id: object,
) -> Path:
    """Return the finalized-artifact root of one version."""

    return (
        review_document_version_path(
            root,
            project_id,
            review_document_id,
            review_document_version_id,
        )
        / FINALIZED_DIRECTORY_NAME
    )


def reviewed_document_path(
    root: Path | str,
    project_id: object,
    review_document_id: object,
    review_document_version_id: object,
) -> Path:
    """Return the finalized reviewed-document path."""

    return (
        finalized_review_path(
            root,
            project_id,
            review_document_id,
            review_document_version_id,
        )
        / REVIEWED_DOCUMENT_FILENAME
    )


def effective_decisions_path(
    root: Path | str,
    project_id: object,
    review_document_id: object,
    review_document_version_id: object,
) -> Path:
    """Return the finalized effective-decisions path."""

    return (
        finalized_review_path(
            root,
            project_id,
            review_document_id,
            review_document_version_id,
        )
        / EFFECTIVE_DECISIONS_FILENAME
    )


def reviewed_report_path(
    root: Path | str,
    project_id: object,
    review_document_id: object,
    review_document_version_id: object,
) -> Path:
    """Return the finalized human-readable report path."""

    return (
        finalized_review_path(
            root,
            project_id,
            review_document_id,
            review_document_version_id,
        )
        / REVIEWED_REPORT_FILENAME
    )
