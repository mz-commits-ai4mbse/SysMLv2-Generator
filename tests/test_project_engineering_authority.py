"""Tests for ADR-032 S4 project-level Engineering Authority."""

from __future__ import annotations

from dataclasses import asdict, replace
from hashlib import sha256
import json

import pytest

from modules.approved_engineering_information.projection import (
    APPROVED_ENGINEERING_INFORMATION_SCHEMA_VERSION,
    ApprovedEngineeringInformationSet,
    ApprovedEngineeringSubject,
)
from modules.approved_input.event_manifest import (
    create_approved_input_event,
)
from modules.approved_input.manifest import create_approved_input_manifest
from modules.approved_input.types import ApprovedInputCanonicalContent
from modules.project_engineering_authority import (
    ProjectEngineeringAuthorityIntegrityError,
    ProjectEngineeringAuthorityValidationError,
    build_project_engineering_authority_state,
    create_project_authority_decision,
    prepare_project_authority_bindings,
    project_engineering_authority_to_json,
)
from modules.project_processing.event_manifest import (
    create_processing_artifact_reference,
)

from tests.test_project_semantic_reconciliation import (
    Client,
    refs,
    service,
    two_sources,
)


PROJECT_ID = "318604"
TIMESTAMP = "2026-08-31T07:30:00Z"


def canonical_sha(value):
    return sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def reconciliation(outcome="complementary"):
    left, right = refs()
    shared = [] if outcome in {"distinct", "uncertain"} else ["streaming"]
    differences = (
        []
        if outcome in {"equivalent", "uncertain"}
        else ["engineering meaning or abstraction differs"]
    )
    return service(
        Client(
            {
                "relations": [
                    {
                        "left_subject_ref": left,
                        "right_subject_ref": right,
                        "outcome": outcome,
                        "rationale": "Cross-source comparison evidence.",
                        "shared_concepts": shared,
                        "material_differences": differences,
                    }
                ],
                "unmatched_subject_refs": [],
            }
        )
    ).reconcile(
        two_sources(),
        provider="openai",
        model="gpt-test",
    )


def approved_input(
    *,
    sequence,
    source_id,
    source_sha,
    run_id,
    stable_subject_key,
    statement,
):
    artifact = create_processing_artifact_reference(
        artifact_type="subject_consensus",
        artifact_id="SUBJ-000001",
        content_fingerprint=source_sha,
        repository_relative_path=(
            f"projects/{PROJECT_ID}/processing/{run_id}/"
            "artifacts/SUBJ-000001.json"
        ),
    )
    return create_approved_input_manifest(
        project_id=PROJECT_ID,
        approved_input_id=f"AIN-{sequence:06d}",
        approved_input_kind="element_statement",
        canonical_content=ApprovedInputCanonicalContent(
            title=f"Reviewed Subject {sequence}",
            primary_text=statement,
            description=None,
            information_type="constraint",
            modality="descriptive",
            epistemic_status="explicit",
        ),
        selected_classification=None,
        selected_framework_assignment=None,
        selected_terminology_assignment=None,
        selected_source_assignments=(),
        selected_relationship_representation=None,
        stable_subject_key=stable_subject_key,
        review_document_id=f"RVD-{sequence:06d}",
        review_document_version_id=f"RVV-{sequence:06d}",
        review_revision_id=f"RVR-{sequence:06d}",
        review_item_id=f"RIT-{sequence:06d}",
        review_item_kind="element",
        review_item_fingerprint=f"{sequence}"[-1] * 64,
        finalized_artifact_set_fingerprint="c" * 64,
        finalization_decision_id=f"HRD-{sequence:06d}",
        finalization_decision_fingerprint="d" * 64,
        finalization_validation_fingerprint="e" * 64,
        source_id=source_id,
        source_sha256=source_sha,
        processing_run_id=run_id,
        attempt_id="ATT-000001",
        primary_artifact_reference=artifact,
        supporting_artifact_references=(),
        proposal_references=(),
        created_at=TIMESTAMP,
    )


def authority_inputs(*, same_stable_key=False):
    first_statement = "The system shall provide remote viewing."
    second_statement = (
        "The streaming subsystem encodes microscope images for "
        "remote transmission."
    )
    first = approved_input(
        sequence=1,
        source_id="SRC-000001",
        source_sha="a" * 64,
        run_id="RUN-000001",
        stable_subject_key="remote-viewing",
        statement=first_statement,
    )
    second = approved_input(
        sequence=2,
        source_id="SRC-000002",
        source_sha="b" * 64,
        run_id="RUN-000002",
        stable_subject_key=(
            "remote-viewing"
            if same_stable_key
            else "streaming-encoder"
        ),
        statement=second_statement,
    )
    return (
        (first, second),
        (),
        (
            aei(first, "SUBJ-000001"),
            aei(second, "SUBJ-000001"),
        ),
    )


