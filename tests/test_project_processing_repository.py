"""Tests for project-local Processing Run persistence and scanning."""

from __future__ import annotations

from pathlib import Path

import pytest

from modules.project_processing.decision_manifest import (
    create_processing_decision,
)
from modules.project_processing.errors import (
    DuplicateProcessingDecisionError,
    DuplicateProcessingEventError,
    ProcessingEventChainError,
    ProcessingIntegrityError,
    ProcessingPersistenceError,
    ProcessingRecoveryRequiredError,
    ProcessingReferenceError,
    ProcessingRunNotFoundError,
    ProcessingValidationError,
    UnsafeProcessingPathError,
)
from modules.project_processing.event_manifest import (
    create_processing_event,
)
from modules.project_processing.paths import (
    attempt_artifact_path,
    event_path,
    processing_decision_path,
    run_manifest_path,
    run_path,
)
from modules.project_processing.repository import (
    ProjectProcessingRepository,
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
TIMESTAMP = "2026-07-25T10:00:00Z"


@pytest.fixture
def projects_root(tmp_path: Path) -> Path:
    root = tmp_path / "projects"
    workspace = ProjectWorkspace(
        root=root,
        id_generator=lambda: PROJECT_ID,
    )
    workspace.create_project("Processing Repository Test")
    return root


@pytest.fixture
def source_manifest(
    projects_root: Path,
    tmp_path: Path,
):
    source_path = tmp_path / "requirements.txt"
    source_path.write_text(
        "The system shall preserve source traceability.",
        encoding="utf-8",
    )
    registry = ProjectSourceRegistry(root=projects_root)
    return registry.register_source(
        PROJECT_ID,
        source_path,
        source_role=ENGINEERING_SOURCE_ROLE,
    )


@pytest.fixture
def repository(
    projects_root: Path,
) -> ProjectProcessingRepository:
    return ProjectProcessingRepository(root=projects_root)


def _semantic_reference_versions():
    return (
        create_semantic_reference_version(
            reference_system_id="BFO",
            reference_version="2020",
        ),
        create_semantic_reference_version(
            reference_system_id="IOF_CORE",
            reference_version="202602",
        ),
        create_semantic_reference_version(
            reference_system_id="TURING_CORE_VOCABULARY",
            reference_version="1.0.0",
        ),
    )


def _manifest(source_manifest, **overrides):
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
        "semantic_reference_versions": (
            _semantic_reference_versions()
        ),
        "timestamp": TIMESTAMP,
        "supersedes_run_id": None,
    }
    values.update(overrides)
    return create_processing_run_manifest(**values)


def _initial_event(**overrides):
    values = {
        "project_id": PROJECT_ID,
        "processing_run_id": "RUN-000001",
        "event_id": "EVT-000001",
        "event_sequence": 1,
        "previous_state": None,
        "next_state": "created",
        "processing_stage": None,
        "event_type": "run_created",
        "attempt_id": None,
        "reason_code": "run_created",
        "artifact_references": (),
        "timestamp": TIMESTAMP,
        "previous_event_fingerprint": None,
    }
    values.update(overrides)
    return create_processing_event(**values)


def _started_event(previous_event, **overrides):
    values = {
        "project_id": PROJECT_ID,
        "processing_run_id": "RUN-000001",
        "event_id": "EVT-000002",
        "event_sequence": 2,
        "previous_state": "created",
        "next_state": "running",
        "processing_stage": "source_projection",
        "event_type": "stage_started",
        "attempt_id": "ATT-000001",
        "reason_code": "source_projection_started",
        "artifact_references": (),
        "timestamp": "2026-07-25T10:01:00Z",
        "previous_event_fingerprint": (
            previous_event.event_fingerprint
        ),
    }
    values.update(overrides)
    return create_processing_event(**values)


