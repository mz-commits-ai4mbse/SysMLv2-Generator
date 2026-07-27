from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

import pytest

import modules.project_coverage as public_api
from modules.framework_assignment.reference_validation import (
    FrameworkAssignmentReferenceValidationResult,
)
from modules.project_coverage.errors import (
    CoverageIntegrityError,
    CoverageReferenceError,
    CoverageValidationError,
)
from modules.project_coverage.service import (
    ProjectCoverageRepositoryInputProvider,
    ProjectCoverageSemanticReferences,
    ProjectCoverageService,
)
from modules.project_processing.types import ProcessingArtifactLifecycle
from modules.semantics import (
    OntologyRegistry,
    ReferenceConceptIndex,
    TuringCoreVocabulary,
)
from modules.terminology_mapping.reference_validation import (
    TerminologyMappingReferenceValidationResult,
)

from modules.framework_assignment.types import (
    FrameworkAssignmentAgentCandidateReference,
    FrameworkAssignmentBasis,
    FrameworkAssignmentCandidate,
    FrameworkAssignmentProposal,
)
from modules.information_units.types import (
    InformationUnit,
    InformationUnitExtractionProvenance,
    InformationUnitSourceAnchor,
)
from modules.project_coverage.profile import (
    parse_preliminary_support_profile,
)
from modules.project_processing.types import SourceProcessingSummary
from modules.project_sources.types import SourceManifest


PROJECT_ID = "318604"
SOURCE_ID = "SRC-000001"
UNIT_ID = "IU-000001"
CANDIDATE_ID = "FAC-000001"
CONTENT_HASH = "a" * 64
SOURCE_HASH = "b" * 64

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
        "FW_STAKEHOLDER_STAKEHOLDERS": (
            "stakeholder.stakeholders",
            "Stakeholders",
        ),
        "FW_STAKEHOLDER_USER_NEEDS": (
            "stakeholder.user_needs",
            "User Needs",
        ),
        "FW_STAKEHOLDER_STAKEHOLDER_REQUIREMENTS": (
            "stakeholder.stakeholder_requirements",
            "Stakeholder Requirements",
        ),
        "FW_STAKEHOLDER_USE_CASES": (
            "stakeholder.use_cases",
            "Use Cases",
        ),
        "FW_SYSTEM_REQUIREMENTS": ("system.requirements", "Requirements"),
        "FW_SYSTEM_FUNCTIONAL": ("system.functional", "Functional"),
        "FW_SYSTEM_LOGICAL": ("system.logical", "Logical"),
        "FW_SYSTEM_PHYSICAL": ("system.physical", "Physical"),
        "FW_SUBSYSTEM_REQUIREMENTS": (
            "subsystem.requirements",
            "Requirements",
        ),
        "FW_SUBSYSTEM_FUNCTIONAL": (
            "subsystem.functional",
            "Functional",
        ),
        "FW_SUBSYSTEM_LOGICAL": ("subsystem.logical", "Logical"),
        "FW_SUBSYSTEM_PHYSICAL": ("subsystem.physical", "Physical"),
    }
    parent = {
        **{node: "FW_LEVEL_STAKEHOLDER" for node in STAKEHOLDER_NODES},
        **{node: "FW_LEVEL_SYSTEM" for node in SYSTEM_NODES},
        **{node: "FW_LEVEL_SUBSYSTEM" for node in SUBSYSTEM_NODES},
    }
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


def validation() -> FrameworkAssignmentReferenceValidationResult:
    return FrameworkAssignmentReferenceValidationResult(
        project_id=PROJECT_ID,
        framework_assignment_candidate_id=CANDIDATE_ID,
        checked_proposal_count=1,
        references_valid=True,
        issues=(),
    )


@dataclass(frozen=True, slots=True)
class UpstreamIssue:
    project_id: str
    code: str
    message: str
    issue_level: str = "blocking"
    path: Path | None = None
    source_id: str | None = None
    information_unit_id: str | None = None
    framework_assignment_candidate_id: str | None = None
    human_review_decision_id: str | None = None
    target_type: str | None = None
    target_id: str | None = None


class SourceRepository:
    def __init__(self, scan):
        self.scan = scan
        self.calls = []

    def scan_sources(self, project_id):
        self.calls.append(project_id)
        return self.scan


