"""Immutable in-memory contracts for ADR-033 reconciliation Cases."""

from __future__ import annotations

from dataclasses import dataclass


PROJECT_SEMANTIC_INDEX_SCHEMA_VERSION = "1.0.0"
PROJECT_SEMANTIC_INDEX_PROVENANCE_SCHEMA_VERSION = "1.1.0"
PROJECT_RECONCILIATION_CASE_ASSESSMENT_SCHEMA_VERSION = "1.0.0"
PROJECT_RECONCILIATION_SUMMARY_SCHEMA_VERSION = "1.0.0"

PROJECT_RECONCILIATION_CASE_OUTCOMES = frozenset(
    {
        "equivalent",
        "complementary",
        "potential_conflict",
        "distinct",
        "uncertain",
        "unique",
    }
)


@dataclass(frozen=True, slots=True)
class SemanticIndexGroupProposal:
    """Non-authoritative S3A grouping proposal from bounded semantic indexing."""

    group_label: str
    member_subject_refs: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ProjectReconciliationCase:
    """Deterministically identified group of Subjects sharing one concern."""

    case_id: str
    group_label: str
    member_subject_refs: tuple[str, ...]
    source_ids: tuple[str, ...]
    singleton: bool
    case_fingerprint: str


@dataclass(frozen=True, slots=True)
class ProjectSemanticIndexArtifact:
    """Validated non-authoritative S3A index over exact project Subjects."""

    schema_version: str
    project_id: str
    input_fingerprint: str
    subject_refs: tuple[str, ...]
    source_ids: tuple[str, ...]
    cases: tuple[ProjectReconciliationCase, ...]
    human_review_required: bool
    content_fingerprint: str
    llm_provider: str | None = None
    llm_model: str | None = None
    llm_response_id: str | None = None
    llm_output_fingerprint: str | None = None


@dataclass(frozen=True, slots=True)
class ReconciliationClaimGroupProposal:
    """Non-authoritative proposed claim/variant grouping inside one Case."""

    summary: str
    supported_by_subject_refs: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ReconciliationClaimGroup:
    """Deterministically identified claim/variant evidence inside one Case."""

    claim_group_id: str
    summary: str
    supported_by_subject_refs: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ProjectReconciliationCaseAssessment:
    """Non-authoritative S3B assessment of one complete engineering concern."""

    schema_version: str
    project_id: str
    case_id: str
    case_fingerprint: str
    member_subject_refs: tuple[str, ...]
    source_ids: tuple[str, ...]
    shared_concern: str
    outcome: str
    summary: str
    shared_concepts: tuple[str, ...]
    material_differences: tuple[str, ...]
    claim_groups: tuple[ReconciliationClaimGroup, ...]
    llm_provider: str | None
    llm_model: str | None
    llm_response_id: str | None
    human_review_required: bool
    content_fingerprint: str


@dataclass(frozen=True, slots=True)
class ProjectReconciliationSummary:
    """Deterministic aggregate over complete Case assessments."""

    schema_version: str
    project_id: str
    semantic_index_fingerprint: str
    case_count: int
    outcome_counts: tuple[tuple[str, int], ...]
    potential_conflicts_present: bool
    uncertainties_present: bool
    regrouping_required: bool
    human_project_authority_required: bool
    content_fingerprint: str
