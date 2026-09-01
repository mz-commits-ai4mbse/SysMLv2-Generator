
from __future__ import annotations

from contextlib import nullcontext
from types import SimpleNamespace

from app.guided_workflow_ui import render_guided_workflow_ui
from app.turing_generator_navigation import (
    APP_VIEW_REVIEW,
    SESSION_PENDING_NAVIGATION,
    SESSION_PROJECT_ID,
)
from modules.guided_workflow import (
    build_guided_workflow_view,
    create_stage_view,
)


class Column:
    def __init__(self, parent):
        self.parent = parent

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def metric(self, label, value):
        self.parent.calls.append(
            ("metric", label, value)
        )


class FakeStreamlit:
    def __init__(self, clicked=()):
        self.session_state = {}
        self.clicked = set(clicked)
        self.calls = []
        self.rerun_count = 0

    def header(self, value):
        self.calls.append(("header", value))

    def subheader(self, value):
        self.calls.append(("subheader", value))

    def caption(self, value):
        self.calls.append(("caption", value))

    def info(self, value):
        self.calls.append(("info", value))

    def checkbox(self, label, *, key, help=None):
        self.calls.append(
            ("checkbox", label, key, help)
        )
        return bool(
            self.session_state.get(key, False)
        )

    def error(self, value):
        self.calls.append(("error", value))

    def success(self, value):
        self.calls.append(("success", value))

    def write(self, value):
        self.calls.append(("write", value))

    def markdown(self, value, unsafe_allow_html=False):
        self.calls.append(
            ("markdown", value, unsafe_allow_html)
        )

    def button(self, label, *, key, type=None):
        self.calls.append(
            ("button", label, key, type)
        )
        return key in self.clicked

    def columns(self, count):
        if isinstance(count, int):
            number = count
        else:
            number = len(count)
        return tuple(
            Column(self)
            for _ in range(number)
        )

    def container(self, *, border=False):
        return nullcontext()

    def expander(self, label):
        self.calls.append(("expander", label))
        return nullcontext()

    def rerun(self):
        self.rerun_count += 1


class Workspace:
    def load_project(self, project_id):
        return SimpleNamespace(
            project_id=project_id,
            display_name="Example System",
        )


class Service:
    def __init__(self, view):
        self.view = view

    def load_view(self, project_id):
        return self.view


def _view(*, human_decisions=0):
    stages = (
        create_stage_view(
            stage_id="project_sources",
            presentation_status="complete",
            semantic="positive",
            summary="2 sources provided.",
            action_label="Manage sources",
        ),
        create_stage_view(
            stage_id="processing",
            presentation_status="complete",
            semantic="positive",
            summary="2 awaiting review",
            action_label="Inspect processing results",
        ),
        create_stage_view(
            stage_id="human_review",
            presentation_status=(
                "action_required"
                if human_decisions
                else "complete"
            ),
            semantic=(
                "attention"
                if human_decisions
                else "positive"
            ),
            summary="Engineering review",
            decision_count=human_decisions,
            action_label=(
                "Resolve Human decisions"
                if human_decisions
                else None
            ),
            target_entity_id=(
                "RVD-000001"
                if human_decisions
                else None
            ),
        ),
        create_stage_view(
            stage_id="project_reconciliation",
            presentation_status="not_started",
            semantic="neutral",
            summary="No project reconciliation yet.",
        ),
        create_stage_view(
            stage_id="model_proposal",
            presentation_status="not_started",
            semantic="neutral",
            summary="No proposal yet.",
        ),
        create_stage_view(
            stage_id="final_model_review",
            presentation_status="not_started",
            semantic="neutral",
            summary="No final review yet.",
        ),
        create_stage_view(
            stage_id="published_output",
            presentation_status="not_started",
            semantic="neutral",
            summary="No published output yet.",
        ),
    )
    return build_guided_workflow_view(
        project_id="123456",
        stages=stages,
        confirmed_result_count=4,
    )


