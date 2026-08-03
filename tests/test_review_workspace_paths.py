"""Tests for canonical Review Workspace persistence paths."""

from __future__ import annotations

from pathlib import Path

import pytest

from modules.review_workspace.errors import (
    ReviewValidationError,
)
from modules.review_workspace.paths import (
    EFFECTIVE_DECISIONS_FILENAME,
    FINALIZED_DIRECTORY_NAME,
    REVIEWS_DIRECTORY_NAME,
    REVIEWED_DOCUMENT_FILENAME,
    REVIEWED_REPORT_FILENAME,
    REVISIONS_DIRECTORY_NAME,
    SCOPED_ACTIONS_DIRECTORY_NAME,
    VERSIONS_DIRECTORY_NAME,
    effective_decisions_path,
    finalized_review_path,
    project_path,
    review_document_manifest_path,
    review_document_path,
    review_document_version_manifest_path,
    review_document_version_path,
    review_revision_path,
    review_revisions_path,
    review_versions_path,
    reviewed_document_path,
    reviewed_report_path,
    reviews_path,
    scoped_review_action_path,
    scoped_review_actions_path,
)


ROOT = Path("data/projects")
PROJECT_ID = "000001"
DOCUMENT_ID = "RVD-000001"
VERSION_ID = "RVV-000001"
REVISION_ID = "RVR-000001"
ACTION_ID = "SRA-000001"


def test_directory_and_filename_constants_are_explicit() -> None:
    assert REVIEWS_DIRECTORY_NAME == "reviews"
    assert VERSIONS_DIRECTORY_NAME == "versions"
    assert REVISIONS_DIRECTORY_NAME == "revisions"
    assert SCOPED_ACTIONS_DIRECTORY_NAME == (
        "scoped_actions"
    )
    assert FINALIZED_DIRECTORY_NAME == "finalized"

    assert REVIEWED_DOCUMENT_FILENAME == (
        "reviewed_document.json"
    )
    assert EFFECTIVE_DECISIONS_FILENAME == (
        "effective_decisions.json"
    )
    assert REVIEWED_REPORT_FILENAME == (
        "reviewed_report.md"
    )


def test_project_and_review_roots_are_canonical() -> None:
    assert project_path(
        ROOT,
        PROJECT_ID,
    ) == Path(
        "data/projects/000001"
    )

    assert reviews_path(
        ROOT,
        PROJECT_ID,
    ) == Path(
        "data/projects/000001/reviews"
    )


def test_review_document_paths_are_canonical() -> None:
    assert review_document_path(
        ROOT,
        PROJECT_ID,
        DOCUMENT_ID,
    ) == Path(
        "data/projects/000001/reviews/RVD-000001"
    )

    assert review_document_manifest_path(
        ROOT,
        PROJECT_ID,
        DOCUMENT_ID,
    ) == Path(
        "data/projects/000001/reviews/RVD-000001/"
        "review_document_manifest.json"
    )


def test_review_version_paths_are_canonical() -> None:
    assert review_versions_path(
        ROOT,
        PROJECT_ID,
        DOCUMENT_ID,
    ) == Path(
        "data/projects/000001/reviews/RVD-000001/"
        "versions"
    )

    assert review_document_version_path(
        ROOT,
        PROJECT_ID,
        DOCUMENT_ID,
        VERSION_ID,
    ) == Path(
        "data/projects/000001/reviews/RVD-000001/"
        "versions/RVV-000001"
    )

    assert review_document_version_manifest_path(
        ROOT,
        PROJECT_ID,
        DOCUMENT_ID,
        VERSION_ID,
    ) == Path(
        "data/projects/000001/reviews/RVD-000001/"
        "versions/RVV-000001/"
        "review_version_manifest.json"
    )


def test_review_revision_paths_are_canonical() -> None:
    assert review_revisions_path(
        ROOT,
        PROJECT_ID,
        DOCUMENT_ID,
        VERSION_ID,
    ) == Path(
        "data/projects/000001/reviews/RVD-000001/"
        "versions/RVV-000001/revisions"
    )

    assert review_revision_path(
        ROOT,
        PROJECT_ID,
        DOCUMENT_ID,
        VERSION_ID,
        REVISION_ID,
    ) == Path(
        "data/projects/000001/reviews/RVD-000001/"
        "versions/RVV-000001/revisions/"
        "RVR-000001.json"
    )


