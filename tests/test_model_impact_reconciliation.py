"""Tests for ADR-032 S5 Model Impact Reconciliation."""

from __future__ import annotations

from dataclasses import replace
import json
from types import SimpleNamespace

import pytest

from modules.internal_model import build_authority_backed_internal_model
from modules.model_impact_reconciliation import (
    ModelImpactReconciliationIntegrityError,
    ModelImpactReconciliationValidationError,
    model_impact_reconciliation_to_json,
    reconcile_model_impact,
)
from modules.project_engineering_authority import (
    build_project_engineering_authority_state,
)

from tests.test_project_engineering_authority import (
    PROJECT_ID,
    TIMESTAMP,
    bindings,
    decision,
)


def authority_state(
    *,
    outcome="remain_independent",
    concern=None,
    retained=None,
):
    rec, manifests, events, aei_sets, subject_bindings = bindings()
    human = decision(
        rec,
        subject_bindings,
        outcome=outcome,
        concern=concern,
        retained=retained,
    )
    return build_project_engineering_authority_state(
        rec,
        manifests,
        events,
        aei_sets,
        (human,),
    )


def accepted_model(
    project_authority,
    represented_ain_ids=(),
    *,
    extra_elements=(),
):
    entry_by_id = {
        entry.approved_input_id: entry
        for entry in project_authority.entries
    }

    profile_id = "MSCP-TEST"
    profile_version = "1.0.0"
    profile_fingerprint = "5" * 64
    comparison_fingerprint = "1" * 64
    draft_fingerprint = "2" * 64
    placement_fingerprint = "3" * 64
    aei_fingerprint = "4" * 64

    elements = []
    for index, approved_input_id in enumerate(
        represented_ain_ids,
        start=1,
    ):
        entry = entry_by_id[approved_input_id]
        elements.append(
            SimpleNamespace(
                approved_input_id=approved_input_id,
                stable_subject_key=entry.stable_subject_key,
                title=f"Accepted {approved_input_id}",
                primary_text=f"Accepted model statement {approved_input_id}.",
                model_area="requirements",
                element_type="requirement",
                framework_assignment="FN-REQ",
                placement_decision_id=f"MPD-{index:06d}",
                placement_decision_fingerprint=f"{index}" * 64,
            )
        )

    next_index = len(elements) + 1
    for offset, (approved_input_id, stable_subject_key) in enumerate(
        extra_elements,
        start=next_index,
    ):
        elements.append(
            SimpleNamespace(
                approved_input_id=approved_input_id,
                stable_subject_key=stable_subject_key,
                title=f"Existing unrelated {approved_input_id}",
                primary_text=f"Existing model statement {approved_input_id}.",
                model_area="requirements",
                element_type="requirement",
                framework_assignment="FN-REQ",
                placement_decision_id=f"MPD-{offset:06d}",
                placement_decision_fingerprint="a" * 64,
            )
        )

    draft = SimpleNamespace(
        project_id=PROJECT_ID,
        comparison_fingerprint=comparison_fingerprint,
        content_fingerprint=draft_fingerprint,
        approved_placement_set_fingerprint=placement_fingerprint,
        approved_engineering_information_fingerprint=aei_fingerprint,
        profile_id=profile_id,
        profile_version=profile_version,
        profile_fingerprint=profile_fingerprint,
        elements=tuple(elements),
        relationships=(),
    )
    final_decision = SimpleNamespace(
        decision="approved",
        project_id=PROJECT_ID,
        comparison_fingerprint=comparison_fingerprint,
        assembly_draft_fingerprint=draft_fingerprint,
        approved_placement_set_fingerprint=placement_fingerprint,
        approved_engineering_information_fingerprint=aei_fingerprint,
        final_assembly_decision_id="FAD-000001",
        decision_fingerprint="7" * 64,
        relationship_resolutions=(),
    )
    profile = SimpleNamespace(
        profile_id=profile_id,
        profile_version=profile_version,
        profile_fingerprint=profile_fingerprint,
        model_areas=(
            SimpleNamespace(
                model_area_id="requirements",
                framework_node_id="FN-REQ",
                permitted_element_types=("requirement",),
            ),
        ),
        relationship_semantics=(),
    )
    framework_template = {
        "template_id": "TURING_RFLP_FRAMEWORK",
        "template_version": "1.0.0",
        "nodes": [
            {
                "node_id": "FN-REQ",
                "mapping_key": "requirements",
                "name": "Requirements",
                "node_type": "package",
                "parent_node_id": None,
                "order": 1,
            }
        ],
    }
    return build_authority_backed_internal_model(
        draft=draft,
        final_decision=final_decision,
        profile=profile,
        framework_template=framework_template,
        internal_engineering_model_id="IEM-000001",
        created_at=TIMESTAMP,
    )


