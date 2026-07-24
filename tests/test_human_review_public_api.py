"""Public API contract for the Human Review module."""

from __future__ import annotations

from dataclasses import fields

import modules.human_review as human_review
from modules.human_review import (
    DEFAULT_TOKEN_BUDGET_POLICY,
    HUMAN_REVIEWS_DIRECTORY_NAME,
    HUMAN_REVIEW_DECISIONS,
    HUMAN_REVIEW_MODES,
    HUMAN_REVIEW_TARGET_TYPES,
    REFERENCE_VALIDATION_STATUSES,
    TOKEN_BUDGET_CATEGORIES,
    HumanReviewDecision,
    HumanReviewRepository,
    HumanReviewTargetSnapshot,
    TokenBudgetAssessment,
    TokenBudgetContextItem,
    TokenBudgetPolicy,
    assess_token_budget,
    create_human_review_decision,
    create_human_review_target_snapshot,
    create_token_budget_context_item,
    require_token_budget,
)


def test_public_api_has_no_duplicate_exports() -> None:
    assert len(human_review.__all__) == len(set(human_review.__all__))


def test_every_declared_export_exists() -> None:
    assert all(hasattr(human_review, name) for name in human_review.__all__)


def test_review_contract_constants() -> None:
    assert HUMAN_REVIEW_TARGET_TYPES == frozenset(
        {
            "information_unit_publication",
            "terminology_mapping_candidate",
            "framework_assignment_candidate",
        }
    )
    assert HUMAN_REVIEW_DECISIONS == frozenset(
        {"confirm", "reject", "request_changes"}
    )
    assert HUMAN_REVIEW_MODES == frozenset(
        {"quick_confirmation", "detailed_review"}
    )
    assert REFERENCE_VALIDATION_STATUSES == frozenset(
        {"valid", "invalid", "not_applicable"}
    )


def test_token_category_order_is_public_and_stable() -> None:
    assert TOKEN_BUDGET_CATEGORIES == (
        "instruction_and_schema",
        "information_unit",
        "project_terminology",
        "turing_core",
        "external_reference_concepts",
        "framework_targets",
        "supplementary_context",
    )


def test_review_dataclasses_are_public() -> None:
    assert HumanReviewTargetSnapshot.__dataclass_params__.frozen
    assert HumanReviewDecision.__dataclass_params__.frozen
    assert HumanReviewTargetSnapshot.__slots__
    assert HumanReviewDecision.__slots__


def test_token_dataclasses_are_public() -> None:
    for data_type in (
        TokenBudgetPolicy,
        TokenBudgetContextItem,
        TokenBudgetAssessment,
    ):
        assert data_type.__dataclass_params__.frozen
        assert data_type.__slots__


def test_review_repository_is_public() -> None:
    assert HumanReviewRepository is not None
    assert HUMAN_REVIEWS_DIRECTORY_NAME == "human_reviews"
    for method_name in (
        "record_decision",
        "load_decision",
        "list_decisions",
        "scan_decisions",
        "require_confirmation",
        "decision_path",
    ):
        assert callable(getattr(HumanReviewRepository, method_name))


def test_review_factories_are_public() -> None:
    assert callable(create_human_review_target_snapshot)
    assert callable(create_human_review_decision)
    assert tuple(field.name for field in fields(HumanReviewDecision)) == (
        "schema_version",
        "project_id",
        "human_review_decision_id",
        "target",
        "review_mode",
        "decision",
        "reviewer_identity",
        "rationale",
        "decided_at",
        "decision_fingerprint",
    )


def test_token_budget_operations_are_public() -> None:
    assert callable(create_token_budget_context_item)
    assert callable(assess_token_budget)
    assert callable(require_token_budget)
    assert DEFAULT_TOKEN_BUDGET_POLICY.policy_version == "1.0.0"


def test_public_api_does_not_expose_automatic_release() -> None:
    forbidden = {
        "automatic_release",
        "auto_publish",
        "publish_without_review",
        "truncate_required_context",
    }
    assert forbidden.isdisjoint(human_review.__all__)