"""Safe and deterministic Evidence Reference operations for P7."""

from __future__ import annotations

import re
from pathlib import Path, PurePosixPath
from typing import Iterable

from modules.project_dashboard.errors import (
    DashboardIntegrityError,
    DashboardReferenceError,
    DashboardValidationError,
)
from modules.project_dashboard.types import (
    DASHBOARD_EVIDENCE_ROLES,
    DASHBOARD_NAVIGATION_MODES,
    EvidenceLocation,
    EvidenceNavigation,
    EvidenceReference,
)


_PROJECT_ID_PATTERN = re.compile(r"^[0-9]{6}$")
_TOKEN_PATTERN = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
_REFERENCE_ID_PATTERN = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,191}$"
)
_MEDIA_TYPE_PATTERN = re.compile(
    r"^[a-z0-9][a-z0-9!#$&^_.+-]*/"
    r"[a-z0-9][a-z0-9!#$&^_.+-]*$"
)
_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_SOURCE_ROLES = frozenset({"engineering_source", "context_only"})


def validate_evidence_location(
    value: object,
) -> EvidenceLocation:
    """Return one valid optional document location."""

    if not isinstance(value, EvidenceLocation):
        raise DashboardValidationError(
            "location must be an EvidenceLocation."
        )

    if value.section_anchor is not None:
        _require_nonempty_text(
            value.section_anchor,
            "section_anchor",
        )

    if value.line_start is None and value.line_end is not None:
        raise DashboardValidationError(
            "line_end requires line_start."
        )
    if value.line_start is not None:
        if (
            isinstance(value.line_start, bool)
            or not isinstance(value.line_start, int)
            or value.line_start < 1
        ):
            raise DashboardValidationError(
                "line_start must be a positive integer."
            )
        if value.line_end is not None and (
            isinstance(value.line_end, bool)
            or not isinstance(value.line_end, int)
            or value.line_end < value.line_start
        ):
            raise DashboardValidationError(
                "line_end must be greater than or equal to line_start."
            )

    if value.json_pointer is not None:
        if not isinstance(value.json_pointer, str):
            raise DashboardValidationError(
                "json_pointer must be a string."
            )
        if (
            value.json_pointer
            and not value.json_pointer.startswith("/")
        ):
            raise DashboardValidationError(
                "json_pointer must be empty or start with '/'."
            )

    if value.table_row_key is not None:
        _require_nonempty_text(
            value.table_row_key,
            "table_row_key",
        )

    locator_families = sum(
        (
            value.section_anchor is not None
            or value.line_start is not None,
            value.json_pointer is not None,
            value.table_row_key is not None,
        )
    )
    if locator_families > 1:
        raise DashboardValidationError(
            "location may use text, JSON or table navigation, not several."
        )

    return value


def validate_evidence_reference(
    value: object,
) -> EvidenceReference:
    """Validate one project-bound, repository-relative reference."""

    if not isinstance(value, EvidenceReference):
        raise DashboardValidationError(
            "value must be an EvidenceReference."
        )

    if _PROJECT_ID_PATTERN.fullmatch(value.project_id) is None:
        raise DashboardValidationError(
            "project_id must be a six-digit numeric string."
        )

    _require_token(value.reference_type, "reference_type")
    _require_reference_id(value.reference_id)
    _require_nonempty_text(value.display_label, "display_label")
    _validate_repository_relative_path(
        value.repository_relative_path,
        project_id=value.project_id,
    )

    if value.content_fingerprint is not None and (
        not isinstance(value.content_fingerprint, str)
        or _SHA256_PATTERN.fullmatch(value.content_fingerprint) is None
    ):
        raise DashboardValidationError(
            "content_fingerprint must be lowercase SHA-256 or None."
        )

    if (
        not isinstance(value.media_type, str)
        or _MEDIA_TYPE_PATTERN.fullmatch(value.media_type) is None
    ):
        raise DashboardValidationError(
            "media_type must be a normalized MIME type."
        )

    if (
        value.source_role is not None
        and value.source_role not in _SOURCE_ROLES
    ):
        raise DashboardValidationError(
            "source_role must be engineering_source, context_only or None."
        )

    _require_token(value.relationship, "relationship")

    if value.evidence_role not in DASHBOARD_EVIDENCE_ROLES:
        raise DashboardValidationError(
            "evidence_role must be direct or contextual."
        )

    if value.location is not None:
        validate_evidence_location(value.location)

    return value


def evidence_reference_key(
    reference: EvidenceReference,
) -> tuple[object, ...]:
    """Return one exact identity key for duplicate detection."""

    validated = validate_evidence_reference(reference)
    location = validated.location
    return (
        validated.project_id,
        validated.reference_type,
        validated.reference_id,
        validated.repository_relative_path,
        validated.content_fingerprint,
        validated.relationship,
        validated.evidence_role,
        None if location is None else location.section_anchor,
        None if location is None else location.line_start,
        None if location is None else location.line_end,
        None if location is None else location.json_pointer,
        None if location is None else location.table_row_key,
    )


def canonicalize_evidence_references(
    references: Iterable[EvidenceReference],
) -> tuple[EvidenceReference, ...]:
    """Validate, deduplicate and deterministically order references."""

    try:
        supplied = tuple(references)
    except TypeError as exc:
        raise DashboardValidationError(
            "references must be iterable."
        ) from exc

    by_key: dict[tuple[object, ...], EvidenceReference] = {}

    for reference in supplied:
        validated = validate_evidence_reference(reference)
        key = evidence_reference_key(validated)
        existing = by_key.get(key)
        if existing is not None and existing != validated:
            raise DashboardIntegrityError(
                "Equivalent Evidence Reference identity has conflicting "
                "display metadata."
            )
        by_key[key] = validated

    return tuple(
        sorted(
            by_key.values(),
            key=lambda reference: (
                0 if reference.evidence_role == "direct" else 1,
                reference.reference_type,
                reference.display_label.casefold(),
                reference.reference_id,
                reference.repository_relative_path,
                reference.relationship,
            ),
        )
    )


