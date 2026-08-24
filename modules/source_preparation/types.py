"""Immutable result type for reusable Source Preparation."""

from __future__ import annotations

from dataclasses import dataclass


SOURCE_PREPARATION_SCHEMA_VERSION = "1.0.0"
SOURCE_PREPARATION_STATUSES = frozenset(
    {"prepared", "dry_run", "skipped_context_only"}
)


@dataclass(frozen=True, slots=True)
class SourcePreparationResult:
    """One persisted preparation for one Projection/detector configuration."""

    schema_version: str
    project_id: str
    source_id: str
    source_projection_id: str
    source_projection_fingerprint: str
    provider: str
    model: str
    prompt_schema_version: str
    reference_examples_sha256: str
    dry_run: bool
    source_analysis_unit_ids: tuple[str, ...]
    source_evidence_ids: tuple[str, ...]
    detector_response_ids: tuple[str | None, ...]
    status: str
    preparation_fingerprint: str
    created_at: str
