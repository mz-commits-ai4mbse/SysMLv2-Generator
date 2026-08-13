from __future__ import annotations

from dataclasses import replace

import pytest

from modules.framework import load_framework_template
from modules.internal_model import (
    InternalModelAssemblyBlockedError,
    InternalModelAssemblyProvenance,
    InternalModelAssemblyService,
)
from modules.model_candidates.structure_profile import (
    load_model_structure_profile,
)
from modules.model_candidates.types import (
    ModelCandidateApprovedInputReference,
    ModelCandidateAssemblyInput,
    ModelCandidateAttribute,
    ModelCandidateGenerationProvenance,
    ModelCandidateReviewDecisionReference,
    ModelDerivationRulesReference,
    ModelElementCandidate,
    ModelRelationshipCandidate,
    ModelRelationshipEndpoint,
    ModelStructureProfileReference,
    RelationshipPriorityAssessment,
    RelationshipPriorityCriterionResult,
    StructuralComparabilityAssessment,
    StructuralProfileConformance,
)
from modules.project_workspace.types import FrameworkTemplateReference


def _profile_reference() -> ModelStructureProfileReference:
    template = load_framework_template()
    profile = load_model_structure_profile(
        framework_template=template,
    )
    return ModelStructureProfileReference(
        profile_id=profile.profile_id,
        profile_version=profile.profile_version,
        profile_fingerprint=profile.profile_fingerprint,
    )


def _approved_input(
    approved_input_id: str = "AIN-000001",
) -> ModelCandidateApprovedInputReference:
    return ModelCandidateApprovedInputReference(
        approved_input_id=approved_input_id,
        content_fingerprint="a" * 64,
        stable_subject_key=f"source.{approved_input_id.lower()}",
        provenance_role="direct_support",
    )


def _conformance() -> StructuralProfileConformance:
    return StructuralProfileConformance(
        status="conformant",
        finding_ids=(),
        conformance_fingerprint="b" * 64,
    )


def _requirement_candidate() -> ModelElementCandidate:
    return ModelElementCandidate(
        schema_version="1.0.0",
        project_id="000001",
        candidate_set_id="MCS-000001",
        model_element_candidate_id="MCE-000001",
        candidate_subject_key="system.requirement.one",
        comparison_anchor_id="system.requirements:system.requirement.one",
        proposed_name="Requirement One",
        description="Accepted system requirement.",
        model_area="system.requirements",
        element_type="system_requirement",
        framework_assignment="FW_SYSTEM_REQUIREMENTS",
        terminology_assignment=None,
        attributes=(
            ModelCandidateAttribute(
                name="kind",
                value="requirement",
            ),
        ),
        approved_input_references=(_approved_input(),),
        derivation_rationale="Reviewed in Phase H.",
        support_level="supported",
        assumptions=(),
        missing_information=(),
        structure_profile_conformance=_conformance(),
        predecessor_candidate_ids=(),
        created_at="2026-08-13T09:00:00Z",
        content_fingerprint="1" * 64,
    )


def _logical_candidate() -> ModelElementCandidate:
    return ModelElementCandidate(
        schema_version="1.0.0",
        project_id="000001",
        candidate_set_id="MCS-000001",
        model_element_candidate_id="MCE-000002",
        candidate_subject_key="system.controller",
        comparison_anchor_id="system.logical:system.controller",
        proposed_name="Controller",
        description="Accepted logical component.",
        model_area="system.logical",
        element_type="logical_component",
        framework_assignment="FW_SYSTEM_LOGICAL",
        terminology_assignment=None,
        attributes=(
            ModelCandidateAttribute(
                name="kind",
                value="logical",
            ),
        ),
        approved_input_references=(_approved_input(),),
        derivation_rationale="Reviewed in Phase H.",
        support_level="supported",
        assumptions=(),
        missing_information=(),
        structure_profile_conformance=_conformance(),
        predecessor_candidate_ids=(),
        created_at="2026-08-13T09:00:00Z",
        content_fingerprint="2" * 64,
    )


