"""Immutable data types for project-bound ingestion integration."""

from __future__ import annotations

from dataclasses import dataclass

from modules.project_processing import ProcessingArtifactReference


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


@dataclass(frozen=True, slots=True)
class ProjectBoundIngestionWorkResult:
    """Safe result of execution into non-authoritative Run work."""

    project_id: str
    source_id: str
    source_projection_id: str | None
    processing_run_id: str
    attempt_id: str
    run_state: str
    processing_stage: str
    dry_run: bool
    projection_result: str | None
    phase_f_run_id: str | None
    failure_reason: str | None = None


@dataclass(frozen=True, slots=True)
class ProjectBoundIngestionResult:
    """Safe final project-bound execution and publication result."""

    project_id: str
    source_id: str
    source_projection_id: str | None
    processing_run_id: str
    attempt_id: str
    run_state: str
    processing_stage: str
    dry_run: bool
    projection_result: str | None
    phase_f_run_id: str | None
    artifact_references: tuple[
        ProcessingArtifactReference,
        ...
    ] = ()
    failure_reason: str | None = None
    recovery_required: bool = False
