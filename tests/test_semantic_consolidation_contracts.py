from dataclasses import replace

import pytest

from modules.semantic_consolidation import (
    SemanticComparison,
    SemanticConsolidationIntegrityError,
    SemanticConsolidationValidationError,
    SemanticProposalBinding,
    SemanticSubject,
    SemanticUpstreamArtifactBinding,
    build_semantic_consolidation_artifact,
    semantic_consolidation_artifact_from_dict,
    semantic_consolidation_artifact_to_dict,
    validate_semantic_consolidation_artifact,
)


FP_A = "a" * 64
FP_B = "b" * 64


def _upstream(
    artifact_ref: str = "agent-output://derivation/A/run-1",
    fingerprint: str = FP_A,
) -> SemanticUpstreamArtifactBinding:
    return SemanticUpstreamArtifactBinding(
        artifact_ref=artifact_ref,
        artifact_fingerprint=fingerprint,
    )


def _proposal(
    ref: str,
    *,
    kind: str = "element",
    persona: str = "persona-a",
    run: int = 1,
    upstream: str = "agent-output://derivation/A/run-1",
) -> SemanticProposalBinding:
    return SemanticProposalBinding(
        proposal_ref=ref,
        proposal_kind=kind,
        agent_id="derivation-agent",
        persona_id=persona,
        run_index=run,
        upstream_artifact_ref=upstream,
        evidence_refs=(f"evidence://{ref}",),
    )


def _subject(
    subject_id: str,
    *proposal_refs: str,
    kind: str = "element",
) -> SemanticSubject:
    return SemanticSubject(
        semantic_subject_id=subject_id,
        proposal_kind=kind,
        member_proposal_refs=tuple(sorted(proposal_refs)),
    )


def _comparison(
    left: str,
    right: str,
    *,
    outcome: str = "equivalent",
) -> SemanticComparison:
    return SemanticComparison(
        left_proposal_ref=left,
        right_proposal_ref=right,
        outcome=outcome,
        method="semantic_model",
        trace_ref=f"comparison://{min(left, right)}--{max(left, right)}",
        rationale=f"{left} and {right}: {outcome}",
    )


def _artifact(
    *,
    upstream_artifacts=None,
    proposals=None,
    subjects=None,
    comparisons=None,
):
    if upstream_artifacts is None:
        upstream_artifacts = (_upstream(),)
    if proposals is None:
        proposals = (
            _proposal("proposal://workstation/a", persona="persona-a"),
            _proposal("proposal://workstation/b", persona="persona-b"),
        )
    if subjects is None:
        subjects = (
            _subject(
                "semantic://workstation",
                "proposal://workstation/a",
                "proposal://workstation/b",
            ),
        )
    if comparisons is None:
        comparisons = (
            _comparison(
                "proposal://workstation/a",
                "proposal://workstation/b",
            ),
        )
    return build_semantic_consolidation_artifact(
        project_id="965294",
        processing_run_id="RUN-000001",
        created_at_utc="2026-08-17T14:00:00Z",
        upstream_artifacts=tuple(upstream_artifacts),
        proposals=tuple(proposals),
        subjects=tuple(subjects),
        comparisons=tuple(comparisons),
    )


def test_valid_artifact_round_trips_with_exact_fingerprints():
    artifact = _artifact()
    payload = semantic_consolidation_artifact_to_dict(artifact)
    restored = semantic_consolidation_artifact_from_dict(payload)
    assert restored == artifact
    assert len(artifact.input_set_fingerprint) == 64
    assert len(artifact.artifact_fingerprint) == 64


def test_builder_canonicalizes_collection_order():
    upstream_a = _upstream("agent-output://a", FP_A)
    upstream_b = _upstream("agent-output://b", FP_B)
    proposal_a = _proposal("proposal://a", upstream="agent-output://a")
    proposal_b = _proposal("proposal://b", upstream="agent-output://b")
    subject_a = _subject("semantic://a", "proposal://a")
    subject_b = _subject("semantic://b", "proposal://b")
    comparison = _comparison(
        "proposal://b",
        "proposal://a",
        outcome="distinct",
    )

    first = _artifact(
        upstream_artifacts=(upstream_b, upstream_a),
        proposals=(proposal_b, proposal_a),
        subjects=(subject_b, subject_a),
        comparisons=(comparison,),
    )
    second = _artifact(
        upstream_artifacts=(upstream_a, upstream_b),
        proposals=(proposal_a, proposal_b),
        subjects=(subject_a, subject_b),
        comparisons=(comparison,),
    )

    assert first == second
    assert first.artifact_fingerprint == second.artifact_fingerprint


def test_tampered_artifact_fingerprint_fails_closed():
    artifact = _artifact()
    tampered = replace(artifact, processing_run_id="RUN-999999")
    with pytest.raises(
        SemanticConsolidationIntegrityError,
        match="artifact_fingerprint",
    ):
        validate_semantic_consolidation_artifact(tampered)


def test_tampered_input_set_fingerprint_fails_closed():
    artifact = _artifact()
    tampered = replace(artifact, input_set_fingerprint="f" * 64)
    with pytest.raises(
        SemanticConsolidationIntegrityError,
        match="input_set_fingerprint",
    ):
        validate_semantic_consolidation_artifact(tampered)


