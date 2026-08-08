"""Service tests for G6.3b1 Review structure commands."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from modules.review_workspace.errors import ReviewIntegrityError
from modules.review_workspace.workflow_service import (
    ReviewApprovalWorkflowService,
)


class FakeRepository:
    def __init__(self, occupied=()):
        self.occupied = tuple(occupied)
        self.appended = []

    def scan_project(self, project_id):
        revisions = tuple(
            SimpleNamespace(
                review_items=(
                    SimpleNamespace(
                        review_item_id=item_id,
                        review_document_id="RVD-000099",
                        stable_subject_key=f"subject:{item_id.lower()}",
                    ),
                )
            )
            for item_id in self.occupied
        )
        return SimpleNamespace(
            revisions=revisions,
            issues=(),
        )

    def append_revision(self, revision):
        self.appended.append(revision)


def test_project_allocator_returns_sequential_non_reused_ids():
    service = object.__new__(
        ReviewApprovalWorkflowService
    )
    service._review_repository = FakeRepository(
        occupied=(
            "RIT-000001",
            "RIT-000002",
        )
    )

    occupied, allocated = (
        service._allocate_project_review_item_ids(
            "123456",
            2,
        )
    )

    assert occupied == (
        "RIT-000001",
        "RIT-000002",
    )
    assert allocated == (
        "RIT-000003",
        "RIT-000004",
    )


def test_project_allocator_recheck_fails_closed_on_concurrent_change():
    service = object.__new__(
        ReviewApprovalWorkflowService
    )
    repository = FakeRepository(
        occupied=("RIT-000001",)
    )
    service._review_repository = repository

    occupied, _ = (
        service._allocate_project_review_item_ids(
            "123456",
            1,
        )
    )
    repository.occupied = (
        "RIT-000001",
        "RIT-000002",
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="allocation changed",
    ):
        service._assert_project_review_item_allocation_unchanged(
            "123456",
            occupied,
        )
