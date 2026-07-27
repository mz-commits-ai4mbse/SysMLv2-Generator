from __future__ import annotations

from dataclasses import replace
import re

import pytest

import modules.project_coverage as public_api
from modules.framework_assignment.reference_validation import (
    FrameworkAssignmentReferenceValidationResult,
)
from modules.framework_assignment.types import (
    FrameworkAssignmentAgentCandidateReference,
    FrameworkAssignmentBasis,
    FrameworkAssignmentCandidate,
    FrameworkAssignmentProposal,
)
from modules.human_review.types import (
    HumanReviewDecision,
    HumanReviewTargetSnapshot,
)
from modules.information_units.types import (
    InformationUnit,
    InformationUnitExtractionProvenance,
    InformationUnitSourceAnchor,
)
from modules.project_coverage.errors import (
    CoverageAssessmentError,
    CoverageIntegrityError,
    CoverageProfileError,
    CoverageReferenceError,
    CoverageValidationError,
)
from modules.project_coverage.evidence import (
    calculate_framework_assignment_reference_validation_fingerprint,
)
from modules.project_coverage.profile import (
    parse_preliminary_support_profile,
)
from modules.project_coverage.service import (
    APPROVED_READINESS_AVAILABLE_FROM_PHASE,
    APPROVED_READINESS_STATUS,
    PROJECT_COVERAGE_ASSESSMENT_ALGORITHM_ID,
    PROJECT_COVERAGE_ASSESSMENT_ALGORITHM_VERSION,
    ProjectCoverageInputBundle,
    ProjectCoverageService,
    assemble_project_coverage_assessment,
    calculate_project_coverage_assessment_fingerprint,
)
from modules.project_coverage.types import CoverageIssue
from modules.project_processing.types import (
    ProcessingArtifactLifecycle,
    ProcessingArtifactReference,
    SourceProcessingSummary,
)
from modules.project_sources.types import SourceManifest


PROJECT_ID = "318604"
SOURCE_ID = "SRC-000001"
UNIT_ID = "IU-000001"
CANDIDATE_ID = "FAC-000001"
CONTENT_HASH = "a" * 64
SOURCE_HASH = "b" * 64
DECISION_HASH = "c" * 64

STAKEHOLDER_NODES = (
    "FW_STAKEHOLDER_STAKEHOLDERS",
    "FW_STAKEHOLDER_USER_NEEDS",
    "FW_STAKEHOLDER_STAKEHOLDER_REQUIREMENTS",
    "FW_STAKEHOLDER_USE_CASES",
)
SYSTEM_NODES = (
    "FW_SYSTEM_REQUIREMENTS",
    "FW_SYSTEM_FUNCTIONAL",
    "FW_SYSTEM_LOGICAL",
    "FW_SYSTEM_PHYSICAL",
)
SUBSYSTEM_NODES = (
    "FW_SUBSYSTEM_REQUIREMENTS",
    "FW_SUBSYSTEM_FUNCTIONAL",
    "FW_SUBSYSTEM_LOGICAL",
    "FW_SUBSYSTEM_PHYSICAL",
)
ALL_NODES = STAKEHOLDER_NODES + SYSTEM_NODES + SUBSYSTEM_NODES


