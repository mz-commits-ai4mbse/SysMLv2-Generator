from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from modules.framework import load_framework_template
from modules.framework_assignment.reference_validation import (
    FrameworkAssignmentReferenceValidationResult,
)
from modules.framework_assignment.types import (
    FrameworkAssignmentBasis,
    FrameworkAssignmentCandidate,
    FrameworkAssignmentIssue,
    FrameworkAssignmentProposal,
)
from modules.human_review.types import (
    HumanReviewDecision,
    HumanReviewTargetSnapshot,
)
from modules.information_units.types import (
    InformationUnit,
    InformationUnitExtractionProvenance,
)
from modules.project_coverage.errors import (
    CoverageIntegrityError,
    CoverageReferenceError,
    CoverageValidationError,
)
from modules.project_coverage.evidence import (
    calculate_framework_assignment_reference_validation_fingerprint,
    derive_framework_assignment_coverage_evidence,
    resolve_latest_exact_framework_assignment_review,
)
from modules.project_processing.types import (
    ProcessingArtifactLifecycle,
    ProcessingArtifactReference,
    SourceProcessingSummary,
)
from modules.project_sources.types import SourceManifest


PROJECT_ID = "318604"
OTHER_PROJECT_ID = "481516"
SOURCE_ID = "SRC-000001"
IU_ID = "IU-000001"
FAC_ID = "FAC-000001"
NODE_ID = "FW_STAKEHOLDER_USER_NEEDS"
SHA_A = "a" * 64
SHA_B = "b" * 64


def template():
    return load_framework_template(
        Path("context/frameworks/turing_rflp_framework.json")
    )


def source(
    *,
    project_id: str = PROJECT_ID,
    source_id: str = SOURCE_ID,
    role: str = "engineering_source",
) -> SourceManifest:
    return SourceManifest(
        schema_version="1.0.0",
        project_id=project_id,
        source_id=source_id,
        source_role=role,
        original_filename="source.txt",
        stored_filename="content.txt",
        media_type="text/plain",
        size_bytes=1,
        sha256=SHA_A,
        registered_at="2026-07-27T08:00:00Z",
        updated_at="2026-07-27T08:00:00Z",
    )


def summary(
    *,
    project_id: str = PROJECT_ID,
    source_id: str = SOURCE_ID,
    disposition: str = "in_scope",
) -> SourceProcessingSummary:
    return SourceProcessingSummary(
        project_id=project_id,
        source_id=source_id,
        processing_disposition=disposition,
        current_processing_run_id="RUN-000001",
        run_state="completed",
        processing_stage="publication",
        latest_attempt_id="ATT-000001",
        blocking_issue_codes=(),
        failure_issue_codes=(),
        pending_review=False,
        superseded_run_ids=(),
        invalidated_artifact_count=0,
    )


def unit(
    *,
    project_id: str = PROJECT_ID,
    source_id: str = SOURCE_ID,
    information_unit_id: str = IU_ID,
    projection_id: str = "SP-000001",
) -> InformationUnit:
    return InformationUnit(
        schema_version="1.0.0",
        project_id=project_id,
        information_unit_id=information_unit_id,
        source_id=source_id,
        source_projection_id=projection_id,
        source_anchors=(),
        source_excerpt="Need text",
        interpreted_statement="The user needs a function.",
        information_type="user_need",
        statement_modality="descriptive",
        epistemic_class="explicit",
        supporting_information_unit_ids=(),
        derivation_rationale=None,
        missing_evidence=None,
        extraction_provenance=InformationUnitExtractionProvenance(
            team_id="TEAM",
            persona_ids=("systems_engineer",),
            llm_provider="openai",
            llm_model="test-model",
            prompt_schema_version="1.0.0",
            consensus_report_id="CR-000001",
        ),
        confidence="high",
        confidence_rationale="Explicit statement.",
        content_fingerprint=SHA_B,
        created_at="2026-07-27T08:01:00Z",
    )


