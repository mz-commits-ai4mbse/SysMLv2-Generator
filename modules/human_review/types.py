"""Immutable types for Human Review and deterministic token budgets."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


HUMAN_REVIEW_TARGET_TYPES = frozenset(
    {
        "information_unit_publication",
        "terminology_mapping_candidate",
        "framework_assignment_candidate",
    }
)

HUMAN_REVIEW_DECISIONS = frozenset(
    {
        "confirm",
        "reject",
        "request_changes",
    }
)

HUMAN_REVIEW_MODES = frozenset(
    {
        "quick_confirmation",
        "detailed_review",
    }
)

REFERENCE_VALIDATION_STATUSES = frozenset(
    {
        "valid",
        "invalid",
        "not_applicable",
    }
)

TOKEN_BUDGET_CATEGORIES = (
    "instruction_and_schema",
    "information_unit",
    "project_terminology",
    "turing_core",
    "external_reference_concepts",
    "framework_targets",
    "supplementary_context",
)


@dataclass(frozen=True, slots=True)
class HumanReviewTargetSnapshot:
    """Immutable identity and gate state presented to the reviewer."""

    target_type: str
    target_id: str
    target_content_fingerprint: str
    recommended_review_mode: str
    confirmation_required: bool
    reference_validation_status: str
    reference_validation_fingerprint: str | None


@dataclass(frozen=True, slots=True)
class HumanReviewDecision:
    """One immutable human decision about one exact artifact snapshot."""

    schema_version: str
    project_id: str
    human_review_decision_id: str
    target: HumanReviewTargetSnapshot
    review_mode: str
    decision: str
    reviewer_identity: str
    rationale: str | None
    decided_at: str
    decision_fingerprint: str


@dataclass(frozen=True, slots=True)
class HumanReviewIssue:
    """One deterministic review persistence or gate issue."""

    project_id: str
    code: str
    message: str
    issue_level: str
    path: Path | None = None
    human_review_decision_id: str | None = None
    target_type: str | None = None
    target_id: str | None = None


@dataclass(frozen=True, slots=True)
class HumanReviewScanResult:
    """Validated Human Review Decisions and persistence issues."""

    decisions: tuple[HumanReviewDecision, ...] = ()
    issues: tuple[HumanReviewIssue, ...] = ()


@dataclass(frozen=True, slots=True)
class TokenBudgetPolicy:
    """Versioned deterministic policy for one LLM context window."""

    policy_id: str
    policy_version: str
    safety_margin_tokens: int
    reserved_output_tokens: int
    reserved_system_tokens: int
    category_priority: tuple[str, ...]
    block_on_required_context_overflow: bool
    silent_required_context_truncation_allowed: bool


@dataclass(frozen=True, slots=True)
class TokenBudgetContextItem:
    """One traceable context item considered for a prompt."""

    category: str
    reference_id: str
    reference_version: str | None
    content: str
    content_sha256: str
    required: bool
    estimated_tokens: int


@dataclass(frozen=True, slots=True)
class TokenBudgetAllocation:
    """Deterministic selected and omitted context for one category."""

    category: str
    available_tokens_before: int
    allocated_tokens: int
    selected_reference_ids: tuple[str, ...]
    omitted_reference_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class TokenBudgetAssessment:
    """Auditable result of applying one policy to one model window."""

    policy_id: str
    policy_version: str
    model_context_window_tokens: int
    available_input_tokens: int
    required_context_tokens: int
    optional_context_tokens: int
    allocated_context_tokens: int
    context_fits: bool
    blocked: bool
    blocked_reason: str | None
    allocations: tuple[TokenBudgetAllocation, ...]