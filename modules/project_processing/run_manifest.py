"""Create, validate and serialize immutable Processing Run Manifests."""

from __future__ import annotations

from datetime import datetime
import hashlib
import json
import re
from typing import Any

from modules.project_sources.manifest import (
    CONTEXT_ONLY_SOURCE_ROLE,
    ENGINEERING_SOURCE_ROLE,
    validate_source_role,
)
from modules.project_workspace.identifiers import (
    is_valid_project_id,
)

from .errors import ProcessingValidationError
from .identifiers import validate_processing_run_id
from .types import (
    PROCESSING_WORKFLOW_PROFILES,
    ProcessingRunManifest,
    SemanticReferenceVersion,
)


PROCESSING_RUN_MANIFEST_SCHEMA_VERSION = "1.0.0"
PROCESSING_RUN_MANIFEST_FILENAME = "run_manifest.json"

_ENGINEERING_WORKFLOW_PROFILE = (
    "engineering_source_processing"
)
_CONTEXT_ONLY_WORKFLOW_PROFILE = (
    "context_only_processing"
)

_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_SEMANTIC_VERSION_PATTERN = re.compile(
    r"^[0-9]+\.[0-9]+\.[0-9]+$"
)
_FRAMEWORK_TEMPLATE_ID_PATTERN = re.compile(
    r"^[A-Z][A-Z0-9_]*$"
)
_REFERENCE_SYSTEM_ID_PATTERN = re.compile(
    r"^[A-Z][A-Z0-9_]*$"
)
_UTC_TIMESTAMP_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T"
    r"\d{2}:\d{2}:\d{2}"
    r"(?:\.\d+)?Z$"
)

_RUN_MANIFEST_FIELDS = frozenset(
    {
        "schema_version",
        "project_id",
        "processing_run_id",
        "source_id",
        "source_sha256",
        "source_role_snapshot",
        "workflow_profile",
        "configuration_fingerprint",
        "framework_template_id",
        "framework_template_version",
        "semantic_reference_versions",
        "created_at",
        "supersedes_run_id",
    }
)

_SEMANTIC_REFERENCE_FIELDS = frozenset(
    {
        "reference_system_id",
        "reference_version",
    }
)


def create_processing_run_manifest(
    *,
    project_id: str,
    processing_run_id: str,
    source_id: str,
    source_sha256: str,
    source_role_snapshot: str,
    workflow_profile: str,
    configuration_fingerprint: str,
    framework_template_id: str,
    framework_template_version: str,
    semantic_reference_versions: tuple[
        SemanticReferenceVersion,
        ...
    ],
    timestamp: str,
    supersedes_run_id: str | None = None,
) -> ProcessingRunManifest:
    """Create and validate one immutable Run Manifest."""

    manifest = ProcessingRunManifest(
        schema_version=(
            PROCESSING_RUN_MANIFEST_SCHEMA_VERSION
        ),
        project_id=project_id,
        processing_run_id=processing_run_id,
        source_id=source_id,
        source_sha256=source_sha256,
        source_role_snapshot=source_role_snapshot,
        workflow_profile=workflow_profile,
        configuration_fingerprint=configuration_fingerprint,
        framework_template_id=framework_template_id,
        framework_template_version=framework_template_version,
        semantic_reference_versions=(
            semantic_reference_versions
        ),
        created_at=timestamp,
        supersedes_run_id=supersedes_run_id,
    )

    validate_processing_run_manifest(manifest)

    return manifest


def create_semantic_reference_version(
    *,
    reference_system_id: str,
    reference_version: str,
) -> SemanticReferenceVersion:
    """Create and validate one semantic reference binding."""

    reference = SemanticReferenceVersion(
        reference_system_id=reference_system_id,
        reference_version=reference_version,
    )

    _validate_semantic_reference_version(reference)

    return reference


