"""ADR-032 I1B: Multi-Source authority binding through Assembly -> Final Review -> IEM."""

from __future__ import annotations

from dataclasses import replace
import json
from types import SimpleNamespace

import pytest

from modules.internal_model.authority_backed import (
    authority_backed_internal_model_from_json,
    authority_backed_internal_model_to_json,
    build_authority_backed_internal_model,
)
from modules.model_assembly import (
    build_model_assembly_draft,
    create_final_model_review_decision,
)
from modules.model_assembly.builder import (
    model_assembly_draft_from_json,
    model_assembly_draft_to_json,
)
from modules.model_assembly.final_review import (
    final_model_review_decision_from_json,
    final_model_review_decision_to_json,
)
from modules.model_candidates import (
    create_project_authority_phase_h_handoff,
    phase_h_subject_key,
    select_project_authority_active_inputs,
)
from modules.model_impact_reconciliation import reconcile_model_impact
from modules.model_placement.errors import ModelPlacementContractError
from modules.project_engineering_authority import (
    build_project_engineering_authority_state,
)

from tests.test_project_engineering_authority import (
    PROJECT_ID,
    TIMESTAMP,
    bindings,
    decision,
)


def _context(*, same_stable_key=True):
    rec, manifests, events, aeis, subject_bindings = bindings(
        same_stable_key=same_stable_key
    )
    human = decision(
        rec,
        subject_bindings,
        outcome="remain_independent",
    )
    authority = build_project_engineering_authority_state(
        rec,
        manifests,
        events,
        aeis,
        (human,),
    )
    impact = reconcile_model_impact(authority, None)
    handoff = create_project_authority_phase_h_handoff(
        project_authority=authority,
        model_impact=impact,
        approved_input_manifests=manifests,
        approved_engineering_information_sets=aeis,
    )
    active = select_project_authority_active_inputs(
        manifests,
        handoff,
    )
    request = SimpleNamespace(
        project_id=PROJECT_ID,
        approved_inputs=active,
        approved_engineering_information=None,
        project_authority_handoff=handoff,
    )
    return request, handoff, authority, impact, aeis


def _profile():
    return SimpleNamespace(
        profile_id="PROFILE",
        profile_version="1.0.0",
        profile_fingerprint="a" * 64,
        model_areas=(
            SimpleNamespace(
                model_area_id="requirements",
                framework_node_id="FN-REQ",
                permitted_element_types=("requirement",),
            ),
        ),
        relationship_semantics=(),
    )


def _placement_set(request):
    placements = tuple(
        SimpleNamespace(
            approved_input_id=item.approved_input_id,
            stable_subject_key=phase_h_subject_key(request, item),
            selected_rule_id="RULE-1",
            model_area="requirements",
            element_type="requirement",
            framework_assignment="FN-REQ",
            review_decision_id=f"MPD-{index:06d}",
            review_decision_fingerprint=str(index) * 64,
        )
        for index, item in enumerate(
            request.approved_inputs,
            start=1,
        )
    )
    return SimpleNamespace(
        project_id=PROJECT_ID,
        comparison_fingerprint="b" * 64,
        profile_id="PROFILE",
        profile_version="1.0.0",
        profile_fingerprint="a" * 64,
        placements=placements,
        explicitly_not_materialized_approved_input_ids=(),
        content_fingerprint="c" * 64,
    )


def _draft():
    request, handoff, authority, impact, aeis = _context()
    draft = build_model_assembly_draft(
        request=request,
        approved_placement_set=_placement_set(request),
        profile=_profile(),
        relationship_executor=None,
    )
    return draft, request, handoff, authority, impact, aeis


def _final(draft):
    return create_final_model_review_decision(
        draft=draft,
        profile=_profile(),
        final_assembly_decision_id="FAD-000001",
        decision="approved",
        selected_relationship_rules={},
        reviewer_identity="human-reviewer",
        rationale="Approved project-level multi-source model.",
        reviewed_at=TIMESTAMP,
    )


