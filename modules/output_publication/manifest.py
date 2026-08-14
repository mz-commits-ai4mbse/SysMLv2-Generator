"""Strict manifest contract for immutable published output packages."""

from __future__ import annotations

from dataclasses import asdict, replace
import json
from pathlib import PurePosixPath
import re
from typing import Any

from modules.project_workspace.identifiers import is_valid_project_id

from .errors import (
    OutputPublicationIntegrityError,
    OutputPublicationValidationError,
)
from .identifiers import validate_output_package_id
from .types import (
    OUTPUT_FILE_ROLES,
    OutputPublicationProfile,
    OutputPublicationProfileReference,
    PublishedOutputFileReference,
    PublishedOutputManifest,
)


PUBLISHED_OUTPUT_MANIFEST_SCHEMA_VERSION = "1.0.0"
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_IEM_ID = re.compile(r"^IEM-[0-9]{6}$")
_FMR_ID = re.compile(r"^FMR-[0-9]{6}$")
_FRV_ID = re.compile(r"^FRV-[0-9]{6}$")
_FRD_ID = re.compile(r"^FRD-[0-9]{6}$")
_TIMESTAMP = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T"
    r"[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]+)?Z$"
)
_MANIFEST_FIELDS = {
    "schema_version",
    "project_id",
    "output_package_id",
    "source_internal_engineering_model_id",
    "source_artifact_set_fingerprint",
    "validation_result_fingerprint",
    "final_model_review_id",
    "final_model_review_revision_id",
    "final_review_revision_fingerprint",
    "final_review_decision_id",
    "final_review_decision_fingerprint",
    "final_release_gate_fingerprint",
    "output_profile_reference",
    "publication_input_fingerprint",
    "files",
    "published_at",
    "content_fingerprint",
}
_PROFILE_FIELDS = {
    "profile_id",
    "profile_version",
    "profile_fingerprint",
}
_FILE_FIELDS = {
    "relative_path",
    "role",
    "content_fingerprint",
    "source_generated_unit_id",
}


def create_published_output_file_reference(
    *,
    relative_path: str,
    role: str,
    content_fingerprint: str,
    source_generated_unit_id: str | None = None,
) -> PublishedOutputFileReference:
    selected_role = _choice(role, OUTPUT_FILE_ROLES, "role")
    generated_unit_id = _optional_generated_unit_id(source_generated_unit_id)
    if selected_role == "sysml_unit" and generated_unit_id is None:
        raise OutputPublicationValidationError(
            "sysml_unit file references require source_generated_unit_id."
        )
    if selected_role != "sysml_unit" and generated_unit_id is not None:
        raise OutputPublicationValidationError(
            "only sysml_unit file references may identify a generated unit."
        )
    path = _safe_relative_path(relative_path)
    if selected_role == "sysml_unit" and PurePosixPath(path).suffix != ".sysml":
        raise OutputPublicationValidationError(
            "published SysML unit paths must end in .sysml."
        )
    return PublishedOutputFileReference(
        relative_path=path,
        role=selected_role,
        content_fingerprint=_sha256(content_fingerprint, "content_fingerprint"),
        source_generated_unit_id=generated_unit_id,
    )


def calculate_publication_input_fingerprint(
    *,
    source_artifact_set_fingerprint: str,
    validation_result_fingerprint: str,
    final_review_decision_fingerprint: str,
    final_review_revision_fingerprint: str,
    output_profile_reference: OutputPublicationProfileReference,
) -> str:
    payload = {
        "source_artifact_set_fingerprint": _sha256(
            source_artifact_set_fingerprint,
            "source_artifact_set_fingerprint",
        ),
        "validation_result_fingerprint": _sha256(
            validation_result_fingerprint,
            "validation_result_fingerprint",
        ),
        "final_review_decision_fingerprint": _sha256(
            final_review_decision_fingerprint,
            "final_review_decision_fingerprint",
        ),
        "final_review_revision_fingerprint": _sha256(
            final_review_revision_fingerprint,
            "final_review_revision_fingerprint",
        ),
        "output_profile_reference": asdict(
            _profile_reference(output_profile_reference)
        ),
    }
    return _json_fingerprint(payload)


