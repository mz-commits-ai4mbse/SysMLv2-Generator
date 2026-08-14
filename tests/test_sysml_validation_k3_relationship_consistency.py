from __future__ import annotations

from dataclasses import replace
from types import SimpleNamespace

from modules.model_candidates.types import (
    ModelCandidateApprovedInputReference,
    ModelCandidateReviewDecisionReference,
)
from modules.sysml_generation.artifact_builder import SysMLArtifactSetBuilder
from modules.sysml_generation.artifact_structure import load_artifact_structure_profile
from modules.sysml_validation import validate_relationship_consistency


def _framework_ref():
    return SimpleNamespace(
        template_id="TURING_RFLP_FRAMEWORK",
        template_version="1.0.0",
    )


def _approved_ref(subject: str):
    return ModelCandidateApprovedInputReference(
        approved_input_id=f"AIN-{subject}",
        content_fingerprint="a" * 64,
        stable_subject_key=subject,
        provenance_role="primary",
    )


def _review(candidate_id: str, target_type: str):
    return ModelCandidateReviewDecisionReference(
        model_candidate_review_decision_id="MCD-" + candidate_id.split("-")[-1],
        target_type=target_type,
        candidate_id=candidate_id,
        decision="accepted",
        decision_fingerprint="b" * 64,
    )


def _node(item, memberships):
    return SimpleNamespace(
        framework_node_id=item["framework_node_id"],
        mapping_key=item["mapping_key"],
        name=item["mapping_key"],
        node_type="framework_node",
        parent_framework_node_id=item["parent_framework_node_id"],
        order=item["order"],
        internal_model_element_ids=tuple(
            memberships.get(item["framework_node_id"], ())
        ),
    )


def _element(element_id, *, area, element_type, assignment, name, candidate_id):
    return SimpleNamespace(
        schema_version="1.0.0",
        project_id="000001",
        internal_engineering_model_id="IEM-000001",
        internal_model_element_id=element_id,
        model_subject_key=element_id,
        source_model_element_candidate_id=candidate_id,
        source_model_element_candidate_fingerprint="c" * 64,
        name=name,
        description=f"Description for {name}.",
        model_area=area,
        element_type=element_type,
        framework_assignment=assignment,
        terminology_assignment=None,
        attributes=(),
        comparison_anchor_id=None,
        approved_input_references=(_approved_ref(element_id),),
        review_decision_reference=_review(candidate_id, "element_candidate"),
        accepted_exception_reference=None,
        content_fingerprint="d" * 64,
    )


def _relationship(relation_id, *, source, target, family, intent, candidate_id):
    return SimpleNamespace(
        schema_version="1.0.0",
        project_id="000001",
        internal_engineering_model_id="IEM-000001",
        internal_model_relationship_id=relation_id,
        source_internal_model_element_id=source,
        target_internal_model_element_id=target,
        source_model_subject_key=source,
        target_model_subject_key=target,
        relationship_family=family,
        semantic_intent=intent,
        directionality="source_to_target",
        source_model_relationship_candidate_id=candidate_id,
        source_model_relationship_candidate_fingerprint="e" * 64,
        approved_input_references=(_approved_ref(relation_id),),
        review_decision_reference=_review(candidate_id, "relationship_candidate"),
        accepted_exception_reference=None,
        content_fingerprint="f" * 64,
    )


def _snapshot():
    artifact = load_artifact_structure_profile()
    memberships = {
        "FW_SYSTEM_REQUIREMENTS": ("IME-000003",),
        "FW_SYSTEM_FUNCTIONAL": ("IME-000001",),
        "FW_SYSTEM_LOGICAL": ("IME-000002",),
    }
    nodes = tuple(
        _node(item, memberships)
        for item in artifact["framework_package_mappings"]
    )
    elements = (
        _element(
            "IME-000003",
            area="system.requirements",
            element_type="system_requirement",
            assignment="FW_SYSTEM_REQUIREMENTS",
            name="Example Requirement",
            candidate_id="MCE-000003",
        ),
        _element(
            "IME-000001",
            area="system.functional",
            element_type="function",
            assignment="FW_SYSTEM_FUNCTIONAL",
            name="Example Function",
            candidate_id="MCE-000001",
        ),
        _element(
            "IME-000002",
            area="system.logical",
            element_type="logical_component",
            assignment="FW_SYSTEM_LOGICAL",
            name="Example Component",
            candidate_id="MCE-000002",
        ),
    )
    relationships = (
        _relationship(
            "IMR-000001",
            source="IME-000001",
            target="IME-000002",
            family="allocation",
            intent="allocated_to",
            candidate_id="MCR-000001",
        ),
        _relationship(
            "IMR-000002",
            source="IME-000002",
            target="IME-000003",
            family="refinement",
            intent="satisfies",
            candidate_id="MCR-000002",
        ),
    )
    return SimpleNamespace(
        manifest=SimpleNamespace(
            schema_version="1.0.0",
            project_id="000001",
            internal_engineering_model_id="IEM-000001",
            content_fingerprint="1" * 64,
        ),
        structure=SimpleNamespace(
            schema_version="1.0.0",
            project_id="000001",
            internal_engineering_model_id="IEM-000001",
            framework_template_reference=_framework_ref(),
            nodes=nodes,
            content_fingerprint="2" * 64,
        ),
        elements=elements,
        relationships=relationships,
    )


