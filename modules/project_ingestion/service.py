"""Project-bound Source upload and registration orchestration."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from modules.project_sources import (
    ProjectSourceRegistry,
    SourceManifest,
)

from .errors import (
    ProjectIngestionInputError,
    ProjectIngestionTemporaryFileError,
)
from .types import (
    ProjectBoundSourceInventory,
    ProjectBoundSourceIssue,
    ProjectBoundSourceSummary,
)


DEFAULT_PROJECTS_ROOT = Path("data/projects")


class ProjectBoundIngestionService:
    """Coordinate project-bound ingestion without replacing P2-P5."""

    def __init__(
        self,
        root: Path | str = DEFAULT_PROJECTS_ROOT,
        *,
        source_registry: ProjectSourceRegistry | None = None,
    ) -> None:
        self.root = Path(root)
        self._source_registry = (
            ProjectSourceRegistry(root=self.root)
            if source_registry is None
            else source_registry
        )

    def register_uploaded_source(
        self,
        project_id: str,
        *,
        original_filename: str,
        content: bytes | bytearray | memoryview,
        source_role: str,
    ) -> ProjectBoundSourceSummary:
        """Register exact uploaded bytes through the authoritative P3 API."""

        validated_filename = _validate_upload_filename(
            original_filename
        )
        validated_content = _validate_upload_content(content)

        try:
            with TemporaryDirectory(
                prefix="turing-source-upload-"
            ) as temporary_directory:
                temporary_path = (
                    Path(temporary_directory) / validated_filename
                )
                temporary_path.write_bytes(validated_content)

                manifest = self._source_registry.register_source(
                    project_id,
                    temporary_path,
                    source_role=source_role,
                )
        except OSError as exc:
            raise ProjectIngestionTemporaryFileError(
                "Unable to prepare the temporary Source upload."
            ) from exc

        return _source_summary(manifest)

    def list_registered_sources(
        self,
        project_id: str,
    ) -> ProjectBoundSourceInventory:
        """Return safe Source inventory data for one Project."""

        scan = self._source_registry.scan_sources(project_id)

        return ProjectBoundSourceInventory(
            project_id=project_id,
            sources=tuple(
                _source_summary(manifest)
                for manifest in scan.valid_sources
            ),
            issues=tuple(
                ProjectBoundSourceIssue(
                    code=issue.code,
                    source_id=issue.source_id,
                )
                for issue in scan.source_issues
            ),
        )

    def load_registered_source(
        self,
        project_id: str,
        source_id: str,
    ) -> ProjectBoundSourceSummary:
        """Load one Source through P3 and return safe metadata."""

        return _source_summary(
            self._source_registry.load_source(
                project_id,
                source_id,
            )
        )


def _source_summary(
    manifest: SourceManifest,
) -> ProjectBoundSourceSummary:
    return ProjectBoundSourceSummary(
        project_id=manifest.project_id,
        source_id=manifest.source_id,
        source_role=manifest.source_role,
        original_filename=manifest.original_filename,
        media_type=manifest.media_type,
        size_bytes=manifest.size_bytes,
        sha256=manifest.sha256,
        registered_at=manifest.registered_at,
    )


def _validate_upload_filename(value: Any) -> str:
    if not isinstance(value, str):
        raise ProjectIngestionInputError(
            "Uploaded Source filename must be a string."
        )

    if not value.strip():
        raise ProjectIngestionInputError(
            "Uploaded Source filename must not be empty."
        )

    if value in {".", ".."}:
        raise ProjectIngestionInputError(
            "Uploaded Source filename must be a file basename."
        )

    if any(character in value for character in ("/", "\\", "\x00")):
        raise ProjectIngestionInputError(
            "Uploaded Source filename must not contain path separators."
        )

    if any(ord(character) < 32 for character in value):
        raise ProjectIngestionInputError(
            "Uploaded Source filename must not contain control characters."
        )

    return value


def _validate_upload_content(
    value: Any,
) -> bytes:
    if not isinstance(value, (bytes, bytearray, memoryview)):
        raise ProjectIngestionInputError(
            "Uploaded Source content must be bytes."
        )

    content = bytes(value)

    if not content:
        raise ProjectIngestionInputError(
            "Uploaded Source content must not be empty."
        )

    return content
