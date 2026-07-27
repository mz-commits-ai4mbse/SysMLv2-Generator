from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

import modules.project_dashboard as public_api
from modules.project_coverage.types import (
    CoverageIssue,
    FrameworkLevelCoverage,
    FrameworkNodeCoverage,
    PotentialSupportAssessment,
    ProjectCoverageAssessment,
)
from modules.project_dashboard import (
    DashboardPresentationError,
    DashboardProjectOption,
    DashboardProjectSelection,
    DashboardValidationError,
    ProjectDashboardService,
    ProjectOverviewView,
    make_project_option,
    make_project_overview,
    make_project_selection,
    make_section_view,
    validate_project_option,
    validate_project_overview,
    validate_project_selection,
)
from modules.project_processing.types import (
    ProcessingIssue,
    ProjectProcessingSummary,
    SourceProcessingSummary,
)
from modules.project_workspace.types import (
    FrameworkTemplateReference,
    ProjectManifest,
    WorkspaceIssue,
    WorkspaceScanResult,
)


PROJECT_ID = "318604"
OTHER_PROJECT_ID = "318605"
FRAMEWORK_ID = "TURING_RFLP_FRAMEWORK"
FRAMEWORK_VERSION = "1.0.0"
SUPPORT_PROFILE_ID = "TURING_PRELIMINARY_SUPPORT"
SUPPORT_PROFILE_VERSION = "1.0.0"


def manifest(
    *,
    project_id: str = PROJECT_ID,
    display_name: str = "Turing Demo",
    description: str = "Dashboard integration project",
) -> ProjectManifest:
    return ProjectManifest(
        schema_version="1.0.0",
        project_id=project_id,
        display_name=display_name,
        description=description,
        framework_template=FrameworkTemplateReference(
            template_id=FRAMEWORK_ID,
            template_version=FRAMEWORK_VERSION,
        ),
        created_at="2026-07-27T08:00:00Z",
        updated_at="2026-07-27T08:00:00Z",
    )


def source_summary(
    source_id: str = "SRC-000001",
    *,
    project_id: str = PROJECT_ID,
    run_id: str | None = "RUN-000001",
    state: str | None = "completed",
) -> SourceProcessingSummary:
    return SourceProcessingSummary(
        project_id=project_id,
        source_id=source_id,
        processing_disposition="in_scope",
        current_processing_run_id=run_id,
        run_state=state,
        processing_stage="publication" if run_id else None,
        latest_attempt_id="ATT-000001" if run_id else None,
        blocking_issue_codes=(),
        failure_issue_codes=(),
        pending_review=False,
        superseded_run_ids=(),
        invalidated_artifact_count=0,
    )


def processing_summary(
    *,
    project_id: str = PROJECT_ID,
    project_state: str = "processed",
    sources: tuple[SourceProcessingSummary, ...] | None = None,
    issues: tuple[ProcessingIssue, ...] = (),
) -> ProjectProcessingSummary:
    selected_sources = (
        (source_summary(project_id=project_id),)
        if sources is None
        else sources
    )
    return ProjectProcessingSummary(
        project_id=project_id,
        project_state=project_state,
        total_sources=len(selected_sources),
        in_scope_sources=len(selected_sources),
        context_only_sources=0,
        out_of_scope_sources=0,
        not_started_sources=0,
        running_sources=0,
        awaiting_review_sources=0,
        blocked_sources=0,
        failed_sources=0,
        completed_sources=len(selected_sources),
        superseded_runs=0,
        invalidated_artifacts=0,
        source_summaries=selected_sources,
        issues=issues,
    )


