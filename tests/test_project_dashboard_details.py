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
    DashboardCoverageView,
    DashboardFrameworkLevelCoverage,
    DashboardFrameworkNodeCoverage,
    DashboardPotentialSupport,
    DashboardPresentationError,
    DashboardSourceProcessingRow,
    DashboardSourceProcessingView,
    DashboardValidationError,
    EvidenceReference,
    ProjectDashboardService,
    make_coverage_view,
    make_framework_level_coverage_view,
    make_framework_node_coverage_view,
    make_potential_support_view,
    make_source_processing_row,
    make_source_processing_view,
    present_status,
    validate_coverage_view,
    validate_framework_level_coverage_view,
    validate_framework_node_coverage_view,
    validate_potential_support_view,
    validate_source_processing_row,
    validate_source_processing_view,
)
from modules.project_processing.types import (
    ProcessingIssue,
    ProjectProcessingSummary,
    SourceProcessingSummary,
)
from modules.project_sources.types import (
    SourceIssue,
    SourceManifest,
    SourceScanResult,
)
from modules.project_workspace.types import (
    FrameworkTemplateReference,
    ProjectManifest,
    WorkspaceScanResult,
)


PROJECT_ID = "318604"
OTHER_PROJECT_ID = "318605"
FRAMEWORK_ID = "TURING_RFLP_FRAMEWORK"
FRAMEWORK_VERSION = "1.0.0"
SUPPORT_PROFILE_ID = "TURING_PRELIMINARY_SUPPORT"
SUPPORT_PROFILE_VERSION = "1.0.0"


def manifest(*, project_id: str = PROJECT_ID) -> ProjectManifest:
    return ProjectManifest(
        schema_version="1.0.0",
        project_id=project_id,
        display_name="Turing Demo",
        description="Detailed dashboard project",
        framework_template=FrameworkTemplateReference(
            template_id=FRAMEWORK_ID,
            template_version=FRAMEWORK_VERSION,
        ),
        created_at="2026-07-27T08:00:00Z",
        updated_at="2026-07-27T08:00:00Z",
    )


def source_manifest(
    source_id: str = "SRC-000001",
    *,
    project_id: str = PROJECT_ID,
    role: str = "engineering_source",
    original_filename: str = "requirements.md",
) -> SourceManifest:
    return SourceManifest(
        schema_version="1.0.0",
        project_id=project_id,
        source_id=source_id,
        source_role=role,
        original_filename=original_filename,
        stored_filename="source.md",
        media_type="text/markdown",
        size_bytes=128,
        sha256=("a" if source_id.endswith("1") else "b") * 64,
        registered_at="2026-07-27T08:00:00Z",
        updated_at="2026-07-27T08:00:00Z",
    )


def source_summary(
    source_id: str = "SRC-000001",
    *,
    project_id: str = PROJECT_ID,
    disposition: str = "in_scope",
    run_id: str | None = "RUN-000001",
    run_state: str | None = "completed",
    pending_review: bool = False,
    superseded: tuple[str, ...] = (),
    blocking: tuple[str, ...] = (),
    failure: tuple[str, ...] = (),
) -> SourceProcessingSummary:
    return SourceProcessingSummary(
        project_id=project_id,
        source_id=source_id,
        processing_disposition=disposition,
        current_processing_run_id=run_id,
        run_state=run_state,
        processing_stage="publication" if run_id else None,
        latest_attempt_id="ATT-000001" if run_id else None,
        blocking_issue_codes=blocking,
        failure_issue_codes=failure,
        pending_review=pending_review,
        superseded_run_ids=superseded,
        invalidated_artifact_count=1 if superseded else 0,
    )


