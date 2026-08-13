"""Tests for the sole validated Phase-H → Phase-I gate."""


from datetime import datetime, timezone

from modules.approved_input.types import (
    ApprovedInputCanonicalContent,
    ApprovedInputManifest,
)
from modules.model_candidates import (
    ModelCandidateApprovedInputReference,
    ModelCandidateGenerationProvenance,
    ModelCandidateRepository,
    ModelDerivationRulesReference,
    ModelRelationshipEndpoint,
    ModelStructureProfileReference,
    RelationshipPriorityAssessment,
    RelationshipPriorityCriterionResult,
    StructuralComparabilityAssessment,
    StructuralProfileConformance,
    create_model_candidate_set_manifest,
    create_model_element_candidate,
    create_model_relationship_candidate,
)
from modules.project_workspace import ProjectWorkspace
from modules.project_workspace.types import FrameworkTemplateReference


PROJECT_ID = "318604"
A = "a" * 64
B = "b" * 64
C = "c" * 64
D = "d" * 64
E = "e" * 64


def clock():
    return datetime(2026, 8, 13, 7, 30, tzinfo=timezone.utc)


def create_project(root):
    workspace = ProjectWorkspace(
        root=root,
        id_generator=lambda: PROJECT_ID,
        clock=clock,
    )
    workspace.create_project("H7 Candidate Review Test")
    return workspace


def approved_manifest(
    approved_input_id="AIN-000001",
    fingerprint=A,
    subject="subject.one",
):
    # Direct dataclass construction is enough for the Phase-I activity check.
    return ApprovedInputManifest(
        schema_version="1.0.0",
        project_id=PROJECT_ID,
        approved_input_id=approved_input_id,
        approved_input_kind="element_statement",
        authority_state="active",
        canonical_content=ApprovedInputCanonicalContent(
            title="Reviewed input",
            primary_text="Reviewed input.",
            description=None,
            information_type="requirement",
            modality="shall",
            epistemic_status="reviewed",
        ),
        selected_classification="System Requirement",
        selected_framework_assignment="System Requirements",
        selected_terminology_assignment="requirement",
        selected_source_assignments=("SRC-000001",),
        selected_relationship_representation=None,
        stable_subject_key=subject,
        review_document_id="RVD-000001",
        review_document_version_id="RVV-000001",
        review_revision_id="RVR-000001",
        review_item_id="RIT-000001",
        review_item_kind="element",
        review_item_fingerprint=B,
        finalized_artifact_set_fingerprint=C,
        finalization_decision_id="HRD-000001",
        finalization_decision_fingerprint=D,
        finalization_validation_fingerprint=E,
        source_id="SRC-000001",
        source_sha256=E,
        processing_run_id="RUN-000001",
        attempt_id="ATT-000001",
        primary_artifact_reference=None,
        supporting_artifact_references=(),
        proposal_references=(),
        created_at="2026-08-13T07:00:00Z",
        content_fingerprint=fingerprint,
    )


def conformance(status="conformant", fingerprint=D):
    return StructuralProfileConformance(
        status=status,
        finding_ids=(),
        conformance_fingerprint=fingerprint,
    )


