"""Tests for deterministic non-authoritative Model Proposal projections."""

from dataclasses import replace
import json

from modules.model_candidates import (
    ModelCandidateReadService,
    ModelCandidateRepository,
    ModelCandidateReviewRepository,
    ModelProposalReadService,
    RelationshipPriorityAssessment,
    RelationshipPriorityCriterionResult,
    StructuralComparabilityAssessment,
    create_model_candidate_set_manifest,
    create_model_relationship_candidate,
    model_proposal_view_to_dict,
    model_proposal_view_to_json,
    model_proposal_view_to_markdown,
)

from datetime import datetime, timezone

from modules.approved_input.types import (
    ApprovedInputCanonicalContent,
    ApprovedInputManifest,
)
from modules.model_candidates import (
    ModelCandidateApprovedInputReference,
    ModelCandidateGenerationProvenance,
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
    workspace.create_project("H8 Model Proposal Test")
    return workspace


def approved_manifest(
    approved_input_id="AIN-000001",
    fingerprint=A,
    subject="subject.one",
):
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


def _conformance(status="conformant", fingerprint=D):
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
        structure_profile_conformance=_conformance(),
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
        structure_profile_conformance=_conformance(),
        predecessor_candidate_ids=(),
        created_at="2026-08-13T07:00:00Z",
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
            candidate_subject_key="subject.missing",
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
        structure_profile_conformance=_conformance(
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


class ActiveApprovedInputs:
    def __init__(self, items):
        self.items = tuple(items)

    def list_active_approved_inputs(self, project_id):
        assert project_id == PROJECT_ID
        return self.items


def _service(tmp_path, *, active=None, **bundle_kwargs):
    create_project(tmp_path)
    candidate_repo, snapshot = persist_bundle(
        tmp_path,
        **bundle_kwargs,
    )
    reviews = ModelCandidateReviewRepository(
        root=tmp_path,
        candidate_repository=candidate_repo,
        clock=clock,
    )
    approved = (
        ActiveApprovedInputs((approved_manifest(),))
        if active is None
        else active
    )
    gate = ModelCandidateReadService(
        root=tmp_path,
        candidate_repository=candidate_repo,
        review_repository=reviews,
        approved_input_repository=approved,
    )
    proposal = ModelProposalReadService(
        root=tmp_path,
        candidate_repository=candidate_repo,
        review_repository=reviews,
        phase_i_read_service=gate,
    )
    return snapshot, reviews, proposal, approved


def _accept_elements(reviews):
    for candidate_id in ("MCE-000001", "MCE-000002"):
        reviews.record_decision(
            PROJECT_ID,
            "MCS-000001",
            target_type="element_candidate",
            candidate_id=candidate_id,
            decision="accepted",
            reviewer_identity="moritz",
        )


def test_pending_proposal_is_readable_and_points_to_review(tmp_path):
    snapshot, _, service, _ = _service(tmp_path)
    view = service.load_model_proposal(
        PROJECT_ID,
        "MCS-000001",
    )
    assert view.candidate_set_id == "MCS-000001"
    assert len(view.proposed_elements) == 2
    assert len(view.proposed_relationships) == 1
    assert {
        item.review_state.status
        for item in view.proposed_elements
    } == {"pending"}
    assert view.phase_i_gate_status == "not_ready"
    assert len(view.required_human_decisions) == 3
    assert "Human Review" in view.next_action
    assert (
        view.candidate_set_content_fingerprint
        == snapshot.manifest.content_fingerprint
    )


def test_structural_overview_is_explanatory_candidate_projection(tmp_path):
    _, _, service, _ = _service(tmp_path)
    view = service.load_model_proposal(PROJECT_ID, "MCS-000001")
    assert tuple(
        item.candidate_id
        for item in view.structural_overview.nodes
    ) == ("MCE-000001", "MCE-000002")
    assert tuple(
        item.candidate_id
        for item in view.structural_overview.edges
    ) == ("MCR-000001",)
    assert view.structural_overview.edges[0].resolution_status == (
        "resolved"
    )
    assert view.structural_overview.model_areas == (
        "system.requirements",
    )


def test_terminal_reviews_make_proposal_phase_i_ready(tmp_path):
    _, reviews, service, _ = _service(tmp_path)
    _accept_elements(reviews)
    reviews.record_decision(
        PROJECT_ID,
        "MCS-000001",
        target_type="relationship_candidate",
        candidate_id="MCR-000001",
        decision="accepted",
        reviewer_identity="moritz",
    )
    view = service.load_model_proposal(PROJECT_ID, "MCS-000001")
    assert view.required_human_decisions == ()
    assert view.blocking_issues == ()
    assert view.phase_i_gate_status == "ready"
    assert view.next_action.startswith("Continue to Phase-I")


def test_rejected_candidates_are_terminal_not_required_decisions(tmp_path):
    _, reviews, service, _ = _service(tmp_path)
    _accept_elements(reviews)
    reviews.record_decision(
        PROJECT_ID,
        "MCS-000001",
        target_type="relationship_candidate",
        candidate_id="MCR-000001",
        decision="rejected",
        reviewer_identity="moritz",
        rationale="Not selected.",
    )
    view = service.load_model_proposal(PROJECT_ID, "MCS-000001")
    assert view.required_human_decisions == ()
    assert view.proposed_relationships[0].review_state.status == (
        "rejected"
    )
    assert view.phase_i_gate_status == "ready"


def test_deferred_review_remains_one_required_decision(tmp_path):
    _, reviews, service, _ = _service(tmp_path)
    _accept_elements(reviews)
    reviews.record_decision(
        PROJECT_ID,
        "MCS-000001",
        target_type="relationship_candidate",
        candidate_id="MCR-000001",
        decision="deferred",
        reviewer_identity="moritz",
        rationale="Needs domain review.",
    )
    view = service.load_model_proposal(PROJECT_ID, "MCS-000001")
    assert len(view.required_human_decisions) == 1
    assert (
        view.required_human_decisions[0].target_ids
        == ("MCR-000001",)
    )
    assert view.phase_i_gate_status == "not_ready"


def test_inactive_approved_input_becomes_visible_gate_block(tmp_path):
    active = ActiveApprovedInputs(())
    _, reviews, service, _ = _service(
        tmp_path,
        active=active,
    )
    _accept_elements(reviews)
    reviews.record_decision(
        PROJECT_ID,
        "MCS-000001",
        target_type="relationship_candidate",
        candidate_id="MCR-000001",
        decision="rejected",
        reviewer_identity="moritz",
        rationale="Not selected.",
    )
    view = service.load_model_proposal(PROJECT_ID, "MCS-000001")
    assert view.phase_i_gate_status == "blocked"
    assert tuple(item.code for item in view.blocking_issues) == (
        "phase_i_gate_blocked",
    )
    assert "authority" in view.next_action


def test_unresolved_relationship_is_visible_in_structural_projection(tmp_path):
    _, _, service, _ = _service(
        tmp_path,
        relationship_target="missing",
    )
    view = service.load_model_proposal(PROJECT_ID, "MCS-000001")
    rel = view.proposed_relationships[0]
    assert rel.target_resolution_status == "unresolved"
    assert view.structural_overview.edges[0].resolution_status == (
        "unresolved"
    )
    assert view.comparability_summary.neutral_count == 1


def test_profile_deviation_projection_exposes_exception_candidate(tmp_path):
    _, reviews, service, _ = _service(
        tmp_path,
        relationship_conformance="exception_required",
    )
    _accept_elements(reviews)
    reviews.record_decision(
        PROJECT_ID,
        "MCS-000001",
        target_type="relationship_candidate",
        candidate_id="MCR-000001",
        decision="accepted_exception",
        reviewer_identity="moritz",
        rationale="Intentional reviewed exception.",
    )
    view = service.load_model_proposal(PROJECT_ID, "MCS-000001")
    assert len(view.profile_deviations) == 1
    assert view.profile_deviations[0].candidate_id == "MCR-000001"
    assert (
        view.profile_deviations[0].review_status
        == "accepted_exception"
    )
    assert view.phase_i_gate_status == "ready"


def test_review_repository_issue_is_exposed_without_mutating_candidates(
    tmp_path,
):
    snapshot, reviews, service, _ = _service(tmp_path)
    directory = (
        tmp_path
        / PROJECT_ID
        / "semantics"
        / "model_candidate_reviews"
    )
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "junk.txt").write_text("junk", encoding="utf-8")

    view = service.load_model_proposal(PROJECT_ID, "MCS-000001")
    assert view.phase_i_gate_status == "not_ready"
    assert "unexpected_candidate_review_entry" in {
        item.code for item in view.blocking_issues
    }
    assert (
        snapshot.manifest.content_fingerprint
        == view.candidate_set_content_fingerprint
    )


def test_serializers_are_deterministic_and_json_roundtrips(tmp_path):
    _, _, service, _ = _service(tmp_path)
    view = service.load_model_proposal(PROJECT_ID, "MCS-000001")
    first = model_proposal_view_to_json(view)
    second = model_proposal_view_to_json(view)
    assert first == second
    assert json.loads(first) == model_proposal_view_to_dict(view)


def test_markdown_report_states_non_authority_and_next_action(tmp_path):
    _, _, service, _ = _service(tmp_path)
    view = service.load_model_proposal(PROJECT_ID, "MCS-000001")
    report = model_proposal_view_to_markdown(view)
    assert report.startswith("# Model Proposal — MCS-000001")
    assert "not model authority" in report
    assert view.next_action in report


def test_generation_summary_references_exact_profile_and_input_count(tmp_path):
    _, _, service, _ = _service(tmp_path)
    view = service.load_model_proposal(PROJECT_ID, "MCS-000001")
    assert "fixture" in view.generation_rationale_summary
    assert "1 Approved Input snapshot reference(s)" in (
        view.generation_rationale_summary
    )
    assert "TURING_MODEL_STRUCTURE 1.0.0" in (
        view.generation_rationale_summary
    )


def _choice_service(tmp_path):
    source_root = tmp_path / "fixture_source"
    create_project(source_root)
    _, source_snapshot = persist_bundle(source_root)

    create_project(tmp_path)
    candidate_repo = ModelCandidateRepository(root=tmp_path)
    original = source_snapshot.relationship_candidates[0]
    choice_key = "choice:relationship-one"

    first = create_model_relationship_candidate(
        project_id=PROJECT_ID,
        candidate_set_id="MCS-000001",
        model_relationship_candidate_id="MCR-000001",
        relationship_choice_key=choice_key,
        source=original.source,
        target=original.target,
        relationship_family=original.relationship_family,
        semantic_intent=original.semantic_intent,
        directionality=original.directionality,
        approved_input_references=original.approved_input_references,
        derivation_rationale="Preferred explicit relationship alternative.",
        supporting_evidence=original.supporting_evidence,
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
            rationale="Preferred fixture alternative.",
        ),
        comparability_assessment=original.comparability_assessment,
        structure_profile_conformance=(
            original.structure_profile_conformance
        ),
        upstream_relationship_representation=None,
        predecessor_candidate_ids=(),
        created_at="2026-08-13T07:00:00Z",
    )
    second = create_model_relationship_candidate(
        project_id=PROJECT_ID,
        candidate_set_id="MCS-000001",
        model_relationship_candidate_id="MCR-000002",
        relationship_choice_key=choice_key,
        source=original.source,
        target=original.target,
        relationship_family="allocation",
        semantic_intent="allocated_to",
        directionality="source_to_target",
        approved_input_references=original.approved_input_references,
        derivation_rationale="Supported relationship alternative.",
        supporting_evidence=original.supporting_evidence,
        assumptions=(),
        missing_information=(),
        priority_assessment=RelationshipPriorityAssessment(
            priority_class="supported_alternative",
            criterion_results=(
                RelationshipPriorityCriterionResult(
                    criterion="evidence_directness",
                    result="explicit",
                    rationale="fixture",
                ),
            ),
            rationale="Alternative fixture relationship.",
        ),
        comparability_assessment=StructuralComparabilityAssessment(
            impact="neutral",
            comparison_anchor_ids=(),
            canonical_pattern_match=True,
            deviation_ids=(),
            rationale="Alternative fixture comparability.",
        ),
        structure_profile_conformance=(
            original.structure_profile_conformance
        ),
        upstream_relationship_representation=None,
        predecessor_candidate_ids=(),
        created_at="2026-08-13T07:00:00Z",
    )
    base = source_snapshot.manifest
    manifest = create_model_candidate_set_manifest(
        project_id=base.project_id,
        candidate_set_id=base.candidate_set_id,
        predecessor_candidate_set_id=None,
        regeneration_reason=None,
        approved_input_references=base.approved_input_references,
        framework_template_reference=base.framework_template_reference,
        model_structure_profile_reference=(
            base.model_structure_profile_reference
        ),
        derivation_rules_reference=base.derivation_rules_reference,
        generation_provenance=base.generation_provenance,
        element_candidate_ids=base.element_candidate_ids,
        relationship_candidate_ids=("MCR-000001", "MCR-000002"),
        created_at=base.created_at,
    )
    candidate_repo.persist_candidate_set(
        manifest,
        element_candidates=source_snapshot.element_candidates,
        relationship_candidates=(first, second),
    )

    reviews = ModelCandidateReviewRepository(
        root=tmp_path,
        candidate_repository=candidate_repo,
        clock=clock,
    )
    approved = ActiveApprovedInputs((approved_manifest(),))
    gate = ModelCandidateReadService(
        root=tmp_path,
        candidate_repository=candidate_repo,
        review_repository=reviews,
        approved_input_repository=approved,
    )
    service = ModelProposalReadService(
        root=tmp_path,
        candidate_repository=candidate_repo,
        review_repository=reviews,
        phase_i_read_service=gate,
    )
    return reviews, service