def test_scoped_action_paths_are_canonical() -> None:
    assert scoped_review_actions_path(
        ROOT,
        PROJECT_ID,
        DOCUMENT_ID,
        VERSION_ID,
    ) == Path(
        "data/projects/000001/reviews/RVD-000001/"
        "versions/RVV-000001/scoped_actions"
    )

    assert scoped_review_action_path(
        ROOT,
        PROJECT_ID,
        DOCUMENT_ID,
        VERSION_ID,
        ACTION_ID,
    ) == Path(
        "data/projects/000001/reviews/RVD-000001/"
        "versions/RVV-000001/scoped_actions/"
        "SRA-000001.json"
    )


def test_finalized_artifact_paths_are_canonical() -> None:
    assert finalized_review_path(
        ROOT,
        PROJECT_ID,
        DOCUMENT_ID,
        VERSION_ID,
    ) == Path(
        "data/projects/000001/reviews/RVD-000001/"
        "versions/RVV-000001/finalized"
    )

    assert reviewed_document_path(
        ROOT,
        PROJECT_ID,
        DOCUMENT_ID,
        VERSION_ID,
    ) == Path(
        "data/projects/000001/reviews/RVD-000001/"
        "versions/RVV-000001/finalized/"
        "reviewed_document.json"
    )

    assert effective_decisions_path(
        ROOT,
        PROJECT_ID,
        DOCUMENT_ID,
        VERSION_ID,
    ) == Path(
        "data/projects/000001/reviews/RVD-000001/"
        "versions/RVV-000001/finalized/"
        "effective_decisions.json"
    )

    assert reviewed_report_path(
        ROOT,
        PROJECT_ID,
        DOCUMENT_ID,
        VERSION_ID,
    ) == Path(
        "data/projects/000001/reviews/RVD-000001/"
        "versions/RVV-000001/finalized/"
        "reviewed_report.md"
    )


@pytest.mark.parametrize(
    "project_id",
    (
        "1",
        "00001",
        "0000001",
        "ABCDEF",
        "../001",
        None,
    ),
)
def test_project_path_rejects_invalid_project_ids(
    project_id: object,
) -> None:
    with pytest.raises(ReviewValidationError):
        project_path(ROOT, project_id)


@pytest.mark.parametrize(
    "review_document_id",
    (
        "RVD-000000",
        "RVD-00001",
        "RVD-0000001",
        "../RVD-000001",
        "INVALID",
        None,
    ),
)
def test_document_paths_reject_invalid_ids(
    review_document_id: object,
) -> None:
    with pytest.raises(ReviewValidationError):
        review_document_path(
            ROOT,
            PROJECT_ID,
            review_document_id,
        )


@pytest.mark.parametrize(
    "review_document_version_id",
    (
        "RVV-000000",
        "RVV-00001",
        "RVV-0000001",
        "../RVV-000001",
        "INVALID",
        None,
    ),
)
def test_version_paths_reject_invalid_ids(
    review_document_version_id: object,
) -> None:
    with pytest.raises(ReviewValidationError):
        review_document_version_path(
            ROOT,
            PROJECT_ID,
            DOCUMENT_ID,
            review_document_version_id,
        )


@pytest.mark.parametrize(
    "review_revision_id",
    (
        "RVR-000000",
        "RVR-00001",
        "RVR-0000001",
        "../RVR-000001",
        "INVALID",
        None,
    ),
)
def test_revision_paths_reject_invalid_ids(
    review_revision_id: object,
) -> None:
    with pytest.raises(ReviewValidationError):
        review_revision_path(
            ROOT,
            PROJECT_ID,
            DOCUMENT_ID,
            VERSION_ID,
            review_revision_id,
        )


@pytest.mark.parametrize(
    "scoped_review_action_id",
    (
        "SRA-000000",
        "SRA-00001",
        "SRA-0000001",
        "../SRA-000001",
        "INVALID",
        None,
    ),
)
def test_scoped_action_paths_reject_invalid_ids(
    scoped_review_action_id: object,
) -> None:
    with pytest.raises(ReviewValidationError):
        scoped_review_action_path(
            ROOT,
            PROJECT_ID,
            DOCUMENT_ID,
            VERSION_ID,
            scoped_review_action_id,
        )


def test_custom_root_is_preserved() -> None:
    root = Path("/tmp/turing-projects")

    assert reviewed_report_path(
        root,
        PROJECT_ID,
        DOCUMENT_ID,
        VERSION_ID,
    ) == (
        root
        / PROJECT_ID
        / "reviews"
        / DOCUMENT_ID
        / "versions"
        / VERSION_ID
        / "finalized"
        / "reviewed_report.md"
    )
