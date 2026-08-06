"""Tests for immutable Human Review Workspace data types."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, fields
from pathlib import Path

import pytest

from modules.project_processing.types import (
    ProcessingArtifactReference,
    SemanticReferenceVersion,
)
from modules.project_workspace.types import (
    FrameworkTemplateReference,
)
from modules.review_workspace.types import (
    RELATIONSHIP_PROFILE_VALIDATION_STATUSES,
    REVIEW_ACTION_SCOPES,
    REVIEW_DECISION_DIMENSIONS,
    REVIEW_DOCUMENT_VERSION_STATES,
    REVIEW_ISSUE_LEVELS,
    REVIEW_ITEM_KINDS,
    REVIEW_ITEM_LINEAGE_OPERATIONS,
    REVIEW_ITEM_OUTCOMES,
    REVIEW_ITEM_SECTIONS,
    REVIEW_PRIMARY_VIEWS,
    REVIEW_PROPOSAL_STATES,
    REVIEW_VALUE_ORIGINS,
    MaterializedReviewItemReference,
    ReviewDimensionSelection,
    ReviewDocument,
    ReviewDocumentVersion,
    ReviewEvidenceReference,
    ReviewItem,
    ReviewItemContent,
    ReviewProperty,
    ReviewProposalReference,
    ReviewRelationshipRepresentation,
    ReviewRevision,
    ReviewWorkspaceIssue,
    ReviewWorkspaceScanResult,
    ScopedReviewAction,
)


def _artifact_reference() -> ProcessingArtifactReference:
    return ProcessingArtifactReference(
        artifact_type="review_reports",
        artifact_id="REPORT-001",
        content_fingerprint="a" * 64,
        repository_relative_path=(
            "data/projects/000001/runs/RUN-000001/"
            "artifacts/review_reports/report.md"
        ),
    )


def _relationship() -> ReviewRelationshipRepresentation:
    return ReviewRelationshipRepresentation(
        source_subject_key="source-subject",
        target_subject_key="target-subject",
        semantic_intent="Source depends on target.",
        sysml_v2_construct="dependency",
        construct_properties=(
            ReviewProperty(
                name="direction",
                value="source_to_target",
            ),
        ),
        target_notation_profile_id="SYSML_V2_TARGET",
        target_notation_profile_version="1.0.0",
        textual_notation_preview=(
            "dependency from 'Source' to 'Target';"
        ),
        validation_status="valid",
        validation_fingerprint="b" * 64,
    )


def _proposal() -> ReviewProposalReference:
    return ReviewProposalReference(
        artifact_reference=_artifact_reference(),
        agent_id="AGENT_001",
        persona_id="systems_engineer",
        proposal_id="CAND-001",
        proposal_content_fingerprint="c" * 64,
        original_report_locator="candidate-elements/CAND-001",
        review_state="selected",
    )


def _evidence() -> ReviewEvidenceReference:
    return ReviewEvidenceReference(
        artifact_reference=_artifact_reference(),
        evidence_role="source_evidence",
        evidence_locator="source-information/SI-001",
        evidence_content_fingerprint="d" * 64,
    )


def _selection() -> ReviewDimensionSelection:
    return ReviewDimensionSelection(
        dimension="framework_assignment",
        selected_values=("02_System/01_Requirements",),
        value_origin="item_override",
        source_reference_ids=("FAC-000001",),
        rationale="Document contains system requirements.",
        selected_by="reviewer@example.com",
        selected_at="2026-08-03T15:00:00Z",
    )


def _content() -> ReviewItemContent:
    return ReviewItemContent(
        title="Upload engineering source",
        primary_text=(
            "The system shall accept an engineering source."
        ),
        description=None,
        information_type="requirement",
        modality="shall",
        epistemic_status="asserted",
        human_rationale=None,
        human_confidence="high",
        relationship_representation=None,
    )


def _review_item() -> ReviewItem:
    return ReviewItem(
        schema_version="1.0.0",
        project_id="000001",
        review_document_id="RVD-000001",
        review_document_version_id="RVV-000001",
        review_item_id="RIT-000001",
        review_item_kind="element",
        stable_subject_key="upload-engineering-source",
        section="elements",
        lineage_operation="original",
        derived_from_review_item_ids=(),
        original_report_locator="candidate-elements/CAND-001",
        proposal_references=(_proposal(),),
        source_evidence_references=(_evidence(),),
        consensus_evidence_references=(),
        current_content=_content(),
        dimension_selections=(_selection(),),
        effective_review_outcome="accepted_with_modification",
        item_content_fingerprint="e" * 64,
    )


def _instances() -> tuple[object, ...]:
    document = ReviewDocument(
        schema_version="1.0.0",
        project_id="000001",
        review_document_id="RVD-000001",
        source_id="SRC-000001",
        source_sha256="f" * 64,
        processing_run_id="RUN-000001",
        attempt_id="ATT-000001",
        primary_review_artifact_reference=_artifact_reference(),
        supporting_artifact_references=(),
        framework_template=FrameworkTemplateReference(
            template_id="TURING_RFLP_FRAMEWORK",
            template_version="1.0.0",
        ),
        semantic_reference_versions=(
            SemanticReferenceVersion(
                reference_system_id="TURING_CORE",
                reference_version="1.0.0",
            ),
        ),
        created_at="2026-08-03T15:00:00Z",
        content_fingerprint="1" * 64,
    )

    version = ReviewDocumentVersion(
        schema_version="1.0.0",
        project_id="000001",
        review_document_id="RVD-000001",
        review_document_version_id="RVV-000001",
        version_number=1,
        predecessor_version_id=None,
        reopen_reason=None,
        opened_by="reviewer@example.com",
        opened_at="2026-08-03T15:00:00Z",
        version_state="draft",
        head_revision_id="RVR-000001",
        finalized_revision_id=None,
        finalized_at=None,
        finalization_decision_id=None,
        content_fingerprint="2" * 64,
    )

    revision = ReviewRevision(
        schema_version="1.0.0",
        project_id="000001",
        review_document_id="RVD-000001",
        review_document_version_id="RVV-000001",
        review_revision_id="RVR-000001",
        revision_sequence=1,
        predecessor_revision_id=None,
        review_items=(_review_item(),),
        scoped_review_action_ids=("SRA-000001",),
        created_by="reviewer@example.com",
        created_at="2026-08-03T15:00:00Z",
        revision_fingerprint="3" * 64,
    )

    materialized_item = MaterializedReviewItemReference(
        review_item_id="RIT-000001",
        item_content_fingerprint="e" * 64,
    )

    action = ScopedReviewAction(
        schema_version="1.0.0",
        project_id="000001",
        review_document_id="RVD-000001",
        review_document_version_id="RVV-000001",
        scoped_review_action_id="SRA-000001",
        action_scope="filtered_set",
        decision_dimension="framework_assignment",
        selected_values=("02_System/01_Requirements",),
        filter_definition=(
            "proposed_framework=StakeholderRequirements"
        ),
        materialized_items=(materialized_item,),
        created_by="reviewer@example.com",
        created_at="2026-08-03T15:00:00Z",
        rationale=None,
        action_fingerprint="4" * 64,
    )

    issue = ReviewWorkspaceIssue(
        project_id="000001",
        code="example_issue",
        message="Example issue.",
        issue_level="warning",
        path=Path("data/projects/000001/reviews"),
        review_document_id="RVD-000001",
        review_document_version_id="RVV-000001",
        review_revision_id="RVR-000001",
        review_item_id="RIT-000001",
        scoped_review_action_id="SRA-000001",
    )

    scan = ReviewWorkspaceScanResult(
        documents=(document,),
        versions=(version,),
        revisions=(revision,),
        scoped_actions=(action,),
        issues=(issue,),
    )

    return (
        ReviewProperty(name="key", value="value"),
        _proposal(),
        _evidence(),
        _relationship(),
        _selection(),
        _content(),
        _review_item(),
        document,
        version,
        revision,
        materialized_item,
        action,
        issue,
        scan,
    )


def test_review_vocabularies_are_explicit() -> None:
    assert REVIEW_DOCUMENT_VERSION_STATES == {
        "draft",
        "finalized",
    }

    assert REVIEW_ITEM_KINDS == {
        "element",
        "relationship",
        "open_question",
    }

    assert REVIEW_ITEM_SECTIONS == {
        "elements",
        "relationships",
        "open_questions",
    }

    assert REVIEW_PRIMARY_VIEWS == {
        "elements",
        "relationships",
        "open_questions",
        "rejected_content",
    }

    assert REVIEW_ITEM_OUTCOMES == {
        "open",
        "accepted_as_generated",
        "accepted_with_modification",
        "combined",
        "rejected",
        "deferred",
        "out_of_scope",
        "unresolved",
    }

    assert REVIEW_ACTION_SCOPES == {
        "document_default",
        "filtered_set",
        "explicit_selection",
    }

    assert REVIEW_DECISION_DIMENSIONS == {
        "content",
        "classification",
        "framework_assignment",
        "terminology_assignment",
        "source_assignment",
        "relationship_representation",
        "review_outcome",
    }

    assert REVIEW_VALUE_ORIGINS == {
        "agent_proposal",
        "document_default",
        "filtered_set",
        "explicit_selection",
        "item_override",
    }

    assert REVIEW_PROPOSAL_STATES == {
        "available",
        "selected",
        "not_selected_due_to_human_selection",
        "rejected",
    }

    assert REVIEW_ITEM_LINEAGE_OPERATIONS == {
        "original",
        "split",
        "merge",
        "human_created",
        "carried_forward",
    }

    assert RELATIONSHIP_PROFILE_VALIDATION_STATUSES == {
        "not_applicable",
        "unresolved",
        "valid",
        "invalid",
    }

    assert REVIEW_ISSUE_LEVELS == {
        "warning",
        "blocking",
    }


def test_dataclass_field_contracts_are_explicit() -> None:
    expected = {
        ReviewProperty: (
            "name",
            "value",
        ),
        ReviewProposalReference: (
            "artifact_reference",
            "agent_id",
            "persona_id",
            "proposal_id",
            "proposal_content_fingerprint",
            "original_report_locator",
            "review_state",
        ),
        ReviewRelationshipRepresentation: (
            "source_subject_key",
            "target_subject_key",
            "semantic_intent",
            "sysml_v2_construct",
            "construct_properties",
            "target_notation_profile_id",
            "target_notation_profile_version",
            "textual_notation_preview",
            "validation_status",
            "validation_fingerprint",
        ),
        ReviewDocument: (
            "schema_version",
            "project_id",
            "review_document_id",
            "source_id",
            "source_sha256",
            "processing_run_id",
            "attempt_id",
            "primary_review_artifact_reference",
            "supporting_artifact_references",
            "framework_template",
            "semantic_reference_versions",
            "created_at",
            "content_fingerprint",
        ),
        ReviewDocumentVersion: (
            "schema_version",
            "project_id",
            "review_document_id",
            "review_document_version_id",
            "version_number",
            "predecessor_version_id",
            "reopen_reason",
            "opened_by",
            "opened_at",
            "version_state",
            "head_revision_id",
            "finalized_revision_id",
            "finalized_at",
            "finalization_decision_id",
            "content_fingerprint",
        ),
        ReviewRevision: (
            "schema_version",
            "project_id",
            "review_document_id",
            "review_document_version_id",
            "review_revision_id",
            "revision_sequence",
            "predecessor_revision_id",
            "review_items",
            "scoped_review_action_ids",
            "created_by",
            "created_at",
            "revision_fingerprint",
        ),
        ScopedReviewAction: (
            "schema_version",
            "project_id",
            "review_document_id",
            "review_document_version_id",
            "scoped_review_action_id",
            "action_scope",
            "decision_dimension",
            "selected_values",
            "filter_definition",
            "materialized_items",
            "created_by",
            "created_at",
            "rationale",
            "action_fingerprint",
        ),
    }

    for data_type, expected_fields in expected.items():
        assert tuple(
            field.name
            for field in fields(data_type)
        ) == expected_fields


def test_review_workspace_types_are_frozen_and_slotted() -> None:
    for instance in _instances():
        assert not hasattr(instance, "__dict__")

        first_field = fields(instance)[0].name

        with pytest.raises(FrozenInstanceError):
            setattr(instance, first_field, None)


def test_rejected_content_is_a_derived_view() -> None:
    assert "rejected_content" in REVIEW_PRIMARY_VIEWS
    assert "rejected_content" not in REVIEW_ITEM_KINDS
    assert "rejected_content" not in REVIEW_ITEM_SECTIONS


def test_relationship_construct_is_profile_supplied() -> None:
    relationship = _relationship()

    assert relationship.sysml_v2_construct == "dependency"
    assert relationship.target_notation_profile_id
    assert relationship.target_notation_profile_version
    assert relationship.validation_status == "valid"
