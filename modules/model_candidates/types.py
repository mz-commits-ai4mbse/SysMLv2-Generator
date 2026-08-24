"""Immutable foundation types for the Phase-H Model Candidate layer."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from modules.approved_engineering_information import (
    ApprovedEngineeringInformationSet,
)
from modules.approved_input.types import (
    ApprovedInputManifest,
    ApprovedInputRelationshipRepresentation,
)
from modules.project_workspace.types import FrameworkTemplateReference


MODEL_CANDIDATE_SUPPORT_LEVELS = frozenset(
    {
        "supported",
        "partially_supported",
        "conflicting",
    }
)

MODEL_RELATIONSHIP_PRIORITY_CLASSES = frozenset(
    {
        "preferred",
        "supported_alternative",
        "exception_candidate",
    }
)

STRUCTURAL_COMPARABILITY_IMPACTS = frozenset(
    {
        "improves",
        "neutral",
        "reduces",
        "unknown",
    }
)

RELATIONSHIP_ENDPOINT_RESOLUTION_STATUSES = frozenset(
    {
        "resolved",
        "unresolved",
        "ambiguous",
    }
)


MODEL_CANDIDATE_PROJECTION_DISPOSITIONS = frozenset(
    {
        "mapped",
        "ambiguous",
        "unmapped",
        "intentionally_not_projected",
    }
)


@dataclass(frozen=True, slots=True)
class ModelCandidateProjectionDisposition:
    """One explicit target-projection outcome for one Approved Input."""

    approved_input_id: str
    approved_input_kind: str
    disposition: str
    reason_code: str
    selected_rule_id: str | None
    candidate_rule_ids: tuple[str, ...]
    rationale: str


@dataclass(frozen=True, slots=True)
class ModelCandidateProjectionCoverage:
    """Complete non-persistent projection coverage for one input snapshot."""

    project_id: str
    model_structure_profile_reference: ModelStructureProfileReference
    entries: tuple[ModelCandidateProjectionDisposition, ...]

    @property
    def total_count(self) -> int:
        return len(self.entries)

    def count(self, disposition: str) -> int:
        return sum(
            1
            for item in self.entries
            if item.disposition == disposition
        )

    @property
    def mapped_count(self) -> int:
        return self.count("mapped")

    @property
    def ambiguous_count(self) -> int:
        return self.count("ambiguous")

    @property
    def unmapped_count(self) -> int:
        return self.count("unmapped")

    @property
    def intentionally_not_projected_count(self) -> int:
        return self.count("intentionally_not_projected")

    @property
    def unresolved_approved_input_ids(self) -> tuple[str, ...]:
        return tuple(
            item.approved_input_id
            for item in self.entries
            if item.approved_input_kind != "semantic_relationship"
            and item.disposition in {"ambiguous", "unmapped"}
        )

    @property
    def unresolved_semantic_relationship_ids(self) -> tuple[str, ...]:
        return tuple(
            item.approved_input_id
            for item in self.entries
            if item.approved_input_kind == "semantic_relationship"
            and item.disposition in {"ambiguous", "unmapped"}
        )

    @property
    def approved_input_count(self) -> int:
        return sum(
            1 for item in self.entries
            if item.approved_input_kind != "semantic_relationship"
        )

    @property
    def semantic_relationship_count(self) -> int:
        return sum(
            1 for item in self.entries
            if item.approved_input_kind == "semantic_relationship"
        )

    @property
    def is_complete(self) -> bool:
        return (
            self.mapped_count
            + self.ambiguous_count
            + self.unmapped_count
            + self.intentionally_not_projected_count
            == self.total_count
        )


@dataclass(frozen=True, slots=True)
class ModelCandidateApprovedInputReference:
    """Exact Approved-Input provenance retained by one Candidate artifact."""

    approved_input_id: str
    content_fingerprint: str
    stable_subject_key: str
    provenance_role: str


@dataclass(frozen=True, slots=True)
class ModelStructureProfileReference:
    """Pinned identity of the Model Structure and Comparability Profile."""

    profile_id: str
    profile_version: str
    profile_fingerprint: str


@dataclass(frozen=True, slots=True)
class ModelDerivationRulesReference:
    """Pinned identity of the derivation rules applied to one Candidate Set."""

    context_id: str
    context_version: str
    context_fingerprint: str


@dataclass(frozen=True, slots=True)
class ModelCandidateGenerationProvenance:
    """Traceable description of how one Candidate Set was derived."""

    method: str
    recipe_reference: str | None
    agent_reference: str | None
    model_reference: str | None
    context_fingerprint: str | None


@dataclass(frozen=True, slots=True)
class ModelCandidateAttribute:
    """One immutable proposed attribute of an Element Candidate."""

    name: str
    value: str


@dataclass(frozen=True, slots=True)
class StructuralProfileConformance:
    """One Candidate's assessment against the pinned structure profile."""

    status: str
    finding_ids: tuple[str, ...]
    conformance_fingerprint: str


