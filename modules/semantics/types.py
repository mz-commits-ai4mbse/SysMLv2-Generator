"""Immutable data types for semantic references."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


REFERENCE_ENTITY_TYPES = frozenset(
    {
        "class",
        "object_property",
        "datatype_property",
    }
)

TURING_CORE_CONCEPT_KINDS = frozenset(
    {
        "stakeholder_context",
        "need",
        "requirement",
        "stakeholder_behavior",
        "behavior",
        "architecture_element",
        "system_context",
    }
)

TURING_CORE_CONCEPT_STATUSES = frozenset(
    {
        "active",
        "deprecated",
    }
)

TURING_CORE_EXTERNAL_MAPPING_STATUSES = frozenset(
    {
        "not_reviewed",
        "reviewed",
    }
)

TURING_CORE_EXTERNAL_MAPPING_RELATIONS = frozenset(
    {
        "exact_match",
        "narrower_than",
        "broader_than",
        "related_to",
        "no_equivalent",
    }
)


@dataclass(frozen=True, slots=True)
class Checksum:
    """One content-checksum declaration."""

    algorithm: str
    value: str


@dataclass(frozen=True, slots=True)
class RegistryAuthority:
    """Authority boundary declared by the Ontology Registry."""

    registry_role: str
    ontology_snapshot_role: str
    reference_concept_index_role: str
    engineering_authority: str
    engineering_authority_rule: str


@dataclass(frozen=True, slots=True)
class RuntimeBoundary:
    """Runtime capabilities permitted for ontology references."""

    live_ontology_queries: bool
    automatic_downloads: bool
    automatic_updates: bool
    remote_runtime_dependency_resolution: bool
    owl_reasoner: bool
    triple_store: bool
    unrestricted_graph_traversal: bool
    complete_ontology_prompt_loading: bool
    snapshot_update_policy: str


@dataclass(frozen=True, slots=True)
class SourceAuthority:
    """Pinned upstream authority for one reference system."""

    provider: str
    repository: str
    reference_type: str
    reference: str


@dataclass(frozen=True, slots=True)
class LicenseReference:
    """License metadata for one reference system."""

    identifier: str
    name: str
    url: str
    local_path: Path


@dataclass(frozen=True, slots=True)
class OntologyArtifact:
    """One registered local ontology artifact."""

    artifact_id: str
    artifact_role: str
    serialization: str
    media_type: str
    local_path: Path
    source_path: str
    git_blob_sha: str
    size_bytes: int
    checksum: Checksum
    version_iri: str | None = None
    declared_version_info: str | None = None


@dataclass(frozen=True, slots=True)
class OntologyReferenceSystem:
    """One external ontology reference system."""

    reference_system_id: str
    name: str
    reference_role: str
    version: str
    version_iri: str
    maturity: str
    runtime_enabled: bool
    enabled_runtime_role: str
    source_authority: SourceAuthority
    license: LicenseReference
    artifacts: tuple[OntologyArtifact, ...]


@dataclass(frozen=True, slots=True)
class ReferenceConceptIndexConfiguration:
    """Registry configuration for the generated concept index."""

    schema_version: str
    path: Path
    status: str
    authority: str
    deterministic: bool
    source_reference_system_ids: tuple[str, ...]
    runtime_usage: str
    complete_ontology_prompt_loading: bool


@dataclass(frozen=True, slots=True)
class OntologyRegistry:
    """Validated Ontology Registry content."""

    schema_version: str
    registry_id: str
    registry_version: str
    status: str
    authority: RegistryAuthority
    runtime_boundary: RuntimeBoundary
    reference_systems: tuple[OntologyReferenceSystem, ...]
    reference_concept_index: (
        ReferenceConceptIndexConfiguration
    )


@dataclass(frozen=True, slots=True)
class LocalizedText:
    """One language-qualified source text."""

    language: str
    text: str


@dataclass(frozen=True, slots=True)
class ReferenceConcept:
    """One deterministically indexed external concept."""

    reference_system_id: str
    artifact_id: str
    source_concept_id: str
    iri: str
    entity_type: str
    preferred_labels: tuple[LocalizedText, ...]
    alternative_labels: tuple[LocalizedText, ...]
    definitions: tuple[LocalizedText, ...]
    parent_iris: tuple[str, ...]
    version: str
    version_iri: str


@dataclass(frozen=True, slots=True)
class ReferenceConceptSourceSnapshot:
    """One verified source snapshot used to generate an index."""

    reference_system_id: str
    artifact_id: str
    version: str
    version_iri: str
    checksum: Checksum


@dataclass(frozen=True, slots=True)
class ReferenceConceptIndex:
    """One deterministic, derived Reference Concept Index."""

    schema_version: str
    index_id: str
    index_version: str
    status: str
    authority: str
    generator_id: str
    generator_version: str
    registry_id: str
    registry_version: str
    source_snapshots: tuple[
        ReferenceConceptSourceSnapshot,
        ...
    ]
    concept_count: int
    concepts: tuple[ReferenceConcept, ...]


@dataclass(frozen=True, slots=True)
class TuringCoreAuthority:
    """Authority boundary declared by Turing Core."""

    role: str
    engineering_authority: str
    framework_authority: str
    target_model_semantics: str
    external_reference_systems: tuple[str, ...]
    project_terminology_authority: str
    automatic_project_mutation_allowed: bool
    authority_rule: str


@dataclass(frozen=True, slots=True)
class TuringCoreSourceReference:
    """One repository source used to curate Turing Core."""

    source_reference_id: str
    path: Path
    role: str
    referenced_id: str | None = None
    referenced_version: str | None = None


@dataclass(frozen=True, slots=True)
class TuringCoreIdentifierPolicy:
    """Stable identifier policy for Turing Core concepts."""

    field: str
    pattern: str
    scope: str
    allocation: str
    reuse_allowed: bool
    meaning_change_allowed: bool


@dataclass(frozen=True, slots=True)
class TuringCoreLabelPolicy:
    """Label uniqueness policy for Turing Core concepts."""

    preferred_label_required: bool
    preferred_label_unique_casefolded: bool
    alternative_labels_unique_within_concept_casefolded: bool
    preferred_label_may_equal_alternative_label_casefolded: bool
    automatic_synonym_generation_allowed: bool


@dataclass(frozen=True, slots=True)
class TuringCoreConceptRelationPolicy:
    """Permitted internal concept-reference relations."""

    allowed_relations: tuple[str, ...]
    self_reference_allowed: bool
    unknown_concept_reference_behavior: str


@dataclass(frozen=True, slots=True)
class TuringCoreFrameworkMappingPolicy:
    """Boundary for Turing Core to framework references."""

    framework_template_id: str
    framework_template_version: str
    candidate_target_field: str
    scope_reference_field: str
    candidate_target_must_be_mapping_target: bool
    scope_reference_may_reference_level_node: bool
    automatic_framework_assignment_allowed: bool
    rule: str


@dataclass(frozen=True, slots=True)
class TuringCoreSysMLMappingPolicy:
    """Boundary for SysML v2 representation candidates."""

    target_notation_id: str
    target_notation_version: str
    allowed_relation: str
    unknown_construct_behavior: str
    automatic_model_generation_allowed: bool
    rule: str


@dataclass(frozen=True, slots=True)
class TuringCoreExternalMappingPolicy:
    """Boundary for external ontology mappings."""

    registry_id: str
    allowed_reference_system_ids: tuple[str, ...]
    allowed_relations: tuple[str, ...]
    mapping_required: bool
    review_required: bool
    automatic_exact_match_allowed: bool
    initial_mapping_status: str


@dataclass(frozen=True, slots=True)
class SysMLRepresentationCandidate:
    """One permitted SysML v2 representation candidate."""

    construct_id: str
    relation: str
    rationale: str


@dataclass(frozen=True, slots=True)
class ExternalOntologyMapping:
    """One reviewed mapping to an external ontology concept."""

    reference_system_id: str
    reference_system_version: str
    reference_concept_iri: str
    relation: str
    rationale: str
    provenance_source_reference_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class TuringCoreConcept:
    """One curated global Turing Core concept."""

    concept_id: str
    preferred_label: str
    alternative_labels: tuple[str, ...]
    definition: str
    concept_kind: str
    broader_concept_ids: tuple[str, ...]
    related_concept_ids: tuple[str, ...]
    candidate_framework_node_ids: tuple[str, ...]
    framework_scope_node_ids: tuple[str, ...]
    sysml_v2_representation_candidates: tuple[
        SysMLRepresentationCandidate,
        ...
    ]
    target_notation_note: str
    external_mapping_status: str
    external_mappings: tuple[
        ExternalOntologyMapping,
        ...
    ]
    provenance_source_reference_ids: tuple[str, ...]
    status: str
    order: int


@dataclass(frozen=True, slots=True)
class TuringCoreVocabulary:
    """One validated, versioned Turing Core Vocabulary."""

    schema_version: str
    vocabulary_id: str
    vocabulary_version: str
    name: str
    status: str
    default_language: str
    authority: TuringCoreAuthority
    source_references: tuple[
        TuringCoreSourceReference,
        ...
    ]
    identifier_policy: TuringCoreIdentifierPolicy
    label_policy: TuringCoreLabelPolicy
    concept_relation_policy: (
        TuringCoreConceptRelationPolicy
    )
    framework_mapping_policy: (
        TuringCoreFrameworkMappingPolicy
    )
    sysml_v2_mapping_policy: TuringCoreSysMLMappingPolicy
    external_mapping_policy: (
        TuringCoreExternalMappingPolicy
    )
    concepts: tuple[TuringCoreConcept, ...]