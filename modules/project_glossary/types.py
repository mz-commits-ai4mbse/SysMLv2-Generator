"""Immutable data types for project-specific terminology."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


PROJECT_CONCEPT_LIFECYCLE_STATES = frozenset(
    {
        "candidate",
        "accepted",
        "rejected",
        "deprecated",
    }
)

PROJECT_CONCEPT_PROVENANCE_TYPES = frozenset(
    {
        "engineering_source",
        "context_only_source",
        "terminology_decision",
        "external_reference",
        "turing_core",
    }
)

PROJECT_CONCEPT_MAPPING_RELATIONS = frozenset(
    {
        "exact_match",
        "narrower_than",
        "broader_than",
        "related_to",
        "no_equivalent",
    }
)

AMBIGUITY_RESOLUTION_RULES = frozenset(
    {
        "context_required",
    }
)

TERMINOLOGY_DECISION_ACTIONS = frozenset(
    {
        "accept",
        "reject",
        "deprecate",
    }
)


@dataclass(frozen=True, slots=True)
class LocalizedGlossaryText:
    """One language-qualified glossary text."""

    language: str
    text: str


@dataclass(frozen=True, slots=True)
class ProjectConceptProvenance:
    """One typed provenance reference for a concept revision."""

    provenance_type: str
    reference_id: str
    rationale: str
    reference_system_id: str | None = None
    reference_version: str | None = None
    source_projection_id: str | None = None
    segment_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class TuringCoreConceptMapping:
    """One reviewed or candidate mapping to Turing Core."""

    vocabulary_id: str
    vocabulary_version: str
    turing_core_concept_id: str
    relation: str
    rationale: str


@dataclass(frozen=True, slots=True)
class ProjectExternalOntologyMapping:
    """One project-concept mapping to an external ontology."""

    reference_system_id: str
    reference_system_version: str
    reference_concept_iri: str
    relation: str
    rationale: str


@dataclass(frozen=True, slots=True)
class ProjectConceptRevision:
    """One preserved semantic revision of a Project Concept."""

    revision: int
    lifecycle_status: str
    preferred_labels: tuple[LocalizedGlossaryText, ...]
    alternative_labels: tuple[LocalizedGlossaryText, ...]
    definitions: tuple[LocalizedGlossaryText, ...]
    broader_project_concept_ids: tuple[str, ...]
    related_project_concept_ids: tuple[str, ...]
    turing_core_mappings: tuple[
        TuringCoreConceptMapping,
        ...
    ]
    external_ontology_mappings: tuple[
        ProjectExternalOntologyMapping,
        ...
    ]
    provenance: tuple[ProjectConceptProvenance, ...]
    rationale: str
    created_at: str


@dataclass(frozen=True, slots=True)
class ProjectConcept:
    """One stable Project Concept with preserved revisions."""

    project_concept_id: str
    latest_revision: int
    revisions: tuple[ProjectConceptRevision, ...]


@dataclass(frozen=True, slots=True)
class AmbiguityGroup:
    """One explicit homonym group requiring context."""

    ambiguity_group_id: str
    label: str
    language: str
    candidate_project_concept_ids: tuple[str, ...]
    resolution_rule: str
    rationale: str
    created_at: str


@dataclass(frozen=True, slots=True)
class ProjectGlossary:
    """One validated, versioned Project Glossary."""

    schema_version: str
    project_id: str
    glossary_revision: int
    default_language: str
    created_at: str
    updated_at: str
    concepts: tuple[ProjectConcept, ...]
    ambiguity_groups: tuple[AmbiguityGroup, ...]


@dataclass(frozen=True, slots=True)
class TerminologyDecision:
    """One immutable human terminology decision."""

    schema_version: str
    project_id: str
    terminology_decision_id: str
    project_concept_id: str
    project_concept_revision: int
    decision: str
    previous_lifecycle_status: str
    resulting_lifecycle_status: str
    reviewer_identity: str
    decided_at: str
    rationale: str


@dataclass(frozen=True, slots=True)
class ProjectGlossaryIssue:
    """One deterministic issue found in glossary persistence."""

    project_id: str
    code: str
    message: str
    path: Path
    project_concept_id: str | None = None
    terminology_decision_id: str | None = None
    ambiguity_group_id: str | None = None


@dataclass(frozen=True, slots=True)
class ProjectGlossaryScanResult:
    """Validated glossary state and blocking persistence issues."""

    glossary: ProjectGlossary | None = None
    terminology_decisions: tuple[
        TerminologyDecision,
        ...
    ] = ()
    issues: tuple[ProjectGlossaryIssue, ...] = ()