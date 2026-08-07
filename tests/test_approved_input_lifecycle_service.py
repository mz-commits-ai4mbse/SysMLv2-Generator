"""Tests for G5.6 Approved Input lifecycle services and reconciliation."""

from datetime import datetime, timezone
from pathlib import Path

from modules.approved_input.eligibility import (
    assess_approved_input_promotion_eligibility,
)
from modules.approved_input.lifecycle import (
    derive_approved_input_authority_states,
)
from modules.approved_input.lifecycle_service import (
    ApprovedInputLifecycleService,
)
from modules.approved_input.manifest import create_approved_input_manifest
from modules.approved_input.promotion_plan import (
    create_approved_input_promotion_plan,
)
from modules.approved_input.repository import ApprovedInputRepository
from modules.approved_input.types import ApprovedInputCanonicalContent
from modules.project_workspace import ProjectWorkspace

from tests.test_approved_input_promotion_eligibility import (
    _element_item,
    _inputs,
)


class _HumanReviewRepository:
    def __init__(self, decision) -> None:
        self.decision = decision

    def load_decision(self, project_id, decision_id):
        assert project_id == self.decision.project_id
        assert decision_id == self.decision.human_review_decision_id
        return self.decision


def _clock() -> datetime:
    return datetime(
        2026,
        8,
        7,
        11,
        45,
        tzinfo=timezone.utc,
    )


def _repository(tmp_path: Path) -> ApprovedInputRepository:
    root = tmp_path / "projects"
    ProjectWorkspace(
        root=root,
        id_generator=lambda: "000001",
        clock=_clock,
    ).create_project("Lifecycle Test")
    return ApprovedInputRepository(root=root)


def _promotion_manifest(*items):
    values = _inputs(*items)
    document, artifact_set, _, _, decision = values
    assessment = assess_approved_input_promotion_eligibility(*values)
    plan = create_approved_input_promotion_plan(
        document,
        artifact_set,
        assessment,
        (),
        timestamp="2026-08-07T11:40:00Z",
    )
    manifest = next(
        item.manifest
        for item in plan.items
        if item.manifest is not None
    )
    return artifact_set, decision, manifest


def _changed_predecessor(successor):
    return create_approved_input_manifest(
        project_id=successor.project_id,
        approved_input_id="AIN-000001",
        approved_input_kind=successor.approved_input_kind,
        canonical_content=ApprovedInputCanonicalContent(
            title=successor.canonical_content.title,
            primary_text="Previous reviewed engineering statement.",
            description=successor.canonical_content.description,
            information_type=successor.canonical_content.information_type,
            modality=successor.canonical_content.modality,
            epistemic_status=successor.canonical_content.epistemic_status,
        ),
        selected_classification=successor.selected_classification,
        selected_framework_assignment=(
            successor.selected_framework_assignment
        ),
        selected_terminology_assignment=(
            successor.selected_terminology_assignment
        ),
        selected_source_assignments=successor.selected_source_assignments,
        selected_relationship_representation=(
            successor.selected_relationship_representation
        ),
        stable_subject_key=successor.stable_subject_key,
        review_document_id=successor.review_document_id,
        review_document_version_id="RVV-000002",
        review_revision_id="RVR-000002",
        review_item_id="RIT-000002",
        review_item_kind=successor.review_item_kind,
        review_item_fingerprint="1" * 64,
        finalized_artifact_set_fingerprint="2" * 64,
        finalization_decision_id="HRD-000002",
        finalization_decision_fingerprint="3" * 64,
        finalization_validation_fingerprint="4" * 64,
        source_id=successor.source_id,
        source_sha256=successor.source_sha256,
        processing_run_id=successor.processing_run_id,
        attempt_id=successor.attempt_id,
        primary_artifact_reference=successor.primary_artifact_reference,
        supporting_artifact_references=(
            successor.supporting_artifact_references
        ),
        proposal_references=successor.proposal_references,
        created_at="2026-08-07T11:00:00Z",
    )


