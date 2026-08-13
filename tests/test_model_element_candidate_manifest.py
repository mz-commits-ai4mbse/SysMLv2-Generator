"""Tests for strict Phase-H Model Element Candidate manifests."""

from dataclasses import replace
import json

import pytest

from modules.model_candidates import (
    ModelCandidateApprovedInputReference,
    ModelCandidateAttribute,
    ModelCandidateIntegrityError,
    ModelCandidateValidationError,
    StructuralProfileConformance,
    calculate_model_element_candidate_fingerprint,
    create_model_element_candidate,
    model_element_candidate_from_json,
    model_element_candidate_to_json,
)


A = "a" * 64
B = "b" * 64
C = "c" * 64


def _candidate():
    return create_model_element_candidate(
        project_id="000042",
        candidate_set_id="MCS-000001",
        model_element_candidate_id="MCE-000001",
        candidate_subject_key="subject.session",
        comparison_anchor_id="system.functional.session",
        proposed_name="Manage Session",
        description="Candidate function.",
        model_area="system_functional",
        element_type="function",
        framework_assignment="02_System/02_Functional",
        terminology_assignment=None,
        attributes=(
            ModelCandidateAttribute(name="zeta", value="2"),
            ModelCandidateAttribute(name="alpha", value="1"),
        ),
        approved_input_references=(
            ModelCandidateApprovedInputReference(
                approved_input_id="AIN-000001",
                content_fingerprint=A,
                stable_subject_key="subject.session",
                provenance_role="direct_support",
            ),
        ),
        derivation_rationale="Direct support.",
        support_level="supported",
        assumptions=("z", "a"),
        missing_information=(),
        structure_profile_conformance=StructuralProfileConformance(
            status="conformant",
            finding_ids=(),
            conformance_fingerprint=B,
        ),
        predecessor_candidate_ids=(),
        created_at="2026-08-12T13:00:00Z",
    )


def test_create_normalizes_attributes_and_strings():
    candidate = _candidate()
    assert tuple(item.name for item in candidate.attributes) == (
        "alpha",
        "zeta",
    )
    assert candidate.assumptions == ("a", "z")


def test_roundtrip_is_deterministic():
    candidate = _candidate()
    text = model_element_candidate_to_json(candidate)
    loaded = model_element_candidate_from_json(
        text,
        expected_project_id="000042",
        expected_candidate_set_id="MCS-000001",
        expected_model_element_candidate_id="MCE-000001",
    )
    assert loaded == candidate
    assert model_element_candidate_to_json(loaded) == text


def test_fingerprint_excludes_own_identity_and_timestamp():
    first = _candidate()
    second = replace(
        first,
        model_element_candidate_id="MCE-000999",
        created_at="2026-08-12T14:00:00Z",
    )
    assert calculate_model_element_candidate_fingerprint(first) == (
        calculate_model_element_candidate_fingerprint(second)
    )


def test_duplicate_attribute_names_are_rejected():
    with pytest.raises(ModelCandidateIntegrityError):
        create_model_element_candidate(
            project_id="000042",
            candidate_set_id="MCS-000001",
            model_element_candidate_id="MCE-000001",
            candidate_subject_key="subject.session",
            comparison_anchor_id=None,
            proposed_name="Manage Session",
            description=None,
            model_area="system_functional",
            element_type="function",
            framework_assignment=None,
            terminology_assignment=None,
            attributes=(
                ModelCandidateAttribute(name="x", value="1"),
                ModelCandidateAttribute(name="x", value="2"),
            ),
            approved_input_references=_candidate().approved_input_references,
            derivation_rationale="Direct support.",
            support_level="supported",
            assumptions=(),
            missing_information=(),
            structure_profile_conformance=(
                _candidate().structure_profile_conformance
            ),
            predecessor_candidate_ids=(),
            created_at="2026-08-12T13:00:00Z",
        )


def test_invalid_support_level_is_rejected():
    payload = json.loads(model_element_candidate_to_json(_candidate()))
    payload["support_level"] = "magic"
    payload["content_fingerprint"] = C
    with pytest.raises(ModelCandidateValidationError):
        model_element_candidate_from_json(json.dumps(payload))


def test_self_predecessor_is_rejected():
    payload = json.loads(model_element_candidate_to_json(_candidate()))
    payload["predecessor_candidate_ids"] = ["MCE-000001"]
    payload["content_fingerprint"] = C
    with pytest.raises(ModelCandidateIntegrityError):
        model_element_candidate_from_json(json.dumps(payload))


def test_tampered_content_is_detected():
    payload = json.loads(model_element_candidate_to_json(_candidate()))
    payload["proposed_name"] = "Changed"
    with pytest.raises(ModelCandidateIntegrityError):
        model_element_candidate_from_json(json.dumps(payload))


def test_unsorted_persisted_arrays_are_rejected():
    payload = json.loads(model_element_candidate_to_json(_candidate()))
    payload["assumptions"] = ["z", "a"]
    payload["content_fingerprint"] = C
    with pytest.raises(ModelCandidateValidationError):
        model_element_candidate_from_json(json.dumps(payload))


def test_unknown_fields_are_rejected():
    payload = json.loads(model_element_candidate_to_json(_candidate()))
    payload["unknown"] = True
    with pytest.raises(ModelCandidateValidationError):
        model_element_candidate_from_json(json.dumps(payload))
