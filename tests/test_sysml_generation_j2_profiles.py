from __future__ import annotations

import json

from modules.sysml_generation.artifact_structure import (
    load_artifact_structure_reference,
)
from modules.sysml_generation.generation_profile import (
    find_element_mapping,
    find_relationship_mapping,
    load_generation_profile,
    load_generation_profile_reference,
)


def test_generation_profile_covers_every_current_model_area_element_pair() -> None:
    model_profile = json.load(
        open("context/modeling/turing_model_structure_profile.json", encoding="utf-8")
    )
    generation = load_generation_profile()

    expected = {
        (area["model_area_id"], element_type)
        for area in model_profile["model_areas"]
        for element_type in area["permitted_element_types"]
    }
    actual = {
        (item["model_area"], item["element_type"])
        for item in generation["element_mappings"]
    }
    assert actual == expected


def test_generation_profile_covers_every_current_relationship_semantic_exactly() -> None:
    model_profile = json.load(
        open("context/modeling/turing_model_structure_profile.json", encoding="utf-8")
    )
    generation = load_generation_profile()

    expected = {
        (
            item["relationship_family"],
            item["semantic_intent"],
            item["directionality"],
        )
        for item in model_profile["relationship_semantics"]
    }
    actual = {
        (
            item["relationship_family"],
            item["semantic_intent"],
            item["directionality"],
        )
        for item in generation["relationship_mappings"]
    }
    assert actual == expected


def test_individual_requirements_map_to_requirement_usage_feature() -> None:
    generation = load_generation_profile()

    for model_area, element_type in (
        ("stakeholder.stakeholder_requirements", "stakeholder_requirement"),
        ("system.requirements", "system_requirement"),
        ("subsystem.requirements", "subsystem_requirement"),
    ):
        rule = find_element_mapping(
            generation,
            model_area=model_area,
            element_type=element_type,
        )
        assert rule is not None
        assert rule["mapping_status"] == "supported"
        assert rule["target_construct_id"] == "TN_008"
        assert rule["target_element_kind"] == "feature"


def test_function_and_components_map_to_usages_features_not_definitions() -> None:
    generation = load_generation_profile()

    cases = (
        ("system.functional", "function", "TN_006"),
        ("subsystem.functional", "function", "TN_006"),
        ("system.logical", "logical_component", "TN_004"),
        ("subsystem.logical", "logical_component", "TN_004"),
        ("system.physical", "physical_component", "TN_004"),
        ("subsystem.physical", "physical_component", "TN_004"),
    )
    for area, element_type, target in cases:
        rule = find_element_mapping(
            generation,
            model_area=area,
            element_type=element_type,
        )
        assert rule is not None
        assert rule["mapping_status"] == "supported"
        assert rule["target_construct_id"] == target
        assert rule["target_element_kind"] == "feature"


def test_use_case_definition_is_explicitly_a_definition_endpoint_kind() -> None:
    generation = load_generation_profile()
    rule = find_element_mapping(
        generation,
        model_area="stakeholder.use_cases",
        element_type="use_case",
    )
    assert rule is not None
    assert rule["target_construct_id"] == "TN_012"
    assert rule["target_element_kind"] == "definition"


def test_stakeholder_and_user_need_are_explicitly_unsupported_not_force_fit() -> None:
    generation = load_generation_profile()
    for area, element_type in (
        ("stakeholder.stakeholders", "stakeholder"),
        ("stakeholder.user_needs", "user_need"),
    ):
        rule = find_element_mapping(
            generation,
            model_area=area,
            element_type=element_type,
        )
        assert rule is not None
        assert rule["mapping_status"].startswith("unsupported_")
        assert rule["target_construct_id"] is None
        assert rule["target_element_kind"] is None
        assert rule["production_generation_allowed"] is False


def test_dependency_accepts_features_and_definitions_but_allocation_requires_features() -> None:
    generation = load_generation_profile()
    allocated = find_relationship_mapping(
        generation,
        relationship_family="allocation",
        semantic_intent="allocated_to",
        directionality="source_to_target",
    )
    dependency = find_relationship_mapping(
        generation,
        relationship_family="dependency",
        semantic_intent="dependency",
        directionality="source_to_target",
    )
    assert allocated["source_endpoint_kinds"] == ["feature"]
    assert allocated["target_endpoint_kinds"] == ["feature"]
    assert dependency["source_endpoint_kinds"] == ["feature", "definition"]
    assert dependency["target_endpoint_kinds"] == ["feature", "definition"]


def test_satisfies_maps_source_satisfier_to_target_requirement() -> None:
    generation = load_generation_profile()
    satisfies = find_relationship_mapping(
        generation,
        relationship_family="refinement",
        semantic_intent="satisfies",
        directionality="source_to_target",
    )
    assert satisfies is not None
    assert satisfies["mapping_status"] == "supported"
    assert satisfies["target_construct_id"] == "TN_015"
    assert satisfies["endpoint_rendering"] == "target_by_source"
    assert satisfies["source_endpoint_kinds"] == ["feature"]
    assert satisfies["target_endpoint_kinds"] == ["feature"]
    assert satisfies["source_endpoint_construct_ids"] == ["TN_004", "TN_006"]
    assert satisfies["target_endpoint_construct_ids"] == ["TN_008"]
    assert satisfies["production_generation_allowed"] is True


def test_profile_references_are_deterministic() -> None:
    assert load_generation_profile_reference() == load_generation_profile_reference()
    assert load_artifact_structure_reference() == load_artifact_structure_reference()
