"""Immutable data types for framework-assignment candidates."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


FRAMEWORK_ASSIGNMENT_STATUSES = frozenset(
    {
        "assigned",
        "unassigned",
        "ambiguous",
        "conflict",
    }
)

FRAMEWORK_ASSIGNMENT_BASIS_TYPES = frozenset(
    {
        "information_unit",
        "terminology_mapping_candidate",
        "turing_core_concept",
        "semantic_interpretation",
    }
)

FRAMEWORK_ASSIGNMENT_CONFIDENCE_LEVELS = frozenset(
    {
        "high",
        "medium",
        "low",
    }
)

FRAMEWORK_ASSIGNMENT_CONSENSUS_LEVELS = frozenset(
    {
        "unanimous",
        "majority",
        "single",
        "none",
        "incomparable",
        "incomplete",
    }
)

FRAMEWORK_ASSIGNMENT_VARIANCE_LEVELS = frozenset(
    {
        "low",
        "medium",
        "high",
    }
)

FRAMEWORK_ASSIGNMENT_REVIEW_MODES = frozenset(
    {
        "quick_confirmation",
        "detailed_review",
    }
)

FRAMEWORK_ASSIGNMENT_ISSUE_LEVELS = frozenset(
    {
        "warning",
        "blocking",
    }
)


@dataclass(frozen=True, slots=True)
class FrameworkAssignmentBasis:
    """One versioned evidence reference supporting an assignment."""

    basis_type: str
    reference_id: str
    reference_version: str | None
    rationale: str


@dataclass(frozen=True, slots=True)
class FrameworkAssignmentProposal:
    """One proposed assignment to one stable framework node."""

    framework_node_id: str
    assignment_bases: tuple[FrameworkAssignmentBasis, ...]
    rationale: str


@dataclass(frozen=True, slots=True)
class FrameworkAssignmentAgentCandidate:
    """One result-local proposal set from one configured persona run."""

    framework_assignment_agent_candidate_id: str
    information_unit_id: str
    assignment_status: str
    proposals: tuple[FrameworkAssignmentProposal, ...]
    rationale: str
    uncertainties: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class FrameworkAssignmentAgentResult:
    """Immutable framework-assignment output of one persona run."""

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
    framework_template_id: str
    framework_template_version: str
    turing_core_version: str
    project_glossary_revision: int
    terminology_mapping_candidate_ids: tuple[str, ...]
    candidates: tuple[FrameworkAssignmentAgentCandidate, ...]
    no_candidate_rationale: str | None
    created_at: str


@dataclass(frozen=True, slots=True)
class FrameworkAssignmentAgentCandidateReference:
    """Unambiguous reference to one persona-run assignment candidate."""

    persona_id: str
    agent_id: str
    persona_run_index: int
    framework_assignment_agent_candidate_id: str


@dataclass(frozen=True, slots=True)
class FrameworkAssignmentValueDistribution:
    """One canonical assignment value and its persona support."""

    canonical_value: str
    display_value: str
    supporting_personas: tuple[str, ...]
    candidate_references: tuple[
        FrameworkAssignmentAgentCandidateReference,
        ...
    ]


@dataclass(frozen=True, slots=True)
class FrameworkAssignmentConsensusOutcome:
    """Deterministic consensus for one Information Unit."""

    information_unit_id: str
    assignment_status: str
    selected_proposals: tuple[
        FrameworkAssignmentProposal,
        ...
    ]
    candidate_references: tuple[
        FrameworkAssignmentAgentCandidateReference,
        ...
    ]
    value_distribution: tuple[
        FrameworkAssignmentValueDistribution,
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
class FrameworkAssignmentCandidate:
    """One immutable persisted assignment candidate without authority."""

    schema_version: str
    project_id: str
    source_id: str
    source_projection_id: str
    information_unit_id: str
    framework_assignment_candidate_id: str
    assignment_status: str
    proposals: tuple[FrameworkAssignmentProposal, ...]
    candidate_references: tuple[
        FrameworkAssignmentAgentCandidateReference,
        ...
    ]
    team_id: str
    required_personas: tuple[str, ...]
    llm_provider: str
    llm_model: str
    prompt_schema_version: str
    framework_template_id: str
    framework_template_version: str
    turing_core_version: str
    project_glossary_revision: int
    terminology_mapping_candidate_ids: tuple[str, ...]
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
class FrameworkAssignmentIssue:
    """One deterministic assignment or persistence issue."""

    project_id: str
    code: str
    message: str
    issue_level: str
    path: Path | None = None
    information_unit_id: str | None = None
    framework_assignment_candidate_id: str | None = None
    persona_id: str | None = None
    agent_id: str | None = None
    persona_run_index: int | None = None


@dataclass(frozen=True, slots=True)
class FrameworkAssignmentScanResult:
    """Validated assignment candidates and persistence issues."""

    candidates: tuple[FrameworkAssignmentCandidate, ...] = ()
    issues: tuple[FrameworkAssignmentIssue, ...] = ()