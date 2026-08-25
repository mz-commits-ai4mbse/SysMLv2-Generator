from types import SimpleNamespace

from modules.guided_workflow.write_service import GuidedWorkflowWriteService


class _PlacementRepo:
    def __init__(self):
        self.calls = []

    def finalize_approved_placement_set(self, project_id, fingerprint, **kwargs):
        self.calls.append((project_id, fingerprint, kwargs))
        return "approved-placement-set"


def test_guided_workflow_delegates_placement_finalization():
    placement_repo = _PlacementRepo()
    inert = SimpleNamespace()
    service = GuidedWorkflowWriteService(
        ".",
        candidate_review_repository=inert,
        model_derivation_service=inert,
        model_placement_review_repository=placement_repo,
        final_review_repository=inert,
        final_change_service=inert,
        final_release_service=inert,
        final_publication_service=inert,
    )
    profile = SimpleNamespace()

    result = service.finalize_model_placement_review(
        "120412",
        "a" * 64,
        profile=profile,
    )

    assert result == "approved-placement-set"
    assert placement_repo.calls[0][0] == "120412"
    assert placement_repo.calls[0][2]["profile"] is profile
