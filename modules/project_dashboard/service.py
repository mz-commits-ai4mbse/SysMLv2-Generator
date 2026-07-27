
"""Read-only coordination service for P7 project selection and overview."""

from __future__ import annotations

from pathlib import Path, PurePosixPath
import hashlib
from typing import Iterable

from modules.project_coverage import ProjectCoverageService
from modules.human_review.repository import HumanReviewRepository
from modules.human_review.types import HumanReviewScanResult
from modules.project_coverage.types import ProjectCoverageAssessment
from modules.project_processing import (
    ProcessingArtifactReference,
    ProjectProcessingRepository,
    ProjectProcessingSummaryService,
)
from modules.project_sources import ProjectSourceRegistry
from modules.project_sources.types import SourceIssue, SourceManifest, SourceScanResult
from modules.project_processing.types import ProjectProcessingSummary
from modules.project_workspace import ProjectWorkspace
from modules.project_workspace.identifiers import is_valid_project_id
from modules.project_workspace.types import ProjectManifest, WorkspaceIssue

from modules.project_dashboard.errors import (
    DashboardPresentationError,
    DashboardReferenceError,
    DashboardValidationError,
)
from modules.project_dashboard.presenter import (
    make_attention_review_view,
    make_coverage_view,
    make_dashboard_value,
    make_framework_level_coverage_view,
    make_framework_node_coverage_view,
    make_human_review_row,
    make_issue_view,
    make_potential_support_view,
    make_project_option,
    make_project_overview,
    make_project_selection,
    make_section_view,
    make_source_processing_row,
    make_source_processing_view,
    make_traceability_edge,
    make_traceability_node,
    make_traceability_view,
    present_status,
)
from modules.project_dashboard.types import (
    DashboardAttentionReviewView,
    DashboardCoverageView,
    DashboardFrameworkNodeCoverage,
    DashboardHumanReviewRow,
    DashboardIssueView,
    DashboardProjectOption,
    DashboardProjectSelection,
    DashboardSourceProcessingView,
    DashboardTraceabilityEdge,
    DashboardTraceabilityNode,
    DashboardTraceabilityView,
    EvidenceReference,
    ProjectOverviewView,
)


DEFAULT_PROJECTS_ROOT = Path("data/projects")
DEFAULT_FRAMEWORK_TEMPLATE_PATH = Path(
    "context/frameworks/turing_rflp_framework.json"
)
DEFAULT_SUPPORT_PROFILE_PATH = Path(
    "context/frameworks/turing_preliminary_support_profile.json"
)
PROJECT_MANIFEST_FILENAME = "project_manifest.json"
SOURCE_MANIFEST_FILENAME = "source_manifest.json"
PROCESSING_RUN_MANIFEST_FILENAME = "run_manifest.json"


