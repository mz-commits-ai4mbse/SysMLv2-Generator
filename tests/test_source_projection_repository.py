"""Tests for the persistent Source Projection Repository."""

from __future__ import annotations

from datetime import datetime, timezone
from io import BytesIO
import json
from pathlib import Path

import pytest
from pypdf import PdfWriter

from modules.project_sources import (
    ProjectSourceRegistry,
)
from modules.project_sources.errors import (
    SourceIntegrityError,
    SourceNotFoundError,
)
from modules.project_workspace import ProjectWorkspace
from modules.project_workspace.errors import (
    ProjectNotFoundError,
)
from modules.source_projection.errors import (
    SourceProjectionError,
    SourceProjectionIntegrityError,
    SourceProjectionNotFoundError,
    UnsupportedSourceFormatError,
    UnsupportedTextEncodingError,
    UnsafeSourceProjectionPathError,
)
from modules.source_projection.manifest import (
    calculate_projection_fingerprint,
)
from modules.source_projection.repository import (
    SourceProjectionRepository,
)


PROJECT_ID = "318604"
SECOND_PROJECT_ID = "429715"


class MutableClock:
    """Controllable timezone-aware test clock."""

    def __init__(self) -> None:
        self.value = datetime(
            2026,
            7,
            22,
            16,
            0,
            0,
            tzinfo=timezone.utc,
        )

    def __call__(self) -> datetime:
        return self.value

    def set(
        self,
        *,
        hour: int,
        minute: int = 0,
    ) -> None:
        self.value = datetime(
            2026,
            7,
            22,
            hour,
            minute,
            0,
            tzinfo=timezone.utc,
        )


@pytest.fixture
def clock() -> MutableClock:
    return MutableClock()


@pytest.fixture
def projects_root(
    tmp_path: Path,
) -> Path:
    return tmp_path / "projects"


@pytest.fixture
def input_root(
    tmp_path: Path,
) -> Path:
    path = tmp_path / "inputs"
    path.mkdir()
    return path


@pytest.fixture
def workspace(
    projects_root: Path,
    clock: MutableClock,
) -> ProjectWorkspace:
    result = ProjectWorkspace(
        root=projects_root,
        id_generator=lambda: PROJECT_ID,
        clock=clock,
    )
    result.create_project(
        "Source Projection Repository Test"
    )
    return result


@pytest.fixture
def source_registry(
    workspace: ProjectWorkspace,
    projects_root: Path,
    clock: MutableClock,
) -> ProjectSourceRegistry:
    del workspace
    return ProjectSourceRegistry(
        root=projects_root,
        clock=clock,
    )


@pytest.fixture
def repository(
    workspace: ProjectWorkspace,
    projects_root: Path,
    clock: MutableClock,
) -> SourceProjectionRepository:
    del workspace
    return SourceProjectionRepository(
        root=projects_root,
        clock=clock,
    )


def register_source(
    registry: ProjectSourceRegistry,
    input_root: Path,
    *,
    filename: str = "requirements.txt",
    content: bytes = (
        b"The system shall preserve traceability."
    ),
    source_role: str = "engineering_source",
):
    """Write and register one source."""

    input_path = input_root / filename
    input_path.write_bytes(content)

    return registry.register_source(
        PROJECT_ID,
        input_path,
        source_role=source_role,
    )


def blank_pdf_bytes() -> bytes:
    """Return a valid one-page PDF without a text layer."""

    stream = BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(
        width=72,
        height=72,
    )
    writer.write(stream)
    return stream.getvalue()


def projection_path(
    projects_root: Path,
    source_projection_id: str = "SP-000001",
) -> Path:
    return (
        projects_root
        / PROJECT_ID
        / "semantics"
        / "source_projections"
        / source_projection_id
    )


def projection_manifest_path(
    projects_root: Path,
    source_projection_id: str = "SP-000001",
) -> Path:
    return (
        projection_path(
            projects_root,
            source_projection_id,
        )
        / "projection.json"
    )


def projection_content_path(
    projects_root: Path,
    source_projection_id: str = "SP-000001",
) -> Path:
    return (
        projection_path(
            projects_root,
            source_projection_id,
        )
        / "content.txt"
    )