@dataclass(frozen=True, slots=True)
class ModelCandidateSetManifest:
    """Immutable snapshot boundary for one complete Phase-H proposal."""

    schema_version: str
    project_id: str
    candidate_set_id: str
    predecessor_candidate_set_id: str | None
    regeneration_reason: str | None
    approved_input_references: tuple[
        ModelCandidateApprovedInputReference,
        ...,
    ]
    approved_input_snapshot_fingerprint: str
    framework_template_reference: FrameworkTemplateReference
    model_structure_profile_reference: ModelStructureProfileReference
    derivation_rules_reference: ModelDerivationRulesReference
    generation_provenance: ModelCandidateGenerationProvenance
    element_candidate_ids: tuple[str, ...]
    relationship_candidate_ids: tuple[str, ...]
    created_at: str
    content_fingerprint: str


@dataclass(frozen=True, slots=True)
class ModelElementCandidate:
    """One immutable proposed model element derived in Phase H."""

    schema_version: str
    project_id: str
    candidate_set_id: str
    model_element_candidate_id: str
    candidate_subject_key: str
    comparison_anchor_id: str | None
    proposed_name: str
    description: str | None
    model_area: str
    element_type: str
    framework_assignment: str | None
    terminology_assignment: str | None
    attributes: tuple[ModelCandidateAttribute, ...]
    approved_input_references: tuple[
        ModelCandidateApprovedInputReference,
        ...,
    ]
    derivation_rationale: str
    support_level: str
    assumptions: tuple[str, ...]
    missing_information: tuple[str, ...]
    structure_profile_conformance: StructuralProfileConformance
    predecessor_candidate_ids: tuple[str, ...]
    created_at: str
    content_fingerprint: str


@dataclass(frozen=True, slots=True)
class ModelRelationshipEndpoint:
    """Resolution state for one relationship endpoint."""

    candidate_subject_key: str
    resolution_status: str
    resolved_model_element_candidate_id: str | None
    candidate_model_element_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RelationshipPriorityCriterionResult:
    """Machine-readable result for one advisory priority criterion."""

    criterion: str
    result: str
    rationale: str


@dataclass(frozen=True, slots=True)
class RelationshipPriorityAssessment:
    """Advisory relationship ranking with explicit rationale."""

    priority_class: str
    criterion_results: tuple[
        RelationshipPriorityCriterionResult,
        ...,
    ]
    rationale: str


@dataclass(frozen=True, slots=True)
class StructuralComparabilityAssessment:
    """Impact of one Candidate on cross-model structural comparability."""

    impact: str
    comparison_anchor_ids: tuple[str, ...]
    canonical_pattern_match: bool | None
    deviation_ids: tuple[str, ...]
    rationale: str


@dataclass(frozen=True, slots=True)
class ModelRelationshipCandidate:
    """One immutable proposed relationship between Element Candidates."""

    schema_version: str
    project_id: str
    candidate_set_id: str
    model_relationship_candidate_id: str
    relationship_choice_key: str | None
    source: ModelRelationshipEndpoint
    target: ModelRelationshipEndpoint
    relationship_family: str
    semantic_intent: str
    directionality: str
    approved_input_references: tuple[
        ModelCandidateApprovedInputReference,
        ...,
    ]
    derivation_rationale: str
    supporting_evidence: tuple[str, ...]
    assumptions: tuple[str, ...]
    missing_information: tuple[str, ...]
    priority_assessment: RelationshipPriorityAssessment
    comparability_assessment: StructuralComparabilityAssessment
    structure_profile_conformance: StructuralProfileConformance
    upstream_relationship_representation: (
        ApprovedInputRelationshipRepresentation | None
    )
    predecessor_candidate_ids: tuple[str, ...]
    created_at: str
    content_fingerprint: str


