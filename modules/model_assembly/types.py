"""Immutable Model Assembly Draft contracts."""

from __future__ import annotations

from dataclasses import dataclass


MODEL_ASSEMBLY_DRAFT_SCHEMA_VERSION = "1.0.0"
MODEL_ASSEMBLY_PROJECT_AUTHORITY_SCHEMA_VERSION = "1.1.0"


@dataclass(frozen=True, slots=True)
class ModelAssemblyElement:
    approved_input_id: str
    stable_subject_key: str
    title: str
    primary_text: str
    selected_rule_id: str
    model_area: str
    element_type: str
    framework_assignment: str
    placement_decision_id: str
    placement_decision_fingerprint: str
    content_fingerprint: str


@dataclass(frozen=True, slots=True)
class ModelAssemblyRelationship:
    relationship_decision_id: str
    relationship_decision_fingerprint: str
    source_subject_id: str
    source_subject_key: str
    relationship_kind: str
    target_subject_id: str
    target_subject_key: str
    representation_status: str
    candidate_rule_ids: tuple[str, ...]
    human_rationale: str | None
    projection_rationale: str
    content_fingerprint: str


@dataclass(frozen=True, slots=True)
class ModelAssemblyDraft:
    schema_version: str
    project_id: str
    comparison_fingerprint: str
    approved_placement_set_fingerprint: str
    approved_engineering_information_fingerprint: str | None
    profile_id: str
    profile_version: str
    profile_fingerprint: str
    elements: tuple[ModelAssemblyElement, ...]
    relationships: tuple[ModelAssemblyRelationship, ...]
    intentionally_not_projected_relationship_decision_ids: tuple[str, ...]
    relationship_projection_provider: str | None
    relationship_projection_model: str | None
    relationship_projection_response_fingerprints: tuple[str, ...]
    content_fingerprint: str
    project_authority_handoff_fingerprint: str | None = None
    project_engineering_authority_fingerprint: str | None = None
    model_impact_reconciliation_fingerprint: str | None = None
    source_approved_engineering_information_fingerprints: tuple[str, ...] = ()

    @property
    def relationship_variance_count(self) -> int:
        return sum(
            1
            for item in self.relationships
            if item.representation_status == "persona_variance"
        )

    @property
    def unresolved_relationship_count(self) -> int:
        return sum(
            1
            for item in self.relationships
            if item.representation_status == "unmapped"
        )
