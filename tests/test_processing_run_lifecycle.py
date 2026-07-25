"""Tests for retry and supersession Processing Run contracts."""

from __future__ import annotations

from dataclasses import replace

import pytest

from modules.project_processing.errors import (
    InvalidProcessingTransitionError,
    ProcessingIntegrityError,
    ProcessingRecoveryRequiredError,
    ProcessingReferenceError,
    ProcessingValidationError,
)
from modules.project_processing.event_manifest import (
    create_processing_event,
)
from modules.project_processing.history import (
    create_processing_run_history,
)
from modules.project_processing.run_lifecycle import (
    MATERIAL_RUN_BINDING_FIELDS,
    create_retry_event,
    create_run_superseded_event,
    create_successor_initial_event,
    derive_project_run_states,
    derive_supersession_index,
    material_run_binding_changes,
    validate_successor_manifest,
)
from modules.project_processing.run_manifest import (
    create_processing_run_manifest,
    create_semantic_reference_version,
)
from modules.project_processing.types import ProcessingRunHistory

PROJECT_ID = "318604"
SOURCE_ID = "SRC-000001"
SHA_A = "a" * 64
SHA_B = "b" * 64
CONFIG_A = "c" * 64
CONFIG_B = "d" * 64


def manifest(
    run_id: str,
    *,
    source_id: str = SOURCE_ID,
    source_sha256: str = SHA_A,
    source_role_snapshot: str = "engineering_source",
    workflow_profile: str = "engineering_source_processing",
    configuration_fingerprint: str = CONFIG_A,
    framework_template_id: str = "TURING_RFLP_FRAMEWORK",
    framework_template_version: str = "1.0.0",
    semantic_version: str = "1.0.0",
    timestamp: str = "2026-07-25T10:00:00Z",
    supersedes_run_id: str | None = None,
    project_id: str = PROJECT_ID,
):
    return create_processing_run_manifest(
        project_id=project_id,
        processing_run_id=run_id,
        source_id=source_id,
        source_sha256=source_sha256,
        source_role_snapshot=source_role_snapshot,
        workflow_profile=workflow_profile,
        configuration_fingerprint=configuration_fingerprint,
        framework_template_id=framework_template_id,
        framework_template_version=framework_template_version,
        semantic_reference_versions=(
            create_semantic_reference_version(
                reference_system_id="PROJECT_GLOSSARY",
                reference_version=semantic_version,
            ),
        ),
        timestamp=timestamp,
        supersedes_run_id=supersedes_run_id,
    )


