"""Immutable contracts for deterministic field-level Subject consensus."""

from __future__ import annotations

from dataclasses import dataclass


SUBJECT_CONSENSUS_SCHEMA_VERSION = "1.0.0"

CONSENSUS_LEVELS = frozenset(
    {
        "unanimous",
        "majority",
        "divergent",
        "indeterminate",
    }
)
CONFIDENCE_LEVELS = frozenset({"high", "medium", "low"})


@dataclass(frozen=True, slots=True)
class ConsensusValueDistribution:
    """One structured value and the independent Personas supporting it."""

    value: str
    supporting_personas: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class FieldConsensusAssessment:
    """Deterministic consensus for one structured field of one SUBJ-*."""

    field_name: str
    consensus_level: str
    confidence: str
    selected_value: str | None
    total_personas: int
    supporting_personas: tuple[str, ...]
    dissenting_personas: tuple[str, ...]
    unstable_personas: tuple[str, ...]
    value_distribution: tuple[ConsensusValueDistribution, ...]
    review_attention_required: bool


@dataclass(frozen=True, slots=True)
class PersonaStatementVariant:
    """Preserved free-text interpretation variants for one Persona."""

    persona_id: str
    statements: tuple[str, ...]
    stable_across_runs: bool


@dataclass(frozen=True, slots=True)
class PersonaDiagnosticVariant:
    """Preserved uncertainty or missing-evidence variants for one Persona."""

    persona_id: str
    values: tuple[str, ...]
    stable_across_runs: bool


@dataclass(frozen=True, slots=True)
class SubjectConsensusOutcome:
    """Field-level consensus and preserved prose for one canonical Subject."""

    canonical_subject_id: str
    information_type: FieldConsensusAssessment
    statement_modality: FieldConsensusAssessment
    epistemic_class: FieldConsensusAssessment
    statement_variants: tuple[PersonaStatementVariant, ...]
    uncertainty_variants: tuple[PersonaDiagnosticVariant, ...]
    missing_evidence_variants: tuple[PersonaDiagnosticVariant, ...]
    review_attention_required: bool


@dataclass(frozen=True, slots=True)
class RelationshipConsensusOutcome:
    """Persona support for one canonical directed pre-model relationship key."""

    source_subject_id: str
    relationship_kind: str
    target_subject_id: str
    consensus_level: str
    confidence: str
    total_personas: int
    supporting_personas: tuple[str, ...]
    omitting_personas: tuple[str, ...]
    unstable_personas: tuple[str, ...]
    statement_variants: tuple[PersonaStatementVariant, ...]
    review_attention_required: bool


@dataclass(frozen=True, slots=True)
class SharedSubjectConsensusResult:
    """Deterministic consensus over one SharedSubjectInterpretationResult."""

    schema_version: str
    project_id: str
    source_id: str
    source_projection_id: str
    team_id: str
    required_personas: tuple[str, ...]
    runs_per_persona: int
    canonical_subject_ids: tuple[str, ...]
    subject_outcomes: tuple[SubjectConsensusOutcome, ...]
    relationship_outcomes: tuple[RelationshipConsensusOutcome, ...]
    human_review_required: bool
    content_fingerprint: str