class ProjectDashboardService:
    """Compose P2, P5 and P6 read APIs into dashboard view models."""

    def __init__(
        self,
        root: Path | str = DEFAULT_PROJECTS_ROOT,
        *,
        repository_root: Path | str = Path("."),
        workspace: object | None = None,
        source_registry: object | None = None,
        processing_summary_service: object | None = None,
        processing_repository: object | None = None,
        coverage_service: object | None = None,
        human_review_repository: object | None = None,
    ) -> None:
        self.root = Path(root)
        self.repository_root = Path(repository_root)
        self.workspace = (
            ProjectWorkspace(root=self.root)
            if workspace is None
            else workspace
        )
        self.source_registry = (
            ProjectSourceRegistry(root=self.root)
            if source_registry is None
            else source_registry
        )
        self.processing_summary_service = (
            ProjectProcessingSummaryService(root=self.root)
            if processing_summary_service is None
            else processing_summary_service
        )
        self.processing_repository = (
            ProjectProcessingRepository(root=self.root)
            if processing_repository is None
            else processing_repository
        )
        self.human_review_repository = (
            HumanReviewRepository(root=self.root)
            if human_review_repository is None
            else human_review_repository
        )
        self.coverage_service = (
            ProjectCoverageService(
                root=self.root,
                repository_root=self.repository_root,
            )
            if coverage_service is None
            else coverage_service
        )

    def list_projects(self) -> DashboardProjectSelection:
        """Return all valid projects and explicit workspace scan issues."""

        scan = self.workspace.scan_projects()
        projects = tuple(
            self._project_option(manifest)
            for manifest in scan.valid_projects
        )
        issues = tuple(
            self._workspace_issue_view(issue)
            for issue in scan.workspace_issues
        )
        return make_project_selection(
            projects=projects,
            issues=issues,
        )

    def project_overview(
        self,
        project_id: str,
    ) -> ProjectOverviewView:
        """Return a compact, fail-closed Project Overview."""

        validated_project_id = _require_project_id(project_id)
        manifest = self.workspace.load_project(validated_project_id)
        project = self._project_option(manifest)

        values = [
            make_dashboard_value(
                value_id="project_identity",
                label="Project",
                primary_text=manifest.display_name,
                secondary_text=manifest.project_id,
                evidence_references=(
                    self._project_manifest_reference(manifest),
                ),
            ),
            make_dashboard_value(
                value_id="framework_template",
                label="Framework Template",
                primary_text=(
                    f"{manifest.framework_template.template_id} "
                    f"v{manifest.framework_template.template_version}"
                ),
                secondary_text="Pinned by the Project Manifest",
                evidence_references=(
                    self._project_manifest_reference(manifest),
                    self._framework_template_reference(manifest),
                ),
            ),
        ]
        issues: list[DashboardIssueView] = []

        processing_summary = self._load_processing_summary(
            validated_project_id,
            issues,
        )
        if processing_summary is None:
            unavailable = present_status(
                "not_available",
                label="Unavailable",
                explanation=(
                    "The Processing State summary could not be loaded."
                ),
            )
            values.extend(
                (
                    make_dashboard_value(
                        value_id="processing_state",
                        label="Processing State",
                        primary_text="Unavailable",
                        status=unavailable,
                    ),
                    make_dashboard_value(
                        value_id="registered_sources",
                        label="Registered Sources",
                        primary_text="Unavailable",
                        status=unavailable,
                    ),
                )
            )
        else:
            processing_evidence = self._processing_evidence(
                processing_summary
            )
            values.extend(
                (
                    make_dashboard_value(
                        value_id="processing_state",
                        label="Processing State",
                        primary_text=present_status(
                            processing_summary.project_state
                        ).label,
                        secondary_text=self._processing_secondary_text(
                            processing_summary
                        ),
                        status=present_status(
                            processing_summary.project_state
                        ),
                        evidence_references=processing_evidence,
                    ),
                    make_dashboard_value(
                        value_id="registered_sources",
                        label="Registered Sources",
                        primary_text=str(
                            processing_summary.total_sources
                        ),
                        secondary_text=(
                            f"{processing_summary.in_scope_sources} in scope · "
                            f"{processing_summary.context_only_sources} context only · "
                            f"{processing_summary.out_of_scope_sources} out of scope"
                        ),
                        evidence_references=self._source_manifest_references(
                            processing_summary
                        ),
                    ),
                )
            )
            issues.extend(
                self._processing_issue_views(processing_summary)
            )

        coverage_assessment = self._load_coverage_assessment(
            validated_project_id,
            issues,
        )
        if coverage_assessment is None:
            unavailable = present_status(
                "not_available",
                label="Unavailable",
                explanation=(
                    "The Preliminary Coverage assessment could not be loaded."
                ),
            )
            values.extend(
                (
                    make_dashboard_value(
                        value_id="preliminary_coverage",
                        label="Preliminary Coverage",
                        primary_text="Unavailable",
                        status=unavailable,
                    ),
                    make_dashboard_value(
                        value_id="approved_generation_readiness",
                        label="Approved Generation Readiness",
                        primary_text="Unavailable",
                        status=unavailable,
                    ),
                )
            )
        else:
            coverage_evidence = self._coverage_evidence(
                manifest,
                processing_summary,
                coverage_assessment,
            )
            values.extend(
                (
                    make_dashboard_value(
                        value_id="preliminary_coverage",
                        label="Preliminary Coverage",
                        primary_text=present_status(
                            coverage_assessment.project_coverage_state
                        ).label,
                        secondary_text=self._coverage_secondary_text(
                            coverage_assessment
                        ),
                        status=present_status(
                            coverage_assessment.project_coverage_state
                        ),
                        evidence_references=coverage_evidence,
                    ),
                    make_dashboard_value(
                        value_id="support_profile",
                        label="Preliminary Support Profile",
                        primary_text=(
                            f"{coverage_assessment.support_profile_id} "
                            f"v{coverage_assessment.support_profile_version}"
                        ),
                        evidence_references=(
                            self._support_profile_reference(
                                validated_project_id,
                                coverage_assessment,
                            ),
                        ),
                    ),
                    make_dashboard_value(
                        value_id="approved_generation_readiness",
                        label="Approved Generation Readiness",
                        primary_text=present_status(
                            coverage_assessment.approved_readiness_status
                        ).label,
                        secondary_text=(
                            "Available from Phase "
                            f"{coverage_assessment.approved_readiness_available_from_phase}"
                        ),
                        status=present_status(
                            coverage_assessment.approved_readiness_status,
                            explanation=(
                                "Approved Generation Readiness is not assessed "
                                "in Phase P."
                            ),
                        ),
                        evidence_references=coverage_evidence,
                    ),
                )
            )
            for assessment in coverage_assessment.support_assessments:
                values.append(
                    make_dashboard_value(
                        value_id=(
                            "support_"
                            + _normalize_identifier(
                                assessment.support_target_id
                            )
                        ),
                        label=assessment.name,
                        primary_text=present_status(
                            assessment.support_state
                        ).label,
                        secondary_text=(
                            f"{len(assessment.covered_framework_node_ids)} of "
                            f"{len(assessment.required_framework_node_ids)} "
                            "required framework nodes covered"
                        ),
                        status=present_status(
                            assessment.support_state
                        ),
                        evidence_references=coverage_evidence,
                    )
                )
            issues.extend(
                self._coverage_issue_views(coverage_assessment)
            )

        blocking_count = sum(
            issue.issue_level == "blocking" for issue in issues
        )
        warning_count = sum(
            issue.issue_level == "warning" for issue in issues
        )
        attention_status = (
            present_status(
                "attention_required",
                label="Attention required",
            )
            if blocking_count or warning_count
            else present_status("clear")
        )
        values.append(
            make_dashboard_value(
                value_id="attention_summary",
                label="Attention",
                primary_text=(
                    f"{blocking_count} blocking · {warning_count} warning"
                ),
                status=attention_status,
                evidence_references=_collect_issue_evidence(issues),
            )
        )

        section = make_section_view(
            section_id="project_overview",
            title="Project Overview",
            description=(
                "Read-only project status derived from P2, P5 and P6."
            ),
            values=values,
            issues=issues,
        )
        return make_project_overview(
            project=project,
            section=section,
        )

    def source_processing_view(
        self,
        project_id: str,
    ) -> DashboardSourceProcessingView:
        """Return the detailed read-only Sources and Processing view."""

        validated_project_id = _require_project_id(project_id)
        self.workspace.load_project(validated_project_id)
        source_scan = self._load_source_scan_strict(validated_project_id)
        processing_summary = self.processing_summary_service.project_summary(
            validated_project_id
        )
        if not isinstance(processing_summary, ProjectProcessingSummary):
            raise DashboardPresentationError(
                "processing_summary_service returned an invalid type."
            )
        if processing_summary.project_id != validated_project_id:
            raise DashboardPresentationError(
                "Processing summary belongs to another project."
            )

        source_by_id = {
            source.source_id: source
            for source in source_scan.valid_sources
        }
        summary_by_id = {
            summary.source_id: summary
            for summary in processing_summary.source_summaries
        }
        if set(source_by_id) != set(summary_by_id):
            raise DashboardPresentationError(
                "Source scan and Processing summary disagree on registered Sources."
            )

        rows = tuple(
            make_source_processing_row(
                project_id=validated_project_id,
                source_id=source.source_id,
                original_filename=source.original_filename,
                source_role=source.source_role,
                media_type=source.media_type,
                size_bytes=source.size_bytes,
                sha256=source.sha256,
                processing_disposition=(
                    summary_by_id[source.source_id].processing_disposition
                ),
                current_processing_run_id=(
                    summary_by_id[source.source_id].current_processing_run_id
                ),
                run_state=summary_by_id[source.source_id].run_state,
                processing_stage=(
                    summary_by_id[source.source_id].processing_stage
                ),
                latest_attempt_id=(
                    summary_by_id[source.source_id].latest_attempt_id
                ),
                pending_review=(
                    summary_by_id[source.source_id].pending_review
                ),
                superseded_run_ids=(
                    summary_by_id[source.source_id].superseded_run_ids
                ),
                invalidated_artifact_count=(
                    summary_by_id[source.source_id].invalidated_artifact_count
                ),
                blocking_issue_codes=(
                    summary_by_id[source.source_id].blocking_issue_codes
                ),
                failure_issue_codes=(
                    summary_by_id[source.source_id].failure_issue_codes
                ),
                evidence_references=self._source_processing_row_evidence(
                    source,
                    summary_by_id[source.source_id],
                ),
            )
            for source in source_scan.valid_sources
        )
        issues = (
            self._source_issue_views(source_scan)
            + self._processing_issue_views(processing_summary)
        )
        return make_source_processing_view(
            project_id=validated_project_id,
            project_state=processing_summary.project_state,
            sources=rows,
            issues=issues,
        )

    def coverage_view(
        self,
        project_id: str,
    ) -> DashboardCoverageView:
        """Return detailed Preliminary Coverage and potential support."""

        validated_project_id = _require_project_id(project_id)
        manifest = self.workspace.load_project(validated_project_id)
        assessment = self.coverage_service.assess_project(
            validated_project_id
        )
        if not isinstance(assessment, ProjectCoverageAssessment):
            raise DashboardPresentationError(
                "coverage_service returned an invalid type."
            )
        if assessment.project_id != validated_project_id:
            raise DashboardPresentationError(
                "Coverage assessment belongs to another project."
            )
        if (
            assessment.framework_template_id
            != manifest.framework_template.template_id
            or assessment.framework_template_version
            != manifest.framework_template.template_version
        ):
            raise DashboardPresentationError(
                "Coverage assessment and Project Manifest disagree on Framework Template."
            )

        node_views: list[DashboardFrameworkNodeCoverage] = []
        node_by_id = {}
        for order, node in enumerate(assessment.node_coverages, start=1):
            node_view = make_framework_node_coverage_view(
                display_order=order,
                framework_node_id=node.framework_node_id,
                mapping_key=node.mapping_key,
                node_name=node.node_name,
                level_node_id=node.level_node_id,
                coverage_state=node.coverage_state,
                attention_required=node.attention_required,
                eligible_source_count=node.eligible_source_count,
                information_unit_count=node.information_unit_count,
                assignment_candidate_count=node.assignment_candidate_count,
                confirmed_candidate_count=node.confirmed_candidate_count,
                unreviewed_candidate_count=node.unreviewed_candidate_count,
                rejected_candidate_count=node.rejected_candidate_count,
                ambiguous_candidate_count=node.ambiguous_candidate_count,
                conflicting_candidate_count=node.conflicting_candidate_count,
                source_ids=node.source_ids,
                information_unit_ids=node.information_unit_ids,
                framework_assignment_candidate_ids=(
                    node.framework_assignment_candidate_ids
                ),
                human_review_decision_ids=(
                    node.human_review_decision_ids
                ),
                issue_codes=node.issue_codes,
                evidence_references=self._node_coverage_evidence(
                    validated_project_id,
                    node,
                    manifest,
                ),
            )
            node_views.append(node_view)
            node_by_id[node.framework_node_id] = node_view

        level_views = tuple(
            make_framework_level_coverage_view(
                display_order=order,
                level_node_id=level.level_node_id,
                level_name=level.level_name,
                coverage_state=level.coverage_state,
                covered_node_count=level.covered_node_count,
                total_node_count=level.total_node_count,
                candidate_covered_node_count=(
                    level.candidate_covered_node_count
                ),
                reviewed_candidate_covered_node_count=(
                    level.reviewed_candidate_covered_node_count
                ),
                attention_node_count=level.attention_node_count,
                covered_node_ids=level.covered_node_ids,
                uncovered_node_ids=level.uncovered_node_ids,
                attention_node_ids=level.attention_node_ids,
                evidence_references=self._level_coverage_evidence(
                    validated_project_id,
                    level.covered_node_ids
                    + level.uncovered_node_ids,
                    node_by_id,
                    manifest,
                ),
            )
            for order, level in enumerate(
                assessment.level_coverages,
                start=1,
            )
        )

        support_views = tuple(
            make_potential_support_view(
                display_order=order,
                support_target_id=support.support_target_id,
                name=support.name,
                support_target_type=support.support_target_type,
                support_state=support.support_state,
                required_framework_node_ids=(
                    support.required_framework_node_ids
                ),
                covered_framework_node_ids=(
                    support.covered_framework_node_ids
                ),
                missing_framework_node_ids=(
                    support.missing_framework_node_ids
                ),
                required_support_target_ids=(
                    support.required_support_target_ids
                ),
                satisfied_support_target_ids=(
                    support.satisfied_support_target_ids
                ),
                unsatisfied_support_target_ids=(
                    support.unsatisfied_support_target_ids
                ),
                attention_required=support.attention_required,
                issue_codes=support.issue_codes,
                evidence_references=self._support_evidence(
                    validated_project_id,
                    support.required_framework_node_ids,
                    node_by_id,
                    assessment,
                    manifest,
                ),
            )
            for order, support in enumerate(
                assessment.support_assessments,
                start=1,
            )
        )

        return make_coverage_view(
            project_id=validated_project_id,
            project_coverage_state=assessment.project_coverage_state,
            framework_template_id=assessment.framework_template_id,
            framework_template_version=assessment.framework_template_version,
            support_profile_id=assessment.support_profile_id,
            support_profile_version=assessment.support_profile_version,
            levels=level_views,
            nodes=node_views,
            support_targets=support_views,
            approved_readiness_status=assessment.approved_readiness_status,
            approved_readiness_available_from_phase=(
                assessment.approved_readiness_available_from_phase
            ),
            issues=self._coverage_issue_views(assessment),
        )

    def attention_review_view(
        self,
        project_id: str,
    ) -> DashboardAttentionReviewView:
        """Return combined attention diagnostics and exact Human Review rows."""

        validated_project_id = _require_project_id(project_id)
        self.workspace.load_project(validated_project_id)

        processing_summary = self.processing_summary_service.project_summary(
            validated_project_id
        )
        if not isinstance(processing_summary, ProjectProcessingSummary):
            raise DashboardPresentationError(
                "processing_summary_service returned an invalid type."
            )
        if processing_summary.project_id != validated_project_id:
            raise DashboardPresentationError(
                "Processing summary belongs to another project."
            )

        coverage_assessment = self.coverage_service.assess_project(
            validated_project_id
        )
        if not isinstance(
            coverage_assessment,
            ProjectCoverageAssessment,
        ):
            raise DashboardPresentationError(
                "coverage_service returned an invalid type."
            )
        if coverage_assessment.project_id != validated_project_id:
            raise DashboardPresentationError(
                "Coverage assessment belongs to another project."
            )

        review_scan = self.human_review_repository.scan_decisions(
            validated_project_id
        )
        if not isinstance(review_scan, HumanReviewScanResult):
            raise DashboardPresentationError(
                "human_review_repository returned an invalid type."
            )

        reviews = tuple(
            self._human_review_row(validated_project_id, decision)
            for decision in review_scan.decisions
        )
        issues = (
            self._processing_issue_views(processing_summary)
            + self._coverage_issue_views(coverage_assessment)
            + self._human_review_issue_views(review_scan)
        )
        return make_attention_review_view(
            project_id=validated_project_id,
            reviews=reviews,
            issues=issues,
        )

    def traceability_view(
        self,
        project_id: str,
    ) -> DashboardTraceabilityView:
        """Return a deterministic evidence graph from Source to support scope."""

        validated_project_id = _require_project_id(project_id)
        manifest = self.workspace.load_project(validated_project_id)

        bundle = self.coverage_service.collect_inputs(
            validated_project_id
        )
        assessment = self.coverage_service.assess_project(
            validated_project_id
        )
        if not isinstance(assessment, ProjectCoverageAssessment):
            raise DashboardPresentationError(
                "coverage_service returned an invalid assessment type."
            )
        if assessment.project_id != validated_project_id:
            raise DashboardPresentationError(
                "Coverage assessment belongs to another project."
            )

        review_scan = self.human_review_repository.scan_decisions(
            validated_project_id
        )
        if not isinstance(review_scan, HumanReviewScanResult):
            raise DashboardPresentationError(
                "human_review_repository returned an invalid type."
            )

        nodes: dict[str, DashboardTraceabilityNode] = {}
        edges: dict[str, DashboardTraceabilityEdge] = {}

        def add_node(node: DashboardTraceabilityNode) -> None:
            existing = nodes.get(node.node_key)
            if existing is not None and existing != node:
                raise DashboardPresentationError(
                    "Traceability node identity has conflicting metadata."
                )
            nodes[node.node_key] = node

        def add_edge(edge: DashboardTraceabilityEdge) -> None:
            existing = edges.get(edge.edge_key)
            if existing is not None and existing != edge:
                raise DashboardPresentationError(
                    "Traceability edge identity has conflicting metadata."
                )
            edges[edge.edge_key] = edge

        source_by_id = {}
        for source in tuple(getattr(bundle, "source_manifests", ())):
            if getattr(source, "project_id", None) != validated_project_id:
                raise DashboardPresentationError(
                    "Traceability Source belongs to another project."
                )
            source_by_id[source.source_id] = source
            add_node(
                make_traceability_node(
                    node_type="source",
                    node_id=source.source_id,
                    label=source.original_filename,
                    secondary_text=(
                        f"{source.source_role} · {source.source_id}"
                    ),
                    status=present_status(source.source_role),
                    evidence_references=(
                        self._source_manifest_reference_from_manifest(source),
                        self._source_content_reference(source),
                    ),
                )
            )

        summary_by_source = {}
        for summary in tuple(
            getattr(bundle, "source_processing_summaries", ())
        ):
            if getattr(summary, "project_id", None) != validated_project_id:
                raise DashboardPresentationError(
                    "Traceability Processing summary belongs to another project."
                )
            summary_by_source[summary.source_id] = summary
            if summary.current_processing_run_id is not None:
                run_node = make_traceability_node(
                    node_type="processing_run",
                    node_id=summary.current_processing_run_id,
                    label=summary.current_processing_run_id,
                    secondary_text=summary.processing_stage,
                    status=present_status(summary.run_state),
                    evidence_references=(
                        self._run_manifest_reference(
                            validated_project_id,
                            summary.current_processing_run_id,
                            relationship="records_processing",
                            evidence_role="direct",
                        ),
                    ),
                )
                add_node(run_node)
                source_key = f"source:{summary.source_id}"
                if source_key in nodes:
                    add_edge(
                        make_traceability_edge(
                            source_node_key=source_key,
                            target_node_key=run_node.node_key,
                            relationship="processed_by",
                            label="Processed by",
                        )
                    )

        information_unit_by_id = {}
        for unit in tuple(getattr(bundle, "information_units", ())):
            if getattr(unit, "project_id", None) != validated_project_id:
                raise DashboardPresentationError(
                    "Traceability Information Unit belongs to another project."
                )
            information_unit_by_id[unit.information_unit_id] = unit
            projection_node = make_traceability_node(
                node_type="source_projection",
                node_id=unit.source_projection_id,
                label=unit.source_projection_id,
                secondary_text="Source Projection",
                evidence_references=self._source_projection_references(
                    validated_project_id,
                    unit.source_projection_id,
                ),
            )
            add_node(projection_node)
            unit_node = make_traceability_node(
                node_type="information_unit",
                node_id=unit.information_unit_id,
                label=unit.interpreted_statement,
                secondary_text=(
                    f"{unit.information_type} · {unit.confidence}"
                ),
                evidence_references=(
                    self._information_unit_reference(
                        validated_project_id,
                        unit.information_unit_id,
                        content_fingerprint=unit.content_fingerprint,
                    ),
                ),
            )
            add_node(unit_node)
            source_key = f"source:{unit.source_id}"
            if source_key not in nodes:
                raise DashboardPresentationError(
                    "Information Unit references an unknown Source."
                )
            add_edge(
                make_traceability_edge(
                    source_node_key=source_key,
                    target_node_key=projection_node.node_key,
                    relationship="projected_as",
                    label="Projected as",
                )
            )
            add_edge(
                make_traceability_edge(
                    source_node_key=projection_node.node_key,
                    target_node_key=unit_node.node_key,
                    relationship="contains",
                    label="Contains",
                )
            )
            summary = summary_by_source.get(unit.source_id)
            if (
                summary is not None
                and summary.current_processing_run_id is not None
            ):
                add_edge(
                    make_traceability_edge(
                        source_node_key=(
                            "processing_run:"
                            f"{summary.current_processing_run_id}"
                        ),
                        target_node_key=unit_node.node_key,
                        relationship="produced",
                        label="Produced",
                    )
                )

        candidate_by_id = {}
        for candidate in tuple(
            getattr(bundle, "framework_assignment_candidates", ())
        ):
            if getattr(candidate, "project_id", None) != validated_project_id:
                raise DashboardPresentationError(
                    "Traceability assignment Candidate belongs to another project."
                )
            candidate_by_id[
                candidate.framework_assignment_candidate_id
            ] = candidate
            candidate_node = make_traceability_node(
                node_type="framework_assignment_candidate",
                node_id=candidate.framework_assignment_candidate_id,
                label=candidate.framework_assignment_candidate_id,
                secondary_text=(
                    f"{candidate.assignment_status} · "
                    f"{candidate.confidence} confidence"
                ),
                status=present_status(candidate.assignment_status),
                evidence_references=(
                    self._framework_assignment_reference(
                        validated_project_id,
                        candidate.framework_assignment_candidate_id,
                        content_fingerprint=candidate.content_fingerprint,
                    ),
                ),
            )
            add_node(candidate_node)
            unit_key = f"information_unit:{candidate.information_unit_id}"
            if unit_key not in nodes:
                raise DashboardPresentationError(
                    "Framework Assignment Candidate references an unknown "
                    "Information Unit."
                )
            add_edge(
                make_traceability_edge(
                    source_node_key=unit_key,
                    target_node_key=candidate_node.node_key,
                    relationship="assigned_by",
                    label="Assigned by",
                )
            )
            for terminology_id in sorted(
                candidate.terminology_mapping_candidate_ids
            ):
                terminology_node = make_traceability_node(
                    node_type="terminology_mapping_candidate",
                    node_id=terminology_id,
                    label=terminology_id,
                    secondary_text="Terminology Mapping Candidate",
                    evidence_references=(
                        self._terminology_mapping_reference(
                            validated_project_id,
                            terminology_id,
                        ),
                    ),
                )
                add_node(terminology_node)
                add_edge(
                    make_traceability_edge(
                        source_node_key=unit_key,
                        target_node_key=terminology_node.node_key,
                        relationship="mapped_by",
                        label="Mapped by",
                    )
                )
                add_edge(
                    make_traceability_edge(
                        source_node_key=terminology_node.node_key,
                        target_node_key=candidate_node.node_key,
                        relationship="supports",
                        label="Supports",
                    )
                )

            for proposal in candidate.proposals:
                framework_node_id = proposal.framework_node_id
                coverage = next(
                    (
                        item
                        for item in assessment.node_coverages
                        if item.framework_node_id == framework_node_id
                    ),
                    None,
                )
                if coverage is None:
                    raise DashboardPresentationError(
                        "Framework Assignment Candidate references an "
                        "unknown assessed Framework Node."
                    )
                framework_node = make_traceability_node(
                    node_type="framework_node",
                    node_id=coverage.framework_node_id,
                    label=coverage.node_name,
                    secondary_text=coverage.mapping_key,
                    status=present_status(coverage.coverage_state),
                    evidence_references=self._node_coverage_evidence(
                        validated_project_id,
                        coverage,
                        manifest,
                    ),
                )
                add_node(framework_node)
                add_edge(
                    make_traceability_edge(
                        source_node_key=candidate_node.node_key,
                        target_node_key=framework_node.node_key,
                        relationship="proposes",
                        label="Proposes",
                    )
                )

        for coverage in assessment.node_coverages:
            key = f"framework_node:{coverage.framework_node_id}"
            if key not in nodes:
                add_node(
                    make_traceability_node(
                        node_type="framework_node",
                        node_id=coverage.framework_node_id,
                        label=coverage.node_name,
                        secondary_text=coverage.mapping_key,
                        status=present_status(coverage.coverage_state),
                        evidence_references=self._node_coverage_evidence(
                            validated_project_id,
                            coverage,
                            manifest,
                        ),
                    )
                )

        for support in assessment.support_assessments:
            support_node = make_traceability_node(
                node_type="support_target",
                node_id=support.support_target_id,
                label=support.name,
                secondary_text=support.support_target_type,
                status=present_status(support.support_state),
                evidence_references=self._support_evidence_from_assessment(
                    validated_project_id,
                    support,
                    assessment,
                    manifest,
                ),
            )
            add_node(support_node)
            for node_id in support.required_framework_node_ids:
                node_key = f"framework_node:{node_id}"
                if node_key not in nodes:
                    raise DashboardPresentationError(
                        "Support Target references an unknown Framework Node."
                    )
                add_edge(
                    make_traceability_edge(
                        source_node_key=node_key,
                        target_node_key=support_node.node_key,
                        relationship="required_by",
                        label="Required by",
                    )
                )

        for support in assessment.support_assessments:
            target_key = f"support_target:{support.support_target_id}"
            for dependency_id in support.required_support_target_ids:
                dependency_key = f"support_target:{dependency_id}"
                if dependency_key not in nodes:
                    raise DashboardPresentationError(
                        "Support dependency references an unknown target."
                    )
                add_edge(
                    make_traceability_edge(
                        source_node_key=dependency_key,
                        target_node_key=target_key,
                        relationship="prerequisite_for",
                        label="Prerequisite for",
                    )
                )

        for decision in review_scan.decisions:
            review_node = make_traceability_node(
                node_type="human_review_decision",
                node_id=decision.human_review_decision_id,
                label=decision.human_review_decision_id,
                secondary_text=(
                    f"{decision.decision} · {decision.reviewer_identity}"
                ),
                status=present_status(decision.decision),
                evidence_references=(
                    self._human_review_reference(decision),
                    self._human_review_target_reference(
                        validated_project_id,
                        decision.target,
                    ),
                ),
            )
            add_node(review_node)
            target_key = self._trace_target_node_key(
                decision.target.target_type,
                decision.target.target_id,
            )
            if target_key not in nodes:
                add_node(
                    self._placeholder_target_node(
                        validated_project_id,
                        decision.target,
                    )
                )
            add_edge(
                make_traceability_edge(
                    source_node_key=target_key,
                    target_node_key=review_node.node_key,
                    relationship="reviewed_by",
                    label="Reviewed by",
                )
            )

        issues = (
            self._coverage_issue_views(assessment)
            + self._human_review_issue_views(review_scan)
        )
        return make_traceability_view(
            project_id=validated_project_id,
            nodes=nodes.values(),
            edges=edges.values(),
            issues=issues,
        )

    def _project_option(
        self,
        manifest: ProjectManifest,
    ) -> DashboardProjectOption:
        return make_project_option(
            project_id=manifest.project_id,
            display_name=manifest.display_name,
            description=manifest.description,
            framework_template_id=(
                manifest.framework_template.template_id
            ),
            framework_template_version=(
                manifest.framework_template.template_version
            ),
            evidence_references=(
                self._project_manifest_reference(manifest),
            ),
        )

    def _load_processing_summary(
        self,
        project_id: str,
        issues: list[DashboardIssueView],
    ) -> ProjectProcessingSummary | None:
        try:
            value = self.processing_summary_service.project_summary(
                project_id
            )
        except Exception as exc:
            issues.append(
                make_issue_view(
                    issue_code=(
                        "dashboard.processing_summary_unavailable"
                    ),
                    message=(
                        "Unable to load the Project Processing summary: "
                        f"{type(exc).__name__}."
                    ),
                    issue_level="blocking",
                )
            )
            return None
        if not isinstance(value, ProjectProcessingSummary):
            raise DashboardPresentationError(
                "processing_summary_service returned an invalid type."
            )
        if value.project_id != project_id:
            raise DashboardPresentationError(
                "Processing summary belongs to another project."
            )
        return value

    def _load_coverage_assessment(
        self,
        project_id: str,
        issues: list[DashboardIssueView],
    ) -> ProjectCoverageAssessment | None:
        try:
            value = self.coverage_service.assess_project(project_id)
        except Exception as exc:
            issues.append(
                make_issue_view(
                    issue_code=(
                        "dashboard.coverage_assessment_unavailable"
                    ),
                    message=(
                        "Unable to load the Preliminary Coverage assessment: "
                        f"{type(exc).__name__}."
                    ),
                    issue_level="blocking",
                )
            )
            return None
        if not isinstance(value, ProjectCoverageAssessment):
            raise DashboardPresentationError(
                "coverage_service returned an invalid type."
            )
        if value.project_id != project_id:
            raise DashboardPresentationError(
                "Coverage assessment belongs to another project."
            )
        return value

    def _project_manifest_reference(
        self,
        manifest: ProjectManifest,
    ) -> EvidenceReference:
        return EvidenceReference(
            project_id=manifest.project_id,
            reference_type="project_manifest",
            reference_id=manifest.project_id,
            display_label=(
                f"Project Manifest · {manifest.display_name}"
            ),
            repository_relative_path=(
                f"data/projects/{manifest.project_id}/"
                f"{PROJECT_MANIFEST_FILENAME}"
            ),
            content_fingerprint=None,
            media_type="application/json",
            source_role=None,
            relationship="defines_project",
            evidence_role="direct",
        )

    def _framework_template_reference(
        self,
        manifest: ProjectManifest,
    ) -> EvidenceReference:
        return EvidenceReference(
            project_id=manifest.project_id,
            reference_type="framework_template",
            reference_id=(
                f"{manifest.framework_template.template_id}:"
                f"{manifest.framework_template.template_version}"
            ),
            display_label=(
                f"Framework Template · "
                f"{manifest.framework_template.template_id} "
                f"v{manifest.framework_template.template_version}"
            ),
            repository_relative_path=(
                DEFAULT_FRAMEWORK_TEMPLATE_PATH.as_posix()
            ),
            content_fingerprint=None,
            media_type="application/json",
            source_role=None,
            relationship="defines_framework",
            evidence_role="contextual",
        )

    def _support_profile_reference(
        self,
        project_id: str,
        assessment: ProjectCoverageAssessment,
    ) -> EvidenceReference:
        return EvidenceReference(
            project_id=project_id,
            reference_type="support_profile",
            reference_id=(
                f"{assessment.support_profile_id}:"
                f"{assessment.support_profile_version}"
            ),
            display_label=(
                "Preliminary Support Profile · "
                f"{assessment.support_profile_id} "
                f"v{assessment.support_profile_version}"
            ),
            repository_relative_path=(
                DEFAULT_SUPPORT_PROFILE_PATH.as_posix()
            ),
            content_fingerprint=None,
            media_type="application/json",
            source_role=None,
            relationship="defines_support_rules",
            evidence_role="direct",
        )

    def _source_manifest_references(
        self,
        summary: ProjectProcessingSummary,
    ) -> tuple[EvidenceReference, ...]:
        return tuple(
            EvidenceReference(
                project_id=summary.project_id,
                reference_type="source_manifest",
                reference_id=source.source_id,
                display_label=(
                    f"Source Manifest · {source.source_id}"
                ),
                repository_relative_path=(
                    f"data/projects/{summary.project_id}/sources/"
                    f"{source.source_id}/{SOURCE_MANIFEST_FILENAME}"
                ),
                content_fingerprint=None,
                media_type="application/json",
                source_role=None,
                relationship="contributes_source_state",
                evidence_role="direct",
            )
            for source in summary.source_summaries
        )

    def _processing_evidence(
        self,
        summary: ProjectProcessingSummary,
    ) -> tuple[EvidenceReference, ...]:
        references = list(self._source_manifest_references(summary))
        for source in summary.source_summaries:
            if source.current_processing_run_id is None:
                continue
            references.append(
                EvidenceReference(
                    project_id=summary.project_id,
                    reference_type="processing_run_manifest",
                    reference_id=source.current_processing_run_id,
                    display_label=(
                        "Processing Run Manifest · "
                        f"{source.current_processing_run_id}"
                    ),
                    repository_relative_path=(
                        f"data/projects/{summary.project_id}/runs/"
                        f"{source.current_processing_run_id}/"
                        f"{PROCESSING_RUN_MANIFEST_FILENAME}"
                    ),
                    content_fingerprint=None,
                    media_type="application/json",
                    source_role=None,
                    relationship="contributes_processing_state",
                    evidence_role="direct",
                )
            )
        return tuple(references)

    def _coverage_evidence(
        self,
        manifest: ProjectManifest,
        processing_summary: ProjectProcessingSummary | None,
        assessment: ProjectCoverageAssessment,
    ) -> tuple[EvidenceReference, ...]:
        references = [
            self._framework_template_reference(manifest),
            self._support_profile_reference(
                manifest.project_id,
                assessment,
            ),
        ]
        if processing_summary is not None:
            references.extend(
                self._processing_evidence(processing_summary)
            )
        return tuple(references)

    def _processing_issue_views(
        self,
        summary: ProjectProcessingSummary,
    ) -> tuple[DashboardIssueView, ...]:
        views: list[DashboardIssueView] = []
        for issue in summary.issues:
            evidence = ()
            if issue.path is not None:
                reference = self._path_issue_reference(
                    project_id=summary.project_id,
                    issue_code=issue.code,
                    path=issue.path,
                    label="Processing issue artifact",
                )
                if reference is not None:
                    evidence = (reference,)
            views.append(
                make_issue_view(
                    issue_code=_dashboard_issue_code(
                        "processing",
                        issue.code,
                        issue.message,
                        issue.source_id,
                        issue.processing_run_id,
                        issue.event_id,
                        issue.processing_decision_id,
                        issue.path,
                    ),
                    message=issue.message,
                    issue_level=issue.issue_level,
                    evidence_references=evidence,
                )
            )
        return tuple(views)

    def _coverage_issue_views(
        self,
        assessment: ProjectCoverageAssessment,
    ) -> tuple[DashboardIssueView, ...]:
        views: list[DashboardIssueView] = []
        for issue in assessment.issues:
            evidence = ()
            if issue.path is not None:
                reference = self._path_issue_reference(
                    project_id=assessment.project_id,
                    issue_code=issue.code,
                    path=issue.path,
                    label="Coverage issue artifact",
                )
                if reference is not None:
                    evidence = (reference,)
            views.append(
                make_issue_view(
                    issue_code=_dashboard_issue_code(
                        "coverage",
                        issue.code,
                        issue.message,
                        issue.source_id,
                        issue.information_unit_id,
                        issue.framework_node_id,
                        issue.framework_assignment_candidate_id,
                        issue.human_review_decision_id,
                        issue.support_target_id,
                        issue.path,
                    ),
                    message=issue.message,
                    issue_level=issue.issue_level,
                    evidence_references=evidence,
                )
            )
        return tuple(views)

    def _load_source_scan_strict(
        self,
        project_id: str,
    ) -> SourceScanResult:
        try:
            value = self.source_registry.scan_sources(project_id)
        except Exception as exc:
            raise DashboardPresentationError(
                "Unable to load the Project Source scan."
            ) from exc
        if not isinstance(value, SourceScanResult):
            raise DashboardPresentationError(
                "source_registry returned an invalid type."
            )
        for source in value.valid_sources:
            if source.project_id != project_id:
                raise DashboardPresentationError(
                    "Source scan contains a Source from another project."
                )
        for issue in value.source_issues:
            if issue.project_id != project_id:
                raise DashboardPresentationError(
                    "Source scan contains an issue from another project."
                )
        return value

    def _source_processing_row_evidence(
        self,
        source: SourceManifest,
        summary: object,
    ) -> tuple[EvidenceReference, ...]:
        references = [
            self._source_manifest_reference_from_manifest(source),
            self._source_content_reference(source),
        ]
        current_run_id = getattr(summary, "current_processing_run_id", None)
        if current_run_id is not None:
            references.append(
                self._run_manifest_reference(
                    source.project_id,
                    current_run_id,
                    relationship="is_current_processing_run",
                    evidence_role="direct",
                )
            )
            references.extend(
                self._current_run_published_artifact_evidence(
                    source,
                    summary,
                )
            )
        for run_id in getattr(summary, "superseded_run_ids", ()):
            references.append(
                self._run_manifest_reference(
                    source.project_id,
                    run_id,
                    relationship="is_superseded_processing_run",
                    evidence_role="contextual",
                )
            )
        return tuple(references)

    def _current_run_published_artifact_evidence(
        self,
        source: SourceManifest,
        summary: object,
    ) -> tuple[EvidenceReference, ...]:
        """Return validated P5 publication references for the current Attempt."""

        current_run_id = getattr(
            summary,
            "current_processing_run_id",
            None,
        )
        latest_attempt_id = getattr(
            summary,
            "latest_attempt_id",
            None,
        )
        if current_run_id is None or latest_attempt_id is None:
            return ()

        try:
            history = self.processing_repository.load_run(
                source.project_id,
                current_run_id,
            )
        except Exception:
            # The dashboard remains fail-closed. A pending review without a
            # validated report is rendered explicitly by the UI.
            return ()

        publication_event = next(
            (
                event
                for event in reversed(history.events)
                if event.event_type == "artifact_published"
                and event.attempt_id == latest_attempt_id
            ),
            None,
        )
        if publication_event is None:
            return ()

        return tuple(
            self._processing_artifact_evidence_reference(
                source,
                reference,
            )
            for reference in publication_event.artifact_references
        )

    def _processing_artifact_evidence_reference(
        self,
        source: SourceManifest,
        reference: ProcessingArtifactReference,
    ) -> EvidenceReference:
        reference_type = {
            "review_reports": "ingestion_review_report",
            "run_summaries": "ingestion_run_summary",
            "consensus_reports": "ingestion_consensus_report",
            "agent_outputs": "ingestion_agent_output",
        }.get(
            reference.artifact_type,
            "processing_artifact",
        )
        relationship = {
            "review_reports": "requires_human_review",
            "run_summaries": "summarizes_ingestion_run",
            "consensus_reports": "supports_review_with_consensus",
            "agent_outputs": "supports_review_with_agent_output",
        }.get(
            reference.artifact_type,
            "supports_processing_traceability",
        )
        evidence_role = (
            "direct"
            if reference.artifact_type == "review_reports"
            else "contextual"
        )

        return EvidenceReference(
            project_id=source.project_id,
            reference_type=reference_type,
            reference_id=reference.artifact_id,
            display_label=_processing_artifact_display_label(reference),
            repository_relative_path=reference.repository_relative_path,
            content_fingerprint=reference.content_fingerprint,
            media_type=_processing_artifact_media_type(
                reference.repository_relative_path
            ),
            source_role=source.source_role,
            relationship=relationship,
            evidence_role=evidence_role,
        )

    def _source_manifest_reference_from_manifest(
        self,
        source: SourceManifest,
    ) -> EvidenceReference:
        return EvidenceReference(
            project_id=source.project_id,
            reference_type="source_manifest",
            reference_id=source.source_id,
            display_label=(
                f"Source Manifest · {source.source_id} · "
                f"{source.original_filename}"
            ),
            repository_relative_path=(
                f"data/projects/{source.project_id}/sources/"
                f"{source.source_id}/{SOURCE_MANIFEST_FILENAME}"
            ),
            content_fingerprint=None,
            media_type="application/json",
            source_role=source.source_role,
            relationship="defines_registered_source",
            evidence_role="direct",
        )

    def _source_manifest_reference_by_id(
        self,
        project_id: str,
        source_id: str,
        *,
        evidence_role: str = "contextual",
    ) -> EvidenceReference:
        return EvidenceReference(
            project_id=project_id,
            reference_type="source_manifest",
            reference_id=source_id,
            display_label=f"Source Manifest · {source_id}",
            repository_relative_path=(
                f"data/projects/{project_id}/sources/{source_id}/"
                f"{SOURCE_MANIFEST_FILENAME}"
            ),
            content_fingerprint=None,
            media_type="application/json",
            source_role=None,
            relationship="provides_source_traceability",
            evidence_role=evidence_role,
        )

    def _source_content_reference(
        self,
        source: SourceManifest,
    ) -> EvidenceReference:
        return EvidenceReference(
            project_id=source.project_id,
            reference_type="registered_source_content",
            reference_id=source.source_id,
            display_label=(
                f"Registered Source · {source.original_filename}"
            ),
            repository_relative_path=(
                f"data/projects/{source.project_id}/sources/"
                f"{source.source_id}/{source.stored_filename}"
            ),
            content_fingerprint=source.sha256,
            media_type=source.media_type,
            source_role=source.source_role,
            relationship="is_registered_source_content",
            evidence_role="direct",
        )

    def _run_manifest_reference(
        self,
        project_id: str,
        run_id: str,
        *,
        relationship: str,
        evidence_role: str,
    ) -> EvidenceReference:
        return EvidenceReference(
            project_id=project_id,
            reference_type="processing_run_manifest",
            reference_id=run_id,
            display_label=f"Processing Run Manifest · {run_id}",
            repository_relative_path=(
                f"data/projects/{project_id}/runs/{run_id}/"
                f"{PROCESSING_RUN_MANIFEST_FILENAME}"
            ),
            content_fingerprint=None,
            media_type="application/json",
            source_role=None,
            relationship=relationship,
            evidence_role=evidence_role,
        )

    def _information_unit_reference(
        self,
        project_id: str,
        information_unit_id: str,
        *,
        content_fingerprint: str | None = None,
    ) -> EvidenceReference:
        return EvidenceReference(
            project_id=project_id,
            reference_type="information_unit",
            reference_id=information_unit_id,
            display_label=f"Information Unit · {information_unit_id}",
            repository_relative_path=(
                f"data/projects/{project_id}/semantics/"
                f"information_units/{information_unit_id}.json"
            ),
            content_fingerprint=content_fingerprint,
            media_type="application/json",
            source_role=None,
            relationship="provides_node_evidence",
            evidence_role="direct",
        )

    def _framework_assignment_reference(
        self,
        project_id: str,
        candidate_id: str,
        *,
        content_fingerprint: str | None = None,
    ) -> EvidenceReference:
        return EvidenceReference(
            project_id=project_id,
            reference_type="framework_assignment_candidate",
            reference_id=candidate_id,
            display_label=f"Framework Assignment Candidate · {candidate_id}",
            repository_relative_path=(
                f"data/projects/{project_id}/semantics/"
                f"framework_assignments/{candidate_id}.json"
            ),
            content_fingerprint=content_fingerprint,
            media_type="application/json",
            source_role=None,
            relationship="maps_evidence_to_framework_node",
            evidence_role="direct",
        )

    def _node_coverage_evidence(
        self,
        project_id: str,
        node: object,
        manifest: ProjectManifest,
    ) -> tuple[EvidenceReference, ...]:
        references: list[EvidenceReference] = [
            self._framework_template_reference(manifest)
        ]
        references.extend(
            self._framework_assignment_reference(project_id, candidate_id)
            for candidate_id in node.framework_assignment_candidate_ids
        )
        references.extend(
            self._information_unit_reference(project_id, unit_id)
            for unit_id in node.information_unit_ids
        )
        references.extend(
            self._source_manifest_reference_by_id(project_id, source_id)
            for source_id in node.source_ids
        )
        return tuple(references)

    def _level_coverage_evidence(
        self,
        project_id: str,
        node_ids: tuple[str, ...],
        node_by_id: dict[str, DashboardFrameworkNodeCoverage],
        manifest: ProjectManifest,
    ) -> tuple[EvidenceReference, ...]:
        references: list[EvidenceReference] = [
            self._framework_template_reference(manifest)
        ]
        for node_id in node_ids:
            node_view = node_by_id.get(node_id)
            if node_view is None:
                raise DashboardPresentationError(
                    "Framework Level Coverage references an unknown node."
                )
            references.extend(node_view.evidence.references)
        return tuple(references)

    def _support_evidence(
        self,
        project_id: str,
        required_node_ids: tuple[str, ...],
        node_by_id: dict[str, DashboardFrameworkNodeCoverage],
        assessment: ProjectCoverageAssessment,
        manifest: ProjectManifest,
    ) -> tuple[EvidenceReference, ...]:
        references: list[EvidenceReference] = [
            self._framework_template_reference(manifest),
            self._support_profile_reference(project_id, assessment),
        ]
        for node_id in required_node_ids:
            node_view = node_by_id.get(node_id)
            if node_view is None:
                raise DashboardPresentationError(
                    "Potential Support references an unknown framework node."
                )
            references.extend(node_view.evidence.references)
        return tuple(references)

    def _human_review_row(
        self,
        project_id: str,
        decision: object,
    ) -> DashboardHumanReviewRow:
        if getattr(decision, "project_id", None) != project_id:
            raise DashboardPresentationError(
                "Human Review Decision belongs to another project."
            )
        return make_human_review_row(
            project_id=project_id,
            human_review_decision_id=(
                decision.human_review_decision_id
            ),
            target_type=decision.target.target_type,
            target_id=decision.target.target_id,
            target_content_fingerprint=(
                decision.target.target_content_fingerprint
            ),
            reference_validation_status=(
                decision.target.reference_validation_status
            ),
            reference_validation_fingerprint=(
                decision.target.reference_validation_fingerprint
            ),
            review_mode=decision.review_mode,
            decision=decision.decision,
            reviewer_identity=decision.reviewer_identity,
            rationale=decision.rationale,
            decided_at=decision.decided_at,
            decision_fingerprint=decision.decision_fingerprint,
            evidence_references=(
                self._human_review_reference(decision),
                self._human_review_target_reference(
                    project_id,
                    decision.target,
                ),
            ),
        )

    def _human_review_reference(
        self,
        decision: object,
    ) -> EvidenceReference:
        project_id = decision.project_id
        decision_id = decision.human_review_decision_id
        return EvidenceReference(
            project_id=project_id,
            reference_type="human_review_decision",
            reference_id=decision_id,
            display_label=f"Human Review Decision · {decision_id}",
            repository_relative_path=(
                f"data/projects/{project_id}/semantics/"
                f"human_reviews/{decision_id}.json"
            ),
            content_fingerprint=decision.decision_fingerprint,
            media_type="application/json",
            source_role=None,
            relationship="records_exact_human_review",
            evidence_role="direct",
        )

    def _human_review_target_reference(
        self,
        project_id: str,
        target: object,
    ) -> EvidenceReference:
        target_type = target.target_type
        target_id = target.target_id
        if target_type == "information_unit_publication":
            return self._information_unit_reference(
                project_id,
                target_id,
                content_fingerprint=target.target_content_fingerprint,
            )
        if target_type == "terminology_mapping_candidate":
            return self._terminology_mapping_reference(
                project_id,
                target_id,
                content_fingerprint=target.target_content_fingerprint,
            )
        if target_type == "framework_assignment_candidate":
            return self._framework_assignment_reference(
                project_id,
                target_id,
                content_fingerprint=target.target_content_fingerprint,
            )
        raise DashboardPresentationError(
            "Human Review target_type is not supported."
        )

    def _terminology_mapping_reference(
        self,
        project_id: str,
        candidate_id: str,
        *,
        content_fingerprint: str | None = None,
    ) -> EvidenceReference:
        return EvidenceReference(
            project_id=project_id,
            reference_type="terminology_mapping_candidate",
            reference_id=candidate_id,
            display_label=f"Terminology Mapping Candidate · {candidate_id}",
            repository_relative_path=(
                f"data/projects/{project_id}/semantics/"
                f"terminology_mappings/{candidate_id}.json"
            ),
            content_fingerprint=content_fingerprint,
            media_type="application/json",
            source_role=None,
            relationship="maps_project_terminology",
            evidence_role="direct",
        )

    def _source_projection_references(
        self,
        project_id: str,
        source_projection_id: str,
    ) -> tuple[EvidenceReference, ...]:
        base = (
            f"data/projects/{project_id}/semantics/"
            f"source_projections/{source_projection_id}"
        )
        return (
            EvidenceReference(
                project_id=project_id,
                reference_type="source_projection_manifest",
                reference_id=source_projection_id,
                display_label=(
                    f"Source Projection Manifest · {source_projection_id}"
                ),
                repository_relative_path=f"{base}/projection.json",
                content_fingerprint=None,
                media_type="application/json",
                source_role=None,
                relationship="defines_source_projection",
                evidence_role="direct",
            ),
            EvidenceReference(
                project_id=project_id,
                reference_type="source_projection_content",
                reference_id=f"{source_projection_id}:content",
                display_label=(
                    f"Source Projection Content · {source_projection_id}"
                ),
                repository_relative_path=f"{base}/content.txt",
                content_fingerprint=None,
                media_type="text/plain",
                source_role=None,
                relationship="contains_projected_source",
                evidence_role="direct",
            ),
        )

    def _human_review_issue_views(
        self,
        scan: HumanReviewScanResult,
    ) -> tuple[DashboardIssueView, ...]:
        views = []
        for issue in scan.issues:
            if issue.project_id is None:
                raise DashboardPresentationError(
                    "Human Review issue has no project_id."
                )
            evidence = ()
            if issue.path is not None:
                reference = self._path_issue_reference(
                    project_id=issue.project_id,
                    issue_code=issue.code,
                    path=issue.path,
                    label="Human Review issue artifact",
                )
                if reference is not None:
                    evidence = (reference,)
            views.append(
                make_issue_view(
                    issue_code=_dashboard_issue_code(
                        "human_review",
                        issue.code,
                        issue.message,
                        issue.human_review_decision_id,
                        issue.target_type,
                        issue.target_id,
                        issue.path,
                    ),
                    message=issue.message,
                    issue_level=issue.issue_level,
                    evidence_references=evidence,
                )
            )
        return tuple(views)

    def _support_evidence_from_assessment(
        self,
        project_id: str,
        support: object,
        assessment: ProjectCoverageAssessment,
        manifest: ProjectManifest,
    ) -> tuple[EvidenceReference, ...]:
        node_by_id = {
            item.framework_node_id: item
            for item in assessment.node_coverages
        }
        references = [
            self._framework_template_reference(manifest),
            self._support_profile_reference(project_id, assessment),
        ]
        for node_id in support.required_framework_node_ids:
            node = node_by_id.get(node_id)
            if node is None:
                raise DashboardPresentationError(
                    "Potential Support references an unknown Framework Node."
                )
            references.extend(
                self._node_coverage_evidence(
                    project_id,
                    node,
                    manifest,
                )
            )
        return tuple(references)

    @staticmethod
    def _trace_target_node_key(
        target_type: str,
        target_id: str,
    ) -> str:
        mapping = {
            "information_unit_publication": "information_unit",
            "terminology_mapping_candidate": (
                "terminology_mapping_candidate"
            ),
            "framework_assignment_candidate": (
                "framework_assignment_candidate"
            ),
        }
        node_type = mapping.get(target_type)
        if node_type is None:
            raise DashboardPresentationError(
                "Human Review target_type is not supported."
            )
        return f"{node_type}:{target_id}"

    def _placeholder_target_node(
        self,
        project_id: str,
        target: object,
    ) -> DashboardTraceabilityNode:
        node_key = self._trace_target_node_key(
            target.target_type,
            target.target_id,
        )
        node_type, node_id = node_key.split(":", 1)
        return make_traceability_node(
            node_type=node_type,
            node_id=node_id,
            label=node_id,
            secondary_text=target.target_type,
            status=present_status(
                target.reference_validation_status
            ),
            evidence_references=(
                self._human_review_target_reference(project_id, target),
            ),
        )

    def _source_issue_views(
        self,
        scan: SourceScanResult,
    ) -> tuple[DashboardIssueView, ...]:
        views: list[DashboardIssueView] = []
        for issue in scan.source_issues:
            evidence = ()
            reference = self._path_issue_reference(
                project_id=issue.project_id,
                issue_code=issue.code,
                path=issue.path,
                label="Source issue artifact",
            )
            if reference is not None:
                evidence = (reference,)
            views.append(
                make_issue_view(
                    issue_code=_dashboard_issue_code(
                        "source",
                        issue.code,
                        issue.message,
                        issue.source_id,
                        issue.path,
                    ),
                    message=issue.message,
                    issue_level="blocking",
                    evidence_references=evidence,
                )
            )
        return tuple(views)

    def _workspace_issue_view(
        self,
        issue: WorkspaceIssue,
    ) -> DashboardIssueView:
        issue_level = (
            "warning"
            if issue.code == "unexpected_workspace_entry"
            else "blocking"
        )
        evidence = ()
        if issue.project_id is not None:
            reference = self._path_issue_reference(
                project_id=issue.project_id,
                issue_code=issue.code,
                path=issue.path,
                label="Workspace issue artifact",
            )
            if reference is not None:
                evidence = (reference,)
        return make_issue_view(
            issue_code=_dashboard_issue_code(
                "workspace",
                issue.code,
                issue.message,
                issue.project_id,
                issue.path,
            ),
            message=issue.message,
            issue_level=issue_level,
            evidence_references=evidence,
        )

    def _path_issue_reference(
        self,
        *,
        project_id: str,
        issue_code: str,
        path: Path,
        label: str,
    ) -> EvidenceReference | None:
        try:
            relative = self._to_repository_relative(path)
        except DashboardReferenceError:
            return None
        candidate = self.repository_root / Path(relative)
        if (
            not candidate.exists()
            or not candidate.is_file()
            or candidate.is_symlink()
        ):
            return None
        return EvidenceReference(
            project_id=project_id,
            reference_type="issue_artifact",
            reference_id=f"{issue_code}:{project_id}",
            display_label=f"{label} · {issue_code}",
            repository_relative_path=relative,
            content_fingerprint=None,
            media_type="application/json",
            source_role=None,
            relationship="explains_issue",
            evidence_role="direct",
        )

    def _to_repository_relative(self, path: Path) -> str:
        supplied = Path(path)
        root = self.repository_root.resolve(strict=False)
        candidate = (
            supplied.resolve(strict=False)
            if supplied.is_absolute()
            else (self.repository_root / supplied).resolve(strict=False)
        )
        try:
            relative = candidate.relative_to(root)
        except ValueError as exc:
            raise DashboardReferenceError(
                "Issue path is outside repository_root."
            ) from exc
        return relative.as_posix()

    @staticmethod
    def _processing_secondary_text(
        summary: ProjectProcessingSummary,
    ) -> str:
        return (
            f"{summary.completed_sources} completed · "
            f"{summary.running_sources} running · "
            f"{summary.awaiting_review_sources} awaiting review · "
            f"{summary.blocked_sources + summary.failed_sources} attention"
        )

    @staticmethod
    def _coverage_secondary_text(
        assessment: ProjectCoverageAssessment,
    ) -> str:
        covered = sum(
            node.coverage_state != "uncovered"
            for node in assessment.node_coverages
        )
        total = len(assessment.node_coverages)
        attention = sum(
            node.attention_required
            for node in assessment.node_coverages
        )
        return (
            f"{covered} of {total} framework nodes covered · "
            f"{attention} require attention"
        )



