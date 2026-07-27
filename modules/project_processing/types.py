"""Immutable data types for project-oriented processing."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


PROCESSING_RUN_STATES = frozenset(
    {
        "created",
        "running",
        "awaiting_review",
        "blocked",
        "failed",
        "completed",
        "superseded",
    }
)

PROCESSING_STAGES = frozenset(
    {
        "agentic_ingestion",
        "source_projection",
        "semantic_extraction",
        "semantic_consensus",
        "terminology_mapping",
        "framework_assignment",
        "human_review",
        "publication",
    }
)

PROCESSING_WORKFLOW_PROFILES = frozenset(
    {
        "engineering_source_processing",
        "context_only_processing",
    }
)

SOURCE_PROCESSING_DISPOSITIONS = frozenset(
    {
        "in_scope",
        "context_only",
        "out_of_scope",
    }
)

PROCESSING_DECISION_TYPES = frozenset(
    {
        "source_disposition",
    }
)

PROCESSING_EVENT_TYPES = frozenset(
    {
        "run_created",
        "stage_started",
        "stage_completed",
        "review_requested",
        "review_resolved",
        "run_blocked",
        "run_failed",
        "retry_started",
        "artifact_published",
        "artifact_invalidated",
        "artifact_superseded",
        "recovery_required",
        "recovery_completed",
        "run_completed",
        "run_superseded",
    }
)

ARTIFACT_LIFECYCLE_STATES = frozenset(
    {
        "active",
        "superseded",
        "invalidated",
    }
)

PROJECT_PROCESSING_STATES = frozenset(
    {
        "empty",
        "not_started",
        "in_progress",
        "awaiting_review",
        "attention_required",
        "partially_processed",
        "processed",
    }
)

PROCESSING_ISSUE_LEVELS = frozenset(
    {
        "warning",
        "blocking",
    }
)


@dataclass(frozen=True, slots=True)
class SemanticReferenceVersion:
    """One immutable semantic reference binding for a run."""

    reference_system_id: str
    reference_version: str


@dataclass(frozen=True, slots=True)
class ProcessingArtifactReference:
    """One exact reference to an existing or run-owned artifact."""

    artifact_type: str
    artifact_id: str
    content_fingerprint: str
    repository_relative_path: str


@dataclass(frozen=True, slots=True)
class ProcessingRunManifest:
    """Immutable identity and reproducibility contract for one run."""

    schema_version: str
    project_id: str
    processing_run_id: str
    source_id: str
    source_sha256: str
    source_role_snapshot: str
    workflow_profile: str
    configuration_fingerprint: str
    framework_template_id: str
    framework_template_version: str
    semantic_reference_versions: tuple[
        SemanticReferenceVersion,
        ...
    ]
    created_at: str
    supersedes_run_id: str | None


@dataclass(frozen=True, slots=True)
class ProcessingEvent:
    """One immutable transition in a Processing Run history."""

    schema_version: str
    project_id: str
    processing_run_id: str
    event_id: str
    event_sequence: int
    previous_state: str | None
    next_state: str
    processing_stage: str | None
    event_type: str
    attempt_id: str | None
    reason_code: str
    artifact_references: tuple[
        ProcessingArtifactReference,
        ...
    ]
    occurred_at: str
    previous_event_fingerprint: str | None
    event_fingerprint: str


@dataclass(frozen=True, slots=True)
class ProcessingDecision:
    """One immutable operational Human-in-the-Loop decision."""

    schema_version: str
    project_id: str
    processing_decision_id: str
    decision_type: str
    source_id: str
    source_sha256: str
    disposition: str
    reviewer_identity: str
    rationale: str
    decided_at: str
    supersedes_processing_decision_id: str | None
    decision_fingerprint: str


@dataclass(frozen=True, slots=True)
class ProcessingArtifactLifecycle:
    """Derived operational lifecycle state of one immutable artifact."""

    artifact_reference: ProcessingArtifactReference
    lifecycle_state: str
    caused_by_event_id: str
    superseded_by_artifact_id: str | None = None


@dataclass(frozen=True, slots=True)
class ProcessingIssue:
    """One deterministic processing, persistence or recovery issue."""

    project_id: str
    code: str
    message: str
    issue_level: str
    path: Path | None = None
    source_id: str | None = None
    processing_run_id: str | None = None
    event_id: str | None = None
    processing_decision_id: str | None = None


@dataclass(frozen=True, slots=True)
class ProcessingRunHistory:
    """One validated Run Manifest and its ordered Event History."""

    manifest: ProcessingRunManifest
    events: tuple[ProcessingEvent, ...]


@dataclass(frozen=True, slots=True)
class DerivedProcessingRunState:
    """Current operational state derived from one Event History."""

    project_id: str
    processing_run_id: str
    source_id: str
    run_state: str
    processing_stage: str | None
    latest_attempt_id: str | None
    latest_event_id: str
    superseded_by_run_id: str | None
    blocked_reason: str | None
    failure_reason: str | None
    pending_review: bool


@dataclass(frozen=True, slots=True)
class SourceProcessingSummary:
    """Derived processing view for one registered project source."""

    project_id: str
    source_id: str
    processing_disposition: str
    current_processing_run_id: str | None
    run_state: str | None
    processing_stage: str | None
    latest_attempt_id: str | None
    blocking_issue_codes: tuple[str, ...]
    failure_issue_codes: tuple[str, ...]
    pending_review: bool
    superseded_run_ids: tuple[str, ...]
    invalidated_artifact_count: int


@dataclass(frozen=True, slots=True)
class ProjectProcessingSummary:
    """Derived project-level processing state and explicit counts."""

    project_id: str
    project_state: str
    total_sources: int
    in_scope_sources: int
    context_only_sources: int
    out_of_scope_sources: int
    not_started_sources: int
    running_sources: int
    awaiting_review_sources: int
    blocked_sources: int
    failed_sources: int
    completed_sources: int
    superseded_runs: int
    invalidated_artifacts: int
    source_summaries: tuple[SourceProcessingSummary, ...]
    issues: tuple[ProcessingIssue, ...]


@dataclass(frozen=True, slots=True)
class ProcessingScanResult:
    """Validated processing artifacts and explicit scan issues."""

    run_histories: tuple[ProcessingRunHistory, ...] = ()
    decisions: tuple[ProcessingDecision, ...] = ()
    issues: tuple[ProcessingIssue, ...] = ()