def test_duplicate_proposal_reference_is_rejected():
    proposal = _proposal("proposal://same")
    with pytest.raises(
        SemanticConsolidationIntegrityError,
        match="repeat a proposal_ref",
    ):
        _artifact(
            proposals=(proposal, proposal),
            subjects=(_subject("semantic://same", "proposal://same"),),
            comparisons=(),
        )


def test_subject_reference_to_unknown_proposal_is_rejected():
    with pytest.raises(
        SemanticConsolidationIntegrityError,
        match="unknown proposal",
    ):
        _artifact(
            proposals=(_proposal("proposal://known"),),
            subjects=(
                _subject(
                    "semantic://broken",
                    "proposal://known",
                    "proposal://unknown",
                ),
            ),
            comparisons=(),
        )


def test_proposal_cannot_belong_to_two_subjects():
    proposal = _proposal("proposal://shared")
    with pytest.raises(
        SemanticConsolidationIntegrityError,
        match="exactly one semantic subject",
    ):
        _artifact(
            proposals=(proposal,),
            subjects=(
                _subject("semantic://a", "proposal://shared"),
                _subject("semantic://b", "proposal://shared"),
            ),
            comparisons=(),
        )


def test_every_proposal_must_be_covered_by_a_subject():
    with pytest.raises(
        SemanticConsolidationIntegrityError,
        match="cover every proposal exactly once",
    ):
        _artifact(
            proposals=(
                _proposal("proposal://a"),
                _proposal("proposal://b"),
            ),
            subjects=(_subject("semantic://a", "proposal://a"),),
            comparisons=(),
        )


def test_subject_kind_must_match_member_proposal_kind():
    relationship = _proposal(
        "proposal://relationship",
        kind="relationship",
    )
    with pytest.raises(
        SemanticConsolidationIntegrityError,
        match="kind does not match",
    ):
        _artifact(
            proposals=(relationship,),
            subjects=(
                _subject(
                    "semantic://wrong-kind",
                    "proposal://relationship",
                    kind="element",
                ),
            ),
            comparisons=(),
        )


@pytest.mark.parametrize("outcome", ["distinct", "uncertain"])
def test_non_equivalent_comparison_cannot_exist_inside_one_subject(outcome):
    proposal_a = _proposal("proposal://a")
    proposal_b = _proposal("proposal://b")
    with pytest.raises(
        SemanticConsolidationIntegrityError,
        match="must not belong to the same semantic subject",
    ):
        _artifact(
            proposals=(proposal_a, proposal_b),
            subjects=(
                _subject(
                    "semantic://same",
                    "proposal://a",
                    "proposal://b",
                ),
            ),
            comparisons=(
                _comparison(
                    "proposal://a",
                    "proposal://b",
                    outcome=outcome,
                ),
            ),
        )


def test_equivalent_comparison_cannot_span_two_subjects():
    proposal_a = _proposal("proposal://a")
    proposal_b = _proposal("proposal://b")
    with pytest.raises(
        SemanticConsolidationIntegrityError,
        match="Equivalent proposals",
    ):
        _artifact(
            proposals=(proposal_a, proposal_b),
            subjects=(
                _subject("semantic://a", "proposal://a"),
                _subject("semantic://b", "proposal://b"),
            ),
            comparisons=(
                _comparison(
                    "proposal://a",
                    "proposal://b",
                    outcome="equivalent",
                ),
            ),
        )


def test_multi_member_subject_requires_equivalent_connectivity():
    proposals = (
        _proposal("proposal://a"),
        _proposal("proposal://b"),
        _proposal("proposal://c"),
    )
    with pytest.raises(
        SemanticConsolidationIntegrityError,
        match="connected by explicit equivalent",
    ):
        _artifact(
            proposals=proposals,
            subjects=(
                _subject(
                    "semantic://one",
                    "proposal://a",
                    "proposal://b",
                    "proposal://c",
                ),
            ),
            comparisons=(
                _comparison("proposal://a", "proposal://b"),
            ),
        )


def test_transitive_equivalent_connectivity_is_sufficient():
    proposals = (
        _proposal("proposal://a"),
        _proposal("proposal://b"),
        _proposal("proposal://c"),
    )
    artifact = _artifact(
        proposals=proposals,
        subjects=(
            _subject(
                "semantic://one",
                "proposal://a",
                "proposal://b",
                "proposal://c",
            ),
        ),
        comparisons=(
            _comparison("proposal://a", "proposal://b"),
            _comparison("proposal://b", "proposal://c"),
        ),
    )
    validate_semantic_consolidation_artifact(artifact)


def test_duplicate_unordered_comparison_pair_is_rejected():
    proposals = (
        _proposal("proposal://a"),
        _proposal("proposal://b"),
    )
    with pytest.raises(
        SemanticConsolidationIntegrityError,
        match="unordered proposal pair",
    ):
        _artifact(
            proposals=proposals,
            subjects=(
                _subject(
                    "semantic://one",
                    "proposal://a",
                    "proposal://b",
                ),
            ),
            comparisons=(
                _comparison("proposal://a", "proposal://b"),
                _comparison("proposal://b", "proposal://a"),
            ),
        )


