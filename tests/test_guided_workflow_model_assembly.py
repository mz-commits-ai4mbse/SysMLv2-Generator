from types import SimpleNamespace

from modules.guided_workflow.write_service import GuidedWorkflowWriteService


class _Derivation:
    def __init__(self):
        self.calls = []

    def assemble_model_draft(self, project_id, comparison_fingerprint, **kwargs):
        self.calls.append((project_id, comparison_fingerprint, kwargs))
        return "assembly-draft"


def test_guided_workflow_delegates_model_assembly():
    derivation = _Derivation()
    inert = SimpleNamespace()
    service = GuidedWorkflowWriteService(
        ".",
        candidate_review_repository=inert,
        model_derivation_service=derivation,
        model_placement_review_repository=inert,
        final_review_repository=inert,
        final_change_service=inert,
        final_release_service=inert,
        final_publication_service=inert,
    )

    result = service.assemble_model_draft(
        "120412",
        "a" * 64,
        provider="openai",
        model="gpt-test",
        api_key="key",
    )

    assert result == "assembly-draft"
    assert derivation.calls[0][0] == "120412"
    assert derivation.calls[0][1] == "a" * 64
    assert derivation.calls[0][2]["model"] == "gpt-test"
