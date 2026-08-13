from __future__ import annotations

import json

from modules.sysml_generation.artifact_structure import (
    load_artifact_structure_profile,
)


def test_artifact_structure_covers_exact_framework_template() -> None:
    framework = json.load(
        open("context/frameworks/turing_rflp_framework.json", encoding="utf-8")
    )
    artifact = load_artifact_structure_profile()

    expected = {
        (
            node["node_id"],
            node["mapping_key"],
            node["parent_node_id"],
            node["order"],
        )
        for node in framework["nodes"]
    }
    actual = {
        (
            item["framework_node_id"],
            item["mapping_key"],
            item["parent_framework_node_id"],
            item["order"],
        )
        for item in artifact["framework_package_mappings"]
    }
    assert actual == expected


def test_default_mvp_artifact_structure_is_one_sysml_unit() -> None:
    artifact = load_artifact_structure_profile()
    assert artifact["output_units"] == [
        {
            "unit_id": "GSU-000001",
            "relative_path": "generated_model.sysml",
            "role": "complete_generated_model",
        }
    ]
    assert artifact["root_package"]["package_name"] == "GeneratedModel"


def test_empty_framework_packages_remain_explicit() -> None:
    artifact = load_artifact_structure_profile()
    assert artifact["empty_package_policy"] == "include"
    assert all(
        item["include_empty"] is True
        for item in artifact["framework_package_mappings"]
    )


def test_package_names_are_profile_defined_not_display_identity() -> None:
    artifact = load_artifact_structure_profile()
    assert artifact["naming_policy"]["display_names_are_identity"] is False
    assert artifact["naming_policy"]["generated_element_symbol"] == (
        "internal_model_element_id_with_hyphen_replaced_by_underscore"
    )