def proposal(node_id: str = NODE_ID) -> FrameworkAssignmentProposal:
    return FrameworkAssignmentProposal(
        framework_node_id=node_id,
        assignment_bases=(
            FrameworkAssignmentBasis(
                basis_type="information_unit",
                reference_id=IU_ID,
                reference_version=SHA_B,
                rationale="Exact Information Unit.",
            ),
        ),
        rationale="Maps to the selected framework node.",
    )


def candidate(
    *,
    project_id: str = PROJECT_ID,
    source_id: str = SOURCE_ID,
    information_unit_id: str = IU_ID,
    candidate_id: str = FAC_ID,
    status: str = "assigned",
    proposals: tuple[FrameworkAssignmentProposal, ...] | None = None,
    template_id: str = "TURING_RFLP_FRAMEWORK",
    template_version: str = "1.0.0",
    projection_id: str = "SP-000001",
    fingerprint: str = SHA_A,
) -> FrameworkAssignmentCandidate:
    if proposals is None:
        proposals = () if status == "unassigned" else (proposal(),)
    return FrameworkAssignmentCandidate(
        schema_version="1.0.0",
        project_id=project_id,
        source_id=source_id,
        source_projection_id=projection_id,
        information_unit_id=information_unit_id,
        framework_assignment_candidate_id=candidate_id,
        assignment_status=status,
        proposals=proposals,
        candidate_references=(),
        team_id="TEAM",
        required_personas=("systems_engineer",),
        llm_provider="openai",
        llm_model="test-model",
        prompt_schema_version="1.0.0",
        framework_template_id=template_id,
        framework_template_version=template_version,
        turing_core_version="1.0.0",
        project_glossary_revision=0,
        terminology_mapping_candidate_ids=(),
        consensus_level="unanimous",
        variance_level="low",
        confidence="high",
        confidence_rationale="Agreement.",
        confirmation_required=True,
        review_required=False,
        recommended_review_mode="quick_confirmation",
        content_fingerprint=fingerprint,
        created_at="2026-07-27T08:02:00Z",
    )


def validation(
    *,
    project_id: str = PROJECT_ID,
    candidate_id: str = FAC_ID,
    valid: bool = True,
    issue_code: str = "invalid_reference",
) -> FrameworkAssignmentReferenceValidationResult:
    issues = ()
    if not valid:
        issues = (
            FrameworkAssignmentIssue(
                project_id=project_id,
                code=issue_code,
                message="Reference is invalid.",
                issue_level="blocking",
                information_unit_id=IU_ID,
                framework_assignment_candidate_id=candidate_id,
            ),
        )
    return FrameworkAssignmentReferenceValidationResult(
        project_id=project_id,
        framework_assignment_candidate_id=candidate_id,
        checked_proposal_count=1,
        references_valid=valid,
        issues=issues,
    )


def decision(
    selected_candidate: FrameworkAssignmentCandidate,
    selected_validation: FrameworkAssignmentReferenceValidationResult,
    *,
    decision_id: str = "HRD-000001",
    value: str = "confirm",
    timestamp: str = "2026-07-27T08:03:00Z",
    content_fingerprint: str | None = None,
    validation_fingerprint: str | None = None,
    validation_status: str | None = None,
    project_id: str = PROJECT_ID,
    target_type: str = "framework_assignment_candidate",
    target_id: str | None = None,
) -> HumanReviewDecision:
    expected_validation_fingerprint = (
        calculate_framework_assignment_reference_validation_fingerprint(
            selected_validation
        )
    )
    return HumanReviewDecision(
        schema_version="1.0.0",
        project_id=project_id,
        human_review_decision_id=decision_id,
        target=HumanReviewTargetSnapshot(
            target_type=target_type,
            target_id=(
                selected_candidate.framework_assignment_candidate_id
                if target_id is None
                else target_id
            ),
            target_content_fingerprint=(
                selected_candidate.content_fingerprint
                if content_fingerprint is None
                else content_fingerprint
            ),
            recommended_review_mode="quick_confirmation",
            confirmation_required=True,
            reference_validation_status=(
                "valid" if selected_validation.references_valid else "invalid"
                if validation_status is None
                else validation_status
            ),
            reference_validation_fingerprint=(
                expected_validation_fingerprint
                if validation_fingerprint is None
                else validation_fingerprint
            ),
        ),
        review_mode="quick_confirmation",
        decision=value,
        reviewer_identity="moritz",
        rationale=None,
        decided_at=timestamp,
        decision_fingerprint="c" * 64,
    )


