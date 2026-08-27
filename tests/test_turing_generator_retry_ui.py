"""G7.3 UI tests for current-state feedback and retry."""

from __future__ import annotations

from types import SimpleNamespace

from app.turing_generator_navigation import (
    APP_VIEW_INGESTION,
    APP_VIEW_REVIEW,
    SESSION_PENDING_NAVIGATION,
    ApplicationNavigationState,
    SESSION_APP_VIEW,
    SESSION_PROJECT_ID,
    SESSION_SELECTED_ENTITY_ID,
)
from app.turing_generator_ui import (
    render_ingestion_result_message,
    render_project_ingestion_execution,
)
from modules.project_ingestion import (
    CORRECTED_PIPELINE_CONFIGURATION_VERSION,
    ProjectIngestionConfiguration,
    calculate_ingestion_configuration_fingerprint,
)


PROJECT_ID = "123456"
SOURCE_ID = "SRC-000001"


class FakeStreamlit:
    def __init__(
        self,
        *,
        clicked_keys=(),
        checkbox_values=None,
    ) -> None:
        self.session_state = {
            SESSION_APP_VIEW: APP_VIEW_INGESTION,
            SESSION_PROJECT_ID: PROJECT_ID,
            SESSION_SELECTED_ENTITY_ID: SOURCE_ID,
        }
        self.clicked_keys = set(clicked_keys)
        self.checkbox_values = dict(checkbox_values or {})
        self.calls = []

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

    def selectbox(self, label, *, options, index, key, **kwargs):
        self.calls.append(("selectbox", label, key))
        return options[index]

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
        self.calls.append(("number_input", label, key))
        return value

    def checkbox(self, label, *, value, key):
        self.calls.append(("checkbox", label, key))
        return self.checkbox_values.get(key, value)

    def text_input(self, label, *, value, type, key, help):
        self.calls.append(("text_input", label, key))
        return "sk-correct"

    def button(self, label, *, key, type=None):
        self.calls.append(("button", label, key, type))
        return key in self.clicked_keys


def navigation():
    return ApplicationNavigationState(
        active_view=APP_VIEW_INGESTION,
        project_id=PROJECT_ID,
        return_view="overview",
        selected_entity_id=SOURCE_ID,
    )


def _state(run_state, *, fingerprint=None):
    return SimpleNamespace(
        project_id=PROJECT_ID,
        source_id=SOURCE_ID,
        processing_run_id=(
            None if run_state is None else "RUN-000001"
        ),
        attempt_id=(
            None if run_state is None else "ATT-000001"
        ),
        run_state=run_state,
        processing_stage=(
            None if run_state is None else "agentic_ingestion"
        ),
        failure_reason=(
            "llm_authentication_failed"
            if run_state == "failed"
            else None
        ),
        blocked_reason=None,
        pending_review=(run_state == "awaiting_review"),
        configuration_fingerprint=fingerprint,
        can_start_new=(run_state is None),
        can_retry=(run_state == "failed"),
        recovery_required=(run_state == "blocked"),
    )


class FakeService:
    def __init__(self, state):
        self.state = state
        self.retry_calls = []
        self.execute_calls = []
        self.source = SimpleNamespace(
            source_id=SOURCE_ID,
            source_role="engineering_source",
            original_filename="requirements.md",
            media_type="text/markdown",
            size_bytes=128,
            sha256="a" * 64,
        )

    def list_registered_sources(self, project_id):
        return SimpleNamespace(
            project_id=project_id,
            sources=(self.source,),
            issues=(),
        )

    def source_execution_state(self, project_id, source_id):
        return self.state

    def retry_registered_source(
        self,
        project_id,
        source_id,
        processing_run_id,
        *,
        configuration,
        api_key=None,
        execution_observer=None,
    ):
        self.retry_calls.append(
            (project_id, source_id, processing_run_id)
        )
        if execution_observer:
            execution_observer(
                SimpleNamespace(
                    processing_run_id=processing_run_id,
                    attempt_id="ATT-000002",
                    processing_stage="agentic_ingestion",
                )
            )
        return SimpleNamespace(
            project_id=project_id,
            source_id=source_id,
            processing_run_id=processing_run_id,
            attempt_id="ATT-000002",
            run_state="failed",
            processing_stage="agentic_ingestion",
            dry_run=configuration.dry_run,
            artifact_references=(),
            failure_reason="llm_authentication_failed",
            recovery_required=False,
        )

    def execute_registered_source(self, *args, **kwargs):
        self.execute_calls.append((args, kwargs))
        raise AssertionError("not expected")


