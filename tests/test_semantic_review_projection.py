"""C4.1 tests for semantic Human Review subject projection."""

from __future__ import annotations

from pathlib import Path
import hashlib
import json

import pytest

from modules.project_processing import (
    ProcessingArtifactReference,
    SemanticReferenceVersion,
)
from modules.project_workspace.types import (
    FrameworkTemplateReference,
)
from modules.review_workspace.evidence_adapter import (
    P9ReviewEvidenceSet,
)
from modules.review_workspace.errors import (
    ReviewReferenceError,
)
from modules.review_workspace.p9_evidence_reference_adapter import (
    P9StructuredEvidenceSet,
    P9SubjectEvidence,
)
from modules.review_workspace.p9_proposal_adapter import (
    P9ElementProposal,
    P9RelationshipProposal,
    P9SourceAssignment,
    P9StructuredProposalSet,
    create_element_stable_subject_key,
    create_relationship_stable_subject_key,
)
from modules.review_workspace.p9_review_item_builder import (
    construct_initial_p9_review_items,
)
from modules.review_workspace.semantic_review_projection import (
    SEMANTIC_ELEMENT_ARTIFACT_FILENAME,
    SEMANTIC_RELATIONSHIP_ARTIFACT_FILENAME,
    load_semantic_review_consensus_evidence_facts,
    project_p9_review_inputs_to_semantic_subjects,
)
from modules.review_workspace.types import (
    ReviewEvidenceReference,
    ReviewProposalReference,
)
from modules.semantic_consolidation.artifact import (
    build_semantic_consolidation_artifact,
    semantic_consolidation_artifact_to_dict,
)
from modules.semantic_consolidation.types import (
    SemanticComparison,
    SemanticProposalBinding,
    SemanticSubject,
    SemanticUpstreamArtifactBinding,
)


PROJECT_ID = "123456"
SOURCE_ID = "SRC-000001"
RUN_ID = "RUN-000001"
ATTEMPT_ID = "ATT-000001"


