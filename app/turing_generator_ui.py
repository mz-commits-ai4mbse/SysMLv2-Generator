"""Common Streamlit application shell for the Turing Generator."""

from __future__ import annotations

from collections.abc import Callable
from contextlib import nullcontext
import os
from pathlib import Path
from typing import Any

from app.global_controls import render_global_controls
from app.guided_workflow_detail_ui import (
    render_final_model_review_ui,
    render_model_proposal_ui,
    render_published_output_ui,
)
from app.guided_workflow_ui import render_guided_workflow_ui
from app.human_review_approval_ui import (
    render_human_review_approval_ui,
)
from app.project_dashboard_ui import render_project_dashboard_ui
from app.presentation_preferences import technical_details_enabled
from app.turing_generator_navigation import (
    APP_VIEW_WORKFLOW,
    APP_VIEW_DASHBOARD,
    APP_VIEW_FINAL_REVIEW,
    APP_VIEW_INGESTION,
    APP_VIEW_MODEL_PROPOSAL,
    APP_VIEW_OUTPUT,
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
from modules.guided_workflow import (
    GuidedWorkflowValidationError,
    build_processing_source_view,
)
from modules.project_ingestion import (
    DEFAULT_MODEL,
    DEFAULT_PROVIDER,
    ProjectBoundIngestionService,
    ProjectIngestionConfiguration,
    ProjectIngestionConfigurationError,
    calculate_ingestion_configuration_fingerprint,
    ProjectIngestionError,
    ProjectIngestionExecutionError,
    ProjectIngestionInputError,
    ProjectIngestionRecoveryRequiredError,
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
    APP_VIEW_WORKFLOW: "Engineering Workspace",
    APP_VIEW_DASHBOARD: "Project Dashboard",
    APP_VIEW_INGESTION: "Processing",
    APP_VIEW_REVIEW: "Human Review & Approval",
    APP_VIEW_MODEL_PROPOSAL: "Model Proposal",
    APP_VIEW_FINAL_REVIEW: "Final Model Review",
    APP_VIEW_OUTPUT: "Published Output",
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
_SESSION_INGESTION_IN_PROGRESS = (
    "turing_generator.ingestion_in_progress"
)


def render_turing_generator_ui(
    project_root: Path,
    *,
    streamlit_module: Any | None = None,
    project_workspace: ProjectWorkspace | None = None,
    ingestion_service: ProjectBoundIngestionService | None = None,
    workflow_renderer: Callable[..., None] | None = None,
    dashboard_renderer: Callable[..., None] | None = None,
    review_renderer: Callable[..., None] | None = None,
    model_proposal_renderer: Callable[..., None] | None = None,
    final_review_renderer: Callable[..., None] | None = None,
    output_renderer: Callable[..., None] | None = None,
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
    render_workflow = (
        render_guided_workflow_ui
        if workflow_renderer is None
        else workflow_renderer
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
    render_model_proposal = (
        render_model_proposal_ui
        if model_proposal_renderer is None
        else model_proposal_renderer
    )
    render_final_review = (
        render_final_model_review_ui
        if final_review_renderer is None
        else final_review_renderer
    )
    render_output = (
        render_published_output_ui
        if output_renderer is None
        else output_renderer
    )

    apply_pending_app_view(st.session_state)

    render_global_controls(
        st,
        workspace=workspace,
    )

    navigation = read_navigation_state(st.session_state)
    active_view = render_application_navigation(
        st,
        current_view=navigation.active_view,
    )

    if active_view == APP_VIEW_WORKFLOW:
        render_workflow(
            root,
            streamlit_module=st,
            project_workspace=workspace,
        )
        return

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

    if active_view == APP_VIEW_MODEL_PROPOSAL:
        render_model_proposal(
            root,
            streamlit_module=st,
        )
        return

    if active_view == APP_VIEW_FINAL_REVIEW:
        render_final_review(
            root,
            streamlit_module=st,
        )
        return

    if active_view == APP_VIEW_OUTPUT:
        render_output(
            root,
            streamlit_module=st,
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

    if SESSION_APP_VIEW not in st.session_state:
        st.session_state[SESSION_APP_VIEW] = current_view

    selected = st.radio(
        "Workspace",
        options=APP_VIEWS,
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
    """Render the project-bound Processing workspace."""

    technical = technical_details_enabled(st.session_state)
    st.header("Processing")

    if navigation.project_id is None:
        st.error(
            "No valid Project is selected. Select or create a Project "
            "before processing engineering sources."
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

    if technical:
        st.caption(
            f"Project: {manifest.display_name} · {manifest.project_id}"
        )
    else:
        st.caption(f"Project: {manifest.display_name}")

    st.caption(
        "Add a source, run processing, then continue with Human Review. "
        "Processing results remain unreviewed engineering evidence."
    )

    render_project_source_registration(
        st,
        ingestion_service=ingestion_service,
        navigation=navigation,
    )

    render_project_ingestion_execution(
        st,
        ingestion_service=ingestion_service,
        navigation=read_navigation_state(st.session_state),
    )

    render_dashboard_return_control(
        st,
        project_id=manifest.project_id,
        return_view=navigation.return_view,
        label="Open Project Dashboard",
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

    technical = technical_details_enabled(st.session_state)

    st.subheader("Add source")
    st.caption(
        "Upload an engineering source or supporting context for this Project."
    )
    if technical:
        st.caption(
            "Supported containers: Markdown, text, JSON, CSV, TSV and PDF. "
            "PDF processing requires a machine-readable text layer; "
            "OCR and image-only content remain outside the MVP."
        )

    uploaded_file = st.file_uploader(
        "Upload source",
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
        st.info("Upload a source file to enable registration.")
    else:
        uploaded_size = getattr(uploaded_file, "size", None)
        size_text = (
            _format_source_size(uploaded_size)
            if isinstance(uploaded_size, int)
            else "size unavailable"
        )
        st.caption(
            f"Ready to add: {uploaded_file.name} · {size_text}"
        )

        if st.button(
            "Add source",
            key="turing_generator.register_source",
            type="primary",
        ):
            try:
                result = ingestion_service.register_uploaded_source(
                    navigation.project_id,
                    original_filename=uploaded_file.name,
                    content=_uploaded_file_bytes(uploaded_file),
                    source_role=source_role,
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
                if technical:
                    st.success(
                        f"Source added: {result.original_filename} · "
                        f"{result.source_id}"
                    )
                else:
                    st.success(
                        f"Source added: {result.original_filename}"
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
    """Render registered Sources content-first with optional technical detail."""

    technical = technical_details_enabled(st.session_state)
    st.subheader("Sources")

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
        st.info("No sources have been added yet.")
        return

    rows = []
    for source in inventory.sources:
        row = {
            "Filename": source.original_filename,
            "Role": _SOURCE_ROLE_LABELS.get(
                source.source_role,
                source.source_role,
            ),
            "Size": _format_source_size(source.size_bytes),
        }
        if technical:
            row.update(
                {
                    "Source ID": source.source_id,
                    "Media type": source.media_type,
                    "SHA-256": source.sha256[:12],
                }
            )
        rows.append(row)

    st.table(rows)

    for source in inventory.sources:
        if st.button(
            f"Use {source.original_filename}",
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
        if technical:
            st.caption(
                f"Selected source: {selected_source.original_filename} · "
                f"{selected_source.source_id}"
            )
        else:
            st.caption(
                f"Selected source: {selected_source.original_filename}"
            )


def render_project_ingestion_execution(
    st: Any,
    *,
    ingestion_service: ProjectBoundIngestionService,
    navigation: ApplicationNavigationState,
) -> None:
    """Configure, execute or retry one project-bound Processing operation."""

    if navigation.project_id is None:
        return

    technical = technical_details_enabled(st.session_state)
    st.subheader("Process selected source")

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
        st.info("Select a source above to continue.")
        return

    role_label = _SOURCE_ROLE_LABELS.get(
        selected_source.source_role,
        selected_source.source_role,
    )
    if technical:
        st.caption(
            f"Source: {selected_source.original_filename} · "
            f"{selected_source.source_id} · {role_label}"
        )
    else:
        st.caption(
            f"Source: {selected_source.original_filename} · {role_label}"
        )

    local_execution = st.session_state.get(
        _SESSION_INGESTION_IN_PROGRESS
    )
    if (
        isinstance(local_execution, dict)
        and local_execution.get("project_id")
        == navigation.project_id
        and local_execution.get("source_id")
        == selected_source.source_id
    ):
        st.info(
            "Processing is already running in this application session."
        )
        return

    state_reader = getattr(
        ingestion_service,
        "source_execution_state",
        None,
    )
    supports_state = callable(state_reader)
    if supports_state:
        try:
            execution_state = state_reader(
                navigation.project_id,
                selected_source.source_id,
            )
        except ProjectIngestionError:
            st.error(
                "The current Processing state could not be validated. "
                "No execution action is available."
            )
            return
        except Exception:
            st.error(
                "The current Processing state is unavailable. "
                "No execution action is available."
            )
            return
    else:
        execution_state = None

    try:
        processing_view = build_processing_source_view(
            selected_source,
            execution_state,
        )
    except GuidedWorkflowValidationError:
        st.error(
            "The Processing presentation could not be bound to the "
            "selected Source and current Processing state."
        )
        return

    _render_processing_state_summary(
        st,
        processing_view,
        technical=technical,
    )

    if execution_state is not None:
        if execution_state.run_state == "running":
            render_last_ingestion_result(
                st,
                project_id=navigation.project_id,
            )
            return

        if execution_state.run_state == "awaiting_review":
            render_last_ingestion_result(
                st,
                project_id=navigation.project_id,
            )
            _render_human_review_transition(
                st,
                project_id=navigation.project_id,
                run_id=execution_state.processing_run_id,
            )
            return

        if execution_state.recovery_required:
            render_last_ingestion_result(
                st,
                project_id=navigation.project_id,
            )
            return

        if execution_state.run_state == "completed":
            return

    retry_mode = bool(
        execution_state is not None
        and execution_state.can_retry
    )

    if not technical:
        st.caption(
            "Default processing settings are ready. "
            "Open Processing options to change them."
        )

    with _processing_options_context(
        st,
        expanded=technical,
    ):
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
            if technical:
                st.info(
                    "Dry run is enabled. No external LLM request "
                    "will be sent."
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
                if technical:
                    st.caption(
                        "OPENAI_API_KEY is available from the process "
                        "environment."
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

    configuration = ProjectIngestionConfiguration(
        provider=DEFAULT_PROVIDER,
        model=model,
        runs_per_member=int(runs_per_member),
        max_members_per_team=(
            None if team_scope == "all" else 1
        ),
        dry_run=bool(dry_run),
    )

    configuration_matches = True
    if retry_mode:
        configuration_matches = (
            execution_state.configuration_fingerprint
            == calculate_ingestion_configuration_fingerprint(
                configuration
            )
        )
        if technical:
            st.warning(
                "The previous Processing Attempt failed. Retry preserves "
                f"{execution_state.processing_run_id} and creates a new "
                "immutable Attempt."
            )
        else:
            st.warning(
                "The previous processing attempt failed. "
                "Retry creates a new traceable attempt."
            )

        if not configuration_matches:
            st.warning(
                "Retry requires the exact material configuration of "
                "the failed Run. Restore the original model, team "
                "scope, runs-per-member and dry/live mode."
            )

    action_key = (
        "turing_generator.retry_agentic_ingestion"
        if retry_mode
        else "turing_generator.run_agentic_ingestion"
    )
    action_label = (
        "Retry processing"
        if retry_mode
        else "Run processing"
    )

    action_placeholder = None
    clicked = False
    if not retry_mode or configuration_matches:
        empty_factory = getattr(st, "empty", None)
        if callable(empty_factory):
            action_placeholder = empty_factory()
            clicked = action_placeholder.button(
                action_label,
                key=action_key,
                type="primary",
            )
        else:
            clicked = st.button(
                action_label,
                key=action_key,
                type="primary",
            )

    if clicked:
        if action_placeholder is not None:
            action_placeholder.empty()

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
            st.session_state[
                _SESSION_INGESTION_IN_PROGRESS
            ] = {
                "project_id": navigation.project_id,
                "source_id": selected_source.source_id,
            }
            st.info(
                "Retrying processing…"
                if retry_mode
                else "Starting processing…"
            )

            def render_started(snapshot) -> None:
                if technical:
                    st.info(
                        "Processing is running · "
                        f"{snapshot.processing_run_id} · "
                        f"{snapshot.attempt_id or 'attempt unavailable'} · "
                        f"{snapshot.processing_stage or 'stage unavailable'}."
                    )
                else:
                    st.info("Processing is running…")

            try:
                if retry_mode:
                    result = ingestion_service.retry_registered_source(
                        navigation.project_id,
                        selected_source.source_id,
                        execution_state.processing_run_id,
                        configuration=configuration,
                        api_key=api_key,
                        execution_observer=render_started,
                    )
                elif supports_state:
                    result = ingestion_service.execute_registered_source(
                        navigation.project_id,
                        selected_source.source_id,
                        configuration=configuration,
                        api_key=api_key,
                        execution_observer=render_started,
                    )
                else:
                    result = ingestion_service.execute_registered_source(
                        navigation.project_id,
                        selected_source.source_id,
                        configuration=configuration,
                        api_key=api_key,
                    )
            except ProjectIngestionConfigurationError:
                st.error(
                    "The execution configuration is invalid or no "
                    "longer matches the failed Run."
                )
            except ProjectIngestionExecutionError:
                st.error(
                    "The selected Source cannot start this Processing "
                    "operation. Inspect its current Run in the "
                    "Project Dashboard."
                )
            except ProjectIngestionRecoveryRequiredError:
                st.error(
                    "The Processing Run requires explicit recovery "
                    "before execution can continue."
                )
            except ProjectIngestionError:
                st.error(
                    "Processing failed safely. No successful "
                    "Processing state was inferred."
                )
            except Exception:
                st.error(
                    "Processing failed unexpectedly. "
                    "No success state was inferred."
                )
            else:
                st.session_state[
                    SESSION_SELECTED_ENTITY_ID
                ] = (
                    selected_source.source_id
                    if result.run_state in {"failed", "blocked"}
                    else result.processing_run_id
                )
                st.session_state[
                    _SESSION_LAST_INGESTION_RESULT
                ] = _safe_ingestion_result(result)
                render_ingestion_result_message(st, result)
            finally:
                st.session_state.pop(
                    _SESSION_INGESTION_IN_PROGRESS,
                    None,
                )

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
        return

    if result.run_state == "blocked":
        st.error(
            "The Processing Run requires recovery before it can "
            "continue."
        )
        return

    safe_messages = {
        "llm_authentication_failed": (
            "LLM authentication failed. Check the API credentials "
            "and retry this Processing Run."
        ),
        "llm_permission_denied": (
            "The LLM provider denied access. Check provider permissions "
            "and retry."
        ),
        "llm_rate_limited": (
            "The LLM provider rate-limited this execution. Retry later."
        ),
        "llm_timeout": (
            "The LLM request timed out. Retry the Processing Run."
        ),
        "llm_connection_failed": (
            "The LLM provider could not be reached. Check connectivity "
            "and retry the Processing Run."
        ),
        "llm_request_rejected": (
            "The LLM provider rejected the request. Check the selected "
            "provider/model configuration before retrying."
        ),
        "llm_provider_unavailable": (
            "The LLM provider is currently unavailable. Retry later."
        ),
    }
    st.error(
        safe_messages.get(
            getattr(result, "failure_reason", None),
            (
                "The Processing Run failed. No successful ingestion "
                "state was inferred."
            ),
        )
    )


def render_last_ingestion_result(
    st: Any,
    *,
    project_id: str,
) -> None:
    """Render the last safe Processing result using the current presentation depth."""

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

    technical = technical_details_enabled(st.session_state)
    row = {
        "Status": _processing_result_label(
            payload.get("run_state")
        ),
        "Mode": (
            "Dry run"
            if payload.get("dry_run") is True
            else "Live LLM"
        ),
        "Published outputs": payload.get(
            "artifact_count",
            0,
        ),
    }
    if technical:
        row.update(
            {
                "Processing Run": run_id,
                "Attempt": payload.get("attempt_id", "—"),
                "Stage": payload.get(
                    "processing_stage",
                    "unknown",
                ),
            }
        )

    st.table([row])

    if payload.get("run_state") == "awaiting_review":
        _render_human_review_transition(
            st,
            project_id=project_id,
            run_id=run_id,
        )

    if not technical:
        return

    if not st.button(
        "Open Processing details",
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


def _render_processing_state_summary(
    st: Any,
    view,
    *,
    technical: bool,
) -> None:
    """Render human-readable Processing state before technical identity."""

    if view.run_state is None:
        st.info(view.status_label)
    elif view.run_state == "running":
        st.info("Processing is running.")
    elif view.run_state == "awaiting_review":
        st.info(
            "Processing completed. Human Review is required before "
            "the result can become approved engineering input."
        )
    elif view.recovery_required or view.run_state in {"blocked", "failed"}:
        st.error(view.status_label)
    elif view.run_state == "completed":
        st.success("Processing is complete.")
    else:
        st.info(view.status_label)

    if technical and view.processing_run_id is not None:
        st.caption(
            f"Run: {view.processing_run_id} · "
            f"Attempt: {view.attempt_id or 'unavailable'} · "
            f"State: {view.run_state or 'unavailable'}"
        )
        if view.failure_reason:
            st.caption(f"Failure reason: {view.failure_reason}")
        if view.blocked_reason:
            st.caption(f"Blocked reason: {view.blocked_reason}")


def _processing_options_context(
    st: Any,
    *,
    expanded: bool,
):
    """Collapse optional execution tuning in the Focused presentation."""

    expander = getattr(st, "expander", None)
    if callable(expander):
        return expander(
            "Processing options",
            expanded=expanded,
        )
    return nullcontext()


def _render_human_review_transition(
    st: Any,
    *,
    project_id: str,
    run_id: str | None,
) -> None:
    """Queue Human Review without carrying stale entity navigation."""

    suffix = run_id or "current"
    if not st.button(
        "Continue to Human Review",
        key=f"turing_generator.continue_human_review.{suffix}",
        type="primary",
    ):
        return

    queue_app_view(
        st.session_state,
        active_view=APP_VIEW_REVIEW,
        project_id=project_id,
        selected_entity_id=None,
    )
    request_streamlit_rerun(st)


def _processing_result_label(value: object) -> str:
    labels = {
        "created": "Prepared",
        "running": "Processing",
        "awaiting_review": "Ready for Human Review",
        "blocked": "Recovery required",
        "failed": "Failed",
        "completed": "Complete",
        "superseded": "Superseded",
    }
    return labels.get(value, "Unknown")


def _format_source_size(value: int) -> str:
    if value < 1024:
        return f"{value} B"
    if value < 1024 * 1024:
        return f"{value / 1024:.1f} KB"
    return f"{value / (1024 * 1024):.1f} MB"


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