def parse_processing_run_manifest(
    payload: object,
) -> ProcessingRunManifest:
    """Parse and validate one Run Manifest mapping."""

    if not isinstance(payload, dict):
        raise ProcessingValidationError(
            "Processing Run Manifest must be a JSON object."
        )

    normalized_payload = dict(payload)
    normalized_payload.setdefault(
        "supersedes_run_id",
        None,
    )

    _require_exact_fields(
        normalized_payload,
        expected_fields=_RUN_MANIFEST_FIELDS,
        label="Processing Run Manifest",
    )

    semantic_reference_payloads = normalized_payload[
        "semantic_reference_versions"
    ]

    if not isinstance(semantic_reference_payloads, list):
        raise ProcessingValidationError(
            "semantic_reference_versions must be a JSON array."
        )

    semantic_references = tuple(
        _parse_semantic_reference_version(item)
        for item in semantic_reference_payloads
    )

    manifest = ProcessingRunManifest(
        schema_version=normalized_payload["schema_version"],
        project_id=normalized_payload["project_id"],
        processing_run_id=normalized_payload[
            "processing_run_id"
        ],
        source_id=normalized_payload["source_id"],
        source_sha256=normalized_payload["source_sha256"],
        source_role_snapshot=normalized_payload[
            "source_role_snapshot"
        ],
        workflow_profile=normalized_payload[
            "workflow_profile"
        ],
        configuration_fingerprint=normalized_payload[
            "configuration_fingerprint"
        ],
        framework_template_id=normalized_payload[
            "framework_template_id"
        ],
        framework_template_version=normalized_payload[
            "framework_template_version"
        ],
        semantic_reference_versions=semantic_references,
        created_at=normalized_payload["created_at"],
        supersedes_run_id=normalized_payload[
            "supersedes_run_id"
        ],
    )

    validate_processing_run_manifest(manifest)

    return manifest


def processing_run_manifest_from_json(
    text: object,
) -> ProcessingRunManifest:
    """Parse one Run Manifest from strict JSON."""

    if not isinstance(text, str):
        raise ProcessingValidationError(
            "Processing Run Manifest JSON must be a string."
        )

    try:
        payload = json.loads(
            text,
            object_pairs_hook=_object_without_duplicate_keys,
        )
    except ProcessingValidationError:
        raise
    except json.JSONDecodeError as exc:
        raise ProcessingValidationError(
            "Processing Run Manifest is not valid JSON."
        ) from exc

    return parse_processing_run_manifest(payload)


def processing_run_manifest_to_dict(
    manifest: ProcessingRunManifest,
) -> dict[str, object]:
    """Serialize one validated Run Manifest to a mapping."""

    validate_processing_run_manifest(manifest)

    payload: dict[str, object] = {
        "schema_version": manifest.schema_version,
        "project_id": manifest.project_id,
        "processing_run_id": manifest.processing_run_id,
        "source_id": manifest.source_id,
        "source_sha256": manifest.source_sha256,
        "source_role_snapshot": (
            manifest.source_role_snapshot
        ),
        "workflow_profile": manifest.workflow_profile,
        "configuration_fingerprint": (
            manifest.configuration_fingerprint
        ),
        "framework_template_id": (
            manifest.framework_template_id
        ),
        "framework_template_version": (
            manifest.framework_template_version
        ),
        "semantic_reference_versions": [
            {
                "reference_system_id": (
                    reference.reference_system_id
                ),
                "reference_version": (
                    reference.reference_version
                ),
            }
            for reference in (
                manifest.semantic_reference_versions
            )
        ],
        "created_at": manifest.created_at,
    }

    if manifest.supersedes_run_id is not None:
        payload["supersedes_run_id"] = (
            manifest.supersedes_run_id
        )

    return payload


def processing_run_manifest_to_json(
    manifest: ProcessingRunManifest,
) -> str:
    """Serialize one Run Manifest as deterministic JSON."""

    return (
        json.dumps(
            processing_run_manifest_to_dict(manifest),
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )


def calculate_processing_run_manifest_fingerprint(
    manifest: ProcessingRunManifest,
) -> str:
    """Calculate the deterministic fingerprint of a Run Manifest."""

    payload = processing_run_manifest_to_dict(manifest)

    canonical_json = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )

    return hashlib.sha256(
        canonical_json.encode("utf-8")
    ).hexdigest()


