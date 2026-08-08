"""Common Streamlit application shell for the Turing Generator."""

from __future__ import annotations

from collections.abc import Callable
import os
from pathlib import Path
from typing import Any

from app.human_review_approval_ui import (
    render_human_review_approval_ui,
)
from app.project_dashboard_ui import render_project_dashboard_ui
from app.turing_generator_navigation import (
    APP_VIEW_DASHBOARD,
    APP_VIEW_INGESTION,
    APP_VIEW_REVIEW,
    APP_VIEWS,
    DASHBOARD_VIEW_SOURCES,
    SESSION_APP_VIEW,
    SESSION_SELECTED_ENTITY_ID,
    ApplicationNavigationState,
    apply_pending_app_view,
    queue_app_view,
    read_navigation_state,
)
from modules.project_ingestion import (
    DEFAULT_MODEL,
    DEFAULT_PROVIDER,
    ProjectBoundIngestionService,
    ProjectIngestionConfiguration,
    ProjectIngestionConfigurationError,
    ProjectIngestionError,
    ProjectIngestionExecutionError,
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
    APP_VIEW_REVIEW: "Human Review & Approval",
}

_P9_UPLOAD_TYPES = ("md", "txt", "json", "csv", "tsv", "pdf")
_SOURCE_ROLE_OPTIONS = (
    ENGINEERING_SOURCE_ROLE,
    CONTEXT_ONLY_SOURCE_ROLE,
)
_SOURCE_ROLE_LABELS = {
    ENGINEERING_SOURCE_ROLE: "Engineering source",
    CONTEXT_ONLY_SOURCE_ROLE: "Context only",
}
_P9_MODEL_OPTIONS = (
    "gpt-5.4-mini",
    "gpt-5-mini",
    "gpt-4.1-mini",
    "gpt-4o-mini",
)
_SESSION_LAST_INGESTION_RESULT = (
    "turing_generator.last_ingestion_result"
)


