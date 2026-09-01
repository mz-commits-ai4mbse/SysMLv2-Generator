from __future__ import annotations

from types import SimpleNamespace

from app.turing_generator_navigation import (
    APP_VIEW_INGESTION,
    APP_VIEW_REVIEW,
    SESSION_APP_VIEW,
    SESSION_PENDING_NAVIGATION,
    SESSION_PROJECT_ID,
    SESSION_SELECTED_ENTITY_ID,
    ApplicationNavigationState,
)
from app.turing_generator_ui import render_project_ingestion_execution
from modules.project_ingestion import (
    CORRECTED_PIPELINE_CONFIGURATION_VERSION,
    LEGACY_PIPELINE_CONFIGURATION_VERSION,
    ProjectIngestionConfiguration,
    calculate_ingestion_configuration_fingerprint,
)


PROJECT_ID = "123456"
SOURCE_ID = "SRC-000001"


class FakePlaceholder:
    def __init__(self, st):
        self.st = st

    def button(self, label, *, key, type=None):
        return self.st.button(label, key=key, type=type)

    def empty(self):
        pass


class FakeStreamlit:
    def __init__(self, *, clicked_keys=(), checkbox_values=None):
        self.session_state = {
            SESSION_APP_VIEW: APP_VIEW_INGESTION,
            SESSION_PROJECT_ID: PROJECT_ID,
            SESSION_SELECTED_ENTITY_ID: SOURCE_ID,
        }
        self.clicked_keys = set(clicked_keys)
        self.checkbox_values = dict(checkbox_values or {})
        self.calls = []

    def subheader(self, text): self.calls.append(("subheader", text))
    def caption(self, text): self.calls.append(("caption", text))
    def info(self, text): self.calls.append(("info", text))
    def warning(self, text): self.calls.append(("warning", text))
    def error(self, text): self.calls.append(("error", text))
    def success(self, text): self.calls.append(("success", text))
    def table(self, rows): self.calls.append(("table", rows))

    def selectbox(self, label, *, options, index, key, **kwargs):
        self.calls.append(("selectbox", label, key))
        return options[index]

    def number_input(self, label, *, min_value, max_value, value, step, key):
        self.calls.append(("number_input", label, key))
        return value

    def checkbox(self, label, *, value, key):
        self.calls.append(("checkbox", label, key))
        return self.checkbox_values.get(key, value)

    def text_input(self, label, *, value, type, key, help):
        self.calls.append(("text_input", label, key))
        return "sk-test"

    def button(self, label, *, key, type=None):
        self.calls.append(("button", label, key, type))
        return key in self.clicked_keys

    def empty(self):
        return FakePlaceholder(self)

    def expander(self, *args, **kwargs):
        class Ctx:
            def __enter__(self_inner): return self
            def __exit__(self_inner, *exc): return False
        return Ctx()


def navigation():
    return ApplicationNavigationState(
        active_view=APP_VIEW_INGESTION,
        project_id=PROJECT_ID,
        return_view="overview",
        selected_entity_id=SOURCE_ID,
    )


def _fingerprint(pipeline_version):
    return calculate_ingestion_configuration_fingerprint(
        ProjectIngestionConfiguration(
            provider="openai",
            model="gpt-5.4-mini",
            runs_per_member=1,
            max_members_per_team=None,
            dry_run=False,
            pipeline_configuration_version=pipeline_version,
        )
    )


def _state(pipeline_version):
    return SimpleNamespace(
        project_id=PROJECT_ID,
        source_id=SOURCE_ID,
        processing_run_id="RUN-000001",
        attempt_id="ATT-000001",
        run_state="awaiting_review",
        processing_stage="agentic_ingestion",
        failure_reason=None,
        blocked_reason=None,
        pending_review=True,
        configuration_fingerprint=_fingerprint(pipeline_version),
        can_start_new=False,
        can_retry=False,
        recovery_required=False,
    )


class FakeService:
    def __init__(self, state):
        self.state = state
        self.successor_calls = []
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

    def supersede_and_execute_registered_source(
        self,
        project_id,
        source_id,
        predecessor_run_id,
        *,
        configuration,
        api_key=None,
        execution_observer=None,
        llm_progress_observer=None,
    ):
        self.successor_calls.append(
            (
                project_id,
                source_id,
                predecessor_run_id,
                configuration,
                api_key,
            )
        )
        if execution_observer is not None:
            execution_observer(
                SimpleNamespace(
                    processing_run_id="RUN-000005",
                    attempt_id="ATT-000001",
                )
            )
        return SimpleNamespace(
            project_id=project_id,
            source_id=source_id,
            source_projection_id="SP-000001",
            processing_run_id="RUN-000005",
            attempt_id="ATT-000001",
            run_state="awaiting_review",
            processing_stage="agentic_ingestion",
            dry_run=configuration.dry_run,
            artifact_references=(),
            failure_reason=None,
            recovery_required=False,
        )


def test_legacy_awaiting_review_offers_current_pipeline_reprocessing(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    st = FakeStreamlit()
    service = FakeService(_state(LEGACY_PIPELINE_CONFIGURATION_VERSION))

    render_project_ingestion_execution(
        st,
        ingestion_service=service,
        navigation=navigation(),
    )

    assert any(
        call[0] == "button"
        and call[1] == "Reprocess with current pipeline"
        for call in st.calls
    )
    assert not any(
        call[0] == "button"
        and "continue_human_review" in call[2]
        for call in st.calls
    )


def test_corrected_awaiting_review_keeps_human_review_transition():
    st = FakeStreamlit()
    service = FakeService(_state(CORRECTED_PIPELINE_CONFIGURATION_VERSION))

    render_project_ingestion_execution(
        st,
        ingestion_service=service,
        navigation=navigation(),
    )

    assert any(
        call[0] == "button"
        and "continue_human_review" in call[2]
        for call in st.calls
    )
    assert not any(
        call[0] == "button"
        and call[1] == "Reprocess with current pipeline"
        for call in st.calls
    )


def test_legacy_reprocess_uses_successor_service_and_corrected_pipeline(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    st = FakeStreamlit(
        clicked_keys={"turing_generator.reprocess_current_pipeline"},
        checkbox_values={
            "turing_generator.reprocess_live_confirmation": True,
        },
    )
    service = FakeService(_state(LEGACY_PIPELINE_CONFIGURATION_VERSION))

    render_project_ingestion_execution(
        st,
        ingestion_service=service,
        navigation=navigation(),
    )

    assert len(service.successor_calls) == 1
    (
        project_id,
        source_id,
        predecessor_run_id,
        configuration,
        api_key,
    ) = service.successor_calls[0]

    assert project_id == PROJECT_ID
    assert source_id == SOURCE_ID
    assert predecessor_run_id == "RUN-000001"
    assert (
        configuration.pipeline_configuration_version
        == CORRECTED_PIPELINE_CONFIGURATION_VERSION
    )
    assert configuration.dry_run is False
    assert api_key == "sk-test"
