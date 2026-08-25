from types import SimpleNamespace

from modules.model_placement.request_builder import (
    build_model_placement_request,
)


def _rule(rule_id, model_area, element_type, information_types):
    return SimpleNamespace(
        rule_id=rule_id,
        model_area_id=model_area,
        element_type=element_type,
        information_type_values=tuple(information_types),
    )


def _area(model_area, framework_node):
    return SimpleNamespace(
        model_area_id=model_area,
        framework_node_id=framework_node,
    )


def _input(approved_input_id, information_type):
    return SimpleNamespace(
        approved_input_id=approved_input_id,
        approved_input_kind="element_statement",
        stable_subject_key=f"subject:{approved_input_id.lower()}",
        canonical_content=SimpleNamespace(
            title=approved_input_id,
            primary_text="approved engineering meaning",
            description=None,
            information_type=information_type,
        ),
        selected_classification=None,
        selected_framework_assignment=None,
    )


def _coverage_entry(approved_input_id, disposition, selected=None, candidates=()):
    return SimpleNamespace(
        approved_input_id=approved_input_id,
        disposition=disposition,
        reason_code="test",
        selected_rule_id=selected,
        candidate_rule_ids=tuple(candidates),
    )


def _profile():
    return SimpleNamespace(
        profile_id="TURING_MODEL_STRUCTURE",
        profile_version="1.0.0",
        profile_fingerprint="a" * 64,
        model_areas=(
            _area("stakeholder.stakeholder_requirements", "FW_STK_REQ"),
            _area("system.requirements", "FW_SYS_REQ"),
            _area("subsystem.requirements", "FW_SUB_REQ"),
            _area("system.functional", "FW_SYS_FUN"),
            _area("subsystem.functional", "FW_SUB_FUN"),
            _area("system.logical", "FW_SYS_LOG"),
        ),
        element_derivation_rules=(
            _rule(
                "ELEMENT_STAKEHOLDER_REQUIREMENT",
                "stakeholder.stakeholder_requirements",
                "stakeholder_requirement",
                ("requirement",),
            ),
            _rule(
                "ELEMENT_SYSTEM_REQUIREMENT",
                "system.requirements",
                "system_requirement",
                ("requirement",),
            ),
            _rule(
                "ELEMENT_SUBSYSTEM_REQUIREMENT",
                "subsystem.requirements",
                "subsystem_requirement",
                ("requirement",),
            ),
            _rule(
                "ELEMENT_SYSTEM_FUNCTION",
                "system.functional",
                "function",
                ("function",),
            ),
            _rule(
                "ELEMENT_SUBSYSTEM_FUNCTION",
                "subsystem.functional",
                "function",
                ("function",),
            ),
            _rule(
                "ELEMENT_SYSTEM_LOGICAL",
                "system.logical",
                "logical_component",
                ("logical_element",),
            ),
        ),
    )


def test_requirement_options_explicitly_span_stakeholder_system_subsystem():
    request = SimpleNamespace(
        project_id="120412",
        approved_inputs=(_input("AIN-000001", "requirement"),),
    )
    coverage = SimpleNamespace(
        entries=(
            _coverage_entry(
                "AIN-000001",
                "ambiguous",
                candidates=(
                    "ELEMENT_SYSTEM_REQUIREMENT",
                    "ELEMENT_SUBSYSTEM_REQUIREMENT",
                ),
            ),
        )
    )

    placement = build_model_placement_request(
        request=request,
        coverage=coverage,
        profile=_profile(),
    )

    assert tuple(
        option.rule_id
        for option in placement.items[0].allowed_target_options
    ) == (
        "ELEMENT_STAKEHOLDER_REQUIREMENT",
        "ELEMENT_SUBSYSTEM_REQUIREMENT",
        "ELEMENT_SYSTEM_REQUIREMENT",
    )


def test_function_options_are_bounded_to_functional_levels():
    request = SimpleNamespace(
        project_id="120412",
        approved_inputs=(_input("AIN-000001", "function"),),
    )
    coverage = SimpleNamespace(
        entries=(
            _coverage_entry(
                "AIN-000001",
                "mapped",
                selected="ELEMENT_SYSTEM_FUNCTION",
            ),
        )
    )

    placement = build_model_placement_request(
        request=request,
        coverage=coverage,
        profile=_profile(),
    )

    item = placement.items[0]
    assert item.deterministic_candidate_rule_ids == (
        "ELEMENT_SYSTEM_FUNCTION",
    )
    assert {
        option.rule_id
        for option in item.allowed_target_options
    } == {
        "ELEMENT_SYSTEM_FUNCTION",
        "ELEMENT_SUBSYSTEM_FUNCTION",
    }


def test_profile_gap_falls_back_to_all_profile_options_without_inventing_rule():
    request = SimpleNamespace(
        project_id="120412",
        approved_inputs=(_input("AIN-000001", "interface"),),
    )
    coverage = SimpleNamespace(
        entries=(
            _coverage_entry("AIN-000001", "unmapped"),
        )
    )

    placement = build_model_placement_request(
        request=request,
        coverage=coverage,
        profile=_profile(),
    )

    assert len(placement.items[0].allowed_target_options) == 6
