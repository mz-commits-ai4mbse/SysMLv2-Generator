"""Tests for the constrained P2 Project Workspace bootstrap in the P7 app."""

from __future__ import annotations

from types import SimpleNamespace

import app.project_dashboard_ui as dashboard_ui
from app.project_dashboard_ui import (
    render_project_creation,
    render_project_dashboard_ui,
    render_project_selector,
    request_streamlit_rerun,
)
from modules.project_dashboard.types import DashboardProjectSelection
from modules.project_workspace.errors import ProjectWorkspaceError


class _Context:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False


class FakeStreamlit:
    def __init__(
        self,
        *,
        submitted=False,
        display_name="",
        description="",
        has_rerun=True,
        has_experimental_rerun=False,
    ):
        self.session_state = {}
        self.submitted = submitted
        self.display_name = display_name
        self.description = description
        self.calls = []
        self.rerun_count = 0
        self.experimental_rerun_count = 0
        if not has_rerun:
            self.rerun = None
        if has_experimental_rerun:
            self.experimental_rerun = self._experimental_rerun

    def header(self, text):
        self.calls.append(("header", text))

    def subheader(self, text):
        self.calls.append(("subheader", text))

    def caption(self, text):
        self.calls.append(("caption", text))

    def markdown(self, text, **kwargs):
        self.calls.append(("markdown", text, kwargs))

    def info(self, text):
        self.calls.append(("info", text))

    def error(self, text):
        self.calls.append(("error", text))

    def success(self, text):
        self.calls.append(("success", text))

    def expander(self, label, *, expanded=False):
        self.calls.append(("expander", label, expanded))
        return _Context()

    def form(self, key, *, clear_on_submit=False):
        self.calls.append(("form", key, clear_on_submit))
        return _Context()

    def text_input(self, label, **kwargs):
        self.calls.append(("text_input", label, kwargs))
        return self.display_name

    def text_area(self, label, **kwargs):
        self.calls.append(("text_area", label, kwargs))
        return self.description

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
        if key in self.session_state:
            return self.session_state[key]
        selected = options[index]
        self.session_state[key] = selected
        return selected

    def form_submit_button(self, label, **kwargs):
        self.calls.append(("form_submit_button", label, kwargs))
        return self.submitted

    def rerun(self):
        self.rerun_count += 1

    def _experimental_rerun(self):
        self.experimental_rerun_count += 1


class FakeWorkspace:
    def __init__(self, *, error=None):
        self.error = error
        self.calls = []

    def create_project(self, display_name, description=""):
        self.calls.append((display_name, description))
        if self.error is not None:
            raise self.error
        return SimpleNamespace(
            project_id="654321",
            display_name=display_name,
        )


class EmptyDashboardService:
    def list_projects(self):
        return DashboardProjectSelection(projects=(), issues=())


class ExistingDashboardService:
    def list_projects(self):
        return DashboardProjectSelection(
            projects=(object(),),
            issues=(),
        )


def _call_names(st):
    return tuple(call[0] for call in st.calls)


def test_project_creation_form_does_not_write_before_submission():
    st = FakeStreamlit(submitted=False)
    workspace = FakeWorkspace()

    result = render_project_creation(st, workspace)

    assert result is None
    assert workspace.calls == []
    assert st.rerun_count == 0
    assert "form" in _call_names(st)


def test_additional_project_creation_is_collapsed_and_available():
    st = FakeStreamlit(submitted=False)
    workspace = FakeWorkspace()

    result = render_project_creation(
        st,
        workspace,
        first_project=False,
    )

    assert result is None
    assert workspace.calls == []
    assert ("expander", "Create new project", False) in st.calls
    assert "form_submit_button" in _call_names(st)


def test_project_creation_normalizes_input_and_selects_created_project():
    st = FakeStreamlit(
        submitted=True,
        display_name="  Apollo Migration  ",
        description="  Initial engineering workspace.  ",
    )
    workspace = FakeWorkspace()

    result = render_project_creation(st, workspace)

    assert result == "654321"
    assert workspace.calls == [
        ("Apollo Migration", "Initial engineering workspace.")
    ]
    assert st.session_state["project_dashboard.project_id"] == "654321"
    assert (
        st.session_state["project_dashboard.pending_project_id"]
        == "654321"
    )
    assert st.session_state["project_dashboard.active_view"] == "overview"
    assert st.rerun_count == 1
    assert any(call[0] == "success" for call in st.calls)


def test_project_selector_opens_newly_created_project_after_rerun():
    st = FakeStreamlit()
    st.session_state["project_dashboard.project_id"] = "123456"
    st.session_state["project_dashboard.project_selector"] = "123456"
    st.session_state["project_dashboard.pending_project_id"] = "654321"

    selection = DashboardProjectSelection(
        projects=(
            SimpleNamespace(
                project_id="123456",
                label="Existing Project · 123456",
            ),
            SimpleNamespace(
                project_id="654321",
                label="New Project · 654321",
            ),
        ),
        issues=(),
    )

    selected = render_project_selector(st, selection)

    assert selected == "654321"
    assert st.session_state["project_dashboard.project_id"] == "654321"
    assert st.session_state["project_dashboard.project_selector"] == "654321"
    assert "project_dashboard.pending_project_id" not in st.session_state


