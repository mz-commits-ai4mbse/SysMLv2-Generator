from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from modules.model_assembly.final_review import (
    ModelAssemblyFinalReviewRepository,
)
from modules.model_placement.errors import ModelPlacementContractError


def _clock():
    return datetime(2026, 8, 24, 19, 0, 0, tzinfo=timezone.utc)


def _profile():
    return SimpleNamespace(
        relationship_semantics=(
            SimpleNamespace(semantic_intent="dependency"),
        ),
    )


def _draft():
    relationship = SimpleNamespace(
        relationship_decision_id="SRD-000001",
        representation_status="exact_profile_match",
        candidate_rule_ids=("relationship:dependency",),
    )
    return SimpleNamespace(
        project_id="120412",
        comparison_fingerprint="1" * 64,
        content_fingerprint="2" * 64,
        approved_placement_set_fingerprint="3" * 64,
        approved_engineering_information_fingerprint="4" * 64,
        relationships=(relationship,),
    )


def test_final_review_decision_persists_immutably(tmp_path):
    repo = ModelAssemblyFinalReviewRepository(
        tmp_path,
        clock=_clock,
    )
    value = repo.record(
        draft=_draft(),
        profile=_profile(),
        decision="approved",
        selected_relationship_rules={
            "SRD-000001": "relationship:dependency",
        },
        reviewer_identity="MZ",
    )

    loaded = repo.latest_decision("120412", "1" * 64)

    assert loaded == value
    assert loaded.final_assembly_decision_id == "FAD-000001"


def test_second_decision_for_same_exact_assembly_is_blocked(tmp_path):
    repo = ModelAssemblyFinalReviewRepository(
        tmp_path,
        clock=_clock,
    )
    kwargs = dict(
        draft=_draft(),
        profile=_profile(),
        decision="approved",
        selected_relationship_rules={
            "SRD-000001": "relationship:dependency",
        },
        reviewer_identity="MZ",
    )
    repo.record(**kwargs)

    with pytest.raises(ModelPlacementContractError, match="already"):
        repo.record(**kwargs)
