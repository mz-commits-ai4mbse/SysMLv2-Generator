"""Tests for validated Processing Run histories and state derivation."""

from dataclasses import replace

import pytest

from modules.project_processing.errors import (
    ProcessingEventChainError,
    ProcessingIntegrityError,
    ProcessingValidationError,
)
from modules.project_processing.event_manifest import (
    calculate_processing_event_fingerprint,
    create_processing_event,
)
from modules.project_processing.history import (
    create_processing_run_history,
    derive_processing_run_state,
    validate_processing_run_history,
)
from modules.project_processing.run_manifest import (
    create_processing_run_manifest,
    create_semantic_reference_version,
)
from modules.project_processing.types import (
    DerivedProcessingRunState,
    ProcessingRunHistory,
)


PROJECT_ID = "318604"
PROCESSING_RUN_ID = "RUN-000001"
SOURCE_ID = "SRC-000001"
SOURCE_SHA256 = "a" * 64
CONFIGURATION_FINGERPRINT = "b" * 64


def _manifest(**overrides):
    values = {
        "project_id": PROJECT_ID,
        "processing_run_id": PROCESSING_RUN_ID,
        "source_id": SOURCE_ID,
        "source_sha256": SOURCE_SHA256,
        "source_role_snapshot": "engineering_source",
        "workflow_profile": "engineering_source_processing",
        "configuration_fingerprint": CONFIGURATION_FINGERPRINT,
        "framework_template_id": "TURING_RFLP_FRAMEWORK",
        "framework_template_version": "1.0.0",
        "semantic_reference_versions": (
            create_semantic_reference_version(
                reference_system_id="BFO",
                reference_version="2020",
            ),
            create_semantic_reference_version(
                reference_system_id="IOF_CORE",
                reference_version="202602",
            ),
            create_semantic_reference_version(
                reference_system_id=(
                    "TURING_CORE_VOCABULARY"
                ),
                reference_version="1.0.0",
            ),
        ),
        "timestamp": "2026-07-25T10:00:00Z",
        "supersedes_run_id": None,
    }
    values.update(overrides)
    return create_processing_run_manifest(**values)


def _event(
    *,
    event_sequence,
    previous_event,
    previous_state,
    next_state,
    event_type,
    reason_code,
    processing_stage=None,
    attempt_id=None,
    project_id=PROJECT_ID,
    processing_run_id=PROCESSING_RUN_ID,
):
    return create_processing_event(
        project_id=project_id,
        processing_run_id=processing_run_id,
        event_id=f"EVT-{event_sequence:06d}",
        event_sequence=event_sequence,
        previous_state=previous_state,
        next_state=next_state,
        processing_stage=processing_stage,
        event_type=event_type,
        attempt_id=attempt_id,
        reason_code=reason_code,
        artifact_references=(),
        timestamp=(
            f"2026-07-25T10:{event_sequence - 1:02d}:00Z"
        ),
        previous_event_fingerprint=(
            None
            if previous_event is None
            else previous_event.event_fingerprint
        ),
    )


def _created_event(**overrides):
    values = {
        "event_sequence": 1,
        "previous_event": None,
        "previous_state": None,
        "next_state": "created",
        "event_type": "run_created",
        "reason_code": "run_created",
    }
    values.update(overrides)
    return _event(**values)


def _started_event(previous_event=None, **overrides):
    if previous_event is None:
        previous_event = _created_event()

    values = {
        "event_sequence": 2,
        "previous_event": previous_event,
        "previous_state": "created",
        "next_state": "running",
        "processing_stage": "source_projection",
        "event_type": "stage_started",
        "attempt_id": "ATT-000001",
        "reason_code": "source_projection_started",
    }
    values.update(overrides)
    return _event(**values)


def _review_requested_event(previous_event=None, **overrides):
    if previous_event is None:
        previous_event = _started_event()

    values = {
        "event_sequence": 3,
        "previous_event": previous_event,
        "previous_state": "running",
        "next_state": "awaiting_review",
        "processing_stage": "human_review",
        "event_type": "review_requested",
        "attempt_id": None,
        "reason_code": "human_review_required",
    }
    values.update(overrides)
    return _event(**values)


def _blocked_event(previous_event=None, **overrides):
    if previous_event is None:
        previous_event = _started_event()

    values = {
        "event_sequence": 3,
        "previous_event": previous_event,
        "previous_state": "running",
        "next_state": "blocked",
        "processing_stage": "source_projection",
        "event_type": "run_blocked",
        "attempt_id": None,
        "reason_code": "source_projection_unavailable",
    }
    values.update(overrides)
    return _event(**values)


def _failed_event(previous_event=None, **overrides):
    if previous_event is None:
        previous_event = _started_event()

    values = {
        "event_sequence": 3,
        "previous_event": previous_event,
        "previous_state": "running",
        "next_state": "failed",
        "processing_stage": "source_projection",
        "event_type": "run_failed",
        "attempt_id": None,
        "reason_code": "source_projection_validation_failed",
    }
    values.update(overrides)
    return _event(**values)


def test_create_processing_run_history_validates_created_run():
    manifest = _manifest()
    created = _created_event()

    history = create_processing_run_history(
        manifest=manifest,
        events=(created,),
    )

    assert history == ProcessingRunHistory(
        manifest=manifest,
        events=(created,),
    )
    assert validate_processing_run_history(history) is history


def test_derive_created_processing_run_state():
    history = create_processing_run_history(
        manifest=_manifest(),
        events=(_created_event(),),
    )

    state = derive_processing_run_state(history)

    assert state == DerivedProcessingRunState(
        project_id=PROJECT_ID,
        processing_run_id=PROCESSING_RUN_ID,
        source_id=SOURCE_ID,
        run_state="created",
        processing_stage=None,
        latest_attempt_id=None,
        latest_event_id="EVT-000001",
        superseded_by_run_id=None,
        blocked_reason=None,
        failure_reason=None,
        pending_review=False,
    )


