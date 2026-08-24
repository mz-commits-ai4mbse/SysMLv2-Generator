"""Tests for G6.2 Human Review navigation and queue UI."""

from __future__ import annotations

from types import SimpleNamespace

from modules.review_workspace.types import ReviewItemContent

from app.human_review_approval_ui import (
    render_human_review_approval_ui,
)
from app.presentation_preferences import SESSION_SHOW_TECHNICAL_DETAILS
from app.turing_generator_navigation import (
    APP_VIEW_DASHBOARD,
    APP_VIEW_REVIEW,
    APP_VIEWS,
    SESSION_APP_VIEW,
    SESSION_PROJECT_ID,
    SESSION_SELECTED_ENTITY_ID,
    apply_pending_app_view,
    normalize_app_view,
    read_navigation_state,
    select_app_view,
)
from app.turing_generator_ui import render_turing_generator_ui


class FakeStreamlit:
    def __init__(
        self,
        *,
        clicked_keys=(),
        reviewer_identity="Reviewer A",
    ):
        self.session_state = {}
        self.clicked_keys = set(clicked_keys)
        self.reviewer_identity = reviewer_identity
        self.calls = []
        self.rerun_count = 0

    def columns(self, spec):
        class Context:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

        count = spec if isinstance(spec, int) else len(spec)
        return tuple(Context() for _ in range(count))

    def toggle(self, label, *, key, help=None):
        self.calls.append(("toggle", label, key, help))
        return bool(self.session_state.get(key, False))

    def radio(
        self,
        label,
        *,
        options,
        index=0,
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
        value = options[index]
        self.session_state[key] = value
        return value

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

    def table(self, rows):
        self.calls.append(("table", rows))

    def markdown(self, text):
        self.calls.append(("markdown", text))

    def text_area(
        self,
        label,
        *,
        value,
        key,
    ):
        self.calls.append(("text_area", label, key))
        return value

    def selectbox(
        self,
        label,
        *,
        options,
        index,
        key,
        format_func=None,
        on_change=None,
    ):
        self.calls.append(
            ("selectbox", label, tuple(options), index, key)
        )
        selected = self.session_state.get(
            key,
            options[index],
        )
        self.session_state[key] = selected
        return selected

    def multiselect(
        self,
        label,
        *,
        options,
        default,
        key,
    ):
        self.calls.append(
            ("multiselect", label, tuple(options), key)
        )
        return tuple(default)

    def text_input(
        self,
        label,
        *,
        value,
        key,
        help=None,
    ):
        self.calls.append(
            ("text_input", label, key, help)
        )
        return self.reviewer_identity

    def checkbox(
        self,
        label,
        *,
        value,
        key,
    ):
        self.calls.append(("checkbox", label, key))
        return value

    def button(self, label, *, key, type=None):
        self.calls.append(("button", label, key, type))
        return key in self.clicked_keys

    def rerun(self):
        self.rerun_count += 1


class FakeWorkspace:
    def __init__(self, *, error=None):
        self.error = error
        self.calls = []

    def load_project(self, project_id):
        self.calls.append(project_id)
        if self.error is not None:
            raise self.error
        return SimpleNamespace(
            project_id=project_id,
            display_name="Example Project",
        )

    def scan_projects(self):
        return SimpleNamespace(
            valid_projects=(
                SimpleNamespace(
                    project_id="123456",
                    display_name="Example Project",
                ),
            ),
            workspace_issues=(),
        )


def _queue_item(*, with_workspace=False):
    return SimpleNamespace(
        source_id="SRC-000001",
        original_filename="requirements.md",
        processing_run_id="PRN-000001",
        run_state="awaiting_review",
        review_document_id=(
            "RVD-000001" if with_workspace else None
        ),
        review_document_version_id=(
            "RVV-000001" if with_workspace else None
        ),
        review_item_count=(3 if with_workspace else 0),
        review_outcome_counts=(
            (
                ("open", 1),
                ("deferred", 1),
                ("accepted", 1),
            )
            if with_workspace
            else ()
        ),
        workflow_status=(
            "draft_review"
            if with_workspace
            else "awaiting_workspace"
        ),
        active_approved_input_ids=(),
        issue_codes=(),
    )


def _review_fact():
    return SimpleNamespace(
        review_item_id="RIT-000001",
        item_content_fingerprint="a" * 64,
        consensus_states=("not_available",),
        agent_disagreement_state="not_available",
        human_modification_state="unmodified",
        evidence_sufficiency_state="not_assessed",
        relationship_validation_status="not_applicable",
    )


def _workspace_view():
    item = SimpleNamespace(
        review_item_id="RIT-000001",
        review_item_kind="element",
        stable_subject_key="requirement:example",
        section="elements",
        lineage_operation="original",
        effective_review_outcome="open",
        item_content_fingerprint="a" * 64,
        proposal_references=(),
        source_evidence_references=(),
        consensus_evidence_references=(),
        dimension_selections=(),
        current_content=ReviewItemContent(
            title="Example",
            primary_text="Example statement.",
            description=None,
            information_type="requirement",
            modality=None,
            epistemic_status=None,
            human_rationale=None,
            human_confidence=None,
            relationship_representation=None,
        ),
    )
    return SimpleNamespace(
        document=SimpleNamespace(
            review_document_id="RVD-000001",
        ),
        version=SimpleNamespace(
            version_number=1,
            review_document_version_id="RVV-000001",
            version_state="draft",
        ),
        revision=SimpleNamespace(
            review_revision_id="RVR-000001",
            review_items=(item,),
        ),
        scoped_actions=(),
        can_finalize=False,
        can_promote=False,
        active_approved_input_ids=(),
        has_blocking_issues=False,
    )


class FakeWorkflowService:
    def __init__(self, *, items=()):
        self.items = tuple(items)
        self.project_calls = []
        self.open_calls = []
        self.workspace_calls = []

    def project_view(self, project_id):
        self.project_calls.append(project_id)
        return SimpleNamespace(
            items=self.items,
            issues=(),
        )

    def open_or_create_review(
        self,
        project_id,
        processing_run_id,
        *,
        opened_by,
    ):
        self.open_calls.append(
            (project_id, processing_run_id, opened_by)
        )
        return SimpleNamespace(
            created=True,
            review_document_id="RVD-000001",
        )

    def workspace_view(
        self,
        project_id,
        review_document_id,
    ):
        self.workspace_calls.append(
            (project_id, review_document_id)
        )
        return _workspace_view()

    def review_filter_facts(self, *args):
        return (_review_fact(),)

    def proposal_details(
        self,
        project_id,
        review_document_id,
        review_document_version_id,
        review_item_id,
    ):
        return ()

    def finalization_preview(
        self,
        project_id,
        review_document_id,
        review_document_version_id,
    ):
        return SimpleNamespace(
            assessment=SimpleNamespace(
                review_revision_id="RVR-000001",
                blocking_issue_codes=(
                    "review_item_open:RIT-000001",
                ),
                item_snapshots=(),
                validation_fingerprint="f" * 64,
            ),
            eligible_for_confirmation=False,
            latest_exact_decision_id=None,
            latest_exact_decision=None,
            exact_confirmation_decision_id=None,
            has_exact_confirmation=False,
            can_finalize=False,
        )


def test_review_remains_stable_top_level_application_view():
    assert APP_VIEWS == (
        "workflow",
        APP_VIEW_DASHBOARD,
        "ingestion",
        APP_VIEW_REVIEW,
        "model_proposal",
        "final_review",
        "published_output",
    )
    assert normalize_app_view(APP_VIEW_REVIEW) == APP_VIEW_REVIEW

    state = select_app_view(
        {},
        active_view=APP_VIEW_REVIEW,
        project_id="123456",
        return_view="attention",
    )

    assert state.active_view == APP_VIEW_REVIEW
    assert state.project_id == "123456"


def test_common_shell_routes_review_without_entering_ingestion(tmp_path):
    st = FakeStreamlit()
    st.session_state[SESSION_APP_VIEW] = APP_VIEW_REVIEW
    st.session_state[SESSION_PROJECT_ID] = "123456"
    workspace = FakeWorkspace()
    review_calls = []

    def review_renderer(root, **kwargs):
        review_calls.append((root, kwargs))

    render_turing_generator_ui(
        tmp_path,
        streamlit_module=st,
        project_workspace=workspace,
        ingestion_service=SimpleNamespace(),
        dashboard_renderer=lambda *args, **kwargs: None,
        review_renderer=review_renderer,
    )

    assert len(review_calls) == 1
    root, kwargs = review_calls[0]
    assert root == tmp_path
    assert kwargs["streamlit_module"] is st
    assert kwargs["project_workspace"] is workspace


def test_review_ui_fails_closed_without_selected_project(tmp_path):
    st = FakeStreamlit()
    workflow = FakeWorkflowService()
    workspace = FakeWorkspace()

    render_human_review_approval_ui(
        tmp_path,
        streamlit_module=st,
        project_workspace=workspace,
        workflow_service=workflow,
    )

    assert workflow.project_calls == []
    assert workspace.calls == []
    assert any(
        call[0] == "error"
        and "No valid Project" in call[1]
        for call in st.calls
    )


def test_review_queue_creates_initial_workspace_with_reviewer_identity(
    tmp_path,
):
    st = FakeStreamlit(
        clicked_keys={
            "human_review_approval.create.PRN-000001"
        },
        reviewer_identity="Reviewer A",
    )
    st.session_state[SESSION_APP_VIEW] = APP_VIEW_REVIEW
    st.session_state[SESSION_PROJECT_ID] = "123456"
    workspace = FakeWorkspace()
    workflow = FakeWorkflowService(
        items=(_queue_item(with_workspace=False),)
    )

    render_human_review_approval_ui(
        tmp_path,
        streamlit_module=st,
        project_workspace=workspace,
        workflow_service=workflow,
    )

    assert workflow.open_calls == [
        (
            "123456",
            "PRN-000001",
            "Reviewer A",
        )
    ]
    assert (
        st.session_state[SESSION_SELECTED_ENTITY_ID]
        == "RVD-000001"
    )
    assert st.rerun_count == 1
    assert any(
        call[0] == "success"
        and "Human Review started" in call[1]
        for call in st.calls
    )


def test_review_queue_does_not_create_without_reviewer_identity(
    tmp_path,
):
    st = FakeStreamlit(
        clicked_keys={
            "human_review_approval.create.PRN-000001"
        },
        reviewer_identity="   ",
    )
    st.session_state[SESSION_APP_VIEW] = APP_VIEW_REVIEW
    st.session_state[SESSION_PROJECT_ID] = "123456"
    workflow = FakeWorkflowService(
        items=(_queue_item(with_workspace=False),)
    )

    render_human_review_approval_ui(
        tmp_path,
        streamlit_module=st,
        project_workspace=FakeWorkspace(),
        workflow_service=workflow,
    )

    assert workflow.open_calls == []
    assert any(
        call[0] == "error"
        and "Reviewer identity is required" in call[1]
        for call in st.calls
    )


def test_existing_review_can_be_selected_without_creation(tmp_path):
    st = FakeStreamlit(
        clicked_keys={
            "human_review_approval.open.RVD-000001"
        }
    )
    st.session_state[SESSION_APP_VIEW] = APP_VIEW_REVIEW
    st.session_state[SESSION_PROJECT_ID] = "123456"
    workflow = FakeWorkflowService(
        items=(_queue_item(with_workspace=True),)
    )

    render_human_review_approval_ui(
        tmp_path,
        streamlit_module=st,
        project_workspace=FakeWorkspace(),
        workflow_service=workflow,
    )

    assert workflow.open_calls == []
    assert (
        st.session_state[SESSION_SELECTED_ENTITY_ID]
        == "RVD-000001"
    )
    assert workflow.workspace_calls == [
        ("123456", "RVD-000001")
    ]



def test_completed_review_queue_uses_valid_secondary_button_type(tmp_path):
    st = FakeStreamlit()
    st.session_state[SESSION_APP_VIEW] = APP_VIEW_REVIEW
    st.session_state[SESSION_PROJECT_ID] = "123456"

    item = _queue_item(with_workspace=True)
    item.review_outcome_counts = (
        ("accepted_with_modification", 3),
    )
    workflow = FakeWorkflowService(items=(item,))

    render_human_review_approval_ui(
        tmp_path,
        streamlit_module=st,
        project_workspace=FakeWorkspace(),
        workflow_service=workflow,
    )

    open_buttons = [
        call
        for call in st.calls
        if call[0] == "button"
        and call[1] == "Open review · requirements.md"
    ]
    assert len(open_buttons) == 1
    assert open_buttons[0][3] == "secondary"

def test_review_return_control_preserves_project_and_dashboard_view(
    tmp_path,
):
    st = FakeStreamlit(
        clicked_keys={
            "human_review_approval.return_to_dashboard"
        }
    )
    st.session_state[SESSION_APP_VIEW] = APP_VIEW_REVIEW
    st.session_state[SESSION_PROJECT_ID] = "123456"
    st.session_state[
        "turing_generator.return_view"
    ] = "attention"

    render_human_review_approval_ui(
        tmp_path,
        streamlit_module=st,
        project_workspace=FakeWorkspace(),
        workflow_service=FakeWorkflowService(),
    )

    state = apply_pending_app_view(st.session_state)

    assert state.active_view == APP_VIEW_DASHBOARD
    assert state.project_id == "123456"
    assert state.return_view == "attention"

def test_focused_review_queue_is_filename_and_work_first(tmp_path):
    st = FakeStreamlit()
    st.session_state[SESSION_APP_VIEW] = APP_VIEW_REVIEW
    st.session_state[SESSION_PROJECT_ID] = "123456"
    workflow = FakeWorkflowService(
        items=(_queue_item(with_workspace=True),)
    )

    render_human_review_approval_ui(
        tmp_path,
        streamlit_module=st,
        project_workspace=FakeWorkspace(),
        workflow_service=workflow,
    )

    tables = [
        call[1]
        for call in st.calls
        if call[0] == "table"
    ]
    queue = tables[0][0]
    assert queue["Source"] == "requirements.md"
    assert queue["Decisions required"] == 2
    assert "Source ID" not in queue
    assert "Processing Run" not in queue
    assert "Review Document" not in queue


def test_technical_review_queue_restores_exact_identities(tmp_path):
    st = FakeStreamlit()
    st.session_state[SESSION_APP_VIEW] = APP_VIEW_REVIEW
    st.session_state[SESSION_PROJECT_ID] = "123456"
    st.session_state[SESSION_SHOW_TECHNICAL_DETAILS] = True
    workflow = FakeWorkflowService(
        items=(_queue_item(with_workspace=True),)
    )

    render_human_review_approval_ui(
        tmp_path,
        streamlit_module=st,
        project_workspace=FakeWorkspace(),
        workflow_service=workflow,
    )

    tables = [
        call[1]
        for call in st.calls
        if call[0] == "table"
    ]
    queue = tables[0][0]
    assert queue["Source ID"] == "SRC-000001"
    assert queue["Processing Run"] == "PRN-000001"
    assert queue["Review Document"] == "RVD-000001"
