"""Immutable types for project-level cross-source semantic reconciliation."""

from __future__ import annotations

from dataclasses import dataclass

from modules.engineering_subjects.types import CanonicalSubjectSet
from modules.project_fit.types import ProjectFitAssessment
from modules.subject_consensus.types import SharedSubjectConsensusResult


PROJECT_SEMANTIC_RELATION_OUTCOMES = frozenset(
    {
        "equivalent",
        "complementary",
        "potential_conflict",
        "distinct",
        "uncertain",
    }
)


@dataclass(frozen=True, slots=True)
class ProjectSemanticSourceInput:
    """One admitted source-local semantic result entering project reconciliation."""

    project_fit: ProjectFitAssessment
    canonical_subject_set: CanonicalSubjectSet
    subject_consensus: SharedSubjectConsensusResult


@dataclass(frozen=True, slots=True)
class ProjectSemanticMentionEvidence:
    """Exact grounded Source mention supporting one source-local Subject."""

    mention_id: str
    exact_text: str
    source_evidence_ids: tuple[str, ...]
    mention_fingerprint: str


@dataclass(frozen=True, slots=True)
class ProjectSemanticStatementEvidence:
    """Persona-preserving interpreted statement evidence."""

    persona_id: str
    statements: tuple[str, ...]
    stable_across_runs: bool


@dataclass(frozen=True, slots=True)
class ProjectSemanticFieldEvidence:
    """One consensus field retained as non-authoritative semantic evidence."""

    field_name: str
    selected_value: str | None
    consensus_level: str
    confidence: str
    review_attention_required: bool


@dataclass(frozen=True, slots=True)
class ProjectSemanticSubject:
    """Project-unique reference to one unchanged source-local canonical Subject."""

    subject_ref: str
    project_id: str
    source_id: str
    source_projection_id: str
    canonical_subject_id: str
    canonical_label: str
    subject_form: str
    identity_status: str
    canonical_subject_fingerprint: str
    canonical_subject_set_fingerprint: str
    subject_consensus_fingerprint: str
    project_fit_fingerprint: str
    mention_evidence: tuple[ProjectSemanticMentionEvidence, ...]
    statement_evidence: tuple[ProjectSemanticStatementEvidence, ...]
    field_evidence: tuple[ProjectSemanticFieldEvidence, ...]
    source_review_attention_required: bool
    content_fingerprint: str


@dataclass(frozen=True, slots=True)
class ProjectSemanticRelation:
    """Non-authoritative semantic relationship evidence between two Sources."""

    left_subject_ref: str
    right_subject_ref: str
    outcome: str
    rationale: str
    shared_concepts: tuple[str, ...]
    material_differences: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ProjectSemanticReconciliationArtifact:
    """Fingerprint-bound project-level relationship evidence for Human Review."""

    schema_version: str
    project_id: str
    source_ids: tuple[str, ...]
    subjects: tuple[ProjectSemanticSubject, ...]
    relations: tuple[ProjectSemanticRelation, ...]
    unmatched_subject_refs: tuple[str, ...]
    prompt_schema_version: str
    llm_provider: str
    llm_model: str
    llm_response_id: str | None
    input_fingerprint: str
    human_review_required: bool
    content_fingerprint: str
