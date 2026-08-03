"""Tests for Review Workspace append-only repository mutations."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from modules.project_processing import (
    ProcessingArtifactReference,
)
from modules.project_workspace import ProjectWorkspace
from modules.project_workspace.types import (
    FrameworkTemplateReference,
)
from modules.review_workspace.document_manifest import (
    create_review_document,
)
from modules.review_workspace.errors import (
    DuplicateReviewRevisionError,
    DuplicateScopedReviewActionError,
    InvalidReviewVersionTransitionError,
    ReviewIntegrityError,
    ReviewRecoveryRequiredError,
    ReviewReferenceError,
    StaleReviewRevisionError,
    UnsafeReviewWorkspacePathError,
)
from modules.review_workspace.item_manifest import (
    create_review_item,
)
from modules.review_workspace.paths import (
    review_document_version_path,
    review_revision_path,
    scoped_review_action_path,
)
from modules.review_workspace.repository import (
    ReviewWorkspaceRepository,
)
from modules.review_workspace.revision_manifest import (
    create_review_revision,
    review_revision_to_json,
)
from modules.review_workspace.scoped_action_manifest import (
    create_scoped_review_action,
    scoped_review_action_to_json,
)
from modules.review_workspace.types import (
    MaterializedReviewItemReference,
    ReviewItemContent,
)
from modules.review_workspace.version_manifest import (
    create_review_document_version,
    finalize_review_document_version,
    review_document_version_to_json,
)


def _clock() -> datetime:
    return datetime(
        2026,
        8,
        3,
        16,
        0,
        tzinfo=timezone.utc,
    )


@pytest.fixture
def repository(
    tmp_path: Path,
) -> tuple[ReviewWorkspaceRepository, Path]:
    root = tmp_path / "projects"

    workspace = ProjectWorkspace(
        root=root,
        id_generator=lambda: "000001",
        clock=_clock,
    )
    workspace.create_project(
        "Review Mutation Test",
    )

    store = ReviewWorkspaceRepository(root=root)
    document, version, revision = _bundle()

    store.create_document_workspace(
        document,
        version,
        revision,
    )

    return store, root


def _review_item():
    content = ReviewItemContent(
        title="Clarify source authority",
        primary_text=(
            "Which source is authoritative for this claim?"
        ),
        description=None,
        information_type="open_question",
        modality=None,
        epistemic_status="unresolved",
        human_rationale=None,
        human_confidence=None,
        relationship_representation=None,
    )

    return create_review_item(
        project_id="000001",
        review_document_id="RVD-000001",
        review_document_version_id="RVV-000001",
        review_item_id="RIT-000001",
        review_item_kind="open_question",
        stable_subject_key="clarify-source-authority",
        section="open_questions",
        lineage_operation="human_created",
        derived_from_review_item_ids=(),
        original_report_locator=(
            "open-questions/clarify-source-authority"
        ),
        proposal_references=(),
        source_evidence_references=(),
        consensus_evidence_references=(),
        current_content=content,
        dimension_selections=(),
        effective_review_outcome="open",
    )


def _bundle():
    document = create_review_document(
        project_id="000001",
        review_document_id="RVD-000001",
        source_id="SRC-000001",
        source_sha256="a" * 64,
        processing_run_id="RUN-000001",
        attempt_id="ATT-000001",
        primary_review_artifact_reference=(
            ProcessingArtifactReference(
                artifact_type="review_reports",
                artifact_id="REPORT-001",
                content_fingerprint="b" * 64,
                repository_relative_path=(
                    "data/projects/000001/runs/"
                    "RUN-000001/artifacts/review_reports/"
                    "report.md"
                ),
            )
        ),
        supporting_artifact_references=(),
        framework_template=FrameworkTemplateReference(
            template_id="TURING_RFLP_FRAMEWORK",
            template_version="1.0.0",
        ),
        semantic_reference_versions=(),
        timestamp="2026-08-03T16:00:00Z",
    )

    version = create_review_document_version(
        project_id="000001",
        review_document_id="RVD-000001",
        review_document_version_id="RVV-000001",
        version_number=1,
        predecessor_version_id=None,
        reopen_reason=None,
        opened_by="reviewer@example.com",
        timestamp="2026-08-03T16:00:00Z",
        head_revision_id="RVR-000001",
    )

    revision = create_review_revision(
        project_id="000001",
        review_document_id="RVD-000001",
        review_document_version_id="RVV-000001",
        review_revision_id="RVR-000001",
        revision_sequence=1,
        predecessor_revision_id=None,
        review_items=(_review_item(),),
        scoped_review_action_ids=(),
        created_by="reviewer@example.com",
        timestamp="2026-08-03T16:00:00Z",
    )

    return document, version, revision


def _action(
    *,
    action_id: str = "SRA-000001",
    review_item_id: str = "RIT-000001",
    fingerprint: str | None = None,
    outcome: str = "deferred",
):
    item = _review_item()

    if fingerprint is None:
        fingerprint = item.item_content_fingerprint

    return create_scoped_review_action(
        project_id="000001",
        review_document_id="RVD-000001",
        review_document_version_id="RVV-000001",
        scoped_review_action_id=action_id,
        action_scope="explicit_selection",
        decision_dimension="review_outcome",
        selected_values=(outcome,),
        filter_definition=None,
        materialized_items=(
            MaterializedReviewItemReference(
                review_item_id=review_item_id,
                item_content_fingerprint=fingerprint,
            ),
        ),
        created_by="reviewer@example.com",
        timestamp="2026-08-03T16:05:00Z",
        rationale=None,
    )


def _second_revision(
    *,
    revision_id: str = "RVR-000002",
    revision_sequence: int = 2,
    predecessor_revision_id: str = "RVR-000001",
    action_ids: tuple[str, ...] = (),
    created_by: str = "reviewer@example.com",
):
    return create_review_revision(
        project_id="000001",
        review_document_id="RVD-000001",
        review_document_version_id="RVV-000001",
        review_revision_id=revision_id,
        revision_sequence=revision_sequence,
        predecessor_revision_id=predecessor_revision_id,
        review_items=(_review_item(),),
        scoped_review_action_ids=action_ids,
        created_by=created_by,
        timestamp="2026-08-03T16:10:00Z",
    )


def _finalize_version(
    store: ReviewWorkspaceRepository,
    root: Path,
) -> None:
    version = store.load_version(
        "000001",
        "RVD-000001",
        "RVV-000001",
    )
    finalized = finalize_review_document_version(
        version,
        finalized_revision_id=version.head_revision_id,
        finalization_decision_id="HRD-000001",
        timestamp="2026-08-03T16:30:00Z",
    )
    path = (
        review_document_version_path(
            root,
            "000001",
            "RVD-000001",
            "RVV-000001",
        )
        / "review_version_manifest.json"
    )
    path.write_text(
        review_document_version_to_json(finalized),
        encoding="utf-8",
    )


def test_persist_and_load_scoped_action(
    repository,
) -> None:
    store, _ = repository
    action = _action()

    assert store.persist_scoped_action(action) == action
    assert store.load_scoped_action(
        "000001",
        "RVD-000001",
        "RVV-000001",
        "SRA-000001",
    ) == action


def test_scoped_action_requires_existing_materialized_item(
    repository,
) -> None:
    store, _ = repository
    action = _action(
        review_item_id="RIT-000002",
    )

    with pytest.raises(
        ReviewReferenceError,
        match="unavailable Review Item",
    ):
        store.persist_scoped_action(action)


def test_scoped_action_requires_exact_item_fingerprint(
    repository,
) -> None:
    store, _ = repository
    action = _action(
        fingerprint="f" * 64,
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="fingerprint",
    ):
        store.persist_scoped_action(action)


def test_duplicate_scoped_action_is_rejected(
    repository,
) -> None:
    store, _ = repository
    action = _action()

    store.persist_scoped_action(action)

    with pytest.raises(
        DuplicateScopedReviewActionError,
    ):
        store.persist_scoped_action(action)


def test_action_identifier_cannot_hold_different_content(
    repository,
) -> None:
    store, _ = repository

    store.persist_scoped_action(_action())

    with pytest.raises(
        ReviewIntegrityError,
        match="different content",
    ):
        store.persist_scoped_action(
            _action(outcome="out_of_scope")
        )


def test_missing_scoped_action_uses_reference_error(
    repository,
) -> None:
    store, _ = repository

    with pytest.raises(ReviewReferenceError):
        store.load_scoped_action(
            "000001",
            "RVD-000001",
            "RVV-000001",
            "SRA-000001",
        )


def test_interrupted_action_persistence_requires_recovery(
    repository,
) -> None:
    store, root = repository
    action = _action()
    target = scoped_review_action_path(
        root,
        "000001",
        "RVD-000001",
        "RVV-000001",
        "SRA-000001",
    )
    temporary = target.parent / f".{target.name}.tmp"
    temporary.write_text(
        scoped_review_action_to_json(action),
        encoding="utf-8",
    )

    with pytest.raises(
        ReviewRecoveryRequiredError,
        match="recovery",
    ):
        store.persist_scoped_action(action)


def test_finalized_version_rejects_scoped_action(
    repository,
) -> None:
    store, root = repository
    _finalize_version(store, root)

    with pytest.raises(
        InvalidReviewVersionTransitionError,
        match="draft",
    ):
        store.persist_scoped_action(_action())


def test_append_revision_advances_version_head(
    repository,
) -> None:
    store, _ = repository
    action = _action()
    store.persist_scoped_action(action)

    revision = _second_revision(
        action_ids=("SRA-000001",),
    )
    version, persisted = store.append_revision(
        revision
    )

    assert persisted == revision
    assert version.head_revision_id == "RVR-000002"
    assert store.load_revision(
        "000001",
        "RVD-000001",
        "RVV-000001",
        "RVR-000002",
    ) == revision
    assert store.load_version(
        "000001",
        "RVD-000001",
        "RVV-000001",
    ) == version


def test_append_revision_rejects_stale_predecessor(
    repository,
) -> None:
    store, _ = repository
    revision = _second_revision(
        revision_id="RVR-000003",
        predecessor_revision_id="RVR-000002",
    )

    with pytest.raises(
        StaleReviewRevisionError,
        match="predecessor",
    ):
        store.append_revision(revision)


def test_append_revision_rejects_wrong_sequence(
    repository,
) -> None:
    store, _ = repository
    revision = _second_revision(
        revision_sequence=3,
    )

    with pytest.raises(
        StaleReviewRevisionError,
        match="sequence",
    ):
        store.append_revision(revision)


def test_append_revision_requires_existing_actions(
    repository,
) -> None:
    store, _ = repository
    revision = _second_revision(
        action_ids=("SRA-000001",),
    )

    with pytest.raises(ReviewReferenceError):
        store.append_revision(revision)


def test_finalized_version_rejects_new_revision(
    repository,
) -> None:
    store, root = repository
    _finalize_version(store, root)

    with pytest.raises(
        InvalidReviewVersionTransitionError,
        match="draft",
    ):
        store.append_revision(
            _second_revision()
        )


def test_duplicate_revision_is_rejected(
    repository,
) -> None:
    store, _ = repository
    revision = _second_revision()

    store.append_revision(revision)

    with pytest.raises(
        DuplicateReviewRevisionError,
    ):
        store.append_revision(revision)


def test_revision_identifier_cannot_hold_different_content(
    repository,
) -> None:
    store, root = repository
    existing = _second_revision(
        created_by="other@example.com",
    )
    target = review_revision_path(
        root,
        "000001",
        "RVD-000001",
        "RVV-000001",
        "RVR-000002",
    )
    target.write_text(
        review_revision_to_json(existing),
        encoding="utf-8",
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="different content",
    ):
        store.append_revision(
            _second_revision()
        )


def test_interrupted_revision_append_requires_recovery(
    repository,
) -> None:
    store, root = repository
    revision = _second_revision()
    target = review_revision_path(
        root,
        "000001",
        "RVD-000001",
        "RVV-000001",
        "RVR-000002",
    )
    temporary = target.parent / f".{target.name}.tmp"
    temporary.write_text(
        review_revision_to_json(revision),
        encoding="utf-8",
    )

    with pytest.raises(
        ReviewRecoveryRequiredError,
        match="recovery",
    ):
        store.append_revision(revision)


def test_interrupted_version_update_requires_recovery(
    repository,
) -> None:
    store, root = repository
    version_directory = review_document_version_path(
        root,
        "000001",
        "RVD-000001",
        "RVV-000001",
    )
    temporary = (
        version_directory
        / ".review_version_manifest.json.tmp"
    )
    temporary.write_text(
        "{}\n",
        encoding="utf-8",
    )

    with pytest.raises(
        ReviewRecoveryRequiredError,
        match="recovery",
    ):
        store.append_revision(
            _second_revision()
        )


def test_symbolic_link_scoped_action_is_rejected(
    repository,
) -> None:
    store, root = repository
    action = _action()
    store.persist_scoped_action(action)

    target = scoped_review_action_path(
        root,
        "000001",
        "RVD-000001",
        "RVV-000001",
        "SRA-000001",
    )
    real_target = target.with_name(
        "real-scoped-action.json"
    )
    target.rename(real_target)

    try:
        target.symlink_to(real_target)
    except OSError:
        pytest.skip(
            "Symbolic links are not supported."
        )

    with pytest.raises(
        UnsafeReviewWorkspacePathError,
    ):
        store.load_scoped_action(
            "000001",
            "RVD-000001",
            "RVV-000001",
            "SRA-000001",
        )
