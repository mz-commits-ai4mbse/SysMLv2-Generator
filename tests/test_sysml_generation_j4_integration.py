from __future__ import annotations

from types import SimpleNamespace

from modules.sysml_generation import (
    SysMLElementRenderer,
    SysMLProjectionPlanService,
    load_artifact_structure_profile,
)


def _framework_ref():
    return SimpleNamespace(
        template_id="TURING_RFLP_FRAMEWORK",
        template_version="1.0.0",
    )


def _node(item, element_ids=()):
    return SimpleNamespace(
        framework_node_id=item["framework_node_id"],
        mapping_key=item["mapping_key"],
        name=item["mapping_key"],
        node_type="framework_node",
        parent_framework_node_id=item["parent_framework_node_id"],
        order=item["order"],
        internal_model_element_ids=tuple(element_ids),
    )


def _element(element_id, *, area, element_type, framework_assignment, name):
    return SimpleNamespace(
        project_id="000001",
        internal_model_element_id=element_id,
        model_area=area,
        element_type=element_type,
        framework_assignment=framework_assignment,
        name=name,
        description="Reviewed engineering element.",
    )


def _snapshot():
    artifact = load_artifact_structure_profile()
    memberships = {
        "FW_STAKEHOLDER_STAKEHOLDER_REQUIREMENTS": ("IME-000001",),
        "FW_STAKEHOLDER_USE_CASES": ("IME-000002",),
        "FW_SYSTEM_FUNCTIONAL": ("IME-000003",),
        "FW_SYSTEM_LOGICAL": ("IME-000004",),
        "FW_SYSTEM_PHYSICAL": ("IME-000005",),
        "FW_SUBSYSTEM_REQUIREMENTS": ("IME-000006",),
        "FW_SUBSYSTEM_FUNCTIONAL": ("IME-000007",),
        "FW_SUBSYSTEM_LOGICAL": ("IME-000008",),
        "FW_SUBSYSTEM_PHYSICAL": ("IME-000009",),
        "FW_SYSTEM_REQUIREMENTS": ("IME-000010",),
    }
    nodes = tuple(
        _node(item, memberships.get(item["framework_node_id"], ()))
        for item in artifact["framework_package_mappings"]
    )

    elements = (
        _element("IME-000009", area="subsystem.physical", element_type="physical_component", framework_assignment="FW_SUBSYSTEM_PHYSICAL", name="Subsystem Physical"),
        _element("IME-000001", area="stakeholder.stakeholder_requirements", element_type="stakeholder_requirement", framework_assignment="FW_STAKEHOLDER_STAKEHOLDER_REQUIREMENTS", name="Stakeholder Requirement"),
        _element("IME-000004", area="system.logical", element_type="logical_component", framework_assignment="FW_SYSTEM_LOGICAL", name="System Logical"),
        _element("IME-000003", area="system.functional", element_type="function", framework_assignment="FW_SYSTEM_FUNCTIONAL", name="System Function"),
        _element("IME-000002", area="stakeholder.use_cases", element_type="use_case", framework_assignment="FW_STAKEHOLDER_USE_CASES", name="Use Case"),
        _element("IME-000010", area="system.requirements", element_type="system_requirement", framework_assignment="FW_SYSTEM_REQUIREMENTS", name="System Requirement"),
        _element("IME-000005", area="system.physical", element_type="physical_component", framework_assignment="FW_SYSTEM_PHYSICAL", name="System Physical"),
        _element("IME-000006", area="subsystem.requirements", element_type="subsystem_requirement", framework_assignment="FW_SUBSYSTEM_REQUIREMENTS", name="Subsystem Requirement"),
        _element("IME-000007", area="subsystem.functional", element_type="function", framework_assignment="FW_SUBSYSTEM_FUNCTIONAL", name="Subsystem Function"),
        _element("IME-000008", area="subsystem.logical", element_type="logical_component", framework_assignment="FW_SUBSYSTEM_LOGICAL", name="Subsystem Logical"),
    )

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
            nodes=nodes,
        ),
        elements=elements,
        relationships=(),
    )


def test_j4_renders_every_current_supported_element_mapping_end_to_end() -> None:
    plan = SysMLProjectionPlanService().build(_snapshot())
    rendered = SysMLElementRenderer().render_all(plan)

    assert len(rendered) == 10
    assert {item.target_construct_id for item in rendered} == {
        "TN_004",
        "TN_006",
        "TN_008",
        "TN_012",
    }


def test_current_components_and_functions_render_as_features() -> None:
    plan = SysMLProjectionPlanService().build(_snapshot())
    rendered = SysMLElementRenderer().render_all(plan)

    texts = {item.internal_model_element_id: item.content for item in rendered}
    assert texts["IME-000003"].startswith("action IME_000003 {")
    assert texts["IME-000004"].startswith("part IME_000004 {")
    assert texts["IME-000005"].startswith("part IME_000005 {")
