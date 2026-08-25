from types import SimpleNamespace

import pytest

from modules.model_placement.approved_set import (
    build_approved_model_placement_set,
)
from modules.model_placement.errors import ModelPlacementContractError
from modules.model_placement.review_types import ModelPlacementReviewDecision
from modules.model_placement.types import ModelPlacementReviewItem


def _profile():
    return SimpleNamespace(
        element_derivation_rules=(
            SimpleNamespace(
                rule_id="ELEMENT_SYSTEM_FUNCTION",
                model_area_id="system.functional",
                element_type="function",
            ),
            SimpleNamespace(
                rule_id="ELEMENT_SUBSYSTEM_FUNCTION",
                model_area_id="subsystem.functional",
                element_type="function",
            ),
        ),
        model_areas=(
            SimpleNamespace(
                model_area_id="system.functional",
                framework_node_id="FW_SYSTEM_FUNCTIONAL",
            ),
            SimpleNamespace(
                model_area_id="subsystem.functional",
                framework_node_id="FW_SUBSYSTEM_FUNCTIONAL",
            ),
        ),
    )


def _comparison():
    item = ModelPlacementReviewItem(
        approved_input_id="AIN-000001",
        approved_input_kind="element_statement",
        stable_subject_key="subject:subj-001",
        title="Share live view",
        primary_text="Share live view.",
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
        persona_proposals=(),
        rule_support=(),
        agreement_level="placement_variance",
        unanimous_rule_id=None,
        review_attention_required=True,
        content_fingerprint="1" * 64,
    )
    return SimpleNamespace(
        project_id="120412",
        profile_id="TURING_MODEL_STRUCTURE",
        profile_version="1.0.0",
        profile_fingerprint="2" * 64,
        content_fingerprint="3" * 64,
        items=(item,),
    )


def _decision(outcome, selected=None):
    return ModelPlacementReviewDecision(
        schema_version="1.0.0",
        project_id="120412",
        decision_id="MPD-000001",
        comparison_fingerprint="3" * 64,
        review_item_fingerprint="1" * 64,
        approved_input_id="AIN-000001",
        outcome=outcome,
        selected_rule_id=selected,
        reviewer_identity="MZ",
        rationale="review",
        supersedes_decision_id=None,
        reviewed_at="2026-08-24T18:00:00Z",
        decision_fingerprint="4" * 64,
    )


def test_accepted_human_placement_becomes_authoritative_set():
    result = build_approved_model_placement_set(
        comparison=_comparison(),
        latest_decisions=(
            _decision("accepted", "ELEMENT_SYSTEM_FUNCTION"),
        ),
        profile=_profile(),
    )

    assert len(result.placements) == 1
    placement = result.placements[0]
    assert placement.selected_rule_id == "ELEMENT_SYSTEM_FUNCTION"
    assert placement.model_area == "system.functional"
    assert placement.framework_assignment == "FW_SYSTEM_FUNCTIONAL"
    assert result.explicitly_not_materialized_approved_input_ids == ()


def test_rejected_placement_is_explicitly_not_materialized():
    result = build_approved_model_placement_set(
        comparison=_comparison(),
        latest_decisions=(_decision("rejected"),),
        profile=_profile(),
    )

    assert result.placements == ()
    assert result.explicitly_not_materialized_approved_input_ids == (
        "AIN-000001",
    )


@pytest.mark.parametrize("outcome", ("deferred", "reopened"))
def test_unresolved_human_state_blocks_finalization(outcome):
    with pytest.raises(ModelPlacementContractError, match="block"):
        build_approved_model_placement_set(
            comparison=_comparison(),
            latest_decisions=(_decision(outcome),),
            profile=_profile(),
        )


def test_missing_human_decision_blocks_finalization():
    with pytest.raises(
        ModelPlacementContractError,
        match="every review item",
    ):
        build_approved_model_placement_set(
            comparison=_comparison(),
            latest_decisions=(),
            profile=_profile(),
        )
