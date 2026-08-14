"""Load and validate the versioned Phase-K SysML v2 Validation Profile."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .errors import SysMLValidationProfileError
from .fingerprints import calculate_json_fingerprint
from .types import (
    PUBLICATION_GATES,
    VALIDATION_FINDING_CATEGORIES,
    VALIDATION_SEVERITIES,
    VALIDATION_STATUSES,
    SysMLValidationProfileReference,
)


DEFAULT_VALIDATION_PROFILE_PATH = Path(
    "context/sysml/turing_sysml_v2_validation_profile.json"
)
VALIDATION_PROFILE_SCHEMA_VERSION = "1.0.0"
EXPECTED_VALIDATION_PROFILE_ID = "TURING_SYSML_V2_VALIDATION"
EXPECTED_VALIDATION_PROFILE_VERSION = "1.0.0"
EXPECTED_EXTERNAL_VALIDATOR_ID = "SYSIDE_CLI"
EXPECTED_EXTERNAL_TOOL_NAME = "SYSIDE Modeler CLI"
EXPECTED_EXTERNAL_COMMAND_CONTRACT_ID = "SYSIDE_CHECK_NONMUTATING_V1"

_SEMVER_PATTERN = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
_UPPER_ID_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]*$")
_LOWER_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")

_TOP_FIELDS = frozenset(
    {
        "schema_version",
        "profile_id",
        "profile_version",
        "status",
        "purpose",
        "required_internal_validators",
        "external_validator",
        "severity_policy",
        "publication_policy",
        "diagnostic_normalization",
        "fingerprint_policy",
    }
)
_INTERNAL_VALIDATOR_FIELDS = frozenset(
    {"validator_id", "category", "required"}
)
_EXTERNAL_VALIDATOR_FIELDS = frozenset(
    {
        "validator_id",
        "tool_name",
        "required",
        "command_contract_id",
        "unavailable_validation_status",
        "unavailable_publication_gate",
    }
)
_SEVERITY_POLICY_FIELDS = frozenset(
    {
        "allowed_severities",
        "default_blocking_by_severity",
        "external_warning_blocking",
    }
)
_PUBLICATION_POLICY_FIELDS = frozenset(
    {
        "pass_validation_status",
        "pass_publication_gate",
        "blocking_finding_gate",
        "incomplete_validation_status",
        "incomplete_publication_gate",
    }
)
_DIAGNOSTIC_NORMALIZATION_FIELDS = frozenset(
    {
        "strip_ansi",
        "path_mode",
        "discard_fields",
        "canonical_finding_order",
    }
)
_FINGERPRINT_POLICY_FIELDS = frozenset(
    {
        "algorithm",
        "encoding",
        "canonical_json",
        "validation_input_components",
        "validation_result_excluded_fields",
    }
)

_EXPECTED_INTERNAL_VALIDATORS = (
    ("artifact_set_integrity", "artifact_integrity"),
    ("generation_context", "validation_context"),
    ("target_notation", "target_notation"),
    ("artifact_structure", "artifact_structure"),
    ("traceability", "traceability"),
    ("model_structure_comparability", "validation_context"),
    ("relationship_consistency", "relationship_consistency"),
)
_EXPECTED_DISCARD_FIELDS = (
    "wall_clock_timestamp",
    "temporary_workspace_path",
    "execution_duration",
    "ansi_formatting",
    "machine_absolute_path",
)
_EXPECTED_FINDING_ORDER = (
    "blocking_desc",
    "category",
    "generated_unit_id",
    "start_line",
    "start_column",
    "code",
    "message",
)
_EXPECTED_VALIDATION_INPUT_COMPONENTS = (
    "source_artifact_set_fingerprint",
    "validation_profile_reference",
    "external_validator_identity",
    "external_validator_configuration_fingerprint",
    "command_contract_id",
)


def load_validation_profile(
    path: Path | str = DEFAULT_VALIDATION_PROFILE_PATH,
) -> dict[str, Any]:
    """Load and strictly validate the pinned Phase-K Validation Profile."""

    return validate_validation_profile(_load_json_without_duplicate_keys(path))


def validate_validation_profile(value: object) -> dict[str, Any]:
    """Validate the complete Validation Profile contract without coercion."""

    data = _exact_object(
        value,
        expected=_TOP_FIELDS,
        label="SysML Validation Profile",
    )
    if data["schema_version"] != VALIDATION_PROFILE_SCHEMA_VERSION:
        raise SysMLValidationProfileError(
            "Unsupported SysML Validation Profile schema_version."
        )
    if _require_upper_id(data["profile_id"], "profile_id") != (
        EXPECTED_VALIDATION_PROFILE_ID
    ):
        raise SysMLValidationProfileError(
            "Unexpected SysML Validation Profile profile_id."
        )
    if _require_semver(data["profile_version"], "profile_version") != (
        EXPECTED_VALIDATION_PROFILE_VERSION
    ):
        raise SysMLValidationProfileError(
            "Unexpected SysML Validation Profile profile_version."
        )
    if data["status"] != "active":
        raise SysMLValidationProfileError(
            "SysML Validation Profile must be active."
        )
    _require_nonempty_string(data["purpose"], "purpose")

    normalized_internal = _validate_internal_validators(
        data["required_internal_validators"]
    )
    normalized_external = _validate_external_validator(data["external_validator"])
    normalized_severity = _validate_severity_policy(data["severity_policy"])
    normalized_publication = _validate_publication_policy(
        data["publication_policy"]
    )
    normalized_diagnostics = _validate_diagnostic_normalization(
        data["diagnostic_normalization"]
    )
    normalized_fingerprint = _validate_fingerprint_policy(
        data["fingerprint_policy"]
    )

    normalized = dict(data)
    normalized["required_internal_validators"] = normalized_internal
    normalized["external_validator"] = normalized_external
    normalized["severity_policy"] = normalized_severity
    normalized["publication_policy"] = normalized_publication
    normalized["diagnostic_normalization"] = normalized_diagnostics
    normalized["fingerprint_policy"] = normalized_fingerprint
    return normalized


def calculate_validation_profile_fingerprint(profile: object) -> str:
    """Return the canonical fingerprint of one validated Validation Profile."""

    return calculate_json_fingerprint(validate_validation_profile(profile))


def load_validation_profile_reference(
    path: Path | str = DEFAULT_VALIDATION_PROFILE_PATH,
) -> SysMLValidationProfileReference:
    """Load the pinned profile and return its immutable identity reference."""

    profile = load_validation_profile(path)
    return SysMLValidationProfileReference(
        profile_id=profile["profile_id"],
        profile_version=profile["profile_version"],
        profile_fingerprint=calculate_json_fingerprint(profile),
    )


def _validate_internal_validators(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list) or not value:
        raise SysMLValidationProfileError(
            "required_internal_validators must be a non-empty list."
        )

    normalized: list[dict[str, Any]] = []
    actual_pairs: list[tuple[str, str]] = []
    seen_ids: set[str] = set()
    for raw in value:
        item = _exact_object(
            raw,
            expected=_INTERNAL_VALIDATOR_FIELDS,
            label="required internal validator",
        )
        validator_id = _require_lower_id(item["validator_id"], "validator_id")
        category = _require_enum(
            item["category"],
            allowed=VALIDATION_FINDING_CATEGORIES,
            label="internal validator category",
        )
        if item["required"] is not True:
            raise SysMLValidationProfileError(
                f"Required internal validator {validator_id!r} must set required=true."
            )
        if validator_id in seen_ids:
            raise SysMLValidationProfileError(
                f"Duplicate internal validator_id: {validator_id}."
            )
        seen_ids.add(validator_id)
        actual_pairs.append((validator_id, category))
        normalized.append(dict(item))

    if tuple(actual_pairs) != _EXPECTED_INTERNAL_VALIDATORS:
        raise SysMLValidationProfileError(
            "required_internal_validators must match the Phase-K 1.0.0 contract "
            "in canonical order."
        )
    return normalized


def _validate_external_validator(value: object) -> dict[str, Any]:
    data = _exact_object(
        value,
        expected=_EXTERNAL_VALIDATOR_FIELDS,
        label="external_validator",
    )
    if _require_upper_id(data["validator_id"], "external validator_id") != (
        EXPECTED_EXTERNAL_VALIDATOR_ID
    ):
        raise SysMLValidationProfileError("Unexpected external validator_id.")
    if _require_nonempty_string(data["tool_name"], "external tool_name") != (
        EXPECTED_EXTERNAL_TOOL_NAME
    ):
        raise SysMLValidationProfileError("Unexpected external tool_name.")
    if data["required"] is not True:
        raise SysMLValidationProfileError(
            "SYSIDE external validation must be required."
        )
    if _require_upper_id(
        data["command_contract_id"],
        "command_contract_id",
    ) != EXPECTED_EXTERNAL_COMMAND_CONTRACT_ID:
        raise SysMLValidationProfileError(
            "Unexpected external command_contract_id."
        )
    if data["unavailable_validation_status"] != "incomplete":
        raise SysMLValidationProfileError(
            "Unavailable external validation must produce status 'incomplete'."
        )
    if data["unavailable_publication_gate"] != "blocked":
        raise SysMLValidationProfileError(
            "Unavailable external validation must block publication."
        )
    return dict(data)


def _validate_severity_policy(value: object) -> dict[str, Any]:
    data = _exact_object(
        value,
        expected=_SEVERITY_POLICY_FIELDS,
        label="severity_policy",
    )
    _require_exact_string_list(
        data["allowed_severities"],
        expected=VALIDATION_SEVERITIES,
        label="allowed_severities",
    )
    blocking = _exact_object(
        data["default_blocking_by_severity"],
        expected=frozenset(VALIDATION_SEVERITIES),
        label="default_blocking_by_severity",
    )
    expected_blocking = {"info": False, "warning": False, "error": True}
    if blocking != expected_blocking:
        raise SysMLValidationProfileError(
            "default_blocking_by_severity must keep info/warning nonblocking "
            "and error blocking."
        )
    if data["external_warning_blocking"] is not False:
        raise SysMLValidationProfileError(
            "external_warning_blocking must be false for Validation Profile 1.0.0."
        )
    normalized = dict(data)
    normalized["default_blocking_by_severity"] = dict(blocking)
    return normalized


def _validate_publication_policy(value: object) -> dict[str, Any]:
    data = _exact_object(
        value,
        expected=_PUBLICATION_POLICY_FIELDS,
        label="publication_policy",
    )
    _require_enum(
        data["pass_validation_status"],
        allowed=VALIDATION_STATUSES,
        label="pass_validation_status",
    )
    _require_enum(
        data["pass_publication_gate"],
        allowed=PUBLICATION_GATES,
        label="pass_publication_gate",
    )
    _require_enum(
        data["blocking_finding_gate"],
        allowed=PUBLICATION_GATES,
        label="blocking_finding_gate",
    )
    _require_enum(
        data["incomplete_validation_status"],
        allowed=VALIDATION_STATUSES,
        label="incomplete_validation_status",
    )
    _require_enum(
        data["incomplete_publication_gate"],
        allowed=PUBLICATION_GATES,
        label="incomplete_publication_gate",
    )
    expected = {
        "pass_validation_status": "valid",
        "pass_publication_gate": "passed",
        "blocking_finding_gate": "blocked",
        "incomplete_validation_status": "incomplete",
        "incomplete_publication_gate": "blocked",
    }
    if data != expected:
        raise SysMLValidationProfileError(
            "publication_policy does not match the accepted fail-closed K→L gate."
        )
    return dict(data)


def _validate_diagnostic_normalization(value: object) -> dict[str, Any]:
    data = _exact_object(
        value,
        expected=_DIAGNOSTIC_NORMALIZATION_FIELDS,
        label="diagnostic_normalization",
    )
    if data["strip_ansi"] is not True:
        raise SysMLValidationProfileError("strip_ansi must be true.")
    if data["path_mode"] != "generated_unit_relative":
        raise SysMLValidationProfileError(
            "path_mode must be 'generated_unit_relative'."
        )
    _require_exact_string_list(
        data["discard_fields"],
        expected=_EXPECTED_DISCARD_FIELDS,
        label="discard_fields",
    )
    _require_exact_string_list(
        data["canonical_finding_order"],
        expected=_EXPECTED_FINDING_ORDER,
        label="canonical_finding_order",
    )
    return dict(data)


def _validate_fingerprint_policy(value: object) -> dict[str, Any]:
    data = _exact_object(
        value,
        expected=_FINGERPRINT_POLICY_FIELDS,
        label="fingerprint_policy",
    )
    if data["algorithm"] != "sha256":
        raise SysMLValidationProfileError("fingerprint algorithm must be sha256.")
    if data["encoding"] != "utf-8":
        raise SysMLValidationProfileError("fingerprint encoding must be utf-8.")
    if data["canonical_json"] is not True:
        raise SysMLValidationProfileError("canonical_json must be true.")
    _require_exact_string_list(
        data["validation_input_components"],
        expected=_EXPECTED_VALIDATION_INPUT_COMPONENTS,
        label="validation_input_components",
    )
    _require_exact_string_list(
        data["validation_result_excluded_fields"],
        expected=_EXPECTED_DISCARD_FIELDS,
        label="validation_result_excluded_fields",
    )
    return dict(data)


def _load_json_without_duplicate_keys(path: Path | str) -> dict[str, Any]:
    target = Path(path)
    try:
        raw = target.read_text(encoding="utf-8")
    except OSError as exc:
        raise SysMLValidationProfileError(
            f"Unable to read Phase-K Validation Profile: {target}."
        ) from exc
    try:
        value = json.loads(raw, object_pairs_hook=_without_duplicate_keys)
    except SysMLValidationProfileError:
        raise
    except json.JSONDecodeError as exc:
        raise SysMLValidationProfileError(
            f"Phase-K Validation Profile is not valid JSON: {target}."
        ) from exc
    if not isinstance(value, dict):
        raise SysMLValidationProfileError(
            f"Phase-K Validation Profile must be a JSON object: {target}."
        )
    return value


def _exact_object(
    value: object,
    *,
    expected: frozenset[str],
    label: str,
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise SysMLValidationProfileError(f"{label} must be a JSON object.")
    actual = frozenset(value)
    if actual != expected:
        raise SysMLValidationProfileError(
            f"{label} has invalid fields; "
            f"missing={sorted(expected - actual)}, "
            f"unknown={sorted(actual - expected)}."
        )
    return value


def _require_semver(value: object, label: str) -> str:
    if not isinstance(value, str) or _SEMVER_PATTERN.fullmatch(value) is None:
        raise SysMLValidationProfileError(f"{label} must be a semantic version.")
    return value


def _require_upper_id(value: object, label: str) -> str:
    if not isinstance(value, str) or _UPPER_ID_PATTERN.fullmatch(value) is None:
        raise SysMLValidationProfileError(
            f"{label} must be an uppercase identifier."
        )
    return value


def _require_lower_id(value: object, label: str) -> str:
    if not isinstance(value, str) or _LOWER_ID_PATTERN.fullmatch(value) is None:
        raise SysMLValidationProfileError(
            f"{label} must be a lowercase identifier."
        )
    return value


def _require_nonempty_string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SysMLValidationProfileError(f"{label} must be a non-empty string.")
    return value


def _require_exact_string_list(
    value: object,
    *,
    expected: tuple[str, ...],
    label: str,
) -> tuple[str, ...]:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise SysMLValidationProfileError(f"{label} must be a list of strings.")
    normalized = tuple(value)
    if normalized != expected:
        raise SysMLValidationProfileError(
            f"{label} must match the Phase-K 1.0.0 contract in canonical order."
        )
    return normalized


def _require_enum(
    value: object,
    *,
    allowed: tuple[str, ...],
    label: str,
) -> str:
    if value not in allowed:
        raise SysMLValidationProfileError(
            f"{label} must be one of {list(allowed)!r}."
        )
    return value  # type: ignore[return-value]


def _without_duplicate_keys(
    pairs: list[tuple[str, object]],
) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise SysMLValidationProfileError(
                f"Duplicate JSON key is not allowed: {key!r}."
            )
        result[key] = value
    return result
