"""Load and validate the versioned Phase-L output publication profile."""

from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path, PurePosixPath
import re
from typing import Any

from .errors import (
    OutputPublicationIntegrityError,
    OutputPublicationValidationError,
)
from .types import (
    OUTPUT_FILE_ROLES,
    OutputPublicationProfile,
    OutputPublicationProfileReference,
)


OUTPUT_PUBLICATION_PROFILE_SCHEMA_VERSION = "1.0.0"
OUTPUT_PUBLICATION_PROFILE_ID = "TURING_SYSML_V2_OUTPUT"
OUTPUT_PUBLICATION_PROFILE_VERSION = "1.0.0"
DEFAULT_OUTPUT_PUBLICATION_PROFILE_PATH = Path(
    "context/sysml/turing_sysml_v2_output_profile.json"
)
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_FIELDS = {
    "schema_version",
    "profile_id",
    "profile_version",
    "name",
    "status",
    "output_root",
    "package_id_pattern",
    "required_file_roles",
    "generated_unit_placement",
    "manifest_filename",
    "idempotence_policy",
    "archive_policy",
    "profile_fingerprint",
}


def load_output_publication_profile(
    path: Path | str = DEFAULT_OUTPUT_PUBLICATION_PROFILE_PATH,
) -> OutputPublicationProfile:
    selected = Path(path)
    if selected.is_symlink() or not selected.exists() or not selected.is_file():
        raise OutputPublicationValidationError(
            f"Output Publication Profile not found as a regular file: {selected}."
        )
    try:
        text = selected.read_text(encoding="utf-8")
    except OSError as exc:
        raise OutputPublicationValidationError(
            f"Unable to read Output Publication Profile: {selected}."
        ) from exc
    try:
        payload = json.loads(text, object_pairs_hook=_without_duplicate_keys)
    except OutputPublicationValidationError:
        raise
    except json.JSONDecodeError as exc:
        raise OutputPublicationValidationError(
            "Output Publication Profile contains invalid JSON."
        ) from exc
    if not isinstance(payload, dict):
        raise OutputPublicationValidationError(
            "Output Publication Profile must be a JSON object."
        )
    if set(payload) != _FIELDS:
        raise OutputPublicationValidationError(
            "Output Publication Profile has invalid fields."
        )
    expected_fingerprint = calculate_output_publication_profile_fingerprint(payload)
    stored_fingerprint = payload["profile_fingerprint"]
    if (
        not isinstance(stored_fingerprint, str)
        or _SHA256.fullmatch(stored_fingerprint) is None
        or stored_fingerprint != expected_fingerprint
    ):
        raise OutputPublicationIntegrityError(
            "Output Publication Profile fingerprint does not match its content."
        )
    profile = OutputPublicationProfile(
        schema_version=_expected(
            payload["schema_version"],
            OUTPUT_PUBLICATION_PROFILE_SCHEMA_VERSION,
            "schema_version",
        ),
        profile_id=_expected(
            payload["profile_id"],
            OUTPUT_PUBLICATION_PROFILE_ID,
            "profile_id",
        ),
        profile_version=_expected(
            payload["profile_version"],
            OUTPUT_PUBLICATION_PROFILE_VERSION,
            "profile_version",
        ),
        name=_text(payload["name"], "name"),
        status=_expected(payload["status"], "accepted", "status"),
        output_root=_safe_relative_directory(payload["output_root"]),
        package_id_pattern=_expected(
            payload["package_id_pattern"],
            r"^OUT-[0-9]{6}$",
            "package_id_pattern",
        ),
        required_file_roles=_roles(payload["required_file_roles"]),
        generated_unit_placement=_expected(
            payload["generated_unit_placement"],
            "preserve_relative_path",
            "generated_unit_placement",
        ),
        manifest_filename=_expected(
            payload["manifest_filename"],
            "manifest.json",
            "manifest_filename",
        ),
        idempotence_policy=_expected(
            payload["idempotence_policy"],
            "same_publication_input_returns_existing_package",
            "idempotence_policy",
        ),
        archive_policy=_expected(
            payload["archive_policy"],
            "derived_non_authoritative",
            "archive_policy",
        ),
        profile_fingerprint=stored_fingerprint,
    )
    return profile


def output_publication_profile_reference(
    profile: OutputPublicationProfile,
) -> OutputPublicationProfileReference:
    if not isinstance(profile, OutputPublicationProfile):
        raise OutputPublicationValidationError(
            "profile must be an OutputPublicationProfile."
        )
    return OutputPublicationProfileReference(
        profile_id=profile.profile_id,
        profile_version=profile.profile_version,
        profile_fingerprint=profile.profile_fingerprint,
    )


def calculate_output_publication_profile_fingerprint(payload: object) -> str:
    if isinstance(payload, OutputPublicationProfile):
        data = asdict(payload)
    elif isinstance(payload, dict):
        data = dict(payload)
    else:
        raise OutputPublicationValidationError(
            "Output Publication Profile fingerprint input is invalid."
        )
    data.pop("profile_fingerprint", None)
    try:
        canonical = json.dumps(
            data,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    except (TypeError, ValueError) as exc:
        raise OutputPublicationValidationError(
            "Output Publication Profile is not JSON serializable."
        ) from exc
    import hashlib

    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _roles(value: object) -> tuple[str, ...]:
    if not isinstance(value, list) or not value:
        raise OutputPublicationValidationError(
            "required_file_roles must be a non-empty JSON array."
        )
    if any(not isinstance(item, str) for item in value):
        raise OutputPublicationValidationError(
            "required_file_roles must contain strings."
        )
    selected = tuple(value)
    if selected != tuple(sorted(selected)):
        raise OutputPublicationValidationError(
            "required_file_roles must use canonical ordering."
        )
    if len(selected) != len(set(selected)):
        raise OutputPublicationValidationError(
            "required_file_roles must be unique."
        )
    if set(selected) != set(OUTPUT_FILE_ROLES):
        raise OutputPublicationValidationError(
            "required_file_roles must match the Phase-L MVP file-role set."
        )
    return selected


def _safe_relative_directory(value: object) -> str:
    selected = _text(value, "output_root")
    if "\\" in selected:
        raise OutputPublicationValidationError(
            "output_root must use POSIX separators."
        )
    path = PurePosixPath(selected)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise OutputPublicationValidationError(
            "output_root must be a safe normalized relative path."
        )
    if path.as_posix() != selected:
        raise OutputPublicationValidationError(
            "output_root must already be normalized."
        )
    return selected


def _expected(value: object, expected: str, label: str) -> str:
    if value != expected:
        raise OutputPublicationValidationError(
            f"{label} must be {expected!r}."
        )
    return expected


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise OutputPublicationValidationError(
            f"{label} must be a non-empty trimmed string."
        )
    return value


def _without_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise OutputPublicationValidationError(
                f"Duplicate Output Publication Profile key: {key!r}."
            )
        result[key] = value
    return result
