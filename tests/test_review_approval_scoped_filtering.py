"""Tests for G6.3c1 filter facts and materialization."""

from __future__ import annotations

from modules.review_workspace.item_manifest import create_review_item
from modules.review_workspace.proposal_detail import ReviewProposalDetail
from modules.review_workspace.revision_manifest import create_review_revision
from modules.review_workspace.scoped_workflow import (
    ReviewConsensusFilterFact,
    ReviewFilterSpec,
    build_review_item_filter_fact,
    filter_review_items,
    review_filter_definition,
)
from modules.review_workspace.types import (
    ReviewDimensionSelection,
    ReviewItemContent,
)


def _item():
    content = ReviewItemContent(
        title="Requirement",
        primary_text="The system shall preserve traceability.",
        description=None,
        information_type="requirement",
        modality="shall",
        epistemic_status="asserted",
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
        stable_subject_key="requirement:traceability",
        section="elements",
        lineage_operation="original",
        derived_from_review_item_ids=(),
        original_report_locator="report:x",
        proposal_references=(),
        source_evidence_references=(),
        consensus_evidence_references=(),
        current_content=content,
        dimension_selections=(
            ReviewDimensionSelection(
                dimension="framework_assignment",
                selected_values=("System Requirements",),
                value_origin="item_override",
                source_reference_ids=("RIT-000001",),
                rationale="Corrected.",
                selected_by="Reviewer A",
                selected_at="2026-08-08T08:00:00Z",
            ),
        ),
        effective_review_outcome="deferred",
    )


def _detail():
    return ReviewProposalDetail(
        review_item_id="RIT-000001",
        stable_subject_key="requirement:traceability",
        proposal_key="AGENT-001:CAND-001",
        proposal_kind="element",
        agent_id="AGENT-001",
        persona_id="systems_engineer",
        proposal_id="CAND-001",
        review_state="available",
        proposed_title="Requirement",
        proposed_primary_text="Proposal.",
        proposed_description="Rationale.",
        proposed_information_type="requirement",
        framework_assignment_values=("Stakeholder Requirements",),
        source_assignments=(),
        rationale="Rationale.",
        confidence="high",
        generation_readiness="ready",
        supporting_evidence=("SI-001",),
        missing_evidence=(),
        artifact_id="AGENT-001",
        artifact_content_fingerprint="a" * 64,
        proposal_content_fingerprint="b" * 64,
    )


def test_filter_fact_covers_all_required_filter_dimensions():
    item = _item()
    fact = build_review_item_filter_fact(
        item,
        proposal_details=(_detail(),),
        source_id="SRC-000001",
        consensus_facts=(
            ReviewConsensusFilterFact(
                artifact_id="CONS-001",
                evidence_locator="/groups/0",
                evidence_content_fingerprint="c" * 64,
                agreement_level="majority_with_disagreement",
                review_required=True,
            ),
        ),
    )

    assert fact.review_status == "deferred"
    assert fact.review_item_kind == "element"
    assert fact.proposed_classifications == ("requirement",)
    assert set(fact.effective_classifications) == {
        "requirement",
        "shall",
        "asserted",
    }
    assert fact.proposed_framework_assignments == (
        "Stakeholder Requirements",
    )
    assert fact.effective_framework_assignments == (
        "System Requirements",
    )
    assert fact.agent_identities == ()
    assert fact.confidence_levels == ("high",)
    assert fact.consensus_states == (
        "majority_with_disagreement",
    )
    assert fact.agent_disagreement_state == "present"
    assert fact.human_modification_state == "modified"
    assert fact.source_identities == ("SRC-000001",)
    assert fact.evidence_sufficiency_state == "sufficient"
    assert fact.relationship_validation_status == "not_applicable"


def test_filter_is_conjunctive_and_materializes_exact_fingerprint():
    item = _item()
    revision = create_review_revision(
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
    fact = build_review_item_filter_fact(
        item,
        proposal_details=(_detail(),),
        source_id="SRC-000001",
    )
    spec = ReviewFilterSpec(
        review_status=("deferred",),
        effective_framework_assignment=(
            "System Requirements",
        ),
        evidence_sufficiency=("sufficient",),
    )

    selected = filter_review_items(
        revision,
        (fact,),
        spec,
    )

    assert selected[0].review_item_id == "RIT-000001"
    assert (
        selected[0].item_content_fingerprint
        == item.item_content_fingerprint
    )
    assert review_filter_definition(spec) == (
        '{"effective_framework_assignment":["System Requirements"],'
        '"evidence_sufficiency":["sufficient"],'
        '"review_status":["deferred"]}'
    )