def processing_summary(
    *,
    project_id: str = PROJECT_ID,
    source_summaries: tuple[SourceProcessingSummary, ...] | None = None,
    state: str = "processed",
    issues: tuple[ProcessingIssue, ...] = (),
) -> ProjectProcessingSummary:
    rows = (
        (source_summary(project_id=project_id),)
        if source_summaries is None
        else source_summaries
    )
    return ProjectProcessingSummary(
        project_id=project_id,
        project_state=state,
        total_sources=len(rows),
        in_scope_sources=sum(row.processing_disposition == "in_scope" for row in rows),
        context_only_sources=sum(row.processing_disposition == "context_only" for row in rows),
        out_of_scope_sources=sum(row.processing_disposition == "out_of_scope" for row in rows),
        not_started_sources=sum(row.run_state is None for row in rows),
        running_sources=sum(row.run_state == "running" for row in rows),
        awaiting_review_sources=sum(row.run_state == "awaiting_review" for row in rows),
        blocked_sources=sum(row.run_state == "blocked" for row in rows),
        failed_sources=sum(row.run_state == "failed" for row in rows),
        completed_sources=sum(row.run_state == "completed" for row in rows),
        superseded_runs=sum(len(row.superseded_run_ids) for row in rows),
        invalidated_artifacts=sum(row.invalidated_artifact_count for row in rows),
        source_summaries=rows,
        issues=issues,
    )


def node(
    node_id: str,
    *,
    level_id: str,
    state: str = "reviewed_candidate_covered",
    attention: bool = False,
    candidate_ids: tuple[str, ...] | None = None,
) -> FrameworkNodeCoverage:
    covered = state != "uncovered"
    reviewed = state == "reviewed_candidate_covered"
    unreviewed = state == "candidate_covered"
    candidates = (
        (("FAC-000001",) if covered else ())
        if candidate_ids is None
        else candidate_ids
    )
    return FrameworkNodeCoverage(
        framework_node_id=node_id,
        mapping_key=node_id.lower().replace("fw_", "").replace("_", "."),
        node_name=node_id.replace("FW_", "").replace("_", " ").title(),
        level_node_id=level_id,
        coverage_state=state,
        attention_required=attention,
        eligible_source_count=1 if covered else 0,
        information_unit_count=1 if covered else 0,
        assignment_candidate_count=1 if covered else 0,
        confirmed_candidate_count=1 if reviewed else 0,
        unreviewed_candidate_count=1 if unreviewed else 0,
        rejected_candidate_count=max(0, len(candidates) - (1 if covered else 0)),
        ambiguous_candidate_count=1 if attention else 0,
        conflicting_candidate_count=0,
        source_ids=("SRC-000001",) if covered else (),
        information_unit_ids=("IU-000001",) if covered else (),
        framework_assignment_candidate_ids=candidates,
        human_review_decision_ids=("HRD-000001",) if reviewed else (),
        issue_codes=("coverage.attention",) if attention else (),
    )


def level(
    level_id: str,
    name: str,
    node_ids: tuple[str, ...],
    *,
    state: str = "covered",
    attention_ids: tuple[str, ...] = (),
) -> FrameworkLevelCoverage:
    covered_ids = node_ids if state == "covered" else node_ids[:1]
    uncovered_ids = () if state == "covered" else node_ids[1:]
    return FrameworkLevelCoverage(
        level_node_id=level_id,
        level_name=name,
        coverage_state=state,
        covered_node_count=len(covered_ids),
        total_node_count=len(node_ids),
        candidate_covered_node_count=0,
        reviewed_candidate_covered_node_count=len(covered_ids),
        attention_node_count=len(attention_ids),
        covered_node_ids=covered_ids,
        uncovered_node_ids=uncovered_ids,
        attention_node_ids=attention_ids,
    )


def support(
    support_id: str = "STAKEHOLDER_MODEL",
    *,
    name: str = "Stakeholder Model",
    state: str = "potentially_supported",
    required_nodes: tuple[str, ...] = ("FW_STAKEHOLDER_STAKEHOLDERS",),
    required_support: tuple[str, ...] = (),
) -> PotentialSupportAssessment:
    covered = required_nodes if state == "potentially_supported" else required_nodes[:0]
    missing = tuple(item for item in required_nodes if item not in covered)
    satisfied = required_support if state == "potentially_supported" else required_support[:0]
    unsatisfied = tuple(item for item in required_support if item not in satisfied)
    return PotentialSupportAssessment(
        support_target_id=support_id,
        name=name,
        support_target_type="model",
        support_state=state,
        required_framework_node_ids=required_nodes,
        covered_framework_node_ids=covered,
        missing_framework_node_ids=missing,
        required_support_target_ids=required_support,
        satisfied_support_target_ids=satisfied,
        unsatisfied_support_target_ids=unsatisfied,
        attention_required=state == "attention_required",
        issue_codes=("support.attention",) if state == "attention_required" else (),
    )