def _relationship_candidate() -> ModelRelationshipCandidate:
    return ModelRelationshipCandidate(
        schema_version="1.0.0",
        project_id="000001",
        candidate_set_id="MCS-000001",
        model_relationship_candidate_id="MCR-000001",
        relationship_choice_key=None,
        source=ModelRelationshipEndpoint(
            candidate_subject_key="system.requirement.one",
            resolution_status="resolved",
            resolved_model_element_candidate_id="MCE-000001",
            candidate_model_element_ids=("MCE-000001",),
        ),
        target=ModelRelationshipEndpoint(
            candidate_subject_key="system.controller",
            resolution_status="resolved",
            resolved_model_element_candidate_id="MCE-000002",
            candidate_model_element_ids=("MCE-000002",),
        ),
        relationship_family="allocation",
        semantic_intent="allocated_to",
        directionality="source_to_target",
        approved_input_references=(_approved_input(),),
        derivation_rationale="Reviewed relationship semantics.",
        supporting_evidence=("AIN-000001",),
        assumptions=(),
        missing_information=(),
        priority_assessment=RelationshipPriorityAssessment(
            priority_class="preferred",
            criterion_results=(
                RelationshipPriorityCriterionResult(
                    criterion="semantic_fit",
                    result="strong",
                    rationale="Reviewed canonical meaning.",
                ),
            ),
            rationale="Preferred reviewed relationship.",
        ),
        comparability_assessment=StructuralComparabilityAssessment(
            impact="neutral",
            comparison_anchor_ids=(
                "system.requirements:system.requirement.one",
                "system.logical:system.controller",
            ),
            canonical_pattern_match=True,
            deviation_ids=(),
            rationale="Canonical relationship choice.",
        ),
        structure_profile_conformance=_conformance(),
        upstream_relationship_representation=None,
        predecessor_candidate_ids=(),
        created_at="2026-08-13T09:00:00Z",
        content_fingerprint="3" * 64,
    )


def _review(
    decision_id: str,
    target_type: str,
    candidate_id: str,
    *,
    decision: str = "accepted",
    fingerprint_char: str,
) -> ModelCandidateReviewDecisionReference:
    return ModelCandidateReviewDecisionReference(
        model_candidate_review_decision_id=decision_id,
        target_type=target_type,
        candidate_id=candidate_id,
        decision=decision,
        decision_fingerprint=fingerprint_char * 64,
    )


def _assembly_input(
    *,
    elements: tuple[ModelElementCandidate, ...] | None = None,
    relationships: tuple[ModelRelationshipCandidate, ...] | None = None,
    first_element_decision: str = "accepted",
) -> ModelCandidateAssemblyInput:
    template = load_framework_template()
    selected_elements = (
        (_requirement_candidate(), _logical_candidate())
        if elements is None
        else elements
    )
    selected_relationships = (
        (_relationship_candidate(),)
        if relationships is None
        else relationships
    )

    review_refs = []
    exception_refs = []
    for element in selected_elements:
        decision = (
            first_element_decision
            if element.model_element_candidate_id == "MCE-000001"
            else "accepted"
        )
        reference = _review(
            "MCD-000001"
            if element.model_element_candidate_id == "MCE-000001"
            else "MCD-000002",
            "element_candidate",
            element.model_element_candidate_id,
            decision=decision,
            fingerprint_char=(
                "4"
                if element.model_element_candidate_id == "MCE-000001"
                else "5"
            ),
        )
        review_refs.append(reference)
        if decision == "accepted_exception":
            exception_refs.append(reference)

    for relationship in selected_relationships:
        reference = _review(
            "MCD-000003",
            "relationship_candidate",
            relationship.model_relationship_candidate_id,
            fingerprint_char="6",
        )
        review_refs.append(reference)

    return ModelCandidateAssemblyInput(
        project_id="000001",
        candidate_set_id="MCS-000001",
        candidate_set_content_fingerprint="7" * 64,
        approved_input_snapshot_fingerprint="8" * 64,
        approved_input_references=(_approved_input(),),
        framework_template_reference=FrameworkTemplateReference(
            template_id=template["template_id"],
            template_version=template["template_version"],
        ),
        model_structure_profile_reference=_profile_reference(),
        derivation_rules_reference=ModelDerivationRulesReference(
            context_id="CTX_SYSML_MODEL_DERIVATION_RULES",
            context_version="0.1.0",
            context_fingerprint="9" * 64,
        ),
        generation_provenance=ModelCandidateGenerationProvenance(
            method="profile_driven",
            recipe_reference=None,
            agent_reference=None,
            model_reference=None,
            context_fingerprint=None,
        ),
        accepted_element_candidates=selected_elements,
        accepted_relationship_candidates=selected_relationships,
        accepted_exception_decisions=tuple(exception_refs),
        review_decision_references=tuple(review_refs),
    )