def persist_bundle(
    root,
    *,
    relationship_choice_key=None,
    relationship_conformance="conformant",
    relationship_target="MCE-000002",
):
    repo = ModelCandidateRepository(root=root)
    ref = ModelCandidateApprovedInputReference(
        approved_input_id="AIN-000001",
        content_fingerprint=A,
        stable_subject_key="subject.one",
        provenance_role="active_snapshot",
    )
    e1 = create_model_element_candidate(
        project_id=PROJECT_ID,
        candidate_set_id="MCS-000001",
        model_element_candidate_id="MCE-000001",
        candidate_subject_key="subject.one",
        comparison_anchor_id="system.requirements:subject.one",
        proposed_name="Element One",
        description=None,
        model_area="system.requirements",
        element_type="system_requirement",
        framework_assignment="FW_SYSTEM_REQUIREMENTS",
        terminology_assignment="requirement",
        attributes=(),
        approved_input_references=(ref,),
        derivation_rationale="fixture",
        support_level="supported",
        assumptions=(),
        missing_information=(),
        structure_profile_conformance=conformance(),
        predecessor_candidate_ids=(),
        created_at="2026-08-13T07:00:00Z",
    )
    e2 = create_model_element_candidate(
        project_id=PROJECT_ID,
        candidate_set_id="MCS-000001",
        model_element_candidate_id="MCE-000002",
        candidate_subject_key="subject.two",
        comparison_anchor_id="system.requirements:subject.two",
        proposed_name="Element Two",
        description=None,
        model_area="system.requirements",
        element_type="system_requirement",
        framework_assignment="FW_SYSTEM_REQUIREMENTS",
        terminology_assignment="requirement",
        attributes=(),
        approved_input_references=(ref,),
        derivation_rationale="fixture",
        support_level="supported",
        assumptions=(),
        missing_information=(),
        structure_profile_conformance=conformance(),
        predecessor_candidate_ids=(),
        created_at="2026-08-13T07:00:00Z",
    )
    target_subject = (
        "subject.two"
        if relationship_target == "MCE-000002"
        else "subject.missing"
    )
    target_endpoint = (
        ModelRelationshipEndpoint(
            candidate_subject_key="subject.two",
            resolution_status="resolved",
            resolved_model_element_candidate_id="MCE-000002",
            candidate_model_element_ids=("MCE-000002",),
        )
        if relationship_target == "MCE-000002"
        else ModelRelationshipEndpoint(
            candidate_subject_key=target_subject,
            resolution_status="unresolved",
            resolved_model_element_candidate_id=None,
            candidate_model_element_ids=(),
        )
    )
    r1 = create_model_relationship_candidate(
        project_id=PROJECT_ID,
        candidate_set_id="MCS-000001",
        model_relationship_candidate_id="MCR-000001",
        relationship_choice_key=relationship_choice_key,
        source=ModelRelationshipEndpoint(
            candidate_subject_key="subject.one",
            resolution_status="resolved",
            resolved_model_element_candidate_id="MCE-000001",
            candidate_model_element_ids=("MCE-000001",),
        ),
        target=target_endpoint,
        relationship_family="dependency",
        semantic_intent="dependency",
        directionality="source_to_target",
        approved_input_references=(ref,),
        derivation_rationale="fixture",
        supporting_evidence=("AIN-000001",),
        assumptions=(),
        missing_information=(),
        priority_assessment=RelationshipPriorityAssessment(
            priority_class="preferred",
            criterion_results=(
                RelationshipPriorityCriterionResult(
                    criterion="evidence_directness",
                    result="explicit",
                    rationale="fixture",
                ),
            ),
            rationale="fixture",
        ),
        comparability_assessment=StructuralComparabilityAssessment(
            impact="neutral",
            comparison_anchor_ids=(),
            canonical_pattern_match=True,
            deviation_ids=(),
            rationale="fixture",
        ),
        structure_profile_conformance=conformance(
            relationship_conformance,
            fingerprint=E,
        ),
        upstream_relationship_representation=None,
        predecessor_candidate_ids=(),
        created_at="2026-08-13T07:00:00Z",
    )
    profile = ModelStructureProfileReference(
        profile_id="TURING_MODEL_STRUCTURE",
        profile_version="1.0.0",
        profile_fingerprint=C,
    )
    manifest = create_model_candidate_set_manifest(
        project_id=PROJECT_ID,
        candidate_set_id="MCS-000001",
        predecessor_candidate_set_id=None,
        regeneration_reason=None,
        approved_input_references=(ref,),
        framework_template_reference=FrameworkTemplateReference(
            template_id="TURING_RFLP_FRAMEWORK",
            template_version="1.0.0",
        ),
        model_structure_profile_reference=profile,
        derivation_rules_reference=ModelDerivationRulesReference(
            context_id="CTX_SYSML_MODEL_DERIVATION_RULES",
            context_version="0.1.0",
            context_fingerprint=B,
        ),
        generation_provenance=ModelCandidateGenerationProvenance(
            method="fixture",
            recipe_reference=None,
            agent_reference=None,
            model_reference=None,
            context_fingerprint=None,
        ),
        element_candidate_ids=("MCE-000001", "MCE-000002"),
        relationship_candidate_ids=("MCR-000001",),
        created_at="2026-08-13T07:00:00Z",
    )
    snapshot = repo.persist_candidate_set(
        manifest,
        element_candidates=(e1, e2),
        relationship_candidates=(r1,),
    )
    return repo, snapshot