def create_published_output_manifest(
    *,
    project_id: str,
    output_package_id: str,
    source_internal_engineering_model_id: str,
    source_artifact_set_fingerprint: str,
    validation_result_fingerprint: str,
    final_model_review_id: str,
    final_model_review_revision_id: str,
    final_review_revision_fingerprint: str,
    final_review_decision_id: str,
    final_review_decision_fingerprint: str,
    final_release_gate_fingerprint: str,
    output_profile_reference: OutputPublicationProfileReference,
    publication_input_fingerprint: str,
    files: tuple[PublishedOutputFileReference, ...],
    published_at: str,
) -> PublishedOutputManifest:
    provisional = PublishedOutputManifest(
        schema_version=PUBLISHED_OUTPUT_MANIFEST_SCHEMA_VERSION,
        project_id=_project_id(project_id),
        output_package_id=validate_output_package_id(output_package_id),
        source_internal_engineering_model_id=_id(
            source_internal_engineering_model_id,
            _IEM_ID,
            "source_internal_engineering_model_id",
        ),
        source_artifact_set_fingerprint=_sha256(
            source_artifact_set_fingerprint,
            "source_artifact_set_fingerprint",
        ),
        validation_result_fingerprint=_sha256(
            validation_result_fingerprint,
            "validation_result_fingerprint",
        ),
        final_model_review_id=_id(
            final_model_review_id, _FMR_ID, "final_model_review_id"
        ),
        final_model_review_revision_id=_id(
            final_model_review_revision_id,
            _FRV_ID,
            "final_model_review_revision_id",
        ),
        final_review_revision_fingerprint=_sha256(
            final_review_revision_fingerprint,
            "final_review_revision_fingerprint",
        ),
        final_review_decision_id=_id(
            final_review_decision_id, _FRD_ID, "final_review_decision_id"
        ),
        final_review_decision_fingerprint=_sha256(
            final_review_decision_fingerprint,
            "final_review_decision_fingerprint",
        ),
        final_release_gate_fingerprint=_sha256(
            final_release_gate_fingerprint,
            "final_release_gate_fingerprint",
        ),
        output_profile_reference=_profile_reference(output_profile_reference),
        publication_input_fingerprint=_sha256(
            publication_input_fingerprint,
            "publication_input_fingerprint",
        ),
        files=_files(files),
        published_at=_timestamp(published_at),
        content_fingerprint="0" * 64,
    )
    return replace(
        provisional,
        content_fingerprint=calculate_published_output_manifest_fingerprint(
            provisional
        ),
    )


def calculate_published_output_manifest_fingerprint(
    manifest: PublishedOutputManifest,
) -> str:
    _validate_manifest(manifest, verify_fingerprint=False)
    payload = asdict(manifest)
    payload.pop("content_fingerprint")
    return _json_fingerprint(payload)


def validate_published_output_manifest(
    manifest: PublishedOutputManifest,
) -> None:
    _validate_manifest(manifest, verify_fingerprint=True)


def validate_manifest_against_profile(
    manifest: PublishedOutputManifest,
    profile: OutputPublicationProfile,
) -> None:
    validate_published_output_manifest(manifest)
    if not isinstance(profile, OutputPublicationProfile):
        raise OutputPublicationValidationError(
            "profile must be an OutputPublicationProfile."
        )
    expected_reference = OutputPublicationProfileReference(
        profile_id=profile.profile_id,
        profile_version=profile.profile_version,
        profile_fingerprint=profile.profile_fingerprint,
    )
    if manifest.output_profile_reference != expected_reference:
        raise OutputPublicationIntegrityError(
            "Published Output manifest does not reference the active Output Profile."
        )
    roles = tuple(item.role for item in manifest.files)
    if set(roles) != set(profile.required_file_roles):
        raise OutputPublicationIntegrityError(
            "Published Output manifest file roles do not match the Output Profile."
        )
    for role in profile.required_file_roles:
        count = roles.count(role)
        if role == "sysml_unit":
            if count < 1:
                raise OutputPublicationIntegrityError(
                    "Published Output requires at least one SysML unit."
                )
        elif count != 1:
            raise OutputPublicationIntegrityError(
                f"Published Output requires exactly one {role} file."
            )


def published_output_manifest_to_json(manifest: PublishedOutputManifest) -> str:
    validate_published_output_manifest(manifest)
    return json.dumps(
        asdict(manifest),
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ) + "\n"


