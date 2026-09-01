"""Immutable types for project-level source-fit assessment."""

from __future__ import annotations

from dataclasses import dataclass


PROJECT_FIT_OUTCOMES = frozenset(
    {
        "plausible_in_scope",
        "uncertain",
        "likely_out_of_scope",
    }
)

PROJECT_FIT_GATE_STATES = frozenset(
    {
        "admitted",
        "context_only",
        "human_resolution_required",
    }
)


@dataclass(frozen=True, slots=True)
class ProjectFitContextReference:
    """One exact context artifact used by a Project Fit assessment."""

    reference_kind: str
    reference_id: str
    source_id: str | None
    source_role: str | None
    content_fingerprint: str


@dataclass(frozen=True, slots=True)
class ProjectFitAssessment:
    """Immutable machine-generated evidence about one source's Project fit."""

    schema_version: str
    project_id: str
    source_id: str
    source_role: str
    source_sha256: str
    source_projection_id: str
    candidate_projection_fingerprint: str
    candidate_content_sha256: str
    processing_run_id: str
    attempt_id: str
    outcome: str
    rationale: str
    matched_concepts: tuple[str, ...]
    incompatible_concepts: tuple[str, ...]
    supporting_context_refs: tuple[str, ...]
    context_references: tuple[ProjectFitContextReference, ...]
    prompt_schema_version: str
    llm_provider: str
    llm_model: str
    llm_response_id: str | None
    input_fingerprint: str
    assessment_fingerprint: str
