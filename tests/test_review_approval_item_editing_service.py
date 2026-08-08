"""Service-bound tests for G6.3a item-level editing."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from modules.review_workspace.errors import (
    ReviewIntegrityError,
)
from modules.review_workspace.types import (
    ReviewItemContent,
)
from modules.review_workspace.workflow_editing import (
    ReviewItemEditRequest,
)


class FakeReviewRepository:
    def __init__(self):
        self.next_calls = []
        self.append_calls = []

    def next_revision_id(
        self,
        project_id,
        review_document_id,
        review_document_version_id,
    ):
        self.next_calls.append(
            (
                project_id,
                review_document_id,
                review_document_version_id,
            )
        )
        return "RVR-000002"

    def append_revision(self, revision):
        self.append_calls.append(revision)


def _content():
    return ReviewItemContent(
        title="Statement",
        primary_text=(
            "The system shall preserve traceability."
        ),
        description=None,
        information_type="requirement",
        modality="shall",
        epistemic_status="asserted",
        human_rationale=None,
        human_confidence=None,
        relationship_representation=None,
    )


def _request():
    return ReviewItemEditRequest(
        expected_revision_id="RVR-000001",
        expected_item_content_fingerprint="a" * 64,
        updated_content=_content(),
        selected_proposal_keys=(),
        review_outcome="accepted_with_modification",
    )


def _view(
    *,
    state="draft",
    revision_id="RVR-000001",
):
    return SimpleNamespace(
        version=SimpleNamespace(
            version_state=state,
        ),
        revision=SimpleNamespace(
            review_revision_id=revision_id,
        ),
    )


def test_service_blocks_finalized_version():
    from modules.review_workspace.workflow_service import (
        ReviewApprovalWorkflowService,
    )

    service = object.__new__(
        ReviewApprovalWorkflowService
    )
    repository = FakeReviewRepository()
    service._review_repository = repository
    service.workspace_view = (
        lambda *args: _view(state="finalized")
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="draft",
    ):
        service.save_item_review(
            "123456",
            "RVD-000001",
            "RVV-000001",
            "RIT-000001",
            request=_request(),
            actor_identity="Reviewer A",
        )

    assert repository.append_calls == []


def test_service_blocks_stale_ui_state_before_id_allocation():
    from modules.review_workspace.workflow_service import (
        ReviewApprovalWorkflowService,
    )

    service = object.__new__(
        ReviewApprovalWorkflowService
    )
    repository = FakeReviewRepository()
    service._review_repository = repository
    service.workspace_view = (
        lambda *args: _view(
            revision_id="RVR-000002"
        )
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="changed",
    ):
        service.save_item_review(
            "123456",
            "RVD-000001",
            "RVV-000001",
            "RIT-000001",
            request=_request(),
            actor_identity="Reviewer A",
        )

    assert repository.next_calls == []
    assert repository.append_calls == []


def test_service_allocates_appends_and_reloads(monkeypatch):
    from modules.review_workspace import (
        workflow_service as module,
    )

    service = object.__new__(
        module.ReviewApprovalWorkflowService
    )
    repository = FakeReviewRepository()
    service._review_repository = repository

    views = [
        _view(),
        SimpleNamespace(marker="reloaded"),
    ]
    service.workspace_view = (
        lambda *args: views.pop(0)
    )
    service._timestamp = (
        lambda: "2026-08-08T08:05:00Z"
    )

    created_revision = SimpleNamespace(
        review_revision_id="RVR-000002"
    )
    calls = []

    def fake_create(current_revision, **kwargs):
        calls.append((current_revision, kwargs))
        return created_revision

    monkeypatch.setattr(
        module,
        "create_item_edit_revision",
        fake_create,
    )

    result = service.save_item_review(
        "123456",
        "RVD-000001",
        "RVV-000001",
        "RIT-000001",
        request=_request(),
        actor_identity="Reviewer A",
    )

    assert repository.next_calls == [
        (
            "123456",
            "RVD-000001",
            "RVV-000001",
        )
    ]
    assert repository.append_calls == [
        created_revision
    ]
    assert calls[0][1][
        "new_review_revision_id"
    ] == "RVR-000002"
    assert calls[0][1][
        "review_item_id"
    ] == "RIT-000001"
    assert calls[0][1][
        "actor_identity"
    ] == "Reviewer A"
    assert calls[0][1][
        "timestamp"
    ] == "2026-08-08T08:05:00Z"
    assert result.marker == "reloaded"
