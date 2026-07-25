"""Persistent retry and supersession operations for project processing."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path

from .errors import (
    ProcessingIntegrityError,
    ProcessingRecoveryRequiredError,
    ProcessingReferenceError,
    ProcessingValidationError,
)
from .run_lifecycle import (
    create_retry_event,
    create_run_superseded_event,
    create_successor_initial_event,
    derive_project_run_states,
    derive_supersession_index,
    validate_successor_manifest,
)
from .run_manifest import validate_processing_run_manifest
from .repository import (
    DEFAULT_PROJECTS_ROOT,
    ProjectProcessingRepository,
)
from .types import (
    DerivedProcessingRunState,
    ProcessingIssue,
    ProcessingRunHistory,
    ProcessingRunManifest,
    ProcessingScanResult,
)


def _default_clock() -> datetime:
    return datetime.now(timezone.utc)


class ProjectProcessingOperations:
    """Execute durable retry and supersession workflows."""

    def __init__(
        self,
        root: Path | str = DEFAULT_PROJECTS_ROOT,
        *,
        repository: ProjectProcessingRepository | None = None,
        clock: Callable[[], datetime] = _default_clock,
    ) -> None:
        self.root = Path(root)
        self.repository = (
            repository
            if repository is not None
            else ProjectProcessingRepository(root=self.root)
        )
        self._clock = clock

    def start_retry(
        self,
        project_id: str,
        processing_run_id: str,
        *,
        artifact_kind: str,
        processing_stage: str,
        reason_code: str,
    ) -> ProcessingRunHistory:
        """Create one new Attempt directory and append its retry event."""

        self._require_consistent_project(project_id)
        history = self.repository.load_run(
            project_id,
            processing_run_id,
        )
        attempt_id = self.repository.next_attempt_id(
            project_id,
            processing_run_id,
            processing_stage,
        )
        event = create_retry_event(
            history,
            processing_stage=processing_stage,
            attempt_id=attempt_id,
            reason_code=reason_code,
            timestamp=self._current_utc_timestamp(),
        )

        attempt_directory = self.repository.prepare_attempt_directory(
            project_id,
            processing_run_id,
            artifact_kind=artifact_kind,
            processing_stage=processing_stage,
            attempt_id=attempt_id,
        )

        try:
            return self.repository.append_event(event)
        except Exception as exc:
            self._remove_empty_attempt_directory(
                attempt_directory,
                original_error=exc,
            )
            raise

    def create_successor_run(
        self,
        predecessor_run_id: str,
        successor_manifest: ProcessingRunManifest,
        *,
        reason_code: str,
    ) -> tuple[ProcessingRunHistory, ProcessingRunHistory]:
        """Persist a successor and close its predecessor deterministically."""

        validated_successor = validate_processing_run_manifest(
            successor_manifest
        )
        project_id = validated_successor.project_id
        self._require_consistent_project(project_id)

        predecessor = self.repository.load_run(
            project_id,
            predecessor_run_id,
        )
        validate_successor_manifest(
            predecessor.manifest,
            validated_successor,
        )

        expected_run_id = self.repository.next_run_id(project_id)
        if validated_successor.processing_run_id != expected_run_id:
            raise ProcessingValidationError(
                "Successor processing_run_id must be the next available "
                f"project-local Run ID: {expected_run_id}."
            )

        initial_event = create_successor_initial_event(
            validated_successor
        )
        superseded_event = create_run_superseded_event(
            predecessor,
            validated_successor,
            reason_code=reason_code,
            timestamp=self._current_utc_timestamp(),
        )

        self.repository.create_run(
            validated_successor,
            initial_event,
        )

        try:
            self.repository.append_event(superseded_event)
        except Exception as exc:
            raise ProcessingRecoveryRequiredError(
                "Successor Processing Run was persisted, but the "
                "predecessor supersession event could not be completed."
            ) from exc

        validated_scan = self.scan_project(project_id)
        blocking_issues = tuple(
            issue
            for issue in validated_scan.issues
            if issue.issue_level == "blocking"
        )

        if blocking_issues:
            raise ProcessingRecoveryRequiredError(
                "Persisted supersession requires recovery: "
                + ", ".join(
                    issue.code for issue in blocking_issues
                )
                + "."
            )

        derive_supersession_index(validated_scan.run_histories)

        return (
            self.repository.load_run(
                project_id,
                predecessor_run_id,
            ),
            self.repository.load_run(
                project_id,
                validated_successor.processing_run_id,
            ),
        )

    def scan_project(
        self,
        project_id: str,
    ) -> ProcessingScanResult:
        """Scan records and add deterministic lifecycle diagnostics."""

        scan = self.repository.scan_project(project_id)
        issues = list(scan.issues)

        try:
            derive_supersession_index(scan.run_histories)
        except ProcessingRecoveryRequiredError as exc:
            issues.append(
                self._lifecycle_issue(
                    project_id,
                    code="supersession_recovery_required",
                    message=str(exc),
                )
            )
        except ProcessingReferenceError as exc:
            issues.append(
                self._lifecycle_issue(
                    project_id,
                    code="invalid_supersession_reference",
                    message=str(exc),
                )
            )
        except ProcessingIntegrityError as exc:
            issues.append(
                self._lifecycle_issue(
                    project_id,
                    code="invalid_supersession_relationship",
                    message=str(exc),
                )
            )
        except ProcessingValidationError as exc:
            issues.append(
                self._lifecycle_issue(
                    project_id,
                    code="invalid_supersession_contract",
                    message=str(exc),
                )
            )

        issues.sort(
            key=lambda issue: (
                issue.code,
                str(issue.path or ""),
                issue.processing_run_id or "",
                issue.event_id or "",
                issue.processing_decision_id or "",
            )
        )

        return ProcessingScanResult(
            run_histories=scan.run_histories,
            decisions=scan.decisions,
            issues=tuple(issues),
        )

    def derive_run_states(
        self,
        project_id: str,
    ) -> tuple[DerivedProcessingRunState, ...]:
        """Return run states only when the project scan is consistent."""

        scan = self.scan_project(project_id)
        blocking_codes = tuple(
            issue.code
            for issue in scan.issues
            if issue.issue_level == "blocking"
        )

        if blocking_codes:
            raise ProcessingRecoveryRequiredError(
                "Project Processing State cannot be derived while "
                "blocking issues exist: "
                + ", ".join(blocking_codes)
                + "."
            )

        return derive_project_run_states(scan.run_histories)

    def _require_consistent_project(self, project_id: str) -> None:
        scan = self.scan_project(project_id)
        blocking_codes = tuple(
            issue.code
            for issue in scan.issues
            if issue.issue_level == "blocking"
        )

        if blocking_codes:
            raise ProcessingRecoveryRequiredError(
                "Project processing operations are blocked by: "
                + ", ".join(blocking_codes)
                + "."
            )

    def _current_utc_timestamp(self) -> str:
        value = self._clock()

        if not isinstance(value, datetime):
            raise ProcessingValidationError(
                "clock must return a datetime."
            )

        if value.tzinfo is None or value.utcoffset() is None:
            raise ProcessingValidationError(
                "clock must return a timezone-aware datetime."
            )

        return (
            value.astimezone(timezone.utc)
            .isoformat()
            .replace("+00:00", "Z")
        )

    @staticmethod
    def _lifecycle_issue(
        project_id: str,
        *,
        code: str,
        message: str,
    ) -> ProcessingIssue:
        return ProcessingIssue(
            project_id=project_id,
            code=code,
            message=message,
            issue_level="blocking",
        )

    @staticmethod
    def _remove_empty_attempt_directory(
        path: Path,
        *,
        original_error: Exception,
    ) -> None:
        try:
            path.rmdir()
        except OSError as cleanup_error:
            raise ProcessingRecoveryRequiredError(
                "Retry Event persistence failed and its Attempt "
                "directory could not be rolled back: "
                f"{path}. Cleanup error: {cleanup_error}."
            ) from original_error