def framework_template() -> dict[str, object]:
    levels = (
        ("FW_LEVEL_STAKEHOLDER", "stakeholder_level", "Stakeholder Level", 1),
        ("FW_LEVEL_SYSTEM", "system_level", "System Level", 2),
        ("FW_LEVEL_SUBSYSTEM", "subsystem_level", "Subsystem Level", 3),
    )
    names = {
        "FW_STAKEHOLDER_STAKEHOLDERS": ("stakeholder.stakeholders", "Stakeholders"),
        "FW_STAKEHOLDER_USER_NEEDS": ("stakeholder.user_needs", "User Needs"),
        "FW_STAKEHOLDER_STAKEHOLDER_REQUIREMENTS": (
            "stakeholder.stakeholder_requirements",
            "Stakeholder Requirements",
        ),
        "FW_STAKEHOLDER_USE_CASES": ("stakeholder.use_cases", "Use Cases"),
        "FW_SYSTEM_REQUIREMENTS": ("system.requirements", "Requirements"),
        "FW_SYSTEM_FUNCTIONAL": ("system.functional", "Functional"),
        "FW_SYSTEM_LOGICAL": ("system.logical", "Logical"),
        "FW_SYSTEM_PHYSICAL": ("system.physical", "Physical"),
        "FW_SUBSYSTEM_REQUIREMENTS": ("subsystem.requirements", "Requirements"),
        "FW_SUBSYSTEM_FUNCTIONAL": ("subsystem.functional", "Functional"),
        "FW_SUBSYSTEM_LOGICAL": ("subsystem.logical", "Logical"),
        "FW_SUBSYSTEM_PHYSICAL": ("subsystem.physical", "Physical"),
    }
    parent = {}
    for node in STAKEHOLDER_NODES:
        parent[node] = "FW_LEVEL_STAKEHOLDER"
    for node in SYSTEM_NODES:
        parent[node] = "FW_LEVEL_SYSTEM"
    for node in SUBSYSTEM_NODES:
        parent[node] = "FW_LEVEL_SUBSYSTEM"

    nodes = [
        {
            "node_id": node_id,
            "mapping_key": mapping_key,
            "name": name,
            "node_type": "level",
            "parent_node_id": None,
            "mapping_target": False,
            "order": order,
        }
        for node_id, mapping_key, name, order in levels
    ]
    sibling_orders = {
        **{node: index + 1 for index, node in enumerate(STAKEHOLDER_NODES)},
        **{node: index + 1 for index, node in enumerate(SYSTEM_NODES)},
        **{node: index + 1 for index, node in enumerate(SUBSYSTEM_NODES)},
    }
    nodes.extend(
        {
            "node_id": node_id,
            "mapping_key": names[node_id][0],
            "name": names[node_id][1],
            "node_type": "framework_node",
            "parent_node_id": parent[node_id],
            "mapping_target": True,
            "order": sibling_orders[node_id],
        }
        for node_id in ALL_NODES
    )
    return {
        "schema_version": "1.0.0",
        "template_id": "TURING_RFLP_FRAMEWORK",
        "template_version": "1.0.0",
        "name": "Turing Framework",
        "status": "active",
        "authority": {
            "definition_basis": "test",
            "engineering_authority": "CATIA",
            "shadow_model_rule": "no override",
            "non_normative_references": [],
        },
        "information_unit_mapping": {
            "eligible_source_roles": ["engineering_source"],
            "cardinality_per_information_unit": "zero_to_many",
            "target_reference_field": "node_id",
            "unknown_target_behavior": "reject",
            "context_only_mapping_allowed": False,
        },
        "assessment_semantics": {
            "preliminary_coverage": {
                "label": "Preliminary Coverage",
                "eligible_source_roles": ["engineering_source"],
                "requires_human_approval": False,
                "phase_p_available": True,
                "excluded_source_roles": ["context_only"],
            },
            "approved_readiness": {
                "label": "Approved Readiness",
                "eligible_source_roles": ["engineering_source"],
                "requires_human_approval": True,
                "phase_p_available": False,
                "available_from_phase": "G",
                "excluded_source_roles": ["context_only"],
            },
        },
        "nodes": nodes,
    }


def support_profile():
    template = framework_template()
    return parse_preliminary_support_profile(
        {
            "schema_version": "1.0.0",
            "profile_id": "TURING_PRELIMINARY_SUPPORT_PROFILE",
            "profile_version": "1.0.0",
            "name": "Test Support Profile",
            "status": "active",
            "framework_template_id": template["template_id"],
            "framework_template_version": template["template_version"],
            "support_targets": [
                {
                    "support_target_id": "SUPPORT_STAKEHOLDER_MODEL",
                    "name": "Stakeholder Model",
                    "support_target_type": "model",
                    "order": 1,
                    "required_framework_node_ids": list(STAKEHOLDER_NODES),
                    "required_support_target_ids": [],
                },
                {
                    "support_target_id": "SUPPORT_SYSTEM_MODEL",
                    "name": "System Model",
                    "support_target_type": "model",
                    "order": 2,
                    "required_framework_node_ids": list(SYSTEM_NODES),
                    "required_support_target_ids": [
                        "SUPPORT_STAKEHOLDER_MODEL"
                    ],
                },
                {
                    "support_target_id": "SUPPORT_SUBSYSTEM_MODEL",
                    "name": "Subsystem Model",
                    "support_target_type": "submodel",
                    "order": 3,
                    "required_framework_node_ids": list(SUBSYSTEM_NODES),
                    "required_support_target_ids": [
                        "SUPPORT_SYSTEM_MODEL"
                    ],
                },
            ],
        },
        framework_template=template,
    )


