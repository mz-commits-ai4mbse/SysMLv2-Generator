"""Load, validate and serialize Preliminary Support Profiles."""

from __future__ import annotations

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

from .errors import CoverageProfileError
from .types import (
    SUPPORT_PROFILE_STATUSES,
    SUPPORT_TARGET_TYPES,
    PreliminarySupportProfile,
    PreliminarySupportTarget,
)


DEFAULT_PRELIMINARY_SUPPORT_PROFILE_PATH = Path(
    "context/frameworks/turing_preliminary_support_profile.json"
)
PRELIMINARY_SUPPORT_PROFILE_SCHEMA_VERSION = "1.0.0"

_SEMANTIC_VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")
_PROFILE_ID_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]*$")
_SUPPORT_TARGET_ID_PATTERN = re.compile(r"^SUPPORT_[A-Z0-9_]+$")

_PROFILE_FIELDS = frozenset(
    {
        "schema_version",
        "profile_id",
        "profile_version",
        "name",
        "status",
        "framework_template_id",
        "framework_template_version",
        "support_targets",
    }
)
_TARGET_FIELDS = frozenset(
    {
        "support_target_id",
        "name",
        "support_target_type",
        "order",
        "required_framework_node_ids",
        "required_support_target_ids",
    }
)


def load_preliminary_support_profile(
    path: Path | str = DEFAULT_PRELIMINARY_SUPPORT_PROFILE_PATH,
    *,
    framework_template: dict[str, Any] | None = None,
    framework_template_path: Path | str = DEFAULT_FRAMEWORK_TEMPLATE_PATH,
) -> PreliminarySupportProfile:
    """Load and validate one versioned Preliminary Support Profile."""

    profile_path = Path(path)
    try:
        payload = profile_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise CoverageProfileError(
            f"Unable to read Preliminary Support Profile: {profile_path}."
        ) from exc

    template = framework_template
    if template is None:
        try:
            template = load_framework_template(Path(framework_template_path))
        except FrameworkTemplateError as exc:
            raise CoverageProfileError(
                "Unable to load the bound Framework Template."
            ) from exc

    return preliminary_support_profile_from_json(
        payload,
        framework_template=template,
    )


def preliminary_support_profile_from_json(
    payload: str,
    *,
    framework_template: dict[str, Any],
) -> PreliminarySupportProfile:
    """Parse JSON text and return one validated immutable profile."""

    if not isinstance(payload, str):
        raise CoverageProfileError("Profile JSON payload must be a string.")
    try:
        data = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise CoverageProfileError(
            f"Invalid Preliminary Support Profile JSON: {exc.msg}."
        ) from exc
    return parse_preliminary_support_profile(
        data,
        framework_template=framework_template,
    )


def parse_preliminary_support_profile(
    data: Any,
    *,
    framework_template: dict[str, Any],
) -> PreliminarySupportProfile:
    """Parse and validate a mapping into immutable profile types."""

    validated = validate_preliminary_support_profile(
        data,
        framework_template=framework_template,
    )
    targets = tuple(
        PreliminarySupportTarget(
            support_target_id=item["support_target_id"],
            name=item["name"],
            support_target_type=item["support_target_type"],
            order=item["order"],
            required_framework_node_ids=tuple(
                item["required_framework_node_ids"]
            ),
            required_support_target_ids=tuple(
                item["required_support_target_ids"]
            ),
        )
        for item in validated["support_targets"]
    )
    canonical_without_fingerprint = {
        key: validated[key]
        for key in (
            "schema_version",
            "profile_id",
            "profile_version",
            "name",
            "status",
            "framework_template_id",
            "framework_template_version",
            "support_targets",
        )
    }
    return PreliminarySupportProfile(
        schema_version=validated["schema_version"],
        profile_id=validated["profile_id"],
        profile_version=validated["profile_version"],
        name=validated["name"],
        status=validated["status"],
        framework_template_id=validated["framework_template_id"],
        framework_template_version=validated["framework_template_version"],
        support_targets=targets,
        profile_fingerprint=_fingerprint(canonical_without_fingerprint),
    )


