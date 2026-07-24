"""Deterministic, auditable token budgeting for bounded LLM context."""

from __future__ import annotations

from collections.abc import Callable, Iterable
import hashlib
import re

from .errors import (
    TokenBudgetExceededError,
    TokenBudgetValidationError,
    TokenEstimationError,
)
from .types import (
    TOKEN_BUDGET_CATEGORIES,
    TokenBudgetAllocation,
    TokenBudgetAssessment,
    TokenBudgetContextItem,
    TokenBudgetPolicy,
)


DEFAULT_TOKEN_BUDGET_POLICY = TokenBudgetPolicy(
    policy_id="TURING_DETERMINISTIC_CONTEXT_BUDGET",
    policy_version="1.0.0",
    safety_margin_tokens=1024,
    reserved_output_tokens=4096,
    reserved_system_tokens=2048,
    category_priority=TOKEN_BUDGET_CATEGORIES,
    block_on_required_context_overflow=True,
    silent_required_context_truncation_allowed=False,
)

_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")
_SEMANTIC_VERSION = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_ESTIMATOR_ID = "utf8_bytes_div_4_ceiling_v1"


def deterministic_token_estimate(content: str) -> int:
    """Return a stable conservative proxy independent of an LLM service."""

    if not isinstance(content, str):
        raise TokenEstimationError("content must be a string.")
    if not content:
        return 0
    return (len(content.encode("utf-8")) + 3) // 4


def create_token_budget_context_item(
    *,
    category: str,
    reference_id: str,
    reference_version: str | None,
    content: str,
    required: bool,
    estimator: Callable[[str], int] = deterministic_token_estimate,
) -> TokenBudgetContextItem:
    """Create one hash-bound context item with a recorded estimate."""

    _validate_category(category)
    _identifier(reference_id, "reference_id")
    if reference_version is not None:
        _text(reference_version, "reference_version")
    if not isinstance(content, str) or not content:
        raise TokenBudgetValidationError(
            "content must be a non-empty string."
        )
    if not isinstance(required, bool):
        raise TokenBudgetValidationError("required must be a boolean.")
    if not callable(estimator):
        raise TokenEstimationError("estimator must be callable.")
    try:
        estimated = estimator(content)
    except TokenEstimationError:
        raise
    except Exception as exc:
        raise TokenEstimationError(
            "Token estimator failed."
        ) from exc
    if (
        isinstance(estimated, bool)
        or not isinstance(estimated, int)
        or estimated < 1
    ):
        raise TokenEstimationError(
            "Token estimator must return a positive integer."
        )
    return TokenBudgetContextItem(
        category=category,
        reference_id=reference_id,
        reference_version=reference_version,
        content=content,
        content_sha256=hashlib.sha256(
            content.encode("utf-8")
        ).hexdigest(),
        required=required,
        estimated_tokens=estimated,
    )


def validate_token_budget_policy(policy: TokenBudgetPolicy) -> None:
    """Validate a complete deterministic budget policy."""

    if not isinstance(policy, TokenBudgetPolicy):
        raise TokenBudgetValidationError(
            "policy must be a TokenBudgetPolicy."
        )
    _identifier(policy.policy_id, "policy_id")
    if (
        not isinstance(policy.policy_version, str)
        or _SEMANTIC_VERSION.fullmatch(policy.policy_version) is None
    ):
        raise TokenBudgetValidationError(
            "policy_version must be a semantic version."
        )
    for field_name in (
        "safety_margin_tokens",
        "reserved_output_tokens",
        "reserved_system_tokens",
    ):
        _non_negative_integer(getattr(policy, field_name), field_name)
    if (
        tuple(policy.category_priority)
        != TOKEN_BUDGET_CATEGORIES
    ):
        raise TokenBudgetValidationError(
            "category_priority must contain every accepted category "
            "exactly once in the accepted order."
        )
    if policy.block_on_required_context_overflow is not True:
        raise TokenBudgetValidationError(
            "Required-context overflow must block execution."
        )
    if policy.silent_required_context_truncation_allowed is not False:
        raise TokenBudgetValidationError(
            "Silent required-context truncation must be disabled."
        )


def validate_token_budget_context_item(
    item: TokenBudgetContextItem,
) -> None:
    """Validate one immutable, hash-bound context item."""

    if not isinstance(item, TokenBudgetContextItem):
        raise TokenBudgetValidationError(
            "context item must be a TokenBudgetContextItem."
        )
    _validate_category(item.category)
    _identifier(item.reference_id, "reference_id")
    if item.reference_version is not None:
        _text(item.reference_version, "reference_version")
    if not isinstance(item.content, str) or not item.content:
        raise TokenBudgetValidationError(
            "content must be a non-empty string."
        )
    if (
        not isinstance(item.content_sha256, str)
        or _SHA256.fullmatch(item.content_sha256) is None
    ):
        raise TokenBudgetValidationError(
            "content_sha256 must be lowercase SHA-256."
        )
    actual = hashlib.sha256(
        item.content.encode("utf-8")
    ).hexdigest()
    if actual != item.content_sha256:
        raise TokenBudgetValidationError(
            "Context content does not match content_sha256."
        )
    if not isinstance(item.required, bool):
        raise TokenBudgetValidationError("required must be a boolean.")
    _positive_integer(item.estimated_tokens, "estimated_tokens")