def build_evidence_navigation(
    references: Iterable[EvidenceReference] = (),
) -> EvidenceNavigation:
    """Choose unavailable, direct or chooser navigation deterministically."""

    ordered = canonicalize_evidence_references(references)

    if not ordered:
        mode = "unavailable"
    elif len(ordered) == 1:
        mode = "direct"
    else:
        mode = "chooser"

    navigation = EvidenceNavigation(
        mode=mode,
        references=ordered,
    )
    validate_evidence_navigation(navigation)
    return navigation


def validate_evidence_navigation(
    value: object,
) -> EvidenceNavigation:
    """Validate navigation mode against the exact reference count."""

    if not isinstance(value, EvidenceNavigation):
        raise DashboardValidationError(
            "value must be an EvidenceNavigation."
        )
    if value.mode not in DASHBOARD_NAVIGATION_MODES:
        raise DashboardValidationError(
            "navigation mode is invalid."
        )
    if not isinstance(value.references, tuple):
        raise DashboardValidationError(
            "navigation references must be a tuple."
        )

    ordered = canonicalize_evidence_references(value.references)
    if ordered != value.references:
        raise DashboardValidationError(
            "navigation references must be canonical."
        )

    expected = (
        "unavailable"
        if len(ordered) == 0
        else "direct"
        if len(ordered) == 1
        else "chooser"
    )
    if value.mode != expected:
        raise DashboardValidationError(
            "navigation mode does not match reference count."
        )

    return value


def resolve_evidence_path(
    reference: EvidenceReference,
    *,
    repository_root: Path | str,
    require_exists: bool = True,
) -> Path:
    """Resolve one safe reference without allowing path escape or symlinks."""

    validated = validate_evidence_reference(reference)
    root = Path(repository_root)

    if root.is_symlink():
        raise DashboardReferenceError(
            "repository_root must not be a symbolic link."
        )
    if root.exists() and not root.is_dir():
        raise DashboardReferenceError(
            "repository_root must be a directory."
        )

    try:
        resolved_root = root.resolve(strict=False)
    except OSError as exc:
        raise DashboardReferenceError(
            "Unable to resolve repository_root."
        ) from exc

    relative = PurePosixPath(
        validated.repository_relative_path
    )
    candidate = root.joinpath(*relative.parts)

    _reject_symlink_chain(root, candidate)

    try:
        resolved_candidate = candidate.resolve(strict=False)
    except OSError as exc:
        raise DashboardReferenceError(
            "Unable to resolve Evidence Reference path."
        ) from exc

    if not resolved_candidate.is_relative_to(resolved_root):
        raise DashboardReferenceError(
            "Evidence Reference escapes repository_root."
        )

    if require_exists:
        if not candidate.exists():
            raise DashboardReferenceError(
                "Referenced artifact does not exist."
            )
        if candidate.is_symlink() or not candidate.is_file():
            raise DashboardReferenceError(
                "Referenced artifact must be a regular file."
            )

    return resolved_candidate


def _validate_repository_relative_path(
    value: object,
    *,
    project_id: str,
) -> str:
    if not isinstance(value, str) or not value:
        raise DashboardValidationError(
            "repository_relative_path must be a non-empty string."
        )
    if "\x00" in value or "\\" in value:
        raise DashboardValidationError(
            "repository_relative_path contains an unsafe character."
        )

    path = PurePosixPath(value)
    if path.is_absolute():
        raise DashboardValidationError(
            "repository_relative_path must be relative."
        )
    if any(part in {"", ".", ".."} for part in path.parts):
        raise DashboardValidationError(
            "repository_relative_path must be normalized without dot segments."
        )
    if path.as_posix() != value:
        raise DashboardValidationError(
            "repository_relative_path must use canonical POSIX form."
        )

    parts = path.parts
    if len(parts) >= 3 and parts[:2] == ("data", "projects"):
        if parts[2] != project_id:
            raise DashboardValidationError(
                "project-local Evidence Reference crosses project boundary."
            )

    return value


def _reject_symlink_chain(root: Path, candidate: Path) -> None:
    current = root
    if current.exists() and current.is_symlink():
        raise DashboardReferenceError(
            "repository_root must not be a symbolic link."
        )

    try:
        relative_parts = candidate.relative_to(root).parts
    except ValueError as exc:
        raise DashboardReferenceError(
            "Evidence Reference does not belong to repository_root."
        ) from exc

    for part in relative_parts:
        current = current / part
        if current.exists() and current.is_symlink():
            raise DashboardReferenceError(
                "Evidence Reference path contains a symbolic link."
            )


def _require_nonempty_text(value: object, label: str) -> str:
    if (
        not isinstance(value, str)
        or not value.strip()
        or value != value.strip()
    ):
        raise DashboardValidationError(
            f"{label} must be a trimmed non-empty string."
        )
    return value


def _require_token(value: object, label: str) -> str:
    if (
        not isinstance(value, str)
        or _TOKEN_PATTERN.fullmatch(value) is None
    ):
        raise DashboardValidationError(
            f"{label} must be a lowercase snake-case token."
        )
    return value


def _require_reference_id(value: object) -> str:
    if (
        not isinstance(value, str)
        or _REFERENCE_ID_PATTERN.fullmatch(value) is None
    ):
        raise DashboardValidationError(
            "reference_id has an invalid format."
        )
    return value
