from types import SimpleNamespace

from modules.guided_workflow.write_service import GuidedWorkflowWriteService


class _ValidationRepo:
    def __init__(self):
        self.calls = []

    def load_if_available(self, project_id, iem_id):
        self.calls.append(("load", project_id, iem_id))
        return "validation"

    def validate(self, artifact):
        self.calls.append(("validate", artifact))
        return "validated"


def _service(repo):
    inert = SimpleNamespace()
    return GuidedWorkflowWriteService(
        ".",
        candidate_review_repository=inert,
        model_derivation_service=inert,
        model_placement_review_repository=inert,
        model_assembly_repository=inert,
        model_assembly_final_review_repository=inert,
        authority_backed_internal_model_repository=inert,
        authority_backed_sysml_repository=inert,
        authority_backed_sysml_validation_repository=repo,
        final_review_repository=inert,
        final_change_service=inert,
        final_release_service=inert,
        final_publication_service=inert,
    )


def test_guided_workflow_loads_authority_validation():
    repo = _ValidationRepo()
    service = _service(repo)

    assert service.load_authority_backed_sysml_validation(
        "120412",
        "IEM-000001",
    ) == "validation"


def test_guided_workflow_runs_authority_validation():
    repo = _ValidationRepo()
    service = _service(repo)
    artifact = SimpleNamespace(project_id="120412")

    assert service.validate_authority_backed_sysml(
        "120412",
        artifact=artifact,
    ) == "validated"