def initial_history(run_manifest):
    event = create_processing_event(
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
    return create_processing_run_history(
        manifest=run_manifest,
        events=(event,),
    )


def append_state(
    history: ProcessingRunHistory,
    *,
    next_state: str,
    event_type: str,
    timestamp: str,
    processing_stage: str | None = None,
    attempt_id: str | None = None,
    reason_code: str = "state_changed",
) -> ProcessingRunHistory:
    previous = history.events[-1]
    sequence = len(history.events) + 1
    event = create_processing_event(
        project_id=history.manifest.project_id,
        processing_run_id=history.manifest.processing_run_id,
        event_id=f"EVT-{sequence:06d}",
        event_sequence=sequence,
        previous_state=previous.next_state,
        next_state=next_state,
        processing_stage=processing_stage,
        event_type=event_type,
        attempt_id=attempt_id,
        reason_code=reason_code,
        artifact_references=(),
        timestamp=timestamp,
        previous_event_fingerprint=previous.event_fingerprint,
    )
    return create_processing_run_history(
        manifest=history.manifest,
        events=history.events + (event,),
    )


def successor_manifest(**overrides):
    values = {
        "run_id": "RUN-000002",
        "configuration_fingerprint": CONFIG_B,
        "timestamp": "2026-07-25T11:00:00Z",
        "supersedes_run_id": "RUN-000001",
    }
    values.update(overrides)
    return manifest(**values)


def completed_predecessor():
    history = initial_history(manifest("RUN-000001"))
    history = append_state(
        history,
        next_state="running",
        event_type="stage_started",
        processing_stage="source_projection",
        attempt_id="ATT-000001",
        timestamp="2026-07-25T10:10:00Z",
    )
    return append_state(
        history,
        next_state="completed",
        event_type="run_completed",
        timestamp="2026-07-25T10:30:00Z",
        reason_code="workflow_resolved",
    )


def superseded_pair():
    predecessor = completed_predecessor()
    successor = successor_manifest()
    superseded_event = create_run_superseded_event(
        predecessor,
        successor,
        reason_code="material_binding_changed",
        timestamp="2026-07-25T11:00:01Z",
    )
    predecessor = create_processing_run_history(
        manifest=predecessor.manifest,
        events=predecessor.events + (superseded_event,),
    )
    successor_history = initial_history(successor)
    return predecessor, successor_history


def test_material_binding_fields_are_explicit_and_stable() -> None:
    assert MATERIAL_RUN_BINDING_FIELDS == (
        "source_id",
        "source_sha256",
        "source_role_snapshot",
        "workflow_profile",
        "configuration_fingerprint",
        "framework_template_id",
        "framework_template_version",
        "semantic_reference_versions",
    )


@pytest.mark.parametrize(
    ("override", "expected_field"),
    [
        ({"source_id": "SRC-000002"}, "source_id"),
        ({"source_sha256": SHA_B}, "source_sha256"),
        (
            {
                "source_role_snapshot": "context_only",
                "workflow_profile": "context_only_processing",
            },
            "source_role_snapshot",
        ),
        (
            {
                "source_role_snapshot": "context_only",
                "workflow_profile": "context_only_processing",
            },
            "workflow_profile",
        ),
        ({"configuration_fingerprint": CONFIG_B}, "configuration_fingerprint"),
        ({"framework_template_id": "OTHER_FRAMEWORK"}, "framework_template_id"),
        ({"framework_template_version": "2.0.0"}, "framework_template_version"),
        ({"semantic_version": "2.0.0"}, "semantic_reference_versions"),
    ],
)
def test_material_binding_change_is_detected(override, expected_field) -> None:
    predecessor = manifest("RUN-000001")
    successor_values = {
        "run_id": "RUN-000002",
        "timestamp": "2026-07-25T11:00:00Z",
        "supersedes_run_id": "RUN-000001",
    }
    successor_values.update(override)
    successor = manifest(**successor_values)

    assert expected_field in material_run_binding_changes(
        predecessor,
        successor,
    )


def test_non_binding_identity_and_timestamp_changes_are_ignored() -> None:
    predecessor = manifest("RUN-000001")
    successor = manifest(
        "RUN-000002",
        timestamp="2026-07-25T11:00:00Z",
        supersedes_run_id="RUN-000001",
    )

    assert material_run_binding_changes(predecessor, successor) == ()


def test_successor_manifest_returns_changed_bindings() -> None:
    changed = validate_successor_manifest(
        manifest("RUN-000001"),
        successor_manifest(),
    )

    assert changed == ("configuration_fingerprint",)


def test_successor_must_reference_predecessor() -> None:
    with pytest.raises(ProcessingReferenceError):
        validate_successor_manifest(
            manifest("RUN-000001"),
            successor_manifest(supersedes_run_id="RUN-000009"),
        )


def test_successor_must_remain_project_local() -> None:
    with pytest.raises(ProcessingReferenceError):
        validate_successor_manifest(
            manifest("RUN-000001"),
            successor_manifest(project_id="481516"),
        )


def test_successor_requires_later_timestamp() -> None:
    with pytest.raises(ProcessingValidationError):
        validate_successor_manifest(
            manifest("RUN-000001"),
            successor_manifest(timestamp="2026-07-25T10:00:00Z"),
        )


def test_unchanged_bindings_require_retry_not_successor() -> None:
    with pytest.raises(ProcessingValidationError):
        validate_successor_manifest(
            manifest("RUN-000001"),
            successor_manifest(configuration_fingerprint=CONFIG_A),
        )


def test_create_retry_event_uses_next_identity_and_attempt() -> None:
    history = initial_history(manifest("RUN-000001"))

    event = create_retry_event(
        history,
        processing_stage="semantic_extraction",
        attempt_id="ATT-000002",
        reason_code="review_changes_requested",
        timestamp="2026-07-25T10:20:00Z",
    )

    assert event.event_id == "EVT-000002"
    assert event.event_sequence == 2
    assert event.previous_state == "created"
    assert event.next_state == "running"
    assert event.event_type == "retry_started"
    assert event.processing_stage == "semantic_extraction"
    assert event.attempt_id == "ATT-000002"
    assert event.previous_event_fingerprint == history.events[-1].event_fingerprint


def test_retry_rejects_unsupported_stage() -> None:
    with pytest.raises(ProcessingValidationError):
        create_retry_event(
            initial_history(manifest("RUN-000001")),
            processing_stage="unknown",
            attempt_id="ATT-000001",
            reason_code="retry_requested",
            timestamp="2026-07-25T10:20:00Z",
        )


def test_completed_run_cannot_retry() -> None:
    with pytest.raises(InvalidProcessingTransitionError):
        create_retry_event(
            completed_predecessor(),
            processing_stage="semantic_extraction",
            attempt_id="ATT-000002",
            reason_code="retry_requested",
            timestamp="2026-07-25T10:40:00Z",
        )


def test_successor_initial_event_matches_manifest() -> None:
    successor = successor_manifest()

    event = create_successor_initial_event(successor)

    assert event.processing_run_id == successor.processing_run_id
    assert event.event_id == "EVT-000001"
    assert event.next_state == "created"
    assert event.occurred_at == successor.created_at


def test_initial_event_requires_successor_manifest() -> None:
    with pytest.raises(ProcessingValidationError):
        create_successor_initial_event(manifest("RUN-000001"))


def test_run_superseded_event_closes_predecessor() -> None:
    predecessor = completed_predecessor()

    event = create_run_superseded_event(
        predecessor,
        successor_manifest(),
        reason_code="material_binding_changed",
        timestamp="2026-07-25T11:00:01Z",
    )

    assert event.event_id == "EVT-000004"
    assert event.previous_state == "completed"
    assert event.next_state == "superseded"
    assert event.event_type == "run_superseded"


def test_run_cannot_be_superseded_twice() -> None:
    predecessor, successor = superseded_pair()

    with pytest.raises(ProcessingIntegrityError):
        create_run_superseded_event(
            predecessor,
            successor.manifest,
            reason_code="second_successor",
            timestamp="2026-07-25T12:00:00Z",
        )


def test_complete_supersession_pair_builds_index() -> None:
    predecessor, successor = superseded_pair()

    assert derive_supersession_index((predecessor, successor)) == {
        "RUN-000001": "RUN-000002"
    }


def test_derived_state_contains_successor_id() -> None:
    predecessor, successor = superseded_pair()

    states = derive_project_run_states((successor, predecessor))

    assert tuple(state.processing_run_id for state in states) == (
        "RUN-000001",
        "RUN-000002",
    )
    assert states[0].run_state == "superseded"
    assert states[0].superseded_by_run_id == "RUN-000002"
    assert states[1].superseded_by_run_id is None


def test_successor_without_predecessor_event_requires_recovery() -> None:
    predecessor = completed_predecessor()
    successor = initial_history(successor_manifest())

    with pytest.raises(ProcessingRecoveryRequiredError):
        derive_supersession_index((predecessor, successor))


def test_superseded_predecessor_without_successor_requires_recovery() -> None:
    predecessor, _ = superseded_pair()

    with pytest.raises(ProcessingRecoveryRequiredError):
        derive_supersession_index((predecessor,))


def test_unavailable_predecessor_requires_recovery() -> None:
    successor = initial_history(successor_manifest())

    with pytest.raises(ProcessingRecoveryRequiredError):
        derive_supersession_index((successor,))


def test_multiple_successors_are_rejected() -> None:
    predecessor, successor = superseded_pair()
    second_successor = initial_history(
        successor_manifest(
            run_id="RUN-000003",
            configuration_fingerprint="e" * 64,
            timestamp="2026-07-25T12:00:00Z",
        )
    )

    with pytest.raises(ProcessingIntegrityError):
        derive_supersession_index(
            (predecessor, successor, second_successor)
        )


def test_duplicate_run_identity_is_rejected() -> None:
    history = initial_history(manifest("RUN-000001"))

    with pytest.raises(ProcessingIntegrityError):
        derive_supersession_index((history, history))


def test_cross_project_history_collection_is_rejected() -> None:
    first = initial_history(manifest("RUN-000001"))
    second = initial_history(
        manifest("RUN-000002", project_id="481516")
    )

    with pytest.raises(ProcessingReferenceError):
        derive_supersession_index((first, second))


def test_histories_must_be_tuple() -> None:
    with pytest.raises(ProcessingValidationError):
        derive_supersession_index([])


def test_empty_history_collection_is_valid() -> None:
    assert derive_supersession_index(()) == {}
    assert derive_project_run_states(()) == ()


def test_cycle_is_rejected_even_when_manifests_are_tampered() -> None:
    first = initial_history(manifest("RUN-000001"))
    second = initial_history(successor_manifest())

    first_manifest = replace(
        first.manifest,
        supersedes_run_id="RUN-000002",
        configuration_fingerprint="e" * 64,
        created_at="2026-07-25T12:00:00Z",
    )
    first = ProcessingRunHistory(
        manifest=first_manifest,
        events=first.events,
    )

    with pytest.raises((ProcessingIntegrityError, ProcessingValidationError)):
        derive_supersession_index((first, second))