"""Global application context for the Turing Generator UI."""

from __future__ import annotations

from typing import Any

from app.presentation_preferences import (
    SESSION_SHOW_TECHNICAL_DETAILS,
)
from app.turing_generator_navigation import (
    SESSION_PROJECT_ID,
    SESSION_SELECTED_ENTITY_ID,
)
from modules.project_workspace.errors import ProjectWorkspaceError


SESSION_GLOBAL_CONTROLS_ACTIVE = (
    "turing_generator.global_controls_active"
)
SESSION_GLOBAL_PROJECT_SELECTOR = (
    "turing_generator.global_project_selector"
)
SESSION_GLOBAL_PENDING_PROJECT_ID = (
    "turing_generator.global_pending_project_id"
)
SESSION_GLOBAL_CREATE_PROJECT_FORM = (
    "turing_generator.global_create_project_form"
)


def render_global_controls(
    st: Any,
    *,
    workspace,
) -> None:
    """Render application-level context without engineering authority."""

    st.session_state[SESSION_GLOBAL_CONTROLS_ACTIVE] = True

    columns = st.columns([5, 2])

    # ------------------------------------------------------------------
    # Presentation depth
    # ------------------------------------------------------------------

    with columns[1]:
        technical_details = st.toggle(
            "Technical details",
            key=SESSION_SHOW_TECHNICAL_DETAILS,
            help=(
                "Show processing identities, provenance, traceability "
                "and diagnostic information in addition to the focused "
                "engineering view."
            ),
        )

    # ------------------------------------------------------------------
    # Project discovery
    # ------------------------------------------------------------------

    try:
        scan = workspace.scan_projects()
        projects = tuple(scan.valid_projects)
    except Exception:
        projects = ()

    project_by_id = {
        project.project_id: project
        for project in projects
    }
    valid_project_ids = tuple(project_by_id)

    # A newly created Project is activated only before the selectbox is
    # instantiated on the following Streamlit rerun.
    pending_project_id = st.session_state.pop(
        SESSION_GLOBAL_PENDING_PROJECT_ID,
        None,
    )

    if pending_project_id in project_by_id:
        st.session_state[SESSION_PROJECT_ID] = (
            pending_project_id
        )
        st.session_state[
            SESSION_GLOBAL_PROJECT_SELECTOR
        ] = pending_project_id

    current_project_id = st.session_state.get(
        SESSION_PROJECT_ID
    )

    if current_project_id not in valid_project_ids:
        current_project_id = None
        st.session_state.pop(
            SESSION_PROJECT_ID,
            None,
        )

    # Synchronize programmatic Project-context changes before widget
    # creation. This is presentation state only.
    if (
        st.session_state.get(
            SESSION_GLOBAL_PROJECT_SELECTOR
        )
        != current_project_id
    ):
        st.session_state[
            SESSION_GLOBAL_PROJECT_SELECTOR
        ] = current_project_id

    options = (None, *valid_project_ids)

    def project_label(project_id):
        if project_id is None:
            return (
                "Select project…"
                if valid_project_ids
                else "No project available"
            )

        project = project_by_id[project_id]

        if technical_details:
            return (
                f"{project.display_name} · "
                f"{project.project_id}"
            )

        return project.display_name

    def project_changed() -> None:
        selected = st.session_state.get(
            SESSION_GLOBAL_PROJECT_SELECTOR
        )
        previous = st.session_state.get(
            SESSION_PROJECT_ID
        )

        if selected is None:
            st.session_state.pop(
                SESSION_PROJECT_ID,
                None,
            )
        else:
            st.session_state[
                SESSION_PROJECT_ID
            ] = selected

        if previous != selected:
            _clear_project_local_navigation(st)

    # ------------------------------------------------------------------
    # Global Project context
    # ------------------------------------------------------------------

    with columns[0]:
        selected = st.selectbox(
            "Project",
            options=options,
            index=options.index(current_project_id),
            format_func=project_label,
            key=SESSION_GLOBAL_PROJECT_SELECTOR,
            on_change=project_changed,
        )

        created_project_id = (
            _render_global_project_creation(
                st,
                workspace=workspace,
            )
        )

        # Creation requests a rerun. Do not subsequently synchronize the
        # old selectbox value back over the newly created Project context.
        if created_project_id is not None:
            return

    # Compatibility for Streamlit-like test adapters that do not execute
    # widget callbacks.
    if selected != st.session_state.get(
        SESSION_PROJECT_ID
    ):
        previous = st.session_state.get(
            SESSION_PROJECT_ID
        )

        if selected is None:
            st.session_state.pop(
                SESSION_PROJECT_ID,
                None,
            )
        else:
            st.session_state[
                SESSION_PROJECT_ID
            ] = selected

        if previous != selected:
            _clear_project_local_navigation(st)


def _render_global_project_creation(
    st: Any,
    *,
    workspace,
) -> str | None:
    """Create a Project without leaving the current application view."""

    show_form = (
        st.session_state.get(
            SESSION_GLOBAL_CREATE_PROJECT_FORM,
            False,
        )
        is True
    )

    if not show_form:
        if st.button(
            "＋ Create new project",
            key="turing_generator.open_create_project",
        ):
            st.session_state[
                SESSION_GLOBAL_CREATE_PROJECT_FORM
            ] = True
            show_form = True

    if not show_form:
        return None

    with st.form(
        "turing_generator.create_project",
        clear_on_submit=False,
    ):
        display_name = st.text_input(
            "Project name",
            max_chars=120,
            help=(
                "Human-readable Project name shown throughout "
                "the engineering workspace."
            ),
        )
        description = st.text_area(
            "Description (optional)",
            max_chars=2000,
            help=(
                "Short engineering context for the Project."
            ),
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
        st.error(
            f"Project could not be created: {exc}"
        )
        return None
    except Exception:
        st.error(
            "Project creation failed unexpectedly. "
            "No partial Project state was accepted."
        )
        return None

    # Project identity itself is application context. The selectbox widget
    # is not modified after instantiation; instead the pending identity is
    # consumed before widget creation on the next rerun.
    st.session_state[
        SESSION_PROJECT_ID
    ] = manifest.project_id
    st.session_state[
        SESSION_GLOBAL_PENDING_PROJECT_ID
    ] = manifest.project_id

    _clear_project_local_navigation(st)

    st.session_state.pop(
        SESSION_GLOBAL_CREATE_PROJECT_FORM,
        None,
    )

    st.success(
        f"Project created: {manifest.display_name}"
    )

    rerun = getattr(st, "rerun", None)
    if callable(rerun):
        rerun()

    return manifest.project_id


def _clear_project_local_navigation(st: Any) -> None:
    """Remove UI selections that must not leak between Projects."""

    st.session_state.pop(
        SESSION_SELECTED_ENTITY_ID,
        None,
    )
    st.session_state.pop(
        "project_dashboard.open_reference",
        None,
    )
    st.session_state.pop(
        "project_dashboard.inline_review_reference",
        None,
    )
