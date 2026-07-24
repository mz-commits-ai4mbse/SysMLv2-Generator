"""Immutable types for deterministic semantic consensus."""

from __future__ import annotations

from dataclasses import dataclass

from modules.information_units.types import (
    SEMANTIC_CONFIDENCE_LEVELS,
    InformationUnitSourceAnchor,
)


SEMANTIC_CONSENSUS_LEVELS = frozenset(
    {
        "unanimous",
        "majority",
        "single",
        "none",
        "incomparable",
        "incomplete",
    }
)

SEMANTIC_VARIANCE_LEVELS = frozenset(
    {
        "low",
        "medium",
        "high",
    }
)

PERSONA_STABILITY_LEVELS = frozenset(
    {
        "stable",
        "unstable",
        "indeterminate",
        "not_measured",
        "incomplete",
    }
)

SEMANTIC_CONSENSUS_FIELD_NAMES = frozenset(
    {
        "existence",
        "interpreted_statement",
        "information_type",
        "statement_modality",
        "epistemic_class",
        "semantic_evidence",
    }
)

SEMANTIC_REVIEW_MODES = frozenset(
    {
        "quick_confirmation",
        "detailed_review",
    }
)

SEMANTIC_CONSENSUS_ISSUE_LEVELS = frozenset(
    {
        "warning",
        "blocking",
    }
)


@dataclass(frozen=True, slots=True)
class AgentCandidateReference:
    """One unambiguous reference to one persona-run candidate."""

    persona_id: str
    agent_id: str
    persona_run_index: int
    candidate_id: str


@dataclass(frozen=True, slots=True)
class PersonaRunExpectation:
    """Expected independent repetitions for one required persona."""

    persona_id: str
    expected_run_count: int


@dataclass(frozen=True, slots=True)
class PersonaStabilityAssessment:
    """Intra-persona stability without creating additional votes."""

    persona_id: str
    expected_run_count: int
    observed_run_indices: tuple[int, ...]
    omitted_run_indices: tuple[int, ...]
    stability_level: str
    candidate_references: tuple[
        AgentCandidateReference,
        ...
    ]
    rationale: str


@dataclass(frozen=True, slots=True)
class ConsensusValueDistribution:
    """One canonical field value and its distinct persona support."""

    canonical_value: str
    display_value: str
    supporting_personas: tuple[str, ...]
    candidate_references: tuple[
        AgentCandidateReference,
        ...
    ]


@dataclass(frozen=True, slots=True)
class FieldConsensusAssessment:
    """Deterministic consensus and variance for one critical field."""

    field_name: str
    selected_value: str | None
    consensus_level: str
    variance_level: str
    confidence: str
    total_personas: int
    supporting_personas: tuple[str, ...]
    dissenting_personas: tuple[str, ...]
    omitting_personas: tuple[str, ...]
    value_distribution: tuple[
        ConsensusValueDistribution,
        ...
    ]
    review_required: bool
    rationale: str


@dataclass(frozen=True, slots=True)
class ConsensusInformationUnitDraft:
    """Professional content eligible for a new Information Unit ID."""

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


@dataclass(frozen=True, slots=True)
class SemanticConsensusIssue:
    """One auditable technical or comparison issue."""

    code: str
    message: str
    issue_level: str
    persona_id: str | None = None
    agent_id: str | None = None
    persona_run_index: int | None = None


@dataclass(frozen=True, slots=True)
class SemanticConsensusOutcome:
    """Consensus finding for one source-evidence cluster."""

    consensus_candidate_id: str
    source_anchors: tuple[
        InformationUnitSourceAnchor,
        ...
    ]
    source_excerpt: str
    candidate_references: tuple[
        AgentCandidateReference,
        ...
    ]
    persona_stability: tuple[
        PersonaStabilityAssessment,
        ...
    ]
    field_assessments: tuple[
        FieldConsensusAssessment,
        ...
    ]
    proposed_information_unit: (
        ConsensusInformationUnitDraft | None
    )
    consensus_level: str
    variance_level: str
    confidence: str
    total_personas: int
    supporting_personas: tuple[str, ...]
    dissenting_personas: tuple[str, ...]
    omitting_personas: tuple[str, ...]
    confirmation_required: bool
    review_required: bool
    recommended_review_mode: str
    publication_eligible: bool
    confidence_rationale: str


@dataclass(frozen=True, slots=True)
class SemanticConsensusResult:
    """Immutable deterministic analysis of one semantic persona team."""

    schema_version: str
    project_id: str
    source_id: str
    source_projection_id: str
    team_id: str
    consensus_report_id: str
    required_personas: tuple[str, ...]
    persona_run_expectations: tuple[
        PersonaRunExpectation,
        ...
    ]
    llm_provider: str
    llm_model: str
    prompt_schema_version: str
    outcomes: tuple[SemanticConsensusOutcome, ...]
    issues: tuple[SemanticConsensusIssue, ...]
    created_at: str