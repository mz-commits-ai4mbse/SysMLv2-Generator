"""Load and validate versioned project framework templates.

This module validates only the framework-template contract. It intentionally
does not define project persistence, information-unit storage or coverage
calculation.
"""

from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any


DEFAULT_FRAMEWORK_TEMPLATE_PATH = Path(
    "context/frameworks/turing_rflp_framework.json"
)

_IDENTIFIER_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]*$")
_NODE_IDENTIFIER_PATTERN = re.compile(r"^FW_[A-Z0-9_]+$")
_SEMANTIC_VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")

_NODE_TYPES = {
    "level",
    "framework_node",
}

_ASSESSMENT_KEYS = {
    "preliminary_coverage",
    "approved_readiness",
}


class FrameworkTemplateError(ValueError):
    """Raised when a framework template violates the P1 contract."""


def load_framework_template(
    path: Path = DEFAULT_FRAMEWORK_TEMPLATE_PATH,
) -> dict[str, Any]:
    """Load a JSON framework template and validate its contract."""

    try:
        template = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise FrameworkTemplateError(
            f"Unable to load framework template from {path}: {exc}"
        ) from exc

    validate_framework_template(template)

    return template


def validate_framework_template(template: dict[str, Any]) -> None:
    """Validate metadata, hierarchy and assessment boundaries."""

    if not isinstance(template, dict):
        raise FrameworkTemplateError(
            "Framework template must be a JSON object."
        )

    _validate_metadata(template)
    _validate_authority(template.get("authority"))
    _validate_information_unit_mapping(
        template.get("information_unit_mapping")
    )
    _validate_assessment_semantics(
        template.get("assessment_semantics")
    )
    _validate_nodes(template.get("nodes"))


def mapping_target_ids(template: dict[str, Any]) -> set[str]:
    """Return stable identifiers permitted in framework assignments."""

    validate_framework_template(template)

    return {
        node["node_id"]
        for node in template["nodes"]
        if node["mapping_target"]
    }


def _validate_metadata(template: dict[str, Any]) -> None:
    required_fields = {
        "schema_version",
        "template_id",
        "template_version",
        "name",
        "status",
    }

    _require_fields(
        template,
        required_fields,
        "framework template",
    )

    for field_name in (
        "schema_version",
        "template_version",
    ):
        value = template[field_name]

        if (
            not isinstance(value, str)
            or not _SEMANTIC_VERSION_PATTERN.fullmatch(value)
        ):
            raise FrameworkTemplateError(
                f"{field_name} must use "
                "MAJOR.MINOR.PATCH semantic versioning."
            )

    template_id = template["template_id"]

    if (
        not isinstance(template_id, str)
        or not _IDENTIFIER_PATTERN.fullmatch(template_id)
    ):
        raise FrameworkTemplateError(
            "template_id must be a stable uppercase identifier."
        )

    name = template["name"]

    if not isinstance(name, str) or not name.strip():
        raise FrameworkTemplateError(
            "Framework template name must be a non-empty string."
        )

    status = template["status"]

    if (
        not isinstance(status, str)
        or status not in {"draft", "active", "retired"}
    ):
        raise FrameworkTemplateError(
            "status must be one of: draft, active, retired."
        )


def _validate_authority(authority: Any) -> None:
    if not isinstance(authority, dict):
        raise FrameworkTemplateError(
            "authority must be an object."
        )

    _require_fields(
        authority,
        {
            "definition_basis",
            "engineering_authority",
            "shadow_model_rule",
            "non_normative_references",
        },
        "authority",
    )

    references = authority["non_normative_references"]

    if not isinstance(references, list):
        raise FrameworkTemplateError(
            "authority.non_normative_references must be a list."
        )

    for reference in references:
        if not isinstance(reference, dict):
            raise FrameworkTemplateError(
                "Every non-normative reference must be an object."
            )

        _require_fields(
            reference,
            {
                "source_id",
                "path",
                "repository",
                "reviewed_commit",
                "review_status",
                "usage",
                "adopted_pattern_ids",
            },
            "non-normative reference",
        )

        if reference["review_status"] != "reviewed_for_p1":
            raise FrameworkTemplateError(
                "Every P1 structural reference must be reviewed_for_p1."
            )

        pattern_ids = reference["adopted_pattern_ids"]

        if not isinstance(pattern_ids, list):
            raise FrameworkTemplateError(
                "adopted_pattern_ids must be a list."
            )

        if len(pattern_ids) != len(set(pattern_ids)):
            raise FrameworkTemplateError(
                "adopted_pattern_ids contains duplicate values."
            )


