"""Focused tests for BLK-001 Human-Review admissibility."""

import pytest

from modules.project_processing.types import (
    ProcessingArtifactReference,
)
from modules.review_workspace.errors import (
    ReviewIntegrityError,
)
from modules.review_workspace.p9_review_admissibility_adapter import (
    _adapt_elements_for_review,
    _adapt_relationships_for_review,
)


REFERENCE = ProcessingArtifactReference(
    artifact_type="agent_outputs",
    artifact_id="ART_TEST_DERIVATION",
    content_fingerprint="0" * 64,
    repository_relative_path=(
        "data/projects/123456/runs/RUN-000001/artifacts/"
        "agent_outputs/agentic_ingestion/ATTEMPT-000001/"
        "03_derivation_assessment/test.json"
    ),
)


def _candidate(
    candidate_id,
    name,
    element_type="actor",
    assignment_type="names_element",
):
    return {
        "candidate_id": candidate_id,
        "element_type": element_type,
        "candidate_name": name,
        "description": f"Source-supported candidate {name}.",
        "source_basis": ["SRC_INFO_001"],
        "assigned_source_information": [
            {
                "source_info_id": "SRC_INFO_001",
                "source_statement": f"The source names {name}.",
                "assignment_type": assignment_type,
                "confidence": "high",
            }
        ],
        "confidence": "high",
        "generation_readiness": "ready",
        "missing_information": [],
        "rationale_summary": "Explicit source evidence.",
    }


def _link(
    source,
    target,
    *,
    link_id="LINK_001",
    link_type="works at",
):
    return {
        "link_id": link_id,
        "source_element_candidate": source,
        "link_type": link_type,
        "target_element_candidate": target,
        "source_basis": ["SRC_INFO_002"],
        "source_statement": (
            f"{source} {link_type} {target}."
        ),
        "confidence": "high",
        "rationale_summary": "Explicit source-supported relationship.",
    }


def test_unknown_element_type_becomes_other_plus_open_question():
    elements, questions = _adapt_elements_for_review(
        [
            _candidate(
                "ELEM_001",
                "microscope workstation",
                element_type="physical_element",
            )
        ],
        reference=REFERENCE,
        agent_id="AGENT_TEST",
        persona_id="PERSONA_TEST",
    )

    assert len(elements) == 1
    assert elements[0].element_type == "other"
    assert elements[0].raw_element_type == "physical_element"

    assert len(questions) == 1
    question = questions[0]
    assert question.issue_code == "unsupported_element_type"
    assert question.raw_value == "physical_element"
    assert question.normalized_value == "other"
    assert "Which engineering classification" in question.review_question


def test_unknown_assignment_type_becomes_unclear_plus_open_question():
    elements, questions = _adapt_elements_for_review(
        [
            _candidate(
                "ELEM_001",
                "control constraint",
                element_type="constraint",
                assignment_type="describes_constraint",
            )
        ],
        reference=REFERENCE,
        agent_id="AGENT_TEST",
        persona_id="PERSONA_TEST",
    )

    assert len(elements) == 1
    assert (
        elements[0].source_assignments[0].assignment_type
        == "unclear_assignment"
    )
    assert len(questions) == 1
    assert questions[0].issue_code == "unsupported_assignment_type"
    assert questions[0].raw_value == "describes_constraint"
    assert questions[0].normalized_value == "unclear_assignment"


def test_dangling_relationship_becomes_open_question_without_fake_relation():
    elements, element_questions = _adapt_elements_for_review(
        [_candidate("ELEM_001", "microscope operator")],
        reference=REFERENCE,
        agent_id="AGENT_TEST",
        persona_id="PERSONA_TEST",
    )
    assert element_questions == ()

    relationships, questions = _adapt_relationships_for_review(
        [
            _link(
                "ELEM_001",
                "microscope workstation",
            )
        ],
        reference=REFERENCE,
        agent_id="AGENT_TEST",
        persona_id="PERSONA_TEST",
        element_proposals=elements,
    )

    assert relationships == ()
    assert len(questions) == 1
    question = questions[0]
    assert question.issue_code == "unresolved_relationship_endpoint"
    assert "microscope workstation" in question.raw_value
    assert "Human Review" in question.review_question
    assert question.source_statement


def test_resolvable_relationship_remains_normal_relationship_proposal():
    elements, questions = _adapt_elements_for_review(
        [
            _candidate("ELEM_001", "microscope operator"),
            _candidate(
                "ELEM_002",
                "microscope workstation",
                element_type="system",
            ),
        ],
        reference=REFERENCE,
        agent_id="AGENT_TEST",
        persona_id="PERSONA_TEST",
    )
    assert questions == ()

    relationships, relationship_questions = (
        _adapt_relationships_for_review(
            [_link("ELEM_001", "ELEM_002")],
            reference=REFERENCE,
            agent_id="AGENT_TEST",
            persona_id="PERSONA_TEST",
            element_proposals=elements,
        )
    )

    assert len(relationships) == 1
    assert relationship_questions == ()
    assert relationships[0].source_element_candidate == "ELEM_001"
    assert relationships[0].target_element_candidate == "ELEM_002"


def test_duplicate_relationship_ids_remain_hard_integrity_failure():
    elements, _ = _adapt_elements_for_review(
        [
            _candidate("ELEM_001", "operator"),
            _candidate("ELEM_002", "workstation", element_type="system"),
        ],
        reference=REFERENCE,
        agent_id="AGENT_TEST",
        persona_id="PERSONA_TEST",
    )

    with pytest.raises(ReviewIntegrityError):
        _adapt_relationships_for_review(
            [
                _link("ELEM_001", "ELEM_002", link_id="LINK_001"),
                _link("ELEM_001", "ELEM_002", link_id="LINK_001"),
            ],
            reference=REFERENCE,
            agent_id="AGENT_TEST",
            persona_id="PERSONA_TEST",
            element_proposals=elements,
        )
