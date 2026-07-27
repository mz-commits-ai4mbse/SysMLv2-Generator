"""Stable application navigation contracts for the Turing Generator UI."""

from __future__ import annotations

from collections.abc import MutableMapping
from dataclasses import dataclass
import re
from typing import Any

from modules.project_workspace.identifiers import is_valid_project_id


APP_VIEW_DASHBOARD = "dashboard"
APP_VIEW_INGESTION = "ingestion"
APP_VIEWS = (
    APP_VIEW_DASHBOARD,
    APP_VIEW_INGESTION,
)

DASHBOARD_VIEW_OVERVIEW = "overview"
DASHBOARD_VIEWS = (
    DASHBOARD_VIEW_OVERVIEW,
    "sources",
    "coverage",
    "attention",
    "traceability",
)

SESSION_APP_VIEW = "turing_generator.active_view"
SESSION_PROJECT_ID = "project_dashboard.project_id"
SESSION_DASHBOARD_VIEW = "project_dashboard.active_view"
SESSION_RETURN_VIEW = "turing_generator.return_view"
SESSION_SELECTED_ENTITY_ID = "turing_generator.selected_entity_id"

_ENTITY_ID_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9._-]{0,119}$")


@dataclass(frozen=True, slots=True)
class ApplicationNavigationState:
    """Validated stable navigation state without filesystem paths."""

    active_view: str
    project_id: str | None
    return_view: str
    selected_entity_id: str | None = None


def normalize_app_view(value: object) -> str:
    """Return one supported application view or the dashboard fallback."""

    return value if value in APP_VIEWS else APP_VIEW_DASHBOARD


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
