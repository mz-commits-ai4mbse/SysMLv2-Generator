from types import SimpleNamespace

import pytest

from modules.model_assembly.final_review import (
    build_final_model_review_options,
    create_final_model_review_decision,
)
from modules.model_placement.errors import ModelPlacementContractError


def _profile():
    return SimpleNamespace(
        relationship_semantics=(
            SimpleNamespace(semantic_intent="dependency"),
            SimpleNamespace(semantic_intent="traces_to"),
            SimpleNamespace(semantic_intent="refines"),
        ),
    )


def _relationship(rid, status, candidates):
    return SimpleNamespace(
        relationship_decision_id=rid,
        representation_status=status,
        candidate_rule_ids=tuple(candidates),
    )


def _draft(*relationships):
    return SimpleNamespace(
        project_id="120412",
        comparison_fingerprint="1" * 64,
        content_fingerprint="2" * 64,
        approved_placement_set_fingerprint="3" * 64,
        approved_engineering_information_fingerprint="4" * 64,
        relationships=tuple(relationships),
    )


def test_unmapped_relationship_gets_all_profile_controlled_options():
    draft = _draft(
        _relationship("SRD-000001", "unmapped", ()),
    )

    options = build_final_model_review_options(
        draft=draft,
        profile=_profile(),
    )

    assert options["SRD-000001"] == (
        "relationship:dependency",
        "relationship:refines",
        "relationship:traces_to",
    )


def test_approval_preserves_exact_and_human_resolves_variance():
    draft = _draft(
        _relationship(
            "SRD-000001",
            "exact_profile_match",
            ("relationship:dependency",),
        ),
        _relationship(
            "SRD-000002",
            "persona_variance",
            (
                "relationship:dependency",
                "relationship:traces_to",
            ),
        ),
    )

    decision = create_final_model_review_decision(
        draft=draft,
        profile=_profile(),
        final_assembly_decision_id="FAD-000001",
        decision="approved",
        selected_relationship_rules={
            "SRD-000001": "relationship:dependency",
            "SRD-000002": "relationship:traces_to",
        },
        reviewer_identity="MZ",
        rationale="Resolve the remaining target representation explicitly.",
        reviewed_at="2026-08-24T19:00:00Z",
    )

    assert decision.decision == "approved"
    assert tuple(
        item.resolution_source
        for item in decision.relationship_resolutions
    ) == (
        "exact_profile_match",
        "human_resolved_final_review",
    )


def test_variance_resolution_requires_human_rationale():
    draft = _draft(
        _relationship(
            "SRD-000001",
            "persona_variance",
            (
                "relationship:dependency",
                "relationship:traces_to",
            ),
        ),
    )

    with pytest.raises(ModelPlacementContractError, match="rationale"):
        create_final_model_review_decision(
            draft=draft,
            profile=_profile(),
            final_assembly_decision_id="FAD-000001",
            decision="approved",
            selected_relationship_rules={
                "SRD-000001": "relationship:dependency",
            },
            reviewer_identity="MZ",
            rationale=None,
            reviewed_at="2026-08-24T19:00:00Z",
        )


def test_changes_requested_requires_rationale_but_no_fake_resolution():
    draft = _draft(
        _relationship("SRD-000001", "unmapped", ()),
    )

    decision = create_final_model_review_decision(
        draft=draft,
        profile=_profile(),
        final_assembly_decision_id="FAD-000001",
        decision="changes_requested",
        selected_relationship_rules=None,
        reviewer_identity="MZ",
        rationale="The model structure needs another assembly iteration.",
        reviewed_at="2026-08-24T19:00:00Z",
    )

    assert decision.relationship_resolutions == ()
