"""Immutable deterministic projection-plan contracts for Phase-J J3."""

from __future__ import annotations

from dataclasses import dataclass

from .types import (
    SysMLArtifactStructureReference,
    SysMLGenerationProfileReference,
    TargetNotationReference,
)


@dataclass(frozen=True, slots=True)
class SysMLPackageProjection:
    """One deterministic Framework-node → SysML package projection."""

    framework_node_id: str
    mapping_key: str
    package_name: str
    parent_framework_node_id: str | None
    parent_package_name: str | None
    order: int
    depth: int
    order_path: tuple[int, ...]
    include_empty: bool


@dataclass(frozen=True, slots=True)
class SysMLElementProjection:
    """One deterministic IEM-element placement and symbol projection."""

    internal_model_element_id: str
    generated_symbol: str
    framework_node_id: str
    package_name: str
    model_area: str
    element_type: str
    engineering_name: str
    engineering_description: str | None
    generation_rule_id: str
    target_construct_id: str


@dataclass(frozen=True, slots=True)
class SysMLRelationshipProjection:
    """One deterministic relationship endpoint and target-construct projection."""

    internal_model_relationship_id: str
    generated_trace_symbol: str
    source_internal_model_element_id: str
    target_internal_model_element_id: str
    source_generated_symbol: str
    target_generated_symbol: str
    relationship_family: str
    semantic_intent: str
    directionality: str
    generation_rule_id: str
    target_construct_id: str
    endpoint_rendering: str


@dataclass(frozen=True, slots=True)
class SysMLProjectionPlan:
    """Canonical J3 plan consumed by later element/relationship renderers."""

    project_id: str
    internal_engineering_model_id: str
    target_notation_reference: TargetNotationReference
    generation_profile_reference: SysMLGenerationProfileReference
    artifact_structure_reference: SysMLArtifactStructureReference
    generated_unit_id: str
    relative_path: str
    root_package_name: str
    packages: tuple[SysMLPackageProjection, ...]
    elements: tuple[SysMLElementProjection, ...]
    relationships: tuple[SysMLRelationshipProjection, ...]