@dataclass(frozen=True, slots=True)
class ModelCandidateSetSnapshot:
    """One complete validated persisted Candidate Set bundle."""

    manifest: ModelCandidateSetManifest
    element_candidates: tuple[ModelElementCandidate, ...]
    relationship_candidates: tuple[ModelRelationshipCandidate, ...]


@dataclass(frozen=True, slots=True)
class ModelCandidateRepositoryIssue:
    """One deterministic blocking Candidate repository issue."""

    project_id: str
    code: str
    message: str
    issue_level: str
    path: Path | None
    candidate_set_id: str | None = None
    model_element_candidate_id: str | None = None
    model_relationship_candidate_id: str | None = None


@dataclass(frozen=True, slots=True)
class ModelCandidateRepositoryScanResult:
    """Validated Candidate Sets plus explicit repository diagnostics."""

    candidate_sets: tuple[ModelCandidateSetSnapshot, ...] = ()
    issues: tuple[ModelCandidateRepositoryIssue, ...] = ()


@dataclass(frozen=True, slots=True)
class ModelCandidateApprovedInputSelection:
    """Generation-time selection of one active Approved Input as evidence."""

    approved_input_id: str
    provenance_role: str


@dataclass(frozen=True, slots=True)
class ModelElementCandidateDraft:
    """Profile-derived Element proposal before persistent MCE identity."""

    draft_key: str
    candidate_subject_key: str
    comparison_anchor_id: str | None
    proposed_name: str
    description: str | None
    model_area: str
    element_type: str
    framework_assignment: str | None
    terminology_assignment: str | None
    attributes: tuple[ModelCandidateAttribute, ...]
    approved_input_selections: tuple[
        ModelCandidateApprovedInputSelection,
        ...,
    ]
    derivation_rationale: str
    support_level: str
    assumptions: tuple[str, ...]
    missing_information: tuple[str, ...]
    structure_profile_conformance: StructuralProfileConformance
    predecessor_candidate_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ModelRelationshipCandidateDraft:
    """Profile-derived Relationship proposal before persistent MCR identity."""

    draft_key: str
    relationship_choice_key: str | None
    source_subject_key: str
    target_subject_key: str
    relationship_family: str
    semantic_intent: str
    directionality: str
    approved_input_selections: tuple[
        ModelCandidateApprovedInputSelection,
        ...,
    ]
    derivation_rationale: str
    supporting_evidence: tuple[str, ...]
    assumptions: tuple[str, ...]
    missing_information: tuple[str, ...]
    priority_assessment: RelationshipPriorityAssessment
    comparability_assessment: StructuralComparabilityAssessment
    structure_profile_conformance: StructuralProfileConformance
    upstream_relationship_representation: (
        ApprovedInputRelationshipRepresentation | None
    )
    predecessor_candidate_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ModelCandidateDerivationRequest:
    """Complete joint Phase-H interpretation request for one active snapshot."""

    project_id: str
    approved_inputs: tuple[ApprovedInputManifest, ...]
    framework_template_reference: FrameworkTemplateReference
    model_structure_profile_reference: ModelStructureProfileReference
    derivation_rules_reference: ModelDerivationRulesReference
    predecessor_candidate_set: ModelCandidateSetSnapshot | None
    approved_engineering_information: (
        ApprovedEngineeringInformationSet | None
    ) = None


@dataclass(frozen=True, slots=True)
class ModelCandidateDerivationPlan:
    """Deterministic non-persistent proposal returned by a Phase-H deriver."""

    element_drafts: tuple[ModelElementCandidateDraft, ...] = ()
    relationship_drafts: tuple[ModelRelationshipCandidateDraft, ...] = ()


@dataclass(frozen=True, slots=True)
class ModelStructureAreaDefinition:
    """One profile-defined canonical modeling area."""

    model_area_id: str
    framework_node_id: str
    permitted_element_types: tuple[str, ...]
    comparison_anchor_prefix: str


@dataclass(frozen=True, slots=True)
class ModelElementDerivationRule:
    """Configuration rule mapping reviewed evidence to an Element shape."""

    rule_id: str
    model_area_id: str
    element_type: str
    classification_values: tuple[str, ...]
    framework_assignment_values: tuple[str, ...]
    information_type_values: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ModelRelationshipSemanticRule:
    """Profile-controlled engineering relationship semantic."""

    semantic_intent: str
    relationship_family: str
    directionality: str
    canonical: bool
    deviation_id: str | None


