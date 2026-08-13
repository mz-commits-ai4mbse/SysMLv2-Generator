from __future__ import annotations

from dataclasses import replace

from modules.internal_model import (
    calculate_model_candidate_assembly_input_fingerprint,
)
from modules.model_candidates.types import (
    ModelCandidateAssemblyInput,
    ModelCandidateGenerationProvenance,
    ModelDerivationRulesReference,
    ModelStructureProfileReference,
)
from modules.project_workspace.types import FrameworkTemplateReference


def _input() -> ModelCandidateAssemblyInput:
    return ModelCandidateAssemblyInput(
        project_id="000001",
        candidate_set_id="MCS-000001",
        candidate_set_content_fingerprint="a" * 64,
        approved_input_snapshot_fingerprint="b" * 64,
        approved_input_references=(),
        framework_template_reference=FrameworkTemplateReference(
            template_id="TURING_RFLP_FRAMEWORK",
            template_version="1.0.0",
        ),
        model_structure_profile_reference=ModelStructureProfileReference(
            profile_id="TURING_MODEL_STRUCTURE",
            profile_version="1.0.0",
            profile_fingerprint="c" * 64,
        ),
        derivation_rules_reference=ModelDerivationRulesReference(
            context_id="CTX_SYSML_MODEL_DERIVATION_RULES",
            context_version="0.1.0",
            context_fingerprint="d" * 64,
        ),
        generation_provenance=ModelCandidateGenerationProvenance(
            method="profile_driven",
            recipe_reference=None,
            agent_reference=None,
            model_reference=None,
            context_fingerprint=None,
        ),
        accepted_element_candidates=(),
        accepted_relationship_candidates=(),
        accepted_exception_decisions=(),
        review_decision_references=(),
    )


def test_assembly_input_fingerprint_is_deterministic():
    value = _input()
    assert (
        calculate_model_candidate_assembly_input_fingerprint(value)
        == calculate_model_candidate_assembly_input_fingerprint(value)
    )


def test_framework_reference_changes_assembly_input_fingerprint():
    value = _input()
    changed = replace(
        value,
        framework_template_reference=FrameworkTemplateReference(
            template_id="TURING_RFLP_FRAMEWORK",
            template_version="1.0.1",
        ),
    )
    assert (
        calculate_model_candidate_assembly_input_fingerprint(value)
        != calculate_model_candidate_assembly_input_fingerprint(changed)
    )


def test_derivation_reference_changes_assembly_input_fingerprint():
    value = _input()
    changed = replace(
        value,
        derivation_rules_reference=replace(
            value.derivation_rules_reference,
            context_fingerprint="e" * 64,
        ),
    )
    assert (
        calculate_model_candidate_assembly_input_fingerprint(value)
        != calculate_model_candidate_assembly_input_fingerprint(changed)
    )
