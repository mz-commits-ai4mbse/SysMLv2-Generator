"""Pure retry and supersession contracts for Processing Runs."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime

from .errors import (
    ProcessingIntegrityError,
    ProcessingRecoveryRequiredError,
    ProcessingReferenceError,
    ProcessingValidationError,
)
from .event_manifest import create_processing_event
from .history import (
    derive_processing_run_state,
    validate_processing_run_history,
)
from .identifiers import next_processing_event_id
from .run_manifest import validate_processing_run_manifest
from .types import (
    PROCESSING_STAGES,
    DerivedProcessingRunState,
    ProcessingEvent,
    ProcessingRunHistory,
    ProcessingRunManifest,
)

MATERIAL_RUN_BINDING_FIELDS = (
    "source_id",
    "source_sha256",
    "source_role_snapshot",
    "workflow_profile",
    "configuration_fingerprint",
    "framework_template_id",
    "framework_template_version",
    "semantic_reference_versions",
)


def material_run_binding_changes(
    predecessor: object,
    successor: object,
) -> tuple[str, ...]:
    """Return material bindings that differ between two valid manifests."""

    validated_predecessor = validate_processing_run_manifest(predecessor)
    validated_successor = validate_processing_run_manifest(successor)

    return tuple(
        field_name
        for field_name in MATERIAL_RUN_BINDING_FIELDS
        if getattr(validated_predecessor, field_name)
        != getattr(validated_successor, field_name)
    )


def validate_successor_manifest(
    predecessor: object,
    successor: object,
) -> tuple[str, ...]:
    """Validate one explicit material-change successor relationship."""

    validated_predecessor = validate_processing_run_manifest(predecessor)
    validated_successor = validate_processing_run_manifest(successor)

    if validated_successor.project_id != validated_predecessor.project_id:
        raise ProcessingReferenceError(
            "A successor Processing Run must remain in the same project."
        )

    if (
        validated_successor.supersedes_run_id
        != validated_predecessor.processing_run_id
    ):
        raise ProcessingReferenceError(
            "Successor supersedes_run_id must reference the predecessor Run."
        )

    if _parse_utc_timestamp(validated_successor.created_at) <= (
        _parse_utc_timestamp(validated_predecessor.created_at)
    ):
        raise ProcessingValidationError(
            "A successor Processing Run must be created after its predecessor."
        )

    changed_fields = material_run_binding_changes(
        validated_predecessor,
        validated_successor,
    )

    if not changed_fields:
        raise ProcessingValidationError(
            "A successor Processing Run requires at least one material "
            "binding change; unchanged bindings require a retry in the "
            "existing Run."
        )

    return changed_fields


def create_retry_event(
    history: object,
    *,
    processing_stage: str,
    attempt_id: str,
    reason_code: str,
    timestamp: str,
) -> ProcessingEvent:
    """Create the next immutable retry event within one unchanged Run."""

    validated_history = validate_processing_run_history(history)

    if processing_stage not in PROCESSING_STAGES:
        raise ProcessingValidationError(
            "processing_stage is not supported."
        )

    latest_event = validated_history.events[-1]

    return create_processing_event(
        project_id=validated_history.manifest.project_id,
        processing_run_id=(
            validated_history.manifest.processing_run_id
        ),
        event_id=next_processing_event_id(
            event.event_id for event in validated_history.events
        ),
        event_sequence=len(validated_history.events) + 1,
        previous_state=latest_event.next_state,
        next_state="running",
        processing_stage=processing_stage,
        event_type="retry_started",
        attempt_id=attempt_id,
        reason_code=reason_code,
        artifact_references=(),
        timestamp=timestamp,
        previous_event_fingerprint=latest_event.event_fingerprint,
    )


def create_successor_initial_event(
    successor_manifest: object,
    *,
    reason_code: str = "successor_run_created",
) -> ProcessingEvent:
    """Create EVT-000001 for an already validated successor manifest."""

    validated_manifest = validate_processing_run_manifest(
        successor_manifest
    )

    if validated_manifest.supersedes_run_id is None:
        raise ProcessingValidationError(
            "A successor Run Manifest must reference a predecessor."
        )

    return create_processing_event(
        project_id=validated_manifest.project_id,
        processing_run_id=validated_manifest.processing_run_id,
        event_id="EVT-000001",
        event_sequence=1,
        previous_state=None,
        next_state="created",
        processing_stage=None,
        event_type="run_created",
        attempt_id=None,
        reason_code=reason_code,
        artifact_references=(),
        timestamp=validated_manifest.created_at,
        previous_event_fingerprint=None,
    )


def create_run_superseded_event(
    predecessor_history: object,
    successor_manifest: object,
    *,
    reason_code: str,
    timestamp: str,
) -> ProcessingEvent:
    """Create the predecessor event that completes a supersession pair."""

    validated_history = validate_processing_run_history(
        predecessor_history
    )
    validate_successor_manifest(
        validated_history.manifest,
        successor_manifest,
    )

    latest_event = validated_history.events[-1]

    if latest_event.next_state == "superseded":
        raise ProcessingIntegrityError(
            "A superseded Processing Run cannot be superseded again."
        )

    return create_processing_event(
        project_id=validated_history.manifest.project_id,
        processing_run_id=(
            validated_history.manifest.processing_run_id
        ),
        event_id=next_processing_event_id(
            event.event_id for event in validated_history.events
        ),
        event_sequence=len(validated_history.events) + 1,
        previous_state=latest_event.next_state,
        next_state="superseded",
        processing_stage=None,
        event_type="run_superseded",
        attempt_id=None,
        reason_code=reason_code,
        artifact_references=(),
        timestamp=timestamp,
        previous_event_fingerprint=latest_event.event_fingerprint,
    )


def derive_supersession_index(
    histories: object,
) -> dict[str, str]:
    """Validate project-local successor links and return predecessor mapping."""

    if not isinstance(histories, tuple):
        raise ProcessingValidationError(
            "histories must be a tuple."
        )

    if not histories:
        return {}

    validated_histories = tuple(
        validate_processing_run_history(history)
        for history in histories
    )

    project_ids = {
        history.manifest.project_id
        for history in validated_histories
    }

    if len(project_ids) != 1:
        raise ProcessingReferenceError(
            "Supersession validation is project-local."
        )

    histories_by_run_id: dict[str, ProcessingRunHistory] = {}

    for history in validated_histories:
        run_id = history.manifest.processing_run_id

        if run_id in histories_by_run_id:
            raise ProcessingIntegrityError(
                f"Duplicate Processing Run identity: {run_id}."
            )

        histories_by_run_id[run_id] = history

    successors_by_predecessor: dict[str, str] = {}

    for successor_history in validated_histories:
        predecessor_id = (
            successor_history.manifest.supersedes_run_id
        )

        if predecessor_id is None:
            continue

        predecessor_history = histories_by_run_id.get(
            predecessor_id
        )

        if predecessor_history is None:
            raise ProcessingRecoveryRequiredError(
                "Successor Processing Run references an unavailable "
                f"predecessor: {predecessor_id}."
            )

        if predecessor_id in successors_by_predecessor:
            raise ProcessingIntegrityError(
                "One Processing Run cannot have multiple successors: "
                f"{predecessor_id}."
            )

        validate_successor_manifest(
            predecessor_history.manifest,
            successor_history.manifest,
        )

        successors_by_predecessor[predecessor_id] = (
            successor_history.manifest.processing_run_id
        )

    _validate_acyclic_supersession(successors_by_predecessor)

    for run_id, history in histories_by_run_id.items():
        run_state = history.events[-1].next_state
        has_successor = run_id in successors_by_predecessor

        if has_successor and run_state != "superseded":
            raise ProcessingRecoveryRequiredError(
                "Successor Run exists but predecessor lacks the "
                f"run_superseded event: {run_id}."
            )

        if run_state == "superseded" and not has_successor:
            raise ProcessingRecoveryRequiredError(
                "Processing Run is marked superseded but no successor "
                f"Run Manifest references it: {run_id}."
            )

    return dict(sorted(successors_by_predecessor.items()))


def derive_project_run_states(
    histories: object,
) -> tuple[DerivedProcessingRunState, ...]:
    """Derive run states enriched with validated successor identities."""

    if not isinstance(histories, tuple):
        raise ProcessingValidationError(
            "histories must be a tuple."
        )

    supersession_index = derive_supersession_index(histories)
    states = []

    for history in histories:
        state = derive_processing_run_state(history)
        states.append(
            replace(
                state,
                superseded_by_run_id=supersession_index.get(
                    state.processing_run_id
                ),
            )
        )

    states.sort(key=lambda state: state.processing_run_id)
    return tuple(states)


def _validate_acyclic_supersession(
    successors_by_predecessor: dict[str, str],
) -> None:
    for origin in successors_by_predecessor:
        visited: set[str] = set()
        current = origin

        while current in successors_by_predecessor:
            if current in visited:
                raise ProcessingIntegrityError(
                    "Processing Run supersession relationships contain "
                    "a cycle."
                )

            visited.add(current)
            current = successors_by_predecessor[current]


def _parse_utc_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))