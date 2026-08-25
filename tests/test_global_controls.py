from __future__ import annotations

from types import SimpleNamespace

from app.global_controls import (
    SESSION_GLOBAL_CONTROLS_ACTIVE,
    SESSION_GLOBAL_PENDING_PROJECT_ID,
    SESSION_GLOBAL_PROJECT_SELECTOR,
    render_global_controls,
)
from app.presentation_preferences import (
    SESSION_SHOW_TECHNICAL_DETAILS,
)
from app.turing_generator_navigation import (
    SESSION_PROJECT_ID,
    SESSION_SELECTED_ENTITY_ID,
)


class Context:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class FakeStreamlit:
    def __init__(self, *, selected_project=None, technical=False):
        self.session_state = {}
        self.selected_project = selected_project
        self.technical = technical
        self.calls = []

    def columns(self, spec):
        return tuple(Context() for _ in range(len(spec)))

    def toggle(self, label, *, key, help=None):
        self.calls.append(("toggle", label, key))
        self.session_state[key] = self.technical
        return self.technical

    def button(self, label, *, key, type=None):
        self.calls.append(
            ("button", label, key, type)
        )
        return bool(
            getattr(self, "open_create", False)
            and key == "turing_generator.open_create_project"
        )

    def form(self, key, *, clear_on_submit=False):
        self.calls.append(
            ("form", key, clear_on_submit)
        )
        return Context()

    def text_input(self, label, **kwargs):
        self.calls.append(
            ("text_input", label)
        )
        return getattr(
            self,
            "project_name",
            "",
        )

    def text_area(self, label, **kwargs):
        self.calls.append(
            ("text_area", label)
        )
        return getattr(
            self,
            "description",
            "",
        )

    def form_submit_button(self, label, **kwargs):
        self.calls.append(
            ("form_submit_button", label)
        )
        return bool(
            getattr(self, "submit_create", False)
        )

    def error(self, text):
        self.calls.append(
            ("error", text)
        )

    def success(self, text):
        self.calls.append(
            ("success", text)
        )

    def rerun(self):
        self.rerun_count = (
            getattr(self, "rerun_count", 0) + 1
        )

    def selectbox(
        self,
        label,
        *,
        options,
        index,
        format_func,
        key,
        on_change=None,
    ):
        self.calls.append(
            (
                "selectbox",
                label,
                tuple(options),
                index,
                key,
                tuple(format_func(item) for item in options),
            )
        )
        selected = (
            self.selected_project
            if (
                self.selected_project is not None
                and self.selected_project in options
            )
            else options[index]
        )
        previous = self.session_state.get(key)
        self.session_state[key] = selected

        if selected != previous and on_change is not None:
            on_change()

        return selected


class Workspace:
    def scan_projects(self):
        return SimpleNamespace(
            valid_projects=(
                SimpleNamespace(
                    project_id="111111",
                    display_name="Alpha",
                ),
                SimpleNamespace(
                    project_id="222222",
                    display_name="Beta",
                ),
            ),
            workspace_issues=(),
        )


def test_global_controls_expose_project_and_technical_toggle():
    st = FakeStreamlit()

    render_global_controls(
        st,
        workspace=Workspace(),
    )

    assert st.session_state[
        SESSION_GLOBAL_CONTROLS_ACTIVE
    ] is True
    assert any(call[0] == "toggle" for call in st.calls)
    assert any(
        call[0] == "selectbox"
        and call[1] == "Project"
        for call in st.calls
    )


def test_project_is_not_implicitly_selected():
    st = FakeStreamlit()

    render_global_controls(
        st,
        workspace=Workspace(),
    )

    assert SESSION_PROJECT_ID not in st.session_state


def test_explicit_project_change_updates_global_context():
    st = FakeStreamlit(
        selected_project="222222",
    )

    render_global_controls(
        st,
        workspace=Workspace(),
    )

    assert st.session_state[SESSION_PROJECT_ID] == "222222"
    assert (
        st.session_state[SESSION_GLOBAL_PROJECT_SELECTOR]
        == "222222"
    )


