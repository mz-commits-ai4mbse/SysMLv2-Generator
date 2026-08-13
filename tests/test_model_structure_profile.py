"""Tests for the versioned Model Structure and Comparability Profile."""

from dataclasses import replace
import json

import pytest

from modules.framework import load_framework_template
from modules.model_candidates import (
    RELATIONSHIP_PRIORITY_CRITERIA,
    ModelCandidateValidationError,
    calculate_model_structure_profile_fingerprint,
    load_model_structure_profile,
    model_structure_profile_from_json,
    model_structure_profile_reference,
    model_structure_profile_to_dict,
)


def test_default_profile_loads_and_binds_framework():
    profile = load_model_structure_profile()
    assert profile.profile_id == "TURING_MODEL_STRUCTURE"
    assert profile.profile_version == "1.0.0"
    assert profile.framework_template_id == "TURING_RFLP_FRAMEWORK"
    assert profile.priority_criteria == RELATIONSHIP_PRIORITY_CRITERIA
    assert len(profile.model_areas) == 12
    assert len(profile.element_derivation_rules) == 12
    assert profile.profile_fingerprint == (
        calculate_model_structure_profile_fingerprint(profile)
    )


def test_profile_reference_is_exact_content_reference():
    profile = load_model_structure_profile()
    reference = model_structure_profile_reference(profile)
    assert reference.profile_id == profile.profile_id
    assert reference.profile_version == profile.profile_version
    assert reference.profile_fingerprint == profile.profile_fingerprint


def test_profile_roundtrip_is_canonical():
    profile = load_model_structure_profile()
    template = load_framework_template()
    payload = json.dumps(
        model_structure_profile_to_dict(profile),
        ensure_ascii=False,
    )
    parsed = model_structure_profile_from_json(
        payload,
        framework_template=template,
    )
    assert parsed == profile


def test_profile_rejects_unknown_framework_target():
    profile = load_model_structure_profile()
    template = load_framework_template()
    payload = model_structure_profile_to_dict(profile)
    payload["model_areas"][0]["framework_node_id"] = "FW_UNKNOWN"
    with pytest.raises(ModelCandidateValidationError):
        model_structure_profile_from_json(
            json.dumps(payload),
            framework_template=template,
        )


def test_profile_rejects_priority_order_drift():
    profile = load_model_structure_profile()
    template = load_framework_template()
    payload = model_structure_profile_to_dict(profile)
    payload["priority_criteria"][0], payload["priority_criteria"][1] = (
        payload["priority_criteria"][1],
        payload["priority_criteria"][0],
    )
    with pytest.raises(ModelCandidateValidationError):
        model_structure_profile_from_json(
            json.dumps(payload),
            framework_template=template,
        )


def test_profile_reference_rejects_tampered_fingerprint():
    profile = load_model_structure_profile()
    tampered = replace(profile, profile_fingerprint="a" * 64)
    with pytest.raises(ModelCandidateValidationError):
        model_structure_profile_reference(tampered)
