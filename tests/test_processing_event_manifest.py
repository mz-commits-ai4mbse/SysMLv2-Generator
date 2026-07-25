"""Tests for immutable Processing Event Manifests."""

from dataclasses import replace
import json

import pytest

from modules.project_processing.errors import (
    InvalidProcessingTransitionError,
    ProcessingEventChainError,
    ProcessingIntegrityError,
    ProcessingValidationError,
)
from modules.project_processing.event_manifest import (
    calculate_processing_event_fingerprint,
    create_processing_artifact_reference,
    create_processing_event,
    parse_processing_event,
    processing_event_filename,
    processing_event_from_json,
    processing_event_to_dict,
    processing_event_to_json,
    validate_processing_artifact_reference,
    validate_processing_event,
)


PROJECT_ID = "318604"
PROCESSING_RUN_ID = "RUN-000001"
SOURCE_PROJECTION_PATH = (
    "data/projects/318604/"
    "semantics/source_projections/SRC-000001.json"
)


def _artifact_reference(**overrides):
    values = {
        "artifact_type": "source_projection",
        "artifact_id": "SP-000001",
        "content_fingerprint": "c" * 64,
        "repository_relative_path": SOURCE_PROJECTION_PATH,
    }
    values.update(overrides)
    return create_processing_artifact_reference(**values)


def _run_created_event(**overrides):
    values = {
        "project_id": PROJECT_ID,
        "processing_run_id": PROCESSING_RUN_ID,
        "event_id": "EVT-000001",
        "event_sequence": 1,
        "previous_state": None,
        "next_state": "created",
        "processing_stage": None,
        "event_type": "run_created",
        "attempt_id": None,
        "reason_code": "run_created",
        "artifact_references": (),
        "timestamp": "2026-07-25T10:00:00Z",
        "previous_event_fingerprint": None,
    }
    values.update(overrides)
    return create_processing_event(**values)


