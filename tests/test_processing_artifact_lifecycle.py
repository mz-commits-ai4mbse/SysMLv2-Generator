"""Tests for artifact lifecycle and source-disposition impact contracts."""

from __future__ import annotations

from dataclasses import replace

import pytest

from modules.project_processing.artifact_lifecycle import (
    SourceDispositionImpact,
    create_artifact_invalidation_event,
    create_artifact_supersession_event,
    derive_effective_source_dispositions,
    derive_processing_artifact_lifecycles,
    derive_source_disposition_impacts,
)
from modules.project_processing.decision_manifest import (
    create_processing_decision,
)
from modules.project_processing.errors import (
    ProcessingIntegrityError,
    ProcessingReferenceError,
    ProcessingValidationError,
)
from modules.project_processing.event_manifest import (
    create_processing_artifact_reference,
    create_processing_event,
)
from modules.project_processing.history import (
    create_processing_run_history,
)
from modules.project_processing.run_manifest import (
    create_processing_run_manifest,
    create_semantic_reference_version,
)


PROJECT_ID = "318604"
SOURCE_ID = "SRC-000001"
SOURCE_SHA256 = "a" * 64


def manifest(
    *,
    run_id: str = "RUN-000001",
    project_id: str = PROJECT_ID,
    source_id: str = SOURCE_ID,
    source_sha256: str = SOURCE_SHA256,
    workflow_profile: str = "engineering_source_processing",
    source_role_snapshot: str = "engineering_source",
):
    return create_processing_run_manifest(
        project_id=project_id,
        processing_run_id=run_id,
        source_id=source_id,
        source_sha256=source_sha256,
        source_role_snapshot=source_role_snapshot,
        workflow_profile=workflow_profile,
        configuration_fingerprint="b" * 64,
        framework_template_id="TURING_RFLP_FRAMEWORK",
        framework_template_version="1.0.0",
        semantic_reference_versions=(
            create_semantic_reference_version(
                reference_system_id="TURING_CORE_VOCABULARY",
                reference_version="1.0.0",
            ),
        ),
        timestamp="2026-07-25T10:00:00Z",
    )


def reference(
    artifact_id: str,
    *,
    fingerprint: str = "c" * 64,
    path: str | None = None,
):
    return create_processing_artifact_reference(
        artifact_type="information_unit",
        artifact_id=artifact_id,
        content_fingerprint=fingerprint,
        repository_relative_path=(
            path
            if path is not None
            else f"data/projects/{PROJECT_ID}/semantics/{artifact_id}.json"
        ),
    )


def history_with_events(
    lifecycle_events: tuple[
        tuple[str, tuple, str],
        ...
    ] = (),
    *,
    run_manifest=None,
):
    run_manifest = run_manifest or manifest()
    created = create_processing_event(
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
        timestamp="2026-07-25T10:00:00Z",
        previous_event_fingerprint=None,
    )
    started = create_processing_event(
        project_id=run_manifest.project_id,
        processing_run_id=run_manifest.processing_run_id,
        event_id="EVT-000002",
        event_sequence=2,
        previous_state="created",
        next_state="running",
        processing_stage="semantic_extraction",
        event_type="stage_started",
        attempt_id="ATT-000001",
        reason_code="stage_started",
        artifact_references=(),
        timestamp="2026-07-25T10:01:00Z",
        previous_event_fingerprint=created.event_fingerprint,
    )
    events = [created, started]

    for sequence, (event_type, references, timestamp) in enumerate(
        lifecycle_events,
        start=3,
    ):
        previous = events[-1]
        events.append(
            create_processing_event(
                project_id=run_manifest.project_id,
                processing_run_id=run_manifest.processing_run_id,
                event_id=f"EVT-{sequence:06d}",
                event_sequence=sequence,
                previous_state="running",
                next_state="running",
                processing_stage="publication",
                event_type=event_type,
                attempt_id="ATT-000001",
                reason_code=event_type,
                artifact_references=references,
                timestamp=timestamp,
                previous_event_fingerprint=(
                    previous.event_fingerprint
                ),
            )
        )

    return create_processing_run_history(
        manifest=run_manifest,
        events=tuple(events),
    )


