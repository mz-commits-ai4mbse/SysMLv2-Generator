from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

import pytest

import modules.project_workspace.workspace as workspace_module
from modules.project_workspace.errors import (
    DuplicateProjectNameError,
    ProjectIdGenerationError,
    ProjectManifestError,
    ProjectNotFoundError,
    ProjectWorkspaceError,
    UnsafeProjectPathError,
)
from modules.project_workspace.manifest import (
    PROJECT_MANIFEST_FILENAME,
    create_project_manifest,
    project_manifest_to_json,
)
from modules.project_workspace.workspace import ProjectWorkspace


def _fixed_clock(
    hour: int = 8,
):
    return lambda: datetime(
        2026,
        7,
        22,
        hour,
        0,
        tzinfo=timezone.utc,
    )


def _id_sequence(*project_ids):
    project_id_iterator = iter(project_ids)

    return lambda: next(project_id_iterator)


def test_scan_of_missing_workspace_is_empty(
    tmp_path: Path,
) -> None:
    root = tmp_path / "projects"
    workspace = ProjectWorkspace(root)

    result = workspace.scan_projects()

    assert result.valid_projects == ()
    assert result.workspace_issues == ()
    assert not root.exists()


def test_project_can_be_created_persisted_and_reopened(
    tmp_path: Path,
) -> None:
    root = tmp_path / "projects"

    workspace = ProjectWorkspace(
        root,
        id_generator=lambda: "000042",
        clock=_fixed_clock(),
    )

    created = workspace.create_project(
        "Example Project",
        "Example description",
    )

    project_path = root / "000042"
    manifest_path = project_path / PROJECT_MANIFEST_FILENAME

    assert created.project_id == "000042"
    assert manifest_path.is_file()
    assert sorted(path.name for path in project_path.iterdir()) == [
        PROJECT_MANIFEST_FILENAME
    ]

    reopened_workspace = ProjectWorkspace(root)
    reopened = reopened_workspace.load_project("000042")

    assert reopened == created


def test_project_id_collision_uses_next_candidate(
    tmp_path: Path,
) -> None:
    root = tmp_path / "projects"

    first_workspace = ProjectWorkspace(
        root,
        id_generator=lambda: "000001",
        clock=_fixed_clock(),
    )
    first_workspace.create_project("First Project")

    second_workspace = ProjectWorkspace(
        root,
        id_generator=_id_sequence(
            "000001",
            "000002",
        ),
        clock=_fixed_clock(),
    )
    second = second_workspace.create_project("Second Project")

    assert second.project_id == "000002"
    assert (root / "000001").is_dir()
    assert (root / "000002").is_dir()


def test_invalid_generated_project_id_is_rejected(
    tmp_path: Path,
) -> None:
    root = tmp_path / "projects"

    workspace = ProjectWorkspace(
        root,
        id_generator=lambda: "../outside",
        clock=_fixed_clock(),
    )

    with pytest.raises(
        ProjectIdGenerationError,
        match="invalid value",
    ):
        workspace.create_project("Example Project")

    assert not root.exists()


def test_project_id_generation_attempts_are_bounded(
    tmp_path: Path,
    monkeypatch,
) -> None:
    root = tmp_path / "projects"

    existing_workspace = ProjectWorkspace(
        root,
        id_generator=lambda: "000001",
        clock=_fixed_clock(),
    )
    existing_workspace.create_project("Existing Project")

    monkeypatch.setattr(
        workspace_module,
        "MAX_PROJECT_ID_GENERATION_ATTEMPTS",
        2,
    )

    colliding_workspace = ProjectWorkspace(
        root,
        id_generator=lambda: "000001",
        clock=_fixed_clock(),
    )

    with pytest.raises(
        ProjectIdGenerationError,
        match="after 2 attempts",
    ):
        colliding_workspace.create_project("New Project")


def test_stale_creation_directory_is_retained_and_ignored(
    tmp_path: Path,
) -> None:
    root = tmp_path / "projects"
    root.mkdir()

    stale_directory = root / ".create-000001.tmp"
    stale_directory.mkdir()
    diagnostic_file = stale_directory / "diagnostic.txt"
    diagnostic_file.write_text(
        "retain for diagnosis",
        encoding="utf-8",
    )

    workspace = ProjectWorkspace(
        root,
        id_generator=_id_sequence(
            "000001",
            "000002",
        ),
        clock=_fixed_clock(),
    )

    created = workspace.create_project("Example Project")
    scan = workspace.scan_projects()

    assert created.project_id == "000002"
    assert diagnostic_file.read_text(
        encoding="utf-8"
    ) == "retain for diagnosis"
    assert scan.valid_projects == (created,)
    assert scan.workspace_issues == ()


