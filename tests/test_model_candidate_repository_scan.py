"""Tests for deterministic Phase-H Candidate repository scanning."""

from datetime import datetime, timezone
from pathlib import Path

from modules.model_candidates import (
    ModelCandidateRepository,
)
from modules.project_workspace import ProjectWorkspace


def _clock():
    return datetime(2026, 8, 13, 6, 30, tzinfo=timezone.utc)


def _create_project(root: Path):
    workspace = ProjectWorkspace(
        root=root,
        id_generator=lambda: "000042",
        clock=_clock,
    )
    workspace.create_project("Scan Test")


def test_missing_repository_is_clean_empty_state(tmp_path):
    _create_project(tmp_path)
    repository = ModelCandidateRepository(root=tmp_path)

    result = repository.scan_project("000042")
    assert result.candidate_sets == ()
    assert result.issues == ()


def test_existing_repository_requires_sets_directory(tmp_path):
    _create_project(tmp_path)
    repository_root = (
        tmp_path / "000042" / "model_candidates"
    )
    repository_root.mkdir()

    result = ModelCandidateRepository(
        root=tmp_path
    ).scan_project("000042")
    assert tuple(issue.code for issue in result.issues) == (
        "model_candidate_repository_incomplete",
    )


def test_unexpected_repository_entry_is_reported(tmp_path):
    _create_project(tmp_path)
    repository_root = (
        tmp_path / "000042" / "model_candidates"
    )
    sets_root = repository_root / "sets"
    sets_root.mkdir(parents=True)
    (repository_root / "junk.txt").write_text(
        "junk",
        encoding="utf-8",
    )

    result = ModelCandidateRepository(
        root=tmp_path
    ).scan_project("000042")
    assert "unexpected_model_candidate_repository_entry" in {
        issue.code for issue in result.issues
    }


def test_unexpected_set_entry_is_reported(tmp_path):
    _create_project(tmp_path)
    sets_root = (
        tmp_path
        / "000042"
        / "model_candidates"
        / "sets"
    )
    sets_root.mkdir(parents=True)
    (sets_root / "not-a-set").mkdir()

    result = ModelCandidateRepository(
        root=tmp_path
    ).scan_project("000042")
    assert tuple(issue.code for issue in result.issues) == (
        "unexpected_model_candidate_set_entry",
    )
