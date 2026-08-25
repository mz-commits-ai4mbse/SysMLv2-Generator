from modules.model_assembly.repository import ModelAssemblyRepository


def test_optional_load_returns_none_when_no_draft_exists(tmp_path):
    repo = ModelAssemblyRepository(tmp_path)

    assert repo.load_if_available("120412", "a" * 64) is None
