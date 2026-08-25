"""Immutable contracts for model-placement comparison before Human Review."""

from __future__ import annotations

from dataclasses import dataclass


MODEL_PLACEMENT_SCHEMA_VERSION = "1.0.0"
MODEL_PLACEMENT_RESULTS = frozenset(
    {"proposed_mapping", "ambiguous", "unmapped"}
)
MODEL_PLACEMENT_AGREEMENT_LEVELS = frozenset(
    {
        "unanimous_mapping",
        "partial_mapping_agreement",
        "placement_variance",
        "unresolved",
    }
)


@dataclass(frozen=True, slots=True)
class ModelPlacementPersonaProposal:
    """One persona's exact placement proposal for one Approved Input."""

    persona_id: str
    approved_input_id: str
    result: str
    selected_rule_id: str | None
    alternative_rule_ids: tuple[str, ...]
    rationale: str
    proposal_fingerprint: str


@dataclass(frozen=True, slots=True)
class ModelPlacementRuleSupport:
    """Which personas referenced one profile-controlled placement rule."""

    rule_id: str
    supporting_personas: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ModelPlacementReviewItem:
    """One reviewable placement subject with preserved persona variance."""

    approved_input_id: str
    approved_input_kind: str
    stable_subject_key: str
    title: str
    primary_text: str
    information_type: str | None
    deterministic_disposition: str
    deterministic_candidate_rule_ids: tuple[str, ...]
    allowed_rule_ids: tuple[str, ...]
    persona_proposals: tuple[ModelPlacementPersonaProposal, ...]
    rule_support: tuple[ModelPlacementRuleSupport, ...]
    agreement_level: str
    unanimous_rule_id: str | None
    review_attention_required: bool
    content_fingerprint: str


@dataclass(frozen=True, slots=True)
class ModelPlacementBatchComparison:
    """Immutable comparison for one exact placement-request batch."""

    schema_version: str
    project_id: str
    profile_id: str
    profile_version: str
    profile_fingerprint: str
    request_fingerprint: str
    persona_ids: tuple[str, ...]
    items: tuple[ModelPlacementReviewItem, ...]
    human_review_required: bool
    content_fingerprint: str
