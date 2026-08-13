from __future__ import annotations

from copy import deepcopy
from types import SimpleNamespace

from modules.sysml_generation import (
    SysMLGenerationPreflightService,
    load_artifact_structure_profile,
    load_generation_profile,
)


def _framework_ref():
    return SimpleNamespace(
        template_id="TURING_RFLP_FRAMEWORK",
        template_version="1.0.0",
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


def test_allocation_preflight_blocks_definition_endpoint_kind() -> None:
    artifact = load_artifact_structure_profile()
    generation = deepcopy(load_generation_profile())

    # Intentionally re-create the failed J5.1 representation:
    for item in generation["element_mappings"]:
        if item["model_area"] == "system.logical":
            item["target_construct_id"] = "TN_003"
            item["target_element_kind"] = "definition"
            break

    memberships = {
        "FW_SYSTEM_FUNCTIONAL": ("IME-000001",),
        "FW_SYSTEM_LOGICAL": ("IME-000002",),
    }
    nodes = tuple(
        _node(item, memberships)
        for item in artifact["framework_package_mappings"]
    )
    elements = (
        SimpleNamespace(
            project_id="000001",
            internal_model_element_id="IME-000001",
            model_area="system.functional",
            element_type="function",
            framework_assignment="FW_SYSTEM_FUNCTIONAL",
        ),
        SimpleNamespace(
            project_id="000001",
            internal_model_element_id="IME-000002",
            model_area="system.logical",
            element_type="logical_component",
            framework_assignment="FW_SYSTEM_LOGICAL",
        ),
    )
    relationships = (
        SimpleNamespace(
            internal_model_relationship_id="IMR-000001",
            source_internal_model_element_id="IME-000001",
            target_internal_model_element_id="IME-000002",
            relationship_family="allocation",
            semantic_intent="allocated_to",
            directionality="source_to_target",
        ),
    )
    snapshot = SimpleNamespace(
        manifest=SimpleNamespace(
            project_id="000001",
            internal_engineering_model_id="IEM-000001",
        ),
        structure=SimpleNamespace(
            project_id="000001",
            framework_template_reference=_framework_ref(),
            nodes=nodes,
        ),
        elements=elements,
        relationships=relationships,
    )

    result = SysMLGenerationPreflightService().evaluate(
        snapshot,
        generation_profile=generation,
    )

    assert result.ready is False
    assert any(
        finding.code == "RELATIONSHIP_ENDPOINT_KIND_MISMATCH"
        and finding.target_id == "IMR-000001"
        for finding in result.blocking_findings
    )