def assess_token_budget(
    *,
    model_context_window_tokens: int,
    context_items: Iterable[TokenBudgetContextItem],
    policy: TokenBudgetPolicy = DEFAULT_TOKEN_BUDGET_POLICY,
) -> TokenBudgetAssessment:
    """Select bounded context deterministically and audit every omission."""

    validate_token_budget_policy(policy)
    _positive_integer(
        model_context_window_tokens,
        "model_context_window_tokens",
    )
    if isinstance(context_items, (str, bytes)):
        raise TokenBudgetValidationError(
            "context_items must be an iterable of context items."
        )
    try:
        items = tuple(context_items)
    except TypeError as exc:
        raise TokenBudgetValidationError(
            "context_items must be iterable."
        ) from exc
    for item in items:
        validate_token_budget_context_item(item)
    identities = tuple(
        (item.category, item.reference_id) for item in items
    )
    if len(identities) != len(set(identities)):
        raise TokenBudgetValidationError(
            "Context reference IDs must be unique within a category."
        )

    reserved = (
        policy.safety_margin_tokens
        + policy.reserved_output_tokens
        + policy.reserved_system_tokens
    )
    available = max(model_context_window_tokens - reserved, 0)
    required_tokens = sum(
        item.estimated_tokens for item in items if item.required
    )
    optional_tokens = sum(
        item.estimated_tokens for item in items if not item.required
    )
    blocked = required_tokens > available
    blocked_reason = (
        "required_context_exceeds_available_input_budget"
        if blocked
        else None
    )

    optional_remaining = max(available - required_tokens, 0)
    allocations = []
    allocated_total = 0
    for category in policy.category_priority:
        category_items = sorted(
            (
                item
                for item in items
                if item.category == category
            ),
            key=lambda item: (
                not item.required,
                item.reference_id,
                item.reference_version or "",
                item.content_sha256,
            ),
        )
        before = max(available - allocated_total, 0)
        selected = []
        omitted = []
        allocated = 0
        if blocked:
            omitted.extend(
                item.reference_id for item in category_items
            )
        else:
            for item in category_items:
                if item.required:
                    selected.append(item.reference_id)
                    allocated += item.estimated_tokens
                elif item.estimated_tokens <= optional_remaining:
                    selected.append(item.reference_id)
                    optional_remaining -= item.estimated_tokens
                    allocated += item.estimated_tokens
                else:
                    omitted.append(item.reference_id)
        allocated_total += allocated
        allocations.append(
            TokenBudgetAllocation(
                category=category,
                available_tokens_before=before,
                allocated_tokens=allocated,
                selected_reference_ids=tuple(selected),
                omitted_reference_ids=tuple(omitted),
            )
        )
    return TokenBudgetAssessment(
        policy_id=policy.policy_id,
        policy_version=policy.policy_version,
        model_context_window_tokens=model_context_window_tokens,
        available_input_tokens=available,
        required_context_tokens=required_tokens,
        optional_context_tokens=optional_tokens,
        allocated_context_tokens=allocated_total,
        context_fits=not blocked,
        blocked=blocked,
        blocked_reason=blocked_reason,
        allocations=tuple(allocations),
    )


def require_token_budget(
    assessment: TokenBudgetAssessment,
) -> TokenBudgetAssessment:
    """Return a usable assessment or raise before any LLM invocation."""

    if not isinstance(assessment, TokenBudgetAssessment):
        raise TokenBudgetValidationError(
            "assessment must be a TokenBudgetAssessment."
        )
    if assessment.blocked or not assessment.context_fits:
        raise TokenBudgetExceededError(
            assessment.blocked_reason
            or "Token budget assessment blocks execution."
        )
    return assessment


def selected_context_reference_ids(
    assessment: TokenBudgetAssessment,
) -> tuple[str, ...]:
    """Return selected references in deterministic prompt order."""

    require_token_budget(assessment)
    return tuple(
        reference_id
        for allocation in assessment.allocations
        for reference_id in allocation.selected_reference_ids
    )


def token_estimator_metadata() -> dict[str, str]:
    """Describe the deterministic estimator used by the MVP."""

    return {
        "estimator_id": _ESTIMATOR_ID,
        "unit": "estimated_tokens",
        "algorithm": "ceil(utf8_byte_length / 4)",
    }


def _validate_category(category: object) -> str:
    if not isinstance(category, str):
        raise TokenBudgetValidationError(
            "category must be a string."
        )
    if category not in TOKEN_BUDGET_CATEGORIES:
        raise TokenBudgetValidationError(
            "category is not an accepted token-budget category."
        )
    return category


def _identifier(value: object, label: str) -> str:
    text = _text(value, label)
    if _IDENTIFIER.fullmatch(text) is None:
        raise TokenBudgetValidationError(
            f"{label} has invalid syntax."
        )
    return text


def _text(value: object, label: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
    ):
        raise TokenBudgetValidationError(
            f"{label} must be a non-empty trimmed string."
        )
    return value


def _non_negative_integer(value: object, label: str) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value < 0
    ):
        raise TokenBudgetValidationError(
            f"{label} must be a non-negative integer."
        )
    return value


def _positive_integer(value: object, label: str) -> int:
    result = _non_negative_integer(value, label)
    if result == 0:
        raise TokenBudgetValidationError(
            f"{label} must be greater than zero."
        )
    return result