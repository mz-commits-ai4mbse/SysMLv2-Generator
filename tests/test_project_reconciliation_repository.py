"""I2A tests for immutable S2-S5 Project Reconciliation persistence."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
import json

import pytest

from modules.model_impact_reconciliation import reconcile_model_impact
from modules.project_engineering_authority import (
    build_project_engineering_authority_state,
)
from modules.project_reconciliation import (
    ProjectReconciliationPersistenceIntegrityError,
    ProjectReconciliationRepository,
)

from tests.test_project_engineering_authority import (
    bindings,
    decision,
    reconciliation,
)
from tests.test_project_semantic_reconciliation import two_sources


PROJECT_ID = "318604"


def _clock():
    return datetime(
        2026,
        8,
        31,
        9,
        0,
        0,
        tzinfo=timezone.utc,
    )


def _fits():
    return tuple(
        item.project_fit
        for item in two_sources()
    )


def _authority_context():
    rec = reconciliation()
    rec, manifests, events, aeis, subject_bindings = bindings(rec)
    human = decision(
        rec,
        subject_bindings,
        outcome="remain_independent",
    )
    state = build_project_engineering_authority_state(
        rec,
        manifests,
        events,
        aeis,
        (human,),
    )
    impact = reconcile_model_impact(state, None)
    return (
        rec,
        manifests,
        events,
        aeis,
        subject_bindings,
        human,
        state,
        impact,
    )


def test_cycle_persists_exact_s2_and_s3_roundtrip(tmp_path):
    repository = ProjectReconciliationRepository(
        tmp_path,
        clock=_clock,
    )
    rec = reconciliation()

    cycle = repository.start_cycle(rec, _fits())

    assert cycle.reconciliation_cycle_id == "PRC-000001"
    assert cycle.project_id == PROJECT_ID
    assert cycle.semantic_reconciliation_fingerprint == (
        rec.content_fingerprint
    )
    assert repository.load_cycle(
        PROJECT_ID,
        "PRC-000001",
    ) == cycle
    assert repository.load_semantic_reconciliation(
        PROJECT_ID,
        "PRC-000001",
    ) == rec
    assert tuple(
        item.assessment_fingerprint
        for item in repository.list_project_fit(PROJECT_ID)
    ) == tuple(
        sorted(
            item.assessment_fingerprint
            for item in _fits()
        )
    )


def test_same_s3_artifact_is_idempotent_not_a_second_cycle(tmp_path):
    repository = ProjectReconciliationRepository(
        tmp_path,
        clock=_clock,
    )
    rec = reconciliation()

    first = repository.start_cycle(rec, _fits())
    second = repository.start_cycle(rec, _fits())

    assert second == first
    assert len(repository.list_cycles(PROJECT_ID)) == 1


def test_cycle_rejects_project_fit_set_not_bound_by_s3(tmp_path):
    repository = ProjectReconciliationRepository(
        tmp_path,
        clock=_clock,
    )
    rec = reconciliation()
    fits = _fits()

    with pytest.raises(
        ProjectReconciliationPersistenceIntegrityError,
        match="does not match exact S3 provenance",
    ):
        repository.start_cycle(rec, fits[:1])


def test_s4_bindings_decision_state_and_s5_persist_exactly(tmp_path):
    repository = ProjectReconciliationRepository(
        tmp_path,
        clock=_clock,
    )
    (
        rec,
        _manifests,
        _events,
        _aeis,
        subject_bindings,
        human,
        state,
        impact,
    ) = _authority_context()

    cycle = repository.start_cycle(rec, _fits())
    snapshot = repository.publish_authority_bindings(
        PROJECT_ID,
        cycle.reconciliation_cycle_id,
        subject_bindings,
    )
    persisted_decision = repository.record_authority_decision(
        PROJECT_ID,
        cycle.reconciliation_cycle_id,
        human,
    )
    persisted_state = repository.publish_authority_state(
        PROJECT_ID,
        cycle.reconciliation_cycle_id,
        state,
    )
    persisted_impact = repository.publish_model_impact(
        PROJECT_ID,
        cycle.reconciliation_cycle_id,
        impact,
    )

    assert snapshot.bindings == subject_bindings
    assert persisted_decision == human
    assert persisted_state == state
    assert persisted_impact == impact
    assert repository.load_model_impact(
        PROJECT_ID,
        cycle.reconciliation_cycle_id,
    ) == impact


def test_one_relation_cannot_receive_two_immutable_decisions(tmp_path):
    repository = ProjectReconciliationRepository(
        tmp_path,
        clock=_clock,
    )
    (
        rec,
        _manifests,
        _events,
        _aeis,
        subject_bindings,
        human,
        _state,
        _impact,
    ) = _authority_context()

    cycle = repository.start_cycle(rec, _fits())
    repository.publish_authority_bindings(
        PROJECT_ID,
        cycle.reconciliation_cycle_id,
        subject_bindings,
    )
    repository.record_authority_decision(
        PROJECT_ID,
        cycle.reconciliation_cycle_id,
        human,
    )

    second = decision(
        rec,
        subject_bindings,
        outcome="unresolved",
        decision_id="PEAD-000002",
    )
    with pytest.raises(
        ProjectReconciliationPersistenceIntegrityError,
        match="only one immutable Human",
    ):
        repository.record_authority_decision(
            PROJECT_ID,
            cycle.reconciliation_cycle_id,
            second,
        )


def test_s4_state_must_match_persisted_decision_population(tmp_path):
    repository = ProjectReconciliationRepository(
        tmp_path,
        clock=_clock,
    )
    (
        rec,
        _manifests,
        _events,
        _aeis,
        subject_bindings,
        human,
        state,
        _impact,
    ) = _authority_context()

    cycle = repository.start_cycle(rec, _fits())
    repository.publish_authority_bindings(
        PROJECT_ID,
        cycle.reconciliation_cycle_id,
        subject_bindings,
    )

    with pytest.raises(
        ProjectReconciliationPersistenceIntegrityError,
        match="exact persisted cycle authority",
    ):
        repository.publish_authority_state(
            PROJECT_ID,
            cycle.reconciliation_cycle_id,
            state,
        )

    repository.record_authority_decision(
        PROJECT_ID,
        cycle.reconciliation_cycle_id,
        human,
    )
    assert repository.publish_authority_state(
        PROJECT_ID,
        cycle.reconciliation_cycle_id,
        state,
    ) == state


def test_s5_must_bind_exact_persisted_s4_state(tmp_path):
    repository = ProjectReconciliationRepository(
        tmp_path,
        clock=_clock,
    )
    (
        rec,
        _manifests,
        _events,
        _aeis,
        subject_bindings,
        human,
        state,
        impact,
    ) = _authority_context()

    cycle = repository.start_cycle(rec, _fits())
    repository.publish_authority_bindings(
        PROJECT_ID,
        cycle.reconciliation_cycle_id,
        subject_bindings,
    )
    repository.record_authority_decision(
        PROJECT_ID,
        cycle.reconciliation_cycle_id,
        human,
    )
    repository.publish_authority_state(
        PROJECT_ID,
        cycle.reconciliation_cycle_id,
        state,
    )

    tampered = replace(
        impact,
        project_authority_fingerprint="0" * 64,
    )
    with pytest.raises(Exception):
        repository.publish_model_impact(
            PROJECT_ID,
            cycle.reconciliation_cycle_id,
            tampered,
        )


def test_tampered_persisted_s3_fails_closed(tmp_path):
    repository = ProjectReconciliationRepository(
        tmp_path,
        clock=_clock,
    )
    rec = reconciliation()
    cycle = repository.start_cycle(rec, _fits())

    path = (
        tmp_path
        / PROJECT_ID
        / "project_reconciliation"
        / "cycles"
        / cycle.reconciliation_cycle_id
        / "semantic_reconciliation.json"
    )
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw["llm_model"] = "tampered-model"
    path.write_text(
        json.dumps(raw, indent=2) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(Exception):
        repository.load_semantic_reconciliation(
            PROJECT_ID,
            cycle.reconciliation_cycle_id,
        )


def test_cycle_manifest_and_s3_fit_binding_fail_closed(tmp_path):
    repository = ProjectReconciliationRepository(
        tmp_path,
        clock=_clock,
    )
    rec = reconciliation()
    cycle = repository.start_cycle(rec, _fits())

    manifest_path = (
        tmp_path
        / PROJECT_ID
        / "project_reconciliation"
        / "cycles"
        / cycle.reconciliation_cycle_id
        / "manifest.json"
    )
    raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    raw["project_fit_fingerprints"] = [
        "0" * 64,
        "1" * 64,
    ]

    # Recompute only the outer manifest fingerprint to prove that load-time
    # S2/S3 cross-binding is independently enforced.
    from hashlib import sha256
    body = dict(raw)
    body.pop("content_fingerprint")
    canonical = json.dumps(
        body,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    raw["content_fingerprint"] = sha256(
        canonical.encode("utf-8")
    ).hexdigest()
    manifest_path.write_text(
        json.dumps(raw, indent=2) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(
        ProjectReconciliationPersistenceIntegrityError,
        match="Project Fit fingerprints differ",
    ):
        repository.load_semantic_reconciliation(
            PROJECT_ID,
            cycle.reconciliation_cycle_id,
        )