class ProcessingRepository:
    def __init__(self, scan):
        self.scan = scan
        self.calls = []

    def scan_project(self, project_id):
        self.calls.append(project_id)
        return self.scan


class InformationRepository:
    def __init__(self, scan):
        self.scan = scan
        self.calls = []

    def scan_information_units(self, project_id):
        self.calls.append(project_id)
        return self.scan


class CandidateRepository:
    def __init__(self, scan):
        self.scan = scan
        self.calls = []

    def scan_candidates(self, project_id):
        self.calls.append(project_id)
        return self.scan


class ReviewRepository:
    def __init__(self, scan):
        self.scan = scan
        self.calls = []

    def scan_decisions(self, project_id):
        self.calls.append(project_id)
        return self.scan


class GlossaryRepository:
    def __init__(self, value=object(), error=None):
        self.value = value
        self.error = error
        self.calls = []

    def load_glossary(self, project_id):
        self.calls.append(project_id)
        if self.error is not None:
            raise self.error
        return self.value


class FailingCallable:
    def __init__(self, message):
        self.message = message
        self.calls = 0

    def __call__(self, *args, **kwargs):
        self.calls += 1
        raise RuntimeError(self.message)


def semantic_references():
    """Return typed semantic snapshots without constructing full authorities.

    The integration tests inject stub reference validators, so only exact
    runtime types are required here. Building the complete immutable semantic
    authorities belongs to their dedicated module tests.
    """

    return ProjectCoverageSemanticReferences(
        turing_core_vocabulary=object.__new__(
            TuringCoreVocabulary
        ),
        ontology_registry=object.__new__(OntologyRegistry),
        reference_concept_index=object.__new__(
            ReferenceConceptIndex
        ),
    )


def scans(
    *,
    source_issues=(),
    processing_issues=(),
    information_issues=(),
    terminology_candidates=(),
    terminology_issues=(),
    assignment_candidates=None,
    assignment_issues=(),
    decisions=(),
    review_issues=(),
):
    selected_assignments = (
        (candidate(),)
        if assignment_candidates is None
        else assignment_candidates
    )
    return {
        "source": SimpleNamespace(
            valid_sources=(source(),),
            source_issues=source_issues,
        ),
        "processing": SimpleNamespace(
            run_histories=(),
            decisions=(),
            issues=processing_issues,
        ),
        "information": SimpleNamespace(
            information_units=(unit(),),
            issues=information_issues,
        ),
        "terminology": SimpleNamespace(
            candidates=terminology_candidates,
            issues=terminology_issues,
        ),
        "assignment": SimpleNamespace(
            candidates=selected_assignments,
            issues=assignment_issues,
        ),
        "review": SimpleNamespace(
            decisions=decisions,
            issues=review_issues,
        ),
    }


def provider(
    *,
    selected_scans=None,
    glossary_repository=None,
    semantic_provider=semantic_references,
    terminology_validator=None,
    framework_validator=None,
    source_summary_deriver=None,
    lifecycle_deriver=None,
):
    selected = scans() if selected_scans is None else selected_scans
    return ProjectCoverageRepositoryInputProvider(
        root="data/projects",
        repository_root=".",
        source_registry=SourceRepository(selected["source"]),
        processing_operations=ProcessingRepository(
            selected["processing"]
        ),
        information_unit_repository=InformationRepository(
            selected["information"]
        ),
        terminology_mapping_repository=CandidateRepository(
            selected["terminology"]
        ),
        framework_assignment_repository=CandidateRepository(
            selected["assignment"]
        ),
        human_review_repository=ReviewRepository(selected["review"]),
        project_glossary_repository=(
            GlossaryRepository()
            if glossary_repository is None
            else glossary_repository
        ),
        framework_template_provider=framework_template,
        support_profile_provider=lambda template: support_profile(),
        semantic_reference_provider=semantic_provider,
        terminology_reference_validator=(
            (lambda *args, **kwargs: None)
            if terminology_validator is None
            else terminology_validator
        ),
        framework_reference_validator=(
            (lambda *args, **kwargs: validation())
            if framework_validator is None
            else framework_validator
        ),
        source_summary_deriver=(
            (lambda *args, **kwargs: (summary(),))
            if source_summary_deriver is None
            else source_summary_deriver
        ),
        artifact_lifecycle_deriver=(
            (lambda *args, **kwargs: ())
            if lifecycle_deriver is None
            else lifecycle_deriver
        ),
    )


