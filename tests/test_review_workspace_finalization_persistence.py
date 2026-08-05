"""Tests for atomic authorized Review finalization persistence."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

import pytest

from modules.human_review import (
    HumanReviewRepository,
)
from modules.project_workspace import (
    ProjectWorkspace,
)
from modules.review_workspace.errors import (
    InvalidReviewVersionTransitionError,
    ReviewIntegrityError,
    ReviewRecoveryRequiredError,
    ReviewValidationError,
    StaleReviewRevisionError,
)
from modules.review_workspace.finalization_authorization import (
    authorize_persisted_review_document_finalization,
)
from modules.review_workspace.finalization_validation import (
    assess_review_document_finalization,
    create_review_document_finalization_target,
)
from modules.review_workspace.paths import (
    review_document_version_path,
)
from modules.review_workspace.repository import (
    ReviewWorkspaceRepository,
)
from modules.review_workspace.version_manifest import (
    REVIEW_DOCUMENT_VERSION_MANIFEST_FILENAME,
    finalize_review_document_version,
    review_document_version_to_json,
)

from tests.test_review_workspace_finalization_validation import (
    _element_item,
    _revision,
)
from tests.test_review_workspace_repository_mutations import (
    _bundle,
)


FINALIZATION_TIMESTAMP = "2026-08-05T19:10:00Z"


def _clock() -> datetime:
    return datetime(
        2026,
        8,
        5,
        19,
        5,
        tzinfo=timezone.utc,
    )


def _prepared_finalization(tmp_path: Path):
    root = tmp_path / "projects"

    workspace = ProjectWorkspace(
        root=root,
        id_generator=lambda: "000001",
        clock=_clock,
    )
    workspace.create_project(
        "Finalization Persistence Test"
    )

    review_repository = (
        ReviewWorkspaceRepository(root=root)
    )
    human_review_repository = (
        HumanReviewRepository(
            root=root,
            clock=_clock,
        )
    )

    document, version, _ = _bundle()
    revision = _revision(
        _element_item()
    )

    review_repository.create_document_workspace(
        document,
        version,
        revision,
    )

    assessment = (
        assess_review_document_finalization(
            document,
            version,
            revision,
        )
    )
    target = (
        create_review_document_finalization_target(
            assessment
        )
    )

    decision = (
        human_review_repository.record_decision(
            "000001",
            target,
            review_mode="detailed_review",
            decision="confirm",
            reviewer_identity="moritz",
        )
    )

    authorized = (
        authorize_persisted_review_document_finalization(
            version,
            revision,
            assessment,
            human_review_repository,
            timestamp=FINALIZATION_TIMESTAMP,
        )
    )

    return (
        root,
        review_repository,
        version,
        revision,
        decision,
        authorized,
    )


def test_persists_authorized_finalization(
    tmp_path: Path,
) -> None:
    (
        _,
        repository,
        _,
        revision,
        decision,
        authorized,
    ) = _prepared_finalization(tmp_path)

    persisted = (
        repository.persist_authorized_finalization(
            authorized
        )
    )

    assert persisted.version_state == "finalized"
    assert (
        persisted.finalized_revision_id
        == revision.review_revision_id
    )
    assert (
        persisted.finalization_decision_id
        == decision.human_review_decision_id
    )
    assert persisted == authorized.finalized_version


def test_finalization_preserves_revision(
    tmp_path: Path,
) -> None:
    (
        _,
        repository,
        _,
        revision,
        _,
        authorized,
    ) = _prepared_finalization(tmp_path)

    repository.persist_authorized_finalization(
        authorized
    )

    assert repository.load_revision(
        "000001",
        "RVD-000001",
        "RVV-000001",
        "RVR-000001",
    ) == revision


def test_stale_head_blocks_persistence(
    tmp_path: Path,
) -> None:
    (
        _,
        repository,
        _,
        _,
        _,
        authorized,
    ) = _prepared_finalization(tmp_path)

    successor_revision = _revision(
        _element_item(),
        revision_id="RVR-000002",
        revision_sequence=2,
        predecessor_revision_id="RVR-000001",
    )
    repository.append_revision(
        successor_revision
    )

    with pytest.raises(
        StaleReviewRevisionError,
        match="draft version|head",
    ):
        repository.persist_authorized_finalization(
            authorized
        )


def test_mismatched_finalized_transition_is_rejected(
    tmp_path: Path,
) -> None:
    (
        _,
        repository,
        version,
        _,
        _,
        authorized,
    ) = _prepared_finalization(tmp_path)

    mismatched_version = (
        finalize_review_document_version(
            version,
            finalized_revision_id="RVR-000001",
            finalization_decision_id="HRD-000999",
            timestamp=FINALIZATION_TIMESTAMP,
        )
    )
    mismatched = replace(
        authorized,
        finalized_version=mismatched_version,
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="authorization|authorized transition",
    ):
        repository.persist_authorized_finalization(
            mismatched
        )


def test_interrupted_manifest_requires_recovery(
    tmp_path: Path,
) -> None:
    (
        root,
        repository,
        _,
        _,
        _,
        authorized,
    ) = _prepared_finalization(tmp_path)

    version_directory = (
        review_document_version_path(
            root,
            "000001",
            "RVD-000001",
            "RVV-000001",
        )
    )
    temporary = version_directory / (
        "."
        f"{REVIEW_DOCUMENT_VERSION_MANIFEST_FILENAME}"
        ".tmp"
    )
    temporary.write_text(
        review_document_version_to_json(
            authorized.finalized_version
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        ReviewRecoveryRequiredError,
        match="recovery",
    ):
        repository.persist_authorized_finalization(
            authorized
        )


def test_version_cannot_be_finalized_twice(
    tmp_path: Path,
) -> None:
    (
        _,
        repository,
        _,
        _,
        _,
        authorized,
    ) = _prepared_finalization(tmp_path)

    repository.persist_authorized_finalization(
        authorized
    )

    with pytest.raises(
        InvalidReviewVersionTransitionError,
        match="draft",
    ):
        repository.persist_authorized_finalization(
            authorized
        )


def test_repository_argument_is_strict(
    tmp_path: Path,
) -> None:
    (
        _,
        repository,
        _,
        _,
        _,
        _,
    ) = _prepared_finalization(tmp_path)

    with pytest.raises(
        ReviewValidationError,
        match="AuthorizedReviewDocumentFinalization",
    ):
        repository.persist_authorized_finalization(
            object()
        )


def test_reloaded_version_matches_authorized_result(
    tmp_path: Path,
) -> None:
    (
        _,
        repository,
        _,
        _,
        _,
        authorized,
    ) = _prepared_finalization(tmp_path)

    repository.persist_authorized_finalization(
        authorized
    )

    assert repository.load_version(
        "000001",
        "RVD-000001",
        "RVV-000001",
    ) == authorized.finalized_version
