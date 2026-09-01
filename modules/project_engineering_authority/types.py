"""Immutable ADR-032 S4 project-level Engineering Authority types."""

from __future__ import annotations

from dataclasses import dataclass


PROJECT_AUTHORITY_DECISION_OUTCOMES = frozenset(
    {
        "remain_independent",
        "coexist",
        "supersede",
        "unresolved",
    }
)

PROJECT_AUTHORITY_STATES = frozenset(
    {
        "active",
        "superseded",
        "unresolved",
    }
)


@dataclass(frozen=True, slots=True)
class ProjectAuthoritySubjectBinding:
    """Exact bridge from one S3 Subject to source-local reviewed authority."""

    subject_ref: str
    canonical_subject_id: str
    source_id: str
    approved_input_id: str
    approved_input_fingerprint: str
    stable_subject_key: str
    review_document_id: str
    review_document_version_id: str
    review_revision_id: str
    aei_content_fingerprint: str
    content_fingerprint: str


@dataclass(frozen=True, slots=True)
class ProjectAuthorityDecision:
    """One explicit Human project-level authority decision for one S3 relation."""

    schema_version: str
    project_id: str
    decision_id: str
    reconciliation_fingerprint: str
    relation_fingerprint: str
    left_subject_ref: str
    right_subject_ref: str
    machine_relation_outcome: str
    outcome: str
    authority_concern_id: str | None
    retained_approved_input_ids: tuple[str, ...]
    project_superseded_approved_input_ids: tuple[str, ...]
    reviewer_identity: str
    rationale: str
    decided_at: str
    decision_fingerprint: str


@dataclass(frozen=True, slots=True)
class ProjectAuthorityEntry:
    """Derived project-level authority state for one source-local Approved Input."""

    approved_input_id: str
    source_id: str
    subject_refs: tuple[str, ...]
    approved_input_fingerprint: str
    stable_subject_key: str
    project_authority_state: str
    authority_concern_ids: tuple[str, ...]
    decision_ids: tuple[str, ...]
    content_fingerprint: str


@dataclass(frozen=True, slots=True)
class ProjectEngineeringAuthorityState:
    """Human-authorized project-level authority state consumed by S5."""

    schema_version: str
    project_id: str
    reconciliation_fingerprint: str
    bindings: tuple[ProjectAuthoritySubjectBinding, ...]
    decisions: tuple[ProjectAuthorityDecision, ...]
    entries: tuple[ProjectAuthorityEntry, ...]
    unresolved_decision_ids: tuple[str, ...]
    model_impact_ready: bool
    content_fingerprint: str
