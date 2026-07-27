"""Immutable foundation types for the P7 Project Dashboard."""

from __future__ import annotations

from dataclasses import dataclass


DASHBOARD_STATUS_SEMANTICS = frozenset(
    {
        "neutral",
        "informational",
        "candidate",
        "reviewed",
        "attention",
        "blocking",
        "unavailable",
    }
)

DASHBOARD_EVIDENCE_ROLES = frozenset(
    {
        "direct",
        "contextual",
    }
)

DASHBOARD_NAVIGATION_MODES = frozenset(
    {
        "unavailable",
        "direct",
        "chooser",
    }
)

DASHBOARD_ISSUE_LEVELS = frozenset(
    {
        "warning",
        "blocking",
    }
)

DASHBOARD_DOCUMENT_RENDER_MODES = frozenset(
    {
        "json",
        "markdown",
        "text",
        "table",
        "metadata",
    }
)

DASHBOARD_FINGERPRINT_STATUSES = frozenset(
    {
        "not_provided",
        "verified",
    }
)

DASHBOARD_TRACEABILITY_NODE_TYPES = frozenset(
    {
        "source",
        "processing_run",
        "source_projection",
        "information_unit",
        "terminology_mapping_candidate",
        "framework_assignment_candidate",
        "human_review_decision",
        "framework_node",
        "support_target",
    }
)


@dataclass(frozen=True, slots=True)
class EvidenceLocation:
    """Optional precise location inside one referenced document."""

    section_anchor: str | None = None
    line_start: int | None = None
    line_end: int | None = None
    json_pointer: str | None = None
    table_row_key: str | None = None


@dataclass(frozen=True, slots=True)
class EvidenceReference:
    """One immutable, project-bound dashboard reference to an artifact."""

    project_id: str
    reference_type: str
    reference_id: str
    display_label: str
    repository_relative_path: str
    content_fingerprint: str | None
    media_type: str
    source_role: str | None
    relationship: str
    evidence_role: str
    location: EvidenceLocation | None = None


@dataclass(frozen=True, slots=True)
class EvidenceNavigation:
    """Deterministic navigation behavior for zero, one or many references."""

    mode: str
    references: tuple[EvidenceReference, ...]


@dataclass(frozen=True, slots=True)
class DashboardStatus:
    """Text, icon and semantic status without decorative color ownership."""

    state: str
    label: str
    semantic: str
    icon: str
    explanation: str | None = None


@dataclass(frozen=True, slots=True)
class DashboardValue:
    """One concise value rendered in a dashboard section."""

    value_id: str
    label: str
    primary_text: str
    secondary_text: str | None
    status: DashboardStatus | None
    evidence: EvidenceNavigation


@dataclass(frozen=True, slots=True)
class DashboardIssueView:
    """One warning or blocking issue prepared for dashboard rendering."""

    issue_code: str
    message: str
    issue_level: str
    status: DashboardStatus
    evidence: EvidenceNavigation


@dataclass(frozen=True, slots=True)
class DashboardSectionView:
    """One immutable, display-ready dashboard section."""

    section_id: str
    title: str
    description: str | None
    values: tuple[DashboardValue, ...]
    issues: tuple[DashboardIssueView, ...]


@dataclass(frozen=True, slots=True)
class DashboardProjectOption:
    """One deterministic project choice prepared for the dashboard UI."""

    project_id: str
    display_name: str
    description: str
    label: str
    framework_template_id: str
    framework_template_version: str
    evidence: EvidenceNavigation


@dataclass(frozen=True, slots=True)
class DashboardProjectSelection:
    """All valid selectable projects and explicit workspace issues."""

    projects: tuple[DashboardProjectOption, ...]
    issues: tuple[DashboardIssueView, ...]


@dataclass(frozen=True, slots=True)
class ProjectOverviewView:
    """One selected project and its compact dashboard overview section."""

    project: DashboardProjectOption
    section: DashboardSectionView


@dataclass(frozen=True, slots=True)
class DashboardSourceProcessingRow:
    """One registered Source and its current derived P5 processing state."""

    project_id: str
    source_id: str
    original_filename: str
    source_role: str
    media_type: str
    size_bytes: int
    sha256: str
    processing_disposition: str
    current_processing_run_id: str | None
    run_state: str | None
    processing_stage: str | None
    latest_attempt_id: str | None
    pending_review: bool
    superseded_run_ids: tuple[str, ...]
    invalidated_artifact_count: int
    blocking_issue_codes: tuple[str, ...]
    failure_issue_codes: tuple[str, ...]
    disposition_status: DashboardStatus
    run_status: DashboardStatus
    evidence: EvidenceNavigation


@dataclass(frozen=True, slots=True)
class DashboardSourceProcessingView:
    """Detailed read-only Sources and Processing view for one project."""

    project_id: str
    project_state: str
    project_status: DashboardStatus
    sources: tuple[DashboardSourceProcessingRow, ...]
    issues: tuple[DashboardIssueView, ...]


