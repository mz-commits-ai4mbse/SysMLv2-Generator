import json

import pytest

from modules.semantic_consolidation.element_clustering import (
    ElementSemanticProposal,
    SemanticEvidenceStatement,
    build_element_semantic_comparator_payload,
    consolidate_element_proposals,
)
from modules.semantic_consolidation.errors import (
    SemanticConsolidationIntegrityError,
    SemanticConsolidationValidationError,
)
from modules.semantic_consolidation.types import SemanticUpstreamArtifactBinding


FP = "a" * 64
UPSTREAM = "agent-output://derivation/run"


def _proposal(
    ref: str,
    *,
    name: str,
    element_type: str = "system",
    persona: str = "persona-a",
    run: int = 1,
    evidence_ref: str = "evidence://statement-1",
) -> ElementSemanticProposal:
    return ElementSemanticProposal(
        proposal_ref=ref,
        candidate_name=name,
        proposed_element_type=element_type,
        concise_description=f"Engineering concept: {name}",
        agent_id="derivation-agent",
        persona_id=persona,
        run_index=run,
        upstream_artifact_ref=UPSTREAM,
        evidence_refs=(evidence_ref,),
    )


def _evidence():
    return (
        SemanticEvidenceStatement(
            evidence_ref="evidence://statement-1",
            statement="The operator works at the microscope workstation.",
        ),
    )


def _upstream(fingerprint: str = FP):
    return (
        SemanticUpstreamArtifactBinding(
            artifact_ref=UPSTREAM,
            artifact_fingerprint=fingerprint,
        ),
    )


def _equivalent_result(*refs: str):
    comparisons = []
    for left, right in zip(refs, refs[1:]):
        comparisons.append(
            {
                "left_proposal_ref": left,
                "right_proposal_ref": right,
                "outcome": "equivalent",
                "rationale": "Same engineering concept despite wording/classification.",
            }
        )
    return {
        "method": "semantic_model",
        "trace_ref": "semantic-comparison://test",
        "groups": [{"member_proposal_refs": list(refs)}],
        "comparisons": comparisons,
    }


def _run(proposals, comparator):
    return consolidate_element_proposals(
        project_id="965294",
        processing_run_id="RUN-000001",
        created_at_utc="2026-08-17T14:00:00Z",
        upstream_artifacts=_upstream(),
        proposals=tuple(proposals),
        evidence=_evidence(),
        comparator=comparator,
    )


def test_comparator_payload_is_compact_and_evidence_is_not_duplicated():
    proposals = (
        _proposal("proposal://a", name="microscope workstation"),
        _proposal(
            "proposal://b",
            name="workstation used by microscope operator",
            persona="persona-b",
        ),
    )
    payload = build_element_semantic_comparator_payload(
        proposals=proposals,
        evidence=_evidence(),
    )
    assert len(payload["proposals"]) == 2
    assert len(payload["evidence_catalog"]) == 1
    assert "agent_id" not in payload["proposals"][0]
    assert "persona_id" not in payload["proposals"][0]
    serialized = json.dumps(payload)
    assert serialized.count("The operator works at the microscope workstation.") == 1


def test_payload_rejects_missing_exact_evidence_reference():
    proposal = _proposal(
        "proposal://a",
        name="microscope workstation",
        evidence_ref="evidence://missing",
    )
    with pytest.raises(
        SemanticConsolidationIntegrityError,
        match="unavailable",
    ):
        build_element_semantic_comparator_payload(
            proposals=(proposal,),
            evidence=_evidence(),
        )


def test_semantically_equivalent_different_wording_merges_to_one_subject():
    proposals = (
        _proposal("proposal://a", name="microscope workstation"),
        _proposal(
            "proposal://b",
            name="workstation used by the microscope operator",
            persona="persona-b",
        ),
    )
    result = _run(
        proposals,
        lambda payload: _equivalent_result("proposal://a", "proposal://b"),
    )
    assert result.degraded_to_singletons is False
    assert len(result.artifact.subjects) == 1
    assert result.artifact.subjects[0].member_proposal_refs == (
        "proposal://a",
        "proposal://b",
    )


def test_element_type_is_not_semantic_subject_identity():
    proposals = (
        _proposal(
            "proposal://a",
            name="separate client application",
            element_type="interface",
        ),
        _proposal(
            "proposal://b",
            name="separate client application",
            element_type="system",
            persona="persona-b",
        ),
    )
    result = _run(
        proposals,
        lambda payload: _equivalent_result("proposal://a", "proposal://b"),
    )
    assert len(result.artifact.subjects) == 1


