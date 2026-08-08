"""Tests for G6.4b finalized artifact authority access."""

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
    def __init__(self, artifact_set):
        self.artifact_set = artifact_set
        self.calls = []

    def load_finalized_artifact_set(self, *args):
        self.calls.append(args)
        return self.artifact_set


def _artifact_set(
    *,
    project_id="123456",
    document_id="RVD-000001",
    version_id="RVV-000001",
    revision_id="RVR-000001",
):
    return SimpleNamespace(
        reviewed_document=SimpleNamespace(
            project_id=project_id,
            review_document_id=document_id,
            review_document_version_id=version_id,
            review_revision_id=revision_id,
        )
    )


def test_finalized_artifact_set_requires_finalized_version():
    service = object.__new__(
        ReviewApprovalWorkflowService
    )
    service.workspace_view = lambda *args: SimpleNamespace(
        version=SimpleNamespace(
            version_state="draft",
        ),
        revision=SimpleNamespace(
            review_revision_id="RVR-000001",
        ),
    )
    service._review_repository = FakeRepository(
        _artifact_set()
    )

    with pytest.raises(
        ReviewFinalizationBlockedError,
        match="finalized",
    ):
        service.finalized_artifact_set(
            "123456",
            "RVD-000001",
            "RVV-000001",
        )


def test_finalized_artifact_set_binds_exact_selected_authority():
    artifact_set = _artifact_set()
    repository = FakeRepository(
        artifact_set
    )
    service = object.__new__(
        ReviewApprovalWorkflowService
    )
    service.workspace_view = lambda *args: SimpleNamespace(
        version=SimpleNamespace(
            version_state="finalized",
        ),
        revision=SimpleNamespace(
            review_revision_id="RVR-000001",
        ),
    )
    service._review_repository = repository

    result = service.finalized_artifact_set(
        "123456",
        "RVD-000001",
        "RVV-000001",
    )

    assert result is artifact_set
    assert repository.calls == [
        (
            "123456",
            "RVD-000001",
            "RVV-000001",
        )
    ]


def test_finalized_artifact_set_rejects_wrong_revision_binding():
    service = object.__new__(
        ReviewApprovalWorkflowService
    )
    service.workspace_view = lambda *args: SimpleNamespace(
        version=SimpleNamespace(
            version_state="finalized",
        ),
        revision=SimpleNamespace(
            review_revision_id="RVR-000001",
        ),
    )
    service._review_repository = FakeRepository(
        _artifact_set(
            revision_id="RVR-000099",
        )
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="exact",
    ):
        service.finalized_artifact_set(
            "123456",
            "RVD-000001",
            "RVV-000001",
        )