def node(
    node_id: str,
    *,
    state: str = "reviewed_candidate_covered",
    attention: bool = False,
) -> FrameworkNodeCoverage:
    covered = state != "uncovered"
    reviewed = state == "reviewed_candidate_covered"
    candidate = state == "candidate_covered"
    return FrameworkNodeCoverage(
        framework_node_id=node_id,
        mapping_key=node_id.lower(),
        node_name=node_id.replace("_", " ").title(),
        level_node_id="LEVEL_STAKEHOLDER",
        coverage_state=state,
        attention_required=attention,
        eligible_source_count=1 if covered else 0,
        information_unit_count=1 if covered else 0,
        assignment_candidate_count=1 if covered else 0,
        confirmed_candidate_count=1 if reviewed else 0,
        unreviewed_candidate_count=1 if candidate else 0,
        rejected_candidate_count=0,
        ambiguous_candidate_count=0,
        conflicting_candidate_count=0,
        source_ids=("SRC-000001",) if covered else (),
        information_unit_ids=("IU-000001",) if covered else (),
        framework_assignment_candidate_ids=("FAC-000001",) if covered else (),
        human_review_decision_ids=("HRD-000001",) if reviewed else (),
        issue_codes=("coverage.attention",) if attention else (),
    )


def level(
    *,
    state: str = "covered",
) -> FrameworkLevelCoverage:
    return FrameworkLevelCoverage(
        level_node_id="LEVEL_STAKEHOLDER",
        level_name="Stakeholder Level",
        coverage_state=state,
        covered_node_count=2 if state == "covered" else 1,
        total_node_count=2,
        candidate_covered_node_count=0,
        reviewed_candidate_covered_node_count=(
            2 if state == "covered" else 1
        ),
        attention_node_count=0,
        covered_node_ids=("NODE_A", "NODE_B") if state == "covered" else ("NODE_A",),
        uncovered_node_ids=() if state == "covered" else ("NODE_B",),
        attention_node_ids=(),
    )


def support(
    support_target_id: str = "STAKEHOLDER_MODEL",
    *,
    name: str = "Stakeholder Model",
    state: str = "potentially_supported",
) -> PotentialSupportAssessment:
    return PotentialSupportAssessment(
        support_target_id=support_target_id,
        name=name,
        support_target_type="model",
        support_state=state,
        required_framework_node_ids=("NODE_A", "NODE_B"),
        covered_framework_node_ids=("NODE_A", "NODE_B") if state == "potentially_supported" else ("NODE_A",),
        missing_framework_node_ids=() if state == "potentially_supported" else ("NODE_B",),
        required_support_target_ids=(),
        satisfied_support_target_ids=(),
        unsatisfied_support_target_ids=(),
        attention_required=state == "attention_required",
        issue_codes=(),
    )


def coverage_assessment(
    *,
    project_id: str = PROJECT_ID,
    project_state: str = "covered",
    nodes: tuple[FrameworkNodeCoverage, ...] | None = None,
    supports: tuple[PotentialSupportAssessment, ...] | None = None,
    issues: tuple[CoverageIssue, ...] = (),
) -> ProjectCoverageAssessment:
    selected_nodes = (
        (node("NODE_A"), node("NODE_B"))
        if nodes is None
        else nodes
    )
    selected_supports = (
        (support(),)
        if supports is None
        else supports
    )
    return ProjectCoverageAssessment(
        project_id=project_id,
        framework_template_id=FRAMEWORK_ID,
        framework_template_version=FRAMEWORK_VERSION,
        support_profile_id=SUPPORT_PROFILE_ID,
        support_profile_version=SUPPORT_PROFILE_VERSION,
        project_coverage_state=project_state,
        node_coverages=selected_nodes,
        level_coverages=(level(state=project_state if project_state in {"covered", "partially_covered", "uncovered"} else "covered"),),
        support_assessments=selected_supports,
        approved_readiness_status="not_available",
        approved_readiness_available_from_phase="G",
        assessment_algorithm_id="TURING_PROJECT_COVERAGE_ASSESSMENT",
        assessment_algorithm_version="1.0.0",
        assessment_input_fingerprint="a" * 64,
        issues=issues,
    )


class FakeWorkspace:
    def __init__(
        self,
        projects: tuple[ProjectManifest, ...] = (manifest(),),
        issues: tuple[WorkspaceIssue, ...] = (),
    ) -> None:
        self.projects = projects
        self.issues = issues
        self.loaded: list[str] = []

    def scan_projects(self) -> WorkspaceScanResult:
        return WorkspaceScanResult(
            valid_projects=self.projects,
            workspace_issues=self.issues,
        )

    def load_project(self, project_id: str) -> ProjectManifest:
        self.loaded.append(project_id)
        for project in self.projects:
            if project.project_id == project_id:
                return project
        raise RuntimeError("missing project")