def test_self_comparison_is_rejected():
    with pytest.raises(
        SemanticConsolidationIntegrityError,
        match="must not compare a proposal to itself",
    ):
        _artifact(
            proposals=(_proposal("proposal://a"),),
            subjects=(_subject("semantic://a", "proposal://a"),),
            comparisons=(_comparison("proposal://a", "proposal://a"),),
        )


def test_comparison_requires_known_proposal():
    with pytest.raises(
        SemanticConsolidationIntegrityError,
        match="unknown proposal",
    ):
        _artifact(
            proposals=(_proposal("proposal://known"),),
            subjects=(_subject("semantic://known", "proposal://known"),),
            comparisons=(
                _comparison(
                    "proposal://known",
                    "proposal://unknown",
                    outcome="distinct",
                ),
            ),
        )


def test_comparison_requires_same_proposal_kind():
    element = _proposal("proposal://element", kind="element")
    relationship = _proposal(
        "proposal://relationship",
        kind="relationship",
    )
    with pytest.raises(
        SemanticConsolidationIntegrityError,
        match="same kind",
    ):
        _artifact(
            proposals=(element, relationship),
            subjects=(
                _subject("semantic://element", "proposal://element"),
                _subject(
                    "semantic://relationship",
                    "proposal://relationship",
                    kind="relationship",
                ),
            ),
            comparisons=(
                _comparison(
                    "proposal://element",
                    "proposal://relationship",
                    outcome="distinct",
                ),
            ),
        )


def test_proposal_requires_available_upstream_artifact():
    with pytest.raises(
        SemanticConsolidationIntegrityError,
        match="unavailable upstream artifact",
    ):
        _artifact(
            proposals=(
                _proposal(
                    "proposal://orphan",
                    upstream="agent-output://missing",
                ),
            ),
            subjects=(_subject("semantic://orphan", "proposal://orphan"),),
            comparisons=(),
        )


def test_proposal_requires_at_least_one_evidence_reference():
    proposal = replace(
        _proposal("proposal://no-evidence"),
        evidence_refs=(),
    )
    with pytest.raises(
        SemanticConsolidationIntegrityError,
        match="evidence_refs must not be empty",
    ):
        _artifact(
            proposals=(proposal,),
            subjects=(
                _subject(
                    "semantic://no-evidence",
                    "proposal://no-evidence",
                ),
            ),
            comparisons=(),
        )


def test_same_persona_multiple_runs_are_valid_distinct_proposals():
    proposals = (
        _proposal(
            "proposal://persona-a/run-1",
            persona="persona-a",
            run=1,
        ),
        _proposal(
            "proposal://persona-a/run-2",
            persona="persona-a",
            run=2,
        ),
    )
    artifact = _artifact(
        proposals=proposals,
        subjects=(
            _subject(
                "semantic://same-concept",
                "proposal://persona-a/run-1",
                "proposal://persona-a/run-2",
            ),
        ),
        comparisons=(
            _comparison(
                "proposal://persona-a/run-1",
                "proposal://persona-a/run-2",
            ),
        ),
    )
    assert {proposal.persona_id for proposal in artifact.proposals} == {
        "persona-a"
    }
    assert {proposal.run_index for proposal in artifact.proposals} == {1, 2}


@pytest.mark.parametrize("run_index", [0, -1, True, 1.5])
def test_invalid_run_index_is_rejected(run_index):
    proposal = replace(
        _proposal("proposal://bad-run"),
        run_index=run_index,
    )
    with pytest.raises(SemanticConsolidationValidationError):
        _artifact(
            proposals=(proposal,),
            subjects=(_subject("semantic://bad-run", "proposal://bad-run"),),
            comparisons=(),
        )


def test_from_dict_rejects_unknown_fields():
    payload = semantic_consolidation_artifact_to_dict(_artifact())
    payload["unexpected"] = "not allowed"
    with pytest.raises(
        SemanticConsolidationValidationError,
        match="invalid fields",
    ):
        semantic_consolidation_artifact_from_dict(payload)


def test_from_dict_rejects_noncanonical_collection_order():
    payload = semantic_consolidation_artifact_to_dict(
        _artifact(
            upstream_artifacts=(
                _upstream("agent-output://a", FP_A),
                _upstream("agent-output://b", FP_B),
            ),
            proposals=(
                _proposal("proposal://a", upstream="agent-output://a"),
                _proposal("proposal://b", upstream="agent-output://b"),
            ),
            subjects=(
                _subject("semantic://a", "proposal://a"),
                _subject("semantic://b", "proposal://b"),
            ),
            comparisons=(
                _comparison(
                    "proposal://a",
                    "proposal://b",
                    outcome="distinct",
                ),
            ),
        )
    )
    payload["proposals"] = list(reversed(payload["proposals"]))
    with pytest.raises(
        SemanticConsolidationValidationError,
        match="canonical order",
    ):
        semantic_consolidation_artifact_from_dict(payload)
