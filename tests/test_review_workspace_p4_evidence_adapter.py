"""Tests for deterministic P4 evidence association."""

from __future__ import annotations

from pathlib import Path

import pytest

from modules.framework_assignment import (
    FrameworkAssignmentAgentCandidateReference,
    FrameworkAssignmentConsensusOutcome,
    FrameworkAssignmentConsensusResult,
    FrameworkAssignmentIssue,
    FrameworkAssignmentScanResult,
    create_framework_assignment_basis,
    create_framework_assignment_candidate,
    create_framework_assignment_proposal,
)
from modules.human_review import (
    HumanReviewIssue,
    HumanReviewScanResult,
    create_human_review_decision,
    create_human_review_target_snapshot,
)
from modules.information_units import (
    InformationUnitExtractionProvenance,
    InformationUnitIssue,
    InformationUnitScanResult,
    InformationUnitSourceAnchor,
    create_information_unit,
)
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
from modules.review_workspace.p4_evidence_adapter import (
    select_p4_review_evidence_set,
)
from modules.terminology_mapping import (
    TerminologyMappingAgentCandidateReference,
    TerminologyMappingConsensusOutcome,
    TerminologyMappingConsensusResult,
    TerminologyMappingIssue,
    TerminologyMappingScanResult,
    TerminologyOccurrence,
    create_terminology_mapping_basis,
    create_terminology_mapping_candidate,
    create_terminology_mapping_proposal,
    create_terminology_mapping_target,
)


PROJECT_ID = "123456"
OTHER_PROJECT_ID = "654321"

SOURCE_ID = "SRC-000001"
OTHER_SOURCE_ID = "SRC-000002"

SOURCE_PROJECTION_ID = "SP-000001"
OTHER_SOURCE_PROJECTION_ID = "SP-000002"


def _p9_evidence() -> P9ReviewEvidenceSet:
    review_reference = (
        create_processing_artifact_reference(
            artifact_type="review_reports",
            artifact_id="REVIEW-ATT-000001-0001",
            content_fingerprint="a" * 64,
            repository_relative_path=(
                "data/projects/123456/runs/RUN-000001/"
                "artifacts/review_reports/"
                "agentic_ingestion/ATT-000001/"
                "ingestion_review_report.md"
            ),
        )
    )

    return P9ReviewEvidenceSet(
        project_id=PROJECT_ID,
        source_id=SOURCE_ID,
        source_sha256="b" * 64,
        processing_run_id="RUN-000001",
        attempt_id="ATT-000001",
        framework_template=FrameworkTemplateReference(
            template_id="TURING_RFLP_FRAMEWORK",
            template_version="1.0.0",
        ),
        semantic_reference_versions=(),
        primary_review_artifact_reference=(
            review_reference
        ),
        agent_output_references=(),
        consensus_report_references=(),
        run_summary_references=(),
    )


def _information_unit(
    *,
    information_unit_id: str = "IU-000001",
    project_id: str = PROJECT_ID,
    source_id: str = SOURCE_ID,
    source_projection_id: str = SOURCE_PROJECTION_ID,
    statement: str = (
        "The pump shall preserve source traceability."
    ),
):

    return create_information_unit(
        project_id=project_id,
        information_unit_id=information_unit_id,
        source_id=source_id,
        source_projection_id=source_projection_id,
        source_anchors=(
            InformationUnitSourceAnchor(
                segment_id="SEG-000001",
                start_offset=0,
                end_offset=len(statement),
            ),
        ),
        source_excerpt=statement,
        interpreted_statement=statement,
        information_type="requirement",
        statement_modality="normative",
        epistemic_class="explicit",
        supporting_information_unit_ids=(),
        derivation_rationale=None,
        missing_evidence=None,
        extraction_provenance=(
            InformationUnitExtractionProvenance(
                team_id="TEAM_SEMANTIC_EXTRACTION",
                persona_ids=(
                    "PERSONA_DOMAIN_EXPERT",
                    "PERSONA_SYSTEMS_ENGINEER",
                ),
                llm_provider="test-provider",
                llm_model="test-model",
                prompt_schema_version="1.0.0",
                consensus_report_id=(
                    "CONSENSUS_SEMANTIC_TEST"
                ),
            )
        ),
        confidence="high",
        confidence_rationale=(
            "All required personas agreed."
        ),
        timestamp="2026-08-04T15:00:00Z",
    )


