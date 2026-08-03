"""Tests for deterministic Review Workspace scanning."""

from __future__ import annotations

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
)
from modules.review_workspace.paths import (
    review_document_path,
    review_document_version_path,
    review_revision_path,
    review_revisions_path,
    review_versions_path,
    reviews_path,
    scoped_review_action_path,
    scoped_review_actions_path,
)
from modules.review_workspace.repository import (
    ReviewWorkspaceRepository,
)
from modules.review_workspace.revision_manifest import (
    create_review_revision,
)
from modules.review_workspace.scoped_action_manifest import (
    create_scoped_review_action,
)
from modules.review_workspace.version_manifest import (
    create_review_document_version,
    review_document_version_to_json,
)


def _clock() -> datetime:
    return datetime(
        2026,
        8,
        3,
        17,
        0,
        tzinfo=timezone.utc,
    )


def _create_project(
    root: Path,
    *,
    project_id: str = "000001",
    display_name: str = "Review Scan Test",
) -> None:
    workspace = ProjectWorkspace(
        root=root,
        id_generator=lambda: project_id,
        clock=_clock,
    )
    workspace.create_project(display_name)


def _bundle(
    *,
    project_id: str = "000001",
    document_id: str = "RVD-000001",
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
        timestamp="2026-08-03T17:00:00Z",
    )

    version = create_review_document_version(
        project_id=project_id,
        review_document_id=document_id,
        review_document_version_id="RVV-000001",
        version_number=1,
        predecessor_version_id=None,
        reopen_reason=None,
        opened_by="reviewer@example.com",
        timestamp="2026-08-03T17:00:00Z",
        head_revision_id="RVR-000001",
    )

    revision = create_review_revision(
        project_id=project_id,
        review_document_id=document_id,
        review_document_version_id="RVV-000001",
        review_revision_id="RVR-000001",
        revision_sequence=1,
        predecessor_revision_id=None,
        review_items=(),
        scoped_review_action_ids=(),
        created_by="reviewer@example.com",
        timestamp="2026-08-03T17:00:00Z",
    )

    return document, version, revision


@pytest.fixture
def repository(
    tmp_path: Path,
) -> tuple[ReviewWorkspaceRepository, Path]:
    root = tmp_path / "projects"
    _create_project(root)

    store = ReviewWorkspaceRepository(root=root)
    document, version, revision = _bundle()

    store.create_document_workspace(
        document,
        version,
        revision,
    )

    return store, root


def _action():
    return create_scoped_review_action(
        project_id="000001",
        review_document_id="RVD-000001",
        review_document_version_id="RVV-000001",
        scoped_review_action_id="SRA-000001",
        action_scope="document_default",
        decision_dimension="framework_assignment",
        selected_values=(
            "02_System/01_Requirements",
        ),
        filter_definition=None,
        materialized_items=(),
        created_by="reviewer@example.com",
        timestamp="2026-08-03T17:05:00Z",
        rationale=None,
    )


def _second_revision(
    *,
    action_ids: tuple[str, ...] = (),
):
    return create_review_revision(
        project_id="000001",
        review_document_id="RVD-000001",
        review_document_version_id="RVV-000001",
        review_revision_id="RVR-000002",
        revision_sequence=2,
        predecessor_revision_id="RVR-000001",
        review_items=(),
        scoped_review_action_ids=action_ids,
        created_by="reviewer@example.com",
        timestamp="2026-08-03T17:10:00Z",
    )


def _codes(store: ReviewWorkspaceRepository) -> set[str]:
    return {
        issue.code
        for issue in store.scan_project(
            "000001"
        ).issues
    }


def test_scan_returns_complete_valid_workspace(
    repository,
) -> None:
    store, _ = repository

    result = store.scan_project("000001")

    assert [
        item.review_document_id
        for item in result.documents
    ] == ["RVD-000001"]
    assert [
        item.review_document_version_id
        for item in result.versions
    ] == ["RVV-000001"]
    assert [
        item.review_revision_id
        for item in result.revisions
    ] == ["RVR-000001"]
    assert result.scoped_actions == ()
    assert result.issues == ()


