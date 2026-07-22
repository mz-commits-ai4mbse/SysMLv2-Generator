"""Tests for persistent project source registration."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from modules.project_sources import (
    CONTEXT_ONLY_SOURCE_ROLE,
    ENGINEERING_SOURCE_ROLE,
    DuplicateSourceContentError,
    ProjectSourceRegistry,
    SourceIntegrityError,
    SourceManifestError,
    SourceNotFoundError,
    UnsupportedSourceRoleError,
    UnsafeSourcePathError,
)
from modules.project_workspace import ProjectWorkspace


PROJECT_ID = "318604"
SECOND_PROJECT_ID = "481516"


class MutableClock:
    """Controllable UTC clock used by persistence tests."""

    def __init__(
        self,
        value: datetime = datetime(
            2026,
            7,
            22,
            12,
            0,
            0,
            tzinfo=timezone.utc,
        ),
    ) -> None:
        self.value = value

    def __call__(self) -> datetime:
        return self.value

    def set(
        self,
        year: int,
        month: int,
        day: int,
        hour: int,
        minute: int = 0,
        second: int = 0,
    ) -> None:
        self.value = datetime(
            year,
            month,
            day,
            hour,
            minute,
            second,
            tzinfo=timezone.utc,
        )


@pytest.fixture
def clock() -> MutableClock:
    return MutableClock()


@pytest.fixture
def projects_root(
    tmp_path: Path,
    clock: MutableClock,
) -> Path:
    root = tmp_path / "projects"

    workspace = ProjectWorkspace(
        root=root,
        id_generator=lambda: PROJECT_ID,
        clock=clock,
    )
    workspace.create_project("Project Source Registry Test")

    return root


@pytest.fixture
def registry(
    projects_root: Path,
    clock: MutableClock,
) -> ProjectSourceRegistry:
    return ProjectSourceRegistry(
        root=projects_root,
        clock=clock,
    )


@pytest.fixture
def input_root(tmp_path: Path) -> Path:
    root = tmp_path / "inputs"
    root.mkdir()
    return root


def write_text_source(
    input_root: Path,
    filename: str = "requirements.txt",
    content: str = "The system shall preserve source traceability.",
) -> Path:
    path = input_root / filename
    path.write_text(content, encoding="utf-8")
    return path


def write_binary_source(
    input_root: Path,
    filename: str = "source.bin",
    content: bytes = b"\x00\x01\x02\xff",
) -> Path:
    path = input_root / filename
    path.write_bytes(content)
    return path


def source_directory(
    projects_root: Path,
    source_id: str,
    project_id: str = PROJECT_ID,
) -> Path:
    return (
        projects_root
        / project_id
        / "sources"
        / source_id
    )


def register_text_source(
    registry: ProjectSourceRegistry,
    input_root: Path,
    *,
    filename: str = "requirements.txt",
    content: str = "The system shall preserve source traceability.",
    source_role: str = ENGINEERING_SOURCE_ROLE,
):
    input_path = write_text_source(
        input_root,
        filename=filename,
        content=content,
    )

    return registry.register_source(
        PROJECT_ID,
        input_path,
        source_role=source_role,
    )


def test_register_source_returns_manifest(
    registry: ProjectSourceRegistry,
    input_root: Path,
) -> None:
    registered = register_text_source(
        registry,
        input_root,
    )

    assert registered.schema_version == "1.0.0"
    assert registered.project_id == PROJECT_ID
    assert registered.source_id == "SRC-000001"
    assert registered.source_role == ENGINEERING_SOURCE_ROLE
    assert registered.original_filename == "requirements.txt"
    assert registered.stored_filename == "content.txt"
    assert registered.media_type == "text/plain"
    assert registered.size_bytes == 46
    assert len(registered.sha256) == 64
    assert registered.registered_at == "2026-07-22T12:00:00Z"
    assert registered.updated_at == "2026-07-22T12:00:00Z"


def test_register_source_persists_manifest(
    registry: ProjectSourceRegistry,
    projects_root: Path,
    input_root: Path,
) -> None:
    registered = register_text_source(
        registry,
        input_root,
    )

    manifest_path = (
        source_directory(
            projects_root,
            registered.source_id,
        )
        / "source_manifest.json"
    )

    assert manifest_path.is_file()

    payload = json.loads(
        manifest_path.read_text(encoding="utf-8")
    )

    assert payload == {
        "schema_version": "1.0.0",
        "project_id": PROJECT_ID,
        "source_id": "SRC-000001",
        "source_role": "engineering_source",
        "original_filename": "requirements.txt",
        "stored_filename": "content.txt",
        "media_type": "text/plain",
        "size_bytes": 46,
        "sha256": registered.sha256,
        "registered_at": "2026-07-22T12:00:00Z",
        "updated_at": "2026-07-22T12:00:00Z",
    }


def test_register_source_preserves_original_text_bytes(
    registry: ProjectSourceRegistry,
    projects_root: Path,
    input_root: Path,
) -> None:
    content = (
        "Requirement ÄÖÜ\n"
        "The system shall preserve line order.\n"
    )
    input_path = write_text_source(
        input_root,
        filename="System Requirements.TXT",
        content=content,
    )
    original_bytes = input_path.read_bytes()

    registered = registry.register_source(
        PROJECT_ID,
        input_path,
        source_role=ENGINEERING_SOURCE_ROLE,
    )

    stored_path = (
        source_directory(
            projects_root,
            registered.source_id,
        )
        / registered.stored_filename
    )

    assert stored_path.read_bytes() == original_bytes


def test_register_source_preserves_original_binary_bytes(
    registry: ProjectSourceRegistry,
    projects_root: Path,
    input_root: Path,
) -> None:
    original_bytes = b"\x00\x01\x02\x03\x80\xff"
    input_path = write_binary_source(
        input_root,
        filename="archive.custom",
        content=original_bytes,
    )

    registered = registry.register_source(
        PROJECT_ID,
        input_path,
        source_role=CONTEXT_ONLY_SOURCE_ROLE,
    )

    stored_path = (
        source_directory(
            projects_root,
            registered.source_id,
        )
        / "content.bin"
    )

    assert registered.stored_filename == "content.bin"
    assert registered.media_type == "application/octet-stream"
    assert stored_path.read_bytes() == original_bytes


@pytest.mark.parametrize(
    (
        "filename",
        "expected_stored_filename",
        "expected_media_type",
    ),
    [
        ("requirements.txt", "content.txt", "text/plain"),
        ("requirements.MD", "content.md", "text/markdown"),
        ("requirements.json", "content.json", "application/json"),
        ("requirements.xml", "content.xml", "application/xml"),
        ("requirements.csv", "content.csv", "text/csv"),
        ("requirements.pdf", "content.pdf", "application/pdf"),
        (
            "requirements.docx",
            "content.docx",
            (
                "application/vnd.openxmlformats-officedocument."
                "wordprocessingml.document"
            ),
        ),
        (
            "requirements.unknown",
            "content.bin",
            "application/octet-stream",
        ),
    ],
)
def test_register_source_uses_deterministic_storage_metadata(
    registry: ProjectSourceRegistry,
    input_root: Path,
    filename: str,
    expected_stored_filename: str,
    expected_media_type: str,
) -> None:
    input_path = write_binary_source(
        input_root,
        filename=filename,
        content=b"source content",
    )

    registered = registry.register_source(
        PROJECT_ID,
        input_path,
        source_role=ENGINEERING_SOURCE_ROLE,
    )

    assert registered.stored_filename == expected_stored_filename
    assert registered.media_type == expected_media_type


def test_register_source_rejects_empty_content(
    registry: ProjectSourceRegistry,
    projects_root: Path,
    input_root: Path,
) -> None:
    input_path = write_text_source(
        input_root,
        filename="empty.txt",
        content="",
    )

    with pytest.raises(
        SourceIntegrityError,
        match="Source file must not be empty",
    ):
        registry.register_source(
            PROJECT_ID,
            input_path,
            source_role=CONTEXT_ONLY_SOURCE_ROLE,
        )

    sources_root = (
        projects_root
        / PROJECT_ID
        / "sources"
    )

    assert not sources_root.exists() or not any(
        path.name.startswith("SRC-")
        for path in sources_root.iterdir()
    )


def test_register_source_requires_explicit_valid_role(
    registry: ProjectSourceRegistry,
    input_root: Path,
) -> None:
    input_path = write_text_source(input_root)

    with pytest.raises(UnsupportedSourceRoleError):
        registry.register_source(
            PROJECT_ID,
            input_path,
            source_role="reference",
        )


@pytest.mark.parametrize(
    "source_role",
    [
        "",
        "ENGINEERING_SOURCE",
        "engineering-source",
        "context",
        None,
        42,
    ],
)
def test_register_source_rejects_invalid_roles(
    registry: ProjectSourceRegistry,
    input_root: Path,
    source_role: object,
) -> None:
    input_path = write_text_source(input_root)

    with pytest.raises(UnsupportedSourceRoleError):
        registry.register_source(
            PROJECT_ID,
            input_path,
            source_role=source_role,  # type: ignore[arg-type]
        )


def test_register_source_allocates_sequential_source_ids(
    registry: ProjectSourceRegistry,
    input_root: Path,
) -> None:
    first = register_text_source(
        registry,
        input_root,
        filename="first.txt",
        content="First source",
    )
    second = register_text_source(
        registry,
        input_root,
        filename="second.txt",
        content="Second source",
    )
    third = register_text_source(
        registry,
        input_root,
        filename="third.txt",
        content="Third source",
    )

    assert first.source_id == "SRC-000001"
    assert second.source_id == "SRC-000002"
    assert third.source_id == "SRC-000003"


def test_source_id_allocation_considers_registration_directories(
    registry: ProjectSourceRegistry,
    projects_root: Path,
    input_root: Path,
) -> None:
    temporary_registration_directory = (
        projects_root
        / PROJECT_ID
        / "sources"
        / ".register-SRC-000001.tmp"
    )
    temporary_registration_directory.mkdir(
        parents=True,
    )

    registered = register_text_source(
        registry,
        input_root,
    )

    assert registered.source_id == "SRC-000002"


def test_load_source_returns_persisted_manifest(
    registry: ProjectSourceRegistry,
    input_root: Path,
) -> None:
    registered = register_text_source(
        registry,
        input_root,
    )

    loaded = registry.load_source(
        PROJECT_ID,
        registered.source_id,
    )

    assert loaded == registered


def test_load_source_rejects_unknown_source(
    registry: ProjectSourceRegistry,
) -> None:
    with pytest.raises(SourceNotFoundError):
        registry.load_source(
            PROJECT_ID,
            "SRC-000001",
        )


@pytest.mark.parametrize(
    "source_id",
    [
        "",
        "SRC-1",
        "SRC-000000",
        "SRC-1000000",
        "src-000001",
        "../SRC-000001",
    ],
)
def test_load_source_rejects_invalid_source_id(
    registry: ProjectSourceRegistry,
    source_id: str,
) -> None:
    with pytest.raises(UnsafeSourcePathError):
        registry.load_source(
            PROJECT_ID,
            source_id,
        )


def test_source_content_path_returns_registered_content(
    registry: ProjectSourceRegistry,
    input_root: Path,
) -> None:
    registered = register_text_source(
        registry,
        input_root,
        content="Persisted engineering source.",
    )

    content_path = registry.source_content_path(
        PROJECT_ID,
        registered.source_id,
    )

    assert content_path.name == registered.stored_filename
    assert content_path.read_text(encoding="utf-8") == (
        "Persisted engineering source."
    )


def test_source_content_path_rejects_unknown_source(
    registry: ProjectSourceRegistry,
) -> None:
    with pytest.raises(SourceNotFoundError):
        registry.source_content_path(
            PROJECT_ID,
            "SRC-000001",
        )


def test_update_source_role_persists_change(
    registry: ProjectSourceRegistry,
    input_root: Path,
    clock: MutableClock,
) -> None:
    registered = register_text_source(
        registry,
        input_root,
        source_role=ENGINEERING_SOURCE_ROLE,
    )

    clock.set(2026, 7, 22, 13, 30)

    updated = registry.update_source_role(
        PROJECT_ID,
        registered.source_id,
        source_role=CONTEXT_ONLY_SOURCE_ROLE,
    )

    assert updated.project_id == registered.project_id
    assert updated.source_id == registered.source_id
    assert updated.source_role == CONTEXT_ONLY_SOURCE_ROLE
    assert updated.original_filename == registered.original_filename
    assert updated.stored_filename == registered.stored_filename
    assert updated.media_type == registered.media_type
    assert updated.size_bytes == registered.size_bytes
    assert updated.sha256 == registered.sha256
    assert updated.registered_at == registered.registered_at
    assert updated.updated_at == "2026-07-22T13:30:00Z"

    assert registry.load_source(
        PROJECT_ID,
        registered.source_id,
    ) == updated


def test_update_source_role_preserves_content(
    registry: ProjectSourceRegistry,
    input_root: Path,
    clock: MutableClock,
) -> None:
    registered = register_text_source(
        registry,
        input_root,
        content="Immutable original source content.",
    )
    content_path = registry.source_content_path(
        PROJECT_ID,
        registered.source_id,
    )
    original_bytes = content_path.read_bytes()

    clock.set(2026, 7, 22, 14)

    registry.update_source_role(
        PROJECT_ID,
        registered.source_id,
        source_role=CONTEXT_ONLY_SOURCE_ROLE,
    )

    assert content_path.read_bytes() == original_bytes


def test_update_source_role_rejects_invalid_role(
    registry: ProjectSourceRegistry,
    input_root: Path,
) -> None:
    registered = register_text_source(
        registry,
        input_root,
    )

    with pytest.raises(UnsupportedSourceRoleError):
        registry.update_source_role(
            PROJECT_ID,
            registered.source_id,
            source_role="supporting_document",
        )


def test_update_source_role_rejects_unknown_source(
    registry: ProjectSourceRegistry,
) -> None:
    with pytest.raises(SourceNotFoundError):
        registry.update_source_role(
            PROJECT_ID,
            "SRC-000001",
            source_role=CONTEXT_ONLY_SOURCE_ROLE,
        )


def test_duplicate_content_in_same_project_is_rejected(
    registry: ProjectSourceRegistry,
    input_root: Path,
) -> None:
    first_input = write_text_source(
        input_root,
        filename="first.txt",
        content="Identical source content.",
    )
    second_input = write_text_source(
        input_root,
        filename="second.txt",
        content="Identical source content.",
    )

    first = registry.register_source(
        PROJECT_ID,
        first_input,
        source_role=ENGINEERING_SOURCE_ROLE,
    )

    with pytest.raises(
        DuplicateSourceContentError,
        match=first.source_id,
    ):
        registry.register_source(
            PROJECT_ID,
            second_input,
            source_role=CONTEXT_ONLY_SOURCE_ROLE,
        )


def test_duplicate_rejection_does_not_create_source_directory(
    registry: ProjectSourceRegistry,
    projects_root: Path,
    input_root: Path,
) -> None:
    first_input = write_text_source(
        input_root,
        filename="first.txt",
        content="Duplicate content.",
    )
    second_input = write_text_source(
        input_root,
        filename="second.txt",
        content="Duplicate content.",
    )

    registry.register_source(
        PROJECT_ID,
        first_input,
        source_role=ENGINEERING_SOURCE_ROLE,
    )

    with pytest.raises(DuplicateSourceContentError):
        registry.register_source(
            PROJECT_ID,
            second_input,
            source_role=ENGINEERING_SOURCE_ROLE,
        )

    sources_root = (
        projects_root
        / PROJECT_ID
        / "sources"
    )

    assert sorted(
        path.name
        for path in sources_root.iterdir()
        if not path.name.startswith(".")
    ) == ["SRC-000001"]


def test_different_content_in_same_project_is_accepted(
    registry: ProjectSourceRegistry,
    input_root: Path,
) -> None:
    first = register_text_source(
        registry,
        input_root,
        filename="first.txt",
        content="First content.",
    )
    second = register_text_source(
        registry,
        input_root,
        filename="second.txt",
        content="Second content.",
    )

    assert first.source_id == "SRC-000001"
    assert second.source_id == "SRC-000002"
    assert first.sha256 != second.sha256


def test_same_content_in_different_projects_is_accepted(
    projects_root: Path,
    input_root: Path,
    clock: MutableClock,
) -> None:
    second_workspace = ProjectWorkspace(
        root=projects_root,
        id_generator=lambda: SECOND_PROJECT_ID,
        clock=clock,
    )
    second_workspace.create_project("Second Registry Project")

    registry = ProjectSourceRegistry(
        root=projects_root,
        clock=clock,
    )

    input_path = write_text_source(
        input_root,
        content="Shared source content.",
    )

    first = registry.register_source(
        PROJECT_ID,
        input_path,
        source_role=ENGINEERING_SOURCE_ROLE,
    )
    second = registry.register_source(
        SECOND_PROJECT_ID,
        input_path,
        source_role=ENGINEERING_SOURCE_ROLE,
    )

    assert first.sha256 == second.sha256
    assert first.project_id == PROJECT_ID
    assert second.project_id == SECOND_PROJECT_ID
    assert first.source_id == "SRC-000001"
    assert second.source_id == "SRC-000001"


def test_scan_sources_returns_valid_sources_in_source_id_order(
    registry: ProjectSourceRegistry,
    input_root: Path,
) -> None:
    first = register_text_source(
        registry,
        input_root,
        filename="first.txt",
        content="First source.",
    )
    second = register_text_source(
        registry,
        input_root,
        filename="second.txt",
        content="Second source.",
    )
    third = register_text_source(
        registry,
        input_root,
        filename="third.txt",
        content="Third source.",
    )

    scan = registry.scan_sources(PROJECT_ID)

    assert scan.valid_sources == (
        first,
        second,
        third,
    )
    assert scan.source_issues == ()


def test_scan_sources_returns_empty_result_for_project_without_sources(
    registry: ProjectSourceRegistry,
) -> None:
    scan = registry.scan_sources(PROJECT_ID)

    assert scan.valid_sources == ()
    assert scan.source_issues == ()


def test_scan_sources_ignores_hidden_entries(
    registry: ProjectSourceRegistry,
    projects_root: Path,
) -> None:
    sources_root = (
        projects_root
        / PROJECT_ID
        / "sources"
    )
    sources_root.mkdir(exist_ok=True)

    (sources_root / ".DS_Store").write_bytes(b"metadata")
    (
        sources_root
        / ".register-SRC-000001.tmp"
    ).mkdir()

    scan = registry.scan_sources(PROJECT_ID)

    assert scan.valid_sources == ()
    assert scan.source_issues == ()


def test_scan_sources_reports_visible_unexpected_entry(
    registry: ProjectSourceRegistry,
    projects_root: Path,
) -> None:
    sources_root = (
        projects_root
        / PROJECT_ID
        / "sources"
    )
    sources_root.mkdir(exist_ok=True)

    unexpected_path = sources_root / "unexpected.txt"
    unexpected_path.write_text(
        "Unexpected entry",
        encoding="utf-8",
    )

    scan = registry.scan_sources(PROJECT_ID)

    assert scan.valid_sources == ()
    assert len(scan.source_issues) == 1
    assert scan.source_issues[0].project_id == PROJECT_ID
    assert scan.source_issues[0].path == unexpected_path


def test_scan_sources_reports_missing_manifest(
    registry: ProjectSourceRegistry,
    projects_root: Path,
) -> None:
    incomplete_source_directory = source_directory(
        projects_root,
        "SRC-000001",
    )
    incomplete_source_directory.mkdir(parents=True)

    scan = registry.scan_sources(PROJECT_ID)

    assert scan.valid_sources == ()
    assert len(scan.source_issues) == 1
    assert scan.source_issues[0].source_id == "SRC-000001"


def test_scan_sources_reports_invalid_manifest_json(
    registry: ProjectSourceRegistry,
    projects_root: Path,
) -> None:
    incomplete_source_directory = source_directory(
        projects_root,
        "SRC-000001",
    )
    incomplete_source_directory.mkdir(parents=True)

    (
        incomplete_source_directory
        / "source_manifest.json"
    ).write_text(
        "{not valid JSON",
        encoding="utf-8",
    )

    scan = registry.scan_sources(PROJECT_ID)

    assert scan.valid_sources == ()
    assert len(scan.source_issues) == 1
    assert scan.source_issues[0].source_id == "SRC-000001"


def test_scan_sources_reports_missing_content(
    registry: ProjectSourceRegistry,
    projects_root: Path,
    input_root: Path,
) -> None:
    registered = register_text_source(
        registry,
        input_root,
    )
    content_path = registry.source_content_path(
        PROJECT_ID,
        registered.source_id,
    )
    content_path.unlink()

    scan = registry.scan_sources(PROJECT_ID)

    assert scan.valid_sources == ()
    assert len(scan.source_issues) == 1
    assert scan.source_issues[0].source_id == registered.source_id


def test_scan_sources_reports_modified_content(
    registry: ProjectSourceRegistry,
    input_root: Path,
) -> None:
    registered = register_text_source(
        registry,
        input_root,
    )
    content_path = registry.source_content_path(
        PROJECT_ID,
        registered.source_id,
    )
    content_path.write_text(
        "Modified after registration.",
        encoding="utf-8",
    )

    scan = registry.scan_sources(PROJECT_ID)

    assert scan.valid_sources == ()
    assert len(scan.source_issues) == 1
    assert scan.source_issues[0].source_id == registered.source_id


def test_load_source_rejects_modified_content(
    registry: ProjectSourceRegistry,
    input_root: Path,
) -> None:
    registered = register_text_source(
        registry,
        input_root,
    )
    content_path = registry.source_content_path(
        PROJECT_ID,
        registered.source_id,
    )
    content_path.write_bytes(b"tampered content")

    with pytest.raises(SourceIntegrityError):
        registry.load_source(
            PROJECT_ID,
            registered.source_id,
        )


def test_load_source_rejects_manifest_project_mismatch(
    registry: ProjectSourceRegistry,
    projects_root: Path,
    input_root: Path,
) -> None:
    registered = register_text_source(
        registry,
        input_root,
    )
    manifest_path = (
        source_directory(
            projects_root,
            registered.source_id,
        )
        / "source_manifest.json"
    )
    payload = json.loads(
        manifest_path.read_text(encoding="utf-8")
    )
    payload["project_id"] = SECOND_PROJECT_ID
    manifest_path.write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(SourceManifestError):
        registry.load_source(
            PROJECT_ID,
            registered.source_id,
        )


def test_load_source_rejects_manifest_source_mismatch(
    registry: ProjectSourceRegistry,
    projects_root: Path,
    input_root: Path,
) -> None:
    registered = register_text_source(
        registry,
        input_root,
    )
    manifest_path = (
        source_directory(
            projects_root,
            registered.source_id,
        )
        / "source_manifest.json"
    )
    payload = json.loads(
        manifest_path.read_text(encoding="utf-8")
    )
    payload["source_id"] = "SRC-000002"
    manifest_path.write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(SourceManifestError):
        registry.load_source(
            PROJECT_ID,
            registered.source_id,
        )


def test_register_source_rejects_input_symlink(
    registry: ProjectSourceRegistry,
    input_root: Path,
) -> None:
    target_path = write_text_source(
        input_root,
        filename="target.txt",
    )
    symlink_path = input_root / "linked.txt"

    try:
        symlink_path.symlink_to(target_path)
    except (NotImplementedError, OSError):
        pytest.skip("Symbolic links are not available.")

    with pytest.raises(UnsafeSourcePathError):
        registry.register_source(
            PROJECT_ID,
            symlink_path,
            source_role=ENGINEERING_SOURCE_ROLE,
        )


def test_scan_sources_reports_source_directory_symlink(
    registry: ProjectSourceRegistry,
    projects_root: Path,
    tmp_path: Path,
) -> None:
    external_directory = tmp_path / "external-source"
    external_directory.mkdir()

    linked_source_directory = source_directory(
        projects_root,
        "SRC-000001",
    )
    linked_source_directory.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    try:
        linked_source_directory.symlink_to(
            external_directory,
            target_is_directory=True,
        )
    except (NotImplementedError, OSError):
        pytest.skip("Symbolic links are not available.")

    scan = registry.scan_sources(PROJECT_ID)

    assert scan.valid_sources == ()
    assert len(scan.source_issues) == 1
    assert scan.source_issues[0].source_id == "SRC-000001"


def test_registered_manifest_is_immutable_value_object(
    registry: ProjectSourceRegistry,
    input_root: Path,
) -> None:
    registered = register_text_source(
        registry,
        input_root,
    )

    with pytest.raises(AttributeError):
        registered.source_role = CONTEXT_ONLY_SOURCE_ROLE  # type: ignore[misc]