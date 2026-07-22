"""Persistent and isolated Project Workspace operations."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from dataclasses import replace
from datetime import datetime, timezone
import os
from pathlib import Path
from typing import Any

from modules.project_workspace.errors import (
    DuplicateProjectNameError,
    ProjectIdGenerationError,
    ProjectManifestError,
    ProjectNotFoundError,
    ProjectWorkspaceError,
    UnsafeProjectPathError,
)
from modules.project_workspace.identifiers import (
    generate_project_id,
    is_valid_project_id,
    normalize_display_name,
)
from modules.project_workspace.manifest import (
    PROJECT_MANIFEST_FILENAME,
    create_project_manifest,
    project_manifest_from_json,
    project_manifest_to_json,
    validate_project_manifest,
)
from modules.project_workspace.types import (
    ProjectManifest,
    WorkspaceIssue,
    WorkspaceScanResult,
)


DEFAULT_PROJECTS_ROOT = Path("data/projects")
MAX_PROJECT_ID_GENERATION_ATTEMPTS = 1_000


def _default_clock() -> datetime:
    return datetime.now(timezone.utc)


class ProjectWorkspace:
    """Create, reopen, update and discover isolated projects."""

    def __init__(
        self,
        root: Path | str = DEFAULT_PROJECTS_ROOT,
        *,
        id_generator: Callable[[], str] = generate_project_id,
        clock: Callable[[], datetime] = _default_clock,
    ) -> None:
        self.root = Path(root)
        self._id_generator = id_generator
        self._clock = clock

    def create_project(
        self,
        display_name: str,
        description: str = "",
    ) -> ProjectManifest:
        """Create and atomically persist one new project."""

        self._assert_workspace_root_safe()

        project_id = self._generate_available_project_id()
        timestamp = self._current_utc_timestamp()

        manifest = create_project_manifest(
            project_id,
            display_name,
            description=description,
            timestamp=timestamp,
        )

        self._ensure_display_name_unique(
            manifest.display_name,
        )

        try:
            self.root.mkdir(
                parents=True,
                exist_ok=True,
            )
        except OSError as exc:
            raise ProjectWorkspaceError(
                f"Unable to create workspace root {self.root}: {exc}"
            ) from exc

        self._assert_workspace_root_safe()

        project_path = self._project_path(project_id)
        temporary_path = self.root / (
            f".create-{project_id}.tmp"
        )

        if (
            temporary_path.exists()
            or temporary_path.is_symlink()
        ):
            raise ProjectIdGenerationError(
                "Temporary project creation path already exists: "
                f"{temporary_path}."
            )

        try:
            temporary_path.mkdir()
        except OSError as exc:
            raise ProjectWorkspaceError(
                "Unable to create temporary project directory "
                f"{temporary_path}: {exc}"
            ) from exc

        temporary_manifest_path = (
            temporary_path / PROJECT_MANIFEST_FILENAME
        )

        try:
            serialized = project_manifest_to_json(manifest)

            with temporary_manifest_path.open(
                "x",
                encoding="utf-8",
            ) as manifest_file:
                manifest_file.write(serialized)

            persisted_manifest = project_manifest_from_json(
                temporary_manifest_path.read_text(encoding="utf-8"),
                expected_project_id=project_id,
            )
        except OSError as exc:
            raise ProjectWorkspaceError(
                "Unable to persist temporary project manifest "
                f"{temporary_manifest_path}: {exc}"
            ) from exc

        if persisted_manifest != manifest:
            raise ProjectManifestError(
                "Persisted project manifest differs from the "
                "validated manifest."
            )

        if project_path.exists() or project_path.is_symlink():
            raise ProjectIdGenerationError(
                f"Project path already exists: {project_path}."
            )

        try:
            temporary_path.rename(project_path)
        except OSError as exc:
            raise ProjectWorkspaceError(
                "Unable to finalize project directory "
                f"{project_path}: {exc}"
            ) from exc

        return manifest

    def load_project(
        self,
        project_id: str,
    ) -> ProjectManifest:
        """Load and validate one project by immutable identifier."""

        self._assert_workspace_root_safe()

        project_path = self._project_path(project_id)

        if project_path.is_symlink():
            raise UnsafeProjectPathError(
                f"Symbolic-link project directories are rejected: "
                f"{project_path}."
            )

        if not project_path.exists() or not project_path.is_dir():
            raise ProjectNotFoundError(
                f"Project {project_id!r} was not found."
            )

        return self._load_manifest_from_directory(
            project_id,
            project_path,
        )

    def update_project(
        self,
        project_id: str,
        *,
        display_name: str | None = None,
        description: str | None = None,
    ) -> ProjectManifest:
        """Atomically update mutable project metadata."""

        current = self.load_project(project_id)

        next_display_name: Any = current.display_name

        if display_name is not None:
            next_display_name = display_name

            if isinstance(display_name, str):
                next_display_name = display_name.strip()

        next_description: Any = current.description

        if description is not None:
            next_description = description

        if (
            next_display_name == current.display_name
            and next_description == current.description
        ):
            return current

        updated = replace(
            current,
            display_name=next_display_name,
            description=next_description,
            updated_at=self._current_utc_timestamp(),
        )

        validate_project_manifest(
            updated,
            expected_project_id=project_id,
        )

        self._ensure_display_name_unique(
            updated.display_name,
            excluded_project_id=project_id,
        )

        project_path = self._project_path(project_id)
        manifest_path = project_path / PROJECT_MANIFEST_FILENAME
        temporary_manifest_path = project_path / (
            f"{PROJECT_MANIFEST_FILENAME}.tmp"
        )

        if (
            temporary_manifest_path.exists()
            or temporary_manifest_path.is_symlink()
        ):
            raise ProjectWorkspaceError(
                "Temporary manifest path already exists: "
                f"{temporary_manifest_path}."
            )

        serialized = project_manifest_to_json(updated)

        try:
            with temporary_manifest_path.open(
                "x",
                encoding="utf-8",
            ) as manifest_file:
                manifest_file.write(serialized)

            persisted_manifest = project_manifest_from_json(
                temporary_manifest_path.read_text(encoding="utf-8"),
                expected_project_id=project_id,
            )
        except OSError as exc:
            raise ProjectWorkspaceError(
                "Unable to persist temporary manifest "
                f"{temporary_manifest_path}: {exc}"
            ) from exc

        if persisted_manifest != updated:
            raise ProjectManifestError(
                "Persisted updated manifest differs from the "
                "validated manifest."
            )

        if manifest_path.is_symlink():
            raise UnsafeProjectPathError(
                f"Symbolic-link manifests are rejected: {manifest_path}."
            )

        try:
            os.replace(
                temporary_manifest_path,
                manifest_path,
            )
        except OSError as exc:
            raise ProjectWorkspaceError(
                f"Unable to replace project manifest {manifest_path}: "
                f"{exc}"
            ) from exc

        return updated

    def scan_projects(self) -> WorkspaceScanResult:
        """Discover valid projects and report all workspace issues."""

        if self.root.is_symlink():
            return WorkspaceScanResult(
                valid_projects=(),
                workspace_issues=(
                    WorkspaceIssue(
                        code="unsafe_workspace_root",
                        message=(
                            "Symbolic-link workspace roots are rejected."
                        ),
                        path=self.root,
                    ),
                ),
            )

        if not self.root.exists():
            return WorkspaceScanResult(
                valid_projects=(),
                workspace_issues=(),
            )

        if not self.root.is_dir():
            return WorkspaceScanResult(
                valid_projects=(),
                workspace_issues=(
                    WorkspaceIssue(
                        code="unsafe_workspace_root",
                        message=(
                            "Workspace root is not a directory."
                        ),
                        path=self.root,
                    ),
                ),
            )

        try:
            entries = sorted(
                self.root.iterdir(),
                key=lambda entry: entry.name,
            )
        except OSError as exc:
            return WorkspaceScanResult(
                valid_projects=(),
                workspace_issues=(
                    WorkspaceIssue(
                        code="workspace_read_error",
                        message=(
                            "Unable to inspect workspace root: "
                            f"{exc}"
                        ),
                        path=self.root,
                    ),
                ),
            )

        valid_projects: list[ProjectManifest] = []
        workspace_issues: list[WorkspaceIssue] = []

        for entry in entries:
            if entry.name.startswith("."):
                continue

            if entry.is_symlink():
                workspace_issues.append(
                    WorkspaceIssue(
                        code="unsafe_project_path",
                        message=(
                            "Symbolic-link workspace entries are "
                            "rejected."
                        ),
                        path=entry,
                        project_id=(
                            entry.name
                            if is_valid_project_id(entry.name)
                            else None
                        ),
                    )
                )
                continue

            if not entry.is_dir():
                workspace_issues.append(
                    WorkspaceIssue(
                        code="unexpected_workspace_entry",
                        message=(
                            "Visible workspace entry is not a "
                            "project directory."
                        ),
                        path=entry,
                    )
                )
                continue

            project_id = entry.name

            if not is_valid_project_id(project_id):
                workspace_issues.append(
                    WorkspaceIssue(
                        code="invalid_project_directory",
                        message=(
                            "Visible project directory name must "
                            "contain exactly six digits."
                        ),
                        path=entry,
                    )
                )
                continue

            try:
                manifest = self._load_manifest_from_directory(
                    project_id,
                    entry,
                )
            except UnsafeProjectPathError as exc:
                workspace_issues.append(
                    WorkspaceIssue(
                        code="unsafe_project_path",
                        message=str(exc),
                        path=entry,
                        project_id=project_id,
                    )
                )
                continue
            except ProjectManifestError as exc:
                workspace_issues.append(
                    WorkspaceIssue(
                        code="invalid_manifest",
                        message=str(exc),
                        path=(
                            entry / PROJECT_MANIFEST_FILENAME
                        ),
                        project_id=project_id,
                    )
                )
                continue

            valid_projects.append(manifest)

        workspace_issues.extend(
            self._duplicate_name_issues(valid_projects)
        )

        valid_projects.sort(
            key=lambda manifest: manifest.project_id
        )
        workspace_issues.sort(
            key=lambda issue: (
                str(issue.path),
                issue.code,
                issue.project_id or "",
            )
        )

        return WorkspaceScanResult(
            valid_projects=tuple(valid_projects),
            workspace_issues=tuple(workspace_issues),
        )

    def _generate_available_project_id(self) -> str:
        for _ in range(MAX_PROJECT_ID_GENERATION_ATTEMPTS):
            project_id = self._id_generator()

            if not is_valid_project_id(project_id):
                raise ProjectIdGenerationError(
                    "Project ID generator returned an invalid value: "
                    f"{project_id!r}."
                )

            project_path = self._project_path(project_id)
            temporary_path = self.root / (
                f".create-{project_id}.tmp"
            )

            project_exists = (
                project_path.exists()
                or project_path.is_symlink()
            )
            temporary_exists = (
                temporary_path.exists()
                or temporary_path.is_symlink()
            )

            if not project_exists and not temporary_exists:
                return project_id

        raise ProjectIdGenerationError(
            "Unable to generate an available project ID after "
            f"{MAX_PROJECT_ID_GENERATION_ATTEMPTS} attempts."
        )

    def _project_path(self, project_id: str) -> Path:
        if not is_valid_project_id(project_id):
            raise UnsafeProjectPathError(
                "project_id must be a string containing exactly "
                "six digits."
            )

        return self.root / project_id

    def _assert_workspace_root_safe(self) -> None:
        if self.root.is_symlink():
            raise UnsafeProjectPathError(
                f"Symbolic-link workspace roots are rejected: "
                f"{self.root}."
            )

        if self.root.exists() and not self.root.is_dir():
            raise UnsafeProjectPathError(
                f"Workspace root is not a directory: {self.root}."
            )

    def _load_manifest_from_directory(
        self,
        project_id: str,
        project_path: Path,
    ) -> ProjectManifest:
        if project_path.is_symlink():
            raise UnsafeProjectPathError(
                f"Symbolic-link project directories are rejected: "
                f"{project_path}."
            )

        manifest_path = project_path / PROJECT_MANIFEST_FILENAME

        if manifest_path.is_symlink():
            raise UnsafeProjectPathError(
                f"Symbolic-link manifests are rejected: "
                f"{manifest_path}."
            )

        if not manifest_path.exists():
            raise ProjectManifestError(
                f"Project manifest is missing: {manifest_path}."
            )

        if not manifest_path.is_file():
            raise ProjectManifestError(
                f"Project manifest is not a file: {manifest_path}."
            )

        try:
            text = manifest_path.read_text(encoding="utf-8")
        except OSError as exc:
            raise ProjectManifestError(
                f"Unable to read project manifest "
                f"{manifest_path}: {exc}"
            ) from exc

        return project_manifest_from_json(
            text,
            expected_project_id=project_id,
        )

    def _ensure_display_name_unique(
        self,
        display_name: str,
        *,
        excluded_project_id: str | None = None,
    ) -> None:
        normalized_name = normalize_display_name(display_name)
        scan_result = self.scan_projects()

        for manifest in scan_result.valid_projects:
            if manifest.project_id == excluded_project_id:
                continue

            if (
                normalize_display_name(manifest.display_name)
                == normalized_name
            ):
                raise DuplicateProjectNameError(
                    f"Project display name {display_name!r} conflicts "
                    f"with project {manifest.project_id!r}."
                )

    def _duplicate_name_issues(
        self,
        manifests: list[ProjectManifest],
    ) -> list[WorkspaceIssue]:
        projects_by_name: dict[
            str,
            list[ProjectManifest],
        ] = defaultdict(list)

        for manifest in manifests:
            projects_by_name[
                normalize_display_name(manifest.display_name)
            ].append(manifest)

        issues: list[WorkspaceIssue] = []

        for normalized_name in sorted(projects_by_name):
            conflicting_projects = projects_by_name[
                normalized_name
            ]

            if len(conflicting_projects) < 2:
                continue

            conflicting_ids = sorted(
                manifest.project_id
                for manifest in conflicting_projects
            )

            for manifest in conflicting_projects:
                issues.append(
                    WorkspaceIssue(
                        code="duplicate_project_name",
                        message=(
                            "Normalized display name conflicts with "
                            "projects: "
                            + ", ".join(conflicting_ids)
                            + "."
                        ),
                        path=(
                            self.root
                            / manifest.project_id
                            / PROJECT_MANIFEST_FILENAME
                        ),
                        project_id=manifest.project_id,
                    )
                )

        return issues

    def _current_utc_timestamp(self) -> str:
        value = self._clock()

        if not isinstance(value, datetime):
            raise ProjectWorkspaceError(
                "Project Workspace clock must return a datetime."
            )

        if value.tzinfo is None or value.utcoffset() is None:
            raise ProjectWorkspaceError(
                "Project Workspace clock must return a "
                "timezone-aware datetime."
            )

        utc_value = value.astimezone(timezone.utc)

        return (
            utc_value.isoformat(timespec="seconds")
            .replace("+00:00", "Z")
        )