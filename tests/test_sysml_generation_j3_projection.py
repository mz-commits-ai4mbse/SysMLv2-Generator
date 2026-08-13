from __future__ import annotations

from types import SimpleNamespace

import pytest

from modules.sysml_generation import (
    SysMLGenerationBlockedError,
    SysMLProjectionPlanService,
    load_artifact_structure_profile,
)


def _framework_ref():
    return SimpleNamespace(
        template_id="TURING_RFLP_FRAMEWORK",
        template_version="1.0.0",
    )


def _node(
    framework_node_id,
    mapping_key,
    *,
    parent=None,
    order=1,
    element_ids=(),
):
    return SimpleNamespace(
        framework_node_id=framework_node_id,
        mapping_key=mapping_key,
        name=mapping_key,
        node_type="framework_node",
        parent_framework_node_id=parent,
        order=order,
        internal_model_element_ids=tuple(element_ids),
    )


def _element(
    element_id,
    *,
    model_area,
    element_type,
    framework_assignment,
    name,
    description=None,
):
    return SimpleNamespace(
        project_id="000001",
        internal_model_element_id=element_id,
        model_area=model_area,
        element_type=element_type,
        framework_assignment=framework_assignment,
        name=name,
        description=description,
    )


def _relationship(
    relation_id,
    *,
    source,
    target,
    family="dependency",
    intent="dependency",
    directionality="source_to_target",
):
    return SimpleNamespace(
        internal_model_relationship_id=relation_id,
        source_internal_model_element_id=source,
        target_internal_model_element_id=target,
        relationship_family=family,
        semantic_intent=intent,
        directionality=directionality,
    )


def _snapshot(
    *,
    reverse_nodes=False,
    reverse_elements=False,
    reverse_relationships=False,
    unsafe_description=False,
):
    """Projection fixture uses dependency, not allocation.

    Requirements are intentionally present because J3 tests naming,
    documentation normalization and package ordering. Since J5.2 now correctly
    constrains allocation to PartUsage/ActionUsage endpoints, using requirements
    as synthetic allocation sources would contradict the production profile.
    Dependency remains valid for these generic projection tests.
    """

    artifact = load_artifact_structure_profile()

    memberships = {
        "FW_SYSTEM_REQUIREMENTS": ("IME-000002", "IME-000001"),
        "FW_SYSTEM_LOGICAL": ("IME-000003",),
    }

    nodes = [
        _node(
            item["framework_node_id"],
            item["mapping_key"],
            parent=item["parent_framework_node_id"],
            order=item["order"],
            element_ids=memberships.get(item["framework_node_id"], ()),
        )
        for item in artifact["framework_package_mappings"]
    ]
    if reverse_nodes:
        nodes.reverse()

    elements = [
        _element(
            "IME-000003",
            model_area="system.logical",
            element_type="logical_component",
            framework_assignment="FW_SYSTEM_LOGICAL",
            name="Controller",
            description="Logical controller.",
        ),
        _element(
            "IME-000002",
            model_area="system.requirements",
            element_type="system_requirement",
            framework_assignment="FW_SYSTEM_REQUIREMENTS",
            name="Requirement B",
            description=(
                "bad */ text"
                if unsafe_description
                else "Second reviewed requirement."
            ),
        ),
        _element(
            "IME-000001",
            model_area="system.requirements",
            element_type="system_requirement",
            framework_assignment="FW_SYSTEM_REQUIREMENTS",
            name="Requirement A",
            description="First reviewed requirement.\r\nSecond line.",
        ),
    ]
    if reverse_elements:
        elements.reverse()

    relationships = [
        _relationship(
            "IMR-000002",
            source="IME-000002",
            target="IME-000003",
        ),
        _relationship(
            "IMR-000001",
            source="IME-000001",
            target="IME-000003",
        ),
    ]
    if reverse_relationships:
        relationships.reverse()

    return SimpleNamespace(
        manifest=SimpleNamespace(
            schema_version="1.0.0",
            project_id="000001",
            internal_engineering_model_id="IEM-000001",
        ),
        structure=SimpleNamespace(
            schema_version="1.0.0",
            project_id="000001",
            internal_engineering_model_id="IEM-000001",
            framework_template_reference=_framework_ref(),
            nodes=tuple(nodes),
        ),
        elements=tuple(elements),
        relationships=tuple(relationships),
    )


def test_j3_projection_is_canonical_independent_of_input_tuple_order() -> None:
    service = SysMLProjectionPlanService()
    first = service.build(_snapshot())
    second = service.build(
        _snapshot(
            reverse_nodes=True,
            reverse_elements=True,
            reverse_relationships=True,
        )
    )
    assert first == second