def test_relationship_alternatives_collapse_to_one_required_choice(tmp_path):
    _, service = _choice_service(tmp_path)
    view = service.load_model_proposal(PROJECT_ID, "MCS-000001")
    assert len(view.relationship_choice_groups) == 1
    group = view.relationship_choice_groups[0]
    assert group.candidate_ids == ("MCR-000001", "MCR-000002")
    assert group.preferred_candidate_ids == ("MCR-000001",)
    assert group.review_required is True

    relationship_decisions = tuple(
        item
        for item in view.required_human_decisions
        if item.target_type == "relationship_choice_group"
    )
    assert len(relationship_decisions) == 1
    assert relationship_decisions[0].target_ids == (
        "MCR-000001",
        "MCR-000002",
    )


def test_one_accepted_alternative_and_one_rejected_resolves_choice(tmp_path):
    reviews, service = _choice_service(tmp_path)
    _accept_elements(reviews)
    reviews.record_decision(
        PROJECT_ID,
        "MCS-000001",
        target_type="relationship_candidate",
        candidate_id="MCR-000001",
        decision="accepted",
        reviewer_identity="moritz",
    )
    reviews.record_decision(
        PROJECT_ID,
        "MCS-000001",
        target_type="relationship_candidate",
        candidate_id="MCR-000002",
        decision="rejected",
        reviewer_identity="moritz",
        rationale="Alternative not selected.",
    )

    view = service.load_model_proposal(PROJECT_ID, "MCS-000001")
    group = view.relationship_choice_groups[0]
    assert group.accepted_candidate_ids == ("MCR-000001",)
    assert group.review_required is False
    assert view.required_human_decisions == ()
    assert view.phase_i_gate_status == "ready"


def test_two_accepted_alternatives_remain_a_required_human_choice(tmp_path):
    reviews, service = _choice_service(tmp_path)
    _accept_elements(reviews)
    for candidate_id in ("MCR-000001", "MCR-000002"):
        reviews.record_decision(
            PROJECT_ID,
            "MCS-000001",
            target_type="relationship_candidate",
            candidate_id=candidate_id,
            decision="accepted",
            reviewer_identity="moritz",
        )

    view = service.load_model_proposal(PROJECT_ID, "MCS-000001")
    group = view.relationship_choice_groups[0]
    assert group.accepted_candidate_ids == (
        "MCR-000001",
        "MCR-000002",
    )
    assert group.review_required is True
    assert view.phase_i_gate_status == "not_ready"