def _decision(source_manifest, **overrides):
    values = {
        "project_id": PROJECT_ID,
        "processing_decision_id": "PD-000001",
        "decision_type": "source_disposition",
        "source_id": source_manifest.source_id,
        "source_sha256": source_manifest.sha256,
        "disposition": "in_scope",
        "reviewer_identity": "Moritz Diez",
        "rationale": "The source is relevant engineering evidence.",
        "timestamp": TIMESTAMP,
        "supersedes_processing_decision_id": None,
    }
    values.update(overrides)
    return create_processing_decision(**values)


def _persist_initial_run(repository, source_manifest):
    manifest = _manifest(source_manifest)
    event = _initial_event()
    return repository.create_run(manifest, event)


def test_processing_paths_are_project_local(
    projects_root: Path,
) -> None:
    assert run_path(
        projects_root,
        PROJECT_ID,
        "RUN-000001",
    ) == (
        projects_root
        / PROJECT_ID
        / "runs"
        / "RUN-000001"
    )
    assert event_path(
        projects_root,
        PROJECT_ID,
        "RUN-000001",
        "EVT-000002",
    ).name == "EVT-000002.json"
    assert processing_decision_path(
        projects_root,
        PROJECT_ID,
        "PD-000001",
    ).name == "PD-000001.json"


def test_processing_paths_reject_invalid_identifiers(
    projects_root: Path,
) -> None:
    with pytest.raises(ProcessingValidationError):
        run_path(projects_root, "../318604", "RUN-000001")

    with pytest.raises(ProcessingValidationError):
        event_path(
            projects_root,
            PROJECT_ID,
            "RUN-000001",
            "../../EVT-000001",
        )


def test_next_run_id_starts_at_one(
    repository: ProjectProcessingRepository,
) -> None:
    assert repository.next_run_id(PROJECT_ID) == "RUN-000001"


def test_create_run_persists_minimal_authoritative_layout(
    repository: ProjectProcessingRepository,
    projects_root: Path,
    source_manifest,
) -> None:
    history = _persist_initial_run(repository, source_manifest)
    directory = run_path(
        projects_root,
        PROJECT_ID,
        "RUN-000001",
    )

    assert history.manifest.processing_run_id == "RUN-000001"
    assert run_manifest_path(
        projects_root,
        PROJECT_ID,
        "RUN-000001",
    ).is_file()
    assert (directory / "events" / "EVT-000001.json").is_file()
    assert not (directory / "artifacts").exists()
    assert not (directory / "work").exists()


def test_create_run_round_trip_is_lossless(
    repository: ProjectProcessingRepository,
    source_manifest,
) -> None:
    persisted = _persist_initial_run(repository, source_manifest)
    loaded = repository.load_run(PROJECT_ID, "RUN-000001")

    assert loaded == persisted


def test_create_run_rejects_source_hash_mismatch(
    repository: ProjectProcessingRepository,
    source_manifest,
) -> None:
    manifest = _manifest(
        source_manifest,
        source_sha256="f" * 64,
    )

    with pytest.raises(ProcessingReferenceError):
        repository.create_run(manifest, _initial_event())


def test_create_run_rejects_source_role_mismatch(
    repository: ProjectProcessingRepository,
    source_manifest,
) -> None:
    manifest = _manifest(
        source_manifest,
        source_role_snapshot="context_only",
        workflow_profile="context_only_processing",
    )

    with pytest.raises(ProcessingReferenceError):
        repository.create_run(manifest, _initial_event())


def test_create_run_rejects_existing_run_directory(
    repository: ProjectProcessingRepository,
    source_manifest,
) -> None:
    _persist_initial_run(repository, source_manifest)

    with pytest.raises(ProcessingPersistenceError):
        _persist_initial_run(repository, source_manifest)


def test_create_run_detects_interrupted_temporary_directory(
    repository: ProjectProcessingRepository,
    projects_root: Path,
    source_manifest,
) -> None:
    temporary = (
        projects_root
        / PROJECT_ID
        / "runs"
        / ".create-RUN-000001.tmp"
    )
    temporary.parent.mkdir()
    temporary.mkdir()

    with pytest.raises(ProcessingRecoveryRequiredError):
        _persist_initial_run(repository, source_manifest)


