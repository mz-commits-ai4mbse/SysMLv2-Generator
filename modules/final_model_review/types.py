"""Immutable domain types for Phase-L Final Model Review."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


FINAL_MODEL_REVIEW_LIFECYCLE_STATES = (
    "generated",
    "validation_blocked",
    "review_pending",
    "changes_requested",
    "regeneration_required",
    "ready_for_approval",
    "approved_for_publication",
    "published",
)

FINAL_MODEL_REVIEW_ITEM_KINDS = (
    "generated_unit",
    "generated_symbol",
    "relationship",
    "validation_finding",
    "model_structure",
    "agent_proposal",
    "general",
)

FINAL_MODEL_REVIEW_EVIDENCE_TYPES = (
    "candidate_review_decision",
    "approved_input",
    "agent_proposal",
    "generation_rationale",
    "accepted_exception",
    "validation_finding",
    "other",
)

FINAL_MODEL_REVIEW_DECISIONS = (
    "approved_for_publication",
    "changes_requested",
    "rejected",
)

FINAL_MODEL_REVIEW_VALIDATION_STATUSES = (
    "valid",
    "invalid",
    "incomplete",
)

FINAL_MODEL_REVIEW_PUBLICATION_GATES = (
    "passed",
    "blocked",
)


@dataclass(frozen=True, slots=True)
class FinalModelGeneratedUnitReference:
    """Exact generated unit presented in one Final Model Review revision."""

    generated_unit_id: str
    relative_path: str
    content_fingerprint: str


@dataclass(frozen=True, slots=True)
class FinalModelReviewEvidenceReference:
    """Exact upstream evidence made available to Final Model Review."""

    evidence_type: str
    reference_id: str
    content_fingerprint: str


@dataclass(frozen=True, slots=True)
class FinalModelReviewManifest:
    """Immutable identity container for one long-lived Final Model Review."""

    schema_version: str
    project_id: str
    final_model_review_id: str
    created_at: str
    content_fingerprint: str


@dataclass(frozen=True, slots=True)
class FinalModelReviewRevision:
    """One immutable generated-model + validation review subject."""

    schema_version: str
    project_id: str
    final_model_review_id: str
    final_model_review_revision_id: str
    predecessor_revision_id: str | None
    source_internal_engineering_model_id: str
    generated_artifact_set_fingerprint: str
    validation_result_fingerprint: str
    validation_status: str
    publication_gate: str
    generated_units: tuple[FinalModelGeneratedUnitReference, ...]
    evidence_references: tuple[FinalModelReviewEvidenceReference, ...]
    review_subject_fingerprint: str
    created_at: str
    content_fingerprint: str


@dataclass(frozen=True, slots=True)
class FinalModelReviewItem:
    """One immutable Human-attention item bound to one exact review revision."""

    schema_version: str
    project_id: str
    final_model_review_id: str
    final_model_review_revision_id: str
    final_model_review_item_id: str
    item_kind: str
    summary: str
    detail: str | None
    mandatory: bool
    generated_unit_id: str | None
    generated_symbol_id: str | None
    evidence_references: tuple[FinalModelReviewEvidenceReference, ...]
    content_fingerprint: str


@dataclass(frozen=True, slots=True)
class FinalModelReviewDecisionTargetSnapshot:
    """Exact immutable Final Model Review revision presented for Human decision."""

    final_model_review_id: str
    final_model_review_revision_id: str
    revision_content_fingerprint: str
    review_subject_fingerprint: str
    generated_artifact_set_fingerprint: str
    validation_result_fingerprint: str
    validation_status: str
    publication_gate: str


@dataclass(frozen=True, slots=True)
class FinalModelReviewDecision:
    """One immutable Human decision for one exact Final Model Review revision."""

    schema_version: str
    project_id: str
    final_model_review_decision_id: str
    target: FinalModelReviewDecisionTargetSnapshot
    decision: str
    reviewer_identity: str
    rationale: str | None
    reviewed_at: str
    decision_fingerprint: str


FINAL_MODEL_REVIEW_STORED_FILE_ROLES = (
    "revision",
    "artifact_set_snapshot",
    "validation_result_snapshot",
    "generated_sysml_unit",
)


@dataclass(frozen=True, slots=True)
class FinalModelReviewStoredFileReference:
    relative_path: str
    role: str
    content_fingerprint: str
    source_generated_unit_id: str | None = None


@dataclass(frozen=True, slots=True)
class FinalModelReviewRevisionStorageManifest:
    schema_version: str
    project_id: str
    final_model_review_id: str
    final_model_review_revision_id: str
    revision_content_fingerprint: str
    files: tuple[FinalModelReviewStoredFileReference, ...]
    content_fingerprint: str


@dataclass(frozen=True, slots=True)
class FinalModelReviewStoredGeneratedUnit:
    generated_unit_id: str
    relative_path: str
    content: str
    content_fingerprint: str


@dataclass(frozen=True, slots=True)
class FinalModelReviewRevisionBundle:
    revision: FinalModelReviewRevision
    storage_manifest: FinalModelReviewRevisionStorageManifest
    artifact_set_snapshot: dict[str, object]
    validation_result_snapshot: dict[str, object]
    generated_units: tuple[FinalModelReviewStoredGeneratedUnit, ...]


@dataclass(frozen=True, slots=True)
class FinalModelReviewRepositoryIssue:
    project_id: str
    code: str
    message: str
    issue_level: str
    path: Path | None = None
    final_model_review_id: str | None = None
    final_model_review_revision_id: str | None = None
    final_model_review_item_id: str | None = None
    final_model_review_decision_id: str | None = None


@dataclass(frozen=True, slots=True)
class FinalModelReviewRepositoryScanResult:
    review_manifests: tuple[FinalModelReviewManifest, ...] = ()
    revisions: tuple[FinalModelReviewRevisionBundle, ...] = ()
    items: tuple[FinalModelReviewItem, ...] = ()
    decisions: tuple[FinalModelReviewDecision, ...] = ()
    change_proposals: tuple[FinalModelReviewChangeProposal, ...] = ()
    issues: tuple[FinalModelReviewRepositoryIssue, ...] = ()


FINAL_MODEL_REVIEW_CHANGE_SURFACES = (
    "sysml_code",
    "diagram",
    "validation_finding",
    "agent_proposal",
    "review_comment",
)

FINAL_MODEL_REVIEW_CHANGE_CLASSIFICATIONS = (
    "engineering_semantics",
    "generated_representation",
    "validation_policy_or_tool",
    "review_presentation_only",
)

FINAL_MODEL_REVIEW_CHANGE_ROUTES = (
    "phase_h_candidate_review",
    "phase_j_generation",
    "phase_k_validation",
    "phase_l_presentation",
)

AGENT_REPROPOSAL_REQUEST_STATUSES = (
    "not_requested",
    "requested",
)


@dataclass(frozen=True, slots=True)
class FinalModelReviewChangeTarget:
    """Exact review surface targeted by one Human change proposal."""

    generated_unit_id: str | None
    generated_unit_content_fingerprint: str | None
    generated_symbol_id: str | None
    internal_model_element_id: str | None
    internal_model_relationship_id: str | None
    validation_finding_code: str | None


@dataclass(frozen=True, slots=True)
class FinalModelReviewChangeProposal:
    """Immutable Human change request bound to one exact review revision."""

    schema_version: str
    project_id: str
    final_model_review_id: str
    final_model_review_revision_id: str
    final_model_review_change_proposal_id: str
    base_revision_content_fingerprint: str
    base_review_subject_fingerprint: str
    surface: str
    classification: str
    authority_route: str
    target: FinalModelReviewChangeTarget
    original_text: str | None
    proposed_text: str | None
    reviewer_feedback: str
    agent_reproposal_request_status: str
    requested_agent_personalities: tuple[str, ...]
    created_by: str
    created_at: str
    content_fingerprint: str


@dataclass(frozen=True, slots=True)
class FinalModelReviewChangeRoute:
    """Deterministic routing outcome; never a model mutation."""

    classification: str
    authority_route: str
    required_action: str
    requires_candidate_review: bool
    requires_regeneration: bool
    requires_revalidation: bool
    requires_new_review_revision: bool


@dataclass(frozen=True, slots=True)
class FinalModelReviewAgentReproposalRequest:
    """Bounded agent/LLM handoff created from explicit Human feedback."""

    project_id: str
    final_model_review_id: str
    final_model_review_revision_id: str
    final_model_review_change_proposal_id: str
    change_proposal_fingerprint: str
    authority_route: str
    reviewer_feedback: str
    requested_agent_personalities: tuple[str, ...]
    source_model_candidate_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class FinalModelReviewChangeSubmission:
    """Result of recording one Human change proposal and routing it."""

    proposal: FinalModelReviewChangeProposal
    route: FinalModelReviewChangeRoute
    agent_reproposal_request: FinalModelReviewAgentReproposalRequest | None


@dataclass(frozen=True, slots=True)
class FinalModelReviewCodeLocationView:
    """One deterministic generated-code location for UI navigation."""

    generated_unit_id: str
    generated_symbol_id: str
    start_line: int | None
    end_line: int | None


@dataclass(frozen=True, slots=True)
class FinalModelReviewCodeUnitView:
    """Exact generated SysML code exposed to the Final Model Review UI."""

    generated_unit_id: str
    relative_path: str
    content: str
    content_fingerprint: str
    generated_symbol_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class FinalModelReviewDiagramNodeView:
    """One explanatory diagram node derived from the exact source IEM."""

    internal_model_element_id: str
    generated_symbol_id: str | None
    label: str
    description: str | None
    model_area: str
    element_type: str
    framework_assignment: str
    source_model_candidate_id: str | None
    review_decision_id: str | None
    code_location: FinalModelReviewCodeLocationView | None
    authority_ids: tuple[str, ...] = ()
    authority_types: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class FinalModelReviewDiagramEdgeView:
    """One explanatory diagram edge derived from the exact source IEM."""

    internal_model_relationship_id: str
    generated_symbol_id: str | None
    source_internal_model_element_id: str
    target_internal_model_element_id: str
    relationship_family: str
    semantic_intent: str
    directionality: str
    source_model_candidate_id: str | None
    review_decision_id: str | None
    code_location: FinalModelReviewCodeLocationView | None
    authority_ids: tuple[str, ...] = ()
    authority_types: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class FinalModelReviewDiagramView:
    """Non-authoritative graph projection for Final Model Review."""

    nodes: tuple[FinalModelReviewDiagramNodeView, ...]
    edges: tuple[FinalModelReviewDiagramEdgeView, ...]
    model_areas: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class FinalModelReviewValidationFindingView:
    """One normalized K finding projected into the review UI."""

    code: str
    category: str
    severity: str
    blocking: bool
    message: str
    generated_unit_id: str | None
    generated_symbol_id: str | None
    start_line: int | None
    end_line: int | None
    start_column: int | None
    end_column: int | None
    validator_id: str | None
    validator_rule_id: str | None


@dataclass(frozen=True, slots=True)
class FinalModelReviewTraceabilityView:
    """UI-ready generated-symbol trace without changing authority."""

    generated_unit_id: str
    generated_symbol_id: str
    start_line: int | None
    end_line: int | None
    source_internal_model_element_id: str | None
    source_internal_model_relationship_id: str | None
    source_model_candidate_id: str | None
    approved_input_ids: tuple[str, ...]
    review_decision_id: str | None
    accepted_exception_decision_id: str | None
    authority_ids: tuple[str, ...] = ()
    authority_types: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class FinalModelReviewExternalValidatorView:
    """Exact external-validator evidence projected into Final Model Review."""

    tool_name: str
    tool_version: str | None
    execution_status: str
    exit_code: int | None
    normalized_diagnostic_count: int


@dataclass(frozen=True, slots=True)
class FinalModelReviewAgentProposalView:
    """Optional resolved agent/personality proposal evidence for review."""

    reference_id: str
    content_fingerprint: str
    resolution_status: str
    agent_identity: str | None
    personality: str | None
    proposal_summary: str | None
    rationale: str | None
    confidence: str | None
    alternatives: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class FinalModelReviewView:
    """Deterministic non-authoritative presentation of one exact review revision."""

    project_id: str
    final_model_review_id: str
    final_model_review_revision_id: str
    source_internal_engineering_model_id: str
    generated_artifact_set_fingerprint: str
    validation_result_fingerprint: str
    validation_status: str
    publication_gate: str
    review_state: str
    summary: str
    code_units: tuple[FinalModelReviewCodeUnitView, ...]
    diagram: FinalModelReviewDiagramView
    validation_findings: tuple[FinalModelReviewValidationFindingView, ...]
    traceability: tuple[FinalModelReviewTraceabilityView, ...]
    candidate_proposal: object
    agent_proposals: tuple[FinalModelReviewAgentProposalView, ...]
    review_items: tuple[FinalModelReviewItem, ...]
    review_decisions: tuple[FinalModelReviewDecision, ...]
    change_proposals: tuple[FinalModelReviewChangeProposal, ...]
    required_human_actions: tuple[str, ...]
    next_action: str
    external_validator_evidence: tuple[FinalModelReviewExternalValidatorView, ...] = ()


FINAL_MODEL_REVIEW_RELEASE_STATUSES = (
    "blocked",
    "ready_for_approval",
    "approved_for_publication",
)


@dataclass(frozen=True, slots=True)
class FinalModelReviewReleaseBlocker:
    """One deterministic reason why an exact FRV cannot be released."""

    code: str
    message: str
    reference_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class FinalModelReviewReleaseGateResult:
    """Deterministic Human-release readiness for one explicitly addressed FRV."""

    project_id: str
    final_model_review_id: str
    final_model_review_revision_id: str
    revision_content_fingerprint: str
    review_subject_fingerprint: str
    generated_artifact_set_fingerprint: str
    validation_result_fingerprint: str
    validation_status: str
    publication_gate: str
    release_status: str
    approval_decision_id: str | None
    blockers: tuple[FinalModelReviewReleaseBlocker, ...]
    evaluation_fingerprint: str


@dataclass(frozen=True, slots=True)
class FinalModelReviewReleaseApproval:
    """Result of one explicit Human approval through the normative L5 gate."""

    gate: FinalModelReviewReleaseGateResult
    decision: FinalModelReviewDecision
