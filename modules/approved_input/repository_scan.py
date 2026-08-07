"""Deterministic scan diagnostics for Approved Input persistence."""

from __future__ import annotations

from pathlib import Path
import re

from .errors import (
    ApprovedInputError,
    ApprovedInputIntegrityError,
    ApprovedInputPersistenceError,
)
from .event_manifest import approved_input_event_from_json
from .lifecycle import derive_approved_input_authority_states
from .manifest import approved_input_manifest_from_json
from .paths import (
    APPROVED_INPUT_EVENTS_DIRECTORY_NAME,
    APPROVED_INPUT_MANIFESTS_DIRECTORY_NAME,
    approved_input_events_path,
    approved_input_manifests_path,
    approved_inputs_path,
)
from .types import (
    ApprovedInputEvent,
    ApprovedInputManifest,
    ApprovedInputRepositoryIssue,
    ApprovedInputRepositoryScanResult,
)


_MANIFEST_FILE_PATTERN = re.compile(
    r"^(AIN-[0-9]{6})\.json$"
)
_TEMP_MANIFEST_FILE_PATTERN = re.compile(
    r"^\.(AIN-[0-9]{6})\.json\.tmp$"
)
_EVENT_DIRECTORY_PATTERN = re.compile(
    r"^(AIN-[0-9]{6})$"
)
_EVENT_FILE_PATTERN = re.compile(
    r"^(AIE-[0-9]{6})\.json$"
)
_TEMP_EVENT_FILE_PATTERN = re.compile(
    r"^\.(AIE-[0-9]{6})\.json\.tmp$"
)
_REQUIRED_REPOSITORY_ENTRIES = frozenset(
    {
        APPROVED_INPUT_MANIFESTS_DIRECTORY_NAME,
        APPROVED_INPUT_EVENTS_DIRECTORY_NAME,
    }
)


def scan_approved_input_repository(
    root: Path | str,
    project_id: str,
) -> ApprovedInputRepositoryScanResult:
    """Discover valid manifests and explicit repository issues."""

    root = Path(root)
    manifests: list[ApprovedInputManifest] = []
    events: list[ApprovedInputEvent] = []
    issues: list[ApprovedInputRepositoryIssue] = []
    repository_root = approved_inputs_path(root, project_id)

    if not repository_root.exists() and not repository_root.is_symlink():
        return ApprovedInputRepositoryScanResult()

    if repository_root.is_symlink() or not repository_root.is_dir():
        return ApprovedInputRepositoryScanResult(
            issues=(
                _issue(
                    project_id,
                    code="unsafe_approved_input_path",
                    message=(
                        "Approved Input repository root must be a "
                        "regular directory."
                    ),
                    path=repository_root,
                ),
            )
        )

    try:
        root_entries = tuple(repository_root.iterdir())
    except OSError as exc:
        raise ApprovedInputPersistenceError(
            "Unable to inspect Approved Input repository root "
            f"{repository_root}: {exc}"
        ) from exc

    for entry in root_entries:
        if entry.is_symlink():
            issues.append(
                _issue(
                    project_id,
                    code="unsafe_approved_input_path",
                    message=(
                        "Symbolic-link entries are rejected in the "
                        "Approved Input repository root."
                    ),
                    path=entry,
                )
            )
            continue

        if entry.name not in _REQUIRED_REPOSITORY_ENTRIES:
            issues.append(
                _issue(
                    project_id,
                    code="unexpected_approved_input_repository_entry",
                    message=(
                        "Unexpected entry in Approved Input repository "
                        "root."
                    ),
                    path=entry,
                )
            )

    manifests_root = approved_input_manifests_path(root, project_id)
    events_root = approved_input_events_path(root, project_id)

    _scan_required_directory(
        project_id,
        manifests_root,
        label="Approved Input manifests directory",
        issues=issues,
    )
    _scan_required_directory(
        project_id,
        events_root,
        label="Approved Input events directory",
        issues=issues,
    )

    if (
        manifests_root.exists()
        and manifests_root.is_dir()
        and not manifests_root.is_symlink()
    ):
        _scan_manifests(
            project_id,
            manifests_root,
            manifests,
            issues,
        )

    if (
        events_root.exists()
        and events_root.is_dir()
        and not events_root.is_symlink()
    ):
        _scan_event_directories(
            project_id,
            events_root,
            manifests,
            events,
            issues,
        )

    manifests.sort(key=lambda item: item.approved_input_id)
    events.sort(key=lambda item: item.approved_input_event_id)

    if not issues:
        try:
            derive_approved_input_authority_states(
                tuple(manifests),
                tuple(events),
            )
        except ApprovedInputError as exc:
            issues.append(
                _issue(
                    project_id,
                    code="invalid_approved_input_lifecycle",
                    message=str(exc),
                    path=events_root,
                )
            )

    issues.sort(
        key=lambda issue: (
            str(issue.path or ""),
            issue.code,
            issue.approved_input_id or "",
            issue.approved_input_event_id or "",
            issue.message,
        )
    )

    return ApprovedInputRepositoryScanResult(
        manifests=tuple(manifests),
        events=tuple(events),
        issues=tuple(issues),
    )


