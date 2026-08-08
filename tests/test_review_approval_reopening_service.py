"""Service tests for G6.4c reopening orchestration."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from modules.review_workspace.errors import (
    ReviewFinalizationBlockedError,
    ReviewIntegrityError,
)
from modules.review_workspace.workflow_service import (
    ReviewApprovalWorkflowService,
)


class FakeRepository:
    def __init__(self, bundle):
        self.bundle = bundle
        self.calls = []

    def reopen_finalized_version(
        self,
        *args,
        reopen_reason,
        opened_by,
        timestamp,
    ):
        self.calls.append(
            (
                args,
                reopen_reason,
                opened_by,
                timestamp,
            )
        )
        return self.bundle


def _bundle():
    version = SimpleNamespace(
        review_document_version_id="RVV-000002",
        predecessor_version_id="RVV-000001",
        version_state="draft",
        head_revision_id="RVR-000002",
    )
    revision = SimpleNamespace(
        review_revision_id="RVR-000002",
    )
    return SimpleNamespace(
        predecessor_version_id="RVV-000001",
        version=version,
        initial_revision=revision,
        review_item_id_mapping=(
            ("RIT-000001", "RIT-000002"),
        ),
    )


def test_reopen_service_rejects_nonfinalized_predecessor():
    service = object.__new__(
        ReviewApprovalWorkflowService
    )
    service.workspace_view = lambda *args: SimpleNamespace(
        version=SimpleNamespace(
            version_state="draft",
        )
    )

    with pytest.raises(
        ReviewFinalizationBlockedError,
        match="finalized",
    ):
        service.reopen_review_version(
            "123456",
            "RVD-000001",
            "RVV-000001",
            reopen_reason="Clarify requirement.",
            actor_identity="Reviewer A",
        )


def test_reopen_service_delegates_exact_repository_transition_and_reloads():
    bundle = _bundle()
    repository = FakeRepository(bundle)

    service = object.__new__(
        ReviewApprovalWorkflowService
    )
    service._review_repository = repository
    service._timestamp = (
        lambda: "2026-08-08T13:30:00Z"
    )

    calls = []

    def workspace_view(
        project_id,
        document_id,
        version_id,
    ):
        calls.append(
            (
                project_id,
                document_id,
                version_id,
            )
        )

        if version_id == "RVV-000001":
            return SimpleNamespace(
                version=SimpleNamespace(
                    version_state="finalized",
                ),
            )

        return SimpleNamespace(
            version=bundle.version,
            revision=bundle.initial_revision,
        )

    service.workspace_view = workspace_view

    result = service.reopen_review_version(
        "123456",
        "RVD-000001",
        "RVV-000001",
        reopen_reason="Clarify requirement.",
        actor_identity="Reviewer A",
    )

    assert result is bundle
    assert repository.calls == [
        (
            (
                "123456",
                "RVD-000001",
                "RVV-000001",
            ),
            "Clarify requirement.",
            "Reviewer A",
            "2026-08-08T13:30:00Z",
        )
    ]
    assert calls == [
        (
            "123456",
            "RVD-000001",
            "RVV-000001",
        ),
        (
            "123456",
            "RVD-000001",
            "RVV-000002",
        ),
    ]


def test_reopen_service_fails_closed_on_mismatched_repository_result():
    bundle = _bundle()
    bundle.version.predecessor_version_id = (
        "RVV-000099"
    )

    service = object.__new__(
        ReviewApprovalWorkflowService
    )
    service._review_repository = FakeRepository(
        bundle
    )
    service._timestamp = (
        lambda: "2026-08-08T13:30:00Z"
    )
    service.workspace_view = lambda *args: SimpleNamespace(
        version=SimpleNamespace(
            version_state="finalized",
        ),
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="predecessor",
    ):
        service.reopen_review_version(
            "123456",
            "RVD-000001",
            "RVV-000001",
            reopen_reason="Clarify requirement.",
            actor_identity="Reviewer A",
        )
