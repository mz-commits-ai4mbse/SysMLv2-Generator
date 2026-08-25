from datetime import datetime, timezone

import pytest

from modules.model_placement import (
    ModelPlacementBatchComparison,
    ModelPlacementPersonaProposal,
    ModelPlacementReviewItem,
    ModelPlacementRuleSupport,
)
from modules.model_placement.errors import ModelPlacementContractError
from modules.model_placement.review_repository import (
    ModelPlacementReviewRepository,
)


def _clock():
    return datetime(2026, 8, 24, 16, 0, 0, tzinfo=timezone.utc)


def _comparison():
    proposals = (
        ModelPlacementPersonaProposal(
            persona_id="P1",
            approved_input_id="AIN-000001",
            result="proposed_mapping",
            selected_rule_id="ELEMENT_SYSTEM_FUNCTION",
            alternative_rule_ids=(),
            rationale="system-level function",
            proposal_fingerprint="1" * 64,
        ),
        ModelPlacementPersonaProposal(
            persona_id="P2",
            approved_input_id="AIN-000001",
            result="proposed_mapping",
            selected_rule_id="ELEMENT_SUBSYSTEM_FUNCTION",
            alternative_rule_ids=(),
            rationale="subsystem-level function",
            proposal_fingerprint="2" * 64,
        ),
        ModelPlacementPersonaProposal(
            persona_id="P3",
            approved_input_id="AIN-000001",
            result="unmapped",
            selected_rule_id=None,
            alternative_rule_ids=(),
            rationale="level not established",
            proposal_fingerprint="3" * 64,
        ),
    )
    item = ModelPlacementReviewItem(
        approved_input_id="AIN-000001",
        approved_input_kind="element_statement",
        stable_subject_key="subject:subj-001",
        title="Share live view",
        primary_text="The system shares the live microscope view.",
        information_type="function",
        deterministic_disposition="ambiguous",
        deterministic_candidate_rule_ids=(
            "ELEMENT_SYSTEM_FUNCTION",
            "ELEMENT_SUBSYSTEM_FUNCTION",
        ),
        allowed_rule_ids=(
            "ELEMENT_SUBSYSTEM_FUNCTION",
            "ELEMENT_SYSTEM_FUNCTION",
        ),
        persona_proposals=proposals,
        rule_support=(
            ModelPlacementRuleSupport(
                rule_id="ELEMENT_SUBSYSTEM_FUNCTION",
                supporting_personas=("P2",),
            ),
            ModelPlacementRuleSupport(
                rule_id="ELEMENT_SYSTEM_FUNCTION",
                supporting_personas=("P1",),
            ),
        ),
        agreement_level="placement_variance",
        unanimous_rule_id=None,
        review_attention_required=True,
        content_fingerprint="4" * 64,
    )
    return ModelPlacementBatchComparison(
        schema_version="1.0.0",
        project_id="120412",
        profile_id="TURING_MODEL_STRUCTURE",
        profile_version="1.0.0",
        profile_fingerprint="5" * 64,
        request_fingerprint="6" * 64,
        persona_ids=("P1", "P2", "P3"),
        items=(item,),
        human_review_required=True,
        content_fingerprint="7" * 64,
    )


def test_comparison_is_persisted_and_round_trips(tmp_path):
    repo = ModelPlacementReviewRepository(tmp_path, clock=_clock)
    comparison = _comparison()

    published = repo.publish_comparison(comparison)
    loaded = repo.load_comparison(
        "120412",
        comparison.content_fingerprint,
    )

    assert published == comparison
    assert loaded == comparison


def test_human_acceptance_selects_one_allowed_profile_rule(tmp_path):
    repo = ModelPlacementReviewRepository(tmp_path, clock=_clock)
    comparison = repo.publish_comparison(_comparison())

    decision = repo.record_decision(
        "120412",
        comparison.content_fingerprint,
        approved_input_id="AIN-000001",
        outcome="accepted",
        selected_rule_id="ELEMENT_SYSTEM_FUNCTION",
        reviewer_identity="MZ",
        rationale="System boundary is authoritative for this function.",
    )

    assert decision.outcome == "accepted"
    assert decision.selected_rule_id == "ELEMENT_SYSTEM_FUNCTION"
    state = repo.review_state("120412", comparison.content_fingerprint)
    assert state.is_complete is True
    assert state.accepted_count == 1
    assert state.pending_count == 0


