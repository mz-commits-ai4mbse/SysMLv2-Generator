
"""Engineer-centered Streamlit adapter for the Guided Workflow."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.presentation_preferences import (
    technical_details_enabled,
)
from app.turing_generator_navigation import (
    APP_VIEW_DASHBOARD,
    APP_VIEW_FINAL_REVIEW,
    APP_VIEW_INGESTION,
    APP_VIEW_MODEL_PROPOSAL,
    APP_VIEW_OUTPUT,
    APP_VIEW_REVIEW,
    DASHBOARD_VIEW_OVERVIEW,
    DASHBOARD_VIEW_SOURCES,
    queue_app_view,
    read_navigation_state,
)
from modules.guided_workflow import GuidedWorkflowReadService
from modules.project_workspace import (
    ProjectWorkspace,
    ProjectWorkspaceError,
)


_STATUS_LABELS = {
    "not_started": ("Not started", "○"),
    "in_progress": ("In progress", "◐"),
    "action_required": ("Action required", "!"),
    "ready": ("Ready", "→"),
    "complete": ("Complete", "✓"),
    "blocked": ("Blocked", "×"),
    "unavailable": ("Unavailable", "—"),
}

_STAGE_ROUTES = {
    "project_sources": (
        APP_VIEW_DASHBOARD,
        DASHBOARD_VIEW_SOURCES,
    ),
    "processing": (
        APP_VIEW_INGESTION,
        DASHBOARD_VIEW_SOURCES,
    ),
    "human_review": (
        APP_VIEW_REVIEW,
        DASHBOARD_VIEW_OVERVIEW,
    ),
    "model_proposal": (
        APP_VIEW_MODEL_PROPOSAL,
        DASHBOARD_VIEW_OVERVIEW,
    ),
    "final_model_review": (
        APP_VIEW_FINAL_REVIEW,
        DASHBOARD_VIEW_OVERVIEW,
    ),
    "published_output": (
        APP_VIEW_OUTPUT,
        DASHBOARD_VIEW_OVERVIEW,
    ),
}


def render_guided_workflow_ui(
    project_root: Path,
    *,
    streamlit_module: Any,
    project_workspace: ProjectWorkspace | None = None,
    workflow_service: GuidedWorkflowReadService | None = None,
) -> None:
    """Render the engineer-centered project entry view."""

    st = streamlit_module
    root = Path(project_root)
    navigation = read_navigation_state(st.session_state)

    workspace = (
        ProjectWorkspace(root=root / "data" / "projects")
        if project_workspace is None
        else project_workspace
    )
    service = (
        GuidedWorkflowReadService(project_root=root)
        if workflow_service is None
        else workflow_service
    )

    _inject_workflow_css(st)

    st.header("Engineering Workspace")
    st.caption(
        "Engineering content first · decisions where they matter · "
        "traceability available on demand."
    )

    technical_details = technical_details_enabled(
        st.session_state
    )

    if navigation.project_id is None:
        st.info(
            "Select a Project in the application header to see its "
            "engineering work, open decisions and processing progress."
        )
        return

    try:
        manifest = workspace.load_project(navigation.project_id)
    except ProjectWorkspaceError:
        st.error(
            "The selected Project is unavailable or invalid. "
            "No fallback Project was selected."
        )
        return
    except Exception:
        st.error(
            "The selected Project could not be validated safely."
        )
        return

    st.subheader(manifest.display_name)

    if technical_details:
        st.caption(f"Project {manifest.project_id}")

    try:
        view = service.load_view(manifest.project_id)
    except Exception:
        st.error(
            "The Engineering Workspace could not be reconstructed "
            "from the current authoritative project state."
        )
        return

    _render_your_work(st, view)
    _render_next_action(st, view)
    _render_engineering_flow(
        st,
        view,
        technical_details=technical_details,
    )

    if technical_details:
        _render_technical_views(st)


def _render_your_work(st: Any, view) -> None:
    st.subheader("Your work")

    columns = st.columns(4)
    columns[0].metric(
        "Decisions required",
        view.work_summary.decisions_required,
    )
    columns[1].metric(
        "Results with variance",
        view.work_summary.variance_attention_count,
    )
    columns[2].metric(
        "Blocking issues",
        view.work_summary.blocking_issue_count,
    )
    columns[3].metric(
        "Confirmed results",
        view.work_summary.confirmed_result_count,
    )


def _render_next_action(st: Any, view) -> None:
    st.subheader("Next action")

    if view.next_stage_id is None:
        st.success(
            "No further engineering action is currently required."
        )
        return

    stage = next(
        item
        for item in view.stages
        if item.stage_id == view.next_stage_id
    )

    with st.container(border=True):
        st.markdown(
            f"**{stage.label}**"
        )
        st.write(stage.summary)

        route = _STAGE_ROUTES.get(stage.stage_id)
        if route is None:
            st.info(
                view.next_action
                or stage.action_label
                or "No dedicated action is available."
            )
            return

        label = (
            view.next_action
            or stage.action_label
            or f"Open {stage.label}"
        )
        if st.button(
            label,
            key=f"guided_workflow.next.{stage.stage_id}",
            type="primary",
        ):
            _queue_stage_route(st, stage, route)


def _render_engineering_flow(
    st: Any,
    view,
    *,
    technical_details: bool,
) -> None:
    st.subheader("Engineering flow")

    for start in range(0, len(view.stages), 3):
        columns = st.columns(3)

        for column, stage in zip(
            columns,
            view.stages[start : start + 3],
        ):
            with column:
                with st.container(border=True):
                    stage_number = (
                        view.stages.index(stage) + 1
                    )
                    st.caption(
                        f"STEP {stage_number}"
                    )
                    st.markdown(
                        f"### {stage.label}"
                    )
                    _render_status_pill(st, stage)
                    st.write(stage.summary)

                    attention = []
                    if stage.decision_count:
                        attention.append(
                            f"{stage.decision_count} decision"
                            + (
                                ""
                                if stage.decision_count == 1
                                else "s"
                            )
                        )
                    if stage.variance_attention_count:
                        attention.append(
                            f"{stage.variance_attention_count} "
                            "with variance"
                        )
                    if stage.blocking_issue_count:
                        attention.append(
                            f"{stage.blocking_issue_count} blocking"
                        )

                    if attention:
                        st.caption(" · ".join(attention))

                    if technical_details:
                        with st.expander("Technical details"):
                            st.caption(
                                f"Stage ID: {stage.stage_id}"
                            )
                            st.caption(
                                "Presentation status: "
                                f"{stage.presentation_status}"
                            )
                            st.caption(
                                f"Semantic: {stage.semantic}"
                            )

                            if stage.target_entity_id is not None:
                                st.caption(
                                    "Target entity: "
                                    f"{stage.target_entity_id}"
                                )

                    route = _STAGE_ROUTES.get(stage.stage_id)

                    if route is not None:
                        label = (
                            stage.action_label
                            or f"Open {stage.label}"
                        )
                        if st.button(
                            label,
                            key=(
                                "guided_workflow.stage."
                                f"{stage.stage_id}"
                            ),
                        ):
                            _queue_stage_route(
                                st,
                                stage,
                                route,
                            )
                    elif stage.action_label:
                        st.caption(
                            f"Next: {stage.action_label}"
                        )


def _render_technical_views(st: Any) -> None:
    with st.expander("Technical views"):
        st.caption(
            "These existing views expose deeper processing, diagnostic "
            "and traceability information over the same Project state."
        )
        st.caption(
            "Project Dashboard · Processing · Human Review · "
            "Model Proposal · Final Model Review · Published Output"
        )


def _render_status_pill(st: Any, stage) -> None:
    label, icon = _STATUS_LABELS[
        stage.presentation_status
    ]
    st.markdown(
        (
            '<span class="tg-workflow-status '
            f'tg-workflow-{stage.semantic}">'
            f"{icon}&nbsp;&nbsp;{label}</span>"
        ),
        unsafe_allow_html=True,
    )


def _queue_stage_route(st: Any, stage, route) -> None:
    active_view, dashboard_view = route
    queue_app_view(
        st.session_state,
        active_view=active_view,
        project_id=read_navigation_state(
            st.session_state
        ).project_id,
        dashboard_view=dashboard_view,
        selected_entity_id=stage.target_entity_id,
    )
    st.rerun()


def _inject_workflow_css(st: Any) -> None:
    st.markdown(
        """
<style>
.tg-workflow-status {
    display: inline-block;
    border-radius: 999px;
    padding: 0.18rem 0.6rem;
    font-size: 0.82rem;
    font-weight: 650;
    margin-bottom: 0.35rem;
}
.tg-workflow-positive {
    background: #e6f4ea;
    color: #137333;
}
.tg-workflow-attention {
    background: #fef7e0;
    color: #8a4b00;
}
.tg-workflow-blocking {
    background: #fce8e6;
    color: #b3261e;
}
.tg-workflow-informational {
    background: #e8f0fe;
    color: #174ea6;
}
.tg-workflow-neutral {
    background: #f1f3f4;
    color: #5f6368;
}
</style>
""",
        unsafe_allow_html=True,
    )