def coverage_assessment(
    *,
    project_id: str = PROJECT_ID,
    framework_id: str = FRAMEWORK_ID,
    framework_version: str = FRAMEWORK_VERSION,
    issues: tuple[CoverageIssue, ...] = (),
) -> ProjectCoverageAssessment:
    stakeholder_id = "FW_LEVEL_STAKEHOLDER"
    system_id = "FW_LEVEL_SYSTEM"
    stakeholder_node = node(
        "FW_STAKEHOLDER_STAKEHOLDERS",
        level_id=stakeholder_id,
        candidate_ids=("FAC-000001", "FAC-000002"),
    )
    system_node = node(
        "FW_SYSTEM_REQUIREMENTS",
        level_id=system_id,
        state="candidate_covered",
        attention=True,
    )
    return ProjectCoverageAssessment(
        project_id=project_id,
        framework_template_id=framework_id,
        framework_template_version=framework_version,
        support_profile_id=SUPPORT_PROFILE_ID,
        support_profile_version=SUPPORT_PROFILE_VERSION,
        project_coverage_state="partially_covered",
        node_coverages=(stakeholder_node, system_node),
        level_coverages=(
            level(stakeholder_id, "Stakeholder Level", (stakeholder_node.framework_node_id,)),
            level(
                system_id,
                "System Level",
                (system_node.framework_node_id,),
                attention_ids=(system_node.framework_node_id,),
            ),
        ),
        support_assessments=(
            support(required_nodes=(stakeholder_node.framework_node_id,)),
            support(
                "SYSTEM_MODEL",
                name="System Model",
                state="partially_supported",
                required_nodes=(system_node.framework_node_id,),
                required_support=("STAKEHOLDER_MODEL",),
            ),
        ),
        approved_readiness_status="not_available",
        approved_readiness_available_from_phase="G",
        assessment_algorithm_id="TURING_PROJECT_COVERAGE_ASSESSMENT",
        assessment_algorithm_version="1.0.0",
        assessment_input_fingerprint="c" * 64,
        issues=issues,
    )


class FakeWorkspace:
    def __init__(self, selected: ProjectManifest | None = None) -> None:
        self.selected = selected or manifest()
        self.calls: list[str] = []

    def load_project(self, project_id: str) -> ProjectManifest:
        self.calls.append(project_id)
        if project_id != self.selected.project_id:
            raise RuntimeError("missing project")
        return self.selected

    def scan_projects(self) -> WorkspaceScanResult:
        return WorkspaceScanResult(valid_projects=(self.selected,), workspace_issues=())


class FakeSourceRegistry:
    def __init__(self, value: object) -> None:
        self.value = value
        self.calls: list[str] = []

    def scan_sources(self, project_id: str) -> object:
        self.calls.append(project_id)
        if isinstance(self.value, Exception):
            raise self.value
        return self.value


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


def dashboard_service(
    *,
    selected_manifest: ProjectManifest | None = None,
    source_scan: object | None = None,
    processing: object | None = None,
    coverage: object | None = None,
    repository_root: Path | str = Path("."),
) -> ProjectDashboardService:
    return ProjectDashboardService(
        workspace=FakeWorkspace(selected_manifest),
        source_registry=FakeSourceRegistry(
            SourceScanResult(valid_sources=(source_manifest(),))
            if source_scan is None
            else source_scan
        ),
        processing_summary_service=FakeProcessingService(
            processing_summary() if processing is None else processing
        ),
        coverage_service=FakeCoverageService(
            coverage_assessment() if coverage is None else coverage
        ),
        repository_root=repository_root,
    )


def evidence(reference_id: str = "SRC-000001") -> EvidenceReference:
    return EvidenceReference(
        project_id=PROJECT_ID,
        reference_type="source_manifest",
        reference_id=reference_id,
        display_label=f"Source · {reference_id}",
        repository_relative_path=(
            f"data/projects/{PROJECT_ID}/sources/{reference_id}/source_manifest.json"
        ),
        content_fingerprint=None,
        media_type="application/json",
        source_role="engineering_source",
        relationship="defines_source",
        evidence_role="direct",
    )


