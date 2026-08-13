"""Tests for strict Phase-H Model Candidate Set manifests."""

from dataclasses import replace
import json

import pytest

from modules.model_candidates import (
    ModelCandidateApprovedInputReference,
    ModelCandidateGenerationProvenance,
    ModelCandidateIntegrityError,
    ModelCandidateValidationError,
    ModelDerivationRulesReference,
    ModelStructureProfileReference,
    calculate_model_candidate_set_fingerprint,
    create_model_candidate_set_manifest,
    model_candidate_set_manifest_from_json,
    model_candidate_set_manifest_to_json,
)
from modules.project_workspace.types import FrameworkTemplateReference


A = "a" * 64
B = "b" * 64
C = "c" * 64


def _ref(number: int):
    char = chr(96 + number)
    return ModelCandidateApprovedInputReference(
        approved_input_id=f"AIN-{number:06d}",
        content_fingerprint=char * 64,
        stable_subject_key=f"subject.{number}",
        provenance_role="direct_support",
    )


def _manifest():
    return create_model_candidate_set_manifest(
        project_id="000042",
        candidate_set_id="MCS-000001",
        predecessor_candidate_set_id=None,
        regeneration_reason=None,
        approved_input_references=(_ref(2), _ref(1)),
        framework_template_reference=FrameworkTemplateReference(
            template_id="TURING_RFLP_FRAMEWORK",
            template_version="1.0.0",
        ),
        model_structure_profile_reference=ModelStructureProfileReference(
            profile_id="TURING_MODEL_STRUCTURE",
            profile_version="1.0.0",
            profile_fingerprint=B,
        ),
        derivation_rules_reference=ModelDerivationRulesReference(
            context_id="CTX_SYSML_MODEL_DERIVATION_RULES",
            context_version="0.1.0",
            context_fingerprint=C,
        ),
        generation_provenance=ModelCandidateGenerationProvenance(
            method="deterministic_test",
            recipe_reference="recipe://h",
            agent_reference=None,
            model_reference=None,
            context_fingerprint=None,
        ),
        element_candidate_ids=("MCE-000002", "MCE-000001"),
        relationship_candidate_ids=("MCR-000001",),
        created_at="2026-08-12T13:00:00Z",
    )


def test_create_normalizes_deterministic_order():
    manifest = _manifest()
    assert tuple(
        item.approved_input_id
        for item in manifest.approved_input_references
    ) == ("AIN-000001", "AIN-000002")
    assert manifest.element_candidate_ids == (
        "MCE-000001",
        "MCE-000002",
    )


def test_roundtrip_is_deterministic():
    manifest = _manifest()
    text = model_candidate_set_manifest_to_json(manifest)
    assert text.endswith("\n")
    loaded = model_candidate_set_manifest_from_json(
        text,
        expected_project_id="000042",
        expected_candidate_set_id="MCS-000001",
    )
    assert loaded == manifest
    assert model_candidate_set_manifest_to_json(loaded) == text


def test_fingerprint_excludes_own_identity_and_timestamp():
    first = _manifest()
    second = replace(
        first,
        candidate_set_id="MCS-000999",
        created_at="2026-08-12T14:00:00Z",
    )
    assert calculate_model_candidate_set_fingerprint(first) == (
        calculate_model_candidate_set_fingerprint(second)
    )


def test_tampered_fingerprint_is_rejected():
    with pytest.raises(ModelCandidateIntegrityError):
        model_candidate_set_manifest_to_json(
            replace(_manifest(), content_fingerprint=A)
        )


def test_snapshot_fingerprint_is_bound_to_exact_approved_inputs():
    payload = json.loads(
        model_candidate_set_manifest_to_json(_manifest())
    )
    payload["approved_input_snapshot_fingerprint"] = A
    payload["content_fingerprint"] = A
    with pytest.raises(ModelCandidateIntegrityError):
        model_candidate_set_manifest_from_json(json.dumps(payload))


