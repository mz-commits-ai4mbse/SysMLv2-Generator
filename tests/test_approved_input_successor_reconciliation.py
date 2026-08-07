"""Tests for G5.6 successor retention and replacement planning."""

from modules.approved_input.eligibility import (
    assess_approved_input_promotion_eligibility,
)
from modules.approved_input.manifest import create_approved_input_manifest
from modules.approved_input.promotion_plan import (
    create_approved_input_promotion_plan,
)
from modules.approved_input.types import ApprovedInputCanonicalContent

from tests.test_approved_input_promotion_eligibility import _inputs


TIMESTAMP = "2026-08-07T11:50:00Z"


def _current_authority():
    values = _inputs()
    document, artifact_set, _, _, _ = values
    assessment = assess_approved_input_promotion_eligibility(*values)
    return document, artifact_set, assessment


def _projected_manifest(approved_input_id="AIN-000001"):
    document, artifact_set, assessment = _current_authority()
    plan = create_approved_input_promotion_plan(
        document,
        artifact_set,
        assessment,
        (),
        timestamp=TIMESTAMP,
    )
    current = plan.items[0].manifest
    assert current is not None
    if current.approved_input_id == approved_input_id:
        return current
    return create_approved_input_manifest(
        project_id=current.project_id,
        approved_input_id=approved_input_id,
        approved_input_kind=current.approved_input_kind,
        canonical_content=current.canonical_content,
        selected_classification=current.selected_classification,
        selected_framework_assignment=current.selected_framework_assignment,
        selected_terminology_assignment=(
            current.selected_terminology_assignment
        ),
        selected_source_assignments=current.selected_source_assignments,
        selected_relationship_representation=(
            current.selected_relationship_representation
        ),
        stable_subject_key=current.stable_subject_key,
        review_document_id=current.review_document_id,
        review_document_version_id=current.review_document_version_id,
        review_revision_id=current.review_revision_id,
        review_item_id=current.review_item_id,
        review_item_kind=current.review_item_kind,
        review_item_fingerprint=current.review_item_fingerprint,
        finalized_artifact_set_fingerprint=(
            current.finalized_artifact_set_fingerprint
        ),
        finalization_decision_id=current.finalization_decision_id,
        finalization_decision_fingerprint=(
            current.finalization_decision_fingerprint
        ),
        finalization_validation_fingerprint=(
            current.finalization_validation_fingerprint
        ),
        source_id=current.source_id,
        source_sha256=current.source_sha256,
        processing_run_id=current.processing_run_id,
        attempt_id=current.attempt_id,
        primary_artifact_reference=current.primary_artifact_reference,
        supporting_artifact_references=(
            current.supporting_artifact_references
        ),
        proposal_references=current.proposal_references,
        created_at=current.created_at,
    )


def _predecessor(*, changed=False):
    current = _projected_manifest()
    content = current.canonical_content
    if changed:
        content = ApprovedInputCanonicalContent(
            title=content.title,
            primary_text="Older materially different statement.",
            description=content.description,
            information_type=content.information_type,
            modality=content.modality,
            epistemic_status=content.epistemic_status,
        )
    return create_approved_input_manifest(
        project_id=current.project_id,
        approved_input_id="AIN-000001",
        approved_input_kind=current.approved_input_kind,
        canonical_content=content,
        selected_classification=current.selected_classification,
        selected_framework_assignment=current.selected_framework_assignment,
        selected_terminology_assignment=(
            current.selected_terminology_assignment
        ),
        selected_source_assignments=current.selected_source_assignments,
        selected_relationship_representation=(
            current.selected_relationship_representation
        ),
        stable_subject_key=current.stable_subject_key,
        review_document_id=current.review_document_id,
        review_document_version_id="RVV-000002",
        review_revision_id="RVR-000002",
        review_item_id="RIT-000002",
        review_item_kind=current.review_item_kind,
        review_item_fingerprint="1" * 64,
        finalized_artifact_set_fingerprint="2" * 64,
        finalization_decision_id="HRD-000002",
        finalization_decision_fingerprint="3" * 64,
        finalization_validation_fingerprint="4" * 64,
        source_id=current.source_id,
        source_sha256=current.source_sha256,
        processing_run_id=current.processing_run_id,
        attempt_id=current.attempt_id,
        primary_artifact_reference=current.primary_artifact_reference,
        supporting_artifact_references=(
            current.supporting_artifact_references
        ),
        proposal_references=current.proposal_references,
        created_at="2026-08-07T10:00:00Z",
    )


def test_unchanged_successor_retains_existing_active_ain() -> None:
    document, artifact_set, assessment = _current_authority()
    predecessor = _predecessor(changed=False)

    plan = create_approved_input_promotion_plan(
        document,
        artifact_set,
        assessment,
        (predecessor,),
        active_manifests=(predecessor,),
        timestamp=TIMESTAMP,
    )

    assert plan.create_item_ids == ()
    assert plan.reuse_item_ids == ("RIT-000001",)
    assert plan.items[0].approved_input_id == "AIN-000001"
    assert plan.items[0].manifest == predecessor
    assert plan.items[0].reason_codes == (
        "unchanged_successor_subject",
    )


def test_changed_successor_creates_new_ain_for_supersession() -> None:
    document, artifact_set, assessment = _current_authority()
    predecessor = _predecessor(changed=True)

    plan = create_approved_input_promotion_plan(
        document,
        artifact_set,
        assessment,
        (predecessor,),
        active_manifests=(predecessor,),
        timestamp=TIMESTAMP,
    )

    assert plan.create_item_ids == ("RIT-000001",)
    assert plan.items[0].approved_input_id == "AIN-000002"
