"""Service orchestration tests for G6.4a finalization."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from modules.review_workspace.errors import (
    ReviewFinalizationBlockedError,
)
from modules.review_workspace.workflow_service import (
    ReviewApprovalWorkflowService,
)


class FakeHumanReviewRepository:
    def __init__(self):
        self.record_calls = []

    def record_decision(
        self,
        project_id,
        target,
        *,
        review_mode,
        decision,
        reviewer_identity,
        rationale=None,
    ):
        self.record_calls.append(
            (
                project_id,
                target,
                review_mode,
                decision,
                reviewer_identity,
                rationale,
            )
        )
        return SimpleNamespace(
            human_review_decision_id="HRD-000001"
        )


class FakeReviewRepository:
    def __init__(self):
        self.calls = []

    def persist_authorized_finalization(
        self,
        value,
    ):
        self.calls.append(
            ("persist_finalization", value)
        )
        return value.finalized_version

    def persist_finalized_artifact_set(
        self,
        value,
    ):
        self.calls.append(
            ("persist_artifacts", value)
        )
        return value


def _preview(
    *,
    eligible=True,
    confirmed=True,
):
    return SimpleNamespace(
        assessment=SimpleNamespace(
            eligible_for_finalization=eligible,
        ),
        eligible_for_confirmation=eligible,
        has_exact_confirmation=confirmed,
        can_finalize=(eligible and confirmed),
    )


def test_record_confirmation_uses_detailed_review_and_exact_target(
    monkeypatch,
):
    from modules.review_workspace import workflow_service as module

    service = object.__new__(
        ReviewApprovalWorkflowService
    )
    human_repo = FakeHumanReviewRepository()
    service._human_review_repository = human_repo
    service._reviewer_identity = (
        lambda value: value
    )
    view = SimpleNamespace()
    preview = _preview(
        eligible=True,
        confirmed=False,
    )
    service._finalization_context = (
        lambda *args: (view, preview)
    )

    target = SimpleNamespace(marker="target")
    monkeypatch.setattr(
        module,
        "create_review_document_finalization_target",
        lambda assessment: target,
    )

    result = service.record_finalization_decision(
        "123456",
        "RVD-000001",
        "RVV-000001",
        decision="confirm",
        reviewer_identity="Reviewer A",
    )

    assert (
        result.human_review_decision_id
        == "HRD-000001"
    )
    assert human_repo.record_calls == [
        (
            "123456",
            target,
            "detailed_review",
            "confirm",
            "Reviewer A",
            None,
        )
    ]


def test_confirmation_is_blocked_when_fresh_assessment_is_ineligible():
    service = object.__new__(
        ReviewApprovalWorkflowService
    )
    service._finalization_context = (
        lambda *args: (
            SimpleNamespace(),
            _preview(
                eligible=False,
                confirmed=False,
            ),
        )
    )

    with pytest.raises(
        ReviewFinalizationBlockedError,
        match="blocking",
    ):
        service.record_finalization_decision(
            "123456",
            "RVD-000001",
            "RVV-000001",
            decision="confirm",
            reviewer_identity="Reviewer A",
        )


def test_finalize_requires_exact_current_confirmation():
    service = object.__new__(
        ReviewApprovalWorkflowService
    )
    service._finalization_context = (
        lambda *args: (
            SimpleNamespace(),
            _preview(
                eligible=True,
                confirmed=False,
            ),
        )
    )

    with pytest.raises(
        ReviewFinalizationBlockedError,
        match="exact",
    ):
        service.finalize_review_version(
            "123456",
            "RVD-000001",
            "RVV-000001",
        )


def test_finalize_builds_before_persist_and_publishes_exact_order(
    monkeypatch,
):
    from modules.review_workspace import workflow_service as module

    service = object.__new__(
        ReviewApprovalWorkflowService
    )
    review_repo = FakeReviewRepository()
    service._review_repository = review_repo
    service._human_review_repository = (
        SimpleNamespace()
    )
    service._timestamp = (
        lambda: "2026-08-08T12:05:00Z"
    )

    document = SimpleNamespace()
    version = SimpleNamespace()
    revision = SimpleNamespace(
        review_revision_id="RVR-000001"
    )
    view = SimpleNamespace(
        document=document,
        version=version,
        revision=revision,
    )
    preview = _preview(
        eligible=True,
        confirmed=True,
    )
    service._finalization_context = (
        lambda *args: (view, preview)
    )

    finalized_version = SimpleNamespace(
        version_state="finalized",
        finalized_revision_id="RVR-000001",
    )
    authorization = SimpleNamespace(
        human_review_decision_id="HRD-000001"
    )
    authorized = SimpleNamespace(
        finalized_version=finalized_version,
        authorization=authorization,
    )
    artifact_set = SimpleNamespace(
        artifacts=(
            SimpleNamespace(filename="reviewed_document.json"),
            SimpleNamespace(filename="effective_decisions.json"),
            SimpleNamespace(filename="reviewed_report.md"),
        )
    )

    call_order = []

    def fake_authorize(*args, **kwargs):
        call_order.append("authorize")
        return authorized

    def fake_build(*args, **kwargs):
        call_order.append("build")
        return artifact_set

    monkeypatch.setattr(
        module,
        "authorize_persisted_review_document_finalization",
        fake_authorize,
    )
    monkeypatch.setattr(
        module,
        "build_finalized_review_artifact_set",
        fake_build,
    )

    original_persist_finalization = (
        review_repo.persist_authorized_finalization
    )
    original_persist_artifacts = (
        review_repo.persist_finalized_artifact_set
    )

    def persist_finalization(value):
        call_order.append("persist_finalization")
        return original_persist_finalization(value)

    def persist_artifacts(value):
        call_order.append("persist_artifacts")
        return original_persist_artifacts(value)

    review_repo.persist_authorized_finalization = (
        persist_finalization
    )
    review_repo.persist_finalized_artifact_set = (
        persist_artifacts
    )

    service.workspace_view = lambda *args: SimpleNamespace(
        version=finalized_version,
    )

    result = service.finalize_review_version(
        "123456",
        "RVD-000001",
        "RVV-000001",
    )

    assert call_order == [
        "authorize",
        "build",
        "persist_finalization",
        "persist_artifacts",
    ]
    assert result.artifact_filenames == (
        "reviewed_document.json",
        "effective_decisions.json",
        "reviewed_report.md",
    )
