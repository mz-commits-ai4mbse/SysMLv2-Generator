"""Immutable contracts for Persona interpretation of canonical engineering subjects."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


SUBJECT_INTERPRETATION_SCHEMA_VERSION = "1.2.0"

# This is deliberately NOT an ontology or Subject-kind taxonomy.
# It is a bounded pre-model relationship-hint vocabulary used only to make
# Persona relationship outputs comparable before Human Engineering Review.
PRE_MODEL_RELATIONSHIP_KINDS = frozenset(
    {
        "uses",
        "participates_in",
        "performs",
        "observes",
        "controls",
        "permits",
        "requires",
        "constrains",
        "responsible_for",
        "retains",
        "provides",
        "depends_on",
        "related_to",
    }
)


@dataclass(frozen=True, slots=True)
class PersonaSubjectRelationship:
    """One explicit directed pre-model relationship between fixed Subjects."""

    source_subject_id: str
    relationship_kind: str
    target_subject_id: str
    statement: str
    content_fingerprint: str


@dataclass(frozen=True, slots=True)
class PersonaClassificationRepair:
    """One auditable bounded repair of a required classification field."""

    canonical_subject_id: str
    field_name: str
    original_value: str
    repaired_value: str
    content_fingerprint: str


@dataclass(frozen=True, slots=True)
class RejectedPersonaRelationship:
    """One invalid optional relationship hint excluded from downstream use."""

    source_subject_id: str
    relationship_kind: str
    target_subject_id: str
    statement: str
    reason_code: str
    content_fingerprint: str


@dataclass(frozen=True, slots=True)
class PersonaSubjectInterpretation:
    """One Persona interpretation using the existing ADR-011 dimensions."""

    canonical_subject_id: str
    interpreted_statement: str
    information_type: str
    statement_modality: str
    epistemic_class: str
    missing_evidence: str | None
    rationale: str
    uncertainties: tuple[str, ...]
    content_fingerprint: str


@dataclass(frozen=True, slots=True)
class ParsedSubjectInterpretationOutput:
    """Validated Persona output over one fixed canonical Subject population."""

    interpretations: tuple[PersonaSubjectInterpretation, ...]
    relationships: tuple[PersonaSubjectRelationship, ...]
    rejected_relationships: tuple[RejectedPersonaRelationship, ...] = ()


@dataclass(frozen=True, slots=True)
class SubjectInterpretationRunResult:
    """One complete Persona/run interpretation over the shared Subject population."""

    project_id: str
    source_id: str
    source_projection_id: str
    team_id: str
    agent_id: str
    persona_id: str
    persona_run_index: int
    llm_provider: str
    llm_model: str
    prompt_schema_version: str
    interpretations: tuple[PersonaSubjectInterpretation, ...]
    relationships: tuple[PersonaSubjectRelationship, ...]
    content_fingerprint: str
    rejected_relationships: tuple[RejectedPersonaRelationship, ...] = ()
    classification_repairs: tuple[PersonaClassificationRepair, ...] = ()


@dataclass(frozen=True, slots=True)
class SharedSubjectInterpretationResult:
    """All Persona runs over one immutable canonical Subject population."""

    project_id: str
    source_id: str
    source_projection_id: str
    team_id: str
    canonical_subject_ids: tuple[str, ...]
    required_personas: tuple[str, ...]
    runs_per_persona: int
    run_results: tuple[SubjectInterpretationRunResult, ...]
    output_root: Path
