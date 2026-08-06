"""Tests for deterministic Review Document Version reopening."""

from __future__ import annotations

from pathlib import Path

import pytest

from modules.review_workspace.errors import (
    InvalidReviewVersionTransitionError,
    ReviewIntegrityError,
    ReviewValidationError,
)
from modules.review_workspace.reopening import (
    create_reopened_review_version_bundle,
    validate_reopened_review_version_bundle,
)

from tests.test_finalized_artifact_loading import (
    _persisted_artifact_set,
)
from tests.test_finalized_artifact_persistence import (
    _prepared_artifact_persistence,
)


def _finalized_predecessor(
    tmp_path: Path,
):
    _, repository, _ = (
        _persisted_artifact_set(tmp_path)
    )
    version = repository.load_version(
        "000001",
        "RVD-000001",
        "RVV-000001",
    )
    revision = repository.load_revision(
        "000001",
        "RVD-000001",
        "RVV-000001",
        "RVR-000001",
    )

    return version, revision


def test_creates_documented_successor_bundle(
    tmp_path: Path,
) -> None:
    version, revision = (
        _finalized_predecessor(tmp_path)
    )

    bundle = create_reopened_review_version_bundle(
        version,
        revision,
        review_document_version_id="RVV-000002",
        review_revision_id="RVR-000002",
        review_item_ids=("RIT-000002",),
        reopen_reason="Clarify the reviewed statement.",
        opened_by="reviewer@example.com",
        timestamp="2026-08-06T18:30:00Z",
    )

    assert bundle.version.version_number == 2
    assert bundle.version.version_state == "draft"
    assert (
        bundle.version.predecessor_version_id
        == "RVV-000001"
    )
    assert (
        bundle.version.reopen_reason
        == "Clarify the reviewed statement."
    )
    assert (
        bundle.version.head_revision_id
        == "RVR-000002"
    )
    assert (
        bundle.initial_revision.review_revision_id
        == "RVR-000002"
    )
    assert (
        bundle.initial_revision.revision_sequence
        == 1
    )
    assert (
        bundle.initial_revision
        .predecessor_revision_id
        is None
    )
    assert (
        bundle.initial_revision
        .scoped_review_action_ids
        == ()
    )


def test_carried_items_preserve_review_state(
    tmp_path: Path,
) -> None:
    version, revision = (
        _finalized_predecessor(tmp_path)
    )

    bundle = create_reopened_review_version_bundle(
        version,
        revision,
        review_document_version_id="RVV-000002",
        review_revision_id="RVR-000002",
        review_item_ids=("RIT-000002",),
        reopen_reason="Required correction.",
        opened_by="reviewer@example.com",
        timestamp="2026-08-06T18:30:00Z",
    )

    predecessor = revision.review_items[0]
    carried = bundle.initial_revision.review_items[0]

    assert carried.review_item_id == "RIT-000002"
    assert (
        carried.review_document_version_id
        == "RVV-000002"
    )
    assert (
        carried.lineage_operation
        == "carried_forward"
    )
    assert (
        carried.derived_from_review_item_ids
        == ("RIT-000001",)
    )
    assert (
        carried.stable_subject_key
        == predecessor.stable_subject_key
    )
    assert (
        carried.proposal_references
        == predecessor.proposal_references
    )
    assert (
        carried.source_evidence_references
        == predecessor.source_evidence_references
    )
    assert (
        carried.consensus_evidence_references
        == predecessor
        .consensus_evidence_references
    )
    assert (
        carried.current_content
        == predecessor.current_content
    )
    assert (
        carried.dimension_selections
        == predecessor.dimension_selections
    )
    assert (
        carried.effective_review_outcome
        == predecessor.effective_review_outcome
    )


def test_bundle_validation_accepts_created_bundle(
    tmp_path: Path,
) -> None:
    version, revision = (
        _finalized_predecessor(tmp_path)
    )

    bundle = create_reopened_review_version_bundle(
        version,
        revision,
        review_document_version_id="RVV-000002",
        review_revision_id="RVR-000002",
        review_item_ids=("RIT-000002",),
        reopen_reason="Required correction.",
        opened_by="reviewer@example.com",
        timestamp="2026-08-06T18:30:00Z",
    )

    validate_reopened_review_version_bundle(
        bundle,
        predecessor_version=version,
        predecessor_revision=revision,
    )


def test_draft_version_cannot_be_reopened(
    tmp_path: Path,
) -> None:
    _, repository, _ = (
        _prepared_artifact_persistence(
            tmp_path,
            persist_version=False,
        )
    )
    version = repository.load_version(
        "000001",
        "RVD-000001",
        "RVV-000001",
    )
    revision = repository.load_revision(
        "000001",
        "RVD-000001",
        "RVV-000001",
        "RVR-000001",
    )

    with pytest.raises(
        InvalidReviewVersionTransitionError,
        match="finalized",
    ):
        create_reopened_review_version_bundle(
            version,
            revision,
            review_document_version_id="RVV-000002",
            review_revision_id="RVR-000002",
            review_item_ids=("RIT-000002",),
            reopen_reason="Required correction.",
            opened_by="reviewer@example.com",
            timestamp="2026-08-06T18:30:00Z",
        )


def test_reopening_requires_one_new_id_per_item(
    tmp_path: Path,
) -> None:
    version, revision = (
        _finalized_predecessor(tmp_path)
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="exactly one new Review Item ID",
    ):
        create_reopened_review_version_bundle(
            version,
            revision,
            review_document_version_id="RVV-000002",
            review_revision_id="RVR-000002",
            review_item_ids=(),
            reopen_reason="Required correction.",
            opened_by="reviewer@example.com",
            timestamp="2026-08-06T18:30:00Z",
        )


def test_predecessor_item_id_cannot_be_reused(
    tmp_path: Path,
) -> None:
    version, revision = (
        _finalized_predecessor(tmp_path)
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="must not reuse",
    ):
        create_reopened_review_version_bundle(
            version,
            revision,
            review_document_version_id="RVV-000002",
            review_revision_id="RVR-000002",
            review_item_ids=("RIT-000001",),
            reopen_reason="Required correction.",
            opened_by="reviewer@example.com",
            timestamp="2026-08-06T18:30:00Z",
        )


def test_reopen_reason_is_required(
    tmp_path: Path,
) -> None:
    version, revision = (
        _finalized_predecessor(tmp_path)
    )

    with pytest.raises(
        ReviewValidationError,
        match="reopen_reason",
    ):
        create_reopened_review_version_bundle(
            version,
            revision,
            review_document_version_id="RVV-000002",
            review_revision_id="RVR-000002",
            review_item_ids=("RIT-000002",),
            reopen_reason="",
            opened_by="reviewer@example.com",
            timestamp="2026-08-06T18:30:00Z",
        )
