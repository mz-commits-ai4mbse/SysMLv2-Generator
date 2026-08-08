"""Tests for G6.3a immutable item-level Review editing."""

from __future__ import annotations

from dataclasses import replace

import pytest

from modules.project_processing import (
    ProcessingArtifactReference,
)
from modules.review_workspace.errors import (
    ReviewIntegrityError,
    StaleReviewRevisionError,
)
from modules.review_workspace.item_manifest import (
    create_review_item,
)
from modules.review_workspace.revision_manifest import (
    create_review_revision,
)
from modules.review_workspace.types import (
    ReviewDimensionSelection,
    ReviewItemContent,
    ReviewProposalReference,
)
from modules.review_workspace.workflow_editing import (
    ReviewItemEditRequest,
    create_item_edit_revision,
    proposal_selection_key,
)


def _proposal(
    proposal_id="CAND-001",
    artifact_id="AGENT-001",
):
    artifact = ProcessingArtifactReference(
        artifact_type="agent_outputs",
        artifact_id=artifact_id,
        content_fingerprint="a" * 64,
        repository_relative_path=(
            "data/projects/123456/runs/RUN-000001/"
            f"artifacts/agent_outputs/{artifact_id}.json"
        ),
    )
    return ReviewProposalReference(
        artifact_reference=artifact,
        agent_id="AGENT_001",
        persona_id="systems_engineer",
        proposal_id=proposal_id,
        proposal_content_fingerprint="b" * 64,
        original_report_locator=f"candidate/{proposal_id}",
        review_state="available",
    )


def _content(text="The system shall preserve traceability."):
    return ReviewItemContent(
        title="Preserve traceability",
        primary_text=text,
        description="Source-derived statement.",
        information_type="requirement",
        modality="shall",
        epistemic_status="asserted",
        human_rationale=None,
        human_confidence=None,
        relationship_representation=None,
    )


def _item(*, proposals=None):
    proposals = (
        (_proposal(),)
        if proposals is None
        else tuple(proposals)
    )
    content = _content()
    source_ids = (
        (proposal_selection_key(proposals[0]),)
        if proposals
        else ("IU-000001",)
    )

    return create_review_item(
        project_id="123456",
        review_document_id="RVD-000001",
        review_document_version_id="RVV-000001",
        review_item_id="RIT-000001",
        review_item_kind="element",
        stable_subject_key="preserve-traceability",
        section="elements",
        lineage_operation="original",
        derived_from_review_item_ids=(),
        original_report_locator=(
            "report:requirements/preserve-traceability"
        ),
        proposal_references=proposals,
        source_evidence_references=(),
        consensus_evidence_references=(),
        current_content=content,
        dimension_selections=(
            ReviewDimensionSelection(
                dimension="content",
                selected_values=(content.primary_text,),
                value_origin="agent_proposal",
                source_reference_ids=source_ids,
                rationale="Initial draft.",
                selected_by=None,
                selected_at=None,
            ),
            ReviewDimensionSelection(
                dimension="classification",
                selected_values=(
                    "requirement",
                    "shall",
                    "asserted",
                ),
                value_origin="agent_proposal",
                source_reference_ids=source_ids,
                rationale="Initial draft.",
                selected_by=None,
                selected_at=None,
            ),
        ),
        effective_review_outcome="open",
    )


def _revision(item):
    return create_review_revision(
        project_id="123456",
        review_document_id="RVD-000001",
        review_document_version_id="RVV-000001",
        review_revision_id="RVR-000001",
        revision_sequence=1,
        predecessor_revision_id=None,
        review_items=(item,),
        scoped_review_action_ids=(),
        created_by="Reviewer A",
        timestamp="2026-08-08T08:00:00Z",
    )


def _request(
    item,
    *,
    content=None,
    selected=None,
    outcome="accepted_as_generated",
    rationale=None,
    framework=None,
):
    if selected is None:
        selected = (
            (
                proposal_selection_key(
                    item.proposal_references[0]
                ),
            )
            if item.proposal_references
            else ()
        )

    return ReviewItemEditRequest(
        expected_revision_id="RVR-000001",
        expected_item_content_fingerprint=(
            item.item_content_fingerprint
        ),
        updated_content=(
            item.current_content
            if content is None
            else content
        ),
        selected_proposal_keys=tuple(selected),
        review_outcome=outcome,
        framework_assignment_values=framework,
        rationale=rationale,
    )


def test_accept_generated_creates_successor_revision():
    item = _item()
    original = _revision(item)

    successor = create_item_edit_revision(
        original,
        review_item_id="RIT-000001",
        request=_request(item),
        new_review_revision_id="RVR-000002",
        actor_identity="Reviewer A",
        timestamp="2026-08-08T08:05:00Z",
    )

    assert successor.review_revision_id == "RVR-000002"
    assert successor.revision_sequence == 2
    assert successor.predecessor_revision_id == "RVR-000001"

    assert (
        original.review_items[0].effective_review_outcome
        == "open"
    )
    edited = successor.review_items[0]
    assert (
        edited.effective_review_outcome
        == "accepted_as_generated"
    )
    assert (
        edited.proposal_references[0].review_state
        == "selected"
    )


