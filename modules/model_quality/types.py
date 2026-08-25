"""Immutable types for SEM-015 model-quality refinement."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ModelQualityInputElement:
    internal_model_element_id: str
    approved_input_id: str
    model_subject_key: str
    original_name: str
    original_description: str | None
    element_type: str
    model_area: str
    framework_assignment: str
    source_element_fingerprint: str
    classification_fingerprint: str
    quality_rule_ids: tuple[str, ...]
    quality_rule_texts: tuple[str, ...]
    content_fingerprint: str


@dataclass(frozen=True, slots=True)
class ModelQualityRefinementRequest:
    schema_version: str
    project_id: str
    source_internal_engineering_model_id: str
    source_internal_engineering_model_fingerprint: str
    quality_profile_id: str
    quality_profile_version: str
    quality_profile_fingerprint: str
    elements: tuple[ModelQualityInputElement, ...]
    request_fingerprint: str


@dataclass(frozen=True, slots=True)
class ModelQualityRefinementProposal:
    internal_model_element_id: str
    input_element_fingerprint: str
    classification_fingerprint: str
    refined_name: str
    refined_description: str | None
    quality_findings: tuple[str, ...]
    applied_rule_ids: tuple[str, ...]
    meaning_preserved: bool
    unsupported_information_added: bool
    requires_human_attention: bool
    rationale: str
    content_fingerprint: str


@dataclass(frozen=True, slots=True)
class ModelQualityRefinementBundle:
    schema_version: str
    project_id: str
    review_id: str
    request_fingerprint: str
    source_internal_engineering_model_id: str
    source_internal_engineering_model_fingerprint: str
    quality_profile_id: str
    quality_profile_version: str
    quality_profile_fingerprint: str
    provider: str
    model: str
    proposals: tuple[ModelQualityRefinementProposal, ...]
    supporting_response_fingerprints: tuple[str, ...]
    generated_at: str
    content_fingerprint: str


@dataclass(frozen=True, slots=True)
class ModelQualityDecision:
    schema_version: str
    project_id: str
    decision_id: str
    review_id: str
    review_fingerprint: str
    internal_model_element_id: str
    proposal_fingerprint: str
    decision: str
    approved_name: str | None
    approved_description: str | None
    reviewer_identity: str
    rationale: str
    decided_at: str
    supersedes_decision_id: str | None
    content_fingerprint: str


@dataclass(frozen=True, slots=True)
class ModelQualityAuthoritySet:
    schema_version: str
    project_id: str
    authority_set_id: str
    review_id: str
    review_fingerprint: str
    source_internal_engineering_model_id: str
    source_internal_engineering_model_fingerprint: str
    effective_decisions: tuple[ModelQualityDecision, ...]
    created_at: str
    content_fingerprint: str
