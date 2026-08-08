"""Tests for exact P9 Consensus filter fact extraction."""

from modules.review_workspace.p9_evidence_reference_adapter import (
    load_p9_consensus_evidence_facts,
)

from tests.test_review_workspace_p9_evidence_reference_adapter import (
    _evidence,
    _proposal_set,
    _report,
    _summary,
    _write_consensus,
)


def test_loads_exact_consensus_group_filter_facts(tmp_path):
    root = tmp_path / "repository"
    root.mkdir()
    proposals, agent_refs = _proposal_set()
    report = _report()
    report["groups"][0]["agreement_level"] = (
        "majority_with_disagreement"
    )
    report["groups"][0]["review_required"] = True
    report["summary"] = _summary(
        report["groups"]
    )
    consensus_ref, _ = _write_consensus(
        root,
        report,
    )

    facts = load_p9_consensus_evidence_facts(
        _evidence(agent_refs, (consensus_ref,)),
        proposals,
        repository_root=root,
    )

    assert len(facts) == 2
    assert facts[0].evidence_locator == "/groups/0"
    assert (
        facts[0].agreement_level
        == "majority_with_disagreement"
    )
    assert facts[0].review_required is True
