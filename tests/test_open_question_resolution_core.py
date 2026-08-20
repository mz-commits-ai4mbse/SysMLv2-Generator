"""Focused tests for BLK-001 B.1a/B.1b resolution core."""

import json

import pytest

from modules.project_processing.types import ProcessingArtifactReference
from modules.review_workspace.errors import (
    ReviewIntegrityError,
    StaleReviewRevisionError,
)
from modules.review_workspace.item_manifest import create_review_item
from modules.review_workspace.open_question_resolution import (
    CreateElementFromOpenQuestionRequest,
    ResolveRelationshipEndpointsRequest,
    create_element_from_open_question_revision,
    create_relationship_endpoint_resolution_revision,
)
from modules.review_workspace.p9_proposal_adapter import (
    P9ReviewQuestionProposal,
    create_element_stable_subject_key,
)
from modules.review_workspace.resolution_candidates import (
    project_relationship_resolution_candidates,
)
from modules.review_workspace.revision_manifest import create_review_revision
from modules.review_workspace.types import (
    ReviewDimensionSelection,
    ReviewEvidenceReference,
    ReviewItemContent,
)


PROJECT_ID = "123456"
DOCUMENT_ID = "RVD-000001"
VERSION_ID = "RVV-000001"
REVISION_ID = "RVR-000001"
TIMESTAMP = "2026-08-17T12:00:00Z"

ARTIFACT = ProcessingArtifactReference(
    artifact_type="agent_outputs",
    artifact_id="AGOUT-ATT-000001-0001",
    content_fingerprint="1" * 64,
    repository_relative_path=(
        "data/projects/123456/runs/RUN-000001/artifacts/"
        "agent_outputs/agentic_ingestion/ATT-000001/"
        "03_derivation_assessment/test.json"
    ),
)

EVIDENCE = ReviewEvidenceReference(
    artifact_reference=ARTIFACT,
    evidence_role="agent_source_evidence",
    evidence_locator="output_text:/explicit_source_links/LINK_001",
    evidence_content_fingerprint="2" * 64,
)


def _element(
    review_item_id,
    name,
    element_type,
    *,
    outcome="open",
):
    selections = ()
    if outcome != "open":
        selections = (
            ReviewDimensionSelection(
                dimension="review_outcome",
                selected_values=(outcome,),
                value_origin="item_override",
                source_reference_ids=(),
                rationale="Test outcome.",
                selected_by="MZ",
                selected_at=TIMESTAMP,
            ),
        )
    return create_review_item(
        project_id=PROJECT_ID,
        review_document_id=DOCUMENT_ID,
        review_document_version_id=VERSION_ID,
        review_item_id=review_item_id,
        review_item_kind="element",
        stable_subject_key=create_element_stable_subject_key(
            element_type=element_type,
            candidate_name=name,
        ),
        section="elements",
        lineage_operation="original",
        derived_from_review_item_ids=(),
        original_report_locator=f"test:{review_item_id}",
        proposal_references=(),
        source_evidence_references=(EVIDENCE,),
        consensus_evidence_references=(),
        current_content=ReviewItemContent(
            title=name,
            primary_text=f"Element {name}.",
            description="Source-supported element.",
            information_type=element_type,
            modality=None,
            epistemic_status="proposed",
            human_rationale=None,
            human_confidence=None,
            relationship_representation=None,
        ),
        dimension_selections=selections,
        effective_review_outcome=outcome,
    )


def _question_item():
    return create_review_item(
        project_id=PROJECT_ID,
        review_document_id=DOCUMENT_ID,
        review_document_version_id=VERSION_ID,
        review_item_id="RIT-000003",
        review_item_kind="open_question",
        stable_subject_key="open_question:relationship:test001",
        section="open_questions",
        lineage_operation="original",
        derived_from_review_item_ids=(),
        original_report_locator="test:open_question",
        proposal_references=(),
        source_evidence_references=(EVIDENCE,),
        consensus_evidence_references=(),
        current_content=ReviewItemContent(
            title="Resolve relationship endpoints",
            primary_text="Which element should the endpoint refer to?",
            description="Retained semantic uncertainty.",
            information_type="open_question",
            modality=None,
            epistemic_status="uncertain",
            human_rationale=None,
            human_confidence=None,
            relationship_representation=None,
        ),
        dimension_selections=(),
        effective_review_outcome="open",
    )


