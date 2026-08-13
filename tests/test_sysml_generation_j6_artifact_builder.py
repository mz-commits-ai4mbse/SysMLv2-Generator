from __future__ import annotations

from types import SimpleNamespace

from modules.model_candidates.types import (
    ModelCandidateApprovedInputReference,
    ModelCandidateReviewDecisionReference,
)
from modules.sysml_generation.artifact_builder import (
    SysMLArtifactSetBuilder,
    calculate_generation_input_fingerprint,
    validate_generated_artifact_set_integrity,
)
from modules.sysml_generation.artifact_structure import (
    load_artifact_structure_profile,
)


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
    nodes = tuple(_node(item, memberships) for item in artifact["framework_package_mappings"])

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


def test_j6_builds_one_validation_ready_generated_unit() -> None:
    artifact_set = SysMLArtifactSetBuilder().build(_snapshot())
    assert len(artifact_set.units) == 1
    unit = artifact_set.units[0]
    assert unit.unit_id == "GSU-000001"
    assert unit.relative_path == "generated_model.sysml"
    assert unit.content.startswith("package GeneratedModel {\n")
    assert unit.content.endswith("}\n")


def test_j6_assembles_framework_packages_and_supported_elements() -> None:
    content = SysMLArtifactSetBuilder().build(_snapshot()).units[0].content
    assert "package SystemLevel {" in content
    assert "package Requirements {" in content
    assert "package Functional {" in content
    assert "package Logical {" in content
    assert "requirement IME_000003 {" in content
    assert "action IME_000001 {" in content
    assert "part IME_000002 {" in content


def test_j6_relationships_use_root_relative_qualified_references() -> None:
    content = SysMLArtifactSetBuilder().build(_snapshot()).units[0].content
    assert (
        "allocate SystemLevel::Functional::IME_000001 "
        "to SystemLevel::Logical::IME_000002;"
    ) in content
    assert (
        "satisfy SystemLevel::Requirements::IME_000003 "
        "by SystemLevel::Logical::IME_000002;"
    ) in content


def test_j6_preserves_exact_traceability_for_every_ime_and_imr() -> None:
    snapshot = _snapshot()
    artifact_set = SysMLArtifactSetBuilder().build(snapshot)
    assert len(artifact_set.traceability_entries) == (
        len(snapshot.elements) + len(snapshot.relationships)
    )
    by_element = {
        item.source_internal_model_element_id: item
        for item in artifact_set.traceability_entries
        if item.source_internal_model_element_id is not None
    }
    by_relationship = {
        item.source_internal_model_relationship_id: item
        for item in artifact_set.traceability_entries
        if item.source_internal_model_relationship_id is not None
    }
    assert by_element["IME-000001"].source_model_candidate_id == "MCE-000001"
    assert by_relationship["IMR-000002"].source_model_candidate_id == "MCR-000002"
    assert by_element["IME-000001"].approved_input_references
    assert by_element["IME-000001"].review_decision_reference.decision == "accepted"
    assert by_relationship["IMR-000002"].generated_symbol_id == "IMR_000002"


def test_j6_trace_locations_point_at_exact_generated_text() -> None:
    artifact_set = SysMLArtifactSetBuilder().build(_snapshot())
    lines = artifact_set.units[0].content.splitlines()
    entries = {
        (
            item.source_internal_model_element_id
            or item.source_internal_model_relationship_id
        ): item
        for item in artifact_set.traceability_entries
    }
    element = entries["IME-000001"]
    assert "action IME_000001 {" in lines[element.generated_location.start_line - 1]
    relationship = entries["IMR-000001"]
    assert "allocate " in lines[relationship.generated_location.start_line - 1]


def test_j6_is_byte_and_fingerprint_idempotent() -> None:
    snapshot = _snapshot()
    first = SysMLArtifactSetBuilder().build(snapshot)
    second = SysMLArtifactSetBuilder().build(snapshot)
    assert first == second
    assert first.units[0].content == second.units[0].content
    assert first.units[0].content_fingerprint == second.units[0].content_fingerprint
    assert first.generation_input_fingerprint == second.generation_input_fingerprint
    assert first.content_fingerprint == second.content_fingerprint


def test_generation_input_fingerprint_is_bound_to_source_iem_and_context() -> None:
    artifact_set = SysMLArtifactSetBuilder().build(_snapshot())
    assert artifact_set.generation_input_fingerprint == (
        calculate_generation_input_fingerprint(
            source_iem_content_fingerprint="1" * 64,
            generation_context=artifact_set.generation_context,
        )
    )


def test_j6_integrity_validation_passes_built_artifact_set() -> None:
    snapshot = _snapshot()
    artifact_set = SysMLArtifactSetBuilder().build(snapshot)
    validate_generated_artifact_set_integrity(artifact_set, snapshot=snapshot)
