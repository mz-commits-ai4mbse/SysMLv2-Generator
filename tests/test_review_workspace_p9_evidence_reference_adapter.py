"""Tests for P9 source and consensus evidence references."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
import hashlib
import json
from pathlib import Path

import pytest

from modules.project_processing import (
    create_processing_artifact_reference,
)
from modules.project_workspace.types import (
    FrameworkTemplateReference,
)
from modules.review_workspace.evidence_adapter import (
    P9ReviewEvidenceSet,
)
from modules.review_workspace.errors import (
    ReviewIntegrityError,
    ReviewReferenceError,
)
from modules.review_workspace.p9_evidence_reference_adapter import (
    construct_p9_evidence_references,
)
from modules.review_workspace.p9_proposal_adapter import (
    P9ElementProposal,
    P9RelationshipProposal,
    P9SourceAssignment,
    P9StructuredProposalSet,
    create_element_stable_subject_key,
    create_relationship_stable_subject_key,
)
from modules.review_workspace.types import (
    ReviewProposalReference,
)


PROJECT_ID = "123456"
SOURCE_ID = "SRC-000001"
RUN_ID = "RUN-000001"
ATTEMPT_ID = "ATT-000001"

AGENT_A = "AGENT_DERIVATION_A"
AGENT_B = "AGENT_DERIVATION_B"

PERSONA_A = "PERSONA_DERIVATION_A"
PERSONA_B = "PERSONA_DERIVATION_B"


def _agent_reference(
    *,
    artifact_index: int,
    agent_id: str,
):
    return create_processing_artifact_reference(
        artifact_type="agent_outputs",
        artifact_id=(
            f"AGOUT-{ATTEMPT_ID}-"
            f"{artifact_index:04d}"
        ),
        content_fingerprint=(
            f"{artifact_index:x}" * 64
        )[:64],
        repository_relative_path=(
            f"data/projects/{PROJECT_ID}/runs/{RUN_ID}/"
            "artifacts/agent_outputs/agentic_ingestion/"
            f"{ATTEMPT_ID}/03_derivation_assessment/"
            "team_derivation_assessment/"
            f"{agent_id.lower()}/agent.json"
        ),
    )


def _proposal_reference(
    artifact_reference,
    *,
    agent_id: str,
    persona_id: str,
    proposal_id: str,
):
    return ReviewProposalReference(
        artifact_reference=artifact_reference,
        agent_id=agent_id,
        persona_id=persona_id,
        proposal_id=proposal_id,
        proposal_content_fingerprint="d" * 64,
        original_report_locator=(
            f"report:{proposal_id}"
        ),
        review_state="available",
    )


def _element_proposal(
    artifact_reference,
    *,
    agent_id: str,
    persona_id: str,
    candidate_id: str,
    element_type: str,
    candidate_name: str,
    source_statement: str | None = None,
):
    stable_subject_key = (
        create_element_stable_subject_key(
            element_type=element_type,
            candidate_name=candidate_name,
        )
    )

    return P9ElementProposal(
        stable_subject_key=stable_subject_key,
        candidate_id=candidate_id,
        element_type=element_type,
        candidate_name=candidate_name,
        description=(
            f"Description of {candidate_name}."
        ),
        source_basis=("SRC_INFO_001",),
        source_assignments=(
            P9SourceAssignment(
                source_info_id="SRC_INFO_001",
                source_statement=(
                    source_statement
                    or (
                        "The source identifies "
                        f"{candidate_name}."
                    )
                ),
                assignment_type="defines_element",
                confidence="high",
            ),
        ),
        confidence="high",
        generation_readiness="ready",
        missing_information=(),
        rationale_summary=(
            "Directly source-supported."
        ),
        proposal_reference=_proposal_reference(
            artifact_reference,
            agent_id=agent_id,
            persona_id=persona_id,
            proposal_id=candidate_id,
        ),
    )


def _relationship_proposal(
    artifact_reference,
    *,
    agent_id: str,
    persona_id: str,
    source_proposal: P9ElementProposal,
    target_proposal: P9ElementProposal,
    link_id: str,
):
    stable_subject_key = (
        create_relationship_stable_subject_key(
            source_subject_key=(
                source_proposal.stable_subject_key
            ),
            link_type="controls",
            target_subject_key=(
                target_proposal.stable_subject_key
            ),
        )
    )

    return P9RelationshipProposal(
        stable_subject_key=stable_subject_key,
        link_id=link_id,
        source_element_candidate=(
            source_proposal.candidate_id
        ),
        source_subject_key=(
            source_proposal.stable_subject_key
        ),
        link_type="controls",
        target_element_candidate=(
            target_proposal.candidate_id
        ),
        target_subject_key=(
            target_proposal.stable_subject_key
        ),
        source_basis=("SRC_INFO_002",),
        source_statement=(
            "The operator controls the microscope."
        ),
        confidence="high",
        rationale_summary=(
            "The relationship is explicitly stated."
        ),
        proposal_reference=_proposal_reference(
            artifact_reference,
            agent_id=agent_id,
            persona_id=persona_id,
            proposal_id=link_id,
        ),
    )


def _proposal_set(
    *,
    reverse: bool = False,
    changed_source_statement: str | None = None,
):
    reference_a = _agent_reference(
        artifact_index=1,
        agent_id=AGENT_A,
    )
    reference_b = _agent_reference(
        artifact_index=2,
        agent_id=AGENT_B,
    )

    operator_a = _element_proposal(
        reference_a,
        agent_id=AGENT_A,
        persona_id=PERSONA_A,
        candidate_id="ELEM_001",
        element_type="actor",
        candidate_name="Microscope Operator",
        source_statement=changed_source_statement,
    )
    microscope_a = _element_proposal(
        reference_a,
        agent_id=AGENT_A,
        persona_id=PERSONA_A,
        candidate_id="ELEM_002",
        element_type="system",
        candidate_name="Microscope",
    )
    operator_b = _element_proposal(
        reference_b,
        agent_id=AGENT_B,
        persona_id=PERSONA_B,
        candidate_id="ELEM_101",
        element_type="actor",
        candidate_name="Microscope Operator",
    )
    microscope_b = _element_proposal(
        reference_b,
        agent_id=AGENT_B,
        persona_id=PERSONA_B,
        candidate_id="ELEM_102",
        element_type="system",
        candidate_name="Microscope",
    )

    relationship_a = _relationship_proposal(
        reference_a,
        agent_id=AGENT_A,
        persona_id=PERSONA_A,
        source_proposal=operator_a,
        target_proposal=microscope_a,
        link_id="LINK_001",
    )
    relationship_b = _relationship_proposal(
        reference_b,
        agent_id=AGENT_B,
        persona_id=PERSONA_B,
        source_proposal=operator_b,
        target_proposal=microscope_b,
        link_id="LINK_101",
    )

    element_proposals = (
        operator_a,
        microscope_a,
        operator_b,
        microscope_b,
    )
    relationship_proposals = (
        relationship_a,
        relationship_b,
    )

    if reverse:
        element_proposals = tuple(
            reversed(element_proposals)
        )
        relationship_proposals = tuple(
            reversed(relationship_proposals)
        )

    return (
        P9StructuredProposalSet(
            project_id=PROJECT_ID,
            source_id=SOURCE_ID,
            processing_run_id=RUN_ID,
            attempt_id=ATTEMPT_ID,
            element_proposals=element_proposals,
            relationship_proposals=(
                relationship_proposals
            ),
        ),
        (reference_a, reference_b),
    )


def _group(
    *,
    group_key: str,
    item_type: str = "candidate_model_element",
):
    return {
        "group_key": group_key,
        "item_type": item_type,
        "agreement_level": "full_agreement",
        "total_agents": 2,
        "supporting_agents": [
            AGENT_A,
            AGENT_B,
        ],
        "value_distribution": {
            "ready": [
                AGENT_A,
                AGENT_B,
            ]
        },
        "representative_value": (
            "Representative value."
        ),
        "review_required": False,
        "reason": (
            "All agents produced the same "
            "comparable item."
        ),
        "agent_values": {
            AGENT_A: "Agent A value.",
            AGENT_B: "Agent B value.",
        },
    }


def _default_groups():
    return [
        _group(
            group_key=(
                "candidate_model_element::actor::"
                "microscope operator"
            )
        ),
        _group(
            group_key=(
                "candidate_model_element::system::"
                "microscope"
            )
        ),
        _group(
            group_key=(
                "sysml_model_buildability::"
                "requirements model"
            ),
            item_type="sysml_model_buildability",
        ),
    ]


def _summary(groups):
    counts = {
        "total_groups": len(groups),
        "full_agreement": 0,
        "majority_agreement": 0,
        "majority_with_disagreement": 0,
        "minority_interpretation": 0,
        "conflict": 0,
        "review_required": 0,
    }

    for group in groups:
        counts[group["agreement_level"]] += 1

        if group["review_required"]:
            counts["review_required"] += 1

    return counts


def _report(
    *,
    groups=None,
    team_id: str = (
        "TEAM_DERIVATION_ASSESSMENT"
    ),
    agent_ids=None,
    agent_labels=None,
):
    selected_groups = (
        _default_groups()
        if groups is None
        else groups
    )
    selected_agents = (
        [AGENT_A, AGENT_B]
        if agent_ids is None
        else agent_ids
    )
    selected_labels = (
        {
            AGENT_A: PERSONA_A,
            AGENT_B: PERSONA_B,
        }
        if agent_labels is None
        else agent_labels
    )

    return {
        "consensus_report_id": (
            "CONSENSUS_TEAM_DERIVATION_001"
        ),
        "team_id": team_id,
        "task_name": (
            "Assess downstream model derivation support"
        ),
        "created_at": (
            "2026-08-04T17:00:00+00:00"
        ),
        "total_agents": len(selected_agents),
        "agent_ids": selected_agents,
        "agent_labels": selected_labels,
        "summary": _summary(selected_groups),
        "groups": selected_groups,
    }


def _write_consensus(
    repository_root: Path,
    report,
    *,
    artifact_index: int = 1,
    attempt_id: str = ATTEMPT_ID,
):
    relative_path = (
        Path("data")
        / "projects"
        / PROJECT_ID
        / "runs"
        / RUN_ID
        / "artifacts"
        / "consensus_reports"
        / "agentic_ingestion"
        / attempt_id
        / "03_derivation_assessment"
        / (
            "team_derivation_assessment_"
            f"consensus_{artifact_index}.json"
        )
    )
    target = repository_root / relative_path
    target.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    content = json.dumps(
        report,
        indent=2,
        ensure_ascii=False,
    ).encode("utf-8")

    target.write_bytes(content)

    reference = (
        create_processing_artifact_reference(
            artifact_type="consensus_reports",
            artifact_id=(
                f"CONS-{ATTEMPT_ID}-"
                f"{artifact_index:04d}"
            ),
            content_fingerprint=hashlib.sha256(
                content
            ).hexdigest(),
            repository_relative_path=(
                relative_path.as_posix()
            ),
        )
    )

    return reference, target


def _evidence(
    agent_references,
    consensus_references,
):
    primary = create_processing_artifact_reference(
        artifact_type="review_reports",
        artifact_id="REVIEW-ATT-000001-0001",
        content_fingerprint="a" * 64,
        repository_relative_path=(
            "data/projects/123456/runs/RUN-000001/"
            "artifacts/review_reports/"
            "agentic_ingestion/ATT-000001/"
            "review.md"
        ),
    )

    return P9ReviewEvidenceSet(
        project_id=PROJECT_ID,
        source_id=SOURCE_ID,
        source_sha256="b" * 64,
        processing_run_id=RUN_ID,
        attempt_id=ATTEMPT_ID,
        framework_template=FrameworkTemplateReference(
            template_id="TURING_RFLP_FRAMEWORK",
            template_version="1.0.0",
        ),
        semantic_reference_versions=(),
        primary_review_artifact_reference=primary,
        agent_output_references=tuple(
            agent_references
        ),
        consensus_report_references=tuple(
            consensus_references
        ),
        run_summary_references=(),
    )


def test_constructs_source_and_consensus_evidence(
    tmp_path: Path,
) -> None:
    repository_root = tmp_path / "repository"
    repository_root.mkdir()

    proposals, agent_references = _proposal_set()
    consensus_reference, _ = _write_consensus(
        repository_root,
        _report(),
    )

    selected = construct_p9_evidence_references(
        _evidence(
            agent_references,
            (consensus_reference,),
        ),
        proposals,
        repository_root=repository_root,
    )

    assert selected.project_id == PROJECT_ID
    assert len(selected.subject_evidence) == 3

    operator_key = (
        create_element_stable_subject_key(
            element_type="actor",
            candidate_name="Microscope Operator",
        )
    )
    operator = selected.evidence_for_subject(
        operator_key
    )

    assert operator.review_item_kind == "element"
    assert len(
        operator.source_evidence_references
    ) == 2
    assert len(
        operator.consensus_evidence_references
    ) == 1
    assert (
        operator.consensus_evidence_references[0]
        .evidence_locator
        == "/groups/0"
    )

    relationship = next(
        record
        for record in selected.subject_evidence
        if record.review_item_kind
        == "relationship"
    )

    assert len(
        relationship.source_evidence_references
    ) == 2
    assert (
        relationship.consensus_evidence_references
        == ()
    )


def test_output_is_deterministic(
    tmp_path: Path,
) -> None:
    repository_root = tmp_path / "repository"
    repository_root.mkdir()

    forward, agent_references = _proposal_set()
    reverse, _ = _proposal_set(reverse=True)

    consensus_reference, _ = _write_consensus(
        repository_root,
        _report(),
    )
    evidence = _evidence(
        tuple(reversed(agent_references)),
        (consensus_reference,),
    )

    first = construct_p9_evidence_references(
        evidence,
        forward,
        repository_root=repository_root,
    )
    second = construct_p9_evidence_references(
        evidence,
        reverse,
        repository_root=repository_root,
    )

    assert first == second


def test_changed_source_evidence_changes_fingerprint(
    tmp_path: Path,
) -> None:
    repository_root = tmp_path / "repository"
    repository_root.mkdir()

    first, agent_references = _proposal_set()
    second, _ = _proposal_set(
        changed_source_statement=(
            "The source explicitly identifies "
            "the local operator."
        )
    )

    consensus_reference, _ = _write_consensus(
        repository_root,
        _report(),
    )
    evidence = _evidence(
        agent_references,
        (consensus_reference,),
    )

    first_result = (
        construct_p9_evidence_references(
            evidence,
            first,
            repository_root=repository_root,
        )
    )
    second_result = (
        construct_p9_evidence_references(
            evidence,
            second,
            repository_root=repository_root,
        )
    )

    operator_key = (
        create_element_stable_subject_key(
            element_type="actor",
            candidate_name="Microscope Operator",
        )
    )

    first_fingerprints = {
        item.evidence_content_fingerprint
        for item in (
            first_result
            .evidence_for_subject(operator_key)
            .source_evidence_references
        )
    }
    second_fingerprints = {
        item.evidence_content_fingerprint
        for item in (
            second_result
            .evidence_for_subject(operator_key)
            .source_evidence_references
        )
    }

    assert first_fingerprints != second_fingerprints


def test_rejects_missing_consensus_json(
    tmp_path: Path,
) -> None:
    repository_root = tmp_path / "repository"
    repository_root.mkdir()

    proposals, agent_references = _proposal_set()

    with pytest.raises(
        ReviewReferenceError,
        match="no structured",
    ):
        construct_p9_evidence_references(
            _evidence(agent_references, ()),
            proposals,
            repository_root=repository_root,
        )


def test_rejects_multiple_consensus_json_files(
    tmp_path: Path,
) -> None:
    repository_root = tmp_path / "repository"
    repository_root.mkdir()

    proposals, agent_references = _proposal_set()
    first, _ = _write_consensus(
        repository_root,
        _report(),
        artifact_index=1,
    )
    second, _ = _write_consensus(
        repository_root,
        _report(),
        artifact_index=2,
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="exactly one",
    ):
        construct_p9_evidence_references(
            _evidence(
                agent_references,
                (first, second),
            ),
            proposals,
            repository_root=repository_root,
        )


def test_rejects_consensus_fingerprint_mismatch(
    tmp_path: Path,
) -> None:
    repository_root = tmp_path / "repository"
    repository_root.mkdir()

    proposals, agent_references = _proposal_set()
    reference, target = _write_consensus(
        repository_root,
        _report(),
    )
    target.write_text(
        "{}",
        encoding="utf-8",
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="fingerprint does not match",
    ):
        construct_p9_evidence_references(
            _evidence(
                agent_references,
                (reference,),
            ),
            proposals,
            repository_root=repository_root,
        )


def test_rejects_wrong_consensus_attempt_path(
    tmp_path: Path,
) -> None:
    repository_root = tmp_path / "repository"
    repository_root.mkdir()

    proposals, agent_references = _proposal_set()
    reference, _ = _write_consensus(
        repository_root,
        _report(),
        attempt_id="ATT-000002",
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="Project, Run and Attempt",
    ):
        construct_p9_evidence_references(
            _evidence(
                agent_references,
                (reference,),
            ),
            proposals,
            repository_root=repository_root,
        )


def test_rejects_wrong_consensus_team(
    tmp_path: Path,
) -> None:
    repository_root = tmp_path / "repository"
    repository_root.mkdir()

    proposals, agent_references = _proposal_set()
    reference, _ = _write_consensus(
        repository_root,
        _report(team_id="TEAM_OTHER"),
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="Derivation Assessment Team",
    ):
        construct_p9_evidence_references(
            _evidence(
                agent_references,
                (reference,),
            ),
            proposals,
            repository_root=repository_root,
        )


def test_rejects_missing_element_consensus_group(
    tmp_path: Path,
) -> None:
    repository_root = tmp_path / "repository"
    repository_root.mkdir()

    proposals, agent_references = _proposal_set()
    groups = _default_groups()
    groups.pop(1)

    reference, _ = _write_consensus(
        repository_root,
        _report(groups=groups),
    )

    with pytest.raises(
        ReviewReferenceError,
        match="missing candidate groups",
    ):
        construct_p9_evidence_references(
            _evidence(
                agent_references,
                (reference,),
            ),
            proposals,
            repository_root=repository_root,
        )


def test_rejects_extra_element_consensus_group(
    tmp_path: Path,
) -> None:
    repository_root = tmp_path / "repository"
    repository_root.mkdir()

    proposals, agent_references = _proposal_set()
    groups = _default_groups()
    groups.append(
        _group(
            group_key=(
                "candidate_model_element::system::"
                "unknown system"
            )
        )
    )

    reference, _ = _write_consensus(
        repository_root,
        _report(groups=groups),
    )

    with pytest.raises(
        ReviewReferenceError,
        match="without a matching",
    ):
        construct_p9_evidence_references(
            _evidence(
                agent_references,
                (reference,),
            ),
            proposals,
            repository_root=repository_root,
        )


def test_rejects_duplicate_element_consensus_group(
    tmp_path: Path,
) -> None:
    repository_root = tmp_path / "repository"
    repository_root.mkdir()

    proposals, agent_references = _proposal_set()
    groups = _default_groups()
    groups.append(deepcopy(groups[0]))

    reference, _ = _write_consensus(
        repository_root,
        _report(groups=groups),
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="duplicate candidate",
    ):
        construct_p9_evidence_references(
            _evidence(
                agent_references,
                (reference,),
            ),
            proposals,
            repository_root=repository_root,
        )


def test_rejects_consensus_agent_mismatch(
    tmp_path: Path,
) -> None:
    repository_root = tmp_path / "repository"
    repository_root.mkdir()

    proposals, agent_references = _proposal_set()

    groups = _default_groups()

    for group in groups:
        group["total_agents"] = 1
        group["supporting_agents"] = [AGENT_A]
        group["value_distribution"] = {
            "ready": [AGENT_A]
        }
        group["agent_values"] = {
            AGENT_A: "Agent A value."
        }

    report = _report(
        groups=groups,
        agent_ids=[AGENT_A],
        agent_labels={
            AGENT_A: PERSONA_A,
        },
    )

    reference, _ = _write_consensus(
        repository_root,
        report,
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="Agents do not match",
    ):
        construct_p9_evidence_references(
            _evidence(
                agent_references,
                (reference,),
            ),
            proposals,
            repository_root=repository_root,
        )


def test_rejects_proposal_artifact_outside_evidence_set(
    tmp_path: Path,
) -> None:
    repository_root = tmp_path / "repository"
    repository_root.mkdir()

    proposals, agent_references = _proposal_set()
    outside_reference = _agent_reference(
        artifact_index=3,
        agent_id="AGENT_DERIVATION_C",
    )

    first = proposals.element_proposals[0]
    changed_reference = replace(
        first.proposal_reference,
        artifact_reference=outside_reference,
    )
    changed_first = replace(
        first,
        proposal_reference=changed_reference,
    )
    changed_proposals = replace(
        proposals,
        element_proposals=(
            changed_first,
            *proposals.element_proposals[1:],
        ),
    )

    consensus_reference, _ = _write_consensus(
        repository_root,
        _report(),
    )

    with pytest.raises(
        ReviewReferenceError,
        match="outside the selected",
    ):
        construct_p9_evidence_references(
            _evidence(
                agent_references,
                (consensus_reference,),
            ),
            changed_proposals,
            repository_root=repository_root,
        )