def _terminology_candidate(
    information_unit,
    *,
    candidate_id: str = "TMC-000001",
):
    target = create_terminology_mapping_target(
        target_kind="project_concept",
        display_label="Pump",
        project_concept_id="PC-000001",
        project_concept_revision=1,
    )
    basis = create_terminology_mapping_basis(
        basis_type="accepted_project_glossary",
        reference_id=(
            f"{information_unit.project_id}/"
            "PC-000001/revision/1"
        ),
        reference_version="1",
        rationale="Accepted project terminology.",
    )
    proposal = create_terminology_mapping_proposal(
        mapping_relation="exact_match",
        target=target,
        mapping_bases=(basis,),
        rationale=(
            "The term matches the project concept."
        ),
    )
    occurrence = TerminologyOccurrence(
        information_unit_id=(
            information_unit.information_unit_id
        ),
        text_field="interpreted_statement",
        start_offset=4,
        end_offset=8,
        term_text="pump",
    )
    references = (
        TerminologyMappingAgentCandidateReference(
            persona_id="persona-a",
            agent_id="agent-a",
            persona_run_index=1,
            terminology_mapping_agent_candidate_id=(
                "TMAC-000001"
            ),
        ),
        TerminologyMappingAgentCandidateReference(
            persona_id="persona-b",
            agent_id="agent-b",
            persona_run_index=1,
            terminology_mapping_agent_candidate_id=(
                "TMAC-000001"
            ),
        ),
    )
    outcome = TerminologyMappingConsensusOutcome(
        occurrence=occurrence,
        mapping_status="mapped",
        selected_proposals=(proposal,),
        candidate_references=references,
        value_distribution=(),
        consensus_level="unanimous",
        variance_level="low",
        confidence="high",
        total_personas=2,
        supporting_personas=(
            "persona-a",
            "persona-b",
        ),
        dissenting_personas=(),
        omitting_personas=(),
        confirmation_required=True,
        review_required=False,
        recommended_review_mode=(
            "quick_confirmation"
        ),
        persistence_eligible=True,
        confidence_rationale=(
            "Two of two personas agree."
        ),
    )
    result = TerminologyMappingConsensusResult(
        schema_version="1.0.0",
        project_id=information_unit.project_id,
        source_id=information_unit.source_id,
        source_projection_id=(
            information_unit.source_projection_id
        ),
        information_unit_id=(
            information_unit.information_unit_id
        ),
        team_id="terminology-team",
        required_personas=(
            "persona-a",
            "persona-b",
        ),
        persona_run_expectations=(
            ("persona-a", 1),
            ("persona-b", 1),
        ),
        llm_provider="test-provider",
        llm_model="test-model",
        prompt_schema_version="1.0.0",
        ontology_registry_version="1.0.0",
        reference_concept_index_version="1.0.0",
        turing_core_version="1.0.0",
        project_glossary_revision=1,
        outcomes=(outcome,),
        issues=(),
        created_at="2026-08-04T15:01:00Z",
    )

    return create_terminology_mapping_candidate(
        consensus_result=result,
        outcome=outcome,
        terminology_mapping_candidate_id=(
            candidate_id
        ),
        timestamp="2026-08-04T15:02:00Z",
    )


