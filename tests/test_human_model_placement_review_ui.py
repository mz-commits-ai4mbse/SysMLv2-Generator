import pytest

from app.human_model_placement_review_ui import (
    placement_items_for_view,
    placement_rule_labels,
)
from modules.model_candidates.structure_profile import (
    load_model_structure_profile,
)
from modules.model_placement import (
    ModelPlacementPersonaProposal,
    ModelPlacementReviewItem,
    ModelPlacementRuleSupport,
)
from modules.model_placement.review_types import (
    ModelPlacementReviewDecision,
)


def _item(*, attention=True):
    return ModelPlacementReviewItem(
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
        persona_proposals=(
            ModelPlacementPersonaProposal(
                persona_id="P1",
                approved_input_id="AIN-000001",
                result="proposed_mapping",
                selected_rule_id="ELEMENT_SYSTEM_FUNCTION",
                alternative_rule_ids=(),
                rationale="system",
                proposal_fingerprint="1" * 64,
            ),
        ),
        rule_support=(
            ModelPlacementRuleSupport(
                rule_id="ELEMENT_SYSTEM_FUNCTION",
                supporting_personas=("P1",),
            ),
        ),
        agreement_level="placement_variance",
        unanimous_rule_id=None,
        review_attention_required=attention,
        content_fingerprint="2" * 64,
    )


def _decision(outcome):
    return ModelPlacementReviewDecision(
        schema_version="1.0.0",
        project_id="120412",
        decision_id="MPD-000001",
        comparison_fingerprint="3" * 64,
        review_item_fingerprint="2" * 64,
        approved_input_id="AIN-000001",
        outcome=outcome,
        selected_rule_id=(
            "ELEMENT_SYSTEM_FUNCTION"
            if outcome == "accepted"
            else None
        ),
        reviewer_identity="MZ",
        rationale="review",
        supersedes_decision_id=None,
        reviewed_at="2026-08-24T16:00:00Z",
        decision_fingerprint="4" * 64,
    )


def test_rule_labels_make_rflp_level_prominent():
    profile = load_model_structure_profile()
    labels = placement_rule_labels(profile)

    assert labels["ELEMENT_STAKEHOLDER_REQUIREMENT"].startswith(
        "Stakeholder ·"
    )
    assert labels["ELEMENT_SYSTEM_FUNCTION"].startswith(
        "System ·"
    )
    assert labels["ELEMENT_SUBSYSTEM_FUNCTION"].startswith(
        "Subsystem ·"
    )


@pytest.mark.parametrize(
    ("view_mode", "decision", "expected"),
    (
        ("pending", None, 1),
        ("pending", "accepted", 0),
        ("pending", "reopened", 1),
        ("reviewed", "accepted", 1),
        ("reviewed", "rejected", 1),
        ("reviewed", "reopened", 0),
        ("attention", None, 1),
        ("rejected", "rejected", 1),
        ("rejected", "accepted", 0),
        ("all", "accepted", 1),
    ),
)
def test_familiar_review_views_preserve_effective_decision_state(
    view_mode,
    decision,
    expected,
):
    latest = (
        {}
        if decision is None
        else {"AIN-000001": _decision(decision)}
    )
    visible = placement_items_for_view(
        (_item(),),
        latest_decisions=latest,
        view_mode=view_mode,
    )
    assert len(visible) == expected


def test_attention_view_excludes_clean_item():
    visible = placement_items_for_view(
        (_item(attention=False),),
        latest_decisions={},
        view_mode="attention",
    )
    assert visible == ()


def test_invalid_view_fails_closed():
    with pytest.raises(ValueError, match="Unsupported"):
        placement_items_for_view(
            (_item(),),
            latest_decisions={},
            view_mode="magic",
        )
