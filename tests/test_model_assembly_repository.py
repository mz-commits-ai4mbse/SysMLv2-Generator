from modules.model_assembly.builder import build_model_assembly_draft
from modules.model_assembly.repository import ModelAssemblyRepository
from tests.test_model_assembly_draft import (
    _placement_set,
    _profile,
    _request,
)


def test_model_assembly_draft_round_trips_immutably(tmp_path):
    draft = build_model_assembly_draft(
        request=_request(),
        approved_placement_set=_placement_set(),
        profile=_profile(),
    )
    repo = ModelAssemblyRepository(tmp_path)

    persisted = repo.persist(draft)
    loaded = repo.load("120412", "e" * 64)

    assert persisted == draft
    assert loaded == draft
