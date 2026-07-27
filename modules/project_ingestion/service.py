"""Project-bound Source registration and Processing Run orchestration."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from modules.ingestion.team_agentic_pipeline import (
    run_team_agentic_ingestion,
)
from modules.project_processing import (
    ProjectProcessingRepository,
    create_processing_event,
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

from .configuration import (
    ProjectIngestionConfiguration,
    calculate_ingestion_configuration_fingerprint,
    validate_ingestion_configuration,
    workflow_profile_for_source_role,
)
from .errors import (
    ProjectIngestionExecutionError,
    ProjectIngestionInputError,
    ProjectIngestionPathError,
    ProjectIngestionTemporaryFileError,
)
from .types import (
    ProjectBoundIngestionWorkResult,
    ProjectBoundSourceInventory,
    ProjectBoundSourceIssue,
    ProjectBoundSourceSummary,
)


DEFAULT_PROJECTS_ROOT = Path("data/projects")
AGENTIC_INGESTION_STAGE = "agentic_ingestion"


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
        processing_repository: (
            ProjectProcessingRepository | None
        ) = None,
        project_workspace: ProjectWorkspace | None = None,
        pipeline_runner: Callable[..., Any] = (
            run_team_agentic_ingestion
        ),
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
        self._processing = (
            ProjectProcessingRepository(root=self.root)
            if processing_repository is None
            else processing_repository
        )
        self._workspace = (
            ProjectWorkspace(root=self.root)
            if project_workspace is None
            else project_workspace
        )
        self._pipeline_runner = pipeline_runner

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
    ) -> ProjectBoundIngestionWorkResult:
        """Execute Phase F inside one P5 Run work directory.

        This Step-4 operation creates the Run and Attempt, performs
        deterministic Source Projection and executes Phase F. Generated
        files remain non-authoritative work until Step 5 publishes them.
        """

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
            for (
                reference_id,
                reference_version,
            ) in validated_configuration.semantic_reference_versions
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
            configuration_fingerprint=(
                configuration_fingerprint
            ),
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

        try:
            projection = self._source_projections.create_projection(
                project_id,
                source_id,
            )
        except SourceProjectionError:
            return self._fail_execution(
                history=history,
                attempt_id=attempt_id,
                dry_run=validated_configuration.dry_run,
                source_projection_id=None,
                projection_result=None,
                reason_code="source_normalization_failed",
            )

        if projection.manifest.projection_result == "unavailable":
            return self._fail_execution(
                history=history,
                attempt_id=attempt_id,
                dry_run=validated_configuration.dry_run,
                source_projection_id=(
                    projection.manifest.source_projection_id
                ),
                projection_result=(
                    projection.manifest.projection_result
                ),
                reason_code="text_extraction_insufficient",
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
                recipe_id=validated_configuration.recipe_id,
                raw_input_path=self._repository_relative_path(
                    projection_content_path
                ),
                report_output_path=self._repository_relative_path(
                    report_output_path
                ),
                execution_root=self._repository_relative_path(
                    execution_root
                ),
                provider=validated_configuration.provider,
                model=validated_configuration.model,
                api_key=api_key,
                runs_per_member=(
                    validated_configuration.runs_per_member
                ),
                max_members_per_team=(
                    validated_configuration.max_members_per_team
                ),
                dry_run=validated_configuration.dry_run,
            )
        except Exception:
            return self._fail_execution(
                history=history,
                attempt_id=attempt_id,
                dry_run=validated_configuration.dry_run,
                source_projection_id=(
                    projection.manifest.source_projection_id
                ),
                projection_result=(
                    projection.manifest.projection_result
                ),
                reason_code="team_agentic_ingestion_failed",
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
                dry_run=validated_configuration.dry_run,
                source_projection_id=(
                    projection.manifest.source_projection_id
                ),
                projection_result=(
                    projection.manifest.projection_result
                ),
                reason_code="team_agentic_ingestion_failed",
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
            dry_run=validated_configuration.dry_run,
            projection_result=(
                projection.manifest.projection_result
            ),
            phase_f_run_id=phase_f_run_id,
            failure_reason=None,
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