def test_create_projection_persists_expected_files(
    repository: SourceProjectionRepository,
    source_registry: ProjectSourceRegistry,
    input_root: Path,
    projects_root: Path,
) -> None:
    source = register_source(
        source_registry,
        input_root,
    )

    created = repository.create_projection(
        PROJECT_ID,
        source.source_id,
    )

    stored_path = projection_path(projects_root)

    assert created.manifest.source_projection_id == (
        "SP-000001"
    )
    assert stored_path.is_dir()
    assert sorted(
        entry.name
        for entry in stored_path.iterdir()
    ) == [
        "content.txt",
        "projection.json",
    ]


def test_create_projection_preserves_source_traceability(
    repository: SourceProjectionRepository,
    source_registry: ProjectSourceRegistry,
    input_root: Path,
) -> None:
    source = register_source(
        source_registry,
        input_root,
        source_role="engineering_source",
    )

    created = repository.create_projection(
        PROJECT_ID,
        source.source_id,
    )

    assert created.manifest.project_id == PROJECT_ID
    assert created.manifest.source_id == source.source_id
    assert created.manifest.source_role == (
        "engineering_source"
    )
    assert created.manifest.source_sha256 == source.sha256


def test_load_projection_returns_persisted_artifact(
    repository: SourceProjectionRepository,
    source_registry: ProjectSourceRegistry,
    input_root: Path,
) -> None:
    source = register_source(
        source_registry,
        input_root,
    )
    created = repository.create_projection(
        PROJECT_ID,
        source.source_id,
    )

    loaded = repository.load_projection(
        PROJECT_ID,
        created.manifest.source_projection_id,
    )

    assert loaded == created


def test_projection_survives_repository_restart(
    projects_root: Path,
    source_registry: ProjectSourceRegistry,
    input_root: Path,
    clock: MutableClock,
) -> None:
    source = register_source(
        source_registry,
        input_root,
    )

    first_repository = SourceProjectionRepository(
        root=projects_root,
        clock=clock,
    )
    created = first_repository.create_projection(
        PROJECT_ID,
        source.source_id,
    )

    reopened_repository = SourceProjectionRepository(
        root=projects_root,
        clock=clock,
    )

    assert reopened_repository.load_projection(
        PROJECT_ID,
        "SP-000001",
    ) == created


def test_identical_projection_is_reused(
    repository: SourceProjectionRepository,
    source_registry: ProjectSourceRegistry,
    input_root: Path,
) -> None:
    source = register_source(
        source_registry,
        input_root,
    )

    first = repository.create_projection(
        PROJECT_ID,
        source.source_id,
    )
    second = repository.create_projection(
        PROJECT_ID,
        source.source_id,
    )

    assert second == first
    assert tuple(
        artifact.manifest.source_projection_id
        for artifact in repository.list_projections(
            PROJECT_ID
        )
    ) == ("SP-000001",)


def test_reuse_is_independent_of_later_clock_value(
    repository: SourceProjectionRepository,
    source_registry: ProjectSourceRegistry,
    input_root: Path,
    clock: MutableClock,
) -> None:
    source = register_source(
        source_registry,
        input_root,
    )

    first = repository.create_projection(
        PROJECT_ID,
        source.source_id,
    )

    clock.set(hour=18)

    second = repository.create_projection(
        PROJECT_ID,
        source.source_id,
    )

    assert second == first
    assert second.manifest.created_at == (
        "2026-07-22T16:00:00Z"
    )


def test_different_sources_receive_sequential_projection_ids(
    repository: SourceProjectionRepository,
    source_registry: ProjectSourceRegistry,
    input_root: Path,
) -> None:
    first_source = register_source(
        source_registry,
        input_root,
        filename="first.txt",
        content=b"First source.",
    )
    second_source = register_source(
        source_registry,
        input_root,
        filename="second.txt",
        content=b"Second source.",
    )

    first = repository.create_projection(
        PROJECT_ID,
        first_source.source_id,
    )
    second = repository.create_projection(
        PROJECT_ID,
        second_source.source_id,
    )

    assert first.manifest.source_projection_id == (
        "SP-000001"
    )
    assert second.manifest.source_projection_id == (
        "SP-000002"
    )


