"""Tests for conservative profile-driven Phase-H derivation."""

from dataclasses import replace

import pytest

from modules.approved_input.manifest import create_approved_input_manifest
from modules.approved_input.types import (
    ApprovedInputCanonicalContent,
    ApprovedInputRelationshipProperty,
    ApprovedInputRelationshipRepresentation,
)
from modules.model_candidates import (
    ModelCandidateDerivationError,
    ModelCandidateDerivationRequest,
    ModelCandidateReferenceError,
    ProfileDrivenModelCandidateDeriver,
    load_model_derivation_rules_reference,
    load_model_structure_profile,
    model_structure_profile_reference,
)
from modules.project_processing.types import ProcessingArtifactReference
from modules.project_workspace.types import FrameworkTemplateReference


PROJECT_ID = "318604"
A = "a" * 64
B = "b" * 64
C = "c" * 64
D = "d" * 64
E = "e" * 64


def _artifact(number):
    return ProcessingArtifactReference(
        artifact_type="information_unit",
        artifact_id=f"IU-{number:06d}",
        content_fingerprint=A,
        repository_relative_path=(
            f"data/projects/{PROJECT_ID}/semantics/"
            f"information_units/IU-{number:06d}.json"
        ),
    )


def _relationship(
    *,
    intent="allocated_to",
    construct="allocation",
    preview="allocation preview",
):
    return ApprovedInputRelationshipRepresentation(
        source_subject_key="subject.source",
        target_subject_key="subject.target",
        semantic_intent=intent,
        sysml_v2_construct=construct,
        construct_properties=(
            ApprovedInputRelationshipProperty(
                name="direction",
                value="source_to_target",
            ),
        ),
        target_notation_profile_id="SYSIDE_SYSML_V2",
        target_notation_profile_version="1.0.0",
        textual_notation_preview=preview,
        profile_validation_status="valid",
        profile_validation_fingerprint=E,
    )


def _input(
    number,
    *,
    kind="element_statement",
    subject="subject.source",
    title="Source",
    classification="System Requirement",
    framework="System Requirements",
    information_type="requirement",
    relationship=None,
):
    review_kind = {
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
            primary_text=f"{title} shall do something.",
            description=f"{title} reviewed description.",
            information_type=information_type,
            modality="shall",
            epistemic_status="reviewed",
        ),
        selected_classification=classification,
        selected_framework_assignment=framework,
        selected_terminology_assignment="requirement",
        selected_source_assignments=("SRC-000001",),
        selected_relationship_representation=relationship,
        stable_subject_key=subject,
        review_document_id=f"RVD-{number:06d}",
        review_document_version_id=f"RVV-{number:06d}",
        review_revision_id=f"RVR-{number:06d}",
        review_item_id=f"RIT-{number:06d}",
        review_item_kind=review_kind,
        review_item_fingerprint=A,
        finalized_artifact_set_fingerprint=B,
        finalization_decision_id=f"HRD-{number:06d}",
        finalization_decision_fingerprint=C,
        finalization_validation_fingerprint=D,
        source_id="SRC-000001",
        source_sha256=E,
        processing_run_id=f"RUN-{number:06d}",
        attempt_id="ATT-000001",
        primary_artifact_reference=_artifact(number),
        supporting_artifact_references=(),
        proposal_references=(),
        created_at="2026-08-13T06:30:00Z",
    )


def _setup():
    profile = load_model_structure_profile()
    rules = load_model_derivation_rules_reference()
    deriver = ProfileDrivenModelCandidateDeriver(
        profile=profile,
        derivation_rules_reference=rules,
    )
    return profile, rules, deriver


def _request(inputs):
    profile, rules, _ = _setup()
    return ModelCandidateDerivationRequest(
        project_id=PROJECT_ID,
        approved_inputs=tuple(inputs),
        framework_template_reference=FrameworkTemplateReference(
            template_id="TURING_RFLP_FRAMEWORK",
            template_version="1.0.0",
        ),
        model_structure_profile_reference=(
            model_structure_profile_reference(profile)
        ),
        derivation_rules_reference=rules,
        predecessor_candidate_set=None,
    )


def test_explicit_element_mapping_is_supported_and_preserves_content():
    _, _, deriver = _setup()
    plan = deriver.derive(
        _request((_input(1),))
    )
    assert len(plan.element_drafts) == 1
    draft = plan.element_drafts[0]
    assert draft.candidate_subject_key == "subject.source"
    assert draft.model_area == "system.requirements"
    assert draft.element_type == "system_requirement"
    assert draft.framework_assignment == "FW_SYSTEM_REQUIREMENTS"
    assert draft.support_level == "supported"
    assert draft.comparison_anchor_id == (
        "system.requirements:subject.source"
    )
    attributes = {
        item.name: item.value for item in draft.attributes
    }
    assert attributes["primary_text"] == "Source shall do something."
    assert attributes["source_classification"] == "System Requirement"


def test_framework_fallback_is_partial_and_explicit():
    _, _, deriver = _setup()
    approved = _input(
        1,
        classification=None,
        framework="System Requirements",
        information_type="requirement",
    )
    draft = deriver.derive(
        _request((approved,))
    ).element_drafts[0]
    assert draft.support_level == "partially_supported"
    assert draft.structure_profile_conformance.status == "review_required"
    assert "explicit_profile_classification" in (
        draft.missing_information
    )


