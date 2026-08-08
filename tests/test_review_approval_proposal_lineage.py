"""Tests for G6.3b1 proposal decisions and split/merge lineage."""

from __future__ import annotations

from dataclasses import replace

import pytest

from modules.project_processing import ProcessingArtifactReference
from modules.review_workspace.errors import ReviewIntegrityError
from modules.review_workspace.item_manifest import create_review_item
from modules.review_workspace.proposal_detail import ReviewProposalDetail
from modules.review_workspace.revision_manifest import create_review_revision
from modules.review_workspace.types import (
    ReviewDimensionSelection,
    ReviewEvidenceReference,
    ReviewItemContent,
    ReviewProposalReference,
)
from modules.review_workspace.workflow_editing import proposal_selection_key
from modules.review_workspace.workflow_lineage import (
    ReviewMergeRequest,
    ReviewProposalActionRequest,
    ReviewSplitChildSpec,
    ReviewSplitRequest,
    create_merge_revision,
    create_proposal_accept_revision,
    create_proposal_reject_revision,
    create_split_revision,
    evidence_selection_key,
)


def _artifact(artifact_id):
    return ProcessingArtifactReference(
        artifact_type="agent_outputs",
        artifact_id=artifact_id,
        content_fingerprint="a" * 64,
        repository_relative_path=(
            "data/projects/123456/runs/RUN-000001/"
            f"artifacts/agent_outputs/{artifact_id}.json"
        ),
    )


def _proposal(proposal_id, artifact_id):
    return ReviewProposalReference(
        artifact_reference=_artifact(artifact_id),
        agent_id=artifact_id,
        persona_id="systems_engineer",
        proposal_id=proposal_id,
        proposal_content_fingerprint=(
            ("b" if proposal_id.endswith("1") else "c") * 64
        ),
        original_report_locator="report:recognized_elements/x",
        review_state="available",
    )


def _evidence(artifact_id, locator):
    return ReviewEvidenceReference(
        artifact_reference=_artifact(artifact_id),
        evidence_role="source_evidence",
        evidence_locator=locator,
        evidence_content_fingerprint="d" * 64,
    )


def _content(text):
    return ReviewItemContent(
        title="Requirement",
        primary_text=text,
        description="Rationale.",
        information_type="requirement",
        modality=None,
        epistemic_status=None,
        human_rationale=None,
        human_confidence=None,
        relationship_representation=None,
    )


def _item(
    item_id,
    subject,
    *,
    proposals,
    evidence,
    text,
):
    content = _content(text)
    return create_review_item(
        project_id="123456",
        review_document_id="RVD-000001",
        review_document_version_id="RVV-000001",
        review_item_id=item_id,
        review_item_kind="element",
        stable_subject_key=subject,
        section="elements",
        lineage_operation="original",
        derived_from_review_item_ids=(),
        original_report_locator=f"report:{subject}",
        proposal_references=tuple(proposals),
        source_evidence_references=tuple(evidence),
        consensus_evidence_references=(),
        current_content=content,
        dimension_selections=(
            ReviewDimensionSelection(
                dimension="content",
                selected_values=(content.primary_text,),
                value_origin="agent_proposal",
                source_reference_ids=tuple(
                    proposal_selection_key(reference)
                    for reference in proposals[:1]
                ) or ("IU-000001",),
                rationale="Initial draft.",
                selected_by=None,
                selected_at=None,
            ),
        ),
        effective_review_outcome="open",
    )


def _revision(items):
    return create_review_revision(
        project_id="123456",
        review_document_id="RVD-000001",
        review_document_version_id="RVV-000001",
        review_revision_id="RVR-000001",
        revision_sequence=1,
        predecessor_revision_id=None,
        review_items=tuple(items),
        scoped_review_action_ids=(),
        created_by="Reviewer A",
        timestamp="2026-08-08T08:00:00Z",
    )


