"""Immutable ADR-032 S5 Model Impact Reconciliation types."""

from __future__ import annotations

from dataclasses import dataclass


MODEL_IMPACT_OUTCOMES = frozenset(
    {
        "retain",
        "extend",
        "modify",
        "new",
        "supersede",
        "unresolved",
    }
)


@dataclass(frozen=True, slots=True)
class ModelImpactProposal:
    """Advisory impact evidence for one Human-reviewed Approved Input."""

    approved_input_id: str
    source_id: str
    stable_subject_key: str
    project_authority_state: str
    authority_concern_ids: tuple[str, ...]
    outcome: str
    current_model_element_ids: tuple[str, ...]
    related_model_element_ids: tuple[str, ...]
    impacted_relationship_ids: tuple[str, ...]
    model_change_required: bool
    rationale_code: str
    content_fingerprint: str


@dataclass(frozen=True, slots=True)
class ModelImpactReconciliationArtifact:
    """Immutable advisory comparison between S4 authority and accepted model."""

    schema_version: str
    project_id: str
    project_authority_fingerprint: str
    accepted_model_id: str | None
    accepted_model_fingerprint: str | None
    accepted_model_final_review_decision_id: str | None
    accepted_model_final_review_decision_fingerprint: str | None
    accepted_model_profile_id: str | None
    accepted_model_profile_version: str | None
    accepted_model_profile_fingerprint: str | None
    proposals: tuple[ModelImpactProposal, ...]
    unaffected_model_element_ids: tuple[str, ...]
    unaffected_model_relationship_ids: tuple[str, ...]
    unresolved_approved_input_ids: tuple[str, ...]
    model_change_required: bool
    human_model_review_required: bool
    content_fingerprint: str
