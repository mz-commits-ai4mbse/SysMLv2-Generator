"""Tests for atomic Review Document Version reopening."""

from __future__ import annotations

from pathlib import Path

import pytest

from modules.review_workspace.errors import (
    InvalidReviewVersionTransitionError,
    ReviewIntegrityError,
    ReviewRecoveryRequiredError,
)
from modules.review_workspace.paths import (
    FINALIZED_DIRECTORY_NAME,
    REVISIONS_DIRECTORY_NAME,
    SCOPED_ACTIONS_DIRECTORY_NAME,
    finalized_review_path,
    review_document_version_path,
)
from modules.review_workspace.version_manifest import (
    REVIEW_DOCUMENT_VERSION_MANIFEST_FILENAME,
)

from tests.test_finalized_artifact_loading import (
    _persisted_artifact_set,
)
from tests.test_finalized_artifact_persistence import (
    _prepared_artifact_persistence,
)


def _reopen(repository):
    return repository.reopen_finalized_version(
        "000001",
        "RVD-000001",
        "RVV-000001",
        reopen_reason=(
            "Clarify the finalized engineering statement."
        ),
        opened_by="reviewer@example.com",
        timestamp="2026-08-06T18:30:00Z",
    )


def test_reopening_persists_exact_successor_workspace(
    tmp_path: Path,
) -> None:
    root, repository, _ = (
        _persisted_artifact_set(tmp_path)
    )

    bundle = _reopen(repository)

    assert (
        bundle.version.review_document_version_id
        == "RVV-000002"
    )
    assert (
        bundle.initial_revision.review_revision_id
        == "RVR-000002"
    )
    assert (
        bundle.review_item_id_mapping
        == (("RIT-000001", "RIT-000002"),)
    )

    directory = review_document_version_path(
        root,
        "000001",
        "RVD-000001",
        "RVV-000002",
    )

    assert tuple(
        sorted(
            entry.name
            for entry in directory.iterdir()
        )
    ) == tuple(
        sorted(
            (
                REVIEW_DOCUMENT_VERSION_MANIFEST_FILENAME,
                REVISIONS_DIRECTORY_NAME,
                SCOPED_ACTIONS_DIRECTORY_NAME,
            )
        )
    )
    assert not (
        directory / FINALIZED_DIRECTORY_NAME
    ).exists()
    assert tuple(
        (
            directory
            / SCOPED_ACTIONS_DIRECTORY_NAME
        ).iterdir()
    ) == ()


def test_predecessor_artifacts_remain_unchanged(
    tmp_path: Path,
) -> None:
    root, repository, artifact_set = (
        _persisted_artifact_set(tmp_path)
    )
    predecessor_directory = finalized_review_path(
        root,
        "000001",
        "RVD-000001",
        "RVV-000001",
    )
    before = {
        path.name: path.read_bytes()
        for path in predecessor_directory.iterdir()
    }

    _reopen(repository)

    after = {
        path.name: path.read_bytes()
        for path in predecessor_directory.iterdir()
    }

    assert before == after
    assert before == {
        artifact.filename: artifact.content
        for artifact in artifact_set.artifacts
    }


def test_reopened_history_scans_cleanly(
    tmp_path: Path,
) -> None:
    _, repository, _ = (
        _persisted_artifact_set(tmp_path)
    )
    _reopen(repository)

    result = repository.scan_project("000001")

    assert result.issues == ()
    assert tuple(
        (
            version.review_document_version_id,
            version.version_state,
        )
        for version in result.versions
    ) == (
        ("RVV-000001", "finalized"),
        ("RVV-000002", "draft"),
    )


def test_old_version_cannot_be_reopened_twice(
    tmp_path: Path,
) -> None:
    root, repository, _ = (
        _persisted_artifact_set(tmp_path)
    )
    _reopen(repository)

    with pytest.raises(
        InvalidReviewVersionTransitionError,
        match="draft successor",
    ):
        _reopen(repository)

    assert not review_document_version_path(
        root,
        "000001",
        "RVD-000001",
        "RVV-000003",
    ).exists()


