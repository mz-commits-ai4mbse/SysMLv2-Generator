"""Load and validate deterministic Phase-J SysML artifact structure policy."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .errors import SysMLGenerationProfileError
from .fingerprints import calculate_json_fingerprint
from .identifiers import (
    validate_generated_sysml_symbol,
    validate_generated_sysml_unit_id,
)
from .profile_support import (
    exact_object,
    load_json_without_duplicate_keys,
    require_nonempty_string,
    require_semver,
    require_upper_id,
)
from .types import SysMLArtifactStructureReference


DEFAULT_ARTIFACT_STRUCTURE_PATH = Path(
    "context/sysml/turing_sysml_v2_artifact_structure.json"
)
ARTIFACT_STRUCTURE_SCHEMA_VERSION = "1.0.0"
EXPECTED_ARTIFACT_STRUCTURE_PROFILE_ID = (
    "TURING_SYSML_V2_ARTIFACT_STRUCTURE"
)
EXPECTED_ARTIFACT_STRUCTURE_PROFILE_VERSION = "1.0.0"

_TOP_FIELDS = frozenset(
    {
        "schema_version",
        "profile_id",
        "profile_version",
        "status",
        "purpose",
        "framework_template_id",
        "framework_template_version",
        "output_units",
        "root_package",
        "framework_package_mappings",
        "ordering",
        "empty_package_policy",
        "naming_policy",
    }
)
_UNIT_FIELDS = frozenset({"unit_id", "relative_path", "role"})
_ROOT_FIELDS = frozenset({"package_name", "display_name", "emit"})
_MAPPING_FIELDS = frozenset(
    {
        "framework_node_id",
        "mapping_key",
        "package_name",
        "parent_framework_node_id",
        "order",
        "include_empty",
    }
)
_ORDERING_FIELDS = frozenset(
    {"framework_nodes", "elements_within_package", "relationships"}
)
_NAMING_FIELDS = frozenset(
    {
        "generated_element_symbol",
        "generated_relationship_trace_symbol",
        "package_names",
        "display_names_are_identity",
    }
)


def load_artifact_structure_profile(
    path: Path | str = DEFAULT_ARTIFACT_STRUCTURE_PATH,
) -> dict[str, Any]:
    return validate_artifact_structure_profile(
        load_json_without_duplicate_keys(path)
    )


def validate_artifact_structure_profile(value: object) -> dict[str, Any]:
    data = exact_object(
        value,
        expected=_TOP_FIELDS,
        label="SysML Artifact Structure Profile",
    )
    if data["schema_version"] != ARTIFACT_STRUCTURE_SCHEMA_VERSION:
        raise SysMLGenerationProfileError(
            "Unsupported Artifact Structure schema_version."
        )
    if require_upper_id(data["profile_id"], "profile_id") != (
        EXPECTED_ARTIFACT_STRUCTURE_PROFILE_ID
    ):
        raise SysMLGenerationProfileError(
            "Unexpected Artifact Structure profile_id."
        )
    if require_semver(data["profile_version"], "profile_version") != (
        EXPECTED_ARTIFACT_STRUCTURE_PROFILE_VERSION
    ):
        raise SysMLGenerationProfileError(
            "Unexpected Artifact Structure profile_version."
        )
    if data["status"] != "active":
        raise SysMLGenerationProfileError(
            "Artifact Structure Profile must be active."
        )
    require_nonempty_string(data["purpose"], "purpose")
    require_upper_id(data["framework_template_id"], "framework_template_id")
    require_semver(
        data["framework_template_version"],
        "framework_template_version",
    )

    units = data["output_units"]
    if not isinstance(units, list) or len(units) != 1:
        raise SysMLGenerationProfileError(
            "The J2 MVP Artifact Structure must define exactly one output unit."
        )
    unit = exact_object(
        units[0],
        expected=_UNIT_FIELDS,
        label="output unit",
    )
    validate_generated_sysml_unit_id(unit["unit_id"])
    relative_path = require_nonempty_string(
        unit["relative_path"],
        "relative_path",
    )
    if Path(relative_path).is_absolute() or ".." in Path(relative_path).parts:
        raise SysMLGenerationProfileError(
            "relative_path must be a safe relative output path."
        )
    if not relative_path.endswith(".sysml"):
        raise SysMLGenerationProfileError(
            "Phase-J output unit must end with .sysml."
        )
    require_nonempty_string(unit["role"], "output unit role")

    root = exact_object(
        data["root_package"],
        expected=_ROOT_FIELDS,
        label="root_package",
    )
    validate_generated_sysml_symbol(root["package_name"])
    require_nonempty_string(root["display_name"], "root display_name")
    if root["emit"] is not True:
        raise SysMLGenerationProfileError(
            "J2 default Artifact Structure must emit the root package."
        )

    mappings = data["framework_package_mappings"]
    if not isinstance(mappings, list) or not mappings:
        raise SysMLGenerationProfileError(
            "framework_package_mappings must be a non-empty list."
        )
    normalized_mappings = []
    node_ids: set[str] = set()
    sibling_names: set[tuple[str | None, str]] = set()
    for raw in mappings:
        item = exact_object(
            raw,
            expected=_MAPPING_FIELDS,
            label="framework package mapping",
        )
        node_id = require_upper_id(
            item["framework_node_id"],
            "framework_node_id",
        )
        if node_id in node_ids:
            raise SysMLGenerationProfileError(
                f"Duplicate framework package mapping: {node_id}."
            )
        node_ids.add(node_id)
        require_nonempty_string(item["mapping_key"], "mapping_key")
        package_name = validate_generated_sysml_symbol(item["package_name"])
        parent = item["parent_framework_node_id"]
        if parent is not None:
            require_upper_id(parent, "parent_framework_node_id")
        if (
            isinstance(item["order"], bool)
            or not isinstance(item["order"], int)
            or item["order"] < 1
        ):
            raise SysMLGenerationProfileError(
                f"{node_id} order must be a positive integer."
            )
        if item["include_empty"] is not True:
            raise SysMLGenerationProfileError(
                f"{node_id} include_empty must be true in the default profile."
            )
        sibling_key = (parent, package_name)
        if sibling_key in sibling_names:
            raise SysMLGenerationProfileError(
                f"Duplicate sibling package name: {sibling_key!r}."
            )
        sibling_names.add(sibling_key)
        normalized_mappings.append(dict(item))

    for item in normalized_mappings:
        parent = item["parent_framework_node_id"]
        if parent is not None and parent not in node_ids:
            raise SysMLGenerationProfileError(
                f"Unknown package parent framework node: {parent}."
            )

    ordering = exact_object(
        data["ordering"],
        expected=_ORDERING_FIELDS,
        label="ordering",
    )
    expected_ordering = {
        "framework_nodes": "framework_template_order",
        "elements_within_package": "internal_model_element_id",
        "relationships": "internal_model_relationship_id",
    }
    if ordering != expected_ordering:
        raise SysMLGenerationProfileError(
            "Artifact Structure ordering must remain canonical."
        )
    if data["empty_package_policy"] != "include":
        raise SysMLGenerationProfileError(
            "Default J2 Artifact Structure must include empty packages."
        )

    naming = exact_object(
        data["naming_policy"],
        expected=_NAMING_FIELDS,
        label="naming_policy",
    )
    if naming["display_names_are_identity"] is not False:
        raise SysMLGenerationProfileError(
            "Display names must not be generated identity."
        )

    normalized = dict(data)
    normalized["output_units"] = [dict(unit)]
    normalized["root_package"] = dict(root)
    normalized["framework_package_mappings"] = normalized_mappings
    normalized["ordering"] = dict(ordering)
    normalized["naming_policy"] = dict(naming)
    return normalized


def calculate_artifact_structure_fingerprint(value: object) -> str:
    return calculate_json_fingerprint(validate_artifact_structure_profile(value))


def load_artifact_structure_reference(
    path: Path | str = DEFAULT_ARTIFACT_STRUCTURE_PATH,
) -> SysMLArtifactStructureReference:
    profile = load_artifact_structure_profile(path)
    return SysMLArtifactStructureReference(
        profile_id=profile["profile_id"],
        profile_version=profile["profile_version"],
        profile_fingerprint=calculate_json_fingerprint(profile),
    )