def source_row(**changes) -> DashboardSourceProcessingRow:
    values = dict(
        project_id=PROJECT_ID,
        source_id="SRC-000001",
        original_filename="requirements.md",
        source_role="engineering_source",
        media_type="text/markdown",
        size_bytes=128,
        sha256="a" * 64,
        processing_disposition="in_scope",
        current_processing_run_id="RUN-000001",
        run_state="completed",
        processing_stage="publication",
        latest_attempt_id="ATT-000001",
        pending_review=False,
        superseded_run_ids=(),
        invalidated_artifact_count=0,
        blocking_issue_codes=(),
        failure_issue_codes=(),
        evidence_references=(evidence(),),
    )
    values.update(changes)
    return make_source_processing_row(**values)


def level_view(**changes) -> DashboardFrameworkLevelCoverage:
    values = dict(
        display_order=1,
        level_node_id="FW_LEVEL_STAKEHOLDER",
        level_name="Stakeholder Level",
        coverage_state="covered",
        covered_node_count=1,
        total_node_count=1,
        candidate_covered_node_count=0,
        reviewed_candidate_covered_node_count=1,
        attention_node_count=0,
        covered_node_ids=("FW_STAKEHOLDER_STAKEHOLDERS",),
        uncovered_node_ids=(),
        attention_node_ids=(),
        evidence_references=(evidence(),),
    )
    values.update(changes)
    return make_framework_level_coverage_view(**values)


def node_view(**changes) -> DashboardFrameworkNodeCoverage:
    values = dict(
        display_order=1,
        framework_node_id="FW_STAKEHOLDER_STAKEHOLDERS",
        mapping_key="stakeholder.stakeholders",
        node_name="Stakeholders",
        level_node_id="FW_LEVEL_STAKEHOLDER",
        coverage_state="reviewed_candidate_covered",
        attention_required=False,
        eligible_source_count=1,
        information_unit_count=1,
        assignment_candidate_count=1,
        confirmed_candidate_count=1,
        unreviewed_candidate_count=0,
        rejected_candidate_count=1,
        ambiguous_candidate_count=0,
        conflicting_candidate_count=0,
        source_ids=("SRC-000001",),
        information_unit_ids=("IU-000001",),
        framework_assignment_candidate_ids=("FAC-000001", "FAC-000002"),
        human_review_decision_ids=("HRD-000001",),
        issue_codes=(),
        evidence_references=(evidence(),),
    )
    values.update(changes)
    return make_framework_node_coverage_view(**values)


def support_view(**changes) -> DashboardPotentialSupport:
    values = dict(
        display_order=1,
        support_target_id="STAKEHOLDER_MODEL",
        name="Stakeholder Model",
        support_target_type="model",
        support_state="potentially_supported",
        required_framework_node_ids=("FW_STAKEHOLDER_STAKEHOLDERS",),
        covered_framework_node_ids=("FW_STAKEHOLDER_STAKEHOLDERS",),
        missing_framework_node_ids=(),
        required_support_target_ids=(),
        satisfied_support_target_ids=(),
        unsatisfied_support_target_ids=(),
        attention_required=False,
        issue_codes=(),
        evidence_references=(evidence(),),
    )
    values.update(changes)
    return make_potential_support_view(**values)


@pytest.mark.parametrize(
    "data_type",
    (
        DashboardSourceProcessingRow,
        DashboardSourceProcessingView,
        DashboardFrameworkLevelCoverage,
        DashboardFrameworkNodeCoverage,
        DashboardPotentialSupport,
        DashboardCoverageView,
    ),
)
def test_step_four_types_are_frozen_and_slotted(data_type: type) -> None:
    assert "__slots__" in data_type.__dict__


def test_source_row_is_immutable() -> None:
    row = source_row()
    with pytest.raises(FrozenInstanceError):
        row.source_id = "SRC-999999"  # type: ignore[misc]


@pytest.mark.parametrize(
    ("state", "semantic", "icon"),
    (
        ("created", "informational", "ℹ"),
        ("running", "informational", "ℹ"),
        ("completed", "reviewed", "✓"),
        ("failed", "blocking", "×"),
        ("blocked", "blocking", "×"),
    ),
)
def test_processing_run_states_have_status_semantics(
    state: str,
    semantic: str,
    icon: str,
) -> None:
    status = present_status(state)
    assert status.semantic == semantic
    assert status.icon == icon


def test_source_row_preserves_disposition_and_run_state() -> None:
    row = source_row()
    assert row.disposition_status.state == "in_scope"
    assert row.run_status.state == "completed"


