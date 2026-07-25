"""Validate Processing Run histories and derive current run state."""

from __future__ import annotations

from .errors import (
    ProcessingEventChainError,
    ProcessingValidationError,
)
from .event_manifest import validate_processing_event
from .run_manifest import validate_processing_run_manifest
from .types import (
    DerivedProcessingRunState,
    ProcessingRunHistory,
)


def create_processing_run_history(
    *,
    manifest: object,
    events: object,
) -> ProcessingRunHistory:
    """Create and validate one ordered Processing Run history."""

    history = ProcessingRunHistory(
        manifest=manifest,
        events=events,
    )

    return validate_processing_run_history(history)


def validate_processing_run_history(
    history: object,
) -> ProcessingRunHistory:
    """Validate one Run Manifest and its complete Event History."""

    if not isinstance(history, ProcessingRunHistory):
        raise ProcessingValidationError(
            "history must be a ProcessingRunHistory."
        )

    validate_processing_run_manifest(history.manifest)

    if not isinstance(history.events, tuple):
        raise ProcessingValidationError(
            "events must be a tuple."
        )

    if not history.events:
        raise ProcessingEventChainError(
            "A Processing Run history requires at least one event."
        )

    previous_event = None

    for expected_sequence, event in enumerate(
        history.events,
        start=1,
    ):
        validate_processing_event(event)

        if event.project_id != history.manifest.project_id:
            raise ProcessingEventChainError(
                "Processing Event project_id does not match the "
                "Run Manifest."
            )

        if (
            event.processing_run_id
            != history.manifest.processing_run_id
        ):
            raise ProcessingEventChainError(
                "Processing Event processing_run_id does not match "
                "the Run Manifest."
            )

        if event.event_sequence != expected_sequence:
            raise ProcessingEventChainError(
                "Processing Event sequence is not contiguous and "
                "ordered from one."
            )

        if previous_event is None:
            if event.previous_event_fingerprint is not None:
                raise ProcessingEventChainError(
                    "The first Processing Event must not reference "
                    "a predecessor."
                )
        else:
            if (
                event.previous_event_fingerprint
                != previous_event.event_fingerprint
            ):
                raise ProcessingEventChainError(
                    "Processing Event predecessor fingerprint does "
                    "not match the preceding event."
                )

            if event.previous_state != previous_event.next_state:
                raise ProcessingEventChainError(
                    "Processing Event state history is not "
                    "continuous."
                )

        previous_event = event

    return history


def derive_processing_run_state(
    history: object,
) -> DerivedProcessingRunState:
    """Derive the current operational state from a valid history."""

    validated_history = validate_processing_run_history(history)
    latest_event = validated_history.events[-1]

    latest_attempt_id = next(
        (
            event.attempt_id
            for event in reversed(validated_history.events)
            if event.attempt_id is not None
        ),
        None,
    )

    return DerivedProcessingRunState(
        project_id=validated_history.manifest.project_id,
        processing_run_id=(
            validated_history.manifest.processing_run_id
        ),
        source_id=validated_history.manifest.source_id,
        run_state=latest_event.next_state,
        processing_stage=latest_event.processing_stage,
        latest_attempt_id=latest_attempt_id,
        latest_event_id=latest_event.event_id,
        superseded_by_run_id=None,
        blocked_reason=(
            latest_event.reason_code
            if latest_event.next_state == "blocked"
            else None
        ),
        failure_reason=(
            latest_event.reason_code
            if latest_event.next_state == "failed"
            else None
        ),
        pending_review=(
            latest_event.next_state == "awaiting_review"
        ),
    )