def test_draft_successor_cannot_be_reopened(
    tmp_path: Path,
) -> None:
    _, repository, _ = (
        _persisted_artifact_set(tmp_path)
    )
    _reopen(repository)

    with pytest.raises(
        InvalidReviewVersionTransitionError,
        match="finalized",
    ):
        repository.reopen_finalized_version(
            "000001",
            "RVD-000001",
            "RVV-000002",
            reopen_reason="Another correction.",
            opened_by="reviewer@example.com",
            timestamp="2026-08-06T19:00:00Z",
        )


def test_interrupted_version_creation_requires_recovery(
    tmp_path: Path,
) -> None:
    root, repository, _ = (
        _persisted_artifact_set(tmp_path)
    )
    temporary = (
        review_document_version_path(
            root,
            "000001",
            "RVD-000001",
            "RVV-000002",
        ).parent
        / ".create-RVV-000002.tmp"
    )
    temporary.mkdir()

    with pytest.raises(
        ReviewRecoveryRequiredError,
        match="explicit recovery",
    ):
        _reopen(repository)

    assert temporary.is_dir()


def test_tampered_predecessor_blocks_reopening(
    tmp_path: Path,
) -> None:
    root, repository, _ = (
        _persisted_artifact_set(tmp_path)
    )
    report = (
        finalized_review_path(
            root,
            "000001",
            "RVD-000001",
            "RVV-000001",
        )
        / "reviewed_report.md"
    )
    report.write_text(
        report.read_text(encoding="utf-8")
        + "\nTampered\n",
        encoding="utf-8",
    )

    with pytest.raises(ReviewIntegrityError):
        _reopen(repository)

    assert not review_document_version_path(
        root,
        "000001",
        "RVD-000001",
        "RVV-000002",
    ).exists()


def test_publish_failure_leaves_recoverable_temp(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, repository, _ = (
        _persisted_artifact_set(tmp_path)
    )
    versions = review_document_version_path(
        root,
        "000001",
        "RVD-000001",
        "RVV-000001",
    ).parent
    temporary = (
        versions / ".create-RVV-000002.tmp"
    )
    final = versions / "RVV-000002"
    original_rename = Path.rename

    def fail_publish(
        source: Path,
        target: Path,
    ):
        if (
            source == temporary
            and Path(target) == final
        ):
            raise OSError(
                "Simulated reopening publish failure."
            )

        return original_rename(source, target)

    monkeypatch.setattr(
        Path,
        "rename",
        fail_publish,
    )

    with pytest.raises(
        ReviewRecoveryRequiredError,
        match="atomically publish",
    ):
        _reopen(repository)

    assert temporary.is_dir()
    assert not final.exists()
    assert (
        temporary
        / REVIEW_DOCUMENT_VERSION_MANIFEST_FILENAME
    ).is_file()
    assert (
        temporary
        / REVISIONS_DIRECTORY_NAME
        / "RVR-000002.json"
    ).is_file()


def test_reopening_does_not_copy_scoped_action_ids(
    tmp_path: Path,
) -> None:
    _, repository, _ = (
        _persisted_artifact_set(tmp_path)
    )

    bundle = _reopen(repository)

    assert (
        bundle.initial_revision
        .scoped_review_action_ids
        == ()
    )


def test_unfinalized_initial_version_is_rejected(
    tmp_path: Path,
) -> None:
    _, repository, _ = (
        _prepared_artifact_persistence(
            tmp_path,
            persist_version=False,
        )
    )

    with pytest.raises(
        InvalidReviewVersionTransitionError,
        match="finalized",
    ):
        repository.reopen_finalized_version(
            "000001",
            "RVD-000001",
            "RVV-000001",
            reopen_reason="Required correction.",
            opened_by="reviewer@example.com",
            timestamp="2026-08-06T18:30:00Z",
        )
