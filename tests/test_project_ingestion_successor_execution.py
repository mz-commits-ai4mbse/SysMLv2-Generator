from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from modules.project_ingestion import (
    CORRECTED_PIPELINE_CONFIGURATION_VERSION,
    ProjectBoundIngestionService,
    ProjectIngestionConfiguration,
    ProjectIngestionExecutionError,
    ProjectIngestionRecoveryRequiredError,
)


def _configuration():
    return ProjectIngestionConfiguration(
        provider="openai",
        model="gpt-5.4-mini",
        runs_per_member=1,
        max_members_per_team=1,
        dry_run=False,
        pipeline_configuration_version=(
            CORRECTED_PIPELINE_CONFIGURATION_VERSION
        ),
    )


def _service(*, predecessor_state="awaiting_review"):
    service = ProjectBoundIngestionService.__new__(
        ProjectBoundIngestionService
    )
    service.root = None
    service.repository_root = None
    service._clock = lambda: datetime(
        2026, 8, 31, 10, 0, tzinfo=timezone.utc
    )
    service._workspace = SimpleNamespace(
        load_project=lambda project_id: SimpleNamespace(
            project_id=project_id,
            framework_template=SimpleNamespace(
                template_id="TURING_RFLP_FRAMEWORK",
                template_version="1.0.0",
            ),
        )
    )
    service._source_registry = SimpleNamespace(
        load_source=lambda project_id, source_id: SimpleNamespace(
            source_id=source_id,
            sha256="1" * 64,
            source_role="engineering_source",
        )
    )
    predecessor_manifest = SimpleNamespace(
        project_id="308131",
        processing_run_id="RUN-000001",
        source_id="SRC-000001",
    )
    predecessor = SimpleNamespace(
        manifest=predecessor_manifest,
        events=(SimpleNamespace(),),
    )
    service._processing = SimpleNamespace(
        load_run=lambda project_id, run_id: predecessor,
        next_run_id=lambda project_id: "RUN-000005",
        next_attempt_id=lambda *args: "ATT-000001",
    )
    service._predecessor = predecessor
    service._predecessor_state = predecessor_state
    return service


def test_successor_bridge_binds_exact_predecessor(monkeypatch):
    service = _service()
    captured = {}

    monkeypatch.setattr(
        "modules.project_ingestion.service.derive_processing_run_state",
        lambda history: SimpleNamespace(run_state="awaiting_review"),
    )

    class Operations:
        def create_successor_run(
            self,
            predecessor_run_id,
            successor_manifest,
            *,
            reason_code,
        ):
            captured["predecessor_run_id"] = predecessor_run_id
            captured["manifest"] = successor_manifest
            captured["reason_code"] = reason_code
            return (
                service._predecessor,
                SimpleNamespace(
                    manifest=successor_manifest,
                    events=(
                        SimpleNamespace(
                            event_sequence=1,
                            next_state="created",
                            event_fingerprint="a" * 64,
                        ),
                    ),
                ),
            )

    service._processing_operations = Operations()

    def append_event(event):
        captured["started_event"] = event
        return SimpleNamespace(
            manifest=captured["manifest"],
            events=(
                SimpleNamespace(),
                event,
            ),
        )

    service._processing.append_event = append_event

    work = SimpleNamespace(
        project_id="308131",
        source_id="SRC-000001",
        processing_run_id="RUN-000005",
        attempt_id="ATT-000001",
        run_state="running",
    )
    service._execute_started_attempt = lambda **kwargs: work
    service._complete_work = lambda value: ("complete", value)
    service._notify_execution_observer = lambda *args: None

    result = service.supersede_and_execute_registered_source(
        "308131",
        "SRC-000001",
        "RUN-000001",
        configuration=_configuration(),
    )

    manifest = captured["manifest"]
    assert manifest.processing_run_id == "RUN-000005"
    assert manifest.supersedes_run_id == "RUN-000001"
    assert manifest.source_id == "SRC-000001"
    assert manifest.source_sha256 == "1" * 64
    assert captured["predecessor_run_id"] == "RUN-000001"
    assert captured["reason_code"] == "processing_pipeline_successor"
    assert captured["started_event"].event_type == "stage_started"
    assert captured["started_event"].next_state == "running"
    assert result == ("complete", work)


def test_successor_bridge_rejects_running_predecessor(monkeypatch):
    service = _service(predecessor_state="running")
    monkeypatch.setattr(
        "modules.project_ingestion.service.derive_processing_run_state",
        lambda history: SimpleNamespace(run_state="running"),
    )
    service._processing_operations = SimpleNamespace()

    with pytest.raises(
        ProjectIngestionExecutionError,
        match="cannot supersede a currently active",
    ):
        service.supersede_and_execute_registered_source(
            "308131",
            "SRC-000001",
            "RUN-000001",
            configuration=_configuration(),
        )


def test_successor_bridge_rejects_wrong_source_binding(monkeypatch):
    service = _service()
    service._predecessor.manifest = SimpleNamespace(
        project_id="308131",
        processing_run_id="RUN-000001",
        source_id="SRC-999999",
    )
    monkeypatch.setattr(
        "modules.project_ingestion.service.derive_processing_run_state",
        lambda history: SimpleNamespace(run_state="awaiting_review"),
    )
    service._processing_operations = SimpleNamespace()

    with pytest.raises(
        ProjectIngestionExecutionError,
        match="does not belong to the selected Source",
    ):
        service.supersede_and_execute_registered_source(
            "308131",
            "SRC-000001",
            "RUN-000001",
            configuration=_configuration(),
        )


def test_successor_bridge_start_failure_requires_recovery(monkeypatch):
    service = _service()
    monkeypatch.setattr(
        "modules.project_ingestion.service.derive_processing_run_state",
        lambda history: SimpleNamespace(run_state="awaiting_review"),
    )

    class Operations:
        def create_successor_run(self, predecessor_run_id, successor_manifest, *, reason_code):
            return (
                service._predecessor,
                SimpleNamespace(
                    manifest=successor_manifest,
                    events=(
                        SimpleNamespace(
                            event_sequence=1,
                            next_state="created",
                            event_fingerprint="a" * 64,
                        ),
                    ),
                ),
            )

    service._processing_operations = Operations()
    service._processing.append_event = lambda event: (_ for _ in ()).throw(
        RuntimeError("write failed")
    )

    with pytest.raises(
        ProjectIngestionRecoveryRequiredError,
        match="successor Run exists",
    ):
        service.supersede_and_execute_registered_source(
            "308131",
            "SRC-000001",
            "RUN-000001",
            configuration=_configuration(),
        )