def test_source_without_run_is_presented_as_not_started() -> None:
    row = source_row(
        current_processing_run_id=None,
        run_state=None,
        processing_stage=None,
        latest_attempt_id=None,
    )
    assert row.run_status.state == "not_started"


def test_source_row_rejects_run_state_without_run_id() -> None:
    with pytest.raises(DashboardValidationError):
        source_row(current_processing_run_id=None, run_state="running")


def test_source_row_canonicalizes_issue_codes_and_run_ids() -> None:
    row = source_row(
        superseded_run_ids=("RUN-000003", "RUN-000002", "RUN-000003"),
        blocking_issue_codes=("z", "a", "z"),
    )
    assert row.superseded_run_ids == ("RUN-000002", "RUN-000003")
    assert row.blocking_issue_codes == ("a", "z")


def test_source_processing_view_sorts_sources() -> None:
    first = source_row(source_id="SRC-000002", sha256="b" * 64)
    second = source_row(source_id="SRC-000001")
    view = make_source_processing_view(
        project_id=PROJECT_ID,
        project_state="processed",
        sources=(first, second),
    )
    assert tuple(row.source_id for row in view.sources) == (
        "SRC-000001",
        "SRC-000002",
    )


def test_source_processing_service_builds_full_row() -> None:
    view = dashboard_service().source_processing_view(PROJECT_ID)
    row = view.sources[0]
    assert row.original_filename == "requirements.md"
    assert row.source_role == "engineering_source"
    assert row.processing_disposition == "in_scope"
    assert row.current_processing_run_id == "RUN-000001"


def test_source_row_navigation_includes_manifest_content_and_run() -> None:
    row = dashboard_service().source_processing_view(PROJECT_ID).sources[0]
    assert row.evidence.mode == "chooser"
    assert {reference.reference_type for reference in row.evidence.references} == {
        "processing_run_manifest",
        "registered_source_content",
        "source_manifest",
    }


def test_registered_source_content_uses_exact_sha256() -> None:
    row = dashboard_service().source_processing_view(PROJECT_ID).sources[0]
    source_content = next(
        reference
        for reference in row.evidence.references
        if reference.reference_type == "registered_source_content"
    )
    assert source_content.content_fingerprint == "a" * 64
    assert source_content.repository_relative_path.endswith("/source.md")


def test_superseded_runs_are_contextual_evidence() -> None:
    selected_summary = source_summary(superseded=("RUN-000000",))
    row = dashboard_service(
        processing=processing_summary(source_summaries=(selected_summary,))
    ).source_processing_view(PROJECT_ID).sources[0]
    superseded_reference = next(
        reference
        for reference in row.evidence.references
        if reference.reference_id == "RUN-000000"
    )
    assert superseded_reference.evidence_role == "contextual"
    assert superseded_reference.relationship == "is_superseded_processing_run"


def test_source_and_processing_mismatch_fails_closed() -> None:
    with pytest.raises(DashboardPresentationError):
        dashboard_service(
            source_scan=SourceScanResult(
                valid_sources=(source_manifest("SRC-000002"),)
            )
        ).source_processing_view(PROJECT_ID)


def test_foreign_source_scan_fails_closed() -> None:
    with pytest.raises(DashboardPresentationError):
        dashboard_service(
            source_scan=SourceScanResult(
                valid_sources=(source_manifest(project_id=OTHER_PROJECT_ID),)
            )
        ).source_processing_view(PROJECT_ID)


def test_invalid_source_scan_type_fails_closed() -> None:
    with pytest.raises(DashboardPresentationError):
        dashboard_service(source_scan=object()).source_processing_view(PROJECT_ID)


def test_source_registry_failure_is_wrapped() -> None:
    with pytest.raises(DashboardPresentationError):
        dashboard_service(source_scan=RuntimeError("scan failed")).source_processing_view(PROJECT_ID)


def test_source_issue_remains_visible() -> None:
    issue = SourceIssue(
        project_id=PROJECT_ID,
        code="invalid_source_manifest",
        message="Source Manifest is invalid.",
        path=Path(f"data/projects/{PROJECT_ID}/sources/SRC-000001/source_manifest.json"),
        source_id="SRC-000001",
    )
    view = dashboard_service(
        source_scan=SourceScanResult(
            valid_sources=(source_manifest(),),
            source_issues=(issue,),
        )
    ).source_processing_view(PROJECT_ID)
    assert len(view.issues) == 1
    assert view.issues[0].status.state == "blocking"


