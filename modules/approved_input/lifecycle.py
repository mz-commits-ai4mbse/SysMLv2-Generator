"""Derive Approved Input authority state and successor equivalence."""

from __future__ import annotations

from dataclasses import asdict
import hashlib
import json

from .errors import (
    ApprovedInputIntegrityError,
    ApprovedInputValidationError,
)
from .event_manifest import validate_approved_input_event
from .identifiers import approved_input_event_id_sequence
from .manifest import validate_approved_input_manifest
from .types import (
    ApprovedInputAuthoritySnapshot,
    ApprovedInputEvent,
    ApprovedInputManifest,
)


def calculate_promotion_equivalence_fingerprint(
    manifest: ApprovedInputManifest,
) -> str:
    """Fingerprint the engineering authority relevant to continuity."""

    validate_approved_input_manifest(manifest)
    payload = {
        "approved_input_kind": manifest.approved_input_kind,
        "canonical_content": asdict(manifest.canonical_content),
        "selected_classification": manifest.selected_classification,
        "selected_framework_assignment": (
            manifest.selected_framework_assignment
        ),
        "selected_terminology_assignment": (
            manifest.selected_terminology_assignment
        ),
        "selected_source_assignments": list(
            manifest.selected_source_assignments
        ),
        "selected_relationship_representation": (
            None
            if manifest.selected_relationship_representation is None
            else asdict(manifest.selected_relationship_representation)
        ),
        "stable_subject_key": manifest.stable_subject_key,
        "source_id": manifest.source_id,
        "source_sha256": manifest.source_sha256,
        "primary_artifact_reference": asdict(
            manifest.primary_artifact_reference
        ),
        "supporting_artifact_references": [
            asdict(reference)
            for reference in manifest.supporting_artifact_references
        ],
        "proposal_references": list(manifest.proposal_references),
    }
    canonical_json = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(
        canonical_json.encode("utf-8")
    ).hexdigest()


def derive_approved_input_authority_states(
    manifests: object,
    events: object,
) -> tuple[ApprovedInputAuthoritySnapshot, ...]:
    """Derive current authority states from immutable manifests/events."""

    if not isinstance(manifests, tuple):
        raise ApprovedInputValidationError(
            "manifests must be a tuple."
        )
    if not isinstance(events, tuple):
        raise ApprovedInputValidationError(
            "events must be a tuple."
        )

    by_id: dict[str, ApprovedInputManifest] = {}
    project_id: str | None = None
    for manifest in manifests:
        if not isinstance(manifest, ApprovedInputManifest):
            raise ApprovedInputValidationError(
                "manifests entries must be ApprovedInputManifest values."
            )
        validate_approved_input_manifest(manifest)
        if project_id is None:
            project_id = manifest.project_id
        elif manifest.project_id != project_id:
            raise ApprovedInputIntegrityError(
                "Approved Input lifecycle derivation must be project-local."
            )
        if manifest.approved_input_id in by_id:
            raise ApprovedInputIntegrityError(
                "Approved Input manifests must have unique IDs."
            )
        by_id[manifest.approved_input_id] = manifest

    states = {
        approved_input_id: "active"
        for approved_input_id in by_id
    }
    last_event_fingerprint: dict[str, str | None] = {
        approved_input_id: None
        for approved_input_id in by_id
    }
    seen_event_ids: set[str] = set()

    validated_events: list[ApprovedInputEvent] = []
    for event in events:
        if not isinstance(event, ApprovedInputEvent):
            raise ApprovedInputValidationError(
                "events entries must be ApprovedInputEvent values."
            )
        validate_approved_input_event(event)
        validated_events.append(event)

    ordered_events = tuple(
        sorted(
            validated_events,
            key=lambda item: approved_input_event_id_sequence(
                item.approved_input_event_id
            ),
        )
    )

    for event in ordered_events:
        if event.approved_input_event_id in seen_event_ids:
            raise ApprovedInputIntegrityError(
                "Approved Input Event IDs must be globally unique per project."
            )
        seen_event_ids.add(event.approved_input_event_id)

        manifest = by_id.get(event.approved_input_id)
        if manifest is None:
            raise ApprovedInputIntegrityError(
                "Approved Input Event references an unavailable manifest."
            )
        if event.project_id != manifest.project_id:
            raise ApprovedInputIntegrityError(
                "Approved Input Event crosses a Project boundary."
            )
        if states[event.approved_input_id] != "active":
            raise ApprovedInputIntegrityError(
                "A terminal Approved Input cannot receive another "
                "G5.6 lifecycle event."
            )
        if event.previous_event_fingerprint != last_event_fingerprint[
            event.approved_input_id
        ]:
            raise ApprovedInputIntegrityError(
                "Approved Input Event predecessor fingerprint is stale."
            )

        if event.event_type == "superseded":
            successor_id = event.successor_approved_input_id
            successor = by_id.get(successor_id)
            if successor is None:
                raise ApprovedInputIntegrityError(
                    "Supersession references an unavailable successor."
                )
            if states[successor_id] != "active":
                raise ApprovedInputIntegrityError(
                    "A superseding Approved Input must be active."
                )
            if (
                successor.stable_subject_key
                != manifest.stable_subject_key
            ):
                raise ApprovedInputIntegrityError(
                    "Supersession requires the same stable_subject_key."
                )
            _validate_supersession_causal_binding(event, successor)

        states[event.approved_input_id] = event.next_authority_state
        last_event_fingerprint[event.approved_input_id] = (
            event.event_fingerprint
        )

    return tuple(
        ApprovedInputAuthoritySnapshot(
            manifest=by_id[approved_input_id],
            authority_state=states[approved_input_id],
            latest_event_fingerprint=last_event_fingerprint[
                approved_input_id
            ],
        )
        for approved_input_id in sorted(by_id)
    )


def active_approved_input_manifests(
    manifests: object,
    events: object,
) -> tuple[ApprovedInputManifest, ...]:
    """Return only manifests whose derived authority state is active."""

    return tuple(
        snapshot.manifest
        for snapshot in derive_approved_input_authority_states(
            manifests,
            events,
        )
        if snapshot.authority_state == "active"
    )


def _validate_supersession_causal_binding(
    event: ApprovedInputEvent,
    successor: ApprovedInputManifest,
) -> None:
    bindings = (
        (
            event.causal_review_document_id,
            successor.review_document_id,
            "review_document_id",
        ),
        (
            event.causal_review_document_version_id,
            successor.review_document_version_id,
            "review_document_version_id",
        ),
        (
            event.causal_review_revision_id,
            successor.review_revision_id,
            "review_revision_id",
        ),
        (
            event.causal_finalization_decision_id,
            successor.finalization_decision_id,
            "finalization_decision_id",
        ),
        (
            event.causal_finalization_decision_fingerprint,
            successor.finalization_decision_fingerprint,
            "finalization_decision_fingerprint",
        ),
    )
    for actual, expected, label in bindings:
        if actual != expected:
            raise ApprovedInputIntegrityError(
                "Supersession causal binding does not match the "
                f"successor {label}."
            )
