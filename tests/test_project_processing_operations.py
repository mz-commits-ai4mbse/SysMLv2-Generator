"""Tests for persistent retry and supersession operations."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from modules.project_processing.errors import (
    InvalidProcessingTransitionError,
    ProcessingPersistenceError,
    ProcessingRecoveryRequiredError,
    ProcessingReferenceError,
    ProcessingValidationError,
)
from modules.project_processing.event_manifest import (
    create_processing_event,
)
from modules.project_processing.operations import (
    ProjectProcessingOperations,
)
from modules.project_processing.paths import (
    attempt_artifact_path,
    run_path,
)
from modules.project_processing.repository import (
    ProjectProcessingRepository,
)
from modules.project_processing.run_lifecycle import (
    create_run_superseded_event,
    create_successor_initial_event,
)
from modules.project_processing.run_manifest import (
    create_processing_run_manifest,
    create_semantic_reference_version,
)
from modules.project_sources import (
    ENGINEERING_SOURCE_ROLE,
    ProjectSourceRegistry,
)
from modules.project_workspace import ProjectWorkspace


PROJECT_ID = "318604"
BASE_TIME = datetime(
    2026,
    7,
    25,
    10,
    0,
    0,
    tzinfo=timezone.utc,
)


class MutableClock:
    def __init__(self, value: object = BASE_TIME) -> None:
        self.value = value

    def __call__(self):
        return self.value


@pytest.fixture
def clock() -> MutableClock:
    return MutableClock()


@pytest.fixture
def projects_root(tmp_path: Path) -> Path:
    root = tmp_path / "projects"
    ProjectWorkspace(
        root=root,
        id_generator=lambda: PROJECT_ID,
    ).create_project("Processing Operations Test")
    return root


@pytest.fixture
def source_manifest(projects_root: Path, tmp_path: Path):
    source_path = tmp_path / "requirements.txt"
    source_path.write_text(
        "The system shall preserve source traceability.",
        encoding="utf-8",
    )
    return ProjectSourceRegistry(root=projects_root).register_source(
        PROJECT_ID,
        source_path,
        source_role=ENGINEERING_SOURCE_ROLE,
    )


@pytest.fixture
def repository(projects_root: Path) -> ProjectProcessingRepository:
    return ProjectProcessingRepository(root=projects_root)


@pytest.fixture
def operations(
    projects_root: Path,
    repository: ProjectProcessingRepository,
    clock: MutableClock,
) -> ProjectProcessingOperations:
    return ProjectProcessingOperations(
        root=projects_root,
        repository=repository,
        clock=clock,
    )


def semantic_versions():
    return (
        create_semantic_reference_version(
            reference_system_id="TURING_CORE_VOCABULARY",
            reference_version="1.0.0",
        ),
    )


def manifest(source_manifest, **overrides):
    values = {
        "project_id": PROJECT_ID,
        "processing_run_id": "RUN-000001",
        "source_id": source_manifest.source_id,
        "source_sha256": source_manifest.sha256,
        "source_role_snapshot": source_manifest.source_role,
        "workflow_profile": "engineering_source_processing",
        "configuration_fingerprint": "b" * 64,
        "framework_template_id": "TURING_RFLP_FRAMEWORK",
        "framework_template_version": "1.0.0",
        "semantic_reference_versions": semantic_versions(),
        "timestamp": "2026-07-25T10:00:00Z",
        "supersedes_run_id": None,
    }
    values.update(overrides)
    return create_processing_run_manifest(**values)


def initial_event(run_manifest):
    return create_processing_event(
        project_id=run_manifest.project_id,
        processing_run_id=run_manifest.processing_run_id,
        event_id="EVT-000001",
        event_sequence=1,
        previous_state=None,
        next_state="created",
        processing_stage=None,
        event_type="run_created",
        attempt_id=None,
        reason_code="run_created",
        artifact_references=(),
        timestamp=run_manifest.created_at,
        previous_event_fingerprint=None,
    )


def persist_initial_run(repository, source_manifest):
    run_manifest = manifest(source_manifest)
    return repository.create_run(
        run_manifest,
        initial_event(run_manifest),
    )


def successor_manifest(source_manifest, **overrides):
    values = {
        "processing_run_id": "RUN-000002",
        "configuration_fingerprint": "c" * 64,
        "timestamp": "2026-07-25T11:00:00Z",
        "supersedes_run_id": "RUN-000001",
    }
    values.update(overrides)
    return manifest(source_manifest, **values)


def complete_run(repository, history):
    first = history.events[-1]
    started = create_processing_event(
        project_id=PROJECT_ID,
        processing_run_id="RUN-000001",
        event_id="EVT-000002",
        event_sequence=2,
        previous_state="created",
        next_state="running",
        processing_stage="semantic_extraction",
        event_type="stage_started",
        attempt_id="ATT-000001",
        reason_code="semantic_extraction_started",
        artifact_references=(),
        timestamp="2026-07-25T10:10:00Z",
        previous_event_fingerprint=first.event_fingerprint,
    )
    history = repository.append_event(started)
    completed = create_processing_event(
        project_id=PROJECT_ID,
        processing_run_id="RUN-000001",
        event_id="EVT-000003",
        event_sequence=3,
        previous_state="running",
        next_state="completed",
        processing_stage="publication",
        event_type="run_completed",
        attempt_id="ATT-000001",
        reason_code="workflow_resolved",
        artifact_references=(),
        timestamp="2026-07-25T10:20:00Z",
        previous_event_fingerprint=(
            history.events[-1].event_fingerprint
        ),
    )
    return repository.append_event(completed)


def test_clean_project_scan_is_unchanged(
    operations,
    repository,
    source_manifest,
) -> None:
    persist_initial_run(repository, source_manifest)

    scan = operations.scan_project(PROJECT_ID)

    assert len(scan.run_histories) == 1
    assert scan.issues == ()


def test_start_retry_persists_attempt_and_event(
    operations,
    repository,
    projects_root,
    source_manifest,
    clock,
) -> None:
    persist_initial_run(repository, source_manifest)
    clock.value = datetime(
        2026, 7, 25, 10, 30, tzinfo=timezone.utc
    )

    history = operations.start_retry(
        PROJECT_ID,
        "RUN-000001",
        artifact_kind="agent_outputs",
        processing_stage="semantic_extraction",
        reason_code="review_changes_requested",
    )

    event = history.events[-1]
    assert event.event_id == "EVT-000002"
    assert event.attempt_id == "ATT-000001"
    assert event.event_type == "retry_started"
    assert event.occurred_at == "2026-07-25T10:30:00Z"
    assert attempt_artifact_path(
        projects_root,
        PROJECT_ID,
        "RUN-000001",
        artifact_kind="agent_outputs",
        processing_stage="semantic_extraction",
        attempt_id="ATT-000001",
    ).is_dir()


def test_second_retry_allocates_next_attempt(
    operations,
    repository,
    source_manifest,
    clock,
) -> None:
    persist_initial_run(repository, source_manifest)
    clock.value = datetime(
        2026, 7, 25, 10, 30, tzinfo=timezone.utc
    )
    operations.start_retry(
        PROJECT_ID,
        "RUN-000001",
        artifact_kind="agent_outputs",
        processing_stage="semantic_extraction",
        reason_code="first_retry",
    )
    clock.value = datetime(
        2026, 7, 25, 10, 40, tzinfo=timezone.utc
    )

    history = operations.start_retry(
        PROJECT_ID,
        "RUN-000001",
        artifact_kind="consensus_reports",
        processing_stage="semantic_extraction",
        reason_code="second_retry",
    )

    assert history.events[-1].attempt_id == "ATT-000002"
    assert history.events[-1].event_id == "EVT-000003"


def test_retry_rejects_completed_run_without_attempt_side_effect(
    operations,
    repository,
    projects_root,
    source_manifest,
) -> None:
    completed = complete_run(
        repository,
        persist_initial_run(repository, source_manifest),
    )

    with pytest.raises(InvalidProcessingTransitionError):
        operations.start_retry(
            PROJECT_ID,
            completed.manifest.processing_run_id,
            artifact_kind="agent_outputs",
            processing_stage="semantic_extraction",
            reason_code="retry_completed_run",
        )

    assert not (
        run_path(
            projects_root,
            PROJECT_ID,
            "RUN-000001",
        )
        / "artifacts"
    ).exists()


def test_retry_rejects_naive_clock_before_side_effect(
    projects_root,
    repository,
    source_manifest,
) -> None:
    persist_initial_run(repository, source_manifest)
    operations = ProjectProcessingOperations(
        root=projects_root,
        repository=repository,
        clock=lambda: datetime(2026, 7, 25, 10, 30),
    )

    with pytest.raises(ProcessingValidationError):
        operations.start_retry(
            PROJECT_ID,
            "RUN-000001",
            artifact_kind="agent_outputs",
            processing_stage="semantic_extraction",
            reason_code="retry_requested",
        )


def test_retry_rejects_non_datetime_clock(
    projects_root,
    repository,
    source_manifest,
) -> None:
    persist_initial_run(repository, source_manifest)
    operations = ProjectProcessingOperations(
        root=projects_root,
        repository=repository,
        clock=lambda: "2026-07-25T10:30:00Z",
    )

    with pytest.raises(ProcessingValidationError):
        operations.start_retry(
            PROJECT_ID,
            "RUN-000001",
            artifact_kind="agent_outputs",
            processing_stage="semantic_extraction",
            reason_code="retry_requested",
        )


def test_retry_event_failure_removes_empty_attempt_directory(
    operations,
    repository,
    projects_root,
    source_manifest,
    monkeypatch,
) -> None:
    persist_initial_run(repository, source_manifest)

    def fail_append(event):
        raise ProcessingPersistenceError("synthetic append failure")

    monkeypatch.setattr(repository, "append_event", fail_append)

    with pytest.raises(ProcessingPersistenceError):
        operations.start_retry(
            PROJECT_ID,
            "RUN-000001",
            artifact_kind="agent_outputs",
            processing_stage="semantic_extraction",
            reason_code="retry_requested",
        )

    assert not attempt_artifact_path(
        projects_root,
        PROJECT_ID,
        "RUN-000001",
        artifact_kind="agent_outputs",
        processing_stage="semantic_extraction",
        attempt_id="ATT-000001",
    ).exists()


def test_create_successor_persists_complete_pair(
    operations,
    repository,
    source_manifest,
    clock,
) -> None:
    persist_initial_run(repository, source_manifest)
    successor = successor_manifest(source_manifest)
    clock.value = datetime(
        2026, 7, 25, 11, 0, 1, tzinfo=timezone.utc
    )

    predecessor_history, successor_history = (
        operations.create_successor_run(
            "RUN-000001",
            successor,
            reason_code="material_binding_changed",
        )
    )

    assert predecessor_history.events[-1].next_state == "superseded"
    assert predecessor_history.events[-1].event_type == "run_superseded"
    assert successor_history.manifest == successor
    assert successor_history.events[-1].next_state == "created"
    assert operations.scan_project(PROJECT_ID).issues == ()


def test_successor_states_include_reverse_link(
    operations,
    repository,
    source_manifest,
    clock,
) -> None:
    persist_initial_run(repository, source_manifest)
    clock.value = datetime(
        2026, 7, 25, 11, 0, 1, tzinfo=timezone.utc
    )
    operations.create_successor_run(
        "RUN-000001",
        successor_manifest(source_manifest),
        reason_code="material_binding_changed",
    )

    states = operations.derive_run_states(PROJECT_ID)

    assert tuple(state.processing_run_id for state in states) == (
        "RUN-000001",
        "RUN-000002",
    )
    assert states[0].superseded_by_run_id == "RUN-000002"
    assert states[1].superseded_by_run_id is None


def test_successor_requires_next_available_run_id(
    operations,
    repository,
    source_manifest,
) -> None:
    persist_initial_run(repository, source_manifest)

    with pytest.raises(ProcessingValidationError):
        operations.create_successor_run(
            "RUN-000001",
            successor_manifest(
                source_manifest,
                processing_run_id="RUN-000003",
            ),
            reason_code="material_binding_changed",
        )


def test_successor_requires_material_change(
    operations,
    repository,
    source_manifest,
) -> None:
    persist_initial_run(repository, source_manifest)

    with pytest.raises(ProcessingValidationError):
        operations.create_successor_run(
            "RUN-000001",
            successor_manifest(
                source_manifest,
                configuration_fingerprint="b" * 64,
            ),
            reason_code="unchanged_bindings",
        )


def test_successor_must_reference_requested_predecessor(
    operations,
    repository,
    source_manifest,
) -> None:
    persist_initial_run(repository, source_manifest)

    with pytest.raises(ProcessingReferenceError):
        operations.create_successor_run(
            "RUN-000001",
            successor_manifest(
                source_manifest,
                supersedes_run_id="RUN-000009",
            ),
            reason_code="wrong_predecessor",
        )


def test_interrupted_supersession_retains_successor_and_reports_recovery(
    operations,
    repository,
    source_manifest,
    clock,
    monkeypatch,
) -> None:
    persist_initial_run(repository, source_manifest)
    successor = successor_manifest(source_manifest)
    clock.value = datetime(
        2026, 7, 25, 11, 0, 1, tzinfo=timezone.utc
    )
    original_append = repository.append_event

    def fail_supersession(event):
        if event.event_type == "run_superseded":
            raise ProcessingPersistenceError("synthetic failure")
        return original_append(event)

    monkeypatch.setattr(
        repository,
        "append_event",
        fail_supersession,
    )

    with pytest.raises(ProcessingRecoveryRequiredError):
        operations.create_successor_run(
            "RUN-000001",
            successor,
            reason_code="material_binding_changed",
        )

    assert repository.load_run(
        PROJECT_ID,
        "RUN-000002",
    ).manifest == successor
    scan = operations.scan_project(PROJECT_ID)
    assert tuple(issue.code for issue in scan.issues) == (
        "supersession_recovery_required",
    )


def test_retry_is_blocked_while_supersession_recovery_is_required(
    operations,
    repository,
    source_manifest,
) -> None:
    predecessor = persist_initial_run(repository, source_manifest)
    successor = successor_manifest(source_manifest)
    repository.create_run(
        successor,
        create_successor_initial_event(successor),
    )

    with pytest.raises(ProcessingRecoveryRequiredError):
        operations.start_retry(
            PROJECT_ID,
            predecessor.manifest.processing_run_id,
            artifact_kind="agent_outputs",
            processing_stage="semantic_extraction",
            reason_code="retry_requested",
        )


def test_scan_detects_successor_without_predecessor_event(
    operations,
    repository,
    source_manifest,
) -> None:
    persist_initial_run(repository, source_manifest)
    successor = successor_manifest(source_manifest)
    repository.create_run(
        successor,
        create_successor_initial_event(successor),
    )

    scan = operations.scan_project(PROJECT_ID)

    assert tuple(issue.code for issue in scan.issues) == (
        "supersession_recovery_required",
    )


def test_scan_detects_superseded_run_without_successor(
    operations,
    repository,
    source_manifest,
) -> None:
    predecessor = persist_initial_run(repository, source_manifest)
    successor = successor_manifest(source_manifest)
    event = create_run_superseded_event(
        predecessor,
        successor,
        reason_code="material_binding_changed",
        timestamp="2026-07-25T11:00:01Z",
    )
    repository.append_event(event)

    scan = operations.scan_project(PROJECT_ID)

    assert tuple(issue.code for issue in scan.issues) == (
        "supersession_recovery_required",
    )


def test_scan_detects_multiple_successors(
    operations,
    repository,
    source_manifest,
) -> None:
    predecessor = persist_initial_run(repository, source_manifest)
    first = successor_manifest(source_manifest)
    second = successor_manifest(
        source_manifest,
        processing_run_id="RUN-000003",
        configuration_fingerprint="d" * 64,
        timestamp="2026-07-25T12:00:00Z",
    )
    repository.create_run(first, create_successor_initial_event(first))
    repository.create_run(second, create_successor_initial_event(second))
    repository.append_event(
        create_run_superseded_event(
            predecessor,
            first,
            reason_code="material_binding_changed",
            timestamp="2026-07-25T11:00:01Z",
        )
    )

    scan = operations.scan_project(PROJECT_ID)

    assert tuple(issue.code for issue in scan.issues) == (
        "invalid_supersession_relationship",
    )


def test_derive_states_blocks_on_incomplete_supersession(
    operations,
    repository,
    source_manifest,
) -> None:
    persist_initial_run(repository, source_manifest)
    successor = successor_manifest(source_manifest)
    repository.create_run(
        successor,
        create_successor_initial_event(successor),
    )

    with pytest.raises(ProcessingRecoveryRequiredError):
        operations.derive_run_states(PROJECT_ID)


def test_operations_can_construct_repository_from_root(
    projects_root,
    source_manifest,
    clock,
) -> None:
    repository = ProjectProcessingRepository(root=projects_root)
    persist_initial_run(repository, source_manifest)
    created = ProjectProcessingOperations(
        root=projects_root,
        clock=clock,
    )

    assert created.scan_project(PROJECT_ID).issues == ()


def test_invalid_successor_reason_has_no_persistence_side_effect(
    operations,
    repository,
    projects_root,
    source_manifest,
    clock,
) -> None:
    persist_initial_run(repository, source_manifest)
    clock.value = datetime(
        2026, 7, 25, 11, 0, 1, tzinfo=timezone.utc
    )

    with pytest.raises(ProcessingValidationError):
        operations.create_successor_run(
            "RUN-000001",
            successor_manifest(source_manifest),
            reason_code="Invalid reason code",
        )

    assert not run_path(
        projects_root,
        PROJECT_ID,
        "RUN-000002",
    ).exists()


def test_invalid_successor_clock_has_no_persistence_side_effect(
    projects_root,
    repository,
    source_manifest,
) -> None:
    persist_initial_run(repository, source_manifest)
    operations = ProjectProcessingOperations(
        root=projects_root,
        repository=repository,
        clock=lambda: datetime(2026, 7, 25, 11, 0, 1),
    )

    with pytest.raises(ProcessingValidationError):
        operations.create_successor_run(
            "RUN-000001",
            successor_manifest(source_manifest),
            reason_code="material_binding_changed",
        )

    assert not run_path(
        projects_root,
        PROJECT_ID,
        "RUN-000002",
    ).exists()


def test_successor_requires_manifest_instance(
    operations,
) -> None:
    with pytest.raises(ProcessingValidationError):
        operations.create_successor_run(
            "RUN-000001",
            object(),
            reason_code="material_binding_changed",
        )