def test_processing_issue_remains_visible() -> None:
    issue = ProcessingIssue(
        project_id=PROJECT_ID,
        code="run_failed",
        message="Run failed.",
        issue_level="blocking",
        processing_run_id="RUN-000001",
    )
    view = dashboard_service(
        processing=processing_summary(issues=(issue,))
    ).source_processing_view(PROJECT_ID)
    assert len(view.issues) == 1
    assert view.issues[0].message == "Run failed."


def test_coverage_view_contains_levels_nodes_and_support() -> None:
    view = dashboard_service().coverage_view(PROJECT_ID)
    assert len(view.levels) == 2
    assert len(view.nodes) == 2
    assert len(view.support_targets) == 2


def test_coverage_view_preserves_project_state() -> None:
    view = dashboard_service().coverage_view(PROJECT_ID)
    assert view.project_coverage_state == "partially_covered"
    assert view.project_status.state == "partially_covered"


def test_node_coverage_navigation_contains_exact_evidence_types() -> None:
    view = dashboard_service().coverage_view(PROJECT_ID)
    selected = view.nodes[0]
    assert selected.evidence.mode == "chooser"
    types = {reference.reference_type for reference in selected.evidence.references}
    assert types == {
        "framework_assignment_candidate",
        "framework_template",
        "information_unit",
        "source_manifest",
    }


def test_candidate_paths_are_project_local_and_exact() -> None:
    selected = dashboard_service().coverage_view(PROJECT_ID).nodes[0]
    candidate_paths = {
        reference.repository_relative_path
        for reference in selected.evidence.references
        if reference.reference_type == "framework_assignment_candidate"
    }
    assert candidate_paths == {
        f"data/projects/{PROJECT_ID}/semantics/framework_assignments/FAC-000001.json",
        f"data/projects/{PROJECT_ID}/semantics/framework_assignments/FAC-000002.json",
    }


def test_information_unit_path_is_exact() -> None:
    selected = dashboard_service().coverage_view(PROJECT_ID).nodes[0]
    reference = next(
        reference
        for reference in selected.evidence.references
        if reference.reference_type == "information_unit"
    )
    assert reference.repository_relative_path == (
        f"data/projects/{PROJECT_ID}/semantics/information_units/IU-000001.json"
    )


def test_uncovered_node_has_only_framework_context() -> None:
    assessment = coverage_assessment()
    uncovered = node(
        "FW_SYSTEM_REQUIREMENTS",
        level_id="FW_LEVEL_SYSTEM",
        state="uncovered",
    )
    modified = ProjectCoverageAssessment(
        project_id=assessment.project_id,
        framework_template_id=assessment.framework_template_id,
        framework_template_version=assessment.framework_template_version,
        support_profile_id=assessment.support_profile_id,
        support_profile_version=assessment.support_profile_version,
        project_coverage_state="partially_covered",
        node_coverages=(assessment.node_coverages[0], uncovered),
        level_coverages=(
            assessment.level_coverages[0],
            level(
                "FW_LEVEL_SYSTEM",
                "System Level",
                (uncovered.framework_node_id,),
                state="uncovered",
            ),
        ),
        support_assessments=assessment.support_assessments,
        approved_readiness_status="not_available",
        approved_readiness_available_from_phase="G",
        assessment_algorithm_id=assessment.assessment_algorithm_id,
        assessment_algorithm_version=assessment.assessment_algorithm_version,
        assessment_input_fingerprint=assessment.assessment_input_fingerprint,
        issues=(),
    )
    selected = dashboard_service(coverage=modified).coverage_view(PROJECT_ID).nodes[1]
    assert selected.status.state == "uncovered"
    assert selected.evidence.mode == "direct"
    assert selected.evidence.references[0].reference_type == "framework_template"


def test_node_attention_is_separate_from_coverage() -> None:
    selected = dashboard_service().coverage_view(PROJECT_ID).nodes[1]
    assert selected.status.state == "candidate_covered"
    assert selected.attention_status is not None
    assert selected.attention_status.state == "attention_required"


def test_level_attention_is_separate_from_level_coverage() -> None:
    selected = dashboard_service().coverage_view(PROJECT_ID).levels[1]
    assert selected.status.state == "covered"
    assert selected.attention_status is not None