def validate_processing_run_manifest(
    manifest: object,
) -> ProcessingRunManifest:
    """Validate and return one immutable Run Manifest."""

    if not isinstance(manifest, ProcessingRunManifest):
        raise ProcessingValidationError(
            "manifest must be a ProcessingRunManifest."
        )

    if (
        manifest.schema_version
        != PROCESSING_RUN_MANIFEST_SCHEMA_VERSION
    ):
        raise ProcessingValidationError(
            "Unsupported Processing Run Manifest "
            f"schema_version: {manifest.schema_version!r}."
        )

    if not is_valid_project_id(manifest.project_id):
        raise ProcessingValidationError(
            "project_id must match ^[0-9]{6}$."
        )

    try:
        validate_processing_run_id(
            manifest.processing_run_id
        )
    except Exception as exc:
        raise ProcessingValidationError(
            "processing_run_id is invalid."
        ) from exc

    _validate_source_id(manifest.source_id)

    _validate_sha256(
        manifest.source_sha256,
        label="source_sha256",
    )

    try:
        validate_source_role(
            manifest.source_role_snapshot
        )
    except Exception as exc:
        raise ProcessingValidationError(
            "source_role_snapshot is invalid."
        ) from exc

    _validate_workflow_profile(
        workflow_profile=manifest.workflow_profile,
        source_role_snapshot=(
            manifest.source_role_snapshot
        ),
    )

    _validate_sha256(
        manifest.configuration_fingerprint,
        label="configuration_fingerprint",
    )

    _validate_framework_template_id(
        manifest.framework_template_id
    )

    _validate_semantic_version(
        manifest.framework_template_version,
        label="framework_template_version",
    )

    _validate_semantic_reference_versions(
        manifest.semantic_reference_versions
    )

    _validate_utc_timestamp(
        manifest.created_at,
        label="created_at",
    )

    if manifest.supersedes_run_id is not None:
        try:
            validate_processing_run_id(
                manifest.supersedes_run_id
            )
        except Exception as exc:
            raise ProcessingValidationError(
                "supersedes_run_id is invalid."
            ) from exc

        if (
            manifest.supersedes_run_id
            == manifest.processing_run_id
        ):
            raise ProcessingValidationError(
                "A Processing Run cannot supersede itself."
            )

    return manifest


def _parse_semantic_reference_version(
    payload: object,
) -> SemanticReferenceVersion:
    """Parse one semantic reference binding."""

    if not isinstance(payload, dict):
        raise ProcessingValidationError(
            "Each semantic reference must be a JSON object."
        )

    _require_exact_fields(
        payload,
        expected_fields=_SEMANTIC_REFERENCE_FIELDS,
        label="Semantic reference",
    )

    reference = SemanticReferenceVersion(
        reference_system_id=payload[
            "reference_system_id"
        ],
        reference_version=payload[
            "reference_version"
        ],
    )

    _validate_semantic_reference_version(reference)

    return reference


def _validate_semantic_reference_versions(
    references: object,
) -> None:
    """Validate all semantic references and uniqueness."""

    if not isinstance(references, tuple):
        raise ProcessingValidationError(
            "semantic_reference_versions must be a tuple."
        )

    if not references:
        raise ProcessingValidationError(
            "semantic_reference_versions must not be empty."
        )

    reference_system_ids: list[str] = []

    for reference in references:
        _validate_semantic_reference_version(reference)
        reference_system_ids.append(
            reference.reference_system_id
        )

    if len(reference_system_ids) != len(
        set(reference_system_ids)
    ):
        raise ProcessingValidationError(
            "semantic_reference_versions must contain unique "
            "reference_system_id values."
        )


def _validate_semantic_reference_version(
    reference: object,
) -> None:
    """Validate one semantic reference binding."""

    if not isinstance(reference, SemanticReferenceVersion):
        raise ProcessingValidationError(
            "semantic reference entries must be "
            "SemanticReferenceVersion instances."
        )

    if (
        not isinstance(reference.reference_system_id, str)
        or _REFERENCE_SYSTEM_ID_PATTERN.fullmatch(
            reference.reference_system_id
        )
        is None
    ):
        raise ProcessingValidationError(
            "reference_system_id must match "
            "^[A-Z][A-Z0-9_]*$."
        )

    _validate_trimmed_string(
        reference.reference_version,
        label="reference_version",
        maximum_length=120,
    )


def _validate_workflow_profile(
    *,
    workflow_profile: object,
    source_role_snapshot: str,
) -> None:
    """Validate workflow profile and source-role compatibility."""

    if workflow_profile not in PROCESSING_WORKFLOW_PROFILES:
        raise ProcessingValidationError(
            "workflow_profile is not supported."
        )

    if (
        source_role_snapshot
        == CONTEXT_ONLY_SOURCE_ROLE
        and workflow_profile
        != _CONTEXT_ONLY_WORKFLOW_PROFILE
    ):
        raise ProcessingValidationError(
            "A context_only source requires the "
            "context_only_processing workflow profile."
        )

    if (
        source_role_snapshot
        == ENGINEERING_SOURCE_ROLE
        and workflow_profile
        not in {
            _ENGINEERING_WORKFLOW_PROFILE,
            _CONTEXT_ONLY_WORKFLOW_PROFILE,
        }
    ):
        raise ProcessingValidationError(
            "An engineering_source uses an unsupported "
            "workflow profile."
        )


