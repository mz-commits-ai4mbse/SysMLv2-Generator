"""Tests for P9 project-bound Source upload and registration."""

from __future__ import annotations

from pathlib import Path

import pytest

from modules.project_ingestion import (
    ProjectBoundIngestionService,
    ProjectIngestionInputError,
)
from modules.project_sources import (
    DuplicateSourceContentError,
    ProjectSourceRegistry,
)
from modules.project_workspace import ProjectWorkspace


PROJECT_ID = "123456"


@pytest.fixture
def projects_root(tmp_path: Path) -> Path:
    root = tmp_path / "projects"
    workspace = ProjectWorkspace(
        root=root,
        id_generator=lambda: PROJECT_ID,
    )
    workspace.create_project("P9 Source Registration")
    return root


@pytest.fixture
def service(
    projects_root: Path,
) -> ProjectBoundIngestionService:
    return ProjectBoundIngestionService(root=projects_root)


def test_register_uploaded_source_returns_safe_summary(
    service: ProjectBoundIngestionService,
) -> None:
    result = service.register_uploaded_source(
        PROJECT_ID,
        original_filename="requirements.md",
        content=b"# Requirements\n",
        source_role="engineering_source",
    )

    assert result.project_id == PROJECT_ID
    assert result.source_id == "SRC-000001"
    assert result.source_role == "engineering_source"
    assert result.original_filename == "requirements.md"
    assert result.media_type == "text/markdown"
    assert result.size_bytes == 15
    assert len(result.sha256) == 64


def test_register_uploaded_source_preserves_exact_bytes(
    service: ProjectBoundIngestionService,
    projects_root: Path,
) -> None:
    original = "Requirement ÄÖÜ\nLine 2\n".encode("utf-8")

    result = service.register_uploaded_source(
        PROJECT_ID,
        original_filename="source.txt",
        content=original,
        source_role="context_only",
    )

    registry = ProjectSourceRegistry(root=projects_root)
    stored_path = registry.source_content_path(
        PROJECT_ID,
        result.source_id,
    )

    assert stored_path.read_bytes() == original


def test_register_uploaded_pdf_preserves_original_and_media_type(
    service: ProjectBoundIngestionService,
    projects_root: Path,
) -> None:
    original = (
        b"%PDF-1.4\n"
        b"% project-bound text-layer PDF placeholder\n"
        b"%%EOF\n"
    )

    result = service.register_uploaded_source(
        PROJECT_ID,
        original_filename="requirements.pdf",
        content=original,
        source_role="engineering_source",
    )

    assert result.source_id == "SRC-000001"
    assert result.original_filename == "requirements.pdf"
    assert result.media_type == "application/pdf"

    registry = ProjectSourceRegistry(root=projects_root)
    stored_path = registry.source_content_path(
        PROJECT_ID,
        result.source_id,
    )
    assert stored_path.read_bytes() == original


def test_register_uploaded_source_rejects_empty_content(
    service: ProjectBoundIngestionService,
) -> None:
    with pytest.raises(
        ProjectIngestionInputError,
        match="must not be empty",
    ):
        service.register_uploaded_source(
            PROJECT_ID,
            original_filename="empty.txt",
            content=b"",
            source_role="engineering_source",
        )


@pytest.mark.parametrize("content", [None, "text", 42])
def test_register_uploaded_source_rejects_nonbytes_content(
    service: ProjectBoundIngestionService,
    content,
) -> None:
    with pytest.raises(
        ProjectIngestionInputError,
        match="must be bytes",
    ):
        service.register_uploaded_source(
            PROJECT_ID,
            original_filename="source.txt",
            content=content,
            source_role="engineering_source",
        )


@pytest.mark.parametrize(
    "filename",
    [
        "../source.txt",
        "folder/source.txt",
        "folder\\source.txt",
        ".",
        "..",
        "source\x00.txt",
        "source\n.txt",
    ],
)
def test_register_uploaded_source_rejects_unsafe_filename(
    service: ProjectBoundIngestionService,
    filename: str,
) -> None:
    with pytest.raises(ProjectIngestionInputError):
        service.register_uploaded_source(
            PROJECT_ID,
            original_filename=filename,
            content=b"content",
            source_role="engineering_source",
        )


def test_duplicate_content_remains_owned_by_p3(
    service: ProjectBoundIngestionService,
) -> None:
    service.register_uploaded_source(
        PROJECT_ID,
        original_filename="first.txt",
        content=b"same content",
        source_role="engineering_source",
    )

    with pytest.raises(DuplicateSourceContentError):
        service.register_uploaded_source(
            PROJECT_ID,
            original_filename="second.txt",
            content=b"same content",
            source_role="context_only",
        )


def test_list_registered_sources_returns_sorted_safe_inventory(
    service: ProjectBoundIngestionService,
) -> None:
    first = service.register_uploaded_source(
        PROJECT_ID,
        original_filename="first.txt",
        content=b"first content",
        source_role="engineering_source",
    )
    second = service.register_uploaded_source(
        PROJECT_ID,
        original_filename="second.json",
        content=b'{"value": 2}',
        source_role="context_only",
    )

    inventory = service.list_registered_sources(PROJECT_ID)

    assert inventory.project_id == PROJECT_ID
    assert tuple(
        source.source_id
        for source in inventory.sources
    ) == (
        first.source_id,
        second.source_id,
    )
    assert inventory.issues == ()
    assert not hasattr(inventory.sources[0], "path")


def test_list_registered_sources_removes_issue_paths(
    service: ProjectBoundIngestionService,
    projects_root: Path,
) -> None:
    unexpected = (
        projects_root
        / PROJECT_ID
        / "sources"
        / "unexpected.txt"
    )
    unexpected.parent.mkdir()
    unexpected.write_text("unexpected", encoding="utf-8")

    inventory = service.list_registered_sources(PROJECT_ID)

    assert inventory.sources == ()
    assert len(inventory.issues) == 1
    assert inventory.issues[0].code == "unexpected_source_entry"
    assert not hasattr(inventory.issues[0], "path")