def lifecycle(
    *,
    state: str,
    candidate_id: str = FAC_ID,
    fingerprint: str = SHA_A,
    path: str = "semantics/framework_assignments/FAC-000001.json",
    artifact_type: str = "framework_assignment_candidate",
) -> ProcessingArtifactLifecycle:
    return ProcessingArtifactLifecycle(
        artifact_reference=ProcessingArtifactReference(
            artifact_type=artifact_type,
            artifact_id=candidate_id,
            content_fingerprint=fingerprint,
            repository_relative_path=path,
        ),
        lifecycle_state=state,
        caused_by_event_id="EVT-000001",
    )


def derive(
    *,
    sources: tuple[SourceManifest, ...] | None = None,
    summaries: tuple[SourceProcessingSummary, ...] | None = None,
    units: tuple[InformationUnit, ...] | None = None,
    candidates: tuple[FrameworkAssignmentCandidate, ...] | None = None,
    validations: tuple[FrameworkAssignmentReferenceValidationResult, ...] | None = None,
    decisions: tuple[HumanReviewDecision, ...] = (),
    lifecycles: tuple[ProcessingArtifactLifecycle, ...] = (),
):
    return derive_framework_assignment_coverage_evidence(
        PROJECT_ID,
        framework_template=template(),
        source_manifests=(source(),) if sources is None else sources,
        source_processing_summaries=(summary(),) if summaries is None else summaries,
        information_units=(unit(),) if units is None else units,
        candidates=(candidate(),) if candidates is None else candidates,
        reference_validation_results=(validation(),) if validations is None else validations,
        human_review_decisions=decisions,
        artifact_lifecycles=lifecycles,
    )


def test_validation_fingerprint_is_deterministic() -> None:
    assert calculate_framework_assignment_reference_validation_fingerprint(
        validation()
    ) == calculate_framework_assignment_reference_validation_fingerprint(
        validation()
    )


def test_validation_fingerprint_is_issue_order_independent() -> None:
    first = FrameworkAssignmentIssue(
        project_id=PROJECT_ID,
        code="a",
        message="A",
        issue_level="blocking",
    )
    second = replace(first, code="b", message="B")
    left = replace(validation(valid=False), issues=(first, second))
    right = replace(validation(valid=False), issues=(second, first))
    assert calculate_framework_assignment_reference_validation_fingerprint(
        left
    ) == calculate_framework_assignment_reference_validation_fingerprint(right)


def test_validation_fingerprint_changes_with_result() -> None:
    assert calculate_framework_assignment_reference_validation_fingerprint(
        validation()
    ) != calculate_framework_assignment_reference_validation_fingerprint(
        validation(valid=False)
    )


def test_reference_valid_result_cannot_have_blocking_issue() -> None:
    invalid = replace(validation(valid=False), references_valid=True)
    with pytest.raises(CoverageIntegrityError):
        calculate_framework_assignment_reference_validation_fingerprint(invalid)


def test_reference_invalid_result_requires_blocking_issue() -> None:
    invalid = replace(validation(), references_valid=False)
    with pytest.raises(CoverageIntegrityError):
        calculate_framework_assignment_reference_validation_fingerprint(invalid)


