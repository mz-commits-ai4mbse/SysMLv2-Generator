from __future__ import annotations

from modules.sysml_generation import (
    find_relationship_mapping,
    load_generation_profile,
)


def test_j5_renderer_scope_matches_exact_current_supported_relationship_set() -> None:
    profile = load_generation_profile()
    supported = {
        (
            item["semantic_intent"],
            item["target_construct_id"],
            item["endpoint_rendering"],
        )
        for item in profile["relationship_mappings"]
        if item["mapping_status"] == "supported"
    }

    assert supported == {
        ("allocated_to", "TN_014", "source_to_target"),
        ("dependency", "TN_013", "source_to_target"),
        ("depends_on", "TN_013", "source_to_target"),
        ("satisfies", "TN_015", "target_by_source"),
    }


def test_satisfies_is_explicitly_target_by_source_in_j5_2() -> None:
    profile = load_generation_profile()
    rule = find_relationship_mapping(
        profile,
        relationship_family="refinement",
        semantic_intent="satisfies",
        directionality="source_to_target",
    )
    assert rule is not None
    assert rule["mapping_status"] == "supported"
    assert rule["target_construct_id"] == "TN_015"
    assert rule["endpoint_rendering"] == "target_by_source"
    assert rule["production_generation_allowed"] is True