def test_distinct_engineering_concepts_remain_separate():
    proposals = (
        _proposal("proposal://operator", name="microscope operator", element_type="actor"),
        _proposal("proposal://workstation", name="microscope workstation"),
    )

    def comparator(payload):
        return {
            "method": "semantic_model",
            "trace_ref": "semantic-comparison://distinct",
            "groups": [
                {"member_proposal_refs": ["proposal://operator"]},
                {"member_proposal_refs": ["proposal://workstation"]},
            ],
            "comparisons": [
                {
                    "left_proposal_ref": "proposal://operator",
                    "right_proposal_ref": "proposal://workstation",
                    "outcome": "distinct",
                    "rationale": "Actor and workstation are different engineering concepts.",
                }
            ],
        }

    result = _run(proposals, comparator)
    assert result.degraded_to_singletons is False
    assert len(result.artifact.subjects) == 2
    assert result.artifact.comparisons[0].outcome == "distinct"


def test_uncertain_never_authorizes_merge():
    proposals = (
        _proposal("proposal://a", name="temporary control"),
        _proposal("proposal://b", name="remote microscope control", persona="persona-b"),
    )

    def comparator(payload):
        return {
            "method": "semantic_model",
            "trace_ref": "semantic-comparison://uncertain",
            "groups": [
                {"member_proposal_refs": ["proposal://a"]},
                {"member_proposal_refs": ["proposal://b"]},
            ],
            "comparisons": [
                {
                    "left_proposal_ref": "proposal://a",
                    "right_proposal_ref": "proposal://b",
                    "outcome": "uncertain",
                    "rationale": "Could overlap but evidence is insufficient.",
                }
            ],
        }

    result = _run(proposals, comparator)
    assert result.degraded_to_singletons is False
    assert len(result.artifact.subjects) == 2
    assert result.artifact.comparisons[0].outcome == "uncertain"


def test_uncertain_inside_declared_merge_degrades_to_singletons():
    proposals = (
        _proposal("proposal://a", name="temporary control"),
        _proposal("proposal://b", name="remote microscope control", persona="persona-b"),
    )

    def comparator(payload):
        return {
            "method": "semantic_model",
            "trace_ref": "semantic-comparison://bad-merge",
            "groups": [
                {"member_proposal_refs": ["proposal://a", "proposal://b"]},
            ],
            "comparisons": [
                {
                    "left_proposal_ref": "proposal://a",
                    "right_proposal_ref": "proposal://b",
                    "outcome": "uncertain",
                    "rationale": "Not enough confidence.",
                }
            ],
        }

    result = _run(proposals, comparator)
    assert result.degraded_to_singletons is True
    assert len(result.artifact.subjects) == 2
    assert result.artifact.comparisons == ()


def test_multi_member_merge_requires_explicit_equivalent_connectivity():
    proposals = (
        _proposal("proposal://a", name="client application"),
        _proposal("proposal://b", name="remote client", persona="persona-b"),
        _proposal("proposal://c", name="client software", persona="persona-c"),
    )

    def comparator(payload):
        result = _equivalent_result("proposal://a", "proposal://b")
        result["groups"] = [
            {"member_proposal_refs": ["proposal://a", "proposal://b", "proposal://c"]}
        ]
        return result

    result = _run(proposals, comparator)
    assert result.degraded_to_singletons is True
    assert len(result.artifact.subjects) == 3


def test_transitive_equivalence_connectivity_authorizes_merge():
    proposals = (
        _proposal("proposal://a", name="client application"),
        _proposal("proposal://b", name="remote client", persona="persona-b"),
        _proposal("proposal://c", name="client software", persona="persona-c"),
    )
    result = _run(
        proposals,
        lambda payload: _equivalent_result(
            "proposal://a", "proposal://b", "proposal://c"
        ),
    )
    assert result.degraded_to_singletons is False
    assert len(result.artifact.subjects) == 1


def test_comparator_group_order_and_member_order_are_canonicalized():
    proposals = (
        _proposal("proposal://a", name="operator", element_type="actor"),
        _proposal("proposal://b", name="workstation", persona="persona-b"),
    )

    def comparator(payload):
        return {
            "method": "semantic_model",
            "trace_ref": "semantic-comparison://order",
            "groups": [
                {"member_proposal_refs": ["proposal://b"]},
                {"member_proposal_refs": ["proposal://a"]},
            ],
            "comparisons": [],
        }

    result = _run(proposals, comparator)
    assert result.degraded_to_singletons is False
    assert {s.member_proposal_refs for s in result.artifact.subjects} == {
        ("proposal://a",),
        ("proposal://b",),
    }