def test_package_projection_follows_framework_hierarchy_and_order() -> None:
    plan = SysMLProjectionPlanService().build(_snapshot())
    assert [item.framework_node_id for item in plan.packages] == [
        "FW_LEVEL_STAKEHOLDER",
        "FW_STAKEHOLDER_STAKEHOLDERS",
        "FW_STAKEHOLDER_USER_NEEDS",
        "FW_STAKEHOLDER_STAKEHOLDER_REQUIREMENTS",
        "FW_STAKEHOLDER_USE_CASES",
        "FW_LEVEL_SYSTEM",
        "FW_SYSTEM_REQUIREMENTS",
        "FW_SYSTEM_FUNCTIONAL",
        "FW_SYSTEM_LOGICAL",
        "FW_SYSTEM_PHYSICAL",
        "FW_LEVEL_SUBSYSTEM",
        "FW_SUBSYSTEM_REQUIREMENTS",
        "FW_SUBSYSTEM_FUNCTIONAL",
        "FW_SUBSYSTEM_LOGICAL",
        "FW_SUBSYSTEM_PHYSICAL",
    ]
    assert plan.root_package_name == "GeneratedModel"
    assert plan.generated_unit_id == "GSU-000001"
    assert plan.relative_path == "generated_model.sysml"


def test_element_projection_uses_package_order_then_immutable_element_id() -> None:
    plan = SysMLProjectionPlanService().build(_snapshot())
    assert [item.internal_model_element_id for item in plan.elements] == [
        "IME-000001",
        "IME-000002",
        "IME-000003",
    ]
    assert [item.generated_symbol for item in plan.elements] == [
        "IME_000001",
        "IME_000002",
        "IME_000003",
    ]
    assert plan.elements[0].target_construct_id == "TN_008"
    assert plan.elements[2].target_construct_id == "TN_004"


def test_human_engineering_name_never_becomes_generated_identity() -> None:
    plan = SysMLProjectionPlanService().build(_snapshot())
    item = plan.elements[0]
    assert item.engineering_name == "Requirement A"
    assert item.generated_symbol == "IME_000001"
    assert item.engineering_name != item.generated_symbol


def test_description_line_endings_are_canonicalized_before_rendering() -> None:
    plan = SysMLProjectionPlanService().build(_snapshot())
    assert plan.elements[0].engineering_description == (
        "First reviewed requirement.\nSecond line."
    )


def test_relationship_projection_binds_exact_generated_endpoint_symbols() -> None:
    plan = SysMLProjectionPlanService().build(_snapshot())
    assert [item.internal_model_relationship_id for item in plan.relationships] == [
        "IMR-000001",
        "IMR-000002",
    ]
    first = plan.relationships[0]
    assert first.generated_trace_symbol == "IMR_000001"
    assert first.source_generated_symbol == "IME_000001"
    assert first.target_generated_symbol == "IME_000003"
    assert first.generation_rule_id == "J2_REL_002"
    assert first.target_construct_id == "TN_013"
    assert first.endpoint_rendering == "source_to_target"


def test_unsafe_documentation_content_blocks_instead_of_rewriting() -> None:
    with pytest.raises(SysMLGenerationBlockedError) as exc_info:
        SysMLProjectionPlanService().build(
            _snapshot(unsafe_description=True)
        )
    findings = exc_info.value.findings
    assert len(findings) == 1
    assert findings[0].code == "UNSAFE_DOCUMENTATION_CONTENT"
    assert findings[0].target_id == "IME-000002"


def test_satisfies_projection_reverses_textual_endpoint_order_only() -> None:
    snapshot = _snapshot()
    relation = SimpleNamespace(
        internal_model_relationship_id="IMR-000003",
        source_internal_model_element_id="IME-000003",
        target_internal_model_element_id="IME-000001",
        relationship_family="refinement",
        semantic_intent="satisfies",
        directionality="source_to_target",
    )
    snapshot = SimpleNamespace(
        manifest=snapshot.manifest,
        structure=snapshot.structure,
        elements=snapshot.elements,
        relationships=(relation,),
    )

    plan = SysMLProjectionPlanService().build(snapshot)
    projected = plan.relationships[0]
    assert projected.source_generated_symbol == "IME_000003"
    assert projected.target_generated_symbol == "IME_000001"
    assert projected.target_construct_id == "TN_015"
    assert projected.endpoint_rendering == "target_by_source"
