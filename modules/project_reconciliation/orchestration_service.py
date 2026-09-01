"""S2 -> S3 -> immutable PRC cycle orchestration for ADR-032."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from modules.engineering_subjects import canonical_subject_set_to_dict
from modules.engineering_subjects.types import (
    CanonicalEngineeringSubject,
    CanonicalSubjectSet,
    EngineeringMention,
)
from modules.project_fit import (
    ProjectFitAssessmentService,
    derive_project_fit_gate_state,
)
from modules.project_processing import ProjectProcessingRepository
from modules.project_semantic_reconciliation import (
    ProjectSemanticReconciliationError,
    ProjectSemanticReconciliationIntegrityError,
    ProjectSemanticReconciliationValidationError,
    ProjectSemanticSourceInput,
    prepare_project_semantic_subjects,
)
from modules.project_semantic_reconciliation.case_service import (
    ProjectReconciliationCaseAssessmentService,
)
from modules.project_semantic_reconciliation.semantic_index_service import (
    ProjectSemanticIndexService,
)
from modules.project_sources import (
    ENGINEERING_SOURCE_ROLE,
    ProjectSourceRegistry,
)
from modules.project_workspace import ProjectWorkspace
from modules.review_workspace.subject_review_artifact_adapter import (
    select_subject_review_artifacts,
)
from modules.review_workspace.workflow_service import (
    ReviewApprovalWorkflowService,
)
from modules.source_projection.repository import SourceProjectionRepository
from modules.subject_consensus.analyzer import (
    subject_consensus_result_to_dict,
)
from modules.subject_consensus.types import (
    ConsensusValueDistribution,
    FieldConsensusAssessment,
    PersonaDiagnosticVariant,
    PersonaStatementVariant,
    RelationshipConsensusOutcome,
    SharedSubjectConsensusResult,
    SubjectConsensusOutcome,
)

from .concern_repository import (
    ConcernCentricProjectReconciliationRepository,
)
from .errors import ProjectReconciliationPersistenceError
from .repository import ProjectReconciliationRepository


class ProjectReconciliationOrchestrationError(RuntimeError):
    """Fail-closed S2/S3 reconciliation orchestration error."""


@dataclass(frozen=True, slots=True)
class ProjectReconciliationOrchestrationResult:
    project_id: str
    reconciliation_cycle_id: str
    source_ids: tuple[str, ...]
    project_fit_fingerprints: tuple[str, ...]
    semantic_reconciliation_fingerprint: str | None
    reused_existing_cycle: bool
    semantic_index_fingerprint: str | None = None
    reconciliation_summary_fingerprint: str | None = None
    case_count: int | None = None
    potential_conflicts_present: bool | None = None


@dataclass(frozen=True, slots=True)
class ProjectReconciliationProgressEvent:
    stage: str
    event_type: str
    message: str
    completed: int | None = None
    total: int | None = None
    source_id: str | None = None
    outcome: str | None = None


def _notify_reconciliation_progress(observer, **kwargs) -> None:
    if observer is None:
        return
    observer(ProjectReconciliationProgressEvent(**kwargs))


class ProjectReconciliationOrchestrationService:
    """Create one project-level reconciliation cycle from reviewed source outputs."""

    def __init__(
        self,
        project_root: Path | str = Path("."),
        *,
        workspace=None,
        source_registry=None,
        processing_repository=None,
        source_projection_repository=None,
        review_workflow_service=None,
        reconciliation_repository=None,
        project_fit_service=None,
        semantic_index_service=None,
        case_assessment_service=None,
        concern_reconciliation_repository=None,
    ) -> None:
        self.project_root = Path(project_root)
        self.projects_root = self.project_root / "data" / "projects"
        self._workspace = (
            ProjectWorkspace(root=self.projects_root)
            if workspace is None else workspace
        )
        self._sources = (
            ProjectSourceRegistry(root=self.projects_root)
            if source_registry is None else source_registry
        )
        self._processing = (
            ProjectProcessingRepository(root=self.projects_root)
            if processing_repository is None else processing_repository
        )
        self._projections = (
            SourceProjectionRepository(root=self.projects_root)
            if source_projection_repository is None
            else source_projection_repository
        )
        self._review = (
            ReviewApprovalWorkflowService(
                root=self.projects_root,
                repository_root=self.project_root,
            )
            if review_workflow_service is None
            else review_workflow_service
        )
        self._reconciliation = (
            ProjectReconciliationRepository(root=self.projects_root)
            if reconciliation_repository is None
            else reconciliation_repository
        )
        self._project_fit = (
            ProjectFitAssessmentService()
            if project_fit_service is None else project_fit_service
        )
        self._semantic_index = (
            ProjectSemanticIndexService()
            if semantic_index_service is None
            else semantic_index_service
        )
        self._case_assessment = (
            ProjectReconciliationCaseAssessmentService()
            if case_assessment_service is None
            else case_assessment_service
        )
        self._concern_reconciliation = (
            ConcernCentricProjectReconciliationRepository(
                root=self.projects_root,
            )
            if concern_reconciliation_repository is None
            else concern_reconciliation_repository
        )

    def _mvp_current_engineering_items(
        self,
        project_id: str,
        review_view,
    ) -> tuple:
        """Return only current registered Engineering Source review items."""

        engineering_items = []
        for item in review_view.items:
            if not getattr(item, "is_current_processing_run", False):
                continue
            try:
                source = self._sources.load_source(
                    project_id,
                    item.source_id,
                )
            except Exception as exc:
                raise ProjectReconciliationOrchestrationError(
                    "Registered Source authority cannot be reconstructed."
                ) from exc
            if source.source_role != ENGINEERING_SOURCE_ROLE:
                continue
            engineering_items.append(item)

        values = tuple(
            sorted(
                engineering_items,
                key=lambda item: item.source_id,
            )
        )
        source_ids = tuple(item.source_id for item in values)
        if len(source_ids) != len(set(source_ids)):
            raise ProjectReconciliationOrchestrationError(
                "Current Human Review exposes duplicate Engineering Source "
                "authority items."
            )
        return values

    def read_project_fit_readiness(
        self,
        project_id: str,
    ):
        """Read the active thesis-MVP Project Fit gate without LLM calls."""

        from .project_fit_readiness import (
            derive_project_fit_readiness,
        )

        try:
            review_view = self._review.project_view(project_id)
        except Exception as exc:
            raise ProjectReconciliationOrchestrationError(
                "Current source-local Human Review state cannot be "
                "reconstructed safely."
            ) from exc

        if getattr(review_view, "has_blocking_issues", False):
            raise ProjectReconciliationOrchestrationError(
                "Human Review contains blocking integrity issues."
            )

        engineering_items = self._mvp_current_engineering_items(
            project_id,
            review_view,
        )

        try:
            fits = tuple(
                self._reconciliation.list_project_fit(project_id)
            )
        except Exception as exc:
            raise ProjectReconciliationOrchestrationError(
                "Persisted Project Fit evidence cannot be read safely."
            ) from exc

        try:
            return derive_project_fit_readiness(
                project_id=project_id,
                review_items=engineering_items,
                project_fit_assessments=fits,
            )
        except Exception as exc:
            raise ProjectReconciliationOrchestrationError(
                "Project Fit readiness cannot be reconstructed safely."
            ) from exc

    def assess_project_fit_only(
        self,
        project_id: str,
        *,
        provider: str,
        model: str,
        api_key: str | None = None,
        llm_progress_observer=None,
        progress_observer=None,
    ):
        """Assess only S2 Project Fit for the active thesis MVP.

        This path deliberately stops after Project Fit. It does not call S3A,
        S3B, S4 or S5 and it never creates/reuses a PRC cycle.
        """

        from .project_fit_readiness import (
            derive_project_fit_readiness,
        )

        _notify_reconciliation_progress(
            progress_observer,
            stage="authority_validation",
            event_type="started",
            message=(
                "Validating current source-local engineering authority "
                "for Project Fit"
            ),
        )

        try:
            project = self._workspace.load_project(project_id)
            review_view = self._review.project_view(project_id)
            projections = tuple(
                self._projections.list_projections(project_id)
            )
        except Exception as exc:
            raise ProjectReconciliationOrchestrationError(
                "Project, Human Review, or Source Projection state "
                "cannot be reconstructed safely."
            ) from exc

        if getattr(review_view, "has_blocking_issues", False):
            raise ProjectReconciliationOrchestrationError(
                "Human Review contains blocking integrity issues."
            )

        engineering_items = self._mvp_current_engineering_items(
            project_id,
            review_view,
        )
        source_count = len(engineering_items)

        if source_count <= 1:
            return self.read_project_fit_readiness(project_id)

        incomplete = tuple(
            item.source_id
            for item in engineering_items
            if item.workflow_status != "approved_input_available"
        )
        if incomplete:
            _notify_reconciliation_progress(
                progress_observer,
                stage="authority_validation",
                event_type="failed",
                message=(
                    "Source-local Human Review is incomplete for "
                    + ", ".join(incomplete)
                ),
                completed=source_count - len(incomplete),
                total=source_count,
            )
            raise ProjectReconciliationOrchestrationError(
                "Every Engineering Source must complete source-local Human "
                "Review and Approved Input before Project Fit can open the "
                "multi-source Model Proposal gate."
            )

        _notify_reconciliation_progress(
            progress_observer,
            stage="authority_validation",
            event_type="completed",
            message=(
                "Source authority validated · "
                f"{source_count}/{source_count} Engineering Sources"
            ),
            completed=source_count,
            total=source_count,
        )

        fits = []
        for index, item in enumerate(
            engineering_items,
            start=1,
        ):
            _notify_reconciliation_progress(
                progress_observer,
                stage="project_fit",
                event_type="started",
                message=(
                    f"Project Fit (S2) · Source {index}/{source_count} · "
                    f"{item.source_id}"
                ),
                completed=index - 1,
                total=source_count,
                source_id=item.source_id,
            )

            try:
                _source_input, fit = self._source_input(
                    project=project,
                    item=item,
                    available_projections=projections,
                    provider=provider,
                    model=model,
                    api_key=api_key,
                    llm_progress_observer=llm_progress_observer,
                )
            except Exception:
                _notify_reconciliation_progress(
                    progress_observer,
                    stage="project_fit",
                    event_type="failed",
                    message=(
                        f"Project Fit (S2) failed safely · "
                        f"{item.source_id}"
                    ),
                    completed=index - 1,
                    total=source_count,
                    source_id=item.source_id,
                )
                raise

            gate_state = derive_project_fit_gate_state(fit)
            if gate_state == "admitted":
                message = (
                    f"Project Fit (S2) · {index}/{source_count} admitted · "
                    f"{fit.source_id}"
                )
            else:
                message = (
                    f"Project Fit (S2) · {index}/{source_count} assessed · "
                    f"{fit.source_id} · Human resolution required"
                )

            fits.append(fit)
            _notify_reconciliation_progress(
                progress_observer,
                stage="project_fit",
                event_type="completed",
                message=message,
                completed=index,
                total=source_count,
                source_id=fit.source_id,
                outcome=fit.outcome,
            )

        try:
            return derive_project_fit_readiness(
                project_id=project_id,
                review_items=engineering_items,
                project_fit_assessments=tuple(fits),
            )
        except Exception as exc:
            raise ProjectReconciliationOrchestrationError(
                "Completed Project Fit evidence cannot be projected into "
                "the active multi-source readiness gate safely."
            ) from exc


    def start(
        self,
        project_id: str,
        *,
        provider: str,
        model: str,
        api_key: str | None = None,
        llm_progress_observer=None,
        progress_observer=None,
    ) -> ProjectReconciliationOrchestrationResult:
        _notify_reconciliation_progress(
            progress_observer,
            stage="authority_validation",
            event_type="started",
            message="Validating current source-local engineering authority",
        )
        try:
            project = self._workspace.load_project(project_id)
            review_view = self._review.project_view(project_id)
            projections = tuple(self._projections.list_projections(project_id))
        except Exception as exc:
            raise ProjectReconciliationOrchestrationError(
                "Project, Human Review, or Source Projection state "
                "cannot be reconstructed safely."
            ) from exc

        if getattr(review_view, "has_blocking_issues", False):
            raise ProjectReconciliationOrchestrationError(
                "Human Review contains blocking integrity issues."
            )

        engineering_items = []
        for item in review_view.items:
            if not item.is_current_processing_run:
                continue
            try:
                source = self._sources.load_source(project_id, item.source_id)
            except Exception as exc:
                raise ProjectReconciliationOrchestrationError(
                    "Registered Source authority cannot be reconstructed."
                ) from exc
            if source.source_role != ENGINEERING_SOURCE_ROLE:
                continue
            if item.workflow_status != "approved_input_available":
                raise ProjectReconciliationOrchestrationError(
                    "Every Engineering Source must complete source-local "
                    "Human Review and Approved Input before Project Reconciliation."
                )
            engineering_items.append(item)

        engineering_items = tuple(
            sorted(engineering_items, key=lambda item: item.source_id)
        )
        if len(engineering_items) < 2:
            _notify_reconciliation_progress(
                progress_observer,
                stage="authority_validation",
                event_type="failed",
                message="Current source-local authority is insufficient for S2/S3",
                completed=len(engineering_items),
                total=len(engineering_items),
            )
            raise ProjectReconciliationOrchestrationError(
                "Cross-source Project Reconciliation requires at least "
                "two reviewed Engineering Sources."
            )

        source_count = len(engineering_items)
        _notify_reconciliation_progress(
            progress_observer,
            stage="authority_validation",
            event_type="completed",
            message=(
                "Source authority validated · "
                f"{source_count}/{source_count} Engineering Sources"
            ),
            completed=source_count,
            total=source_count,
        )

        source_inputs = []
        fits = []
        for index, item in enumerate(engineering_items, start=1):
            _notify_reconciliation_progress(
                progress_observer,
                stage="project_fit",
                event_type="started",
                message=(
                    f"Project Fit (S2) · Source {index}/{source_count} · "
                    f"{item.source_id}"
                ),
                completed=index - 1,
                total=source_count,
                source_id=item.source_id,
            )
            source_input, fit = self._source_input(
                project=project,
                item=item,
                available_projections=projections,
                provider=provider,
                model=model,
                api_key=api_key,
                llm_progress_observer=llm_progress_observer,
            )
            gate_state = derive_project_fit_gate_state(fit)
            if gate_state != "admitted":
                _notify_reconciliation_progress(
                    progress_observer,
                    stage="project_fit",
                    event_type="failed",
                    message=(
                        f"Project Fit (S2) requires Human resolution · "
                        f"{fit.source_id} · {fit.outcome}"
                    ),
                    completed=index - 1,
                    total=source_count,
                    source_id=fit.source_id,
                    outcome=fit.outcome,
                )
                raise ProjectReconciliationOrchestrationError(
                    "Project Fit requires explicit Human resolution before "
                    "this Engineering Source may enter S3: "
                    f"{fit.source_id} -> {fit.outcome}. "
                    "No machine-only override is permitted."
                )
            source_inputs.append(source_input)
            fits.append(fit)
            _notify_reconciliation_progress(
                progress_observer,
                stage="project_fit",
                event_type="completed",
                message=(
                    f"Project Fit (S2) · {index}/{source_count} admitted · "
                    f"{fit.source_id}"
                ),
                completed=index,
                total=source_count,
                source_id=fit.source_id,
                outcome=fit.outcome,
            )

        source_inputs = tuple(source_inputs)
        fits = tuple(fits)
        (
            _,
            semantic_subjects,
            input_fingerprint,
        ) = prepare_project_semantic_subjects(source_inputs)

        try:
            existing = (
                self._concern_reconciliation.find_cycle_by_input_fingerprint(
                    project_id,
                    input_fingerprint,
                )
            )
        except Exception as exc:
            raise ProjectReconciliationOrchestrationError(
                "Existing concern-centric Project Reconciliation cycles "
                "cannot be validated safely."
            ) from exc

        if existing is not None:
            try:
                semantic_index = (
                    self._concern_reconciliation.load_semantic_index(
                        project_id,
                        existing.reconciliation_cycle_id,
                    )
                )
                summary = (
                    self._concern_reconciliation.load_reconciliation_summary(
                        project_id,
                        existing.reconciliation_cycle_id,
                    )
                )
            except Exception as exc:
                raise ProjectReconciliationOrchestrationError(
                    "Existing concern-centric Project Reconciliation "
                    "evidence cannot be reconstructed safely."
                ) from exc

            if semantic_index.input_fingerprint != input_fingerprint:
                raise ProjectReconciliationOrchestrationError(
                    "Existing concern-centric cycle does not bind the "
                    "exact prepared S3 input."
                )

            _notify_reconciliation_progress(
                progress_observer,
                stage="persistence",
                event_type="completed",
                message=(
                    "Existing exact concern-centric Project "
                    "Reconciliation cycle reused · "
                    f"{existing.reconciliation_cycle_id}"
                ),
            )
            return ProjectReconciliationOrchestrationResult(
                project_id=project_id,
                reconciliation_cycle_id=(
                    existing.reconciliation_cycle_id
                ),
                source_ids=semantic_index.source_ids,
                project_fit_fingerprints=(
                    existing.project_fit_fingerprints
                ),
                semantic_reconciliation_fingerprint=None,
                reused_existing_cycle=True,
                semantic_index_fingerprint=(
                    semantic_index.content_fingerprint
                ),
                reconciliation_summary_fingerprint=(
                    summary.content_fingerprint
                ),
                case_count=summary.case_count,
                potential_conflicts_present=(
                    summary.potential_conflicts_present
                ),
            )

        _notify_reconciliation_progress(
            progress_observer,
            stage="semantic_reconciliation",
            event_type="started",
            message=(
                "S3A · Global semantic indexing · "
                f"{source_count} Sources"
            ),
            completed=0,
            total=1,
        )
        try:
            semantic_index = self._semantic_index.index(
                source_inputs,
                provider=provider,
                model=model,
                api_key=api_key,
                llm_progress_observer=llm_progress_observer,
            )
        except ProjectSemanticReconciliationValidationError as exc:
            _notify_reconciliation_progress(
                progress_observer,
                stage="semantic_reconciliation",
                event_type="failed",
                message=f"S3A response validation failed · {exc}",
                completed=0,
                total=1,
            )
            raise ProjectReconciliationOrchestrationError(
                f"S3A response validation failed: {exc}"
            ) from exc
        except ProjectSemanticReconciliationIntegrityError as exc:
            _notify_reconciliation_progress(
                progress_observer,
                stage="semantic_reconciliation",
                event_type="failed",
                message=f"S3A response integrity failed · {exc}",
                completed=0,
                total=1,
            )
            raise ProjectReconciliationOrchestrationError(
                f"S3A response integrity failed: {exc}"
            ) from exc
        except ProjectSemanticReconciliationError as exc:
            _notify_reconciliation_progress(
                progress_observer,
                stage="semantic_reconciliation",
                event_type="failed",
                message="S3A semantic indexing failed safely",
                completed=0,
                total=1,
            )
            raise ProjectReconciliationOrchestrationError(
                f"S3A semantic indexing failed: {exc}"
            ) from exc
        except Exception as exc:
            _notify_reconciliation_progress(
                progress_observer,
                stage="semantic_reconciliation",
                event_type="failed",
                message="S3A execution failed before Case assessment",
                completed=0,
                total=1,
            )
            raise ProjectReconciliationOrchestrationError(
                "S3A execution failed safely before Case assessment."
            ) from exc

        if semantic_index.input_fingerprint != input_fingerprint:
            raise ProjectReconciliationOrchestrationError(
                "S3A artifact does not bind the exact prepared "
                "Project semantic Subject set."
            )

        case_count = len(semantic_index.cases)
        _notify_reconciliation_progress(
            progress_observer,
            stage="semantic_reconciliation",
            event_type="completed",
            message=(
                f"S3A · {case_count} Reconciliation Cases identified"
            ),
            completed=1,
            total=1,
        )

        _notify_reconciliation_progress(
            progress_observer,
            stage="semantic_reconciliation",
            event_type="started",
            message=(
                "S3B · Assessing Reconciliation Cases · "
                f"{case_count} total"
            ),
            completed=0,
            total=case_count,
        )

        def observe_case(event):
            if event.event_type == "started":
                completed = event.case_index - 1
                suffix = (
                    " · unique · no LLM"
                    if event.singleton
                    else ""
                )
                message = (
                    "S3B · Case "
                    f"{event.case_index}/{event.total_cases} · "
                    f"{event.case_id} · {event.case_label}"
                    f"{suffix}"
                )
            elif event.event_type == "completed":
                completed = event.case_index
                suffix = (
                    " · unique · no LLM"
                    if event.singleton
                    else " · assessed"
                )
                message = (
                    "S3B · Case "
                    f"{event.case_index}/{event.total_cases} complete · "
                    f"{event.case_id} · {event.case_label}"
                    f"{suffix}"
                )
            else:
                completed = event.case_index - 1
                message = (
                    "S3B · Case "
                    f"{event.case_index}/{event.total_cases} failed · "
                    f"{event.case_id} · {event.case_label}"
                )

            _notify_reconciliation_progress(
                progress_observer,
                stage="semantic_reconciliation",
                event_type=event.event_type,
                message=message,
                completed=completed,
                total=event.total_cases,
            )

        try:
            assessments, summary = self._case_assessment.assess_all(
                semantic_index=semantic_index,
                subjects=semantic_subjects,
                provider=provider,
                model=model,
                api_key=api_key,
                llm_progress_observer=llm_progress_observer,
                case_progress_observer=observe_case,
            )
        except ProjectSemanticReconciliationValidationError as exc:
            _notify_reconciliation_progress(
                progress_observer,
                stage="semantic_reconciliation",
                event_type="failed",
                message=f"S3B response validation failed · {exc}",
                completed=0,
                total=case_count,
            )
            raise ProjectReconciliationOrchestrationError(
                f"S3B response validation failed: {exc}"
            ) from exc
        except ProjectSemanticReconciliationIntegrityError as exc:
            _notify_reconciliation_progress(
                progress_observer,
                stage="semantic_reconciliation",
                event_type="failed",
                message=f"S3B response integrity failed · {exc}",
                completed=0,
                total=case_count,
            )
            raise ProjectReconciliationOrchestrationError(
                f"S3B response integrity failed: {exc}"
            ) from exc
        except ProjectSemanticReconciliationError as exc:
            _notify_reconciliation_progress(
                progress_observer,
                stage="semantic_reconciliation",
                event_type="failed",
                message="S3B Case assessment failed safely",
                completed=0,
                total=case_count,
            )
            raise ProjectReconciliationOrchestrationError(
                f"S3B Case assessment failed: {exc}"
            ) from exc
        except Exception as exc:
            _notify_reconciliation_progress(
                progress_observer,
                stage="semantic_reconciliation",
                event_type="failed",
                message="S3B execution failed before PRC persistence",
                completed=0,
                total=case_count,
            )
            raise ProjectReconciliationOrchestrationError(
                "S3B execution failed safely before PRC persistence."
            ) from exc

        _notify_reconciliation_progress(
            progress_observer,
            stage="semantic_reconciliation",
            event_type="completed",
            message=(
                "S3B · Reconciliation Case assessment completed · "
                f"{summary.case_count} Cases"
            ),
            completed=summary.case_count,
            total=summary.case_count,
        )

        _notify_reconciliation_progress(
            progress_observer,
            stage="persistence",
            event_type="started",
            message=(
                "Persisting immutable concern-centric "
                "Project Reconciliation cycle"
            ),
        )
        try:
            cycle = self._concern_reconciliation.start_cycle(
                semantic_index=semantic_index,
                case_assessments=assessments,
                reconciliation_summary=summary,
                project_fit_assessments=fits,
            )
        except ProjectReconciliationPersistenceError as exc:
            _notify_reconciliation_progress(
                progress_observer,
                stage="persistence",
                event_type="failed",
                message=f"PRC persistence failed · {exc}",
            )
            raise ProjectReconciliationOrchestrationError(
                f"PRC persistence failed: {exc}"
            ) from exc
        except Exception as exc:
            _notify_reconciliation_progress(
                progress_observer,
                stage="persistence",
                event_type="failed",
                message="PRC persistence failed safely",
            )
            raise ProjectReconciliationOrchestrationError(
                "PRC persistence failed safely."
            ) from exc

        _notify_reconciliation_progress(
            progress_observer,
            stage="persistence",
            event_type="completed",
            message=f"{cycle.reconciliation_cycle_id} persisted",
        )

        return ProjectReconciliationOrchestrationResult(
            project_id=project_id,
            reconciliation_cycle_id=cycle.reconciliation_cycle_id,
            source_ids=semantic_index.source_ids,
            project_fit_fingerprints=(
                cycle.project_fit_fingerprints
            ),
            semantic_reconciliation_fingerprint=None,
            reused_existing_cycle=False,
            semantic_index_fingerprint=(
                semantic_index.content_fingerprint
            ),
            reconciliation_summary_fingerprint=(
                summary.content_fingerprint
            ),
            case_count=summary.case_count,
            potential_conflicts_present=(
                summary.potential_conflicts_present
            ),
        )

    def _source_input(
        self,
        *,
        project,
        item,
        available_projections,
        provider,
        model,
        api_key,
        llm_progress_observer,
    ):
        if item.attempt_id is None:
            raise ProjectReconciliationOrchestrationError(
                "Reviewed Engineering Source has no exact Processing Attempt."
            )
        try:
            history = self._processing.load_run(
                project.project_id,
                item.processing_run_id,
            )
            artifacts = select_subject_review_artifacts(history)
        except Exception as exc:
            raise ProjectReconciliationOrchestrationError(
                "Published source-local Subject artifacts cannot be selected "
                "from the reviewed Processing Run."
            ) from exc

        if artifacts is None:
            raise ProjectReconciliationOrchestrationError(
                "Reviewed Engineering Source has no complete canonical "
                "Subject/Consensus artifact chain."
            )
        if artifacts.attempt_id != item.attempt_id:
            raise ProjectReconciliationOrchestrationError(
                "Human Review does not bind the latest published Subject "
                "artifact Attempt."
            )

        subject_set = self._load_canonical_subject_set(
            reference=artifacts.canonical_subject_set,
            history=history,
            attempt_id=item.attempt_id,
        )
        consensus = self._load_subject_consensus(
            reference=artifacts.subject_consensus,
            history=history,
            attempt_id=item.attempt_id,
        )

        if (
            consensus.project_id != subject_set.project_id
            or consensus.source_id != subject_set.source_id
            or consensus.source_projection_id != subject_set.source_projection_id
        ):
            raise ProjectReconciliationOrchestrationError(
                "Canonical Subject Set and Subject Consensus provenance differ."
            )

        try:
            projection = self._projections.load_projection(
                project.project_id,
                subject_set.source_projection_id,
            )
        except Exception as exc:
            raise ProjectReconciliationOrchestrationError(
                "Exact Source Projection referenced by reviewed Subject "
                "artifacts is unavailable."
            ) from exc

        fit = self._find_exact_project_fit(
            project_id=project.project_id,
            projection=projection,
            history=history,
            attempt_id=item.attempt_id,
        )
        if fit is None:
            try:
                fit = self._project_fit.assess(
                    project,
                    history.manifest,
                    projection,
                    available_projections,
                    attempt_id=item.attempt_id,
                    provider=provider,
                    model=model,
                    api_key=api_key,
                    llm_progress_observer=llm_progress_observer,
                )
                fit = self._reconciliation.publish_project_fit(fit)
            except Exception as exc:
                raise ProjectReconciliationOrchestrationError(
                    "Project Fit assessment could not be completed and "
                    "persisted safely."
                ) from exc

        return (
            ProjectSemanticSourceInput(
                project_fit=fit,
                canonical_subject_set=subject_set,
                subject_consensus=consensus,
            ),
            fit,
        )

    def _find_exact_project_fit(
        self,
        *,
        project_id,
        projection,
        history,
        attempt_id,
    ):
        manifest = projection.manifest
        try:
            matches = tuple(
                fit
                for fit in self._reconciliation.list_project_fit(project_id)
                if (
                    fit.source_id == manifest.source_id
                    and fit.source_role == manifest.source_role
                    and fit.source_sha256 == manifest.source_sha256
                    and fit.source_projection_id == manifest.source_projection_id
                    and fit.candidate_projection_fingerprint
                    == manifest.projection_fingerprint
                    and fit.candidate_content_sha256 == manifest.content_sha256
                    and fit.processing_run_id
                    == history.manifest.processing_run_id
                    and fit.attempt_id == attempt_id
                )
            )
        except Exception as exc:
            raise ProjectReconciliationOrchestrationError(
                "Persisted Project Fit evidence cannot be read safely."
            ) from exc

        if len(matches) > 1:
            raise ProjectReconciliationOrchestrationError(
                "More than one Project Fit assessment binds the same exact "
                "source/run/attempt input. Explicit recovery is required."
            )
        return None if not matches else matches[0]

    def _load_canonical_subject_set(self, *, reference, history, attempt_id):
        envelope = self._load_subject_artifact_envelope(
            reference=reference,
            history=history,
            attempt_id=attempt_id,
            expected_kind="canonical_subject_set",
        )
        payload = envelope["payload"]
        try:
            value = CanonicalSubjectSet(
                schema_version=payload["schema_version"],
                project_id=payload["project_id"],
                source_id=payload["source_id"],
                source_projection_id=payload["source_projection_id"],
                source_projection_fingerprint=payload[
                    "source_projection_fingerprint"
                ],
                mentions=tuple(
                    EngineeringMention(
                        mention_id=item["mention_id"],
                        source_span_id=item["source_span_id"],
                        segment_id=item["segment_id"],
                        start_offset=item["start_offset"],
                        end_offset=item["end_offset"],
                        exact_text=item["exact_text"],
                        source_evidence_ids=tuple(item["source_evidence_ids"]),
                        content_fingerprint=item["content_fingerprint"],
                    )
                    for item in payload["mentions"]
                ),
                subjects=tuple(
                    CanonicalEngineeringSubject(
                        canonical_subject_id=item["canonical_subject_id"],
                        canonical_label=item["canonical_label"],
                        subject_form=item["subject_form"],
                        identity_status=item["identity_status"],
                        mention_ids=tuple(item["mention_ids"]),
                        content_fingerprint=item["content_fingerprint"],
                    )
                    for item in payload["subjects"]
                ),
                content_fingerprint=payload["content_fingerprint"],
            )
            canonical_subject_set_to_dict(value)
        except Exception as exc:
            raise ProjectReconciliationOrchestrationError(
                "Published Canonical Subject Set violates its exact contract."
            ) from exc
        return value

    def _load_subject_consensus(self, *, reference, history, attempt_id):
        envelope = self._load_subject_artifact_envelope(
            reference=reference,
            history=history,
            attempt_id=attempt_id,
            expected_kind="subject_consensus",
        )
        payload = envelope["payload"]
        try:
            value = SharedSubjectConsensusResult(
                schema_version=payload["schema_version"],
                project_id=payload["project_id"],
                source_id=payload["source_id"],
                source_projection_id=payload["source_projection_id"],
                team_id=payload["team_id"],
                required_personas=tuple(payload["required_personas"]),
                runs_per_persona=payload["runs_per_persona"],
                canonical_subject_ids=tuple(payload["canonical_subject_ids"]),
                subject_outcomes=tuple(
                    SubjectConsensusOutcome(
                        canonical_subject_id=item["canonical_subject_id"],
                        information_type=self._field(item["information_type"]),
                        statement_modality=self._field(
                            item["statement_modality"]
                        ),
                        epistemic_class=self._field(item["epistemic_class"]),
                        statement_variants=tuple(
                            self._statement_variant(v)
                            for v in item["statement_variants"]
                        ),
                        uncertainty_variants=tuple(
                            self._diagnostic_variant(v)
                            for v in item["uncertainty_variants"]
                        ),
                        missing_evidence_variants=tuple(
                            self._diagnostic_variant(v)
                            for v in item["missing_evidence_variants"]
                        ),
                        review_attention_required=item[
                            "review_attention_required"
                        ],
                    )
                    for item in payload["subject_outcomes"]
                ),
                relationship_outcomes=tuple(
                    RelationshipConsensusOutcome(
                        source_subject_id=item["source_subject_id"],
                        relationship_kind=item["relationship_kind"],
                        target_subject_id=item["target_subject_id"],
                        consensus_level=item["consensus_level"],
                        confidence=item["confidence"],
                        total_personas=item["total_personas"],
                        supporting_personas=tuple(item["supporting_personas"]),
                        omitting_personas=tuple(item["omitting_personas"]),
                        unstable_personas=tuple(item["unstable_personas"]),
                        statement_variants=tuple(
                            self._statement_variant(v)
                            for v in item["statement_variants"]
                        ),
                        review_attention_required=item[
                            "review_attention_required"
                        ],
                    )
                    for item in payload["relationship_outcomes"]
                ),
                human_review_required=payload["human_review_required"],
                content_fingerprint=payload["content_fingerprint"],
            )
            serialized = subject_consensus_result_to_dict(value)
            received = serialized.pop("content_fingerprint")
            if self._canonical_sha(serialized) != received:
                raise ValueError("Subject Consensus fingerprint mismatch.")
        except Exception as exc:
            raise ProjectReconciliationOrchestrationError(
                "Published Subject Consensus violates its exact contract."
            ) from exc
        return value

    def _load_subject_artifact_envelope(
        self,
        *,
        reference,
        history,
        attempt_id,
        expected_kind,
    ):
        path = self.project_root / reference.repository_relative_path
        try:
            root = self.project_root.resolve()
            resolved = path.resolve()
            resolved.relative_to(root)
        except (OSError, ValueError) as exc:
            raise ProjectReconciliationOrchestrationError(
                "Published Subject artifact escaped repository authority."
            ) from exc

        if resolved.is_symlink() or not resolved.exists() or not resolved.is_file():
            raise ProjectReconciliationOrchestrationError(
                "Published Subject artifact is unavailable or unsafe."
            )
        try:
            content = resolved.read_bytes()
        except OSError as exc:
            raise ProjectReconciliationOrchestrationError(
                "Published Subject artifact could not be read."
            ) from exc
        if sha256(content).hexdigest() != reference.content_fingerprint:
            raise ProjectReconciliationOrchestrationError(
                "Published Subject artifact file fingerprint mismatch."
            )
        try:
            envelope = json.loads(content.decode("utf-8"))
        except Exception as exc:
            raise ProjectReconciliationOrchestrationError(
                "Published Subject artifact is not valid UTF-8 JSON."
            ) from exc

        if not isinstance(envelope, dict):
            raise ProjectReconciliationOrchestrationError(
                "Published Subject artifact root is invalid."
            )
        body = {
            key: value
            for key, value in envelope.items()
            if key != "content_fingerprint"
        }
        if envelope.get("content_fingerprint") != self._canonical_sha(body):
            raise ProjectReconciliationOrchestrationError(
                "Published Subject artifact internal fingerprint mismatch."
            )
        if (
            envelope.get("schema_version") != "1.0.0"
            or envelope.get("artifact_kind") != expected_kind
        ):
            raise ProjectReconciliationOrchestrationError(
                "Published Subject artifact schema/kind is invalid."
            )

        authority = envelope.get("authority")
        payload = envelope.get("payload")
        if not isinstance(authority, dict) or not isinstance(payload, dict):
            raise ProjectReconciliationOrchestrationError(
                "Published Subject artifact lacks authority/payload."
            )
        manifest = history.manifest
        expected = {
            "project_id": manifest.project_id,
            "source_id": manifest.source_id,
            "source_sha256": manifest.source_sha256,
            "processing_run_id": manifest.processing_run_id,
            "attempt_id": attempt_id,
        }
        for field_name, expected_value in expected.items():
            if authority.get(field_name) != expected_value:
                raise ProjectReconciliationOrchestrationError(
                    "Published Subject artifact does not bind reviewed "
                    f"Processing authority: {field_name}."
                )
        if (
            payload.get("project_id") != manifest.project_id
            or payload.get("source_id") != manifest.source_id
            or authority.get("source_projection_id")
            != payload.get("source_projection_id")
        ):
            raise ProjectReconciliationOrchestrationError(
                "Published Subject artifact Source Projection binding "
                "is inconsistent."
            )
        return envelope

    @staticmethod
    def _field(raw):
        return FieldConsensusAssessment(
            field_name=raw["field_name"],
            consensus_level=raw["consensus_level"],
            confidence=raw["confidence"],
            selected_value=raw["selected_value"],
            total_personas=raw["total_personas"],
            supporting_personas=tuple(raw["supporting_personas"]),
            dissenting_personas=tuple(raw["dissenting_personas"]),
            unstable_personas=tuple(raw["unstable_personas"]),
            value_distribution=tuple(
                ConsensusValueDistribution(
                    value=item["value"],
                    supporting_personas=tuple(item["supporting_personas"]),
                )
                for item in raw["value_distribution"]
            ),
            review_attention_required=raw["review_attention_required"],
        )

    @staticmethod
    def _statement_variant(raw):
        return PersonaStatementVariant(
            persona_id=raw["persona_id"],
            statements=tuple(raw["statements"]),
            stable_across_runs=raw["stable_across_runs"],
        )

    @staticmethod
    def _diagnostic_variant(raw):
        return PersonaDiagnosticVariant(
            persona_id=raw["persona_id"],
            values=tuple(raw["values"]),
            stable_across_runs=raw["stable_across_runs"],
        )

    @staticmethod
    def _canonical_sha(value: Any) -> str:
        canonical = json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        return sha256(canonical.encode("utf-8")).hexdigest()
