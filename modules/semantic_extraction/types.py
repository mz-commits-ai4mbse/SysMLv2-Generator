"""Immutable types for persona-specific semantic extraction results."""

from __future__ import annotations

from dataclasses import dataclass

from modules.information_units.types import (
    EPISTEMIC_CLASSES,
    INFORMATION_TYPES,
    STATEMENT_MODALITIES,
    InformationUnitSourceAnchor,
)


@dataclass(frozen=True, slots=True)
class InformationUnitCandidate:
    """One result-local semantic claim proposed by one persona run."""

    candidate_id: str
    source_anchors: tuple[
        InformationUnitSourceAnchor,
        ...
    ]
    source_excerpt: str
    interpreted_statement: str
    information_type: str
    statement_modality: str
    epistemic_class: str
    supporting_information_unit_ids: tuple[str, ...]
    derivation_rationale: str | None
    missing_evidence: str | None
    extraction_rationale: str
    uncertainties: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SemanticExtractionAgentResult:
    """Immutable output of one configured extraction persona run."""

    schema_version: str
    project_id: str
    source_id: str
    source_projection_id: str
    team_id: str
    agent_id: str
    persona_id: str
    persona_run_index: int
    persona_configuration_fingerprint: str
    llm_provider: str
    llm_model: str
    prompt_schema_version: str
    candidates: tuple[InformationUnitCandidate, ...]
    no_candidate_rationale: str | None
    created_at: str