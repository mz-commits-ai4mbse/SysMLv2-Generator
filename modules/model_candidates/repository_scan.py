"""Deterministic diagnostics for Model Candidate persistence."""

from __future__ import annotations

from pathlib import Path
import re

from .errors import (
    ModelCandidateError,
    ModelCandidatePersistenceError,
)
from .paths import (
    MODEL_CANDIDATE_SETS_DIRECTORY_NAME,
    model_candidate_sets_path,
    model_candidates_path,
)
from .types import (
    ModelCandidateRepositoryIssue,
    ModelCandidateRepositoryScanResult,
    ModelCandidateSetSnapshot,
)


_CANDIDATE_SET_DIRECTORY_PATTERN = re.compile(
    r"^(MCS-[0-9]{6})$"
)
_TEMP_CANDIDATE_SET_PATTERN = re.compile(
    r"^\.create-(MCS-[0-9]{6})\.tmp$"
)
_REQUIRED_REPOSITORY_ENTRIES = frozenset(
    {MODEL_CANDIDATE_SETS_DIRECTORY_NAME}
)


def scan_model_candidate_repository(
    repository,
    project_id: str,
) -> ModelCandidateRepositoryScanResult:
    """Discover valid Candidate Sets and explicit blocking issues."""

    root = Path(repository.root)
    repository_root = model_candidates_path(root, project_id)
    sets_root = model_candidate_sets_path(root, project_id)
    snapshots: list[ModelCandidateSetSnapshot] = []
    issues: list[ModelCandidateRepositoryIssue] = []

    if (
        not repository_root.exists()
        and not repository_root.is_symlink()
    ):
        return ModelCandidateRepositoryScanResult()

    if (
        repository_root.is_symlink()
        or not repository_root.is_dir()
    ):
        return ModelCandidateRepositoryScanResult(
            issues=(
                _issue(
                    project_id,
                    code="unsafe_model_candidate_path",
                    message=(
                        "Model Candidate repository root must be a "
                        "regular directory."
                    ),
                    path=repository_root,
                ),
            )
        )

    try:
        root_entries = tuple(
            sorted(repository_root.iterdir(), key=lambda item: item.name)
        )
    except OSError as exc:
        raise ModelCandidatePersistenceError(
            "Unable to inspect Model Candidate repository root "
            f"{repository_root}: {exc}"
        ) from exc

    for entry in root_entries:
        if entry.is_symlink():
            issues.append(
                _issue(
                    project_id,
                    code="unsafe_model_candidate_path",
                    message=(
                        "Symbolic-link entries are rejected in the "
                        "Model Candidate repository root."
                    ),
                    path=entry,
                )
            )
            continue
        if entry.name not in _REQUIRED_REPOSITORY_ENTRIES:
            issues.append(
                _issue(
                    project_id,
                    code="unexpected_model_candidate_repository_entry",
                    message=(
                        "Unexpected entry in Model Candidate repository "
                        "root."
                    ),
                    path=entry,
                )
            )

    if sets_root.is_symlink():
        issues.append(
            _issue(
                project_id,
                code="unsafe_model_candidate_path",
                message="Symbolic-link Candidate Set root is rejected.",
                path=sets_root,
            )
        )
    elif not sets_root.exists() or not sets_root.is_dir():
        issues.append(
            _issue(
                project_id,
                code="model_candidate_repository_incomplete",
                message="Required Candidate Set root is missing.",
                path=sets_root,
            )
        )
    else:
        _scan_candidate_sets(
            repository,
            project_id,
            sets_root,
            snapshots,
            issues,
        )

    _detect_project_wide_duplicate_ids(
        project_id,
        snapshots,
        issues,
    )

    snapshots.sort(
        key=lambda item: item.manifest.candidate_set_id
    )
    issues.sort(
        key=lambda issue: (
            str(issue.path or ""),
            issue.code,
            issue.candidate_set_id or "",
            issue.model_element_candidate_id or "",
            issue.model_relationship_candidate_id or "",
            issue.message,
        )
    )
    return ModelCandidateRepositoryScanResult(
        candidate_sets=tuple(snapshots),
        issues=tuple(issues),
    )


