"""Create, validate and serialize immutable Processing Events."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime
import hashlib
import json
from pathlib import PurePosixPath
import re
from typing import Any

from modules.project_workspace.identifiers import (
    is_valid_project_id,
)

from .errors import (
    InvalidProcessingTransitionError,
    ProcessingEventChainError,
    ProcessingIntegrityError,
    ProcessingValidationError,
)
from .identifiers import (
    processing_event_id_sequence,
    validate_processing_attempt_id,
    validate_processing_event_id,
    validate_processing_run_id,
)
from .types import (
    PROCESSING_EVENT_TYPES,
    PROCESSING_RUN_STATES,
    PROCESSING_STAGES,
    ProcessingArtifactReference,
    ProcessingEvent,
)


PROCESSING_EVENT_SCHEMA_VERSION = "1.0.0"

_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_REASON_CODE_PATTERN = re.compile(
    r"^[a-z][a-z0-9_]{0,119}$"
)
_ARTIFACT_TYPE_PATTERN = re.compile(
    r"^[a-z][a-z0-9_]{0,119}$"
)
_ARTIFACT_ID_PATTERN = re.compile(
    r"^[A-Za-z][A-Za-z0-9._-]{0,119}$"
)
_UTC_TIMESTAMP_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T"
    r"\d{2}:\d{2}:\d{2}"
    r"(?:\.\d+)?Z$"
)

_EVENT_FIELDS = frozenset(
    {
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
    }
)

_ARTIFACT_REFERENCE_FIELDS = frozenset(
    {
        "artifact_type",
        "artifact_id",
        "content_fingerprint",
        "repository_relative_path",
    }
)

_ALLOWED_TRANSITIONS = {
    None: frozenset(
        {
            "created",
        }
    ),
    "created": frozenset(
        {
            "running",
            "blocked",
            "failed",
            "superseded",
        }
    ),
    "running": frozenset(
        {
            "running",
            "awaiting_review",
            "blocked",
            "failed",
            "completed",
            "superseded",
        }
    ),
    "awaiting_review": frozenset(
        {
            "awaiting_review",
            "running",
            "completed",
            "blocked",
            "superseded",
        }
    ),
    "blocked": frozenset(
        {
            "blocked",
            "running",
            "failed",
            "superseded",
        }
    ),
    "failed": frozenset(
        {
            "failed",
            "running",
            "superseded",
        }
    ),
    "completed": frozenset(
        {
            "superseded",
        }
    ),
    "superseded": frozenset(),
}


def create_processing_artifact_reference(
    *,
    artifact_type: str,
    artifact_id: str,
    content_fingerprint: str,
    repository_relative_path: str,
) -> ProcessingArtifactReference:
    """Create and validate one exact artifact reference."""

    reference = ProcessingArtifactReference(
        artifact_type=artifact_type,
        artifact_id=artifact_id,
        content_fingerprint=content_fingerprint,
        repository_relative_path=repository_relative_path,
    )

    validate_processing_artifact_reference(reference)

    return reference


def create_processing_event(
    *,
    project_id: str,
    processing_run_id: str,
    event_id: str,
    event_sequence: int,
    previous_state: str | None,
    next_state: str,
    processing_stage: str | None,
    event_type: str,
    attempt_id: str | None,
    reason_code: str,
    artifact_references: tuple[
        ProcessingArtifactReference,
        ...
    ],
    timestamp: str,
    previous_event_fingerprint: str | None,
) -> ProcessingEvent:
    """Create one fingerprinted immutable Processing Event."""

    provisional_event = ProcessingEvent(
        schema_version=PROCESSING_EVENT_SCHEMA_VERSION,
        project_id=project_id,
        processing_run_id=processing_run_id,
        event_id=event_id,
        event_sequence=event_sequence,
        previous_state=previous_state,
        next_state=next_state,
        processing_stage=processing_stage,
        event_type=event_type,
        attempt_id=attempt_id,
        reason_code=reason_code,
        artifact_references=artifact_references,
        occurred_at=timestamp,
        previous_event_fingerprint=(
            previous_event_fingerprint
        ),
        event_fingerprint="0" * 64,
    )

    _validate_processing_event(
        provisional_event,
        verify_fingerprint=False,
    )

    fingerprint = calculate_processing_event_fingerprint(
        provisional_event
    )

    event = replace(
        provisional_event,
        event_fingerprint=fingerprint,
    )

    validate_processing_event(event)

    return event


def parse_processing_event(
    payload: object,
) -> ProcessingEvent:
    """Parse and validate one Processing Event mapping."""

    if not isinstance(payload, dict):
        raise ProcessingValidationError(
            "Processing Event must be a JSON object."
        )

    _require_exact_fields(
        payload,
        expected_fields=_EVENT_FIELDS,
        label="Processing Event",
    )

    artifact_payloads = payload["artifact_references"]

    if not isinstance(artifact_payloads, list):
        raise ProcessingValidationError(
            "artifact_references must be a JSON array."
        )

    artifact_references = tuple(
        _parse_processing_artifact_reference(item)
        for item in artifact_payloads
    )

    event = ProcessingEvent(
        schema_version=payload["schema_version"],
        project_id=payload["project_id"],
        processing_run_id=payload["processing_run_id"],
        event_id=payload["event_id"],
        event_sequence=payload["event_sequence"],
        previous_state=payload["previous_state"],
        next_state=payload["next_state"],
        processing_stage=payload["processing_stage"],
        event_type=payload["event_type"],
        attempt_id=payload["attempt_id"],
        reason_code=payload["reason_code"],
        artifact_references=artifact_references,
        occurred_at=payload["occurred_at"],
        previous_event_fingerprint=payload[
            "previous_event_fingerprint"
        ],
        event_fingerprint=payload["event_fingerprint"],
    )

    validate_processing_event(event)

    return event


def processing_event_from_json(
    text: object,
) -> ProcessingEvent:
    """Parse one Processing Event from strict JSON."""

    if not isinstance(text, str):
        raise ProcessingValidationError(
            "Processing Event JSON must be a string."
        )

    try:
        payload = json.loads(
            text,
            object_pairs_hook=_object_without_duplicate_keys,
        )
    except ProcessingValidationError:
        raise
    except json.JSONDecodeError as exc:
        raise ProcessingValidationError(
            "Processing Event is not valid JSON."
        ) from exc

    return parse_processing_event(payload)


def processing_event_to_dict(
    event: ProcessingEvent,
) -> dict[str, object]:
    """Serialize one validated Processing Event."""

    validate_processing_event(event)

    return _processing_event_payload(
        event,
        include_fingerprint=True,
    )


def processing_event_to_json(
    event: ProcessingEvent,
) -> str:
    """Serialize one Processing Event as deterministic JSON."""

    return (
        json.dumps(
            processing_event_to_dict(event),
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )


def processing_event_filename(event_id: object) -> str:
    """Return the canonical filename for one Processing Event."""

    validated_event_id = validate_processing_event_id(
        event_id
    )

    return f"{validated_event_id}.json"


def calculate_processing_event_fingerprint(
    event: ProcessingEvent,
) -> str:
    """Calculate the deterministic fingerprint of one event."""

    _validate_processing_event(
        event,
        verify_fingerprint=False,
    )

    payload = _processing_event_payload(
        event,
        include_fingerprint=False,
    )

    canonical_json = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )

    return hashlib.sha256(
        canonical_json.encode("utf-8")
    ).hexdigest()


def validate_processing_event(
    event: object,
) -> ProcessingEvent:
    """Validate and return one immutable Processing Event."""

    return _validate_processing_event(
        event,
        verify_fingerprint=True,
    )


def validate_processing_artifact_reference(
    reference: object,
) -> ProcessingArtifactReference:
    """Validate and return one artifact reference."""

    if not isinstance(reference, ProcessingArtifactReference):
        raise ProcessingValidationError(
            "artifact reference must be a "
            "ProcessingArtifactReference."
        )

    if (
        not isinstance(reference.artifact_type, str)
        or _ARTIFACT_TYPE_PATTERN.fullmatch(
            reference.artifact_type
        )
        is None
    ):
        raise ProcessingValidationError(
            "artifact_type must be a lowercase identifier."
        )

    if (
        not isinstance(reference.artifact_id, str)
        or _ARTIFACT_ID_PATTERN.fullmatch(
            reference.artifact_id
        )
        is None
    ):
        raise ProcessingValidationError(
            "artifact_id contains unsupported characters."
        )

    _validate_sha256(
        reference.content_fingerprint,
        label="content_fingerprint",
    )

    _validate_repository_relative_path(
        reference.repository_relative_path
    )

    return reference


def validate_processing_transition(
    previous_state: str | None,
    next_state: object,
) -> str:
    """Validate one canonical Processing Run transition."""

    if previous_state is not None:
        if previous_state not in PROCESSING_RUN_STATES:
            raise InvalidProcessingTransitionError(
                "previous_state is not a supported Run state."
            )

    if next_state not in PROCESSING_RUN_STATES:
        raise InvalidProcessingTransitionError(
            "next_state is not a supported Run state."
        )

    permitted_next_states = _ALLOWED_TRANSITIONS[
        previous_state
    ]

    if next_state not in permitted_next_states:
        raise InvalidProcessingTransitionError(
            "Processing transition is not permitted: "
            f"{previous_state!r} -> {next_state!r}."
        )

    return next_state


def _validate_processing_event(
    event: object,
    *,
    verify_fingerprint: bool,
) -> ProcessingEvent:
    """Validate one event with optional fingerprint checking."""

    if not isinstance(event, ProcessingEvent):
        raise ProcessingValidationError(
            "event must be a ProcessingEvent."
        )

    if event.schema_version != PROCESSING_EVENT_SCHEMA_VERSION:
        raise ProcessingValidationError(
            "Unsupported Processing Event schema_version: "
            f"{event.schema_version!r}."
        )

    if not is_valid_project_id(event.project_id):
        raise ProcessingValidationError(
            "project_id must match ^[0-9]{6}$."
        )

    try:
        validate_processing_run_id(
            event.processing_run_id
        )
        validate_processing_event_id(event.event_id)
    except Exception as exc:
        raise ProcessingValidationError(
            "Processing Event identity is invalid."
        ) from exc

    if (
        isinstance(event.event_sequence, bool)
        or not isinstance(event.event_sequence, int)
        or event.event_sequence < 1
        or event.event_sequence > 999_999
    ):
        raise ProcessingValidationError(
            "event_sequence must be an integer between "
            "1 and 999999."
        )

    if (
        processing_event_id_sequence(event.event_id)
        != event.event_sequence
    ):
        raise ProcessingValidationError(
            "event_sequence must match the sequence encoded "
            "by event_id."
        )

    _validate_event_position_contract(event)

    validate_processing_transition(
        event.previous_state,
        event.next_state,
    )

    if event.processing_stage is not None:
        if event.processing_stage not in PROCESSING_STAGES:
            raise ProcessingValidationError(
                "processing_stage is not supported."
            )

    if event.event_type not in PROCESSING_EVENT_TYPES:
        raise ProcessingValidationError(
            "event_type is not supported."
        )

    if event.attempt_id is not None:
        try:
            validate_processing_attempt_id(
                event.attempt_id
            )
        except Exception as exc:
            raise ProcessingValidationError(
                "attempt_id is invalid."
            ) from exc

    _validate_reason_code(event.reason_code)

    _validate_artifact_references(
        event.artifact_references
    )

    _validate_utc_timestamp(
        event.occurred_at,
        label="occurred_at",
    )

    _validate_event_type_contract(event)

    if verify_fingerprint:
        _validate_sha256(
            event.event_fingerprint,
            label="event_fingerprint",
        )

        expected_fingerprint = (
            calculate_processing_event_fingerprint(event)
        )

        if event.event_fingerprint != expected_fingerprint:
            raise ProcessingIntegrityError(
                "event_fingerprint does not match the "
                "Processing Event content."
            )

    return event


def _validate_event_position_contract(
    event: ProcessingEvent,
) -> None:
    """Validate first-event and predecessor-fingerprint rules."""

    if event.event_sequence == 1:
        if event.event_id != "EVT-000001":
            raise ProcessingEventChainError(
                "The first Processing Event must use "
                "EVT-000001."
            )

        if event.previous_state is not None:
            raise ProcessingEventChainError(
                "The first Processing Event must not have "
                "a previous_state."
            )

        if event.previous_event_fingerprint is not None:
            raise ProcessingEventChainError(
                "The first Processing Event must not have "
                "a previous_event_fingerprint."
            )

        if event.event_type != "run_created":
            raise ProcessingValidationError(
                "The first Processing Event must use "
                "event_type run_created."
            )

        if event.next_state != "created":
            raise InvalidProcessingTransitionError(
                "The first Processing Event must transition "
                "to created."
            )

        return

    if event.previous_state is None:
        raise ProcessingEventChainError(
            "Every Processing Event after the first must have "
            "a previous_state."
        )

    try:
        _validate_sha256(
            event.previous_event_fingerprint,
            label="previous_event_fingerprint",
        )
    except ProcessingValidationError as exc:
        raise ProcessingEventChainError(
            "Every Processing Event after the first must "
            "reference one valid predecessor fingerprint."
        ) from exc

    if event.event_type == "run_created":
        raise ProcessingValidationError(
            "run_created is permitted only for the first event."
        )


def _validate_event_type_contract(
    event: ProcessingEvent,
) -> None:
    """Validate event-type-specific state requirements."""

    required_next_states = {
        "run_created": frozenset({"created"}),
        "stage_started": frozenset({"running"}),
        "stage_completed": frozenset({"running"}),
        "review_requested": frozenset(
            {"awaiting_review"}
        ),
        "review_resolved": frozenset(
            {"running", "completed"}
        ),
        "run_blocked": frozenset({"blocked"}),
        "run_failed": frozenset({"failed"}),
        "retry_started": frozenset({"running"}),
        "recovery_required": frozenset({"blocked"}),
        "recovery_completed": frozenset(
            {"running", "completed"}
        ),
        "run_completed": frozenset({"completed"}),
        "run_superseded": frozenset({"superseded"}),
    }

    permitted_states = required_next_states.get(
        event.event_type
    )

    if (
        permitted_states is not None
        and event.next_state not in permitted_states
    ):
        raise ProcessingValidationError(
            f"event_type {event.event_type!r} is incompatible "
            f"with next_state {event.next_state!r}."
        )

    if event.event_type == "run_created":
        if event.processing_stage is not None:
            raise ProcessingValidationError(
                "event_type 'run_created' must not contain a "
                "processing_stage."
            )

        if event.attempt_id is not None:
            raise ProcessingValidationError(
                "event_type 'run_created' must not contain an "
                "attempt_id."
            )

        if event.artifact_references:
            raise ProcessingValidationError(
                "event_type 'run_created' must not contain "
                "artifact references."
            )

    stage_required_event_types = frozenset(
        {
            "stage_started",
            "stage_completed",
            "retry_started",
        }
    )

    if (
        event.event_type in stage_required_event_types
        and event.processing_stage is None
    ):
        raise ProcessingValidationError(
            f"event_type {event.event_type!r} requires a "
            "processing_stage."
        )

    attempt_required_event_types = frozenset(
        {
            "stage_started",
            "stage_completed",
            "retry_started",
        }
    )

    if (
        event.event_type in attempt_required_event_types
        and event.attempt_id is None
    ):
        raise ProcessingValidationError(
            f"event_type {event.event_type!r} requires an "
            "attempt_id."
        )

    artifact_required_event_types = frozenset(
        {
            "artifact_published",
            "artifact_invalidated",
            "artifact_superseded",
        }
    )

    if (
        event.event_type in artifact_required_event_types
        and not event.artifact_references
    ):
        raise ProcessingValidationError(
            f"event_type {event.event_type!r} requires at "
            "least one artifact reference."
        )


def _parse_processing_artifact_reference(
    payload: object,
) -> ProcessingArtifactReference:
    """Parse one artifact reference mapping."""

    if not isinstance(payload, dict):
        raise ProcessingValidationError(
            "Each artifact reference must be a JSON object."
        )

    _require_exact_fields(
        payload,
        expected_fields=_ARTIFACT_REFERENCE_FIELDS,
        label="Processing artifact reference",
    )

    reference = ProcessingArtifactReference(
        artifact_type=payload["artifact_type"],
        artifact_id=payload["artifact_id"],
        content_fingerprint=payload[
            "content_fingerprint"
        ],
        repository_relative_path=payload[
            "repository_relative_path"
        ],
    )

    validate_processing_artifact_reference(reference)

    return reference


def _validate_artifact_references(
    references: object,
) -> None:
    """Validate immutable artifact references and uniqueness."""

    if not isinstance(references, tuple):
        raise ProcessingValidationError(
            "artifact_references must be a tuple."
        )

    reference_keys: list[
        tuple[str, str, str, str]
    ] = []

    for reference in references:
        validate_processing_artifact_reference(reference)

        reference_keys.append(
            (
                reference.artifact_type,
                reference.artifact_id,
                reference.content_fingerprint,
                reference.repository_relative_path,
            )
        )

    if len(reference_keys) != len(set(reference_keys)):
        raise ProcessingValidationError(
            "artifact_references must not contain duplicates."
        )


def _processing_event_payload(
    event: ProcessingEvent,
    *,
    include_fingerprint: bool,
) -> dict[str, object]:
    """Build the canonical serialized event payload."""

    payload: dict[str, object] = {
        "schema_version": event.schema_version,
        "project_id": event.project_id,
        "processing_run_id": event.processing_run_id,
        "event_id": event.event_id,
        "event_sequence": event.event_sequence,
        "previous_state": event.previous_state,
        "next_state": event.next_state,
        "processing_stage": event.processing_stage,
        "event_type": event.event_type,
        "attempt_id": event.attempt_id,
        "reason_code": event.reason_code,
        "artifact_references": [
            {
                "artifact_type": reference.artifact_type,
                "artifact_id": reference.artifact_id,
                "content_fingerprint": (
                    reference.content_fingerprint
                ),
                "repository_relative_path": (
                    reference.repository_relative_path
                ),
            }
            for reference in event.artifact_references
        ],
        "occurred_at": event.occurred_at,
        "previous_event_fingerprint": (
            event.previous_event_fingerprint
        ),
    }

    if include_fingerprint:
        payload["event_fingerprint"] = (
            event.event_fingerprint
        )

    return payload


def _validate_reason_code(value: object) -> None:
    """Validate one deterministic machine-readable reason code."""

    if (
        not isinstance(value, str)
        or _REASON_CODE_PATTERN.fullmatch(value) is None
    ):
        raise ProcessingValidationError(
            "reason_code must be a lowercase snake-case "
            "identifier containing at most 120 characters."
        )


def _validate_repository_relative_path(value: object) -> None:
    """Validate one canonical repository-relative POSIX path."""

    if not isinstance(value, str) or not value:
        raise ProcessingValidationError(
            "repository_relative_path must be a non-empty string."
        )

    if value != value.strip():
        raise ProcessingValidationError(
            "repository_relative_path must not contain "
            "surrounding whitespace."
        )

    if "\\" in value:
        raise ProcessingValidationError(
            "repository_relative_path must use POSIX separators."
        )

    path = PurePosixPath(value)

    if path.is_absolute():
        raise ProcessingValidationError(
            "repository_relative_path must be relative."
        )

    if any(part in {"", ".", ".."} for part in path.parts):
        raise ProcessingValidationError(
            "repository_relative_path contains unsafe segments."
        )

    if path.as_posix() != value:
        raise ProcessingValidationError(
            "repository_relative_path must use canonical POSIX form."
        )


def _validate_sha256(
    value: object,
    *,
    label: str,
) -> None:
    """Validate one lowercase SHA-256 value."""

    if (
        not isinstance(value, str)
        or _SHA256_PATTERN.fullmatch(value) is None
    ):
        raise ProcessingValidationError(
            f"{label} must be a lowercase 64-character "
            "SHA-256 value."
        )


def _validate_utc_timestamp(
    value: object,
    *,
    label: str,
) -> None:
    """Validate one UTC ISO-8601 timestamp."""

    if (
        not isinstance(value, str)
        or _UTC_TIMESTAMP_PATTERN.fullmatch(value) is None
    ):
        raise ProcessingValidationError(
            f"{label} must be a UTC ISO-8601 timestamp "
            "ending in Z."
        )

    try:
        parsed = datetime.fromisoformat(
            value.removesuffix("Z") + "+00:00"
        )
    except ValueError as exc:
        raise ProcessingValidationError(
            f"{label} is not a valid timestamp."
        ) from exc

    if (
        parsed.utcoffset() is None
        or parsed.utcoffset().total_seconds() != 0
    ):
        raise ProcessingValidationError(
            f"{label} must use UTC."
        )


def _object_without_duplicate_keys(
    pairs: list[tuple[str, Any]],
) -> dict[str, Any]:
    """Reject duplicate JSON object keys."""

    payload: dict[str, Any] = {}

    for key, value in pairs:
        if key in payload:
            raise ProcessingValidationError(
                f"Duplicate JSON field: {key}."
            )
        payload[key] = value

    return payload


def _require_exact_fields(
    payload: dict[str, object],
    *,
    expected_fields: frozenset[str],
    label: str,
) -> None:
    """Require one exact closed field set."""

    actual_fields = frozenset(payload)

    missing_fields = expected_fields - actual_fields
    unknown_fields = actual_fields - expected_fields

    if missing_fields:
        raise ProcessingValidationError(
            f"{label} is missing fields: "
            f"{sorted(missing_fields)}."
        )

    if unknown_fields:
        raise ProcessingValidationError(
            f"{label} contains unknown fields: "
            f"{sorted(unknown_fields)}."
        )