def test_project_change_clears_stale_entity_navigation():
    st = FakeStreamlit(
        selected_project="222222",
    )
    st.session_state[SESSION_PROJECT_ID] = "111111"
    st.session_state[
        SESSION_SELECTED_ENTITY_ID
    ] = "RVD-000001"

    render_global_controls(
        st,
        workspace=Workspace(),
    )

    assert st.session_state[SESSION_PROJECT_ID] == "222222"
    assert (
        SESSION_SELECTED_ENTITY_ID
        not in st.session_state
    )


def test_project_creation_is_available_in_global_shell():
    st = FakeStreamlit()

    render_global_controls(
        st,
        workspace=Workspace(),
    )

    assert any(
        call[0] == "button"
        and call[1] == "＋ Create new project"
        for call in st.calls
    )


def test_global_project_creation_activates_created_project_on_rerun():
    class CreationWorkspace:
        def __init__(self):
            self.projects = [
                SimpleNamespace(
                    project_id="111111",
                    display_name="Alpha",
                ),
            ]
            self.created = []

        def scan_projects(self):
            return SimpleNamespace(
                valid_projects=tuple(self.projects),
                workspace_issues=(),
            )

        def create_project(
            self,
            display_name,
            description="",
        ):
            self.created.append(
                (display_name, description)
            )

            manifest = SimpleNamespace(
                project_id="333333",
                display_name=display_name,
            )
            self.projects.append(manifest)
            return manifest

    st = FakeStreamlit()
    st.open_create = True
    st.submit_create = True
    st.project_name = "  New Architecture  "
    st.description = "  System model.  "

    workspace = CreationWorkspace()

    render_global_controls(
        st,
        workspace=workspace,
    )

    assert workspace.created == [
        ("New Architecture", "System model.")
    ]
    assert (
        st.session_state[SESSION_PROJECT_ID]
        == "333333"
    )
    assert (
        st.session_state[
            SESSION_GLOBAL_PENDING_PROJECT_ID
        ]
        == "333333"
    )
    assert st.rerun_count == 1

    # Simulate the Streamlit rerun after successful creation.
    st.open_create = False
    st.submit_create = False

    render_global_controls(
        st,
        workspace=workspace,
    )

    assert (
        st.session_state[SESSION_PROJECT_ID]
        == "333333"
    )
    assert (
        st.session_state[
            SESSION_GLOBAL_PROJECT_SELECTOR
        ]
        == "333333"
    )
    assert (
        SESSION_GLOBAL_PENDING_PROJECT_ID
        not in st.session_state
    )


def test_technical_toggle_is_global_ui_state_only():
    st = FakeStreamlit(
        selected_project="111111",
        technical=True,
    )

    render_global_controls(
        st,
        workspace=Workspace(),
    )

    assert st.session_state[
        SESSION_SHOW_TECHNICAL_DETAILS
    ] is True
    assert st.session_state[SESSION_PROJECT_ID] == "111111"


def test_technical_toggle_preserves_project_selector_identity_and_context():
    st = FakeStreamlit(
        selected_project="111111",
        technical=False,
    )

    render_global_controls(
        st,
        workspace=Workspace(),
    )

    first_selectbox = [
        call for call in st.calls
        if call[0] == "selectbox" and call[1] == "Project"
    ][-1]
    first_labels = first_selectbox[5]

    assert st.session_state[SESSION_PROJECT_ID] == "111111"

    # Simulate the Streamlit rerun caused only by presentation-depth change.
    st.technical = True
    st.selected_project = None

    render_global_controls(
        st,
        workspace=Workspace(),
    )

    second_selectbox = [
        call for call in st.calls
        if call[0] == "selectbox" and call[1] == "Project"
    ][-1]
    second_labels = second_selectbox[5]

    assert st.session_state[
        SESSION_SHOW_TECHNICAL_DETAILS
    ] is True
    assert st.session_state[SESSION_PROJECT_ID] == "111111"
    assert (
        st.session_state[SESSION_GLOBAL_PROJECT_SELECTOR]
        == "111111"
    )
    assert first_labels == second_labels
