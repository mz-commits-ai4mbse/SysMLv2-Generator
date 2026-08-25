from types import SimpleNamespace

from modules.guided_workflow.write_service import GuidedWorkflowWriteService


class _FinalRepo:
    def __init__(self):
        self.calls = []

    def latest_decision(self, project_id, fingerprint):
        self.calls.append(("latest", project_id, fingerprint))
        return "latest"

    def record(self, **kwargs):
        self.calls.append(("record", kwargs))
        return "recorded"


def _service(repo):
    inert = SimpleNamespace()
    return GuidedWorkflowWriteService(
        ".",
        candidate_review_repository=inert,
        model_derivation_service=inert,
        model_placement_review_repository=inert,
        model_assembly_repository=inert,
        model_assembly_final_review_repository=repo,
        final_review_repository=inert,
        final_change_service=inert,
        final_release_service=inert,
        final_publication_service=inert,
    )


def test_guided_workflow_reads_final_model_decision():
    repo = _FinalRepo()
    service = _service(repo)

    result = service.load_model_final_review_decision(
        "120412",
        "a" * 64,
    )

    assert result == "latest"
    assert repo.calls == [("latest", "120412", "a" * 64)]


def test_guided_workflow_records_whole_model_decision():
    repo = _FinalRepo()
    service = _service(repo)
    draft = SimpleNamespace(
        project_id="120412",
        comparison_fingerprint="a" * 64,
    )
    profile = SimpleNamespace()

    result = service.record_model_final_review_decision(
        "120412",
        draft=draft,
        profile=profile,
        decision="approved",
        selected_relationship_rules={},
        reviewer_identity="MZ",
        rationale=None,
    )

    assert result == "recorded"
    assert repo.calls[0][0] == "record"
    assert repo.calls[0][1]["decision"] == "approved"
