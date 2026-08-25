from types import SimpleNamespace

from modules.guided_workflow.write_service import GuidedWorkflowWriteService


class _IEMRepo:
    def __init__(self, model):
        self.model = model

    def load(self, project_id, iem_id):
        assert project_id == "120412"
        assert iem_id == "IEM-000002"
        return self.model


def _service(tmp_path, model):
    service = object.__new__(GuidedWorkflowWriteService)
    service.project_root = tmp_path
    service._authority_backed_internal_models = _IEMRepo(model)
    return service


def test_successor_discovery_is_explicit_and_bound_to_source(tmp_path):
    root = (
        tmp_path
        / "data/projects/120412/internal_models_v2/IEM-000002"
    )
    root.mkdir(parents=True)
    (root / "semantic_authority.json").write_text(
        '{"authority_binding":{"source_internal_engineering_model_id":"IEM-000001","target_model_formulation_authority_set_id":"TFA-000003","model_quality_authority_set_id":"MQA-000001","intentionally_not_materialized_relationship_ids":["IMR-000001","IMR-000003"]}}',
        encoding="utf-8",
    )
    model = SimpleNamespace(
        internal_engineering_model_id="IEM-000002",
    )
    result = _service(tmp_path, model).list_sem015_successor_internal_models(
        "120412",
        "IEM-000001",
    )

    assert len(result) == 1
    assert result[0]["model"] is model
    assert result[0]["target_model_formulation_authority_set_id"] == "TFA-000003"
    assert result[0]["model_quality_authority_set_id"] == "MQA-000001"
    assert result[0]["intentionally_not_materialized_relationship_ids"] == (
        "IMR-000001",
        "IMR-000003",
    )


def test_successor_discovery_does_not_return_other_source(tmp_path):
    root = (
        tmp_path
        / "data/projects/120412/internal_models_v2/IEM-000002"
    )
    root.mkdir(parents=True)
    (root / "semantic_authority.json").write_text(
        '{"authority_binding":{"source_internal_engineering_model_id":"IEM-999999"}}',
        encoding="utf-8",
    )
    service = _service(
        tmp_path,
        SimpleNamespace(internal_engineering_model_id="IEM-000002"),
    )
    assert service.list_sem015_successor_internal_models(
        "120412",
        "IEM-000001",
    ) == ()