def _processing_artifact_display_label(
    reference: ProcessingArtifactReference,
) -> str:
    path = PurePosixPath(reference.repository_relative_path)
    suffix_label = {
        ".md": "Markdown",
        ".json": "JSON",
        ".txt": "Text",
        ".csv": "CSV",
        ".tsv": "TSV",
        ".pdf": "PDF",
    }.get(path.suffix.lower(), path.suffix.lstrip(".").upper())

    if reference.artifact_type == "review_reports":
        return "Ingestion Review Report"
    if reference.artifact_type == "run_summaries":
        return f"Run Summary · {suffix_label}"

    stage = _processing_artifact_stage_label(path)
    filename = _humanize_artifact_name(path.stem)
    if reference.artifact_type == "consensus_reports":
        return f"Consensus Report · {stage} · {suffix_label}"
    if reference.artifact_type == "agent_outputs":
        return f"Agent Output · {stage} · {filename}"
    return f"Processing Artifact · {filename}"


def _processing_artifact_stage_label(path: PurePosixPath) -> str:
    parts = path.parts
    for index, part in enumerate(parts):
        if part.startswith("ATT-") and index + 1 < len(parts) - 1:
            return _humanize_artifact_name(parts[index + 1])
    return "Agentic ingestion"


def _humanize_artifact_name(value: str) -> str:
    parts = [part for part in value.replace("-", "_").split("_") if part]
    if parts and parts[0].isdigit():
        parts = parts[1:]
    if not parts:
        return "Artifact"
    return " ".join(part.capitalize() for part in parts)