def _validate_information_unit_mapping(mapping: Any) -> None:
    if not isinstance(mapping, dict):
        raise FrameworkTemplateError(
            "information_unit_mapping must be an object."
        )

    _require_fields(
        mapping,
        {
            "eligible_source_roles",
            "cardinality_per_information_unit",
            "target_reference_field",
            "unknown_target_behavior",
            "context_only_mapping_allowed",
        },
        "information_unit_mapping",
    )

    if (
        mapping["cardinality_per_information_unit"]
        != "zero_to_many"
    ):
        raise FrameworkTemplateError(
            "Information units must support zero-to-many "
            "framework assignments."
        )

    if mapping["target_reference_field"] != "node_id":
        raise FrameworkTemplateError(
            "Framework assignments must reference stable node_id values."
        )

    if mapping["unknown_target_behavior"] != "reject":
        raise FrameworkTemplateError(
            "Unknown framework targets must be rejected."
        )

    if mapping["context_only_mapping_allowed"] is not False:
        raise FrameworkTemplateError(
            "context_only sources may not create framework mappings."
        )

    eligible_roles = mapping["eligible_source_roles"]

    _validate_source_roles(
        eligible_roles,
        "information_unit_mapping.eligible_source_roles",
    )

    if "engineering_source" not in eligible_roles:
        raise FrameworkTemplateError(
            "Framework mappings must support engineering_source inputs."
        )

    if "context_only" in eligible_roles:
        raise FrameworkTemplateError(
            "context_only sources may not be eligible "
            "for framework mappings."
        )


def _validate_assessment_semantics(semantics: Any) -> None:
    if not isinstance(semantics, dict):
        raise FrameworkTemplateError(
            "assessment_semantics must be an object."
        )

    missing_assessments = _ASSESSMENT_KEYS - semantics.keys()

    if missing_assessments:
        raise FrameworkTemplateError(
            "assessment_semantics is missing: "
            + ", ".join(sorted(missing_assessments))
        )

    for assessment_name in sorted(_ASSESSMENT_KEYS):
        assessment = semantics[assessment_name]

        if not isinstance(assessment, dict):
            raise FrameworkTemplateError(
                f"assessment_semantics.{assessment_name} "
                "must be an object."
            )

        _require_fields(
            assessment,
            {
                "label",
                "eligible_source_roles",
                "requires_human_approval",
                "phase_p_available",
                "excluded_source_roles",
            },
            f"assessment_semantics.{assessment_name}",
        )

        _validate_source_roles(
            assessment["eligible_source_roles"],
            (
                f"assessment_semantics.{assessment_name}."
                "eligible_source_roles"
            ),
        )

        _validate_source_roles(
            assessment["excluded_source_roles"],
            (
                f"assessment_semantics.{assessment_name}."
                "excluded_source_roles"
            ),
        )

        eligible_roles = set(
            assessment["eligible_source_roles"]
        )
        excluded_roles = set(
            assessment["excluded_source_roles"]
        )

        if eligible_roles & excluded_roles:
            raise FrameworkTemplateError(
                f"{assessment_name} source roles cannot be "
                "both eligible and excluded."
            )

        if "engineering_source" not in eligible_roles:
            raise FrameworkTemplateError(
                f"{assessment_name} must support "
                "engineering_source inputs."
            )

        if "context_only" not in excluded_roles:
            raise FrameworkTemplateError(
                f"{assessment_name} must exclude "
                "context_only sources."
            )

    preliminary = semantics["preliminary_coverage"]
    readiness = semantics["approved_readiness"]

    if preliminary["requires_human_approval"] is not False:
        raise FrameworkTemplateError(
            "Preliminary coverage must not require human approval."
        )

    if preliminary["phase_p_available"] is not True:
        raise FrameworkTemplateError(
            "Preliminary coverage must be available in Phase P."
        )

    if readiness["requires_human_approval"] is not True:
        raise FrameworkTemplateError(
            "Approved readiness must require human approval."
        )

    if readiness["phase_p_available"] is not False:
        raise FrameworkTemplateError(
            "Approved readiness must remain unavailable in Phase P."
        )

    if readiness.get("available_from_phase") != "G":
        raise FrameworkTemplateError(
            "Approved readiness must remain assigned to Phase G."
        )