def proposals_by_id(artifact):
    return {
        proposal.approved_input_id: proposal
        for proposal in artifact.proposals
    }


def test_no_existing_model_makes_active_authority_new():
    state = authority_state()
    artifact = reconcile_model_impact(state, None)
    assert tuple(
        proposal.outcome
        for proposal in artifact.proposals
    ) == ("new", "new")
    assert artifact.accepted_model_id is None
    assert artifact.model_change_required is True
    assert artifact.human_model_review_required is True


def test_exact_existing_authority_is_retained():
    state = authority_state()
    model = accepted_model(
        state,
        ("AIN-000001", "AIN-000002"),
    )
    artifact = reconcile_model_impact(state, model)
    assert tuple(
        proposal.outcome
        for proposal in artifact.proposals
    ) == ("retain", "retain")
    assert artifact.model_change_required is False
    assert artifact.accepted_model_id == "IEM-000001"
    assert artifact.accepted_model_fingerprint == model.content_fingerprint


def test_coexisting_new_authority_extends_existing_concern():
    state = authority_state(
        outcome="coexist",
        concern="PEAC-000001",
    )
    model = accepted_model(state, ("AIN-000001",))
    artifact = reconcile_model_impact(state, model)
    values = proposals_by_id(artifact)
    assert values["AIN-000001"].outcome == "retain"
    assert values["AIN-000002"].outcome == "extend"
    assert values["AIN-000002"].related_model_element_ids == (
        "IME-000001",
    )
    assert values["AIN-000002"].model_change_required is True


def test_human_successor_modifies_existing_concern():
    state = authority_state(
        outcome="supersede",
        concern="PEAC-000001",
        retained="AIN-000002",
    )
    model = accepted_model(state, ("AIN-000001",))
    artifact = reconcile_model_impact(state, model)
    values = proposals_by_id(artifact)

    assert values["AIN-000001"].outcome == "supersede"
    assert values["AIN-000001"].model_change_required is True
    assert values["AIN-000002"].outcome == "modify"
    assert values["AIN-000002"].related_model_element_ids == (
        "IME-000001",
    )


def test_superseded_authority_absent_from_model_needs_no_model_change():
    state = authority_state(
        outcome="supersede",
        concern="PEAC-000001",
        retained="AIN-000002",
    )
    model = accepted_model(state, ())
    artifact = reconcile_model_impact(state, model)
    values = proposals_by_id(artifact)
    assert values["AIN-000001"].outcome == "supersede"
    assert values["AIN-000001"].model_change_required is False
    assert values["AIN-000002"].outcome == "new"
    assert values["AIN-000002"].model_change_required is True


def test_existing_retained_successor_stays_retain():
    state = authority_state(
        outcome="supersede",
        concern="PEAC-000001",
        retained="AIN-000002",
    )
    model = accepted_model(
        state,
        ("AIN-000001", "AIN-000002"),
    )
    artifact = reconcile_model_impact(state, model)
    values = proposals_by_id(artifact)
    assert values["AIN-000001"].outcome == "supersede"
    assert values["AIN-000002"].outcome == "retain"


def test_s4_unresolved_authority_blocks_s5():
    state = authority_state(outcome="unresolved")
    assert state.model_impact_ready is False
    with pytest.raises(
        ModelImpactReconciliationIntegrityError,
        match="S5 is blocked",
    ):
        reconcile_model_impact(state, None)


def test_accepted_model_project_must_match_authority():
    state = authority_state()
    model = accepted_model(state, ("AIN-000001",))
    foreign = replace(model, project_id="999999")
    with pytest.raises(
        ModelImpactReconciliationValidationError,
        match="Accepted authority-backed Internal Model is invalid",
    ):
        reconcile_model_impact(state, foreign)


