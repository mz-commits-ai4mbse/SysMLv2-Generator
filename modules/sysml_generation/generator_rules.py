"""Load and pin deterministic Phase-J generator assembly rules."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .errors import SysMLGenerationProfileError
from .fingerprints import calculate_json_fingerprint
from .profile_support import (
    exact_object,
    load_json_without_duplicate_keys,
    require_nonempty_string,
    require_semver,
    require_upper_id,
)
from .types import SysMLGeneratorRulesReference


DEFAULT_GENERATOR_RULES_PATH = Path(
    "context/sysml/turing_sysml_v2_generator_rules.json"
)
GENERATOR_RULES_SCHEMA_VERSION = "1.0.0"
EXPECTED_GENERATOR_RULES_ID = "TURING_SYSML_V2_GENERATOR_RULES"
EXPECTED_GENERATOR_RULES_VERSION = "1.0.0"

_TOP_FIELDS = frozenset({
    "schema_version", "rules_id", "rules_version", "status", "purpose",
    "unit_assembly", "relationship_placement", "traceability", "fingerprints",
})
_UNIT_FIELDS = frozenset({
    "newline", "terminal_newline", "indentation",
    "root_package_from_artifact_structure_profile",
    "framework_packages_from_projection_plan",
    "framework_package_order", "element_order", "relationship_order",
})
_REL_FIELDS = frozenset({
    "placement", "endpoint_reference", "qualification_separator", "reason",
})
_TRACE_FIELDS = frozenset({
    "line_numbers", "element_entry_per_ime", "relationship_entry_per_imr",
    "relationship_generated_symbol_is_machine_trace_symbol",
    "approved_input_references_preserved",
    "review_decision_reference_preserved",
    "accepted_exception_reference_preserved",
})
_FP_FIELDS = frozenset({
    "algorithm", "json_canonicalization", "unit_content",
    "generation_input_includes",
})


def load_generator_rules(
    path: Path | str = DEFAULT_GENERATOR_RULES_PATH,
) -> dict[str, Any]:
    return validate_generator_rules(load_json_without_duplicate_keys(path))


def validate_generator_rules(value: object) -> dict[str, Any]:
    data = exact_object(value, expected=_TOP_FIELDS, label="SysML Generator Rules")

    if data["schema_version"] != GENERATOR_RULES_SCHEMA_VERSION:
        raise SysMLGenerationProfileError("Unsupported generator-rules schema_version.")
    if require_upper_id(data["rules_id"], "rules_id") != EXPECTED_GENERATOR_RULES_ID:
        raise SysMLGenerationProfileError("Unexpected generator-rules rules_id.")
    if require_semver(data["rules_version"], "rules_version") != EXPECTED_GENERATOR_RULES_VERSION:
        raise SysMLGenerationProfileError("Unexpected generator-rules rules_version.")
    if data["status"] != "active":
        raise SysMLGenerationProfileError("Generator Rules must be active.")
    require_nonempty_string(data["purpose"], "purpose")

    unit = exact_object(data["unit_assembly"], expected=_UNIT_FIELDS, label="unit_assembly")
    expected_unit = {
        "newline": "LF",
        "terminal_newline": True,
        "indentation": "four_spaces",
        "root_package_from_artifact_structure_profile": True,
        "framework_packages_from_projection_plan": True,
        "framework_package_order": "projection_plan_order",
        "element_order": "projection_plan_order",
        "relationship_order": "projection_plan_order",
    }
    if unit != expected_unit:
        raise SysMLGenerationProfileError(
            "Generator unit-assembly rules are not the canonical J6 MVP rules."
        )

    relationship = exact_object(
        data["relationship_placement"],
        expected=_REL_FIELDS,
        label="relationship_placement",
    )
    if relationship["placement"] != "root_package_after_framework_packages":
        raise SysMLGenerationProfileError(
            "Relationships must be emitted in the root package after Framework packages."
        )
    if relationship["endpoint_reference"] != "qualified_from_root_package":
        raise SysMLGenerationProfileError(
            "Relationship endpoints must use root-relative qualified references."
        )
    if relationship["qualification_separator"] != "::":
        raise SysMLGenerationProfileError("Qualified-reference separator must be '::'.")
    require_nonempty_string(relationship["reason"], "relationship placement reason")

    trace = exact_object(data["traceability"], expected=_TRACE_FIELDS, label="traceability")
    if trace["line_numbers"] != "one_based_inclusive":
        raise SysMLGenerationProfileError("Traceability line numbers must be one-based inclusive.")
    for field in (
        "element_entry_per_ime",
        "relationship_entry_per_imr",
        "relationship_generated_symbol_is_machine_trace_symbol",
        "approved_input_references_preserved",
        "review_decision_reference_preserved",
        "accepted_exception_reference_preserved",
    ):
        if trace[field] is not True:
            raise SysMLGenerationProfileError(f"{field} must be true.")

    fingerprints = exact_object(data["fingerprints"], expected=_FP_FIELDS, label="fingerprints")
    if fingerprints["algorithm"] != "sha256":
        raise SysMLGenerationProfileError("Generator fingerprint algorithm must be sha256.")
    if fingerprints["json_canonicalization"] != "utf8_sort_keys_compact":
        raise SysMLGenerationProfileError("Generator JSON canonicalization is unexpected.")
    if fingerprints["unit_content"] != "exact_utf8_bytes":
        raise SysMLGenerationProfileError("Unit-content fingerprint rule is unexpected.")
    expected_inputs = [
        "source_iem_content_fingerprint",
        "target_notation_reference",
        "generation_profile_reference",
        "artifact_structure_reference",
        "generator_rules_reference",
    ]
    if fingerprints["generation_input_includes"] != expected_inputs:
        raise SysMLGenerationProfileError(
            "generation_input_includes does not match ADR-021/J6."
        )

    normalized = dict(data)
    normalized["unit_assembly"] = dict(unit)
    normalized["relationship_placement"] = dict(relationship)
    normalized["traceability"] = dict(trace)
    normalized["fingerprints"] = dict(fingerprints)
    return normalized


def calculate_generator_rules_fingerprint(value: object) -> str:
    return calculate_json_fingerprint(validate_generator_rules(value))


def load_generator_rules_reference(
    path: Path | str = DEFAULT_GENERATOR_RULES_PATH,
) -> SysMLGeneratorRulesReference:
    rules = load_generator_rules(path)
    return SysMLGeneratorRulesReference(
        rules_id=rules["rules_id"],
        rules_version=rules["rules_version"],
        rules_fingerprint=calculate_json_fingerprint(rules),
    )
