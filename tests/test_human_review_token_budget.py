"""Tests for deterministic, fail-closed token budgeting."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
import hashlib

import pytest

from modules.human_review.errors import (
    TokenBudgetExceededError,
    TokenBudgetValidationError,
    TokenEstimationError,
)
from modules.human_review.token_budget import (
    DEFAULT_TOKEN_BUDGET_POLICY,
    assess_token_budget,
    create_token_budget_context_item,
    deterministic_token_estimate,
    require_token_budget,
    selected_context_reference_ids,
    token_estimator_metadata,
    validate_token_budget_context_item,
    validate_token_budget_policy,
)
from modules.human_review.types import (
    TOKEN_BUDGET_CATEGORIES,
    TokenBudgetAssessment,
    TokenBudgetContextItem,
)


def item(
    reference_id: str,
    *,
    category: str = "information_unit",
    content: str = "abcd",
    required: bool = False,
    estimated_tokens: int | None = None,
) -> TokenBudgetContextItem:
    created = create_token_budget_context_item(
        category=category,
        reference_id=reference_id,
        reference_version="1.0.0",
        content=content,
        required=required,
    )
    return (
        created
        if estimated_tokens is None
        else replace(created, estimated_tokens=estimated_tokens)
    )


def policy_window(available: int) -> int:
    policy = DEFAULT_TOKEN_BUDGET_POLICY
    return (
        available
        + policy.safety_margin_tokens
        + policy.reserved_output_tokens
        + policy.reserved_system_tokens
    )


def test_default_policy_is_accepted() -> None:
    assert validate_token_budget_policy(
        DEFAULT_TOKEN_BUDGET_POLICY
    ) is None


def test_default_policy_is_fail_closed() -> None:
    policy = DEFAULT_TOKEN_BUDGET_POLICY
    assert policy.block_on_required_context_overflow is True
    assert policy.silent_required_context_truncation_allowed is False
    assert policy.category_priority == TOKEN_BUDGET_CATEGORIES


@pytest.mark.parametrize(
    ("content", "expected"),
    [
        ("", 0),
        ("a", 1),
        ("abcd", 1),
        ("abcde", 2),
        ("ä", 1),
        ("😀", 1),
        ("😀a", 2),
    ],
)
def test_deterministic_estimator(content, expected) -> None:
    assert deterministic_token_estimate(content) == expected


def test_estimator_rejects_non_string() -> None:
    with pytest.raises(TokenEstimationError):
        deterministic_token_estimate(None)


def test_estimator_metadata_is_explicit() -> None:
    assert token_estimator_metadata() == {
        "estimator_id": "utf8_bytes_div_4_ceiling_v1",
        "unit": "estimated_tokens",
        "algorithm": "ceil(utf8_byte_length / 4)",
    }


def test_context_item_records_hash_and_estimate() -> None:
    created = item("IU-000001", content="abcdefgh")
    assert created.estimated_tokens == 2
    assert created.content_sha256 == hashlib.sha256(
        b"abcdefgh"
    ).hexdigest()


def test_context_item_is_immutable() -> None:
    created = item("IU-000001")
    with pytest.raises(FrozenInstanceError):
        created.content = "changed"


@pytest.mark.parametrize("category", TOKEN_BUDGET_CATEGORIES)
def test_every_category_is_supported(category) -> None:
    assert item("REF-1", category=category).category == category


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("category", "complete_codebase"),
        ("reference_id", ""),
        ("reference_id", "../unsafe"),
        ("reference_version", ""),
        ("content", ""),
        ("required", 1),
        ("estimator", None),
    ],
)
def test_context_factory_rejects_invalid_input(field, value) -> None:
    values = {
        "category": "information_unit",
        "reference_id": "IU-000001",
        "reference_version": "1.0.0",
        "content": "content",
        "required": True,
        "estimator": deterministic_token_estimate,
    }
    values[field] = value
    with pytest.raises((TokenBudgetValidationError, TokenEstimationError)):
        create_token_budget_context_item(**values)


@pytest.mark.parametrize("estimated", [0, -1, 1.5, True, None])
def test_factory_rejects_invalid_estimator_result(estimated) -> None:
    with pytest.raises(TokenEstimationError):
        create_token_budget_context_item(
            category="information_unit",
            reference_id="IU-000001",
            reference_version=None,
            content="content",
            required=True,
            estimator=lambda _: estimated,
        )


def test_factory_wraps_estimator_failure() -> None:
    def fail(_: str) -> int:
        raise RuntimeError("failed")

    with pytest.raises(TokenEstimationError):
        create_token_budget_context_item(
            category="information_unit",
            reference_id="IU-000001",
            reference_version=None,
            content="content",
            required=True,
            estimator=fail,
        )


def test_context_validation_detects_content_tampering() -> None:
    tampered = replace(item("IU-000001"), content="changed")
    with pytest.raises(TokenBudgetValidationError):
        validate_token_budget_context_item(tampered)


def test_context_validation_detects_estimate_tampering() -> None:
    tampered = replace(item("IU-000001"), estimated_tokens=0)
    with pytest.raises(TokenBudgetValidationError):
        validate_token_budget_context_item(tampered)


def test_empty_context_fits() -> None:
    result = assess_token_budget(
        model_context_window_tokens=policy_window(100),
        context_items=(),
    )
    assert result.context_fits is True
    assert result.blocked is False
    assert result.allocated_context_tokens == 0


def test_reservations_reduce_available_input() -> None:
    result = assess_token_budget(
        model_context_window_tokens=policy_window(100),
        context_items=(),
    )
    assert result.available_input_tokens == 100


def test_required_context_is_always_selected() -> None:
    required = item(
        "IU-000001",
        required=True,
        estimated_tokens=10,
    )
    result = assess_token_budget(
        model_context_window_tokens=policy_window(10),
        context_items=(required,),
    )
    assert selected_context_reference_ids(result) == ("IU-000001",)


def test_required_overflow_blocks_without_partial_selection() -> None:
    result = assess_token_budget(
        model_context_window_tokens=policy_window(9),
        context_items=(
            item(
                "IU-000001",
                required=True,
                estimated_tokens=10,
            ),
        ),
    )
    assert result.blocked is True
    assert result.context_fits is False
    assert result.allocated_context_tokens == 0
    assert result.blocked_reason == (
        "required_context_exceeds_available_input_budget"
    )


def test_required_overflow_raises_before_invocation() -> None:
    result = assess_token_budget(
        model_context_window_tokens=policy_window(1),
        context_items=(
            item("IU-000001", required=True, estimated_tokens=2),
        ),
    )
    with pytest.raises(TokenBudgetExceededError):
        require_token_budget(result)


def test_optional_context_may_be_omitted() -> None:
    result = assess_token_budget(
        model_context_window_tokens=policy_window(5),
        context_items=(
            item("IU-000001", estimated_tokens=4),
            item("IU-000002", estimated_tokens=4),
        ),
    )
    allocation = result.allocations[1]
    assert allocation.selected_reference_ids == ("IU-000001",)
    assert allocation.omitted_reference_ids == ("IU-000002",)


def test_required_later_category_is_reserved_before_optional() -> None:
    result = assess_token_budget(
        model_context_window_tokens=policy_window(10),
        context_items=(
            item(
                "SCHEMA-1",
                category="instruction_and_schema",
                estimated_tokens=8,
            ),
            item(
                "FRAMEWORK-1",
                category="framework_targets",
                required=True,
                estimated_tokens=6,
            ),
        ),
    )
    assert selected_context_reference_ids(result) == ("FRAMEWORK-1",)
    assert result.allocations[0].omitted_reference_ids == ("SCHEMA-1",)


def test_priority_precedes_input_order() -> None:
    result = assess_token_budget(
        model_context_window_tokens=policy_window(2),
        context_items=(
            item(
                "SUPPLEMENT-1",
                category="supplementary_context",
                estimated_tokens=2,
            ),
            item(
                "SCHEMA-1",
                category="instruction_and_schema",
                estimated_tokens=2,
            ),
        ),
    )
    assert selected_context_reference_ids(result) == ("SCHEMA-1",)


def test_reference_id_orders_items_within_category() -> None:
    result = assess_token_budget(
        model_context_window_tokens=policy_window(1),
        context_items=(
            item("IU-000002", estimated_tokens=1),
            item("IU-000001", estimated_tokens=1),
        ),
    )
    assert selected_context_reference_ids(result) == ("IU-000001",)


def test_assessment_is_independent_of_input_order() -> None:
    items = (
        item("IU-000002", estimated_tokens=1),
        item("IU-000001", estimated_tokens=1),
    )
    first = assess_token_budget(
        model_context_window_tokens=policy_window(1),
        context_items=items,
    )
    second = assess_token_budget(
        model_context_window_tokens=policy_window(1),
        context_items=reversed(items),
    )
    assert first == second


def test_duplicate_reference_in_category_is_rejected() -> None:
    with pytest.raises(TokenBudgetValidationError):
        assess_token_budget(
            model_context_window_tokens=policy_window(10),
            context_items=(
                item("IU-000001"),
                item("IU-000001", content="different"),
            ),
        )


def test_same_reference_in_distinct_categories_is_allowed() -> None:
    result = assess_token_budget(
        model_context_window_tokens=policy_window(10),
        context_items=(
            item("REF-1", category="information_unit"),
            item("REF-1", category="project_terminology"),
        ),
    )
    assert result.blocked is False


@pytest.mark.parametrize("window", [0, -1, 1.5, True])
def test_invalid_model_window_is_rejected(window) -> None:
    with pytest.raises(TokenBudgetValidationError):
        assess_token_budget(
            model_context_window_tokens=window,
            context_items=(),
        )


@pytest.mark.parametrize("items", [None, "items", 1])
def test_invalid_context_collection_is_rejected(items) -> None:
    with pytest.raises(TokenBudgetValidationError):
        assess_token_budget(
            model_context_window_tokens=policy_window(10),
            context_items=items,
        )


def test_invalid_context_member_is_rejected() -> None:
    with pytest.raises(TokenBudgetValidationError):
        assess_token_budget(
            model_context_window_tokens=policy_window(10),
            context_items=({},),
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("policy_id", ""),
        ("policy_version", "1.0"),
        ("safety_margin_tokens", -1),
        ("reserved_output_tokens", True),
        ("reserved_system_tokens", 1.5),
        ("category_priority", tuple(reversed(TOKEN_BUDGET_CATEGORIES))),
        ("block_on_required_context_overflow", False),
        ("silent_required_context_truncation_allowed", True),
    ],
)
def test_invalid_policy_is_rejected(field, value) -> None:
    with pytest.raises(TokenBudgetValidationError):
        validate_token_budget_policy(
            replace(DEFAULT_TOKEN_BUDGET_POLICY, **{field: value})
        )


def test_policy_wrong_type_is_rejected() -> None:
    with pytest.raises(TokenBudgetValidationError):
        validate_token_budget_policy({})


def test_require_budget_rejects_wrong_type() -> None:
    with pytest.raises(TokenBudgetValidationError):
        require_token_budget({})


def test_require_budget_rejects_inconsistent_non_fitting_assessment() -> None:
    assessment = TokenBudgetAssessment(
        policy_id="POLICY",
        policy_version="1.0.0",
        model_context_window_tokens=100,
        available_input_tokens=50,
        required_context_tokens=60,
        optional_context_tokens=0,
        allocated_context_tokens=0,
        context_fits=False,
        blocked=False,
        blocked_reason=None,
        allocations=(),
    )
    with pytest.raises(TokenBudgetExceededError):
        require_token_budget(assessment)


def test_allocation_accounting_is_consistent() -> None:
    result = assess_token_budget(
        model_context_window_tokens=policy_window(20),
        context_items=(
            item("REQ-1", required=True, estimated_tokens=5),
            item("OPT-1", estimated_tokens=7),
            item("OPT-2", estimated_tokens=12),
        ),
    )
    assert result.required_context_tokens == 5
    assert result.optional_context_tokens == 19
    assert result.allocated_context_tokens == 12
    assert sum(
        allocation.allocated_tokens
        for allocation in result.allocations
    ) == 12


def test_assessment_has_one_allocation_per_category() -> None:
    result = assess_token_budget(
        model_context_window_tokens=policy_window(10),
        context_items=(),
    )
    assert tuple(
        allocation.category for allocation in result.allocations
    ) == TOKEN_BUDGET_CATEGORIES