def _framework_candidate(
    information_unit,
    terminology_candidate,
    *,
    candidate_id: str = "FAC-000001",
    framework_version: str = "1.0.0",
):
    basis = create_framework_assignment_basis(
        basis_type="information_unit",
        reference_id=(
            information_unit.information_unit_id
        ),
        reference_version=(
            information_unit.content_fingerprint
        ),
        rationale="Exact Information Unit.",
    )
    proposal = create_framework_assignment_proposal(
        framework_node_id="FW_SYSTEM_REQUIREMENTS",
        assignment_bases=(basis,),
        rationale=(
            "The claim is a System Requirement."
        ),
    )
    references = (
        FrameworkAssignmentAgentCandidateReference(
            persona_id="persona-a",
            agent_id="agent-a",
            persona_run_index=1,
            framework_assignment_agent_candidate_id=(
                "FAAC-000001"
            ),
        ),
        FrameworkAssignmentAgentCandidateReference(
            persona_id="persona-b",
            agent_id="agent-b",
            persona_run_index=1,
            framework_assignment_agent_candidate_id=(
                "FAAC-000001"
            ),
        ),
    )
    outcome = FrameworkAssignmentConsensusOutcome(
        information_unit_id=(
            information_unit.information_unit_id
        ),
        assignment_status="assigned",
        selected_proposals=(proposal,),
        candidate_references=references,
        value_distribution=(),
        consensus_level="unanimous",
        variance_level="low",
        confidence="high",
        total_personas=2,
        supporting_personas=(
            "persona-a",
            "persona-b",
        ),
        dissenting_personas=(),
        omitting_personas=(),
        confirmation_required=True,
        review_required=False,
        recommended_review_mode=(
            "quick_confirmation"
        ),
        persistence_eligible=True,
        confidence_rationale=(
            "Two of two personas agree."
        ),
    )
    result = FrameworkAssignmentConsensusResult(
        schema_version="1.0.0",
        project_id=information_unit.project_id,
        source_id=information_unit.source_id,
        source_projection_id=(
            information_unit.source_projection_id
        ),
        information_unit_id=(
            information_unit.information_unit_id
        ),
        team_id="framework-team",
        required_personas=(
            "persona-a",
            "persona-b",
        ),
        persona_run_expectations=(
            ("persona-a", 1),
            ("persona-b", 1),
        ),
        llm_provider="test-provider",
        llm_model="test-model",
        prompt_schema_version="1.0.0",
        framework_template_id=(
            "TURING_RFLP_FRAMEWORK"
        ),
        framework_template_version=(
            framework_version
        ),
        turing_core_version="1.0.0",
        project_glossary_revision=1,
        terminology_mapping_candidate_ids=(
            terminology_candidate
            .terminology_mapping_candidate_id,
        ),
        outcomes=(outcome,),
        issues=(),
        created_at="2026-08-04T15:03:00Z",
    )

    return create_framework_assignment_candidate(
        consensus_result=result,
        outcome=outcome,
        framework_assignment_candidate_id=(
            candidate_id
        ),
        timestamp="2026-08-04T15:04:00Z",
    )


def _decision(
    *,
    decision_id: str,
    target_type: str,
    target_id: str,
    content_fingerprint: str,
):
    information_unit_target = (
        target_type == "information_unit_publication"
    )

    target = create_human_review_target_snapshot(
        target_type=target_type,
        target_id=target_id,
        target_content_fingerprint=(
            content_fingerprint
        ),
        recommended_review_mode=(
            "quick_confirmation"
        ),
        confirmation_required=True,
        reference_validation_status=(
            "not_applicable"
            if information_unit_target
            else "valid"
        ),
        reference_validation_fingerprint=(
            None
            if information_unit_target
            else "c" * 64
        ),
    )

    return create_human_review_decision(
        project_id=PROJECT_ID,
        human_review_decision_id=decision_id,
        target=target,
        review_mode="quick_confirmation",
        decision="confirm",
        reviewer_identity="moritz",
        rationale="Reviewed.",
        timestamp="2026-08-04T15:05:00Z",
    )