def _artifact():
    return SysMLArtifactSetBuilder().build(_snapshot())


def _with_content_replacement(artifact, old: str, new: str):
    unit = artifact.units[0]
    assert old in unit.content
    return replace(
        artifact,
        units=(replace(unit, content=unit.content.replace(old, new, 1)),),
    )


def _codes(findings):
    return {item.code for item in findings}


def test_k3_accepts_actual_phase_j_relationship_output():
    artifact = _artifact()
    content = artifact.units[0].content
    assert "GeneratedModel::SystemLevel" not in content
    assert validate_relationship_consistency(artifact) == ()


def test_k3_accepts_dependency_contract_on_generated_endpoints():
    artifact = _artifact()
    changed = _with_content_replacement(
        artifact,
        "allocate SystemLevel::Functional::IME_000001 "
        "to SystemLevel::Logical::IME_000002;",
        "dependency from SystemLevel::Functional::IME_000001 "
        "to SystemLevel::Logical::IME_000002;",
    )
    assert validate_relationship_consistency(changed) == ()



def test_k3_rejects_unresolved_relationship_target():
    artifact = _artifact()
    changed = _with_content_replacement(
        artifact,
        "allocate SystemLevel::Functional::IME_000001 "
        "to SystemLevel::Logical::IME_000002;",
        "allocate SystemLevel::Functional::IME_000001 "
        "to SystemLevel::Logical::IME_999999;",
    )
    assert "K3_REL_TARGET_ENDPOINT_UNRESOLVED" in _codes(
        validate_relationship_consistency(changed)
    )


def test_k3_rejects_allocation_target_construct_mismatch():
    artifact = _artifact()
    changed = _with_content_replacement(
        artifact,
        "allocate SystemLevel::Functional::IME_000001 "
        "to SystemLevel::Logical::IME_000002;",
        "allocate SystemLevel::Functional::IME_000001 "
        "to SystemLevel::Requirements::IME_000003;",
    )
    assert "K3_REL_TARGET_ENDPOINT_CONSTRUCT_INCOMPATIBLE" in _codes(
        validate_relationship_consistency(changed)
    )


def test_k3_satisfaction_preserves_target_by_source_role_contract():
    artifact = _artifact()
    changed = _with_content_replacement(
        artifact,
        "satisfy SystemLevel::Requirements::IME_000003 "
        "by SystemLevel::Logical::IME_000002;",
        "satisfy SystemLevel::Requirements::IME_000003 "
        "by SystemLevel::Requirements::IME_000003;",
    )
    assert "K3_REL_SOURCE_ENDPOINT_CONSTRUCT_INCOMPATIBLE" in _codes(
        validate_relationship_consistency(changed)
    )


def test_k3_rejects_root_package_prefixed_endpoint_reference():
    artifact = _artifact()
    changed = _with_content_replacement(
        artifact,
        "allocate SystemLevel::Functional::IME_000001 "
        "to SystemLevel::Logical::IME_000002;",
        "allocate GeneratedModel::SystemLevel::Functional::IME_000001 "
        "to SystemLevel::Logical::IME_000002;",
    )
    assert "K3_REL_SOURCE_ENDPOINT_UNRESOLVED" in _codes(
        validate_relationship_consistency(changed)
    )


def test_k3_relationship_findings_point_to_relationship_trace_symbol():
    artifact = _artifact()
    changed = _with_content_replacement(
        artifact,
        "allocate SystemLevel::Functional::IME_000001 "
        "to SystemLevel::Logical::IME_000002;",
        "allocate SystemLevel::Functional::IME_000001 "
        "to SystemLevel::Logical::IME_999999;",
    )
    findings = validate_relationship_consistency(changed)
    target = next(
        item
        for item in findings
        if item.code == "K3_REL_TARGET_ENDPOINT_UNRESOLVED"
    )
    assert target.generated_unit_id == "GSU-000001"
    assert target.generated_symbol_id == "IMR_000001"
    assert target.generated_location is not None
    assert target.blocking is True
    assert target.severity == "error"