def _framework():
    return {
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


def test_multisource_assembly_uses_additive_project_authority_binding():
    draft, _, handoff, authority, impact, aeis = _draft()

    assert draft.schema_version == "1.1.0"
    assert draft.approved_engineering_information_fingerprint is None
    assert (
        draft.project_authority_handoff_fingerprint
        == handoff.content_fingerprint
    )
    assert (
        draft.project_engineering_authority_fingerprint
        == authority.content_fingerprint
    )
    assert (
        draft.model_impact_reconciliation_fingerprint
        == impact.content_fingerprint
    )
    assert draft.source_approved_engineering_information_fingerprints == tuple(
        sorted(item.content_fingerprint for item in aeis)
    )


def test_multisource_assembly_keeps_source_scoped_model_subject_identity():
    draft, _, _, _, _, _ = _draft()

    keys = tuple(item.stable_subject_key for item in draft.elements)
    assert keys == (
        "project_subject:src-000001:remote-viewing",
        "project_subject:src-000002:remote-viewing",
    )
    assert len(set(keys)) == 2


def test_multisource_assembly_roundtrip_preserves_authority_binding():
    draft, _, _, _, _, _ = _draft()
    loaded = model_assembly_draft_from_json(
        model_assembly_draft_to_json(draft)
    )
    assert loaded == draft
    payload = json.loads(model_assembly_draft_to_json(draft))
    assert payload["approved_engineering_information_fingerprint"] is None
    assert payload["project_authority_handoff_fingerprint"] is not None


def test_final_model_review_binds_exact_multisource_authority():
    draft, _, _, _, _, _ = _draft()
    final = _final(draft)

    assert final.schema_version == "1.1.0"
    assert final.approved_engineering_information_fingerprint is None
    assert (
        final.project_authority_handoff_fingerprint
        == draft.project_authority_handoff_fingerprint
    )
    assert (
        final.source_approved_engineering_information_fingerprints
        == draft.source_approved_engineering_information_fingerprints
    )
    assert final_model_review_decision_from_json(
        final_model_review_decision_to_json(final)
    ) == final


def test_internal_model_carries_multisource_authority_binding():
    draft, _, _, _, _, _ = _draft()
    final = _final(draft)

    snapshot = build_authority_backed_internal_model(
        draft=draft,
        final_decision=final,
        profile=_profile(),
        framework_template=_framework(),
        internal_engineering_model_id="IEM-000001",
        created_at=TIMESTAMP,
    )

    assert snapshot.schema_version == "2.2.0"
    assert snapshot.approved_engineering_information_fingerprint is None
    assert (
        snapshot.project_authority_handoff_fingerprint
        == draft.project_authority_handoff_fingerprint
    )
    assert (
        snapshot.project_engineering_authority_fingerprint
        == draft.project_engineering_authority_fingerprint
    )
    assert (
        snapshot.model_impact_reconciliation_fingerprint
        == draft.model_impact_reconciliation_fingerprint
    )
    assert tuple(item.model_subject_key for item in snapshot.elements) == (
        "project_subject:src-000001:remote-viewing",
        "project_subject:src-000002:remote-viewing",
    )


def test_internal_model_multisource_roundtrip_is_exact():
    draft, _, _, _, _, _ = _draft()
    final = _final(draft)
    snapshot = build_authority_backed_internal_model(
        draft=draft,
        final_decision=final,
        profile=_profile(),
        framework_template=_framework(),
        internal_engineering_model_id="IEM-000001",
        created_at=TIMESTAMP,
    )

    loaded = authority_backed_internal_model_from_json(
        authority_backed_internal_model_to_json(snapshot)
    )
    assert loaded == snapshot


def test_tampered_final_review_project_authority_binding_fails_closed():
    draft, _, _, _, _, _ = _draft()
    final = _final(draft)
    tampered = replace(
        final,
        project_authority_handoff_fingerprint="0" * 64,
    )

    with pytest.raises(
        ModelPlacementContractError,
        match="exact Assembly Draft",
    ):
        build_authority_backed_internal_model(
            draft=draft,
            final_decision=tampered,
            profile=_profile(),
            framework_template=_framework(),
            internal_engineering_model_id="IEM-000001",
            created_at=TIMESTAMP,
        )


def test_multisource_assembly_rejects_synthetic_single_aei_envelope():
    draft, request, _, _, _, aeis = _draft()
    del draft
    invalid_request = SimpleNamespace(
        project_id=request.project_id,
        approved_inputs=request.approved_inputs,
        approved_engineering_information=aeis[0],
        project_authority_handoff=request.project_authority_handoff,
    )

    with pytest.raises(
        ModelPlacementContractError,
        match="exactly one engineering authority mode",
    ):
        build_model_assembly_draft(
            request=invalid_request,
            approved_placement_set=_placement_set(request),
            profile=_profile(),
            relationship_executor=None,
        )