def test_ambiguous_or_unknown_element_mapping_is_not_silently_guessed():
    _, _, deriver = _setup()
    unknown = _input(
        1,
        classification="Mystery",
        framework=None,
        information_type="mystery",
    )
    with pytest.raises(ModelCandidateDerivationError):
        deriver.derive(_request((unknown,)))

    ambiguous = _input(
        2,
        classification="Function",
        framework=None,
        information_type="function",
    )
    with pytest.raises(ModelCandidateDerivationError):
        deriver.derive(_request((ambiguous,)))


def test_human_clarification_remains_context_only():
    _, _, deriver = _setup()
    clarification = _input(
        1,
        kind="human_clarification",
        subject="clarification.one",
        title="Clarification",
        classification=None,
        framework=None,
        information_type=None,
    )
    plan = deriver.derive(_request((clarification,)))
    assert plan.element_drafts == ()
    assert plan.relationship_drafts == ()


def test_explicit_relationship_preserves_semantic_intent_and_upstream_evidence():
    _, _, deriver = _setup()
    source = _input(1, subject="subject.source", title="Source")
    target = _input(2, subject="subject.target", title="Target")
    rel = _input(
        3,
        kind="relationship_statement",
        subject="relationship.source.target",
        title="Allocation",
        classification=None,
        framework=None,
        information_type="relationship",
        relationship=_relationship(),
    )
    draft = deriver.derive(
        _request((source, target, rel))
    ).relationship_drafts[0]
    assert draft.semantic_intent == "allocated_to"
    assert draft.relationship_family == "allocation"
    assert draft.directionality == "source_to_target"
    assert (
        draft.upstream_relationship_representation
        == rel.selected_relationship_representation
    )
    assert draft.priority_assessment.priority_class == "preferred"
    assert tuple(
        item.criterion
        for item in draft.priority_assessment.criterion_results
    ) == (
        "evidence_directness",
        "semantic_fit",
        "endpoint_certainty",
        "structural_profile_preference",
        "structural_comparability_impact",
        "assumption_burden",
        "conformance",
    )
    assert draft.comparability_assessment.impact == "improves"


def test_unresolved_relationship_is_advisory_not_falsely_preferred():
    _, _, deriver = _setup()
    source = _input(1, subject="subject.source", title="Source")
    rel = _input(
        2,
        kind="relationship_statement",
        subject="relationship.source.target",
        title="Allocation",
        classification=None,
        framework=None,
        information_type="relationship",
        relationship=_relationship(),
    )
    draft = deriver.derive(
        _request((source, rel))
    ).relationship_drafts[0]
    assert draft.priority_assessment.priority_class == (
        "supported_alternative"
    )
    assert draft.comparability_assessment.impact == "unknown"
    assert draft.missing_information == (
        "exact_relationship_endpoint_resolution",
    )


def test_same_explicit_relationship_aggregates_provenance():
    _, _, deriver = _setup()
    source = _input(1, subject="subject.source", title="Source")
    target = _input(2, subject="subject.target", title="Target")
    rel_a = _input(
        3,
        kind="relationship_statement",
        subject="relationship.a",
        title="Allocation A",
        classification=None,
        framework=None,
        information_type="relationship",
        relationship=_relationship(),
    )
    rel_b = _input(
        4,
        kind="relationship_statement",
        subject="relationship.b",
        title="Allocation B",
        classification=None,
        framework=None,
        information_type="relationship",
        relationship=_relationship(),
    )
    drafts = deriver.derive(
        _request((source, target, rel_a, rel_b))
    ).relationship_drafts
    assert len(drafts) == 1
    assert tuple(
        item.approved_input_id
        for item in drafts[0].approved_input_selections
    ) == ("AIN-000003", "AIN-000004")


def test_materially_distinct_relationships_share_choice_key():
    _, _, deriver = _setup()
    source = _input(1, subject="subject.source", title="Source")
    target = _input(2, subject="subject.target", title="Target")
    rel_a = _input(
        3,
        kind="relationship_statement",
        subject="relationship.a",
        title="Allocation",
        classification=None,
        framework=None,
        information_type="relationship",
        relationship=_relationship(),
    )
    rel_b = _input(
        4,
        kind="relationship_statement",
        subject="relationship.b",
        title="Dependency",
        classification=None,
        framework=None,
        information_type="relationship",
        relationship=_relationship(
            intent="dependency",
            construct="dependency",
            preview="dependency preview",
        ),
    )
    drafts = deriver.derive(
        _request((source, target, rel_a, rel_b))
    ).relationship_drafts
    assert len(drafts) == 2
    assert drafts[0].relationship_choice_key is not None
    assert (
        drafts[0].relationship_choice_key
        == drafts[1].relationship_choice_key
    )
    assert {item.semantic_intent for item in drafts} == {
        "allocated_to",
        "dependency",
    }


def test_unknown_relationship_semantic_is_blocked_not_collapsed():
    _, _, deriver = _setup()
    rel = _input(
        1,
        kind="relationship_statement",
        subject="relationship.unknown",
        title="Unknown relationship",
        classification=None,
        framework=None,
        information_type="relationship",
        relationship=_relationship(
            intent="mystery_relation",
            construct="dependency",
            preview="mystery preview",
        ),
    )
    with pytest.raises(ModelCandidateDerivationError):
        deriver.derive(_request((rel,)))


def test_profile_reference_mismatch_is_rejected():
    profile, rules, deriver = _setup()
    request = _request((_input(1),))
    bad = replace(
        request,
        model_structure_profile_reference=replace(
            model_structure_profile_reference(profile),
            profile_fingerprint="f" * 64,
        ),
    )
    with pytest.raises(ModelCandidateReferenceError):
        deriver.derive(bad)