def test_next_run_id_does_not_reuse_gaps(
    repository: ProjectProcessingRepository,
    projects_root: Path,
) -> None:
    root = projects_root / PROJECT_ID / "runs"
    root.mkdir()
    (root / "RUN-000001").mkdir()
    (root / "RUN-000003").mkdir()

    assert repository.next_run_id(PROJECT_ID) == "RUN-000004"


def test_next_run_id_reserves_interrupted_creation(
    repository: ProjectProcessingRepository,
    projects_root: Path,
) -> None:
    root = projects_root / PROJECT_ID / "runs"
    root.mkdir()
    (root / ".create-RUN-000001.tmp").mkdir()

    assert repository.next_run_id(PROJECT_ID) == "RUN-000002"


def test_append_event_extends_persisted_history(
    repository: ProjectProcessingRepository,
    projects_root: Path,
    source_manifest,
) -> None:
    history = _persist_initial_run(repository, source_manifest)
    event = _started_event(history.events[-1])

    updated = repository.append_event(event)

    assert updated.events == history.events + (event,)
    assert event_path(
        projects_root,
        PROJECT_ID,
        "RUN-000001",
        "EVT-000002",
    ).is_file()


def test_append_event_rejects_identical_duplicate(
    repository: ProjectProcessingRepository,
    source_manifest,
) -> None:
    history = _persist_initial_run(repository, source_manifest)
    event = _started_event(history.events[-1])
    repository.append_event(event)

    with pytest.raises(DuplicateProcessingEventError):
        repository.append_event(event)


def test_append_event_rejects_broken_chain(
    repository: ProjectProcessingRepository,
    source_manifest,
) -> None:
    history = _persist_initial_run(repository, source_manifest)
    event = _started_event(
        history.events[-1],
        previous_event_fingerprint="f" * 64,
    )

    with pytest.raises(ProcessingEventChainError):
        repository.append_event(event)


def test_append_event_detects_interrupted_temporary_file(
    repository: ProjectProcessingRepository,
    projects_root: Path,
    source_manifest,
) -> None:
    history = _persist_initial_run(repository, source_manifest)
    event = _started_event(history.events[-1])
    temporary = (
        projects_root
        / PROJECT_ID
        / "runs"
        / "RUN-000001"
        / "events"
        / ".EVT-000002.json.tmp"
    )
    temporary.write_text("{}\n", encoding="utf-8")

    with pytest.raises(ProcessingRecoveryRequiredError):
        repository.append_event(event)


def test_load_run_rejects_missing_run(
    repository: ProjectProcessingRepository,
) -> None:
    with pytest.raises(ProcessingRunNotFoundError):
        repository.load_run(PROJECT_ID, "RUN-000001")


def test_load_run_rejects_manipulated_event_content(
    repository: ProjectProcessingRepository,
    projects_root: Path,
    source_manifest,
) -> None:
    _persist_initial_run(repository, source_manifest)
    path = event_path(
        projects_root,
        PROJECT_ID,
        "RUN-000001",
        "EVT-000001",
    )
    text = path.read_text(encoding="utf-8")
    path.write_text(
        text.replace('"reason_code": "run_created"',
                     '"reason_code": "manipulated"'),
        encoding="utf-8",
    )

    with pytest.raises(ProcessingIntegrityError):
        repository.load_run(PROJECT_ID, "RUN-000001")


def test_load_run_rejects_event_filename_mismatch(
    repository: ProjectProcessingRepository,
    projects_root: Path,
    source_manifest,
) -> None:
    _persist_initial_run(repository, source_manifest)
    events = (
        projects_root
        / PROJECT_ID
        / "runs"
        / "RUN-000001"
        / "events"
    )
    original = events / "EVT-000001.json"
    original.rename(events / "EVT-000002.json")

    with pytest.raises(ProcessingIntegrityError):
        repository.load_run(PROJECT_ID, "RUN-000001")


