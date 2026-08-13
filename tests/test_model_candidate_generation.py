"""Tests for Approved-Input-only Phase-H Candidate generation."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from modules.approved_input.manifest import (
    create_approved_input_manifest,
)
from modules.approved_input.types import (
    ApprovedInputCanonicalContent,
    ApprovedInputRelationshipProperty,
    ApprovedInputRelationshipRepresentation,
)
from modules.model_candidates import (
    ModelCandidateApprovedInputSelection,
    ModelCandidateDerivationError,
    ModelCandidateDerivationPlan,
    ModelCandidateGenerationBlockedError,
    ModelCandidateGenerationProvenance,
    ModelCandidateGenerationService,
    ModelCandidateReferenceError,
    ModelCandidateRepository,
    ModelDerivationRulesReference,
    ModelElementCandidateDraft,
    ModelRelationshipCandidateDraft,
    ModelStructureProfileReference,
    RelationshipPriorityAssessment,
    RelationshipPriorityCriterionResult,
    StructuralComparabilityAssessment,
    StructuralProfileConformance,
)
from modules.project_processing.types import ProcessingArtifactReference
from modules.project_workspace import ProjectWorkspace


PROJECT_ID = "318604"
SHA_A = "a" * 64
SHA_B = "b" * 64
SHA_C = "c" * 64
SHA_D = "d" * 64
SHA_E = "e" * 64


def _clock():
    return datetime(2026, 8, 13, 6, 45, tzinfo=timezone.utc)


def _artifact_reference(
    artifact_id: str,
    fingerprint: str,
) -> ProcessingArtifactReference:
    return ProcessingArtifactReference(
        artifact_type="information_unit",
        artifact_id=artifact_id,
        content_fingerprint=fingerprint,
        repository_relative_path=(
            f"data/projects/{PROJECT_ID}/semantics/"
            f"information_units/{artifact_id}.json"
        ),
    )


def _relationship_representation():
    return ApprovedInputRelationshipRepresentation(
        source_subject_key="subject.source",
        target_subject_key="subject.target",
        semantic_intent="allocated_to",
        sysml_v2_construct="allocation",
        construct_properties=(
            ApprovedInputRelationshipProperty(
                name="direction",
                value="source_to_target",
            ),
        ),
        target_notation_profile_id="SYSIDE_SYSML_V2",
        target_notation_profile_version="1.0.0",
        textual_notation_preview="allocation preview",
        profile_validation_status="valid",
        profile_validation_fingerprint=SHA_E,
    )


def _approved_input(
    number: int,
    *,
    kind: str,
    subject_key: str,
    title: str,
):
    review_item_kind = {
        "element_statement": "element",
        "relationship_statement": "relationship",
        "human_clarification": "open_question",
    }[kind]
    return create_approved_input_manifest(
        project_id=PROJECT_ID,
        approved_input_id=f"AIN-{number:06d}",
        approved_input_kind=kind,
        canonical_content=ApprovedInputCanonicalContent(
            title=title,
            primary_text=f"{title} primary text.",
            description=f"{title} description.",
            information_type="requirement",
            modality="shall",
            epistemic_status="reviewed",
        ),
        selected_classification="System Requirement",
        selected_framework_assignment="System Requirements",
        selected_terminology_assignment="requirement",
        selected_source_assignments=("SRC-000001",),
        selected_relationship_representation=(
            _relationship_representation()
            if kind == "relationship_statement"
            else None
        ),
        stable_subject_key=subject_key,
        review_document_id=f"RVD-{number:06d}",
        review_document_version_id=f"RVV-{number:06d}",
        review_revision_id=f"RVR-{number:06d}",
        review_item_id=f"RIT-{number:06d}",
        review_item_kind=review_item_kind,
        review_item_fingerprint=SHA_A,
        finalized_artifact_set_fingerprint=SHA_B,
        finalization_decision_id=f"HRD-{number:06d}",
        finalization_decision_fingerprint=SHA_C,
        finalization_validation_fingerprint=SHA_D,
        source_id="SRC-000001",
        source_sha256=SHA_E,
        processing_run_id=f"RUN-{number:06d}",
        attempt_id="ATT-000001",
        primary_artifact_reference=_artifact_reference(
            f"IU-{number:06d}",
            SHA_A,
        ),
        supporting_artifact_references=(),
        proposal_references=(),
        created_at="2026-08-13T06:30:00Z",
    )


class _ActiveApprovedInputs:
    def __init__(self, inputs):
        self.inputs = tuple(inputs)
        self.calls = []
        self.list_manifests_called = False

    def list_active_approved_inputs(self, project_id):
        self.calls.append(project_id)
        return self.inputs

    def list_manifests(self, project_id):
        self.list_manifests_called = True
        raise AssertionError(
            "H5 must not consume list_manifests as authority."
        )


def _profile():
    return ModelStructureProfileReference(
        profile_id="TURING_MODEL_STRUCTURE",
        profile_version="1.0.0",
        profile_fingerprint=SHA_B,
    )


def _rules():
    return ModelDerivationRulesReference(
        context_id="CTX_SYSML_MODEL_DERIVATION_RULES",
        context_version="0.1.0",
        context_fingerprint=SHA_C,
    )


def _provenance():
    return ModelCandidateGenerationProvenance(
        method="test_deriver",
        recipe_reference="recipe://phase-h",
        agent_reference=None,
        model_reference=None,
        context_fingerprint=SHA_D,
    )


def _conformance():
    return StructuralProfileConformance(
        status="conformant",
        finding_ids=(),
        conformance_fingerprint=SHA_E,
    )


def _priority():
    return RelationshipPriorityAssessment(
        priority_class="preferred",
        criterion_results=(
            RelationshipPriorityCriterionResult(
                criterion="evidence_directness",
                result="explicit",
                rationale="Explicit Approved Input relationship.",
            ),
        ),
        rationale="Direct relationship evidence.",
    )


def _comparability():
    return StructuralComparabilityAssessment(
        impact="neutral",
        comparison_anchor_ids=(),
        canonical_pattern_match=None,
        deviation_ids=(),
        rationale="No H6 profile preference in fixture.",
    )


def _element_draft(
    draft_key,
    subject_key,
    approved_input_id,
    *,
    predecessor_candidate_ids=(),
):
    return ModelElementCandidateDraft(
        draft_key=draft_key,
        candidate_subject_key=subject_key,
        comparison_anchor_id=None,
        proposed_name=f"Element {draft_key}",
        description=None,
        model_area="test_area",
        element_type="test_element",
        framework_assignment=None,
        terminology_assignment=None,
        attributes=(),
        approved_input_selections=(
            ModelCandidateApprovedInputSelection(
                approved_input_id=approved_input_id,
                provenance_role="direct_support",
            ),
        ),
        derivation_rationale="Fixture derivation.",
        support_level="supported",
        assumptions=(),
        missing_information=(),
        structure_profile_conformance=_conformance(),
        predecessor_candidate_ids=predecessor_candidate_ids,
    )


def _relationship_draft(
    *,
    source_subject_key="subject.source",
    target_subject_key="subject.target",
    predecessor_candidate_ids=(),
):
    return ModelRelationshipCandidateDraft(
        draft_key="rel.main",
        relationship_choice_key=None,
        source_subject_key=source_subject_key,
        target_subject_key=target_subject_key,
        relationship_family="allocation",
        semantic_intent="allocated_to",
        directionality="source_to_target",
        approved_input_selections=(
            ModelCandidateApprovedInputSelection(
                approved_input_id="AIN-000003",
                provenance_role="explicit_relationship",
            ),
        ),
        derivation_rationale="Fixture relationship derivation.",
        supporting_evidence=("AIN-000003",),
        assumptions=(),
        missing_information=(),
        priority_assessment=_priority(),
        comparability_assessment=_comparability(),
        structure_profile_conformance=_conformance(),
        upstream_relationship_representation=(
            _relationship_representation()
        ),
        predecessor_candidate_ids=predecessor_candidate_ids,
    )


class _Deriver:
    def __init__(self, plan):
        self.plan = plan
        self.requests = []

    def derive(self, request):
        self.requests.append(request)
        return self.plan


def _workspace(tmp_path):
    workspace = ProjectWorkspace(
        root=tmp_path,
        id_generator=lambda: PROJECT_ID,
        clock=_clock,
    )
    workspace.create_project("H5 Generation Test")
    return workspace


def _service(tmp_path, approved_inputs):
    workspace = _workspace(tmp_path)
    source = _ActiveApprovedInputs(approved_inputs)
    candidates = ModelCandidateRepository(root=tmp_path)
    service = ModelCandidateGenerationService(
        root=tmp_path,
        approved_input_repository=source,
        candidate_repository=candidates,
        workspace=workspace,
        clock=_clock,
    )
    return service, source, candidates


def _active_fixture():
    return (
        _approved_input(
            1,
            kind="element_statement",
            subject_key="subject.source",
            title="Source",
        ),
        _approved_input(
            2,
            kind="human_clarification",
            subject_key="clarification.session",
            title="Clarification",
        ),
        _approved_input(
            3,
            kind="relationship_statement",
            subject_key="relationship.source.target",
            title="Source to target",
        ),
        _approved_input(
            4,
            kind="element_statement",
            subject_key="subject.target",
            title="Target",
        ),
    )


def test_generation_consumes_joint_active_snapshot_once(tmp_path):
    service, source, candidates = _service(
        tmp_path,
        _active_fixture(),
    )
    deriver = _Deriver(
        ModelCandidateDerivationPlan(
            element_drafts=(
                _element_draft(
                    "z.target",
                    "subject.target",
                    "AIN-000004",
                ),
                _element_draft(
                    "a.source",
                    "subject.source",
                    "AIN-000001",
                ),
            ),
            relationship_drafts=(_relationship_draft(),),
        )
    )

    snapshot = service.generate_candidate_set(
        PROJECT_ID,
        deriver=deriver,
        model_structure_profile_reference=_profile(),
        derivation_rules_reference=_rules(),
        generation_provenance=_provenance(),
    )

    assert source.calls == [PROJECT_ID]
    assert source.list_manifests_called is False
    assert len(deriver.requests) == 1
    assert tuple(
        item.approved_input_id
        for item in deriver.requests[0].approved_inputs
    ) == (
        "AIN-000001",
        "AIN-000002",
        "AIN-000003",
        "AIN-000004",
    )
    assert tuple(
        item.approved_input_id
        for item in snapshot.manifest.approved_input_references
    ) == (
        "AIN-000001",
        "AIN-000002",
        "AIN-000003",
        "AIN-000004",
    )
    assert snapshot.manifest.candidate_set_id == "MCS-000001"
    assert tuple(
        item.model_element_candidate_id
        for item in snapshot.element_candidates
    ) == ("MCE-000001", "MCE-000002")
    assert (
        snapshot.element_candidates[0].candidate_subject_key
        == "subject.source"
    )
    assert (
        snapshot.relationship_candidates[0].source.resolution_status
        == "resolved"
    )
    assert (
        snapshot.relationship_candidates[0].target.resolution_status
        == "resolved"
    )
    assert candidates.load_candidate_set(
        PROJECT_ID,
        "MCS-000001",
    ) == snapshot


def test_human_clarification_is_context_not_auto_materialized(tmp_path):
    service, _, _ = _service(tmp_path, _active_fixture())
    deriver = _Deriver(
        ModelCandidateDerivationPlan(
            element_drafts=(
                _element_draft(
                    "source",
                    "subject.source",
                    "AIN-000001",
                ),
            ),
        )
    )

    snapshot = service.generate_candidate_set(
        PROJECT_ID,
        deriver=deriver,
        model_structure_profile_reference=_profile(),
        derivation_rules_reference=_rules(),
        generation_provenance=_provenance(),
    )

    assert "AIN-000002" in {
        item.approved_input_id
        for item in snapshot.manifest.approved_input_references
    }
    assert all(
        item.candidate_subject_key != "clarification.session"
        for item in snapshot.element_candidates
    )


def test_no_active_inputs_blocks_before_derivation(tmp_path):
    service, source, _ = _service(tmp_path, ())
    deriver = _Deriver(ModelCandidateDerivationPlan())

    with pytest.raises(ModelCandidateGenerationBlockedError):
        service.generate_candidate_set(
            PROJECT_ID,
            deriver=deriver,
            model_structure_profile_reference=_profile(),
            derivation_rules_reference=_rules(),
            generation_provenance=_provenance(),
        )

    assert source.calls == [PROJECT_ID]
    assert deriver.requests == []


def test_candidate_provenance_cannot_escape_active_snapshot(tmp_path):
    service, _, _ = _service(tmp_path, _active_fixture())
    deriver = _Deriver(
        ModelCandidateDerivationPlan(
            element_drafts=(
                _element_draft(
                    "bad",
                    "subject.bad",
                    "AIN-999999",
                ),
            ),
        )
    )

    with pytest.raises(ModelCandidateReferenceError):
        service.generate_candidate_set(
            PROJECT_ID,
            deriver=deriver,
            model_structure_profile_reference=_profile(),
            derivation_rules_reference=_rules(),
            generation_provenance=_provenance(),
        )


def test_endpoint_resolution_reports_unresolved_and_ambiguous(tmp_path):
    service, _, _ = _service(tmp_path, _active_fixture())
    deriver = _Deriver(
        ModelCandidateDerivationPlan(
            element_drafts=(
                _element_draft(
                    "one",
                    "subject.shared",
                    "AIN-000001",
                ),
                _element_draft(
                    "two",
                    "subject.shared",
                    "AIN-000004",
                ),
            ),
            relationship_drafts=(
                _relationship_draft(
                    source_subject_key="subject.shared",
                    target_subject_key="subject.missing",
                ),
            ),
        )
    )

    snapshot = service.generate_candidate_set(
        PROJECT_ID,
        deriver=deriver,
        model_structure_profile_reference=_profile(),
        derivation_rules_reference=_rules(),
        generation_provenance=_provenance(),
    )

    relationship = snapshot.relationship_candidates[0]
    assert relationship.source.resolution_status == "ambiguous"
    assert relationship.source.candidate_model_element_ids == (
        "MCE-000001",
        "MCE-000002",
    )
    assert relationship.target.resolution_status == "unresolved"
    assert relationship.target.candidate_model_element_ids == ()


def test_draft_order_does_not_control_persistent_identity(tmp_path):
    service, _, _ = _service(tmp_path, _active_fixture())
    deriver = _Deriver(
        ModelCandidateDerivationPlan(
            element_drafts=(
                _element_draft(
                    "z.last",
                    "subject.target",
                    "AIN-000004",
                ),
                _element_draft(
                    "a.first",
                    "subject.source",
                    "AIN-000001",
                ),
            ),
        )
    )

    snapshot = service.generate_candidate_set(
        PROJECT_ID,
        deriver=deriver,
        model_structure_profile_reference=_profile(),
        derivation_rules_reference=_rules(),
        generation_provenance=_provenance(),
    )

    assert tuple(
        (
            item.model_element_candidate_id,
            item.candidate_subject_key,
        )
        for item in snapshot.element_candidates
    ) == (
        ("MCE-000001", "subject.source"),
        ("MCE-000002", "subject.target"),
    )


def test_regeneration_creates_new_ids_and_validates_predecessors(tmp_path):
    service, _, _ = _service(tmp_path, _active_fixture())

    first = service.generate_candidate_set(
        PROJECT_ID,
        deriver=_Deriver(
            ModelCandidateDerivationPlan(
                element_drafts=(
                    _element_draft(
                        "source",
                        "subject.source",
                        "AIN-000001",
                    ),
                ),
                relationship_drafts=(_relationship_draft(),),
            )
        ),
        model_structure_profile_reference=_profile(),
        derivation_rules_reference=_rules(),
        generation_provenance=_provenance(),
    )

    second = service.generate_candidate_set(
        PROJECT_ID,
        deriver=_Deriver(
            ModelCandidateDerivationPlan(
                element_drafts=(
                    _element_draft(
                        "source",
                        "subject.source",
                        "AIN-000001",
                        predecessor_candidate_ids=(
                            first.element_candidates[
                                0
                            ].model_element_candidate_id,
                        ),
                    ),
                ),
                relationship_drafts=(
                    _relationship_draft(
                        predecessor_candidate_ids=(
                            first.relationship_candidates[
                                0
                            ].model_relationship_candidate_id,
                        ),
                    ),
                ),
            )
        ),
        model_structure_profile_reference=_profile(),
        derivation_rules_reference=_rules(),
        generation_provenance=_provenance(),
        predecessor_candidate_set_id="MCS-000001",
        regeneration_reason="Approved Input interpretation updated.",
    )

    assert second.manifest.candidate_set_id == "MCS-000002"
    assert second.manifest.predecessor_candidate_set_id == "MCS-000001"
    assert (
        second.element_candidates[0].model_element_candidate_id
        == "MCE-000002"
    )
    assert second.element_candidates[0].predecessor_candidate_ids == (
        "MCE-000001",
    )
    assert (
        second.relationship_candidates[
            0
        ].model_relationship_candidate_id
        == "MCR-000002"
    )
    assert (
        second.relationship_candidates[0].predecessor_candidate_ids
        == ("MCR-000001",)
    )


def test_invalid_predecessor_reference_is_rejected(tmp_path):
    service, _, _ = _service(tmp_path, _active_fixture())
    first = service.generate_candidate_set(
        PROJECT_ID,
        deriver=_Deriver(
            ModelCandidateDerivationPlan(
                element_drafts=(
                    _element_draft(
                        "source",
                        "subject.source",
                        "AIN-000001",
                    ),
                ),
            )
        ),
        model_structure_profile_reference=_profile(),
        derivation_rules_reference=_rules(),
        generation_provenance=_provenance(),
    )
    assert first.manifest.candidate_set_id == "MCS-000001"

    with pytest.raises(ModelCandidateReferenceError):
        service.generate_candidate_set(
            PROJECT_ID,
            deriver=_Deriver(
                ModelCandidateDerivationPlan(
                    element_drafts=(
                        _element_draft(
                            "source",
                            "subject.source",
                            "AIN-000001",
                            predecessor_candidate_ids=(
                                "MCE-999999",
                            ),
                        ),
                    ),
                )
            ),
            model_structure_profile_reference=_profile(),
            derivation_rules_reference=_rules(),
            generation_provenance=_provenance(),
            predecessor_candidate_set_id="MCS-000001",
            regeneration_reason="Retry.",
        )


def test_deriver_must_return_explicit_plan(tmp_path):
    service, _, _ = _service(tmp_path, _active_fixture())

    class BadDeriver:
        def derive(self, request):
            return ()

    with pytest.raises(ModelCandidateDerivationError):
        service.generate_candidate_set(
            PROJECT_ID,
            deriver=BadDeriver(),
            model_structure_profile_reference=_profile(),
            derivation_rules_reference=_rules(),
            generation_provenance=_provenance(),
        )