def _clean_scans(
    information_units=(),
    terminology_candidates=(),
    framework_candidates=(),
    decisions=(),
):
    return {
        "information_unit_scan": (
            InformationUnitScanResult(
                information_units=tuple(
                    information_units
                ),
                issues=(),
            )
        ),
        "terminology_mapping_scan": (
            TerminologyMappingScanResult(
                candidates=tuple(
                    terminology_candidates
                ),
                issues=(),
            )
        ),
        "framework_assignment_scan": (
            FrameworkAssignmentScanResult(
                candidates=tuple(
                    framework_candidates
                ),
                issues=(),
            )
        ),
        "human_review_scan": HumanReviewScanResult(
            decisions=tuple(decisions),
            issues=(),
        ),
    }


def test_groups_complete_p4_evidence_for_p9_source() -> None:
    information_unit = _information_unit()
    terminology = _terminology_candidate(
        information_unit
    )
    framework = _framework_candidate(
        information_unit,
        terminology,
    )

    decisions = (
        _decision(
            decision_id="HRD-000001",
            target_type=(
                "information_unit_publication"
            ),
            target_id=(
                information_unit.information_unit_id
            ),
            content_fingerprint=(
                information_unit.content_fingerprint
            ),
        ),
        _decision(
            decision_id="HRD-000002",
            target_type=(
                "terminology_mapping_candidate"
            ),
            target_id=(
                terminology
                .terminology_mapping_candidate_id
            ),
            content_fingerprint=(
                terminology.content_fingerprint
            ),
        ),
        _decision(
            decision_id="HRD-000003",
            target_type=(
                "framework_assignment_candidate"
            ),
            target_id=(
                framework
                .framework_assignment_candidate_id
            ),
            content_fingerprint=(
                framework.content_fingerprint
            ),
        ),
    )

    selected = select_p4_review_evidence_set(
        _p9_evidence(),
        **_clean_scans(
            information_units=(information_unit,),
            terminology_candidates=(terminology,),
            framework_candidates=(framework,),
            decisions=decisions,
        ),
    )

    assert selected.project_id == PROJECT_ID
    assert selected.source_id == SOURCE_ID
    assert len(selected.records) == 1

    record = selected.records[0]

    assert record.information_unit == information_unit
    assert (
        record.terminology_mapping_candidates
        == (terminology,)
    )
    assert (
        record.framework_assignment_candidates
        == (framework,)
    )
    assert record.human_review_decisions == decisions


def test_returns_empty_set_without_matching_information_units() -> None:
    other = _information_unit(
        source_id=OTHER_SOURCE_ID,
        source_projection_id=(
            OTHER_SOURCE_PROJECTION_ID
        ),
    )

    selected = select_p4_review_evidence_set(
        _p9_evidence(),
        **_clean_scans(
            information_units=(other,),
        ),
    )

    assert selected.records == ()
    assert selected.information_units == ()