def validate_preliminary_support_profile(
    data: Any,
    *,
    framework_template: dict[str, Any],
) -> dict[str, Any]:
    """Validate profile metadata, target references and dependency graph."""

    if not isinstance(data, dict):
        raise CoverageProfileError(
            "Preliminary Support Profile must be a JSON object."
        )
    _require_exact_fields(data, _PROFILE_FIELDS, "support profile")
    _validate_framework_template(framework_template)
    _validate_metadata(data)
    _validate_template_binding(data, framework_template)

    targets = data["support_targets"]
    if not isinstance(targets, list) or not targets:
        raise CoverageProfileError(
            "support_targets must be a non-empty list."
        )

    valid_mapping_targets = mapping_target_ids(framework_template)

    raw_target_ids = [
        target.get("support_target_id")
        for target in targets
        if isinstance(target, dict)
    ]
    duplicate_raw_ids = {
        target_id
        for target_id in raw_target_ids
        if raw_target_ids.count(target_id) > 1
    }
    if duplicate_raw_ids:
        raise CoverageProfileError(
            "Duplicate support_target_id: "
            + ", ".join(sorted(str(item) for item in duplicate_raw_ids))
            + "."
        )

    target_ids: set[str] = set()
    orders: set[int] = set()
    normalized_targets: list[dict[str, Any]] = []

    for index, target in enumerate(targets):
        label = f"support target at index {index}"
        if not isinstance(target, dict):
            raise CoverageProfileError(f"{label} must be an object.")
        _require_exact_fields(target, _TARGET_FIELDS, label)
        normalized = _validate_target(
            target,
            label=label,
            valid_mapping_targets=valid_mapping_targets,
        )
        target_id = normalized["support_target_id"]
        if target_id in target_ids:
            raise CoverageProfileError(
                f"Duplicate support_target_id: {target_id}."
            )
        if normalized["order"] in orders:
            raise CoverageProfileError(
                f"Duplicate support target order: {normalized['order']}."
            )
        target_ids.add(target_id)
        orders.add(normalized["order"])
        normalized_targets.append(normalized)

    normalized_targets.sort(key=lambda item: item["order"])
    if [item["order"] for item in normalized_targets] != list(
        range(1, len(normalized_targets) + 1)
    ):
        raise CoverageProfileError(
            "Support target order values must be contiguous from 1."
        )

    _validate_dependencies(normalized_targets)

    return {
        "schema_version": data["schema_version"],
        "profile_id": data["profile_id"],
        "profile_version": data["profile_version"],
        "name": data["name"].strip(),
        "status": data["status"],
        "framework_template_id": data["framework_template_id"],
        "framework_template_version": data["framework_template_version"],
        "support_targets": normalized_targets,
    }


def validate_preliminary_support_profile_instance(
    profile: PreliminarySupportProfile,
    *,
    framework_template: dict[str, Any],
) -> PreliminarySupportProfile:
    """Revalidate one immutable profile and its stored fingerprint."""

    if not isinstance(profile, PreliminarySupportProfile):
        raise CoverageProfileError(
            "profile must be a PreliminarySupportProfile."
        )
    data = preliminary_support_profile_to_dict(profile)
    parsed = parse_preliminary_support_profile(
        data,
        framework_template=framework_template,
    )
    if parsed != profile:
        raise CoverageProfileError(
            "Preliminary Support Profile fingerprint or content is invalid."
        )
    return profile