def test_review_resolver_returns_none_without_decision() -> None:
    assert resolve_latest_exact_framework_assignment_review(
        candidate(), validation(), ()
    ) is None


def test_review_resolver_returns_exact_decision() -> None:
    item = decision(candidate(), validation())
    assert resolve_latest_exact_framework_assignment_review(
        candidate(), validation(), (item,)
    ) == item


def test_review_resolver_uses_latest_exact_decision() -> None:
    first = decision(candidate(), validation(), value="confirm")
    second = decision(
        candidate(),
        validation(),
        decision_id="HRD-000002",
        value="reject",
        timestamp="2026-07-27T09:00:00Z",
    )
    assert resolve_latest_exact_framework_assignment_review(
        candidate(), validation(), (second, first)
    ) == second


def test_review_resolver_ignores_stale_content() -> None:
    stale = decision(candidate(), validation(), content_fingerprint=SHA_B)
    assert resolve_latest_exact_framework_assignment_review(
        candidate(), validation(), (stale,)
    ) is None


def test_review_resolver_ignores_stale_validation() -> None:
    stale = decision(
        candidate(), validation(), validation_fingerprint="d" * 64
    )
    assert resolve_latest_exact_framework_assignment_review(
        candidate(), validation(), (stale,)
    ) is None


def test_review_resolver_ignores_other_target_type() -> None:
    other = decision(
        candidate(),
        validation(),
        target_type="information_unit_publication",
        target_id=IU_ID,
    )
    assert resolve_latest_exact_framework_assignment_review(
        candidate(), validation(), (other,)
    ) is None


def test_review_resolver_rejects_mixed_project() -> None:
    other = decision(
        candidate(), validation(), project_id=OTHER_PROJECT_ID
    )
    with pytest.raises(CoverageReferenceError):
        resolve_latest_exact_framework_assignment_review(
            candidate(), validation(), (other,)
        )


def test_review_resolver_rejects_duplicate_decision_ids() -> None:
    item = decision(candidate(), validation())
    with pytest.raises(CoverageIntegrityError):
        resolve_latest_exact_framework_assignment_review(
            candidate(), validation(), (item, item)
        )


def test_review_resolver_rejects_validation_candidate_mismatch() -> None:
    with pytest.raises(CoverageReferenceError):
        resolve_latest_exact_framework_assignment_review(
            candidate(), validation(candidate_id="FAC-000002"), ()
        )


def test_assigned_candidate_is_eligible_unreviewed() -> None:
    item = derive()[0]
    assert item.evidence_state == "eligible_unreviewed"
    assert item.framework_node_ids == (NODE_ID,)
    assert item.attention_required is False


def test_exact_confirmation_creates_confirmed_evidence() -> None:
    selected_candidate = candidate()
    selected_validation = validation()
    item = derive(
        candidates=(selected_candidate,),
        validations=(selected_validation,),
        decisions=(decision(selected_candidate, selected_validation),),
    )[0]
    assert item.evidence_state == "eligible_confirmed"
    assert item.human_review_decision_id == "HRD-000001"


def test_exact_rejection_excludes_candidate() -> None:
    selected_candidate = candidate()
    selected_validation = validation()
    item = derive(
        candidates=(selected_candidate,),
        validations=(selected_validation,),
        decisions=(
            decision(selected_candidate, selected_validation, value="reject"),
        ),
    )[0]
    assert item.evidence_state == "excluded_rejected"
    assert item.attention_required is False


def test_request_changes_excludes_and_requires_attention() -> None:
    selected_candidate = candidate()
    selected_validation = validation()
    item = derive(
        candidates=(selected_candidate,),
        validations=(selected_validation,),
        decisions=(
            decision(
                selected_candidate,
                selected_validation,
                value="request_changes",
            ),
        ),
    )[0]
    assert item.evidence_state == "excluded_request_changes"
    assert item.attention_required is True


