"""Project-bound Source registration and Processing Run orchestration."""

from __future__ import annotations

import inspect

from modules.engineering_subjects import (
    EngineeringSubjectDiscoveryAgent,
    EngineeringSubjectGroundingError,
    EngineeringSubjectIntegrityError,
    EngineeringSubjectValidationError,
)
from modules.subject_consensus import analyze_subject_consensus
from modules.subject_interpretation import SubjectInterpretationPipeline
from modules.subject_review import build_subject_review_bundle
from modules.subject_review.artifacts import (
    write_subject_processing_artifacts,
)

from collections.abc import Callable
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from modules.ingestion.team_agentic_pipeline import (
    run_team_agentic_ingestion,
)
from modules.llm.progress import (
    LLMRequestProgressObserver,
    notify_llm_progress,
    notify_processing_phase,
)
from modules.evidence_interpretation import (
    SharedEvidenceInterpretationPipeline,
    build_shared_evidence_review_input,
    shared_evidence_review_input_to_json,
)
from modules.source_evidence import SourceEvidenceRepository
from modules.source_preparation import (
    SourcePreparationService,
    source_preparation_result_to_dict,
)
import json
from modules.project_processing import (
    ProjectProcessingRepository,
    create_processing_event,
    create_retry_event,
    derive_processing_run_state,
    create_processing_run_manifest,
    create_semantic_reference_version,
)
from modules.project_sources import (
    ProjectSourceRegistry,
    SourceManifest,
)
from modules.project_workspace import ProjectWorkspace
from modules.source_projection.errors import (
    SourceProjectionError,
)
from modules.source_projection.repository import (
    SourceProjectionRepository,
)
from modules.source_analysis_units.errors import (
    SourceAnalysisUnitError,
)
from modules.source_analysis_units.repository import (
    SourceAnalysisUnitRepository,
)
from modules.semantic_consolidation.errors import (
    SemanticConsolidationError,
    SemanticConsolidationIntegrityError,
    SemanticConsolidationValidationError,
)
from modules.semantic_consolidation.processing_adapter import (
    consolidate_phase_f_source_anchored_pipeline,
)

from .configuration import (
    ProjectIngestionConfiguration,
    CORRECTED_PIPELINE_CONFIGURATION_VERSION,
    calculate_ingestion_configuration_fingerprint,
    validate_ingestion_configuration,
    workflow_profile_for_source_role,
)
from .failure_classification import (
    classify_pipeline_failure,
)
from .publisher import ProjectIngestionPublisher
from .errors import (
    ProjectIngestionConfigurationError,
    ProjectIngestionExecutionError,
    ProjectIngestionInputError,
    ProjectIngestionOutputValidationError,
    ProjectIngestionPathError,
    ProjectIngestionPublicationError,
    ProjectIngestionRecoveryRequiredError,
    ProjectIngestionTemporaryFileError,
)
from .types import (
    ProjectBoundIngestionExecutionState,
    ProjectBoundIngestionResult,
    ProjectBoundIngestionWorkResult,
    ProjectBoundSourceInventory,
    ProjectBoundSourceIssue,
    ProjectBoundSourceSummary,
)


DEFAULT_PROJECTS_ROOT = Path("data/projects")
AGENTIC_INGESTION_STAGE = "agentic_ingestion"
SUBJECT_DISCOVERY_RAW_RESPONSE_SCHEMA_VERSION = "1.0.0"


def _accepts_optional_keyword_argument(
    function,
    name: str,
) -> bool:
    """Return whether one injected callable accepts an optional keyword."""

    try:
        parameters = inspect.signature(function).parameters.values()
    except (TypeError, ValueError):
        return False

    return any(
        parameter.kind == inspect.Parameter.VAR_KEYWORD
        or parameter.name == name
        for parameter in parameters
    )


def _write_subject_discovery_raw_response(
    *,
    output_root: Path,
    response_kind: str,
    result,
) -> None:
    """Persist one exact non-authoritative raw Subject Discovery response."""

    if response_kind not in {"initial", "grounding_correction"}:
        raise ValueError("Unsupported Subject Discovery response kind.")

    output_text = getattr(result, "text", None)
    provider = getattr(result, "provider", None)
    model = getattr(result, "model", None)
    response_id = getattr(result, "response_id", None)

    if not isinstance(output_text, str):
        raise TypeError("Subject Discovery raw response text must be text.")

    payload = {
        "schema_version": SUBJECT_DISCOVERY_RAW_RESPONSE_SCHEMA_VERSION,
        "diagnostic_only": True,
        "engineering_authority": False,
        "response_kind": response_kind,
        "provider": provider,
        "model": model,
        "response_id": response_id,
        "output_sha256": sha256(
            output_text.encode("utf-8")
        ).hexdigest(),
        "output_text": output_text,
    }

    output_root.mkdir(parents=True, exist_ok=True)
    path = output_root / f"{response_kind}.json"
    temporary = output_root / f".{response_kind}.json.tmp"
    temporary.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _subject_discovery_failure_reason(
    error: Exception,
) -> str:
    if isinstance(error, EngineeringSubjectGroundingError):
        return "subject_discovery_grounding_failed"
    if isinstance(error, EngineeringSubjectValidationError):
        return "subject_discovery_validation_failed"
    if isinstance(error, EngineeringSubjectIntegrityError):
        return "subject_discovery_integrity_failed"
    return "subject_discovery_execution_failed"


def _semantic_consolidation_failure_reason(
    error: SemanticConsolidationError,
) -> str:
    # Recoverable semantic uncertainty must be represented inside semantic
    # consolidation as singleton/unresolved subjects plus warnings and Human
    # Review findings. Only non-recoverable contract/validation/integrity
    # errors are expected to reach this service boundary.
    if isinstance(error, SemanticConsolidationIntegrityError):
        return "semantic_consolidation_integrity_failed"
    if isinstance(error, SemanticConsolidationValidationError):
        return "semantic_consolidation_validation_failed"
    return "semantic_consolidation_contract_failed"


def _default_clock() -> datetime:
    return datetime.now(timezone.utc)


