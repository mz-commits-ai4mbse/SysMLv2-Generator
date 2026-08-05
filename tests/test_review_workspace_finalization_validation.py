"""Tests for deterministic Review Version finalization validation."""

from __future__ import annotations

from dataclasses import replace

import pytest

from modules.human_review import (
    create_human_review_decision,
)
from modules.human_review.errors import (
    HumanReviewIntegrityError,
)
from modules.review_workspace.errors import (
    ReviewIntegrityError,
    ReviewValidationError,
)
from modules.review_workspace.finalization_validation import (
    assess_review_document_finalization,
    create_review_document_finalization_target,
    validate_review_finalization_assessment,
)
from modules.review_workspace.item_manifest import (
    create_review_item,
)
from modules.review_workspace.revision_manifest import (
    create_review_revision,
)
from modules.review_workspace.types import (
    ReviewItemContent,
    ReviewRelationshipRepresentation,
)
from modules.review_workspace.version_manifest import (
    finalize_review_document_version,
)

from tests.test_review_workspace_repository_mutations import (
    _bundle,
)


TIMESTAMP = "2026-08-05T19:00:00Z"


def _element_item(
    *,
    review_item_id: str = "RIT-000001",
    outcome: str = "accepted_with_modification",
):
    content = ReviewItemContent(
        title="Preserve traceability",
        primary_text=(
            "The system shall preserve source "
            "traceability."
        ),
        description=None,
        information_type="requirement",
        modality="normative",
        epistemic_status="explicit",
        human_rationale=(
            "Confirmed during detailed review."
        ),
        human_confidence="high",
        relationship_representation=None,
    )

    return create_review_item(
        project_id="000001",
        review_document_id="RVD-000001",
        review_document_version_id="RVV-000001",
        review_item_id=review_item_id,
        review_item_kind="element",
        stable_subject_key=(
            "review-subject:"
            f"{review_item_id.lower()}"
        ),
        section="elements",
        lineage_operation="human_created",
        derived_from_review_item_ids=(),
        original_report_locator=(
            "elements/"
            f"{review_item_id.lower()}"
        ),
        proposal_references=(),
        source_evidence_references=(),
        consensus_evidence_references=(),
        current_content=content,
        dimension_selections=(),
        effective_review_outcome=outcome,
    )


def _open_question_item(
    *,
    review_item_id: str = "RIT-000002",
    outcome: str = "deferred",
):
    content = ReviewItemContent(
        title="Clarify source authority",
        primary_text=(
            "Which source is authoritative?"
        ),
        description=None,
        information_type="open_question",
        modality="interrogative",
        epistemic_status="unresolved",
        human_rationale=None,
        human_confidence=None,
        relationship_representation=None,
    )

    return create_review_item(
        project_id="000001",
        review_document_id="RVD-000001",
        review_document_version_id="RVV-000001",
        review_item_id=review_item_id,
        review_item_kind="open_question",
        stable_subject_key=(
            "review-question:"
            f"{review_item_id.lower()}"
        ),
        section="open_questions",
        lineage_operation="human_created",
        derived_from_review_item_ids=(),
        original_report_locator=(
            "open-questions/"
            f"{review_item_id.lower()}"
        ),
        proposal_references=(),
        source_evidence_references=(),
        consensus_evidence_references=(),
        current_content=content,
        dimension_selections=(),
        effective_review_outcome=outcome,
    )


def _relationship_item(
    *,
    review_item_id: str = "RIT-000003",
    outcome: str = "deferred",
):
    relationship = ReviewRelationshipRepresentation(
        source_subject_key="subject:source",
        target_subject_key="subject:target",
        semantic_intent="depends_on",
        sysml_v2_construct=None,
        construct_properties=(),
        target_notation_profile_id=(
            "SYSML_V2_TARGET"
        ),
        target_notation_profile_version="1.0.0",
        textual_notation_preview=None,
        validation_status="unresolved",
        validation_fingerprint=None,
    )

    content = ReviewItemContent(
        title="Source depends on target",
        primary_text=(
            "The source may depend on the target."
        ),
        description=None,
        information_type="relationship",
        modality="descriptive",
        epistemic_status="interpretation",
        human_rationale=None,
        human_confidence=None,
        relationship_representation=relationship,
    )

    return create_review_item(
        project_id="000001",
        review_document_id="RVD-000001",
        review_document_version_id="RVV-000001",
        review_item_id=review_item_id,
        review_item_kind="relationship",
        stable_subject_key=(
            "review-relationship:"
            f"{review_item_id.lower()}"
        ),
        section="relationships",
        lineage_operation="human_created",
        derived_from_review_item_ids=(),
        original_report_locator=(
            "relationships/"
            f"{review_item_id.lower()}"
        ),
        proposal_references=(),
        source_evidence_references=(),
        consensus_evidence_references=(),
        current_content=content,
        dimension_selections=(),
        effective_review_outcome=outcome,
    )