def source() -> SourceManifest:
    return SourceManifest(
        schema_version="1.0.0",
        project_id=PROJECT_ID,
        source_id=SOURCE_ID,
        source_role="engineering_source",
        original_filename="source.md",
        stored_filename="content.md",
        media_type="text/markdown",
        size_bytes=10,
        sha256=SOURCE_HASH,
        registered_at="2026-07-27T08:00:00Z",
        updated_at="2026-07-27T08:00:00Z",
    )


def summary() -> SourceProcessingSummary:
    return SourceProcessingSummary(
        project_id=PROJECT_ID,
        source_id=SOURCE_ID,
        processing_disposition="in_scope",
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


def unit() -> InformationUnit:
    return InformationUnit(
        schema_version="1.0.0",
        project_id=PROJECT_ID,
        information_unit_id=UNIT_ID,
        source_id=SOURCE_ID,
        source_projection_id="PRJ-000001",
        source_anchors=(
            InformationUnitSourceAnchor("SEG-000001", 0, 10),
        ),
        source_excerpt="Stakeholder",
        interpreted_statement="A stakeholder exists.",
        information_type="stakeholder",
        statement_modality="descriptive",
        epistemic_class="explicit",
        supporting_information_unit_ids=(),
        derivation_rationale=None,
        missing_evidence=None,
        extraction_provenance=InformationUnitExtractionProvenance(
            team_id="TEAM",
            persona_ids=("systems_engineer",),
            llm_provider="openai",
            llm_model="test",
            prompt_schema_version="1.0.0",
            consensus_report_id="CR-000001",
        ),
        confidence="high",
        confidence_rationale="explicit",
        content_fingerprint=CONTENT_HASH,
        created_at="2026-07-27T08:00:00Z",
    )


def candidate(
    node_id: str = STAKEHOLDER_NODES[0],
) -> FrameworkAssignmentCandidate:
    proposal = FrameworkAssignmentProposal(
        framework_node_id=node_id,
        assignment_bases=(
            FrameworkAssignmentBasis(
                basis_type="information_unit",
                reference_id=UNIT_ID,
                reference_version=CONTENT_HASH,
                rationale="exact",
            ),
        ),
        rationale="mapped",
    )
    return FrameworkAssignmentCandidate(
        schema_version="1.0.0",
        project_id=PROJECT_ID,
        source_id=SOURCE_ID,
        source_projection_id="PRJ-000001",
        information_unit_id=UNIT_ID,
        framework_assignment_candidate_id=CANDIDATE_ID,
        assignment_status="assigned",
        proposals=(proposal,),
        candidate_references=(
            FrameworkAssignmentAgentCandidateReference(
                persona_id="systems_engineer",
                agent_id="agent",
                persona_run_index=1,
                framework_assignment_agent_candidate_id="FAAC-000001",
            ),
        ),
        team_id="TEAM",
        required_personas=("systems_engineer",),
        llm_provider="openai",
        llm_model="test",
        prompt_schema_version="1.0.0",
        framework_template_id="TURING_RFLP_FRAMEWORK",
        framework_template_version="1.0.0",
        turing_core_version="1.0.0",
        project_glossary_revision=1,
        terminology_mapping_candidate_ids=(),
        consensus_level="unanimous",
        variance_level="low",
        confidence="high",
        confidence_rationale="exact",
        confirmation_required=True,
        review_required=True,
        recommended_review_mode="quick_confirmation",
        content_fingerprint="d" * 64,
        created_at="2026-07-27T08:00:00Z",
    )


def validation():
    return FrameworkAssignmentReferenceValidationResult(
        project_id=PROJECT_ID,
        framework_assignment_candidate_id=CANDIDATE_ID,
        checked_proposal_count=1,
        references_valid=True,
        issues=(),
    )


def review(selected_candidate=None) -> HumanReviewDecision:
    selected = candidate() if selected_candidate is None else selected_candidate
    validation_fingerprint = (
        calculate_framework_assignment_reference_validation_fingerprint(
            validation()
        )
    )
    return HumanReviewDecision(
        schema_version="1.0.0",
        project_id=PROJECT_ID,
        human_review_decision_id="HRD-000001",
        target=HumanReviewTargetSnapshot(
            target_type="framework_assignment_candidate",
            target_id=selected.framework_assignment_candidate_id,
            target_content_fingerprint=selected.content_fingerprint,
            recommended_review_mode="quick_confirmation",
            confirmation_required=True,
            reference_validation_status="valid",
            reference_validation_fingerprint=validation_fingerprint,
        ),
        review_mode="quick_confirmation",
        decision="confirm",
        reviewer_identity="moritz",
        rationale=None,
        decided_at="2026-07-27T09:00:00Z",
        decision_fingerprint=DECISION_HASH,
    )


def bundle(
    *,
    decisions=(),
    issues=(),
    candidates=None,
    summaries=None,
    lifecycles=(),
) -> ProjectCoverageInputBundle:
    selected_candidates = (
        (candidate(),) if candidates is None else candidates
    )
    return ProjectCoverageInputBundle(
        framework_template=framework_template(),
        support_profile=support_profile(),
        source_manifests=(source(),),
        source_processing_summaries=(
            (summary(),) if summaries is None else summaries
        ),
        information_units=(unit(),),
        framework_assignment_candidates=selected_candidates,
        reference_validation_results=(validation(),),
        human_review_decisions=decisions,
        artifact_lifecycles=lifecycles,
        issues=issues,
    )


def test_bundle_is_frozen() -> None:
    selected = bundle()
    with pytest.raises(Exception):
        selected.issues = ()


def test_assembly_returns_complete_assessment() -> None:
    result = assemble_project_coverage_assessment(
        PROJECT_ID,
        bundle(),
    )
    assert result.project_id == PROJECT_ID
    assert result.framework_template_id == "TURING_RFLP_FRAMEWORK"
    assert result.support_profile_id == "TURING_PRELIMINARY_SUPPORT_PROFILE"
    assert result.project_coverage_state == "partially_covered"
    assert len(result.node_coverages) == 12
    assert len(result.level_coverages) == 3
    assert len(result.support_assessments) == 3


def test_unreviewed_candidate_creates_candidate_coverage() -> None:
    result = assemble_project_coverage_assessment(PROJECT_ID, bundle())
    assert result.node_coverages[0].coverage_state == "candidate_covered"


def test_exact_confirmation_creates_reviewed_coverage() -> None:
    selected = candidate()
    result = assemble_project_coverage_assessment(
        PROJECT_ID,
        bundle(
            candidates=(selected,),
            decisions=(review(selected),),
        ),
    )
    assert result.node_coverages[0].coverage_state == (
        "reviewed_candidate_covered"
    )


def test_approved_readiness_is_explicitly_unavailable() -> None:
    result = assemble_project_coverage_assessment(PROJECT_ID, bundle())
    assert result.approved_readiness_status == APPROVED_READINESS_STATUS
    assert result.approved_readiness_status == "not_available"
    assert result.approved_readiness_available_from_phase == (
        APPROVED_READINESS_AVAILABLE_FROM_PHASE
    )
    assert result.approved_readiness_available_from_phase == "G"


def test_assessment_algorithm_metadata() -> None:
    result = assemble_project_coverage_assessment(PROJECT_ID, bundle())
    assert result.assessment_algorithm_id == (
        PROJECT_COVERAGE_ASSESSMENT_ALGORITHM_ID
    )
    assert result.assessment_algorithm_version == (
        PROJECT_COVERAGE_ASSESSMENT_ALGORITHM_VERSION
    )


def test_fingerprint_is_sha256() -> None:
    value = calculate_project_coverage_assessment_fingerprint(
        PROJECT_ID,
        bundle(),
    )
    assert re.fullmatch(r"[0-9a-f]{64}", value)


def test_assessment_uses_calculated_fingerprint() -> None:
    selected = bundle()
    result = assemble_project_coverage_assessment(PROJECT_ID, selected)
    assert result.assessment_input_fingerprint == (
        calculate_project_coverage_assessment_fingerprint(
            PROJECT_ID,
            selected,
        )
    )


def test_fingerprint_is_source_order_independent() -> None:
    selected = bundle()
    second_source = replace(
        selected.source_manifests[0],
        source_id="SRC-000002",
        sha256="9" * 64,
        original_filename="second.md",
    )
    second_summary = replace(
        selected.source_processing_summaries[0],
        source_id="SRC-000002",
        current_processing_run_id=None,
        run_state=None,
        processing_stage=None,
        latest_attempt_id=None,
    )
    forward = replace(
        selected,
        source_manifests=(
            selected.source_manifests[0],
            second_source,
        ),
        source_processing_summaries=(
            selected.source_processing_summaries[0],
            second_summary,
        ),
    )
    reverse = replace(
        forward,
        source_manifests=tuple(reversed(forward.source_manifests)),
        source_processing_summaries=tuple(
            reversed(forward.source_processing_summaries)
        ),
    )
    assert calculate_project_coverage_assessment_fingerprint(
        PROJECT_ID, forward
    ) == calculate_project_coverage_assessment_fingerprint(
        PROJECT_ID, reverse
    )


def test_fingerprint_is_issue_order_independent() -> None:
    first = CoverageIssue(
        project_id=PROJECT_ID,
        code="a",
        message="A",
        issue_level="warning",
    )
    second = CoverageIssue(
        project_id=PROJECT_ID,
        code="b",
        message="B",
        issue_level="blocking",
    )
    forward = bundle(issues=(first, second))
    reverse = bundle(issues=(second, first))
    assert calculate_project_coverage_assessment_fingerprint(
        PROJECT_ID, forward
    ) == calculate_project_coverage_assessment_fingerprint(
        PROJECT_ID, reverse
    )


def test_fingerprint_changes_with_source_hash() -> None:
    selected = bundle()
    changed = replace(
        selected,
        source_manifests=(
            replace(selected.source_manifests[0], sha256="e" * 64),
        ),
    )
    assert calculate_project_coverage_assessment_fingerprint(
        PROJECT_ID, selected
    ) != calculate_project_coverage_assessment_fingerprint(
        PROJECT_ID, changed
    )


def test_fingerprint_changes_with_disposition() -> None:
    selected = bundle()
    changed = replace(
        selected,
        source_processing_summaries=(
            replace(
                selected.source_processing_summaries[0],
                processing_disposition="out_of_scope",
            ),
        ),
    )
    assert calculate_project_coverage_assessment_fingerprint(
        PROJECT_ID, selected
    ) != calculate_project_coverage_assessment_fingerprint(
        PROJECT_ID, changed
    )


def test_fingerprint_changes_with_candidate_content() -> None:
    selected = bundle()
    changed_candidate = replace(
        selected.framework_assignment_candidates[0],
        content_fingerprint="f" * 64,
    )
    changed = replace(
        selected,
        framework_assignment_candidates=(changed_candidate,),
    )
    assert calculate_project_coverage_assessment_fingerprint(
        PROJECT_ID, selected
    ) != calculate_project_coverage_assessment_fingerprint(
        PROJECT_ID, changed
    )


def test_fingerprint_changes_with_review() -> None:
    selected = bundle()
    changed = replace(selected, human_review_decisions=(review(),))
    assert calculate_project_coverage_assessment_fingerprint(
        PROJECT_ID, selected
    ) != calculate_project_coverage_assessment_fingerprint(
        PROJECT_ID, changed
    )


def test_fingerprint_changes_with_lifecycle() -> None:
    selected = bundle()
    lifecycle = ProcessingArtifactLifecycle(
        artifact_reference=ProcessingArtifactReference(
            artifact_type="framework_assignment_candidate",
            artifact_id=CANDIDATE_ID,
            content_fingerprint=selected.framework_assignment_candidates[
                0
            ].content_fingerprint,
            repository_relative_path="semantics/framework_assignments/x.json",
        ),
        lifecycle_state="active",
        caused_by_event_id="EVT-000001",
    )
    changed = replace(selected, artifact_lifecycles=(lifecycle,))
    assert calculate_project_coverage_assessment_fingerprint(
        PROJECT_ID, selected
    ) != calculate_project_coverage_assessment_fingerprint(
        PROJECT_ID, changed
    )


def test_issues_are_sorted() -> None:
    warning = CoverageIssue(
        project_id=PROJECT_ID,
        code="z_warning",
        message="Z",
        issue_level="warning",
    )
    blocking = CoverageIssue(
        project_id=PROJECT_ID,
        code="a_blocking",
        message="A",
        issue_level="blocking",
    )
    result = assemble_project_coverage_assessment(
        PROJECT_ID,
        bundle(issues=(warning, blocking)),
    )
    assert tuple(item.issue_level for item in result.issues) == (
        "blocking",
        "warning",
    )


def test_duplicate_issue_is_rejected() -> None:
    selected = CoverageIssue(
        project_id=PROJECT_ID,
        code="duplicate",
        message="same",
        issue_level="warning",
    )
    with pytest.raises(CoverageIntegrityError):
        assemble_project_coverage_assessment(
            PROJECT_ID,
            bundle(issues=(selected, selected)),
        )


def test_issue_from_another_project_is_rejected() -> None:
    selected = CoverageIssue(
        project_id="999999",
        code="foreign",
        message="wrong",
        issue_level="warning",
    )
    with pytest.raises(CoverageReferenceError):
        assemble_project_coverage_assessment(
            PROJECT_ID,
            bundle(issues=(selected,)),
        )


def test_bundle_record_from_another_project_is_rejected() -> None:
    selected = bundle()
    foreign = replace(selected.source_manifests[0], project_id="999999")
    with pytest.raises(CoverageReferenceError):
        assemble_project_coverage_assessment(
            PROJECT_ID,
            replace(selected, source_manifests=(foreign,)),
        )


def test_profile_fingerprint_mismatch_is_rejected() -> None:
    selected = bundle()
    changed_profile = replace(
        selected.support_profile,
        profile_fingerprint="0" * 64,
    )
    with pytest.raises(CoverageProfileError):
        assemble_project_coverage_assessment(
            PROJECT_ID,
            replace(selected, support_profile=changed_profile),
        )


def test_invalid_bundle_type_is_rejected() -> None:
    with pytest.raises(CoverageValidationError):
        assemble_project_coverage_assessment(PROJECT_ID, object())


def test_service_rejects_non_callable_provider() -> None:
    with pytest.raises(CoverageValidationError):
        ProjectCoverageService(None)


def test_service_collects_and_assesses_once() -> None:
    calls = []
    def provider(project_id):
        calls.append(project_id)
        return bundle()
    service = ProjectCoverageService(provider)
    result = service.assess_project(PROJECT_ID)
    assert result.project_id == PROJECT_ID
    assert calls == [PROJECT_ID]


def test_service_wraps_provider_failure() -> None:
    def provider(project_id):
        raise RuntimeError(project_id)
    service = ProjectCoverageService(provider)
    with pytest.raises(CoverageAssessmentError):
        service.collect_inputs(PROJECT_ID)


def test_service_preserves_coverage_errors() -> None:
    def provider(project_id):
        raise CoverageReferenceError(project_id)
    service = ProjectCoverageService(provider)
    with pytest.raises(CoverageReferenceError):
        service.collect_inputs(PROJECT_ID)


def test_service_rejects_provider_bundle_from_other_project() -> None:
    selected = bundle()
    foreign = replace(selected.source_manifests[0], project_id="999999")
    service = ProjectCoverageService(
        lambda project_id: replace(
            selected,
            source_manifests=(foreign,),
        )
    )
    with pytest.raises(CoverageReferenceError):
        service.collect_inputs(PROJECT_ID)


def test_service_projection_methods() -> None:
    service = ProjectCoverageService(lambda project_id: bundle())
    assert len(service.node_coverages(PROJECT_ID)) == 12
    assert len(service.level_coverages(PROJECT_ID)) == 3
    assert len(service.support_assessments(PROJECT_ID)) == 3
    item = service.support_assessment(
        PROJECT_ID,
        "SUPPORT_STAKEHOLDER_MODEL",
    )
    assert item.support_target_id == "SUPPORT_STAKEHOLDER_MODEL"


def test_public_api_exports_are_unique() -> None:
    assert len(public_api.__all__) == len(set(public_api.__all__))


@pytest.mark.parametrize(
    "name",
    [
        "ProjectCoverageInputBundle",
        "ProjectCoverageService",
        "ProjectCoverageAssessment",
        "assemble_project_coverage_assessment",
        "calculate_project_coverage_assessment_fingerprint",
        "derive_framework_assignment_coverage_evidence",
        "derive_project_preliminary_coverage",
        "derive_potential_support_assessments",
        "load_preliminary_support_profile",
    ],
)
def test_public_api_exports_expected_name(name: str) -> None:
    assert name in public_api.__all__
    assert hasattr(public_api, name)