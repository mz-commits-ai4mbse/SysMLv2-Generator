"""Immutable types for terminology and ontology mapping candidates."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


TERMINOLOGY_TEXT_FIELDS = frozenset(
    {
        "source_excerpt",
        "interpreted_statement",
    }
)

TERMINOLOGY_MAPPING_STATUSES = frozenset(
    {
        "mapped",
        "unmapped",
        "ambiguous",
        "conflict",
        "no_equivalent",
    }
)

TERMINOLOGY_MAPPING_RELATIONS = frozenset(
    {
        "exact_match",
        "narrower_than",
        "broader_than",
        "related_to",
        "no_equivalent",
    }
)

TERMINOLOGY_MAPPING_TARGET_KINDS = frozenset(
    {
        "project_concept",
        "turing_core_concept",
        "external_reference_concept",
    }
)

TERMINOLOGY_MAPPING_BASIS_TYPES = frozenset(
    {
        "accepted_project_glossary",
        "turing_core",
        "reference_concept_index",
        "semantic_interpretation",
    }
)

TERMINOLOGY_MAPPING_CONFIDENCE_LEVELS = frozenset(
    {
        "high",
        "medium",
        "low",
    }
)

TERMINOLOGY_MAPPING_CONSENSUS_LEVELS = frozenset(
    {
        "unanimous",
        "majority",
        "single",
        "none",
        "incomparable",
        "incomplete",
    }
)

TERMINOLOGY_MAPPING_VARIANCE_LEVELS = frozenset(
    {
        "low",
        "medium",
        "high",
    }
)

TERMINOLOGY_MAPPING_REVIEW_MODES = frozenset(
    {
        "quick_confirmation",
        "detailed_review",
    }
)

TERMINOLOGY_MAPPING_ISSUE_LEVELS = frozenset(
    {
        "warning",
        "blocking",
    }
)


@dataclass(frozen=True, slots=True)
class TerminologyOccurrence:
    """One exact term occurrence in one immutable Information Unit."""

    information_unit_id: str
    text_field: str
    start_offset: int
    end_offset: int
    term_text: str


@dataclass(frozen=True, slots=True)
class TerminologyMappingTarget:
    """One explicit project, Turing Core or external target."""

    target_kind: str
    display_label: str
    project_concept_id: str | None = None
    project_concept_revision: int | None = None
    turing_core_concept_id: str | None = None
    reference_system_id: str | None = None
    reference_system_version: str | None = None
    reference_concept_iri: str | None = None


@dataclass(frozen=True, slots=True)
class TerminologyMappingBasis:
    """One versioned evidence reference supporting a mapping proposal."""

    basis_type: str
    reference_id: str
    reference_version: str | None
    rationale: str


@dataclass(frozen=True, slots=True)
class TerminologyMappingProposal:
    """One candidate semantic relation to one target or no equivalent."""

    mapping_relation: str
    target: TerminologyMappingTarget | None
    mapping_bases: tuple[TerminologyMappingBasis, ...]
    rationale: str


@dataclass(frozen=True, slots=True)
class TerminologyMappingAgentCandidate:
    """One result-local proposal from one configured persona run."""

    terminology_mapping_agent_candidate_id: str
    occurrence: TerminologyOccurrence
    mapping_status: str
    proposals: tuple[TerminologyMappingProposal, ...]
    rationale: str
    uncertainties: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class TerminologyMappingAgentResult:
    """Immutable terminology-mapping output of one persona run."""

    schema_version: str
    project_id: str
    source_id: str
    source_projection_id: str
    information_unit_id: str
    team_id: str
    agent_id: str
    persona_id: str
    persona_run_index: int
    persona_configuration_fingerprint: str
    llm_provider: str
    llm_model: str
    prompt_schema_version: str
    ontology_registry_version: str
    reference_concept_index_version: str
    turing_core_version: str
    project_glossary_revision: int
    candidates: tuple[
        TerminologyMappingAgentCandidate,
        ...
    ]
    no_candidate_rationale: str | None
    created_at: str


@dataclass(frozen=True, slots=True)
class TerminologyMappingAgentCandidateReference:
    """Unambiguous reference to one persona-run mapping candidate."""

    persona_id: str
    agent_id: str
    persona_run_index: int
    terminology_mapping_agent_candidate_id: str


@dataclass(frozen=True, slots=True)
class TerminologyMappingValueDistribution:
    """One canonical mapping value and its distinct persona support."""

    canonical_value: str
    display_value: str
    supporting_personas: tuple[str, ...]
    candidate_references: tuple[
        TerminologyMappingAgentCandidateReference,
        ...
    ]


@dataclass(frozen=True, slots=True)
class TerminologyMappingConsensusOutcome:
    """Deterministic consensus for one aligned term occurrence."""

    occurrence: TerminologyOccurrence
    mapping_status: str
    selected_proposals: tuple[
        TerminologyMappingProposal,
        ...
    ]
    candidate_references: tuple[
        TerminologyMappingAgentCandidateReference,
        ...
    ]
    value_distribution: tuple[
        TerminologyMappingValueDistribution,
        ...
    ]
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
    persistence_eligible: bool
    confidence_rationale: str


@dataclass(frozen=True, slots=True)
class TerminologyMappingCandidate:
    """One immutable persisted mapping candidate without authority."""

    schema_version: str
    project_id: str
    source_id: str
    source_projection_id: str
    information_unit_id: str
    terminology_mapping_candidate_id: str
    occurrence: TerminologyOccurrence
    mapping_status: str
    proposals: tuple[TerminologyMappingProposal, ...]
    candidate_references: tuple[
        TerminologyMappingAgentCandidateReference,
        ...
    ]
    team_id: str
    required_personas: tuple[str, ...]
    llm_provider: str
    llm_model: str
    prompt_schema_version: str
    ontology_registry_version: str
    reference_concept_index_version: str
    turing_core_version: str
    project_glossary_revision: int
    consensus_level: str
    variance_level: str
    confidence: str
    confidence_rationale: str
    confirmation_required: bool
    review_required: bool
    recommended_review_mode: str
    content_fingerprint: str
    created_at: str


@dataclass(frozen=True, slots=True)
class TerminologyMappingIssue:
    """One deterministic mapping or persistence issue."""

    project_id: str
    code: str
    message: str
    issue_level: str
    path: Path | None = None
    information_unit_id: str | None = None
    terminology_mapping_candidate_id: str | None = None
    persona_id: str | None = None
    agent_id: str | None = None
    persona_run_index: int | None = None


@dataclass(frozen=True, slots=True)
class TerminologyMappingScanResult:
    """Validated mapping candidates and blocking persistence issues."""

    candidates: tuple[TerminologyMappingCandidate, ...] = ()
    issues: tuple[TerminologyMappingIssue, ...] = ()