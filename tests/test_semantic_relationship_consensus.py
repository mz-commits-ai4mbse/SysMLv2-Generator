"""Tests for Persona-aware relationship semantic consensus."""

from modules.semantic_consolidation.element_clustering import (
    SemanticEvidenceStatement,
)
from modules.semantic_consolidation.relationship_clustering import (
    RelationshipSemanticProposal,
    consolidate_relationship_proposals,
)
from modules.semantic_consolidation.relationship_consensus import (
    project_relationship_persona_consensus,
)
from modules.semantic_consolidation.types import (
    SemanticUpstreamArtifactBinding,
)


def _proposal(ref, persona, run, relationship_type):
    return RelationshipSemanticProposal(
        proposal_ref=ref,
        source_element_proposal_ref=f"{ref}:source",
        source_semantic_subject_id="semantic:element:source",
        proposed_relationship_type=relationship_type,
        target_element_proposal_ref=f"{ref}:target",
        target_semantic_subject_id="semantic:element:target",
        semantic_statement="The operator observes the live image.",
        agent_id=f"agent-{persona}",
        persona_id=persona,
        run_index=run,
        upstream_artifact_ref=f"artifact-{persona}-{run}",
        evidence_refs=(f"evidence-{ref}",),
    )


def test_persona_counts_once_and_run_classification_variance_is_visible():
    proposals = (
        _proposal("r-a1", "A", 1, "observes"),
        _proposal("r-a2", "A", 2, "views"),
        _proposal("r-b1", "B", 1, "observes"),
    )
    evidence = tuple(
        SemanticEvidenceStatement(
            evidence_ref=item.evidence_refs[0],
            statement=item.semantic_statement,
        )
        for item in proposals
    )
    upstream = tuple(
        SemanticUpstreamArtifactBinding(
            artifact_ref=ref,
            artifact_fingerprint=("b" * 64),
        )
        for ref in sorted(
            {item.upstream_artifact_ref for item in proposals}
        )
    )

    def comparator(_payload):
        return {
            "method": "semantic_model",
            "trace_ref": "trace:consensus",
            "groups": [
                {
                    "member_proposal_refs": [
                        "r-a1",
                        "r-a2",
                        "r-b1",
                    ]
                }
            ],
            "comparisons": [
                {
                    "left_proposal_ref": "r-a1",
                    "right_proposal_ref": "r-a2",
                    "outcome": "equivalent",
                    "rationale": "same relation",
                },
                {
                    "left_proposal_ref": "r-a1",
                    "right_proposal_ref": "r-b1",
                    "outcome": "equivalent",
                    "rationale": "same relation",
                },
            ],
        }

    artifact = consolidate_relationship_proposals(
        project_id="123456",
        processing_run_id="RUN-000001",
        created_at_utc="2026-08-18T00:00:00Z",
        upstream_artifacts=upstream,
        proposals=proposals,
        evidence=evidence,
        comparator=comparator,
    ).artifact

    consensus = project_relationship_persona_consensus(
        artifact=artifact,
        proposals=proposals,
        expected_persona_ids=("A", "B"),
    )[0]

    assert consensus.recognition_count == 2
    assert consensus.recognized_persona_ids == ("A", "B")
    assert consensus.full_recognition is True
    assert consensus.intra_persona_instability is True
    assert consensus.unanimous_stable_classification is None

    by_persona = {
        item.persona_id: item
        for item in consensus.perspectives
    }
    assert by_persona["A"].run_indexes == (1, 2)
    assert by_persona["A"].classification_options == (
        "observes",
        "views",
    )
    assert by_persona["A"].intra_persona_instability is True
    assert by_persona["B"].stable_classification == "observes"
    assert consensus.human_approval is False
