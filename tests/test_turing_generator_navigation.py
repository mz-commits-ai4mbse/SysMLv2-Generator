"""Tests for the common P9 Turing Generator navigation shell."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.turing_generator_navigation import (
    APP_VIEW_DASHBOARD,
    APP_VIEW_INGESTION,
    SESSION_APP_VIEW,
    SESSION_PROJECT_ID,
    ApplicationNavigationState,
    normalize_app_view,
    read_navigation_state,
    select_app_view,
)
from app.turing_generator_ui import (
    render_project_bound_ingestion_entry,
    render_turing_generator_ui,
)


class _Context:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False


class FakeStreamlit:
    def __init__(self, *, clicked_keys=()):
        self.session_state = {}
        self.clicked_keys = set(clicked_keys)
        self.calls = []
        self.rerun_count = 0

    def radio(
        self,
        label,
        *,
        options,
        index,
        format_func,
        horizontal,
        key,
    ):
        self.calls.append(
            (
                "radio",
                label,
                tuple(options),
                index,
                horizontal,
                key,
            )
        )
        if key in self.session_state:
            return self.session_state[key]
        selected = options[index]
        self.session_state[key] = selected
        return selected

    def header(self, text):
        self.calls.append(("header", text))

    def caption(self, text):
        self.calls.append(("caption", text))

    def info(self, text):
        self.calls.append(("info", text))

    def error(self, text):
        self.calls.append(("error", text))

    def button(self, label, *, key):
        self.calls.append(("button", label, key))
        return key in self.clicked_keys

    def rerun(self):
        self.rerun_count += 1


class FakeWorkspace:
    def __init__(self, *, manifest=None, error=None):
        self.manifest = (
            SimpleNamespace(
                project_id="123456",
                display_name="Example Project",
            )
            if manifest is None
            else manifest
        )
        self.error = error
        self.calls = []

    def load_project(self, project_id):
        self.calls.append(project_id)
        if self.error is not None:
            raise self.error
        return self.manifest


def test_navigation_defaults_to_dashboard_without_project():
    state = read_navigation_state({})

    assert state == ApplicationNavigationState(
        active_view=APP_VIEW_DASHBOARD,
        project_id=None,
        return_view="overview",
        selected_entity_id=None,
    )


def test_invalid_application_view_normalizes_to_dashboard():
    assert normalize_app_view("unsupported") == APP_VIEW_DASHBOARD


def test_select_app_view_persists_only_stable_navigation_state():
    session_state = {}

    state = select_app_view(
        session_state,
        active_view=APP_VIEW_INGESTION,
        project_id="123456",
        return_view="sources",
        selected_entity_id="SRC-000001",
    )

    assert state.active_view == APP_VIEW_INGESTION
    assert state.project_id == "123456"
    assert state.return_view == "sources"
    assert state.selected_entity_id == "SRC-000001"


def test_select_app_view_rejects_invalid_project_id():
    with pytest.raises(ValueError, match="six digits"):
        select_app_view(
            {},
            active_view=APP_VIEW_INGESTION,
            project_id="../123456",
        )


def test_select_app_view_rejects_filesystem_like_entity_identity():
    with pytest.raises(ValueError, match="filesystem path"):
        select_app_view(
            {},
            active_view=APP_VIEW_INGESTION,
            project_id="123456",
            selected_entity_id="../../secret",
        )


def test_common_shell_routes_dashboard_without_reimplementing_it(
    tmp_path,
):
    st = FakeStreamlit()
    workspace = FakeWorkspace()
    dashboard_calls = []

    def dashboard_renderer(root, **kwargs):
        dashboard_calls.append((root, kwargs))

    render_turing_generator_ui(
        tmp_path,
        streamlit_module=st,
        project_workspace=workspace,
        dashboard_renderer=dashboard_renderer,
    )

    assert len(dashboard_calls) == 1
    root, kwargs = dashboard_calls[0]
    assert root == tmp_path
    assert kwargs["streamlit_module"] is st
    assert kwargs["project_workspace"] is workspace
    assert workspace.calls == []


def test_ingestion_entry_fails_closed_without_selected_project(
    tmp_path,
):
    st = FakeStreamlit()
    st.session_state[SESSION_APP_VIEW] = APP_VIEW_INGESTION
    workspace = FakeWorkspace()

    render_turing_generator_ui(
        tmp_path,
        streamlit_module=st,
        project_workspace=workspace,
        dashboard_renderer=lambda *args, **kwargs: None,
    )

    assert workspace.calls == []
    assert any(call[0] == "error" for call in st.calls)
    assert not any(
        call[0] == "caption" and "Selected Project:" in call[1]
        for call in st.calls
    )


def test_valid_ingestion_entry_shows_project_and_returns_to_dashboard():
    st = FakeStreamlit(
        clicked_keys={"turing_generator.return_to_dashboard"}
    )
    st.session_state[SESSION_APP_VIEW] = APP_VIEW_INGESTION
    st.session_state[SESSION_PROJECT_ID] = "123456"
    workspace = FakeWorkspace()

    render_project_bound_ingestion_entry(
        st,
        workspace=workspace,
        navigation=read_navigation_state(st.session_state),
    )

    assert workspace.calls == ["123456"]
    assert any(
        call[0] == "caption"
        and "Example Project · 123456" in call[1]
        for call in st.calls
    )
    assert st.session_state[SESSION_APP_VIEW] == APP_VIEW_DASHBOARD
    assert st.session_state[SESSION_PROJECT_ID] == "123456"
    assert st.rerun_count == 1
