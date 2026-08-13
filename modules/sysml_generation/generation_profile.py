"""Load and validate the Phase-J IEM → SysML v2 Generation Profile."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .errors import SysMLGenerationProfileError
from .fingerprints import calculate_json_fingerprint
from .profile_support import (
    exact_object,
    load_json_without_duplicate_keys,
    require_nonempty_string,
    require_rule_id,
    require_semver,
    require_upper_id,
)
from .types import SysMLGenerationProfileReference


DEFAULT_GENERATION_PROFILE_PATH = Path(
    "context/sysml/turing_sysml_v2_generation_profile.json"
)
GENERATION_PROFILE_SCHEMA_VERSION = "1.0.0"
EXPECTED_GENERATION_PROFILE_ID = "TURING_SYSML_V2_GENERATION"
EXPECTED_GENERATION_PROFILE_VERSION = "1.0.0"

_TOP_FIELDS = frozenset(
    {
        "schema_version",
        "profile_id",
        "profile_version",
        "status",
        "purpose",
        "target_notation_context_id",
        "target_notation_version",
        "framework_template_id",
        "framework_template_version",
        "model_structure_profile_id",
        "model_structure_profile_version",
        "element_mappings",
        "relationship_mappings",
        "attribute_policy",
        "documentation_policy",
        "unsupported_behavior",
    }
)
_ELEMENT_FIELDS = frozenset(
    {
        "rule_id",
        "model_area",
        "element_type",
        "mapping_status",
        "target_construct_id",
        "target_element_kind",
        "production_generation_allowed",
        "rationale",
    }
)
_REL_FIELDS = frozenset(
    {
        "rule_id",
        "semantic_intent",
        "relationship_family",
        "directionality",
        "mapping_status",
        "target_construct_id",
        "endpoint_rendering",
        "source_endpoint_kinds",
        "target_endpoint_kinds",
        "source_endpoint_construct_ids",
        "target_endpoint_construct_ids",
        "production_generation_allowed",
        "rationale",
    }
)
_ATTRIBUTE_FIELDS = frozenset(
    {
        "default_generic_attribute_projection",
        "formal_attribute_rules",
        "raw_attribute_to_formal_sysml_allowed",
        "unsupported_semantic_attribute_behavior",
    }
)
_DOCUMENTATION_FIELDS = frozenset(
    {
        "description_projection",
        "generic_metadata_projection",
        "raw_text_injection_allowed",
        "documentation_is_semantic_fallback",
    }
)
_SUPPORTED_ELEMENT_KINDS = frozenset({"feature", "definition"})


def load_generation_profile(
    path: Path | str = DEFAULT_GENERATION_PROFILE_PATH,
) -> dict[str, Any]:
    return validate_generation_profile(load_json_without_duplicate_keys(path))


def validate_generation_profile(value: object) -> dict[str, Any]:
    data = exact_object(
        value,
        expected=_TOP_FIELDS,
        label="SysML Generation Profile",
    )
    if data["schema_version"] != GENERATION_PROFILE_SCHEMA_VERSION:
        raise SysMLGenerationProfileError(
            "Unsupported SysML Generation Profile schema_version."
        )
    if require_upper_id(data["profile_id"], "profile_id") != (
        EXPECTED_GENERATION_PROFILE_ID
    ):
        raise SysMLGenerationProfileError(
            "Unexpected SysML Generation Profile profile_id."
        )
    if require_semver(data["profile_version"], "profile_version") != (
        EXPECTED_GENERATION_PROFILE_VERSION
    ):
        raise SysMLGenerationProfileError(
            "Unexpected SysML Generation Profile profile_version."
        )
    if data["status"] != "active":
        raise SysMLGenerationProfileError(
            "SysML Generation Profile must be active."
        )
    require_nonempty_string(data["purpose"], "purpose")
    require_upper_id(
        data["target_notation_context_id"],
        "target_notation_context_id",
    )
    require_semver(data["target_notation_version"], "target_notation_version")
    require_upper_id(data["framework_template_id"], "framework_template_id")
    require_semver(
        data["framework_template_version"],
        "framework_template_version",
    )
    require_upper_id(
        data["model_structure_profile_id"],
        "model_structure_profile_id",
    )
    require_semver(
        data["model_structure_profile_version"],
        "model_structure_profile_version",
    )

    elements = data["element_mappings"]
    if not isinstance(elements, list) or not elements:
        raise SysMLGenerationProfileError(
            "element_mappings must be a non-empty list."
        )
    normalized_elements = []
    element_keys: set[tuple[str, str]] = set()
    rule_ids: set[str] = set()
    for raw in elements:
        item = exact_object(
            raw,
            expected=_ELEMENT_FIELDS,
            label="element mapping",
        )
        rule_id = require_rule_id(item["rule_id"], "element mapping rule_id")
        if rule_id in rule_ids:
            raise SysMLGenerationProfileError(
                f"Duplicate generation rule_id: {rule_id}."
            )
        rule_ids.add(rule_id)
        model_area = require_nonempty_string(item["model_area"], "model_area")
        element_type = require_nonempty_string(
            item["element_type"],
            "element_type",
        )
        key = (model_area, element_type)
        if key in element_keys:
            raise SysMLGenerationProfileError(
                f"Duplicate element mapping key: {key!r}."
            )
        element_keys.add(key)
        _validate_element_mapping_state(item, label=rule_id)
        normalized_elements.append(dict(item))

    relationships = data["relationship_mappings"]
    if not isinstance(relationships, list) or not relationships:
        raise SysMLGenerationProfileError(
            "relationship_mappings must be a non-empty list."
        )
    normalized_relationships = []
    relationship_keys: set[tuple[str, str, str]] = set()
    for raw in relationships:
        item = exact_object(
            raw,
            expected=_REL_FIELDS,
            label="relationship mapping",
        )
        rule_id = require_rule_id(
            item["rule_id"],
            "relationship mapping rule_id",
        )
        if rule_id in rule_ids:
            raise SysMLGenerationProfileError(
                f"Duplicate generation rule_id: {rule_id}."
            )
        rule_ids.add(rule_id)
        key = (
            require_nonempty_string(
                item["relationship_family"],
                "relationship_family",
            ),
            require_nonempty_string(
                item["semantic_intent"],
                "semantic_intent",
            ),
            require_nonempty_string(
                item["directionality"],
                "directionality",
            ),
        )
        if key in relationship_keys:
            raise SysMLGenerationProfileError(
                f"Duplicate relationship mapping key: {key!r}."
            )
        relationship_keys.add(key)
        _validate_relationship_mapping_state(item, label=rule_id)
        normalized_relationships.append(dict(item))

    attribute_policy = exact_object(
        data["attribute_policy"],
        expected=_ATTRIBUTE_FIELDS,
        label="attribute_policy",
    )
    if attribute_policy["raw_attribute_to_formal_sysml_allowed"] is not False:
        raise SysMLGenerationProfileError(
            "raw_attribute_to_formal_sysml_allowed must be false."
        )
    if not isinstance(attribute_policy["formal_attribute_rules"], list):
        raise SysMLGenerationProfileError(
            "formal_attribute_rules must be a list."
        )

    documentation_policy = exact_object(
        data["documentation_policy"],
        expected=_DOCUMENTATION_FIELDS,
        label="documentation_policy",
    )
    if documentation_policy["raw_text_injection_allowed"] is not False:
        raise SysMLGenerationProfileError(
            "raw_text_injection_allowed must be false."
        )
    if documentation_policy["documentation_is_semantic_fallback"] is not False:
        raise SysMLGenerationProfileError(
            "documentation_is_semantic_fallback must be false."
        )
    if data["unsupported_behavior"] != "blocking":
        raise SysMLGenerationProfileError(
            "unsupported_behavior must be 'blocking'."
        )

    normalized = dict(data)
    normalized["element_mappings"] = normalized_elements
    normalized["relationship_mappings"] = normalized_relationships
    normalized["attribute_policy"] = dict(attribute_policy)
    normalized["documentation_policy"] = dict(documentation_policy)
    return normalized


def _validate_element_mapping_state(
    item: dict[str, Any],
    *,
    label: str,
) -> None:
    status = require_nonempty_string(item["mapping_status"], "mapping_status")
    allowed = item["production_generation_allowed"]
    target = item["target_construct_id"]
    target_kind = item["target_element_kind"]

    if not isinstance(allowed, bool):
        raise SysMLGenerationProfileError(
            f"{label} production_generation_allowed must be boolean."
        )
    require_nonempty_string(item["rationale"], f"{label} rationale")

    if status == "supported":
        if allowed is not True:
            raise SysMLGenerationProfileError(
                f"{label} supported mapping must allow production generation."
            )
        if not isinstance(target, str) or not target.startswith("TN_"):
            raise SysMLGenerationProfileError(
                f"{label} supported mapping requires a TN_ target construct."
            )
        if target_kind not in _SUPPORTED_ELEMENT_KINDS:
            raise SysMLGenerationProfileError(
                f"{label} supported mapping requires target_element_kind "
                "'feature' or 'definition'."
            )
    else:
        if allowed is not False:
            raise SysMLGenerationProfileError(
                f"{label} unsupported mapping must block production generation."
            )
        if target is not None or target_kind is not None:
            raise SysMLGenerationProfileError(
                f"{label} unsupported mapping must not define a target construct "
                "or target element kind."
            )


def _validate_relationship_mapping_state(
    item: dict[str, Any],
    *,
    label: str,
) -> None:
    status = require_nonempty_string(item["mapping_status"], "mapping_status")
    allowed = item["production_generation_allowed"]
    target = item["target_construct_id"]

    if not isinstance(allowed, bool):
        raise SysMLGenerationProfileError(
            f"{label} production_generation_allowed must be boolean."
        )
    require_nonempty_string(item["rationale"], f"{label} rationale")

    for field in ("source_endpoint_kinds", "target_endpoint_kinds"):
        kinds = item[field]
        if not isinstance(kinds, list):
            raise SysMLGenerationProfileError(
                f"{label} {field} must be a list."
            )
        if any(kind not in _SUPPORTED_ELEMENT_KINDS for kind in kinds):
            raise SysMLGenerationProfileError(
                f"{label} {field} contains an unsupported element kind."
            )
        if len(kinds) != len(set(kinds)):
            raise SysMLGenerationProfileError(
                f"{label} {field} must not contain duplicates."
            )

    for field in (
        "source_endpoint_construct_ids",
        "target_endpoint_construct_ids",
    ):
        construct_ids = item[field]
        if not isinstance(construct_ids, list):
            raise SysMLGenerationProfileError(
                f"{label} {field} must be a list."
            )
        if any(
            not isinstance(construct_id, str)
            or not construct_id.startswith("TN_")
            for construct_id in construct_ids
        ):
            raise SysMLGenerationProfileError(
                f"{label} {field} must contain only TN_ construct IDs."
            )
        if len(construct_ids) != len(set(construct_ids)):
            raise SysMLGenerationProfileError(
                f"{label} {field} must not contain duplicates."
            )

    if status == "supported":
        if allowed is not True:
            raise SysMLGenerationProfileError(
                f"{label} supported mapping must allow production generation."
            )
        if not isinstance(target, str) or not target.startswith("TN_"):
            raise SysMLGenerationProfileError(
                f"{label} supported mapping requires a TN_ target construct."
            )
        if item["endpoint_rendering"] not in {
            "source_to_target",
            "target_by_source",
        }:
            raise SysMLGenerationProfileError(
                f"{label} supported relationship requires endpoint_rendering."
            )
        if (
            not item["source_endpoint_kinds"]
            or not item["target_endpoint_kinds"]
        ):
            raise SysMLGenerationProfileError(
                f"{label} supported relationship requires explicit endpoint kinds."
            )
        if (
            not item["source_endpoint_construct_ids"]
            or not item["target_endpoint_construct_ids"]
        ):
            raise SysMLGenerationProfileError(
                f"{label} supported relationship requires explicit endpoint "
                "construct IDs."
            )
    else:
        if allowed is not False:
            raise SysMLGenerationProfileError(
                f"{label} unsupported mapping must block production generation."
            )
        if target is not None:
            raise SysMLGenerationProfileError(
                f"{label} unsupported mapping must not name a target construct."
            )
        if item["endpoint_rendering"] is not None:
            raise SysMLGenerationProfileError(
                f"{label} unsupported relationship must not render endpoints."
            )
        if item["source_endpoint_kinds"] or item["target_endpoint_kinds"]:
            raise SysMLGenerationProfileError(
                f"{label} unsupported relationship must not claim endpoint kinds."
            )
        if (
            item["source_endpoint_construct_ids"]
            or item["target_endpoint_construct_ids"]
        ):
            raise SysMLGenerationProfileError(
                f"{label} unsupported relationship must not claim endpoint "
                "construct IDs."
            )


def calculate_generation_profile_fingerprint(value: object) -> str:
    return calculate_json_fingerprint(validate_generation_profile(value))


def load_generation_profile_reference(
    path: Path | str = DEFAULT_GENERATION_PROFILE_PATH,
) -> SysMLGenerationProfileReference:
    profile = load_generation_profile(path)
    return SysMLGenerationProfileReference(
        profile_id=profile["profile_id"],
        profile_version=profile["profile_version"],
        profile_fingerprint=calculate_json_fingerprint(profile),
    )


def find_element_mapping(
    profile: dict[str, Any],
    *,
    model_area: str,
    element_type: str,
) -> dict[str, Any] | None:
    validated = validate_generation_profile(profile)
    for item in validated["element_mappings"]:
        if (
            item["model_area"] == model_area
            and item["element_type"] == element_type
        ):
            return item
    return None


def find_relationship_mapping(
    profile: dict[str, Any],
    *,
    relationship_family: str,
    semantic_intent: str,
    directionality: str,
) -> dict[str, Any] | None:
    validated = validate_generation_profile(profile)
    for item in validated["relationship_mappings"]:
        if (
            item["relationship_family"] == relationship_family
            and item["semantic_intent"] == semantic_intent
            and item["directionality"] == directionality
        ):
            return item
    return None