class FakeProcessingService:
    def __init__(self, value: object) -> None:
        self.value = value
        self.calls: list[str] = []

    def project_summary(self, project_id: str) -> object:
        self.calls.append(project_id)
        if isinstance(self.value, Exception):
            raise self.value
        return self.value


class FakeCoverageService:
    def __init__(self, value: object) -> None:
        self.value = value
        self.calls: list[str] = []

    def assess_project(self, project_id: str) -> object:
        self.calls.append(project_id)
        if isinstance(self.value, Exception):
            raise self.value
        return self.value


def service(
    *,
    workspace: FakeWorkspace | None = None,
    processing: object | None = None,
    coverage: object | None = None,
    repository_root: Path | str = Path("."),
) -> ProjectDashboardService:
    return ProjectDashboardService(
        workspace=workspace or FakeWorkspace(),
        processing_summary_service=FakeProcessingService(
            processing_summary() if processing is None else processing
        ),
        coverage_service=FakeCoverageService(
            coverage_assessment() if coverage is None else coverage
        ),
        repository_root=repository_root,
    )


def value_by_id(overview: ProjectOverviewView, value_id: str):
    return next(
        value
        for value in overview.section.values
        if value.value_id == value_id
    )


def test_project_option_is_frozen_and_slotted() -> None:
    option = make_project_option(
        project_id=PROJECT_ID,
        display_name="Turing Demo",
        description="",
        framework_template_id=FRAMEWORK_ID,
        framework_template_version=FRAMEWORK_VERSION,
    )
    assert not hasattr(option, "__dict__")
    with pytest.raises(FrozenInstanceError):
        option.display_name = "Changed"  # type: ignore[misc]


def test_project_option_label_contains_name_and_id() -> None:
    option = make_project_option(
        project_id=PROJECT_ID,
        display_name="Turing Demo",
        description="",
        framework_template_id=FRAMEWORK_ID,
        framework_template_version=FRAMEWORK_VERSION,
    )
    assert option.label == "Turing Demo · 318604"
    assert validate_project_option(option) is option


@pytest.mark.parametrize("project_id", ["31860", "3186040", "ABC604", 318604])
def test_project_option_rejects_invalid_project_id(project_id: object) -> None:
    with pytest.raises(DashboardValidationError):
        make_project_option(
            project_id=project_id,  # type: ignore[arg-type]
            display_name="Turing Demo",
            description="",
            framework_template_id=FRAMEWORK_ID,
            framework_template_version=FRAMEWORK_VERSION,
        )


def test_project_selection_sorts_by_display_name_then_id() -> None:
    options = (
        make_project_option(
            project_id=OTHER_PROJECT_ID,
            display_name="Zulu",
            description="",
            framework_template_id=FRAMEWORK_ID,
            framework_template_version=FRAMEWORK_VERSION,
        ),
        make_project_option(
            project_id=PROJECT_ID,
            display_name="alpha",
            description="",
            framework_template_id=FRAMEWORK_ID,
            framework_template_version=FRAMEWORK_VERSION,
        ),
    )
    selection = make_project_selection(projects=options)
    assert [item.project_id for item in selection.projects] == [PROJECT_ID, OTHER_PROJECT_ID]
    assert validate_project_selection(selection) is selection


def test_project_selection_rejects_duplicate_project_ids() -> None:
    option = make_project_option(
        project_id=PROJECT_ID,
        display_name="Turing Demo",
        description="",
        framework_template_id=FRAMEWORK_ID,
        framework_template_version=FRAMEWORK_VERSION,
    )
    with pytest.raises(DashboardValidationError):
        make_project_selection(projects=(option, option))


