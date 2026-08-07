"""Foundation types and vocabularies for Approved Input."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from modules.project_processing.types import (
    ProcessingArtifactReference,
)


APPROVED_INPUT_KINDS = frozenset(
    {
        "element_statement",
        "relationship_statement",
        "human_clarification",
    }
)

APPROVED_INPUT_AUTHORITY_STATES = frozenset(
    {
        "active",
        "invalidated",
        "revoked",
        "superseded",
    }
)

INITIAL_APPROVED_INPUT_AUTHORITY_STATE = "active"

APPROVED_INPUT_EVENT_TYPES = frozenset(
    {
        "invalidated",
        "revoked",
        "superseded",
    }
)


@dataclass(frozen=True, slots=True)
class ApprovedInputEvent:
    """One immutable terminal lifecycle transition for an Approved Input."""

    schema_version: str
    project_id: str
    approved_input_event_id: str
    approved_input_id: str
    event_type: str
    previous_authority_state: str
    next_authority_state: str
    reason_code: str
    rationale: str | None
    actor_identity: str
    successor_approved_input_id: str | None
    causal_review_document_id: str | None
    causal_review_document_version_id: str | None
    causal_review_revision_id: str | None
    causal_finalization_decision_id: str | None
    causal_finalization_decision_fingerprint: str | None
    occurred_at: str
    previous_event_fingerprint: str | None
    event_fingerprint: str


@dataclass(frozen=True, slots=True)
class ApprovedInputCanonicalContent:
    """Canonical reviewed engineering content of one Approved Input."""

    title: str
    primary_text: str
    description: str | None
    information_type: str | None
    modality: str | None
    epistemic_status: str | None


@dataclass(frozen=True, slots=True)
class ApprovedInputRelationshipProperty:
    """One immutable relationship construct property."""

    name: str
    value: str


@dataclass(frozen=True, slots=True)
class ApprovedInputRelationshipRepresentation:
    """One profile-valid relationship representation for downstream use."""

    source_subject_key: str
    target_subject_key: str
    semantic_intent: str
    sysml_v2_construct: str
    construct_properties: tuple[
        ApprovedInputRelationshipProperty,
        ...,
    ]
    target_notation_profile_id: str
    target_notation_profile_version: str
    textual_notation_preview: str
    profile_validation_status: str
    profile_validation_fingerprint: str


@dataclass(frozen=True, slots=True)
class ApprovedInputManifest:
    """Immutable approved engineering-information item."""

    schema_version: str
    project_id: str
    approved_input_id: str
    approved_input_kind: str
    authority_state: str
    canonical_content: ApprovedInputCanonicalContent
    selected_classification: str | None
    selected_framework_assignment: str | None
    selected_terminology_assignment: str | None
    selected_source_assignments: tuple[str, ...]
    selected_relationship_representation: (
        ApprovedInputRelationshipRepresentation | None
    )
    stable_subject_key: str
    review_document_id: str
    review_document_version_id: str
    review_revision_id: str
    review_item_id: str
    review_item_kind: str
    review_item_fingerprint: str
    finalized_artifact_set_fingerprint: str
    finalization_decision_id: str
    finalization_decision_fingerprint: str
    finalization_validation_fingerprint: str
    source_id: str
    source_sha256: str
    processing_run_id: str
    attempt_id: str
    primary_artifact_reference: ProcessingArtifactReference
    supporting_artifact_references: tuple[
        ProcessingArtifactReference,
        ...,
    ]
    proposal_references: tuple[str, ...]
    created_at: str
    content_fingerprint: str


APPROVED_INPUT_REPOSITORY_ISSUE_LEVELS = frozenset(
    {
        "warning",
        "blocking",
    }
)


@dataclass(frozen=True, slots=True)
class ApprovedInputAuthoritySnapshot:
    """Derived current authority state for one immutable manifest."""

    manifest: ApprovedInputManifest
    authority_state: str
    latest_event_fingerprint: str | None


@dataclass(frozen=True, slots=True)
class ApprovedInputRepositoryIssue:
    """One deterministic Approved Input repository issue."""

    project_id: str
    code: str
    message: str
    issue_level: str
    path: Path | None
    approved_input_id: str | None
    approved_input_event_id: str | None = None


@dataclass(frozen=True, slots=True)
class ApprovedInputRepositoryScanResult:
    """Validated Approved Input manifests and explicit scan issues."""

    manifests: tuple[ApprovedInputManifest, ...] = ()
    events: tuple[ApprovedInputEvent, ...] = ()
    issues: tuple[ApprovedInputRepositoryIssue, ...] = ()
