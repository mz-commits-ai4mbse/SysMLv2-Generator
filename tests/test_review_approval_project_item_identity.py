"""Regression tests for project-wide Review Item identity allocation."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from modules.review_workspace.errors import ReviewIntegrityError
from modules.review_workspace.review_document_assembly import (
    assemble_initial_review_document,
)
from modules.review_workspace.workflow_service import (
    ReviewApprovalWorkflowService,
)

from tests.test_review_workspace_review_document_assembly import (
    _inputs,
)


def test_initial_assembly_reserves_existing_project_review_item_ids(
    tmp_path,
):
    selected = assemble_initial_review_document(
        **_inputs(tmp_path),
        review_document_id="RVD-000002",
        review_document_version_id="RVV-000001",
        review_revision_id="RVR-000001",
        opened_by="reviewer@example.com",
        timestamp="2026-08-08T08:30:00Z",
        occupied_review_item_ids=(
            "RIT-000001",
            "RIT-000002",
        ),
    )

    created_ids = tuple(
        item.review_item_id
        for item in selected.initial_revision.review_items
    )

    assert set(created_ids).isdisjoint(
        {"RIT-000001", "RIT-000002"}
    )
    assert tuple(sorted(created_ids)) == (
        "RIT-000003",
        "RIT-000004",
        "RIT-000005",
        "RIT-000006",
    )


def _revision(
    *,
    document_id,
    item_id,
    stable_subject_key,
):
    return SimpleNamespace(
        review_items=(
            SimpleNamespace(
                review_item_id=item_id,
                review_document_id=document_id,
                stable_subject_key=stable_subject_key,
            ),
        )
    )


class FakeReviewRepository:
    def __init__(self, revisions, issues=()):
        self.revisions = tuple(revisions)
        self.issues = tuple(issues)

    def scan_project(self, project_id):
        return SimpleNamespace(
            revisions=self.revisions,
            issues=self.issues,
        )


def _service(repository):
    service = object.__new__(
        ReviewApprovalWorkflowService
    )
    service._review_repository = repository
    return service


def test_project_identity_scan_deduplicates_same_item_across_revisions():
    repository = FakeReviewRepository(
        (
            _revision(
                document_id="RVD-000001",
                item_id="RIT-000001",
                stable_subject_key="subject-a",
            ),
            _revision(
                document_id="RVD-000001",
                item_id="RIT-000001",
                stable_subject_key="subject-a",
            ),
            _revision(
                document_id="RVD-000001",
                item_id="RIT-000002",
                stable_subject_key="subject-b",
            ),
        )
    )

    assert _service(
        repository
    )._occupied_review_item_ids(
        "123456"
    ) == (
        "RIT-000001",
        "RIT-000002",
    )


def test_project_identity_scan_rejects_reused_id_for_other_subject():
    repository = FakeReviewRepository(
        (
            _revision(
                document_id="RVD-000001",
                item_id="RIT-000001",
                stable_subject_key="subject-a",
            ),
            _revision(
                document_id="RVD-000002",
                item_id="RIT-000001",
                stable_subject_key="subject-b",
            ),
        )
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="multiple Review Item identities",
    ):
        _service(
            repository
        )._occupied_review_item_ids(
            "123456"
        )