def _revision(*items):
    return create_review_revision(
        project_id=PROJECT_ID,
        review_document_id=DOCUMENT_ID,
        review_document_version_id=VERSION_ID,
        review_revision_id=REVISION_ID,
        revision_sequence=1,
        predecessor_revision_id=None,
        review_items=tuple(items),
        scoped_review_action_ids=(),
        created_by="MZ",
        timestamp=TIMESTAMP,
    )


def _question_proposal(
    *,
    source="microscope operator",
    target="microscope workstation",
):
    raw = {
        "link_id": "LINK_001",
        "source_element_candidate": source,
        "link_type": "works at",
        "target_element_candidate": target,
        "source_basis": ["SRC_INFO_003"],
        "source_statement": (
            "The microscope operator works at the microscope workstation."
        ),
        "confidence": "high",
        "rationale_summary": "Explicit relationship.",
    }
    return P9ReviewQuestionProposal(
        stable_subject_key="open_question:relationship:test001",
        question_id="RQ_TEST001",
        issue_code="unresolved_relationship_endpoint",
        title="Resolve relationship endpoints",
        review_question="Which elements should the endpoints refer to?",
        raw_value=f"{source} --works at--> {target}",
        normalized_value="unresolved",
        source_basis=("SRC_INFO_003",),
        source_statement=raw["source_statement"],
        raw_fragment_json=json.dumps(raw),
        artifact_reference=ARTIFACT,
        agent_id="AGENT_001",
        persona_id="PERSONA_001",
        evidence_locator="output_text:/explicit_source_links/LINK_001",
        evidence_content_fingerprint="2" * 64,
        rationale_summary="Retained for Human Review.",
    )


def test_projection_returns_exact_element_cards_only():
    operator = _element("RIT-000001", "microscope operator", "actor")
    workstation = _element(
        "RIT-000002",
        "microscope workstation",
        "system",
    )
    other = _element("RIT-000004", "workstation", "system")

    projection = project_relationship_resolution_candidates(
        _question_proposal(),
        (operator, workstation, other, _question_item()),
    )

    assert projection.semantic_intent == "works at"
    assert [card.title for card in projection.source_candidates] == [
        "microscope operator"
    ]
    assert [card.title for card in projection.target_candidates] == [
        "microscope workstation"
    ]
    assert projection.target_candidates[0].information_type == "system"


def test_projection_does_not_fuzzy_match_endpoint_names():
    operator = _element("RIT-000001", "microscope operator", "actor")

    projection = project_relationship_resolution_candidates(
        _question_proposal(source="operator"),
        (operator, _question_item()),
    )

    assert projection.source_candidates == ()


def test_projection_keeps_alternative_classifications_as_cards():
    system = _element(
        "RIT-000001",
        "microscope workstation",
        "system",
    )
    other = _element(
        "RIT-000002",
        "microscope workstation",
        "other",
    )

    projection = project_relationship_resolution_candidates(
        _question_proposal(source="microscope workstation"),
        (system, other, _question_item()),
    )

    assert {
        card.information_type
        for card in projection.source_candidates
    } == {"system", "other"}


def test_human_can_create_source_supported_element_without_resolving_question():
    question = _question_item()
    revision = _revision(question)

    successor = create_element_from_open_question_revision(
        revision,
        open_question_item_id=question.review_item_id,
        request=CreateElementFromOpenQuestionRequest(
            expected_revision_id=revision.review_revision_id,
            expected_question_fingerprint=question.item_content_fingerprint,
            element_name="microscope workstation",
            element_type="system",
            primary_text="Workstation used by the microscope operator.",
            description="Explicitly named in source evidence.",
            rationale="The source explicitly names the workstation.",
        ),
        new_review_item_id="RIT-000004",
        new_review_revision_id="RVR-000002",
        actor_identity="MZ",
        timestamp="2026-08-17T12:05:00Z",
    )

    created = next(
        item for item in successor.review_items
        if item.review_item_id == "RIT-000004"
    )
    original_question = next(
        item for item in successor.review_items
        if item.review_item_id == question.review_item_id
    )

    assert created.review_item_kind == "element"
    assert created.lineage_operation == "human_created"
    assert created.source_evidence_references == (EVIDENCE,)
    assert created.current_content.title == "microscope workstation"
    assert created.effective_review_outcome == "open"
    assert original_question.effective_review_outcome == "open"