def test_level_navigation_aggregates_node_evidence() -> None:
    selected = dashboard_service().coverage_view(PROJECT_ID).levels[0]
    assert selected.evidence.mode == "chooser"
    assert any(
        reference.reference_type == "framework_assignment_candidate"
        for reference in selected.evidence.references
    )


def test_support_navigation_contains_profile_and_node_evidence() -> None:
    selected = dashboard_service().coverage_view(PROJECT_ID).support_targets[0]
    types = {reference.reference_type for reference in selected.evidence.references}
    assert "support_profile" in types
    assert "framework_assignment_candidate" in types


def test_potential_support_is_not_renamed_ready() -> None:
    selected = dashboard_service().coverage_view(PROJECT_ID).support_targets[0]
    assert selected.status.label == "Potentially supported"
    assert "ready" not in selected.status.label.lower()
    assert "approved" in (selected.status.explanation or "").lower()


def test_approved_readiness_remains_unavailable_from_phase_g() -> None:
    view = dashboard_service().coverage_view(PROJECT_ID)
    assert view.approved_readiness_status == "not_available"
    assert view.approved_readiness.state == "not_available"
    assert view.approved_readiness_available_from_phase == "G"


def test_coverage_issue_remains_visible() -> None:
    issue = CoverageIssue(
        project_id=PROJECT_ID,
        code="coverage.warning",
        message="Coverage requires attention.",
        issue_level="warning",
        framework_node_id="FW_SYSTEM_REQUIREMENTS",
    )
    view = dashboard_service(
        coverage=coverage_assessment(issues=(issue,))
    ).coverage_view(PROJECT_ID)
    assert view.issues[0].issue_level == "warning"


def test_framework_mismatch_fails_closed() -> None:
    with pytest.raises(DashboardPresentationError):
        dashboard_service(
            coverage=coverage_assessment(framework_version="2.0.0")
        ).coverage_view(PROJECT_ID)


def test_foreign_coverage_assessment_fails_closed() -> None:
    with pytest.raises(DashboardPresentationError):
        dashboard_service(
            coverage=coverage_assessment(project_id=OTHER_PROJECT_ID)
        ).coverage_view(PROJECT_ID)


def test_unknown_level_node_reference_fails_closed() -> None:
    assessment = coverage_assessment()
    bad_level = level(
        "FW_LEVEL_STAKEHOLDER",
        "Stakeholder Level",
        ("FW_UNKNOWN",),
    )
    modified = ProjectCoverageAssessment(
        project_id=assessment.project_id,
        framework_template_id=assessment.framework_template_id,
        framework_template_version=assessment.framework_template_version,
        support_profile_id=assessment.support_profile_id,
        support_profile_version=assessment.support_profile_version,
        project_coverage_state=assessment.project_coverage_state,
        node_coverages=assessment.node_coverages,
        level_coverages=(bad_level,),
        support_assessments=assessment.support_assessments,
        approved_readiness_status=assessment.approved_readiness_status,
        approved_readiness_available_from_phase=assessment.approved_readiness_available_from_phase,
        assessment_algorithm_id=assessment.assessment_algorithm_id,
        assessment_algorithm_version=assessment.assessment_algorithm_version,
        assessment_input_fingerprint=assessment.assessment_input_fingerprint,
        issues=assessment.issues,
    )
    with pytest.raises(DashboardPresentationError):
        dashboard_service(coverage=modified).coverage_view(PROJECT_ID)


def test_unknown_support_node_reference_fails_closed() -> None:
    assessment = coverage_assessment()
    bad_support = support(required_nodes=("FW_UNKNOWN",))
    modified = ProjectCoverageAssessment(
        project_id=assessment.project_id,
        framework_template_id=assessment.framework_template_id,
        framework_template_version=assessment.framework_template_version,
        support_profile_id=assessment.support_profile_id,
        support_profile_version=assessment.support_profile_version,
        project_coverage_state=assessment.project_coverage_state,
        node_coverages=assessment.node_coverages,
        level_coverages=assessment.level_coverages,
        support_assessments=(bad_support,),
        approved_readiness_status=assessment.approved_readiness_status,
        approved_readiness_available_from_phase=assessment.approved_readiness_available_from_phase,
        assessment_algorithm_id=assessment.assessment_algorithm_id,
        assessment_algorithm_version=assessment.assessment_algorithm_version,
        assessment_input_fingerprint=assessment.assessment_input_fingerprint,
        issues=assessment.issues,
    )
    with pytest.raises(DashboardPresentationError):
        dashboard_service(coverage=modified).coverage_view(PROJECT_ID)


