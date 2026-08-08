"""Service orchestration tests for G6.3c1 scoped actions."""

from types import SimpleNamespace

from modules.review_workspace.scoped_workflow import (
    ReviewItemFilterFact,
    ScopedReviewActionRequest,
)
from modules.review_workspace.workflow_service import (
    ReviewApprovalWorkflowService,
)


class FakeRepository:
    def __init__(self):
        self.calls = []

    def next_scoped_action_id(self, *args):
        self.calls.append(("next_action", args))
        return "SRA-000001"

    def next_revision_id(self, *args):
        self.calls.append(("next_revision", args))
        return "RVR-000002"

    def persist_scoped_action(self, action):
        self.calls.append(("persist_action", action))

    def append_revision(self, revision):
        self.calls.append(("append_revision", revision))


def test_apply_scoped_action_persists_action_before_referencing_revision(
    monkeypatch,
):
    from modules.review_workspace import workflow_service as module

    service = object.__new__(
        ReviewApprovalWorkflowService
    )
    repo = FakeRepository()
    service._review_repository = repo

    revision = SimpleNamespace(
        review_revision_id="RVR-000001"
    )
    view = SimpleNamespace(
        revision=revision,
    )
    service._draft_workspace_view = lambda *args: view
    service.review_filter_facts = lambda *args: (
        ReviewItemFilterFact(
            review_item_id="RIT-000001",
            item_content_fingerprint="a" * 64,
            review_status="open",
            review_item_kind="element",
            proposed_classifications=(),
            effective_classifications=(),
            proposed_framework_assignments=(),
            effective_framework_assignments=(),
            agent_identities=(),
            confidence_levels=(),
            consensus_states=("not_available",),
            agent_disagreement_state="not_available",
            human_modification_state="unmodified",
            source_identities=("SRC-000001",),
            evidence_sufficiency_state="not_assessed",
            relationship_validation_status="not_applicable",
        ),
    )
    service._timestamp = lambda: "2026-08-08T08:05:00Z"
    service.workspace_view = lambda *args: SimpleNamespace(
        marker="reloaded"
    )

    action = SimpleNamespace(scoped_review_action_id="SRA-000001")
    successor = SimpleNamespace(review_revision_id="RVR-000002")

    monkeypatch.setattr(
        module,
        "create_scoped_review_action_mutation",
        lambda *args, **kwargs: SimpleNamespace(
            action=action,
            revision=successor,
        ),
    )

    result = service.apply_scoped_action(
        "123456",
        "RVD-000001",
        "RVV-000001",
        request=ScopedReviewActionRequest(
            expected_revision_id="RVR-000001",
            action_scope="explicit_selection",
            decision_dimension="source_assignment",
            selected_values=("SRC_INFO_001",),
            explicit_review_item_ids=("RIT-000001",),
        ),
        actor_identity="Reviewer A",
    )

    assert [call[0] for call in repo.calls] == [
        "next_action",
        "next_revision",
        "persist_action",
        "append_revision",
    ]
    assert result.marker == "reloaded"
