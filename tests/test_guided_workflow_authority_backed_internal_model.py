from types import SimpleNamespace

from modules.guided_workflow.write_service import GuidedWorkflowWriteService


class _InternalRepo:
    def __init__(self):
        self.calls = []

    def find_by_comparison(self, project_id, fingerprint):
        self.calls.append(("find", project_id, fingerprint))
        return "existing"

    def materialize(self, **kwargs):
        self.calls.append(("materialize", kwargs))
        return "materialized"


def _service(internal_repo):
    inert = SimpleNamespace()
    return GuidedWorkflowWriteService(
        ".",
        candidate_review_repository=inert,
        model_derivation_service=inert,
        model_placement_review_repository=inert,
        model_assembly_repository=inert,
        model_assembly_final_review_repository=inert,
        authority_backed_internal_model_repository=internal_repo,
        final_review_repository=inert,
        final_change_service=inert,
        final_release_service=inert,
        final_publication_service=inert,
    )


def test_guided_workflow_reads_materialized_internal_model():
    repo = _InternalRepo()
    service = _service(repo)

    result = service.load_authority_backed_internal_model(
        "120412",
        "a" * 64,
    )

    assert result == "existing"


def test_guided_workflow_materializes_only_exact_bound_authority():
    repo = _InternalRepo()
    service = _service(repo)
    draft = SimpleNamespace(
        project_id="120412",
        comparison_fingerprint="a" * 64,
    )
    final = SimpleNamespace(project_id="120412")
    profile = SimpleNamespace()
    template = {}

    result = service.materialize_authority_backed_internal_model(
        "120412",
        draft=draft,
        final_decision=final,
        profile=profile,
        framework_template=template,
    )

    assert result == "materialized"
    assert repo.calls[0][0] == "materialize"
