from __future__ import annotations

from dataclasses import replace

import pytest

from modules.framework import load_framework_template
from modules.internal_model import (
    InternalModelAssemblyBlockedError,
    InternalModelReferenceError,
    InternalModelStructureMaterializer,
    InternalModelStructureResolver,
    calculate_internal_model_assembly_rules_fingerprint,
    load_internal_model_assembly_rules,
    load_internal_model_assembly_rules_reference,
)
from modules.model_candidates.structure_profile import (
    load_model_structure_profile,
)
from modules.model_candidates.types import (
    ModelCandidateAssemblyInput,
    ModelCandidateGenerationProvenance,
    ModelDerivationRulesReference,
    ModelElementCandidate,
    ModelStructureProfileReference,
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


def _candidate(
    *,
    candidate_id: str,
    subject_key: str,
    name: str,
    model_area: str,
    element_type: str,
    framework_assignment: str,
    fingerprint_char: str,
) -> ModelElementCandidate:
    return ModelElementCandidate(
        schema_version="1.0.0",
        project_id="000001",
        candidate_set_id="MCS-000001",
        model_element_candidate_id=candidate_id,
        candidate_subject_key=subject_key,
        comparison_anchor_id=f"{model_area}:{subject_key}",
        proposed_name=name,
        description=None,
        model_area=model_area,
        element_type=element_type,
        framework_assignment=framework_assignment,
        terminology_assignment=None,
        attributes=(),
        approved_input_references=(),
        derivation_rationale="Reviewed Phase-H profile mapping.",
        support_level="supported",
        assumptions=(),
        missing_information=(),
        structure_profile_conformance=StructuralProfileConformance(
            status="conformant",
            finding_ids=(),
            conformance_fingerprint="a" * 64,
        ),
        predecessor_candidate_ids=(),
        created_at="2026-08-13T09:00:00Z",
        content_fingerprint=fingerprint_char * 64,
    )


def _assembly_input(
    elements: tuple[ModelElementCandidate, ...] = (),
) -> ModelCandidateAssemblyInput:
    template = load_framework_template()
    return ModelCandidateAssemblyInput(
        project_id="000001",
        candidate_set_id="MCS-000001",
        candidate_set_content_fingerprint="b" * 64,
        approved_input_snapshot_fingerprint="c" * 64,
        approved_input_references=(),
        framework_template_reference=FrameworkTemplateReference(
            template_id=template["template_id"],
            template_version=template["template_version"],
        ),
        model_structure_profile_reference=_profile_reference(),
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
        accepted_element_candidates=elements,
        accepted_relationship_candidates=(),
        accepted_exception_decisions=(),
        review_decision_references=(),
    )


def _system_logical_candidate() -> ModelElementCandidate:
    return _candidate(
        candidate_id="MCE-000001",
        subject_key="system.controller",
        name="Controller",
        model_area="system.logical",
        element_type="logical_component",
        framework_assignment="FW_SYSTEM_LOGICAL",
        fingerprint_char="1",
    )


def _system_requirement_candidate() -> ModelElementCandidate:
    return _candidate(
        candidate_id="MCE-000002",
        subject_key="system.requirement.one",
        name="Requirement One",
        model_area="system.requirements",
        element_type="system_requirement",
        framework_assignment="FW_SYSTEM_REQUIREMENTS",
        fingerprint_char="2",
    )


def test_assembly_rules_are_strict_and_reference_is_deterministic():
    rules = load_internal_model_assembly_rules()
    reference = load_internal_model_assembly_rules_reference()

    assert rules["rules_id"] == "TURING_INTERNAL_MODEL_ASSEMBLY"
    assert rules["policies"]["unreviewed_reclassification_allowed"] is False
    assert rules["policies"]["invent_engineering_hierarchy_allowed"] is False
    assert (
        reference.rules_fingerprint
        == calculate_internal_model_assembly_rules_fingerprint(rules)
    )


def test_resolver_binds_exact_framework_profile_and_rules():
    assembly_input = _assembly_input()
    resolved = InternalModelStructureResolver().resolve(assembly_input)

    assert (
        resolved.assembly_context.framework_template_reference
        == assembly_input.framework_template_reference
    )
    assert (
        resolved.assembly_context.model_structure_profile_reference
        == assembly_input.model_structure_profile_reference
    )
    assert (
        resolved.assembly_context.derivation_rules_reference
        == assembly_input.derivation_rules_reference
    )
    assert (
        resolved.assembly_context.assembly_rules_reference.rules_id
        == "TURING_INTERNAL_MODEL_ASSEMBLY"
    )


def test_resolver_rejects_framework_reference_mismatch():
    assembly_input = _assembly_input()
    changed = replace(
        assembly_input,
        framework_template_reference=FrameworkTemplateReference(
            template_id="TURING_RFLP_FRAMEWORK",
            template_version="9.9.9",
        ),
    )

    with pytest.raises(InternalModelReferenceError):
        InternalModelStructureResolver().resolve(changed)


def test_resolver_rejects_profile_fingerprint_mismatch():
    assembly_input = _assembly_input()
    changed = replace(
        assembly_input,
        model_structure_profile_reference=replace(
            assembly_input.model_structure_profile_reference,
            profile_fingerprint="f" * 64,
        ),
    )

    with pytest.raises(InternalModelReferenceError):
        InternalModelStructureResolver().resolve(changed)


def test_materializer_builds_complete_framework_hierarchy_with_empty_nodes():
    element = _system_logical_candidate()
    assembly_input = _assembly_input((element,))
    resolved = InternalModelStructureResolver().resolve(assembly_input)

    structure = InternalModelStructureMaterializer().materialize(
        project_id="000001",
        internal_engineering_model_id="IEM-000001",
        assembly_input=assembly_input,
        resolved_context=resolved,
        internal_element_id_by_candidate_id={
            "MCE-000001": "IME-000001",
        },
    )

    assert len(structure.nodes) == 15
    assert structure.nodes[0].framework_node_id == "FW_LEVEL_STAKEHOLDER"
    assert structure.nodes[5].framework_node_id == "FW_LEVEL_SYSTEM"
    assert structure.nodes[10].framework_node_id == "FW_LEVEL_SUBSYSTEM"

    logical = next(
        node
        for node in structure.nodes
        if node.framework_node_id == "FW_SYSTEM_LOGICAL"
    )
    assert logical.internal_model_element_ids == ("IME-000001",)

    physical = next(
        node
        for node in structure.nodes
        if node.framework_node_id == "FW_SYSTEM_PHYSICAL"
    )
    assert physical.internal_model_element_ids == ()


def test_materializer_places_elements_using_reviewed_phase_h_assignment():
    logical = _system_logical_candidate()
    requirement = _system_requirement_candidate()
    assembly_input = _assembly_input((logical, requirement))
    resolved = InternalModelStructureResolver().resolve(assembly_input)

    structure = InternalModelStructureMaterializer().materialize(
        project_id="000001",
        internal_engineering_model_id="IEM-000001",
        assembly_input=assembly_input,
        resolved_context=resolved,
        internal_element_id_by_candidate_id={
            "MCE-000001": "IME-000002",
            "MCE-000002": "IME-000001",
        },
    )

    by_node = {
        node.framework_node_id: node.internal_model_element_ids
        for node in structure.nodes
    }
    assert by_node["FW_SYSTEM_LOGICAL"] == ("IME-000002",)
    assert by_node["FW_SYSTEM_REQUIREMENTS"] == ("IME-000001",)


def test_materialization_is_deterministic_for_candidate_order():
    logical = _system_logical_candidate()
    requirement = _system_requirement_candidate()
    first = _assembly_input((logical, requirement))
    second = _assembly_input((requirement, logical))

    materializer = InternalModelStructureMaterializer()
    first_structure = materializer.materialize(
        project_id="000001",
        internal_engineering_model_id="IEM-000001",
        assembly_input=first,
        resolved_context=InternalModelStructureResolver().resolve(first),
        internal_element_id_by_candidate_id={
            "MCE-000001": "IME-000002",
            "MCE-000002": "IME-000001",
        },
    )
    second_structure = materializer.materialize(
        project_id="000001",
        internal_engineering_model_id="IEM-000001",
        assembly_input=second,
        resolved_context=InternalModelStructureResolver().resolve(second),
        internal_element_id_by_candidate_id={
            "MCE-000001": "IME-000002",
            "MCE-000002": "IME-000001",
        },
    )

    assert first_structure == second_structure


def test_materializer_rejects_missing_ime_mapping():
    element = _system_logical_candidate()
    assembly_input = _assembly_input((element,))
    resolved = InternalModelStructureResolver().resolve(assembly_input)

    with pytest.raises(InternalModelAssemblyBlockedError):
        InternalModelStructureMaterializer().materialize(
            project_id="000001",
            internal_engineering_model_id="IEM-000001",
            assembly_input=assembly_input,
            resolved_context=resolved,
            internal_element_id_by_candidate_id={},
        )


def test_materializer_rejects_duplicate_ime_assignment():
    elements = (
        _system_logical_candidate(),
        _system_requirement_candidate(),
    )
    assembly_input = _assembly_input(elements)
    resolved = InternalModelStructureResolver().resolve(assembly_input)

    with pytest.raises(InternalModelAssemblyBlockedError):
        InternalModelStructureMaterializer().materialize(
            project_id="000001",
            internal_engineering_model_id="IEM-000001",
            assembly_input=assembly_input,
            resolved_context=resolved,
            internal_element_id_by_candidate_id={
                "MCE-000001": "IME-000001",
                "MCE-000002": "IME-000001",
            },
        )


def test_materializer_rejects_reclassification_by_framework_assignment():
    element = replace(
        _system_logical_candidate(),
        framework_assignment="FW_SYSTEM_PHYSICAL",
    )
    assembly_input = _assembly_input((element,))
    resolved = InternalModelStructureResolver().resolve(assembly_input)

    with pytest.raises(InternalModelAssemblyBlockedError):
        InternalModelStructureMaterializer().materialize(
            project_id="000001",
            internal_engineering_model_id="IEM-000001",
            assembly_input=assembly_input,
            resolved_context=resolved,
            internal_element_id_by_candidate_id={
                "MCE-000001": "IME-000001",
            },
        )


def test_materializer_rejects_element_type_not_permitted_in_area():
    element = replace(
        _system_logical_candidate(),
        element_type="physical_component",
    )
    assembly_input = _assembly_input((element,))
    resolved = InternalModelStructureResolver().resolve(assembly_input)

    with pytest.raises(InternalModelAssemblyBlockedError):
        InternalModelStructureMaterializer().materialize(
            project_id="000001",
            internal_engineering_model_id="IEM-000001",
            assembly_input=assembly_input,
            resolved_context=resolved,
            internal_element_id_by_candidate_id={
                "MCE-000001": "IME-000001",
            },
        )