def preliminary_support_profile_to_dict(
    profile: PreliminarySupportProfile,
) -> dict[str, Any]:
    """Return the canonical JSON-compatible representation without fingerprint."""

    if not isinstance(profile, PreliminarySupportProfile):
        raise CoverageProfileError(
            "profile must be a PreliminarySupportProfile."
        )
    return {
        "schema_version": profile.schema_version,
        "profile_id": profile.profile_id,
        "profile_version": profile.profile_version,
        "name": profile.name,
        "status": profile.status,
        "framework_template_id": profile.framework_template_id,
        "framework_template_version": profile.framework_template_version,
        "support_targets": [
            {
                "support_target_id": target.support_target_id,
                "name": target.name,
                "support_target_type": target.support_target_type,
                "order": target.order,
                "required_framework_node_ids": list(
                    target.required_framework_node_ids
                ),
                "required_support_target_ids": list(
                    target.required_support_target_ids
                ),
            }
            for target in profile.support_targets
        ],
    }


def preliminary_support_profile_to_json(
    profile: PreliminarySupportProfile,
) -> str:
    """Serialize one profile using deterministic formatting and newline at EOF."""

    return json.dumps(
        preliminary_support_profile_to_dict(profile),
        ensure_ascii=False,
        indent=2,
        sort_keys=False,
    ) + "\n"


def calculate_preliminary_support_profile_fingerprint(
    profile: PreliminarySupportProfile,
) -> str:
    """Calculate the canonical profile-content fingerprint."""

    return _fingerprint(preliminary_support_profile_to_dict(profile))


def support_target_by_id(
    profile: PreliminarySupportProfile,
    support_target_id: str,
) -> PreliminarySupportTarget:
    """Return one target by stable identifier or raise a profile error."""

    if not isinstance(profile, PreliminarySupportProfile):
        raise CoverageProfileError(
            "profile must be a PreliminarySupportProfile."
        )
    if not isinstance(support_target_id, str):
        raise CoverageProfileError("support_target_id must be a string.")
    for target in profile.support_targets:
        if target.support_target_id == support_target_id:
            return target
    raise CoverageProfileError(
        f"Unknown support_target_id: {support_target_id!r}."
    )


def _validate_framework_template(template: Any) -> None:
    try:
        validate_framework_template(template)
    except FrameworkTemplateError as exc:
        raise CoverageProfileError(
            "The bound Framework Template is invalid."
        ) from exc


def _validate_metadata(data: dict[str, Any]) -> None:
    for field_name in ("schema_version", "profile_version"):
        value = data[field_name]
        if not isinstance(value, str) or not _SEMANTIC_VERSION_PATTERN.fullmatch(value):
            raise CoverageProfileError(
                f"{field_name} must use MAJOR.MINOR.PATCH semantic versioning."
            )
    if data["schema_version"] != PRELIMINARY_SUPPORT_PROFILE_SCHEMA_VERSION:
        raise CoverageProfileError(
            "Unsupported Preliminary Support Profile schema_version."
        )
    profile_id = data["profile_id"]
    if not isinstance(profile_id, str) or not _PROFILE_ID_PATTERN.fullmatch(profile_id):
        raise CoverageProfileError(
            "profile_id must be a stable uppercase identifier."
        )
    name = data["name"]
    if not isinstance(name, str) or not name.strip():
        raise CoverageProfileError("Profile name must be a non-empty string.")
    if data["status"] not in SUPPORT_PROFILE_STATUSES:
        raise CoverageProfileError(
            "status must be one of: active, draft, retired."
        )


def _validate_template_binding(
    data: dict[str, Any],
    framework_template: dict[str, Any],
) -> None:
    if data["framework_template_id"] != framework_template["template_id"]:
        raise CoverageProfileError(
            "Support Profile framework_template_id does not match the Framework Template."
        )
    if data["framework_template_version"] != framework_template["template_version"]:
        raise CoverageProfileError(
            "Support Profile framework_template_version does not match the Framework Template."
        )


