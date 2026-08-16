"""Streamlit rendering for the read-only P7 Project Dashboard.

The module intentionally keeps Streamlit behind a function boundary so that
all rendering contracts can be tested without starting a Streamlit server.
"""

from __future__ import annotations

from contextlib import nullcontext
from dataclasses import dataclass
from html import escape
from pathlib import Path
import hashlib
from typing import Any, Iterable, Sequence

from modules.project_dashboard.errors import ProjectDashboardError
from modules.project_dashboard.service import ProjectDashboardService
from modules.project_dashboard.types import (
    DashboardAttentionReviewView,
    DashboardCoverageView,
    DashboardDocumentPreview,
    DashboardIssueView,
    DashboardProjectOption,
    DashboardProjectSelection,
    DashboardSourceProcessingView,
    DashboardStatus,
    DashboardTraceabilityView,
    EvidenceNavigation,
    EvidenceReference,
    ProjectOverviewView,
)
from app.global_controls import (
    SESSION_GLOBAL_CONTROLS_ACTIVE,
)
from app.turing_generator_navigation import (
    SESSION_DASHBOARD_VIEW,
    SESSION_PROJECT_ID,
)
from modules.project_dashboard.viewer import DashboardDocumentViewer
from modules.project_workspace import ProjectWorkspace
from modules.project_workspace.errors import ProjectWorkspaceError


_SESSION_PROJECT_ID = SESSION_PROJECT_ID
_SESSION_ACTIVE_VIEW = SESSION_DASHBOARD_VIEW
_SESSION_OPEN_REFERENCE = "project_dashboard.open_reference"
_SESSION_INLINE_REVIEW_REFERENCE = (
    "project_dashboard.inline_review_reference"
)
_SESSION_PROJECT_CHANGE_TOKEN = "project_dashboard.project_change_token"
_SESSION_PROJECT_SELECTOR = "project_dashboard.project_selector"
_SESSION_PENDING_PROJECT_ID = "project_dashboard.pending_project_id"

_VIEW_OPTIONS = (
    ("overview", "Overview"),
    ("sources", "Sources & Processing"),
    ("coverage", "Coverage & Support"),
    ("attention", "Attention & Review"),
    ("traceability", "Traceability"),
)

_STATUS_COLOR_TOKENS = {
    "neutral": ("#475569", "#f1f5f9", "#cbd5e1"),
    "informational": ("#1d4ed8", "#eff6ff", "#bfdbfe"),
    "candidate": ("#1d4ed8", "#eff6ff", "#93c5fd"),
    "reviewed": ("#166534", "#f0fdf4", "#bbf7d0"),
    "attention": ("#92400e", "#fffbeb", "#fde68a"),
    "blocking": ("#991b1b", "#fef2f2", "#fecaca"),
    "unavailable": ("#475569", "#f8fafc", "#cbd5e1"),
}


@dataclass(frozen=True, slots=True)
class EvidenceControl:
    """One display-ready evidence chooser row."""

    key: str
    label: str
    detail: str
    reference: EvidenceReference


@dataclass(frozen=True, slots=True)
class SourceEvidenceSections:
    """Human-oriented grouping of one Source row's evidence."""

    review_reports: tuple[EvidenceReference, ...]
    run_summaries: tuple[EvidenceReference, ...]
    consensus_reports: tuple[EvidenceReference, ...]
    agent_outputs: tuple[EvidenceReference, ...]
    technical_evidence: tuple[EvidenceReference, ...]


