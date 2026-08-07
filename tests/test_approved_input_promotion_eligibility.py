"""Tests for deterministic Approved Input promotion eligibility."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, replace

import pytest

from modules.approved_input.eligibility import (
    PROMOTABLE_REVIEW_ITEM_OUTCOMES,
    PROMOTION_ALLOWED_RUN_STATES,
    ApprovedInputPromotionEligibilityAssessment,
    ApprovedInputPromotionItemAssessment,
    assess_approved_input_promotion_eligibility,
)
from modules.approved_input.errors import (
    ApprovedInputValidationError,
)
from modules.human_review import (
    create_human_review_decision,
)
from modules.project_processing import (
    create_processing_event,
    create_processing_run_history,
    create_processing_run_manifest,
    create_semantic_reference_version,
)
from modules.project_sources.manifest import (
    create_source_manifest,
    update_source_role_manifest,
)
from modules.review_workspace.document_manifest import (
    create_review_document,
)
from modules.review_workspace.effective_decisions_manifest import (
    create_effective_review_decision_set,
)
from modules.review_workspace.finalization_authorization import (
    authorize_review_document_finalization,
)
from modules.review_workspace.finalization_validation import (
    assess_review_document_finalization,
)
from modules.review_workspace.finalized_artifact_set import (
    create_finalized_review_artifact_set,
)
from modules.review_workspace.item_manifest import create_review_item
from modules.review_workspace.reviewed_document_manifest import (
    create_finalized_reviewed_document,
)
from modules.review_workspace.reviewed_report_renderer import (
    create_rendered_reviewed_report,
)
from modules.review_workspace.types import (
    ReviewItemContent,
    ReviewRelationshipRepresentation,
)

from tests.test_review_workspace_finalization_authorization import (
    FINALIZATION_TIMESTAMP,
    _decision,
)
from tests.test_review_workspace_finalization_validation import (
    _element_item,
    _open_question_item,
    _revision,
)
from tests.test_review_workspace_repository_mutations import _bundle


PROJECT_ID = "000001"
SOURCE_ID = "SRC-000001"
RUN_ID = "RUN-000001"
ATTEMPT_ID = "ATT-000001"
SOURCE_SHA256 = "a" * 64

SEMANTIC_REFERENCE_VERSIONS = (
    create_semantic_reference_version(
        reference_system_id="BFO_2020",
        reference_version="1.0.0",
    ),
)


def _finalized_evidence(*items):
    base_document, version, _ = _bundle()

    document = create_review_document(
        project_id=base_document.project_id,
        review_document_id=(
            base_document.review_document_id
        ),
        source_id=base_document.source_id,
        source_sha256=base_document.source_sha256,
        processing_run_id=(
            base_document.processing_run_id
        ),
        attempt_id=base_document.attempt_id,
        primary_review_artifact_reference=(
            base_document
            .primary_review_artifact_reference
        ),
        supporting_artifact_references=(
            base_document
            .supporting_artifact_references
        ),
        framework_template=(
            base_document.framework_template
        ),
        semantic_reference_versions=(
            SEMANTIC_REFERENCE_VERSIONS
        ),
        timestamp=base_document.created_at,
    )
    revision = _revision(
        *(
            items
            if items
            else (_element_item(),)
        )
    )
    assessment = assess_review_document_finalization(
        document,
        version,
        revision,
    )
    decision = _decision(assessment)
    authorized = authorize_review_document_finalization(
        version,
        revision,
        assessment,
        decision,
        timestamp=FINALIZATION_TIMESTAMP,
    )
    reviewed_document = create_finalized_reviewed_document(
        document,
        authorized.finalized_version,
        revision,
        authorized.authorization,
    )
    effective_decisions = create_effective_review_decision_set(
        reviewed_document,
        revision,
    )
    reviewed_report = create_rendered_reviewed_report(
        reviewed_document,
        effective_decisions,
    )
    artifact_set = create_finalized_review_artifact_set(
        reviewed_document,
        effective_decisions,
        reviewed_report,
    )

    return document, artifact_set, decision


def _source_manifest():
    return create_source_manifest(
        PROJECT_ID,
        SOURCE_ID,
        "engineering_source",
        "source.md",
        size_bytes=128,
        sha256=SOURCE_SHA256,
        timestamp="2026-08-05T18:00:00Z",
    )


def _processing_history(
    primary_reference,
    *,
    terminal_state: str = "awaiting_review",
):
    manifest = create_processing_run_manifest(
        project_id=PROJECT_ID,
        processing_run_id=RUN_ID,
        source_id=SOURCE_ID,
        source_sha256=SOURCE_SHA256,
        source_role_snapshot="engineering_source",
        workflow_profile="engineering_source_processing",
        configuration_fingerprint="c" * 64,
        framework_template_id="TURING_RFLP_FRAMEWORK",
        framework_template_version="1.0.0",
        semantic_reference_versions=(
            SEMANTIC_REFERENCE_VERSIONS
        ),
        timestamp="2026-08-05T18:00:00Z",
    )
    created = create_processing_event(
        project_id=PROJECT_ID,
        processing_run_id=RUN_ID,
        event_id="EVT-000001",
        event_sequence=1,
        previous_state=None,
        next_state="created",
        processing_stage=None,
        event_type="run_created",
        attempt_id=None,
        reason_code="run_created",
        artifact_references=(),
        timestamp="2026-08-05T18:00:01Z",
        previous_event_fingerprint=None,
    )
    started = create_processing_event(
        project_id=PROJECT_ID,
        processing_run_id=RUN_ID,
        event_id="EVT-000002",
        event_sequence=2,
        previous_state="created",
        next_state="running",
        processing_stage="agentic_ingestion",
        event_type="stage_started",
        attempt_id=ATTEMPT_ID,
        reason_code="agentic_ingestion_started",
        artifact_references=(),
        timestamp="2026-08-05T18:00:02Z",
        previous_event_fingerprint=created.event_fingerprint,
    )
    published = create_processing_event(
        project_id=PROJECT_ID,
        processing_run_id=RUN_ID,
        event_id="EVT-000003",
        event_sequence=3,
        previous_state="running",
        next_state="running",
        processing_stage="agentic_ingestion",
        event_type="artifact_published",
        attempt_id=ATTEMPT_ID,
        reason_code="agentic_ingestion_artifacts_published",
        artifact_references=(primary_reference,),
        timestamp="2026-08-05T18:00:03Z",
        previous_event_fingerprint=started.event_fingerprint,
    )
    requested = create_processing_event(
        project_id=PROJECT_ID,
        processing_run_id=RUN_ID,
        event_id="EVT-000004",
        event_sequence=4,
        previous_state="running",
        next_state="awaiting_review",
        processing_stage="agentic_ingestion",
        event_type="review_requested",
        attempt_id=ATTEMPT_ID,
        reason_code="agentic_ingestion_review_requested",
        artifact_references=(),
        timestamp="2026-08-05T18:00:04Z",
        previous_event_fingerprint=published.event_fingerprint,
    )
    events = [created, started, published, requested]

    if terminal_state == "completed":
        resolved = create_processing_event(
            project_id=PROJECT_ID,
            processing_run_id=RUN_ID,
            event_id="EVT-000005",
            event_sequence=5,
            previous_state="awaiting_review",
            next_state="completed",
            processing_stage="agentic_ingestion",
            event_type="review_resolved",
            attempt_id=ATTEMPT_ID,
            reason_code="human_review_resolved",
            artifact_references=(),
            timestamp="2026-08-05T18:00:05Z",
            previous_event_fingerprint=requested.event_fingerprint,
        )
        events.append(resolved)
    elif terminal_state == "blocked":
        blocked = create_processing_event(
            project_id=PROJECT_ID,
            processing_run_id=RUN_ID,
            event_id="EVT-000005",
            event_sequence=5,
            previous_state="awaiting_review",
            next_state="blocked",
            processing_stage="agentic_ingestion",
            event_type="run_blocked",
            attempt_id=ATTEMPT_ID,
            reason_code="blocking_integrity_issue",
            artifact_references=(),
            timestamp="2026-08-05T18:00:05Z",
            previous_event_fingerprint=requested.event_fingerprint,
        )
        events.append(blocked)

    return create_processing_run_history(
        manifest=manifest,
        events=tuple(events),
    )


def _inputs(*items, terminal_state="awaiting_review"):
    document, artifact_set, decision = _finalized_evidence(*items)
    source = _source_manifest()
    history = _processing_history(
        document.primary_review_artifact_reference,
        terminal_state=terminal_state,
    )
    return document, artifact_set, source, history, decision


def _valid_relationship_item():
    relationship = ReviewRelationshipRepresentation(
        source_subject_key="subject:source",
        target_subject_key="subject:target",
        semantic_intent="depends_on",
        sysml_v2_construct="dependency",
        construct_properties=(),
        target_notation_profile_id="SYSML_V2_TARGET",
        target_notation_profile_version="1.0.0",
        textual_notation_preview=(
            "dependency from 'Source' to 'Target';"
        ),
        validation_status="valid",
        validation_fingerprint="d" * 64,
    )
    content = ReviewItemContent(
        title="Source depends on target",
        primary_text="The source depends on the target.",
        description=None,
        information_type="relationship",
        modality="descriptive",
        epistemic_status="reviewed",
        human_rationale="Validated during detailed review.",
        human_confidence="high",
        relationship_representation=relationship,
    )

    return create_review_item(
        project_id=PROJECT_ID,
        review_document_id="RVD-000001",
        review_document_version_id="RVV-000001",
        review_item_id="RIT-000003",
        review_item_kind="relationship",
        stable_subject_key="review-relationship:rit-000003",
        section="relationships",
        lineage_operation="human_created",
        derived_from_review_item_ids=(),
        original_report_locator="relationships/rit-000003",
        proposal_references=(),
        source_evidence_references=(),
        consensus_evidence_references=(),
        current_content=content,
        dimension_selections=(),
        effective_review_outcome="accepted_with_modification",
    )


def test_assessment_types_are_frozen_and_slotted() -> None:
    item = ApprovedInputPromotionItemAssessment(
        review_item_id="RIT-000001",
        stable_subject_key="subject",
        review_item_kind="element",
        effective_review_outcome="accepted_as_generated",
        review_item_fingerprint="a" * 64,
        approved_input_kind="element_statement",
        eligible_for_promotion=True,
        reason_codes=(),
    )
    assessment = ApprovedInputPromotionEligibilityAssessment(
        project_id=PROJECT_ID,
        review_document_id="RVD-000001",
        review_document_version_id="RVV-000001",
        review_revision_id="RVR-000001",
        finalized_artifact_set_fingerprint="b" * 64,
        finalization_decision_id="HRD-000001",
        finalization_decision_fingerprint="c" * 64,
        finalization_validation_fingerprint="d" * 64,
        item_assessments=(item,),
        blocking_issue_codes=(),
        eligible_for_promotion=True,
    )

    assert item.__dataclass_params__.frozen
    assert item.__slots__
    assert assessment.__dataclass_params__.frozen
    assert assessment.__slots__
    assert assessment.promotable_item_ids == ("RIT-000001",)

    with pytest.raises(FrozenInstanceError):
        item.review_item_id = "RIT-000002"


def test_promotion_vocabularies_are_explicit() -> None:
    assert PROMOTABLE_REVIEW_ITEM_OUTCOMES == frozenset(
        {
            "accepted_as_generated",
            "accepted_with_modification",
            "combined",
        }
    )
    assert PROMOTION_ALLOWED_RUN_STATES == frozenset(
        {"awaiting_review", "completed"}
    )


def test_accepted_element_is_promotable() -> None:
    assessment = assess_approved_input_promotion_eligibility(
        *_inputs()
    )

    assert assessment.eligible_for_promotion is True
    assert assessment.blocking_issue_codes == ()
    assert assessment.promotable_item_ids == ("RIT-000001",)

    item = assessment.item_assessments[0]
    assert item.approved_input_kind == "element_statement"
    assert item.reason_codes == ()


def test_completed_processing_run_remains_promotable() -> None:
    assessment = assess_approved_input_promotion_eligibility(
        *_inputs(terminal_state="completed")
    )

    assert assessment.eligible_for_promotion is True


@pytest.mark.parametrize(
    "outcome",
    ("rejected", "deferred", "out_of_scope"),
)
def test_nonaccepted_element_is_skipped_without_blocking_document(
    outcome: str,
) -> None:
    assessment = assess_approved_input_promotion_eligibility(
        *_inputs(_element_item(outcome=outcome))
    )

    assert assessment.eligible_for_promotion is True
    assert assessment.promotable_item_ids == ()
    assert assessment.item_assessments[0].reason_codes == (
        f"review_outcome_not_promotable:{outcome}",
    )


def test_open_question_never_promotes_under_g5_4_contract() -> None:
    assessment = assess_approved_input_promotion_eligibility(
        *_inputs(
            _open_question_item(
                outcome="accepted_with_modification"
            )
        )
    )

    assert assessment.eligible_for_promotion is True
    assert assessment.promotable_item_ids == ()
    assert assessment.item_assessments[0].approved_input_kind is None
    assert assessment.item_assessments[0].reason_codes == (
        "open_question_conversion_not_supported",
    )


def test_profile_valid_accepted_relationship_is_promotable() -> None:
    assessment = assess_approved_input_promotion_eligibility(
        *_inputs(_valid_relationship_item())
    )

    assert assessment.eligible_for_promotion is True
    item = assessment.item_assessments[0]
    assert item.eligible_for_promotion is True
    assert item.approved_input_kind == "relationship_statement"


def test_blocked_processing_run_blocks_promotion() -> None:
    assessment = assess_approved_input_promotion_eligibility(
        *_inputs(terminal_state="blocked")
    )

    assert assessment.eligible_for_promotion is False
    assert "processing_run_not_promotable:blocked" in (
        assessment.blocking_issue_codes
    )


def test_changed_source_role_blocks_promotion() -> None:
    document, artifact_set, source, history, decision = _inputs()
    source = update_source_role_manifest(
        source,
        "context_only",
        timestamp="2026-08-05T18:10:00Z",
    )

    assessment = assess_approved_input_promotion_eligibility(
        document,
        artifact_set,
        source,
        history,
        decision,
    )

    assert assessment.eligible_for_promotion is False
    assert "source_not_engineering_source" in (
        assessment.blocking_issue_codes
    )


def test_changed_source_fingerprint_blocks_promotion() -> None:
    document, artifact_set, source, history, decision = _inputs()
    source = replace(source, sha256="e" * 64)

    assessment = assess_approved_input_promotion_eligibility(
        document,
        artifact_set,
        source,
        history,
        decision,
    )

    assert assessment.eligible_for_promotion is False
    assert "source_fingerprint_mismatch" in (
        assessment.blocking_issue_codes
    )


def test_stale_or_different_finalization_decision_blocks_promotion() -> None:
    document, artifact_set, source, history, decision = _inputs()
    rejected = create_human_review_decision(
        project_id=decision.project_id,
        human_review_decision_id=(
            decision.human_review_decision_id
        ),
        target=decision.target,
        review_mode="detailed_review",
        decision="reject",
        reviewer_identity=decision.reviewer_identity,
        rationale="Promotion must not continue.",
        timestamp=decision.decided_at,
    )

    assessment = assess_approved_input_promotion_eligibility(
        document,
        artifact_set,
        source,
        history,
        rejected,
    )

    assert assessment.eligible_for_promotion is False
    assert "finalization_decision_not_confirmed" in (
        assessment.blocking_issue_codes
    )
    assert "finalization_decision_fingerprint_mismatch" in (
        assessment.blocking_issue_codes
    )


def test_wrong_input_type_is_rejected() -> None:
    _, artifact_set, source, history, decision = _inputs()

    with pytest.raises(ApprovedInputValidationError):
        assess_approved_input_promotion_eligibility(
            None,
            artifact_set,
            source,
            history,
            decision,
        )