def test_stale_review_keeps_unreviewed_coverage_with_attention() -> None:
    selected_candidate = candidate()
    selected_validation = validation()
    stale = decision(
        selected_candidate,
        selected_validation,
        content_fingerprint=SHA_B,
    )
    item = derive(decisions=(stale,))[0]
    assert item.evidence_state == "eligible_unreviewed"
    assert item.attention_required is True
    assert item.issue_codes == ("stale_human_review_binding",)


@pytest.mark.parametrize(
    ("role", "disposition"),
    [
        ("context_only", "context_only"),
        ("engineering_source", "out_of_scope"),
        ("context_only", "in_scope"),
    ],
)
def test_ineligible_source_cannot_create_coverage(role, disposition) -> None:
    item = derive(
        sources=(source(role=role),),
        summaries=(summary(disposition=disposition),),
    )[0]
    assert item.evidence_state == "excluded_source"


@pytest.mark.parametrize(
    ("status", "expected", "attention"),
    [
        ("unassigned", "excluded_unassigned", False),
        ("ambiguous", "excluded_ambiguous", True),
        ("conflict", "excluded_conflict", True),
    ],
)
def test_non_covering_assignment_states(status, expected, attention) -> None:
    selected = candidate(status=status)
    item = derive(candidates=(selected,))[0]
    assert item.evidence_state == expected
    assert item.attention_required is attention


@pytest.mark.parametrize("state", ["invalidated", "superseded"])
def test_non_active_candidate_is_excluded(state) -> None:
    item = derive(lifecycles=(lifecycle(state=state),))[0]
    assert item.evidence_state == "excluded_invalidated"
    assert item.attention_required is True


def test_active_lifecycle_does_not_exclude_candidate() -> None:
    item = derive(lifecycles=(lifecycle(state="active"),))[0]
    assert item.evidence_state == "eligible_unreviewed"


def test_invalid_reference_result_excludes_candidate() -> None:
    item = derive(validations=(validation(valid=False),))[0]
    assert item.evidence_state == "excluded_invalid_reference"
    assert "invalid_reference" in item.issue_codes


def test_missing_reference_result_excludes_candidate() -> None:
    item = derive(validations=())[0]
    assert item.evidence_state == "excluded_invalid_reference"
    assert item.issue_codes == ("missing_reference_validation",)


def test_unknown_source_excludes_candidate() -> None:
    item = derive(sources=(), summaries=())[0]
    assert item.evidence_state == "excluded_invalid_reference"
    assert "unknown_source" in item.issue_codes


def test_unknown_information_unit_excludes_candidate() -> None:
    item = derive(units=())[0]
    assert item.evidence_state == "excluded_invalid_reference"


def test_missing_source_summary_excludes_candidate() -> None:
    item = derive(summaries=())[0]
    assert item.evidence_state == "excluded_invalid_reference"


def test_information_unit_source_mismatch_excludes_candidate() -> None:
    item = derive(units=(unit(source_id="SRC-000002"),))[0]
    assert item.evidence_state == "excluded_invalid_reference"
    assert "candidate_information_unit_source_mismatch" in item.issue_codes


def test_information_unit_projection_mismatch_excludes_candidate() -> None:
    item = derive(units=(unit(projection_id="SP-000002"),))[0]
    assert item.evidence_state == "excluded_invalid_reference"


def test_framework_template_id_mismatch_excludes_candidate() -> None:
    item = derive(candidates=(candidate(template_id="OTHER_TEMPLATE"),))[0]
    assert item.evidence_state == "excluded_invalid_reference"


def test_framework_template_version_mismatch_excludes_candidate() -> None:
    item = derive(candidates=(candidate(template_version="2.0.0"),))[0]
    assert item.evidence_state == "excluded_invalid_reference"


