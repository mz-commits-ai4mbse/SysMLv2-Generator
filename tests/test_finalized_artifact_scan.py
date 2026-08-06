"""Tests for finalized Review Artifact Set scan integration."""

from __future__ import annotations

from pathlib import Path

from modules.review_workspace.paths import (
    finalized_review_path,
    reviewed_report_path,
)

from tests.test_finalized_artifact_loading import (
    _persisted_artifact_set,
)
from tests.test_finalized_artifact_persistence import (
    _prepared_artifact_persistence,
    _temporary_directory,
)


def _issue_codes(result) -> tuple[str, ...]:
    return tuple(
        issue.code
        for issue in result.issues
    )


def test_valid_finalized_artifact_set_scans_cleanly(
    tmp_path: Path,
) -> None:
    _, repository, _ = (
        _persisted_artifact_set(tmp_path)
    )

    result = repository.scan_project("000001")

    assert result.issues == ()
    assert len(result.documents) == 1
    assert len(result.versions) == 1
    assert len(result.revisions) == 1


def test_finalized_version_without_artifacts_is_reported(
    tmp_path: Path,
) -> None:
    _, repository, _ = (
        _prepared_artifact_persistence(tmp_path)
    )

    result = repository.scan_project("000001")

    assert _issue_codes(result) == (
        "missing_finalized_artifact_set",
    )
    issue = result.issues[0]
    assert issue.review_document_id == "RVD-000001"
    assert (
        issue.review_document_version_id
        == "RVV-000001"
    )
    assert issue.review_revision_id == "RVR-000001"


def test_draft_version_without_artifacts_scans_cleanly(
    tmp_path: Path,
) -> None:
    _, repository, _ = (
        _prepared_artifact_persistence(
            tmp_path,
            persist_version=False,
        )
    )

    result = repository.scan_project("000001")

    assert result.issues == ()


def test_draft_version_with_finalized_directory_is_reported(
    tmp_path: Path,
) -> None:
    root, repository, _ = (
        _prepared_artifact_persistence(
            tmp_path,
            persist_version=False,
        )
    )
    finalized_review_path(
        root,
        "000001",
        "RVD-000001",
        "RVV-000001",
    ).mkdir()

    result = repository.scan_project("000001")

    assert _issue_codes(result) == (
        "unexpected_finalized_artifact_set",
    )


def test_interrupted_finalized_persistence_is_reported(
    tmp_path: Path,
) -> None:
    root, repository, _ = (
        _prepared_artifact_persistence(tmp_path)
    )
    temporary = _temporary_directory(root)
    temporary.mkdir()
    partial = temporary / "reviewed_document.json"
    partial.write_bytes(b"partial")

    result = repository.scan_project("000001")

    assert _issue_codes(result) == (
        "interrupted_finalized_artifact_persistence",
    )
    assert result.issues[0].path == temporary
    assert temporary.is_dir()
    assert partial.read_bytes() == b"partial"


def test_regular_file_finalized_path_is_reported(
    tmp_path: Path,
) -> None:
    root, repository, _ = (
        _prepared_artifact_persistence(tmp_path)
    )
    path = finalized_review_path(
        root,
        "000001",
        "RVD-000001",
        "RVV-000001",
    )
    path.write_bytes(b"occupied")

    result = repository.scan_project("000001")

    assert _issue_codes(result) == (
        "unsafe_finalized_artifact_path",
    )
    assert path.read_bytes() == b"occupied"


def test_symbolic_link_finalized_path_is_reported(
    tmp_path: Path,
) -> None:
    root, repository, _ = (
        _prepared_artifact_persistence(tmp_path)
    )
    outside = tmp_path / "outside-finalized"
    outside.mkdir()
    path = finalized_review_path(
        root,
        "000001",
        "RVD-000001",
        "RVV-000001",
    )
    path.symlink_to(
        outside,
        target_is_directory=True,
    )

    result = repository.scan_project("000001")

    assert _issue_codes(result) == (
        "unsafe_finalized_artifact_path",
    )
    assert path.is_symlink()
    assert outside.is_dir()


def test_tampered_finalized_artifact_set_is_reported(
    tmp_path: Path,
) -> None:
    root, repository, _ = (
        _persisted_artifact_set(tmp_path)
    )
    path = reviewed_report_path(
        root,
        "000001",
        "RVD-000001",
        "RVV-000001",
    )
    path.write_text(
        path.read_text(encoding="utf-8")
        + "\nTampered\n",
        encoding="utf-8",
    )

    result = repository.scan_project("000001")

    assert _issue_codes(result) == (
        "invalid_finalized_artifact_set",
    )


def test_unexpected_fourth_finalized_artifact_is_reported(
    tmp_path: Path,
) -> None:
    root, repository, _ = (
        _persisted_artifact_set(tmp_path)
    )
    path = (
        finalized_review_path(
            root,
            "000001",
            "RVD-000001",
            "RVV-000001",
        )
        / "artifact_set.json"
    )
    path.write_text(
        "{}\n",
        encoding="utf-8",
    )

    result = repository.scan_project("000001")

    assert _issue_codes(result) == (
        "invalid_finalized_artifact_set",
    )
    assert path.read_text(encoding="utf-8") == "{}\n"


def test_scan_does_not_modify_valid_finalized_artifacts(
    tmp_path: Path,
) -> None:
    root, repository, artifact_set = (
        _persisted_artifact_set(tmp_path)
    )
    directory = finalized_review_path(
        root,
        "000001",
        "RVD-000001",
        "RVV-000001",
    )
    before = {
        path.name: path.read_bytes()
        for path in directory.iterdir()
    }

    result = repository.scan_project("000001")

    after = {
        path.name: path.read_bytes()
        for path in directory.iterdir()
    }

    assert result.issues == ()
    assert before == after
    assert before == {
        artifact.filename: artifact.content
        for artifact in artifact_set.artifacts
    }