def test_service_lists_projects_in_display_order() -> None:
    selected_workspace = FakeWorkspace(
        projects=(
            manifest(project_id=OTHER_PROJECT_ID, display_name="Zulu"),
            manifest(project_id=PROJECT_ID, display_name="Alpha"),
        )
    )
    selection = service(workspace=selected_workspace).list_projects()
    assert isinstance(selection, DashboardProjectSelection)
    assert [project.label for project in selection.projects] == [
        "Alpha · 318604",
        "Zulu · 318605",
    ]


def test_project_option_opens_project_manifest_directly() -> None:
    option = service().list_projects().projects[0]
    assert option.evidence.mode == "direct"
    reference = option.evidence.references[0]
    assert reference.reference_type == "project_manifest"
    assert reference.repository_relative_path == "data/projects/318604/project_manifest.json"


def test_workspace_issue_remains_visible() -> None:
    selected_workspace = FakeWorkspace(
        issues=(
            WorkspaceIssue(
                code="invalid_manifest",
                message="Manifest is invalid.",
                path=Path("data/projects/318605/project_manifest.json"),
                project_id=OTHER_PROJECT_ID,
            ),
        )
    )
    selection = service(workspace=selected_workspace).list_projects()
    assert len(selection.issues) == 1
    assert selection.issues[0].issue_level == "blocking"
    assert selection.issues[0].message == "Manifest is invalid."


def test_unexpected_workspace_entry_is_warning() -> None:
    selected_workspace = FakeWorkspace(
        issues=(
            WorkspaceIssue(
                code="unexpected_workspace_entry",
                message="Unexpected file.",
                path=Path("data/projects/README.txt"),
            ),
        )
    )
    assert service(workspace=selected_workspace).list_projects().issues[0].issue_level == "warning"


def test_complete_overview_contains_core_values() -> None:
    overview = service().project_overview(PROJECT_ID)
    assert isinstance(overview, ProjectOverviewView)
    assert overview.project.project_id == PROJECT_ID
    assert overview.section.section_id == "project_overview"
    assert {
        value.value_id for value in overview.section.values
    } >= {
        "project_identity",
        "framework_template",
        "registered_sources",
        "processing_state",
        "preliminary_coverage",
        "support_profile",
        "support_stakeholder_model",
        "approved_generation_readiness",
        "attention_summary",
    }
    assert validate_project_overview(overview) is overview


def test_processing_state_preserves_p5_state_meaning() -> None:
    value = value_by_id(service().project_overview(PROJECT_ID), "processing_state")
    assert value.primary_text == "Processed"
    assert value.status is not None
    assert value.status.state == "processed"
    assert value.status.semantic == "reviewed"


def test_registered_source_count_uses_processing_summary() -> None:
    sources = (
        source_summary("SRC-000001", run_id="RUN-000001"),
        source_summary("SRC-000002", run_id="RUN-000002"),
    )
    overview = service(processing=processing_summary(sources=sources)).project_overview(PROJECT_ID)
    value = value_by_id(overview, "registered_sources")
    assert value.primary_text == "2"
    assert value.evidence.mode == "chooser"
    assert [ref.reference_id for ref in value.evidence.references] == ["SRC-000001", "SRC-000002"]


def test_one_source_manifest_opens_directly() -> None:
    value = value_by_id(service().project_overview(PROJECT_ID), "registered_sources")
    assert value.evidence.mode == "direct"
    assert value.evidence.references[0].reference_id == "SRC-000001"


def test_processing_state_evidence_contains_source_and_run_manifest() -> None:
    value = value_by_id(service().project_overview(PROJECT_ID), "processing_state")
    assert value.evidence.mode == "chooser"
    assert {ref.reference_type for ref in value.evidence.references} == {
        "source_manifest",
        "processing_run_manifest",
    }


def test_coverage_ratio_is_exact_not_weighted_score() -> None:
    assessment = coverage_assessment(
        project_state="partially_covered",
        nodes=(
            node("NODE_A"),
            node("NODE_B", state="uncovered"),
        ),
    )
    value = value_by_id(
        service(coverage=assessment).project_overview(PROJECT_ID),
        "preliminary_coverage",
    )
    assert value.primary_text == "Partially covered"
    assert value.secondary_text == "1 of 2 framework nodes covered · 0 require attention"
    assert "%" not in value.secondary_text


