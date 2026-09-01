"""Focused ADR-032 I1A tests for Project Authority -> Phase-H handoff."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from modules.model_candidates import (
    ModelCandidateDerivationPlan,
    ModelCandidateGenerationProvenance,
    ModelCandidateGenerationService,
    ModelDerivationRulesReference,
    ModelElementCandidateDraft,
    ModelStructureProfileReference,
    create_project_authority_phase_h_handoff,
    phase_h_subject_key,
    select_project_authority_active_inputs,
)
from modules.model_candidates.errors import (
    ModelCandidateGenerationBlockedError,
    ModelCandidateReferenceError,
)
from modules.model_candidates.types import (
    ModelCandidateApprovedInputSelection,
    ModelCandidateProjectionCoverage,
    ModelCandidateProjectionDisposition,
    StructuralProfileConformance,
)
from modules.model_impact_reconciliation import (
    reconcile_model_impact,
)
from modules.model_placement.request_builder import (
    build_model_placement_request,
)
from modules.project_engineering_authority import (
    build_project_engineering_authority_state,
)
from modules.project_workspace.types import FrameworkTemplateReference

from tests.test_project_engineering_authority import (
    PROJECT_ID,
    bindings,
    decision,
)


def _authority(
    *,
    same_stable_key=False,
    outcome="remain_independent",
    retained=None,
    concern=None,
):
    rec, manifests, events, aeis, subject_bindings = bindings(
        same_stable_key=same_stable_key
    )
    human = decision(
        rec,
        subject_bindings,
        outcome=outcome,
        retained=retained,
        concern=concern,
    )
    state = build_project_engineering_authority_state(
        rec,
        manifests,
        events,
        aeis,
        (human,),
    )
    impact = reconcile_model_impact(state, None)
    return state, impact, manifests, aeis


def _handoff(**kwargs):
    state, impact, manifests, aeis = _authority(**kwargs)
    value = create_project_authority_phase_h_handoff(
        project_authority=state,
        model_impact=impact,
        approved_input_manifests=manifests,
        approved_engineering_information_sets=aeis,
    )
    return value, state, impact, manifests, aeis


def _request(value, manifests):
    return SimpleNamespace(
        project_id=PROJECT_ID,
        approved_inputs=select_project_authority_active_inputs(
            manifests,
            value,
        ),
        approved_engineering_information=None,
        project_authority_handoff=value,
    )


def test_same_local_subject_key_is_source_scoped_in_multi_source():
    value, _, _, _, _ = _handoff(same_stable_key=True)

    assert value.subject_key_mode == "source_scoped"
    assert tuple(
        item.phase_h_subject_key
        for item in value.subjects
    ) == (
        "project_subject:src-000001:remote-viewing",
        "project_subject:src-000002:remote-viewing",
    )


def test_source_local_aei_sets_remain_separate_and_exact():
    value, _, _, _, aeis = _handoff()

    assert len(value.source_aei_references) == 2
    assert {
        item.content_fingerprint
        for item in value.source_aei_references
    } == {
        item.content_fingerprint
        for item in aeis
    }


def test_project_superseded_ain_is_filtered_from_phase_h():
    value, _, _, manifests, _ = _handoff(
        outcome="supersede",
        concern="PEAC-000001",
        retained="AIN-000002",
    )

    assert {
        item.approved_input_id: item.project_authority_state
        for item in value.subjects
    } == {
        "AIN-000001": "superseded",
        "AIN-000002": "active",
    }
    assert tuple(
        item.approved_input_id
        for item in select_project_authority_active_inputs(
            manifests,
            value,
        )
    ) == ("AIN-000002",)


def test_stale_model_impact_binding_is_rejected():
    state_a, _, manifests_a, aeis_a = _authority()
    state_b, impact_b, _, _ = _authority(
        outcome="coexist",
        concern="PEAC-000001",
    )
    assert state_a.content_fingerprint != state_b.content_fingerprint

    with pytest.raises(ModelCandidateReferenceError):
        create_project_authority_phase_h_handoff(
            project_authority=state_a,
            model_impact=impact_b,
            approved_input_manifests=manifests_a,
            approved_engineering_information_sets=aeis_a,
        )


def test_phase_h_subject_key_is_legacy_without_handoff():
    _, _, manifests, _ = _authority()
    request = SimpleNamespace(
        approved_engineering_information=None,
        project_authority_handoff=None,
    )

    assert phase_h_subject_key(
        request,
        manifests[0],
    ) == manifests[0].stable_subject_key


def _coverage(request):
    return ModelCandidateProjectionCoverage(
        project_id=PROJECT_ID,
        model_structure_profile_reference=ModelStructureProfileReference(
            profile_id="PROFILE",
            profile_version="1.0.0",
            profile_fingerprint="a" * 64,
        ),
        entries=tuple(
            ModelCandidateProjectionDisposition(
                approved_input_id=item.approved_input_id,
                approved_input_kind=item.approved_input_kind,
                disposition="mapped",
                reason_code="fixture",
                selected_rule_id="RULE-1",
                candidate_rule_ids=("RULE-1",),
                rationale="fixture",
            )
            for item in request.approved_inputs
        ),
    )


def _placement_profile():
    return SimpleNamespace(
        profile_id="PROFILE",
        profile_version="1.0.0",
        profile_fingerprint="a" * 64,
        element_derivation_rules=(
            SimpleNamespace(
                rule_id="RULE-1",
                model_area_id="requirements",
                element_type="requirement",
                information_type_values=("constraint",),
            ),
        ),
        model_areas=(
            SimpleNamespace(
                model_area_id="requirements",
                framework_node_id="FN-REQ",
            ),
        ),
    )


def test_model_placement_request_uses_project_safe_subject_keys():
    value, _, _, manifests, _ = _handoff(
        same_stable_key=True
    )
    request = _request(value, manifests)

    placement = build_model_placement_request(
        request=request,
        coverage=_coverage(request),
        profile=_placement_profile(),
    )

    assert tuple(
        item.stable_subject_key
        for item in placement.items
    ) == (
        "project_subject:src-000001:remote-viewing",
        "project_subject:src-000002:remote-viewing",
    )


class _Workspace:
    def load_project(self, project_id):
        return SimpleNamespace(
            framework_template=FrameworkTemplateReference(
                template_id="TURING_RFLP_FRAMEWORK",
                template_version="1.0.0",
            )
        )


class _ApprovedInputRepo:
    def __init__(self, values):
        self.values = values

    def list_active_approved_inputs(self, project_id):
        return self.values


class _CandidateRepo:
    def list_candidate_sets(self, project_id):
        return ()

    def next_candidate_set_id(self, project_id):
        return "MCS-000001"

    def persist_candidate_set(
        self,
        manifest,
        *,
        element_candidates,
        relationship_candidates,
    ):
        return SimpleNamespace(
            manifest=manifest,
            element_candidates=element_candidates,
            relationship_candidates=relationship_candidates,
        )


class _Deriver:
    def __init__(self):
        self.requests = []

    def derive(self, request):
        self.requests.append(request)
        item = request.approved_inputs[0]
        return ModelCandidateDerivationPlan(
            element_drafts=(
                ModelElementCandidateDraft(
                    draft_key="element:fixture",
                    candidate_subject_key=phase_h_subject_key(
                        request,
                        item,
                    ),
                    comparison_anchor_id=None,
                    proposed_name="Fixture",
                    description=None,
                    model_area="requirements",
                    element_type="requirement",
                    framework_assignment=None,
                    terminology_assignment=None,
                    attributes=(),
                    approved_input_selections=(
                        ModelCandidateApprovedInputSelection(
                            approved_input_id=item.approved_input_id,
                            provenance_role="direct_support",
                        ),
                    ),
                    derivation_rationale="fixture",
                    support_level="supported",
                    assumptions=(),
                    missing_information=(),
                    structure_profile_conformance=(
                        StructuralProfileConformance(
                            status="conformant",
                            finding_ids=(),
                            conformance_fingerprint="b" * 64,
                        )
                    ),
                ),
            )
        )


def _profile_ref():
    return ModelStructureProfileReference(
        profile_id="PROFILE",
        profile_version="1.0.0",
        profile_fingerprint="a" * 64,
    )


def _rules_ref():
    return ModelDerivationRulesReference(
        context_id="CTX_TEST",
        context_version="1.0.0",
        context_fingerprint="c" * 64,
    )


def _provenance():
    return ModelCandidateGenerationProvenance(
        method="fixture",
        recipe_reference=None,
        agent_reference=None,
        model_reference=None,
        context_fingerprint="d" * 64,
    )


def test_candidate_generation_filters_project_superseded_ain():
    value, _, _, manifests, _ = _handoff(
        outcome="supersede",
        concern="PEAC-000001",
        retained="AIN-000002",
    )
    deriver = _Deriver()
    service = ModelCandidateGenerationService(
        approved_input_repository=_ApprovedInputRepo(manifests),
        candidate_repository=_CandidateRepo(),
        workspace=_Workspace(),
    )

    result = service.generate_candidate_set(
        PROJECT_ID,
        deriver=deriver,
        model_structure_profile_reference=_profile_ref(),
        derivation_rules_reference=_rules_ref(),
        generation_provenance=_provenance(),
        project_authority_handoff=value,
    )

    assert tuple(
        item.approved_input_id
        for item in deriver.requests[0].approved_inputs
    ) == ("AIN-000002",)
    assert tuple(
        item.approved_input_id
        for item in result.manifest.approved_input_references
    ) == ("AIN-000002",)
    assert (
        result.element_candidates[0].candidate_subject_key
        == "project_subject:src-000002:streaming-encoder"
    )
    assert (
        result.manifest.generation_provenance.context_fingerprint
        != "d" * 64
    )


def test_multi_source_generation_without_handoff_fails_closed():
    _, _, manifests, _ = _authority()
    service = ModelCandidateGenerationService(
        approved_input_repository=_ApprovedInputRepo(manifests),
        candidate_repository=_CandidateRepo(),
        workspace=_Workspace(),
    )

    with pytest.raises(ModelCandidateGenerationBlockedError):
        service.generate_candidate_set(
            PROJECT_ID,
            deriver=_Deriver(),
            model_structure_profile_reference=_profile_ref(),
            derivation_rules_reference=_rules_ref(),
            generation_provenance=_provenance(),
        )