def test_temporary_projection_directory_reserves_id(
    repository: SourceProjectionRepository,
    source_registry: ProjectSourceRegistry,
    input_root: Path,
    projects_root: Path,
) -> None:
    source = register_source(
        source_registry,
        input_root,
    )

    projections_root = (
        projects_root
        / PROJECT_ID
        / "semantics"
        / "source_projections"
    )
    projections_root.mkdir(parents=True)
    (
        projections_root
        / ".create-SP-000001.tmp"
    ).mkdir()

    created = repository.create_projection(
        PROJECT_ID,
        source.source_id,
    )

    assert created.manifest.source_projection_id == (
        "SP-000002"
    )


def test_successful_creation_removes_own_temporary_directory(
    repository: SourceProjectionRepository,
    source_registry: ProjectSourceRegistry,
    input_root: Path,
    projects_root: Path,
) -> None:
    source = register_source(
        source_registry,
        input_root,
    )

    repository.create_projection(
        PROJECT_ID,
        source.source_id,
    )

    projections_root = (
        projects_root
        / PROJECT_ID
        / "semantics"
        / "source_projections"
    )

    assert not any(
        entry.name.startswith(".create-")
        for entry in projections_root.iterdir()
    )


@pytest.mark.parametrize(
    (
        "filename",
        "content",
        "expected_adapter",
        "expected_result",
    ),
    [
        (
            "source.txt",
            b"Text source.",
            "plain_text",
            "complete",
        ),
        (
            "source.MD",
            b"# Markdown",
            "markdown",
            "complete",
        ),
        (
            "source.json",
            b'{"value":"JSON"}',
            "json",
            "complete",
        ),
        (
            "source.csv",
            b"id,value\nA,B",
            "csv",
            "complete",
        ),
        (
            "source.TSV",
            b"id\tvalue\nA\tB",
            "tsv",
            "complete",
        ),
        (
            "source.pdf",
            None,
            "pdf_text_layer",
            "unavailable",
        ),
    ],
)
def test_repository_routes_supported_formats(
    repository: SourceProjectionRepository,
    source_registry: ProjectSourceRegistry,
    input_root: Path,
    filename: str,
    content: bytes | None,
    expected_adapter: str,
    expected_result: str,
) -> None:
    if content is None:
        content = blank_pdf_bytes()

    source = register_source(
        source_registry,
        input_root,
        filename=filename,
        content=content,
    )

    created = repository.create_projection(
        PROJECT_ID,
        source.source_id,
    )

    assert created.manifest.adapter_id == (
        expected_adapter
    )
    assert created.manifest.projection_result == (
        expected_result
    )


def test_unavailable_pdf_is_persisted_with_empty_content(
    repository: SourceProjectionRepository,
    source_registry: ProjectSourceRegistry,
    input_root: Path,
    projects_root: Path,
) -> None:
    source = register_source(
        source_registry,
        input_root,
        filename="blank.pdf",
        content=blank_pdf_bytes(),
    )

    created = repository.create_projection(
        PROJECT_ID,
        source.source_id,
    )

    assert created.content == ""
    assert created.manifest.content_length == 0
    assert projection_content_path(
        projects_root
    ).read_text(encoding="utf-8") == ""


@pytest.mark.parametrize(
    "filename",
    [
        "source.doc",
        "source.docx",
        "source.odt",
        "source.rtf",
        "source.xml",
        "source.bin",
    ],
)
def test_repository_rejects_unsupported_formats(
    repository: SourceProjectionRepository,
    source_registry: ProjectSourceRegistry,
    input_root: Path,
    projects_root: Path,
    filename: str,
) -> None:
    source = register_source(
        source_registry,
        input_root,
        filename=filename,
        content=b"Unsupported source container.",
    )

    with pytest.raises(
        UnsupportedSourceFormatError
    ):
        repository.create_projection(
            PROJECT_ID,
            source.source_id,
        )

    assert not (
        projects_root
        / PROJECT_ID
        / "semantics"
    ).exists()


def test_repository_rejects_invalid_utf8_before_persistence(
    repository: SourceProjectionRepository,
    source_registry: ProjectSourceRegistry,
    input_root: Path,
    projects_root: Path,
) -> None:
    source = register_source(
        source_registry,
        input_root,
        filename="invalid.txt",
        content=b"\xff\xfe",
    )

    with pytest.raises(
        UnsupportedTextEncodingError
    ):
        repository.create_projection(
            PROJECT_ID,
            source.source_id,
        )

    assert not (
        projects_root
        / PROJECT_ID
        / "semantics"
    ).exists()