def test_scan_returns_valid_action_and_revision_chain(
    repository,
) -> None:
    store, _ = repository

    store.persist_scoped_action(_action())
    store.append_revision(
        _second_revision(
            action_ids=("SRA-000001",),
        )
    )

    result = store.scan_project("000001")

    assert [
        item.review_revision_id
        for item in result.revisions
    ] == [
        "RVR-000001",
        "RVR-000002",
    ]
    assert [
        item.scoped_review_action_id
        for item in result.scoped_actions
    ] == ["SRA-000001"]
    assert result.issues == ()


def test_interrupted_document_creation_is_reported(
    repository,
) -> None:
    store, root = repository

    (
        reviews_path(root, "000001")
        / ".create-RVD-000002.tmp"
    ).mkdir()

    assert (
        "interrupted_review_document_creation"
        in _codes(store)
    )


def test_unexpected_review_root_entry_is_reported(
    repository,
) -> None:
    store, root = repository

    (
        reviews_path(root, "000001")
        / "unexpected.txt"
    ).write_text(
        "unexpected\n",
        encoding="utf-8",
    )

    assert "unexpected_review_entry" in _codes(store)


def test_invalid_document_directory_is_reported(
    repository,
) -> None:
    store, root = repository

    (
        reviews_path(root, "000001")
        / "invalid-document"
    ).mkdir()

    assert (
        "invalid_review_document_directory"
        in _codes(store)
    )


def test_interrupted_version_creation_is_reported(
    repository,
) -> None:
    store, root = repository

    (
        review_versions_path(
            root,
            "000001",
            "RVD-000001",
        )
        / ".create-RVV-000002.tmp"
    ).mkdir()

    assert (
        "interrupted_review_version_creation"
        in _codes(store)
    )


def test_interrupted_version_update_is_reported(
    repository,
) -> None:
    store, root = repository

    directory = review_document_version_path(
        root,
        "000001",
        "RVD-000001",
        "RVV-000001",
    )
    (
        directory
        / ".review_version_manifest.json.tmp"
    ).write_text(
        "{}\n",
        encoding="utf-8",
    )

    assert (
        "interrupted_review_version_update"
        in _codes(store)
    )


def test_interrupted_revision_append_is_reported(
    repository,
) -> None:
    store, root = repository

    (
        review_revisions_path(
            root,
            "000001",
            "RVD-000001",
            "RVV-000001",
        )
        / ".RVR-000002.json.tmp"
    ).write_text(
        "{}\n",
        encoding="utf-8",
    )

    assert (
        "interrupted_review_revision_append"
        in _codes(store)
    )


def test_invalid_revision_and_missing_head_are_reported(
    repository,
) -> None:
    store, root = repository

    path = review_revision_path(
        root,
        "000001",
        "RVD-000001",
        "RVV-000001",
        "RVR-000001",
    )
    path.write_text(
        "{invalid",
        encoding="utf-8",
    )

    codes = _codes(store)

    assert "review_validation_error" in codes
    assert "missing_head_revision" in codes


def test_interrupted_scoped_action_is_reported(
    repository,
) -> None:
    store, root = repository

    (
        scoped_review_actions_path(
            root,
            "000001",
            "RVD-000001",
            "RVV-000001",
        )
        / ".SRA-000001.json.tmp"
    ).write_text(
        "{}\n",
        encoding="utf-8",
    )

    assert (
        "interrupted_scoped_action_persistence"
        in _codes(store)
    )


def test_unreferenced_scoped_action_is_reported(
    repository,
) -> None:
    store, _ = repository

    store.persist_scoped_action(_action())

    result = store.scan_project("000001")

    assert [
        item.scoped_review_action_id
        for item in result.scoped_actions
    ] == ["SRA-000001"]
    assert (
        "unreferenced_scoped_action"
        in {
            issue.code
            for issue in result.issues
        }
    )