def test_coverage_evidence_uses_explicit_chooser() -> None:
    value = value_by_id(service().project_overview(PROJECT_ID), "preliminary_coverage")
    assert value.evidence.mode == "chooser"
    assert "framework_template" in {ref.reference_type for ref in value.evidence.references}
    assert "support_profile" in {ref.reference_type for ref in value.evidence.references}


def test_potential_support_is_not_presented_as_readiness() -> None:
    value = value_by_id(service().project_overview(PROJECT_ID), "support_stakeholder_model")
    assert value.primary_text == "Potentially supported"
    assert value.status is not None
    assert value.status.state == "potentially_supported"
    assert "approved" in (value.status.explanation or "").lower()


def test_approved_generation_readiness_remains_unavailable() -> None:
    value = value_by_id(service().project_overview(PROJECT_ID), "approved_generation_readiness")
    assert value.primary_text == "Not available"
    assert value.secondary_text == "Available from Phase G"
    assert value.status is not None
    assert value.status.state == "not_available"


def test_no_attention_uses_explicit_clear_status() -> None:
    value = value_by_id(service().project_overview(PROJECT_ID), "attention_summary")
    assert value.primary_text == "0 blocking · 0 warning"
    assert value.status is not None
    assert value.status.state == "clear"
    assert value.status.label == "No attention"


def test_coverage_warning_changes_attention_summary() -> None:
    issue = CoverageIssue(
        project_id=PROJECT_ID,
        code="candidate.ambiguous",
        message="Candidate is ambiguous.",
        issue_level="warning",
        framework_assignment_candidate_id="FAC-000001",
    )
    overview = service(
        coverage=coverage_assessment(issues=(issue,))
    ).project_overview(PROJECT_ID)
    value = value_by_id(overview, "attention_summary")
    assert value.primary_text == "0 blocking · 1 warning"
    assert value.status is not None
    assert value.status.state == "attention_required"


def test_processing_failure_produces_partial_overview() -> None:
    overview = service(
        processing=RuntimeError("processing unavailable")
    ).project_overview(PROJECT_ID)
    processing_value = value_by_id(overview, "processing_state")
    source_value = value_by_id(overview, "registered_sources")
    coverage_value = value_by_id(overview, "preliminary_coverage")
    assert processing_value.primary_text == "Unavailable"
    assert source_value.primary_text == "Unavailable"
    assert coverage_value.primary_text == "Covered"
    assert any(
        issue.message.startswith("Unable to load the Project Processing summary")
        for issue in overview.section.issues
    )


def test_coverage_failure_produces_partial_overview() -> None:
    overview = service(
        coverage=RuntimeError("coverage unavailable")
    ).project_overview(PROJECT_ID)
    assert value_by_id(overview, "processing_state").primary_text == "Processed"
    assert value_by_id(overview, "preliminary_coverage").primary_text == "Unavailable"
    assert value_by_id(overview, "approved_generation_readiness").primary_text == "Unavailable"
    assert any(
        issue.message.startswith("Unable to load the Preliminary Coverage assessment")
        for issue in overview.section.issues
    )


def test_both_section_failures_do_not_fabricate_success() -> None:
    overview = service(
        processing=RuntimeError("processing unavailable"),
        coverage=RuntimeError("coverage unavailable"),
    ).project_overview(PROJECT_ID)
    assert value_by_id(overview, "processing_state").status.state == "not_available"
    assert value_by_id(overview, "preliminary_coverage").status.state == "not_available"
    assert value_by_id(overview, "attention_summary").primary_text == "2 blocking · 0 warning"


def test_wrong_project_processing_summary_is_rejected() -> None:
    with pytest.raises(DashboardPresentationError):
        service(
            processing=processing_summary(project_id=OTHER_PROJECT_ID)
        ).project_overview(PROJECT_ID)


def test_wrong_project_coverage_assessment_is_rejected() -> None:
    with pytest.raises(DashboardPresentationError):
        service(
            coverage=coverage_assessment(project_id=OTHER_PROJECT_ID)
        ).project_overview(PROJECT_ID)