def render_project_dashboard_ui(
    project_root: Path,
    *,
    service: ProjectDashboardService | None = None,
    viewer: DashboardDocumentViewer | None = None,
    streamlit_module: Any | None = None,
    project_workspace: ProjectWorkspace | None = None,
) -> None:
    """Render the complete read-only Project Dashboard."""

    st = streamlit_module if streamlit_module is not None else _streamlit()
    root = Path(project_root)
    dashboard_service = (
        ProjectDashboardService(
            root=root / "data" / "projects",
            repository_root=root,
        )
        if service is None
        else service
    )
    document_viewer = (
        DashboardDocumentViewer(repository_root=root)
        if viewer is None
        else viewer
    )
    workspace = (
        ProjectWorkspace(root=root / "data" / "projects")
        if project_workspace is None
        else project_workspace
    )

    _ensure_session_state(st)
    _inject_dashboard_css(st)

    st.header("Project Dashboard")
    st.caption(
        "Read-only project status, Preliminary Coverage and traceable evidence. "
        "Potential support is not Approved Generation Readiness."
    )

    try:
        selection = dashboard_service.list_projects()
    except Exception:
        st.error(
            "Project discovery is unavailable. No project state was inferred."
        )
        return

    render_issue_views(
        st,
        selection.issues,
        key_prefix="workspace",
        viewer=document_viewer,
    )

    if not selection.projects:
        st.info(
            "No valid Project Workspace is currently available. "
            "Create the first project to begin."
        )
        render_project_creation(
            st,
            workspace,
            first_project=True,
        )
        return

    if st.session_state.get(SESSION_GLOBAL_CONTROLS_ACTIVE) is True:
        valid_project_ids = {
            project.project_id
            for project in selection.projects
        }
        selected_project_id = st.session_state.get(
            SESSION_PROJECT_ID
        )

        if selected_project_id not in valid_project_ids:
            st.info(
                "Select a Project in the application header."
            )
            render_project_creation(
                st,
                workspace,
                first_project=False,
            )
            return
    else:
        selected_project_id = render_project_selector(
            st,
            selection,
        )

    render_project_creation(
        st,
        workspace,
        first_project=False,
    )
    active_view = render_view_selector(st)

    try:
        if active_view == "overview":
            render_overview(
                st,
                dashboard_service.project_overview(selected_project_id),
                document_viewer,
            )
        elif active_view == "sources":
            render_sources_processing(
                st,
                dashboard_service.source_processing_view(
                    selected_project_id
                ),
                document_viewer,
            )
        elif active_view == "coverage":
            render_coverage_support(
                st,
                dashboard_service.coverage_view(selected_project_id),
                document_viewer,
            )
        elif active_view == "attention":
            render_attention_review(
                st,
                dashboard_service.attention_review_view(
                    selected_project_id
                ),
                document_viewer,
            )
        elif active_view == "traceability":
            render_traceability(
                st,
                dashboard_service.traceability_view(selected_project_id),
                document_viewer,
            )
        else:
            st.error("The selected dashboard view is not supported.")
    except ProjectDashboardError:
        st.error(
            "This dashboard section is unavailable because its validated "
            "project evidence could not be presented."
        )
    except Exception:
        st.error(
            "This dashboard section is unavailable. No replacement status "
            "was inferred."
        )

    render_document_viewer(st, document_viewer)


def render_project_creation(
    st: Any,
    workspace: ProjectWorkspace,
    *,
    first_project: bool = True,
) -> str | None:
    """Render the constrained P2 Project Workspace creation action."""

    if first_project:
        st.subheader("Create first project")
        creation_context = nullcontext()
    else:
        creation_context = st.expander(
            "Create new project",
            expanded=False,
        )

    with creation_context:
        st.caption(
            "This creates only a Project Workspace. Dashboard views remain "
            "read-only, and the six-digit Project ID is generated automatically."
        )

        with st.form(
            "project_dashboard.create_project",
            clear_on_submit=False,
        ):
            display_name = st.text_input(
                "Project name",
                max_chars=120,
                help="Human-readable name shown in the project selector.",
            )
            description = st.text_area(
                "Description (optional)",
                max_chars=2000,
                help="Short project context. This can remain empty.",
            )
            submitted = st.form_submit_button(
                "Create project",
                type="primary",
            )

    if not submitted:
        return None

    normalized_name = (
        display_name.strip()
        if isinstance(display_name, str)
        else ""
    )
    normalized_description = (
        description.strip()
        if isinstance(description, str)
        else ""
    )

    if not normalized_name:
        st.error("Project name is required.")
        return None

    try:
        manifest = workspace.create_project(
            normalized_name,
            description=normalized_description,
        )
    except ProjectWorkspaceError as exc:
        st.error(f"Project could not be created: {exc}")
        return None
    except Exception:
        st.error(
            "Project creation failed unexpectedly. No partial project "
            "state was accepted."
        )
        return None

    st.session_state[_SESSION_PROJECT_ID] = manifest.project_id
    st.session_state[_SESSION_PENDING_PROJECT_ID] = manifest.project_id
    st.session_state[_SESSION_ACTIVE_VIEW] = "overview"
    st.session_state.pop(_SESSION_OPEN_REFERENCE, None)
    st.success(
        f"Project created: {manifest.display_name} · "
        f"{manifest.project_id}"
    )
    request_streamlit_rerun(st)
    return manifest.project_id


def request_streamlit_rerun(st: Any) -> None:
    """Request a Streamlit rerun while supporting older APIs in tests."""

    rerun = getattr(st, "rerun", None)
    if callable(rerun):
        rerun()
        return

    experimental_rerun = getattr(st, "experimental_rerun", None)
    if callable(experimental_rerun):
        experimental_rerun()



def render_project_selector(
    st: Any,
    selection: DashboardProjectSelection,
) -> str:
    """Render deterministic project selection and preserve context."""

    project_by_id = {
        project.project_id: project
        for project in selection.projects
    }
    pending_project_id = st.session_state.pop(
        _SESSION_PENDING_PROJECT_ID,
        None,
    )
    if pending_project_id in project_by_id:
        st.session_state[_SESSION_PROJECT_ID] = pending_project_id
        st.session_state[_SESSION_PROJECT_SELECTOR] = pending_project_id

    project_id = choose_project_id(
        selection.projects,
        st.session_state.get(_SESSION_PROJECT_ID),
    )
    options = tuple(project_by_id)
    selected = st.selectbox(
        "Project",
        options=options,
        index=options.index(project_id),
        format_func=lambda item: project_by_id[item].label,
        key=_SESSION_PROJECT_SELECTOR,
    )
    previous = st.session_state.get(_SESSION_PROJECT_ID)
    st.session_state[_SESSION_PROJECT_ID] = selected
    if previous is not None and previous != selected:
        st.session_state.pop(_SESSION_OPEN_REFERENCE, None)
        st.session_state[_SESSION_PROJECT_CHANGE_TOKEN] = selected
    return selected