def _validate_source_id(value: object) -> None:
    """Validate one Source ID without leaking source errors."""

    if (
        not isinstance(value, str)
        or re.fullmatch(r"^SRC-[0-9]{6}$", value)
        is None
        or value == "SRC-000000"
    ):
        raise ProcessingValidationError(
            "source_id must match ^SRC-[0-9]{6}$ and use "
            "a sequence from 000001 to 999999."
        )


def _validate_sha256(
    value: object,
    *,
    label: str,
) -> None:
    """Validate one lowercase SHA-256 value."""

    if (
        not isinstance(value, str)
        or _SHA256_PATTERN.fullmatch(value) is None
    ):
        raise ProcessingValidationError(
            f"{label} must be a lowercase 64-character "
            "SHA-256 value."
        )


def _validate_framework_template_id(value: object) -> None:
    """Validate one framework-template identifier."""

    if (
        not isinstance(value, str)
        or _FRAMEWORK_TEMPLATE_ID_PATTERN.fullmatch(value)
        is None
    ):
        raise ProcessingValidationError(
            "framework_template_id must match "
            "^[A-Z][A-Z0-9_]*$."
        )


def _validate_semantic_version(
    value: object,
    *,
    label: str,
) -> None:
    """Validate one semantic version."""

    if (
        not isinstance(value, str)
        or _SEMANTIC_VERSION_PATTERN.fullmatch(value)
        is None
    ):
        raise ProcessingValidationError(
            f"{label} must use semantic versioning."
        )


def _validate_utc_timestamp(
    value: object,
    *,
    label: str,
) -> None:
    """Validate one UTC ISO-8601 timestamp."""

    if (
        not isinstance(value, str)
        or _UTC_TIMESTAMP_PATTERN.fullmatch(value) is None
    ):
        raise ProcessingValidationError(
            f"{label} must be a UTC ISO-8601 timestamp "
            "ending in Z."
        )

    try:
        parsed = datetime.fromisoformat(
            value.removesuffix("Z") + "+00:00"
        )
    except ValueError as exc:
        raise ProcessingValidationError(
            f"{label} is not a valid timestamp."
        ) from exc

    if parsed.utcoffset() is None:
        raise ProcessingValidationError(
            f"{label} must include the UTC timezone."
        )

    if parsed.utcoffset().total_seconds() != 0:
        raise ProcessingValidationError(
            f"{label} must use UTC."
        )


def _validate_trimmed_string(
    value: object,
    *,
    label: str,
    maximum_length: int,
) -> None:
    """Validate one required stored string."""

    if not isinstance(value, str):
        raise ProcessingValidationError(
            f"{label} must be a string."
        )

    if not value:
        raise ProcessingValidationError(
            f"{label} must not be empty."
        )

    if value != value.strip():
        raise ProcessingValidationError(
            f"{label} must not contain surrounding whitespace."
        )

    if len(value) > maximum_length:
        raise ProcessingValidationError(
            f"{label} must contain at most "
            f"{maximum_length} characters."
        )


def _object_without_duplicate_keys(
    pairs: list[tuple[str, Any]],
) -> dict[str, Any]:
    """Reject duplicate JSON object keys."""

    payload: dict[str, Any] = {}

    for key, value in pairs:
        if key in payload:
            raise ProcessingValidationError(
                f"Duplicate JSON field: {key}."
            )
        payload[key] = value

    return payload


def _require_exact_fields(
    payload: dict[str, object],
    *,
    expected_fields: frozenset[str],
    label: str,
) -> None:
    """Require one exact closed field set."""

    actual_fields = frozenset(payload)

    missing_fields = expected_fields - actual_fields
    unknown_fields = actual_fields - expected_fields

    if missing_fields:
        raise ProcessingValidationError(
            f"{label} is missing fields: "
            f"{sorted(missing_fields)}."
        )

    if unknown_fields:
        raise ProcessingValidationError(
            f"{label} contains unknown fields: "
            f"{sorted(unknown_fields)}."
        )