def _detail(item, proposal, text):
    return ReviewProposalDetail(
        review_item_id=item.review_item_id,
        stable_subject_key=item.stable_subject_key,
        proposal_key=proposal_selection_key(proposal),
        proposal_kind="element",
        agent_id=proposal.agent_id,
        persona_id=proposal.persona_id,
        proposal_id=proposal.proposal_id,
        review_state=proposal.review_state,
        proposed_title="Requirement",
        proposed_primary_text=text,
        proposed_description="Supported.",
        proposed_information_type="requirement",
        framework_assignment_values=(),
        source_assignments=(),
        rationale="Supported.",
        confidence="high",
        generation_readiness="ready",
        supporting_evidence=("SI-001",),
        missing_evidence=(),
        artifact_id=proposal.artifact_reference.artifact_id,
        artifact_content_fingerprint=(
            proposal.artifact_reference.content_fingerprint
        ),
        proposal_content_fingerprint=(
            proposal.proposal_content_fingerprint
        ),
    )


def test_accept_second_proposal_selects_exact_variant():
    p1 = _proposal("CAND-001", "AGENT-001")
    p2 = _proposal("CAND-002", "AGENT-002")
    item = _item(
        "RIT-000001",
        "requirement:traceability",
        proposals=(p1, p2),
        evidence=(),
        text="First proposal.",
    )

    result = create_proposal_accept_revision(
        _revision((item,)),
        review_item_id=item.review_item_id,
        detail=_detail(
            item,
            p2,
            "Second exact proposal.",
        ),
        request=ReviewProposalActionRequest(
            expected_revision_id="RVR-000001",
            expected_item_content_fingerprint=(
                item.item_content_fingerprint
            ),
            proposal_key=proposal_selection_key(p2),
        ),
        new_review_revision_id="RVR-000002",
        actor_identity="Reviewer A",
        timestamp="2026-08-08T08:05:00Z",
    )

    edited = result.review_items[0]
    assert (
        edited.current_content.primary_text
        == "Second exact proposal."
    )
    assert (
        edited.effective_review_outcome
        == "accepted_as_generated"
    )
    states = {
        proposal.proposal_id: proposal.review_state
        for proposal in edited.proposal_references
    }
    assert states == {
        "CAND-001": "not_selected_due_to_human_selection",
        "CAND-002": "selected",
    }


def test_reject_one_proposal_keeps_item_independent_and_records_rationale():
    p1 = _proposal("CAND-001", "AGENT-001")
    p2 = _proposal("CAND-002", "AGENT-002")
    item = _item(
        "RIT-000001",
        "requirement:traceability",
        proposals=(p1, p2),
        evidence=(),
        text="First proposal.",
    )

    result = create_proposal_reject_revision(
        _revision((item,)),
        review_item_id=item.review_item_id,
        request=ReviewProposalActionRequest(
            expected_revision_id="RVR-000001",
            expected_item_content_fingerprint=(
                item.item_content_fingerprint
            ),
            proposal_key=proposal_selection_key(p1),
            rationale="Unsupported interpretation.",
        ),
        new_review_revision_id="RVR-000002",
        actor_identity="Reviewer A",
        timestamp="2026-08-08T08:05:00Z",
    )

    edited = result.review_items[0]
    assert edited.effective_review_outcome == "open"
    assert edited.proposal_references[0].review_state == "rejected"
    outcome = next(
        selection
        for selection in edited.dimension_selections
        if selection.dimension == "review_outcome"
    )
    assert outcome.rationale == "Unsupported interpretation."


