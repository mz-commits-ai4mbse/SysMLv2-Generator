from types import SimpleNamespace

from modules.guided_workflow.write_service import (
    GuidedWorkflowWriteService,
)


class _PlacementRepository:
    def __init__(self):
        self.calls = []

    def list_comparisons(self, project_id):
        self.calls.append(("list", project_id))
        return ("comparison",)

    def review_state(self, project_id, fingerprint):
        self.calls.append(("state", project_id, fingerprint))
        return "state"

    def record_decision(self, project_id, fingerprint, **kwargs):
        self.calls.append(("record", project_id, fingerprint, kwargs))
        return "decision"

    def reopen_decision(self, project_id, fingerprint, **kwargs):
        self.calls.append(("reopen", project_id, fingerprint, kwargs))
        return "reopened"


def _service(repo):
    inert = SimpleNamespace()
    return GuidedWorkflowWriteService(
        ".",
        candidate_review_repository=inert,
        model_derivation_service=inert,
        model_placement_review_repository=repo,
        final_review_repository=inert,
        final_change_service=inert,
        final_release_service=inert,
        final_publication_service=inert,
    )


def test_guided_workflow_lists_model_placement_comparisons():
    repo = _PlacementRepository()
    service = _service(repo)

    assert service.list_model_placement_comparisons("120412") == (
        "comparison",
    )
    assert repo.calls == [("list", "120412")]


def test_guided_workflow_delegates_model_placement_decision():
    repo = _PlacementRepository()
    service = _service(repo)

    result = service.record_model_placement_review_decision(
        "120412",
        "a" * 64,
        approved_input_id="AIN-000001",
        outcome="accepted",
        selected_rule_id="ELEMENT_SYSTEM_FUNCTION",
        reviewer_identity="MZ",
        rationale="system level",
    )

    assert result == "decision"
    assert repo.calls[0][0] == "record"
    assert repo.calls[0][3]["selected_rule_id"] == (
        "ELEMENT_SYSTEM_FUNCTION"
    )


def test_guided_workflow_delegates_reopen():
    repo = _PlacementRepository()
    service = _service(repo)

    result = service.reopen_model_placement_review_decision(
        "120412",
        "a" * 64,
        approved_input_id="AIN-000001",
        reviewer_identity="MZ",
        rationale="reconsider",
    )

    assert result == "reopened"
    assert repo.calls[0][0] == "reopen"
