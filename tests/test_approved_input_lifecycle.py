"""Tests for derived Approved Input lifecycle authority and equivalence."""

from modules.approved_input.event_manifest import create_approved_input_event
from modules.approved_input.lifecycle import (
    active_approved_input_manifests,
    calculate_promotion_equivalence_fingerprint,
    derive_approved_input_authority_states,
)
from modules.approved_input.manifest import create_approved_input_manifest
from modules.approved_input.types import ApprovedInputCanonicalContent

from tests.test_approved_input_repository import _manifest


SHA_A = "a" * 64


def _changed_successor():
    base = _manifest(approved_input_id="AIN-000002")
    return create_approved_input_manifest(
        project_id=base.project_id,
        approved_input_id=base.approved_input_id,
        approved_input_kind=base.approved_input_kind,
        canonical_content=ApprovedInputCanonicalContent(
            title=base.canonical_content.title,
            primary_text="Changed reviewed engineering statement.",
            description=base.canonical_content.description,
            information_type=base.canonical_content.information_type,
            modality=base.canonical_content.modality,
            epistemic_status=base.canonical_content.epistemic_status,
        ),
        selected_classification=base.selected_classification,
        selected_framework_assignment=(
            base.selected_framework_assignment
        ),
        selected_terminology_assignment=(
            base.selected_terminology_assignment
        ),
        selected_source_assignments=base.selected_source_assignments,
        selected_relationship_representation=(
            base.selected_relationship_representation
        ),
        stable_subject_key=base.stable_subject_key,
        review_document_id=base.review_document_id,
        review_document_version_id="RVV-000002",
        review_revision_id="RVR-000002",
        review_item_id="RIT-000002",
        review_item_kind=base.review_item_kind,
        review_item_fingerprint="1" * 64,
        finalized_artifact_set_fingerprint="2" * 64,
        finalization_decision_id="HRD-000002",
        finalization_decision_fingerprint="3" * 64,
        finalization_validation_fingerprint="4" * 64,
        source_id=base.source_id,
        source_sha256=base.source_sha256,
        processing_run_id=base.processing_run_id,
        attempt_id=base.attempt_id,
        primary_artifact_reference=base.primary_artifact_reference,
        supporting_artifact_references=(
            base.supporting_artifact_references
        ),
        proposal_references=base.proposal_references,
        created_at="2026-08-07T11:10:00Z",
    )


def test_equivalence_ignores_review_and_approval_identity() -> None:
    first = _manifest(approved_input_id="AIN-000001")
    second_base = _manifest(approved_input_id="AIN-000002")
    second = create_approved_input_manifest(
        project_id=second_base.project_id,
        approved_input_id=second_base.approved_input_id,
        approved_input_kind=second_base.approved_input_kind,
        canonical_content=second_base.canonical_content,
        selected_classification=second_base.selected_classification,
        selected_framework_assignment=(
            second_base.selected_framework_assignment
        ),
        selected_terminology_assignment=(
            second_base.selected_terminology_assignment
        ),
        selected_source_assignments=(
            second_base.selected_source_assignments
        ),
        selected_relationship_representation=None,
        stable_subject_key=second_base.stable_subject_key,
        review_document_id=second_base.review_document_id,
        review_document_version_id="RVV-000002",
        review_revision_id="RVR-000002",
        review_item_id="RIT-000002",
        review_item_kind=second_base.review_item_kind,
        review_item_fingerprint="1" * 64,
        finalized_artifact_set_fingerprint="2" * 64,
        finalization_decision_id="HRD-000002",
        finalization_decision_fingerprint="3" * 64,
        finalization_validation_fingerprint="4" * 64,
        source_id=second_base.source_id,
        source_sha256=second_base.source_sha256,
        processing_run_id=second_base.processing_run_id,
        attempt_id=second_base.attempt_id,
        primary_artifact_reference=(
            second_base.primary_artifact_reference
        ),
        supporting_artifact_references=(
            second_base.supporting_artifact_references
        ),
        proposal_references=second_base.proposal_references,
        created_at="2026-08-07T11:10:00Z",
    )

    assert (
        calculate_promotion_equivalence_fingerprint(first)
        == calculate_promotion_equivalence_fingerprint(second)
    )


def test_changed_engineering_content_changes_equivalence() -> None:
    first = _manifest(approved_input_id="AIN-000001")
    second = _changed_successor()

    assert (
        calculate_promotion_equivalence_fingerprint(first)
        != calculate_promotion_equivalence_fingerprint(second)
    )


def test_no_events_means_all_manifests_are_active() -> None:
    manifests = (
        _manifest(approved_input_id="AIN-000001"),
        _manifest(approved_input_id="AIN-000002"),
    )

    snapshots = derive_approved_input_authority_states(
        manifests,
        (),
    )

    assert tuple(
        snapshot.authority_state for snapshot in snapshots
    ) == ("active", "active")
    assert active_approved_input_manifests(manifests, ()) == manifests


def test_supersession_derives_terminal_predecessor_state() -> None:
    predecessor = _manifest(approved_input_id="AIN-000001")
    successor = _changed_successor()
    event = create_approved_input_event(
        project_id=predecessor.project_id,
        approved_input_event_id="AIE-000001",
        approved_input_id=predecessor.approved_input_id,
        event_type="superseded",
        reason_code="successor_review_item_changed",
        rationale=None,
        actor_identity="reviewer@example.com",
        successor_approved_input_id=successor.approved_input_id,
        causal_review_document_id=successor.review_document_id,
        causal_review_document_version_id=(
            successor.review_document_version_id
        ),
        causal_review_revision_id=successor.review_revision_id,
        causal_finalization_decision_id=(
            successor.finalization_decision_id
        ),
        causal_finalization_decision_fingerprint=(
            successor.finalization_decision_fingerprint
        ),
        occurred_at="2026-08-07T11:20:00Z",
    )

    snapshots = derive_approved_input_authority_states(
        (predecessor, successor),
        (event,),
    )

    states = {
        snapshot.manifest.approved_input_id: snapshot.authority_state
        for snapshot in snapshots
    }
    assert states == {
        "AIN-000001": "superseded",
        "AIN-000002": "active",
    }
    assert active_approved_input_manifests(
        (predecessor, successor),
        (event,),
    ) == (successor,)