def decision(
    decision_id: str = "PD-000001",
    *,
    project_id: str = PROJECT_ID,
    source_id: str = SOURCE_ID,
    source_sha256: str = SOURCE_SHA256,
    disposition: str = "in_scope",
    timestamp: str = "2026-07-25T12:00:00Z",
    supersedes: str | None = None,
):
    return create_processing_decision(
        project_id=project_id,
        processing_decision_id=decision_id,
        decision_type="source_disposition",
        source_id=source_id,
        source_sha256=source_sha256,
        disposition=disposition,
        reviewer_identity="reviewer@example.com",
        rationale="Validated source treatment.",
        timestamp=timestamp,
        supersedes_processing_decision_id=supersedes,
    )


def test_empty_histories_have_no_lifecycles() -> None:
    assert derive_processing_artifact_lifecycles(()) == ()


def test_histories_must_be_tuple() -> None:
    with pytest.raises(ProcessingValidationError):
        derive_processing_artifact_lifecycles([])


def test_lifecycle_derivation_is_project_local() -> None:
    first = history_with_events()
    second = history_with_events(
        run_manifest=manifest(
            run_id="RUN-000002",
            project_id="481516",
        )
    )
    with pytest.raises(ProcessingReferenceError):
        derive_processing_artifact_lifecycles((first, second))


def test_published_artifact_becomes_active() -> None:
    artifact = reference("IU-000001")
    history = history_with_events(
        (("artifact_published", (artifact,), "2026-07-25T10:02:00Z"),)
    )
    lifecycles = derive_processing_artifact_lifecycles((history,))
    assert len(lifecycles) == 1
    assert lifecycles[0].artifact_reference == artifact
    assert lifecycles[0].lifecycle_state == "active"
    assert lifecycles[0].caused_by_event_id == "EVT-000003"


def test_multiple_artifacts_are_sorted_deterministically() -> None:
    later = reference("IU-000002")
    earlier = reference("IU-000001")
    history = history_with_events(
        (("artifact_published", (later, earlier), "2026-07-25T10:02:00Z"),)
    )
    lifecycles = derive_processing_artifact_lifecycles((history,))
    assert tuple(
        item.artifact_reference.artifact_id for item in lifecycles
    ) == ("IU-000001", "IU-000002")


def test_same_local_artifact_identity_is_independent_across_runs() -> None:
    first_artifact = reference(
        "IU-000001",
        fingerprint="c" * 64,
        path=(
            f"data/projects/{PROJECT_ID}/runs/RUN-000001/"
            "artifacts/IU-000001.json"
        ),
    )
    second_artifact = reference(
        "IU-000001",
        fingerprint="d" * 64,
        path=(
            f"data/projects/{PROJECT_ID}/runs/RUN-000002/"
            "artifacts/IU-000001.json"
        ),
    )
    first = history_with_events(
        (("artifact_published", (first_artifact,), "2026-07-25T10:02:00Z"),),
        run_manifest=manifest(run_id="RUN-000001"),
    )
    second = history_with_events(
        (("artifact_published", (second_artifact,), "2026-07-25T10:02:00Z"),),
        run_manifest=manifest(run_id="RUN-000002"),
    )

    lifecycles = derive_processing_artifact_lifecycles((second, first))

    assert len(lifecycles) == 2
    assert tuple(
        item.artifact_reference.content_fingerprint
        for item in lifecycles
    ) == ("c" * 64, "d" * 64)
    assert all(item.lifecycle_state == "active" for item in lifecycles)


def test_duplicate_publication_is_rejected() -> None:
    artifact = reference("IU-000001")
    history = history_with_events(
        (
            ("artifact_published", (artifact,), "2026-07-25T10:02:00Z"),
            ("artifact_published", (artifact,), "2026-07-25T10:03:00Z"),
        )
    )
    with pytest.raises(ProcessingIntegrityError):
        derive_processing_artifact_lifecycles((history,))


def test_conflicting_reference_fingerprint_is_rejected() -> None:
    original = reference("IU-000001")
    conflict = reference("IU-000001", fingerprint="d" * 64)
    history = history_with_events(
        (
            ("artifact_published", (original,), "2026-07-25T10:02:00Z"),
            ("artifact_invalidated", (conflict,), "2026-07-25T10:03:00Z"),
        )
    )
    with pytest.raises(ProcessingReferenceError):
        derive_processing_artifact_lifecycles((history,))


