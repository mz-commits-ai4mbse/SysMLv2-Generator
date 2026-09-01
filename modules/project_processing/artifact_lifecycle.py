"""Derive immutable artifact lifecycle and source-disposition impacts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .decision_manifest import validate_processing_decision
from .errors import (
    ProcessingIntegrityError,
    ProcessingReferenceError,
    ProcessingValidationError,
)
from .event_manifest import (
    create_processing_event,
    validate_processing_artifact_reference,
)
from .history import validate_processing_run_history
from .identifiers import next_processing_event_id
from .types import (
    ProcessingArtifactLifecycle,
    ProcessingArtifactReference,
    ProcessingDecision,
    ProcessingEvent,
    ProcessingRunHistory,
)


@dataclass(frozen=True, slots=True)
class SourceDispositionImpact:
    """Deterministic invalidation impact of one effective source decision."""

    project_id: str
    source_id: str
    processing_decision_id: str
    disposition: str
    invalidated_run_ids: tuple[str, ...]
    artifact_references: tuple[ProcessingArtifactReference, ...]


def create_artifact_invalidation_event(
    history: object,
    *,
    artifact_references: tuple[ProcessingArtifactReference, ...],
    next_state: str,
    processing_stage: str | None,
    attempt_id: str | None,
    reason_code: str,
    timestamp: str,
) -> ProcessingEvent:
    """Create the next immutable event invalidating exact artifacts."""

    validated_history = validate_processing_run_history(history)
    references = _validate_reference_tuple(
        artifact_references,
        label="artifact_references",
        require_nonempty=True,
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
        next_state=next_state,
        processing_stage=processing_stage,
        event_type="artifact_invalidated",
        attempt_id=attempt_id,
        reason_code=reason_code,
        artifact_references=references,
        timestamp=timestamp,
        previous_event_fingerprint=latest_event.event_fingerprint,
    )


def create_artifact_supersession_event(
    history: object,
    *,
    superseded_artifact: ProcessingArtifactReference,
    successor_artifact: ProcessingArtifactReference,
    next_state: str,
    processing_stage: str | None,
    attempt_id: str | None,
    reason_code: str,
    timestamp: str,
) -> ProcessingEvent:
    """Create the next event replacing one exact artifact with another."""

    validated_history = validate_processing_run_history(history)
    validate_processing_artifact_reference(superseded_artifact)
    validate_processing_artifact_reference(successor_artifact)

    if _artifact_key(superseded_artifact) == _artifact_key(
        successor_artifact
    ):
        raise ProcessingValidationError(
            "Artifact supersession requires two distinct artifact identities."
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
        next_state=next_state,
        processing_stage=processing_stage,
        event_type="artifact_superseded",
        attempt_id=attempt_id,
        reason_code=reason_code,
        artifact_references=(
            superseded_artifact,
            successor_artifact,
        ),
        timestamp=timestamp,
        previous_event_fingerprint=latest_event.event_fingerprint,
    )


def derive_processing_artifact_lifecycles(
    histories: object,
) -> tuple[ProcessingArtifactLifecycle, ...]:
    """Derive current artifact lifecycle from validated project histories."""

    validated_histories = _validate_project_histories(histories)
    lifecycles = _derive_contextual_artifact_lifecycles(
        validated_histories
    )
    return tuple(
        lifecycles[key]
        for key in sorted(lifecycles)
    )


def _derive_contextual_artifact_lifecycles(
    validated_histories: tuple[ProcessingRunHistory, ...],
) -> dict[tuple[str, str, str], ProcessingArtifactLifecycle]:
    """Derive lifecycles keyed by run-local artifact identity."""

    canonical_references: dict[
        tuple[str, str, str], ProcessingArtifactReference
    ] = {}
    lifecycles: dict[
        tuple[str, str, str], ProcessingArtifactLifecycle
    ] = {}

    ordered_events = sorted(
        (
            event
            for history in validated_histories
            for event in history.events
        ),
        key=lambda event: (
            _parse_utc_timestamp(event.occurred_at),
            event.processing_run_id,
            event.event_sequence,
        ),
    )

    for event in ordered_events:
        for reference in event.artifact_references:
            _register_exact_contextual_reference(
                canonical_references,
                event.processing_run_id,
                reference,
            )

        if event.event_type == "artifact_published":
            for reference in event.artifact_references:
                key = _contextual_artifact_key(
                    event.processing_run_id,
                    reference,
                )
                if key in lifecycles:
                    raise ProcessingIntegrityError(
                        "An immutable artifact identity cannot be published "
                        "more than once within one Processing Run: "
                        f"{reference.artifact_id}."
                    )
                lifecycles[key] = ProcessingArtifactLifecycle(
                    artifact_reference=reference,
                    lifecycle_state="active",
                    caused_by_event_id=event.event_id,
                )
            continue

        if event.event_type == "artifact_invalidated":
            for reference in event.artifact_references:
                key = _contextual_artifact_key(
                    event.processing_run_id,
                    reference,
                )
                current = lifecycles.get(key)
                if current is None:
                    raise ProcessingReferenceError(
                        "Artifact invalidation references an artifact without "
                        f"a lifecycle origin: {reference.artifact_id}."
                    )
                if current.lifecycle_state == "invalidated":
                    raise ProcessingIntegrityError(
                        "An artifact cannot be invalidated more than once: "
                        f"{reference.artifact_id}."
                    )
                lifecycles[key] = ProcessingArtifactLifecycle(
                    artifact_reference=reference,
                    lifecycle_state="invalidated",
                    caused_by_event_id=event.event_id,
                )
            continue

        if event.event_type == "artifact_superseded":
            if len(event.artifact_references) != 2:
                raise ProcessingValidationError(
                    "artifact_superseded requires exactly two references: "
                    "the replaced artifact followed by its successor."
                )
            replaced, successor = event.artifact_references
            replaced_key = _contextual_artifact_key(
                event.processing_run_id, replaced
            )
            successor_key = _contextual_artifact_key(
                event.processing_run_id, successor
            )
            if replaced_key == successor_key:
                raise ProcessingValidationError(
                    "Artifact supersession requires distinct identities."
                )
            current_replaced = lifecycles.get(replaced_key)
            if current_replaced is None:
                raise ProcessingReferenceError(
                    "Artifact supersession references an artifact without "
                    f"a lifecycle origin: {replaced.artifact_id}."
                )
            if current_replaced.lifecycle_state != "active":
                raise ProcessingIntegrityError(
                    "Only an active artifact may be superseded: "
                    f"{replaced.artifact_id}."
                )
            current_successor = lifecycles.get(successor_key)
            if current_successor is not None and current_successor.lifecycle_state != "active":
                raise ProcessingIntegrityError(
                    "A superseding artifact must be active or newly "
                    f"introduced: {successor.artifact_id}."
                )
            lifecycles[replaced_key] = ProcessingArtifactLifecycle(
                artifact_reference=replaced,
                lifecycle_state="superseded",
                caused_by_event_id=event.event_id,
                superseded_by_artifact_id=successor.artifact_id,
            )
            if current_successor is None:
                lifecycles[successor_key] = ProcessingArtifactLifecycle(
                    artifact_reference=successor,
                    lifecycle_state="active",
                    caused_by_event_id=event.event_id,
                )

    return lifecycles

def derive_effective_source_dispositions(
    decisions: object,
) -> dict[str, ProcessingDecision]:
    """Validate decision chains and return the effective decision per source."""

    if not isinstance(decisions, tuple):
        raise ProcessingValidationError(
            "decisions must be a tuple."
        )

    if not decisions:
        return {}

    validated = tuple(
        validate_processing_decision(decision)
        for decision in decisions
    )
    project_ids = {decision.project_id for decision in validated}
    if len(project_ids) != 1:
        raise ProcessingReferenceError(
            "Source-disposition decisions must be project-local."
        )

    by_id: dict[str, ProcessingDecision] = {}
    successors: dict[str, str] = {}
    roots_by_source: dict[str, list[str]] = {}

    for decision in validated:
        decision_id = decision.processing_decision_id
        if decision_id in by_id:
            raise ProcessingIntegrityError(
                f"Duplicate Processing Decision identity: {decision_id}."
            )
        by_id[decision_id] = decision

    for decision in validated:
        predecessor_id = decision.supersedes_processing_decision_id
        if predecessor_id is None:
            roots_by_source.setdefault(decision.source_id, []).append(
                decision.processing_decision_id
            )
            continue

        predecessor = by_id.get(predecessor_id)
        if predecessor is None:
            raise ProcessingReferenceError(
                "Processing Decision references an unavailable predecessor: "
                f"{predecessor_id}."
            )
        if predecessor.project_id != decision.project_id:
            raise ProcessingReferenceError(
                "A Processing Decision predecessor must remain in the same "
                "project."
            )
        if predecessor.source_id != decision.source_id:
            raise ProcessingReferenceError(
                "A Processing Decision may supersede only a decision for "
                "the same source."
            )
        if predecessor.decision_type != decision.decision_type:
            raise ProcessingReferenceError(
                "A Processing Decision may supersede only the same "
                "decision type."
            )
        if _parse_utc_timestamp(decision.decided_at) <= (
            _parse_utc_timestamp(predecessor.decided_at)
        ):
            raise ProcessingValidationError(
                "A superseding Processing Decision must be later than its "
                "predecessor."
            )
        if predecessor_id in successors:
            raise ProcessingIntegrityError(
                "One Processing Decision cannot have multiple successors: "
                f"{predecessor_id}."
            )
        successors[predecessor_id] = decision.processing_decision_id

    for source_id, roots in roots_by_source.items():
        if len(roots) != 1:
            raise ProcessingIntegrityError(
                "One source must have one unambiguous Processing Decision "
                f"chain root: {source_id}."
            )

    sources_with_decisions = {decision.source_id for decision in validated}
    if set(roots_by_source) != sources_with_decisions:
        raise ProcessingIntegrityError(
            "Processing Decision chains contain a cycle or lack a root."
        )

    effective: dict[str, ProcessingDecision] = {}
    for source_id, roots in roots_by_source.items():
        current_id = roots[0]
        visited: set[str] = set()
        while current_id in successors:
            if current_id in visited:
                raise ProcessingIntegrityError(
                    "Processing Decision chains contain a cycle."
                )
            visited.add(current_id)
            current_id = successors[current_id]
        effective[source_id] = by_id[current_id]

    if len(effective) != len(sources_with_decisions):
        raise ProcessingIntegrityError(
            "Processing Decision chains are ambiguous."
        )

    return dict(sorted(effective.items()))


def derive_source_disposition_impacts(
    histories: object,
    decisions: object,
) -> tuple[SourceDispositionImpact, ...]:
    """Identify engineering runs and artifacts invalidated by dispositions."""

    validated_histories = _validate_project_histories(histories)
    effective = derive_effective_source_dispositions(decisions)

    project_ids = {
        history.manifest.project_id
        for history in validated_histories
    } | {
        decision.project_id
        for decision in effective.values()
    }
    if len(project_ids) > 1:
        raise ProcessingReferenceError(
            "Source-disposition impact analysis must be project-local."
        )

    lifecycle_by_key = _derive_contextual_artifact_lifecycles(
        validated_histories
    )
    impacts: list[SourceDispositionImpact] = []

    for source_id, decision in effective.items():
        if decision.disposition == "in_scope":
            continue

        source_histories = tuple(
            history
            for history in validated_histories
            if history.manifest.source_id == source_id
        )
        for history in source_histories:
            if history.manifest.source_sha256 != decision.source_sha256:
                raise ProcessingReferenceError(
                    "Processing Decision source fingerprint does not match "
                    "a dependent Processing Run."
                )

        engineering_histories = tuple(
            history
            for history in source_histories
            if history.manifest.workflow_profile
            == "engineering_source_processing"
        )
        run_ids = tuple(
            sorted(
                history.manifest.processing_run_id
                for history in engineering_histories
            )
        )

        produced_references: dict[
            tuple[str, str, str], ProcessingArtifactReference
        ] = {}
        for history in engineering_histories:
            processing_run_id = history.manifest.processing_run_id
            for event in history.events:
                if event.event_type == "artifact_published":
                    candidates = event.artifact_references
                elif event.event_type == "artifact_superseded":
                    candidates = event.artifact_references[1:2]
                else:
                    candidates = ()

                for reference in candidates:
                    _register_exact_contextual_reference(
                        produced_references,
                        processing_run_id,
                        reference,
                    )

        invalidation_targets = []
        for key in sorted(produced_references):
            lifecycle = lifecycle_by_key.get(key)
            if lifecycle is None:
                raise ProcessingIntegrityError(
                    "A produced artifact lacks a derived lifecycle state."
                )
            if lifecycle.lifecycle_state != "invalidated":
                invalidation_targets.append(
                    lifecycle.artifact_reference
                )

        impacts.append(
            SourceDispositionImpact(
                project_id=decision.project_id,
                source_id=source_id,
                processing_decision_id=(
                    decision.processing_decision_id
                ),
                disposition=decision.disposition,
                invalidated_run_ids=run_ids,
                artifact_references=tuple(invalidation_targets),
            )
        )

    impacts.sort(key=lambda impact: impact.source_id)
    return tuple(impacts)

def _validate_project_histories(
    histories: object,
) -> tuple[ProcessingRunHistory, ...]:
    if not isinstance(histories, tuple):
        raise ProcessingValidationError(
            "histories must be a tuple."
        )

    validated = tuple(
        validate_processing_run_history(history)
        for history in histories
    )
    project_ids = {
        history.manifest.project_id
        for history in validated
    }
    if len(project_ids) > 1:
        raise ProcessingReferenceError(
            "Artifact lifecycle derivation must be project-local."
        )
    return validated


def _validate_reference_tuple(
    references: object,
    *,
    label: str,
    require_nonempty: bool,
) -> tuple[ProcessingArtifactReference, ...]:
    if not isinstance(references, tuple):
        raise ProcessingValidationError(
            f"{label} must be a tuple."
        )
    if require_nonempty and not references:
        raise ProcessingValidationError(
            f"{label} must not be empty."
        )

    seen: set[tuple[str, str]] = set()
    for reference in references:
        validate_processing_artifact_reference(reference)
        key = _artifact_key(reference)
        if key in seen:
            raise ProcessingValidationError(
                f"{label} must not contain duplicate artifact identities."
            )
        seen.add(key)
    return references


def _register_exact_contextual_reference(
    references: dict[
        tuple[str, str, str],
        ProcessingArtifactReference,
    ],
    processing_run_id: str,
    reference: ProcessingArtifactReference,
) -> None:
    key = _contextual_artifact_key(
        processing_run_id,
        reference,
    )
    current = references.get(key)
    if current is not None and current != reference:
        raise ProcessingReferenceError(
            "One run-local artifact identity is referenced with conflicting "
            f"content or paths: {processing_run_id}/{reference.artifact_id}."
        )
    references[key] = reference


def _contextual_artifact_key(
    processing_run_id: str,
    reference: ProcessingArtifactReference,
) -> tuple[str, str, str]:
    return (
        processing_run_id,
        reference.artifact_type,
        reference.artifact_id,
    )

def _artifact_key(
    reference: ProcessingArtifactReference,
) -> tuple[str, str]:
    return (reference.artifact_type, reference.artifact_id)


def _parse_utc_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))