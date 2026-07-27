"""Immutable data types for project-bound ingestion integration."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProjectBoundSourceSummary:
    """Safe project-bound metadata for one registered Source."""

    project_id: str
    source_id: str
    source_role: str
    original_filename: str
    media_type: str
    size_bytes: int
    sha256: str
    registered_at: str


@dataclass(frozen=True, slots=True)
class ProjectBoundSourceIssue:
    """Safe issue identity without unrestricted filesystem paths."""

    code: str
    source_id: str | None = None


@dataclass(frozen=True, slots=True)
class ProjectBoundSourceInventory:
    """Validated registered Sources and safe issue identities."""

    project_id: str
    sources: tuple[ProjectBoundSourceSummary, ...] = ()
    issues: tuple[ProjectBoundSourceIssue, ...] = ()
