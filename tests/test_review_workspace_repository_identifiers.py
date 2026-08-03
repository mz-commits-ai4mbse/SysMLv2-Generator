"""Tests for project-local Review Workspace ID allocation."""

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
from modules.review_workspace.errors import (
    ReviewDocumentNotFoundError,
    ReviewDocumentVersionNotFoundError,
)
from modules.review_workspace.paths import (
    review_revisions_path,
    review_versions_path,
    reviews_path,
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


def _create_project(
    root: Path,
    project_id: str,
    display_name: str,
) -> None:
    workspace = ProjectWorkspace(
        root=root,
        id_generator=lambda: project_id,
        clock=_clock,
    )
    workspace.create_project(display_name)


@pytest.fixture
def repository(
    tmp_path: Path,
) -> tuple[ReviewWorkspaceRepository, Path]:
    root = tmp_path / "projects"

    _create_project(
        root,
        "000001",
        "Identifier Test Project",
    )

    return ReviewWorkspaceRepository(root=root), root


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


def _persist_workspace(
    store: ReviewWorkspaceRepository,
    *,
    project_id: str = "000001",
) -> None:
    document, version, revision = _bundle(
        project_id=project_id,
    )

    store.create_document_workspace(
        document,
        version,
        revision,
    )


def _document_default_action():
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
        timestamp="2026-08-03T16:05:00Z",
        rationale=None,
    )


def test_next_document_id_starts_at_one(
    repository,
) -> None:
    store, _ = repository

    assert store.next_document_id(
        "000001"
    ) == "RVD-000001"


def test_next_document_id_advances_after_creation(
    repository,
) -> None:
    store, _ = repository
    _persist_workspace(store)

    assert store.next_document_id(
        "000001"
    ) == "RVD-000002"


def test_document_id_uses_highest_occupied_value(
    repository,
) -> None:
    store, root = repository
    review_root = reviews_path(
        root,
        "000001",
    )
    review_root.mkdir()

    (
        review_root / "RVD-000004"
    ).write_text(
        "occupied\n",
        encoding="utf-8",
    )
    (
        review_root / ".create-RVD-000006.tmp"
    ).mkdir()

    assert store.next_document_id(
        "000001"
    ) == "RVD-000007"


def test_document_ids_are_project_isolated(
    repository,
) -> None:
    store, root = repository
    _persist_workspace(store)

    _create_project(
        root,
        "000002",
        "Second Identifier Project",
    )

    assert store.next_document_id(
        "000001"
    ) == "RVD-000002"

    assert store.next_document_id(
        "000002"
    ) == "RVD-000001"


def test_next_version_id_advances_after_initial_version(
    repository,
) -> None:
    store, _ = repository
    _persist_workspace(store)

    assert store.next_version_id(
        "000001",
        "RVD-000001",
    ) == "RVV-000002"


def test_temporary_version_id_is_reserved(
    repository,
) -> None:
    store, root = repository
    _persist_workspace(store)

    root_path = review_versions_path(
        root,
        "000001",
        "RVD-000001",
    )
    (
        root_path / ".create-RVV-000004.tmp"
    ).mkdir()

    assert store.next_version_id(
        "000001",
        "RVD-000001",
    ) == "RVV-000005"


def test_next_revision_id_advances_after_initial_revision(
    repository,
) -> None:
    store, _ = repository
    _persist_workspace(store)

    assert store.next_revision_id(
        "000001",
        "RVD-000001",
        "RVV-000001",
    ) == "RVR-000002"


def test_revision_allocator_reserves_files_and_temporaries(
    repository,
) -> None:
    store, root = repository
    _persist_workspace(store)

    root_path = review_revisions_path(
        root,
        "000001",
        "RVD-000001",
        "RVV-000001",
    )

    (
        root_path / "RVR-000004.json"
    ).write_text(
        "{}\n",
        encoding="utf-8",
    )
    (
        root_path / ".RVR-000006.json.tmp"
    ).write_text(
        "{}\n",
        encoding="utf-8",
    )

    assert store.next_revision_id(
        "000001",
        "RVD-000001",
        "RVV-000001",
    ) == "RVR-000007"


def test_next_scoped_action_id_starts_at_one(
    repository,
) -> None:
    store, _ = repository
    _persist_workspace(store)

    assert store.next_scoped_action_id(
        "000001",
        "RVD-000001",
        "RVV-000001",
    ) == "SRA-000001"


def test_next_scoped_action_id_advances_after_persistence(
    repository,
) -> None:
    store, _ = repository
    _persist_workspace(store)

    store.persist_scoped_action(
        _document_default_action()
    )

    assert store.next_scoped_action_id(
        "000001",
        "RVD-000001",
        "RVV-000001",
    ) == "SRA-000002"


def test_temporary_scoped_action_id_is_reserved(
    repository,
) -> None:
    store, root = repository
    _persist_workspace(store)

    root_path = scoped_review_actions_path(
        root,
        "000001",
        "RVD-000001",
        "RVV-000001",
    )
    (
        root_path / ".SRA-000005.json.tmp"
    ).write_text(
        "{}\n",
        encoding="utf-8",
    )

    assert store.next_scoped_action_id(
        "000001",
        "RVD-000001",
        "RVV-000001",
    ) == "SRA-000006"


def test_invalid_names_do_not_occupy_identifiers(
    repository,
) -> None:
    store, root = repository
    review_root = reviews_path(
        root,
        "000001",
    )
    review_root.mkdir()

    (
        review_root / "RVD-invalid"
    ).mkdir()
    (
        review_root / ".create-invalid.tmp"
    ).mkdir()

    assert store.next_document_id(
        "000001"
    ) == "RVD-000001"


def test_next_version_id_requires_existing_document(
    repository,
) -> None:
    store, _ = repository

    with pytest.raises(
        ReviewDocumentNotFoundError,
    ):
        store.next_version_id(
            "000001",
            "RVD-000001",
        )


def test_revision_allocator_requires_existing_version(
    repository,
) -> None:
    store, _ = repository
    _persist_workspace(store)

    with pytest.raises(
        ReviewDocumentVersionNotFoundError,
    ):
        store.next_revision_id(
            "000001",
            "RVD-000001",
            "RVV-000002",
        )
