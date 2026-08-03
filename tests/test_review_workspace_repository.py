"""Tests for project-isolated Review Workspace persistence."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

import pytest

from modules.project_processing import (
    ProcessingArtifactReference,
)
from modules.project_workspace import ProjectWorkspace
from modules.project_workspace.types import (
    FrameworkTemplateReference,
)
from modules.review_workspace.document_manifest import (
    create_review_document,
    review_document_to_json,
)
from modules.review_workspace.errors import (
    ReviewDocumentNotFoundError,
    ReviewDocumentVersionNotFoundError,
    ReviewIntegrityError,
    ReviewPersistenceError,
    ReviewRecoveryRequiredError,
    ReviewReferenceError,
    ReviewRevisionNotFoundError,
    UnsafeReviewWorkspacePathError,
)
from modules.review_workspace.paths import (
    review_document_path,
    review_document_version_path,
    review_revision_path,
    reviews_path,
)
from modules.review_workspace.repository import (
    ReviewWorkspaceRepository,
)
from modules.review_workspace.revision_manifest import (
    create_review_revision,
    review_revision_to_json,
)
from modules.review_workspace.version_manifest import (
    create_review_document_version,
    finalize_review_document_version,
    review_document_version_to_json,
)


def _clock() -> datetime:
    return datetime(
        2026,
        8,
        3,
        16,
        0,
        tzinfo=timezone.utc,
    )


def _create_project(root: Path) -> None:
    workspace = ProjectWorkspace(
        root=root,
        id_generator=lambda: "000001",
        clock=_clock,
    )
    workspace.create_project(
        "Review Repository Test",
    )


@pytest.fixture
def repository(
    tmp_path: Path,
) -> tuple[ReviewWorkspaceRepository, Path]:
    root = tmp_path / "projects"
    _create_project(root)

    return (
        ReviewWorkspaceRepository(root=root),
        root,
    )


def _bundle(
    *,
    project_id: str = "000001",
    document_id: str = "RVD-000001",
    version_id: str = "RVV-000001",
    revision_id: str = "RVR-000001",
):
    document = create_review_document(
        project_id=project_id,
        review_document_id=document_id,
        source_id="SRC-000001",
        source_sha256="a" * 64,
        processing_run_id="RUN-000001",
        attempt_id="ATT-000001",
        primary_review_artifact_reference=(
            ProcessingArtifactReference(
                artifact_type="review_reports",
                artifact_id="REPORT-001",
                content_fingerprint="b" * 64,
                repository_relative_path=(
                    f"data/projects/{project_id}/runs/"
                    "RUN-000001/artifacts/review_reports/"
                    "report.md"
                ),
            )
        ),
        supporting_artifact_references=(),
        framework_template=FrameworkTemplateReference(
            template_id="TURING_RFLP_FRAMEWORK",
            template_version="1.0.0",
        ),
        semantic_reference_versions=(),
        timestamp="2026-08-03T16:00:00Z",
    )

    version = create_review_document_version(
        project_id=project_id,
        review_document_id=document_id,
        review_document_version_id=version_id,
        version_number=1,
        predecessor_version_id=None,
        reopen_reason=None,
        opened_by="reviewer@example.com",
        timestamp="2026-08-03T16:00:00Z",
        head_revision_id=revision_id,
    )

    revision = create_review_revision(
        project_id=project_id,
        review_document_id=document_id,
        review_document_version_id=version_id,
        review_revision_id=revision_id,
        revision_sequence=1,
        predecessor_revision_id=None,
        review_items=(),
        scoped_review_action_ids=(),
        created_by="reviewer@example.com",
        timestamp="2026-08-03T16:00:00Z",
    )

    return document, version, revision


def _persist(
    repository: ReviewWorkspaceRepository,
):
    document, version, revision = _bundle()

    return repository.create_document_workspace(
        document,
        version,
        revision,
    )


def test_create_workspace_round_trips_all_records(
    repository,
) -> None:
    store, _ = repository
    document, version, revision = _bundle()

    persisted = store.create_document_workspace(
        document,
        version,
        revision,
    )

    assert persisted == (
        document,
        version,
        revision,
    )

    assert store.load_document(
        "000001",
        "RVD-000001",
    ) == document

    assert store.load_version(
        "000001",
        "RVD-000001",
        "RVV-000001",
    ) == version

    assert store.load_revision(
        "000001",
        "RVD-000001",
        "RVV-000001",
        "RVR-000001",
    ) == revision


def test_created_workspace_has_exact_initial_structure(
    repository,
) -> None:
    store, root = repository
    _persist(store)

    directory = review_document_path(
        root,
        "000001",
        "RVD-000001",
    )
    version_directory = review_document_version_path(
        root,
        "000001",
        "RVD-000001",
        "RVV-000001",
    )

    assert {
        item.name
        for item in directory.iterdir()
    } == {
        "review_document_manifest.json",
        "versions",
    }

    assert {
        item.name
        for item in version_directory.iterdir()
    } == {
        "review_version_manifest.json",
        "revisions",
        "scoped_actions",
    }

    assert not (
        version_directory / "current.json"
    ).exists()
    assert not (
        version_directory / "finalized"
    ).exists()


def test_create_workspace_rejects_duplicate_document(
    repository,
) -> None:
    store, _ = repository
    document, version, revision = _bundle()

    store.create_document_workspace(
        document,
        version,
        revision,
    )

    with pytest.raises(
        ReviewPersistenceError,
        match="already exists",
    ):
        store.create_document_workspace(
            document,
            version,
            revision,
        )


def test_interrupted_creation_requires_recovery(
    repository,
) -> None:
    store, root = repository
    document, version, revision = _bundle()

    temporary = (
        reviews_path(root, "000001")
        / ".create-RVD-000001.tmp"
    )
    temporary.parent.mkdir()
    temporary.mkdir()

    with pytest.raises(
        ReviewRecoveryRequiredError,
        match="recovery",
    ):
        store.create_document_workspace(
            document,
            version,
            revision,
        )


def test_create_workspace_requires_existing_project(
    tmp_path: Path,
) -> None:
    store = ReviewWorkspaceRepository(
        root=tmp_path / "projects"
    )
    document, version, revision = _bundle()

    with pytest.raises(
        ReviewReferenceError,
        match="unavailable",
    ):
        store.create_document_workspace(
            document,
            version,
            revision,
        )


@pytest.mark.parametrize(
    ("component", "replacement"),
    (
        (
            "version",
            {
                "project_id": "000002",
            },
        ),
        (
            "version",
            {
                "review_document_id": "RVD-000002",
            },
        ),
        (
            "revision",
            {
                "project_id": "000002",
            },
        ),
        (
            "revision",
            {
                "review_document_id": "RVD-000002",
            },
        ),
        (
            "revision",
            {
                "review_document_version_id": "RVV-000002",
            },
        ),
    ),
)
def test_create_workspace_rejects_cross_binding(
    repository,
    component: str,
    replacement: dict[str, str],
) -> None:
    store, _ = repository
    document, version, revision = _bundle()

    if component == "version":
        version = create_review_document_version(
            project_id=replacement.get(
                "project_id",
                version.project_id,
            ),
            review_document_id=replacement.get(
                "review_document_id",
                version.review_document_id,
            ),
            review_document_version_id=(
                version.review_document_version_id
            ),
            version_number=1,
            predecessor_version_id=None,
            reopen_reason=None,
            opened_by=version.opened_by,
            timestamp=version.opened_at,
            head_revision_id=version.head_revision_id,
        )
    else:
        revision = create_review_revision(
            project_id=replacement.get(
                "project_id",
                revision.project_id,
            ),
            review_document_id=replacement.get(
                "review_document_id",
                revision.review_document_id,
            ),
            review_document_version_id=replacement.get(
                "review_document_version_id",
                revision.review_document_version_id,
            ),
            review_revision_id=(
                revision.review_revision_id
            ),
            revision_sequence=1,
            predecessor_revision_id=None,
            review_items=(),
            scoped_review_action_ids=(),
            created_by=revision.created_by,
            timestamp=revision.created_at,
        )

    with pytest.raises(ReviewReferenceError):
        store.create_document_workspace(
            document,
            version,
            revision,
        )


def test_initial_version_must_be_draft(
    repository,
) -> None:
    store, _ = repository
    document, version, revision = _bundle()

    finalized = finalize_review_document_version(
        version,
        finalized_revision_id="RVR-000001",
        finalization_decision_id="HRD-000001",
        timestamp="2026-08-03T16:05:00Z",
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="draft",
    ):
        store.create_document_workspace(
            document,
            finalized,
            revision,
        )


def test_initial_version_must_reference_initial_revision(
    repository,
) -> None:
    store, _ = repository
    document, _, revision = _bundle()

    version = create_review_document_version(
        project_id="000001",
        review_document_id="RVD-000001",
        review_document_version_id="RVV-000001",
        version_number=1,
        predecessor_version_id=None,
        reopen_reason=None,
        opened_by="reviewer@example.com",
        timestamp="2026-08-03T16:00:00Z",
        head_revision_id="RVR-000002",
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="head_revision_id",
    ):
        store.create_document_workspace(
            document,
            version,
            revision,
        )


def test_initial_revision_must_not_reference_actions(
    repository,
) -> None:
    store, _ = repository
    document, version, revision = _bundle()

    revision = create_review_revision(
        project_id=revision.project_id,
        review_document_id=revision.review_document_id,
        review_document_version_id=(
            revision.review_document_version_id
        ),
        review_revision_id=revision.review_revision_id,
        revision_sequence=1,
        predecessor_revision_id=None,
        review_items=(),
        scoped_review_action_ids=("SRA-000001",),
        created_by=revision.created_by,
        timestamp=revision.created_at,
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="Scoped Review Actions",
    ):
        store.create_document_workspace(
            document,
            version,
            revision,
        )


def test_load_missing_document_uses_specific_error(
    repository,
) -> None:
    store, _ = repository

    with pytest.raises(
        ReviewDocumentNotFoundError,
    ):
        store.load_document(
            "000001",
            "RVD-000001",
        )


def test_load_missing_version_uses_specific_error(
    repository,
) -> None:
    store, _ = repository
    _persist(store)

    with pytest.raises(
        ReviewDocumentVersionNotFoundError,
    ):
        store.load_version(
            "000001",
            "RVD-000001",
            "RVV-000002",
        )


def test_load_missing_revision_uses_specific_error(
    repository,
) -> None:
    store, _ = repository
    _persist(store)

    with pytest.raises(
        ReviewRevisionNotFoundError,
    ):
        store.load_revision(
            "000001",
            "RVD-000001",
            "RVV-000001",
            "RVR-000002",
        )


def test_document_loader_rejects_unexpected_current_file(
    repository,
) -> None:
    store, root = repository
    _persist(store)

    document_directory = review_document_path(
        root,
        "000001",
        "RVD-000001",
    )
    (
        document_directory / "current.json"
    ).write_text(
        "{}\n",
        encoding="utf-8",
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="unknown",
    ):
        store.load_document(
            "000001",
            "RVD-000001",
        )


def test_version_loader_rejects_unexpected_entry(
    repository,
) -> None:
    store, root = repository
    _persist(store)

    version_directory = review_document_version_path(
        root,
        "000001",
        "RVD-000001",
        "RVV-000001",
    )
    (
        version_directory / "unexpected.json"
    ).write_text(
        "{}\n",
        encoding="utf-8",
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="unknown",
    ):
        store.load_version(
            "000001",
            "RVD-000001",
            "RVV-000001",
        )


def test_document_manifest_binding_is_enforced(
    repository,
) -> None:
    store, root = repository
    _persist(store)

    wrong_document, _, _ = _bundle(
        document_id="RVD-000002",
    )
    manifest_path = (
        review_document_path(
            root,
            "000001",
            "RVD-000001",
        )
        / "review_document_manifest.json"
    )
    manifest_path.write_text(
        review_document_to_json(wrong_document),
        encoding="utf-8",
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="ID",
    ):
        store.load_document(
            "000001",
            "RVD-000001",
        )


def test_version_manifest_binding_is_enforced(
    repository,
) -> None:
    store, root = repository
    _persist(store)

    wrong_version = create_review_document_version(
        project_id="000001",
        review_document_id="RVD-000002",
        review_document_version_id="RVV-000001",
        version_number=1,
        predecessor_version_id=None,
        reopen_reason=None,
        opened_by="reviewer@example.com",
        timestamp="2026-08-03T16:00:00Z",
        head_revision_id="RVR-000001",
    )
    manifest_path = (
        review_document_version_path(
            root,
            "000001",
            "RVD-000001",
            "RVV-000001",
        )
        / "review_version_manifest.json"
    )
    manifest_path.write_text(
        review_document_version_to_json(
            wrong_version
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="belong",
    ):
        store.load_version(
            "000001",
            "RVD-000001",
            "RVV-000001",
        )


def test_revision_binding_is_enforced(
    repository,
) -> None:
    store, root = repository
    _persist(store)

    wrong_revision = create_review_revision(
        project_id="000001",
        review_document_id="RVD-000001",
        review_document_version_id="RVV-000002",
        review_revision_id="RVR-000001",
        revision_sequence=1,
        predecessor_revision_id=None,
        review_items=(),
        scoped_review_action_ids=(),
        created_by="reviewer@example.com",
        timestamp="2026-08-03T16:00:00Z",
    )
    path = review_revision_path(
        root,
        "000001",
        "RVD-000001",
        "RVV-000001",
        "RVR-000001",
    )
    path.write_text(
        review_revision_to_json(wrong_revision),
        encoding="utf-8",
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="Version",
    ):
        store.load_revision(
            "000001",
            "RVD-000001",
            "RVV-000001",
            "RVR-000001",
        )


def test_symbolic_link_document_directory_is_rejected(
    repository,
) -> None:
    store, root = repository
    _persist(store)

    directory = review_document_path(
        root,
        "000001",
        "RVD-000001",
    )
    real_directory = directory.with_name(
        "real-review-document"
    )
    directory.rename(real_directory)

    try:
        directory.symlink_to(
            real_directory,
            target_is_directory=True,
        )
    except OSError:
        pytest.skip(
            "Symbolic links are not supported."
        )

    with pytest.raises(
        UnsafeReviewWorkspacePathError,
    ):
        store.load_document(
            "000001",
            "RVD-000001",
        )


def test_symbolic_link_revision_file_is_rejected(
    repository,
) -> None:
    store, root = repository
    _persist(store)

    path = review_revision_path(
        root,
        "000001",
        "RVD-000001",
        "RVV-000001",
        "RVR-000001",
    )
    real_path = path.with_name(
        "real-revision.json"
    )
    path.rename(real_path)

    try:
        path.symlink_to(real_path)
    except OSError:
        pytest.skip(
            "Symbolic links are not supported."
        )

    with pytest.raises(
        UnsafeReviewWorkspacePathError,
    ):
        store.load_revision(
            "000001",
            "RVD-000001",
            "RVV-000001",
            "RVR-000001",
        )