def _validate_target(
    target: dict[str, Any],
    *,
    label: str,
    valid_mapping_targets: set[str],
) -> dict[str, Any]:
    target_id = target["support_target_id"]
    if not isinstance(target_id, str) or not _SUPPORT_TARGET_ID_PATTERN.fullmatch(target_id):
        raise CoverageProfileError(
            f"{label} has an invalid support_target_id."
        )
    name = target["name"]
    if not isinstance(name, str) or not name.strip():
        raise CoverageProfileError(f"{target_id} name must be non-empty.")
    target_type = target["support_target_type"]
    if target_type not in SUPPORT_TARGET_TYPES:
        raise CoverageProfileError(
            f"{target_id} has unsupported support_target_type {target_type!r}."
        )
    order = target["order"]
    if isinstance(order, bool) or not isinstance(order, int) or order < 1:
        raise CoverageProfileError(
            f"{target_id} order must be a positive integer."
        )
    node_ids = _validate_identifier_list(
        target["required_framework_node_ids"],
        field_name=f"{target_id}.required_framework_node_ids",
        allow_empty=False,
    )
    unknown_nodes = set(node_ids) - valid_mapping_targets
    if unknown_nodes:
        raise CoverageProfileError(
            f"{target_id} references unknown or non-mapping framework nodes: "
            + ", ".join(sorted(unknown_nodes))
            + "."
        )
    dependency_ids = _validate_identifier_list(
        target["required_support_target_ids"],
        field_name=f"{target_id}.required_support_target_ids",
        allow_empty=True,
        pattern=_SUPPORT_TARGET_ID_PATTERN,
    )
    if target_id in dependency_ids:
        raise CoverageProfileError(
            f"{target_id} cannot depend on itself."
        )
    return {
        "support_target_id": target_id,
        "name": name.strip(),
        "support_target_type": target_type,
        "order": order,
        "required_framework_node_ids": list(node_ids),
        "required_support_target_ids": list(dependency_ids),
    }


def _validate_dependencies(targets: list[dict[str, Any]]) -> None:
    by_id = {item["support_target_id"]: item for item in targets}
    for item in targets:
        target_id = item["support_target_id"]
        for dependency_id in item["required_support_target_ids"]:
            dependency = by_id.get(dependency_id)
            if dependency is None:
                raise CoverageProfileError(
                    f"{target_id} references unknown support target {dependency_id}."
                )
            if dependency["order"] >= item["order"]:
                raise CoverageProfileError(
                    f"{target_id} dependencies must reference earlier support targets."
                )

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(target_id: str) -> None:
        if target_id in visiting:
            raise CoverageProfileError("Support target dependency cycle detected.")
        if target_id in visited:
            return
        visiting.add(target_id)
        for dependency_id in by_id[target_id]["required_support_target_ids"]:
            visit(dependency_id)
        visiting.remove(target_id)
        visited.add(target_id)

    for target_id in by_id:
        visit(target_id)


def _validate_identifier_list(
    value: Any,
    *,
    field_name: str,
    allow_empty: bool,
    pattern: re.Pattern[str] | None = None,
) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise CoverageProfileError(f"{field_name} must be a list.")
    if not allow_empty and not value:
        raise CoverageProfileError(f"{field_name} must not be empty.")
    if any(not isinstance(item, str) or not item for item in value):
        raise CoverageProfileError(
            f"{field_name} must contain non-empty string identifiers."
        )
    if len(value) != len(set(value)):
        raise CoverageProfileError(f"{field_name} contains duplicate identifiers.")
    if pattern is not None:
        invalid = [item for item in value if not pattern.fullmatch(item)]
        if invalid:
            raise CoverageProfileError(
                f"{field_name} contains invalid identifiers: "
                + ", ".join(sorted(invalid))
                + "."
            )
    return tuple(value)


def _require_exact_fields(
    data: dict[str, Any],
    expected: frozenset[str],
    label: str,
) -> None:
    missing = expected - data.keys()
    extra = data.keys() - expected
    if missing:
        raise CoverageProfileError(
            f"{label} is missing required fields: "
            + ", ".join(sorted(missing))
            + "."
        )
    if extra:
        raise CoverageProfileError(
            f"{label} contains unsupported fields: "
            + ", ".join(sorted(extra))
            + "."
        )


def _fingerprint(data: dict[str, Any]) -> str:
    canonical = json.dumps(
        data,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()