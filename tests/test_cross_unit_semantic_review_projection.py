"""D5 tests for Human Review projection from D4 synthesized subjects."""

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
    ReviewIntegrityError,
)
from modules.review_workspace.p9_evidence_reference_adapter import (
    P9StructuredEvidenceSet,
    P9SubjectEvidence,
    construct_p9_source_evidence_references,
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
    CROSS_UNIT_SEMANTIC_SYNTHESIS_ARTIFACT_FILENAME,
    load_semantic_review_consensus_evidence_facts,
    project_p9_review_inputs_to_semantic_subjects,
)
from modules.review_workspace.types import (
    ReviewEvidenceReference,
    ReviewProposalReference,
)
from modules.semantic_consolidation.cross_unit_synthesis import (
    LocalElementSubject,
    LocalRelationshipSubject,
    cross_unit_semantic_synthesis_artifact_to_dict,
    synthesize_cross_unit_semantics,
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


def _proposal_reference(
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
    return P9ElementProposal(
        stable_subject_key=create_element_stable_subject_key(
            element_type=element_type,
            candidate_name=name,
        ),
        candidate_id=candidate_id,
        element_type=element_type,
        candidate_name=name,
        description=f"Description for {name}",
        source_basis=("SRC_INFO_001",),
        source_assignments=(
            P9SourceAssignment(
                source_info_id="SRC_INFO_001",
                source_statement=f"Source for {name}",
                assignment_type="direct",
                confidence="high",
            ),
        ),
        confidence="high",
        generation_readiness="ready",
        missing_information=(),
        rationale_summary=f"Rationale for {name}",
        proposal_reference=_proposal_reference(
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
    target: P9ElementProposal,
) -> P9RelationshipProposal:
    return P9RelationshipProposal(
        stable_subject_key=create_relationship_stable_subject_key(
            source_subject_key=source.stable_subject_key,
            link_type="observes",
            target_subject_key=target.stable_subject_key,
        ),
        link_id=link_id,
        source_element_candidate=source.candidate_id,
        source_subject_key=source.stable_subject_key,
        link_type="observes",
        target_element_candidate=target.candidate_id,
        target_subject_key=target.stable_subject_key,
        source_basis=("SRC_INFO_001",),
        source_statement=(
            f"{source.candidate_name} observes {target.candidate_name}."
        ),
        confidence="high",
        rationale_summary="Direct source-supported relationship.",
        proposal_reference=_proposal_reference(
            artifact,
            agent=agent,
            persona=persona,
            proposal_id=link_id,
        ),
    )


def _source_evidence(
    proposal: P9ElementProposal | P9RelationshipProposal,
) -> ReviewEvidenceReference:
    reference = proposal.proposal_reference
    locator = (
        "output_text:/candidate_model_elements/"
        f"{proposal.candidate_id}/source_evidence"
        if isinstance(proposal, P9ElementProposal)
        else (
            "output_text:/explicit_source_links/"
            f"{proposal.link_id}/source_evidence"
        )
    )
    return ReviewEvidenceReference(
        artifact_reference=reference.artifact_reference,
        evidence_role="agent_source_evidence",
        evidence_locator=locator,
        evidence_content_fingerprint=_fp(locator),
    )


def _subject_evidence(
    proposal: P9ElementProposal | P9RelationshipProposal,
) -> P9SubjectEvidence:
    return P9SubjectEvidence(
        stable_subject_key=proposal.stable_subject_key,
        review_item_kind=(
            "element"
            if isinstance(proposal, P9ElementProposal)
            else "relationship"
        ),
        source_evidence_references=(
            _source_evidence(proposal),
        ),
        consensus_evidence_references=(),
    )


def _work_ref(
    *,
    sau: str,
    agent: str,
    proposal_kind: str,
    proposal_id: str,
) -> str:
    return (
        "data/projects/123456/runs/RUN-000001/work/"
        "agentic_ingestion/ATT-000001/phase_f/agent_outputs/"
        f"03_derivation_assessment/{sau}/"
        f"team_derivation_assessment/{agent}/"
        f"{agent}_run_01.json"
        f"#{proposal_kind}:{proposal_id}"
    )


def _published_agent_path(
    *,
    sau: str,
    agent: str,
) -> str:
    return (
        "data/projects/123456/runs/RUN-000001/artifacts/"
        "agent_outputs/agentic_ingestion/ATT-000001/"
        f"03_derivation_assessment/{sau}/"
        f"team_derivation_assessment/{agent}/"
        f"{agent}_run_01.json"
    )


def _equivalent_comparator(
    groups: list[list[str]],
):
    def compare(payload):
        comparisons = []
        for group in groups:
            for left, right in zip(group, group[1:]):
                comparisons.append(
                    {
                        "left_ref": left,
                        "right_ref": right,
                        "outcome": "equivalent",
                        "rationale": "Same engineering subject.",
                    }
                )
        return {
            "schema_version": "1.0.0",
            "method": "semantic_model",
            "trace_ref": "trace:d5-test",
            "groups": [
                {"member_refs": group}
                for group in groups
            ],
            "comparisons": comparisons,
        }

    return compare


def _fixture(tmp_path: Path):
    repository_root = tmp_path / "repo"
    repository_root.mkdir()

    fp_a = _fp("agent-a")
    fp_b = _fp("agent-b")
    art_a = _artifact_ref(
        "AGOUT-A",
        fingerprint=fp_a,
        path=_published_agent_path(
            sau="SAU-000001",
            agent="agent_a",
        ),
    )
    art_b = _artifact_ref(
        "AGOUT-B",
        fingerprint=fp_b,
        path=_published_agent_path(
            sau="SAU-000002",
            agent="agent_b",
        ),
    )

    a_operator = _element(
        art_a,
        agent="agent_a",
        persona="PERSONA_A",
        candidate_id="ELEM_001",
        name="Microscope Operator",
        element_type="actor",
    )
    a_image = _element(
        art_a,
        agent="agent_a",
        persona="PERSONA_A",
        candidate_id="ELEM_002",
        name="Live Microscope Image",
        element_type="item",
    )
    b_operator = _element(
        art_b,
        agent="agent_b",
        persona="PERSONA_B",
        candidate_id="ELEM_007",
        name="Operator of Microscope",
        element_type="actor",
    )
    b_image = _element(
        art_b,
        agent="agent_b",
        persona="PERSONA_B",
        candidate_id="ELEM_008",
        name="Microscope Live Image",
        element_type="item",
    )

    rel_a = _relationship(
        art_a,
        agent="agent_a",
        persona="PERSONA_A",
        link_id="LINK_001",
        source=a_operator,
        target=a_image,
    )
    rel_b = _relationship(
        art_b,
        agent="agent_b",
        persona="PERSONA_B",
        link_id="LINK_009",
        source=b_operator,
        target=b_image,
    )

    proposals = P9StructuredProposalSet(
        project_id=PROJECT_ID,
        source_id=SOURCE_ID,
        processing_run_id=RUN_ID,
        attempt_id=ATTEMPT_ID,
        element_proposals=(
            a_operator,
            a_image,
            b_operator,
            b_image,
        ),
        relationship_proposals=(
            rel_a,
            rel_b,
        ),
    )
    evidence = P9StructuredEvidenceSet(
        project_id=PROJECT_ID,
        source_id=SOURCE_ID,
        processing_run_id=RUN_ID,
        attempt_id=ATTEMPT_ID,
        subject_evidence=tuple(
            _subject_evidence(proposal)
            for proposal in (
                *proposals.element_proposals,
                *proposals.relationship_proposals,
            )
        ),
    )

    element_refs = {
        "a_operator": _work_ref(
            sau="SAU-000001",
            agent="agent_a",
            proposal_kind="element",
            proposal_id="ELEM_001",
        ),
        "a_image": _work_ref(
            sau="SAU-000001",
            agent="agent_a",
            proposal_kind="element",
            proposal_id="ELEM_002",
        ),
        "b_operator": _work_ref(
            sau="SAU-000002",
            agent="agent_b",
            proposal_kind="element",
            proposal_id="ELEM_007",
        ),
        "b_image": _work_ref(
            sau="SAU-000002",
            agent="agent_b",
            proposal_kind="element",
            proposal_id="ELEM_008",
        ),
    }
    relationship_refs = {
        "a": _work_ref(
            sau="SAU-000001",
            agent="agent_a",
            proposal_kind="relationship",
            proposal_id="LINK_001",
        ),
        "b": _work_ref(
            sau="SAU-000002",
            agent="agent_b",
            proposal_kind="relationship",
            proposal_id="LINK_009",
        ),
    }

    local_elements = (
        LocalElementSubject(
            local_subject_ref="LE-001",
            source_analysis_unit_id="SAU-000001",
            local_semantic_subject_id="semantic:element:operator-a",
            member_proposal_refs=(element_refs["a_operator"],),
            candidate_names=("Microscope Operator",),
            proposed_element_types=("actor",),
            concise_descriptions=("Operator A",),
            evidence_refs=("EV-A-OP",),
        ),
        LocalElementSubject(
            local_subject_ref="LE-002",
            source_analysis_unit_id="SAU-000001",
            local_semantic_subject_id="semantic:element:image-a",
            member_proposal_refs=(element_refs["a_image"],),
            candidate_names=("Live Microscope Image",),
            proposed_element_types=("item",),
            concise_descriptions=("Image A",),
            evidence_refs=("EV-A-IM",),
        ),
        LocalElementSubject(
            local_subject_ref="LE-003",
            source_analysis_unit_id="SAU-000002",
            local_semantic_subject_id="semantic:element:operator-b",
            member_proposal_refs=(element_refs["b_operator"],),
            candidate_names=("Operator of Microscope",),
            proposed_element_types=("actor",),
            concise_descriptions=("Operator B",),
            evidence_refs=("EV-B-OP",),
        ),
        LocalElementSubject(
            local_subject_ref="LE-004",
            source_analysis_unit_id="SAU-000002",
            local_semantic_subject_id="semantic:element:image-b",
            member_proposal_refs=(element_refs["b_image"],),
            candidate_names=("Microscope Live Image",),
            proposed_element_types=("item",),
            concise_descriptions=("Image B",),
            evidence_refs=("EV-B-IM",),
        ),
    )
    local_relationships = (
        LocalRelationshipSubject(
            local_subject_ref="LR-001",
            source_analysis_unit_id="SAU-000001",
            local_semantic_subject_id="semantic:relationship:a",
            member_proposal_refs=(relationship_refs["a"],),
            source_local_element_subject_ref="LE-001",
            source_unresolved_endpoint_ref=None,
            target_local_element_subject_ref="LE-002",
            target_unresolved_endpoint_ref=None,
            proposed_relationship_types=("observes",),
            semantic_statements=("Operator observes image.",),
            evidence_refs=("EV-A-REL",),
        ),
        LocalRelationshipSubject(
            local_subject_ref="LR-002",
            source_analysis_unit_id="SAU-000002",
            local_semantic_subject_id="semantic:relationship:b",
            member_proposal_refs=(relationship_refs["b"],),
            source_local_element_subject_ref="LE-003",
            source_unresolved_endpoint_ref=None,
            target_local_element_subject_ref="LE-004",
            target_unresolved_endpoint_ref=None,
            proposed_relationship_types=("observes",),
            semantic_statements=("Operator observes image.",),
            evidence_refs=("EV-B-REL",),
        ),
    )

    d4 = synthesize_cross_unit_semantics(
        project_id=PROJECT_ID,
        processing_run_id=RUN_ID,
        created_at_utc="2026-08-18T20:00:00Z",
        source_analysis_unit_ids=(
            "SAU-000001",
            "SAU-000002",
        ),
        local_element_subjects=local_elements,
        local_relationship_subjects=local_relationships,
        element_comparator=_equivalent_comparator(
            [
                ["LE-001", "LE-003"],
                ["LE-002", "LE-004"],
            ]
        ),
        relationship_comparator=_equivalent_comparator(
            [["LR-001", "LR-002"]]
        ),
    )

    relative = (
        Path("data/projects")
        / PROJECT_ID
        / "runs"
        / RUN_ID
        / "artifacts"
        / "consensus_reports"
        / "agentic_ingestion"
        / ATTEMPT_ID
        / "06_cross_unit_synthesis"
        / CROSS_UNIT_SEMANTIC_SYNTHESIS_ARTIFACT_FILENAME
    )
    path = repository_root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    wrapper = {
        "cross_unit_semantic_synthesis": (
            cross_unit_semantic_synthesis_artifact_to_dict(
                d4.artifact
            )
        ),
        "execution": {},
    }
    content = (
        json.dumps(
            wrapper,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")
    path.write_bytes(content)
    d4_ref = _artifact_ref(
        "CONS-D4",
        fingerprint=hashlib.sha256(content).hexdigest(),
        path=relative.as_posix(),
        artifact_type="consensus_reports",
    )

    # D3 publishes several same-named local C2/C3 artifacts. D5 must prefer
    # the one D4 authority artifact and must not trip legacy filename
    # uniqueness checks over those local files.
    local_c2_a = _artifact_ref(
        "CONS-D3-A",
        fingerprint=_fp("local-c2-a"),
        path=(
            "data/projects/123456/runs/RUN-000001/artifacts/"
            "consensus_reports/agentic_ingestion/ATT-000001/"
            "05_semantic_consolidation/SAU-000001/"
            "semantic_element_consolidation.json"
        ),
        artifact_type="consensus_reports",
    )
    local_c2_b = _artifact_ref(
        "CONS-D3-B",
        fingerprint=_fp("local-c2-b"),
        path=(
            "data/projects/123456/runs/RUN-000001/artifacts/"
            "consensus_reports/agentic_ingestion/ATT-000001/"
            "05_semantic_consolidation/SAU-000002/"
            "semantic_element_consolidation.json"
        ),
        artifact_type="consensus_reports",
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
        primary_review_artifact_reference=_artifact_ref(
            "REVIEW-1",
            fingerprint=_fp("review"),
            path=(
                "data/projects/123456/runs/RUN-000001/"
                "artifacts/review_reports/review.md"
            ),
            artifact_type="review_reports",
        ),
        agent_output_references=(art_a, art_b),
        consensus_report_references=(
            local_c2_a,
            local_c2_b,
            d4_ref,
        ),
        run_summary_references=(),
    )
    return (
        repository_root,
        p9_evidence,
        proposals,
        evidence,
        path,
    )


def test_d4_preprojection_source_evidence_does_not_require_legacy_consensus(
    tmp_path: Path,
) -> None:
    root, p9_evidence, proposals, _, _ = _fixture(tmp_path)

    evidence = construct_p9_source_evidence_references(
        p9_evidence,
        proposals,
        repository_root=root,
    )

    assert evidence.project_id == PROJECT_ID
    assert evidence.source_id == SOURCE_ID
    assert evidence.processing_run_id == RUN_ID
    assert evidence.attempt_id == ATTEMPT_ID
    assert evidence.subject_evidence

    assert all(
        record.source_evidence_references
        for record in evidence.subject_evidence
    )
    assert all(
        not record.consensus_evidence_references
        for record in evidence.subject_evidence
    )


def test_d4_projection_compiles_raw_proposals_into_synthesized_review_subjects(
    tmp_path: Path,
) -> None:
    root, p9_evidence, proposals, evidence, _ = _fixture(
        tmp_path
    )

    projected = project_p9_review_inputs_to_semantic_subjects(
        p9_evidence,
        proposals,
        evidence,
        repository_root=root,
    )

    assert projected.used_semantic_projection is True
    assert projected.element_semantic_subject_count == 2
    assert projected.relationship_semantic_subject_count == 1

    assert {
        proposal.stable_subject_key
        for proposal in projected.proposals.element_proposals
    } == {
        "semantic:element:ses-000001",
        "semantic:element:ses-000002",
    }
    relationships = (
        projected.proposals.relationship_proposals
    )
    assert {
        proposal.stable_subject_key
        for proposal in relationships
    } == {"semantic:relationship:srs-000001"}
    assert {
        proposal.source_subject_key
        for proposal in relationships
    } == {"semantic:element:ses-000001"}
    assert {
        proposal.target_subject_key
        for proposal in relationships
    } == {"semantic:element:ses-000002"}

    evidence_by_subject = {
        item.stable_subject_key: item
        for item in projected.evidence.subject_evidence
    }
    assert set(evidence_by_subject) == {
        "semantic:element:ses-000001",
        "semantic:element:ses-000002",
        "semantic:relationship:srs-000001",
    }
    assert len(
        evidence_by_subject["semantic:element:ses-000001"]
        .source_evidence_references
    ) == 2
    assert len(
        evidence_by_subject["semantic:element:ses-000002"]
        .source_evidence_references
    ) == 2
    assert len(
        evidence_by_subject["semantic:relationship:srs-000001"]
        .source_evidence_references
    ) == 2

    expected_d4_ids = {
        "semantic:element:ses-000001": "SES-000001",
        "semantic:element:ses-000002": "SES-000002",
        "semantic:relationship:srs-000001": "SRS-000001",
    }
    for subject_key, record in evidence_by_subject.items():
        assert len(record.consensus_evidence_references) == 1
        reference = record.consensus_evidence_references[0]
        assert (
            reference.artifact_reference.artifact_id
            == "CONS-D4"
        )
        assert (
            "cross_unit_semantic_synthesis:/"
            in reference.evidence_locator
        )
        assert (
            expected_d4_ids[subject_key]
            in reference.evidence_locator
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
    assert (
        len(
            review_items.item_for_subject(
                "semantic:element:ses-000001"
            ).proposal_references
        )
        == 2
    )
    assert (
        len(
            review_items.item_for_subject(
                "semantic:relationship:srs-000001"
            ).proposal_references
        )
        == 2
    )


def test_d4_projection_exposes_distinct_persona_recognition_consensus(
    tmp_path: Path,
) -> None:
    root, p9_evidence, proposals, _, _ = _fixture(
        tmp_path
    )

    facts = load_semantic_review_consensus_evidence_facts(
        p9_evidence,
        proposals,
        repository_root=root,
    )

    assert len(facts) == 3
    assert {
        fact.agreement_level for fact in facts
    } == {"full_agreement"}
    assert all(fact.review_required for fact in facts)
    assert all(
        fact.artifact_id == "CONS-D4"
        for fact in facts
    )


def test_d4_projection_rejects_tampered_internal_artifact(
    tmp_path: Path,
) -> None:
    root, p9_evidence, proposals, evidence, path = (
        _fixture(tmp_path)
    )
    wrapper = json.loads(path.read_text(encoding="utf-8"))
    wrapper[
        "cross_unit_semantic_synthesis"
    ][
        "synthesized_element_subjects"
    ][0][
        "source_analysis_unit_ids"
    ] = ["SAU-000002"]
    tampered = (
        json.dumps(
            wrapper,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")
    path.write_bytes(tampered)

    d4_reference = next(
        reference
        for reference
        in p9_evidence.consensus_report_references
        if reference.artifact_id == "CONS-D4"
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
            (
                _artifact_ref(
                    reference.artifact_id,
                    fingerprint=hashlib.sha256(
                        tampered
                    ).hexdigest(),
                    path=reference.repository_relative_path,
                    artifact_type=reference.artifact_type,
                )
                if reference is d4_reference
                else reference
            )
            for reference
            in p9_evidence.consensus_report_references
        ),
        run_summary_references=(
            p9_evidence.run_summary_references
        ),
    )

    with pytest.raises(ReviewIntegrityError):
        project_p9_review_inputs_to_semantic_subjects(
            p9_evidence,
            proposals,
            evidence,
            repository_root=root,
        )
