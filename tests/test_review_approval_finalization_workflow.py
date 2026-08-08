"""Tests for G6.4a finalization preview and artifact orchestration."""

from __future__ import annotations

from dataclasses import replace

import pytest

from modules.human_review import (
    create_human_review_decision,
)
from modules.review_workspace.finalization_workflow import (
    build_finalized_review_artifact_set,
    create_review_finalization_workflow_preview,
)
from modules.review_workspace.finalization_authorization import (
    authorize_review_document_finalization,
)
from modules.review_workspace.finalization_validation import (
    create_review_document_finalization_target,
)
from modules.review_workspace.errors import (
    ReviewIntegrityError,
)
from modules.review_workspace.item_manifest import (
    create_review_item,
)
from modules.review_workspace.types import (
    ReviewRelationshipRepresentation,
)

from tests.test_review_workspace_finalization_validation import (
    _element_item,
    _relationship_item,
    _revision,
)
from tests.test_review_workspace_repository_mutations import (
    _bundle,
)


DECIDED_AT = "2026-08-08T12:00:00Z"
FINALIZED_AT = "2026-08-08T12:05:00Z"


def _inputs(*items):
    document, version, _ = _bundle()
    revision = _revision(*items)
    return document, version, revision


def _valid_accepted_relationship():
    base = _relationship_item(
        outcome="deferred",
    )
    representation = (
        base.current_content
        .relationship_representation
    )
    valid_representation = replace(
        representation,
        sysml_v2_construct="dependency",
        textual_notation_preview=(
            "dependency from 'Source' to 'Target';"
        ),
        validation_status="valid",
        validation_fingerprint="f" * 64,
    )
    content = replace(
        base.current_content,
        relationship_representation=(
            valid_representation
        ),
    )

    return create_review_item(
        project_id=base.project_id,
        review_document_id=base.review_document_id,
        review_document_version_id=(
            base.review_document_version_id
        ),
        review_item_id=base.review_item_id,
        review_item_kind=base.review_item_kind,
        stable_subject_key=base.stable_subject_key,
        section=base.section,
        lineage_operation=base.lineage_operation,
        derived_from_review_item_ids=(
            base.derived_from_review_item_ids
        ),
        original_report_locator=(
            base.original_report_locator
        ),
        proposal_references=base.proposal_references,
        source_evidence_references=(
            base.source_evidence_references
        ),
        consensus_evidence_references=(
            base.consensus_evidence_references
        ),
        current_content=content,
        dimension_selections=(
            base.dimension_selections
        ),
        effective_review_outcome=(
            "accepted_with_modification"
        ),
    )


def _decision(assessment, *, value="confirm", rationale=None):
    target = create_review_document_finalization_target(
        assessment
    )
    return create_human_review_decision(
        project_id=assessment.project_id,
        human_review_decision_id="HRD-000001",
        target=target,
        review_mode="detailed_review",
        decision=value,
        reviewer_identity="Reviewer A",
        rationale=rationale,
        timestamp=DECIDED_AT,
    )


def test_existing_item_contract_blocks_invalid_accepted_relationship():
    with pytest.raises(
        ReviewIntegrityError,
        match="accepted relationship requires a valid",
    ):
        _relationship_item(
            outcome="accepted_with_modification",
        )


def test_deferred_unresolved_relationship_remains_finalizable():
    relationship = _relationship_item(
        outcome="deferred",
    )
    document, version, revision = _inputs(
        relationship
    )

    preview = create_review_finalization_workflow_preview(
        document,
        version,
        revision,
        (),
    )

    assert preview.eligible_for_confirmation is True
    assert preview.blocking_issue_codes == ()


def test_valid_accepted_relationship_is_finalizable():
    relationship = _valid_accepted_relationship()
    document, version, revision = _inputs(
        relationship
    )

    preview = create_review_finalization_workflow_preview(
        document,
        version,
        revision,
        (),
    )

    assert preview.eligible_for_confirmation is True


def test_latest_exact_nonconfirm_decision_blocks_finalization():
    document, version, revision = _inputs(
        _element_item()
    )
    first_preview = create_review_finalization_workflow_preview(
        document,
        version,
        revision,
        (),
    )
    target = create_review_document_finalization_target(
        first_preview.assessment
    )
    confirm = create_human_review_decision(
        project_id="000001",
        human_review_decision_id="HRD-000001",
        target=target,
        review_mode="detailed_review",
        decision="confirm",
        reviewer_identity="Reviewer A",
        rationale=None,
        timestamp="2026-08-08T12:00:00Z",
    )
    request_changes = create_human_review_decision(
        project_id="000001",
        human_review_decision_id="HRD-000002",
        target=target,
        review_mode="detailed_review",
        decision="request_changes",
        reviewer_identity="Reviewer A",
        rationale="Further changes required.",
        timestamp="2026-08-08T12:01:00Z",
    )

    preview = create_review_finalization_workflow_preview(
        document,
        version,
        revision,
        (
            confirm,
            request_changes,
        ),
    )

    assert preview.latest_exact_decision_id == "HRD-000002"
    assert preview.latest_exact_decision == "request_changes"
    assert preview.has_exact_confirmation is False
    assert preview.can_finalize is False


def test_exact_confirmation_enables_finalization():
    document, version, revision = _inputs(
        _element_item()
    )
    preliminary = create_review_finalization_workflow_preview(
        document,
        version,
        revision,
        (),
    )
    decision = _decision(
        preliminary.assessment
    )

    preview = create_review_finalization_workflow_preview(
        document,
        version,
        revision,
        (decision,),
    )

    assert preview.has_exact_confirmation is True
    assert preview.can_finalize is True
    assert (
        preview.exact_confirmation_decision_id
        == "HRD-000001"
    )


def test_builds_exact_three_artifact_set_before_persistence():
    document, version, revision = _inputs(
        _element_item()
    )
    preview = create_review_finalization_workflow_preview(
        document,
        version,
        revision,
        (),
    )
    decision = _decision(
        preview.assessment
    )
    authorized = authorize_review_document_finalization(
        version,
        revision,
        preview.assessment,
        decision,
        timestamp=FINALIZED_AT,
    )

    artifact_set = build_finalized_review_artifact_set(
        document,
        revision,
        authorized,
    )

    assert tuple(
        artifact.filename
        for artifact in artifact_set.artifacts
    ) == (
        "reviewed_document.json",
        "effective_decisions.json",
        "reviewed_report.md",
    )