@dataclass(frozen=True, slots=True)
class DashboardFrameworkLevelCoverage:
    """Display-ready P6 coverage summary for one framework level."""

    display_order: int
    level_node_id: str
    level_name: str
    coverage_state: str
    covered_node_count: int
    total_node_count: int
    candidate_covered_node_count: int
    reviewed_candidate_covered_node_count: int
    attention_node_count: int
    covered_node_ids: tuple[str, ...]
    uncovered_node_ids: tuple[str, ...]
    attention_node_ids: tuple[str, ...]
    status: DashboardStatus
    attention_status: DashboardStatus | None
    evidence: EvidenceNavigation


@dataclass(frozen=True, slots=True)
class DashboardFrameworkNodeCoverage:
    """Display-ready P6 coverage and trace identifiers for one framework node."""

    display_order: int
    framework_node_id: str
    mapping_key: str
    node_name: str
    level_node_id: str
    coverage_state: str
    attention_required: bool
    eligible_source_count: int
    information_unit_count: int
    assignment_candidate_count: int
    confirmed_candidate_count: int
    unreviewed_candidate_count: int
    rejected_candidate_count: int
    ambiguous_candidate_count: int
    conflicting_candidate_count: int
    source_ids: tuple[str, ...]
    information_unit_ids: tuple[str, ...]
    framework_assignment_candidate_ids: tuple[str, ...]
    human_review_decision_ids: tuple[str, ...]
    issue_codes: tuple[str, ...]
    status: DashboardStatus
    attention_status: DashboardStatus | None
    evidence: EvidenceNavigation


@dataclass(frozen=True, slots=True)
class DashboardPotentialSupport:
    """Display-ready P6 potential support result for one model scope."""

    display_order: int
    support_target_id: str
    name: str
    support_target_type: str
    support_state: str
    required_framework_node_ids: tuple[str, ...]
    covered_framework_node_ids: tuple[str, ...]
    missing_framework_node_ids: tuple[str, ...]
    required_support_target_ids: tuple[str, ...]
    satisfied_support_target_ids: tuple[str, ...]
    unsatisfied_support_target_ids: tuple[str, ...]
    attention_required: bool
    issue_codes: tuple[str, ...]
    status: DashboardStatus
    attention_status: DashboardStatus | None
    evidence: EvidenceNavigation


@dataclass(frozen=True, slots=True)
class DashboardCoverageView:
    """Detailed Preliminary Coverage and potential-support view."""

    project_id: str
    project_coverage_state: str
    project_status: DashboardStatus
    framework_template_id: str
    framework_template_version: str
    support_profile_id: str
    support_profile_version: str
    levels: tuple[DashboardFrameworkLevelCoverage, ...]
    nodes: tuple[DashboardFrameworkNodeCoverage, ...]
    support_targets: tuple[DashboardPotentialSupport, ...]
    approved_readiness_status: str
    approved_readiness_available_from_phase: str
    approved_readiness: DashboardStatus
    issues: tuple[DashboardIssueView, ...]



@dataclass(frozen=True, slots=True)
class DashboardHumanReviewRow:
    """One exact immutable Human Review Decision prepared for display."""

    project_id: str
    human_review_decision_id: str
    target_type: str
    target_id: str
    target_content_fingerprint: str
    reference_validation_status: str
    reference_validation_fingerprint: str | None
    review_mode: str
    decision: str
    reviewer_identity: str
    rationale: str | None
    decided_at: str
    decision_fingerprint: str
    status: DashboardStatus
    evidence: EvidenceNavigation


@dataclass(frozen=True, slots=True)
class DashboardAttentionReviewView:
    """Project attention and Human Review information."""

    project_id: str
    status: DashboardStatus
    reviews: tuple[DashboardHumanReviewRow, ...]
    issues: tuple[DashboardIssueView, ...]


@dataclass(frozen=True, slots=True)
class DashboardTraceabilityNode:
    """One typed node in the read-only project traceability graph."""

    node_key: str
    node_type: str
    node_id: str
    label: str
    secondary_text: str | None
    status: DashboardStatus | None
    evidence: EvidenceNavigation


@dataclass(frozen=True, slots=True)
class DashboardTraceabilityEdge:
    """One deterministic directed relationship between traceability nodes."""

    edge_key: str
    source_node_key: str
    target_node_key: str
    relationship: str
    label: str


@dataclass(frozen=True, slots=True)
class DashboardTraceabilityView:
    """Complete deterministic project traceability graph."""

    project_id: str
    nodes: tuple[DashboardTraceabilityNode, ...]
    edges: tuple[DashboardTraceabilityEdge, ...]
    issues: tuple[DashboardIssueView, ...]


@dataclass(frozen=True, slots=True)
class DashboardDocumentPreview:
    """Safe immutable payload for the internal dashboard document viewer."""

    project_id: str
    reference: EvidenceReference
    repository_relative_path: str
    title: str
    media_type: str
    file_size_bytes: int
    actual_sha256: str
    fingerprint_status: str
    render_mode: str
    content_text: str | None
    highlighted_text: str | None
    table_columns: tuple[str, ...]
    table_rows: tuple[tuple[str, ...], ...]
    selected_json_pointer: str | None
    selected_table_row_key: str | None
    truncated: bool
    issue: str | None