def _stage_started_event(
    previous_event=None,
    **overrides,
):
    if previous_event is None:
        previous_event = _run_created_event()

    values = {
        "project_id": PROJECT_ID,
        "processing_run_id": PROCESSING_RUN_ID,
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


def _stage_completed_event(
    previous_event=None,
    **overrides,
):
    if previous_event is None:
        previous_event = _stage_started_event()

    values = {
        "project_id": PROJECT_ID,
        "processing_run_id": PROCESSING_RUN_ID,
        "event_id": "EVT-000003",
        "event_sequence": 3,
        "previous_state": "running",
        "next_state": "running",
        "processing_stage": "source_projection",
        "event_type": "stage_completed",
        "attempt_id": "ATT-000001",
        "reason_code": "source_projection_completed",
        "artifact_references": (_artifact_reference(),),
        "timestamp": "2026-07-25T10:02:00Z",
        "previous_event_fingerprint": (
            previous_event.event_fingerprint
        ),
    }
    values.update(overrides)
    return create_processing_event(**values)


def test_create_processing_artifact_reference():
    reference = _artifact_reference()

    assert reference.artifact_type == "source_projection"
    assert reference.artifact_id == "SP-000001"
    assert reference.content_fingerprint == "c" * 64
    assert reference.repository_relative_path == SOURCE_PROJECTION_PATH


def test_create_initial_run_created_event():
    event = _run_created_event()

    assert event.schema_version == "1.0.0"
    assert event.project_id == PROJECT_ID
    assert event.processing_run_id == PROCESSING_RUN_ID
    assert event.event_id == "EVT-000001"
    assert event.event_sequence == 1
    assert event.previous_state is None
    assert event.next_state == "created"
    assert event.processing_stage is None
    assert event.event_type == "run_created"
    assert event.attempt_id is None
    assert event.reason_code == "run_created"
    assert event.artifact_references == ()
    assert event.previous_event_fingerprint is None
    assert len(event.event_fingerprint) == 64


def test_create_subsequent_stage_started_event():
    created_event = _run_created_event()
    event = _stage_started_event(created_event)

    assert event.event_id == "EVT-000002"
    assert event.event_sequence == 2
    assert event.previous_state == "created"
    assert event.next_state == "running"
    assert event.processing_stage == "source_projection"
    assert event.event_type == "stage_started"
    assert event.attempt_id == "ATT-000001"
    assert (
        event.previous_event_fingerprint
        == created_event.event_fingerprint
    )


def test_create_stage_completed_event_with_artifact():
    started_event = _stage_started_event()
    event = _stage_completed_event(started_event)

    assert event.previous_state == "running"
    assert event.next_state == "running"
    assert event.event_type == "stage_completed"
    assert event.processing_stage == "source_projection"
    assert event.attempt_id == "ATT-000001"
    assert event.artifact_references == (_artifact_reference(),)
    assert (
        event.previous_event_fingerprint
        == started_event.event_fingerprint
    )


def test_processing_event_round_trip_is_lossless():
    event = _stage_completed_event()

    document = processing_event_to_json(event)
    parsed = processing_event_from_json(document)

    assert parsed == event


def test_processing_event_dictionary_round_trip():
    event = _stage_completed_event()

    payload = processing_event_to_dict(event)
    parsed = parse_processing_event(payload)

    assert parsed == event


def test_processing_event_json_is_deterministic():
    event = _stage_completed_event()

    first = processing_event_to_json(event)
    second = processing_event_to_json(event)

    assert first == second
    assert first.endswith("\n")


def test_processing_event_filename():
    assert processing_event_filename("EVT-000001") == "EVT-000001.json"
    assert processing_event_filename("EVT-999999") == "EVT-999999.json"


@pytest.mark.parametrize(
    "event_id",
    [
        "",
        "EVT-000000",
        "EVT-1",
        "evt-000001",
        "RUN-000001",
    ],
)
def test_processing_event_filename_rejects_invalid_id(event_id):
    with pytest.raises(ProcessingValidationError):
        processing_event_filename(event_id)


def test_processing_event_fingerprint_is_stable_sha256():
    event = _stage_completed_event()

    first = calculate_processing_event_fingerprint(event)
    second = calculate_processing_event_fingerprint(event)

    assert first == event.event_fingerprint
    assert first == second
    assert len(first) == 64
    assert set(first) <= set("0123456789abcdef")


def test_processing_event_fingerprint_changes_with_event_content():
    event = _stage_completed_event()
    changed = replace(
        event,
        reason_code="different_reason",
    )

    assert (
        calculate_processing_event_fingerprint(event)
        != calculate_processing_event_fingerprint(changed)
    )


def test_validate_processing_event_rejects_tampered_fingerprint():
    event = replace(
        _stage_completed_event(),
        event_fingerprint="0" * 64,
    )

    with pytest.raises(ProcessingIntegrityError):
        validate_processing_event(event)


@pytest.mark.parametrize(
    ("field_name", "invalid_value"),
    [
        ("project_id", ""),
        ("project_id", "31860"),
        ("processing_run_id", ""),
        ("processing_run_id", "RUN-000000"),
        ("processing_run_id", "RUN-1"),
        ("event_id", ""),
        ("event_id", "EVT-000000"),
        ("event_id", "EVT-1"),
        ("event_sequence", 0),
        ("event_sequence", -1),
        ("event_sequence", True),
        ("reason_code", ""),
        ("reason_code", " "),
        ("reason_code", " reason"),
        ("occurred_at", ""),
        ("occurred_at", "2026-07-25"),
        ("occurred_at", "2026-07-25T10:00:00"),
        ("occurred_at", "not-a-timestamp"),
    ],
)
def test_processing_event_rejects_invalid_common_field(
    field_name,
    invalid_value,
):
    event = _stage_completed_event()
    invalid_event = replace(
        event,
        **{field_name: invalid_value},
    )

    with pytest.raises(
        (
            ProcessingValidationError,
            ProcessingIntegrityError,
        )
    ):
        validate_processing_event(invalid_event)


def test_event_sequence_must_match_event_identifier():
    event = replace(
        _stage_completed_event(),
        event_sequence=4,
    )

    with pytest.raises(ProcessingValidationError):
        validate_processing_event(event)


def test_initial_event_must_be_evt_000001():
    with pytest.raises(ProcessingEventChainError):
        _run_created_event(
            event_id="EVT-000002",
            event_sequence=2,
        )


def test_initial_event_must_not_have_previous_event_fingerprint():
    with pytest.raises(ProcessingEventChainError):
        _run_created_event(
            previous_event_fingerprint="a" * 64,
        )


def test_initial_event_must_not_have_previous_state():
    with pytest.raises(ProcessingEventChainError):
        _run_created_event(previous_state="created")


def test_initial_event_must_be_run_created():
    with pytest.raises(ProcessingValidationError):
        _run_created_event(event_type="stage_started")


def test_initial_event_must_transition_to_created():
    with pytest.raises(InvalidProcessingTransitionError):
        _run_created_event(next_state="running")


def test_subsequent_event_requires_previous_event_fingerprint():
    with pytest.raises(ProcessingEventChainError):
        _stage_started_event(
            previous_event_fingerprint=None,
        )


def test_subsequent_event_requires_previous_state():
    with pytest.raises(ProcessingEventChainError):
        _stage_started_event(previous_state=None)


def test_subsequent_event_rejects_invalid_previous_fingerprint():
    with pytest.raises(ProcessingEventChainError):
        _stage_started_event(
            previous_event_fingerprint="a" * 63,
        )


def test_run_created_is_not_valid_as_subsequent_event():
    with pytest.raises(ProcessingValidationError):
        _stage_started_event(
            event_type="run_created",
        )


@pytest.mark.parametrize(
    ("previous_state", "next_state", "event_type"),
    [
        ("created", "completed", "run_completed"),
        ("completed", "running", "stage_started"),
        ("completed", "failed", "run_failed"),
        ("superseded", "running", "stage_started"),
        ("superseded", "completed", "run_completed"),
    ],
)
def test_processing_event_rejects_invalid_state_transition(
    previous_state,
    next_state,
    event_type,
):
    with pytest.raises(InvalidProcessingTransitionError):
        _stage_started_event(
            previous_state=previous_state,
            next_state=next_state,
            event_type=event_type,
        )


def test_stage_started_requires_processing_stage():
    with pytest.raises(ProcessingValidationError):
        _stage_started_event(processing_stage=None)


def test_stage_started_requires_attempt_id():
    with pytest.raises(ProcessingValidationError):
        _stage_started_event(attempt_id=None)


@pytest.mark.parametrize(
    "processing_stage",
    [
        "",
        "SOURCE_PROJECTION",
        "unknown_stage",
    ],
)
def test_event_rejects_invalid_processing_stage(processing_stage):
    with pytest.raises(ProcessingValidationError):
        _stage_started_event(
            processing_stage=processing_stage,
        )


@pytest.mark.parametrize(
    "attempt_id",
    [
        "",
        "ATT-000000",
        "ATT-1",
        "att-000001",
    ],
)
def test_event_rejects_invalid_attempt_id(attempt_id):
    with pytest.raises(ProcessingValidationError):
        _stage_started_event(attempt_id=attempt_id)


def test_run_created_rejects_processing_stage():
    with pytest.raises(ProcessingValidationError):
        _run_created_event(
            processing_stage="source_projection",
        )


def test_run_created_rejects_attempt_id():
    with pytest.raises(ProcessingValidationError):
        _run_created_event(attempt_id="ATT-000001")


def test_run_created_rejects_artifact_references():
    with pytest.raises(ProcessingValidationError):
        _run_created_event(
            artifact_references=(_artifact_reference(),),
        )


def test_artifact_references_must_be_tuple():
    event = replace(
        _stage_completed_event(),
        artifact_references=[_artifact_reference()],
    )

    with pytest.raises(ProcessingValidationError):
        validate_processing_event(event)


def test_artifact_references_must_contain_expected_type():
    event = replace(
        _stage_completed_event(),
        artifact_references=("SP-000001",),
    )

    with pytest.raises(ProcessingValidationError):
        validate_processing_event(event)


@pytest.mark.parametrize(
    ("field_name", "invalid_value"),
    [
        ("artifact_type", ""),
        ("artifact_type", " "),
        ("artifact_type", "Source Projection"),
        ("artifact_id", ""),
        ("artifact_id", " "),
        ("content_fingerprint", ""),
        ("content_fingerprint", "c" * 63),
        ("content_fingerprint", "C" * 64),
        ("content_fingerprint", "z" * 64),
        ("repository_relative_path", ""),
        ("repository_relative_path", " "),
        ("repository_relative_path", "/absolute/path.json"),
        (
            "repository_relative_path",
            "../outside-project.json",
        ),
        (
            "repository_relative_path",
            "data/projects/318604/../outside.json",
        ),
        (
            "repository_relative_path",
            r"data\projects\318604\artifact.json",
        ),
    ],
)
def test_processing_artifact_reference_rejects_invalid_field(
    field_name,
    invalid_value,
):
    reference = _artifact_reference()
    invalid_reference = replace(
        reference,
        **{field_name: invalid_value},
    )

    with pytest.raises(ProcessingValidationError):
        validate_processing_artifact_reference(invalid_reference)


def test_repository_relative_path_accepts_nested_posix_path():
    reference = _artifact_reference(
        repository_relative_path=(
            "data/projects/318604/runs/RUN-000001/"
            "artifacts/agent_outputs/source_projection/"
            "ATT-000001/output.json"
        )
    )

    validate_processing_artifact_reference(reference)


def test_parse_processing_event_rejects_unknown_field():
    payload = processing_event_to_dict(_stage_completed_event())
    payload["unexpected_field"] = "unexpected"

    with pytest.raises(ProcessingValidationError):
        parse_processing_event(payload)


@pytest.mark.parametrize(
    "field_name",
    [
        "schema_version",
        "project_id",
        "processing_run_id",
        "event_id",
        "event_sequence",
        "previous_state",
        "next_state",
        "processing_stage",
        "event_type",
        "attempt_id",
        "reason_code",
        "artifact_references",
        "occurred_at",
        "previous_event_fingerprint",
        "event_fingerprint",
    ],
)
def test_parse_processing_event_rejects_missing_field(field_name):
    payload = processing_event_to_dict(_stage_completed_event())
    del payload[field_name]

    with pytest.raises(ProcessingValidationError):
        parse_processing_event(payload)


def test_parse_processing_event_rejects_wrong_schema_version():
    payload = processing_event_to_dict(_stage_completed_event())
    payload["schema_version"] = "2.0.0"

    with pytest.raises(ProcessingValidationError):
        parse_processing_event(payload)


def test_processing_event_from_json_rejects_invalid_json():
    with pytest.raises(ProcessingValidationError):
        processing_event_from_json("{not valid json}")


def test_processing_event_from_json_rejects_non_object():
    with pytest.raises(ProcessingValidationError):
        processing_event_from_json("[]")


def test_processing_event_from_json_rejects_duplicate_keys():
    payload = processing_event_to_dict(_stage_completed_event())
    document = json.dumps(payload)
    duplicate_document = (
        document[:-1]
        + f', "event_id": "{payload["event_id"]}"'
        + "}"
    )

    with pytest.raises(ProcessingValidationError):
        processing_event_from_json(duplicate_document)


def test_processing_event_from_json_rejects_tampered_content():
    payload = processing_event_to_dict(_stage_completed_event())
    payload["reason_code"] = "tampered_reason"

    with pytest.raises(ProcessingIntegrityError):
        processing_event_from_json(json.dumps(payload))