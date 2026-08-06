"""Immutable data types for the Human Review Workspace."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from modules.project_processing.types import (
    ProcessingArtifactReference,
    SemanticReferenceVersion,
)
from modules.project_workspace.types import (
    FrameworkTemplateReference,
)


REVIEW_DOCUMENT_VERSION_STATES = frozenset(
    {
        "draft",
        "finalized",
    }
)

REVIEW_ITEM_KINDS = frozenset(
    {
        "element",
        "relationship",
        "open_question",
    }
)

REVIEW_ITEM_SECTIONS = frozenset(
    {
        "elements",
        "relationships",
        "open_questions",
    }
)

REVIEW_PRIMARY_VIEWS = frozenset(
    {
        "elements",
        "relationships",
        "open_questions",
        "rejected_content",
    }
)

REVIEW_ITEM_OUTCOMES = frozenset(
    {
        "open",
        "accepted_as_generated",
        "accepted_with_modification",
        "combined",
        "rejected",
        "deferred",
        "out_of_scope",
        "unresolved",
    }
)

REVIEW_ACTION_SCOPES = frozenset(
    {
        "document_default",
        "filtered_set",
        "explicit_selection",
    }
)

REVIEW_DECISION_DIMENSIONS = frozenset(
    {
        "content",
        "classification",
        "framework_assignment",
        "terminology_assignment",
        "source_assignment",
        "relationship_representation",
        "review_outcome",
    }
)

REVIEW_VALUE_ORIGINS = frozenset(
    {
        "agent_proposal",
        "document_default",
        "filtered_set",
        "explicit_selection",
        "item_override",
    }
)

REVIEW_PROPOSAL_STATES = frozenset(
    {
        "available",
        "selected",
        "not_selected_due_to_human_selection",
        "rejected",
    }
)

REVIEW_ITEM_LINEAGE_OPERATIONS = frozenset(
    {
        "original",
        "split",
        "merge",
        "human_created",
        "carried_forward",
    }
)

RELATIONSHIP_PROFILE_VALIDATION_STATUSES = frozenset(
    {
        "not_applicable",
        "unresolved",
        "valid",
        "invalid",
    }
)

REVIEW_ISSUE_LEVELS = frozenset(
    {
        "warning",
        "blocking",
    }
)


@dataclass(frozen=True, slots=True)
class ReviewProperty:
    """One immutable construct-specific property."""

    name: str
    value: str


@dataclass(frozen=True, slots=True)
class ReviewProposalReference:
    """One exact immutable Agent proposal reference."""

    artifact_reference: ProcessingArtifactReference
    agent_id: str
    persona_id: str
    proposal_id: str
    proposal_content_fingerprint: str
    original_report_locator: str
    review_state: str


@dataclass(frozen=True, slots=True)
class ReviewEvidenceReference:
    """One exact evidence fragment supporting a Review Item."""

    artifact_reference: ProcessingArtifactReference
    evidence_role: str
    evidence_locator: str
    evidence_content_fingerprint: str


@dataclass(frozen=True, slots=True)
class ReviewRelationshipRepresentation:
    """One reviewable SysML v2 relationship representation."""

    source_subject_key: str
    target_subject_key: str
    semantic_intent: str
    sysml_v2_construct: str | None
    construct_properties: tuple[ReviewProperty, ...]
    target_notation_profile_id: str
    target_notation_profile_version: str
    textual_notation_preview: str | None
    validation_status: str
    validation_fingerprint: str | None


@dataclass(frozen=True, slots=True)
class ReviewDimensionSelection:
    """One effective draft selection for a review dimension."""

    dimension: str
    selected_values: tuple[str, ...]
    value_origin: str
    source_reference_ids: tuple[str, ...]
    rationale: str | None
    selected_by: str | None
    selected_at: str | None


@dataclass(frozen=True, slots=True)
class ReviewItemContent:
    """Current human-reviewable content of one Review Item."""

    title: str
    primary_text: str
    description: str | None
    information_type: str | None
    modality: str | None
    epistemic_status: str | None
    human_rationale: str | None
    human_confidence: str | None
    relationship_representation: (
        ReviewRelationshipRepresentation | None
    )


@dataclass(frozen=True, slots=True)
class ReviewItem:
    """One independently reviewable subject in one revision."""

    schema_version: str
    project_id: str
    review_document_id: str
    review_document_version_id: str
    review_item_id: str
    review_item_kind: str
    stable_subject_key: str
    section: str
    lineage_operation: str
    derived_from_review_item_ids: tuple[str, ...]
    original_report_locator: str
    proposal_references: tuple[
        ReviewProposalReference,
        ...,
    ]
    source_evidence_references: tuple[
        ReviewEvidenceReference,
        ...,
    ]
    consensus_evidence_references: tuple[
        ReviewEvidenceReference,
        ...,
    ]
    current_content: ReviewItemContent
    dimension_selections: tuple[
        ReviewDimensionSelection,
        ...,
    ]
    effective_review_outcome: str
    item_content_fingerprint: str


@dataclass(frozen=True, slots=True)
class ReviewDocument:
    """Immutable identity of one Human Review Workspace document."""

    schema_version: str
    project_id: str
    review_document_id: str
    source_id: str
    source_sha256: str
    processing_run_id: str
    attempt_id: str
    primary_review_artifact_reference: (
        ProcessingArtifactReference
    )
    supporting_artifact_references: tuple[
        ProcessingArtifactReference,
        ...,
    ]
    framework_template: FrameworkTemplateReference
    semantic_reference_versions: tuple[
        SemanticReferenceVersion,
        ...,
    ]
    created_at: str
    content_fingerprint: str


@dataclass(frozen=True, slots=True)
class ReviewDocumentVersion:
    """One immutable version-state record of a Review Document."""

    schema_version: str
    project_id: str
    review_document_id: str
    review_document_version_id: str
    version_number: int
    predecessor_version_id: str | None
    reopen_reason: str | None
    opened_by: str
    opened_at: str
    version_state: str
    head_revision_id: str
    finalized_revision_id: str | None
    finalized_at: str | None
    finalization_decision_id: str | None
    content_fingerprint: str


@dataclass(frozen=True, slots=True)
class ReviewRevision:
    """One immutable saved snapshot of a draft review version."""

    schema_version: str
    project_id: str
    review_document_id: str
    review_document_version_id: str
    review_revision_id: str
    revision_sequence: int
    predecessor_revision_id: str | None
    review_items: tuple[ReviewItem, ...]
    scoped_review_action_ids: tuple[str, ...]
    created_by: str
    created_at: str
    revision_fingerprint: str


@dataclass(frozen=True, slots=True)
class MaterializedReviewItemReference:
    """One exact Review Item captured by a scoped action."""

    review_item_id: str
    item_content_fingerprint: str


@dataclass(frozen=True, slots=True)
class ScopedReviewAction:
    """One immutable action over an exact set of Review Items."""

    schema_version: str
    project_id: str
    review_document_id: str
    review_document_version_id: str
    scoped_review_action_id: str
    action_scope: str
    decision_dimension: str
    selected_values: tuple[str, ...]
    filter_definition: str | None
    materialized_items: tuple[
        MaterializedReviewItemReference,
        ...,
    ]
    created_by: str
    created_at: str
    rationale: str | None
    action_fingerprint: str


@dataclass(frozen=True, slots=True)
class ReviewWorkspaceIssue:
    """One deterministic review-workspace issue."""

    project_id: str
    code: str
    message: str
    issue_level: str
    path: Path | None
    review_document_id: str | None
    review_document_version_id: str | None
    review_revision_id: str | None
    review_item_id: str | None
    scoped_review_action_id: str | None


@dataclass(frozen=True, slots=True)
class ReviewWorkspaceScanResult:
    """Validated review artifacts and explicit scan issues."""

    documents: tuple[ReviewDocument, ...] = ()
    versions: tuple[ReviewDocumentVersion, ...] = ()
    revisions: tuple[ReviewRevision, ...] = ()
    scoped_actions: tuple[ScopedReviewAction, ...] = ()
    issues: tuple[ReviewWorkspaceIssue, ...] = ()
