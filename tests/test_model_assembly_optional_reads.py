from types import SimpleNamespace

from modules.guided_workflow.write_service import GuidedWorkflowWriteService


class _PlacementRepo:
    def load_approved_placement_set_if_available(
        self,
        project_id,
        fingerprint,
    ):
        return ("placement", project_id, fingerprint)


class _AssemblyRepo:
    def load_if_available(self, project_id, fingerprint):
        return ("assembly", project_id, fingerprint)


def _service():
    inert = SimpleNamespace()
    return GuidedWorkflowWriteService(
        ".",
        candidate_review_repository=inert,
        model_derivation_service=inert,
        model_placement_review_repository=_PlacementRepo(),
        model_assembly_repository=_AssemblyRepo(),
        final_review_repository=inert,
        final_change_service=inert,
        final_release_service=inert,
        final_publication_service=inert,
    )


def test_optional_placement_authority_read_is_delegated():
    service = _service()

    assert service.load_finalized_model_placement_set(
        "120412",
        "a" * 64,
    ) == ("placement", "120412", "a" * 64)


def test_optional_assembly_read_is_delegated():
    service = _service()

    assert service.load_model_assembly_draft(
        "120412",
        "a" * 64,
    ) == ("assembly", "120412", "a" * 64)
