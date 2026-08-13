"""Tests for immutable Phase-H Model Candidate foundation types."""

from dataclasses import FrozenInstanceError

import pytest

from modules.approved_input.types import (
    ApprovedInputRelationshipProperty,
    ApprovedInputRelationshipRepresentation,
)
from modules.model_candidates import (
    MODEL_CANDIDATE_SUPPORT_LEVELS,
    MODEL_RELATIONSHIP_PRIORITY_CLASSES,
    RELATIONSHIP_ENDPOINT_RESOLUTION_STATUSES,
    STRUCTURAL_COMPARABILITY_IMPACTS,
    ModelCandidateApprovedInputReference,
    ModelCandidateAttribute,
    ModelCandidateGenerationProvenance,
    ModelCandidateSetManifest,
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


SHA_A = "a" * 64
SHA_B = "b" * 64
SHA_C = "c" * 64
SHA_D = "d" * 64


def _approved_reference():
    return ModelCandidateApprovedInputReference(
        approved_input_id="AIN-000001",
        content_fingerprint=SHA_A,
        stable_subject_key="subject.session",
        provenance_role="direct_support",
    )


def _profile_reference():
    return ModelStructureProfileReference(
        profile_id="TURING_MODEL_STRUCTURE",
        profile_version="1.0.0",
        profile_fingerprint=SHA_B,
    )


def _conformance():
    return StructuralProfileConformance(
        status="conformant",
        finding_ids=(),
        conformance_fingerprint=SHA_C,
    )


def test_candidate_vocabularies_match_accepted_architecture():
    assert MODEL_CANDIDATE_SUPPORT_LEVELS == frozenset(
        {
            "supported",
            "partially_supported",
            "conflicting",
        }
    )
    assert MODEL_RELATIONSHIP_PRIORITY_CLASSES == frozenset(
        {
            "preferred",
            "supported_alternative",
            "exception_candidate",
        }
    )
    assert STRUCTURAL_COMPARABILITY_IMPACTS == frozenset(
        {
            "improves",
            "neutral",
            "reduces",
            "unknown",
        }
    )
    assert RELATIONSHIP_ENDPOINT_RESOLUTION_STATUSES == frozenset(
        {
            "resolved",
            "unresolved",
            "ambiguous",
        }
    )


def test_candidate_set_manifest_captures_pinned_inputs_and_profiles():
    manifest = ModelCandidateSetManifest(
        schema_version="1.0.0",
        project_id="000042",
        candidate_set_id="MCS-000001",
        predecessor_candidate_set_id=None,
        regeneration_reason=None,
        approved_input_references=(_approved_reference(),),
        approved_input_snapshot_fingerprint=SHA_D,
        framework_template_reference=FrameworkTemplateReference(
            template_id="TURING_RFLP_FRAMEWORK",
            template_version="1.0.0",
        ),
        model_structure_profile_reference=_profile_reference(),
        derivation_rules_reference=ModelDerivationRulesReference(
            context_id="CTX_SYSML_MODEL_DERIVATION_RULES",
            context_version="0.1.0",
            context_fingerprint=SHA_C,
        ),
        generation_provenance=ModelCandidateGenerationProvenance(
            method="deterministic_test",
            recipe_reference=None,
            agent_reference=None,
            model_reference=None,
            context_fingerprint=None,
        ),
        element_candidate_ids=("MCE-000001",),
        relationship_candidate_ids=("MCR-000001",),
        created_at="2026-08-12T13:00:00Z",
        content_fingerprint=SHA_A,
    )

    assert manifest.approved_input_references[0].approved_input_id == (
        "AIN-000001"
    )
    assert manifest.framework_template_reference.template_id == (
        "TURING_RFLP_FRAMEWORK"
    )


def test_element_candidate_keeps_instance_identity_separate_from_subject_key():
    candidate = ModelElementCandidate(
        schema_version="1.0.0",
        project_id="000042",
        candidate_set_id="MCS-000001",
        model_element_candidate_id="MCE-000001",
        candidate_subject_key="subject.session",
        comparison_anchor_id="system.functional.session",
        proposed_name="Manage Session",
        description="Proposed functional model element.",
        model_area="system_functional",
        element_type="function",
        framework_assignment="02_System/02_Functional",
        terminology_assignment=None,
        attributes=(
            ModelCandidateAttribute(
                name="source_kind",
                value="element_statement",
            ),
        ),
        approved_input_references=(_approved_reference(),),
        derivation_rationale="Directly supported by Approved Input.",
        support_level="supported",
        assumptions=(),
        missing_information=(),
        structure_profile_conformance=_conformance(),
        predecessor_candidate_ids=(),
        created_at="2026-08-12T13:00:00Z",
        content_fingerprint=SHA_B,
    )

    assert candidate.model_element_candidate_id == "MCE-000001"
    assert candidate.candidate_subject_key == "subject.session"
    assert candidate.comparison_anchor_id == "system.functional.session"



def test_relationship_endpoint_represents_all_resolution_states():
    resolved = ModelRelationshipEndpoint(
        candidate_subject_key="subject.session",
        resolution_status="resolved",
        resolved_model_element_candidate_id="MCE-000001",
        candidate_model_element_ids=("MCE-000001",),
    )
    unresolved = ModelRelationshipEndpoint(
        candidate_subject_key="subject.unknown",
        resolution_status="unresolved",
        resolved_model_element_candidate_id=None,
        candidate_model_element_ids=(),
    )
    ambiguous = ModelRelationshipEndpoint(
        candidate_subject_key="subject.component",
        resolution_status="ambiguous",
        resolved_model_element_candidate_id=None,
        candidate_model_element_ids=("MCE-000002", "MCE-000003"),
    )

    assert resolved.resolved_model_element_candidate_id == "MCE-000001"
    assert unresolved.candidate_model_element_ids == ()
    assert len(ambiguous.candidate_model_element_ids) == 2

def test_relationship_candidate_uses_exact_element_endpoints():
    priority = RelationshipPriorityAssessment(
        priority_class="preferred",
        criterion_results=(
            RelationshipPriorityCriterionResult(
                criterion="semantic_fit",
                result="strong",
                rationale="Meaning matches allocation intent.",
            ),
        ),
        rationale="Preferred canonical relationship.",
    )
    comparability = StructuralComparabilityAssessment(
        impact="improves",
        comparison_anchor_ids=("system.functional.session",),
        canonical_pattern_match=True,
        deviation_ids=(),
        rationale="Uses canonical structural choice.",
    )
    upstream = ApprovedInputRelationshipRepresentation(
        source_subject_key="subject.session",
        target_subject_key="subject.component",
        semantic_intent="allocated_to",
        sysml_v2_construct="allocation",
        construct_properties=(
            ApprovedInputRelationshipProperty(
                name="direction",
                value="source_to_target",
            ),
        ),
        target_notation_profile_id="SYSML_V2_TARGET",
        target_notation_profile_version="1.0.0",
        textual_notation_preview="allocation preview",
        profile_validation_status="valid",
        profile_validation_fingerprint=SHA_D,
    )

    candidate = ModelRelationshipCandidate(
        schema_version="1.0.0",
        project_id="000042",
        candidate_set_id="MCS-000001",
        model_relationship_candidate_id="MCR-000001",
        relationship_choice_key="choice.session.component",
        source=ModelRelationshipEndpoint(
            candidate_subject_key="subject.session",
            resolution_status="resolved",
            resolved_model_element_candidate_id="MCE-000001",
            candidate_model_element_ids=("MCE-000001",),
        ),
        target=ModelRelationshipEndpoint(
            candidate_subject_key="subject.component",
            resolution_status="resolved",
            resolved_model_element_candidate_id="MCE-000002",
            candidate_model_element_ids=("MCE-000002",),
        ),
        relationship_family="allocation",
        semantic_intent="allocated_to",
        directionality="source_to_target",
        approved_input_references=(_approved_reference(),),
        derivation_rationale="Approved relationship carried forward.",
        supporting_evidence=("AIN-000001",),
        assumptions=(),
        missing_information=(),
        priority_assessment=priority,
        comparability_assessment=comparability,
        structure_profile_conformance=_conformance(),
        upstream_relationship_representation=upstream,
        predecessor_candidate_ids=(),
        created_at="2026-08-12T13:00:00Z",
        content_fingerprint=SHA_C,
    )

    assert (
        candidate.source.resolved_model_element_candidate_id
        == "MCE-000001"
    )
    assert (
        candidate.target.resolved_model_element_candidate_id
        == "MCE-000002"
    )
    assert candidate.priority_assessment.priority_class == "preferred"
    assert candidate.upstream_relationship_representation is upstream


@pytest.mark.parametrize(
    "instance",
    [
        _approved_reference(),
        _profile_reference(),
        _conformance(),
        ModelCandidateAttribute(name="a", value="b"),
        ModelRelationshipEndpoint(
            candidate_subject_key="subject.session",
            resolution_status="resolved",
            resolved_model_element_candidate_id="MCE-000001",
            candidate_model_element_ids=("MCE-000001",),
        ),
    ],
)
def test_foundation_types_are_immutable(instance):
    with pytest.raises(FrozenInstanceError):
        first_field = next(iter(instance.__dataclass_fields__))
        setattr(instance, first_field, "changed")


def test_slots_prevent_dynamic_attributes():
    instance = _approved_reference()

    with pytest.raises((AttributeError, TypeError)):
        instance.unplanned_field = "not allowed"