def test_project_creation_requires_nonempty_display_name():
    st = FakeStreamlit(
        submitted=True,
        display_name="   ",
        description="ignored",
    )
    workspace = FakeWorkspace()

    result = render_project_creation(st, workspace)

    assert result is None
    assert workspace.calls == []
    assert st.rerun_count == 0
    assert ("error", "Project name is required.") in st.calls


def test_project_creation_rejects_nonstring_display_name():
    st = FakeStreamlit(submitted=True, display_name=None)
    workspace = FakeWorkspace()

    result = render_project_creation(st, workspace)

    assert result is None
    assert workspace.calls == []
    assert ("error", "Project name is required.") in st.calls


def test_project_creation_surfaces_expected_workspace_error():
    st = FakeStreamlit(submitted=True, display_name="Duplicate")
    workspace = FakeWorkspace(
        error=ProjectWorkspaceError("Display name already exists.")
    )

    result = render_project_creation(st, workspace)

    assert result is None
    assert workspace.calls == [("Duplicate", "")]
    assert st.rerun_count == 0
    assert any(
        call[0] == "error" and "Display name already exists" in call[1]
        for call in st.calls
    )


def test_project_creation_hides_unexpected_exception_details():
    st = FakeStreamlit(submitted=True, display_name="Example")
    workspace = FakeWorkspace(error=RuntimeError("secret detail"))

    result = render_project_creation(st, workspace)

    assert result is None
    errors = [call[1] for call in st.calls if call[0] == "error"]
    assert errors == [
        "Project creation failed unexpectedly. No partial project state "
        "was accepted."
    ]
    assert "secret detail" not in errors[0]


def test_request_streamlit_rerun_prefers_current_api():
    st = FakeStreamlit(
        has_rerun=True,
        has_experimental_rerun=True,
    )

    request_streamlit_rerun(st)

    assert st.rerun_count == 1
    assert st.experimental_rerun_count == 0


def test_request_streamlit_rerun_supports_legacy_api():
    st = FakeStreamlit(
        has_rerun=False,
        has_experimental_rerun=True,
    )

    request_streamlit_rerun(st)

    assert st.experimental_rerun_count == 1


def test_request_streamlit_rerun_is_safe_without_rerun_api():
    st = FakeStreamlit(
        has_rerun=False,
        has_experimental_rerun=False,
    )

    request_streamlit_rerun(st)

    assert st.rerun_count == 0
    assert st.experimental_rerun_count == 0


def test_empty_dashboard_renders_bootstrap_and_creates_first_project(tmp_path):
    st = FakeStreamlit(
        submitted=True,
        display_name="First Project",
        description="Bootstrap",
    )
    workspace = FakeWorkspace()

    render_project_dashboard_ui(
        tmp_path,
        service=EmptyDashboardService(),
        viewer=object(),
        streamlit_module=st,
        project_workspace=workspace,
    )

    assert workspace.calls == [("First Project", "Bootstrap")]
    assert st.session_state["project_dashboard.project_id"] == "654321"
    assert st.rerun_count == 1
    assert any(
        call[0] == "info" and "Create the first project" in call[1]
        for call in st.calls
    )


def test_existing_dashboard_always_invokes_additional_project_creation(
    tmp_path,
    monkeypatch,
):
    st = FakeStreamlit(submitted=False)
    workspace = FakeWorkspace()
    creation_modes = []

    monkeypatch.setattr(
        dashboard_ui,
        "render_project_selector",
        lambda streamlit, selection: "123456",
    )
    monkeypatch.setattr(
        dashboard_ui,
        "render_project_creation",
        lambda streamlit, current_workspace, *, first_project=True: (
            creation_modes.append(first_project)
        ),
    )
    monkeypatch.setattr(
        dashboard_ui,
        "render_view_selector",
        lambda streamlit: "unsupported",
    )
    monkeypatch.setattr(
        dashboard_ui,
        "render_document_viewer",
        lambda *args, **kwargs: None,
    )

    render_project_dashboard_ui(
        tmp_path,
        service=ExistingDashboardService(),
        viewer=object(),
        streamlit_module=st,
        project_workspace=workspace,
    )

    assert creation_modes == [False]


def test_empty_dashboard_does_not_create_without_explicit_submission(tmp_path):
    st = FakeStreamlit(submitted=False)
    workspace = FakeWorkspace()

    render_project_dashboard_ui(
        tmp_path,
        service=EmptyDashboardService(),
        viewer=object(),
        streamlit_module=st,
        project_workspace=workspace,
    )

    assert workspace.calls == []
    assert st.rerun_count == 0
    assert "form_submit_button" in _call_names(st)