def test_context_only_source_projection_is_permitted(
    repository: SourceProjectionRepository,
    source_registry: ProjectSourceRegistry,
    input_root: Path,
) -> None:
    source = register_source(
        source_registry,
        input_root,
        source_role="context_only",
    )

    created = repository.create_projection(
        PROJECT_ID,
        source.source_id,
    )

    assert created.manifest.source_role == (
        "context_only"
    )


def test_source_role_change_creates_new_projection(
    repository: SourceProjectionRepository,
    source_registry: ProjectSourceRegistry,
    input_root: Path,
) -> None:
    source = register_source(
        source_registry,
        input_root,
        source_role="engineering_source",
    )

    engineering_projection = (
        repository.create_projection(
            PROJECT_ID,
            source.source_id,
        )
    )

    source_registry.update_source_role(
        PROJECT_ID,
        source.source_id,
        source_role="context_only",
    )

    context_projection = repository.create_projection(
        PROJECT_ID,
        source.source_id,
    )

    assert (
        engineering_projection.manifest.source_projection_id
        == "SP-000001"
    )
    assert (
        engineering_projection.manifest.source_role
        == "engineering_source"
    )
    assert (
        context_projection.manifest.source_projection_id
        == "SP-000002"
    )
    assert (
        context_projection.manifest.source_role
        == "context_only"
    )


def test_old_projection_remains_loadable_after_role_change(
    repository: SourceProjectionRepository,
    source_registry: ProjectSourceRegistry,
    input_root: Path,
) -> None:
    source = register_source(
        source_registry,
        input_root,
        source_role="engineering_source",
    )
    original = repository.create_projection(
        PROJECT_ID,
        source.source_id,
    )

    source_registry.update_source_role(
        PROJECT_ID,
        source.source_id,
        source_role="context_only",
    )

    assert repository.load_projection(
        PROJECT_ID,
        "SP-000001",
    ) == original


def test_list_projections_returns_identifier_order(
    repository: SourceProjectionRepository,
    source_registry: ProjectSourceRegistry,
    input_root: Path,
) -> None:
    sources = [
        register_source(
            source_registry,
            input_root,
            filename=f"source-{index}.txt",
            content=f"Source {index}.".encode(),
        )
        for index in range(1, 4)
    ]

    created = tuple(
        repository.create_projection(
            PROJECT_ID,
            source.source_id,
        )
        for source in sources
    )

    assert repository.list_projections(
        PROJECT_ID
    ) == created


def test_list_projections_can_filter_by_source(
    repository: SourceProjectionRepository,
    source_registry: ProjectSourceRegistry,
    input_root: Path,
) -> None:
    first_source = register_source(
        source_registry,
        input_root,
        filename="first.txt",
        content=b"First.",
    )
    second_source = register_source(
        source_registry,
        input_root,
        filename="second.txt",
        content=b"Second.",
    )

    first = repository.create_projection(
        PROJECT_ID,
        first_source.source_id,
    )
    repository.create_projection(
        PROJECT_ID,
        second_source.source_id,
    )

    assert repository.list_projections(
        PROJECT_ID,
        source_id=first_source.source_id,
    ) == (first,)


def test_list_projections_is_empty_before_creation(
    repository: SourceProjectionRepository,
) -> None:
    assert repository.list_projections(
        PROJECT_ID
    ) == ()


def test_projection_content_path_returns_validated_file(
    repository: SourceProjectionRepository,
    source_registry: ProjectSourceRegistry,
    input_root: Path,
) -> None:
    source = register_source(
        source_registry,
        input_root,
    )
    created = repository.create_projection(
        PROJECT_ID,
        source.source_id,
    )

    content_path = repository.projection_content_path(
        PROJECT_ID,
        "SP-000001",
    )

    assert content_path.name == "content.txt"
    assert content_path.read_text(
        encoding="utf-8"
    ) == created.content


