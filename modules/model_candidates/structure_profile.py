"""Load and validate the Phase-H Model Structure and Comparability Profile."""

from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path
import re
from typing import Any

from modules.framework import (
    DEFAULT_FRAMEWORK_TEMPLATE_PATH,
    FrameworkTemplateError,
    load_framework_template,
    mapping_target_ids,
    validate_framework_template,
)

from .errors import ModelCandidateValidationError
from .types import (
    ModelElementDerivationRule,
    ModelRelationshipSemanticRule,
    ModelStructureAreaDefinition,
    ModelStructureProfile,
    ModelStructureProfileReference,
)


DEFAULT_MODEL_STRUCTURE_PROFILE_PATH = Path(
    "context/modeling/turing_model_structure_profile.json"
)
MODEL_STRUCTURE_PROFILE_SCHEMA_VERSION = "1.0.0"

RELATIONSHIP_PRIORITY_CRITERIA = (
    "evidence_directness",
    "semantic_fit",
    "endpoint_certainty",
    "structural_profile_preference",
    "structural_comparability_impact",
    "assumption_burden",
    "conformance",
)

_PROFILE_ID_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]*$")
_RULE_ID_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]*$")
_MODEL_AREA_PATTERN = re.compile(
    r"^[a-z0-9][a-z0-9._-]*$"
)
_SEMVER_PATTERN = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
_IDENTIFIER_PATTERN = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9._:-]*$"
)

_PROFILE_FIELDS = frozenset(
    {
        "schema_version",
        "profile_id",
        "profile_version",
        "name",
        "status",
        "framework_template_id",
        "framework_template_version",
        "model_areas",
        "element_derivation_rules",
        "relationship_semantics",
        "priority_criteria",
        "exception_policy",
    }
)
_AREA_FIELDS = frozenset(
    {
        "model_area_id",
        "framework_node_id",
        "permitted_element_types",
        "comparison_anchor_prefix",
    }
)
_ELEMENT_RULE_FIELDS = frozenset(
    {
        "rule_id",
        "model_area_id",
        "element_type",
        "classification_values",
        "framework_assignment_values",
        "information_type_values",
    }
)
_RELATIONSHIP_RULE_FIELDS = frozenset(
    {
        "semantic_intent",
        "relationship_family",
        "directionality",
        "canonical",
        "deviation_id",
    }
)
_EXCEPTION_POLICY_FIELDS = frozenset(
    {
        "noncanonical_relationship_requires_exception",
        "intentional_deviation_requires_rationale",
    }
)


def load_model_structure_profile(
    path: Path | str = DEFAULT_MODEL_STRUCTURE_PROFILE_PATH,
    *,
    framework_template: dict[str, Any] | None = None,
    framework_template_path: (
        Path | str
    ) = DEFAULT_FRAMEWORK_TEMPLATE_PATH,
) -> ModelStructureProfile:
    """Load one versioned structure profile bound to the RFLP template."""

    profile_path = Path(path)
    try:
        payload = profile_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ModelCandidateValidationError(
            f"Unable to read Model Structure Profile: {profile_path}."
        ) from exc

    template = framework_template
    if template is None:
        try:
            template = load_framework_template(
                Path(framework_template_path)
            )
        except FrameworkTemplateError as exc:
            raise ModelCandidateValidationError(
                "Unable to load bound Framework Template."
            ) from exc

    return model_structure_profile_from_json(
        payload,
        framework_template=template,
    )


