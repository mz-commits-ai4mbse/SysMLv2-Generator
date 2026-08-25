from modules.sysml_generation.authority_backed import (
    AuthorityBackedSysMLArtifactRepository,
)
from tests.test_authority_backed_sysml_generation import _source_model


def test_authority_backed_sysml_repository_round_trips(tmp_path):
    model = _source_model()
    repo = AuthorityBackedSysMLArtifactRepository(tmp_path)

    artifact = repo.generate(model)
    loaded = repo.load(
        "120412",
        model.internal_engineering_model_id,
    )

    assert loaded == artifact
    generated = (
        tmp_path
        / "120412"
        / "generated_sysml_v2"
        / model.internal_engineering_model_id
        / "generated"
        / artifact.units[0].relative_path
    )
    assert generated.read_text(encoding="utf-8") == (
        artifact.units[0].content
    )
