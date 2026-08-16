from __future__ import annotations

from types import SimpleNamespace

from app.turing_generator_ui import render_project_ingestion_execution
from modules.project_ingestion import (
    DEFAULT_MODEL,
    DEFAULT_PROVIDER,
    ProjectIngestionConfiguration,
    calculate_ingestion_configuration_fingerprint,
)


class _ActionPlaceholder:
    def __init__(self, st):
        self._st = st
        self.cleared = False

    def button(self, label, *, key, type=None):
        self._st.events.append(("action_button", key))
        return key == "turing_generator.retry_agentic_ingestion"

    def empty(self):
        self.cleared = True
        self._st.events.append(("action_cleared", None))


class _FakeStreamlit:
    def __init__(self):
        self.session_state = {}
        self.events = []
        self.action_placeholder = None
        self.empty_calls = 0

    def subheader(self, *args, **kwargs):
        return None

    def caption(self, *args, **kwargs):
        return None

    def info(self, *args, **kwargs):
        self.events.append(("info", args[0] if args else None))
        return None

    def warning(self, *args, **kwargs):
        return None

    def error(self, *args, **kwargs):
        return None

    def success(self, *args, **kwargs):
        return None

    def table(self, *args, **kwargs):
        return None

    def selectbox(self, label, *, options, index=0, **kwargs):
        return options[index]

    def number_input(self, label, *, value, **kwargs):
        return value

    def checkbox(self, label, *, value=False, **kwargs):
        return value

    def text_input(self, *args, **kwargs):
        return ""

    def button(self, label, *, key=None, **kwargs):
        # Non-ingestion controls, e.g. "Open Processing Run", remain idle.
        self.events.append(("ordinary_button", key))
        return False

    def empty(self):
        self.empty_calls += 1
        self.action_placeholder = _ActionPlaceholder(self)
        return self.action_placeholder


class _RetryService:
    def __init__(self, st):
        self._st = st
        self.retry_called = False
        configuration = ProjectIngestionConfiguration(
            provider=DEFAULT_PROVIDER,
            model=DEFAULT_MODEL,
            runs_per_member=1,
            max_members_per_team=1,
            dry_run=True,
        )
        self._state = SimpleNamespace(
            project_id="000001",
            source_id="SRC-000001",
            processing_run_id="RUN-000001",
            attempt_id="ATT-000002",
            run_state="failed",
            processing_stage="agentic_ingestion",
            failure_reason="llm_provider_unavailable",
            blocked_reason=None,
            pending_review=False,
            recovery_required=False,
            can_start_new=False,
            can_retry=True,
            configuration_fingerprint=(
                calculate_ingestion_configuration_fingerprint(configuration)
            ),
        )

    def list_registered_sources(self, project_id):
        return SimpleNamespace(
            sources=[
                SimpleNamespace(
                    source_id="SRC-000001",
                    original_filename="fixture.md",
                    source_role="engineering_source",
                    media_type="text/markdown",
                    size_bytes=128,
                    sha256="a" * 64,
                )
            ]
        )

    def source_execution_state(self, project_id, source_id):
        return self._state

    def retry_registered_source(
        self,
        project_id,
        source_id,
        processing_run_id,
        *,
        configuration,
        api_key,
        execution_observer,
    ):
        self.retry_called = True
        self._st.events.append(("retry_call", None))

        assert self._st.action_placeholder is not None
        assert self._st.action_placeholder.cleared is True

        execution_observer(
            SimpleNamespace(
                processing_run_id="RUN-000001",
                attempt_id="ATT-000003",
                processing_stage="agentic_ingestion",
            )
        )

        return SimpleNamespace(
            project_id=project_id,
            source_id=source_id,
            processing_run_id="RUN-000001",
            attempt_id="ATT-000003",
            run_state="failed",
            processing_stage="agentic_ingestion",
            dry_run=True,
            artifact_references=(),
            failure_reason="llm_provider_unavailable",
            recovery_required=False,
        )


class _RunningService:
    def __init__(self):
        self.retry_called = False

    def list_registered_sources(self, project_id):
        return SimpleNamespace(
            sources=[
                SimpleNamespace(
                    source_id="SRC-000001",
                    original_filename="fixture.md",
                    source_role="engineering_source",
                    media_type="text/markdown",
                    size_bytes=128,
                    sha256="a" * 64,
                )
            ]
        )

    def source_execution_state(self, project_id, source_id):
        return SimpleNamespace(
            project_id="000001",
            source_id="SRC-000001",
            processing_run_id="RUN-000001",
            attempt_id="ATT-000003",
            run_state="running",
            processing_stage="agentic_ingestion",
            failure_reason=None,
            blocked_reason=None,
            pending_review=False,
            recovery_required=False,
            can_start_new=False,
            can_retry=False,
            configuration_fingerprint=None,
        )


def _navigation():
    return SimpleNamespace(
        project_id="000001",
        selected_entity_id="SRC-000001",
    )


def test_retry_action_is_removed_before_running_observer_is_rendered():
    st = _FakeStreamlit()
    service = _RetryService(st)

    render_project_ingestion_execution(
        st,
        ingestion_service=service,
        navigation=_navigation(),
    )

    assert service.retry_called is True
    assert st.action_placeholder is not None
    assert st.action_placeholder.cleared is True

    event_names = [event[0] for event in st.events]
    assert event_names.index("action_cleared") < event_names.index("retry_call")


def test_recorded_running_state_renders_no_ingestion_write_action():
    st = _FakeStreamlit()
    service = _RunningService()

    render_project_ingestion_execution(
        st,
        ingestion_service=service,
        navigation=_navigation(),
    )

    assert st.empty_calls == 0
    assert not any(
        event[0] == "action_button"
        for event in st.events
    )