def render_view_selector(st: Any) -> str:
    """Render the stable dashboard section selector without duplicate defaults."""

    valid_ids = tuple(view_id for view_id, _ in _VIEW_OPTIONS)
    current = normalize_active_view(
        st.session_state.get(_SESSION_ACTIVE_VIEW)
    )
    labels = dict(_VIEW_OPTIONS)
    widget_key = "project_dashboard.view_selector"
    if st.session_state.get(widget_key) not in valid_ids:
        st.session_state[widget_key] = current
    selected = st.radio(
        "Dashboard view",
        options=valid_ids,
        format_func=lambda item: labels[item],
        horizontal=True,
        key=widget_key,
    )
    st.session_state[_SESSION_ACTIVE_VIEW] = selected
    return selected


def render_overview(
    st: Any,
    view: ProjectOverviewView,
    viewer: DashboardDocumentViewer,
) -> None:
    """Render the compact project overview."""

    st.subheader(view.project.display_name)
    st.caption(
        f"Project ID {view.project.project_id} · "
        f"{view.project.framework_template_id} "
        f"v{view.project.framework_template_version}"
    )
    if view.project.description:
        st.write(view.project.description)

    render_issue_views(
        st,
        view.section.issues,
        key_prefix="overview_issues",
        viewer=viewer,
    )

    for start in range(0, len(view.section.values), 3):
        columns = st.columns(3)
        for column, value in zip(
            columns,
            view.section.values[start : start + 3],
        ):
            with column:
                with st.container(border=True):
                    st.caption(value.label)
                    if value.status is not None:
                        st.markdown(
                            status_badge_html(value.status),
                            unsafe_allow_html=True,
                        )
                    st.markdown(f"**{escape(value.primary_text)}**")
                    if value.secondary_text:
                        st.caption(value.secondary_text)
                    render_evidence_navigation(
                        st,
                        value.evidence,
                        key_prefix=f"overview_{value.value_id}",
                    )


def render_sources_processing(
    st: Any,
    view: DashboardSourceProcessingView,
    viewer: DashboardDocumentViewer,
) -> None:
    """Render Source metadata and current P5 Processing State."""

    st.subheader("Sources & Processing")
    st.markdown(
        status_badge_html(view.project_status),
        unsafe_allow_html=True,
    )
    render_issue_views(
        st,
        view.issues,
        key_prefix="sources_issues",
        viewer=viewer,
    )

    if not view.sources:
        st.info("No registered Sources are available.")
        return

    for row in view.sources:
        title = (
            f"{row.run_status.icon} {row.original_filename} · "
            f"{row.source_id}"
        )
        with st.expander(title, expanded=False):
            first = st.columns(4)
            _render_labeled_status(
                st,
                first[0],
                "Source role",
                row.source_role,
                row.disposition_status,
            )
            _render_labeled_status(
                st,
                first[1],
                "Disposition",
                row.processing_disposition,
                row.disposition_status,
            )
            _render_labeled_status(
                st,
                first[2],
                "Run state",
                row.run_state or "not_started",
                row.run_status,
            )
            _render_labeled_text(
                st,
                first[3],
                "Processing stage",
                row.processing_stage or "—",
            )

            second = st.columns(4)
            _render_labeled_text(
                st,
                second[0],
                "Current run",
                row.current_processing_run_id or "—",
            )
            _render_labeled_text(
                st,
                second[1],
                "Latest attempt",
                row.latest_attempt_id or "—",
            )
            _render_labeled_text(
                st,
                second[2],
                "Pending review",
                "Yes" if row.pending_review else "No",
            )
            _render_labeled_text(
                st,
                second[3],
                "File size",
                format_file_size(row.size_bytes),
            )

            st.caption(
                f"Media type: {row.media_type} · SHA-256: {row.sha256}"
            )
            if row.superseded_run_ids:
                st.caption(
                    "Superseded runs: "
                    + ", ".join(row.superseded_run_ids)
                )
            if row.invalidated_artifact_count:
                st.caption(
                    "Invalidated artifacts: "
                    f"{row.invalidated_artifact_count}"
                )
            if row.blocking_issue_codes:
                st.error(
                    "Blocking issues: "
                    + ", ".join(row.blocking_issue_codes)
                )
            if row.failure_issue_codes:
                st.error(
                    "Failure issues: "
                    + ", ".join(row.failure_issue_codes)
                )
            render_source_evidence_sections(
                st,
                row,
                viewer,
                key_prefix=f"source_{row.source_id}",
            )