def test_unknown_framework_node_excludes_candidate() -> None:
    selected = candidate(proposals=(proposal("FW_UNKNOWN"),))
    item = derive(candidates=(selected,))[0]
    assert item.evidence_state == "excluded_invalid_reference"


def test_proposal_node_ids_are_unique_and_sorted() -> None:
    selected = candidate(
        proposals=(
            proposal("FW_SYSTEM_FUNCTIONAL"),
            proposal(NODE_ID),
            proposal(NODE_ID),
        )
    )
    selected_validation = replace(validation(), checked_proposal_count=3)
    item = derive(
        candidates=(selected,), validations=(selected_validation,)
    )[0]
    assert item.framework_node_ids == (
        NODE_ID,
        "FW_SYSTEM_FUNCTIONAL",
    )


def test_evidence_is_sorted_by_candidate_id() -> None:
    second = candidate(candidate_id="FAC-000002", fingerprint=SHA_B)
    second_validation = validation(candidate_id="FAC-000002")
    result = derive(
        candidates=(second, candidate()),
        validations=(second_validation, validation()),
    )
    assert tuple(
        item.framework_assignment_candidate_id for item in result
    ) == ("FAC-000001", "FAC-000002")


def test_duplicate_candidate_identity_is_rejected() -> None:
    with pytest.raises(CoverageIntegrityError):
        derive(candidates=(candidate(), candidate()))


def test_duplicate_source_identity_is_rejected() -> None:
    with pytest.raises(CoverageIntegrityError):
        derive(sources=(source(), source()))


def test_unknown_summary_source_is_rejected() -> None:
    with pytest.raises(CoverageReferenceError):
        derive(summaries=(summary(source_id="SRC-000002"),))


def test_unknown_validation_candidate_is_rejected() -> None:
    with pytest.raises(CoverageReferenceError):
        derive(
            validations=(
                validation(),
                validation(candidate_id="FAC-000002"),
            )
        )


def test_mixed_project_source_is_rejected() -> None:
    with pytest.raises(CoverageReferenceError):
        derive(sources=(source(project_id=OTHER_PROJECT_ID),))


def test_mixed_project_decision_is_rejected() -> None:
    other = decision(candidate(), validation(), project_id=OTHER_PROJECT_ID)
    with pytest.raises(CoverageReferenceError):
        derive(decisions=(other,))


def test_collections_must_be_tuples() -> None:
    with pytest.raises(CoverageValidationError):
        derive_framework_assignment_coverage_evidence(
            PROJECT_ID,
            framework_template=template(),
            source_manifests=[source()],
            source_processing_summaries=(summary(),),
            information_units=(unit(),),
            candidates=(candidate(),),
            reference_validation_results=(validation(),),
            human_review_decisions=(),
        )


def test_invalid_framework_template_is_rejected() -> None:
    with pytest.raises(CoverageValidationError):
        derive_framework_assignment_coverage_evidence(
            PROJECT_ID,
            framework_template={},
            source_manifests=(source(),),
            source_processing_summaries=(summary(),),
            information_units=(unit(),),
            candidates=(candidate(),),
            reference_validation_results=(validation(),),
            human_review_decisions=(),
        )


def test_non_candidate_artifact_lifecycle_is_ignored() -> None:
    item = derive(
        lifecycles=(
            lifecycle(state="invalidated", artifact_type="information_unit"),
        )
    )[0]
    assert item.evidence_state == "eligible_unreviewed"


def test_inconsistent_artifact_identity_is_rejected() -> None:
    with pytest.raises(CoverageIntegrityError):
        derive(
            lifecycles=(
                lifecycle(state="active"),
                lifecycle(state="active", fingerprint=SHA_B),
            )
        )


def test_multiple_artifact_lifecycle_states_are_rejected() -> None:
    with pytest.raises(CoverageIntegrityError):
        derive(
            lifecycles=(
                lifecycle(state="active"),
                lifecycle(state="invalidated"),
            )
        )