def test_persist_and_load_processing_decision(
    repository: ProjectProcessingRepository,
    projects_root: Path,
    source_manifest,
) -> None:
    decision = _decision(source_manifest)

    persisted = repository.persist_decision(decision)
    loaded = repository.load_decision(PROJECT_ID, "PD-000001")

    assert persisted == decision
    assert loaded == decision
    assert processing_decision_path(
        projects_root,
        PROJECT_ID,
        "PD-000001",
    ).is_file()


def test_persist_decision_rejects_identical_duplicate(
    repository: ProjectProcessingRepository,
    source_manifest,
) -> None:
    decision = _decision(source_manifest)
    repository.persist_decision(decision)

    with pytest.raises(DuplicateProcessingDecisionError):
        repository.persist_decision(decision)


def test_persist_decision_rejects_source_hash_mismatch(
    repository: ProjectProcessingRepository,
    source_manifest,
) -> None:
    decision = _decision(
        source_manifest,
        source_sha256="f" * 64,
    )

    with pytest.raises(ProcessingReferenceError):
        repository.persist_decision(decision)


def test_superseding_decision_requires_same_source(
    repository: ProjectProcessingRepository,
    source_manifest,
    projects_root: Path,
    tmp_path: Path,
) -> None:
    first = _decision(source_manifest)
    repository.persist_decision(first)

    source_path = tmp_path / "context.txt"
    source_path.write_text("Context", encoding="utf-8")
    second_source = ProjectSourceRegistry(
        root=projects_root
    ).register_source(
        PROJECT_ID,
        source_path,
        source_role=ENGINEERING_SOURCE_ROLE,
    )
    successor = _decision(
        second_source,
        processing_decision_id="PD-000002",
        supersedes_processing_decision_id="PD-000001",
    )

    with pytest.raises(ProcessingReferenceError):
        repository.persist_decision(successor)


def test_next_decision_id_does_not_reuse_gaps(
    repository: ProjectProcessingRepository,
    projects_root: Path,
) -> None:
    root = projects_root / PROJECT_ID / "processing_decisions"
    root.mkdir()
    (root / "PD-000001.json").write_text("{}\n", encoding="utf-8")
    (root / "PD-000003.json").write_text("{}\n", encoding="utf-8")

    assert repository.next_decision_id(PROJECT_ID) == "PD-000004"


def test_prepare_attempt_directory_uses_canonical_layout(
    repository: ProjectProcessingRepository,
    projects_root: Path,
    source_manifest,
) -> None:
    _persist_initial_run(repository, source_manifest)

    created = repository.prepare_attempt_directory(
        PROJECT_ID,
        "RUN-000001",
        artifact_kind="agent_outputs",
        processing_stage="semantic_extraction",
        attempt_id="ATT-000001",
    )

    assert created == attempt_artifact_path(
        projects_root,
        PROJECT_ID,
        "RUN-000001",
        artifact_kind="agent_outputs",
        processing_stage="semantic_extraction",
        attempt_id="ATT-000001",
    )
    assert created.is_dir()


def test_prepare_attempt_directory_never_overwrites(
    repository: ProjectProcessingRepository,
    source_manifest,
) -> None:
    _persist_initial_run(repository, source_manifest)
    arguments = {
        "artifact_kind": "agent_outputs",
        "processing_stage": "semantic_extraction",
        "attempt_id": "ATT-000001",
    }
    repository.prepare_attempt_directory(
        PROJECT_ID,
        "RUN-000001",
        **arguments,
    )

    with pytest.raises(ProcessingPersistenceError):
        repository.prepare_attempt_directory(
            PROJECT_ID,
            "RUN-000001",
            **arguments,
        )