def test_derive_running_processing_run_state():
    created = _created_event()
    started = _started_event(created)
    history = create_processing_run_history(
        manifest=_manifest(),
        events=(created, started),
    )

    state = derive_processing_run_state(history)

    assert state.run_state == "running"
    assert state.processing_stage == "source_projection"
    assert state.latest_attempt_id == "ATT-000001"
    assert state.latest_event_id == "EVT-000002"
    assert state.pending_review is False


def test_derive_awaiting_review_preserves_latest_attempt():
    created = _created_event()
    started = _started_event(created)
    review_requested = _review_requested_event(started)
    history = create_processing_run_history(
        manifest=_manifest(),
        events=(created, started, review_requested),
    )

    state = derive_processing_run_state(history)

    assert state.run_state == "awaiting_review"
    assert state.processing_stage == "human_review"
    assert state.latest_attempt_id == "ATT-000001"
    assert state.latest_event_id == "EVT-000003"
    assert state.pending_review is True


def test_derive_blocked_processing_run_state():
    created = _created_event()
    started = _started_event(created)
    blocked = _blocked_event(started)
    history = create_processing_run_history(
        manifest=_manifest(),
        events=(created, started, blocked),
    )

    state = derive_processing_run_state(history)

    assert state.run_state == "blocked"
    assert state.blocked_reason == (
        "source_projection_unavailable"
    )
    assert state.failure_reason is None
    assert state.pending_review is False


def test_derive_failed_processing_run_state():
    created = _created_event()
    started = _started_event(created)
    failed = _failed_event(started)
    history = create_processing_run_history(
        manifest=_manifest(),
        events=(created, started, failed),
    )

    state = derive_processing_run_state(history)

    assert state.run_state == "failed"
    assert state.blocked_reason is None
    assert state.failure_reason == (
        "source_projection_validation_failed"
    )
    assert state.pending_review is False


def test_processing_run_history_requires_expected_type():
    with pytest.raises(ProcessingValidationError):
        validate_processing_run_history(object())


def test_processing_run_history_requires_event_tuple():
    history = ProcessingRunHistory(
        manifest=_manifest(),
        events=[_created_event()],
    )

    with pytest.raises(ProcessingValidationError):
        validate_processing_run_history(history)


def test_processing_run_history_requires_at_least_one_event():
    history = ProcessingRunHistory(
        manifest=_manifest(),
        events=(),
    )

    with pytest.raises(ProcessingEventChainError):
        validate_processing_run_history(history)


def test_processing_run_history_rejects_project_mismatch():
    created = _created_event(project_id="999999")
    history = ProcessingRunHistory(
        manifest=_manifest(),
        events=(created,),
    )

    with pytest.raises(ProcessingEventChainError):
        validate_processing_run_history(history)


def test_processing_run_history_rejects_run_mismatch():
    created = _created_event(
        processing_run_id="RUN-000002",
    )
    history = ProcessingRunHistory(
        manifest=_manifest(),
        events=(created,),
    )

    with pytest.raises(ProcessingEventChainError):
        validate_processing_run_history(history)


def test_processing_run_history_rejects_non_contiguous_sequence():
    created = _created_event()
    third = _event(
        event_sequence=3,
        previous_event=created,
        previous_state="created",
        next_state="running",
        processing_stage="source_projection",
        event_type="stage_started",
        attempt_id="ATT-000001",
        reason_code="source_projection_started",
    )
    history = ProcessingRunHistory(
        manifest=_manifest(),
        events=(created, third),
    )

    with pytest.raises(ProcessingEventChainError):
        validate_processing_run_history(history)


def test_processing_run_history_rejects_reordered_events():
    created = _created_event()
    started = _started_event(created)
    history = ProcessingRunHistory(
        manifest=_manifest(),
        events=(started, created),
    )

    with pytest.raises(ProcessingEventChainError):
        validate_processing_run_history(history)


def test_processing_run_history_rejects_wrong_predecessor():
    created = _created_event()
    started = _started_event(created)
    started = replace(
        started,
        previous_event_fingerprint="f" * 64,
    )
    started = replace(
        started,
        event_fingerprint=(
            calculate_processing_event_fingerprint(started)
        ),
    )
    history = ProcessingRunHistory(
        manifest=_manifest(),
        events=(created, started),
    )

    with pytest.raises(ProcessingEventChainError):
        validate_processing_run_history(history)


def test_processing_run_history_rejects_state_discontinuity():
    created = _created_event()
    started = _started_event(created)
    third = _event(
        event_sequence=3,
        previous_event=started,
        previous_state="created",
        next_state="running",
        processing_stage="semantic_extraction",
        event_type="stage_started",
        attempt_id="ATT-000002",
        reason_code="semantic_extraction_started",
    )
    history = ProcessingRunHistory(
        manifest=_manifest(),
        events=(created, started, third),
    )

    with pytest.raises(ProcessingEventChainError):
        validate_processing_run_history(history)


def test_processing_run_history_rejects_invalid_event():
    created = replace(
        _created_event(),
        event_fingerprint="0" * 64,
    )
    history = ProcessingRunHistory(
        manifest=_manifest(),
        events=(created,),
    )

    with pytest.raises(ProcessingIntegrityError):
        validate_processing_run_history(history)


def test_derive_processing_run_state_validates_history():
    history = ProcessingRunHistory(
        manifest=_manifest(),
        events=(),
    )

    with pytest.raises(ProcessingEventChainError):
        derive_processing_run_state(history)