def test_create_projection_rejects_unknown_project(
    projects_root: Path,
    clock: MutableClock,
) -> None:
    repository = SourceProjectionRepository(
        root=projects_root,
        clock=clock,
    )

    with pytest.raises(ProjectNotFoundError):
        repository.create_projection(
            "999999",
            "SRC-000001",
        )


def test_create_projection_rejects_unknown_source(
    repository: SourceProjectionRepository,
) -> None:
    with pytest.raises(SourceNotFoundError):
        repository.create_projection(
            PROJECT_ID,
            "SRC-000001",
        )


def test_load_projection_rejects_unknown_projection(
    repository: SourceProjectionRepository,
) -> None:
    with pytest.raises(
        SourceProjectionNotFoundError
    ):
        repository.load_projection(
            PROJECT_ID,
            "SP-000001",
        )


@pytest.mark.parametrize(
    "source_projection_id",
    [
        "",
        "SP-000000",
        "SP-1000000",
        "sp-000001",
        "../SP-000001",
    ],
)
def test_load_projection_rejects_invalid_identifier(
    repository: SourceProjectionRepository,
    source_projection_id: str,
) -> None:
    with pytest.raises(
        UnsafeSourceProjectionPathError
    ):
        repository.load_projection(
            PROJECT_ID,
            source_projection_id,
        )


def test_load_rejects_modified_content(
    repository: SourceProjectionRepository,
    source_registry: ProjectSourceRegistry,
    input_root: Path,
    projects_root: Path,
) -> None:
    source = register_source(
        source_registry,
        input_root,
    )
    repository.create_projection(
        PROJECT_ID,
        source.source_id,
    )

    content_path = projection_content_path(
        projects_root
    )
    original = content_path.read_text(
        encoding="utf-8"
    )
    content_path.write_text(
        "X" + original[1:],
        encoding="utf-8",
    )

    with pytest.raises(
        SourceProjectionIntegrityError
    ):
        repository.load_projection(
            PROJECT_ID,
            "SP-000001",
        )


def test_load_rejects_invalid_manifest_json(
    repository: SourceProjectionRepository,
    source_registry: ProjectSourceRegistry,
    input_root: Path,
    projects_root: Path,
) -> None:
    source = register_source(
        source_registry,
        input_root,
    )
    repository.create_projection(
        PROJECT_ID,
        source.source_id,
    )

    projection_manifest_path(
        projects_root
    ).write_text(
        "{invalid",
        encoding="utf-8",
    )

    with pytest.raises(
        SourceProjectionIntegrityError
    ):
        repository.load_projection(
            PROJECT_ID,
            "SP-000001",
        )


@pytest.mark.parametrize(
    "missing_filename",
    [
        "projection.json",
        "content.txt",
    ],
)
def test_load_rejects_missing_required_file(
    repository: SourceProjectionRepository,
    source_registry: ProjectSourceRegistry,
    input_root: Path,
    projects_root: Path,
    missing_filename: str,
) -> None:
    source = register_source(
        source_registry,
        input_root,
    )
    repository.create_projection(
        PROJECT_ID,
        source.source_id,
    )

    (
        projection_path(projects_root)
        / missing_filename
    ).unlink()

    with pytest.raises(
        SourceProjectionIntegrityError,
        match="entries are invalid",
    ):
        repository.load_projection(
            PROJECT_ID,
            "SP-000001",
        )


def test_load_rejects_unexpected_visible_file(
    repository: SourceProjectionRepository,
    source_registry: ProjectSourceRegistry,
    input_root: Path,
    projects_root: Path,
) -> None:
    source = register_source(
        source_registry,
        input_root,
    )
    repository.create_projection(
        PROJECT_ID,
        source.source_id,
    )

    (
        projection_path(projects_root)
        / "unexpected.txt"
    ).write_text(
        "unexpected",
        encoding="utf-8",
    )

    with pytest.raises(
        SourceProjectionIntegrityError,
        match="unexpected",
    ):
        repository.load_projection(
            PROJECT_ID,
            "SP-000001",
        )


def test_load_ignores_hidden_metadata_file(
    repository: SourceProjectionRepository,
    source_registry: ProjectSourceRegistry,
    input_root: Path,
    projects_root: Path,
) -> None:
    source = register_source(
        source_registry,
        input_root,
    )
    created = repository.create_projection(
        PROJECT_ID,
        source.source_id,
    )

    (
        projection_path(projects_root)
        / ".DS_Store"
    ).write_bytes(b"metadata")

    assert repository.load_projection(
        PROJECT_ID,
        "SP-000001",
    ) == created