def test_stale_revision_is_rejected():
    item = _item()
    request = replace(
        _request(item),
        expected_revision_id="RVR-000099",
    )

    with pytest.raises(
        StaleReviewRevisionError,
        match="current Review Revision",
    ):
        create_item_edit_revision(
            _revision(item),
            review_item_id="RIT-000001",
            request=request,
            new_review_revision_id="RVR-000002",
            actor_identity="Reviewer A",
            timestamp="2026-08-08T08:05:00Z",
        )


def test_stale_item_fingerprint_is_rejected():
    item = _item()
    request = replace(
        _request(item),
        expected_item_content_fingerprint="f" * 64,
    )

    with pytest.raises(
        StaleReviewRevisionError,
        match="fingerprint",
    ):
        create_item_edit_revision(
            _revision(item),
            review_item_id="RIT-000001",
            request=request,
            new_review_revision_id="RVR-000002",
            actor_identity="Reviewer A",
            timestamp="2026-08-08T08:05:00Z",
        )


def test_rejection_requires_rationale():
    item = _item()

    with pytest.raises(
        ReviewIntegrityError,
        match="requires a rationale",
    ):
        create_item_edit_revision(
            _revision(item),
            review_item_id="RIT-000001",
            request=_request(
                item,
                selected=(),
                outcome="rejected",
            ),
            new_review_revision_id="RVR-000002",
            actor_identity="Reviewer A",
            timestamp="2026-08-08T08:05:00Z",
        )


def test_rejection_marks_all_proposals_rejected():
    item = _item(
        proposals=(
            _proposal("CAND-001", "AGENT-001"),
            _proposal("CAND-002", "AGENT-002"),
        )
    )

    successor = create_item_edit_revision(
        _revision(item),
        review_item_id="RIT-000001",
        request=_request(
            item,
            selected=(),
            outcome="rejected",
            rationale="Contradicted by source evidence.",
        ),
        new_review_revision_id="RVR-000002",
        actor_identity="Reviewer A",
        timestamp="2026-08-08T08:05:00Z",
    )

    assert {
        proposal.review_state
        for proposal
        in successor.review_items[0].proposal_references
    } == {"rejected"}


def test_human_content_change_becomes_item_override():
    item = _item()
    changed = replace(
        item.current_content,
        primary_text=(
            "The system shall preserve end-to-end traceability."
        ),
        human_rationale="Clarified scope.",
    )

    successor = create_item_edit_revision(
        _revision(item),
        review_item_id="RIT-000001",
        request=_request(
            item,
            content=changed,
            outcome="accepted_with_modification",
            rationale="Clarified scope.",
        ),
        new_review_revision_id="RVR-000002",
        actor_identity="Reviewer A",
        timestamp="2026-08-08T08:05:00Z",
    )

    selection = next(
        selection
        for selection
        in successor.review_items[0].dimension_selections
        if selection.dimension == "content"
    )

    assert selection.value_origin == "item_override"
    assert selection.selected_by == "Reviewer A"
    assert selection.selected_at == "2026-08-08T08:05:00Z"


def test_assignment_override_is_independent_dimension():
    item = _item()

    successor = create_item_edit_revision(
        _revision(item),
        review_item_id="RIT-000001",
        request=_request(
            item,
            outcome="accepted_with_modification",
            framework=("System Requirements",),
        ),
        new_review_revision_id="RVR-000002",
        actor_identity="Reviewer A",
        timestamp="2026-08-08T08:05:00Z",
    )

    selection = next(
        selection
        for selection
        in successor.review_items[0].dimension_selections
        if selection.dimension == "framework_assignment"
    )

    assert selection.selected_values == (
        "System Requirements",
    )
    assert selection.value_origin == "item_override"


def test_evidence_only_item_accepts_human_review_without_proposal():
    item = _item(proposals=())

    successor = create_item_edit_revision(
        _revision(item),
        review_item_id="RIT-000001",
        request=_request(
            item,
            selected=(),
            outcome="accepted_with_modification",
        ),
        new_review_revision_id="RVR-000002",
        actor_identity="Reviewer A",
        timestamp="2026-08-08T08:05:00Z",
    )

    assert (
        successor.review_items[0].effective_review_outcome
        == "accepted_with_modification"
    )


def test_accept_generated_cannot_hide_human_content_change():
    item = _item()
    changed = replace(
        item.current_content,
        primary_text="Human changed statement.",
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="must not contain human-edited content",
    ):
        create_item_edit_revision(
            _revision(item),
            review_item_id="RIT-000001",
            request=_request(
                item,
                content=changed,
            ),
            new_review_revision_id="RVR-000002",
            actor_identity="Reviewer A",
            timestamp="2026-08-08T08:05:00Z",
        )