def aei(manifest, canonical_subject_id):
    content = manifest.canonical_content
    subject = ApprovedEngineeringSubject(
        canonical_subject_id=canonical_subject_id,
        approved_input_id=manifest.approved_input_id,
        stable_subject_key=manifest.stable_subject_key,
        title=content.title,
        engineering_statement=content.primary_text,
        information_type=content.information_type,
        statement_modality=content.modality,
        epistemic_class=content.epistemic_status,
        review_item_id=manifest.review_item_id,
        review_item_fingerprint=manifest.review_item_fingerprint,
        approved_input_fingerprint=manifest.content_fingerprint,
    )
    body = {
        "schema_version": (
            APPROVED_ENGINEERING_INFORMATION_SCHEMA_VERSION
        ),
        "project_id": PROJECT_ID,
        "review_document_id": manifest.review_document_id,
        "review_document_version_id": (
            manifest.review_document_version_id
        ),
        "review_revision_id": manifest.review_revision_id,
        "subjects": [asdict(subject)],
        "relationships": [],
        "non_promotable_subject_ids": [],
        "non_projectable_relationship_decision_ids": [],
        "relationship_decision_authority_fingerprint": "f" * 64,
    }
    return ApprovedEngineeringInformationSet(
        schema_version=(
            APPROVED_ENGINEERING_INFORMATION_SCHEMA_VERSION
        ),
        project_id=PROJECT_ID,
        review_document_id=manifest.review_document_id,
        review_document_version_id=(
            manifest.review_document_version_id
        ),
        review_revision_id=manifest.review_revision_id,
        subjects=(subject,),
        relationships=(),
        relationship_decision_authority_fingerprint="f" * 64,
        content_fingerprint=canonical_sha(body),
        non_promotable_subject_ids=(),
        non_projectable_relationship_decision_ids=(),
    )


def bindings(rec=None, *, same_stable_key=False):
    rec = reconciliation() if rec is None else rec
    manifests, events, aei_sets = authority_inputs(
        same_stable_key=same_stable_key
    )
    return (
        rec,
        manifests,
        events,
        aei_sets,
        prepare_project_authority_bindings(
            rec,
            manifests,
            events,
            aei_sets,
        ),
    )


def decision(
    rec,
    subject_bindings,
    *,
    outcome,
    retained=None,
    concern=None,
    decision_id="PEAD-000001",
):
    left, right = refs()
    return create_project_authority_decision(
        rec,
        subject_bindings,
        decision_id=decision_id,
        left_subject_ref=left,
        right_subject_ref=right,
        outcome=outcome,
        authority_concern_id=concern,
        retained_approved_input_id=retained,
        reviewer_identity="human-reviewer",
        rationale="Explicit project-level Human Engineering Authority decision.",
        decided_at=TIMESTAMP,
    )


def test_bindings_resolve_same_local_subject_id_to_distinct_source_authority():
    rec, manifests, events, aei_sets, subject_bindings = bindings()
    assert tuple(
        item.canonical_subject_id
        for item in subject_bindings
    ) == ("SUBJ-000001", "SUBJ-000001")
    assert tuple(
        item.approved_input_id
        for item in subject_bindings
    ) == ("AIN-000001", "AIN-000002")
    assert tuple(
        item.source_id
        for item in subject_bindings
    ) == ("SRC-000001", "SRC-000002")


def test_binding_requires_source_local_aei_for_every_s3_subject():
    rec = reconciliation()
    manifests, events, aei_sets = authority_inputs()
    with pytest.raises(
        ProjectEngineeringAuthorityIntegrityError,
        match="Every S3 Subject",
    ):
        prepare_project_authority_bindings(
            rec,
            manifests,
            events,
            aei_sets[:1],
        )


def test_tampered_aei_is_rejected():
    rec = reconciliation()
    manifests, events, aei_sets = authority_inputs()
    tampered = replace(
        aei_sets[0],
        content_fingerprint="0" * 64,
    )
    with pytest.raises(
        ProjectEngineeringAuthorityIntegrityError,
        match="AEI|Approved Engineering Information",
    ):
        prepare_project_authority_bindings(
            rec,
            manifests,
            events,
            (tampered, aei_sets[1]),
        )


