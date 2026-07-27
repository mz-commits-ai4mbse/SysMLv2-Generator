"""Tests for the common P9 Turing Generator navigation shell."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from modules.project_sources import DuplicateSourceContentError

from app.turing_generator_navigation import (
    APP_VIEW_DASHBOARD,
    APP_VIEW_INGESTION,
    SESSION_APP_VIEW,
    SESSION_PENDING_NAVIGATION,
    SESSION_PROJECT_ID,
    SESSION_SELECTED_ENTITY_ID,
    ApplicationNavigationState,
    apply_pending_app_view,
    normalize_app_view,
    read_navigation_state,
    select_app_view,
)
from app.turing_generator_ui import (
    render_project_bound_ingestion_entry,
    render_project_source_registration,
    render_turing_generator_ui,
)


class _Context:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False


class FakeStreamlit:
    def __init__(
        self,
        *,
        clicked_keys=(),
        uploaded_file=None,
        selected_source_role="engineering_source",
    ):
        self.session_state = {}
        self.clicked_keys = set(clicked_keys)
        self.uploaded_file = uploaded_file
        self.selected_source_role = selected_source_role
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

    def subheader(self, text):
        self.calls.append(("subheader", text))

    def caption(self, text):
        self.calls.append(("caption", text))

    def info(self, text):
        self.calls.append(("info", text))

    def warning(self, text):
        self.calls.append(("warning", text))

    def error(self, text):
        self.calls.append(("error", text))

    def success(self, text):
        self.calls.append(("success", text))

    def file_uploader(self, label, *, type, key):
        self.calls.append(
            ("file_uploader", label, tuple(type), key)
        )
        return self.uploaded_file

    def selectbox(
        self,
        label,
        *,
        options,
        index,
        format_func,
        key,
    ):
        self.calls.append(
            (
                "selectbox",
                label,
                tuple(options),
                index,
                key,
            )
        )
        return self.selected_source_role

    def table(self, rows):
        self.calls.append(("table", rows))

    def button(self, label, *, key, type=None):
        self.calls.append(("button", label, key, type))
        return key in self.clicked_keys

    def rerun(self):
        self.rerun_count += 1


class FakeUploadedFile:
    def __init__(self, name, content):
        self.name = name
        self._content = content
        self.size = len(content)

    def getvalue(self):
        return self._content


class FakeIngestionService:
    def __init__(
        self,
        *,
        sources=(),
        issues=(),
        register_error=None,
    ):
        self.sources = tuple(sources)
        self.issues = tuple(issues)
        self.register_error = register_error
        self.register_calls = []
        self.inventory_calls = []

    def register_uploaded_source(
        self,
        project_id,
        *,
        original_filename,
        content,
        source_role,
    ):
        self.register_calls.append(
            (
                project_id,
                original_filename,
                content,
                source_role,
            )
        )
        if self.register_error is not None:
            raise self.register_error
        result = SimpleNamespace(
            project_id=project_id,
            source_id="SRC-000001",
            source_role=source_role,
            original_filename=original_filename,
            media_type="text/plain",
            size_bytes=len(content),
            sha256="a" * 64,
            registered_at="2026-07-27T12:00:00Z",
        )
        self.sources = (*self.sources, result)
        return result

    def list_registered_sources(self, project_id):
        self.inventory_calls.append(project_id)
        return SimpleNamespace(
            project_id=project_id,
            sources=self.sources,
            issues=self.issues,
        )


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
    ingestion_service = FakeIngestionService()

    render_project_bound_ingestion_entry(
        st,
        workspace=workspace,
        ingestion_service=ingestion_service,
        navigation=read_navigation_state(st.session_state),
    )

    assert workspace.calls == ["123456"]
    assert any(
        call[0] == "caption"
        and "Example Project · 123456" in call[1]
        for call in st.calls
    )
    assert st.session_state[SESSION_APP_VIEW] == APP_VIEW_INGESTION
    assert SESSION_PENDING_NAVIGATION in st.session_state
    assert st.rerun_count == 1

    state = apply_pending_app_view(st.session_state)

    assert state.active_view == APP_VIEW_DASHBOARD
    assert state.project_id == "123456"
    assert st.session_state[SESSION_PROJECT_ID] == "123456"


def test_source_registration_uses_selected_project_and_role():
    uploaded = FakeUploadedFile(
        "requirements.txt",
        b"The system shall preserve traceability.",
    )
    st = FakeStreamlit(
        clicked_keys={"turing_generator.register_source"},
        uploaded_file=uploaded,
        selected_source_role="context_only",
    )
    st.session_state[SESSION_APP_VIEW] = APP_VIEW_INGESTION
    st.session_state[SESSION_PROJECT_ID] = "123456"
    workspace = FakeWorkspace()
    ingestion_service = FakeIngestionService()

    render_project_bound_ingestion_entry(
        st,
        workspace=workspace,
        ingestion_service=ingestion_service,
        navigation=read_navigation_state(st.session_state),
    )

    assert ingestion_service.register_calls == [
        (
            "123456",
            "requirements.txt",
            b"The system shall preserve traceability.",
            "context_only",
        )
    ]
    assert (
        st.session_state[SESSION_SELECTED_ENTITY_ID]
        == "SRC-000001"
    )
    assert any(call[0] == "success" for call in st.calls)
    assert any(call[0] == "table" for call in st.calls)


def test_source_registration_uploader_accepts_pdf():
    st = FakeStreamlit()
    st.session_state[SESSION_APP_VIEW] = APP_VIEW_INGESTION
    st.session_state[SESSION_PROJECT_ID] = "123456"
    workspace = FakeWorkspace()
    ingestion_service = FakeIngestionService()

    render_project_bound_ingestion_entry(
        st,
        workspace=workspace,
        ingestion_service=ingestion_service,
        navigation=read_navigation_state(st.session_state),
    )

    uploader_calls = [
        call
        for call in st.calls
        if call[0] == "file_uploader"
    ]

    assert len(uploader_calls) == 1
    assert uploader_calls[0][2] == (
        "md",
        "txt",
        "json",
        "csv",
        "tsv",
        "pdf",
    )


def test_source_registration_does_not_rewrite_active_view_widget(
    monkeypatch,
):
    uploaded = FakeUploadedFile(
        "requirements.txt",
        b"The system shall preserve traceability.",
    )
    st = FakeStreamlit(
        clicked_keys={"turing_generator.register_source"},
        uploaded_file=uploaded,
    )
    st.session_state[SESSION_APP_VIEW] = APP_VIEW_INGESTION
    st.session_state[SESSION_PROJECT_ID] = "123456"
    ingestion_service = FakeIngestionService()

    def reject_navigation_rewrite(*args, **kwargs):
        raise AssertionError(
            "Source registration must not rewrite the active-view widget."
        )

    monkeypatch.setattr(
        "app.turing_generator_ui.queue_app_view",
        reject_navigation_rewrite,
    )

    render_project_source_registration(
        st,
        ingestion_service=ingestion_service,
        navigation=read_navigation_state(st.session_state),
    )

    assert st.session_state[SESSION_APP_VIEW] == APP_VIEW_INGESTION
    assert (
        st.session_state[SESSION_SELECTED_ENTITY_ID]
        == "SRC-000001"
    )


def test_duplicate_source_registration_surfaces_safe_message():
    uploaded = FakeUploadedFile("duplicate.txt", b"duplicate")
    st = FakeStreamlit(
        clicked_keys={"turing_generator.register_source"},
        uploaded_file=uploaded,
    )
    st.session_state[SESSION_APP_VIEW] = APP_VIEW_INGESTION
    st.session_state[SESSION_PROJECT_ID] = "123456"
    workspace = FakeWorkspace()
    ingestion_service = FakeIngestionService(
        register_error=DuplicateSourceContentError(
            "private path details"
        )
    )

    render_project_bound_ingestion_entry(
        st,
        workspace=workspace,
        ingestion_service=ingestion_service,
        navigation=read_navigation_state(st.session_state),
    )

    errors = [
        call[1]
        for call in st.calls
        if call[0] == "error"
    ]
    assert errors == [
        "This exact Source content is already registered "
        "in the selected Project."
    ]
    assert "private path details" not in errors[0]


def test_registered_source_inventory_contains_no_paths():
    source = SimpleNamespace(
        project_id="123456",
        source_id="SRC-000004",
        source_role="engineering_source",
        original_filename="system.json",
        media_type="application/json",
        size_bytes=128,
        sha256="b" * 64,
        registered_at="2026-07-27T12:00:00Z",
    )
    st = FakeStreamlit()
    st.session_state[SESSION_APP_VIEW] = APP_VIEW_INGESTION
    st.session_state[SESSION_PROJECT_ID] = "123456"
    workspace = FakeWorkspace()
    ingestion_service = FakeIngestionService(
        sources=(source,),
    )

    render_project_bound_ingestion_entry(
        st,
        workspace=workspace,
        ingestion_service=ingestion_service,
        navigation=read_navigation_state(st.session_state),
    )

    tables = [
        call[1]
        for call in st.calls
        if call[0] == "table"
    ]
    assert len(tables) == 1
    assert tables[0][0]["Source ID"] == "SRC-000004"
    assert "path" not in {
        key.lower()
        for key in tables[0][0]
    }
