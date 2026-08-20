import pytest

from modules.semantic_consolidation.element_clustering import (
    ElementSemanticProposal,
    SemanticEvidenceStatement,
    consolidate_element_proposals,
)
from modules.semantic_consolidation.persona_consensus import (
    project_element_persona_consensus,
)
from modules.semantic_consolidation.errors import SemanticConsolidationIntegrityError
from modules.semantic_consolidation.types import SemanticUpstreamArtifactBinding


FP = "a" * 64
UPSTREAM = "agent-output://derivation/run"
EVIDENCE = (
    SemanticEvidenceStatement(
        evidence_ref="evidence://1",
        statement="The client application is used by the remote expert.",
    ),
)
UPSTREAMS = (
    SemanticUpstreamArtifactBinding(
        artifact_ref=UPSTREAM,
        artifact_fingerprint=FP,
    ),
)
EXPECTED = ("persona-a", "persona-b", "persona-c")


def _proposal(
    ref,
    *,
    persona,
    run,
    classification,
    name="separate client application",
):
    return ElementSemanticProposal(
        proposal_ref=ref,
        candidate_name=name,
        proposed_element_type=classification,
        concise_description="A separate client application for remote collaboration.",
        agent_id="derivation-agent",
        persona_id=persona,
        run_index=run,
        upstream_artifact_ref=UPSTREAM,
        evidence_refs=("evidence://1",),
    )


def _artifact(proposals, groups, comparisons):
    def comparator(payload):
        return {
            "method": "semantic_model",
            "trace_ref": "semantic-comparison://consensus-test",
            "groups": [
                {"member_proposal_refs": list(group)} for group in groups
            ],
            "comparisons": [
                {
                    "left_proposal_ref": left,
                    "right_proposal_ref": right,
                    "outcome": outcome,
                    "rationale": rationale,
                }
                for left, right, outcome, rationale in comparisons
            ],
        }

    result = consolidate_element_proposals(
        project_id="965294",
        processing_run_id="RUN-000001",
        created_at_utc="2026-08-17T14:00:00Z",
        upstream_artifacts=UPSTREAMS,
        proposals=tuple(proposals),
        evidence=EVIDENCE,
        comparator=comparator,
    )
    assert result.degraded_to_singletons is False
    return result.artifact


def _equivalent_chain(refs):
    return [
        (left, right, "equivalent", "same engineering concept")
        for left, right in zip(refs, refs[1:])
    ]


def test_multiple_runs_from_same_persona_count_as_one_recognition():
    proposals = (
        _proposal("proposal://a1", persona="persona-a", run=1, classification="system"),
        _proposal("proposal://a2", persona="persona-a", run=2, classification="system"),
        _proposal("proposal://b1", persona="persona-b", run=1, classification="system"),
    )
    refs = tuple(p.proposal_ref for p in proposals)
    artifact = _artifact(proposals, (refs,), _equivalent_chain(refs))
    consensus = project_element_persona_consensus(
        artifact=artifact,
        proposals=proposals,
        expected_persona_ids=EXPECTED,
    )[0]
    assert consensus.recognition_count == 2
    assert consensus.recognized_persona_ids == ("persona-a", "persona-b")
    perspective_a = next(
        item for item in consensus.perspectives if item.persona_id == "persona-a"
    )
    assert perspective_a.run_indexes == (1, 2)
    assert perspective_a.stable_classification == "system"


def test_missing_persona_recognition_is_partial_not_zero_variance():
    proposals = (
        _proposal("proposal://a", persona="persona-a", run=1, classification="system"),
        _proposal("proposal://b", persona="persona-b", run=1, classification="system"),
    )
    refs = tuple(p.proposal_ref for p in proposals)
    artifact = _artifact(proposals, (refs,), _equivalent_chain(refs))
    consensus = project_element_persona_consensus(
        artifact=artifact,
        proposals=proposals,
        expected_persona_ids=EXPECTED,
    )[0]
    assert consensus.full_recognition is False
    assert consensus.recognition_count == 2
    assert consensus.expected_persona_count == 3


def test_different_classifications_same_subject_are_visible_variance():
    proposals = (
        _proposal("proposal://a", persona="persona-a", run=1, classification="interface"),
        _proposal("proposal://b", persona="persona-b", run=1, classification="system"),
        _proposal("proposal://c", persona="persona-c", run=1, classification="system"),
    )
    refs = tuple(p.proposal_ref for p in proposals)
    artifact = _artifact(proposals, (refs,), _equivalent_chain(refs))
    consensus = project_element_persona_consensus(
        artifact=artifact,
        proposals=proposals,
        expected_persona_ids=EXPECTED,
    )[0]
    assert consensus.full_recognition is True
    assert consensus.classification_variance is True
    support = {
        item.classification: item.persona_ids
        for item in consensus.classification_support
    }
    assert support == {
        "interface": ("persona-a",),
        "system": ("persona-b", "persona-c"),
    }
    assert consensus.unanimous_stable_classification is None


