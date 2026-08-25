from __future__ import annotations

from copy import deepcopy
from types import SimpleNamespace

import pytest

from modules.sysml_generation import SysMLGenerationBlockedError
from modules.sysml_generation.artifact_structure import (
    load_artifact_structure_profile,
)
from modules.sysml_generation.generation_profile import (
    load_generation_profile,
)
from modules.sysml_generation.preflight import (
    SysMLGenerationPreflightService,
)
from modules.sysml_generation.target_notation import load_target_notation


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
):
    return SimpleNamespace(
        internal_model_element_id=element_id,
        model_area=model_area,
        element_type=element_type,
        framework_assignment=framework_assignment,
    )


def _relationship(
    relation_id="IMR-000001",
    *,
    source="IME-000001",
    target="IME-000002",
    family="allocation",
    intent="allocated_to",
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


def _snapshot(*, relationships=None):
    """Synthetic snapshot with endpoint roles matching the active J5.2 profile.

    IME-000001 = function / ActionUsage / Feature
    IME-000002 = logical component / PartUsage / Feature
    IME-000003 = system requirement / RequirementUsage / Feature

    The default relationship is therefore a valid function -> component
    allocation. Satisfaction tests use component/function -> requirement.
    """

    artifact = load_artifact_structure_profile()
    memberships = {
        "FW_SYSTEM_FUNCTIONAL": ("IME-000001",),
        "FW_SYSTEM_LOGICAL": ("IME-000002",),
        "FW_SYSTEM_REQUIREMENTS": ("IME-000003",),
    }
    nodes = tuple(
        _node(
            item["framework_node_id"],
            item["mapping_key"],
            parent=item["parent_framework_node_id"],
            order=item["order"],
            element_ids=memberships.get(item["framework_node_id"], ()),
        )
        for item in artifact["framework_package_mappings"]
    )

    elements = (
        _element(
            "IME-000001",
            model_area="system.functional",
            element_type="function",
            framework_assignment="FW_SYSTEM_FUNCTIONAL",
        ),
        _element(
            "IME-000002",
            model_area="system.logical",
            element_type="logical_component",
            framework_assignment="FW_SYSTEM_LOGICAL",
        ),
        _element(
            "IME-000003",
            model_area="system.requirements",
            element_type="system_requirement",
            framework_assignment="FW_SYSTEM_REQUIREMENTS",
        ),
    )

    return SimpleNamespace(
        manifest=SimpleNamespace(
            internal_engineering_model_id="IEM-000001",
        ),
        structure=SimpleNamespace(
            framework_template_reference=_framework_ref(),
            nodes=nodes,
        ),
        elements=elements,
        relationships=(
            (_relationship(),)
            if relationships is None
            else tuple(relationships)
        ),
    )


def test_supported_snapshot_passes_j2_preflight() -> None:
    result = SysMLGenerationPreflightService().evaluate(_snapshot())
    assert result.ready is True
    assert result.findings == ()


def test_allocation_rejects_requirement_usage_endpoint() -> None:
    result = SysMLGenerationPreflightService().evaluate(
        _snapshot(
            relationships=(
                _relationship(
                    source="IME-000003",
                    target="IME-000002",
                ),
            )
        )
    )
    assert result.ready is False
    assert any(
        item.code == "RELATIONSHIP_ENDPOINT_CONSTRUCT_MISMATCH"
        and item.profile_rule_id == "J2_REL_001"
        for item in result.blocking_findings
    )


def test_stakeholder_mapping_blocks_without_force_fit() -> None:
    artifact = load_artifact_structure_profile()
    memberships = {
        "FW_STAKEHOLDER_STAKEHOLDERS": ("IME-000001",),
    }
    nodes = tuple(
        _node(
            item["framework_node_id"],
            item["mapping_key"],
            parent=item["parent_framework_node_id"],
            order=item["order"],
            element_ids=memberships.get(item["framework_node_id"], ()),
        )
        for item in artifact["framework_package_mappings"]
    )
    snapshot = SimpleNamespace(
        manifest=SimpleNamespace(internal_engineering_model_id="IEM-000001"),
        structure=SimpleNamespace(
            framework_template_reference=_framework_ref(),
            nodes=nodes,
        ),
        elements=(
            _element(
                "IME-000001",
                model_area="stakeholder.stakeholders",
                element_type="stakeholder",
                framework_assignment="FW_STAKEHOLDER_STAKEHOLDERS",
            ),
        ),
        relationships=(),
    )
    result = SysMLGenerationPreflightService().evaluate(snapshot)
    assert result.ready is True
    assert result.blocking_findings == ()


def test_satisfies_blocks_when_iem_endpoint_roles_are_wrong() -> None:
    # Requirement as source and component as target is the inverse of
    # the accepted canonical source-satisfies-target convention.
    result = SysMLGenerationPreflightService().evaluate(
        _snapshot(
            relationships=(
                _relationship(
                    source="IME-000003",
                    target="IME-000002",
                    family="refinement",
                    intent="satisfies",
                ),
            )
        )
    )
    assert result.ready is False
    assert any(
        item.code == "RELATIONSHIP_ENDPOINT_CONSTRUCT_MISMATCH"
        and item.profile_rule_id == "J2_REL_008"
        for item in result.blocking_findings
    )


@pytest.mark.parametrize("source", ["IME-000001", "IME-000002"])
def test_satisfies_preflight_accepts_function_or_component_source_requirement_target(
    source: str,
) -> None:
    result = SysMLGenerationPreflightService().evaluate(
        _snapshot(
            relationships=(
                _relationship(
                    source=source,
                    target="IME-000003",
                    family="refinement",
                    intent="satisfies",
                ),
            )
        )
    )
    assert result.ready is True
    assert result.findings == ()


def test_unknown_endpoint_blocks_generation() -> None:
    result = SysMLGenerationPreflightService().evaluate(
        _snapshot(
            relationships=(
                _relationship(target="IME-999999"),
            )
        )
    )
    assert result.ready is False
    assert any(
        item.code == "UNRESOLVED_GENERATED_ENDPOINT"
        for item in result.blocking_findings
    )


def test_profile_construct_not_allowed_blocks_generation() -> None:
    target = deepcopy(load_target_notation())
    target["allowed_constructs"] = [
        item
        for item in target["allowed_constructs"]
        if item["construct_id"] != "TN_014"
    ]
    result = SysMLGenerationPreflightService().evaluate(
        _snapshot(),
        target_notation=target,
    )
    assert result.ready is False
    assert any(
        item.code == "TARGET_CONSTRUCT_NOT_ALLOWED"
        for item in result.blocking_findings
    )


def test_structure_profile_mismatch_blocks_generation() -> None:
    artifact = deepcopy(load_artifact_structure_profile())
    for item in artifact["framework_package_mappings"]:
        if item["framework_node_id"] == "FW_SYSTEM_LOGICAL":
            item["mapping_key"] = "wrong.logical"
            break
    result = SysMLGenerationPreflightService().evaluate(
        _snapshot(),
        artifact_structure=artifact,
    )
    assert result.ready is False
    assert any(
        item.code == "STRUCTURE_PROJECTION_ERROR"
        for item in result.blocking_findings
    )


def test_require_ready_raises_structured_blocked_error() -> None:
    with pytest.raises(SysMLGenerationBlockedError) as exc_info:
        SysMLGenerationPreflightService().require_ready(
            _snapshot(
                relationships=(
                    _relationship(
                        source="IME-000003",
                        target="IME-000002",
                        family="refinement",
                        intent="satisfies",
                    ),
                )
            )
        )
    assert exc_info.value.findings
    assert all(item.blocking for item in exc_info.value.findings)
