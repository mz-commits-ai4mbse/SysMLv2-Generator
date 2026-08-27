import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import json
import pytest

from modules.target_model_formulation.authority import create_formulation_decision
from modules.target_model_formulation.errors import TargetModelFormulationError
from modules.target_model_formulation.repository import (
    TargetModelFormulationAuthorityRepository,
)
from target_model_formulation_authority_helpers import review_four


def test_review_snapshot_is_persisted_before_human_decisions(tmp_path):
    repo = TargetModelFormulationAuthorityRepository(tmp_path)
    review = review_four()
    with pytest.raises(TargetModelFormulationError, match="must be persisted"):
        repo.record_selection(
            review=review,
            authority_subject_id="IME-000001",
            selected_candidate_id="TFC-000001",
            reviewer_identity="MZ",
            rationale="approve",
            decided_at="2026-08-25T14:00:00Z",
        )


def test_record_selection_allocates_immutable_tfd_and_binds_review(tmp_path):
    repo = TargetModelFormulationAuthorityRepository(tmp_path)
    review = review_four()
    review_path = repo.record_review(review)
    value = repo.record_selection(
        review=review,
        authority_subject_id="IME-000001",
        selected_candidate_id="TFC-000001",
        reviewer_identity="MZ",
        rationale="approve standalone role definition",
        decided_at="2026-08-25T14:00:00Z",
    )
    assert value.decision_id == "TFD-000001"
    assert value.supersedes_decision_id is None
    assert review_path.is_file()
    decision_path = (
        tmp_path / "120412" / "target_model_formulation" / "decisions" / "TFD-000001.json"
    )
    assert decision_path.is_file()
    assert json.loads(decision_path.read_text())["review_fingerprint"] == review.content_fingerprint


def test_successor_selection_supersedes_current_effective_decision(tmp_path):
    repo = TargetModelFormulationAuthorityRepository(tmp_path)
    review = review_four()
    repo.record_review(review)
    first = repo.record_selection(
        review=review,
        authority_subject_id="IME-000001",
        selected_candidate_id="TFC-000001",
        reviewer_identity="MZ",
        rationale="first review",
        decided_at="2026-08-25T14:00:00Z",
    )
    second = repo.record_selection(
        review=review,
        authority_subject_id="IME-000001",
        selected_candidate_id="TFC-000001",
        reviewer_identity="MZ",
        rationale="re-reviewed with updated rationale",
        decided_at="2026-08-25T14:10:00Z",
    )
    assert second.decision_id == "TFD-000002"
    assert second.supersedes_decision_id == first.decision_id
    latest = repo.latest_decision_for_subject("120412", "TFR-000001", "IME-000001")
    assert latest.decision_id == "TFD-000002"


def test_manual_successor_must_point_to_current_effective_decision(tmp_path):
    repo = TargetModelFormulationAuthorityRepository(tmp_path)
    review = review_four()
    repo.record_review(review)
    repo.record_selection(
        review=review,
        authority_subject_id="IME-000001",
        selected_candidate_id="TFC-000001",
        reviewer_identity="MZ",
        rationale="first",
        decided_at="2026-08-25T14:00:00Z",
    )
    bad = create_formulation_decision(
        review=review,
        decision_id="TFD-000002",
        authority_subject_id="IME-000001",
        selected_candidate_id="TFC-000001",
        reviewer_identity="MZ",
        rationale="bad successor",
        decided_at="2026-08-25T14:10:00Z",
        supersedes_decision_id=None,
    )
    with pytest.raises(TargetModelFormulationError, match="must supersede"):
        repo.record_decision(review=review, decision=bad)


def test_authority_set_cannot_finalize_until_all_four_items_are_decided(tmp_path):
    repo = TargetModelFormulationAuthorityRepository(tmp_path)
    review = review_four()
    repo.record_review(review)
    repo.record_selection(
        review=review,
        authority_subject_id="IME-000001",
        selected_candidate_id="TFC-000001",
        reviewer_identity="MZ",
        rationale="approve",
        decided_at="2026-08-25T14:00:00Z",
    )
    with pytest.raises(TargetModelFormulationError, match="cover every review item"):
        repo.finalize_authority_set(
            review=review,
            created_at="2026-08-25T14:20:00Z",
        )


def test_complete_four_item_authority_set_is_persisted(tmp_path):
    repo = TargetModelFormulationAuthorityRepository(tmp_path)
    review = review_four()
    repo.record_review(review)
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
    authority = repo.finalize_authority_set(
        review=review,
        created_at="2026-08-25T14:20:00Z",
    )
    assert authority.authority_set_id == "TFA-000001"
    assert len(authority.effective_decisions) == 4
    path = (
        tmp_path / "120412" / "target_model_formulation" / "authority_sets" / "TFA-000001.json"
    )
    assert path.is_file()


def test_review_snapshot_is_immutable(tmp_path):
    repo = TargetModelFormulationAuthorityRepository(tmp_path)
    review = review_four()
    path = repo.record_review(review)
    repo.record_review(review)
    payload = json.loads(path.read_text())
    payload["created_at"] = "tampered"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(TargetModelFormulationError, match="immutable"):
        repo.record_review(review)


def test_find_review_for_source_returns_latest_immutable_revision(tmp_path):
    from modules.target_model_formulation.contract import (
        create_formulation_review,
    )

    repo = TargetModelFormulationAuthorityRepository(tmp_path)
    first = review_four()
    repo.record_review(first)

    second = create_formulation_review(
        project_id=first.project_id,
        review_id="TFR-000002",
        source_internal_engineering_model_id=(
            first.source_internal_engineering_model_id
        ),
        source_internal_engineering_model_fingerprint=(
            first.source_internal_engineering_model_fingerprint
        ),
        final_model_review_decision_id=(
            first.final_model_review_decision_id
        ),
        final_model_review_decision_fingerprint=(
            first.final_model_review_decision_fingerprint
        ),
        target_model_profile_id=first.target_model_profile_id,
        target_model_profile_version=first.target_model_profile_version,
        target_model_profile_fingerprint=(
            first.target_model_profile_fingerprint
        ),
        target_notation_fingerprint=(
            first.target_notation_fingerprint
        ),
        items=first.items,
        created_at="2026-08-25T15:00:00Z",
    )
    repo.record_review(second)

    current = repo.find_review_for_source(
        first.project_id,
        first.source_internal_engineering_model_id,
        first.source_internal_engineering_model_fingerprint,
    )

    assert current is not None
    assert current.review_id == "TFR-000002"

    # Prior Human-authority history remains immutable and readable.
    assert repo.load_review(
        first.project_id,
        "TFR-000001",
    ) == first