def test_intra_persona_instability_is_not_two_votes():
    proposals = (
        _proposal("proposal://a1", persona="persona-a", run=1, classification="system"),
        _proposal("proposal://a2", persona="persona-a", run=2, classification="interface"),
        _proposal("proposal://b", persona="persona-b", run=1, classification="system"),
        _proposal("proposal://c", persona="persona-c", run=1, classification="system"),
    )
    refs = tuple(p.proposal_ref for p in proposals)
    artifact = _artifact(proposals, (refs,), _equivalent_chain(refs))
    consensus = project_element_persona_consensus(
        artifact=artifact,
        proposals=proposals,
        expected_persona_ids=EXPECTED,
    )[0]
    assert consensus.recognition_count == 3
    assert consensus.intra_persona_instability is True
    perspective_a = next(
        item for item in consensus.perspectives if item.persona_id == "persona-a"
    )
    assert perspective_a.classification_options == ("interface", "system")
    assert perspective_a.stable_classification is None
    support = {
        item.classification: item.persona_ids
        for item in consensus.classification_support
    }
    assert support == {"system": ("persona-b", "persona-c")}
    assert consensus.unanimous_stable_classification is None


def test_full_stable_agreement_is_processing_evidence_not_human_approval():
    proposals = tuple(
        _proposal(
            f"proposal://{persona}",
            persona=persona,
            run=1,
            classification="system",
        )
        for persona in EXPECTED
    )
    refs = tuple(p.proposal_ref for p in proposals)
    artifact = _artifact(proposals, (refs,), _equivalent_chain(refs))
    consensus = project_element_persona_consensus(
        artifact=artifact,
        proposals=proposals,
        expected_persona_ids=EXPECTED,
    )[0]
    assert consensus.full_recognition is True
    assert consensus.classification_variance is False
    assert consensus.intra_persona_instability is False
    assert consensus.unanimous_stable_classification == "system"
    assert consensus.human_approval is False


def test_consensus_rejects_persona_outside_expected_set():
    proposals = (
        _proposal("proposal://x", persona="persona-x", run=1, classification="system"),
    )
    artifact = _artifact(proposals, (("proposal://x",),), ())
    with pytest.raises(
        SemanticConsolidationIntegrityError,
        match="outside expected_persona_ids",
    ):
        project_element_persona_consensus(
            artifact=artifact,
            proposals=proposals,
            expected_persona_ids=EXPECTED,
        )


def test_consensus_rejects_provenance_mismatch_against_artifact():
    proposal = _proposal(
        "proposal://a",
        persona="persona-a",
        run=1,
        classification="system",
    )
    artifact = _artifact((proposal,), (("proposal://a",),), ())
    changed = ElementSemanticProposal(
        proposal_ref=proposal.proposal_ref,
        candidate_name=proposal.candidate_name,
        proposed_element_type=proposal.proposed_element_type,
        concise_description=proposal.concise_description,
        agent_id=proposal.agent_id,
        persona_id=proposal.persona_id,
        run_index=2,
        upstream_artifact_ref=proposal.upstream_artifact_ref,
        evidence_refs=proposal.evidence_refs,
    )
    with pytest.raises(
        SemanticConsolidationIntegrityError,
        match="provenance",
    ):
        project_element_persona_consensus(
            artifact=artifact,
            proposals=(changed,),
            expected_persona_ids=EXPECTED,
        )


def test_consensus_is_deterministic_independent_of_proposal_input_order():
    proposals = (
        _proposal("proposal://a", persona="persona-a", run=1, classification="system"),
        _proposal("proposal://b", persona="persona-b", run=1, classification="system"),
        _proposal("proposal://c", persona="persona-c", run=1, classification="system"),
    )
    refs = tuple(p.proposal_ref for p in proposals)
    artifact = _artifact(proposals, (refs,), _equivalent_chain(refs))
    first = project_element_persona_consensus(
        artifact=artifact,
        proposals=proposals,
        expected_persona_ids=EXPECTED,
    )
    second = project_element_persona_consensus(
        artifact=artifact,
        proposals=tuple(reversed(proposals)),
        expected_persona_ids=EXPECTED,
    )
    assert first == second