def _scan_candidate_sets(
    repository,
    project_id: str,
    sets_root: Path,
    snapshots: list[ModelCandidateSetSnapshot],
    issues: list[ModelCandidateRepositoryIssue],
) -> None:
    try:
        entries = tuple(
            sorted(sets_root.iterdir(), key=lambda item: item.name)
        )
    except OSError as exc:
        raise ModelCandidatePersistenceError(
            f"Unable to inspect Candidate Set root {sets_root}: {exc}"
        ) from exc

    for entry in entries:
        temp_match = _TEMP_CANDIDATE_SET_PATTERN.fullmatch(
            entry.name
        )
        if temp_match is not None:
            issues.append(
                _issue(
                    project_id,
                    code="model_candidate_persistence_interrupted",
                    message=(
                        "Temporary Candidate Set state requires "
                        "explicit recovery."
                    ),
                    path=entry,
                    candidate_set_id=temp_match.group(1),
                )
            )
            continue

        match = _CANDIDATE_SET_DIRECTORY_PATTERN.fullmatch(
            entry.name
        )
        if (
            entry.is_symlink()
            or match is None
            or not entry.is_dir()
        ):
            issues.append(
                _issue(
                    project_id,
                    code="unexpected_model_candidate_set_entry",
                    message=(
                        "Candidate Set root may contain only regular "
                        "MCS-named directories."
                    ),
                    path=entry,
                    candidate_set_id=(
                        match.group(1) if match is not None else None
                    ),
                )
            )
            continue

        candidate_set_id = match.group(1)
        try:
            snapshot = repository._load_snapshot_from_directory(
                project_id,
                candidate_set_id,
                entry,
            )
        except (ModelCandidateError, OSError, UnicodeError) as exc:
            issues.append(
                _issue(
                    project_id,
                    code="invalid_model_candidate_set",
                    message=str(exc),
                    path=entry,
                    candidate_set_id=candidate_set_id,
                )
            )
            continue
        snapshots.append(snapshot)


def _detect_project_wide_duplicate_ids(
    project_id: str,
    snapshots: list[ModelCandidateSetSnapshot],
    issues: list[ModelCandidateRepositoryIssue],
) -> None:
    element_locations: dict[str, tuple[str, Path]] = {}
    relationship_locations: dict[str, tuple[str, Path]] = {}

    for snapshot in snapshots:
        set_id = snapshot.manifest.candidate_set_id
        set_path = Path(
            next(
                (
                    issue.path
                    for issue in issues
                    if issue.candidate_set_id == set_id
                    and issue.path is not None
                ),
                "",
            )
        )

        for candidate in snapshot.element_candidates:
            candidate_id = candidate.model_element_candidate_id
            previous = element_locations.get(candidate_id)
            if previous is None:
                element_locations[candidate_id] = (
                    set_id,
                    set_path,
                )
                continue
            issues.append(
                _issue(
                    project_id,
                    code="duplicate_model_element_candidate_id",
                    message=(
                        "Model Element Candidate IDs must be "
                        "project-local unique across Candidate Sets; "
                        f"{candidate_id} occurs in {previous[0]} "
                        f"and {set_id}."
                    ),
                    path=None,
                    candidate_set_id=set_id,
                    model_element_candidate_id=candidate_id,
                )
            )

        for candidate in snapshot.relationship_candidates:
            candidate_id = candidate.model_relationship_candidate_id
            previous = relationship_locations.get(candidate_id)
            if previous is None:
                relationship_locations[candidate_id] = (
                    set_id,
                    set_path,
                )
                continue
            issues.append(
                _issue(
                    project_id,
                    code="duplicate_model_relationship_candidate_id",
                    message=(
                        "Model Relationship Candidate IDs must be "
                        "project-local unique across Candidate Sets; "
                        f"{candidate_id} occurs in {previous[0]} "
                        f"and {set_id}."
                    ),
                    path=None,
                    candidate_set_id=set_id,
                    model_relationship_candidate_id=candidate_id,
                )
            )


def _issue(
    project_id: str,
    *,
    code: str,
    message: str,
    path: Path | None,
    candidate_set_id: str | None = None,
    model_element_candidate_id: str | None = None,
    model_relationship_candidate_id: str | None = None,
) -> ModelCandidateRepositoryIssue:
    return ModelCandidateRepositoryIssue(
        project_id=project_id,
        code=code,
        message=message,
        issue_level="blocking",
        path=path,
        candidate_set_id=candidate_set_id,
        model_element_candidate_id=model_element_candidate_id,
        model_relationship_candidate_id=(
            model_relationship_candidate_id
        ),
    )