def test_running_state_is_visible_and_has_no_start_button() -> None:
    st = FakeStreamlit()
    service = FakeService(_state("running"))

    render_project_ingestion_execution(
        st,
        ingestion_service=service,
        navigation=navigation(),
    )

    assert any(
        call[0] == "info"
        and "Processing is running" in call[1]
        for call in st.calls
    )
    assert not any(
        call[0] in {"info", "caption"}
        and "RUN-000001" in call[1]
        for call in st.calls
    )
    assert not any(
        call[0] == "button"
        and call[2]
        in {
            "turing_generator.run_agentic_ingestion",
            "turing_generator.retry_agentic_ingestion",
        }
        for call in st.calls
    )


def test_failed_run_offers_retry_when_configuration_matches() -> None:
    configuration = ProjectIngestionConfiguration()
    st = FakeStreamlit(
        clicked_keys={
            "turing_generator.retry_agentic_ingestion"
        }
    )
    service = FakeService(
        _state(
            "failed",
            fingerprint=(
                calculate_ingestion_configuration_fingerprint(
                    configuration
                )
            ),
        )
    )

    render_project_ingestion_execution(
        st,
        ingestion_service=service,
        navigation=navigation(),
    )

    assert service.retry_calls == [
        (PROJECT_ID, SOURCE_ID, "RUN-000001")
    ]
    assert not any(
        call[0] in {"info", "caption"}
        and "ATT-000002" in call[1]
        for call in st.calls
    )


def test_changed_configuration_blocks_retry_button() -> None:
    st = FakeStreamlit()
    service = FakeService(
        _state(
            "failed",
            fingerprint="f" * 64,
        )
    )

    render_project_ingestion_execution(
        st,
        ingestion_service=service,
        navigation=navigation(),
    )

    assert service.retry_calls == []
    assert any(
        call[0] == "warning"
        and "exact material configuration" in call[1]
        for call in st.calls
    )
    assert not any(
        call[0] == "button"
        and call[2] == "turing_generator.retry_agentic_ingestion"
        for call in st.calls
    )


def test_authentication_failure_message_is_actionable() -> None:
    st = FakeStreamlit()
    render_ingestion_result_message(
        st,
        SimpleNamespace(
            run_state="failed",
            failure_reason="llm_authentication_failed",
        ),
    )
    assert any(
        call[0] == "error"
        and "authentication" in call[1].lower()
        and "credentials" in call[1].lower()
        for call in st.calls
    )

def test_awaiting_review_offers_direct_human_review_transition() -> None:
    st = FakeStreamlit(
        clicked_keys={
            "turing_generator.continue_human_review.RUN-000001"
        }
    )
    service = FakeService(_state("awaiting_review"))

    render_project_ingestion_execution(
        st,
        ingestion_service=service,
        navigation=navigation(),
    )

    pending = st.session_state[SESSION_PENDING_NAVIGATION]
    assert pending["active_view"] == APP_VIEW_REVIEW
    assert pending["project_id"] == PROJECT_ID
    assert pending["selected_entity_id"] is None


def test_failed_corrected_run_reconstructs_v2_retry_configuration() -> None:
    configuration = ProjectIngestionConfiguration(
        max_members_per_team=None,
        pipeline_configuration_version=(
            CORRECTED_PIPELINE_CONFIGURATION_VERSION
        ),
    )
    st = FakeStreamlit(
        clicked_keys={
            "turing_generator.retry_agentic_ingestion"
        }
    )
    service = FakeService(
        _state(
            "failed",
            fingerprint=(
                calculate_ingestion_configuration_fingerprint(
                    configuration
                )
            ),
        )
    )

    render_project_ingestion_execution(
        st,
        ingestion_service=service,
        navigation=navigation(),
    )

    assert service.retry_calls == [
        (PROJECT_ID, SOURCE_ID, "RUN-000001")
    ]