def render_coverage_support(
    st: Any,
    view: DashboardCoverageView,
    viewer: DashboardDocumentViewer,
) -> None:
    """Render P6 Preliminary Coverage and potential support."""

    st.subheader("Preliminary Coverage")
    st.markdown(
        status_badge_html(view.project_status),
        unsafe_allow_html=True,
    )
    st.caption(
        f"{view.framework_template_id} v{view.framework_template_version} · "
        f"{view.support_profile_id} v{view.support_profile_version}"
    )
    render_issue_views(
        st,
        view.issues,
        key_prefix="coverage_issues",
        viewer=viewer,
    )

    node_by_level: dict[str, list[Any]] = {}
    for node in view.nodes:
        node_by_level.setdefault(node.level_node_id, []).append(node)

    for level in view.levels:
        with st.container(border=True):
            heading = st.columns((3, 1))
            with heading[0]:
                st.markdown(f"**{escape(level.level_name)}**")
                st.caption(
                    f"{level.covered_node_count} of "
                    f"{level.total_node_count} framework nodes covered"
                )
            with heading[1]:
                st.markdown(
                    status_badge_html(level.status),
                    unsafe_allow_html=True,
                )
            if level.attention_status is not None:
                st.markdown(
                    status_badge_html(level.attention_status),
                    unsafe_allow_html=True,
                )
            render_evidence_navigation(
                st,
                level.evidence,
                key_prefix=f"level_{level.level_node_id}",
            )

            for node in node_by_level.get(level.level_node_id, ()):
                with st.expander(
                    f"{node.status.icon} {node.node_name}",
                    expanded=False,
                ):
                    st.markdown(
                        status_badge_html(node.status),
                        unsafe_allow_html=True,
                    )
                    if node.attention_status is not None:
                        st.markdown(
                            status_badge_html(node.attention_status),
                            unsafe_allow_html=True,
                        )
                    st.caption(
                        f"{node.mapping_key} · {node.framework_node_id}"
                    )
                    counts = st.columns(4)
                    _render_labeled_text(
                        st,
                        counts[0],
                        "Sources",
                        str(node.eligible_source_count),
                    )
                    _render_labeled_text(
                        st,
                        counts[1],
                        "Information Units",
                        str(node.information_unit_count),
                    )
                    _render_labeled_text(
                        st,
                        counts[2],
                        "Covering candidates",
                        str(node.assignment_candidate_count),
                    )
                    _render_labeled_text(
                        st,
                        counts[3],
                        "Confirmed",
                        str(node.confirmed_candidate_count),
                    )
                    st.caption(
                        "Unreviewed "
                        f"{node.unreviewed_candidate_count} · "
                        "Rejected "
                        f"{node.rejected_candidate_count} · "
                        "Ambiguous "
                        f"{node.ambiguous_candidate_count} · "
                        "Conflicting "
                        f"{node.conflicting_candidate_count}"
                    )
                    if node.issue_codes:
                        st.warning(
                            "Node issues: "
                            + ", ".join(node.issue_codes)
                        )
                    render_evidence_navigation(
                        st,
                        node.evidence,
                        key_prefix=(
                            f"node_{node.framework_node_id}"
                        ),
                    )

    st.subheader("Potential Model Support")
    for target in view.support_targets:
        with st.container(border=True):
            columns = st.columns((3, 1))
            with columns[0]:
                st.markdown(f"**{escape(target.name)}**")
                st.caption(
                    f"{target.support_target_type} · "
                    f"{target.support_target_id}"
                )
            with columns[1]:
                st.markdown(
                    status_badge_html(target.status),
                    unsafe_allow_html=True,
                )
            if target.attention_status is not None:
                st.markdown(
                    status_badge_html(target.attention_status),
                    unsafe_allow_html=True,
                )
            st.caption(
                "Required nodes: "
                + compact_identifiers(
                    target.required_framework_node_ids
                )
            )
            st.caption(
                "Covered nodes: "
                + compact_identifiers(
                    target.covered_framework_node_ids
                )
            )
            if target.missing_framework_node_ids:
                st.warning(
                    "Missing nodes: "
                    + compact_identifiers(
                        target.missing_framework_node_ids
                    )
                )
            if target.unsatisfied_support_target_ids:
                st.warning(
                    "Unsatisfied support dependencies: "
                    + compact_identifiers(
                        target.unsatisfied_support_target_ids
                    )
                )
            render_evidence_navigation(
                st,
                target.evidence,
                key_prefix=f"support_{target.support_target_id}",
            )

    st.subheader("Approved Generation Readiness")
    st.markdown(
        status_badge_html(view.approved_readiness),
        unsafe_allow_html=True,
    )
    st.info(
        "Approved Generation Readiness is not assessed in Phase P. "
        f"It becomes available from Phase "
        f"{view.approved_readiness_available_from_phase}."
    )