def model_structure_profile_from_json(
    payload: object,
    *,
    framework_template: dict[str, Any],
) -> ModelStructureProfile:
    """Parse strict JSON text into an immutable validated profile."""

    if not isinstance(payload, str):
        raise ModelCandidateValidationError(
            "Model Structure Profile JSON must be a string."
        )
    try:
        data = json.loads(
            payload,
            object_pairs_hook=_without_duplicate_keys,
        )
    except ModelCandidateValidationError:
        raise
    except json.JSONDecodeError as exc:
        raise ModelCandidateValidationError(
            "Model Structure Profile is not valid JSON."
        ) from exc

    normalized = validate_model_structure_profile(
        data,
        framework_template=framework_template,
    )
    areas = tuple(
        ModelStructureAreaDefinition(
            model_area_id=item["model_area_id"],
            framework_node_id=item["framework_node_id"],
            permitted_element_types=tuple(
                item["permitted_element_types"]
            ),
            comparison_anchor_prefix=item[
                "comparison_anchor_prefix"
            ],
        )
        for item in normalized["model_areas"]
    )
    element_rules = tuple(
        ModelElementDerivationRule(
            rule_id=item["rule_id"],
            model_area_id=item["model_area_id"],
            element_type=item["element_type"],
            classification_values=tuple(
                item["classification_values"]
            ),
            framework_assignment_values=tuple(
                item["framework_assignment_values"]
            ),
            information_type_values=tuple(
                item["information_type_values"]
            ),
        )
        for item in normalized["element_derivation_rules"]
    )
    relationship_rules = tuple(
        ModelRelationshipSemanticRule(
            semantic_intent=item["semantic_intent"],
            relationship_family=item["relationship_family"],
            directionality=item["directionality"],
            canonical=item["canonical"],
            deviation_id=item["deviation_id"],
        )
        for item in normalized["relationship_semantics"]
    )
    policy = normalized["exception_policy"]
    profile = ModelStructureProfile(
        schema_version=normalized["schema_version"],
        profile_id=normalized["profile_id"],
        profile_version=normalized["profile_version"],
        name=normalized["name"],
        status=normalized["status"],
        framework_template_id=normalized[
            "framework_template_id"
        ],
        framework_template_version=normalized[
            "framework_template_version"
        ],
        model_areas=areas,
        element_derivation_rules=element_rules,
        relationship_semantics=relationship_rules,
        priority_criteria=tuple(normalized["priority_criteria"]),
        noncanonical_relationship_requires_exception=policy[
            "noncanonical_relationship_requires_exception"
        ],
        intentional_deviation_requires_rationale=policy[
            "intentional_deviation_requires_rationale"
        ],
        profile_fingerprint="0" * 64,
    )
    return replace(
        profile,
        profile_fingerprint=(
            calculate_model_structure_profile_fingerprint(profile)
        ),
    )


