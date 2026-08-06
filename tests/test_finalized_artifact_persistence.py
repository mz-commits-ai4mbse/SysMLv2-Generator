"""Tests for atomic finalized Review Artifact Set persistence."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from modules.review_workspace.effective_decisions_manifest import (
    create_effective_review_decision_set,
)
from modules.review_workspace.errors import (
    InvalidReviewVersionTransitionError,
    ReviewIntegrityError,
    ReviewPersistenceError,
    ReviewRecoveryRequiredError,
    ReviewValidationError,
    UnsafeReviewWorkspacePathError,
)
from modules.review_workspace.finalized_artifact_set import (
    FINALIZED_REVIEW_ARTIFACT_ORDER,
    create_finalized_review_artifact_set,
)
from modules.review_workspace.paths import (
    finalized_review_path,
    review_document_version_path,
)
from modules.review_workspace.repository import (
    ReviewWorkspaceRepository,
)
from modules.review_workspace.reviewed_document_manifest import (
    calculate_finalized_reviewed_document_fingerprint,
    create_finalized_reviewed_document,
)
from modules.review_workspace.reviewed_report_renderer import (
    create_rendered_reviewed_report,
)

from tests.test_finalized_artifact_set import (
    _artifact_set,
)
from tests.test_review_workspace_finalization_persistence import (
    _prepared_finalization,
)
from tests.test_review_workspace_finalization_validation import (
    _element_item,
)


def _artifact_set_with_reviewed_document_change(
    repository: ReviewWorkspaceRepository,
    artifact_set,
    *,
    field: str,
    value: object,
):
    provisional = replace(
        artifact_set.reviewed_document,
        **{
            field: value,
            "content_fingerprint": "0" * 64,
        },
    )
    reviewed_document = replace(
        provisional,
        content_fingerprint=(
            calculate_finalized_reviewed_document_fingerprint(
                provisional
            )
        ),
    )

    revision = repository.load_revision(
        reviewed_document.project_id,
        reviewed_document.review_document_id,
        reviewed_document.review_document_version_id,
        reviewed_document.review_revision_id,
    )
    effective_decisions = (
        create_effective_review_decision_set(
            reviewed_document,
            revision,
        )
    )
    reviewed_report = (
        create_rendered_reviewed_report(
            reviewed_document,
            effective_decisions,
        )
    )

    return create_finalized_review_artifact_set(
        reviewed_document,
        effective_decisions,
        reviewed_report,
    )


def _prepared_artifact_persistence(
    tmp_path: Path,
    *,
    persist_version: bool = True,
):
    (
        root,
        repository,
        _,
        revision,
        _,
        authorized,
    ) = _prepared_finalization(tmp_path)

    if persist_version:
        finalized_version = (
            repository.persist_authorized_finalization(
                authorized
            )
        )
    else:
        finalized_version = (
            authorized.finalized_version
        )

    document = repository.load_document(
        "000001",
        "RVD-000001",
    )

    reviewed_document = (
        create_finalized_reviewed_document(
            document,
            finalized_version,
            revision,
            authorized.authorization,
        )
    )
    effective_decisions = (
        create_effective_review_decision_set(
            reviewed_document,
            revision,
        )
    )
    reviewed_report = (
        create_rendered_reviewed_report(
            reviewed_document,
            effective_decisions,
        )
    )
    artifact_set = (
        create_finalized_review_artifact_set(
            reviewed_document,
            effective_decisions,
            reviewed_report,
        )
    )

    return root, repository, artifact_set


def _final_directory(root: Path) -> Path:
    return finalized_review_path(
        root,
        "000001",
        "RVD-000001",
        "RVV-000001",
    )


def _temporary_directory(root: Path) -> Path:
    return (
        review_document_version_path(
            root,
            "000001",
            "RVD-000001",
            "RVV-000001",
        )
        / ".finalized.tmp"
    )


def test_persists_exact_three_artifact_set(
    tmp_path: Path,
) -> None:
    root, repository, artifact_set = (
        _prepared_artifact_persistence(tmp_path)
    )

    persisted = (
        repository.persist_finalized_artifact_set(
            artifact_set
        )
    )

    directory = _final_directory(root)

    assert persisted is artifact_set
    assert directory.is_dir()
    assert tuple(
        sorted(
            entry.name
            for entry in directory.iterdir()
        )
    ) == tuple(
        sorted(FINALIZED_REVIEW_ARTIFACT_ORDER)
    )

    for artifact in artifact_set.artifacts:
        assert (
            directory
            .joinpath(artifact.filename)
            .read_bytes()
            == artifact.content
        )


def test_does_not_persist_fourth_artifact(
    tmp_path: Path,
) -> None:
    root, repository, artifact_set = (
        _prepared_artifact_persistence(tmp_path)
    )

    repository.persist_finalized_artifact_set(
        artifact_set
    )

    directory = _final_directory(root)

    assert not (
        directory / "artifact_set.json"
    ).exists()


def test_success_removes_temporary_visibility(
    tmp_path: Path,
) -> None:
    root, repository, artifact_set = (
        _prepared_artifact_persistence(tmp_path)
    )

    repository.persist_finalized_artifact_set(
        artifact_set
    )

    assert not _temporary_directory(root).exists()
    assert _final_directory(root).is_dir()


def test_draft_version_blocks_artifact_persistence(
    tmp_path: Path,
) -> None:
    root, repository, artifact_set = (
        _prepared_artifact_persistence(
            tmp_path,
            persist_version=False,
        )
    )

    with pytest.raises(
        InvalidReviewVersionTransitionError,
        match="finalized Review Document Version",
    ):
        repository.persist_finalized_artifact_set(
            artifact_set
        )

    assert not _temporary_directory(root).exists()
    assert not _final_directory(root).exists()


def test_invalid_artifact_set_is_rejected_before_write(
    tmp_path: Path,
) -> None:
    root, repository, artifact_set = (
        _prepared_artifact_persistence(tmp_path)
    )
    invalid = replace(
        artifact_set,
        artifact_set_fingerprint="f" * 64,
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="Artifact-set fingerprint",
    ):
        repository.persist_finalized_artifact_set(
            invalid
        )

    assert not _temporary_directory(root).exists()
    assert not _final_directory(root).exists()


@pytest.mark.parametrize(
    ("field", "value", "message"),
    (
        (
            "source_id",
            "SRC-000002",
            "source_id",
        ),
        (
            "source_sha256",
            "c" * 64,
            "source_sha256",
        ),
        (
            "processing_run_id",
            "RUN-000002",
            "processing_run_id",
        ),
        (
            "attempt_id",
            "ATT-000002",
            "attempt_id",
        ),
        (
            "review_document_content_fingerprint",
            "d" * 64,
            "content fingerprint",
        ),
    ),
)
def test_persisted_document_binding_mismatch_is_rejected(
    tmp_path: Path,
    field: str,
    value: object,
    message: str,
) -> None:
    root, repository, artifact_set = (
        _prepared_artifact_persistence(tmp_path)
    )
    mismatched = (
        _artifact_set_with_reviewed_document_change(
            repository,
            artifact_set,
            field=field,
            value=value,
        )
    )

    with pytest.raises(
        ReviewIntegrityError,
        match=message,
    ):
        repository.persist_finalized_artifact_set(
            mismatched
        )

    assert not _temporary_directory(root).exists()
    assert not _final_directory(root).exists()


def test_persisted_revision_mismatch_is_rejected(
    tmp_path: Path,
) -> None:
    root, repository, _ = (
        _prepared_artifact_persistence(tmp_path)
    )
    *_, foreign_artifact_set = _artifact_set(
        _element_item(
            review_item_id="RIT-000002",
        )
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="persisted Review Revision",
    ):
        repository.persist_finalized_artifact_set(
            foreign_artifact_set
        )

    assert not _temporary_directory(root).exists()
    assert not _final_directory(root).exists()


def test_existing_finalized_directory_is_not_overwritten(
    tmp_path: Path,
) -> None:
    _, repository, artifact_set = (
        _prepared_artifact_persistence(tmp_path)
    )

    repository.persist_finalized_artifact_set(
        artifact_set
    )

    with pytest.raises(
        ReviewPersistenceError,
        match="already exists",
    ):
        repository.persist_finalized_artifact_set(
            artifact_set
        )


def test_interrupted_temporary_directory_requires_recovery(
    tmp_path: Path,
) -> None:
    root, repository, artifact_set = (
        _prepared_artifact_persistence(tmp_path)
    )
    temporary = _temporary_directory(root)
    temporary.mkdir()

    with pytest.raises(
        ReviewRecoveryRequiredError,
        match="explicit recovery",
    ):
        repository.persist_finalized_artifact_set(
            artifact_set
        )

    assert temporary.is_dir()
    assert not _final_directory(root).exists()


def test_symbolic_link_finalized_directory_is_rejected(
    tmp_path: Path,
) -> None:
    root, repository, artifact_set = (
        _prepared_artifact_persistence(tmp_path)
    )
    outside = tmp_path / "outside-finalized"
    outside.mkdir()

    _final_directory(root).symlink_to(
        outside,
        target_is_directory=True,
    )

    with pytest.raises(
        UnsafeReviewWorkspacePathError,
        match="Symbolic-link",
    ):
        repository.persist_finalized_artifact_set(
            artifact_set
        )


def test_partial_write_never_publishes_final_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, repository, artifact_set = (
        _prepared_artifact_persistence(tmp_path)
    )
    original_write = (
        ReviewWorkspaceRepository._write_new_bytes
    )
    calls = 0

    def fail_second_write(
        path: Path,
        content: bytes,
        *,
        label: str,
    ) -> None:
        nonlocal calls

        calls += 1

        if calls == 2:
            raise ReviewPersistenceError(
                "Simulated finalized artifact write failure."
            )

        original_write(
            path,
            content,
            label=label,
        )

    monkeypatch.setattr(
        ReviewWorkspaceRepository,
        "_write_new_bytes",
        staticmethod(fail_second_write),
    )

    with pytest.raises(
        ReviewPersistenceError,
        match="Simulated",
    ):
        repository.persist_finalized_artifact_set(
            artifact_set
        )

    temporary = _temporary_directory(root)

    assert temporary.is_dir()
    assert not _final_directory(root).exists()
    assert tuple(
        entry.name
        for entry in temporary.iterdir()
    ) == (
        FINALIZED_REVIEW_ARTIFACT_ORDER[0],
    )

    with pytest.raises(
        ReviewRecoveryRequiredError,
        match="explicit recovery",
    ):
        repository.persist_finalized_artifact_set(
            artifact_set
        )


def test_regular_file_finalized_path_is_rejected(
    tmp_path: Path,
) -> None:
    root, repository, artifact_set = (
        _prepared_artifact_persistence(tmp_path)
    )
    final_directory = _final_directory(root)
    final_directory.write_bytes(b"occupied")

    with pytest.raises(
        UnsafeReviewWorkspacePathError,
        match="not a directory",
    ):
        repository.persist_finalized_artifact_set(
            artifact_set
        )

    assert final_directory.is_file()
    assert (
        final_directory.read_bytes()
        == b"occupied"
    )
    assert not _temporary_directory(root).exists()


def test_publish_rename_failure_requires_recovery(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, repository, artifact_set = (
        _prepared_artifact_persistence(tmp_path)
    )
    temporary = _temporary_directory(root)
    final_directory = _final_directory(root)
    original_rename = Path.rename

    def fail_finalized_publish(
        source: Path,
        target: Path,
    ):
        if (
            source == temporary
            and Path(target) == final_directory
        ):
            raise OSError(
                "Simulated finalized artifact "
                "publish failure."
            )

        return original_rename(
            source,
            target,
        )

    monkeypatch.setattr(
        Path,
        "rename",
        fail_finalized_publish,
    )

    with pytest.raises(
        ReviewRecoveryRequiredError,
        match="atomically publish",
    ):
        repository.persist_finalized_artifact_set(
            artifact_set
        )

    assert temporary.is_dir()
    assert not final_directory.exists()
    assert tuple(
        sorted(
            entry.name
            for entry in temporary.iterdir()
        )
    ) == tuple(
        sorted(FINALIZED_REVIEW_ARTIFACT_ORDER)
    )

    for artifact in artifact_set.artifacts:
        assert (
            temporary
            .joinpath(artifact.filename)
            .read_bytes()
            == artifact.content
        )


def test_repository_argument_is_strict(
    tmp_path: Path,
) -> None:
    _, repository, _ = (
        _prepared_artifact_persistence(tmp_path)
    )

    with pytest.raises(
        ReviewValidationError,
        match="FinalizedReviewArtifactSet",
    ):
        repository.persist_finalized_artifact_set(
            object()
        )