def render_attention_review(
    st: Any,
    view: DashboardAttentionReviewView,
    viewer: DashboardDocumentViewer,
) -> None:
    """Render combined project attention and immutable review decisions."""

    st.subheader("Attention & Review")
    st.markdown(
        status_badge_html(view.status),
        unsafe_allow_html=True,
    )
    render_issue_views(
        st,
        view.issues,
        key_prefix="attention_issues",
        viewer=viewer,
    )

    st.markdown("**Human Review Decisions**")
    if not view.reviews:
        st.info("No Human Review Decisions are available.")
        return

    for review in view.reviews:
        with st.expander(
            f"{review.status.icon} "
            f"{review.human_review_decision_id} · "
            f"{review.target_id}",
            expanded=False,
        ):
            st.markdown(
                status_badge_html(review.status),
                unsafe_allow_html=True,
            )
            details = st.columns(3)
            _render_labeled_text(
                st,
                details[0],
                "Target type",
                review.target_type,
            )
            _render_labeled_text(
                st,
                details[1],
                "Review mode",
                review.review_mode,
            )
            _render_labeled_text(
                st,
                details[2],
                "Reviewer",
                review.reviewer_identity,
            )
            st.caption(f"Decision time: {review.decided_at}")
            st.caption(
                "Reference validation: "
                f"{review.reference_validation_status}"
            )
            st.caption(
                "Target fingerprint: "
                f"{review.target_content_fingerprint}"
            )
            if review.reference_validation_fingerprint:
                st.caption(
                    "Validation fingerprint: "
                    f"{review.reference_validation_fingerprint}"
                )
            if review.rationale:
                st.write(review.rationale)
            render_evidence_navigation(
                st,
                review.evidence,
                key_prefix=(
                    f"review_{review.human_review_decision_id}"
                ),
            )


def render_traceability(
    st: Any,
    view: DashboardTraceabilityView,
    viewer: DashboardDocumentViewer,
) -> None:
    """Render a compact navigable traceability graph projection."""

    st.subheader("Traceability")
    render_issue_views(
        st,
        view.issues,
        key_prefix="traceability_issues",
        viewer=viewer,
    )

    node_types = tuple(
        sorted({node.node_type for node in view.nodes})
    )
    selected_type = st.selectbox(
        "Node type",
        options=("all",) + node_types,
        format_func=lambda value: (
            "All node types"
            if value == "all"
            else value.replace("_", " ").title()
        ),
        key="project_dashboard.traceability_node_type",
    )
    nodes = tuple(
        node
        for node in view.nodes
        if selected_type == "all"
        or node.node_type == selected_type
    )
    st.caption(
        f"{len(view.nodes)} nodes · {len(view.edges)} relationships"
    )

    incoming: dict[str, list[Any]] = {}
    outgoing: dict[str, list[Any]] = {}
    for edge in view.edges:
        outgoing.setdefault(edge.source_node_key, []).append(edge)
        incoming.setdefault(edge.target_node_key, []).append(edge)

    for node in nodes:
        prefix = node.status.icon if node.status is not None else "○"
        with st.expander(
            f"{prefix} {node.label}",
            expanded=False,
        ):
            st.caption(
                f"{node.node_type} · {node.node_id}"
            )
            if node.secondary_text:
                st.write(node.secondary_text)
            if node.status is not None:
                st.markdown(
                    status_badge_html(node.status),
                    unsafe_allow_html=True,
                )
            related = (
                tuple(outgoing.get(node.node_key, ()))
                + tuple(incoming.get(node.node_key, ()))
            )
            if related:
                st.markdown("**Relationships**")
                for edge in sorted(
                    related,
                    key=lambda item: item.edge_key,
                ):
                    direction = (
                        "→"
                        if edge.source_node_key == node.node_key
                        else "←"
                    )
                    other = (
                        edge.target_node_key
                        if direction == "→"
                        else edge.source_node_key
                    )
                    st.caption(
                        f"{direction} {edge.label} · {other}"
                    )
            render_evidence_navigation(
                st,
                node.evidence,
                key_prefix=f"trace_{node.node_key}",
            )


def render_issue_views(
    st: Any,
    issues: Sequence[DashboardIssueView],
    *,
    key_prefix: str,
    viewer: DashboardDocumentViewer,
) -> None:
    """Render issues with optional supporting evidence."""

    for index, issue in enumerate(issues):
        message = f"{issue.issue_code}: {issue.message}"
        if issue.issue_level == "blocking":
            st.error(message)
        else:
            st.warning(message)
        render_evidence_navigation(
            st,
            issue.evidence,
            key_prefix=f"{key_prefix}_{index}_{issue.issue_code}",
        )



