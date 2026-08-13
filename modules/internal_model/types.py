"""Immutable domain types for Phase-I Internal Engineering Models."""

from __future__ import annotations

from dataclasses import dataclass

from modules.model_candidates.types import (
    ModelCandidateApprovedInputReference,
    ModelCandidateReviewDecisionReference,
    ModelDerivationRulesReference,
    ModelStructureProfileReference,
)
from modules.project_workspace.types import FrameworkTemplateReference


@dataclass(frozen=True, slots=True)
class InternalModelAssemblyRulesReference:
    """Pinned identity of deterministic Phase-I assembly rules."""

    rules_id: str
    rules_version: str
    rules_fingerprint: str


@dataclass(frozen=True, slots=True)
class InternalModelAssemblyProvenance:
    """Traceable description of one deterministic Phase-I assembly."""

    method: str
    implementation_reference: str | None
    recipe_reference: str | None
    context_fingerprint: str | None


@dataclass(frozen=True, slots=True)
class InternalModelAssemblyContext:
    """Pinned configuration required to reproduce Internal Model assembly."""

    framework_template_reference: FrameworkTemplateReference
    model_structure_profile_reference: ModelStructureProfileReference
    derivation_rules_reference: ModelDerivationRulesReference
    assembly_rules_reference: InternalModelAssemblyRulesReference


@dataclass(frozen=True, slots=True)
class InternalModelAttribute:
    """One immutable assembled engineering-model attribute."""

    name: str
    value: str


@dataclass(frozen=True, slots=True)
class InternalModelElement:
    """One immutable engineering element assembled from an accepted MCE."""

    schema_version: str
    project_id: str
    internal_engineering_model_id: str
    internal_model_element_id: str
    model_subject_key: str
    source_model_element_candidate_id: str
    source_model_element_candidate_fingerprint: str
    name: str
    description: str | None
    model_area: str
    element_type: str
    framework_assignment: str
    terminology_assignment: str | None
    attributes: tuple[InternalModelAttribute, ...]
    comparison_anchor_id: str | None
    approved_input_references: tuple[
        ModelCandidateApprovedInputReference,
        ...,
    ]
    review_decision_reference: ModelCandidateReviewDecisionReference
    accepted_exception_reference: (
        ModelCandidateReviewDecisionReference | None
    )
    content_fingerprint: str


@dataclass(frozen=True, slots=True)
class InternalModelRelationship:
    """One immutable relationship assembled from an accepted MCR."""

    schema_version: str
    project_id: str
    internal_engineering_model_id: str
    internal_model_relationship_id: str
    source_internal_model_element_id: str
    target_internal_model_element_id: str
    source_model_subject_key: str
    target_model_subject_key: str
    relationship_family: str
    semantic_intent: str
    directionality: str
    source_model_relationship_candidate_id: str
    source_model_relationship_candidate_fingerprint: str
    approved_input_references: tuple[
        ModelCandidateApprovedInputReference,
        ...,
    ]
    review_decision_reference: ModelCandidateReviewDecisionReference
    accepted_exception_reference: (
        ModelCandidateReviewDecisionReference | None
    )
    content_fingerprint: str


@dataclass(frozen=True, slots=True)
class InternalModelStructureNode:
    """One materialized Framework Template node in an IEM snapshot."""

    framework_node_id: str
    mapping_key: str
    name: str
    node_type: str
    parent_framework_node_id: str | None
    order: int
    internal_model_element_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class InternalModelStructure:
    """Deterministic structural skeleton plus exact IME membership."""

    schema_version: str
    project_id: str
    internal_engineering_model_id: str
    framework_template_reference: FrameworkTemplateReference
    nodes: tuple[InternalModelStructureNode, ...]
    content_fingerprint: str


@dataclass(frozen=True, slots=True)
class InternalModelAssemblyFinding:
    """Explicit fail-closed diagnostic produced during deterministic assembly."""

    code: str
    message: str
    issue_level: str
    target_type: str | None = None
    target_id: str | None = None


@dataclass(frozen=True, slots=True)
class InternalEngineeringModelManifest:
    """Immutable snapshot manifest for one complete Internal Engineering Model."""

    schema_version: str
    project_id: str
    internal_engineering_model_id: str
    assembly_input_fingerprint: str
    candidate_set_id: str
    candidate_set_content_fingerprint: str
    approved_input_snapshot_fingerprint: str
    assembly_context: InternalModelAssemblyContext
    assembly_provenance: InternalModelAssemblyProvenance
    structure_content_fingerprint: str
    internal_model_element_ids: tuple[str, ...]
    internal_model_relationship_ids: tuple[str, ...]
    review_decision_references: tuple[
        ModelCandidateReviewDecisionReference,
        ...,
    ]
    accepted_exception_references: tuple[
        ModelCandidateReviewDecisionReference,
        ...,
    ]
    created_at: str
    content_fingerprint: str


@dataclass(frozen=True, slots=True)
class InternalEngineeringModelSnapshot:
    """One complete validated in-memory Internal Engineering Model bundle."""

    manifest: InternalEngineeringModelManifest
    structure: InternalModelStructure
    elements: tuple[InternalModelElement, ...]
    relationships: tuple[InternalModelRelationship, ...]
