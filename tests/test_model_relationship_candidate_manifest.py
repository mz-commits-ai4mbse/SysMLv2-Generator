"""Tests for strict Phase-H Model Relationship Candidate manifests."""

import json

import pytest

from modules.approved_input.types import (
    ApprovedInputRelationshipProperty,
    ApprovedInputRelationshipRepresentation,
)
from modules.model_candidates import (
    ModelCandidateApprovedInputReference,
    ModelCandidateIntegrityError,
    ModelCandidateValidationError,
    ModelRelationshipEndpoint,
    RelationshipPriorityAssessment,
    RelationshipPriorityCriterionResult,
    StructuralComparabilityAssessment,
    StructuralProfileConformance,
    create_model_relationship_candidate,
    model_relationship_candidate_from_json,
    model_relationship_candidate_to_json,
)


A = "a" * 64
B = "b" * 64
C = "c" * 64
D = "d" * 64


def _resolved(subject: str, mce: str):
    return ModelRelationshipEndpoint(
        candidate_subject_key=subject,
        resolution_status="resolved",
        resolved_model_element_candidate_id=mce,
        candidate_model_element_ids=(mce,),
    )


def _candidate(source=None, target=None):
    return create_model_relationship_candidate(
        project_id="000042",
        candidate_set_id="MCS-000001",
        model_relationship_candidate_id="MCR-000001",
        relationship_choice_key="choice.session.component",
        source=source or _resolved(
            "subject.session",
            "MCE-000001",
        ),
        target=target or _resolved(
            "subject.component",
            "MCE-000002",
        ),
        relationship_family="allocation",
        semantic_intent="allocated_to",
        directionality="source_to_target",
        approved_input_references=(
            ModelCandidateApprovedInputReference(
                approved_input_id="AIN-000001",
                content_fingerprint=A,
                stable_subject_key="subject.session",
                provenance_role="relationship_support",
            ),
        ),
        derivation_rationale="Explicit Approved Input relationship.",
        supporting_evidence=("AIN-000001",),
        assumptions=(),
        missing_information=(),
        priority_assessment=RelationshipPriorityAssessment(
            priority_class="preferred",
            criterion_results=(
                RelationshipPriorityCriterionResult(
                    criterion="evidence_directness",
                    result="explicit",
                    rationale="Explicit relationship evidence.",
                ),
                RelationshipPriorityCriterionResult(
                    criterion="semantic_fit",
                    result="strong",
                    rationale="Semantics fit allocation.",
                ),
            ),
            rationale="Preferred relationship.",
        ),
        comparability_assessment=StructuralComparabilityAssessment(
            impact="improves",
            comparison_anchor_ids=("system.functional.session",),
            canonical_pattern_match=True,
            deviation_ids=(),
            rationale="Matches canonical structure.",
        ),
        structure_profile_conformance=StructuralProfileConformance(
            status="conformant",
            finding_ids=(),
            conformance_fingerprint=B,
        ),
        upstream_relationship_representation=(
            ApprovedInputRelationshipRepresentation(
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
                profile_validation_fingerprint=C,
            )
        ),
        predecessor_candidate_ids=(),
        created_at="2026-08-12T13:00:00Z",
    )


def test_roundtrip_is_deterministic():
    candidate = _candidate()
    text = model_relationship_candidate_to_json(candidate)
    loaded = model_relationship_candidate_from_json(
        text,
        expected_project_id="000042",
        expected_candidate_set_id="MCS-000001",
        expected_model_relationship_candidate_id="MCR-000001",
    )
    assert loaded == candidate
    assert model_relationship_candidate_to_json(loaded) == text


def test_resolved_endpoint_requires_exact_single_candidate():
    bad = ModelRelationshipEndpoint(
        candidate_subject_key="subject.session",
        resolution_status="resolved",
        resolved_model_element_candidate_id="MCE-000001",
        candidate_model_element_ids=(
            "MCE-000001",
            "MCE-000002",
        ),
    )
    with pytest.raises(ModelCandidateIntegrityError):
        _candidate(source=bad)


def test_unresolved_endpoint_has_no_candidate_ids():
    candidate = _candidate(
        target=ModelRelationshipEndpoint(
            candidate_subject_key="subject.unknown",
            resolution_status="unresolved",
            resolved_model_element_candidate_id=None,
            candidate_model_element_ids=(),
        )
    )
    assert candidate.target.resolution_status == "unresolved"


def test_ambiguous_endpoint_requires_multiple_candidate_ids():
    candidate = _candidate(
        target=ModelRelationshipEndpoint(
            candidate_subject_key="subject.component",
            resolution_status="ambiguous",
            resolved_model_element_candidate_id=None,
            candidate_model_element_ids=(
                "MCE-000002",
                "MCE-000003",
            ),
        )
    )
    assert candidate.target.resolution_status == "ambiguous"

    bad = ModelRelationshipEndpoint(
        candidate_subject_key="subject.component",
        resolution_status="ambiguous",
        resolved_model_element_candidate_id=None,
        candidate_model_element_ids=("MCE-000002",),
    )
    with pytest.raises(ModelCandidateIntegrityError):
        _candidate(target=bad)


def test_priority_criteria_must_be_unique():
    payload = json.loads(
        model_relationship_candidate_to_json(_candidate())
    )
    payload["priority_assessment"]["criterion_results"][1][
        "criterion"
    ] = "evidence_directness"
    payload["content_fingerprint"] = D
    with pytest.raises(ModelCandidateIntegrityError):
        model_relationship_candidate_from_json(json.dumps(payload))


def test_invalid_comparability_impact_is_rejected():
    payload = json.loads(
        model_relationship_candidate_to_json(_candidate())
    )
    payload["comparability_assessment"]["impact"] = "excellent"
    payload["content_fingerprint"] = D
    with pytest.raises(ModelCandidateValidationError):
        model_relationship_candidate_from_json(json.dumps(payload))


def test_upstream_relationship_is_structurally_roundtripped():
    loaded = model_relationship_candidate_from_json(
        model_relationship_candidate_to_json(_candidate())
    )
    assert (
        loaded.upstream_relationship_representation.semantic_intent
        == "allocated_to"
    )


def test_tampered_content_is_detected():
    payload = json.loads(
        model_relationship_candidate_to_json(_candidate())
    )
    payload["semantic_intent"] = "depends_on"
    with pytest.raises(ModelCandidateIntegrityError):
        model_relationship_candidate_from_json(json.dumps(payload))


def test_self_predecessor_is_rejected():
    payload = json.loads(
        model_relationship_candidate_to_json(_candidate())
    )
    payload["predecessor_candidate_ids"] = ["MCR-000001"]
    payload["content_fingerprint"] = D
    with pytest.raises(ModelCandidateIntegrityError):
        model_relationship_candidate_from_json(json.dumps(payload))


def test_unknown_fields_are_rejected():
    payload = json.loads(
        model_relationship_candidate_to_json(_candidate())
    )
    payload["unknown"] = True
    with pytest.raises(ModelCandidateValidationError):
        model_relationship_candidate_from_json(json.dumps(payload))