def test_duplicate_normalized_name_is_rejected_on_create(
    tmp_path: Path,
) -> None:
    root = tmp_path / "projects"

    workspace = ProjectWorkspace(
        root,
        id_generator=_id_sequence(
            "000001",
            "000002",
        ),
        clock=_fixed_clock(),
    )

    workspace.create_project("Straße")

    with pytest.raises(DuplicateProjectNameError):
        workspace.create_project("  STRASSE  ")

    assert not (root / "000002").exists()


def test_project_update_preserves_immutable_metadata(
    tmp_path: Path,
) -> None:
    root = tmp_path / "projects"
    timestamps = iter(
        [
            datetime(
                2026,
                7,
                22,
                8,
                0,
                tzinfo=timezone.utc,
            ),
            datetime(
                2026,
                7,
                22,
                9,
                0,
                tzinfo=timezone.utc,
            ),
        ]
    )

    workspace = ProjectWorkspace(
        root,
        id_generator=lambda: "000042",
        clock=lambda: next(timestamps),
    )

    created = workspace.create_project(
        "Initial Name",
        "Initial description",
    )

    updated = workspace.update_project(
        "000042",
        display_name="  Updated Name  ",
        description="Updated description",
    )

    assert updated.project_id == created.project_id
    assert updated.created_at == created.created_at
    assert (
        updated.framework_template
        == created.framework_template
    )
    assert updated.display_name == "Updated Name"
    assert updated.description == "Updated description"
    assert updated.updated_at == "2026-07-22T09:00:00Z"

    reopened = ProjectWorkspace(root).load_project("000042")

    assert reopened == updated
    assert not (
        root
        / "000042"
        / f"{PROJECT_MANIFEST_FILENAME}.tmp"
    ).exists()


def test_unchanged_update_is_a_no_op(
    tmp_path: Path,
) -> None:
    root = tmp_path / "projects"

    creator = ProjectWorkspace(
        root,
        id_generator=lambda: "000042",
        clock=_fixed_clock(),
    )
    created = creator.create_project(
        "Example Project",
        "Description",
    )

    def unexpected_clock_call():
        raise AssertionError(
            "No-op update must not request a new timestamp."
        )

    updater = ProjectWorkspace(
        root,
        clock=unexpected_clock_call,
    )

    unchanged = updater.update_project(
        "000042",
        display_name="Example Project",
        description="Description",
    )

    assert unchanged == created


def test_duplicate_name_is_rejected_on_update(
    tmp_path: Path,
) -> None:
    root = tmp_path / "projects"
    timestamps = iter(
        [
            datetime(
                2026,
                7,
                22,
                8,
                0,
                tzinfo=timezone.utc,
            ),
            datetime(
                2026,
                7,
                22,
                9,
                0,
                tzinfo=timezone.utc,
            ),
            datetime(
                2026,
                7,
                22,
                10,
                0,
                tzinfo=timezone.utc,
            ),
        ]
    )

    workspace = ProjectWorkspace(
        root,
        id_generator=_id_sequence(
            "000001",
            "000002",
        ),
        clock=lambda: next(timestamps),
    )

    first = workspace.create_project("First Project")
    second = workspace.create_project("Second Project")

    with pytest.raises(DuplicateProjectNameError):
        workspace.update_project(
            second.project_id,
            display_name="  FIRST   PROJECT  ",
        )

    assert workspace.load_project(first.project_id) == first
    assert workspace.load_project(second.project_id) == second


def test_invalid_update_does_not_replace_manifest(
    tmp_path: Path,
) -> None:
    root = tmp_path / "projects"
    timestamps = iter(
        [
            datetime(
                2026,
                7,
                22,
                8,
                0,
                tzinfo=timezone.utc,
            ),
            datetime(
                2026,
                7,
                22,
                9,
                0,
                tzinfo=timezone.utc,
            ),
        ]
    )

    workspace = ProjectWorkspace(
        root,
        id_generator=lambda: "000042",
        clock=lambda: next(timestamps),
    )
    original = workspace.create_project("Example Project")

    with pytest.raises(ProjectManifestError):
        workspace.update_project(
            "000042",
            description="X" * 2001,
        )

    assert workspace.load_project("000042") == original


