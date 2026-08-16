"""Tests for P9 execution controls and queued Dashboard return."""

from __future__ import annotations

from types import SimpleNamespace

from app.presentation_preferences import SESSION_SHOW_TECHNICAL_DETAILS
from app.turing_generator_navigation import (
    APP_VIEW_DASHBOARD,
    APP_VIEW_INGESTION,
    DASHBOARD_VIEW_SOURCES,
    SESSION_APP_VIEW,
    SESSION_DASHBOARD_VIEW,
    SESSION_PENDING_NAVIGATION,
    SESSION_PROJECT_ID,
    SESSION_SELECTED_ENTITY_ID,
    ApplicationNavigationState,
    apply_pending_app_view,
)
from app.turing_generator_ui import (
    render_project_ingestion_execution,
)


PROJECT_ID = "123456"
SOURCE_ID = "SRC-000001"


class FakeStreamlit:
    """Minimal configurable Streamlit double for execution controls."""

    def __init__(
        self,
        *,
        clicked_keys=(),
        select_values=None,
        number_values=None,
        checkbox_values=None,
        text_values=None,
    ) -> None:
        self.session_state = {
            SESSION_APP_VIEW: APP_VIEW_INGESTION,
            SESSION_PROJECT_ID: PROJECT_ID,
            SESSION_SELECTED_ENTITY_ID: SOURCE_ID,
        }
        self.clicked_keys = set(clicked_keys)
        self.select_values = dict(select_values or {})
        self.number_values = dict(number_values or {})
        self.checkbox_values = dict(checkbox_values or {})
        self.text_values = dict(text_values or {})
        self.calls: list[tuple] = []
        self.rerun_count = 0

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

    def selectbox(
        self,
        label,
        *,
        options,
        index,
        key,
        **kwargs,
    ):
        self.calls.append(
            ("selectbox", label, tuple(options), index, key)
        )
        return self.select_values.get(key, options[index])

    def number_input(
        self,
        label,
        *,
        min_value,
        max_value,
        value,
        step,
        key,
    ):
        self.calls.append(
            ("number_input", label, key)
        )
        return self.number_values.get(key, value)

    def checkbox(
        self,
        label,
        *,
        value,
        key,
    ):
        self.calls.append(("checkbox", label, key))
        return self.checkbox_values.get(key, value)

    def text_input(
        self,
        label,
        *,
        value,
        type,
        key,
        help,
    ):
        self.calls.append(("text_input", label, key, type))
        return self.text_values.get(key, value)

    def button(
        self,
        label,
        *,
        key,
        type=None,
    ):
        self.calls.append(("button", label, key, type))
        return key in self.clicked_keys

    def rerun(self):
        self.rerun_count += 1


class FakeExecutionService:
    def __init__(
        self,
        *,
        result_state="awaiting_review",
        execution_error=None,
    ) -> None:
        self.source = SimpleNamespace(
            project_id=PROJECT_ID,
            source_id=SOURCE_ID,
            source_role="engineering_source",
            original_filename="requirements.txt",
            media_type="text/plain",
            size_bytes=42,
            sha256="a" * 64,
            registered_at="2026-07-27T18:00:00Z",
        )
        self.result_state = result_state
        self.execution_error = execution_error
        self.calls: list[dict[str, object]] = []

    def list_registered_sources(self, project_id):
        return SimpleNamespace(
            project_id=project_id,
            sources=(self.source,),
            issues=(),
        )

    def execute_registered_source(
        self,
        project_id,
        source_id,
        *,
        configuration,
        api_key=None,
    ):
        self.calls.append(
            {
                "project_id": project_id,
                "source_id": source_id,
                "configuration": configuration,
                "api_key": api_key,
            }
        )
        if self.execution_error is not None:
            raise self.execution_error

        return SimpleNamespace(
            project_id=project_id,
            source_id=source_id,
            processing_run_id="RUN-000001",
            attempt_id="ATT-000001",
            run_state=self.result_state,
            processing_stage="agentic_ingestion",
            dry_run=configuration.dry_run,
            artifact_references=(
                SimpleNamespace(),
                SimpleNamespace(),
            ),
            failure_reason=(
                None
                if self.result_state == "awaiting_review"
                else "controlled_failure"
            ),
            recovery_required=(
                self.result_state == "blocked"
            ),
        )


def navigation() -> ApplicationNavigationState:
    return ApplicationNavigationState(
        active_view=APP_VIEW_INGESTION,
        project_id=PROJECT_ID,
        return_view="overview",
        selected_entity_id=SOURCE_ID,
    )