def test_published_artifact_can_be_invalidated() -> None:
    artifact = reference("IU-000001")
    history = history_with_events(
        (
            ("artifact_published", (artifact,), "2026-07-25T10:02:00Z"),
            ("artifact_invalidated", (artifact,), "2026-07-25T10:03:00Z"),
        )
    )
    lifecycle = derive_processing_artifact_lifecycles((history,))[0]
    assert lifecycle.lifecycle_state == "invalidated"
    assert lifecycle.caused_by_event_id == "EVT-000004"
    assert lifecycle.superseded_by_artifact_id is None


def test_unknown_artifact_cannot_be_invalidated() -> None:
    history = history_with_events(
        (("artifact_invalidated", (reference("IU-000001"),), "2026-07-25T10:02:00Z"),)
    )
    with pytest.raises(ProcessingReferenceError):
        derive_processing_artifact_lifecycles((history,))


def test_artifact_cannot_be_invalidated_twice() -> None:
    artifact = reference("IU-000001")
    history = history_with_events(
        (
            ("artifact_published", (artifact,), "2026-07-25T10:02:00Z"),
            ("artifact_invalidated", (artifact,), "2026-07-25T10:03:00Z"),
            ("artifact_invalidated", (artifact,), "2026-07-25T10:04:00Z"),
        )
    )
    with pytest.raises(ProcessingIntegrityError):
        derive_processing_artifact_lifecycles((history,))


def test_artifact_supersession_updates_both_artifacts() -> None:
    old = reference("IU-000001")
    new = reference("IU-000002", fingerprint="d" * 64)
    history = history_with_events(
        (
            ("artifact_published", (old,), "2026-07-25T10:02:00Z"),
            ("artifact_superseded", (old, new), "2026-07-25T10:03:00Z"),
        )
    )
    by_id = {
        item.artifact_reference.artifact_id: item
        for item in derive_processing_artifact_lifecycles((history,))
    }
    assert by_id["IU-000001"].lifecycle_state == "superseded"
    assert by_id["IU-000001"].superseded_by_artifact_id == "IU-000002"
    assert by_id["IU-000002"].lifecycle_state == "active"


def test_existing_active_successor_is_preserved() -> None:
    old = reference("IU-000001")
    new = reference("IU-000002", fingerprint="d" * 64)
    history = history_with_events(
        (
            ("artifact_published", (old, new), "2026-07-25T10:02:00Z"),
            ("artifact_superseded", (old, new), "2026-07-25T10:03:00Z"),
        )
    )
    by_id = {
        item.artifact_reference.artifact_id: item
        for item in derive_processing_artifact_lifecycles((history,))
    }
    assert by_id["IU-000002"].caused_by_event_id == "EVT-000003"


def test_supersession_requires_exactly_two_references() -> None:
    artifact = reference("IU-000001")
    history = history_with_events(
        (
            ("artifact_published", (artifact,), "2026-07-25T10:02:00Z"),
            ("artifact_superseded", (artifact,), "2026-07-25T10:03:00Z"),
        )
    )
    with pytest.raises(ProcessingValidationError):
        derive_processing_artifact_lifecycles((history,))


def test_unknown_artifact_cannot_be_superseded() -> None:
    old = reference("IU-000001")
    new = reference("IU-000002", fingerprint="d" * 64)
    history = history_with_events(
        (("artifact_superseded", (old, new), "2026-07-25T10:02:00Z"),)
    )
    with pytest.raises(ProcessingReferenceError):
        derive_processing_artifact_lifecycles((history,))


def test_invalidated_artifact_cannot_be_superseded() -> None:
    old = reference("IU-000001")
    new = reference("IU-000002", fingerprint="d" * 64)
    history = history_with_events(
        (
            ("artifact_published", (old,), "2026-07-25T10:02:00Z"),
            ("artifact_invalidated", (old,), "2026-07-25T10:03:00Z"),
            ("artifact_superseded", (old, new), "2026-07-25T10:04:00Z"),
        )
    )
    with pytest.raises(ProcessingIntegrityError):
        derive_processing_artifact_lifecycles((history,))