def render_turing_generator_ui(
    project_root: Path,
    *,
    streamlit_module: Any | None = None,
    project_workspace: ProjectWorkspace | None = None,
    ingestion_service: ProjectBoundIngestionService | None = None,
    dashboard_renderer: Callable[..., None] | None = None,
    review_renderer: Callable[..., None] | None = None,
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
            root=root / "data" / "projects",
            repository_root=root,
        )
        if ingestion_service is None
        else ingestion_service
    )
    render_dashboard = (
        render_project_dashboard_ui
        if dashboard_renderer is None
        else dashboard_renderer
    )
    render_review = (
        render_human_review_approval_ui
        if review_renderer is None
        else review_renderer
    )

    apply_pending_app_view(st.session_state)
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

    if active_view == APP_VIEW_REVIEW:
        render_review(
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

    render_project_ingestion_execution(
        st,
        ingestion_service=ingestion_service,
        navigation=navigation,
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
        "Supported Source containers: Markdown, text, JSON, CSV, TSV and PDF. "
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

    for source in inventory.sources:
        if st.button(
            f"Select {source.source_id} for execution",
            key=(
                "turing_generator.select_source."
                f"{source.source_id}"
            ),
        ):
            st.session_state[
                SESSION_SELECTED_ENTITY_ID
            ] = source.source_id
            request_streamlit_rerun(st)

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


def render_project_ingestion_execution(
    st: Any,
    *,
    ingestion_service: ProjectBoundIngestionService,
    navigation: ApplicationNavigationState,
) -> None:
    """Configure and execute one project-bound Agentic Ingestion Run."""

    if navigation.project_id is None:
        return

    st.subheader("2. Run Agentic Ingestion")

    try:
        inventory = ingestion_service.list_registered_sources(
            navigation.project_id
        )
    except Exception:
        st.error(
            "Registered Sources could not be prepared for execution."
        )
        return

    selected_source = next(
        (
            source
            for source in inventory.sources
            if source.source_id == navigation.selected_entity_id
        ),
        None,
    )

    if selected_source is None:
        render_last_ingestion_result(
            st,
            project_id=navigation.project_id,
        )
        st.info(
            "Select a registered Source above to configure "
            "Agentic Ingestion."
        )
        return

    st.caption(
        f"Execution Source: {selected_source.original_filename} · "
        f"{selected_source.source_id} · "
        f"{_SOURCE_ROLE_LABELS.get(selected_source.source_role, selected_source.source_role)}"
    )

    model = st.selectbox(
        "Model",
        options=_P9_MODEL_OPTIONS,
        index=_P9_MODEL_OPTIONS.index(DEFAULT_MODEL),
        key="turing_generator.execution_model",
    )
    team_scope = st.selectbox(
        "Maximum team members per stage",
        options=("1", "all"),
        index=0,
        key="turing_generator.execution_team_scope",
    )
    runs_per_member = st.number_input(
        "Runs per team member",
        min_value=1,
        max_value=5,
        value=1,
        step=1,
        key="turing_generator.execution_runs_per_member",
    )
    dry_run = st.checkbox(
        "Dry run — no LLM calls",
        value=True,
        key="turing_generator.execution_dry_run",
    )

    api_key: str | None = None
    live_confirmation = False

    if dry_run:
        st.info(
            "Dry run is enabled. No external LLM request will be sent."
        )
    else:
        st.warning(
            "Live execution sends the normalized Source text to the "
            "selected LLM provider and may incur costs."
        )
        live_confirmation = st.checkbox(
            "I confirm this live LLM execution.",
            value=False,
            key="turing_generator.execution_live_confirmation",
        )

        environment_key = os.getenv("OPENAI_API_KEY")
        if environment_key:
            api_key = None
            st.caption(
                "OPENAI_API_KEY is available from the process environment."
            )
        else:
            entered_key = st.text_input(
                "OpenAI API key for this run",
                value="",
                type="password",
                key="turing_generator.execution_api_key",
                help=(
                    "Used only for this execution. The key is not "
                    "persisted in project evidence."
                ),
            )
            api_key = entered_key.strip() or None

    if st.button(
        "Run Agentic Ingestion",
        key="turing_generator.run_agentic_ingestion",
        type="primary",
    ):
        if not dry_run and not live_confirmation:
            st.error(
                "Live execution requires explicit confirmation."
            )
        elif (
            not dry_run
            and os.getenv("OPENAI_API_KEY") is None
            and api_key is None
        ):
            st.error(
                "Live OpenAI execution requires an API key."
            )
        else:
            configuration = ProjectIngestionConfiguration(
                provider=DEFAULT_PROVIDER,
                model=model,
                runs_per_member=int(runs_per_member),
                max_members_per_team=(
                    None if team_scope == "all" else 1
                ),
                dry_run=bool(dry_run),
            )

            try:
                result = (
                    ingestion_service.execute_registered_source(
                        navigation.project_id,
                        selected_source.source_id,
                        configuration=configuration,
                        api_key=api_key,
                    )
                )
            except ProjectIngestionConfigurationError:
                st.error(
                    "The execution configuration is invalid."
                )
            except ProjectIngestionExecutionError:
                st.error(
                    "The selected Source cannot start a new Processing "
                    "Run. Inspect its current Run or project issues in "
                    "the Project Dashboard."
                )
            except ProjectIngestionError:
                st.error(
                    "Agentic Ingestion failed safely. No successful "
                    "Processing state was inferred."
                )
            except Exception:
                st.error(
                    "Agentic Ingestion failed unexpectedly. "
                    "No success state was inferred."
                )
            else:
                st.session_state[
                    SESSION_SELECTED_ENTITY_ID
                ] = result.processing_run_id
                st.session_state[
                    _SESSION_LAST_INGESTION_RESULT
                ] = _safe_ingestion_result(result)
                render_ingestion_result_message(st, result)

    render_last_ingestion_result(
        st,
        project_id=navigation.project_id,
    )


def render_ingestion_result_message(
    st: Any,
    result: Any,
) -> None:
    """Render one safe result without exposing filesystem paths."""

    if result.run_state == "awaiting_review":
        st.success(
            "Agentic Ingestion completed and published its "
            "unreviewed artifacts. Human review is required."
        )
    elif result.run_state == "blocked":
        st.error(
            "The Processing Run requires recovery before it can "
            "continue."
        )
    else:
        st.error(
            "The Processing Run failed. No successful ingestion "
            "state was inferred."
        )


def render_last_ingestion_result(
    st: Any,
    *,
    project_id: str,
) -> None:
    """Render the last safe execution identity and dashboard transition."""

    payload = st.session_state.get(
        _SESSION_LAST_INGESTION_RESULT
    )
    if (
        not isinstance(payload, dict)
        or payload.get("project_id") != project_id
    ):
        return

    run_id = payload.get("processing_run_id")
    if not isinstance(run_id, str):
        return

    st.table(
        [
            {
                "Processing Run": run_id,
                "Attempt": payload.get("attempt_id", "—"),
                "State": payload.get("run_state", "unknown"),
                "Stage": payload.get(
                    "processing_stage",
                    "unknown",
                ),
                "Mode": (
                    "Dry run"
                    if payload.get("dry_run") is True
                    else "Live LLM"
                ),
                "Published files": payload.get(
                    "artifact_count",
                    0,
                ),
            }
        ]
    )

    if not st.button(
        "Open Processing Run in Project Dashboard",
        key=(
            "turing_generator.open_processing_run."
            f"{run_id}"
        ),
    ):
        return

    queue_app_view(
        st.session_state,
        active_view=APP_VIEW_DASHBOARD,
        project_id=project_id,
        dashboard_view=DASHBOARD_VIEW_SOURCES,
        selected_entity_id=run_id,
    )
    request_streamlit_rerun(st)


def _safe_ingestion_result(
    result: Any,
) -> dict[str, object]:
    """Reduce a result to stable, secret-free UI state."""

    return {
        "project_id": result.project_id,
        "source_id": result.source_id,
        "processing_run_id": result.processing_run_id,
        "attempt_id": result.attempt_id,
        "run_state": result.run_state,
        "processing_stage": result.processing_stage,
        "dry_run": result.dry_run,
        "artifact_count": len(result.artifact_references),
        "failure_reason": result.failure_reason,
        "recovery_required": result.recovery_required,
    }


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

    queue_app_view(
        st.session_state,
        active_view=APP_VIEW_DASHBOARD,
        project_id=project_id,
        dashboard_view=return_view,
        selected_entity_id=(
            st.session_state.get(
                SESSION_SELECTED_ENTITY_ID
            )
            if project_id is not None
            else None
        ),
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