def validate_model_structure_profile(
    data: object,
    *,
    framework_template: dict[str, Any],
) -> dict[str, Any]:
    """Validate metadata, framework binding, mappings and vocabularies."""

    if not isinstance(data, dict):
        raise ModelCandidateValidationError(
            "Model Structure Profile must be a JSON object."
        )
    _exact_fields(data, _PROFILE_FIELDS, "Model Structure Profile")
    try:
        validate_framework_template(framework_template)
    except FrameworkTemplateError as exc:
        raise ModelCandidateValidationError(
            "Bound Framework Template is invalid."
        ) from exc

    if data["schema_version"] != MODEL_STRUCTURE_PROFILE_SCHEMA_VERSION:
        raise ModelCandidateValidationError(
            "Unsupported Model Structure Profile schema_version."
        )
    _semver(data["profile_version"], "profile_version")
    _uppercase_id(data["profile_id"], "profile_id")
    _text(data["name"], "name")
    if data["status"] not in {"draft", "active", "retired"}:
        raise ModelCandidateValidationError(
            "Model Structure Profile status is invalid."
        )
    if data["framework_template_id"] != framework_template["template_id"]:
        raise ModelCandidateValidationError(
            "Model Structure Profile framework_template_id does not "
            "match bound Framework Template."
        )
    if (
        data["framework_template_version"]
        != framework_template["template_version"]
    ):
        raise ModelCandidateValidationError(
            "Model Structure Profile framework_template_version does "
            "not match bound Framework Template."
        )

    mapping_targets = mapping_target_ids(framework_template)
    raw_areas = _list(data["model_areas"], "model_areas")
    if not raw_areas:
        raise ModelCandidateValidationError(
            "model_areas must not be empty."
        )
    areas = []
    seen_area_ids = set()
    seen_framework_nodes = set()
    for raw in raw_areas:
        item = _exact_object(
            raw,
            _AREA_FIELDS,
            "Model Structure Area",
        )
        area_id = _model_area_id(item["model_area_id"])
        if area_id in seen_area_ids:
            raise ModelCandidateValidationError(
                f"Duplicate model_area_id: {area_id}."
            )
        framework_node_id = _uppercase_id(
            item["framework_node_id"],
            "framework_node_id",
        )
        if framework_node_id not in mapping_targets:
            raise ModelCandidateValidationError(
                f"Unknown framework mapping target: {framework_node_id}."
            )
        if framework_node_id in seen_framework_nodes:
            raise ModelCandidateValidationError(
                f"Framework node used by multiple model areas: "
                f"{framework_node_id}."
            )
        permitted = _sorted_unique_identifiers(
            item["permitted_element_types"],
            "permitted_element_types",
        )
        if not permitted:
            raise ModelCandidateValidationError(
                "permitted_element_types must not be empty."
            )
        prefix = _identifier(
            item["comparison_anchor_prefix"],
            "comparison_anchor_prefix",
        )
        seen_area_ids.add(area_id)
        seen_framework_nodes.add(framework_node_id)
        areas.append(
            {
                "model_area_id": area_id,
                "framework_node_id": framework_node_id,
                "permitted_element_types": list(permitted),
                "comparison_anchor_prefix": prefix,
            }
        )

    areas.sort(key=lambda item: item["model_area_id"])
    area_by_id = {
        item["model_area_id"]: item for item in areas
    }

    raw_element_rules = _list(
        data["element_derivation_rules"],
        "element_derivation_rules",
    )
    if not raw_element_rules:
        raise ModelCandidateValidationError(
            "element_derivation_rules must not be empty."
        )
    element_rules = []
    rule_ids = set()
    for raw in raw_element_rules:
        item = _exact_object(
            raw,
            _ELEMENT_RULE_FIELDS,
            "Element Derivation Rule",
        )
        rule_id = _uppercase_id(item["rule_id"], "rule_id")
        if not _RULE_ID_PATTERN.fullmatch(rule_id):
            raise ModelCandidateValidationError(
                "Element rule_id has invalid syntax."
            )
        if rule_id in rule_ids:
            raise ModelCandidateValidationError(
                f"Duplicate Element rule_id: {rule_id}."
            )
        area_id = _model_area_id(item["model_area_id"])
        area = area_by_id.get(area_id)
        if area is None:
            raise ModelCandidateValidationError(
                f"Element rule references unknown model_area_id: "
                f"{area_id}."
            )
        element_type = _identifier(
            item["element_type"],
            "element_type",
        )
        if element_type not in area["permitted_element_types"]:
            raise ModelCandidateValidationError(
                f"Element type {element_type!r} is not permitted in "
                f"{area_id}."
            )
        classifications = _sorted_unique_text(
            item["classification_values"],
            "classification_values",
        )
        framework_values = _sorted_unique_text(
            item["framework_assignment_values"],
            "framework_assignment_values",
        )
        information_types = _sorted_unique_text(
            item["information_type_values"],
            "information_type_values",
        )
        if not (
            classifications
            or framework_values
            or information_types
        ):
            raise ModelCandidateValidationError(
                f"{rule_id} has no matching evidence values."
            )
        rule_ids.add(rule_id)
        element_rules.append(
            {
                "rule_id": rule_id,
                "model_area_id": area_id,
                "element_type": element_type,
                "classification_values": list(classifications),
                "framework_assignment_values": list(framework_values),
                "information_type_values": list(information_types),
            }
        )

    element_rules.sort(key=lambda item: item["rule_id"])

    raw_relationship_rules = _list(
        data["relationship_semantics"],
        "relationship_semantics",
    )
    if not raw_relationship_rules:
        raise ModelCandidateValidationError(
            "relationship_semantics must not be empty."
        )
    relationship_rules = []
    seen_intents = set()
    for raw in raw_relationship_rules:
        item = _exact_object(
            raw,
            _RELATIONSHIP_RULE_FIELDS,
            "Relationship Semantic Rule",
        )
        intent = _identifier(
            item["semantic_intent"],
            "semantic_intent",
        )
        if intent in seen_intents:
            raise ModelCandidateValidationError(
                f"Duplicate semantic_intent: {intent}."
            )
        family = _identifier(
            item["relationship_family"],
            "relationship_family",
        )
        directionality = _identifier(
            item["directionality"],
            "directionality",
        )
        if directionality not in {
            "source_to_target",
            "bidirectional",
            "undirected",
        }:
            raise ModelCandidateValidationError(
                f"Unsupported directionality: {directionality}."
            )
        canonical = item["canonical"]
        if not isinstance(canonical, bool):
            raise ModelCandidateValidationError(
                "relationship canonical must be boolean."
            )
        deviation_id = item["deviation_id"]
        if canonical:
            if deviation_id is not None:
                raise ModelCandidateValidationError(
                    "Canonical relationship semantics must not define "
                    "deviation_id."
                )
        else:
            deviation_id = _uppercase_id(
                deviation_id,
                "deviation_id",
            )
        seen_intents.add(intent)
        relationship_rules.append(
            {
                "semantic_intent": intent,
                "relationship_family": family,
                "directionality": directionality,
                "canonical": canonical,
                "deviation_id": deviation_id,
            }
        )

    relationship_rules.sort(
        key=lambda item: item["semantic_intent"]
    )

    priority = tuple(
        _list(data["priority_criteria"], "priority_criteria")
    )
    if priority != RELATIONSHIP_PRIORITY_CRITERIA:
        raise ModelCandidateValidationError(
            "priority_criteria must match the ADR-018 conceptual "
            "priority order."
        )

    policy = _exact_object(
        data["exception_policy"],
        _EXCEPTION_POLICY_FIELDS,
        "exception_policy",
    )
    for field in sorted(_EXCEPTION_POLICY_FIELDS):
        if not isinstance(policy[field], bool):
            raise ModelCandidateValidationError(
                f"exception_policy.{field} must be boolean."
            )

    return {
        "schema_version": data["schema_version"],
        "profile_id": data["profile_id"],
        "profile_version": data["profile_version"],
        "name": data["name"].strip(),
        "status": data["status"],
        "framework_template_id": data["framework_template_id"],
        "framework_template_version": data[
            "framework_template_version"
        ],
        "model_areas": areas,
        "element_derivation_rules": element_rules,
        "relationship_semantics": relationship_rules,
        "priority_criteria": list(priority),
        "exception_policy": {
            field: policy[field]
            for field in sorted(_EXCEPTION_POLICY_FIELDS)
        },
    }