def test_semantic_reference_bundle_is_frozen_and_slotted():
    value = semantic_references()
    assert value.__dataclass_params__.frozen
    assert value.__slots__


def test_repository_provider_collects_complete_bundle():
    result = provider()(PROJECT_ID)
    assert result.source_manifests == (source(),)
    assert result.source_processing_summaries == (summary(),)
    assert result.information_units == (unit(),)
    assert result.framework_assignment_candidates == (candidate(),)
    assert result.reference_validation_results == (validation(),)
    assert result.human_review_decisions == ()
    assert result.artifact_lifecycles == ()
    assert result.issues == ()


def test_repository_provider_calls_every_project_scan():
    selected = scans()
    source_repo = SourceRepository(selected["source"])
    processing_repo = ProcessingRepository(selected["processing"])
    information_repo = InformationRepository(selected["information"])
    terminology_repo = CandidateRepository(selected["terminology"])
    assignment_repo = CandidateRepository(selected["assignment"])
    review_repo = ReviewRepository(selected["review"])
    selected_provider = ProjectCoverageRepositoryInputProvider(
        source_registry=source_repo,
        processing_operations=processing_repo,
        information_unit_repository=information_repo,
        terminology_mapping_repository=terminology_repo,
        framework_assignment_repository=assignment_repo,
        human_review_repository=review_repo,
        project_glossary_repository=GlossaryRepository(),
        framework_template_provider=framework_template,
        support_profile_provider=lambda template: support_profile(),
        semantic_reference_provider=semantic_references,
        framework_reference_validator=lambda *args, **kwargs: validation(),
        terminology_reference_validator=lambda *args, **kwargs: None,
        source_summary_deriver=lambda *args: (summary(),),
        artifact_lifecycle_deriver=lambda *args: (),
    )
    selected_provider(PROJECT_ID)
    for repository in (
        source_repo,
        processing_repo,
        information_repo,
        terminology_repo,
        assignment_repo,
        review_repo,
    ):
        assert repository.calls == [PROJECT_ID]


def test_no_assignment_candidates_skip_semantic_authorities():
    selected = scans(assignment_candidates=())
    glossary = GlossaryRepository(error=AssertionError("not called"))
    semantic = FailingCallable("not called")
    result = provider(
        selected_scans=selected,
        glossary_repository=glossary,
        semantic_provider=semantic,
    )(PROJECT_ID)
    assert result.reference_validation_results == ()
    assert glossary.calls == []
    assert semantic.calls == 0


def test_project_glossary_failure_is_fail_closed():
    glossary = GlossaryRepository(error=RuntimeError("missing glossary"))
    result = provider(glossary_repository=glossary)(PROJECT_ID)
    assert result.reference_validation_results == ()
    assert [item.code for item in result.issues] == [
        "repository_integration.project_glossary_unavailable"
    ]
    assessment = ProjectCoverageService(
        lambda project_id: result
    ).assess_project(PROJECT_ID)
    assert assessment.project_coverage_state == "attention_required"


def test_semantic_reference_failure_is_fail_closed():
    result = provider(
        semantic_provider=FailingCallable("semantic failure")
    )(PROJECT_ID)
    assert result.reference_validation_results == ()
    assert [item.code for item in result.issues] == [
        "repository_integration.semantic_references_unavailable"
    ]


def test_framework_validator_failure_is_visible():
    result = provider(
        framework_validator=FailingCallable("validation failure")
    )(PROJECT_ID)
    assert result.reference_validation_results == ()
    assert result.issues[0].code == (
        "repository_integration.framework_reference_validation_failed"
    )
    assert result.issues[0].framework_assignment_candidate_id == CANDIDATE_ID


def test_missing_candidate_source_or_unit_skips_validation():
    selected = scans()
    selected["source"] = SimpleNamespace(
        valid_sources=(),
        source_issues=(),
    )
    result = provider(selected_scans=selected)(PROJECT_ID)
    assert result.reference_validation_results == ()
    issue = result.issues[0]
    assert issue.code == (
        "repository_integration.framework_validation_input_missing"
    )
    assert issue.source_id == SOURCE_ID
    assert issue.information_unit_id == UNIT_ID


