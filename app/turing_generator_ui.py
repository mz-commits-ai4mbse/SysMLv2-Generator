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
    SESSION_SELECTED_ENTITY_ID,
    ApplicationNavigationState,
    read_navigation_state,
    select_app_view,
)
from modules.project_ingestion import (
    ProjectBoundIngestionService,
    ProjectIngestionInputError,
)
from modules.project_sources import (
    CONTEXT_ONLY_SOURCE_ROLE,
    ENGINEERING_SOURCE_ROLE,
    DuplicateSourceContentError,
    ProjectSourceError,
)
from modules.project_workspace import (
    ProjectWorkspace,
    ProjectWorkspaceError,
)


_APP_VIEW_LABELS = {
    APP_VIEW_DASHBOARD: "Project Dashboard",
    APP_VIEW_INGESTION: "Agentic Ingestion",
}

_P9_UPLOAD_TYPES = ("md", "txt", "json", "csv", "pdf")
_SOURCE_ROLE_OPTIONS = (
    ENGINEERING_SOURCE_ROLE,
    CONTEXT_ONLY_SOURCE_ROLE,
)
_SOURCE_ROLE_LABELS = {
    ENGINEERING_SOURCE_ROLE: "Engineering source",
    CONTEXT_ONLY_SOURCE_ROLE: "Context only",
}


def render_turing_generator_ui(
    project_root: Path,
    *,
    streamlit_module: Any | None = None,
    project_workspace: ProjectWorkspace | None = None,
    ingestion_service: ProjectBoundIngestionService | None = None,
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
    source_service = (
        ProjectBoundIngestionService(
            root=root / "data" / "projects"
        )
        if ingestion_service is None
        else ingestion_service
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
        ingestion_service=source_service,
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
    ingestion_service: ProjectBoundIngestionService,
    navigation: ApplicationNavigationState,
) -> None:
    """Render the project-bound P9 Source registration entry."""

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
    st.warning(
        "Registered Sources remain unreviewed. Registration preserves "
        "traceability but does not approve engineering content."
    )

    render_project_source_registration(
        st,
        ingestion_service=ingestion_service,
        navigation=navigation,
    )

    st.info(
        "Processing Run creation and Team Agentic Ingestion execution "
        "are introduced in P9 Steps 4 and 5."
    )

    render_dashboard_return_control(
        st,
        project_id=manifest.project_id,
        return_view=navigation.return_view,
        label="Return to Project Dashboard",
    )


def render_project_source_registration(
    st: Any,
    *,
    ingestion_service: ProjectBoundIngestionService,
    navigation: ApplicationNavigationState,
) -> None:
    """Upload and register one immutable Source through P3."""

    if navigation.project_id is None:
        return

    st.subheader("1. Register Source")
    st.caption(
        "Supported Source containers: Markdown, text, JSON, CSV and PDF. "
        "PDF processing is limited to machine-readable text layers; "
        "OCR and image-only content remain outside the MVP."
    )

    uploaded_file = st.file_uploader(
        "Upload legacy Source",
        type=list(_P9_UPLOAD_TYPES),
        key="turing_generator.source_upload",
    )
    source_role = st.selectbox(
        "Source role",
        options=_SOURCE_ROLE_OPTIONS,
        index=0,
        format_func=lambda item: _SOURCE_ROLE_LABELS[item],
        key="turing_generator.source_role",
    )

    if uploaded_file is None:
        st.info("Upload a Source file to enable registration.")
    else:
        uploaded_size = getattr(uploaded_file, "size", None)
        size_text = (
            f"{uploaded_size} bytes"
            if isinstance(uploaded_size, int)
            else "size unavailable"
        )
        st.caption(
            f"Prepared upload: {uploaded_file.name} · {size_text}"
        )

        if st.button(
            "Register Source",
            key="turing_generator.register_source",
            type="primary",
        ):
            try:
                result = (
                    ingestion_service.register_uploaded_source(
                        navigation.project_id,
                        original_filename=uploaded_file.name,
                        content=_uploaded_file_bytes(uploaded_file),
                        source_role=source_role,
                    )
                )
            except DuplicateSourceContentError:
                st.error(
                    "This exact Source content is already registered "
                    "in the selected Project."
                )
            except ProjectIngestionInputError as exc:
                st.error(f"Source upload was not accepted: {exc}")
            except ProjectSourceError:
                st.error(
                    "Source registration failed validation or persistence. "
                    "No partial Source was accepted."
                )
            except Exception:
                st.error(
                    "Source registration failed unexpectedly. "
                    "No success state was inferred."
                )
            else:
                st.session_state[
                    SESSION_SELECTED_ENTITY_ID
                ] = result.source_id
                st.success(
                    f"Source registered: {result.original_filename} · "
                    f"{result.source_id}"
                )

    render_registered_source_inventory(
        st,
        ingestion_service=ingestion_service,
        project_id=navigation.project_id,
    )


def render_registered_source_inventory(
    st: Any,
    *,
    ingestion_service: ProjectBoundIngestionService,
    project_id: str,
) -> None:
    """Render safe project-local Source metadata without filesystem paths."""

    st.subheader("Registered Sources")

    try:
        inventory = ingestion_service.list_registered_sources(
            project_id
        )
    except ProjectSourceError:
        st.error(
            "Registered Sources could not be validated for this Project."
        )
        return
    except Exception:
        st.error(
            "Registered Source inventory is unavailable. "
            "No replacement inventory was inferred."
        )
        return

    if inventory.issues:
        st.warning(
            f"{len(inventory.issues)} Source Registry issue(s) "
            "require technical attention."
        )

    if not inventory.sources:
        st.info("No registered Sources are currently available.")
        return

    rows = [
        {
            "Source ID": source.source_id,
            "Filename": source.original_filename,
            "Role": _SOURCE_ROLE_LABELS.get(
                source.source_role,
                source.source_role,
            ),
            "Media type": source.media_type,
            "Size": source.size_bytes,
            "SHA-256": source.sha256[:12],
        }
        for source in inventory.sources
    ]
    st.table(rows)

    selected_source_id = st.session_state.get(
        SESSION_SELECTED_ENTITY_ID
    )
    selected_source = next(
        (
            source
            for source in inventory.sources
            if source.source_id == selected_source_id
        ),
        None,
    )
    if selected_source is not None:
        st.caption(
            f"Selected Source: {selected_source.original_filename} · "
            f"{selected_source.source_id}"
        )


def _uploaded_file_bytes(uploaded_file: Any) -> bytes:
    getvalue = getattr(uploaded_file, "getvalue", None)
    if callable(getvalue):
        return bytes(getvalue())

    getbuffer = getattr(uploaded_file, "getbuffer", None)
    if callable(getbuffer):
        return bytes(getbuffer())

    raise ProjectIngestionInputError(
        "Uploaded Source content could not be read as bytes."
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