def test_detail_service_calls_exact_project_id() -> None:
    selected = dashboard_service()
    selected.source_processing_view(PROJECT_ID)
    selected.coverage_view(PROJECT_ID)
    assert selected.workspace.calls == [PROJECT_ID, PROJECT_ID]
    assert selected.source_registry.calls == [PROJECT_ID]
    assert selected.processing_summary_service.calls == [PROJECT_ID]
    assert selected.coverage_service.calls == [PROJECT_ID]


@pytest.mark.parametrize("project_id", ("31860", "3186040", "ABC604", 318604, None))
def test_detail_views_reject_invalid_project_id_before_dependencies(
    project_id: object,
) -> None:
    selected = dashboard_service()
    with pytest.raises(DashboardValidationError):
        selected.source_processing_view(project_id)  # type: ignore[arg-type]
    with pytest.raises(DashboardValidationError):
        selected.coverage_view(project_id)  # type: ignore[arg-type]
    assert selected.workspace.calls == []


def test_node_factory_allows_auditable_excluded_candidate_ids() -> None:
    selected = node_view()
    assert selected.assignment_candidate_count == 1
    assert len(selected.framework_assignment_candidate_ids) == 2


def test_node_factory_rejects_covering_count_larger_than_candidate_ids() -> None:
    with pytest.raises(DashboardValidationError):
        node_view(
            assignment_candidate_count=2,
            confirmed_candidate_count=2,
            framework_assignment_candidate_ids=("FAC-000001",),
        )


def test_support_factory_rejects_incomplete_partition() -> None:
    with pytest.raises(DashboardValidationError):
        support_view(
            required_framework_node_ids=("NODE_A", "NODE_B"),
            covered_framework_node_ids=("NODE_A",),
            missing_framework_node_ids=(),
        )


def test_coverage_view_orders_by_explicit_display_order() -> None:
    first_level = level_view(display_order=2, level_node_id="LEVEL_B")
    second_level = level_view(
        display_order=1,
        level_node_id="LEVEL_A",
        covered_node_ids=("NODE_A",),
    )
    first_node = node_view(
        display_order=2,
        framework_node_id="NODE_B",
        level_node_id="LEVEL_B",
    )
    second_node = node_view(
        display_order=1,
        framework_node_id="NODE_A",
        level_node_id="LEVEL_A",
    )
    view = make_coverage_view(
        project_id=PROJECT_ID,
        project_coverage_state="covered",
        framework_template_id=FRAMEWORK_ID,
        framework_template_version=FRAMEWORK_VERSION,
        support_profile_id=SUPPORT_PROFILE_ID,
        support_profile_version=SUPPORT_PROFILE_VERSION,
        levels=(first_level, second_level),
        nodes=(first_node, second_node),
        support_targets=(support_view(),),
        approved_readiness_status="not_available",
        approved_readiness_available_from_phase="G",
    )
    assert tuple(item.level_node_id for item in view.levels) == ("LEVEL_A", "LEVEL_B")
    assert tuple(item.framework_node_id for item in view.nodes) == ("NODE_A", "NODE_B")


def test_public_api_exports_step_four_contracts() -> None:
    for name in (
        "DashboardCoverageView",
        "DashboardFrameworkLevelCoverage",
        "DashboardFrameworkNodeCoverage",
        "DashboardPotentialSupport",
        "DashboardSourceProcessingRow",
        "DashboardSourceProcessingView",
        "make_coverage_view",
        "make_framework_level_coverage_view",
        "make_framework_node_coverage_view",
        "make_potential_support_view",
        "make_source_processing_row",
        "make_source_processing_view",
        "validate_coverage_view",
        "validate_framework_level_coverage_view",
        "validate_framework_node_coverage_view",
        "validate_potential_support_view",
        "validate_source_processing_row",
        "validate_source_processing_view",
    ):
        assert hasattr(public_api, name), name


def test_detail_views_are_deterministic() -> None:
    selected = dashboard_service()
    assert selected.source_processing_view(PROJECT_ID) == selected.source_processing_view(PROJECT_ID)
    assert selected.coverage_view(PROJECT_ID) == selected.coverage_view(PROJECT_ID)