class ProjectBoundIngestionService:
    """Coordinate project-bound ingestion without replacing P2-P5."""

    def __init__(
        self,
        root: Path | str = DEFAULT_PROJECTS_ROOT,
        *,
        repository_root: Path | str = Path("."),
        source_registry: ProjectSourceRegistry | None = None,
        source_projection_repository: (
            SourceProjectionRepository | None
        ) = None,
        source_analysis_unit_repository: (
            SourceAnalysisUnitRepository | None
        ) = None,
        processing_repository: (
            ProjectProcessingRepository | None
        ) = None,
        publisher: ProjectIngestionPublisher | None = None,
        project_workspace: ProjectWorkspace | None = None,
        pipeline_runner: Callable[..., Any] = (
            run_team_agentic_ingestion
        ),
        semantic_consolidator: Callable[..., Any] = (
            consolidate_phase_f_source_anchored_pipeline
        ),
        source_preparation_service: Any | None = None,
        source_evidence_repository: Any | None = None,
        shared_evidence_interpretation_pipeline: Any | None = None,
        engineering_subject_discovery_agent: Any | None = None,
        subject_interpretation_pipeline: Any | None = None,
        clock: Callable[[], datetime] = _default_clock,
    ) -> None:
        self.root = Path(root)
        self.repository_root = Path(repository_root)
        self._clock = clock
        self._source_registry = (
            ProjectSourceRegistry(root=self.root)
            if source_registry is None
            else source_registry
        )
        self._source_projections = (
            SourceProjectionRepository(root=self.root)
            if source_projection_repository is None
            else source_projection_repository
        )
        self._source_analysis_units = (
            SourceAnalysisUnitRepository(
                root=self.root,
                clock=clock,
                source_projection_repository=(
                    self._source_projections
                ),
            )
            if source_analysis_unit_repository is None
            else source_analysis_unit_repository
        )
        self._processing = (
            ProjectProcessingRepository(root=self.root)
            if processing_repository is None
            else processing_repository
        )
        self._publisher = (
            ProjectIngestionPublisher(
                root=self.root,
                repository_root=self.repository_root,
                processing_repository=self._processing,
            )
            if publisher is None
            else publisher
        )
        self._workspace = (
            ProjectWorkspace(root=self.root)
            if project_workspace is None
            else project_workspace
        )
        self._pipeline_runner = pipeline_runner
        self._semantic_consolidator = semantic_consolidator
        self._source_evidence = (
            SourceEvidenceRepository(
                root=self.root,
                clock=clock,
                source_projection_repository=self._source_projections,
            )
            if source_evidence_repository is None
            else source_evidence_repository
        )
        self._source_preparation = (
            SourcePreparationService(
                root=self.root,
                repository_root=self.repository_root,
                clock=clock,
                source_registry=self._source_registry,
                source_projection_repository=self._source_projections,
                source_analysis_unit_repository=self._source_analysis_units,
                source_evidence_repository=self._source_evidence,
            )
            if source_preparation_service is None
            else source_preparation_service
        )
        self._shared_evidence_interpretation = (
            SharedEvidenceInterpretationPipeline(
                project_root=self.repository_root,
                clock=clock,
            )
            if shared_evidence_interpretation_pipeline is None
            else shared_evidence_interpretation_pipeline
        )
        self._engineering_subject_discovery = (
            EngineeringSubjectDiscoveryAgent()
            if engineering_subject_discovery_agent is None
            else engineering_subject_discovery_agent
        )
        self._subject_interpretation = (
            SubjectInterpretationPipeline(
                project_root=self.repository_root,
            )
            if subject_interpretation_pipeline is None
            else subject_interpretation_pipeline
        )

    def register_uploaded_source(
        self,
        project_id: str,
        *,
        original_filename: str,
        content: bytes | bytearray | memoryview,
        source_role: str,
    ) -> ProjectBoundSourceSummary:
        """Register exact uploaded bytes through the authoritative P3 API."""

        validated_filename = _validate_upload_filename(
            original_filename
        )
        validated_content = _validate_upload_content(content)

        try:
            with TemporaryDirectory(
                prefix="turing-source-upload-"
            ) as temporary_directory:
                temporary_path = (
                    Path(temporary_directory) / validated_filename
                )
                temporary_path.write_bytes(validated_content)

                manifest = self._source_registry.register_source(
                    project_id,
                    temporary_path,
                    source_role=source_role,
                )
        except OSError as exc:
            raise ProjectIngestionTemporaryFileError(
                "Unable to prepare the temporary Source upload."
            ) from exc

        return _source_summary(manifest)

    def list_registered_sources(
        self,
        project_id: str,
    ) -> ProjectBoundSourceInventory:
        """Return safe Source inventory data for one Project."""

        scan = self._source_registry.scan_sources(project_id)

        return ProjectBoundSourceInventory(
            project_id=project_id,
            sources=tuple(
                _source_summary(manifest)
                for manifest in scan.valid_sources
            ),
            issues=tuple(
                ProjectBoundSourceIssue(
                    code=issue.code,
                    source_id=issue.source_id,
                )
                for issue in scan.source_issues
            ),
        )

    def load_registered_source(
        self,
        project_id: str,
        source_id: str,
    ) -> ProjectBoundSourceSummary:
        """Load one Source through P3 and return safe metadata."""

        return _source_summary(
            self._source_registry.load_source(
                project_id,
                source_id,
            )
        )

    def execute_registered_source_to_work(
        self,
        project_id: str,
        source_id: str,
        *,
        configuration: ProjectIngestionConfiguration,
        api_key: str | None = None,
        execution_observer: (
            Callable[[ProjectBoundIngestionExecutionState], None]
            | None
        ) = None,
        llm_progress_observer: LLMRequestProgressObserver | None = None,
    ) -> ProjectBoundIngestionWorkResult:
        """Create one new Run and execute its first Phase-F Attempt."""

        validated_configuration = (
            validate_ingestion_configuration(configuration)
        )
        project_manifest = self._workspace.load_project(project_id)
        source_manifest = self._source_registry.load_source(
            project_id,
            source_id,
        )
        processing_run_id = self._processing.next_run_id(
            project_id
        )
        configuration_fingerprint = (
            calculate_ingestion_configuration_fingerprint(
                validated_configuration
            )
        )
        semantic_references = tuple(
            create_semantic_reference_version(
                reference_system_id=reference_id,
                reference_version=reference_version,
            )
            for reference_id, reference_version
            in validated_configuration.semantic_reference_versions
        )
        created_at = self._current_utc_timestamp()

        run_manifest = create_processing_run_manifest(
            project_id=project_id,
            processing_run_id=processing_run_id,
            source_id=source_manifest.source_id,
            source_sha256=source_manifest.sha256,
            source_role_snapshot=source_manifest.source_role,
            workflow_profile=workflow_profile_for_source_role(
                source_manifest.source_role
            ),
            configuration_fingerprint=configuration_fingerprint,
            framework_template_id=(
                project_manifest.framework_template.template_id
            ),
            framework_template_version=(
                project_manifest.framework_template.template_version
            ),
            semantic_reference_versions=semantic_references,
            timestamp=created_at,
        )
        initial_event = create_processing_event(
            project_id=project_id,
            processing_run_id=processing_run_id,
            event_id="EVT-000001",
            event_sequence=1,
            previous_state=None,
            next_state="created",
            processing_stage=None,
            event_type="run_created",
            attempt_id=None,
            reason_code="run_created",
            artifact_references=(),
            timestamp=created_at,
            previous_event_fingerprint=None,
        )
        history = self._processing.create_run(
            run_manifest,
            initial_event,
        )

        attempt_id = self._processing.next_attempt_id(
            project_id,
            processing_run_id,
            AGENTIC_INGESTION_STAGE,
        )
        started_event = create_processing_event(
            project_id=project_id,
            processing_run_id=processing_run_id,
            event_id="EVT-000002",
            event_sequence=2,
            previous_state="created",
            next_state="running",
            processing_stage=AGENTIC_INGESTION_STAGE,
            event_type="stage_started",
            attempt_id=attempt_id,
            reason_code="agentic_ingestion_started",
            artifact_references=(),
            timestamp=self._current_utc_timestamp(),
            previous_event_fingerprint=(
                history.events[-1].event_fingerprint
            ),
        )
        history = self._processing.append_event(started_event)
        self._notify_execution_observer(
            execution_observer,
            history,
        )
        return self._execute_started_attempt(
            history=history,
            attempt_id=attempt_id,
            configuration=validated_configuration,
            api_key=api_key,
            llm_progress_observer=llm_progress_observer,
        )

    def retry_registered_source_to_work(
        self,
        project_id: str,
        source_id: str,
        processing_run_id: str,
        *,
        configuration: ProjectIngestionConfiguration,
        api_key: str | None = None,
        execution_observer: (
            Callable[[ProjectBoundIngestionExecutionState], None]
            | None
        ) = None,
        llm_progress_observer: LLMRequestProgressObserver | None = None,
    ) -> ProjectBoundIngestionWorkResult:
        """Retry one failed unchanged Run as a new immutable Attempt."""

        validated_configuration = (
            validate_ingestion_configuration(configuration)
        )
        project_manifest = self._workspace.load_project(project_id)
        source_manifest = self._source_registry.load_source(
            project_id,
            source_id,
        )
        history = self._processing.load_run(
            project_id,
            processing_run_id,
        )
        self._validate_retry_binding(
            history=history,
            project_manifest=project_manifest,
            source_manifest=source_manifest,
            configuration=validated_configuration,
        )

        attempt_id = self._processing.next_attempt_id(
            project_id,
            processing_run_id,
            AGENTIC_INGESTION_STAGE,
        )
        retry_event = create_retry_event(
            history,
            processing_stage=AGENTIC_INGESTION_STAGE,
            attempt_id=attempt_id,
            reason_code="agentic_ingestion_retry_started",
            timestamp=self._current_utc_timestamp(),
        )
        history = self._processing.append_event(retry_event)
        self._notify_execution_observer(
            execution_observer,
            history,
        )
        return self._execute_started_attempt(
            history=history,
            attempt_id=attempt_id,
            configuration=validated_configuration,
            api_key=api_key,
            llm_progress_observer=llm_progress_observer,
        )

    def _execute_started_attempt(
        self,
        *,
        history: Any,
        attempt_id: str,
        configuration: ProjectIngestionConfiguration,
        api_key: str | None,
        llm_progress_observer: LLMRequestProgressObserver | None,
    ) -> ProjectBoundIngestionWorkResult:
        project_id = history.manifest.project_id
        source_id = history.manifest.source_id
        processing_run_id = history.manifest.processing_run_id

        if (
            configuration.pipeline_configuration_version
            == CORRECTED_PIPELINE_CONFIGURATION_VERSION
        ):
            return self._execute_shared_evidence_attempt(
                history=history,
                attempt_id=attempt_id,
                configuration=configuration,
                api_key=api_key,
                llm_progress_observer=llm_progress_observer,
            )

        try:
            projection = self._source_projections.create_projection(
                project_id,
                source_id,
            )
        except SourceProjectionError:
            return self._fail_execution(
                history=history,
                attempt_id=attempt_id,
                dry_run=configuration.dry_run,
                source_projection_id=None,
                projection_result=None,
                reason_code="source_normalization_failed",
            )

        if projection.manifest.projection_result == "unavailable":
            return self._fail_execution(
                history=history,
                attempt_id=attempt_id,
                dry_run=configuration.dry_run,
                source_projection_id=(
                    projection.manifest.source_projection_id
                ),
                projection_result=(
                    projection.manifest.projection_result
                ),
                reason_code="text_extraction_insufficient",
            )

        try:
            source_analysis_units = (
                self._source_analysis_units.ensure_projection_units(
                    project_id,
                    projection.manifest.source_projection_id,
                )
            )
        except SourceAnalysisUnitError:
            return self._fail_execution(
                history=history,
                attempt_id=attempt_id,
                dry_run=configuration.dry_run,
                source_projection_id=(
                    projection.manifest.source_projection_id
                ),
                projection_result=(
                    projection.manifest.projection_result
                ),
                reason_code=(
                    "source_analysis_unit_preparation_failed"
                ),
            )

        try:
            attempt_work = self._prepare_attempt_work_directory(
                project_id=project_id,
                processing_run_id=processing_run_id,
                attempt_id=attempt_id,
            )
            projection_content_path = (
                self._source_projections.projection_content_path(
                    project_id,
                    projection.manifest.source_projection_id,
                )
            )
            execution_root = attempt_work / "phase_f"
            report_output_path = (
                attempt_work / "ingestion_review_report.md"
            )
            phase_f_result = self._pipeline_runner(
                project_root=self.repository_root,
                task_id=_task_id(
                    project_id=project_id,
                    source_id=source_id,
                    processing_run_id=processing_run_id,
                    attempt_id=attempt_id,
                ),
                recipe_id=configuration.recipe_id,
                raw_input_path=self._repository_relative_path(
                    projection_content_path
                ),
                report_output_path=self._repository_relative_path(
                    report_output_path
                ),
                execution_root=self._repository_relative_path(
                    execution_root
                ),
                source_analysis_units=source_analysis_units,
                provider=configuration.provider,
                model=configuration.model,
                api_key=api_key,
                runs_per_member=configuration.runs_per_member,
                max_members_per_team=(
                    configuration.max_members_per_team
                ),
                dry_run=configuration.dry_run,
            )
        except Exception as exc:
            return self._fail_execution(
                history=history,
                attempt_id=attempt_id,
                dry_run=configuration.dry_run,
                source_projection_id=(
                    projection.manifest.source_projection_id
                ),
                projection_result=(
                    projection.manifest.projection_result
                ),
                reason_code=classify_pipeline_failure(exc),
            )

        phase_f_run_id = getattr(
            phase_f_result,
            "run_id",
            None,
        )
        if (
            not isinstance(phase_f_run_id, str)
            or not phase_f_run_id
        ):
            return self._fail_execution(
                history=history,
                attempt_id=attempt_id,
                dry_run=configuration.dry_run,
                source_projection_id=(
                    projection.manifest.source_projection_id
                ),
                projection_result=(
                    projection.manifest.projection_result
                ),
                reason_code="team_agentic_ingestion_failed",
            )

        try:
            self._semantic_consolidator(
                project_id=project_id,
                processing_run_id=processing_run_id,
                created_at_utc=self._current_utc_timestamp(),
                phase_f_result=phase_f_result,
                phase_f_root=execution_root,
                repository_root=self.repository_root,
                provider=configuration.provider,
                model=configuration.model,
                api_key=api_key,
                dry_run=configuration.dry_run,
            )
        except SemanticConsolidationError as exc:
            return self._fail_execution(
                history=history,
                attempt_id=attempt_id,
                dry_run=configuration.dry_run,
                source_projection_id=(
                    projection.manifest.source_projection_id
                ),
                projection_result=(
                    projection.manifest.projection_result
                ),
                reason_code=_semantic_consolidation_failure_reason(exc),
            )
        except Exception:
            return self._fail_execution(
                history=history,
                attempt_id=attempt_id,
                dry_run=configuration.dry_run,
                source_projection_id=(
                    projection.manifest.source_projection_id
                ),
                projection_result=(
                    projection.manifest.projection_result
                ),
                reason_code="semantic_consolidation_execution_failed",
            )

        return ProjectBoundIngestionWorkResult(
            project_id=project_id,
            source_id=source_id,
            source_projection_id=(
                projection.manifest.source_projection_id
            ),
            processing_run_id=processing_run_id,
            attempt_id=attempt_id,
            run_state="running",
            processing_stage=AGENTIC_INGESTION_STAGE,
            dry_run=configuration.dry_run,
            projection_result=(
                projection.manifest.projection_result
            ),
            phase_f_run_id=phase_f_run_id,
            failure_reason=None,
        )

    def _execute_shared_evidence_attempt(
        self,
        *,
        history: Any,
        attempt_id: str,
        configuration: ProjectIngestionConfiguration,
        api_key: str | None,
        llm_progress_observer: LLMRequestProgressObserver | None,
    ) -> ProjectBoundIngestionWorkResult:
        """Execute Source Preparation and shared-Evidence interpretation."""

        project_id = history.manifest.project_id
        source_id = history.manifest.source_id
        processing_run_id = history.manifest.processing_run_id

        try:
            preparation = self._source_preparation.prepare_registered_source(
                project_id,
                source_id,
                provider=configuration.provider,
                model=configuration.model,
                api_key=api_key,
                dry_run=configuration.dry_run,
                llm_progress_observer=llm_progress_observer,
            )
            projection = self._source_projections.load_projection(
                project_id,
                preparation.source_projection_id,
            )
            attempt_work = self._prepare_attempt_work_directory(
                project_id=project_id,
                processing_run_id=processing_run_id,
                attempt_id=attempt_id,
            )
            phase_f_root = attempt_work / "phase_f"
            phase_f_root.mkdir()
        except Exception:
            return self._fail_execution(
                history=history,
                attempt_id=attempt_id,
                dry_run=configuration.dry_run,
                source_projection_id=None,
                projection_result=None,
                reason_code="source_preparation_failed",
            )

        if (
            preparation.status == "skipped_context_only"
            or configuration.dry_run
        ):
            status = (
                "dry_run_completed"
                if configuration.dry_run
                else "context_only_prepared"
            )
            self._write_shared_evidence_compatibility_outputs(
                attempt_work=attempt_work,
                phase_f_root=phase_f_root,
                status=status,
                preparation=preparation,
                review_input_json=None,
            )
            return ProjectBoundIngestionWorkResult(
                project_id=project_id,
                source_id=source_id,
                source_projection_id=preparation.source_projection_id,
                processing_run_id=processing_run_id,
                attempt_id=attempt_id,
                run_state="running",
                processing_stage=AGENTIC_INGESTION_STAGE,
                dry_run=configuration.dry_run,
                projection_result=projection.manifest.projection_result,
                phase_f_run_id="SHARED-EVIDENCE-V2",
                failure_reason=None,
                workflow_contract="shared_evidence_v2_no_review",
            )

        try:
            all_evidence = self._source_evidence.list_source_evidence(
                project_id,
                source_id=source_id,
                source_projection_id=preparation.source_projection_id,
            )
            required_ids = set(preparation.source_evidence_ids)
            evidence = tuple(
                item
                for item in all_evidence
                if item.source_evidence_id in required_ids
            )
            if {
                item.source_evidence_id for item in evidence
            } != required_ids:
                raise ProjectIngestionExecutionError(
                    "Prepared Source Evidence could not be reopened exactly."
                )

            if not evidence:
                self._write_shared_evidence_compatibility_outputs(
                    attempt_work=attempt_work,
                    phase_f_root=phase_f_root,
                    status="no_source_evidence_detected",
                    preparation=preparation,
                    review_input_json=None,
                )
                return ProjectBoundIngestionWorkResult(
                    project_id=project_id,
                    source_id=source_id,
                    source_projection_id=preparation.source_projection_id,
                    processing_run_id=processing_run_id,
                    attempt_id=attempt_id,
                    run_state="running",
                    processing_stage=AGENTIC_INGESTION_STAGE,
                    dry_run=False,
                    projection_result=projection.manifest.projection_result,
                    phase_f_run_id="SHARED-EVIDENCE-V2",
                    failure_reason=None,
                    workflow_contract="shared_evidence_v2_no_review",
                )

            if llm_progress_observer is not None:
                shared_request_count = (
                    self._shared_evidence_interpretation
                    .planned_request_count(
                        runs_per_persona=configuration.runs_per_member,
                        max_members=configuration.max_members_per_team,
                    )
                )
                subject_request_count = (
                    self._subject_interpretation.planned_request_count(
                        runs_per_persona=configuration.runs_per_member,
                        max_members=None,
                    )
                )
                notify_llm_progress(
                    llm_progress_observer,
                    event_type="planned",
                    stage="evidence_interpretation",
                    request_count=shared_request_count,
                )
                notify_llm_progress(
                    llm_progress_observer,
                    event_type="planned",
                    stage="subject_discovery",
                    request_count=1,
                )
                notify_llm_progress(
                    llm_progress_observer,
                    event_type="planned",
                    stage="subject_interpretation",
                    request_count=subject_request_count,
                )

            interpretation = (
                self._shared_evidence_interpretation.run(
                    source_projection=projection,
                    source_evidence=evidence,
                    execution_root=phase_f_root,
                    provider=configuration.provider,
                    model=configuration.model,
                    api_key=api_key,
                    runs_per_persona=configuration.runs_per_member,
                    max_members=configuration.max_members_per_team,
                    dry_run=False,
                    llm_progress_observer=llm_progress_observer,
                )
            )
            source_manifest = self._source_registry.load_source(
                project_id,
                source_id,
            )
            review_input = build_shared_evidence_review_input(
                source_sha256=source_manifest.sha256,
                processing_run_id=processing_run_id,
                attempt_id=attempt_id,
                source_evidence=evidence,
                interpretation_result=interpretation,
            )
            review_input_json = shared_evidence_review_input_to_json(
                review_input
            )
            self._write_shared_evidence_compatibility_outputs(
                attempt_work=attempt_work,
                phase_f_root=phase_f_root,
                status="awaiting_human_engineering_review",
                preparation=preparation,
                review_input_json=review_input_json,
            )
            # R4c Subject-centric authority is materialized once inside the
            # Processing Attempt. The legacy shared-Evidence outputs above
            # remain a temporary compatibility shadow only.
            try:
                subject_discovery_kwargs = {
                    "source_projection": projection,
                    "source_evidence": evidence,
                    "provider": configuration.provider,
                    "model": configuration.model,
                    "api_key": api_key,
                    "llm_progress_observer": llm_progress_observer,
                }

                discovery_method = (
                    self._engineering_subject_discovery.discover
                )
                if _accepts_optional_keyword_argument(
                    discovery_method,
                    "raw_response_observer",
                ):
                    raw_response_root = (
                        phase_f_root
                        / "agent_outputs"
                        / "subject_discovery"
                        / "raw_responses"
                    )
                    subject_discovery_kwargs[
                        "raw_response_observer"
                    ] = (
                        lambda response_kind, result: (
                            _write_subject_discovery_raw_response(
                                output_root=raw_response_root,
                                response_kind=response_kind,
                                result=result,
                            )
                        )
                    )

                subject_discovery = discovery_method(
                    **subject_discovery_kwargs
                )
            except Exception as exc:
                return self._fail_execution(
                    history=history,
                    attempt_id=attempt_id,
                    dry_run=False,
                    source_projection_id=(
                        preparation.source_projection_id
                    ),
                    projection_result=(
                        projection.manifest.projection_result
                    ),
                    reason_code=_subject_discovery_failure_reason(exc),
                )

            canonical_subject_set = (
                subject_discovery.canonical_subject_set
            )

            try:
                subject_interpretations = (
                    self._subject_interpretation.run(
                        source_projection=projection,
                        subject_set=canonical_subject_set,
                        execution_root=(
                            phase_f_root
                            / "r4c_subject_interpretation"
                        ),
                        provider=configuration.provider,
                        model=configuration.model,
                        api_key=api_key,
                        runs_per_persona=(
                            configuration.runs_per_member
                        ),
                        llm_progress_observer=llm_progress_observer,
                    )
                )
            except Exception:
                return self._fail_execution(
                    history=history,
                    attempt_id=attempt_id,
                    dry_run=False,
                    source_projection_id=(
                        preparation.source_projection_id
                    ),
                    projection_result=(
                        projection.manifest.projection_result
                    ),
                    reason_code="subject_interpretation_failed",
                )

            notify_processing_phase(
                llm_progress_observer,
                stage="compilation",
                detail="validating and assembling processing artifacts",
            )

            try:
                subject_consensus = analyze_subject_consensus(
                    subject_interpretations
                )
            except Exception:
                return self._fail_execution(
                    history=history,
                    attempt_id=attempt_id,
                    dry_run=False,
                    source_projection_id=(
                        preparation.source_projection_id
                    ),
                    projection_result=(
                        projection.manifest.projection_result
                    ),
                    reason_code="subject_consensus_failed",
                )

            try:
                subject_review_bundle = build_subject_review_bundle(
                    subject_set=canonical_subject_set,
                    interpretations=subject_interpretations,
                    consensus=subject_consensus,
                )
                write_subject_processing_artifacts(
                    output_root=phase_f_root / "consensus_reports",
                    source_sha256=source_manifest.sha256,
                    processing_run_id=processing_run_id,
                    attempt_id=attempt_id,
                    subject_set=canonical_subject_set,
                    interpretations=subject_interpretations,
                    consensus=subject_consensus,
                    review_bundle=subject_review_bundle,
                )
            except Exception:
                return self._fail_execution(
                    history=history,
                    attempt_id=attempt_id,
                    dry_run=False,
                    source_projection_id=(
                        preparation.source_projection_id
                    ),
                    projection_result=(
                        projection.manifest.projection_result
                    ),
                    reason_code="subject_review_artifact_failed",
                )
        except Exception:
            return self._fail_execution(
                history=history,
                attempt_id=attempt_id,
                dry_run=False,
                source_projection_id=preparation.source_projection_id,
                projection_result=projection.manifest.projection_result,
                reason_code="shared_evidence_interpretation_failed",
            )

        return ProjectBoundIngestionWorkResult(
            project_id=project_id,
            source_id=source_id,
            source_projection_id=preparation.source_projection_id,
            processing_run_id=processing_run_id,
            attempt_id=attempt_id,
            run_state="running",
            processing_stage=AGENTIC_INGESTION_STAGE,
            dry_run=False,
            projection_result=projection.manifest.projection_result,
            phase_f_run_id="SHARED-EVIDENCE-V2",
            failure_reason=None,
            workflow_contract="shared_evidence_v2_review",
        )

    def _write_shared_evidence_compatibility_outputs(
        self,
        *,
        attempt_work: Path,
        phase_f_root: Path,
        status: str,
        preparation: Any,
        review_input_json: str | None,
    ) -> None:
        """Use the existing immutable P5 publisher as a transport envelope."""

        agent_root = phase_f_root / "agent_outputs"
        consensus_root = phase_f_root / "consensus_reports"
        agent_root.mkdir(exist_ok=True)
        consensus_root.mkdir(exist_ok=True)

        preparation_payload = source_preparation_result_to_dict(
            preparation
        )
        preparation_json = (
            json.dumps(
                preparation_payload,
                ensure_ascii=False,
                indent=2,
            )
            + "\n"
        )
        (
            agent_root / "source_preparation_result.json"
        ).write_text(
            preparation_json,
            encoding="utf-8",
        )

        if review_input_json is not None:
            (
                consensus_root / "shared_evidence_review_input.json"
            ).write_text(
                review_input_json,
                encoding="utf-8",
            )
        elif not any(consensus_root.iterdir()):
            (
                consensus_root / "source_preparation_status.json"
            ).write_text(
                json.dumps(
                    {
                        "schema_version": "1.0.0",
                        "status": status,
                        "source_evidence_ids": list(
                            preparation.source_evidence_ids
                        ),
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

        summary = {
            "schema_version": "1.0.0",
            "run_id": "SHARED-EVIDENCE-V2",
            "status": status,
            "pipeline_contract": "shared_evidence_v2",
            "source_evidence_ids": list(
                preparation.source_evidence_ids
            ),
            "pre_review_model_derivation": False,
            "semantic_consolidation_d3_d4": False,
        }
        summary_json = (
            json.dumps(
                summary,
                ensure_ascii=False,
                indent=2,
            )
            + "\n"
        )
        (
            phase_f_root
            / "team_agentic_ingestion_run_summary.json"
        ).write_text(
            summary_json,
            encoding="utf-8",
        )
        (
            phase_f_root
            / "team_agentic_ingestion_run_summary.md"
        ).write_text(
            "# Shared-Evidence Processing Summary\n\n"
            f"- Status: {status}\n"
            "- Evidence identity fixed before persona interpretation: yes\n"
            "- Pre-review model derivation: no\n"
            "- Pre-review D3/D4 semantic consolidation: no\n",
            encoding="utf-8",
        )
        (
            attempt_work / "ingestion_review_report.md"
        ).write_text(
            "# Shared-Evidence Engineering Review Input\n\n"
            f"Status: {status}\n\n"
            "This corrected pipeline establishes source-grounded Evidence "
            "before persona interpretation. Architecture/model derivation "
            "occurs only after Human Engineering Review.\n",
            encoding="utf-8",
        )

    def source_execution_state(
        self,
        project_id: str,
        source_id: str,
    ) -> ProjectBoundIngestionExecutionState:
        self._workspace.load_project(project_id)
        self._source_registry.load_source(project_id, source_id)
        scan = self._processing.scan_project(project_id)

        blocking_codes = tuple(
            issue.code
            for issue in scan.issues
            if issue.issue_level == "blocking"
        )
        if blocking_codes:
            raise ProjectIngestionRecoveryRequiredError(
                "Project Processing requires recovery before execution."
            )

        current = []
        for history in scan.run_histories:
            if history.manifest.source_id != source_id:
                continue
            state = derive_processing_run_state(history)
            if state.run_state != "superseded":
                current.append((history, state))

        if len(current) > 1:
            raise ProjectIngestionRecoveryRequiredError(
                "Multiple current Processing Runs exist for one Source."
            )

        if not current:
            return ProjectBoundIngestionExecutionState(
                project_id=project_id,
                source_id=source_id,
                processing_run_id=None,
                attempt_id=None,
                run_state=None,
                processing_stage=None,
                failure_reason=None,
                blocked_reason=None,
                pending_review=False,
                configuration_fingerprint=None,
                can_start_new=True,
                can_retry=False,
                recovery_required=False,
            )

        history, state = current[0]
        return self._execution_state_from_history(
            history,
            state=state,
        )

    def execute_registered_source(
        self,
        project_id: str,
        source_id: str,
        *,
        configuration: ProjectIngestionConfiguration,
        api_key: str | None = None,
        execution_observer: (
            Callable[[ProjectBoundIngestionExecutionState], None]
            | None
        ) = None,
        llm_progress_observer: LLMRequestProgressObserver | None = None,
    ) -> ProjectBoundIngestionResult:
        self._require_no_current_run(project_id, source_id)
        work = self.execute_registered_source_to_work(
            project_id,
            source_id,
            configuration=configuration,
            api_key=api_key,
            execution_observer=execution_observer,
            llm_progress_observer=llm_progress_observer,
        )
        return self._complete_work(work)

    def retry_registered_source(
        self,
        project_id: str,
        source_id: str,
        processing_run_id: str,
        *,
        configuration: ProjectIngestionConfiguration,
        api_key: str | None = None,
        execution_observer: (
            Callable[[ProjectBoundIngestionExecutionState], None]
            | None
        ) = None,
        llm_progress_observer: LLMRequestProgressObserver | None = None,
    ) -> ProjectBoundIngestionResult:
        work = self.retry_registered_source_to_work(
            project_id,
            source_id,
            processing_run_id,
            configuration=configuration,
            api_key=api_key,
            execution_observer=execution_observer,
            llm_progress_observer=llm_progress_observer,
        )
        return self._complete_work(work)

    def _complete_work(
        self,
        work: ProjectBoundIngestionWorkResult,
    ) -> ProjectBoundIngestionResult:
        if work.run_state != "running":
            return self._final_result_from_work(work)

        try:
            artifact_references = (
                self._publisher.publish_attempt_outputs(
                    work.project_id,
                    work.processing_run_id,
                    work.attempt_id,
                )
            )
        except ProjectIngestionOutputValidationError:
            return self._finalize_work_failure(
                work,
                reason_code="ingestion_output_validation_failed",
            )
        except ProjectIngestionRecoveryRequiredError:
            return self._finalize_work_recovery(
                work,
                reason_code="artifact_publication_recovery_required",
            )
        except ProjectIngestionPublicationError:
            return self._finalize_work_failure(
                work,
                reason_code="artifact_publication_failed",
            )

        history = self._processing.load_run(
            work.project_id,
            work.processing_run_id,
        )
        latest = history.events[-1]
        published_event = create_processing_event(
            project_id=work.project_id,
            processing_run_id=work.processing_run_id,
            event_id=f"EVT-{latest.event_sequence + 1:06d}",
            event_sequence=latest.event_sequence + 1,
            previous_state=latest.next_state,
            next_state="running",
            processing_stage=AGENTIC_INGESTION_STAGE,
            event_type="artifact_published",
            attempt_id=work.attempt_id,
            reason_code="agentic_ingestion_artifacts_published",
            artifact_references=artifact_references,
            timestamp=self._current_utc_timestamp(),
            previous_event_fingerprint=latest.event_fingerprint,
        )
        try:
            history = self._processing.append_event(
                published_event
            )
        except Exception:
            return self._finalize_work_recovery(
                work,
                reason_code=(
                    "artifact_publication_event_recovery_required"
                ),
                artifact_references=artifact_references,
            )

        if work.workflow_contract == "shared_evidence_v2_no_review":
            latest = history.events[-1]
            completed_event = create_processing_event(
                project_id=work.project_id,
                processing_run_id=work.processing_run_id,
                event_id=f"EVT-{latest.event_sequence + 1:06d}",
                event_sequence=latest.event_sequence + 1,
                previous_state=latest.next_state,
                next_state="completed",
                processing_stage=AGENTIC_INGESTION_STAGE,
                event_type="run_completed",
                attempt_id=work.attempt_id,
                reason_code="shared_evidence_preparation_completed",
                artifact_references=(),
                timestamp=self._current_utc_timestamp(),
                previous_event_fingerprint=latest.event_fingerprint,
            )
            try:
                self._processing.append_event(completed_event)
            except Exception:
                return self._finalize_work_recovery(
                    work,
                    reason_code="corrected_completion_recovery_required",
                    artifact_references=artifact_references,
                )

            return ProjectBoundIngestionResult(
                project_id=work.project_id,
                source_id=work.source_id,
                source_projection_id=work.source_projection_id,
                processing_run_id=work.processing_run_id,
                attempt_id=work.attempt_id,
                run_state="completed",
                processing_stage=work.processing_stage,
                dry_run=work.dry_run,
                projection_result=work.projection_result,
                phase_f_run_id=work.phase_f_run_id,
                artifact_references=artifact_references,
                failure_reason=None,
                recovery_required=False,
            )

        latest = history.events[-1]
        review_event = create_processing_event(
            project_id=work.project_id,
            processing_run_id=work.processing_run_id,
            event_id=f"EVT-{latest.event_sequence + 1:06d}",
            event_sequence=latest.event_sequence + 1,
            previous_state=latest.next_state,
            next_state="awaiting_review",
            processing_stage=AGENTIC_INGESTION_STAGE,
            event_type="review_requested",
            attempt_id=work.attempt_id,
            reason_code="agentic_ingestion_review_requested",
            artifact_references=(),
            timestamp=self._current_utc_timestamp(),
            previous_event_fingerprint=latest.event_fingerprint,
        )
        try:
            self._processing.append_event(review_event)
        except Exception:
            return self._finalize_work_recovery(
                work,
                reason_code="review_request_recovery_required",
                artifact_references=artifact_references,
            )

        return ProjectBoundIngestionResult(
            project_id=work.project_id,
            source_id=work.source_id,
            source_projection_id=work.source_projection_id,
            processing_run_id=work.processing_run_id,
            attempt_id=work.attempt_id,
            run_state="awaiting_review",
            processing_stage=work.processing_stage,
            dry_run=work.dry_run,
            projection_result=work.projection_result,
            phase_f_run_id=work.phase_f_run_id,
            artifact_references=artifact_references,
            failure_reason=None,
            recovery_required=False,
        )

    def _validate_retry_binding(
        self,
        *,
        history: Any,
        project_manifest: Any,
        source_manifest: SourceManifest,
        configuration: ProjectIngestionConfiguration,
    ) -> None:
        state = derive_processing_run_state(history)
        if state.run_state == "blocked":
            raise ProjectIngestionRecoveryRequiredError(
                "Blocked Runs require explicit recovery, not retry."
            )
        if state.run_state != "failed":
            raise ProjectIngestionExecutionError(
                "Only a failed current Processing Run can be retried."
            )

        manifest = history.manifest
        if manifest.source_id != source_manifest.source_id:
            raise ProjectIngestionExecutionError(
                "Retry Source identity does not match the Run."
            )
        if (
            manifest.source_sha256 != source_manifest.sha256
            or manifest.source_role_snapshot
            != source_manifest.source_role
        ):
            raise ProjectIngestionExecutionError(
                "Registered Source bindings changed; retry is unsafe."
            )
        if (
            manifest.workflow_profile
            != workflow_profile_for_source_role(
                source_manifest.source_role
            )
        ):
            raise ProjectIngestionExecutionError(
                "Workflow profile changed; retry is unsafe."
            )

        fingerprint = (
            calculate_ingestion_configuration_fingerprint(
                configuration
            )
        )
        if manifest.configuration_fingerprint != fingerprint:
            raise ProjectIngestionConfigurationError(
                "Retry requires the exact material configuration "
                "of the failed Processing Run."
            )

        expected_semantics = tuple(
            configuration.semantic_reference_versions
        )
        actual_semantics = tuple(
            (
                item.reference_system_id,
                item.reference_version,
            )
            for item in manifest.semantic_reference_versions
        )
        if actual_semantics != expected_semantics:
            raise ProjectIngestionConfigurationError(
                "Retry semantic reference bindings changed."
            )

        framework = project_manifest.framework_template
        if (
            manifest.framework_template_id
            != framework.template_id
            or manifest.framework_template_version
            != framework.template_version
        ):
            raise ProjectIngestionExecutionError(
                "Framework binding changed; successor Run required."
            )

    def _execution_state_from_history(
        self,
        history: Any,
        *,
        state: Any | None = None,
    ) -> ProjectBoundIngestionExecutionState:
        derived = (
            derive_processing_run_state(history)
            if state is None
            else state
        )
        return ProjectBoundIngestionExecutionState(
            project_id=history.manifest.project_id,
            source_id=history.manifest.source_id,
            processing_run_id=(
                history.manifest.processing_run_id
            ),
            attempt_id=derived.latest_attempt_id,
            run_state=derived.run_state,
            processing_stage=derived.processing_stage,
            failure_reason=derived.failure_reason,
            blocked_reason=derived.blocked_reason,
            pending_review=derived.pending_review,
            configuration_fingerprint=(
                history.manifest.configuration_fingerprint
            ),
            can_start_new=False,
            can_retry=(derived.run_state == "failed"),
            recovery_required=(derived.run_state == "blocked"),
        )

    def _notify_execution_observer(
        self,
        observer: (
            Callable[[ProjectBoundIngestionExecutionState], None]
            | None
        ),
        history: Any,
    ) -> None:
        if observer is None:
            return
        snapshot = self._execution_state_from_history(history)
        try:
            observer(snapshot)
        except Exception:
            # Presentation callbacks never control Processing authority.
            return

    def _require_no_current_run(
        self,
        project_id: str,
        source_id: str,
    ) -> None:
        scan = self._processing.scan_project(project_id)
        blocking_codes = tuple(
            issue.code
            for issue in scan.issues
            if issue.issue_level == "blocking"
        )

        if blocking_codes:
            raise ProjectIngestionExecutionError(
                "Project Processing contains blocking issues."
            )

        for history in scan.run_histories:
            if history.manifest.source_id != source_id:
                continue

            state = derive_processing_run_state(history)
            if state.run_state != "superseded":
                raise ProjectIngestionExecutionError(
                    "The selected Source already has a current "
                    "Processing Run. Retry or successor handling "
                    "is required instead of creating another Run."
                )

    def _final_result_from_work(
        self,
        work: ProjectBoundIngestionWorkResult,
    ) -> ProjectBoundIngestionResult:
        return ProjectBoundIngestionResult(
            project_id=work.project_id,
            source_id=work.source_id,
            source_projection_id=work.source_projection_id,
            processing_run_id=work.processing_run_id,
            attempt_id=work.attempt_id,
            run_state=work.run_state,
            processing_stage=work.processing_stage,
            dry_run=work.dry_run,
            projection_result=work.projection_result,
            phase_f_run_id=work.phase_f_run_id,
            artifact_references=(),
            failure_reason=work.failure_reason,
            recovery_required=False,
        )

    def _finalize_work_failure(
        self,
        work: ProjectBoundIngestionWorkResult,
        *,
        reason_code: str,
    ) -> ProjectBoundIngestionResult:
        history = self._processing.load_run(
            work.project_id,
            work.processing_run_id,
        )
        latest = history.events[-1]
        event = create_processing_event(
            project_id=work.project_id,
            processing_run_id=work.processing_run_id,
            event_id=f"EVT-{latest.event_sequence + 1:06d}",
            event_sequence=latest.event_sequence + 1,
            previous_state=latest.next_state,
            next_state="failed",
            processing_stage=AGENTIC_INGESTION_STAGE,
            event_type="run_failed",
            attempt_id=work.attempt_id,
            reason_code=reason_code,
            artifact_references=(),
            timestamp=self._current_utc_timestamp(),
            previous_event_fingerprint=latest.event_fingerprint,
        )
        self._processing.append_event(event)

        return ProjectBoundIngestionResult(
            project_id=work.project_id,
            source_id=work.source_id,
            source_projection_id=work.source_projection_id,
            processing_run_id=work.processing_run_id,
            attempt_id=work.attempt_id,
            run_state="failed",
            processing_stage=work.processing_stage,
            dry_run=work.dry_run,
            projection_result=work.projection_result,
            phase_f_run_id=work.phase_f_run_id,
            artifact_references=(),
            failure_reason=reason_code,
            recovery_required=False,
        )

    def _finalize_work_recovery(
        self,
        work: ProjectBoundIngestionWorkResult,
        *,
        reason_code: str,
        artifact_references: tuple = (),
    ) -> ProjectBoundIngestionResult:
        history = self._processing.load_run(
            work.project_id,
            work.processing_run_id,
        )
        latest = history.events[-1]
        event = create_processing_event(
            project_id=work.project_id,
            processing_run_id=work.processing_run_id,
            event_id=f"EVT-{latest.event_sequence + 1:06d}",
            event_sequence=latest.event_sequence + 1,
            previous_state=latest.next_state,
            next_state="blocked",
            processing_stage=AGENTIC_INGESTION_STAGE,
            event_type="recovery_required",
            attempt_id=work.attempt_id,
            reason_code=reason_code,
            artifact_references=(),
            timestamp=self._current_utc_timestamp(),
            previous_event_fingerprint=latest.event_fingerprint,
        )
        self._processing.append_event(event)

        return ProjectBoundIngestionResult(
            project_id=work.project_id,
            source_id=work.source_id,
            source_projection_id=work.source_projection_id,
            processing_run_id=work.processing_run_id,
            attempt_id=work.attempt_id,
            run_state="blocked",
            processing_stage=work.processing_stage,
            dry_run=work.dry_run,
            projection_result=work.projection_result,
            phase_f_run_id=work.phase_f_run_id,
            artifact_references=artifact_references,
            failure_reason=reason_code,
            recovery_required=True,
        )

    def _fail_execution(
        self,
        *,
        history: Any,
        attempt_id: str,
        dry_run: bool,
        source_projection_id: str | None,
        projection_result: str | None,
        reason_code: str,
    ) -> ProjectBoundIngestionWorkResult:
        latest = history.events[-1]
        failed_event = create_processing_event(
            project_id=history.manifest.project_id,
            processing_run_id=(
                history.manifest.processing_run_id
            ),
            event_id=f"EVT-{latest.event_sequence + 1:06d}",
            event_sequence=latest.event_sequence + 1,
            previous_state=latest.next_state,
            next_state="failed",
            processing_stage=AGENTIC_INGESTION_STAGE,
            event_type="run_failed",
            attempt_id=attempt_id,
            reason_code=reason_code,
            artifact_references=(),
            timestamp=self._current_utc_timestamp(),
            previous_event_fingerprint=(
                latest.event_fingerprint
            ),
        )
        self._processing.append_event(failed_event)

        return ProjectBoundIngestionWorkResult(
            project_id=history.manifest.project_id,
            source_id=history.manifest.source_id,
            source_projection_id=source_projection_id,
            processing_run_id=(
                history.manifest.processing_run_id
            ),
            attempt_id=attempt_id,
            run_state="failed",
            processing_stage=AGENTIC_INGESTION_STAGE,
            dry_run=dry_run,
            projection_result=projection_result,
            phase_f_run_id=None,
            failure_reason=reason_code,
        )

    def _prepare_attempt_work_directory(
        self,
        *,
        project_id: str,
        processing_run_id: str,
        attempt_id: str,
    ) -> Path:
        work_root = self._processing.work_directory(
            project_id,
            processing_run_id,
            create=True,
        )
        attempt_work = (
            work_root
            / AGENTIC_INGESTION_STAGE
            / attempt_id
        )

        self._assert_project_bound(attempt_work)

        for candidate in (
            attempt_work.parent,
            attempt_work,
        ):
            if candidate.is_symlink():
                raise ProjectIngestionPathError(
                    "Symbolic-link execution work paths are rejected."
                )

        if attempt_work.exists():
            raise ProjectIngestionExecutionError(
                "Processing Attempt work directory already exists."
            )

        try:
            attempt_work.mkdir(parents=True)
        except OSError as exc:
            raise ProjectIngestionExecutionError(
                "Unable to create the Processing Attempt work "
                "directory."
            ) from exc

        return attempt_work

    def _repository_relative_path(
        self,
        path: Path,
    ) -> Path:
        resolved_root = self.repository_root.resolve()
        resolved_path = Path(path).resolve()

        try:
            relative = resolved_path.relative_to(
                resolved_root
            )
        except ValueError as exc:
            raise ProjectIngestionPathError(
                "Project-bound execution paths must remain "
                "inside the repository root."
            ) from exc

        if relative.is_absolute() or ".." in relative.parts:
            raise ProjectIngestionPathError(
                "Project-bound repository-relative path is unsafe."
            )

        return relative

    def _assert_project_bound(
        self,
        path: Path,
    ) -> None:
        resolved_project_root = self.root.resolve()
        resolved_path = Path(path).resolve()

        try:
            resolved_path.relative_to(resolved_project_root)
        except ValueError as exc:
            raise ProjectIngestionPathError(
                "Execution work path escaped the project root."
            ) from exc

    def _current_utc_timestamp(self) -> str:
        value = self._clock()

        if not isinstance(value, datetime):
            raise ProjectIngestionExecutionError(
                "clock must return a datetime."
            )

        if value.tzinfo is None:
            raise ProjectIngestionExecutionError(
                "clock must return a timezone-aware datetime."
            )

        return (
            value.astimezone(timezone.utc)
            .isoformat()
            .replace("+00:00", "Z")
        )


def _source_summary(
    manifest: SourceManifest,
) -> ProjectBoundSourceSummary:
    return ProjectBoundSourceSummary(
        project_id=manifest.project_id,
        source_id=manifest.source_id,
        source_role=manifest.source_role,
        original_filename=manifest.original_filename,
        media_type=manifest.media_type,
        size_bytes=manifest.size_bytes,
        sha256=manifest.sha256,
        registered_at=manifest.registered_at,
    )


def _task_id(
    *,
    project_id: str,
    source_id: str,
    processing_run_id: str,
    attempt_id: str,
) -> str:
    values = (
        project_id,
        source_id,
        processing_run_id,
        attempt_id,
    )
    normalized = "_".join(
        value.replace("-", "_")
        for value in values
    )
    return f"P9_{normalized}"


def _validate_upload_filename(value: Any) -> str:
    if not isinstance(value, str):
        raise ProjectIngestionInputError(
            "Uploaded Source filename must be a string."
        )

    if not value.strip():
        raise ProjectIngestionInputError(
            "Uploaded Source filename must not be empty."
        )

    if value in {".", ".."}:
        raise ProjectIngestionInputError(
            "Uploaded Source filename must be a file basename."
        )

    if any(
        character in value
        for character in ("/", "\\", "\x00")
    ):
        raise ProjectIngestionInputError(
            "Uploaded Source filename must not contain path "
            "separators."
        )

    if any(ord(character) < 32 for character in value):
        raise ProjectIngestionInputError(
            "Uploaded Source filename must not contain control "
            "characters."
        )

    return value


def _validate_upload_content(
    value: Any,
) -> bytes:
    if not isinstance(
        value,
        (bytes, bytearray, memoryview),
    ):
        raise ProjectIngestionInputError(
            "Uploaded Source content must be bytes."
        )

    content = bytes(value)

    if not content:
        raise ProjectIngestionInputError(
            "Uploaded Source content must not be empty."
        )

    return content