def _revision(
    *items,
    revision_id: str = "RVR-000001",
    revision_sequence: int = 1,
    predecessor_revision_id: str | None = None,
):
    return create_review_revision(
        project_id="000001",
        review_document_id="RVD-000001",
        review_document_version_id="RVV-000001",
        review_revision_id=revision_id,
        revision_sequence=revision_sequence,
        predecessor_revision_id=(
            predecessor_revision_id
        ),
        review_items=tuple(items),
        scoped_review_action_ids=(),
        created_by="moritz",
        timestamp=TIMESTAMP,
    )


def _assessment(
    revision,
    *,
    additional_blocking_issue_codes=(),
    version=None,
):
    document, default_version, _ = _bundle()

    return assess_review_document_finalization(
        document,
        (
            default_version
            if version is None
            else version
        ),
        revision,
        additional_blocking_issue_codes=(
            additional_blocking_issue_codes
        ),
    )


def test_accepted_and_deferred_items_are_eligible() -> None:
    revision = _revision(
        _element_item(),
        _open_question_item(),
    )

    assessment = _assessment(revision)

    assert (
        assessment.eligible_for_finalization
        is True
    )
    assert assessment.blocking_issue_codes == ()
    assert tuple(
        snapshot.review_item_id
        for snapshot in assessment.item_snapshots
    ) == (
        "RIT-000001",
        "RIT-000002",
    )
    assert (
        validate_review_finalization_assessment(
            assessment
        )
        is None
    )


@pytest.mark.parametrize(
    ("outcome", "expected_code"),
    (
        (
            "open",
            "review_item_open:RIT-000001",
        ),
        (
            "unresolved",
            "review_item_unresolved:RIT-000001",
        ),
    ),
)
def test_unresolved_item_state_blocks_finalization(
    outcome: str,
    expected_code: str,
) -> None:
    revision = _revision(
        _element_item(outcome=outcome)
    )

    assessment = _assessment(revision)

    assert (
        assessment.eligible_for_finalization
        is False
    )
    assert expected_code in (
        assessment.blocking_issue_codes
    )


def test_deferred_unresolved_relationship_is_allowed() -> None:
    revision = _revision(
        _relationship_item(outcome="deferred")
    )

    assessment = _assessment(revision)

    assert (
        assessment.eligible_for_finalization
        is True
    )
    assert (
        assessment.item_snapshots[0]
        .relationship_validation_status
        == "unresolved"
    )


def test_unresolved_relationship_outcome_blocks() -> None:
    revision = _revision(
        _relationship_item(
            outcome="unresolved"
        )
    )

    assessment = _assessment(revision)

    assert (
        assessment.blocking_issue_codes
        == (
            "review_item_unresolved:"
            "RIT-000003",
        )
    )


def test_non_head_revision_blocks_finalization() -> None:
    revision = _revision(
        _element_item(),
        revision_id="RVR-000002",
        revision_sequence=2,
        predecessor_revision_id="RVR-000001",
    )

    assessment = _assessment(revision)

    assert (
        "review_revision_not_current_head"
        in assessment.blocking_issue_codes
    )


def test_finalized_version_cannot_be_finalized_again() -> None:
    document, version, _ = _bundle()
    revision = _revision(
        _element_item()
    )

    finalized = finalize_review_document_version(
        version,
        finalized_revision_id="RVR-000001",
        finalization_decision_id="HRD-000001",
        timestamp="2026-08-05T19:10:00Z",
    )

    assessment = assess_review_document_finalization(
        document,
        finalized,
        revision,
    )

    assert (
        assessment.eligible_for_finalization
        is False
    )
    assert (
        "review_version_not_draft"
        in assessment.blocking_issue_codes
    )