def test_split_replaces_parent_with_children_and_exact_reference_partition():
    p1 = _proposal("CAND-001", "AGENT-001")
    p2 = _proposal("CAND-002", "AGENT-002")
    e1 = _evidence("EVIDENCE-001", "source/1")
    e2 = _evidence("EVIDENCE-002", "source/2")
    parent = _item(
        "RIT-000001",
        "requirement:combined",
        proposals=(p1, p2),
        evidence=(e1, e2),
        text="Combined statement.",
    )

    request = ReviewSplitRequest(
        expected_revision_id="RVR-000001",
        expected_item_content_fingerprint=(
            parent.item_content_fingerprint
        ),
        children=(
            ReviewSplitChildSpec(
                stable_subject_key="requirement:child-a",
                current_content=_content("Statement A."),
                proposal_keys=(proposal_selection_key(p1),),
                source_evidence_keys=(evidence_selection_key(e1),),
                consensus_evidence_keys=(),
            ),
            ReviewSplitChildSpec(
                stable_subject_key="requirement:child-b",
                current_content=_content("Statement B."),
                proposal_keys=(proposal_selection_key(p2),),
                source_evidence_keys=(evidence_selection_key(e2),),
                consensus_evidence_keys=(),
            ),
        ),
        rationale="Two independent requirements.",
    )

    result = create_split_revision(
        _revision((parent,)),
        review_item_id=parent.review_item_id,
        request=request,
        new_review_item_ids=(
            "RIT-000002",
            "RIT-000003",
        ),
        new_review_revision_id="RVR-000002",
        actor_identity="Reviewer A",
        timestamp="2026-08-08T08:05:00Z",
    )

    assert tuple(
        item.review_item_id
        for item in result.review_items
    ) == (
        "RIT-000002",
        "RIT-000003",
    )
    assert all(
        item.lineage_operation == "split"
        and item.derived_from_review_item_ids
        == ("RIT-000001",)
        and item.effective_review_outcome == "open"
        for item in result.review_items
    )


def test_split_rejects_reference_loss():
    p1 = _proposal("CAND-001", "AGENT-001")
    p2 = _proposal("CAND-002", "AGENT-002")
    parent = _item(
        "RIT-000001",
        "requirement:combined",
        proposals=(p1, p2),
        evidence=(),
        text="Combined statement.",
    )

    request = ReviewSplitRequest(
        expected_revision_id="RVR-000001",
        expected_item_content_fingerprint=(
            parent.item_content_fingerprint
        ),
        children=(
            ReviewSplitChildSpec(
                stable_subject_key="requirement:child-a",
                current_content=_content("A."),
                proposal_keys=(proposal_selection_key(p1),),
                source_evidence_keys=(),
                consensus_evidence_keys=(),
            ),
            ReviewSplitChildSpec(
                stable_subject_key="requirement:child-b",
                current_content=_content("B."),
                proposal_keys=(),
                source_evidence_keys=(),
                consensus_evidence_keys=(),
            ),
        ),
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="exact partition",
    ):
        create_split_revision(
            _revision((parent,)),
            review_item_id=parent.review_item_id,
            request=request,
            new_review_item_ids=(
                "RIT-000002",
                "RIT-000003",
            ),
            new_review_revision_id="RVR-000002",
            actor_identity="Reviewer A",
            timestamp="2026-08-08T08:05:00Z",
        )


def test_merge_preserves_union_of_original_references_and_lineage():
    p1 = _proposal("CAND-001", "AGENT-001")
    p2 = _proposal("CAND-002", "AGENT-002")
    e1 = _evidence("EVIDENCE-001", "source/1")
    e2 = _evidence("EVIDENCE-002", "source/2")
    first = _item(
        "RIT-000001",
        "requirement:first",
        proposals=(p1,),
        evidence=(e1,),
        text="First.",
    )
    second = _item(
        "RIT-000002",
        "requirement:second",
        proposals=(p2,),
        evidence=(e2,),
        text="Second.",
    )

    result = create_merge_revision(
        _revision((first, second)),
        request=ReviewMergeRequest(
            expected_revision_id="RVR-000001",
            expected_item_fingerprints=(
                (
                    first.review_item_id,
                    first.item_content_fingerprint,
                ),
                (
                    second.review_item_id,
                    second.item_content_fingerprint,
                ),
            ),
            stable_subject_key="requirement:merged",
            current_content=_content("Merged statement."),
            rationale="One engineering subject.",
        ),
        new_review_item_id="RIT-000003",
        new_review_revision_id="RVR-000002",
        actor_identity="Reviewer A",
        timestamp="2026-08-08T08:05:00Z",
    )

    assert len(result.review_items) == 1
    merged = result.review_items[0]
    assert merged.review_item_id == "RIT-000003"
    assert merged.lineage_operation == "merge"
    assert merged.derived_from_review_item_ids == (
        "RIT-000001",
        "RIT-000002",
    )
    assert {
        proposal.proposal_id
        for proposal in merged.proposal_references
    } == {
        "CAND-001",
        "CAND-002",
    }
    assert len(merged.source_evidence_references) == 2
    assert merged.effective_review_outcome == "open"
