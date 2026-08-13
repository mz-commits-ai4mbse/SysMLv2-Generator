"""Load and validate deterministic Phase-I Internal Model assembly rules."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
from typing import Any

from .errors import InternalModelValidationError
from .types import InternalModelAssemblyRulesReference


DEFAULT_INTERNAL_MODEL_ASSEMBLY_RULES_PATH = Path(
    "context/modeling/turing_internal_model_assembly_rules.json"
)
INTERNAL_MODEL_ASSEMBLY_RULES_SCHEMA_VERSION = "1.0.0"
EXPECTED_INTERNAL_MODEL_ASSEMBLY_RULES_ID = "TURING_INTERNAL_MODEL_ASSEMBLY"

_SEMVER_PATTERN = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
_UPPER_ID_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]*$")

_TOP_FIELDS = frozenset(
    {
        "schema_version",
        "rules_id",
        "rules_version",
        "status",
        "framework_template_id",
        "framework_template_version",
        "model_structure_profile_id",
        "model_structure_profile_version",
        "policies",
    }
)
_POLICY_FIELDS = frozenset(
    {
        "materialize_complete_framework_hierarchy",
        "allow_empty_structure_nodes",
        "element_membership_cardinality",
        "candidate_framework_assignment_authority",
        "unknown_framework_assignment_behavior",
        "profile_mismatch_behavior",
        "unreviewed_reclassification_allowed",
        "invent_engineering_hierarchy_allowed",
        "structure_node_ordering",
        "element_membership_ordering",
    }
)


def load_internal_model_assembly_rules(
    path: Path | str = DEFAULT_INTERNAL_MODEL_ASSEMBLY_RULES_PATH,
) -> dict[str, Any]:
    rules_path = Path(path)
    try:
        payload = rules_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise InternalModelValidationError(
            f"Unable to read Internal Model assembly rules: {rules_path}."
        ) from exc

    try:
        data = json.loads(
            payload,
            object_pairs_hook=_without_duplicate_keys,
        )
    except InternalModelValidationError:
        raise
    except json.JSONDecodeError as exc:
        raise InternalModelValidationError(
            "Internal Model assembly rules are not valid JSON."
        ) from exc

    return validate_internal_model_assembly_rules(data)


def validate_internal_model_assembly_rules(
    value: object,
) -> dict[str, Any]:
    data = _exact_object(
        value,
        expected=_TOP_FIELDS,
        label="Internal Model assembly rules",
    )

    if data["schema_version"] != INTERNAL_MODEL_ASSEMBLY_RULES_SCHEMA_VERSION:
        raise InternalModelValidationError(
            "Unsupported Internal Model assembly-rules schema_version."
        )

    rules_id = _upper_id(data["rules_id"], "rules_id")
    if rules_id != EXPECTED_INTERNAL_MODEL_ASSEMBLY_RULES_ID:
        raise InternalModelValidationError(
            "Unexpected Internal Model assembly rules_id."
        )

    _semver(data["rules_version"], "rules_version")
    if data["status"] != "active":
        raise InternalModelValidationError(
            "Internal Model assembly rules must be active."
        )

    _upper_id(data["framework_template_id"], "framework_template_id")
    _semver(
        data["framework_template_version"],
        "framework_template_version",
    )
    _upper_id(
        data["model_structure_profile_id"],
        "model_structure_profile_id",
    )
    _semver(
        data["model_structure_profile_version"],
        "model_structure_profile_version",
    )

    policy = _exact_object(
        data["policies"],
        expected=_POLICY_FIELDS,
        label="Internal Model assembly policies",
    )

    required_bools = {
        "materialize_complete_framework_hierarchy": True,
        "allow_empty_structure_nodes": True,
        "unreviewed_reclassification_allowed": False,
        "invent_engineering_hierarchy_allowed": False,
    }
    for field, expected in required_bools.items():
        if policy[field] is not expected:
            raise InternalModelValidationError(
                f"Assembly policy {field} must be {expected}."
            )

    required_values = {
        "element_membership_cardinality": "exactly_one",
        "candidate_framework_assignment_authority": "phase_h",
        "unknown_framework_assignment_behavior": "reject",
        "profile_mismatch_behavior": "reject",
        "structure_node_ordering": "template_order",
        "element_membership_ordering": "internal_model_element_id",
    }
    for field, expected in required_values.items():
        if policy[field] != expected:
            raise InternalModelValidationError(
                f"Assembly policy {field} must be {expected!r}."
            )

    return {
        "schema_version": data["schema_version"],
        "rules_id": rules_id,
        "rules_version": data["rules_version"],
        "status": data["status"],
        "framework_template_id": data["framework_template_id"],
        "framework_template_version": data["framework_template_version"],
        "model_structure_profile_id": data["model_structure_profile_id"],
        "model_structure_profile_version": data[
            "model_structure_profile_version"
        ],
        "policies": dict(policy),
    }


def calculate_internal_model_assembly_rules_fingerprint(
    value: dict[str, Any],
) -> str:
    normalized = validate_internal_model_assembly_rules(value)
    canonical = json.dumps(
        normalized,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def load_internal_model_assembly_rules_reference(
    path: Path | str = DEFAULT_INTERNAL_MODEL_ASSEMBLY_RULES_PATH,
) -> InternalModelAssemblyRulesReference:
    rules = load_internal_model_assembly_rules(path)
    return InternalModelAssemblyRulesReference(
        rules_id=rules["rules_id"],
        rules_version=rules["rules_version"],
        rules_fingerprint=(
            calculate_internal_model_assembly_rules_fingerprint(rules)
        ),
    )


def _exact_object(
    value: object,
    *,
    expected: frozenset[str],
    label: str,
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise InternalModelValidationError(
            f"{label} must be a JSON object."
        )
    actual = frozenset(value)
    if actual != expected:
        raise InternalModelValidationError(
            f"{label} has invalid fields; "
            f"missing={sorted(expected - actual)}, "
            f"unknown={sorted(actual - expected)}."
        )
    return value


def _upper_id(value: object, label: str) -> str:
    if (
        not isinstance(value, str)
        or _UPPER_ID_PATTERN.fullmatch(value) is None
    ):
        raise InternalModelValidationError(
            f"{label} must be an uppercase identifier."
        )
    return value


def _semver(value: object, label: str) -> str:
    if (
        not isinstance(value, str)
        or _SEMVER_PATTERN.fullmatch(value) is None
    ):
        raise InternalModelValidationError(
            f"{label} must be a semantic version."
        )
    return value


def _without_duplicate_keys(
    pairs: list[tuple[str, object]],
) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise InternalModelValidationError(
                f"Duplicate JSON key is not allowed: {key!r}."
            )
        result[key] = value
    return result
