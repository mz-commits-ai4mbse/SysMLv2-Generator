from modules.internal_model.authority_backed import (
    AuthorityBackedInternalModelRepository,
    authority_backed_internal_model_to_json,
)
from tests.test_authority_backed_internal_model import (
    _draft,
    _final,
    _profile,
    _template,
)


def test_repository_persists_v2_model_and_never_serializes_fake_mcd(tmp_path):
    repo = AuthorityBackedInternalModelRepository(tmp_path)

    model = repo.materialize(
        draft=_draft(),
        final_decision=_final(),
        profile=_profile(),
        framework_template=_template(),
    )

    assert model.internal_engineering_model_id == "IEM-000001"
    assert repo.find_by_comparison("120412", "1" * 64) == model
    serialized = authority_backed_internal_model_to_json(model)
    assert "MCD-" not in serialized
    assert "model_candidate_review" not in serialized


def test_repository_allocates_after_legacy_iem_ids(tmp_path):
    legacy = (
        tmp_path
        / "120412"
        / "internal_models"
        / "IEM-000007"
    )
    legacy.mkdir(parents=True)

    repo = AuthorityBackedInternalModelRepository(tmp_path)
    model = repo.materialize(
        draft=_draft(),
        final_decision=_final(),
        profile=_profile(),
        framework_template=_template(),
    )

    assert model.internal_engineering_model_id == "IEM-000008"