import pytest

from modules.model_candidates import (
    ModelCandidatePhaseIGateError,
    ModelCandidateReadService,
    ModelCandidateReviewRepository,
)


class ActiveApprovedInputs:
    def __init__(self, items):
        self.items = tuple(items)

    def list_active_approved_inputs(self, project_id):
        assert project_id == PROJECT_ID
        return self.items


def setup_gate(
    tmp_path,
    *,
    relationship_conformance="conformant",
    relationship_target="MCE-000002",
):
    create_project(tmp_path)
    candidate_repo, snapshot = persist_bundle(
        tmp_path,
        relationship_conformance=relationship_conformance,
        relationship_target=relationship_target,
    )
    reviews = ModelCandidateReviewRepository(
        root=tmp_path,
        candidate_repository=candidate_repo,
        clock=clock,
    )
    active = ActiveApprovedInputs((approved_manifest(),))
    service = ModelCandidateReadService(
        root=tmp_path,
        candidate_repository=candidate_repo,
        review_repository=reviews,
        approved_input_repository=active,
    )
    return snapshot, reviews, service, active


def decide_all(
    reviews,
    *,
    e1="accepted",
    e2="accepted",
    relationship="accepted",
    relationship_rationale=None,
):
    reviews.record_decision(
        PROJECT_ID,
        "MCS-000001",
        target_type="element_candidate",
        candidate_id="MCE-000001",
        decision=e1,
        reviewer_identity="moritz",
        rationale=(
            None if e1 == "accepted" else "Element decision rationale."
        ),
    )
    reviews.record_decision(
        PROJECT_ID,
        "MCS-000001",
        target_type="element_candidate",
        candidate_id="MCE-000002",
        decision=e2,
        reviewer_identity="moritz",
        rationale=(
            None if e2 == "accepted" else "Element decision rationale."
        ),
    )
    reviews.record_decision(
        PROJECT_ID,
        "MCS-000001",
        target_type="relationship_candidate",
        candidate_id="MCR-000001",
        decision=relationship,
        reviewer_identity="moritz",
        rationale=relationship_rationale,
    )


def test_phase_i_returns_only_explicitly_authorized_content(tmp_path):
    snapshot, reviews, service, _ = setup_gate(tmp_path)
    decide_all(
        reviews,
        e1="accepted",
        e2="rejected",
        relationship="rejected",
        relationship_rationale="Relationship not selected.",
    )
    result = service.load_phase_i_input(
        PROJECT_ID,
        "MCS-000001",
    )
    assert tuple(
        item.model_element_candidate_id
        for item in result.accepted_element_candidates
    ) == ("MCE-000001",)
    assert result.accepted_relationship_candidates == ()
    assert len(result.review_decision_references) == 3
    assert (
        result.candidate_set_content_fingerprint
        == snapshot.manifest.content_fingerprint
    )


def test_unreviewed_candidate_blocks_phase_i(tmp_path):
    _, reviews, service, _ = setup_gate(tmp_path)
    reviews.record_decision(
        PROJECT_ID,
        "MCS-000001",
        target_type="element_candidate",
        candidate_id="MCE-000001",
        decision="accepted",
        reviewer_identity="moritz",
    )
    with pytest.raises(ModelCandidatePhaseIGateError):
        service.load_phase_i_input(PROJECT_ID, "MCS-000001")


def test_deferred_candidate_blocks_phase_i(tmp_path):
    _, reviews, service, _ = setup_gate(tmp_path)
    decide_all(
        reviews,
        e2="deferred",
        relationship="rejected",
        relationship_rationale="Not selected.",
    )
    with pytest.raises(ModelCandidatePhaseIGateError):
        service.load_phase_i_input(PROJECT_ID, "MCS-000001")