def _assemble(
    assembly_input: ModelCandidateAssemblyInput,
    *,
    occupied_element_ids=(),
    occupied_relationship_ids=(),
):
    return InternalModelAssemblyService().assemble(
        project_id="000001",
        internal_engineering_model_id="IEM-000001",
        assembly_input=assembly_input,
        assembly_provenance=InternalModelAssemblyProvenance(
            method="deterministic",
            implementation_reference="I4-test",
            recipe_reference=None,
            context_fingerprint=None,
        ),
        created_at="2026-08-13T10:00:00Z",
        occupied_internal_model_element_ids=occupied_element_ids,
        occupied_internal_model_relationship_ids=(
            occupied_relationship_ids
        ),
    )


def test_assembly_creates_complete_iem_snapshot():
    snapshot = _assemble(_assembly_input())

    assert snapshot.manifest.internal_engineering_model_id == "IEM-000001"
    assert tuple(
        item.internal_model_element_id for item in snapshot.elements
    ) == ("IME-000001", "IME-000002")
    assert tuple(
        item.internal_model_relationship_id
        for item in snapshot.relationships
    ) == ("IMR-000001",)
    assert snapshot.manifest.internal_model_element_ids == (
        "IME-000001",
        "IME-000002",
    )
    assert snapshot.manifest.internal_model_relationship_ids == (
        "IMR-000001",
    )


def test_mce_to_ime_preserves_identity_semantics_and_traceability():
    snapshot = _assemble(_assembly_input())
    requirement = snapshot.elements[0]

    assert requirement.internal_model_element_id == "IME-000001"
    assert requirement.source_model_element_candidate_id == "MCE-000001"
    assert requirement.model_subject_key == "system.requirement.one"
    assert requirement.model_area == "system.requirements"
    assert requirement.element_type == "system_requirement"
    assert requirement.framework_assignment == "FW_SYSTEM_REQUIREMENTS"
    assert requirement.approved_input_references[0].approved_input_id == (
        "AIN-000001"
    )
    assert (
        requirement.review_decision_reference
        .model_candidate_review_decision_id
        == "MCD-000001"
    )


def test_mcr_to_imr_preserves_semantics_and_resolves_exact_ime_endpoints():
    snapshot = _assemble(_assembly_input())
    relationship = snapshot.relationships[0]

    assert relationship.source_model_relationship_candidate_id == (
        "MCR-000001"
    )
    assert relationship.source_internal_model_element_id == "IME-000001"
    assert relationship.target_internal_model_element_id == "IME-000002"
    assert relationship.relationship_family == "allocation"
    assert relationship.semantic_intent == "allocated_to"
    assert relationship.directionality == "source_to_target"


def test_structure_membership_uses_newly_allocated_ime_ids():
    snapshot = _assemble(_assembly_input())
    membership = {
        node.framework_node_id: node.internal_model_element_ids
        for node in snapshot.structure.nodes
    }

    assert membership["FW_SYSTEM_REQUIREMENTS"] == ("IME-000001",)
    assert membership["FW_SYSTEM_LOGICAL"] == ("IME-000002",)


def test_candidate_order_does_not_change_snapshot():
    normal = _assembly_input()
    reversed_input = replace(
        normal,
        accepted_element_candidates=tuple(
            reversed(normal.accepted_element_candidates)
        ),
    )

    assert _assemble(normal) == _assemble(reversed_input)