def source_evidence_sections(
    navigation: EvidenceNavigation,
) -> SourceEvidenceSections:
    """Partition P9 review artifacts from supporting and technical evidence."""

    groups: dict[str, list[EvidenceReference]] = {
        "review_reports": [],
        "run_summaries": [],
        "consensus_reports": [],
        "agent_outputs": [],
        "technical_evidence": [],
    }
    mapping = {
        "ingestion_review_report": "review_reports",
        "ingestion_run_summary": "run_summaries",
        "ingestion_consensus_report": "consensus_reports",
        "ingestion_agent_output": "agent_outputs",
    }
    for reference in navigation.references:
        group = mapping.get(
            reference.reference_type,
            "technical_evidence",
        )
        groups[group].append(reference)

    return SourceEvidenceSections(
        review_reports=tuple(groups["review_reports"]),
        run_summaries=tuple(groups["run_summaries"]),
        consensus_reports=tuple(groups["consensus_reports"]),
        agent_outputs=tuple(groups["agent_outputs"]),
        technical_evidence=tuple(groups["technical_evidence"]),
    )


def render_source_evidence_sections(
    st: Any,
    row: Any,
    viewer: DashboardDocumentViewer,
    *,
    key_prefix: str,
) -> None:
    """Render the review target first and supporting evidence by purpose."""

    sections = source_evidence_sections(row.evidence)

    if row.pending_review:
        with st.container(border=True):
            st.markdown("### Review required")
            st.write(
                "Review the Phase-F Ingestion Review Report. It is the "
                "primary Human-in-the-Loop artifact for this Processing Run."
            )
            if len(sections.review_reports) == 1:
                review_reference = sections.review_reports[0]
                columns = st.columns((4, 1))
                with columns[0]:
                    st.markdown("**Ingestion Review Report**")
                    st.caption(
                        "Consolidated findings, gaps, risks and review "
                        "questions from Team Agentic Ingestion."
                    )
                with columns[1]:
                    if st.button(
                        "Open review report",
                        key=safe_widget_key(
                            key_prefix,
                            "primary_review",
                            review_reference.reference_id,
                        ),
                    ):
                        st.session_state[
                            _SESSION_INLINE_REVIEW_REFERENCE
                        ] = review_reference
                render_inline_review_report(
                    st,
                    viewer,
                    review_reference,
                    key_prefix=key_prefix,
                )
            elif not sections.review_reports:
                st.error(
                    "The Run is awaiting review, but no validated Ingestion "
                    "Review Report is linked to the current publication event."
                )
            else:
                st.error(
                    "The current publication event contains multiple primary "
                    "review reports. Review navigation is blocked until the "
                    "ambiguity is resolved."
                )

    supporting_count = (
        len(sections.run_summaries)
        + len(sections.consensus_reports)
        + len(sections.agent_outputs)
    )
    if supporting_count:
        with st.expander(
            f"Supporting evidence ({supporting_count})",
            expanded=False,
        ):
            st.caption(
                "Use these artifacts to inspect how the review report was "
                "produced. They are supporting evidence, not the primary "
                "review target."
            )
            render_reference_group(
                st,
                "Run summaries",
                sections.run_summaries,
                key_prefix=f"{key_prefix}_summaries",
            )
            render_reference_group(
                st,
                "Consensus reports",
                sections.consensus_reports,
                key_prefix=f"{key_prefix}_consensus",
            )
            render_reference_group(
                st,
                "Agent outputs",
                sections.agent_outputs,
                key_prefix=f"{key_prefix}_agents",
            )

    if sections.technical_evidence:
        with st.expander(
            f"Technical evidence ({len(sections.technical_evidence)})",
            expanded=False,
        ):
            st.caption(
                "Immutable Source and Processing manifests used for identity, "
                "integrity and traceability."
            )
            render_reference_rows(
                st,
                sections.technical_evidence,
                key_prefix=f"{key_prefix}_technical",
            )


def render_inline_review_report(
    st: Any,
    viewer: DashboardDocumentViewer,
    reference: EvidenceReference,
    *,
    key_prefix: str,
) -> None:
    selected = st.session_state.get(
        _SESSION_INLINE_REVIEW_REFERENCE
    )
    if selected != reference:
        return

    heading = st.columns((5, 1))
    with heading[0]:
        st.markdown("#### Ingestion Review Report")
    with heading[1]:
        if st.button(
            "Close",
            key=safe_widget_key(key_prefix, "close_primary_review"),
        ):
            st.session_state.pop(
                _SESSION_INLINE_REVIEW_REFERENCE,
                None,
            )
            return

    try:
        preview = viewer.open(reference)
    except ProjectDashboardError:
        st.error("The Ingestion Review Report could not be opened safely.")
        return
    except Exception:
        st.error("The Ingestion Review Report is unavailable.")
        return

    render_document_preview(st, preview)


def render_reference_group(
    st: Any,
    label: str,
    references: Sequence[EvidenceReference],
    *,
    key_prefix: str,
) -> None:
    if not references:
        return
    st.markdown(f"**{escape(label)} ({len(references)})**")
    render_reference_rows(
        st,
        references,
        key_prefix=key_prefix,
    )


def render_reference_rows(
    st: Any,
    references: Sequence[EvidenceReference],
    *,
    key_prefix: str,
) -> None:
    for reference in references:
        columns = st.columns((5, 1))
        with columns[0]:
            st.markdown(f"**{escape(reference.display_label)}**")
            st.caption(evidence_reference_detail(reference))
        with columns[1]:
            if st.button(
                "Open",
                key=safe_widget_key(
                    key_prefix,
                    reference.reference_type,
                    reference.reference_id,
                    reference.repository_relative_path,
                ),
            ):
                st.session_state[_SESSION_OPEN_REFERENCE] = reference