def test_stale_update_file_is_not_overwritten(
    tmp_path: Path,
) -> None:
    root = tmp_path / "projects"
    timestamps = iter(
        [
            datetime(
                2026,
                7,
                22,
                8,
                0,
                tzinfo=timezone.utc,
            ),
            datetime(
                2026,
                7,
                22,
                9,
                0,
                tzinfo=timezone.utc,
            ),
        ]
    )

    workspace = ProjectWorkspace(
        root,
        id_generator=lambda: "000042",
        clock=lambda: next(timestamps),
    )
    original = workspace.create_project("Example Project")

    temporary_manifest_path = (
        root
        / "000042"
        / f"{PROJECT_MANIFEST_FILENAME}.tmp"
    )
    temporary_manifest_path.write_text(
        "retain for diagnosis",
        encoding="utf-8",
    )

    with pytest.raises(
        ProjectWorkspaceError,
        match="already exists",
    ):
        workspace.update_project(
            "000042",
            description="Changed",
        )

    assert temporary_manifest_path.read_text(
        encoding="utf-8"
    ) == "retain for diagnosis"
    assert workspace.load_project("000042") == original


def test_scan_is_deterministic_and_ignores_hidden_entries(
    tmp_path: Path,
) -> None:
    root = tmp_path / "projects"

    workspace = ProjectWorkspace(
        root,
        id_generator=_id_sequence(
            "000002",
            "000001",
        ),
        clock=_fixed_clock(),
    )

    second = workspace.create_project("Second Project")
    first = workspace.create_project("First Project")

    (root / ".DS_Store").write_text(
        "ignored",
        encoding="utf-8",
    )
    (root / ".create-999999.tmp").mkdir()

    result = workspace.scan_projects()

    assert result.valid_projects == (
        first,
        second,
    )
    assert result.workspace_issues == ()
    assert (root / ".create-999999.tmp").exists()


def test_scan_reports_bad_entries_without_hiding_valid_project(
    tmp_path: Path,
) -> None:
    root = tmp_path / "projects"

    workspace = ProjectWorkspace(
        root,
        id_generator=lambda: "000001",
        clock=_fixed_clock(),
    )
    valid = workspace.create_project("Valid Project")

    (root / "000002").mkdir()

    invalid_json_directory = root / "000003"
    invalid_json_directory.mkdir()
    (
        invalid_json_directory / PROJECT_MANIFEST_FILENAME
    ).write_text(
        "{",
        encoding="utf-8",
    )

    (root / "not-a-project").mkdir()
    (root / "README.txt").write_text(
        "unexpected",
        encoding="utf-8",
    )
    (root / ".DS_Store").write_text(
        "ignored",
        encoding="utf-8",
    )

    result = workspace.scan_projects()
    issue_codes = {
        issue.code
        for issue in result.workspace_issues
    }

    assert result.valid_projects == (valid,)
    assert issue_codes == {
        "invalid_manifest",
        "invalid_project_directory",
        "unexpected_workspace_entry",
    }
    assert len(result.workspace_issues) == 4


def test_scan_reports_manifest_directory_mismatch(
    tmp_path: Path,
) -> None:
    root = tmp_path / "projects"
    project_path = root / "000042"
    project_path.mkdir(parents=True)

    mismatched_manifest = create_project_manifest(
        "000043",
        "Mismatched Project",
        timestamp="2026-07-22T08:00:00Z",
    )

    (
        project_path / PROJECT_MANIFEST_FILENAME
    ).write_text(
        project_manifest_to_json(mismatched_manifest),
        encoding="utf-8",
    )

    result = ProjectWorkspace(root).scan_projects()

    assert result.valid_projects == ()
    assert len(result.workspace_issues) == 1
    assert result.workspace_issues[0].code == "invalid_manifest"
    assert "does not match" in result.workspace_issues[0].message