def test_invalidate_derives_invalidated_without_mutating_manifest(
    tmp_path,
) -> None:
    _, decision, manifest = _promotion_manifest()
    repository = _repository(tmp_path)
    repository.persist_manifest(manifest)
    before = repository.load_manifest("000001", manifest.approved_input_id)
    service = ApprovedInputLifecycleService(
        root=repository.root,
        clock=_clock,
        approved_input_repository=repository,
        human_review_repository=_HumanReviewRepository(decision),
    )

    event = service.invalidate(
        "000001",
        manifest.approved_input_id,
        reason_code="source_integrity_failure",
        actor_identity="integrity-checker",
    )

    after = repository.load_manifest("000001", manifest.approved_input_id)
    snapshots = derive_approved_input_authority_states(
        repository.list_manifests("000001"),
        repository.list_events("000001"),
    )
    assert before == after
    assert after.authority_state == "active"
    assert event.event_type == "invalidated"
    assert snapshots[0].authority_state == "invalidated"


def test_changed_successor_supersedes_previous_active_input(
    tmp_path,
) -> None:
    artifact_set, decision, current_base = _promotion_manifest()
    current = create_approved_input_manifest(
        project_id=current_base.project_id,
        approved_input_id="AIN-000002",
        approved_input_kind=current_base.approved_input_kind,
        canonical_content=current_base.canonical_content,
        selected_classification=current_base.selected_classification,
        selected_framework_assignment=current_base.selected_framework_assignment,
        selected_terminology_assignment=(
            current_base.selected_terminology_assignment
        ),
        selected_source_assignments=current_base.selected_source_assignments,
        selected_relationship_representation=(
            current_base.selected_relationship_representation
        ),
        stable_subject_key=current_base.stable_subject_key,
        review_document_id=current_base.review_document_id,
        review_document_version_id=current_base.review_document_version_id,
        review_revision_id=current_base.review_revision_id,
        review_item_id=current_base.review_item_id,
        review_item_kind=current_base.review_item_kind,
        review_item_fingerprint=current_base.review_item_fingerprint,
        finalized_artifact_set_fingerprint=(
            current_base.finalized_artifact_set_fingerprint
        ),
        finalization_decision_id=current_base.finalization_decision_id,
        finalization_decision_fingerprint=(
            current_base.finalization_decision_fingerprint
        ),
        finalization_validation_fingerprint=(
            current_base.finalization_validation_fingerprint
        ),
        source_id=current_base.source_id,
        source_sha256=current_base.source_sha256,
        processing_run_id=current_base.processing_run_id,
        attempt_id=current_base.attempt_id,
        primary_artifact_reference=current_base.primary_artifact_reference,
        supporting_artifact_references=(
            current_base.supporting_artifact_references
        ),
        proposal_references=current_base.proposal_references,
        created_at=current_base.created_at,
    )
    predecessor = _changed_predecessor(current)
    repository = _repository(tmp_path)
    repository.persist_manifest(predecessor)
    repository.persist_manifest(current)
    service = ApprovedInputLifecycleService(
        root=repository.root,
        clock=_clock,
        approved_input_repository=repository,
        human_review_repository=_HumanReviewRepository(decision),
    )

    events = service.reconcile_finalized_version(
        artifact_set,
        (current,),
    )

    assert len(events) == 1
    assert events[0].event_type == "superseded"
    assert events[0].approved_input_id == "AIN-000001"
    assert events[0].successor_approved_input_id == "AIN-000002"


def test_rejected_successor_revokes_previous_active_input(tmp_path) -> None:
    previous_artifact_set, _, predecessor = _promotion_manifest()
    del previous_artifact_set
    rejected_item = _element_item(outcome="rejected")
    artifact_set, decision, _ = _promotion_manifest(
        _element_item()
    )
    # Build the rejected finalized authority directly through the common helper.
    values = _inputs(rejected_item)
    rejected_artifact_set = values[1]
    decision = values[4]
    repository = _repository(tmp_path)
    repository.persist_manifest(predecessor)
    service = ApprovedInputLifecycleService(
        root=repository.root,
        clock=_clock,
        approved_input_repository=repository,
        human_review_repository=_HumanReviewRepository(decision),
    )

    events = service.reconcile_finalized_version(
        rejected_artifact_set,
        (),
    )

    assert len(events) == 1
    assert events[0].event_type == "revoked"
    assert events[0].rationale