def _scan_manifests(
    project_id: str,
    manifests_root: Path,
    manifests: list[ApprovedInputManifest],
    issues: list[ApprovedInputRepositoryIssue],
) -> None:
    try:
        entries = tuple(manifests_root.iterdir())
    except OSError as exc:
        raise ApprovedInputPersistenceError(
            "Unable to inspect Approved Input manifests directory "
            f"{manifests_root}: {exc}"
        ) from exc

    for entry in entries:
        if entry.is_symlink():
            issues.append(
                _issue(
                    project_id,
                    code="unsafe_approved_input_path",
                    message=(
                        "Symbolic-link Approved Input Manifest entries "
                        "are rejected."
                    ),
                    path=entry,
                    approved_input_id=_id_from_entry_name(entry.name),
                )
            )
            continue

        temporary_match = _TEMP_MANIFEST_FILE_PATTERN.fullmatch(
            entry.name
        )
        if temporary_match is not None:
            issues.append(
                _issue(
                    project_id,
                    code="approved_input_persistence_interrupted",
                    message=(
                        "Temporary Approved Input Manifest state "
                        "requires recovery."
                    ),
                    path=entry,
                    approved_input_id=temporary_match.group(1),
                )
            )
            continue

        manifest_match = _MANIFEST_FILE_PATTERN.fullmatch(entry.name)
        if manifest_match is None or not entry.is_file():
            issues.append(
                _issue(
                    project_id,
                    code="unexpected_approved_input_manifest_entry",
                    message=(
                        "Unexpected entry in Approved Input manifests "
                        "directory."
                    ),
                    path=entry,
                    approved_input_id=_id_from_entry_name(entry.name),
                )
            )
            continue

        approved_input_id = manifest_match.group(1)

        try:
            manifest = _load_scanned_manifest(
                entry,
                expected_project_id=project_id,
                expected_approved_input_id=approved_input_id,
            )
        except ApprovedInputError as exc:
            issues.append(
                _issue(
                    project_id,
                    code="invalid_approved_input_manifest",
                    message=str(exc),
                    path=entry,
                    approved_input_id=approved_input_id,
                )
            )
            continue

        manifests.append(manifest)


def _load_scanned_manifest(
    path: Path,
    *,
    expected_project_id: str,
    expected_approved_input_id: str,
) -> ApprovedInputManifest:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise ApprovedInputIntegrityError(
            "Approved Input Manifest is not valid UTF-8."
        ) from exc
    except OSError as exc:
        raise ApprovedInputPersistenceError(
            f"Unable to read Approved Input Manifest {path}: {exc}"
        ) from exc

    manifest = approved_input_manifest_from_json(text)

    if manifest.project_id != expected_project_id:
        raise ApprovedInputIntegrityError(
            "Approved Input Manifest project_id does not match its "
            "Project directory."
        )

    if manifest.approved_input_id != expected_approved_input_id:
        raise ApprovedInputIntegrityError(
            "Approved Input Manifest ID does not match its filename."
        )

    return manifest


def _scan_event_directories(
    project_id: str,
    events_root: Path,
    manifests: list[ApprovedInputManifest],
    events: list[ApprovedInputEvent],
    issues: list[ApprovedInputRepositoryIssue],
) -> None:
    """Validate AIN event directories and immutable AIE files."""

    manifest_ids = {
        manifest.approved_input_id for manifest in manifests
    }
    seen_event_ids: set[str] = set()

    try:
        entries = tuple(events_root.iterdir())
    except OSError as exc:
        raise ApprovedInputPersistenceError(
            "Unable to inspect Approved Input events directory "
            f"{events_root}: {exc}"
        ) from exc

    for entry in entries:
        match = _EVENT_DIRECTORY_PATTERN.fullmatch(entry.name)
        if entry.is_symlink() or match is None or not entry.is_dir():
            issues.append(
                _issue(
                    project_id,
                    code="unexpected_approved_input_event_entry",
                    message=(
                        "Approved Input event root may contain only "
                        "regular AIN-named directories."
                    ),
                    path=entry,
                    approved_input_id=(
                        match.group(1) if match is not None else None
                    ),
                )
            )
            continue

        approved_input_id = match.group(1)
        if approved_input_id not in manifest_ids:
            issues.append(
                _issue(
                    project_id,
                    code="orphan_approved_input_event_directory",
                    message=(
                        "Approved Input event directory has no "
                        "corresponding manifest."
                    ),
                    path=entry,
                    approved_input_id=approved_input_id,
                )
            )
            continue

        _scan_event_files(
            project_id,
            approved_input_id,
            entry,
            events,
            seen_event_ids,
            issues,
        )