def _validate_nodes(nodes: Any) -> None:
    if not isinstance(nodes, list) or not nodes:
        raise FrameworkTemplateError(
            "nodes must be a non-empty list."
        )

    node_ids: set[str] = set()
    mapping_keys: set[str] = set()
    sibling_orders: set[tuple[str | None, int]] = set()

    for node in nodes:
        if not isinstance(node, dict):
            raise FrameworkTemplateError(
                "Every framework node must be an object."
            )

        _require_fields(
            node,
            {
                "node_id",
                "mapping_key",
                "name",
                "node_type",
                "parent_node_id",
                "mapping_target",
                "order",
            },
            "framework node",
        )

        node_id = node["node_id"]

        if (
            not isinstance(node_id, str)
            or not _NODE_IDENTIFIER_PATTERN.fullmatch(node_id)
        ):
            raise FrameworkTemplateError(
                f"Invalid stable framework node identifier: "
                f"{node_id!r}."
            )

        if node_id in node_ids:
            raise FrameworkTemplateError(
                f"Duplicate node_id: {node_id}."
            )

        node_ids.add(node_id)

        mapping_key = node["mapping_key"]

        if (
            not isinstance(mapping_key, str)
            or not mapping_key.strip()
        ):
            raise FrameworkTemplateError(
                f"Node {node_id} must define "
                "a non-empty mapping_key."
            )

        if mapping_key in mapping_keys:
            raise FrameworkTemplateError(
                f"Duplicate mapping_key: {mapping_key}."
            )

        mapping_keys.add(mapping_key)

        name = node["name"]

        if not isinstance(name, str) or not name.strip():
            raise FrameworkTemplateError(
                f"Node {node_id} must define a non-empty name."
            )

        node_type = node["node_type"]

        if node_type not in _NODE_TYPES:
            raise FrameworkTemplateError(
                f"Node {node_id} has unsupported "
                f"node_type {node_type!r}."
            )

        if not isinstance(node["mapping_target"], bool):
            raise FrameworkTemplateError(
                f"Node {node_id} mapping_target must be boolean."
            )

        order = node["order"]

        if (
            isinstance(order, bool)
            or not isinstance(order, int)
            or order < 1
        ):
            raise FrameworkTemplateError(
                f"Node {node_id} order must be "
                "a positive integer."
            )

        parent_id = node["parent_node_id"]
        sibling_order = (parent_id, order)

        if sibling_order in sibling_orders:
            raise FrameworkTemplateError(
                f"Duplicate sibling order {order} "
                f"under {parent_id!r}."
            )

        sibling_orders.add(sibling_order)

    level_ids = {
        node["node_id"]
        for node in nodes
        if node["node_type"] == "level"
    }

    for node in nodes:
        node_id = node["node_id"]
        node_type = node["node_type"]
        parent_id = node["parent_node_id"]
        mapping_target = node["mapping_target"]

        if node_type == "level":
            if parent_id is not None or mapping_target:
                raise FrameworkTemplateError(
                    f"Level node {node_id} must be "
                    "a non-mapping root node."
                )

            continue

        if parent_id not in node_ids:
            raise FrameworkTemplateError(
                f"Framework node {node_id} references "
                f"unknown parent {parent_id!r}."
            )

        if parent_id not in level_ids:
            raise FrameworkTemplateError(
                f"Framework node {node_id} must be "
                "a direct child of a level."
            )

        if not mapping_target:
            raise FrameworkTemplateError(
                f"Framework node {node_id} must be "
                "an explicit mapping target."
            )


def _validate_source_roles(
    roles: Any,
    field_name: str,
) -> None:
    if not isinstance(roles, list) or not roles:
        raise FrameworkTemplateError(
            f"{field_name} must be a non-empty list."
        )

    if any(
        not isinstance(role, str) or not role
        for role in roles
    ):
        raise FrameworkTemplateError(
            f"{field_name} contains an invalid role."
        )

    if len(roles) != len(set(roles)):
        raise FrameworkTemplateError(
            f"{field_name} contains duplicate roles."
        )


def _require_fields(
    value: dict[str, Any],
    fields: set[str],
    object_name: str,
) -> None:
    missing_fields = fields - value.keys()

    if missing_fields:
        raise FrameworkTemplateError(
            f"{object_name} is missing required fields: "
            + ", ".join(sorted(missing_fields))
        )