def test_terminology_validation_is_forwarded_to_framework_validation():
    terminology_candidate = SimpleNamespace(
        project_id=PROJECT_ID,
        terminology_mapping_candidate_id="TMC-000001",
        source_id=SOURCE_ID,
        information_unit_id=UNIT_ID,
    )
    terminology_result = TerminologyMappingReferenceValidationResult(
        project_id=PROJECT_ID,
        terminology_mapping_candidate_id="TMC-000001",
        checked_proposal_count=1,
        references_valid=True,
        issues=(),
    )
    observed = {}

    def terminology_validator(selected, **kwargs):
        observed["terminology_candidate"] = selected
        observed["terminology_kwargs"] = kwargs
        return terminology_result

    def framework_validator(selected, **kwargs):
        observed["framework_candidate"] = selected
        observed["framework_kwargs"] = kwargs
        return validation()

    result = provider(
        selected_scans=scans(
            terminology_candidates=(terminology_candidate,)
        ),
        terminology_validator=terminology_validator,
        framework_validator=framework_validator,
    )(PROJECT_ID)
    assert result.reference_validation_results == (validation(),)
    assert observed["terminology_candidate"] is terminology_candidate
    assert observed["framework_candidate"] == candidate()
    assert observed["framework_kwargs"][
        "terminology_mapping_candidates"
    ] == (terminology_candidate,)
    assert observed["framework_kwargs"][
        "terminology_reference_validation_results"
    ] == (terminology_result,)


def test_terminology_validator_failure_is_visible_and_framework_continues():
    terminology_candidate = SimpleNamespace(
        project_id=PROJECT_ID,
        terminology_mapping_candidate_id="TMC-000001",
        source_id=SOURCE_ID,
        information_unit_id=UNIT_ID,
    )
    observed = {}

    def framework_validator(selected, **kwargs):
        observed.update(kwargs)
        return validation()

    result = provider(
        selected_scans=scans(
            terminology_candidates=(terminology_candidate,)
        ),
        terminology_validator=FailingCallable("term failure"),
        framework_validator=framework_validator,
    )(PROJECT_ID)
    assert result.reference_validation_results == (validation(),)
    assert observed["terminology_reference_validation_results"] == ()
    assert result.issues[0].code == (
        "repository_integration.terminology_reference_validation_failed"
    )


def test_source_summary_failure_creates_blocking_issue():
    result = provider(
        source_summary_deriver=FailingCallable("summary failure")
    )(PROJECT_ID)
    assert result.source_processing_summaries == ()
    assert any(
        item.code
        == "repository_integration.source_processing_summary_failed"
        for item in result.issues
    )


def test_artifact_lifecycle_failure_creates_blocking_issue():
    result = provider(
        lifecycle_deriver=FailingCallable("lifecycle failure")
    )(PROJECT_ID)
    assert result.artifact_lifecycles == ()
    assert any(
        item.code
        == "repository_integration.artifact_lifecycle_derivation_failed"
        for item in result.issues
    )


def test_invalid_source_summary_deriver_result_is_rejected():
    with pytest.raises(CoverageIntegrityError):
        provider(source_summary_deriver=lambda *args: [])(PROJECT_ID)


def test_invalid_lifecycle_deriver_result_is_rejected():
    with pytest.raises(CoverageIntegrityError):
        provider(lifecycle_deriver=lambda *args: [])(PROJECT_ID)


def test_scan_issues_are_namespaced_and_preserve_fields():
    selected = scans(
        source_issues=(
            UpstreamIssue(
                project_id=PROJECT_ID,
                code="source_corrupt",
                message="corrupt",
                path=Path("source.json"),
                source_id=SOURCE_ID,
            ),
        ),
        review_issues=(
            UpstreamIssue(
                project_id=PROJECT_ID,
                code="review_corrupt",
                message="review",
                human_review_decision_id="HRD-000001",
                target_type="framework_assignment_candidate",
                target_id=CANDIDATE_ID,
            ),
        ),
    )
    result = provider(selected_scans=selected)(PROJECT_ID)
    by_code = {item.code: item for item in result.issues}
    source_issue = by_code["source_scan.source_corrupt"]
    assert source_issue.source_id == SOURCE_ID
    assert source_issue.path == Path("source.json")
    review_issue = by_code["human_review_scan.review_corrupt"]
    assert review_issue.human_review_decision_id == "HRD-000001"
    assert review_issue.framework_assignment_candidate_id == CANDIDATE_ID