def test_list_rejects_unexpected_visible_root_entry(
    repository: SourceProjectionRepository,
    projects_root: Path,
) -> None:
    projections_root = (
        projects_root
        / PROJECT_ID
        / "semantics"
        / "source_projections"
    )
    projections_root.mkdir(parents=True)
    (
        projections_root
        / "unexpected.txt"
    ).write_text(
        "unexpected",
        encoding="utf-8",
    )

    with pytest.raises(
        SourceProjectionIntegrityError
    ):
        repository.list_projections(PROJECT_ID)


def test_list_ignores_hidden_root_entries(
    repository: SourceProjectionRepository,
    projects_root: Path,
) -> None:
    projections_root = (
        projects_root
        / PROJECT_ID
        / "semantics"
        / "source_projections"
    )
    projections_root.mkdir(parents=True)
    (
        projections_root
        / ".DS_Store"
    ).write_bytes(b"metadata")

    assert repository.list_projections(
        PROJECT_ID
    ) == ()


def test_load_rejects_manifest_source_hash_mismatch(
    repository: SourceProjectionRepository,
    source_registry: ProjectSourceRegistry,
    input_root: Path,
    projects_root: Path,
) -> None:
    source = register_source(
        source_registry,
        input_root,
    )
    repository.create_projection(
        PROJECT_ID,
        source.source_id,
    )

    manifest_path = projection_manifest_path(
        projects_root
    )
    payload = json.loads(
        manifest_path.read_text(encoding="utf-8")
    )
    payload["source_sha256"] = "b" * 64
    payload["projection_fingerprint"] = (
        calculate_projection_fingerprint(
            source_sha256="b" * 64,
            adapter_id=payload["adapter_id"],
            adapter_version=payload["adapter_version"],
            adapter_configuration=tuple(
                payload["adapter_configuration"].items()
            ),
        )
    )
    manifest_path.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(
        SourceProjectionIntegrityError,
        match="registered source",
    ):
        repository.load_projection(
            PROJECT_ID,
            "SP-000001",
        )


def test_load_fails_when_registered_source_is_tampered(
    repository: SourceProjectionRepository,
    source_registry: ProjectSourceRegistry,
    input_root: Path,
) -> None:
    source = register_source(
        source_registry,
        input_root,
    )
    repository.create_projection(
        PROJECT_ID,
        source.source_id,
    )

    registered_content = (
        source_registry.source_content_path(
            PROJECT_ID,
            source.source_id,
        )
    )
    registered_content.write_bytes(
        b"Tampered source content."
    )

    with pytest.raises(SourceIntegrityError):
        repository.load_projection(
            PROJECT_ID,
            "SP-000001",
        )


def test_cross_project_projection_ids_remain_isolated(
    projects_root: Path,
    input_root: Path,
    clock: MutableClock,
) -> None:
    first_workspace = ProjectWorkspace(
        root=projects_root,
        id_generator=lambda: PROJECT_ID,
        clock=clock,
    )
    first_workspace.create_project("First Project")

    second_workspace = ProjectWorkspace(
        root=projects_root,
        id_generator=lambda: SECOND_PROJECT_ID,
        clock=clock,
    )
    second_workspace.create_project("Second Project")

    first_registry = ProjectSourceRegistry(
        root=projects_root,
        clock=clock,
    )
    second_registry = ProjectSourceRegistry(
        root=projects_root,
        clock=clock,
    )

    first_input = input_root / "first.txt"
    first_input.write_text(
        "First project source.",
        encoding="utf-8",
    )
    second_input = input_root / "second.txt"
    second_input.write_text(
        "Second project source.",
        encoding="utf-8",
    )

    first_source = first_registry.register_source(
        PROJECT_ID,
        first_input,
        source_role="engineering_source",
    )
    second_source = second_registry.register_source(
        SECOND_PROJECT_ID,
        second_input,
        source_role="engineering_source",
    )

    repository = SourceProjectionRepository(
        root=projects_root,
        clock=clock,
    )

    first = repository.create_projection(
        PROJECT_ID,
        first_source.source_id,
    )
    second = repository.create_projection(
        SECOND_PROJECT_ID,
        second_source.source_id,
    )

    assert first.manifest.source_projection_id == (
        "SP-000001"
    )
    assert second.manifest.source_projection_id == (
        "SP-000001"
    )
    assert first.manifest.project_id == PROJECT_ID
    assert second.manifest.project_id == (
        SECOND_PROJECT_ID
    )