def model_structure_profile_to_dict(
    profile: ModelStructureProfile,
) -> dict[str, Any]:
    """Return canonical JSON-compatible profile content without fingerprint."""

    if not isinstance(profile, ModelStructureProfile):
        raise ModelCandidateValidationError(
            "profile must be a ModelStructureProfile."
        )
    return {
        "schema_version": profile.schema_version,
        "profile_id": profile.profile_id,
        "profile_version": profile.profile_version,
        "name": profile.name,
        "status": profile.status,
        "framework_template_id": profile.framework_template_id,
        "framework_template_version": (
            profile.framework_template_version
        ),
        "model_areas": [
            {
                "model_area_id": item.model_area_id,
                "framework_node_id": item.framework_node_id,
                "permitted_element_types": list(
                    item.permitted_element_types
                ),
                "comparison_anchor_prefix": (
                    item.comparison_anchor_prefix
                ),
            }
            for item in profile.model_areas
        ],
        "element_derivation_rules": [
            {
                "rule_id": item.rule_id,
                "model_area_id": item.model_area_id,
                "element_type": item.element_type,
                "classification_values": list(
                    item.classification_values
                ),
                "framework_assignment_values": list(
                    item.framework_assignment_values
                ),
                "information_type_values": list(
                    item.information_type_values
                ),
            }
            for item in profile.element_derivation_rules
        ],
        "relationship_semantics": [
            {
                "semantic_intent": item.semantic_intent,
                "relationship_family": item.relationship_family,
                "directionality": item.directionality,
                "canonical": item.canonical,
                "deviation_id": item.deviation_id,
            }
            for item in profile.relationship_semantics
        ],
        "priority_criteria": list(profile.priority_criteria),
        "exception_policy": {
            "intentional_deviation_requires_rationale": (
                profile.intentional_deviation_requires_rationale
            ),
            "noncanonical_relationship_requires_exception": (
                profile.noncanonical_relationship_requires_exception
            ),
        },
    }