@pytest.mark.parametrize(
    "scan_name",
    (
        "information_unit_scan",
        "terminology_mapping_scan",
        "framework_assignment_scan",
        "human_review_scan",
    ),
)
def test_rejects_scan_issues(
    scan_name: str,
) -> None:
    scans = _clean_scans()

    if scan_name == "information_unit_scan":
        scans[scan_name] = InformationUnitScanResult(
            issues=(
                InformationUnitIssue(
                    project_id=PROJECT_ID,
                    code="invalid_information_unit",
                    message="Invalid.",
                    path=Path("invalid-iu"),
                ),
            )
        )
    elif scan_name == "terminology_mapping_scan":
        scans[scan_name] = TerminologyMappingScanResult(
            issues=(
                TerminologyMappingIssue(
                    project_id=PROJECT_ID,
                    code="invalid_mapping_candidate",
                    message="Invalid.",
                    issue_level="blocking",
                    path=Path("invalid-tmc"),
                ),
            )
        )
    elif scan_name == "framework_assignment_scan":
        scans[scan_name] = FrameworkAssignmentScanResult(
            issues=(
                FrameworkAssignmentIssue(
                    project_id=PROJECT_ID,
                    code="invalid_mapping_candidate",
                    message="Invalid.",
                    issue_level="blocking",
                    path=Path("invalid-fac"),
                ),
            )
        )
    else:
        scans[scan_name] = HumanReviewScanResult(
            issues=(
                HumanReviewIssue(
                    project_id=PROJECT_ID,
                    code="invalid_review_decision",
                    message="Invalid.",
                    issue_level="blocking",
                    path=Path("invalid-hrd"),
                ),
            )
        )

    with pytest.raises(
        ReviewIntegrityError,
        match="scan contains",
    ):
        select_p4_review_evidence_set(
            _p9_evidence(),
            **scans,
        )


def test_rejects_cross_project_information_unit() -> None:
    information_unit = _information_unit(
        project_id=OTHER_PROJECT_ID,
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="selected Project",
    ):
        select_p4_review_evidence_set(
            _p9_evidence(),
            **_clean_scans(
                information_units=(
                    information_unit,
                ),
            ),
        )


def test_rejects_framework_template_mismatch() -> None:
    information_unit = _information_unit()
    terminology = _terminology_candidate(
        information_unit
    )
    framework = _framework_candidate(
        information_unit,
        terminology,
        framework_version="2.0.0",
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="framework template",
    ):
        select_p4_review_evidence_set(
            _p9_evidence(),
            **_clean_scans(
                information_units=(
                    information_unit,
                ),
                terminology_candidates=(
                    terminology,
                ),
                framework_candidates=(
                    framework,
                ),
            ),
        )


def test_rejects_missing_terminology_reference() -> None:
    information_unit = _information_unit()
    terminology = _terminology_candidate(
        information_unit
    )
    framework = _framework_candidate(
        information_unit,
        terminology,
    )

    with pytest.raises(
        ReviewReferenceError,
        match="unavailable Terminology",
    ):
        select_p4_review_evidence_set(
            _p9_evidence(),
            **_clean_scans(
                information_units=(
                    information_unit,
                ),
                framework_candidates=(
                    framework,
                ),
            ),
        )


def test_rejects_decision_for_missing_target() -> None:
    decision = _decision(
        decision_id="HRD-000001",
        target_type="information_unit_publication",
        target_id="IU-000999",
        content_fingerprint="d" * 64,
    )

    with pytest.raises(
        ReviewReferenceError,
        match="unavailable target",
    ):
        select_p4_review_evidence_set(
            _p9_evidence(),
            **_clean_scans(
                decisions=(decision,),
            ),
        )


def test_rejects_stale_decision_fingerprint() -> None:
    information_unit = _information_unit()
    decision = _decision(
        decision_id="HRD-000001",
        target_type="information_unit_publication",
        target_id=(
            information_unit.information_unit_id
        ),
        content_fingerprint="d" * 64,
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="immutable target fingerprint",
    ):
        select_p4_review_evidence_set(
            _p9_evidence(),
            **_clean_scans(
                information_units=(
                    information_unit,
                ),
                decisions=(decision,),
            ),
        )


def test_record_order_is_deterministic() -> None:
    second = _information_unit(
        information_unit_id="IU-000002",
        statement=(
            "The pump shall preserve model traceability."
        ),
    )
    first = _information_unit(
        information_unit_id="IU-000001",
    )

    selected = select_p4_review_evidence_set(
        _p9_evidence(),
        **_clean_scans(
            information_units=(
                second,
                first,
            ),
        ),
    )

    assert tuple(
        record.information_unit.information_unit_id
        for record in selected.records
    ) == (
        "IU-000001",
        "IU-000002",
    )
