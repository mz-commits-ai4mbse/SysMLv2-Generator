"""Atomic immutable persistence for final published output packages."""

from __future__ import annotations

from collections.abc import Mapping
import hashlib
import os
from pathlib import Path, PurePosixPath
import re
import uuid

from .errors import (
    OutputPublicationIntegrityError,
    OutputPublicationNotFoundError,
    OutputPublicationPersistenceError,
)
from .identifiers import validate_output_package_id
from .manifest import (
    published_output_manifest_from_json,
    published_output_manifest_to_json,
    validate_published_output_manifest,
)
from .paths import (
    DEFAULT_OUTPUT_ROOT,
    output_manifest_path,
    output_package_path,
    output_project_path,
)
from .types import (
    OutputPublicationRepositoryIssue,
    OutputPublicationRepositoryScanResult,
    PublishedOutputManifest,
    PublishedOutputPackage,
)


_OUTPUT_DIR = re.compile(r"^(OUT-[0-9]{6})$")
_TEMP_DIR = re.compile(r"^\.OUT-[0-9]{6}\.tmp-[A-Za-z0-9-]+$")


class OutputPublicationRepository:
    """Persist and verify authoritative immutable OUT packages."""

    def __init__(
        self,
        output_root: Path | str = DEFAULT_OUTPUT_ROOT,
        *,
        rename=os.rename,
    ) -> None:
        self.output_root = Path(output_root)
        self._rename = rename

    def publish_package(
        self,
        manifest: PublishedOutputManifest,
        files: Mapping[str, bytes],
    ) -> PublishedOutputPackage:
        validate_published_output_manifest(manifest)
        if not isinstance(files, Mapping):
            raise OutputPublicationPersistenceError(
                "files must be a mapping of relative paths to bytes."
            )
        expected = {item.relative_path: item for item in manifest.files}
        if set(files) != set(expected):
            raise OutputPublicationIntegrityError(
                "Published Output file set does not match its manifest."
            )
        for relative, data in files.items():
            if not isinstance(data, bytes):
                raise OutputPublicationPersistenceError(
                    "Published Output file content must be bytes."
                )
            reference = expected[relative]
            if hashlib.sha256(data).hexdigest() != reference.content_fingerprint:
                raise OutputPublicationIntegrityError(
                    f"Published Output file fingerprint mismatch: {relative}."
                )

        self._ensure_output_root()
        project_dir = output_project_path(
            self.output_root, manifest.project_id
        )
        self._ensure_directory(project_dir)
        final_dir = output_package_path(
            self.output_root,
            manifest.project_id,
            manifest.output_package_id,
        )
        self._reject_symlink(final_dir, "Published Output package")
        if final_dir.exists():
            raise OutputPublicationPersistenceError(
                "Published Output package path is already occupied."
            )
        temp_dir = project_dir / (
            f".{manifest.output_package_id}.tmp-{uuid.uuid4().hex}"
        )
        self._reject_symlink(temp_dir, "temporary Published Output package")
        if temp_dir.exists():
            raise OutputPublicationPersistenceError(
                "temporary Published Output package path is occupied."
            )
        try:
            temp_dir.mkdir()
            for relative in sorted(files):
                path = temp_dir.joinpath(*PurePosixPath(relative).parts)
                self._ensure_directory(path.parent)
                self._write_bytes(path, files[relative])
            self._write_bytes(
                temp_dir / "manifest.json",
                published_output_manifest_to_json(manifest).encode("utf-8"),
            )
            self._validate_package_directory(
                temp_dir,
                expected_project_id=manifest.project_id,
                expected_output_package_id=manifest.output_package_id,
            )
            self._rename(temp_dir, final_dir)
        except Exception:
            # Preserve interrupted publication as explicit recovery evidence.
            raise
        return self.load_output(
            manifest.project_id,
            manifest.output_package_id,
        )

    def load_output(
        self,
        project_id: str,
        output_package_id: str,
    ) -> PublishedOutputPackage:
        validated_id = validate_output_package_id(output_package_id)
        directory = output_package_path(
            self.output_root, project_id, validated_id
        )
        self._require_directory(directory, "Published Output package")
        manifest = self._validate_package_directory(
            directory,
            expected_project_id=project_id,
            expected_output_package_id=validated_id,
        )
        return PublishedOutputPackage(
            manifest=manifest,
            package_path=directory,
        )

    def read_file(
        self,
        project_id: str,
        output_package_id: str,
        relative_path: str,
    ) -> bytes:
        package = self.load_output(project_id, output_package_id)
        allowed = {item.relative_path for item in package.manifest.files}
        if relative_path not in allowed:
            raise OutputPublicationNotFoundError(
                "Requested path is not part of the Published Output manifest."
            )
        path = package.package_path.joinpath(*PurePosixPath(relative_path).parts)
        self._require_regular_file(path, "Published Output file")
        try:
            return path.read_bytes()
        except OSError as exc:
            raise OutputPublicationPersistenceError(
                f"Unable to read Published Output file: {path}."
            ) from exc

    def scan_project(
        self,
        project_id: str,
    ) -> OutputPublicationRepositoryScanResult:
        try:
            project_dir = output_project_path(self.output_root, project_id)
        except Exception as exc:
            return OutputPublicationRepositoryScanResult(
                issues=(
                    self._issue(
                        project_id,
                        code="unsafe_output_project_path",
                        message=str(exc),
                        path=None,
                    ),
                )
            )
        if not self.output_root.exists():
            return OutputPublicationRepositoryScanResult()
        if self.output_root.is_symlink() or not self.output_root.is_dir():
            return OutputPublicationRepositoryScanResult(
                issues=(
                    self._issue(
                        project_id,
                        code="unsafe_output_root",
                        message="Output root is not a safe directory.",
                        path=self.output_root,
                    ),
                )
            )
        if not project_dir.exists():
            return OutputPublicationRepositoryScanResult()
        if project_dir.is_symlink() or not project_dir.is_dir():
            return OutputPublicationRepositoryScanResult(
                issues=(
                    self._issue(
                        project_id,
                        code="unsafe_output_project_path",
                        message="Project output path is not a safe directory.",
                        path=project_dir,
                    ),
                )
            )
        packages = []
        issues = []
        publication_inputs: dict[str, str] = {}
        for entry in sorted(project_dir.iterdir(), key=lambda item: item.name):
            if _TEMP_DIR.fullmatch(entry.name):
                issues.append(
                    self._issue(
                        project_id,
                        code="interrupted_output_publication",
                        message="Interrupted Published Output publication exists.",
                        path=entry,
                    )
                )
                continue
            match = _OUTPUT_DIR.fullmatch(entry.name)
            if match is None:
                issues.append(
                    self._issue(
                        project_id,
                        code="unexpected_output_entry",
                        message="Unexpected entry in Project output directory.",
                        path=entry,
                    )
                )
                continue
            output_id = match.group(1)
            try:
                package = self.load_output(project_id, output_id)
                prior = publication_inputs.get(
                    package.manifest.publication_input_fingerprint
                )
                if prior is not None:
                    issues.append(
                        self._issue(
                            project_id,
                            code="duplicate_publication_input",
                            message=(
                                "Multiple OUT packages claim the same publication "
                                "input fingerprint."
                            ),
                            path=entry,
                            output_package_id=output_id,
                        )
                    )
                else:
                    publication_inputs[
                        package.manifest.publication_input_fingerprint
                    ] = output_id
                packages.append(package)
            except Exception as exc:
                issues.append(
                    self._issue(
                        project_id,
                        code="invalid_output_package",
                        message=str(exc),
                        path=entry,
                        output_package_id=output_id,
                    )
                )
        return OutputPublicationRepositoryScanResult(
            packages=tuple(packages),
            issues=tuple(issues),
        )

    def list_outputs(
        self,
        project_id: str,
    ) -> tuple[PublishedOutputPackage, ...]:
        scan = self.scan_project(project_id)
        if scan.issues:
            first = scan.issues[0]
            raise OutputPublicationIntegrityError(
                "Published Output repository contains blocking issue "
                f"{first.code}: {first.message}"
            )
        return scan.packages

    def _validate_package_directory(
        self,
        directory: Path,
        *,
        expected_project_id: str,
        expected_output_package_id: str,
    ) -> PublishedOutputManifest:
        self._require_directory(directory, "Published Output package")
        manifest_path = directory / "manifest.json"
        self._require_regular_file(manifest_path, "Published Output manifest")
        try:
            manifest_text = manifest_path.read_text(encoding="utf-8")
        except OSError as exc:
            raise OutputPublicationPersistenceError(
                f"Unable to read Published Output manifest: {manifest_path}."
            ) from exc
        manifest = published_output_manifest_from_json(
            manifest_text,
            expected_project_id=expected_project_id,
            expected_output_package_id=expected_output_package_id,
        )
        expected_paths = {"manifest.json"} | {
            item.relative_path for item in manifest.files
        }
        actual_paths: set[str] = set()
        for path in directory.rglob("*"):
            if path.is_symlink():
                raise OutputPublicationIntegrityError(
                    "Published Output package contains a symbolic link."
                )
            if path.is_file():
                actual_paths.add(path.relative_to(directory).as_posix())
        if actual_paths != expected_paths:
            raise OutputPublicationIntegrityError(
                "Published Output package file set does not match its manifest."
            )
        for reference in manifest.files:
            path = directory.joinpath(
                *PurePosixPath(reference.relative_path).parts
            )
            self._require_regular_file(path, "Published Output file")
            try:
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
            except OSError as exc:
                raise OutputPublicationPersistenceError(
                    f"Unable to read Published Output file: {path}."
                ) from exc
            if digest != reference.content_fingerprint:
                raise OutputPublicationIntegrityError(
                    "Published Output file fingerprint does not match manifest: "
                    f"{reference.relative_path}."
                )
        return manifest


    def _ensure_output_root(self) -> None:
        self._reject_symlink(self.output_root, "Output root")
        try:
            self.output_root.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise OutputPublicationPersistenceError(
                f"Unable to create output root: {self.output_root}."
            ) from exc
        self._reject_symlink(self.output_root, "Output root")
        if not self.output_root.is_dir():
            raise OutputPublicationPersistenceError(
                f"Output root is not a directory: {self.output_root}."
            )

    def _ensure_directory(self, path: Path) -> None:
        self._reject_symlink(path, "Output directory")
        try:
            path.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise OutputPublicationPersistenceError(
                f"Unable to create output directory: {path}."
            ) from exc
        self._reject_symlink(path, "Output directory")
        if not path.is_dir():
            raise OutputPublicationPersistenceError(
                f"Output path is not a directory: {path}."
            )

    def _require_directory(self, path: Path, label: str) -> None:
        self._reject_symlink(path, label)
        if not path.exists() or not path.is_dir():
            raise OutputPublicationNotFoundError(f"{label} not found: {path}.")

    def _require_regular_file(self, path: Path, label: str) -> None:
        self._reject_symlink(path, label)
        if not path.exists() or not path.is_file():
            raise OutputPublicationNotFoundError(f"{label} not found: {path}.")

    def _reject_symlink(self, path: Path, label: str) -> None:
        if path.is_symlink():
            raise OutputPublicationPersistenceError(
                f"{label} must not be a symbolic link: {path}."
            )

    def _write_bytes(self, path: Path, data: bytes) -> None:
        self._reject_symlink(path, "Published Output file")
        try:
            with path.open("xb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
        except OSError as exc:
            raise OutputPublicationPersistenceError(
                f"Unable to write Published Output file: {path}."
            ) from exc

    def _issue(
        self,
        project_id: str,
        *,
        code: str,
        message: str,
        path: Path | None,
        output_package_id: str | None = None,
    ) -> OutputPublicationRepositoryIssue:
        return OutputPublicationRepositoryIssue(
            project_id=project_id,
            code=code,
            message=message,
            issue_level="blocking",
            path=path,
            output_package_id=output_package_id,
        )