def test_human_endpoint_resolution_materializes_open_relationship_and_closes_question():
    source = _element("RIT-000001", "microscope operator", "actor")
    target = _element(
        "RIT-000002",
        "microscope workstation",
        "system",
    )
    question = _question_item()
    revision = _revision(source, target, question)

    successor = create_relationship_endpoint_resolution_revision(
        revision,
        open_question_item_id=question.review_item_id,
        request=ResolveRelationshipEndpointsRequest(
            expected_revision_id=revision.review_revision_id,
            expected_question_fingerprint=question.item_content_fingerprint,
            source_subject_key=source.stable_subject_key,
            target_subject_key=target.stable_subject_key,
            semantic_intent="works at",
            relationship_title="operator works at workstation",
            relationship_primary_text=(
                "The microscope operator works at the microscope workstation."
            ),
            rationale="Both endpoints are explicit source-supported elements.",
        ),
        new_relationship_review_item_id="RIT-000004",
        new_review_revision_id="RVR-000002",
        actor_identity="MZ",
        timestamp="2026-08-17T12:10:00Z",
    )

    relationship = next(
        item for item in successor.review_items
        if item.review_item_id == "RIT-000004"
    )
    resolved_question = next(
        item for item in successor.review_items
        if item.review_item_id == question.review_item_id
    )

    assert relationship.review_item_kind == "relationship"
    assert relationship.lineage_operation == "human_created"
    assert relationship.effective_review_outcome == "open"
    assert relationship.source_evidence_references == (EVIDENCE,)

    representation = relationship.current_content.relationship_representation
    assert representation is not None
    assert representation.source_subject_key == source.stable_subject_key
    assert representation.target_subject_key == target.stable_subject_key
    assert representation.semantic_intent == "works at"
    assert representation.validation_status == "unresolved"
    assert representation.sysml_v2_construct is None

    assert (
        resolved_question.effective_review_outcome
        == "accepted_with_modification"
    )
    assert (
        resolved_question.current_content.human_rationale
        == "Both endpoints are explicit source-supported elements."
    )
    assert successor.predecessor_revision_id == revision.review_revision_id


def test_resolution_remains_fail_closed_for_stale_question():
    source = _element("RIT-000001", "microscope operator", "actor")
    target = _element(
        "RIT-000002",
        "microscope workstation",
        "system",
    )
    question = _question_item()
    revision = _revision(source, target, question)

    with pytest.raises(StaleReviewRevisionError):
        create_relationship_endpoint_resolution_revision(
            revision,
            open_question_item_id=question.review_item_id,
            request=ResolveRelationshipEndpointsRequest(
                expected_revision_id="RVR-000999",
                expected_question_fingerprint=question.item_content_fingerprint,
                source_subject_key=source.stable_subject_key,
                target_subject_key=target.stable_subject_key,
                semantic_intent="works at",
                relationship_title="operator works at workstation",
                relationship_primary_text="Explicit relationship.",
                rationale="Human resolution.",
            ),
            new_relationship_review_item_id="RIT-000004",
            new_review_revision_id="RVR-000002",
            actor_identity="MZ",
            timestamp="2026-08-17T12:10:00Z",
        )


def test_rejected_element_cannot_be_selected_as_relationship_endpoint():
    source = _element("RIT-000001", "microscope operator", "actor")
    rejected_target = _element(
        "RIT-000002",
        "microscope workstation",
        "system",
        outcome="rejected",
    )
    question = _question_item()
    revision = _revision(source, rejected_target, question)

    with pytest.raises(ReviewIntegrityError):
        create_relationship_endpoint_resolution_revision(
            revision,
            open_question_item_id=question.review_item_id,
            request=ResolveRelationshipEndpointsRequest(
                expected_revision_id=revision.review_revision_id,
                expected_question_fingerprint=question.item_content_fingerprint,
                source_subject_key=source.stable_subject_key,
                target_subject_key=rejected_target.stable_subject_key,
                semantic_intent="works at",
                relationship_title="operator works at workstation",
                relationship_primary_text="Explicit relationship.",
                rationale="Human resolution.",
            ),
            new_relationship_review_item_id="RIT-000004",
            new_review_revision_id="RVR-000002",
            actor_identity="MZ",
            timestamp="2026-08-17T12:10:00Z",
        )