def test_accepted_relationship_requires_accepted_endpoints(tmp_path):
    _, reviews, service, _ = setup_gate(tmp_path)
    decide_all(
        reviews,
        e2="rejected",
        relationship="accepted",
    )
    with pytest.raises(ModelCandidatePhaseIGateError):
        service.load_phase_i_input(PROJECT_ID, "MCS-000001")


def test_unresolved_relationship_cannot_be_accepted(tmp_path):
    _, reviews, service, _ = setup_gate(
        tmp_path,
        relationship_target="missing",
    )
    decide_all(
        reviews,
        relationship="accepted",
    )
    with pytest.raises(ModelCandidatePhaseIGateError):
        service.load_phase_i_input(PROJECT_ID, "MCS-000001")


def test_nonconformant_relationship_can_pass_only_as_exception(tmp_path):
    _, reviews, service, _ = setup_gate(
        tmp_path,
        relationship_conformance="exception_required",
    )
    reviews.record_decision(
        PROJECT_ID,
        "MCS-000001",
        target_type="element_candidate",
        candidate_id="MCE-000001",
        decision="accepted",
        reviewer_identity="moritz",
    )
    reviews.record_decision(
        PROJECT_ID,
        "MCS-000001",
        target_type="element_candidate",
        candidate_id="MCE-000002",
        decision="accepted",
        reviewer_identity="moritz",
    )
    reviews.record_decision(
        PROJECT_ID,
        "MCS-000001",
        target_type="relationship_candidate",
        candidate_id="MCR-000001",
        decision="accepted_exception",
        reviewer_identity="moritz",
        rationale="Intentional reviewed structural exception.",
    )
    result = service.load_phase_i_input(PROJECT_ID, "MCS-000001")
    assert tuple(
        item.model_relationship_candidate_id
        for item in result.accepted_relationship_candidates
    ) == ("MCR-000001",)
    assert len(result.accepted_exception_decisions) == 1


def test_inactive_approved_input_invalidates_historical_set(tmp_path):
    _, reviews, service, active = setup_gate(tmp_path)
    decide_all(
        reviews,
        relationship="rejected",
        relationship_rationale="Not selected.",
    )
    active.items = ()
    with pytest.raises(ModelCandidatePhaseIGateError):
        service.load_phase_i_input(PROJECT_ID, "MCS-000001")


def test_approved_input_fingerprint_drift_blocks_phase_i(tmp_path):
    _, reviews, service, active = setup_gate(tmp_path)
    decide_all(
        reviews,
        relationship="rejected",
        relationship_rationale="Not selected.",
    )
    active.items = (
        approved_manifest(fingerprint="f" * 64),
    )
    with pytest.raises(ModelCandidatePhaseIGateError):
        service.load_phase_i_input(PROJECT_ID, "MCS-000001")


def test_latest_exact_decision_controls_selection(tmp_path):
    _, reviews, service, _ = setup_gate(tmp_path)
    reviews.record_decision(
        PROJECT_ID,
        "MCS-000001",
        target_type="element_candidate",
        candidate_id="MCE-000001",
        decision="rejected",
        reviewer_identity="moritz",
        rationale="Initial rejection.",
    )
    reviews.record_decision(
        PROJECT_ID,
        "MCS-000001",
        target_type="element_candidate",
        candidate_id="MCE-000001",
        decision="accepted",
        reviewer_identity="moritz",
    )
    reviews.record_decision(
        PROJECT_ID,
        "MCS-000001",
        target_type="element_candidate",
        candidate_id="MCE-000002",
        decision="rejected",
        reviewer_identity="moritz",
        rationale="Not selected.",
    )
    reviews.record_decision(
        PROJECT_ID,
        "MCS-000001",
        target_type="relationship_candidate",
        candidate_id="MCR-000001",
        decision="rejected",
        reviewer_identity="moritz",
        rationale="Not selected.",
    )
    result = service.load_phase_i_input(PROJECT_ID, "MCS-000001")
    assert tuple(
        item.model_element_candidate_id
        for item in result.accepted_element_candidates
    ) == ("MCE-000001",)
