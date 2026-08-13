"""Deterministic diagnostics for Internal Engineering Model persistence."""

from __future__ import annotations

from pathlib import Path
import re

from .errors import InternalModelError, InternalModelPersistenceError
from .paths import internal_models_path
from .repository_types import (
    InternalModelRepositoryIssue,
    InternalModelRepositoryScanResult,
)
from .types import InternalEngineeringModelSnapshot


_IEM_DIRECTORY_PATTERN = re.compile(r"^(IEM-[0-9]{6})$")
_TEMP_IEM_PATTERN = re.compile(r"^\.create-(IEM-[0-9]{6})\.tmp$")


def scan_internal_model_repository(
    repository,
    project_id: str,
) -> InternalModelRepositoryScanResult:
    """Discover valid IEM snapshots and explicit blocking issues."""

    root = Path(repository.root)
    repository_root = internal_models_path(root, project_id)
    snapshots: list[InternalEngineeringModelSnapshot] = []
    issues: list[InternalModelRepositoryIssue] = []

    if (
        not repository_root.exists()
        and not repository_root.is_symlink()
    ):
        return InternalModelRepositoryScanResult()

    if (
        repository_root.is_symlink()
        or not repository_root.is_dir()
    ):
        return InternalModelRepositoryScanResult(
            issues=(
                _issue(
                    project_id,
                    code="unsafe_internal_model_path",
                    message=(
                        "Internal Model repository root must be a "
                        "regular directory."
                    ),
                    path=repository_root,
                ),
            )
        )

    try:
        entries = tuple(
            sorted(repository_root.iterdir(), key=lambda item: item.name)
        )
    except OSError as exc:
        raise InternalModelPersistenceError(
            "Unable to inspect Internal Model repository root "
            f"{repository_root}: {exc}"
        ) from exc

    for entry in entries:
        temp_match = _TEMP_IEM_PATTERN.fullmatch(entry.name)
        if temp_match is not None:
            issues.append(
                _issue(
                    project_id,
                    code="internal_model_persistence_interrupted",
                    message=(
                        "Temporary IEM publication state requires "
                        "explicit recovery."
                    ),
                    path=entry,
                    internal_engineering_model_id=temp_match.group(1),
                )
            )
            continue

        match = _IEM_DIRECTORY_PATTERN.fullmatch(entry.name)
        if (
            entry.is_symlink()
            or match is None
            or not entry.is_dir()
        ):
            issues.append(
                _issue(
                    project_id,
                    code="unexpected_internal_model_repository_entry",
                    message=(
                        "Internal Model repository may contain only "
                        "regular IEM-named directories."
                    ),
                    path=entry,
                    internal_engineering_model_id=(
                        match.group(1) if match is not None else None
                    ),
                )
            )
            continue

        iem_id = match.group(1)
        try:
            snapshot = repository._load_snapshot_from_directory(
                project_id,
                iem_id,
                entry,
            )
        except (InternalModelError, OSError, UnicodeError) as exc:
            issues.append(
                _issue(
                    project_id,
                    code="invalid_internal_engineering_model",
                    message=str(exc),
                    path=entry,
                    internal_engineering_model_id=iem_id,
                )
            )
            continue
        snapshots.append(snapshot)

    _detect_project_wide_duplicate_ids(
        project_id,
        snapshots,
        issues,
    )
    _detect_duplicate_assembly_identity(
        project_id,
        snapshots,
        issues,
    )

    snapshots.sort(
        key=lambda item: item.manifest.internal_engineering_model_id
    )
    issues.sort(
        key=lambda issue: (
            str(issue.path or ""),
            issue.code,
            issue.internal_engineering_model_id or "",
            issue.internal_model_element_id or "",
            issue.internal_model_relationship_id or "",
            issue.message,
        )
    )
    return InternalModelRepositoryScanResult(
        snapshots=tuple(snapshots),
        issues=tuple(issues),
    )


def _detect_project_wide_duplicate_ids(
    project_id: str,
    snapshots: list[InternalEngineeringModelSnapshot],
    issues: list[InternalModelRepositoryIssue],
) -> None:
    element_locations: dict[str, str] = {}
    relationship_locations: dict[str, str] = {}

    for snapshot in snapshots:
        iem_id = snapshot.manifest.internal_engineering_model_id

        for element in snapshot.elements:
            internal_id = element.internal_model_element_id
            previous = element_locations.get(internal_id)
            if previous is None:
                element_locations[internal_id] = iem_id
                continue
            issues.append(
                _issue(
                    project_id,
                    code="duplicate_internal_model_element_id",
                    message=(
                        "IME IDs must be project-local unique across "
                        f"IEM snapshots; {internal_id} occurs in "
                        f"{previous} and {iem_id}."
                    ),
                    path=None,
                    internal_engineering_model_id=iem_id,
                    internal_model_element_id=internal_id,
                )
            )

        for relationship in snapshot.relationships:
            internal_id = relationship.internal_model_relationship_id
            previous = relationship_locations.get(internal_id)
            if previous is None:
                relationship_locations[internal_id] = iem_id
                continue
            issues.append(
                _issue(
                    project_id,
                    code="duplicate_internal_model_relationship_id",
                    message=(
                        "IMR IDs must be project-local unique across "
                        f"IEM snapshots; {internal_id} occurs in "
                        f"{previous} and {iem_id}."
                    ),
                    path=None,
                    internal_engineering_model_id=iem_id,
                    internal_model_relationship_id=internal_id,
                )
            )



def _detect_duplicate_assembly_identity(
    project_id: str,
    snapshots: list[InternalEngineeringModelSnapshot],
    issues: list[InternalModelRepositoryIssue],
) -> None:
    identities: dict[tuple[str, str, str, str], str] = {}

    for snapshot in snapshots:
        manifest = snapshot.manifest
        rules = manifest.assembly_context.assembly_rules_reference
        key = (
            manifest.assembly_input_fingerprint,
            rules.rules_id,
            rules.rules_version,
            rules.rules_fingerprint,
        )
        previous = identities.get(key)
        if previous is None:
            identities[key] = manifest.internal_engineering_model_id
            continue

        issues.append(
            _issue(
                project_id,
                code="duplicate_internal_model_assembly_identity",
                message=(
                    "Exact assembly input plus assembly rules must be "
                    "idempotent; duplicate snapshots occur in "
                    f"{previous} and "
                    f"{manifest.internal_engineering_model_id}."
                ),
                path=None,
                internal_engineering_model_id=(
                    manifest.internal_engineering_model_id
                ),
            )
        )

def _issue(
    project_id: str,
    *,
    code: str,
    message: str,
    path: Path | None,
    internal_engineering_model_id: str | None = None,
    internal_model_element_id: str | None = None,
    internal_model_relationship_id: str | None = None,
) -> InternalModelRepositoryIssue:
    return InternalModelRepositoryIssue(
        project_id=project_id,
        code=code,
        message=message,
        issue_level="blocking",
        path=path,
        internal_engineering_model_id=internal_engineering_model_id,
        internal_model_element_id=internal_model_element_id,
        internal_model_relationship_id=internal_model_relationship_id,
    )