def _scan_event_files(
    project_id: str,
    approved_input_id: str,
    directory: Path,
    events: list[ApprovedInputEvent],
    seen_event_ids: set[str],
    issues: list[ApprovedInputRepositoryIssue],
) -> None:
    try:
        entries = tuple(directory.iterdir())
    except OSError as exc:
        raise ApprovedInputPersistenceError(
            "Unable to inspect Approved Input event directory "
            f"{directory}: {exc}"
        ) from exc

    for entry in entries:
        if entry.is_symlink():
            issues.append(
                _issue(
                    project_id,
                    code="unsafe_approved_input_path",
                    message=(
                        "Symbolic-link Approved Input Event entries "
                        "are rejected."
                    ),
                    path=entry,
                    approved_input_id=approved_input_id,
                )
            )
            continue

        temporary_match = _TEMP_EVENT_FILE_PATTERN.fullmatch(
            entry.name
        )
        if temporary_match is not None:
            issues.append(
                _issue(
                    project_id,
                    code=(
                        "approved_input_event_persistence_interrupted"
                    ),
                    message=(
                        "Temporary Approved Input Event state "
                        "requires recovery."
                    ),
                    path=entry,
                    approved_input_id=approved_input_id,
                    approved_input_event_id=(
                        temporary_match.group(1)
                    ),
                )
            )
            continue

        event_match = _EVENT_FILE_PATTERN.fullmatch(entry.name)
        if event_match is None or not entry.is_file():
            issues.append(
                _issue(
                    project_id,
                    code="unexpected_approved_input_event_file",
                    message=(
                        "Unexpected entry in Approved Input event "
                        "directory."
                    ),
                    path=entry,
                    approved_input_id=approved_input_id,
                )
            )
            continue

        event_id = event_match.group(1)
        if event_id in seen_event_ids:
            issues.append(
                _issue(
                    project_id,
                    code="duplicate_approved_input_event_id",
                    message=(
                        "Approved Input Event IDs must be project-wide "
                        "unique."
                    ),
                    path=entry,
                    approved_input_id=approved_input_id,
                    approved_input_event_id=event_id,
                )
            )
            continue

        try:
            event = _load_scanned_event(
                entry,
                expected_project_id=project_id,
                expected_approved_input_id=approved_input_id,
                expected_event_id=event_id,
            )
        except ApprovedInputError as exc:
            issues.append(
                _issue(
                    project_id,
                    code="invalid_approved_input_event",
                    message=str(exc),
                    path=entry,
                    approved_input_id=approved_input_id,
                    approved_input_event_id=event_id,
                )
            )
            continue

        seen_event_ids.add(event_id)
        events.append(event)


def _load_scanned_event(
    path: Path,
    *,
    expected_project_id: str,
    expected_approved_input_id: str,
    expected_event_id: str,
) -> ApprovedInputEvent:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise ApprovedInputIntegrityError(
            "Approved Input Event is not valid UTF-8."
        ) from exc
    except OSError as exc:
        raise ApprovedInputPersistenceError(
            f"Unable to read Approved Input Event {path}: {exc}"
        ) from exc

    event = approved_input_event_from_json(text)
    if event.project_id != expected_project_id:
        raise ApprovedInputIntegrityError(
            "Approved Input Event project_id does not match path."
        )
    if event.approved_input_id != expected_approved_input_id:
        raise ApprovedInputIntegrityError(
            "Approved Input Event does not match its AIN directory."
        )
    if event.approved_input_event_id != expected_event_id:
        raise ApprovedInputIntegrityError(
            "Approved Input Event ID does not match its filename."
        )
    return event

def _scan_required_directory(
    project_id: str,
    path: Path,
    *,
    label: str,
    issues: list[ApprovedInputRepositoryIssue],
) -> None:
    if path.is_symlink():
        issues.append(
            _issue(
                project_id,
                code="unsafe_approved_input_path",
                message=f"Symbolic-link {label} is rejected.",
                path=path,
            )
        )
        return

    if not path.exists() or not path.is_dir():
        issues.append(
            _issue(
                project_id,
                code="approved_input_repository_incomplete",
                message=f"Required {label} is missing.",
                path=path,
            )
        )


def _issue(
    project_id: str,
    *,
    code: str,
    message: str,
    path: Path | None,
    approved_input_id: str | None = None,
    approved_input_event_id: str | None = None,
) -> ApprovedInputRepositoryIssue:
    return ApprovedInputRepositoryIssue(
        project_id=project_id,
        code=code,
        message=message,
        issue_level="blocking",
        path=path,
        approved_input_id=approved_input_id,
        approved_input_event_id=approved_input_event_id,
    )


def _id_from_entry_name(name: str) -> str | None:
    manifest_match = _MANIFEST_FILE_PATTERN.fullmatch(name)
    if manifest_match is not None:
        return manifest_match.group(1)

    temporary_match = _TEMP_MANIFEST_FILE_PATTERN.fullmatch(name)
    if temporary_match is not None:
        return temporary_match.group(1)

    return None