def render_evidence_navigation(
    st: Any,
    navigation: EvidenceNavigation,
    *,
    key_prefix: str,
) -> None:
    """Render direct or chooser navigation without opening arbitrary paths."""

    controls = evidence_controls(navigation)
    if navigation.mode == "unavailable":
        st.caption("No linked evidence is available.")
        return

    if navigation.mode == "direct":
        control = controls[0]
        if st.button(
            "Open document",
            key=safe_widget_key(key_prefix, control.key),
            help=control.detail,
        ):
            st.session_state[_SESSION_OPEN_REFERENCE] = (
                control.reference
            )
        return

    with st.expander(
        f"Documents ({len(controls)})",
        expanded=False,
    ):
        for control in controls:
            columns = st.columns((5, 1))
            with columns[0]:
                st.markdown(f"**{escape(control.label)}**")
                st.caption(control.detail)
            with columns[1]:
                if st.button(
                    "Open",
                    key=safe_widget_key(
                        key_prefix,
                        control.key,
                    ),
                ):
                    st.session_state[_SESSION_OPEN_REFERENCE] = (
                        control.reference
                    )


def render_document_viewer(
    st: Any,
    viewer: DashboardDocumentViewer,
) -> None:
    """Render the currently selected internal document preview."""

    reference = st.session_state.get(_SESSION_OPEN_REFERENCE)
    if not isinstance(reference, EvidenceReference):
        return

    st.divider()
    heading = st.columns((5, 1))
    with heading[0]:
        st.subheader("Document")
    with heading[1]:
        if st.button(
            "Close",
            key="project_dashboard.close_document",
        ):
            st.session_state.pop(_SESSION_OPEN_REFERENCE, None)
            return

    try:
        preview = viewer.open(reference)
    except ProjectDashboardError:
        st.error(
            "The linked document could not be opened safely."
        )
        return
    except Exception:
        st.error(
            "The linked document is unavailable. No fallback path "
            "was used."
        )
        return

    render_document_preview(st, preview)


def render_document_preview(
    st: Any,
    preview: DashboardDocumentPreview,
) -> None:
    """Render one validated document payload."""

    st.markdown(f"**{escape(preview.title)}**")
    st.caption(preview.repository_relative_path)
    metadata = st.columns(4)
    _render_labeled_text(
        st,
        metadata[0],
        "Media type",
        preview.media_type,
    )
    _render_labeled_text(
        st,
        metadata[1],
        "Size",
        format_file_size(preview.file_size_bytes),
    )
    _render_labeled_text(
        st,
        metadata[2],
        "Fingerprint",
        preview.fingerprint_status,
    )
    _render_labeled_text(
        st,
        metadata[3],
        "Render mode",
        preview.render_mode,
    )
    st.caption(f"SHA-256: {preview.actual_sha256}")

    if preview.issue:
        st.warning(preview.issue)
    if preview.truncated:
        st.warning(
            "The preview is bounded. The referenced file was not modified."
        )

    if preview.highlighted_text:
        st.markdown("**Selected location**")
        st.code(preview.highlighted_text)

    if preview.render_mode == "json":
        st.code(preview.content_text or "", language="json")
    elif preview.render_mode == "markdown":
        st.markdown(preview.content_text or "")
        with st.expander("Markdown source", expanded=False):
            st.code(preview.content_text or "", language="markdown")
    elif preview.render_mode == "text":
        st.code(preview.content_text or "")
    elif preview.render_mode == "table":
        rows = document_table_rows(preview)
        if rows:
            st.table(rows)
        else:
            st.info("The table contains no preview rows.")
    else:
        st.info(
            "A text preview is not available for this artifact. "
            "Metadata remains visible."
        )


def status_badge_html(status: DashboardStatus) -> str:
    """Return escaped, status-only badge markup."""

    semantic = (
        status.semantic
        if status.semantic in _STATUS_COLOR_TOKENS
        else "neutral"
    )
    title = (
        ""
        if not status.explanation
        else f' title="{escape(status.explanation, quote=True)}"'
    )
    return (
        f'<span class="turing-status" '
        f'data-semantic="{escape(semantic, quote=True)}"{title}>'
        f'<span aria-hidden="true">{escape(status.icon)}</span>'
        f'<span>{escape(status.label)}</span>'
        f"</span>"
    )


def dashboard_css() -> str:
    """Return neutral layout CSS with colors restricted to status badges."""

    semantic_rules = []
    for semantic, (foreground, background, border) in (
        _STATUS_COLOR_TOKENS.items()
    ):
        semantic_rules.append(
            ".turing-status[data-semantic="
            f'"{semantic}"]{{color:{foreground};'
            f"background:{background};border-color:{border};}}"
        )
    return (
        "<style>"
        ".turing-status{display:inline-flex;align-items:center;"
        "gap:.35rem;padding:.18rem .55rem;border:1px solid;"
        "border-radius:999px;font-size:.78rem;font-weight:600;"
        "line-height:1.2;white-space:nowrap;}"
        + "".join(semantic_rules)
        + "</style>"
    )