def test_invalid_project_id_is_rejected_before_dependencies_are_called() -> None:
    selected_workspace = FakeWorkspace()
    selected_processing = FakeProcessingService(processing_summary())
    selected_coverage = FakeCoverageService(coverage_assessment())
    dashboard = ProjectDashboardService(
        workspace=selected_workspace,
        processing_summary_service=selected_processing,
        coverage_service=selected_coverage,
    )
    with pytest.raises(DashboardValidationError):
        dashboard.project_overview("31860")
    assert selected_workspace.loaded == []
    assert selected_processing.calls == []
    assert selected_coverage.calls == []


def test_dependencies_receive_exact_project_id() -> None:
    selected_workspace = FakeWorkspace()
    selected_processing = FakeProcessingService(processing_summary())
    selected_coverage = FakeCoverageService(coverage_assessment())
    dashboard = ProjectDashboardService(
        workspace=selected_workspace,
        processing_summary_service=selected_processing,
        coverage_service=selected_coverage,
    )
    dashboard.project_overview(PROJECT_ID)
    assert selected_workspace.loaded == [PROJECT_ID]
    assert selected_processing.calls == [PROJECT_ID]
    assert selected_coverage.calls == [PROJECT_ID]


def test_overview_is_deterministic() -> None:
    dashboard = service()
    assert dashboard.project_overview(PROJECT_ID) == dashboard.project_overview(PROJECT_ID)


def test_support_target_id_is_normalized_for_value_id() -> None:
    assessment = coverage_assessment(
        supports=(support("SUBSYSTEM-MODEL/ALPHA", name="Subsystem Model"),)
    )
    overview = service(coverage=assessment).project_overview(PROJECT_ID)
    assert value_by_id(overview, "support_subsystem_model_alpha").label == "Subsystem Model"


def test_processing_issue_codes_remain_unique_for_same_domain_code() -> None:
    issues = (
        ProcessingIssue(
            project_id=PROJECT_ID,
            code="run.failed",
            message="Run one failed.",
            issue_level="blocking",
            source_id="SRC-000001",
            processing_run_id="RUN-000001",
        ),
        ProcessingIssue(
            project_id=PROJECT_ID,
            code="run.failed",
            message="Run two failed.",
            issue_level="blocking",
            source_id="SRC-000002",
            processing_run_id="RUN-000002",
        ),
    )
    overview = service(
        processing=processing_summary(issues=issues)
    ).project_overview(PROJECT_ID)
    codes = [issue.issue_code for issue in overview.section.issues]
    assert len(codes) == len(set(codes))
    assert all(code.startswith("processing.run.failed.") for code in codes)


def test_project_overview_requires_canonical_section_id() -> None:
    option = make_project_option(
        project_id=PROJECT_ID,
        display_name="Turing Demo",
        description="",
        framework_template_id=FRAMEWORK_ID,
        framework_template_version=FRAMEWORK_VERSION,
    )
    with pytest.raises(DashboardValidationError):
        make_project_overview(
            project=option,
            section=make_section_view(
                section_id="wrong_section",
                title="Wrong",
            ),
        )


def test_public_api_exports_step_three_contracts() -> None:
    expected = {
        "DashboardProjectOption",
        "DashboardProjectSelection",
        "ProjectDashboardService",
        "ProjectOverviewView",
        "make_project_option",
        "make_project_overview",
        "make_project_selection",
        "validate_project_option",
        "validate_project_overview",
        "validate_project_selection",
    }
    assert expected <= set(public_api.__all__)
    for name in expected:
        assert hasattr(public_api, name)


def test_project_selection_type_is_frozen_and_slotted() -> None:
    selection = service().list_projects()
    assert not hasattr(selection, "__dict__")
    with pytest.raises(FrozenInstanceError):
        selection.projects = ()  # type: ignore[misc]


def test_project_overview_type_is_frozen_and_slotted() -> None:
    overview = service().project_overview(PROJECT_ID)
    assert not hasattr(overview, "__dict__")
    with pytest.raises(FrozenInstanceError):
        overview.section = make_section_view(  # type: ignore[misc]
            section_id="project_overview",
            title="Changed",
        )