def test_acceptance_cannot_select_rule_outside_pinned_review_item(tmp_path):
    repo = ModelPlacementReviewRepository(tmp_path, clock=_clock)
    comparison = repo.publish_comparison(_comparison())

    with pytest.raises(
        ModelPlacementContractError,
        match="allowed profile rule",
    ):
        repo.record_decision(
            "120412",
            comparison.content_fingerprint,
            approved_input_id="AIN-000001",
            outcome="accepted",
            selected_rule_id="ELEMENT_SYSTEM_LOGICAL",
            reviewer_identity="MZ",
        )


def test_reopen_is_immutable_and_returns_item_to_pending(tmp_path):
    repo = ModelPlacementReviewRepository(tmp_path, clock=_clock)
    comparison = repo.publish_comparison(_comparison())

    accepted = repo.record_decision(
        "120412",
        comparison.content_fingerprint,
        approved_input_id="AIN-000001",
        outcome="accepted",
        selected_rule_id="ELEMENT_SYSTEM_FUNCTION",
        reviewer_identity="MZ",
    )
    reopened = repo.reopen_decision(
        "120412",
        comparison.content_fingerprint,
        approved_input_id="AIN-000001",
        reviewer_identity="MZ",
        rationale="Placement requires reconsideration.",
    )

    assert reopened.outcome == "reopened"
    assert reopened.supersedes_decision_id == accepted.decision_id
    assert len(repo.list_decisions("120412", comparison.content_fingerprint)) == 2

    state = repo.review_state("120412", comparison.content_fingerprint)
    assert state.is_complete is False
    assert state.reopened_count == 1
    assert state.pending_count == 1


def test_new_decision_after_reopen_supersedes_reopen(tmp_path):
    repo = ModelPlacementReviewRepository(tmp_path, clock=_clock)
    comparison = repo.publish_comparison(_comparison())

    repo.record_decision(
        "120412",
        comparison.content_fingerprint,
        approved_input_id="AIN-000001",
        outcome="accepted",
        selected_rule_id="ELEMENT_SYSTEM_FUNCTION",
        reviewer_identity="MZ",
    )
    reopened = repo.reopen_decision(
        "120412",
        comparison.content_fingerprint,
        approved_input_id="AIN-000001",
        reviewer_identity="MZ",
        rationale="Review again.",
    )
    corrected = repo.record_decision(
        "120412",
        comparison.content_fingerprint,
        approved_input_id="AIN-000001",
        outcome="accepted",
        selected_rule_id="ELEMENT_SUBSYSTEM_FUNCTION",
        reviewer_identity="MZ",
        rationale="Subsystem boundary is the correct placement.",
    )

    assert corrected.supersedes_decision_id == reopened.decision_id
    assert corrected.selected_rule_id == "ELEMENT_SUBSYSTEM_FUNCTION"

    state = repo.review_state("120412", comparison.content_fingerprint)
    assert state.is_complete is True
    assert state.accepted_count == 1
    assert state.reopened_count == 0


def test_reject_requires_rationale_and_remains_a_decision(tmp_path):
    repo = ModelPlacementReviewRepository(tmp_path, clock=_clock)
    comparison = repo.publish_comparison(_comparison())

    with pytest.raises(
        ModelPlacementContractError,
        match="require a rationale",
    ):
        repo.record_decision(
            "120412",
            comparison.content_fingerprint,
            approved_input_id="AIN-000001",
            outcome="rejected",
            selected_rule_id=None,
            reviewer_identity="MZ",
        )

    rejected = repo.record_decision(
        "120412",
        comparison.content_fingerprint,
        approved_input_id="AIN-000001",
        outcome="rejected",
        selected_rule_id=None,
        reviewer_identity="MZ",
        rationale="Approved engineering information is not model-promotable here.",
    )
    state = repo.review_state("120412", comparison.content_fingerprint)

    assert rejected.outcome == "rejected"
    assert state.rejected_count == 1
    assert state.is_complete is True