def test_missing_proposal_from_comparator_partition_degrades_safely():
    proposals = (
        _proposal("proposal://a", name="operator"),
        _proposal("proposal://b", name="workstation", persona="persona-b"),
    )

    def comparator(payload):
        return {
            "method": "semantic_model",
            "trace_ref": "semantic-comparison://missing",
            "groups": [{"member_proposal_refs": ["proposal://a"]}],
            "comparisons": [],
        }

    result = _run(proposals, comparator)
    assert result.degraded_to_singletons is True
    assert len(result.artifact.subjects) == 2


def test_duplicate_proposal_across_groups_degrades_safely():
    proposals = (
        _proposal("proposal://a", name="operator"),
        _proposal("proposal://b", name="workstation", persona="persona-b"),
    )

    def comparator(payload):
        return {
            "method": "semantic_model",
            "trace_ref": "semantic-comparison://duplicate",
            "groups": [
                {"member_proposal_refs": ["proposal://a"]},
                {"member_proposal_refs": ["proposal://a", "proposal://b"]},
            ],
            "comparisons": [
                {
                    "left_proposal_ref": "proposal://a",
                    "right_proposal_ref": "proposal://b",
                    "outcome": "equivalent",
                    "rationale": "bad overlapping result",
                }
            ],
        }

    result = _run(proposals, comparator)
    assert result.degraded_to_singletons is True


def test_unknown_comparison_reference_degrades_safely():
    proposal = _proposal("proposal://a", name="operator")

    def comparator(payload):
        return {
            "method": "semantic_model",
            "trace_ref": "semantic-comparison://unknown",
            "groups": [{"member_proposal_refs": ["proposal://a"]}],
            "comparisons": [
                {
                    "left_proposal_ref": "proposal://a",
                    "right_proposal_ref": "proposal://unknown",
                    "outcome": "distinct",
                    "rationale": "invalid reference",
                }
            ],
        }

    result = _run((proposal,), comparator)
    assert result.degraded_to_singletons is True


def test_comparator_exception_degrades_to_singletons():
    proposals = (
        _proposal("proposal://a", name="operator"),
        _proposal("proposal://b", name="workstation", persona="persona-b"),
    )

    def comparator(payload):
        raise RuntimeError("semantic provider unavailable")

    result = _run(proposals, comparator)
    assert result.degraded_to_singletons is True
    assert result.warning_codes == (
        "semantic_comparator_unavailable",
    )


def test_missing_comparator_degrades_to_singletons():
    proposals = (
        _proposal("proposal://a", name="operator"),
        _proposal("proposal://b", name="workstation", persona="persona-b"),
    )
    result = _run(proposals, None)
    assert result.degraded_to_singletons is True
    assert len(result.artifact.subjects) == 2


def test_malformed_comparator_result_degrades_to_singletons():
    proposals = (
        _proposal("proposal://a", name="operator"),
        _proposal("proposal://b", name="workstation", persona="persona-b"),
    )
    result = _run(proposals, lambda payload: {"groups": []})
    assert result.degraded_to_singletons is True
    assert result.warning_codes == ("semantic_comparator_invalid",)


def test_exact_upstream_integrity_failure_is_not_hidden_by_fallback():
    proposal = _proposal("proposal://a", name="operator")
    wrong_upstream = (
        SemanticUpstreamArtifactBinding(
            artifact_ref="agent-output://different",
            artifact_fingerprint=FP,
        ),
    )
    with pytest.raises(
        SemanticConsolidationIntegrityError,
        match="unavailable upstream artifact",
    ):
        consolidate_element_proposals(
            project_id="965294",
            processing_run_id="RUN-000001",
            created_at_utc="2026-08-17T14:00:00Z",
            upstream_artifacts=wrong_upstream,
            proposals=(proposal,),
            evidence=_evidence(),
            comparator=None,
        )


def test_exact_input_validation_failure_is_not_hidden_by_fallback():
    invalid = ElementSemanticProposal(
        proposal_ref="proposal://a",
        candidate_name="operator",
        proposed_element_type="actor",
        concise_description="operator",
        agent_id="agent",
        persona_id="persona-a",
        run_index=0,
        upstream_artifact_ref=UPSTREAM,
        evidence_refs=("evidence://statement-1",),
    )
    with pytest.raises(
        SemanticConsolidationValidationError,
        match="run_index",
    ):
        _run((invalid,), None)


def test_same_exact_inputs_and_comparator_result_reconstruct_same_fingerprint():
    proposals = (
        _proposal("proposal://a", name="client application"),
        _proposal("proposal://b", name="remote client", persona="persona-b"),
    )
    comparator = lambda payload: _equivalent_result(
        "proposal://a", "proposal://b"
    )
    first = _run(proposals, comparator)
    second = _run(tuple(reversed(proposals)), comparator)
    assert first.artifact == second.artifact
    assert first.artifact.artifact_fingerprint == second.artifact.artifact_fingerprint