def test_issue_without_level_defaults_to_blocking():
    issue = SimpleNamespace(
        project_id=PROJECT_ID,
        code="legacy_issue",
        message="legacy",
        path=Path("legacy"),
        source_id=SOURCE_ID,
    )
    result = provider(
        selected_scans=scans(source_issues=(issue,))
    )(PROJECT_ID)
    translated = next(
        item for item in result.issues
        if item.code == "source_scan.legacy_issue"
    )
    assert translated.issue_level == "blocking"


def test_warning_scan_issue_remains_warning():
    result = provider(
        selected_scans=scans(
            assignment_issues=(
                UpstreamIssue(
                    project_id=PROJECT_ID,
                    code="uncertain",
                    message="uncertain",
                    issue_level="warning",
                    framework_assignment_candidate_id=CANDIDATE_ID,
                ),
            )
        )
    )(PROJECT_ID)
    translated = next(
        item for item in result.issues
        if item.code == "framework_assignment_scan.uncertain"
    )
    assert translated.issue_level == "warning"


def test_issue_from_another_project_is_rejected():
    selected = scans(
        source_issues=(
            UpstreamIssue(
                project_id="999999",
                code="bad",
                message="bad",
            ),
        )
    )
    with pytest.raises(CoverageReferenceError):
        provider(selected_scans=selected)(PROJECT_ID)


def test_non_tuple_scan_issues_are_rejected():
    selected = scans()
    selected["source"] = SimpleNamespace(
        valid_sources=(source(),),
        source_issues=[],
    )
    with pytest.raises(CoverageIntegrityError):
        provider(selected_scans=selected)(PROJECT_ID)


def test_provider_rejects_non_callable_dependencies():
    with pytest.raises(CoverageValidationError):
        ProjectCoverageRepositoryInputProvider(
            framework_template_provider=object()
        )


def test_provider_rejects_invalid_semantic_reference_result():
    with pytest.raises(CoverageIntegrityError):
        provider(semantic_provider=lambda: object())(PROJECT_ID)


def test_provider_rejects_invalid_framework_validation_result():
    with pytest.raises(CoverageIntegrityError):
        provider(framework_validator=lambda *args, **kwargs: object())(
            PROJECT_ID
        )


def test_provider_rejects_invalid_terminology_validation_result():
    terminology_candidate = SimpleNamespace(
        project_id=PROJECT_ID,
        terminology_mapping_candidate_id="TMC-000001",
        source_id=SOURCE_ID,
        information_unit_id=UNIT_ID,
    )
    with pytest.raises(CoverageIntegrityError):
        provider(
            selected_scans=scans(
                terminology_candidates=(terminology_candidate,)
            ),
            terminology_validator=lambda *args, **kwargs: object(),
        )(PROJECT_ID)


def test_service_accepts_repository_input_provider():
    selected_provider = provider()
    service = ProjectCoverageService(
        repository_input_provider=selected_provider
    )
    assert service.assess_project(PROJECT_ID).project_id == PROJECT_ID


def test_service_rejects_two_provider_modes():
    with pytest.raises(CoverageValidationError):
        ProjectCoverageService(
            lambda project_id: None,
            repository_input_provider=lambda project_id: None,
        )


@pytest.mark.parametrize(
    "name",
    (
        "FrameworkTemplateProvider",
        "ProjectCoverageRepositoryInputProvider",
        "ProjectCoverageSemanticReferences",
        "SemanticReferenceProvider",
        "SupportProfileProvider",
    ),
)
def test_public_api_exports_repository_integration(name):
    assert name in public_api.__all__
    assert hasattr(public_api, name)


def test_public_api_exports_remain_unique():
    assert len(public_api.__all__) == len(set(public_api.__all__))