def test_missing_scoped_action_reference_is_reported(
    repository,
) -> None:
    store, root = repository

    store.persist_scoped_action(_action())
    store.append_revision(
        _second_revision(
            action_ids=("SRA-000001",),
        )
    )

    scoped_review_action_path(
        root,
        "000001",
        "RVD-000001",
        "RVV-000001",
        "SRA-000001",
    ).unlink()

    assert (
        "missing_scoped_action_reference"
        in _codes(store)
    )


def test_missing_head_revision_is_reported(
    repository,
) -> None:
    store, root = repository

    review_revision_path(
        root,
        "000001",
        "RVD-000001",
        "RVV-000001",
        "RVR-000001",
    ).unlink()

    assert "missing_head_revision" in _codes(store)


def test_stale_version_head_is_reported(
    repository,
) -> None:
    store, root = repository

    initial_version = store.load_version(
        "000001",
        "RVD-000001",
        "RVV-000001",
    )
    store.append_revision(_second_revision())

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
            initial_version
        ),
        encoding="utf-8",
    )

    assert "stale_version_head" in _codes(store)


def test_unexpected_document_entry_blocks_document(
    repository,
) -> None:
    store, root = repository

    (
        review_document_path(
            root,
            "000001",
            "RVD-000001",
        )
        / "current.json"
    ).write_text(
        "{}\n",
        encoding="utf-8",
    )

    result = store.scan_project("000001")

    assert result.documents == ()
    assert "review_integrity_error" in {
        issue.code
        for issue in result.issues
    }


def test_invalid_version_binding_is_reported(
    repository,
) -> None:
    store, root = repository

    wrong_version = create_review_document_version(
        project_id="000001",
        review_document_id="RVD-000002",
        review_document_version_id="RVV-000001",
        version_number=1,
        predecessor_version_id=None,
        reopen_reason=None,
        opened_by="reviewer@example.com",
        timestamp="2026-08-03T17:00:00Z",
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

    result = store.scan_project("000001")

    assert result.documents
    assert result.versions == ()
    assert "review_integrity_error" in {
        issue.code
        for issue in result.issues
    }


def test_scan_issues_are_deterministically_sorted(
    repository,
) -> None:
    store, root = repository
    review_root = reviews_path(
        root,
        "000001",
    )

    (
        review_root / "z-unexpected"
    ).write_text(
        "z\n",
        encoding="utf-8",
    )
    (
        review_root / "a-unexpected"
    ).write_text(
        "a\n",
        encoding="utf-8",
    )

    result = store.scan_project("000001")

    expected = tuple(
        sorted(
            result.issues,
            key=lambda issue: (
                str(issue.path or ""),
                issue.code,
                issue.review_document_id or "",
                issue.review_document_version_id or "",
                issue.review_revision_id or "",
                issue.review_item_id or "",
                issue.scoped_review_action_id or "",
                issue.message,
            ),
        )
    )

    assert result.issues == expected


def test_scan_is_project_isolated(
    repository,
) -> None:
    store, root = repository

    _create_project(
        root,
        project_id="000002",
        display_name="Second Scan Project",
    )
    document, version, revision = _bundle(
        project_id="000002",
    )
    store.create_document_workspace(
        document,
        version,
        revision,
    )

    first = store.scan_project("000001")
    second = store.scan_project("000002")

    assert {
        item.project_id
        for item in first.documents
    } == {"000001"}
    assert {
        item.project_id
        for item in second.documents
    } == {"000002"}


def test_symbolic_link_revision_is_reported(
    repository,
) -> None:
    store, root = repository

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

    codes = _codes(store)

    assert "unsafe_review_revision_path" in codes
    assert "missing_head_revision" in codes