def published_output_manifest_from_json(
    text: object,
    *,
    expected_project_id: str | None = None,
    expected_output_package_id: str | None = None,
) -> PublishedOutputManifest:
    if not isinstance(text, str):
        raise OutputPublicationValidationError(
            "Published Output manifest JSON must be a string."
        )
    try:
        payload = json.loads(text, object_pairs_hook=_without_duplicate_keys)
    except OutputPublicationValidationError:
        raise
    except json.JSONDecodeError as exc:
        raise OutputPublicationValidationError(
            "Published Output manifest contains invalid JSON."
        ) from exc
    if not isinstance(payload, dict) or set(payload) != _MANIFEST_FIELDS:
        raise OutputPublicationValidationError(
            "Published Output manifest has invalid fields."
        )
    profile_data = _exact_object(
        payload["output_profile_reference"],
        _PROFILE_FIELDS,
        "output_profile_reference",
    )
    profile_reference = OutputPublicationProfileReference(
        profile_id=_text(profile_data["profile_id"], "profile_id"),
        profile_version=_text(
            profile_data["profile_version"], "profile_version"
        ),
        profile_fingerprint=_sha256(
            profile_data["profile_fingerprint"], "profile_fingerprint"
        ),
    )
    file_payloads = payload["files"]
    if not isinstance(file_payloads, list):
        raise OutputPublicationValidationError(
            "Published Output manifest files must be a JSON array."
        )
    files = tuple(
        create_published_output_file_reference(
            relative_path=_text(
                _exact_object(item, _FILE_FIELDS, "published file")["relative_path"],
                "relative_path",
            ),
            role=_text(
                _exact_object(item, _FILE_FIELDS, "published file")["role"],
                "role",
            ),
            content_fingerprint=_text(
                _exact_object(item, _FILE_FIELDS, "published file")[
                    "content_fingerprint"
                ],
                "content_fingerprint",
            ),
            source_generated_unit_id=_exact_object(
                item, _FILE_FIELDS, "published file"
            )["source_generated_unit_id"],
        )
        for item in file_payloads
    )
    manifest = create_published_output_manifest(
        project_id=payload["project_id"],
        output_package_id=payload["output_package_id"],
        source_internal_engineering_model_id=(
            payload["source_internal_engineering_model_id"]
        ),
        source_artifact_set_fingerprint=payload[
            "source_artifact_set_fingerprint"
        ],
        validation_result_fingerprint=payload[
            "validation_result_fingerprint"
        ],
        final_model_review_id=payload["final_model_review_id"],
        final_model_review_revision_id=payload[
            "final_model_review_revision_id"
        ],
        final_review_revision_fingerprint=payload[
            "final_review_revision_fingerprint"
        ],
        final_review_decision_id=payload["final_review_decision_id"],
        final_review_decision_fingerprint=payload[
            "final_review_decision_fingerprint"
        ],
        final_release_gate_fingerprint=payload[
            "final_release_gate_fingerprint"
        ],
        output_profile_reference=profile_reference,
        publication_input_fingerprint=payload[
            "publication_input_fingerprint"
        ],
        files=files,
        published_at=payload["published_at"],
    )
    if payload["schema_version"] != PUBLISHED_OUTPUT_MANIFEST_SCHEMA_VERSION:
        raise OutputPublicationValidationError(
            "unsupported Published Output manifest schema_version."
        )
    stored = payload["content_fingerprint"]
    _sha256(stored, "content_fingerprint")
    if manifest.content_fingerprint != stored:
        raise OutputPublicationIntegrityError(
            "Published Output manifest fingerprint does not match its content."
        )
    if expected_project_id is not None and manifest.project_id != expected_project_id:
        raise OutputPublicationIntegrityError(
            "Published Output manifest project_id does not match its path."
        )
    if (
        expected_output_package_id is not None
        and manifest.output_package_id != expected_output_package_id
    ):
        raise OutputPublicationIntegrityError(
            "Published Output manifest ID does not match its path."
        )
    return manifest


def _validate_manifest(
    manifest: PublishedOutputManifest,
    *,
    verify_fingerprint: bool,
) -> None:
    if not isinstance(manifest, PublishedOutputManifest):
        raise OutputPublicationValidationError(
            "manifest must be a PublishedOutputManifest."
        )
    if manifest.schema_version != PUBLISHED_OUTPUT_MANIFEST_SCHEMA_VERSION:
        raise OutputPublicationValidationError(
            "unsupported Published Output manifest schema_version."
        )
    _project_id(manifest.project_id)
    validate_output_package_id(manifest.output_package_id)
    _id(
        manifest.source_internal_engineering_model_id,
        _IEM_ID,
        "source_internal_engineering_model_id",
    )
    _sha256(
        manifest.source_artifact_set_fingerprint,
        "source_artifact_set_fingerprint",
    )
    _sha256(
        manifest.validation_result_fingerprint,
        "validation_result_fingerprint",
    )
    _id(manifest.final_model_review_id, _FMR_ID, "final_model_review_id")
    _id(
        manifest.final_model_review_revision_id,
        _FRV_ID,
        "final_model_review_revision_id",
    )
    _sha256(
        manifest.final_review_revision_fingerprint,
        "final_review_revision_fingerprint",
    )
    _id(
        manifest.final_review_decision_id,
        _FRD_ID,
        "final_review_decision_id",
    )
    _sha256(
        manifest.final_review_decision_fingerprint,
        "final_review_decision_fingerprint",
    )
    _sha256(
        manifest.final_release_gate_fingerprint,
        "final_release_gate_fingerprint",
    )
    _profile_reference(manifest.output_profile_reference)
    _sha256(
        manifest.publication_input_fingerprint,
        "publication_input_fingerprint",
    )
    _files(manifest.files)
    _timestamp(manifest.published_at)
    _sha256(manifest.content_fingerprint, "content_fingerprint")
    if verify_fingerprint:
        expected = calculate_published_output_manifest_fingerprint(
            replace(manifest, content_fingerprint="0" * 64)
        )
        if manifest.content_fingerprint != expected:
            raise OutputPublicationIntegrityError(
                "Published Output manifest fingerprint mismatch."
            )