def test_id_allocation_continues_after_highest_project_local_ids():
    snapshot = _assemble(
        _assembly_input(),
        occupied_element_ids=("IME-000003",),
        occupied_relationship_ids=("IMR-000008",),
    )

    assert tuple(
        item.internal_model_element_id for item in snapshot.elements
    ) == ("IME-000004", "IME-000005")
    assert snapshot.relationships[0].internal_model_relationship_id == (
        "IMR-000009"
    )


def test_no_relationship_candidates_means_no_relationships_are_invented():
    snapshot = _assemble(
        _assembly_input(relationships=())
    )

    assert snapshot.relationships == ()
    assert snapshot.manifest.internal_model_relationship_ids == ()


def test_accepted_exception_is_preserved_on_ime_and_manifest():
    snapshot = _assemble(
        _assembly_input(first_element_decision="accepted_exception")
    )

    requirement = snapshot.elements[0]
    assert requirement.accepted_exception_reference is not None
    assert (
        requirement.accepted_exception_reference.decision
        == "accepted_exception"
    )
    assert snapshot.manifest.accepted_exception_references == (
        requirement.accepted_exception_reference,
    )


def test_missing_review_reference_blocks_assembly():
    assembly_input = _assembly_input()
    changed = replace(
        assembly_input,
        review_decision_references=tuple(
            item
            for item in assembly_input.review_decision_references
            if item.candidate_id != "MCR-000001"
        ),
    )

    with pytest.raises(InternalModelAssemblyBlockedError):
        _assemble(changed)


def test_nonexact_relationship_endpoint_blocks_assembly():
    assembly_input = _assembly_input()
    relationship = replace(
        assembly_input.accepted_relationship_candidates[0],
        source=replace(
            assembly_input.accepted_relationship_candidates[0].source,
            resolution_status="ambiguous",
            resolved_model_element_candidate_id=None,
            candidate_model_element_ids=(
                "MCE-000001",
                "MCE-000002",
            ),
        ),
    )
    changed = replace(
        assembly_input,
        accepted_relationship_candidates=(relationship,),
    )

    with pytest.raises(InternalModelAssemblyBlockedError):
        _assemble(changed)


def test_relationship_subject_mismatch_blocks_assembly():
    assembly_input = _assembly_input()
    relationship = replace(
        assembly_input.accepted_relationship_candidates[0],
        source=replace(
            assembly_input.accepted_relationship_candidates[0].source,
            candidate_subject_key="different.subject",
        ),
    )
    changed = replace(
        assembly_input,
        accepted_relationship_candidates=(relationship,),
    )

    with pytest.raises(InternalModelAssemblyBlockedError):
        _assemble(changed)


def test_cross_project_candidate_blocks_assembly():
    assembly_input = _assembly_input()
    changed_element = replace(
        assembly_input.accepted_element_candidates[0],
        project_id="000002",
    )
    changed = replace(
        assembly_input,
        accepted_element_candidates=(
            changed_element,
            assembly_input.accepted_element_candidates[1],
        ),
    )

    with pytest.raises(InternalModelAssemblyBlockedError):
        _assemble(changed)


def test_duplicate_semantic_subject_identity_blocks_assembly():
    assembly_input = _assembly_input()
    duplicate_subject = replace(
        assembly_input.accepted_element_candidates[1],
        candidate_subject_key=(
            assembly_input.accepted_element_candidates[0]
            .candidate_subject_key
        ),
    )
    changed = replace(
        assembly_input,
        accepted_element_candidates=(
            assembly_input.accepted_element_candidates[0],
            duplicate_subject,
        ),
    )

    with pytest.raises(InternalModelAssemblyBlockedError):
        _assemble(changed)


def test_manifest_binds_exact_assembly_context_and_input():
    assembly_input = _assembly_input()
    snapshot = _assemble(assembly_input)

    assert (
        snapshot.manifest.assembly_context.framework_template_reference
        == assembly_input.framework_template_reference
    )
    assert (
        snapshot.manifest.assembly_context.model_structure_profile_reference
        == assembly_input.model_structure_profile_reference
    )
    assert (
        snapshot.manifest.assembly_context.derivation_rules_reference
        == assembly_input.derivation_rules_reference
    )
    assert len(snapshot.manifest.assembly_input_fingerprint) == 64
