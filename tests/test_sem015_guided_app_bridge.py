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

def test_refined_model_materialization_normalizes_dataclass_authorities_for_repository(
    tmp_path,
    monkeypatch,
):
    from dataclasses import dataclass

    import modules.internal_model.semantic_successor as semantic_successor

    @dataclass(frozen=True)
    class Decision:
        decision_id: str

    @dataclass(frozen=True)
    class Authority:
        authority_set_id: str
        effective_decisions: tuple[Decision, ...]

    captured = {}
    expected = object()

    class FakeRepository:
        def __init__(self, root):
            captured["root"] = root

        def materialize(
            self,
            *,
            source,
            target_model_formulation_authority,
            model_quality_authority,
        ):
            captured["source"] = source
            captured["tfa"] = target_model_formulation_authority
            captured["mqa"] = model_quality_authority
            return expected

    monkeypatch.setattr(
        semantic_successor,
        "SEM015InternalModelSuccessorRepository",
        FakeRepository,
    )

    service = object.__new__(GuidedWorkflowWriteService)
    service.project_root = tmp_path

    source = SimpleNamespace(project_id="120412")
    tfa = Authority(
        authority_set_id="TFA-000001",
        effective_decisions=(Decision("TFD-000001"),),
    )
    mqa = Authority(
        authority_set_id="MQA-000001",
        effective_decisions=(
            Decision("MQD-000001"),
            Decision("MQD-000002"),
        ),
    )

    result = service.materialize_refined_internal_model(
        "120412",
        source_snapshot=source,
        target_model_formulation_authority=tfa,
        model_quality_authority=mqa,
    )

    assert result is expected
    assert captured["source"] is source

    assert isinstance(captured["tfa"]["effective_decisions"], list)
    assert captured["tfa"]["effective_decisions"] == [
        {"decision_id": "TFD-000001"}
    ]

    assert isinstance(captured["mqa"]["effective_decisions"], list)
    assert captured["mqa"]["effective_decisions"] == [
        {"decision_id": "MQD-000001"},
        {"decision_id": "MQD-000002"},
    ]
