"""Persistent project-local Source Projection repository."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
import re
import shutil

from modules.project_sources import (
    ProjectSourceRegistry,
    SourceManifest,
)
from modules.project_workspace import ProjectWorkspace

from .errors import (
    SourceProjectionError,
    SourceProjectionIntegrityError,
    SourceProjectionManifestError,
    SourceProjectionNotFoundError,
    UnsupportedSourceFormatError,
    UnsafeSourceProjectionPathError,
)
from .identifiers import (
    next_source_projection_id,
    validate_source_projection_id,
)
from .json_adapter import project_json
from .manifest import (
    SOURCE_PROJECTION_CONTENT_FILENAME,
    SOURCE_PROJECTION_MANIFEST_FILENAME,
    create_source_projection_artifact,
    source_projection_artifact_from_json,
    source_projection_manifest_to_json,
)
from .pdf_adapter import project_pdf
from .table_adapter import (
    project_csv,
    project_tsv,
)
from .text_adapter import (
    project_markdown,
    project_plain_text,
)
from .types import (
    SourceProjectionArtifact,
    SourceProjectionDraft,
)


DEFAULT_PROJECTS_ROOT = Path("data/projects")
MAX_PROJECTION_CREATION_ATTEMPTS = 1_000

_SUPPORTED_SOURCE_SUFFIXES = frozenset(
    {
        ".txt",
        ".md",
        ".json",
        ".csv",
        ".tsv",
        ".pdf",
    }
)

_TEMPORARY_PROJECTION_PATTERN = re.compile(
    r"^\.create-(SP-[0-9]{6})\.tmp$"
)


def _default_clock() -> datetime:
    return datetime.now(timezone.utc)


class SourceProjectionRepository:
    """Create, reopen and validate project-local Source Projections."""

    def __init__(
        self,
        root: Path | str = DEFAULT_PROJECTS_ROOT,
        *,
        clock: Callable[[], datetime] = _default_clock,
    ) -> None:
        self.root = Path(root)
        self._clock = clock
        self._workspace = ProjectWorkspace(
            root=self.root,
            clock=clock,
        )
        self._source_registry = ProjectSourceRegistry(
            root=self.root,
            clock=clock,
        )

    def create_projection(
        self,
        project_id: str,
        source_id: str,
    ) -> SourceProjectionArtifact:
        """Create or reuse one deterministic Source Projection."""

        self._workspace.load_project(project_id)

        source_manifest = self._source_registry.load_source(
            project_id,
            source_id,
        )
        source_content_path = (
            self._source_registry.source_content_path(
                project_id,
                source_id,
            )
        )

        try:
            source_content = source_content_path.read_bytes()
        except OSError as exc:
            raise SourceProjectionError(
                "Unable to read registered source content "
                f"{source_content_path}: {exc}"
            ) from exc

        draft = self._project_source(
            source_manifest,
            source_content,
        )
        timestamp = self._current_utc_timestamp()

        preview = create_source_projection_artifact(
            project_id=project_id,
            source_id=source_manifest.source_id,
            source_projection_id="SP-000001",
            source_role=source_manifest.source_role,
            source_sha256=source_manifest.sha256,
            draft=draft,
            timestamp=timestamp,
        )

        reusable = self._find_reusable_projection(
            project_id=project_id,
            source_manifest=source_manifest,
            preview=preview,
        )

        if reusable is not None:
            return reusable

        projections_root = self._projections_root(
            project_id
        )
        self._prepare_projection_root(
            projections_root
        )

        for _ in range(
            MAX_PROJECTION_CREATION_ATTEMPTS
        ):
            occupied_ids = self._occupied_projection_ids(
                projections_root
            )
            source_projection_id = (
                next_source_projection_id(
                    occupied_ids
                )
            )

            temporary_path = projections_root / (
                f".create-{source_projection_id}.tmp"
            )
            final_path = (
                projections_root
                / source_projection_id
            )

            if (
                temporary_path.exists()
                or temporary_path.is_symlink()
            ):
                continue

            try:
                temporary_path.mkdir()
            except FileExistsError:
                continue
            except OSError as exc:
                raise SourceProjectionError(
                    "Unable to create temporary Source "
                    f"Projection directory {temporary_path}: "
                    f"{exc}"
                ) from exc

            try:
                artifact = (
                    create_source_projection_artifact(
                        project_id=project_id,
                        source_id=source_manifest.source_id,
                        source_projection_id=(
                            source_projection_id
                        ),
                        source_role=source_manifest.source_role,
                        source_sha256=source_manifest.sha256,
                        draft=draft,
                        timestamp=timestamp,
                    )
                )

                self._write_temporary_artifact(
                    temporary_path,
                    artifact,
                )

                persisted = (
                    self._load_artifact_from_directory(
                        project_id=project_id,
                        source_projection_id=(
                            source_projection_id
                        ),
                        projection_path=temporary_path,
                        validate_registered_source=True,
                    )
                )

                if persisted != artifact:
                    raise SourceProjectionIntegrityError(
                        "Persisted Source Projection differs "
                        "from the validated artifact."
                    )

                if final_path.exists() or final_path.is_symlink():
                    continue

                try:
                    temporary_path.rename(final_path)
                except FileExistsError:
                    continue
                except OSError as exc:
                    raise SourceProjectionError(
                        "Unable to finalize Source Projection "
                        f"directory {final_path}: {exc}"
                    ) from exc

                return self.load_projection(
                    project_id,
                    source_projection_id,
                )
            finally:
                self._remove_temporary_directory(
                    temporary_path
                )

        raise SourceProjectionError(
            "Unable to allocate and finalize a Source "
            "Projection ID after "
            f"{MAX_PROJECTION_CREATION_ATTEMPTS} attempts."
        )

    def load_projection(
        self,
        project_id: str,
        source_projection_id: str,
    ) -> SourceProjectionArtifact:
        """Load and fully validate one persisted projection."""

        self._workspace.load_project(project_id)

        projection_path = self._projection_path(
            project_id,
            source_projection_id,
        )

        if projection_path.is_symlink():
            raise UnsafeSourceProjectionPathError(
                "Symbolic-link Source Projection directories "
                f"are rejected: {projection_path}."
            )

        if (
            not projection_path.exists()
            or not projection_path.is_dir()
        ):
            raise SourceProjectionNotFoundError(
                "Source Projection was not found: "
                f"{project_id}/{source_projection_id}."
            )

        return self._load_artifact_from_directory(
            project_id=project_id,
            source_projection_id=source_projection_id,
            projection_path=projection_path,
            validate_registered_source=True,
        )

    def list_projections(
        self,
        project_id: str,
        *,
        source_id: str | None = None,
    ) -> tuple[SourceProjectionArtifact, ...]:
        """Return valid projections in identifier order."""

        self._workspace.load_project(project_id)

        if source_id is not None:
            self._source_registry.load_source(
                project_id,
                source_id,
            )

        projections_root = self._projections_root(
            project_id
        )
        self._assert_projection_root_safe(
            projections_root
        )

        if not projections_root.exists():
            return ()

        projection_ids: list[str] = []

        for entry in projections_root.iterdir():
            if entry.name.startswith("."):
                continue

            try:
                projection_id = (
                    validate_source_projection_id(
                        entry.name
                    )
                )
            except Exception as exc:
                raise SourceProjectionIntegrityError(
                    "Unexpected visible entry in Source "
                    f"Projection root: {entry}."
                ) from exc

            if not entry.is_dir() or entry.is_symlink():
                raise UnsafeSourceProjectionPathError(
                    "Source Projection entries must be "
                    f"regular directories: {entry}."
                )

            projection_ids.append(projection_id)

        artifacts = tuple(
            self.load_projection(
                project_id,
                projection_id,
            )
            for projection_id in sorted(
                projection_ids
            )
        )

        if source_id is None:
            return artifacts

        return tuple(
            artifact
            for artifact in artifacts
            if artifact.manifest.source_id == source_id
        )

    def projection_content_path(
        self,
        project_id: str,
        source_projection_id: str,
    ) -> Path:
        """Return the validated projected-content path."""

        self.load_projection(
            project_id,
            source_projection_id,
        )

        projection_path = self._projection_path(
            project_id,
            source_projection_id,
        )
        content_path = (
            projection_path
            / SOURCE_PROJECTION_CONTENT_FILENAME
        )

        self._assert_path_within(
            content_path,
            projection_path,
        )

        return content_path

    def _project_source(
        self,
        source_manifest: SourceManifest,
        content: bytes,
    ) -> SourceProjectionDraft:
        suffix = Path(
            source_manifest.original_filename
        ).suffix.lower()

        if suffix == ".txt":
            return project_plain_text(content)

        if suffix == ".md":
            return project_markdown(content)

        if suffix == ".json":
            return project_json(content)

        if suffix == ".csv":
            return project_csv(content)

        if suffix == ".tsv":
            return project_tsv(content)

        if suffix == ".pdf":
            return project_pdf(content)

        supported = ", ".join(
            sorted(_SUPPORTED_SOURCE_SUFFIXES)
        )
        raise UnsupportedSourceFormatError(
            "No deterministic Source Projection adapter "
            f"supports {source_manifest.original_filename!r}. "
            f"Supported suffixes: {supported}."
        )

    def _find_reusable_projection(
        self,
        *,
        project_id: str,
        source_manifest: SourceManifest,
        preview: SourceProjectionArtifact,
    ) -> SourceProjectionArtifact | None:
        existing = self.list_projections(
            project_id,
            source_id=source_manifest.source_id,
        )

        for artifact in existing:
            manifest = artifact.manifest

            if (
                manifest.source_role
                == source_manifest.source_role
                and manifest.source_sha256
                == source_manifest.sha256
                and manifest.projection_fingerprint
                == preview.manifest.projection_fingerprint
                and manifest.projection_result
                == preview.manifest.projection_result
                and manifest.content_sha256
                == preview.manifest.content_sha256
            ):
                return artifact

        return None

    def _write_temporary_artifact(
        self,
        temporary_path: Path,
        artifact: SourceProjectionArtifact,
    ) -> None:
        manifest_path = (
            temporary_path
            / SOURCE_PROJECTION_MANIFEST_FILENAME
        )
        content_path = (
            temporary_path
            / SOURCE_PROJECTION_CONTENT_FILENAME
        )

        try:
            with manifest_path.open(
                "x",
                encoding="utf-8",
            ) as manifest_file:
                manifest_file.write(
                    source_projection_manifest_to_json(
                        artifact.manifest
                    )
                )

            with content_path.open(
                "x",
                encoding="utf-8",
                newline="",
            ) as content_file:
                content_file.write(artifact.content)
        except OSError as exc:
            raise SourceProjectionError(
                "Unable to persist temporary Source "
                f"Projection {temporary_path}: {exc}"
            ) from exc

    def _load_artifact_from_directory(
        self,
        *,
        project_id: str,
        source_projection_id: str,
        projection_path: Path,
        validate_registered_source: bool,
    ) -> SourceProjectionArtifact:
        self._assert_path_within(
            projection_path,
            self._project_path(project_id),
        )

        if projection_path.is_symlink():
            raise UnsafeSourceProjectionPathError(
                "Symbolic-link Source Projection directories "
                f"are rejected: {projection_path}."
            )

        expected_visible_entries = {
            SOURCE_PROJECTION_MANIFEST_FILENAME,
            SOURCE_PROJECTION_CONTENT_FILENAME,
        }

        try:
            visible_entries = {
                entry.name
                for entry in projection_path.iterdir()
                if not entry.name.startswith(".")
            }
        except OSError as exc:
            raise SourceProjectionIntegrityError(
                "Unable to inspect Source Projection "
                f"directory {projection_path}: {exc}"
            ) from exc

        if visible_entries != expected_visible_entries:
            missing = sorted(
                expected_visible_entries
                - visible_entries
            )
            unexpected = sorted(
                visible_entries
                - expected_visible_entries
            )
            raise SourceProjectionIntegrityError(
                "Source Projection directory entries are "
                f"invalid; missing={missing}, "
                f"unexpected={unexpected}."
            )

        manifest_path = (
            projection_path
            / SOURCE_PROJECTION_MANIFEST_FILENAME
        )
        content_path = (
            projection_path
            / SOURCE_PROJECTION_CONTENT_FILENAME
        )

        for artifact_path in (
            manifest_path,
            content_path,
        ):
            if artifact_path.is_symlink():
                raise UnsafeSourceProjectionPathError(
                    "Symbolic-link Source Projection files "
                    f"are rejected: {artifact_path}."
                )

            if (
                not artifact_path.exists()
                or not artifact_path.is_file()
            ):
                raise SourceProjectionIntegrityError(
                    "Required Source Projection file is "
                    f"missing: {artifact_path}."
                )

        try:
            manifest_text = manifest_path.read_text(
                encoding="utf-8"
            )
            content = content_path.read_text(
                encoding="utf-8"
            )
        except UnicodeDecodeError as exc:
            raise SourceProjectionIntegrityError(
                "Source Projection files must use UTF-8."
            ) from exc
        except OSError as exc:
            raise SourceProjectionIntegrityError(
                "Unable to read Source Projection files: "
                f"{exc}"
            ) from exc

        try:
            artifact = source_projection_artifact_from_json(
                manifest_text,
                content,
                expected_project_id=project_id,
                expected_source_projection_id=(
                    source_projection_id
                ),
            )
        except SourceProjectionManifestError as exc:
            raise SourceProjectionIntegrityError(
                "Persisted Source Projection Manifest "
                f"is invalid: {exc}"
            ) from exc

        if validate_registered_source:
            source_manifest = (
                self._source_registry.load_source(
                    project_id,
                    artifact.manifest.source_id,
                )
            )

            if (
                artifact.manifest.source_sha256
                != source_manifest.sha256
            ):
                raise SourceProjectionIntegrityError(
                    "Source Projection source_sha256 does not "
                    "match the registered source."
                )

        return artifact

    def _prepare_projection_root(
        self,
        projections_root: Path,
    ) -> None:
        semantics_root = projections_root.parent

        self._assert_semantics_root_safe(
            semantics_root
        )

        try:
            semantics_root.mkdir(
                parents=False,
                exist_ok=True,
            )
        except OSError as exc:
            raise SourceProjectionError(
                "Unable to create semantic root "
                f"{semantics_root}: {exc}"
            ) from exc

        self._assert_semantics_root_safe(
            semantics_root
        )

        try:
            projections_root.mkdir(
                parents=False,
                exist_ok=True,
            )
        except OSError as exc:
            raise SourceProjectionError(
                "Unable to create Source Projection root "
                f"{projections_root}: {exc}"
            ) from exc

        self._assert_projection_root_safe(
            projections_root
        )

    def _occupied_projection_ids(
        self,
        projections_root: Path,
    ) -> tuple[str, ...]:
        occupied: set[str] = set()

        for entry in projections_root.iterdir():
            try:
                occupied.add(
                    validate_source_projection_id(
                        entry.name
                    )
                )
                continue
            except Exception:
                pass

            temporary_match = (
                _TEMPORARY_PROJECTION_PATTERN.fullmatch(
                    entry.name
                )
            )

            if temporary_match is not None:
                occupied.add(
                    validate_source_projection_id(
                        temporary_match.group(1)
                    )
                )
                continue

            if entry.name.startswith("."):
                continue

            raise SourceProjectionIntegrityError(
                "Unexpected visible entry in Source "
                f"Projection root: {entry}."
            )

        return tuple(sorted(occupied))

    def _projections_root(
        self,
        project_id: str,
    ) -> Path:
        return (
            self._project_path(project_id)
            / "semantics"
            / "source_projections"
        )

    def _projection_path(
        self,
        project_id: str,
        source_projection_id: str,
    ) -> Path:
        try:
            validated_projection_id = (
                validate_source_projection_id(
                    source_projection_id
                )
            )
        except Exception as exc:
            raise UnsafeSourceProjectionPathError(
                "source_projection_id must match "
                "^SP-[0-9]{6}$ and use a sequence from "
                "000001 to 999999."
            ) from exc

        projection_path = (
            self._projections_root(project_id)
            / validated_projection_id
        )

        self._assert_path_within(
            projection_path,
            self._project_path(project_id),
        )

        return projection_path

    def _project_path(
        self,
        project_id: str,
    ) -> Path:
        project_manifest = self._workspace.load_project(
            project_id
        )
        return self.root / project_manifest.project_id

    def _assert_semantics_root_safe(
        self,
        semantics_root: Path,
    ) -> None:
        if semantics_root.is_symlink():
            raise UnsafeSourceProjectionPathError(
                "Symbolic-link semantic roots are rejected: "
                f"{semantics_root}."
            )

        if (
            semantics_root.exists()
            and not semantics_root.is_dir()
        ):
            raise UnsafeSourceProjectionPathError(
                "Project semantic root is not a directory: "
                f"{semantics_root}."
            )

        self._assert_path_within(
            semantics_root,
            self._project_path(
                semantics_root.parent.name
            ),
        )

    def _assert_projection_root_safe(
        self,
        projections_root: Path,
    ) -> None:
        if projections_root.is_symlink():
            raise UnsafeSourceProjectionPathError(
                "Symbolic-link Source Projection roots "
                f"are rejected: {projections_root}."
            )

        if (
            projections_root.exists()
            and not projections_root.is_dir()
        ):
            raise UnsafeSourceProjectionPathError(
                "Source Projection root is not a directory: "
                f"{projections_root}."
            )

        self._assert_path_within(
            projections_root,
            projections_root.parent,
        )

    def _assert_path_within(
        self,
        path: Path,
        parent: Path,
    ) -> None:
        try:
            path.resolve(
                strict=False
            ).relative_to(
                parent.resolve(strict=False)
            )
        except ValueError as exc:
            raise UnsafeSourceProjectionPathError(
                "Path escapes its permitted parent: "
                f"{path}."
            ) from exc

    def _remove_temporary_directory(
        self,
        temporary_path: Path,
    ) -> None:
        if (
            not temporary_path.exists()
            and not temporary_path.is_symlink()
        ):
            return

        if temporary_path.is_symlink():
            raise UnsafeSourceProjectionPathError(
                "Refusing to remove symbolic-link temporary "
                f"projection path: {temporary_path}."
            )

        try:
            shutil.rmtree(temporary_path)
        except OSError as exc:
            raise SourceProjectionError(
                "Unable to remove temporary Source "
                f"Projection directory {temporary_path}: "
                f"{exc}"
            ) from exc

    def _current_utc_timestamp(self) -> str:
        value = self._clock()

        if not isinstance(value, datetime):
            raise SourceProjectionError(
                "Source Projection Repository clock must "
                "return a datetime."
            )

        if value.tzinfo is None:
            raise SourceProjectionError(
                "Source Projection Repository clock must "
                "return a timezone-aware datetime."
            )

        utc_value = value.astimezone(timezone.utc)

        return utc_value.isoformat().replace(
            "+00:00",
            "Z",
        )