from datetime import datetime, timezone
from types import SimpleNamespace

from modules.model_placement import (
    ModelPlacementBatchComparison,
    ModelPlacementReviewItem,
)
from modules.model_placement.review_repository import (
    ModelPlacementReviewRepository,
)


def _clock():
    return datetime(2026, 8, 24, 18, 0, 0, tzinfo=timezone.utc)


def _comparison():
    item = ModelPlacementReviewItem(
        approved_input_id="AIN-000001",
        approved_input_kind="element_statement",
        stable_subject_key="subject:subj-001",
        title="Share live view",
        primary_text="Share live view.",
        information_type="function",
        deterministic_disposition="mapped",
        deterministic_candidate_rule_ids=("ELEMENT_SYSTEM_FUNCTION",),
        allowed_rule_ids=(
            "ELEMENT_SYSTEM_FUNCTION",
            "ELEMENT_SUBSYSTEM_FUNCTION",
        ),
        persona_proposals=(),
        rule_support=(),
        agreement_level="unanimous_mapping",
        unanimous_rule_id="ELEMENT_SYSTEM_FUNCTION",
        review_attention_required=False,
        content_fingerprint="1" * 64,
    )
    return ModelPlacementBatchComparison(
        schema_version="1.0.0",
        project_id="120412",
        profile_id="TURING_MODEL_STRUCTURE",
        profile_version="1.0.0",
        profile_fingerprint="2" * 64,
        request_fingerprint="3" * 64,
        persona_ids=(),
        items=(item,),
        human_review_required=True,
        content_fingerprint="4" * 64,
    )


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


def test_repository_finalizes_and_round_trips_approved_placement_set(tmp_path):
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

    approved = repo.finalize_approved_placement_set(
        "120412",
        comparison.content_fingerprint,
        profile=_profile(),
    )
    loaded = repo.load_approved_placement_set(
        "120412",
        comparison.content_fingerprint,
    )

    assert loaded == approved
    assert approved.placements[0].selected_rule_id == (
        "ELEMENT_SYSTEM_FUNCTION"
    )
