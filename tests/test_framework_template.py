from copy import deepcopy

import pytest

from modules.framework import (
    FrameworkTemplateError,
    load_framework_template,
    mapping_target_ids,
    validate_framework_template,
)


EXPECTED_LEVELS = {
    "FW_LEVEL_STAKEHOLDER": [
        "FW_STAKEHOLDER_STAKEHOLDERS",
        "FW_STAKEHOLDER_USER_NEEDS",
        "FW_STAKEHOLDER_STAKEHOLDER_REQUIREMENTS",
        "FW_STAKEHOLDER_USE_CASES",
    ],
    "FW_LEVEL_SYSTEM": [
        "FW_SYSTEM_REQUIREMENTS",
        "FW_SYSTEM_FUNCTIONAL",
        "FW_SYSTEM_LOGICAL",
        "FW_SYSTEM_PHYSICAL",
    ],
    "FW_LEVEL_SUBSYSTEM": [
        "FW_SUBSYSTEM_REQUIREMENTS",
        "FW_SUBSYSTEM_FUNCTIONAL",
        "FW_SUBSYSTEM_LOGICAL",
        "FW_SUBSYSTEM_PHYSICAL",
    ],
}


def test_default_framework_template_is_valid_and_versioned() -> None:
    template = load_framework_template()

    assert template["template_id"] == "TURING_RFLP_FRAMEWORK"
    assert template["schema_version"] == "1.0.0"
    assert template["template_version"] == "1.0.0"
    assert template["status"] == "active"


def test_framework_has_expected_stable_mapping_targets() -> None:
    template = load_framework_template()
    nodes = template["nodes"]

    actual_levels = {
        level_id: [
            node["node_id"]
            for node in sorted(
                nodes,
                key=lambda item: item["order"],
            )
            if node["parent_node_id"] == level_id
        ]
        for level_id in EXPECTED_LEVELS
    }

    expected_targets = {
        node_id
        for child_ids in EXPECTED_LEVELS.values()
        for node_id in child_ids
    }

    assert actual_levels == EXPECTED_LEVELS
    assert mapping_target_ids(template) == expected_targets


def test_apollo_reference_is_reviewed_and_non_normative() -> None:
    template = load_framework_template()
    references = template["authority"]["non_normative_references"]

    assert len(references) == 1

    reference = references[0]

    assert reference["source_id"] == "SRC_APOLLO11_SYSML_V2"
    assert reference["reviewed_commit"] == "6e9c93f"
    assert reference["review_status"] == "reviewed_for_p1"

    assert set(reference["adopted_pattern_ids"]) == {
        "APOLLO_PATTERN_001",
        "APOLLO_PATTERN_002",
        "APOLLO_PATTERN_003",
        "APOLLO_PATTERN_004",
        "APOLLO_PATTERN_005",
        "APOLLO_PATTERN_006",
        "APOLLO_PATTERN_007",
        "APOLLO_PATTERN_008",
    }

    assert "APOLLO_PATTERN_009" not in reference[
        "adopted_pattern_ids"
    ]
    assert "APOLLO_PATTERN_010" not in reference[
        "adopted_pattern_ids"
    ]


def test_preliminary_coverage_and_readiness_are_separate() -> None:
    template = load_framework_template()
    semantics = template["assessment_semantics"]

    preliminary = semantics["preliminary_coverage"]
    readiness = semantics["approved_readiness"]

    assert preliminary["requires_human_approval"] is False
    assert preliminary["phase_p_available"] is True

    assert readiness["requires_human_approval"] is True
    assert readiness["phase_p_available"] is False
    assert readiness["available_from_phase"] == "G"

    assert "context_only" in preliminary["excluded_source_roles"]
    assert "context_only" in readiness["excluded_source_roles"]


def test_context_only_sources_cannot_create_framework_mappings() -> None:
    template = load_framework_template()
    mapping = template["information_unit_mapping"]

    assert (
        mapping["cardinality_per_information_unit"]
        == "zero_to_many"
    )
    assert mapping["target_reference_field"] == "node_id"
    assert mapping["unknown_target_behavior"] == "reject"
    assert mapping["context_only_mapping_allowed"] is False
    assert mapping["eligible_source_roles"] == [
        "engineering_source"
    ]


def test_context_only_mapping_eligibility_is_rejected() -> None:
    template = deepcopy(load_framework_template())

    template["information_unit_mapping"][
        "eligible_source_roles"
    ].append("context_only")

    with pytest.raises(
        FrameworkTemplateError,
        match="may not be eligible",
    ):
        validate_framework_template(template)


def test_duplicate_node_ids_are_rejected() -> None:
    template = deepcopy(load_framework_template())

    template["nodes"][1]["node_id"] = template["nodes"][0][
        "node_id"
    ]

    with pytest.raises(
        FrameworkTemplateError,
        match="Duplicate node_id",
    ):
        validate_framework_template(template)


def test_unknown_parent_is_rejected() -> None:
    template = deepcopy(load_framework_template())

    template["nodes"][1][
        "parent_node_id"
    ] = "FW_LEVEL_UNKNOWN"

    with pytest.raises(
        FrameworkTemplateError,
        match="unknown parent",
    ):
        validate_framework_template(template)


def test_approved_readiness_cannot_be_enabled_in_phase_p() -> None:
    template = deepcopy(load_framework_template())

    template["assessment_semantics"]["approved_readiness"][
        "phase_p_available"
    ] = True

    with pytest.raises(
        FrameworkTemplateError,
        match="unavailable in Phase P",
    ):
        validate_framework_template(template)