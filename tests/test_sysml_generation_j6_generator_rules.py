from __future__ import annotations

from modules.sysml_generation.generator_rules import (
    load_generator_rules,
    load_generator_rules_reference,
)


def test_j6_generator_rules_pin_root_relationship_placement() -> None:
    rules = load_generator_rules()
    relationship = rules["relationship_placement"]
    assert relationship["placement"] == "root_package_after_framework_packages"
    assert relationship["endpoint_reference"] == "qualified_from_root_package"
    assert relationship["qualification_separator"] == "::"


def test_j6_generator_rules_pin_machine_readable_traceability() -> None:
    trace = load_generator_rules()["traceability"]
    assert trace["element_entry_per_ime"] is True
    assert trace["relationship_entry_per_imr"] is True
    assert trace["approved_input_references_preserved"] is True
    assert trace["review_decision_reference_preserved"] is True
    assert trace["accepted_exception_reference_preserved"] is True


def test_generator_rules_reference_is_deterministic() -> None:
    assert load_generator_rules_reference() == load_generator_rules_reference()
