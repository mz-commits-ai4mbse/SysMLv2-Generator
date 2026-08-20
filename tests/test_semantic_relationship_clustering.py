"""Tests for authority-safe relationship semantic clustering."""

from modules.semantic_consolidation.element_clustering import (
    SemanticEvidenceStatement,
)
from modules.semantic_consolidation.relationship_clustering import (
    RelationshipSemanticProposal,
    build_relationship_semantic_comparator_payload,
    consolidate_relationship_proposals,
)
from modules.semantic_consolidation.types import (
    SemanticUpstreamArtifactBinding,
)


def _proposal(
    ref: str,
    *,
    persona: str,
    run: int,
    relationship_type: str,
    source_subject: str = "semantic:element:source",
    target_subject: str = "semantic:element:target",
) -> RelationshipSemanticProposal:
    return RelationshipSemanticProposal(
        proposal_ref=ref,
        source_element_proposal_ref=f"{ref}:source",
        source_semantic_subject_id=source_subject,
        proposed_relationship_type=relationship_type,
        target_element_proposal_ref=f"{ref}:target",
        target_semantic_subject_id=target_subject,
        semantic_statement="The operator observes the live microscope image.",
        agent_id=f"agent-{persona}",
        persona_id=persona,
        run_index=run,
        upstream_artifact_ref=f"artifact-{persona}-{run}",
        evidence_refs=(f"evidence-{ref}",),
    )


def _evidence(*proposals: RelationshipSemanticProposal):
    return tuple(
        SemanticEvidenceStatement(
            evidence_ref=proposal.evidence_refs[0],
            statement=proposal.semantic_statement,
        )
        for proposal in sorted(
            proposals,
            key=lambda item: item.evidence_refs[0],
        )
    )


def _upstream(*proposals: RelationshipSemanticProposal):
    refs = sorted(
        {proposal.upstream_artifact_ref for proposal in proposals}
    )
    return tuple(
        SemanticUpstreamArtifactBinding(
            artifact_ref=ref,
            artifact_fingerprint=("a" * 64),
        )
        for ref in refs
    )


def test_payload_keeps_endpoint_subjects_and_classification_separate():
    first = _proposal(
        "rel-1",
        persona="A",
        run=1,
        relationship_type="observes",
    )
    payload = build_relationship_semantic_comparator_payload(
        proposals=(first,),
        evidence=_evidence(first),
    )

    proposal = payload["proposals"][0]
    assert proposal["source_semantic_subject_id"] == (
        "semantic:element:source"
    )
    assert proposal["target_semantic_subject_id"] == (
        "semantic:element:target"
    )
    assert proposal["proposed_relationship_type"] == "observes"
    assert payload["authority_constraints"][
        "may_select_relationship_classification"
    ] is False


def test_equivalent_wording_and_type_variants_can_share_one_subject():
    first = _proposal(
        "rel-1",
        persona="A",
        run=1,
        relationship_type="observes",
    )
    second = _proposal(
        "rel-2",
        persona="B",
        run=1,
        relationship_type="views",
    )

    def comparator(_payload):
        return {
            "method": "semantic_model",
            "trace_ref": "trace:1",
            "groups": [
                {"member_proposal_refs": ["rel-1", "rel-2"]}
            ],
            "comparisons": [
                {
                    "left_proposal_ref": "rel-1",
                    "right_proposal_ref": "rel-2",
                    "outcome": "equivalent",
                    "rationale": "same directed engineering relation",
                }
            ],
        }

    result = consolidate_relationship_proposals(
        project_id="123456",
        processing_run_id="RUN-000001",
        created_at_utc="2026-08-18T00:00:00Z",
        upstream_artifacts=_upstream(first, second),
        proposals=(first, second),
        evidence=_evidence(first, second),
        comparator=comparator,
    )

    assert result.degraded_to_singletons is False
    assert len(result.artifact.subjects) == 1
    assert result.artifact.subjects[0].member_proposal_refs == (
        "rel-1",
        "rel-2",
    )


def test_different_semantic_endpoints_reject_merge_and_degrade_safely():
    first = _proposal(
        "rel-1",
        persona="A",
        run=1,
        relationship_type="observes",
    )
    second = _proposal(
        "rel-2",
        persona="B",
        run=1,
        relationship_type="observes",
        target_subject="semantic:element:other-target",
    )

    def comparator(_payload):
        return {
            "method": "semantic_model",
            "trace_ref": "trace:bad",
            "groups": [
                {"member_proposal_refs": ["rel-1", "rel-2"]}
            ],
            "comparisons": [
                {
                    "left_proposal_ref": "rel-1",
                    "right_proposal_ref": "rel-2",
                    "outcome": "equivalent",
                    "rationale": "incorrect merge suggestion",
                }
            ],
        }

    result = consolidate_relationship_proposals(
        project_id="123456",
        processing_run_id="RUN-000001",
        created_at_utc="2026-08-18T00:00:00Z",
        upstream_artifacts=_upstream(first, second),
        proposals=(first, second),
        evidence=_evidence(first, second),
        comparator=comparator,
    )

    assert result.degraded_to_singletons is True
    assert result.warning_codes == (
        "relationship_semantic_comparator_invalid",
    )
    assert len(result.artifact.subjects) == 2


def test_unavailable_comparator_degrades_to_singletons():
    first = _proposal(
        "rel-1",
        persona="A",
        run=1,
        relationship_type="observes",
    )
    second = _proposal(
        "rel-2",
        persona="B",
        run=1,
        relationship_type="views",
    )

    result = consolidate_relationship_proposals(
        project_id="123456",
        processing_run_id="RUN-000001",
        created_at_utc="2026-08-18T00:00:00Z",
        upstream_artifacts=_upstream(first, second),
        proposals=(first, second),
        evidence=_evidence(first, second),
        comparator=None,
    )

    assert result.degraded_to_singletons is True
    assert len(result.artifact.subjects) == 2
