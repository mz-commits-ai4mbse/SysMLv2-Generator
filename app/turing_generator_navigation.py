"""Stable application navigation contracts for the Turing Generator UI."""

from __future__ import annotations

from collections.abc import MutableMapping
from dataclasses import dataclass
import re
from typing import Any

from modules.project_workspace.identifiers import is_valid_project_id


APP_VIEW_WORKFLOW = "workflow"
APP_VIEW_DASHBOARD = "dashboard"
APP_VIEW_INGESTION = "ingestion"
APP_VIEW_REVIEW = "review"
APP_VIEW_MODEL_PROPOSAL = "model_proposal"
APP_VIEW_FINAL_REVIEW = "final_review"
APP_VIEW_OUTPUT = "published_output"
APP_VIEWS = (
    APP_VIEW_WORKFLOW,
    APP_VIEW_DASHBOARD,
    APP_VIEW_INGESTION,
    APP_VIEW_REVIEW,
    APP_VIEW_MODEL_PROPOSAL,
    APP_VIEW_FINAL_REVIEW,
    APP_VIEW_OUTPUT,
)

DASHBOARD_VIEW_OVERVIEW = "overview"
DASHBOARD_VIEW_SOURCES = "sources"
DASHBOARD_VIEWS = (
    DASHBOARD_VIEW_OVERVIEW,
    DASHBOARD_VIEW_SOURCES,
    "coverage",
    "attention",
    "traceability",
)

SESSION_APP_VIEW = "turing_generator.active_view"
SESSION_PROJECT_ID = "project_dashboard.project_id"
SESSION_DASHBOARD_VIEW = "project_dashboard.active_view"
SESSION_RETURN_VIEW = "turing_generator.return_view"
SESSION_SELECTED_ENTITY_ID = "turing_generator.selected_entity_id"
SESSION_PENDING_NAVIGATION = "turing_generator.pending_navigation"

_ENTITY_ID_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9._-]{0,119}$")


@dataclass(frozen=True, slots=True)
class ApplicationNavigationState:
    """Validated stable navigation state without filesystem paths."""

    active_view: str
    project_id: str | None
    return_view: str
    selected_entity_id: str | None = None


def normalize_app_view(value: object) -> str:
    """Return one supported application view or the Guided Workflow fallback."""

    return value if value in APP_VIEWS else APP_VIEW_WORKFLOW


def normalize_dashboard_view(value: object) -> str:
    """Return one supported dashboard view or the Overview fallback."""

    return value if value in DASHBOARD_VIEWS else DASHBOARD_VIEW_OVERVIEW


def normalize_project_id(value: object) -> str | None:
    """Return a valid six-digit Project ID or no selected project."""

    return value if is_valid_project_id(value) else None


def normalize_selected_entity_id(value: object) -> str | None:
    """Return one safe stable entity identity or no selected entity."""

    if value is None:
        return None
    if not isinstance(value, str):
        return None
    if _ENTITY_ID_PATTERN.fullmatch(value) is None:
        return None
    return value


def read_navigation_state(
    session_state: MutableMapping[str, Any],
) -> ApplicationNavigationState:
    """Read and normalize navigation state from a Streamlit-like mapping."""

    return ApplicationNavigationState(
        active_view=normalize_app_view(
            session_state.get(SESSION_APP_VIEW)
        ),
        project_id=normalize_project_id(
            session_state.get(SESSION_PROJECT_ID)
        ),
        return_view=normalize_dashboard_view(
            session_state.get(
                SESSION_RETURN_VIEW,
                session_state.get(SESSION_DASHBOARD_VIEW),
            )
        ),
        selected_entity_id=normalize_selected_entity_id(
            session_state.get(SESSION_SELECTED_ENTITY_ID)
        ),
    )


def select_app_view(
    session_state: MutableMapping[str, Any],
    *,
    active_view: str,
    project_id: str | None = None,
    return_view: str | None = None,
    selected_entity_id: str | None = None,
) -> ApplicationNavigationState:
    """Persist one validated application-navigation transition."""

    if active_view not in APP_VIEWS:
        raise ValueError("active_view is not supported.")

    if project_id is not None and not is_valid_project_id(project_id):
        raise ValueError(
            "project_id must be a string containing exactly six digits."
        )

    normalized_return_view = normalize_dashboard_view(return_view)

    if selected_entity_id is not None:
        normalized_entity_id = normalize_selected_entity_id(
            selected_entity_id
        )
        if normalized_entity_id is None:
            raise ValueError(
                "selected_entity_id must be a stable identifier and "
                "must not contain a filesystem path."
            )
    else:
        normalized_entity_id = None

    session_state[SESSION_APP_VIEW] = active_view

    if project_id is not None:
        session_state[SESSION_PROJECT_ID] = project_id

    session_state[SESSION_RETURN_VIEW] = normalized_return_view

    if normalized_entity_id is None:
        session_state.pop(SESSION_SELECTED_ENTITY_ID, None)
    else:
        session_state[
            SESSION_SELECTED_ENTITY_ID
        ] = normalized_entity_id

    return read_navigation_state(session_state)


def queue_app_view(
    session_state: MutableMapping[str, Any],
    *,
    active_view: str,
    project_id: str | None = None,
    dashboard_view: str | None = None,
    selected_entity_id: str | None = None,
) -> None:
    """Queue a validated transition for the next Streamlit rerun."""

    if active_view not in APP_VIEWS:
        raise ValueError("active_view is not supported.")

    if project_id is not None and not is_valid_project_id(project_id):
        raise ValueError(
            "project_id must be a string containing exactly six digits."
        )

    normalized_dashboard_view = normalize_dashboard_view(
        dashboard_view
    )
    normalized_entity_id = normalize_selected_entity_id(
        selected_entity_id
    )
    if (
        selected_entity_id is not None
        and normalized_entity_id is None
    ):
        raise ValueError(
            "selected_entity_id must be a stable identifier and "
            "must not contain a filesystem path."
        )

    session_state[SESSION_PENDING_NAVIGATION] = {
        "active_view": active_view,
        "project_id": project_id,
        "dashboard_view": normalized_dashboard_view,
        "selected_entity_id": normalized_entity_id,
    }


def apply_pending_app_view(
    session_state: MutableMapping[str, Any],
) -> ApplicationNavigationState:
    """Apply one queued transition before Streamlit widgets are created."""

    payload = session_state.pop(
        SESSION_PENDING_NAVIGATION,
        None,
    )
    if not isinstance(payload, dict):
        return read_navigation_state(session_state)

    project_id = normalize_project_id(
        payload.get("project_id")
    )
    if project_id is None:
        session_state.pop(SESSION_PROJECT_ID, None)

    dashboard_view = normalize_dashboard_view(
        payload.get("dashboard_view")
    )
    state = select_app_view(
        session_state,
        active_view=normalize_app_view(
            payload.get("active_view")
        ),
        project_id=project_id,
        return_view=dashboard_view,
        selected_entity_id=normalize_selected_entity_id(
            payload.get("selected_entity_id")
        ),
    )
    session_state[SESSION_DASHBOARD_VIEW] = dashboard_view
    session_state[
        "project_dashboard.view_selector"
    ] = dashboard_view
    session_state.pop(
        "project_dashboard.open_reference",
        None,
    )
    return state