def test_regeneration_requires_predecessor_and_reason_together():
    kwargs = {
        "project_id": "000042",
        "candidate_set_id": "MCS-000002",
        "approved_input_references": (_ref(1),),
        "framework_template_reference": FrameworkTemplateReference(
            template_id="TURING_RFLP_FRAMEWORK",
            template_version="1.0.0",
        ),
        "model_structure_profile_reference": ModelStructureProfileReference(
            profile_id="TURING_MODEL_STRUCTURE",
            profile_version="1.0.0",
            profile_fingerprint=B,
        ),
        "derivation_rules_reference": ModelDerivationRulesReference(
            context_id="CTX_SYSML_MODEL_DERIVATION_RULES",
            context_version="0.1.0",
            context_fingerprint=C,
        ),
        "generation_provenance": ModelCandidateGenerationProvenance(
            method="test",
            recipe_reference=None,
            agent_reference=None,
            model_reference=None,
            context_fingerprint=None,
        ),
        "element_candidate_ids": (),
        "relationship_candidate_ids": (),
        "created_at": "2026-08-12T13:00:00Z",
    }
    with pytest.raises(ModelCandidateIntegrityError):
        create_model_candidate_set_manifest(
            predecessor_candidate_set_id=None,
            regeneration_reason="inputs changed",
            **kwargs,
        )
    with pytest.raises(ModelCandidateIntegrityError):
        create_model_candidate_set_manifest(
            predecessor_candidate_set_id="MCS-000001",
            regeneration_reason=None,
            **kwargs,
        )


def test_self_predecessor_is_rejected():
    payload = json.loads(
        model_candidate_set_manifest_to_json(_manifest())
    )
    payload["predecessor_candidate_set_id"] = "MCS-000001"
    payload["regeneration_reason"] = "retry"
    payload["content_fingerprint"] = A
    with pytest.raises(ModelCandidateIntegrityError):
        model_candidate_set_manifest_from_json(json.dumps(payload))


def test_duplicate_approved_input_ids_are_rejected():
    with pytest.raises(ModelCandidateIntegrityError):
        create_model_candidate_set_manifest(
            project_id="000042",
            candidate_set_id="MCS-000001",
            predecessor_candidate_set_id=None,
            regeneration_reason=None,
            approved_input_references=(_ref(1), _ref(1)),
            framework_template_reference=FrameworkTemplateReference(
                template_id="TURING_RFLP_FRAMEWORK",
                template_version="1.0.0",
            ),
            model_structure_profile_reference=ModelStructureProfileReference(
                profile_id="TURING_MODEL_STRUCTURE",
                profile_version="1.0.0",
                profile_fingerprint=B,
            ),
            derivation_rules_reference=ModelDerivationRulesReference(
                context_id="CTX_SYSML_MODEL_DERIVATION_RULES",
                context_version="0.1.0",
                context_fingerprint=C,
            ),
            generation_provenance=ModelCandidateGenerationProvenance(
                method="test",
                recipe_reference=None,
                agent_reference=None,
                model_reference=None,
                context_fingerprint=None,
            ),
            element_candidate_ids=(),
            relationship_candidate_ids=(),
            created_at="2026-08-12T13:00:00Z",
        )


def test_duplicate_json_keys_are_rejected():
    text = model_candidate_set_manifest_to_json(_manifest())
    duplicate = text.replace(
        '"project_id": "000042",',
        '"project_id": "000042", "project_id": "000042",',
        1,
    )
    with pytest.raises(ModelCandidateValidationError):
        model_candidate_set_manifest_from_json(duplicate)


def test_unknown_fields_are_rejected():
    payload = json.loads(
        model_candidate_set_manifest_to_json(_manifest())
    )
    payload["unknown"] = "value"
    with pytest.raises(ModelCandidateValidationError):
        model_candidate_set_manifest_from_json(json.dumps(payload))