@dataclass(frozen=True, slots=True)
class ModelStructureProfile:
    """Immutable versioned Model Structure and Comparability Profile."""

    schema_version: str
    profile_id: str
    profile_version: str
    name: str
    status: str
    framework_template_id: str
    framework_template_version: str
    model_areas: tuple[ModelStructureAreaDefinition, ...]
    element_derivation_rules: tuple[ModelElementDerivationRule, ...]
    relationship_semantics: tuple[ModelRelationshipSemanticRule, ...]
    priority_criteria: tuple[str, ...]
    noncanonical_relationship_requires_exception: bool
    intentional_deviation_requires_rationale: bool
    profile_fingerprint: str


MODEL_CANDIDATE_REVIEW_TARGET_TYPES = frozenset(
    {
        "element_candidate",
        "relationship_candidate",
    }
)

MODEL_CANDIDATE_REVIEW_DECISIONS = frozenset(
    {
        "accepted",
        "rejected",
        "deferred",
        "accepted_exception",
    }
)


@dataclass(frozen=True, slots=True)
class ModelCandidateReviewTargetSnapshot:
    """Exact immutable Candidate snapshot presented for authorization."""

    candidate_set_id: str
    candidate_set_content_fingerprint: str
    target_type: str
    candidate_id: str
    candidate_content_fingerprint: str
    model_structure_profile_reference: ModelStructureProfileReference
    structure_profile_conformance_status: str
    structure_profile_conformance_fingerprint: str
    approved_input_snapshot_fingerprint: str


@dataclass(frozen=True, slots=True)
class ModelCandidateReviewDecision:
    """One immutable human authorization decision for exact Candidate content."""

    schema_version: str
    project_id: str
    model_candidate_review_decision_id: str
    target: ModelCandidateReviewTargetSnapshot
    decision: str
    reviewer_identity: str
    rationale: str | None
    reviewed_at: str
    decision_fingerprint: str


@dataclass(frozen=True, slots=True)
class ModelCandidateReviewIssue:
    """One deterministic Candidate Review persistence or integrity issue."""

    project_id: str
    code: str
    message: str
    issue_level: str
    path: Path | None = None
    model_candidate_review_decision_id: str | None = None
    candidate_set_id: str | None = None
    target_type: str | None = None
    candidate_id: str | None = None


@dataclass(frozen=True, slots=True)
class ModelCandidateReviewScanResult:
    """Validated Candidate Review Decisions plus explicit blocking issues."""

    decisions: tuple[ModelCandidateReviewDecision, ...] = ()
    issues: tuple[ModelCandidateReviewIssue, ...] = ()


@dataclass(frozen=True, slots=True)
class ModelCandidateReviewDecisionReference:
    """Compact immutable Phase-I traceability reference to one review decision."""

    model_candidate_review_decision_id: str
    target_type: str
    candidate_id: str
    decision: str
    decision_fingerprint: str


@dataclass(frozen=True, slots=True)
class ModelCandidateAssemblyInput:
    """Sole validated Phase-H → Phase-I authority transfer object."""

    project_id: str
    candidate_set_id: str
    candidate_set_content_fingerprint: str
    approved_input_snapshot_fingerprint: str
    approved_input_references: tuple[
        ModelCandidateApprovedInputReference,
        ...,
    ]
    framework_template_reference: FrameworkTemplateReference
    model_structure_profile_reference: ModelStructureProfileReference
    derivation_rules_reference: ModelDerivationRulesReference
    generation_provenance: ModelCandidateGenerationProvenance
    accepted_element_candidates: tuple[ModelElementCandidate, ...]
    accepted_relationship_candidates: tuple[
        ModelRelationshipCandidate,
        ...,
    ]
    accepted_exception_decisions: tuple[
        ModelCandidateReviewDecisionReference,
        ...,
    ]
    review_decision_references: tuple[
        ModelCandidateReviewDecisionReference,
        ...,
    ]


MODEL_PROPOSAL_REVIEW_STATES = frozenset(
    {
        "pending",
        "accepted",
        "rejected",
        "deferred",
        "accepted_exception",
        "stale",
    }
)

MODEL_PROPOSAL_PHASE_I_GATE_STATUSES = frozenset(
    {
        "not_ready",
        "blocked",
        "ready",
    }
)


