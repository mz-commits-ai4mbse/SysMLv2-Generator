"""Tests for Phase-H Candidate Review persistence."""


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
    ModelCandidateIntegrityError,
    ModelCandidateReviewRepository,
)


def test_record_decision_binds_exact_persisted_candidate(tmp_path):
    create_project(tmp_path)
    candidate_repo, snapshot = persist_bundle(tmp_path)
    reviews = ModelCandidateReviewRepository(
        root=tmp_path,
        candidate_repository=candidate_repo,
        clock=clock,
    )
    item = reviews.record_decision(
        PROJECT_ID,
        "MCS-000001",
        target_type="element_candidate",
        candidate_id="MCE-000001",
        decision="accepted",
        reviewer_identity="moritz",
    )
    assert item.model_candidate_review_decision_id == "MCD-000001"
    assert (
        item.target.candidate_content_fingerprint
        == snapshot.element_candidates[0].content_fingerprint
    )
    assert (
        item.target.candidate_set_content_fingerprint
        == snapshot.manifest.content_fingerprint
    )
    assert reviews.load_decision(PROJECT_ID, "MCD-000001") == item


def test_review_ids_are_project_local_sequential(tmp_path):
    create_project(tmp_path)
    candidate_repo, _ = persist_bundle(tmp_path)
    reviews = ModelCandidateReviewRepository(
        root=tmp_path,
        candidate_repository=candidate_repo,
        clock=clock,
    )
    first = reviews.record_decision(
        PROJECT_ID,
        "MCS-000001",
        target_type="element_candidate",
        candidate_id="MCE-000001",
        decision="accepted",
        reviewer_identity="moritz",
    )
    second = reviews.record_decision(
        PROJECT_ID,
        "MCS-000001",
        target_type="element_candidate",
        candidate_id="MCE-000002",
        decision="rejected",
        reviewer_identity="moritz",
        rationale="Not part of selected architecture.",
    )
    assert first.model_candidate_review_decision_id == "MCD-000001"
    assert second.model_candidate_review_decision_id == "MCD-000002"


def test_equivalent_duplicate_decision_is_rejected(tmp_path):
    create_project(tmp_path)
    candidate_repo, _ = persist_bundle(tmp_path)
    reviews = ModelCandidateReviewRepository(
        root=tmp_path,
        candidate_repository=candidate_repo,
        clock=clock,
    )
    kwargs = dict(
        target_type="element_candidate",
        candidate_id="MCE-000001",
        decision="accepted",
        reviewer_identity="moritz",
    )
    reviews.record_decision(
        PROJECT_ID,
        "MCS-000001",
        **kwargs,
    )
    with pytest.raises(ModelCandidateIntegrityError):
        reviews.record_decision(
            PROJECT_ID,
            "MCS-000001",
            **kwargs,
        )


def test_scan_reports_unexpected_review_entry(tmp_path):
    create_project(tmp_path)
    candidate_repo, _ = persist_bundle(tmp_path)
    reviews = ModelCandidateReviewRepository(
        root=tmp_path,
        candidate_repository=candidate_repo,
        clock=clock,
    )
    reviews.record_decision(
        PROJECT_ID,
        "MCS-000001",
        target_type="element_candidate",
        candidate_id="MCE-000001",
        decision="accepted",
        reviewer_identity="moritz",
    )
    directory = (
        tmp_path
        / PROJECT_ID
        / "semantics"
        / "model_candidate_reviews"
    )
    (directory / "junk.txt").write_text("junk", encoding="utf-8")
    result = reviews.scan_decisions(PROJECT_ID)
    assert "unexpected_candidate_review_entry" in {
        item.code for item in result.issues
    }