def test_additional_blocking_issues_are_bound() -> None:
    revision = _revision(
        _element_item()
    )

    assessment = _assessment(
        revision,
        additional_blocking_issue_codes=(
            "supporting_artifact_unavailable",
            "source_fingerprint_mismatch",
        ),
    )

    assert (
        assessment.blocking_issue_codes
        == (
            "source_fingerprint_mismatch",
            "supporting_artifact_unavailable",
        )
    )
    assert (
        assessment.eligible_for_finalization
        is False
    )


def test_duplicate_additional_issue_is_rejected() -> None:
    revision = _revision(
        _element_item()
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="must be unique",
    ):
        _assessment(
            revision,
            additional_blocking_issue_codes=(
                "source_fingerprint_mismatch",
                "source_fingerprint_mismatch",
            ),
        )


def test_additional_issues_must_be_tuple() -> None:
    revision = _revision(
        _element_item()
    )

    with pytest.raises(
        ReviewValidationError,
        match="must be a tuple",
    ):
        assess_review_document_finalization(
            _bundle()[0],
            _bundle()[1],
            revision,
            additional_blocking_issue_codes=[
                "invalid"
            ],
        )


def test_assessment_is_deterministic() -> None:
    revision = _revision(
        _element_item(),
        _open_question_item(),
    )

    first = _assessment(revision)
    second = _assessment(revision)

    assert first == second


def test_item_change_changes_validation_fingerprint() -> None:
    accepted = _assessment(
        _revision(
            _element_item(
                outcome=(
                    "accepted_with_modification"
                )
            )
        )
    )
    rejected = _assessment(
        _revision(
            _element_item(
                outcome="rejected"
            )
        )
    )

    assert (
        accepted.validation_fingerprint
        != rejected.validation_fingerprint
    )


def test_exact_finalization_target_is_created() -> None:
    assessment = _assessment(
        _revision(
            _element_item()
        )
    )

    target = (
        create_review_document_finalization_target(
            assessment
        )
    )

    assert (
        target.target_type
        == "review_document_finalization"
    )
    assert target.target_id == "RVV-000001"
    assert (
        target.target_content_fingerprint
        == assessment
        .review_document_version_content_fingerprint
    )
    assert (
        target.reference_validation_fingerprint
        == assessment.validation_fingerprint
    )
    assert (
        target.reference_validation_status
        == "valid"
    )


def test_blocked_assessment_creates_invalid_target() -> None:
    assessment = _assessment(
        _revision(
            _element_item(outcome="open")
        )
    )

    target = (
        create_review_document_finalization_target(
            assessment
        )
    )

    assert (
        target.reference_validation_status
        == "invalid"
    )

    with pytest.raises(
        HumanReviewIntegrityError,
        match="must not be confirmed",
    ):
        create_human_review_decision(
            project_id="000001",
            human_review_decision_id=(
                "HRD-000001"
            ),
            target=target,
            review_mode="detailed_review",
            decision="confirm",
            reviewer_identity="moritz",
            rationale=None,
            timestamp=TIMESTAMP,
        )


def test_cross_document_revision_is_rejected() -> None:
    document, version, _ = _bundle()

    foreign_item = create_review_item(
        project_id="000001",
        review_document_id="RVD-000002",
        review_document_version_id="RVV-000001",
        review_item_id="RIT-000001",
        review_item_kind="element",
        stable_subject_key="foreign:subject",
        section="elements",
        lineage_operation="human_created",
        derived_from_review_item_ids=(),
        original_report_locator="elements/foreign",
        proposal_references=(),
        source_evidence_references=(),
        consensus_evidence_references=(),
        current_content=ReviewItemContent(
            title="Foreign item",
            primary_text="Foreign content.",
            description=None,
            information_type="requirement",
            modality="normative",
            epistemic_status="explicit",
            human_rationale=None,
            human_confidence=None,
            relationship_representation=None,
        ),
        dimension_selections=(),
        effective_review_outcome="rejected",
    )

    foreign_revision = create_review_revision(
        project_id="000001",
        review_document_id="RVD-000002",
        review_document_version_id="RVV-000001",
        review_revision_id="RVR-000001",
        revision_sequence=1,
        predecessor_revision_id=None,
        review_items=(foreign_item,),
        scoped_review_action_ids=(),
        created_by="moritz",
        timestamp=TIMESTAMP,
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="selected Review Document",
    ):
        assess_review_document_finalization(
            document,
            version,
            foreign_revision,
        )