@dataclass(frozen=True, slots=True)
class ModelProposalReviewState:
    """Current presentation state of Human Review for one Candidate."""

    status: str
    decision_id: str | None
    decision_fingerprint: str | None
    rationale: str | None


@dataclass(frozen=True, slots=True)
class ModelProposalElementView:
    """Human-facing deterministic projection of one Element Candidate."""

    candidate_id: str
    candidate_subject_key: str
    proposed_name: str
    description: str | None
    model_area: str
    element_type: str
    comparison_anchor_id: str | None
    support_level: str
    conformance_status: str
    review_state: ModelProposalReviewState
    approved_input_ids: tuple[str, ...]
    assumptions: tuple[str, ...]
    missing_information: tuple[str, ...]
    rationale: str


@dataclass(frozen=True, slots=True)
class ModelProposalRelationshipView:
    """Human-facing deterministic projection of one Relationship Candidate."""

    candidate_id: str
    relationship_choice_key: str | None
    source_subject_key: str
    target_subject_key: str
    source_resolution_status: str
    target_resolution_status: str
    relationship_family: str
    semantic_intent: str
    directionality: str
    priority_class: str
    comparability_impact: str
    conformance_status: str
    review_state: ModelProposalReviewState
    approved_input_ids: tuple[str, ...]
    assumptions: tuple[str, ...]
    missing_information: tuple[str, ...]
    rationale: str


@dataclass(frozen=True, slots=True)
class ModelProposalStructuralNode:
    """One explanatory node for a lightweight architecture projection."""

    candidate_id: str
    label: str
    model_area: str
    element_type: str
    review_status: str


@dataclass(frozen=True, slots=True)
class ModelProposalStructuralEdge:
    """One explanatory edge; not formal SysML v2 notation."""

    candidate_id: str
    source_subject_key: str
    target_subject_key: str
    semantic_intent: str
    relationship_family: str
    review_status: str
    resolution_status: str


@dataclass(frozen=True, slots=True)
class ModelProposalStructuralOverview:
    """Lightweight graph projection suitable for later UI visualization."""

    nodes: tuple[ModelProposalStructuralNode, ...]
    edges: tuple[ModelProposalStructuralEdge, ...]
    model_areas: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ModelProposalRelationshipChoiceGroup:
    """One group of materially distinct Relationship alternatives."""

    relationship_choice_key: str
    candidate_ids: tuple[str, ...]
    preferred_candidate_ids: tuple[str, ...]
    accepted_candidate_ids: tuple[str, ...]
    review_required: bool


@dataclass(frozen=True, slots=True)
class ModelProposalComparabilitySummary:
    """Aggregated structural-comparability evidence for the proposal."""

    improves_count: int
    neutral_count: int
    reduces_count: int
    unknown_count: int
    comparison_anchor_ids: tuple[str, ...]
    deviation_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ModelProposalProfileDeviation:
    """One profile finding or explicit structural deviation."""

    target_type: str
    candidate_id: str
    conformance_status: str
    finding_ids: tuple[str, ...]
    deviation_ids: tuple[str, ...]
    review_status: str
    rationale: str


@dataclass(frozen=True, slots=True)
class ModelProposalRequiredDecision:
    """One concise user action required to progress the proposal."""

    decision_key: str
    target_type: str
    target_ids: tuple[str, ...]
    reason: str
    recommended_action: str


@dataclass(frozen=True, slots=True)
class ModelProposalBlockingIssue:
    """One non-review blocking issue affecting proposal progression."""

    code: str
    message: str


@dataclass(frozen=True, slots=True)
class ModelProposalView:
    """Deterministic non-authoritative presentation of one Candidate Set."""

    project_id: str
    candidate_set_id: str
    candidate_set_content_fingerprint: str
    summary: str
    proposed_elements: tuple[ModelProposalElementView, ...]
    proposed_relationships: tuple[ModelProposalRelationshipView, ...]
    structural_overview: ModelProposalStructuralOverview
    relationship_choice_groups: tuple[
        ModelProposalRelationshipChoiceGroup,
        ...,
    ]
    comparability_summary: ModelProposalComparabilitySummary
    profile_deviations: tuple[ModelProposalProfileDeviation, ...]
    required_human_decisions: tuple[
        ModelProposalRequiredDecision,
        ...,
    ]
    blocking_issues: tuple[ModelProposalBlockingIssue, ...]
    generation_rationale_summary: str
    phase_i_gate_status: str
    next_action: str
