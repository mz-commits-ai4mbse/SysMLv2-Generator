"""Persistent and isolated Project Source Registry operations."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
import re

from modules.project_workspace import ProjectWorkspace

from .errors import (
    DuplicateSourceContentError,
    ProjectSourceError,
    SourceIntegrityError,
    SourceManifestError,
    SourceNotFoundError,
    UnsafeSourcePathError,
)
from .identifiers import (
    next_source_id,
    validate_source_id,
)
from .manifest import (
    SOURCE_MANIFEST_FILENAME,
    create_source_manifest,
    source_manifest_from_json,
    source_manifest_to_json,
    update_source_role_manifest,
    validate_source_role,
)
from .types import (
    SourceIssue,
    SourceManifest,
    SourceScanResult,
)


DEFAULT_PROJECTS_ROOT = Path("data/projects")
COPY_CHUNK_SIZE = 1024 * 1024
MAX_SOURCE_REGISTRATION_ATTEMPTS = 1_000

_TEMP_REGISTRATION_PATTERN = re.compile(
    r"^\.register-(SRC-[0-9]{6})\.tmp$"
)


def _default_clock() -> datetime:
    return datetime.now(timezone.utc)


class ProjectSourceRegistry:
    """Register, validate and discover project-local original sources."""

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

    def register_source(
        self,
        project_id: str,
        source_path: Path | str,
        *,
        source_role: str,
    ) -> SourceManifest:
        """Atomically register one immutable source in a project."""

        self._workspace.load_project(project_id)
        validate_source_role(source_role)

        input_path = self._validate_input_file(source_path)
        input_size, input_sha256 = self._hash_file(input_path)

        if input_size <= 0:
            raise SourceIntegrityError(
                f"Source file must not be empty: {input_path}."
            )

        sources_path = self._sources_path(project_id)
        self._assert_sources_root_safe(sources_path)

        existing_scan = self.scan_sources(project_id)

        for manifest in existing_scan.valid_sources:
            if manifest.sha256 == input_sha256:
                raise DuplicateSourceContentError(
                    "Source content already exists in project "
                    f"{project_id!r} as {manifest.source_id!r}."
                )

        try:
            sources_path.mkdir(
                parents=False,
                exist_ok=True,
            )
        except OSError as exc:
            raise ProjectSourceError(
                f"Unable to create source root {sources_path}: {exc}"
            ) from exc

        self._assert_sources_root_safe(sources_path)

        for _ in range(MAX_SOURCE_REGISTRATION_ATTEMPTS):
            occupied_source_ids = self._occupied_source_ids(
                sources_path
            )
            source_id = next_source_id(occupied_source_ids)

            temporary_path = sources_path / (
                f".register-{source_id}.tmp"
            )
            final_path = sources_path / source_id

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
                raise ProjectSourceError(
                    "Unable to create temporary source directory "
                    f"{temporary_path}: {exc}"
                ) from exc

            timestamp = self._current_utc_timestamp()

            manifest = create_source_manifest(
                project_id,
                source_id,
                source_role,
                input_path.name,
                size_bytes=input_size,
                sha256=input_sha256,
                timestamp=timestamp,
            )

            temporary_content_path = (
                temporary_path / manifest.stored_filename
            )
            temporary_manifest_path = (
                temporary_path / SOURCE_MANIFEST_FILENAME
            )

            copied_size, copied_sha256 = self._copy_and_hash(
                input_path,
                temporary_content_path,
            )

            if (
                copied_size != input_size
                or copied_sha256 != input_sha256
            ):
                raise SourceIntegrityError(
                    "Source file changed while it was being "
                    f"registered: {input_path}."
                )

            serialized = source_manifest_to_json(manifest)

            try:
                with temporary_manifest_path.open(
                    "x",
                    encoding="utf-8",
                ) as manifest_file:
                    manifest_file.write(serialized)
            except OSError as exc:
                raise ProjectSourceError(
                    "Unable to persist temporary Source Manifest "
                    f"{temporary_manifest_path}: {exc}"
                ) from exc

            persisted_manifest = (
                self._load_manifest_and_validate_content(
                    project_id,
                    source_id,
                    temporary_path,
                )
            )

            if persisted_manifest != manifest:
                raise SourceManifestError(
                    "Persisted Source Manifest differs from the "
                    "validated manifest."
                )

            if final_path.exists() or final_path.is_symlink():
                continue

            try:
                temporary_path.rename(final_path)
            except FileExistsError:
                continue
            except OSError as exc:
                raise ProjectSourceError(
                    "Unable to finalize source directory "
                    f"{final_path}: {exc}"
                ) from exc

            return self.load_source(
                project_id,
                source_id,
            )

        raise ProjectSourceError(
            "Unable to allocate and finalize a Source ID after "
            f"{MAX_SOURCE_REGISTRATION_ATTEMPTS} attempts."
        )

    def load_source(
        self,
        project_id: str,
        source_id: str,
    ) -> SourceManifest:
        """Load and fully validate one registered source."""

        self._workspace.load_project(project_id)

        source_path = self._source_path(
            project_id,
            source_id,
        )

        if source_path.is_symlink():
            raise UnsafeSourcePathError(
                "Symbolic-link source directories are rejected: "
                f"{source_path}."
            )

        if not source_path.exists() or not source_path.is_dir():
            raise SourceNotFoundError(
                "Source was not found: "
                f"{project_id}/{source_id}."
            )

        return self._load_manifest_and_validate_content(
            project_id,
            source_id,
            source_path,
        )

    def source_content_path(
        self,
        project_id: str,
        source_id: str,
    ) -> Path:
        """Return the validated stored-content path for one source."""

        manifest = self.load_source(
            project_id,
            source_id,
        )
        source_path = self._source_path(
            project_id,
            source_id,
        )
        content_path = source_path / manifest.stored_filename

        self._assert_path_within(
            content_path,
            source_path,
        )

        return content_path

    def update_source_role(
        self,
        project_id: str,
        source_id: str,
        *,
        source_role: str,
    ) -> SourceManifest:
        """Atomically correct a source role before dependent runs exist."""

        current = self.load_source(
            project_id,
            source_id,
        )
        validated_role = validate_source_role(source_role)

        if validated_role == current.source_role:
            return current

        updated = update_source_role_manifest(
            current,
            validated_role,
            timestamp=self._current_utc_timestamp(),
        )

        source_path = self._source_path(
            project_id,
            source_id,
        )
        manifest_path = (
            source_path / SOURCE_MANIFEST_FILENAME
        )
        temporary_manifest_path = source_path / (
            f"{SOURCE_MANIFEST_FILENAME}.tmp"
        )

        if (
            temporary_manifest_path.exists()
            or temporary_manifest_path.is_symlink()
        ):
            raise ProjectSourceError(
                "Temporary Source Manifest path already exists: "
                f"{temporary_manifest_path}."
            )

        serialized = source_manifest_to_json(updated)

        try:
            with temporary_manifest_path.open(
                "x",
                encoding="utf-8",
            ) as manifest_file:
                manifest_file.write(serialized)

            persisted_manifest = source_manifest_from_json(
                temporary_manifest_path.read_text(
                    encoding="utf-8"
                ),
                expected_project_id=project_id,
                expected_source_id=source_id,
            )
        except OSError as exc:
            raise ProjectSourceError(
                "Unable to persist temporary Source Manifest "
                f"{temporary_manifest_path}: {exc}"
            ) from exc

        if persisted_manifest != updated:
            raise SourceManifestError(
                "Persisted updated Source Manifest differs from "
                "the validated manifest."
            )

        if manifest_path.is_symlink():
            raise UnsafeSourcePathError(
                "Symbolic-link Source Manifests are rejected: "
                f"{manifest_path}."
            )

        try:
            os.replace(
                temporary_manifest_path,
                manifest_path,
            )
        except OSError as exc:
            raise ProjectSourceError(
                "Unable to replace Source Manifest "
                f"{manifest_path}: {exc}"
            ) from exc

        return self.load_source(
            project_id,
            source_id,
        )

    def scan_sources(
        self,
        project_id: str,
    ) -> SourceScanResult:
        """Discover valid project sources and explicit source issues."""

        self._workspace.load_project(project_id)

        sources_path = self._sources_path(project_id)

        if sources_path.is_symlink():
            return SourceScanResult(
                valid_sources=(),
                source_issues=(
                    SourceIssue(
                        project_id=project_id,
                        code="unsafe_sources_root",
                        message=(
                            "Symbolic-link source roots are rejected."
                        ),
                        path=sources_path,
                    ),
                ),
            )

        if not sources_path.exists():
            return SourceScanResult()

        if not sources_path.is_dir():
            return SourceScanResult(
                valid_sources=(),
                source_issues=(
                    SourceIssue(
                        project_id=project_id,
                        code="unsafe_sources_root",
                        message=(
                            "Project source root is not a directory."
                        ),
                        path=sources_path,
                    ),
                ),
            )

        try:
            entries = sorted(
                sources_path.iterdir(),
                key=lambda entry: entry.name,
            )
        except OSError as exc:
            return SourceScanResult(
                valid_sources=(),
                source_issues=(
                    SourceIssue(
                        project_id=project_id,
                        code="source_root_read_error",
                        message=(
                            "Unable to inspect project source root: "
                            f"{exc}"
                        ),
                        path=sources_path,
                    ),
                ),
            )

        valid_sources: list[SourceManifest] = []
        source_issues: list[SourceIssue] = []

        for entry in entries:
            if entry.name.startswith("."):
                continue

            candidate_source_id = (
                entry.name
                if self._is_valid_source_id(entry.name)
                else None
            )

            if entry.is_symlink():
                source_issues.append(
                    SourceIssue(
                        project_id=project_id,
                        source_id=candidate_source_id,
                        code="unsafe_source_path",
                        message=(
                            "Symbolic-link source entries are "
                            "rejected."
                        ),
                        path=entry,
                    )
                )
                continue

            if not entry.is_dir():
                source_issues.append(
                    SourceIssue(
                        project_id=project_id,
                        source_id=candidate_source_id,
                        code="unexpected_source_entry",
                        message=(
                            "Visible source entry is not a "
                            "source directory."
                        ),
                        path=entry,
                    )
                )
                continue

            if candidate_source_id is None:
                source_issues.append(
                    SourceIssue(
                        project_id=project_id,
                        code="invalid_source_directory",
                        message=(
                            "Visible source directory name must "
                            "match ^SRC-[0-9]{6}$ and use a "
                            "sequence from 000001 to 999999."
                        ),
                        path=entry,
                    )
                )
                continue

            try:
                manifest = (
                    self._load_manifest_and_validate_content(
                        project_id,
                        candidate_source_id,
                        entry,
                    )
                )
            except UnsafeSourcePathError as exc:
                source_issues.append(
                    SourceIssue(
                        project_id=project_id,
                        source_id=candidate_source_id,
                        code="unsafe_source_path",
                        message=str(exc),
                        path=entry,
                    )
                )
                continue
            except SourceIntegrityError as exc:
                source_issues.append(
                    SourceIssue(
                        project_id=project_id,
                        source_id=candidate_source_id,
                        code="source_integrity_error",
                        message=str(exc),
                        path=entry,
                    )
                )
                continue
            except SourceManifestError as exc:
                source_issues.append(
                    SourceIssue(
                        project_id=project_id,
                        source_id=candidate_source_id,
                        code="invalid_source_manifest",
                        message=str(exc),
                        path=(
                            entry / SOURCE_MANIFEST_FILENAME
                        ),
                    )
                )
                continue
            except ProjectSourceError as exc:
                source_issues.append(
                    SourceIssue(
                        project_id=project_id,
                        source_id=candidate_source_id,
                        code="source_read_error",
                        message=str(exc),
                        path=entry,
                    )
                )
                continue

            valid_sources.append(manifest)

        duplicate_issues, conflicting_source_ids = (
            self._duplicate_content_issues(
                project_id,
                valid_sources,
            )
        )
        source_issues.extend(duplicate_issues)

        valid_sources = [
            manifest
            for manifest in valid_sources
            if manifest.source_id not in conflicting_source_ids
        ]

        valid_sources.sort(
            key=lambda manifest: manifest.source_id
        )
        source_issues.sort(
            key=lambda issue: (
                str(issue.path),
                issue.code,
                issue.source_id or "",
            )
        )

        return SourceScanResult(
            valid_sources=tuple(valid_sources),
            source_issues=tuple(source_issues),
        )

    def _load_manifest_and_validate_content(
        self,
        project_id: str,
        source_id: str,
        source_path: Path,
    ) -> SourceManifest:
        if source_path.is_symlink():
            raise UnsafeSourcePathError(
                "Symbolic-link source directories are rejected: "
                f"{source_path}."
            )

        if not source_path.exists() or not source_path.is_dir():
            raise SourceNotFoundError(
                "Source directory was not found: "
                f"{source_path}."
            )

        self._assert_path_within(
            source_path,
            self._project_path(project_id),
        )

        manifest_path = (
            source_path / SOURCE_MANIFEST_FILENAME
        )

        if manifest_path.is_symlink():
            raise UnsafeSourcePathError(
                "Symbolic-link Source Manifests are rejected: "
                f"{manifest_path}."
            )

        if not manifest_path.exists():
            raise SourceManifestError(
                f"Source Manifest is missing: {manifest_path}."
            )

        if not manifest_path.is_file():
            raise SourceManifestError(
                "Source Manifest is not a file: "
                f"{manifest_path}."
            )

        try:
            manifest_text = manifest_path.read_text(
                encoding="utf-8"
            )
        except OSError as exc:
            raise ProjectSourceError(
                "Unable to read Source Manifest "
                f"{manifest_path}: {exc}"
            ) from exc

        manifest = source_manifest_from_json(
            manifest_text,
            expected_project_id=project_id,
            expected_source_id=source_id,
        )

        content_path = (
            source_path / manifest.stored_filename
        )

        self._assert_path_within(
            content_path,
            source_path,
        )

        if content_path.is_symlink():
            raise UnsafeSourcePathError(
                "Symbolic-link source content is rejected: "
                f"{content_path}."
            )

        if not content_path.exists():
            raise SourceIntegrityError(
                f"Stored source content is missing: {content_path}."
            )

        if not content_path.is_file():
            raise SourceIntegrityError(
                "Stored source content is not a regular file: "
                f"{content_path}."
            )

        self._validate_source_directory_entries(
            source_path,
            manifest.stored_filename,
        )

        actual_size, actual_sha256 = self._hash_file(
            content_path
        )

        if actual_size != manifest.size_bytes:
            raise SourceIntegrityError(
                "Stored source size does not match its manifest: "
                f"{actual_size} != {manifest.size_bytes}."
            )

        if actual_sha256 != manifest.sha256:
            raise SourceIntegrityError(
                "Stored source SHA-256 does not match its "
                f"manifest for {project_id}/{source_id}."
            )

        return manifest

    def _validate_source_directory_entries(
        self,
        source_path: Path,
        stored_filename: str,
    ) -> None:
        expected_names = {
            SOURCE_MANIFEST_FILENAME,
            stored_filename,
        }

        try:
            entries = tuple(source_path.iterdir())
        except OSError as exc:
            raise ProjectSourceError(
                "Unable to inspect source directory "
                f"{source_path}: {exc}"
            ) from exc

        unexpected_names = sorted(
            entry.name
            for entry in entries
            if not entry.name.startswith(".")
            and entry.name not in expected_names
        )

        if unexpected_names:
            raise SourceManifestError(
                "Source directory contains unexpected entries: "
                + ", ".join(unexpected_names)
                + "."
            )

    def _duplicate_content_issues(
        self,
        project_id: str,
        manifests: list[SourceManifest],
    ) -> tuple[list[SourceIssue], set[str]]:
        sources_by_sha256: dict[
            str,
            list[SourceManifest],
        ] = defaultdict(list)

        for manifest in manifests:
            sources_by_sha256[manifest.sha256].append(manifest)

        issues: list[SourceIssue] = []
        conflicting_source_ids: set[str] = set()

        for sha256 in sorted(sources_by_sha256):
            conflicting_sources = sources_by_sha256[sha256]

            if len(conflicting_sources) < 2:
                continue

            conflicting_ids = sorted(
                manifest.source_id
                for manifest in conflicting_sources
            )
            conflicting_source_ids.update(conflicting_ids)

            for manifest in conflicting_sources:
                issues.append(
                    SourceIssue(
                        project_id=project_id,
                        source_id=manifest.source_id,
                        code="duplicate_source_content",
                        message=(
                            "Source content SHA-256 conflicts "
                            "with sources: "
                            + ", ".join(conflicting_ids)
                            + "."
                        ),
                        path=(
                            self._source_path(
                                project_id,
                                manifest.source_id,
                            )
                            / SOURCE_MANIFEST_FILENAME
                        ),
                    )
                )

        return issues, conflicting_source_ids

    def _occupied_source_ids(
        self,
        sources_path: Path,
    ) -> tuple[str, ...]:
        try:
            entries = tuple(sources_path.iterdir())
        except OSError as exc:
            raise ProjectSourceError(
                "Unable to inspect source identifiers in "
                f"{sources_path}: {exc}"
            ) from exc

        occupied: set[str] = set()

        for entry in entries:
            if self._is_valid_source_id(entry.name):
                occupied.add(entry.name)
                continue

            temporary_match = (
                _TEMP_REGISTRATION_PATTERN.fullmatch(entry.name)
            )

            if temporary_match is None:
                continue

            temporary_source_id = temporary_match.group(1)

            if self._is_valid_source_id(temporary_source_id):
                occupied.add(temporary_source_id)

        return tuple(sorted(occupied))

    def _validate_input_file(
        self,
        source_path: Path | str,
    ) -> Path:
        try:
            input_path = Path(source_path)
        except TypeError as exc:
            raise UnsafeSourcePathError(
                "source_path must be a filesystem path."
            ) from exc

        if input_path.is_symlink():
            raise UnsafeSourcePathError(
                "Symbolic-link input sources are rejected: "
                f"{input_path}."
            )

        if not input_path.exists():
            raise UnsafeSourcePathError(
                f"Input source does not exist: {input_path}."
            )

        if not input_path.is_file():
            raise UnsafeSourcePathError(
                "Input source must be a regular file: "
                f"{input_path}."
            )

        if not input_path.name:
            raise UnsafeSourcePathError(
                "Input source must have a filename."
            )

        return input_path

    def _copy_and_hash(
        self,
        source_path: Path,
        destination_path: Path,
    ) -> tuple[int, str]:
        digest = hashlib.sha256()
        size_bytes = 0

        try:
            with source_path.open("rb") as source_file:
                with destination_path.open("xb") as destination_file:
                    while True:
                        chunk = source_file.read(COPY_CHUNK_SIZE)

                        if not chunk:
                            break

                        destination_file.write(chunk)
                        digest.update(chunk)
                        size_bytes += len(chunk)
        except OSError as exc:
            raise ProjectSourceError(
                "Unable to copy source content from "
                f"{source_path} to {destination_path}: {exc}"
            ) from exc

        return size_bytes, digest.hexdigest()

    def _hash_file(
        self,
        path: Path,
    ) -> tuple[int, str]:
        digest = hashlib.sha256()
        size_bytes = 0

        try:
            with path.open("rb") as source_file:
                while True:
                    chunk = source_file.read(COPY_CHUNK_SIZE)

                    if not chunk:
                        break

                    digest.update(chunk)
                    size_bytes += len(chunk)
        except OSError as exc:
            raise ProjectSourceError(
                f"Unable to read source content {path}: {exc}"
            ) from exc

        return size_bytes, digest.hexdigest()

    def _sources_path(
        self,
        project_id: str,
    ) -> Path:
        return self._project_path(project_id) / "sources"

    def _source_path(
        self,
        project_id: str,
        source_id: str,
    ) -> Path:
        try:
            validated_source_id = validate_source_id(source_id)
        except SourceManifestError as exc:
            raise UnsafeSourcePathError(
                "source_id must match ^SRC-[0-9]{6}$ and "
                "use a sequence from 000001 to 999999."
            ) from exc

        source_path = (
            self._sources_path(project_id)
            / validated_source_id
        )

        self._assert_path_within(
            source_path,
            self._project_path(project_id),
        )

        return source_path

    def _project_path(
        self,
        project_id: str,
    ) -> Path:
        project_manifest = self._workspace.load_project(
            project_id
        )
        return self.root / project_manifest.project_id

    def _assert_sources_root_safe(
        self,
        sources_path: Path,
    ) -> None:
        if sources_path.is_symlink():
            raise UnsafeSourcePathError(
                "Symbolic-link source roots are rejected: "
                f"{sources_path}."
            )

        if sources_path.exists() and not sources_path.is_dir():
            raise UnsafeSourcePathError(
                "Project source root is not a directory: "
                f"{sources_path}."
            )

        self._assert_path_within(
            sources_path,
            sources_path.parent,
        )

    def _assert_path_within(
        self,
        path: Path,
        parent: Path,
    ) -> None:
        try:
            path.resolve(strict=False).relative_to(
                parent.resolve(strict=False)
            )
        except ValueError as exc:
            raise UnsafeSourcePathError(
                f"Path escapes its permitted parent: {path}."
            ) from exc

    def _is_valid_source_id(
        self,
        value: str,
    ) -> bool:
        try:
            validate_source_id(value)
        except SourceManifestError:
            return False

        return True

    def _current_utc_timestamp(self) -> str:
        value = self._clock()

        if not isinstance(value, datetime):
            raise ProjectSourceError(
                "Project Source Registry clock must return "
                "a datetime."
            )

        if value.tzinfo is None or value.utcoffset() is None:
            raise ProjectSourceError(
                "Project Source Registry clock must return "
                "a timezone-aware datetime."
            )

        utc_value = value.astimezone(timezone.utc)

        return (
            utc_value.isoformat(timespec="seconds")
            .replace("+00:00", "Z")
        )