def test_without_project_engineering_workspace_requests_global_selection():
    st = FakeStreamlit()

    render_guided_workflow_ui(
        ".",
        streamlit_module=st,
        project_workspace=Workspace(),
        workflow_service=Service(_view()),
    )

    assert any(
        call[0] == "info"
        and "application header" in call[1]
        for call in st.calls
    )
    assert st.rerun_count == 0


def test_engineering_workspace_renders_your_work_and_seven_stages():
    st = FakeStreamlit()
    st.session_state[SESSION_PROJECT_ID] = "123456"

    render_guided_workflow_ui(
        ".",
        streamlit_module=st,
        project_workspace=Workspace(),
        workflow_service=Service(
            _view(human_decisions=2)
        ),
    )

    metrics = [
        call
        for call in st.calls
        if call[0] == "metric"
    ]
    assert ("metric", "Decisions required", 2) in metrics

    stage_headings = [
        call
        for call in st.calls
        if call[0] == "markdown"
        and call[1].startswith("### ")
    ]
    assert len(stage_headings) == 7


def test_focused_view_hides_technical_project_identity():
    st = FakeStreamlit()
    st.session_state[SESSION_PROJECT_ID] = "123456"

    render_guided_workflow_ui(
        ".",
        streamlit_module=st,
        project_workspace=Workspace(),
        workflow_service=Service(_view()),
    )

    assert not any(
        call[0] == "caption"
        and call[1] == "Project 123456"
        for call in st.calls
    )

    assert not any(
        call[0] == "expander"
        and call[1] == "Technical details"
        for call in st.calls
    )


def test_technical_view_exposes_project_and_stage_details():
    from app.presentation_preferences import (
        SESSION_SHOW_TECHNICAL_DETAILS,
    )

    st = FakeStreamlit()
    st.session_state[SESSION_PROJECT_ID] = "123456"
    st.session_state[
        SESSION_SHOW_TECHNICAL_DETAILS
    ] = True

    render_guided_workflow_ui(
        ".",
        streamlit_module=st,
        project_workspace=Workspace(),
        workflow_service=Service(_view()),
    )

    assert (
        "caption",
        "Project 123456",
    ) in st.calls

    technical_expanders = [
        call
        for call in st.calls
        if call[0] == "expander"
        and call[1] == "Technical details"
    ]

    assert len(technical_expanders) == 7


def test_presentation_depth_does_not_change_workflow_projection():
    from app.presentation_preferences import (
        SESSION_SHOW_TECHNICAL_DETAILS,
    )

    focused = FakeStreamlit()
    focused.session_state[SESSION_PROJECT_ID] = "123456"

    technical = FakeStreamlit()
    technical.session_state[SESSION_PROJECT_ID] = "123456"
    technical.session_state[
        SESSION_SHOW_TECHNICAL_DETAILS
    ] = True

    view = _view(human_decisions=2)

    render_guided_workflow_ui(
        ".",
        streamlit_module=focused,
        project_workspace=Workspace(),
        workflow_service=Service(view),
    )

    render_guided_workflow_ui(
        ".",
        streamlit_module=technical,
        project_workspace=Workspace(),
        workflow_service=Service(view),
    )

    focused_metrics = [
        call
        for call in focused.calls
        if call[0] == "metric"
    ]

    technical_metrics = [
        call
        for call in technical.calls
        if call[0] == "metric"
    ]

    assert focused_metrics == technical_metrics


def test_human_review_stage_routes_exact_review_document():
    st = FakeStreamlit(
        clicked={"guided_workflow.stage.human_review"}
    )
    st.session_state[SESSION_PROJECT_ID] = "123456"

    render_guided_workflow_ui(
        ".",
        streamlit_module=st,
        project_workspace=Workspace(),
        workflow_service=Service(
            _view(human_decisions=2)
        ),
    )

    payload = st.session_state[
        SESSION_PENDING_NAVIGATION
    ]
    assert payload["active_view"] == APP_VIEW_REVIEW
    assert payload["selected_entity_id"] == "RVD-000001"
    assert st.rerun_count == 1