def _processing_artifact_media_type(path: str) -> str:
    return {
        ".md": "text/markdown",
        ".json": "application/json",
        ".txt": "text/plain",
        ".csv": "text/csv",
        ".tsv": "text/tab-separated-values",
        ".pdf": "application/pdf",
    }.get(
        PurePosixPath(path).suffix.lower(),
        "application/octet-stream",
    )

def _require_project_id(project_id: object) -> str:
    if not is_valid_project_id(project_id):
        raise DashboardValidationError(
            "project_id must be a six-digit numeric string."
        )
    return project_id


def _normalize_identifier(value: str) -> str:
    normalized = "".join(
        character.lower() if character.isalnum() else "_"
        for character in value
    )
    normalized = "_".join(
        part for part in normalized.split("_") if part
    )
    if not normalized:
        raise DashboardValidationError(
            "support_target_id cannot be normalized for display."
        )
    if normalized[0].isdigit():
        normalized = f"target_{normalized}"
    return normalized


def _collect_issue_evidence(
    issues: Iterable[DashboardIssueView],
) -> tuple[EvidenceReference, ...]:
    references: list[EvidenceReference] = []
    for issue in issues:
        references.extend(issue.evidence.references)
    return tuple(references)


def _dashboard_issue_code(
    namespace: str,
    domain_code: str,
    *identity_parts: object,
) -> str:
    normalized_namespace = _normalize_identifier(namespace)
    normalized_code = ".".join(
        _normalize_identifier(part)
        for part in domain_code.split(".")
        if part
    )
    identity = "|".join(
        "" if part is None else str(part)
        for part in identity_parts
    )
    digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:10]
    return f"{normalized_namespace}.{normalized_code}.{digest}"