def test_inactive_approved_input_is_rejected():
    rec = reconciliation()
    manifests, _, aei_sets = authority_inputs()
    first = manifests[0]
    event = create_approved_input_event(
        project_id=PROJECT_ID,
        approved_input_event_id="AIE-000001",
        approved_input_id=first.approved_input_id,
        event_type="invalidated",
        reason_code="source_authority_invalidated",
        rationale="No longer source-local authority.",
        actor_identity="human-reviewer",
        successor_approved_input_id=None,
        causal_review_document_id=None,
        causal_review_document_version_id=None,
        causal_review_revision_id=None,
        causal_finalization_decision_id=None,
        causal_finalization_decision_fingerprint=None,
        occurred_at="2026-08-31T07:31:00Z",
        previous_event_fingerprint=None,
    )
    with pytest.raises(
        ProjectEngineeringAuthorityIntegrityError,
        match="not currently active",
    ):
        prepare_project_authority_bindings(
            rec,
            manifests,
            (event,),
            aei_sets,
        )


def test_remain_independent_keeps_both_active_without_common_identity():
    rec, manifests, events, aei_sets, subject_bindings = bindings()
    human = decision(
        rec,
        subject_bindings,
        outcome="remain_independent",
    )
    state = build_project_engineering_authority_state(
        rec,
        manifests,
        events,
        aei_sets,
        (human,),
    )
    assert tuple(
        entry.project_authority_state
        for entry in state.entries
    ) == ("active", "active")
    assert all(
        entry.authority_concern_ids == ()
        for entry in state.entries
    )
    assert state.model_impact_ready is True


def test_coexist_requires_explicit_human_concern_identity():
    rec, manifests, events, aei_sets, subject_bindings = bindings()
    with pytest.raises(
        ProjectEngineeringAuthorityValidationError,
        match="requires an explicit Human authority_concern_id",
    ):
        decision(
            rec,
            subject_bindings,
            outcome="coexist",
        )

    human = decision(
        rec,
        subject_bindings,
        outcome="coexist",
        concern="PEAC-000001",
    )
    state = build_project_engineering_authority_state(
        rec,
        manifests,
        events,
        aei_sets,
        (human,),
    )
    assert all(
        entry.project_authority_state == "active"
        for entry in state.entries
    )
    assert all(
        entry.authority_concern_ids == ("PEAC-000001",)
        for entry in state.entries
    )


def test_same_stable_subject_key_never_creates_project_identity_automatically():
    rec, manifests, events, aei_sets, subject_bindings = bindings(
        same_stable_key=True
    )
    assert (
        subject_bindings[0].stable_subject_key
        == subject_bindings[1].stable_subject_key
    )
    human = decision(
        rec,
        subject_bindings,
        outcome="remain_independent",
    )
    state = build_project_engineering_authority_state(
        rec,
        manifests,
        events,
        aei_sets,
        (human,),
    )
    assert all(
        entry.authority_concern_ids == ()
        for entry in state.entries
    )


def test_supersede_is_project_level_only_and_keeps_source_manifests_immutable():
    rec, manifests, events, aei_sets, subject_bindings = bindings()
    human = decision(
        rec,
        subject_bindings,
        outcome="supersede",
        concern="PEAC-000001",
        retained="AIN-000002",
    )
    state = build_project_engineering_authority_state(
        rec,
        manifests,
        events,
        aei_sets,
        (human,),
    )
    by_id = {
        entry.approved_input_id: entry
        for entry in state.entries
    }
    assert by_id["AIN-000001"].project_authority_state == "superseded"
    assert by_id["AIN-000002"].project_authority_state == "active"
    assert manifests[0].authority_state == "active"
    assert manifests[1].authority_state == "active"


def test_supersede_can_bridge_different_source_local_stable_subject_keys():
    rec, manifests, events, aei_sets, subject_bindings = bindings()
    assert (
        subject_bindings[0].stable_subject_key
        != subject_bindings[1].stable_subject_key
    )
    human = decision(
        rec,
        subject_bindings,
        outcome="supersede",
        concern="PEAC-000002",
        retained="AIN-000001",
    )
    state = build_project_engineering_authority_state(
        rec,
        manifests,
        events,
        aei_sets,
        (human,),
    )
    assert state.entries[0].project_authority_state == "active"
    assert state.entries[1].project_authority_state == "superseded"


def test_unresolved_blocks_s5_model_impact_readiness():
    rec, manifests, events, aei_sets, subject_bindings = bindings()
    human = decision(
        rec,
        subject_bindings,
        outcome="unresolved",
    )
    state = build_project_engineering_authority_state(
        rec,
        manifests,
        events,
        aei_sets,
        (human,),
    )
    assert all(
        entry.project_authority_state == "unresolved"
        for entry in state.entries
    )
    assert state.unresolved_decision_ids == ("PEAD-000001",)
    assert state.model_impact_ready is False