def test_dry_run_execution_uses_selected_source_and_configuration(
    monkeypatch,
):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    st = FakeStreamlit(
        clicked_keys={
            "turing_generator.run_agentic_ingestion"
        },
        select_values={
            "turing_generator.execution_model": "gpt-5-mini",
            "turing_generator.execution_team_scope": "all",
        },
        number_values={
            "turing_generator.execution_runs_per_member": 2,
        },
    )
    service = FakeExecutionService()

    render_project_ingestion_execution(
        st,
        ingestion_service=service,
        navigation=navigation(),
    )

    assert len(service.calls) == 1
    call = service.calls[0]
    configuration = call["configuration"]
    assert call["project_id"] == PROJECT_ID
    assert call["source_id"] == SOURCE_ID
    assert call["api_key"] is None
    assert configuration.model == "gpt-5-mini"
    assert configuration.runs_per_member == 2
    assert configuration.max_members_per_team is None
    assert configuration.dry_run is True
    assert (
        st.session_state[SESSION_SELECTED_ENTITY_ID]
        == "RUN-000001"
    )
    assert any(call[0] == "success" for call in st.calls)


def test_live_execution_requires_explicit_confirmation(
    monkeypatch,
):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    st = FakeStreamlit(
        clicked_keys={
            "turing_generator.run_agentic_ingestion"
        },
        checkbox_values={
            "turing_generator.execution_dry_run": False,
            "turing_generator.execution_live_confirmation": False,
        },
        text_values={
            "turing_generator.execution_api_key": "sk-test",
        },
    )
    service = FakeExecutionService()

    render_project_ingestion_execution(
        st,
        ingestion_service=service,
        navigation=navigation(),
    )

    assert service.calls == []
    errors = [
        call[1]
        for call in st.calls
        if call[0] == "error"
    ]
    assert "explicit confirmation" in errors[-1]


def test_live_execution_passes_session_key_without_persisting_it(
    monkeypatch,
):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    secret = "sk-session-only"
    st = FakeStreamlit(
        clicked_keys={
            "turing_generator.run_agentic_ingestion"
        },
        checkbox_values={
            "turing_generator.execution_dry_run": False,
            "turing_generator.execution_live_confirmation": True,
        },
        text_values={
            "turing_generator.execution_api_key": secret,
        },
    )
    service = FakeExecutionService()

    render_project_ingestion_execution(
        st,
        ingestion_service=service,
        navigation=navigation(),
    )

    assert service.calls[0]["api_key"] == secret
    assert secret not in repr(st.session_state)


def test_open_run_queues_dashboard_sources_transition():
    st = FakeStreamlit(
        clicked_keys={
            "turing_generator.open_processing_run.RUN-000001"
        },
    )
    st.session_state[
        "turing_generator.last_ingestion_result"
    ] = {
        "project_id": PROJECT_ID,
        "source_id": SOURCE_ID,
        "processing_run_id": "RUN-000001",
        "attempt_id": "ATT-000001",
        "run_state": "awaiting_review",
        "processing_stage": "agentic_ingestion",
        "dry_run": True,
        "artifact_count": 5,
        "failure_reason": None,
        "recovery_required": False,
    }
    st.session_state[SESSION_SHOW_TECHNICAL_DETAILS] = True
    service = FakeExecutionService()

    render_project_ingestion_execution(
        st,
        ingestion_service=service,
        navigation=ApplicationNavigationState(
            active_view=APP_VIEW_INGESTION,
            project_id=PROJECT_ID,
            return_view="overview",
            selected_entity_id="RUN-000001",
        ),
    )

    assert SESSION_PENDING_NAVIGATION in st.session_state
    assert st.session_state[SESSION_APP_VIEW] == (
        APP_VIEW_INGESTION
    )
    assert st.rerun_count == 1

    state = apply_pending_app_view(st.session_state)

    assert state.active_view == APP_VIEW_DASHBOARD
    assert state.project_id == PROJECT_ID
    assert state.return_view == DASHBOARD_VIEW_SOURCES
    assert state.selected_entity_id == "RUN-000001"
    assert st.session_state[SESSION_DASHBOARD_VIEW] == (
        DASHBOARD_VIEW_SOURCES
    )
    assert st.session_state[
        "project_dashboard.view_selector"
    ] == DASHBOARD_VIEW_SOURCES


def test_failed_result_remains_visible_and_does_not_claim_success():
    st = FakeStreamlit(
        clicked_keys={
            "turing_generator.run_agentic_ingestion"
        },
    )
    service = FakeExecutionService(
        result_state="failed",
    )

    render_project_ingestion_execution(
        st,
        ingestion_service=service,
        navigation=navigation(),
    )

    assert any(call[0] == "error" for call in st.calls)
    assert not any(call[0] == "success" for call in st.calls)
    payload = st.session_state[
        "turing_generator.last_ingestion_result"
    ]
    assert payload["run_state"] == "failed"
    assert payload["artifact_count"] == 2