def test_create_invalidation_event_uses_next_identity() -> None:
    artifact = reference("IU-000001")
    history = history_with_events(
        (("artifact_published", (artifact,), "2026-07-25T10:02:00Z"),)
    )
    event = create_artifact_invalidation_event(
        history,
        artifact_references=(artifact,),
        next_state="running",
        processing_stage="publication",
        attempt_id="ATT-000001",
        reason_code="source_disposition_changed",
        timestamp="2026-07-25T10:03:00Z",
    )
    assert event.event_id == "EVT-000004"
    assert event.event_type == "artifact_invalidated"
    assert event.artifact_references == (artifact,)


def test_create_invalidation_event_requires_tuple() -> None:
    history = history_with_events()
    with pytest.raises(ProcessingValidationError):
        create_artifact_invalidation_event(
            history,
            artifact_references=[],
            next_state="running",
            processing_stage="publication",
            attempt_id=None,
            reason_code="invalidated",
            timestamp="2026-07-25T10:03:00Z",
        )


def test_create_invalidation_event_requires_artifacts() -> None:
    history = history_with_events()
    with pytest.raises(ProcessingValidationError):
        create_artifact_invalidation_event(
            history,
            artifact_references=(),
            next_state="running",
            processing_stage="publication",
            attempt_id=None,
            reason_code="invalidated",
            timestamp="2026-07-25T10:03:00Z",
        )


def test_create_supersession_event_orders_references() -> None:
    old = reference("IU-000001")
    new = reference("IU-000002", fingerprint="d" * 64)
    history = history_with_events(
        (("artifact_published", (old,), "2026-07-25T10:02:00Z"),)
    )
    event = create_artifact_supersession_event(
        history,
        superseded_artifact=old,
        successor_artifact=new,
        next_state="running",
        processing_stage="publication",
        attempt_id="ATT-000001",
        reason_code="replacement_published",
        timestamp="2026-07-25T10:03:00Z",
    )
    assert event.event_type == "artifact_superseded"
    assert event.artifact_references == (old, new)


def test_create_supersession_event_rejects_same_identity() -> None:
    artifact = reference("IU-000001")
    history = history_with_events()
    with pytest.raises(ProcessingValidationError):
        create_artifact_supersession_event(
            history,
            superseded_artifact=artifact,
            successor_artifact=artifact,
            next_state="running",
            processing_stage="publication",
            attempt_id=None,
            reason_code="replacement",
            timestamp="2026-07-25T10:03:00Z",
        )


def test_empty_decisions_have_no_effective_dispositions() -> None:
    assert derive_effective_source_dispositions(()) == {}


def test_decisions_must_be_tuple() -> None:
    with pytest.raises(ProcessingValidationError):
        derive_effective_source_dispositions([])


def test_single_decision_is_effective() -> None:
    current = decision(disposition="context_only")
    assert derive_effective_source_dispositions((current,)) == {
        SOURCE_ID: current
    }


def test_latest_decision_in_chain_is_effective() -> None:
    first = decision()
    second = decision(
        "PD-000002",
        disposition="out_of_scope",
        timestamp="2026-07-25T13:00:00Z",
        supersedes="PD-000001",
    )
    assert derive_effective_source_dispositions((second, first)) == {
        SOURCE_ID: second
    }


def test_decision_chains_are_project_local() -> None:
    first = decision()
    other = decision(
        "PD-000002",
        project_id="481516",
        source_id="SRC-000002",
    )
    with pytest.raises(ProcessingReferenceError):
        derive_effective_source_dispositions((first, other))


def test_missing_decision_predecessor_is_rejected() -> None:
    current = decision(
        "PD-000002",
        supersedes="PD-000001",
    )
    with pytest.raises(ProcessingReferenceError):
        derive_effective_source_dispositions((current,))


def test_cross_source_decision_predecessor_is_rejected() -> None:
    first = decision()
    second = decision(
        "PD-000002",
        source_id="SRC-000002",
        supersedes="PD-000001",
        timestamp="2026-07-25T13:00:00Z",
    )
    with pytest.raises(ProcessingReferenceError):
        derive_effective_source_dispositions((first, second))


def test_one_decision_cannot_have_multiple_successors() -> None:
    first = decision()
    second = decision(
        "PD-000002",
        disposition="context_only",
        supersedes="PD-000001",
        timestamp="2026-07-25T13:00:00Z",
    )
    third = decision(
        "PD-000003",
        disposition="out_of_scope",
        supersedes="PD-000001",
        timestamp="2026-07-25T14:00:00Z",
    )
    with pytest.raises(ProcessingIntegrityError):
        derive_effective_source_dispositions((first, second, third))