def test_next_attempt_id_considers_all_artifact_kinds(
    repository: ProjectProcessingRepository,
    source_manifest,
) -> None:
    _persist_initial_run(repository, source_manifest)
    repository.prepare_attempt_directory(
        PROJECT_ID,
        "RUN-000001",
        artifact_kind="agent_outputs",
        processing_stage="semantic_extraction",
        attempt_id="ATT-000001",
    )
    repository.prepare_attempt_directory(
        PROJECT_ID,
        "RUN-000001",
        artifact_kind="consensus_reports",
        processing_stage="semantic_extraction",
        attempt_id="ATT-000003",
    )

    assert repository.next_attempt_id(
        PROJECT_ID,
        "RUN-000001",
        "semantic_extraction",
    ) == "ATT-000004"


def test_work_directory_is_created_only_when_requested(
    repository: ProjectProcessingRepository,
    source_manifest,
) -> None:
    _persist_initial_run(repository, source_manifest)

    path = repository.work_directory(
        PROJECT_ID,
        "RUN-000001",
    )
    assert not path.exists()

    created = repository.work_directory(
        PROJECT_ID,
        "RUN-000001",
        create=True,
    )
    assert created.is_dir()


def test_scan_empty_processing_state(
    repository: ProjectProcessingRepository,
) -> None:
    scan = repository.scan_project(PROJECT_ID)

    assert scan.run_histories == ()
    assert scan.decisions == ()
    assert scan.issues == ()


def test_scan_returns_valid_runs_and_decisions(
    repository: ProjectProcessingRepository,
    source_manifest,
) -> None:
    history = _persist_initial_run(repository, source_manifest)
    decision = repository.persist_decision(
        _decision(source_manifest)
    )

    scan = repository.scan_project(PROJECT_ID)

    assert scan.run_histories == (history,)
    assert scan.decisions == (decision,)
    assert scan.issues == ()


def test_scan_reports_interrupted_run_creation(
    repository: ProjectProcessingRepository,
    projects_root: Path,
) -> None:
    temporary = (
        projects_root
        / PROJECT_ID
        / "runs"
        / ".create-RUN-000001.tmp"
    )
    temporary.parent.mkdir()
    temporary.mkdir()

    scan = repository.scan_project(PROJECT_ID)

    assert [issue.code for issue in scan.issues] == [
        "interrupted_run_creation"
    ]
    assert scan.issues[0].processing_run_id == "RUN-000001"


def test_scan_reports_corrupted_event_history(
    repository: ProjectProcessingRepository,
    projects_root: Path,
    source_manifest,
) -> None:
    history = _persist_initial_run(repository, source_manifest)
    event = _started_event(history.events[-1])
    repository.append_event(event)
    path = event_path(
        projects_root,
        PROJECT_ID,
        "RUN-000001",
        "EVT-000002",
    )
    serialized = path.read_text(encoding="utf-8")
    path.write_text(
        serialized.replace(
            event.previous_event_fingerprint,
            "f" * 64,
        ),
        encoding="utf-8",
    )

    scan = repository.scan_project(PROJECT_ID)

    assert scan.run_histories == ()
    assert len(scan.issues) == 1
    assert scan.issues[0].code in {
        "processing_integrity_error",
        "invalid_event_history",
    }


def test_scan_reports_invalid_decision_file(
    repository: ProjectProcessingRepository,
    projects_root: Path,
) -> None:
    root = projects_root / PROJECT_ID / "processing_decisions"
    root.mkdir()
    (root / "PD-000001.json").write_text("{}\n", encoding="utf-8")

    scan = repository.scan_project(PROJECT_ID)

    assert scan.decisions == ()
    assert len(scan.issues) == 1
    assert scan.issues[0].code == "invalid_processing_decision"


def test_load_run_rejects_symlink_directory(
    repository: ProjectProcessingRepository,
    projects_root: Path,
    tmp_path: Path,
) -> None:
    runs = projects_root / PROJECT_ID / "runs"
    runs.mkdir()
    target = tmp_path / "outside"
    target.mkdir()

    try:
        (runs / "RUN-000001").symlink_to(
            target,
            target_is_directory=True,
        )
    except (OSError, NotImplementedError):
        pytest.skip("Symbolic links are unavailable.")

    with pytest.raises(UnsafeProcessingPathError):
        repository.load_run(PROJECT_ID, "RUN-000001")