def evidence_controls(
    navigation: EvidenceNavigation,
) -> tuple[EvidenceControl, ...]:
    """Transform validated navigation into deterministic chooser rows."""

    if navigation.mode == "unavailable":
        if navigation.references:
            raise ValueError(
                "Unavailable navigation must not contain references."
            )
        return ()
    if navigation.mode == "direct" and len(navigation.references) != 1:
        raise ValueError(
            "Direct navigation requires exactly one reference."
        )
    if navigation.mode == "chooser" and len(navigation.references) < 2:
        raise ValueError(
            "Chooser navigation requires multiple references."
        )
    if navigation.mode not in {"direct", "chooser"}:
        raise ValueError("Unsupported evidence navigation mode.")

    return tuple(
        EvidenceControl(
            key=safe_widget_key(
                reference.reference_type,
                reference.reference_id,
                reference.repository_relative_path,
            ),
            label=reference.display_label,
            detail=evidence_reference_detail(reference),
            reference=reference,
        )
        for reference in navigation.references
    )


def evidence_reference_detail(reference: EvidenceReference) -> str:
    """Return a concise relationship and path description."""

    role = (
        "Direct evidence"
        if reference.evidence_role == "direct"
        else "Context"
    )
    source_role = (
        ""
        if reference.source_role is None
        else f" · {reference.source_role}"
    )
    return (
        f"{role} · {reference.relationship}{source_role} · "
        f"{reference.repository_relative_path}"
    )


def choose_project_id(
    projects: Sequence[DashboardProjectOption],
    current_project_id: object,
) -> str:
    """Choose a valid existing project without guessing identifiers."""

    if not projects:
        raise ValueError("At least one project is required.")
    known_ids = tuple(project.project_id for project in projects)
    if (
        isinstance(current_project_id, str)
        and current_project_id in known_ids
    ):
        return current_project_id
    return known_ids[0]


def normalize_active_view(value: object) -> str:
    """Return one supported view identifier."""

    valid = tuple(item[0] for item in _VIEW_OPTIONS)
    return value if isinstance(value, str) and value in valid else valid[0]


def safe_widget_key(*parts: object) -> str:
    """Return a deterministic Streamlit widget key."""

    payload = "\x1f".join(str(part) for part in parts)
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:20]
    return f"project_dashboard.{digest}"


def format_file_size(size_bytes: int) -> str:
    """Format a non-negative byte count without locale-sensitive mutation."""

    if not isinstance(size_bytes, int) or isinstance(size_bytes, bool):
        raise TypeError("size_bytes must be an integer.")
    if size_bytes < 0:
        raise ValueError("size_bytes must not be negative.")
    value = float(size_bytes)
    units = ("B", "KiB", "MiB", "GiB")
    unit = units[0]
    for unit in units:
        if value < 1024.0 or unit == units[-1]:
            break
        value /= 1024.0
    if unit == "B":
        return f"{int(value)} {unit}"
    return f"{value:.1f} {unit}"


def compact_identifiers(
    values: Iterable[str],
    *,
    limit: int = 5,
) -> str:
    """Return a bounded deterministic identifier summary."""

    ordered = tuple(values)
    if not ordered:
        return "—"
    if limit < 1:
        raise ValueError("limit must be positive.")
    visible = ordered[:limit]
    suffix = (
        ""
        if len(ordered) <= limit
        else f" · +{len(ordered) - limit} more"
    )
    return ", ".join(visible) + suffix


def document_table_rows(
    preview: DashboardDocumentPreview,
) -> list[dict[str, str]]:
    """Convert immutable table payload into Streamlit table rows."""

    columns = preview.table_columns
    return [
        {
            column: row[index] if index < len(row) else ""
            for index, column in enumerate(columns)
        }
        for row in preview.table_rows
    ]


def _render_labeled_status(
    st: Any,
    column: Any,
    label: str,
    text: str,
    status: DashboardStatus,
) -> None:
    with column:
        st.caption(label)
        st.write(text)
        st.markdown(
            status_badge_html(status),
            unsafe_allow_html=True,
        )


def _render_labeled_text(
    st: Any,
    column: Any,
    label: str,
    text: str,
) -> None:
    with column:
        st.caption(label)
        st.write(text)


def _ensure_session_state(st: Any) -> None:
    if _SESSION_ACTIVE_VIEW not in st.session_state:
        st.session_state[_SESSION_ACTIVE_VIEW] = _VIEW_OPTIONS[0][0]


def _inject_dashboard_css(st: Any) -> None:
    st.markdown(dashboard_css(), unsafe_allow_html=True)


def _streamlit() -> Any:
    import streamlit as st

    return st