@pytest.mark.parametrize(
    "machine_outcome,human_outcome,concern",
    (
        ("equivalent", "remain_independent", None),
        ("distinct", "coexist", "PEAC-000003"),
        ("potential_conflict", "coexist", "PEAC-000004"),
        ("uncertain", "remain_independent", None),
    ),
)
def test_machine_relation_never_dictates_human_authority(
    machine_outcome,
    human_outcome,
    concern,
):
    rec = reconciliation(machine_outcome)
    (
        rec,
        manifests,
        events,
        aei_sets,
        subject_bindings,
    ) = bindings(rec)
    human = decision(
        rec,
        subject_bindings,
        outcome=human_outcome,
        concern=concern,
    )
    assert human.machine_relation_outcome == machine_outcome
    assert human.outcome == human_outcome
    state = build_project_engineering_authority_state(
        rec,
        manifests,
        events,
        aei_sets,
        (human,),
    )
    assert state.model_impact_ready is True


def test_every_s3_relation_requires_exactly_one_human_decision():
    rec, manifests, events, aei_sets, _ = bindings()
    with pytest.raises(
        ProjectEngineeringAuthorityIntegrityError,
        match="Every S3 semantic relation",
    ):
        build_project_engineering_authority_state(
            rec,
            manifests,
            events,
            aei_sets,
            (),
        )


def test_duplicate_human_decision_for_same_relation_is_rejected():
    rec, manifests, events, aei_sets, subject_bindings = bindings()
    first = decision(
        rec,
        subject_bindings,
        outcome="remain_independent",
        decision_id="PEAD-000001",
    )
    second = decision(
        rec,
        subject_bindings,
        outcome="remain_independent",
        decision_id="PEAD-000002",
    )
    with pytest.raises(
        ProjectEngineeringAuthorityIntegrityError,
        match="exactly one Human",
    ):
        build_project_engineering_authority_state(
            rec,
            manifests,
            events,
            aei_sets,
            (first, second),
        )


def test_unresolved_and_independent_must_not_fabricate_concern_identity():
    rec, _, _, _, subject_bindings = bindings()
    for outcome in ("remain_independent", "unresolved"):
        with pytest.raises(
            ProjectEngineeringAuthorityValidationError,
            match="must not establish",
        ):
            decision(
                rec,
                subject_bindings,
                outcome=outcome,
                concern="PEAC-000010",
            )


def test_supersede_requires_one_retained_participant():
    rec, _, _, _, subject_bindings = bindings()
    with pytest.raises(
        ProjectEngineeringAuthorityValidationError,
        match="retained participant",
    ):
        decision(
            rec,
            subject_bindings,
            outcome="supersede",
            concern="PEAC-000001",
        )
    with pytest.raises(
        ProjectEngineeringAuthorityValidationError,
        match="retained participant",
    ):
        decision(
            rec,
            subject_bindings,
            outcome="supersede",
            concern="PEAC-000001",
            retained="AIN-999999",
        )


def test_serialization_preserves_human_and_source_authority_provenance():
    rec, manifests, events, aei_sets, subject_bindings = bindings()
    human = decision(
        rec,
        subject_bindings,
        outcome="coexist",
        concern="PEAC-000001",
    )
    state = build_project_engineering_authority_state(
        rec,
        manifests,
        events,
        aei_sets,
        (human,),
    )
    payload = json.loads(
        project_engineering_authority_to_json(state)
    )
    assert payload["reconciliation_fingerprint"] == rec.content_fingerprint
    assert payload["decisions"][0]["reviewer_identity"] == "human-reviewer"
    assert payload["decisions"][0]["authority_concern_id"] == "PEAC-000001"
    assert payload["bindings"][0]["source_id"] == "SRC-000001"
    assert payload["bindings"][1]["source_id"] == "SRC-000002"
    assert payload["bindings"][0]["approved_input_id"] == "AIN-000001"
    assert payload["bindings"][1]["approved_input_id"] == "AIN-000002"


def test_tampered_project_authority_state_fails_closed():
    rec, manifests, events, aei_sets, subject_bindings = bindings()
    human = decision(
        rec,
        subject_bindings,
        outcome="coexist",
        concern="PEAC-000001",
    )
    state = build_project_engineering_authority_state(
        rec,
        manifests,
        events,
        aei_sets,
        (human,),
    )
    tampered = replace(
        state,
        model_impact_ready=False,
    )
    with pytest.raises(
        ProjectEngineeringAuthorityIntegrityError
    ):
        project_engineering_authority_to_json(tampered)