def test_source_cannot_have_multiple_chain_roots() -> None:
    first = decision()
    second = decision(
        "PD-000002",
        disposition="context_only",
        timestamp="2026-07-25T13:00:00Z",
    )
    with pytest.raises(ProcessingIntegrityError):
        derive_effective_source_dispositions((first, second))


def test_superseding_decision_must_be_later() -> None:
    first = decision(timestamp="2026-07-25T13:00:00Z")
    second = decision(
        "PD-000002",
        disposition="context_only",
        supersedes="PD-000001",
        timestamp="2026-07-25T12:00:00Z",
    )
    with pytest.raises(ProcessingValidationError):
        derive_effective_source_dispositions((first, second))


def test_in_scope_decision_has_no_invalidation_impact() -> None:
    run = history_with_events()
    assert derive_source_disposition_impacts(
        (run,),
        (decision(disposition="in_scope"),),
    ) == ()


def test_context_only_decision_invalidates_engineering_run() -> None:
    artifact = reference("IU-000001")
    run = history_with_events(
        (("artifact_published", (artifact,), "2026-07-25T10:02:00Z"),)
    )
    impacts = derive_source_disposition_impacts(
        (run,),
        (decision(disposition="context_only"),),
    )
    assert impacts == (
        SourceDispositionImpact(
            project_id=PROJECT_ID,
            source_id=SOURCE_ID,
            processing_decision_id="PD-000001",
            disposition="context_only",
            invalidated_run_ids=("RUN-000001",),
            artifact_references=(artifact,),
        ),
    )


def test_out_of_scope_decision_invalidates_engineering_run() -> None:
    run = history_with_events()
    impact = derive_source_disposition_impacts(
        (run,),
        (decision(disposition="out_of_scope"),),
    )[0]
    assert impact.disposition == "out_of_scope"
    assert impact.invalidated_run_ids == ("RUN-000001",)


def test_context_only_run_is_not_engineering_invalidation_target() -> None:
    context_manifest = manifest(
        workflow_profile="context_only_processing",
        source_role_snapshot="context_only",
    )
    run = history_with_events(run_manifest=context_manifest)
    impact = derive_source_disposition_impacts(
        (run,),
        (decision(disposition="context_only"),),
    )[0]
    assert impact.invalidated_run_ids == ()
    assert impact.artifact_references == ()


def test_impact_analysis_requires_matching_source_fingerprint() -> None:
    run = history_with_events()
    changed = decision(
        disposition="context_only",
        source_sha256="d" * 64,
    )
    with pytest.raises(ProcessingReferenceError):
        derive_source_disposition_impacts((run,), (changed,))


def test_already_invalidated_artifact_is_not_targeted_again() -> None:
    artifact = reference("IU-000001")
    run = history_with_events(
        (
            ("artifact_published", (artifact,), "2026-07-25T10:02:00Z"),
            ("artifact_invalidated", (artifact,), "2026-07-25T10:03:00Z"),
        )
    )
    impact = derive_source_disposition_impacts(
        (run,),
        (decision(disposition="out_of_scope"),),
    )[0]
    assert impact.artifact_references == ()


def test_superseding_artifact_is_invalidation_target() -> None:
    old = reference("IU-000001")
    new = reference("IU-000002", fingerprint="d" * 64)
    run = history_with_events(
        (
            ("artifact_published", (old,), "2026-07-25T10:02:00Z"),
            ("artifact_superseded", (old, new), "2026-07-25T10:03:00Z"),
        )
    )
    impact = derive_source_disposition_impacts(
        (run,),
        (decision(disposition="context_only"),),
    )[0]
    assert tuple(
        item.artifact_id for item in impact.artifact_references
    ) == ("IU-000001", "IU-000002")


def test_impact_analysis_is_project_local() -> None:
    run = history_with_events()
    other = decision(
        project_id="481516",
        source_id="SRC-000002",
        disposition="context_only",
    )
    with pytest.raises(ProcessingReferenceError):
        derive_source_disposition_impacts((run,), (other,))