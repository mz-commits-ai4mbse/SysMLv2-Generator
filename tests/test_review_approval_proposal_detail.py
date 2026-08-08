"""Tests for exact G6.3b1 Agent proposal reconstruction."""

from __future__ import annotations

from dataclasses import replace

import pytest

from modules.project_processing import ProcessingArtifactReference
from modules.review_workspace.errors import ReviewIntegrityError
from modules.review_workspace.item_manifest import create_review_item
from modules.review_workspace.p9_proposal_adapter import (
    P9ElementProposal,
    P9SourceAssignment,
    P9StructuredProposalSet,
)
from modules.review_workspace.proposal_detail import (
    build_review_proposal_details,
)
from modules.review_workspace.types import (
    ReviewDimensionSelection,
    ReviewItemContent,
    ReviewProposalReference,
)


def _reference(
    proposal_id,
    *,
    artifact_id,
    fingerprint,
):
    return ReviewProposalReference(
        artifact_reference=ProcessingArtifactReference(
            artifact_type="agent_outputs",
            artifact_id=artifact_id,
            content_fingerprint="a" * 64,
            repository_relative_path=(
                "data/projects/123456/runs/RUN-000001/"
                f"artifacts/agent_outputs/{artifact_id}.json"
            ),
        ),
        agent_id=artifact_id,
        persona_id="systems_engineer",
        proposal_id=proposal_id,
        proposal_content_fingerprint=fingerprint,
        original_report_locator=(
            "report:recognized_elements/"
            "requirement:preserve-traceability"
        ),
        review_state="available",
    )


def _proposal(
    proposal_id,
    *,
    artifact_id,
    text,
    fingerprint,
):
    reference = _reference(
        proposal_id,
        artifact_id=artifact_id,
        fingerprint=fingerprint,
    )
    return P9ElementProposal(
        stable_subject_key="requirement:preserve-traceability",
        candidate_id=proposal_id,
        element_type="requirement",
        candidate_name="Preserve Traceability",
        description=text,
        source_basis=("SI-001",),
        source_assignments=(
            P9SourceAssignment(
                source_info_id="SI-001",
                source_statement="Traceability is required.",
                assignment_type="states_requirement",
                confidence="high",
            ),
        ),
        confidence="high",
        generation_readiness="ready",
        missing_information=(),
        rationale_summary="Supported by source evidence.",
        proposal_reference=reference,
    )


def _item(proposals):
    content = ReviewItemContent(
        title="Preserve Traceability",
        primary_text=proposals[0].description,
        description=proposals[0].rationale_summary,
        information_type="requirement",
        modality=None,
        epistemic_status=None,
        human_rationale=None,
        human_confidence=None,
        relationship_representation=None,
    )
    return create_review_item(
        project_id="123456",
        review_document_id="RVD-000001",
        review_document_version_id="RVV-000001",
        review_item_id="RIT-000001",
        review_item_kind="element",
        stable_subject_key="requirement:preserve-traceability",
        section="elements",
        lineage_operation="original",
        derived_from_review_item_ids=(),
        original_report_locator="report:recognized_elements/x",
        proposal_references=tuple(
            proposal.proposal_reference
            for proposal in proposals
        ),
        source_evidence_references=(),
        consensus_evidence_references=(),
        current_content=content,
        dimension_selections=(
            ReviewDimensionSelection(
                dimension="content",
                selected_values=(content.primary_text,),
                value_origin="agent_proposal",
                source_reference_ids=(
                    f"{proposals[0].proposal_reference.artifact_reference.artifact_id}:"
                    f"{proposals[0].candidate_id}",
                ),
                rationale="Initial draft.",
                selected_by=None,
                selected_at=None,
            ),
        ),
        effective_review_outcome="open",
    )


def test_proposal_details_expose_full_structured_agent_content():
    proposals = (
        _proposal(
            "CAND-001",
            artifact_id="AGENT-001",
            text="The system shall preserve traceability.",
            fingerprint="b" * 64,
        ),
        _proposal(
            "CAND-002",
            artifact_id="AGENT-002",
            text="The system shall preserve end-to-end traceability.",
            fingerprint="c" * 64,
        ),
    )
    proposal_set = P9StructuredProposalSet(
        project_id="123456",
        source_id="SRC-000001",
        processing_run_id="RUN-000001",
        attempt_id="ATT-000001",
        element_proposals=proposals,
        relationship_proposals=(),
    )

    details = build_review_proposal_details(
        _item(proposals),
        proposal_set,
    )

    assert len(details) == 2
    assert details[1].proposal_key == "AGENT-002:CAND-002"
    assert (
        details[1].proposed_primary_text
        == "The system shall preserve end-to-end traceability."
    )
    assert details[1].confidence == "high"
    assert details[1].generation_readiness == "ready"
    assert details[1].supporting_evidence == ("SI-001",)
    assert details[1].missing_evidence == ()
    assert (
        details[1].source_assignments[0].assignment_type
        == "states_requirement"
    )
    assert details[1].framework_assignment_values == ()


def test_proposal_detail_rejects_reference_fingerprint_mismatch():
    proposal = _proposal(
        "CAND-001",
        artifact_id="AGENT-001",
        text="The system shall preserve traceability.",
        fingerprint="b" * 64,
    )
    item = _item((proposal,))
    changed_reference = replace(
        item.proposal_references[0],
        proposal_content_fingerprint="f" * 64,
    )
    item = replace(
        item,
        proposal_references=(changed_reference,),
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="identity differs",
    ):
        build_review_proposal_details(
            item,
            P9StructuredProposalSet(
                project_id="123456",
                source_id="SRC-000001",
                processing_run_id="RUN-000001",
                attempt_id="ATT-000001",
                element_proposals=(proposal,),
                relationship_proposals=(),
            ),
        )