def _files(
    value: tuple[PublishedOutputFileReference, ...],
) -> tuple[PublishedOutputFileReference, ...]:
    if not isinstance(value, tuple) or not value:
        raise OutputPublicationValidationError(
            "Published Output files must be a non-empty tuple."
        )
    paths: list[str] = []
    unit_ids: list[str] = []
    for item in value:
        if not isinstance(item, PublishedOutputFileReference):
            raise OutputPublicationValidationError(
                "Published Output files contain an invalid value."
            )
        parsed = create_published_output_file_reference(
            relative_path=item.relative_path,
            role=item.role,
            content_fingerprint=item.content_fingerprint,
            source_generated_unit_id=item.source_generated_unit_id,
        )
        paths.append(parsed.relative_path)
        if parsed.source_generated_unit_id is not None:
            unit_ids.append(parsed.source_generated_unit_id)
    if len(paths) != len(set(paths)):
        raise OutputPublicationValidationError(
            "Published Output file paths must be unique."
        )
    if tuple(paths) != tuple(sorted(paths)):
        raise OutputPublicationValidationError(
            "Published Output files must use canonical path ordering."
        )
    if len(unit_ids) != len(set(unit_ids)):
        raise OutputPublicationValidationError(
            "Published SysML unit IDs must be unique."
        )
    return value


def _profile_reference(value: object) -> OutputPublicationProfileReference:
    if not isinstance(value, OutputPublicationProfileReference):
        raise OutputPublicationValidationError(
            "output_profile_reference is invalid."
        )
    _text(value.profile_id, "profile_id")
    _text(value.profile_version, "profile_version")
    _sha256(value.profile_fingerprint, "profile_fingerprint")
    return value


def _optional_generated_unit_id(value: object) -> str | None:
    if value is None:
        return None
    if (
        not isinstance(value, str)
        or re.fullmatch(r"^GSU-[0-9]{6}$", value) is None
        or value == "GSU-000000"
    ):
        raise OutputPublicationValidationError(
            "source_generated_unit_id is invalid."
        )
    return value


def _safe_relative_path(value: object) -> str:
    selected = _text(value, "relative_path")
    if "\\" in selected:
        raise OutputPublicationValidationError(
            "relative_path must use POSIX separators."
        )
    path = PurePosixPath(selected)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise OutputPublicationValidationError(
            "relative_path must be a safe normalized relative path."
        )
    if path.as_posix() != selected or selected == "manifest.json":
        raise OutputPublicationValidationError(
            "relative_path is reserved or not normalized."
        )
    return selected


def _project_id(value: object) -> str:
    if not is_valid_project_id(value):
        raise OutputPublicationValidationError(
            "project_id must be a valid six-digit Project ID."
        )
    return value


def _id(value: object, pattern: re.Pattern[str], label: str) -> str:
    if (
        not isinstance(value, str)
        or pattern.fullmatch(value) is None
        or value.endswith("000000")
    ):
        raise OutputPublicationValidationError(f"{label} is invalid.")
    return value


def _timestamp(value: object) -> str:
    if not isinstance(value, str) or _TIMESTAMP.fullmatch(value) is None:
        raise OutputPublicationValidationError(
            "published_at must be a UTC timestamp ending in Z."
        )
    return value


def _sha256(value: object, label: str) -> str:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise OutputPublicationValidationError(
            f"{label} must be a lowercase SHA-256 value."
        )
    return value


def _choice(value: object, allowed: tuple[str, ...], label: str) -> str:
    if not isinstance(value, str) or value not in allowed:
        raise OutputPublicationValidationError(
            f"{label} must be one of {allowed}."
        )
    return value


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise OutputPublicationValidationError(
            f"{label} must be a non-empty trimmed string."
        )
    return value


def _json_fingerprint(payload: object) -> str:
    import hashlib

    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _exact_object(value: object, fields: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != fields:
        raise OutputPublicationValidationError(f"{label} has invalid fields.")
    return value


def _without_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise OutputPublicationValidationError(
                f"Duplicate Published Output manifest key: {key!r}."
            )
        result[key] = value
    return result