def test_repository_rejects_semantics_root_file(
    repository: SourceProjectionRepository,
    source_registry: ProjectSourceRegistry,
    input_root: Path,
    projects_root: Path,
) -> None:
    source = register_source(
        source_registry,
        input_root,
    )
    semantics_path = (
        projects_root
        / PROJECT_ID
        / "semantics"
    )
    semantics_path.write_text(
        "not a directory",
        encoding="utf-8",
    )

    with pytest.raises(
        UnsafeSourceProjectionPathError
    ):
        repository.create_projection(
            PROJECT_ID,
            source.source_id,
        )


def test_repository_rejects_projection_root_file(
    repository: SourceProjectionRepository,
    source_registry: ProjectSourceRegistry,
    input_root: Path,
    projects_root: Path,
) -> None:
    source = register_source(
        source_registry,
        input_root,
    )
    semantics_path = (
        projects_root
        / PROJECT_ID
        / "semantics"
    )
    semantics_path.mkdir()
    (
        semantics_path
        / "source_projections"
    ).write_text(
        "not a directory",
        encoding="utf-8",
    )

    with pytest.raises(
        UnsafeSourceProjectionPathError
    ):
        repository.create_projection(
            PROJECT_ID,
            source.source_id,
        )


def test_load_rejects_projection_directory_symlink(
    repository: SourceProjectionRepository,
    projects_root: Path,
    tmp_path: Path,
) -> None:
    external = tmp_path / "external"
    external.mkdir()

    linked = projection_path(projects_root)
    linked.parent.mkdir(parents=True)

    try:
        linked.symlink_to(
            external,
            target_is_directory=True,
        )
    except (NotImplementedError, OSError):
        pytest.skip("Symbolic links are unavailable.")

    with pytest.raises(
        UnsafeSourceProjectionPathError
    ):
        repository.load_projection(
            PROJECT_ID,
            "SP-000001",
        )


def test_load_rejects_projection_file_symlink(
    repository: SourceProjectionRepository,
    source_registry: ProjectSourceRegistry,
    input_root: Path,
    projects_root: Path,
    tmp_path: Path,
) -> None:
    source = register_source(
        source_registry,
        input_root,
    )
    repository.create_projection(
        PROJECT_ID,
        source.source_id,
    )

    content_path = projection_content_path(
        projects_root
    )
    external = tmp_path / "external.txt"
    external.write_text(
        "external",
        encoding="utf-8",
    )
    content_path.unlink()

    try:
        content_path.symlink_to(external)
    except (NotImplementedError, OSError):
        pytest.skip("Symbolic links are unavailable.")

    with pytest.raises(
        UnsafeSourceProjectionPathError
    ):
        repository.load_projection(
            PROJECT_ID,
            "SP-000001",
        )


def test_repository_rejects_non_datetime_clock(
    projects_root: Path,
    source_registry: ProjectSourceRegistry,
    input_root: Path,
) -> None:
    source = register_source(
        source_registry,
        input_root,
    )
    repository = SourceProjectionRepository(
        root=projects_root,
        clock=lambda: "invalid",  # type: ignore[arg-type]
    )

    with pytest.raises(
        SourceProjectionError,
        match="must return a datetime",
    ):
        repository.create_projection(
            PROJECT_ID,
            source.source_id,
        )


def test_repository_rejects_naive_clock(
    projects_root: Path,
    source_registry: ProjectSourceRegistry,
    input_root: Path,
) -> None:
    source = register_source(
        source_registry,
        input_root,
    )
    repository = SourceProjectionRepository(
        root=projects_root,
        clock=lambda: datetime(
            2026,
            7,
            22,
            16,
            0,
            0,
        ),
    )

    with pytest.raises(
        SourceProjectionError,
        match="timezone-aware",
    ):
        repository.create_projection(
            PROJECT_ID,
            source.source_id,
        )