def _fp(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _artifact_ref(
    artifact_id: str,
    *,
    fingerprint: str,
    path: str,
    artifact_type: str = "agent_outputs",
) -> ProcessingArtifactReference:
    return ProcessingArtifactReference(
        artifact_type=artifact_type,
        artifact_id=artifact_id,
        content_fingerprint=fingerprint,
        repository_relative_path=path,
    )


def _proposal_ref(
    artifact: ProcessingArtifactReference,
    *,
    agent: str,
    persona: str,
    proposal_id: str,
) -> ReviewProposalReference:
    return ReviewProposalReference(
        artifact_reference=artifact,
        agent_id=agent,
        persona_id=persona,
        proposal_id=proposal_id,
        proposal_content_fingerprint=_fp(
            f"{artifact.artifact_id}:{proposal_id}"
        ),
        original_report_locator=f"report:{proposal_id}",
        review_state="available",
    )


def _element(
    artifact: ProcessingArtifactReference,
    *,
    agent: str,
    persona: str,
    candidate_id: str,
    name: str,
    element_type: str,
) -> P9ElementProposal:
    stable = create_element_stable_subject_key(
        element_type=element_type,
        candidate_name=name,
    )
    return P9ElementProposal(
        stable_subject_key=stable,
        candidate_id=candidate_id,
        element_type=element_type,
        candidate_name=name,
        description=f"Description for {name}",
        source_basis=("S1",),
        source_assignments=(
            P9SourceAssignment(
                source_info_id="S1",
                source_statement=f"Source for {name}",
                assignment_type="direct",
                confidence="high",
            ),
        ),
        confidence="high",
        generation_readiness="ready",
        missing_information=(),
        rationale_summary=f"Rationale for {name}",
        proposal_reference=_proposal_ref(
            artifact,
            agent=agent,
            persona=persona,
            proposal_id=candidate_id,
        ),
    )


def _relationship(
    artifact: ProcessingArtifactReference,
    *,
    agent: str,
    persona: str,
    link_id: str,
    source: P9ElementProposal,
    link_type: str,
    target: P9ElementProposal,
) -> P9RelationshipProposal:
    stable = create_relationship_stable_subject_key(
        source_subject_key=source.stable_subject_key,
        link_type=link_type,
        target_subject_key=target.stable_subject_key,
    )
    return P9RelationshipProposal(
        stable_subject_key=stable,
        link_id=link_id,
        source_element_candidate=source.candidate_id,
        source_subject_key=source.stable_subject_key,
        link_type=link_type,
        target_element_candidate=target.candidate_id,
        target_subject_key=target.stable_subject_key,
        source_basis=("S1",),
        source_statement=(
            f"{source.candidate_name} {link_type} "
            f"{target.candidate_name}."
        ),
        confidence="high",
        rationale_summary="Direct source-supported relationship.",
        proposal_reference=_proposal_ref(
            artifact,
            agent=agent,
            persona=persona,
            proposal_id=link_id,
        ),
    )


def _source_evidence(proposal):
    reference = proposal.proposal_reference
    if isinstance(proposal, P9ElementProposal):
        locator = (
            "output_text:/candidate_model_elements/"
            f"{proposal.candidate_id}/source_evidence"
        )
    else:
        locator = (
            "output_text:/explicit_source_links/"
            f"{proposal.link_id}/source_evidence"
        )
    return ReviewEvidenceReference(
        artifact_reference=reference.artifact_reference,
        evidence_role="agent_source_evidence",
        evidence_locator=locator,
        evidence_content_fingerprint=_fp(locator),
    )


def _subject_evidence(proposal):
    kind = (
        "element"
        if isinstance(proposal, P9ElementProposal)
        else "relationship"
    )
    return P9SubjectEvidence(
        stable_subject_key=proposal.stable_subject_key,
        review_item_kind=kind,
        source_evidence_references=(
            _source_evidence(proposal),
        ),
        consensus_evidence_references=(),
    )


def _semantic_artifact(
    *,
    kind: str,
    upstream: tuple[
        tuple[str, str],
        ...,
    ],
    bindings: tuple[
        tuple[str, str, str, int, str],
        ...,
    ],
    subjects: tuple[
        tuple[str, tuple[str, ...]],
        ...,
    ],
    comparisons: tuple[
        tuple[str, str],
        ...,
    ],
):
    upstream_bindings = tuple(
        SemanticUpstreamArtifactBinding(
            artifact_ref=artifact_ref,
            artifact_fingerprint=fingerprint,
        )
        for artifact_ref, fingerprint in upstream
    )
    proposal_bindings = tuple(
        sorted(
            (
                SemanticProposalBinding(
                    proposal_ref=proposal_ref,
                    proposal_kind=kind,
                    agent_id=agent,
                    persona_id=persona,
                    run_index=run_index,
                    upstream_artifact_ref=artifact_ref,
                    evidence_refs=(
                        f"{proposal_ref}#evidence",
                    ),
                )
                for (
                    proposal_ref,
                    agent,
                    persona,
                    run_index,
                    artifact_ref,
                ) in bindings
            ),
            key=lambda item: item.proposal_ref,
        )
    )
    semantic_subjects = tuple(
        sorted(
            (
                SemanticSubject(
                    semantic_subject_id=subject_id,
                    proposal_kind=kind,
                    member_proposal_refs=tuple(
                        sorted(members)
                    ),
                )
                for subject_id, members in subjects
            ),
            key=lambda item: item.semantic_subject_id,
        )
    )
    semantic_comparisons = tuple(
        sorted(
            (
                SemanticComparison(
                    left_proposal_ref=min(left, right),
                    right_proposal_ref=max(left, right),
                    outcome="equivalent",
                    method="semantic_model",
                    trace_ref="trace:test",
                    rationale=(
                        "same semantic engineering subject"
                    ),
                )
                for left, right in comparisons
            ),
            key=lambda item: (
                item.left_proposal_ref,
                item.right_proposal_ref,
            ),
        )
    )
    return build_semantic_consolidation_artifact(
        project_id=PROJECT_ID,
        processing_run_id=RUN_ID,
        created_at_utc="2026-08-18T00:00:00Z",
        upstream_artifacts=upstream_bindings,
        proposals=proposal_bindings,
        subjects=semantic_subjects,
        comparisons=semantic_comparisons,
    )


def _publish_semantic(
    repository_root: Path,
    *,
    filename: str,
    artifact,
    artifact_id: str,
) -> ProcessingArtifactReference:
    relative = (
        Path("data")
        / "projects"
        / PROJECT_ID
        / "runs"
        / RUN_ID
        / "artifacts"
        / "consensus_reports"
        / filename
    )
    path = repository_root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "semantic_consolidation": (
            semantic_consolidation_artifact_to_dict(
                artifact
            )
        ),
        "execution": {},
    }
    content = (
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")
    path.write_bytes(content)
    return _artifact_ref(
        artifact_id,
        fingerprint=hashlib.sha256(content).hexdigest(),
        path=relative.as_posix(),
        artifact_type="consensus_reports",
    )


def _fixture(tmp_path: Path, *, include_relationship=True):
    repository_root = tmp_path / "repo"
    repository_root.mkdir()

    fp_a = _fp("wrapper-A")
    fp_b = _fp("wrapper-B")
    art_a = _artifact_ref(
        "AGOUT-A",
        fingerprint=fp_a,
        path="data/projects/123456/runs/RUN-000001/artifacts/agent_outputs/A.json",
    )
    art_b = _artifact_ref(
        "AGOUT-B",
        fingerprint=fp_b,
        path="data/projects/123456/runs/RUN-000001/artifacts/agent_outputs/B.json",
    )

    a_source = _element(
        art_a,
        agent="agent-A",
        persona="A",
        candidate_id="E1",
        name="Microscope Operator",
        element_type="actor",
    )
    a_target = _element(
        art_a,
        agent="agent-A",
        persona="A",
        candidate_id="E2",
        name="Live Microscope Image",
        element_type="item",
    )
    b_source = _element(
        art_b,
        agent="agent-B",
        persona="B",
        candidate_id="E7",
        name="Operator of Microscope",
        element_type="actor",
    )
    b_target = _element(
        art_b,
        agent="agent-B",
        persona="B",
        candidate_id="E8",
        name="Microscope Live Image",
        element_type="item",
    )

    relationships = ()
    if include_relationship:
        relationships = (
            _relationship(
                art_a,
                agent="agent-A",
                persona="A",
                link_id="L1",
                source=a_source,
                link_type="observes",
                target=a_target,
            ),
            _relationship(
                art_b,
                agent="agent-B",
                persona="B",
                link_id="L9",
                source=b_source,
                link_type="views",
                target=b_target,
            ),
        )

    proposals = P9StructuredProposalSet(
        project_id=PROJECT_ID,
        source_id=SOURCE_ID,
        processing_run_id=RUN_ID,
        attempt_id=ATTEMPT_ID,
        element_proposals=(
            a_source,
            a_target,
            b_source,
            b_target,
        ),
        relationship_proposals=relationships,
    )

    evidence = P9StructuredEvidenceSet(
        project_id=PROJECT_ID,
        source_id=SOURCE_ID,
        processing_run_id=RUN_ID,
        attempt_id=ATTEMPT_ID,
        subject_evidence=tuple(
            _subject_evidence(item)
            for item in (
                *proposals.element_proposals,
                *proposals.relationship_proposals,
            )
        ),
    )

    element_artifact = _semantic_artifact(
        kind="element",
        upstream=(
            ("work/A.json", fp_a),
            ("work/B.json", fp_b),
        ),
        bindings=(
            (
                "work/A.json#element:E1",
                "agent-A",
                "A",
                1,
                "work/A.json",
            ),
            (
                "work/A.json#element:E2",
                "agent-A",
                "A",
                1,
                "work/A.json",
            ),
            (
                "work/B.json#element:E7",
                "agent-B",
                "B",
                1,
                "work/B.json",
            ),
            (
                "work/B.json#element:E8",
                "agent-B",
                "B",
                1,
                "work/B.json",
            ),
        ),
        subjects=(
            (
                "semantic:element:operator",
                (
                    "work/A.json#element:E1",
                    "work/B.json#element:E7",
                ),
            ),
            (
                "semantic:element:live-image",
                (
                    "work/A.json#element:E2",
                    "work/B.json#element:E8",
                ),
            ),
        ),
        comparisons=(
            (
                "work/A.json#element:E1",
                "work/B.json#element:E7",
            ),
            (
                "work/A.json#element:E2",
                "work/B.json#element:E8",
            ),
        ),
    )
    consensus_refs = [
        _publish_semantic(
            repository_root,
            filename=SEMANTIC_ELEMENT_ARTIFACT_FILENAME,
            artifact=element_artifact,
            artifact_id="CONS-SEM-E",
        )
    ]

    if include_relationship:
        relationship_artifact = _semantic_artifact(
            kind="relationship",
            upstream=(
                ("work/A.json", fp_a),
                ("work/B.json", fp_b),
            ),
            bindings=(
                (
                    "work/A.json#relationship:L1",
                    "agent-A",
                    "A",
                    1,
                    "work/A.json",
                ),
                (
                    "work/B.json#relationship:L9",
                    "agent-B",
                    "B",
                    1,
                    "work/B.json",
                ),
            ),
            subjects=(
                (
                    "semantic:relationship:observe",
                    (
                        "work/A.json#relationship:L1",
                        "work/B.json#relationship:L9",
                    ),
                ),
            ),
            comparisons=(
                (
                    "work/A.json#relationship:L1",
                    "work/B.json#relationship:L9",
                ),
            ),
        )
        consensus_refs.append(
            _publish_semantic(
                repository_root,
                filename=(
                    SEMANTIC_RELATIONSHIP_ARTIFACT_FILENAME
                ),
                artifact=relationship_artifact,
                artifact_id="CONS-SEM-R",
            )
        )

    primary = _artifact_ref(
        "REVIEW-1",
        fingerprint=_fp("review"),
        path="data/projects/123456/runs/RUN-000001/artifacts/review_reports/review.md",
        artifact_type="review_reports",
    )
    p9_evidence = P9ReviewEvidenceSet(
        project_id=PROJECT_ID,
        source_id=SOURCE_ID,
        source_sha256=_fp("source"),
        processing_run_id=RUN_ID,
        attempt_id=ATTEMPT_ID,
        framework_template=FrameworkTemplateReference(
            template_id="TURING_RFLP_FRAMEWORK",
            template_version="1.0.0",
        ),
        semantic_reference_versions=(
            SemanticReferenceVersion(
                reference_system_id="TEST",
                reference_version="1",
            ),
        ),
        primary_review_artifact_reference=primary,
        agent_output_references=(art_a, art_b),
        consensus_report_references=tuple(
            consensus_refs
        ),
        run_summary_references=(),
    )
    return repository_root, p9_evidence, proposals, evidence


def test_semantic_projection_reduces_raw_subjects_to_review_cards(
    tmp_path: Path,
) -> None:
    root, p9_evidence, proposals, evidence = _fixture(
        tmp_path
    )

    raw_subject_count = len(
        {
            item.stable_subject_key
            for item in (
                *proposals.element_proposals,
                *proposals.relationship_proposals,
            )
        }
    )
    assert raw_subject_count == 6

    projected = (
        project_p9_review_inputs_to_semantic_subjects(
            p9_evidence,
            proposals,
            evidence,
            repository_root=root,
        )
    )

    assert projected.used_semantic_projection is True
    assert projected.element_semantic_subject_count == 2
    assert projected.relationship_semantic_subject_count == 1
    assert {
        item.stable_subject_key
        for item in projected.proposals.element_proposals
    } == {
        "semantic:element:operator",
        "semantic:element:live-image",
    }
    assert {
        item.stable_subject_key
        for item in projected.proposals.relationship_proposals
    } == {
        "semantic:relationship:observe",
    }

    relationship = (
        projected.proposals.relationship_proposals[0]
    )
    assert relationship.source_subject_key == (
        "semantic:element:operator"
    )
    assert relationship.target_subject_key == (
        "semantic:element:live-image"
    )

    review_items = construct_initial_p9_review_items(
        projected.proposals,
        projected.evidence,
        review_document_id="RVD-000001",
        review_document_version_id="RVV-000001",
    )

    assert len(review_items.review_items) == 3
    assert len(review_items.element_items) == 2
    assert len(review_items.relationship_items) == 1

    operator_item = review_items.item_for_subject(
        "semantic:element:operator"
    )
    relationship_item = review_items.item_for_subject(
        "semantic:relationship:observe"
    )
    assert len(operator_item.proposal_references) == 2
    assert len(
        relationship_item.proposal_references
    ) == 2
    assert len(
        operator_item.source_evidence_references
    ) == 2
    assert len(
        relationship_item.source_evidence_references
    ) == 2

    assert len(
        operator_item.consensus_evidence_references
    ) == 1
    assert len(
        relationship_item.consensus_evidence_references
    ) == 1
    assert (
        operator_item.consensus_evidence_references[0]
        .evidence_locator
        == (
            "semantic_consolidation:/subjects/"
            "semantic:element:operator"
        )
    )
    assert (
        relationship_item.consensus_evidence_references[0]
        .evidence_locator
        == (
            "semantic_consolidation:/subjects/"
            "semantic:relationship:observe"
        )
    )


def test_projection_preserves_exact_proposal_references(
    tmp_path: Path,
) -> None:
    root, p9_evidence, proposals, evidence = _fixture(
        tmp_path
    )
    projected = (
        project_p9_review_inputs_to_semantic_subjects(
            p9_evidence,
            proposals,
            evidence,
            repository_root=root,
        )
    )

    raw_refs = {
        item.proposal_reference
        for item in (
            *proposals.element_proposals,
            *proposals.relationship_proposals,
        )
    }
    projected_refs = {
        item.proposal_reference
        for item in (
            *projected.proposals.element_proposals,
            *projected.proposals.relationship_proposals,
        )
    }
    assert projected_refs == raw_refs


def test_missing_relationship_semantic_artifact_fails_closed(
    tmp_path: Path,
) -> None:
    root, p9_evidence, proposals, evidence = _fixture(
        tmp_path
    )
    p9_evidence = P9ReviewEvidenceSet(
        project_id=p9_evidence.project_id,
        source_id=p9_evidence.source_id,
        source_sha256=p9_evidence.source_sha256,
        processing_run_id=p9_evidence.processing_run_id,
        attempt_id=p9_evidence.attempt_id,
        framework_template=p9_evidence.framework_template,
        semantic_reference_versions=(
            p9_evidence.semantic_reference_versions
        ),
        primary_review_artifact_reference=(
            p9_evidence.primary_review_artifact_reference
        ),
        agent_output_references=(
            p9_evidence.agent_output_references
        ),
        consensus_report_references=tuple(
            reference
            for reference
            in p9_evidence.consensus_report_references
            if not reference.repository_relative_path.endswith(
                SEMANTIC_RELATIONSHIP_ARTIFACT_FILENAME
            )
        ),
        run_summary_references=(
            p9_evidence.run_summary_references
        ),
    )

    with pytest.raises(
        ReviewReferenceError,
        match="relationship semantic consolidation",
    ):
        project_p9_review_inputs_to_semantic_subjects(
            p9_evidence,
            proposals,
            evidence,
            repository_root=root,
        )


def test_historical_run_without_semantic_artifacts_keeps_legacy_projection(
    tmp_path: Path,
) -> None:
    root, p9_evidence, proposals, evidence = _fixture(
        tmp_path,
        include_relationship=False,
    )
    p9_evidence = P9ReviewEvidenceSet(
        project_id=p9_evidence.project_id,
        source_id=p9_evidence.source_id,
        source_sha256=p9_evidence.source_sha256,
        processing_run_id=p9_evidence.processing_run_id,
        attempt_id=p9_evidence.attempt_id,
        framework_template=p9_evidence.framework_template,
        semantic_reference_versions=(
            p9_evidence.semantic_reference_versions
        ),
        primary_review_artifact_reference=(
            p9_evidence.primary_review_artifact_reference
        ),
        agent_output_references=(
            p9_evidence.agent_output_references
        ),
        consensus_report_references=(),
        run_summary_references=(
            p9_evidence.run_summary_references
        ),
    )

    result = project_p9_review_inputs_to_semantic_subjects(
        p9_evidence,
        proposals,
        evidence,
        repository_root=root,
    )

    assert result.used_semantic_projection is False
    assert result.proposals == proposals
    assert result.evidence == evidence

def test_semantic_subject_evidence_is_tamper_evident(
    tmp_path: Path,
) -> None:
    root, p9_evidence, proposals, evidence = _fixture(
        tmp_path
    )
    result = project_p9_review_inputs_to_semantic_subjects(
        p9_evidence,
        proposals,
        evidence,
        repository_root=root,
    )
    refs = tuple(
        reference
        for record in result.evidence.subject_evidence
        for reference in record.consensus_evidence_references
        if record.stable_subject_key.startswith("semantic:")
    )
    assert len(refs) == 3
    assert all(
        len(reference.evidence_content_fingerprint) == 64
        for reference in refs
    )
    assert len(
        {
            (
                reference.evidence_locator,
                reference.evidence_content_fingerprint,
            )
            for reference in refs
        }
    ) == 3

def test_semantic_filter_facts_reconstruct_exact_subject_evidence(
    tmp_path: Path,
) -> None:
    root, p9_evidence, proposals, _ = _fixture(
        tmp_path
    )

    facts = load_semantic_review_consensus_evidence_facts(
        p9_evidence,
        proposals,
        repository_root=root,
    )

    assert len(facts) == 3
    by_locator = {
        fact.evidence_locator: fact
        for fact in facts
    }
    assert set(by_locator) == {
        (
            "semantic_consolidation:/subjects/"
            "semantic:element:operator"
        ),
        (
            "semantic_consolidation:/subjects/"
            "semantic:element:live-image"
        ),
        (
            "semantic_consolidation:/subjects/"
            "semantic:relationship:observe"
        ),
    }
    assert {
        fact.agreement_level
        for fact in facts
    } == {"full_agreement"}
    assert all(fact.review_required for fact in facts)


def test_historical_run_has_no_semantic_filter_facts(
    tmp_path: Path,
) -> None:
    root, p9_evidence, proposals, _ = _fixture(
        tmp_path,
        include_relationship=False,
    )
    p9_evidence = P9ReviewEvidenceSet(
        project_id=p9_evidence.project_id,
        source_id=p9_evidence.source_id,
        source_sha256=p9_evidence.source_sha256,
        processing_run_id=p9_evidence.processing_run_id,
        attempt_id=p9_evidence.attempt_id,
        framework_template=p9_evidence.framework_template,
        semantic_reference_versions=(
            p9_evidence.semantic_reference_versions
        ),
        primary_review_artifact_reference=(
            p9_evidence.primary_review_artifact_reference
        ),
        agent_output_references=(
            p9_evidence.agent_output_references
        ),
        consensus_report_references=(),
        run_summary_references=(
            p9_evidence.run_summary_references
        ),
    )

    assert load_semantic_review_consensus_evidence_facts(
        p9_evidence,
        proposals,
        repository_root=root,
    ) == ()

