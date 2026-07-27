"""Common Streamlit application shell for the Turing Generator."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from app.project_dashboard_ui import render_project_dashboard_ui
from app.turing_generator_navigation import (
    APP_VIEW_DASHBOARD,
    APP_VIEW_INGESTION,
    APP_VIEWS,
    SESSION_APP_VIEW,
    ApplicationNavigationState,
    read_navigation_state,
    select_app_view,
)
from modules.project_workspace import (
    ProjectWorkspace,
    ProjectWorkspaceError,
)


_APP_VIEW_LABELS = {
    APP_VIEW_DASHBOARD: "Project Dashboard",
    APP_VIEW_INGESTION: "Agentic Ingestion",
}


def render_turing_generator_ui(
    project_root: Path,
    *,
    streamlit_module: Any | None = None,
    project_workspace: ProjectWorkspace | None = None,
    dashboard_renderer: Callable[..., None] | None = None,
) -> None:
    """Render the common application shell and route the selected view."""

    st = (
        streamlit_module
        if streamlit_module is not None
        else _streamlit()
    )
    root = Path(project_root)
    workspace = (
        ProjectWorkspace(root=root / "data" / "projects")
        if project_workspace is None
        else project_workspace
    )
    render_dashboard = (
        render_project_dashboard_ui
        if dashboard_renderer is None
        else dashboard_renderer
    )

    navigation = read_navigation_state(st.session_state)
    active_view = render_application_navigation(
        st,
        current_view=navigation.active_view,
    )

    if active_view == APP_VIEW_DASHBOARD:
        render_dashboard(
            root,
            streamlit_module=st,
            project_workspace=workspace,
        )
        return

    render_project_bound_ingestion_entry(
        st,
        workspace=workspace,
        navigation=read_navigation_state(st.session_state),
    )


def render_application_navigation(
    st: Any,
    *,
    current_view: str,
) -> str:
    """Render the stable top-level application navigation."""

    selected = st.radio(
        "Turing Generator view",
        options=APP_VIEWS,
        index=APP_VIEWS.index(current_view),
        format_func=lambda item: _APP_VIEW_LABELS[item],
        horizontal=True,
        key=SESSION_APP_VIEW,
    )
    return selected


def render_project_bound_ingestion_entry(
    st: Any,
    *,
    workspace: ProjectWorkspace,
    navigation: ApplicationNavigationState,
) -> None:
    """Render the fail-closed P9 execution entry established in Step 2."""

    st.header("Project-bound Agentic Ingestion")

    if navigation.project_id is None:
        st.error(
            "No valid Project is selected. Open the Project Dashboard "
            "and select or create a Project before starting ingestion."
        )
        render_dashboard_return_control(
            st,
            project_id=None,
            return_view=navigation.return_view,
            label="Open Project Dashboard",
        )
        return

    try:
        manifest = workspace.load_project(navigation.project_id)
    except ProjectWorkspaceError:
        st.error(
            "The selected Project Workspace is unavailable or invalid. "
            "No fallback Project was selected."
        )
        render_dashboard_return_control(
            st,
            project_id=None,
            return_view=navigation.return_view,
            label="Open Project Dashboard",
        )
        return
    except Exception:
        st.error(
            "The selected Project Workspace could not be validated. "
            "No fallback Project was selected."
        )
        render_dashboard_return_control(
            st,
            project_id=None,
            return_view=navigation.return_view,
            label="Open Project Dashboard",
        )
        return

    st.caption(
        f"Selected Project: {manifest.display_name} · "
        f"{manifest.project_id}"
    )
    st.info(
        "Project-bound Source upload, registration and pipeline execution "
        "are introduced in P9 Steps 3 to 5. This view currently establishes "
        "the validated Project and navigation boundary only."
    )

    render_dashboard_return_control(
        st,
        project_id=manifest.project_id,
        return_view=navigation.return_view,
        label="Return to Project Dashboard",
    )


def render_dashboard_return_control(
    st: Any,
    *,
    project_id: str | None,
    return_view: str,
    label: str,
) -> None:
    """Return to the dashboard while preserving only stable identities."""

    if not st.button(
        label,
        key="turing_generator.return_to_dashboard",
    ):
        return

    select_app_view(
        st.session_state,
        active_view=APP_VIEW_DASHBOARD,
        project_id=project_id,
        return_view=return_view,
    )
    request_streamlit_rerun(st)


def request_streamlit_rerun(st: Any) -> None:
    """Request one Streamlit rerun while supporting the legacy API."""

    rerun = getattr(st, "rerun", None)
    if callable(rerun):
        rerun()
        return

    experimental_rerun = getattr(
        st,
        "experimental_rerun",
        None,
    )
    if callable(experimental_rerun):
        experimental_rerun()


def _streamlit() -> Any:
    import streamlit as st

    return st
