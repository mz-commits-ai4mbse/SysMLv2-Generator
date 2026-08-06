"""Tests for exact finalized Review Artifact Set loading."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from modules.review_workspace.errors import (
    InvalidReviewVersionTransitionError,
    ReviewIntegrityError,
    ReviewRecoveryRequiredError,
    ReviewReferenceError,
    UnsafeReviewWorkspacePathError,
)
from modules.review_workspace.paths import (
    EFFECTIVE_DECISIONS_FILENAME,
    REVIEWED_DOCUMENT_FILENAME,
    REVIEWED_REPORT_FILENAME,
    effective_decisions_path,
    finalized_review_path,
    reviewed_document_path,
    reviewed_report_path,
)
from modules.review_workspace.repository import (
    ReviewWorkspaceRepository,
)

from tests.test_finalized_artifact_persistence import (
    _artifact_set_with_reviewed_document_change,
    _prepared_artifact_persistence,
    _temporary_directory,
)


def _persisted_artifact_set(
    tmp_path: Path,
):
    root, repository, artifact_set = (
        _prepared_artifact_persistence(tmp_path)
    )
    repository.persist_finalized_artifact_set(
        artifact_set
    )

    return root, repository, artifact_set


def test_loads_exact_persisted_artifact_set(
    tmp_path: Path,
) -> None:
    _, repository, artifact_set = (
        _persisted_artifact_set(tmp_path)
    )

    loaded = repository.load_finalized_artifact_set(
        "000001",
        "RVD-000001",
        "RVV-000001",
    )

    assert loaded == artifact_set
    assert (
        loaded.artifact_set_fingerprint
        == artifact_set.artifact_set_fingerprint
    )
    assert loaded.artifacts == artifact_set.artifacts


def test_load_recomputes_in_memory_set_fingerprint(
    tmp_path: Path,
) -> None:
    _, repository, artifact_set = (
        _persisted_artifact_set(tmp_path)
    )

    loaded = repository.load_finalized_artifact_set(
        "000001",
        "RVD-000001",
        "RVV-000001",
    )

    assert (
        loaded.artifact_set_fingerprint
        == artifact_set.artifact_set_fingerprint
    )
    assert all(
        artifact.filename != "artifact_set.json"
        for artifact in loaded.artifacts
    )


def test_missing_finalized_directory_is_rejected(
    tmp_path: Path,
) -> None:
    _, repository, _ = (
        _prepared_artifact_persistence(tmp_path)
    )

    with pytest.raises(
        ReviewReferenceError,
        match="was not found",
    ):
        repository.load_finalized_artifact_set(
            "000001",
            "RVD-000001",
            "RVV-000001",
        )


def test_draft_version_blocks_loading(
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
        match="finalized Review Document Version",
    ):
        repository.load_finalized_artifact_set(
            "000001",
            "RVD-000001",
            "RVV-000001",
        )


def test_interrupted_temporary_directory_blocks_loading(
    tmp_path: Path,
) -> None:
    root, repository, _ = (
        _persisted_artifact_set(tmp_path)
    )
    _temporary_directory(root).mkdir()

    with pytest.raises(
        ReviewRecoveryRequiredError,
        match="explicit recovery",
    ):
        repository.load_finalized_artifact_set(
            "000001",
            "RVD-000001",
            "RVV-000001",
        )


def test_regular_file_finalized_path_is_rejected(
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

    with pytest.raises(
        UnsafeReviewWorkspacePathError,
        match="not a directory",
    ):
        repository.load_finalized_artifact_set(
            "000001",
            "RVD-000001",
            "RVV-000001",
        )


def test_symbolic_link_finalized_path_is_rejected(
    tmp_path: Path,
) -> None:
    root, repository, _ = (
        _prepared_artifact_persistence(tmp_path)
    )
    outside = tmp_path / "outside-finalized"
    outside.mkdir()

    finalized_review_path(
        root,
        "000001",
        "RVD-000001",
        "RVV-000001",
    ).symlink_to(
        outside,
        target_is_directory=True,
    )

    with pytest.raises(
        UnsafeReviewWorkspacePathError,
        match="Symbolic-link",
    ):
        repository.load_finalized_artifact_set(
            "000001",
            "RVD-000001",
            "RVV-000001",
        )


@pytest.mark.parametrize(
    "filename",
    (
        REVIEWED_DOCUMENT_FILENAME,
        EFFECTIVE_DECISIONS_FILENAME,
        REVIEWED_REPORT_FILENAME,
    ),
)
def test_missing_artifact_is_rejected(
    tmp_path: Path,
    filename: str,
) -> None:
    root, repository, _ = (
        _persisted_artifact_set(tmp_path)
    )
    (
        finalized_review_path(
            root,
            "000001",
            "RVD-000001",
            "RVV-000001",
        )
        / filename
    ).unlink()

    with pytest.raises(
        ReviewIntegrityError,
        match="invalid entries",
    ):
        repository.load_finalized_artifact_set(
            "000001",
            "RVD-000001",
            "RVV-000001",
        )


def test_unexpected_fourth_artifact_is_rejected(
    tmp_path: Path,
) -> None:
    root, repository, _ = (
        _persisted_artifact_set(tmp_path)
    )
    (
        finalized_review_path(
            root,
            "000001",
            "RVD-000001",
            "RVV-000001",
        )
        / "artifact_set.json"
    ).write_text(
        "{}\n",
        encoding="utf-8",
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="invalid entries",
    ):
        repository.load_finalized_artifact_set(
            "000001",
            "RVD-000001",
            "RVV-000001",
        )


def test_invalid_utf8_is_rejected(
    tmp_path: Path,
) -> None:
    root, repository, _ = (
        _persisted_artifact_set(tmp_path)
    )
    effective_decisions_path(
        root,
        "000001",
        "RVD-000001",
        "RVV-000001",
    ).write_bytes(b"\xff\xfe")

    with pytest.raises(
        ReviewIntegrityError,
        match="valid UTF-8",
    ):
        repository.load_finalized_artifact_set(
            "000001",
            "RVD-000001",
            "RVV-000001",
        )


def test_semantically_valid_noncanonical_json_is_rejected(
    tmp_path: Path,
) -> None:
    root, repository, _ = (
        _persisted_artifact_set(tmp_path)
    )
    path = reviewed_document_path(
        root,
        "000001",
        "RVD-000001",
        "RVV-000001",
    )
    payload = json.loads(
        path.read_text(encoding="utf-8")
    )
    path.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=4,
        )
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="exact canonical bytes",
    ):
        repository.load_finalized_artifact_set(
            "000001",
            "RVD-000001",
            "RVV-000001",
        )


def test_tampered_reviewed_report_is_rejected(
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

    with pytest.raises(
        ReviewIntegrityError,
        match="deterministic rendering",
    ):
        repository.load_finalized_artifact_set(
            "000001",
            "RVD-000001",
            "RVV-000001",
        )


def test_repository_binding_is_revalidated_on_load(
    tmp_path: Path,
) -> None:
    root, repository, artifact_set = (
        _persisted_artifact_set(tmp_path)
    )
    mismatched = (
        _artifact_set_with_reviewed_document_change(
            repository,
            artifact_set,
            field="source_id",
            value="SRC-000002",
        )
    )
    directory = finalized_review_path(
        root,
        "000001",
        "RVD-000001",
        "RVV-000001",
    )

    for artifact in mismatched.artifacts:
        (
            directory / artifact.filename
        ).write_bytes(artifact.content)

    with pytest.raises(
        ReviewIntegrityError,
        match="source_id",
    ):
        repository.load_finalized_artifact_set(
            "000001",
            "RVD-000001",
            "RVV-000001",
        )
