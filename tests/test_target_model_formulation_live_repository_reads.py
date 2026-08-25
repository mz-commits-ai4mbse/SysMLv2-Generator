import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from target_model_formulation_authority_helpers import review_four

from modules.target_model_formulation.repository import (
    TargetModelFormulationAuthorityRepository,
)


def _complete(repo, review):
    selections = (
        ("IME-000001", "TFC-000001"),
        ("IME-000003", "TFC-000002"),
        ("IMR-000001", "TFC-000003"),
        ("IMR-000003", "TFC-000004"),
    )
    for index, (subject, candidate) in enumerate(selections, start=1):
        repo.record_selection(
            review=review,
            authority_subject_id=subject,
            selected_candidate_id=candidate,
            reviewer_identity="MZ",
            rationale=f"Human decision {index}",
            decided_at=f"2026-08-25T14:{index:02d}:00Z",
        )


def test_review_can_be_loaded_and_found_by_exact_source_iem(tmp_path):
    repo = TargetModelFormulationAuthorityRepository(tmp_path)
    review = review_four()
    repo.record_review(review)

    loaded = repo.load_review("120412", "TFR-000001")
    found = repo.find_review_for_source(
        "120412",
        "IEM-000001",
        "1" * 64,
    )

    assert loaded == review
    assert found == review
    assert repo.allocate_review_id("120412") == "TFR-000002"


def test_persisted_review_tampering_fails_closed(tmp_path):
    repo = TargetModelFormulationAuthorityRepository(tmp_path)
    review = review_four()
    path = repo.record_review(review)
    text = path.read_text(encoding="utf-8").replace(
        "materialize_formally",
        "retain_as_context_only",
        1,
    )
    path.write_text(text, encoding="utf-8")

    import pytest
    from modules.target_model_formulation.errors import (
        TargetModelFormulationError,
    )

    with pytest.raises(TargetModelFormulationError):
        repo.load_review("120412", "TFR-000001")


def test_authority_set_can_be_loaded_and_latest_for_review_is_resolved(tmp_path):
    repo = TargetModelFormulationAuthorityRepository(tmp_path)
    review = review_four()
    repo.record_review(review)
    _complete(repo, review)

    authority = repo.finalize_authority_set(
        review=review,
        created_at="2026-08-25T14:20:00Z",
    )

    loaded = repo.load_authority_set(
        "120412",
        authority.authority_set_id,
    )
    latest = repo.latest_authority_set_for_review(
        "120412",
        "TFR-000001",
    )

    assert loaded == authority
    assert latest == authority