def test_model_traceability_stable_subject_key_mismatch_fails_closed():
    state = authority_state()
    model = accepted_model(state, ("AIN-000001",))
    bad_element = replace(
        model.elements[0],
        model_subject_key="wrong-subject-key",
    )
    # This also makes the accepted model fingerprint stale. S5 must reject it
    # before attempting impact inference.
    tampered = replace(
        model,
        elements=(bad_element,),
    )
    with pytest.raises(
        ModelImpactReconciliationValidationError,
        match="Accepted authority-backed Internal Model is invalid",
    ):
        reconcile_model_impact(state, tampered)


def test_unrelated_accepted_model_elements_are_reported_unaffected():
    state = authority_state()
    model = accepted_model(
        state,
        (),
        extra_elements=(("AIN-009999", "unrelated-subject"),),
    )
    artifact = reconcile_model_impact(state, model)
    assert artifact.unaffected_model_element_ids == ("IME-000001",)
    assert artifact.unaffected_model_relationship_ids == ()


def test_stable_subject_key_alone_never_authorizes_model_continuity():
    state = authority_state()
    stable_key = {
        entry.approved_input_id: entry.stable_subject_key
        for entry in state.entries
    }["AIN-000001"]
    model = accepted_model(
        state,
        (),
        extra_elements=(("AIN-009999", stable_key),),
    )
    artifact = reconcile_model_impact(state, model)
    values = proposals_by_id(artifact)

    assert values["AIN-000001"].outcome == "unresolved"
    assert values["AIN-000001"].model_change_required is False
    assert values["AIN-000001"].related_model_element_ids == (
        "IME-000001",
    )
    assert artifact.unresolved_approved_input_ids == ("AIN-000001",)
    assert artifact.human_model_review_required is True


def test_model_authority_metadata_is_bound_into_s5_artifact():
    state = authority_state()
    model = accepted_model(state, ("AIN-000001",))
    artifact = reconcile_model_impact(state, model)
    assert (
        artifact.accepted_model_final_review_decision_id
        == model.final_model_review_decision_id
    )
    assert (
        artifact.accepted_model_final_review_decision_fingerprint
        == model.final_model_review_decision_fingerprint
    )
    assert artifact.accepted_model_profile_id == model.profile_id
    assert artifact.accepted_model_profile_version == model.profile_version
    assert (
        artifact.accepted_model_profile_fingerprint
        == model.profile_fingerprint
    )


def test_s5_never_mutates_accepted_model():
    state = authority_state(
        outcome="supersede",
        concern="PEAC-000001",
        retained="AIN-000002",
    )
    model = accepted_model(state, ("AIN-000001",))
    original = model
    artifact = reconcile_model_impact(state, model)
    assert model == original
    assert proposals_by_id(artifact)["AIN-000001"].outcome == "supersede"


def test_serialization_preserves_s4_and_model_authority_bindings():
    state = authority_state(
        outcome="coexist",
        concern="PEAC-000001",
    )
    model = accepted_model(state, ("AIN-000001",))
    artifact = reconcile_model_impact(state, model)
    payload = json.loads(
        model_impact_reconciliation_to_json(artifact)
    )
    assert (
        payload["project_authority_fingerprint"]
        == state.content_fingerprint
    )
    assert (
        payload["accepted_model_fingerprint"]
        == model.content_fingerprint
    )
    assert payload["human_model_review_required"] is True
    assert payload["proposals"][1]["outcome"] == "extend"


def test_tampered_s5_artifact_fails_closed():
    state = authority_state()
    artifact = reconcile_model_impact(state, None)
    tampered = replace(
        artifact,
        model_change_required=False,
    )
    with pytest.raises(
        ModelImpactReconciliationIntegrityError
    ):
        model_impact_reconciliation_to_json(tampered)


def test_human_model_review_is_always_required_even_when_all_retained():
    state = authority_state()
    model = accepted_model(
        state,
        ("AIN-000001", "AIN-000002"),
    )
    artifact = reconcile_model_impact(state, model)
    assert artifact.model_change_required is False
    assert artifact.unresolved_approved_input_ids == ()
    assert artifact.human_model_review_required is True
