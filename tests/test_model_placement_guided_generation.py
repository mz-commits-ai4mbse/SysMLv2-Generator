from types import SimpleNamespace

from modules.guided_workflow.write_service import (
    GuidedWorkflowWriteService,
)


class _Derivation:
    def __init__(self):
        self.calls = []

    def prepare_model_placement_review(self, project_id, **kwargs):
        self.calls.append((project_id, kwargs))
        return "comparison"


def test_guided_write_service_delegates_placement_generation():
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

    result = service.generate_model_placement_review(
        "120412",
        mode="llm_assisted",
        provider="openai",
        model="gpt-5.4-mini",
        api_key="test",
    )

    assert result == "comparison"
    assert derivation.calls[0][0] == "120412"
    assert derivation.calls[0][1]["mode"] == "llm_assisted"
