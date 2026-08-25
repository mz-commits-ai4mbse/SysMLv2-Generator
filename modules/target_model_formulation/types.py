"""Immutable Target-Model Formulation review contracts."""

from __future__ import annotations

from dataclasses import dataclass


TARGET_MODEL_RELEVANCE_OUTCOMES = frozenset(
    {
        "materialize_formally",
        "retain_as_context_only",
        "intentionally_not_materialized",
        "unresolved_human_review",
    }
)

REFERENCE_EVIDENCE_ROLES = frozenset(
    {
        "primary_language_and_syntax_reference",
        "validated_syntax_fixture",
        "non_normative_modeling_pattern_reference",
        "project_modeling_context_reference",
        "requirements_authoring_guidance",
        "target_model_formulation_guidance",
    }
)

TARGET_MODEL_SUBJECT_KINDS = frozenset({"element", "relationship"})


@dataclass(frozen=True, slots=True)
class TargetModelReferenceEvidence:
    source_id: str
    role: str
    locator: str
    evidence_note: str
    content_fingerprint: str


@dataclass(frozen=True, slots=True)
class TargetModelFormulationCandidate:
    candidate_id: str
    relevance_outcome: str
    target_model_pattern_id: str | None
    target_notation_construct_id: str | None
    formulation_text: str | None
    applied_formulation_rule_ids: tuple[str, ...]
    reference_evidence: tuple[TargetModelReferenceEvidence, ...]
    rationale: str
    unresolved_questions: tuple[str, ...]
    content_fingerprint: str


@dataclass(frozen=True, slots=True)
class TargetModelFormulationReviewItem:
    subject_kind: str
    authority_subject_id: str
    current_engineering_type: str
    current_target_representation: str
    candidates: tuple[TargetModelFormulationCandidate, ...]
    content_fingerprint: str


@dataclass(frozen=True, slots=True)
class TargetModelFormulationReview:
    schema_version: str
    project_id: str
    review_id: str
    source_internal_engineering_model_id: str
    source_internal_engineering_model_fingerprint: str
    final_model_review_decision_id: str
    final_model_review_decision_fingerprint: str
    target_model_profile_id: str
    target_model_profile_version: str
    target_model_profile_fingerprint: str
    target_notation_fingerprint: str
    items: tuple[TargetModelFormulationReviewItem, ...]
    created_at: str
    content_fingerprint: str
