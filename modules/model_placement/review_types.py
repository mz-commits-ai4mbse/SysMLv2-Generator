"""Immutable Human Model Placement Review contracts."""

from __future__ import annotations

from dataclasses import dataclass


MODEL_PLACEMENT_REVIEW_DECISION_SCHEMA_VERSION = "1.0.0"
MODEL_PLACEMENT_REVIEW_OUTCOMES = frozenset(
    {"accepted", "rejected", "deferred", "reopened"}
)


@dataclass(frozen=True, slots=True)
class ModelPlacementReviewDecision:
    """One immutable Human decision bound to one exact placement review item."""

    schema_version: str
    project_id: str
    decision_id: str
    comparison_fingerprint: str
    review_item_fingerprint: str
    approved_input_id: str
    outcome: str
    selected_rule_id: str | None
    reviewer_identity: str
    rationale: str | None
    supersedes_decision_id: str | None
    reviewed_at: str
    decision_fingerprint: str


@dataclass(frozen=True, slots=True)
class ModelPlacementReviewState:
    """Effective Human-review state for one placement comparison bundle."""

    project_id: str
    comparison_fingerprint: str
    total_count: int
    pending_count: int
    accepted_count: int
    rejected_count: int
    deferred_count: int
    reopened_count: int
    latest_decisions: tuple[ModelPlacementReviewDecision, ...]

    @property
    def is_complete(self) -> bool:
        return self.pending_count == 0 and self.reopened_count == 0
