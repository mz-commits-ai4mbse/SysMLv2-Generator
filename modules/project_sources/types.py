"""Immutable data types for the Project Source Registry."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class SourceManifest:
    """Validated metadata for one registered project source."""

    schema_version: str
    project_id: str
    source_id: str
    source_role: str
    original_filename: str
    stored_filename: str
    media_type: str
    size_bytes: int
    sha256: str
    registered_at: str
    updated_at: str


@dataclass(frozen=True, slots=True)
class SourceIssue:
    """One deterministic issue discovered while scanning project sources."""

    project_id: str
    code: str
    message: str
    path: Path
    source_id: str | None = None


@dataclass(frozen=True, slots=True)
class SourceScanResult:
    """Valid sources and blocking issues discovered for one project."""

    valid_sources: tuple[SourceManifest, ...] = ()
    source_issues: tuple[SourceIssue, ...] = ()