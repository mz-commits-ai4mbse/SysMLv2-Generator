"""Tests for deterministic G5.5 Approved Input promotion plans."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, replace

import pytest

from modules.approved_input.eligibility import (
    assess_approved_input_promotion_eligibility,
)
from modules.approved_input.errors import (
    ApprovedInputIntegrityError,
    ApprovedInputPromotionBlockedError,
)
from modules.approved_input.manifest import (
    create_approved_input_manifest,
)
from modules.approved_input.promotion_plan import (
    PROMOTION_PLAN_ACTIONS,
    ApprovedInputPromotionPlan,
    ApprovedInputPromotionPlanItem,
    create_approved_input_promotion_plan,
)
from modules.review_workspace.item_manifest import create_review_item
from modules.review_workspace.types import ReviewDimensionSelection

from tests.test_approved_input_promotion_eligibility import (
    _element_item,
    _inputs,
    _open_question_item,
    _valid_relationship_item,
)


TIMESTAMP = "2026-08-07T10:00:00Z"


def _assessment_inputs(*items, terminal_state="awaiting_review"):
    values = _inputs(*items, terminal_state=terminal_state)
    assessment = assess_approved_input_promotion_eligibility(
        *values
    )
    document, artifact_set, _, _, _ = values
    return document, artifact_set, assessment


def _item_with_dimensions():
    base = _element_item()
    selections = (
        ReviewDimensionSelection(
            dimension="classification",
            selected_values=("System Requirement",),
            value_origin="item_override",
            source_reference_ids=(),
            rationale=None,
            selected_by="moritz",
            selected_at=TIMESTAMP,
        ),
        ReviewDimensionSelection(
            dimension="framework_assignment",
            selected_values=("02_System/01_Requirements",),
            value_origin="item_override",
            source_reference_ids=(),
            rationale=None,
            selected_by="moritz",
            selected_at=TIMESTAMP,
        ),
        ReviewDimensionSelection(
            dimension="terminology_assignment",
            selected_values=("requirement",),
            value_origin="item_override",
            source_reference_ids=(),
            rationale=None,
            selected_by="moritz",
            selected_at=TIMESTAMP,
        ),
        ReviewDimensionSelection(
            dimension="source_assignment",
            selected_values=("SRC-000001", "SRC-000002"),
            value_origin="item_override",
            source_reference_ids=(),
            rationale=None,
            selected_by="moritz",
            selected_at=TIMESTAMP,
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
        original_report_locator=base.original_report_locator,
        proposal_references=base.proposal_references,
        source_evidence_references=(
            base.source_evidence_references
        ),
        consensus_evidence_references=(
            base.consensus_evidence_references
        ),
        current_content=base.current_content,
        dimension_selections=selections,
        effective_review_outcome=base.effective_review_outcome,
    )


def test_plan_types_are_frozen_and_slotted() -> None:
    item = ApprovedInputPromotionPlanItem(
        review_item_id="RIT-000001",
        stable_subject_key="subject",
        action="skip",
        approved_input_id=None,
        manifest=None,
        reason_codes=("not_promotable",),
    )
    plan = ApprovedInputPromotionPlan(
        project_id="000001",
        review_document_id="RVD-000001",
        review_document_version_id="RVV-000001",
        review_revision_id="RVR-000001",
        finalized_artifact_set_fingerprint="a" * 64,
        finalization_decision_fingerprint="b" * 64,
        planned_at=TIMESTAMP,
        items=(item,),
    )

    assert PROMOTION_PLAN_ACTIONS == frozenset(
        {"create", "reuse", "skip"}
    )
    assert item.__dataclass_params__.frozen
    assert item.__slots__
    assert plan.__dataclass_params__.frozen
    assert plan.__slots__

    with pytest.raises(FrozenInstanceError):
        item.action = "create"  # type: ignore[misc]


def test_promotable_element_creates_one_exact_manifest() -> None:
    document, artifact_set, assessment = _assessment_inputs()

    plan = create_approved_input_promotion_plan(
        document,
        artifact_set,
        assessment,
        (),
        timestamp=TIMESTAMP,
    )

    assert plan.create_item_ids == ("RIT-000001",)
    assert plan.reuse_item_ids == ()
    assert plan.skipped_item_ids == ()

    item = plan.items[0]
    assert item.action == "create"
    assert item.approved_input_id == "AIN-000001"
    assert item.manifest is not None
    assert item.manifest.approved_input_kind == "element_statement"
    assert item.manifest.review_item_id == "RIT-000001"
    assert (
        item.manifest.finalized_artifact_set_fingerprint
        == artifact_set.artifact_set_fingerprint
    )


def test_effective_dimension_values_are_materialized() -> None:
    item = _item_with_dimensions()
    document, artifact_set, assessment = _assessment_inputs(item)

    plan = create_approved_input_promotion_plan(
        document,
        artifact_set,
        assessment,
        (),
        timestamp=TIMESTAMP,
    )
    manifest = plan.items[0].manifest

    assert manifest is not None
    assert manifest.selected_classification == "System Requirement"
    assert (
        manifest.selected_framework_assignment
        == "02_System/01_Requirements"
    )
    assert manifest.selected_terminology_assignment == "requirement"
    assert manifest.selected_source_assignments == (
        "SRC-000001",
        "SRC-000002",
    )


def test_r4c_semantic_classification_tuple_is_carried_by_canonical_content() -> None:
    base = _element_item()
    semantic_values = tuple(
        value
        for value in (
            base.current_content.information_type,
            base.current_content.modality,
            base.current_content.epistemic_status,
        )
        if value is not None
    )
    assert len(semantic_values) > 1

    item = create_review_item(
        project_id=base.project_id,
        review_document_id=base.review_document_id,
        review_document_version_id=base.review_document_version_id,
        review_item_id=base.review_item_id,
        review_item_kind=base.review_item_kind,
        stable_subject_key=base.stable_subject_key,
        section=base.section,
        lineage_operation=base.lineage_operation,
        derived_from_review_item_ids=base.derived_from_review_item_ids,
        original_report_locator=base.original_report_locator,
        proposal_references=base.proposal_references,
        source_evidence_references=base.source_evidence_references,
        consensus_evidence_references=base.consensus_evidence_references,
        current_content=base.current_content,
        dimension_selections=(
            ReviewDimensionSelection(
                dimension="classification",
                selected_values=semantic_values,
                value_origin="item_override",
                source_reference_ids=(),
                rationale="R4c semantic Human Review classification.",
                selected_by="moritz",
                selected_at=TIMESTAMP,
            ),
        ),
        effective_review_outcome=base.effective_review_outcome,
    )
    document, artifact_set, assessment = _assessment_inputs(item)

    plan = create_approved_input_promotion_plan(
        document,
        artifact_set,
        assessment,
        (),
        timestamp=TIMESTAMP,
    )
    manifest = plan.items[0].manifest

    assert manifest is not None
    assert manifest.selected_classification is None
    assert (
        manifest.canonical_content.information_type
        == base.current_content.information_type
    )
    assert (
        manifest.canonical_content.modality
        == base.current_content.modality
    )
    assert (
        manifest.canonical_content.epistemic_status
        == base.current_content.epistemic_status
    )


def test_multiple_items_receive_sequential_ids() -> None:
    first = _element_item(review_item_id="RIT-000001")
    second = _element_item(review_item_id="RIT-000002")
    document, artifact_set, assessment = _assessment_inputs(
        first,
        second,
    )

    plan = create_approved_input_promotion_plan(
        document,
        artifact_set,
        assessment,
        (),
        timestamp=TIMESTAMP,
    )

    assert tuple(
        item.approved_input_id for item in plan.items
    ) == (
        "AIN-000001",
        "AIN-000002",
    )


def test_exact_existing_manifest_is_reused_idempotently() -> None:
    document, artifact_set, assessment = _assessment_inputs()
    first = create_approved_input_promotion_plan(
        document,
        artifact_set,
        assessment,
        (),
        timestamp=TIMESTAMP,
    )
    manifest = first.items[0].manifest
    assert manifest is not None

    second = create_approved_input_promotion_plan(
        document,
        artifact_set,
        assessment,
        (manifest,),
        timestamp="2026-08-07T10:05:00Z",
    )

    assert second.create_item_ids == ()
    assert second.reuse_item_ids == ("RIT-000001",)
    assert second.items[0].manifest == manifest


def test_idempotence_key_collision_with_different_content_is_rejected() -> None:
    document, artifact_set, assessment = _assessment_inputs()
    first = create_approved_input_promotion_plan(
        document,
        artifact_set,
        assessment,
        (),
        timestamp=TIMESTAMP,
    )
    manifest = first.items[0].manifest
    assert manifest is not None

    conflicting = create_approved_input_manifest(
        project_id=manifest.project_id,
        approved_input_id=manifest.approved_input_id,
        approved_input_kind=manifest.approved_input_kind,
        canonical_content=manifest.canonical_content,
        selected_classification="Conflicting Classification",
        selected_framework_assignment=(
            manifest.selected_framework_assignment
        ),
        selected_terminology_assignment=(
            manifest.selected_terminology_assignment
        ),
        selected_source_assignments=(
            manifest.selected_source_assignments
        ),
        selected_relationship_representation=(
            manifest.selected_relationship_representation
        ),
        stable_subject_key=manifest.stable_subject_key,
        review_document_id=manifest.review_document_id,
        review_document_version_id=(
            manifest.review_document_version_id
        ),
        review_revision_id=manifest.review_revision_id,
        review_item_id=manifest.review_item_id,
        review_item_kind=manifest.review_item_kind,
        review_item_fingerprint=manifest.review_item_fingerprint,
        finalized_artifact_set_fingerprint=(
            manifest.finalized_artifact_set_fingerprint
        ),
        finalization_decision_id=manifest.finalization_decision_id,
        finalization_decision_fingerprint=(
            manifest.finalization_decision_fingerprint
        ),
        finalization_validation_fingerprint=(
            manifest.finalization_validation_fingerprint
        ),
        source_id=manifest.source_id,
        source_sha256=manifest.source_sha256,
        processing_run_id=manifest.processing_run_id,
        attempt_id=manifest.attempt_id,
        primary_artifact_reference=(
            manifest.primary_artifact_reference
        ),
        supporting_artifact_references=(
            manifest.supporting_artifact_references
        ),
        proposal_references=manifest.proposal_references,
        created_at=manifest.created_at,
    )

    with pytest.raises(
        ApprovedInputIntegrityError,
        match="idempotence key",
    ):
        create_approved_input_promotion_plan(
            document,
            artifact_set,
            assessment,
            (conflicting,),
            timestamp=TIMESTAMP,
        )


def test_nonpromotable_open_question_is_explicitly_skipped() -> None:
    question = _open_question_item(
        outcome="accepted_with_modification"
    )
    document, artifact_set, assessment = _assessment_inputs(question)

    plan = create_approved_input_promotion_plan(
        document,
        artifact_set,
        assessment,
        (),
        timestamp=TIMESTAMP,
    )

    assert plan.create_item_ids == ()
    assert plan.skipped_item_ids == ("RIT-000002",)
    assert plan.items[0].action == "skip"
    assert (
        "open_question_conversion_not_supported"
        in plan.items[0].reason_codes
    )


def test_valid_relationship_is_materialized_exactly() -> None:
    relationship_item = _valid_relationship_item()
    document, artifact_set, assessment = _assessment_inputs(
        relationship_item
    )

    plan = create_approved_input_promotion_plan(
        document,
        artifact_set,
        assessment,
        (),
        timestamp=TIMESTAMP,
    )
    manifest = plan.items[0].manifest

    assert manifest is not None
    assert manifest.approved_input_kind == "relationship_statement"
    relationship = manifest.selected_relationship_representation
    assert relationship is not None
    assert relationship.sysml_v2_construct == "dependency"
    assert relationship.profile_validation_status == "valid"


def test_blocked_assessment_cannot_create_plan() -> None:
    document, artifact_set, assessment = _assessment_inputs(
        terminal_state="blocked"
    )

    assert assessment.eligible_for_promotion is False

    with pytest.raises(ApprovedInputPromotionBlockedError):
        create_approved_input_promotion_plan(
            document,
            artifact_set,
            assessment,
            (),
            timestamp=TIMESTAMP,
        )


def test_stale_assessment_binding_is_rejected() -> None:
    document, artifact_set, assessment = _assessment_inputs()
    stale = replace(
        assessment,
        finalized_artifact_set_fingerprint="f" * 64,
    )

    with pytest.raises(
        ApprovedInputIntegrityError,
        match="exact finalized Review authority",
    ):
        create_approved_input_promotion_plan(
            document,
            artifact_set,
            stale,
            (),
            timestamp=TIMESTAMP,
        )