def calculate_model_structure_profile_fingerprint(
    profile: ModelStructureProfile,
) -> str:
    """Calculate the canonical profile fingerprint."""

    payload = model_structure_profile_to_dict(profile)
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(
        canonical.encode("utf-8")
    ).hexdigest()


def model_structure_profile_reference(
    profile: ModelStructureProfile,
) -> ModelStructureProfileReference:
    """Return the exact immutable reference bound into Candidate Sets."""

    expected = calculate_model_structure_profile_fingerprint(profile)
    if profile.profile_fingerprint != expected:
        raise ModelCandidateValidationError(
            "Model Structure Profile fingerprint does not match content."
        )
    return ModelStructureProfileReference(
        profile_id=profile.profile_id,
        profile_version=profile.profile_version,
        profile_fingerprint=profile.profile_fingerprint,
    )


def _without_duplicate_keys(
    pairs: list[tuple[str, object]],
) -> dict[str, object]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ModelCandidateValidationError(
                f"Duplicate JSON key is not allowed: {key!r}."
            )
        result[key] = value
    return result


def _exact_fields(
    value: dict[str, Any],
    expected: frozenset[str],
    label: str,
) -> None:
    actual = frozenset(value)
    if actual != expected:
        raise ModelCandidateValidationError(
            f"{label} has invalid fields; "
            f"missing={sorted(expected - actual)}, "
            f"unknown={sorted(actual - expected)}."
        )


def _exact_object(
    value: object,
    expected: frozenset[str],
    label: str,
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ModelCandidateValidationError(
            f"{label} must be a JSON object."
        )
    _exact_fields(value, expected, label)
    return value


def _list(value: object, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise ModelCandidateValidationError(
            f"{label} must be a JSON array."
        )
    return value


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ModelCandidateValidationError(
            f"{label} must be a non-empty string."
        )
    if value != value.strip():
        raise ModelCandidateValidationError(
            f"{label} must not contain surrounding whitespace."
        )
    return value


def _identifier(value: object, label: str) -> str:
    selected = _text(value, label)
    if _IDENTIFIER_PATTERN.fullmatch(selected) is None:
        raise ModelCandidateValidationError(
            f"{label} has invalid identifier syntax."
        )
    return selected


def _uppercase_id(value: object, label: str) -> str:
    selected = _text(value, label)
    if _PROFILE_ID_PATTERN.fullmatch(selected) is None:
        raise ModelCandidateValidationError(
            f"{label} must be an uppercase identifier."
        )
    return selected


def _model_area_id(value: object) -> str:
    selected = _text(value, "model_area_id")
    if _MODEL_AREA_PATTERN.fullmatch(selected) is None:
        raise ModelCandidateValidationError(
            "model_area_id has invalid syntax."
        )
    return selected


def _semver(value: object, label: str) -> str:
    selected = _text(value, label)
    if _SEMVER_PATTERN.fullmatch(selected) is None:
        raise ModelCandidateValidationError(
            f"{label} must be a semantic version."
        )
    return selected


def _sorted_unique_text(
    value: object,
    label: str,
) -> tuple[str, ...]:
    items = tuple(_text(item, label) for item in _list(value, label))
    if items != tuple(sorted(items)):
        raise ModelCandidateValidationError(
            f"{label} must use deterministic sorted order."
        )
    if len(items) != len(set(items)):
        raise ModelCandidateValidationError(
            f"{label} must contain unique values."
        )
    return items


def _sorted_unique_identifiers(
    value: object,
    label: str,
) -> tuple[str, ...]:
    items = tuple(
        _identifier(item, label) for item in _list(value, label)
    )
    if items != tuple(sorted(items)):
        raise ModelCandidateValidationError(
            f"{label} must use deterministic sorted order."
        )
    if len(items) != len(set(items)):
        raise ModelCandidateValidationError(
            f"{label} must contain unique values."
        )
    return items