def test_scan_reports_both_duplicate_names(
    tmp_path: Path,
) -> None:
    root = tmp_path / "projects"

    workspace = ProjectWorkspace(
        root,
        id_generator=_id_sequence(
            "000001",
            "000002",
        ),
        clock=_fixed_clock(),
    )

    first = workspace.create_project("First Project")
    second = workspace.create_project("Second Project")

    second_manifest_path = (
        root
        / second.project_id
        / PROJECT_MANIFEST_FILENAME
    )
    second_payload = json.loads(
        second_manifest_path.read_text(encoding="utf-8")
    )
    second_payload["display_name"] = "  First Project  ".strip()

    second_manifest_path.write_text(
        json.dumps(
            second_payload,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    result = workspace.scan_projects()
    duplicate_issues = [
        issue
        for issue in result.workspace_issues
        if issue.code == "duplicate_project_name"
    ]

    assert {
        manifest.project_id
        for manifest in result.valid_projects
    } == {
        first.project_id,
        second.project_id,
    }
    assert {
        issue.project_id
        for issue in duplicate_issues
    } == {
        first.project_id,
        second.project_id,
    }
    assert len(duplicate_issues) == 2


@pytest.mark.parametrize(
    "project_id",
    [
        "",
        "42",
        "1234567",
        "../000042",
        "/000042",
        "ABCDEF",
    ],
)
def test_unsafe_project_identifiers_are_rejected(
    tmp_path: Path,
    project_id,
) -> None:
    workspace = ProjectWorkspace(tmp_path / "projects")

    with pytest.raises(UnsafeProjectPathError):
        workspace.load_project(project_id)


def test_missing_project_raises_explicit_error(
    tmp_path: Path,
) -> None:
    workspace = ProjectWorkspace(tmp_path / "projects")

    with pytest.raises(ProjectNotFoundError):
        workspace.load_project("000042")


def test_symbolic_link_project_directory_is_rejected(
    tmp_path: Path,
) -> None:
    root = tmp_path / "projects"
    root.mkdir()

    external_directory = tmp_path / "external-project"
    external_directory.mkdir()

    symbolic_link = root / "000042"

    try:
        symbolic_link.symlink_to(
            external_directory,
            target_is_directory=True,
        )
    except OSError:
        pytest.skip("Symbolic links are unavailable.")

    workspace = ProjectWorkspace(root)
    result = workspace.scan_projects()

    assert result.valid_projects == ()
    assert len(result.workspace_issues) == 1
    assert result.workspace_issues[0].code == (
        "unsafe_project_path"
    )

    with pytest.raises(UnsafeProjectPathError):
        workspace.load_project("000042")


def test_symbolic_link_manifest_is_rejected(
    tmp_path: Path,
) -> None:
    root = tmp_path / "projects"
    project_path = root / "000042"
    project_path.mkdir(parents=True)

    external_manifest = tmp_path / "external-manifest.json"
    manifest = create_project_manifest(
        "000042",
        "External Project",
        timestamp="2026-07-22T08:00:00Z",
    )
    external_manifest.write_text(
        project_manifest_to_json(manifest),
        encoding="utf-8",
    )

    symbolic_link = project_path / PROJECT_MANIFEST_FILENAME

    try:
        symbolic_link.symlink_to(external_manifest)
    except OSError:
        pytest.skip("Symbolic links are unavailable.")

    workspace = ProjectWorkspace(root)
    result = workspace.scan_projects()

    assert result.valid_projects == ()
    assert len(result.workspace_issues) == 1
    assert result.workspace_issues[0].code == (
        "unsafe_project_path"
    )

    with pytest.raises(UnsafeProjectPathError):
        workspace.load_project("000042")


def test_workspace_root_file_is_reported_and_rejected(
    tmp_path: Path,
) -> None:
    root = tmp_path / "projects"
    root.write_text("not a directory", encoding="utf-8")

    workspace = ProjectWorkspace(
        root,
        id_generator=lambda: "000042",
        clock=_fixed_clock(),
    )

    result = workspace.scan_projects()

    assert result.valid_projects == ()
    assert len(result.workspace_issues) == 1
    assert result.workspace_issues[0].code == (
        "unsafe_workspace_root"
    )

    with pytest.raises(UnsafeProjectPathError):
        workspace.create_project("Example Project")


def test_workspace_clock_is_converted_to_utc(
    tmp_path: Path,
) -> None:
    local_timezone = timezone(timedelta(hours=2))

    workspace = ProjectWorkspace(
        tmp_path / "projects",
        id_generator=lambda: "000042",
        clock=lambda: datetime(
            2026,
            7,
            22,
            10,
            0,
            tzinfo=local_timezone,
        ),
    )

    created = workspace.create_project("Example Project")

    assert created.created_at == "2026-07-22T08:00:00Z"
    assert created.updated_at == "2026-07-22T08:00:00Z"


@pytest.mark.parametrize(
    "clock_value",
    [
        None,
        "2026-07-22T08:00:00Z",
        datetime(2026, 7, 22, 8, 0),
    ],
)
def test_invalid_workspace_clock_is_rejected(
    tmp_path: Path,
    clock_value,
) -> None:
    workspace = ProjectWorkspace(
        tmp_path / "projects",
        id_generator=lambda: "000042",
        clock=lambda: clock_value,
    )

    with pytest.raises(ProjectWorkspaceError):
        workspace.create_project("Example Project")