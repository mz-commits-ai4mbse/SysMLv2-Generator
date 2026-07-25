"""Persistent project-local Processing Run and Decision operations."""

from __future__ import annotations

import os
from pathlib import Path
import re

from modules.project_sources import (
    ProjectSourceError,
    ProjectSourceRegistry,
)
from modules.project_workspace import (
    ProjectWorkspace,
    ProjectWorkspaceError,
)

from .decision_manifest import (
    processing_decision_filename,
    processing_decision_from_json,
    processing_decision_to_json,
    validate_processing_decision,
)
from .errors import (
    DuplicateProcessingDecisionError,
    DuplicateProcessingEventError,
    ProcessingDecisionNotFoundError,
    ProcessingEventChainError,
    ProcessingIntegrityError,
    ProcessingPersistenceError,
    ProcessingRecoveryRequiredError,
    ProcessingReferenceError,
    ProcessingValidationError,
    ProjectProcessingError,
    ProcessingRunNotFoundError,
    UnsafeProcessingPathError,
)
from .event_manifest import (
    processing_event_filename,
    processing_event_from_json,
    processing_event_to_json,
    validate_processing_event,
)
from .history import (
    create_processing_run_history,
    validate_processing_run_history,
)
from .identifiers import (
    is_valid_processing_attempt_id,
    is_valid_processing_decision_id,
    is_valid_processing_run_id,
    next_processing_attempt_id,
    next_processing_decision_id,
    next_processing_run_id,
    validate_processing_attempt_id,
    validate_processing_decision_id,
    validate_processing_run_id,
)
from .paths import (
    PROCESSING_ARTIFACT_KINDS,
    artifacts_path,
    attempt_artifact_path,
    event_path,
    processing_decision_path,
    processing_decisions_path,
    project_path,
    run_path,
    runs_path,
    work_path,
)
from .run_manifest import (
    PROCESSING_RUN_MANIFEST_FILENAME,
    processing_run_manifest_from_json,
    processing_run_manifest_to_json,
    validate_processing_run_manifest,
)
from .types import (
    PROCESSING_STAGES,
    ProcessingDecision,
    ProcessingEvent,
    ProcessingIssue,
    ProcessingRunHistory,
    ProcessingRunManifest,
    ProcessingScanResult,
)


DEFAULT_PROJECTS_ROOT = Path("data/projects")
_TEMP_RUN_PATTERN = re.compile(
    r"^\.create-(RUN-[0-9]{6})\.tmp$"
)
_TEMP_EVENT_PATTERN = re.compile(
    r"^\.(EVT-[0-9]{6}\.json)\.tmp$"
)
_TEMP_DECISION_PATTERN = re.compile(
    r"^\.(PD-[0-9]{6}\.json)\.tmp$"
)


class ProjectProcessingRepository:
    """Persist, reopen and scan immutable project processing records."""

    def __init__(
        self,
        root: Path | str = DEFAULT_PROJECTS_ROOT,
    ) -> None:
        self.root = Path(root)
        self._workspace = ProjectWorkspace(root=self.root)
        self._sources = ProjectSourceRegistry(root=self.root)

    def next_run_id(self, project_id: str) -> str:
        """Return the next run identifier without reusing gaps."""

        self._workspace.load_project(project_id)
        runs_root = runs_path(self.root, project_id)
        self._assert_optional_directory_safe(
            runs_root,
            label="Processing Run root",
        )

        return next_processing_run_id(
            self._occupied_run_ids(runs_root)
        )

    def next_decision_id(self, project_id: str) -> str:
        """Return the next Processing Decision identifier."""

        self._workspace.load_project(project_id)
        decisions_root = processing_decisions_path(
            self.root,
            project_id,
        )
        self._assert_optional_directory_safe(
            decisions_root,
            label="Processing Decision root",
        )

        return next_processing_decision_id(
            self._occupied_decision_ids(decisions_root)
        )

    def next_attempt_id(
        self,
        project_id: str,
        processing_run_id: str,
        processing_stage: str,
    ) -> str:
        """Return the next attempt ID for one run and stage."""

        self.load_run(project_id, processing_run_id)

        if processing_stage not in PROCESSING_STAGES:
            raise ProcessingValidationError(
                "processing_stage is not supported."
            )

        occupied: set[str] = set()

        for artifact_kind in PROCESSING_ARTIFACT_KINDS:
            stage_path = (
                artifacts_path(
                    self.root,
                    project_id,
                    processing_run_id,
                )
                / artifact_kind
                / processing_stage
            )

            self._assert_optional_directory_safe(
                stage_path,
                label="Processing Attempt stage directory",
            )

            if not stage_path.exists():
                continue

            try:
                entries = tuple(stage_path.iterdir())
            except OSError as exc:
                raise ProcessingPersistenceError(
                    "Unable to inspect Processing Attempt "
                    f"directory {stage_path}: {exc}"
                ) from exc

            for entry in entries:
                if is_valid_processing_attempt_id(entry.name):
                    occupied.add(entry.name)

        return next_processing_attempt_id(occupied)

    def create_run(
        self,
        manifest: ProcessingRunManifest,
        initial_event: ProcessingEvent,
    ) -> ProcessingRunHistory:
        """Atomically persist a new run and its first event."""

        validate_processing_run_manifest(manifest)
        validate_processing_event(initial_event)

        history = create_processing_run_history(
            manifest=manifest,
            events=(initial_event,),
        )

        self._validate_manifest_references(manifest)

        runs_root = runs_path(self.root, manifest.project_id)
        self._ensure_directory(
            runs_root,
            parent=project_path(self.root, manifest.project_id),
            label="Processing Run root",
        )

        final_path = run_path(
            self.root,
            manifest.project_id,
            manifest.processing_run_id,
        )
        temporary_path = runs_root / (
            f".create-{manifest.processing_run_id}.tmp"
        )

        if final_path.exists() or final_path.is_symlink():
            raise ProcessingPersistenceError(
                "Processing Run path already exists: "
                f"{final_path}."
            )

        if temporary_path.exists() or temporary_path.is_symlink():
            raise ProcessingRecoveryRequiredError(
                "Interrupted Processing Run creation requires "
                f"recovery: {temporary_path}."
            )

        try:
            temporary_path.mkdir()
            temporary_events_path = (
                temporary_path / "events"
            )
            temporary_events_path.mkdir()
        except OSError as exc:
            raise ProcessingPersistenceError(
                "Unable to create temporary Processing Run "
                f"directory {temporary_path}: {exc}"
            ) from exc

        manifest_file = (
            temporary_path / PROCESSING_RUN_MANIFEST_FILENAME
        )
        event_file = temporary_events_path / processing_event_filename(
            initial_event.event_id
        )

        self._write_new_text(
            manifest_file,
            processing_run_manifest_to_json(manifest),
            label="Processing Run Manifest",
        )
        self._write_new_text(
            event_file,
            processing_event_to_json(initial_event),
            label="Processing Event",
        )

        persisted = self._load_run_from_directory(
            manifest.project_id,
            manifest.processing_run_id,
            temporary_path,
            validate_references=True,
        )

        if persisted != history:
            raise ProcessingIntegrityError(
                "Persisted Processing Run differs from the "
                "validated history."
            )

        if final_path.exists() or final_path.is_symlink():
            raise ProcessingPersistenceError(
                "Processing Run path appeared during creation: "
                f"{final_path}."
            )

        try:
            temporary_path.rename(final_path)
        except OSError as exc:
            raise ProcessingPersistenceError(
                "Unable to finalize Processing Run directory "
                f"{final_path}: {exc}"
            ) from exc

        return self.load_run(
            manifest.project_id,
            manifest.processing_run_id,
        )

    def append_event(
        self,
        event: ProcessingEvent,
    ) -> ProcessingRunHistory:
        """Append one immutable event to an existing history."""

        validate_processing_event(event)

        current = self.load_run(
            event.project_id,
            event.processing_run_id,
        )
        target = event_path(
            self.root,
            event.project_id,
            event.processing_run_id,
            event.event_id,
        )

        if target.is_symlink():
            raise UnsafeProcessingPathError(
                "Symbolic-link Processing Events are rejected: "
                f"{target}."
            )

        if target.exists():
            existing = self._load_event_file(target)

            if existing == event:
                raise DuplicateProcessingEventError(
                    "Processing Event already exists unchanged: "
                    f"{event.event_id}."
                )

            raise ProcessingIntegrityError(
                "Processing Event identifier is already occupied "
                f"by different content: {event.event_id}."
            )

        candidate = create_processing_run_history(
            manifest=current.manifest,
            events=current.events + (event,),
        )

        temporary_path = target.parent / (
            f".{target.name}.tmp"
        )

        if temporary_path.exists() or temporary_path.is_symlink():
            raise ProcessingRecoveryRequiredError(
                "Interrupted Processing Event append requires "
                f"recovery: {temporary_path}."
            )

        self._write_new_text(
            temporary_path,
            processing_event_to_json(event),
            label="temporary Processing Event",
        )

        persisted_event = self._load_event_file(temporary_path)

        if persisted_event != event:
            raise ProcessingIntegrityError(
                "Persisted Processing Event differs from the "
                "validated event."
            )

        if target.exists() or target.is_symlink():
            raise ProcessingPersistenceError(
                "Processing Event path appeared during append: "
                f"{target}."
            )

        try:
            temporary_path.rename(target)
        except OSError as exc:
            raise ProcessingPersistenceError(
                "Unable to finalize Processing Event "
                f"{target}: {exc}"
            ) from exc

        persisted_history = self.load_run(
            event.project_id,
            event.processing_run_id,
        )

        if persisted_history != candidate:
            raise ProcessingIntegrityError(
                "Persisted Event History differs from the "
                "validated candidate history."
            )

        return persisted_history

    def load_run(
        self,
        project_id: str,
        processing_run_id: str,
    ) -> ProcessingRunHistory:
        """Load and validate one complete Processing Run history."""

        self._workspace.load_project(project_id)
        validated_run_id = validate_processing_run_id(
            processing_run_id
        )
        directory = run_path(
            self.root,
            project_id,
            validated_run_id,
        )

        if directory.is_symlink():
            raise UnsafeProcessingPathError(
                "Symbolic-link Processing Run directories are "
                f"rejected: {directory}."
            )

        if not directory.exists() or not directory.is_dir():
            raise ProcessingRunNotFoundError(
                "Processing Run was not found: "
                f"{project_id}/{validated_run_id}."
            )

        return self._load_run_from_directory(
            project_id,
            validated_run_id,
            directory,
            validate_references=True,
        )

    def persist_decision(
        self,
        decision: ProcessingDecision,
    ) -> ProcessingDecision:
        """Persist one immutable project-local Processing Decision."""

        validate_processing_decision(decision)
        self._validate_decision_references(decision)

        if decision.supersedes_processing_decision_id is not None:
            predecessor = self.load_decision(
                decision.project_id,
                decision.supersedes_processing_decision_id,
            )

            if predecessor.source_id != decision.source_id:
                raise ProcessingReferenceError(
                    "A Processing Decision may supersede only a "
                    "decision for the same source."
                )

            if predecessor.decision_type != decision.decision_type:
                raise ProcessingReferenceError(
                    "A Processing Decision may supersede only the "
                    "same decision type."
                )

        decisions_root = processing_decisions_path(
            self.root,
            decision.project_id,
        )
        self._ensure_directory(
            decisions_root,
            parent=project_path(self.root, decision.project_id),
            label="Processing Decision root",
        )

        target = processing_decision_path(
            self.root,
            decision.project_id,
            decision.processing_decision_id,
        )

        if target.is_symlink():
            raise UnsafeProcessingPathError(
                "Symbolic-link Processing Decisions are rejected: "
                f"{target}."
            )

        if target.exists():
            existing = self._load_decision_file(
                target,
                expected_project_id=decision.project_id,
                expected_decision_id=(
                    decision.processing_decision_id
                ),
            )

            if existing == decision:
                raise DuplicateProcessingDecisionError(
                    "Processing Decision already exists unchanged: "
                    f"{decision.processing_decision_id}."
                )

            raise ProcessingIntegrityError(
                "Processing Decision identifier is occupied by "
                "different content: "
                f"{decision.processing_decision_id}."
            )

        temporary_path = target.parent / (
            f".{target.name}.tmp"
        )

        if temporary_path.exists() or temporary_path.is_symlink():
            raise ProcessingRecoveryRequiredError(
                "Interrupted Processing Decision persistence "
                f"requires recovery: {temporary_path}."
            )

        self._write_new_text(
            temporary_path,
            processing_decision_to_json(decision),
            label="temporary Processing Decision",
        )

        persisted = self._load_decision_file(
            temporary_path,
            expected_project_id=decision.project_id,
            expected_decision_id=(
                decision.processing_decision_id
            ),
        )

        if persisted != decision:
            raise ProcessingIntegrityError(
                "Persisted Processing Decision differs from the "
                "validated decision."
            )

        if target.exists() or target.is_symlink():
            raise ProcessingPersistenceError(
                "Processing Decision path appeared during "
                f"persistence: {target}."
            )

        try:
            temporary_path.rename(target)
        except OSError as exc:
            raise ProcessingPersistenceError(
                "Unable to finalize Processing Decision "
                f"{target}: {exc}"
            ) from exc

        return self.load_decision(
            decision.project_id,
            decision.processing_decision_id,
        )

    def load_decision(
        self,
        project_id: str,
        processing_decision_id: str,
    ) -> ProcessingDecision:
        """Load and validate one Processing Decision."""

        self._workspace.load_project(project_id)
        validated_decision_id = validate_processing_decision_id(
            processing_decision_id
        )
        path = processing_decision_path(
            self.root,
            project_id,
            validated_decision_id,
        )

        if path.is_symlink():
            raise UnsafeProcessingPathError(
                "Symbolic-link Processing Decisions are rejected: "
                f"{path}."
            )

        if not path.exists() or not path.is_file():
            raise ProcessingDecisionNotFoundError(
                "Processing Decision was not found: "
                f"{project_id}/{validated_decision_id}."
            )

        decision = self._load_decision_file(
            path,
            expected_project_id=project_id,
            expected_decision_id=validated_decision_id,
        )
        self._validate_decision_references(decision)

        return decision

    def prepare_attempt_directory(
        self,
        project_id: str,
        processing_run_id: str,
        *,
        artifact_kind: str,
        processing_stage: str,
        attempt_id: str,
    ) -> Path:
        """Create one immutable run/stage/attempt artifact directory."""

        self.load_run(project_id, processing_run_id)
        validate_processing_attempt_id(attempt_id)

        target = attempt_artifact_path(
            self.root,
            project_id,
            processing_run_id,
            artifact_kind=artifact_kind,
            processing_stage=processing_stage,
            attempt_id=attempt_id,
        )
        run_directory = run_path(
            self.root,
            project_id,
            processing_run_id,
        )

        current = run_directory
        for part in target.relative_to(run_directory).parts[:-1]:
            current = current / part
            self._ensure_directory(
                current,
                parent=current.parent,
                label="Processing Attempt parent directory",
            )

        if target.exists() or target.is_symlink():
            raise ProcessingPersistenceError(
                "Processing Attempt artifact directory already "
                f"exists: {target}."
            )

        try:
            target.mkdir()
        except OSError as exc:
            raise ProcessingPersistenceError(
                "Unable to create Processing Attempt artifact "
                f"directory {target}: {exc}"
            ) from exc

        return target

    def work_directory(
        self,
        project_id: str,
        processing_run_id: str,
        *,
        create: bool = False,
    ) -> Path:
        """Return, and optionally create, the temporary work path."""

        self.load_run(project_id, processing_run_id)
        path = work_path(
            self.root,
            project_id,
            processing_run_id,
        )

        if create:
            self._ensure_directory(
                path,
                parent=path.parent,
                label="Processing Run work directory",
            )
        else:
            self._assert_optional_directory_safe(
                path,
                label="Processing Run work directory",
            )

        return path

    def scan_project(
        self,
        project_id: str,
    ) -> ProcessingScanResult:
        """Discover valid processing records and explicit issues."""

        self._workspace.load_project(project_id)

        histories: list[ProcessingRunHistory] = []
        decisions: list[ProcessingDecision] = []
        issues: list[ProcessingIssue] = []

        self._scan_runs(
            project_id,
            histories,
            issues,
        )
        self._scan_decisions(
            project_id,
            decisions,
            issues,
        )

        histories.sort(
            key=lambda history: (
                history.manifest.processing_run_id
            )
        )
        decisions.sort(
            key=lambda decision: (
                decision.processing_decision_id
            )
        )
        issues.sort(
            key=lambda issue: (
                str(issue.path or ""),
                issue.code,
                issue.processing_run_id or "",
                issue.event_id or "",
                issue.processing_decision_id or "",
            )
        )

        return ProcessingScanResult(
            run_histories=tuple(histories),
            decisions=tuple(decisions),
            issues=tuple(issues),
        )

    def _load_run_from_directory(
        self,
        project_id: str,
        processing_run_id: str,
        directory: Path,
        *,
        validate_references: bool,
    ) -> ProcessingRunHistory:
        self._assert_directory_safe(
            directory,
            label="Processing Run directory",
        )

        manifest_file = directory / PROCESSING_RUN_MANIFEST_FILENAME
        events_directory = directory / "events"

        self._assert_file_safe(
            manifest_file,
            label="Processing Run Manifest",
        )
        self._assert_directory_safe(
            events_directory,
            label="Processing Event directory",
        )

        manifest = processing_run_manifest_from_json(
            self._read_text(
                manifest_file,
                label="Processing Run Manifest",
            )
        )

        if manifest.project_id != project_id:
            raise ProcessingIntegrityError(
                "Run Manifest project_id does not match its "
                "project directory."
            )

        if manifest.processing_run_id != processing_run_id:
            raise ProcessingIntegrityError(
                "Run Manifest processing_run_id does not match "
                "its run directory."
            )

        if validate_references:
            self._validate_manifest_references(manifest)

        try:
            entries = sorted(
                events_directory.iterdir(),
                key=lambda entry: entry.name,
            )
        except OSError as exc:
            raise ProcessingPersistenceError(
                "Unable to inspect Processing Event directory "
                f"{events_directory}: {exc}"
            ) from exc

        events: list[ProcessingEvent] = []

        for entry in entries:
            if _TEMP_EVENT_PATTERN.fullmatch(entry.name):
                raise ProcessingRecoveryRequiredError(
                    "Interrupted Processing Event append requires "
                    f"recovery: {entry}."
                )

            if entry.name.startswith("."):
                raise ProcessingIntegrityError(
                    "Unexpected hidden Processing Event entry: "
                    f"{entry}."
                )

            if entry.is_symlink():
                raise UnsafeProcessingPathError(
                    "Symbolic-link Processing Event entries are "
                    f"rejected: {entry}."
                )

            if not entry.is_file():
                raise ProcessingIntegrityError(
                    "Processing Event entries must be files: "
                    f"{entry}."
                )

            event = self._load_event_file(entry)
            expected_filename = processing_event_filename(
                event.event_id
            )

            if entry.name != expected_filename:
                raise ProcessingIntegrityError(
                    "Processing Event filename does not match its "
                    f"event_id: {entry.name!r} != "
                    f"{expected_filename!r}."
                )

            events.append(event)

        history = create_processing_run_history(
            manifest=manifest,
            events=tuple(events),
        )
        validate_processing_run_history(history)

        self._validate_optional_run_directories(
            project_id,
            processing_run_id,
        )

        return history

    def _load_event_file(self, path: Path) -> ProcessingEvent:
        self._assert_file_safe(
            path,
            label="Processing Event",
        )

        return processing_event_from_json(
            self._read_text(path, label="Processing Event")
        )

    def _load_decision_file(
        self,
        path: Path,
        *,
        expected_project_id: str,
        expected_decision_id: str,
    ) -> ProcessingDecision:
        self._assert_file_safe(
            path,
            label="Processing Decision",
        )
        decision = processing_decision_from_json(
            self._read_text(path, label="Processing Decision")
        )

        if decision.project_id != expected_project_id:
            raise ProcessingIntegrityError(
                "Processing Decision project_id does not match "
                "its project directory."
            )

        if (
            decision.processing_decision_id
            != expected_decision_id
        ):
            raise ProcessingIntegrityError(
                "Processing Decision ID does not match its "
                "filename."
            )

        expected_filename = processing_decision_filename(
            decision.processing_decision_id
        )

        if path.name not in {
            expected_filename,
            f".{expected_filename}.tmp",
        }:
            raise ProcessingIntegrityError(
                "Processing Decision filename does not match its "
                "identifier."
            )

        return decision

    def _validate_manifest_references(
        self,
        manifest: ProcessingRunManifest,
    ) -> None:
        try:
            self._workspace.load_project(manifest.project_id)
            source = self._sources.load_source(
                manifest.project_id,
                manifest.source_id,
            )
        except (ProjectWorkspaceError, ProjectSourceError) as exc:
            raise ProcessingReferenceError(
                "Processing Run references an unavailable project "
                "or source."
            ) from exc

        if source.sha256 != manifest.source_sha256:
            raise ProcessingReferenceError(
                "Processing Run source_sha256 does not match the "
                "registered source."
            )

        if source.source_role != manifest.source_role_snapshot:
            raise ProcessingReferenceError(
                "Processing Run source_role_snapshot does not match "
                "the registered source."
            )

        if manifest.supersedes_run_id is not None:
            predecessor = self.load_run(
                manifest.project_id,
                manifest.supersedes_run_id,
            )

            if predecessor.manifest.source_id != manifest.source_id:
                raise ProcessingReferenceError(
                    "A successor Processing Run must reference the "
                    "same primary source as its predecessor."
                )

    def _validate_decision_references(
        self,
        decision: ProcessingDecision,
    ) -> None:
        try:
            self._workspace.load_project(decision.project_id)
            source = self._sources.load_source(
                decision.project_id,
                decision.source_id,
            )
        except (ProjectWorkspaceError, ProjectSourceError) as exc:
            raise ProcessingReferenceError(
                "Processing Decision references an unavailable "
                "project or source."
            ) from exc

        if source.sha256 != decision.source_sha256:
            raise ProcessingReferenceError(
                "Processing Decision source_sha256 does not match "
                "the registered source."
            )

    def _validate_optional_run_directories(
        self,
        project_id: str,
        processing_run_id: str,
    ) -> None:
        artifact_root = artifacts_path(
            self.root,
            project_id,
            processing_run_id,
        )
        temporary_work = work_path(
            self.root,
            project_id,
            processing_run_id,
        )

        self._assert_optional_directory_safe(
            artifact_root,
            label="Processing artifact root",
        )
        self._assert_optional_directory_safe(
            temporary_work,
            label="Processing work directory",
        )

        if not artifact_root.exists():
            return

        try:
            kind_entries = tuple(artifact_root.iterdir())
        except OSError as exc:
            raise ProcessingPersistenceError(
                "Unable to inspect Processing artifact root "
                f"{artifact_root}: {exc}"
            ) from exc

        for kind_entry in kind_entries:
            if kind_entry.name.startswith("."):
                raise ProcessingIntegrityError(
                    "Unexpected hidden processing artifact entry: "
                    f"{kind_entry}."
                )

            if kind_entry.name not in PROCESSING_ARTIFACT_KINDS:
                raise ProcessingIntegrityError(
                    "Unexpected processing artifact kind: "
                    f"{kind_entry.name!r}."
                )

            self._assert_directory_safe(
                kind_entry,
                label="Processing artifact kind directory",
            )

            for stage_entry in kind_entry.iterdir():
                if stage_entry.name not in PROCESSING_STAGES:
                    raise ProcessingIntegrityError(
                        "Unexpected Processing Stage directory: "
                        f"{stage_entry.name!r}."
                    )

                self._assert_directory_safe(
                    stage_entry,
                    label="Processing Stage directory",
                )

                for attempt_entry in stage_entry.iterdir():
                    if not is_valid_processing_attempt_id(
                        attempt_entry.name
                    ):
                        raise ProcessingIntegrityError(
                            "Unexpected Processing Attempt "
                            f"directory: {attempt_entry.name!r}."
                        )

                    self._assert_directory_safe(
                        attempt_entry,
                        label="Processing Attempt directory",
                    )

    def _scan_runs(
        self,
        project_id: str,
        histories: list[ProcessingRunHistory],
        issues: list[ProcessingIssue],
    ) -> None:
        root = runs_path(self.root, project_id)

        if root.is_symlink():
            issues.append(
                self._issue(
                    project_id,
                    code="unsafe_runs_root",
                    message=(
                        "Symbolic-link Processing Run roots are "
                        "rejected."
                    ),
                    path=root,
                )
            )
            return

        if not root.exists():
            return

        if not root.is_dir():
            issues.append(
                self._issue(
                    project_id,
                    code="unsafe_runs_root",
                    message=(
                        "Processing Run root is not a directory."
                    ),
                    path=root,
                )
            )
            return

        try:
            entries = sorted(root.iterdir(), key=lambda item: item.name)
        except OSError as exc:
            issues.append(
                self._issue(
                    project_id,
                    code="runs_root_read_error",
                    message=(
                        "Unable to inspect Processing Run root: "
                        f"{exc}"
                    ),
                    path=root,
                )
            )
            return

        for entry in entries:
            temporary_match = _TEMP_RUN_PATTERN.fullmatch(entry.name)

            if temporary_match is not None:
                issues.append(
                    self._issue(
                        project_id,
                        code="interrupted_run_creation",
                        message=(
                            "Interrupted Processing Run creation "
                            "requires explicit recovery."
                        ),
                        path=entry,
                        processing_run_id=temporary_match.group(1),
                    )
                )
                continue

            candidate_run_id = (
                entry.name
                if is_valid_processing_run_id(entry.name)
                else None
            )

            if entry.is_symlink():
                issues.append(
                    self._issue(
                        project_id,
                        code="unsafe_run_path",
                        message=(
                            "Symbolic-link Processing Run entries "
                            "are rejected."
                        ),
                        path=entry,
                        processing_run_id=candidate_run_id,
                    )
                )
                continue

            if entry.name.startswith("."):
                issues.append(
                    self._issue(
                        project_id,
                        code="unexpected_hidden_run_entry",
                        message=(
                            "Unexpected hidden Processing Run entry."
                        ),
                        path=entry,
                    )
                )
                continue

            if not entry.is_dir():
                issues.append(
                    self._issue(
                        project_id,
                        code="unexpected_run_entry",
                        message=(
                            "Processing Run entries must be "
                            "directories."
                        ),
                        path=entry,
                        processing_run_id=candidate_run_id,
                    )
                )
                continue

            if candidate_run_id is None:
                issues.append(
                    self._issue(
                        project_id,
                        code="invalid_run_directory",
                        message=(
                            "Processing Run directory name must "
                            "match ^RUN-[0-9]{6}$."
                        ),
                        path=entry,
                    )
                )
                continue

            try:
                histories.append(
                    self.load_run(project_id, candidate_run_id)
                )
            except ProjectProcessingError as exc:
                issues.append(
                    self._issue(
                        project_id,
                        code=self._issue_code_for_exception(
                            exc,
                            default="invalid_run_history",
                        ),
                        message=str(exc),
                        path=entry,
                        processing_run_id=candidate_run_id,
                    )
                )

    def _scan_decisions(
        self,
        project_id: str,
        decisions: list[ProcessingDecision],
        issues: list[ProcessingIssue],
    ) -> None:
        root = processing_decisions_path(self.root, project_id)

        if root.is_symlink():
            issues.append(
                self._issue(
                    project_id,
                    code="unsafe_decisions_root",
                    message=(
                        "Symbolic-link Processing Decision roots "
                        "are rejected."
                    ),
                    path=root,
                )
            )
            return

        if not root.exists():
            return

        if not root.is_dir():
            issues.append(
                self._issue(
                    project_id,
                    code="unsafe_decisions_root",
                    message=(
                        "Processing Decision root is not a directory."
                    ),
                    path=root,
                )
            )
            return

        try:
            entries = sorted(root.iterdir(), key=lambda item: item.name)
        except OSError as exc:
            issues.append(
                self._issue(
                    project_id,
                    code="decisions_root_read_error",
                    message=(
                        "Unable to inspect Processing Decision root: "
                        f"{exc}"
                    ),
                    path=root,
                )
            )
            return

        for entry in entries:
            temporary_match = _TEMP_DECISION_PATTERN.fullmatch(entry.name)

            if temporary_match is not None:
                decision_id = temporary_match.group(1).removesuffix(
                    ".json"
                )
                issues.append(
                    self._issue(
                        project_id,
                        code="interrupted_decision_persistence",
                        message=(
                            "Interrupted Processing Decision "
                            "persistence requires explicit recovery."
                        ),
                        path=entry,
                        processing_decision_id=decision_id,
                    )
                )
                continue

            if entry.is_symlink():
                issues.append(
                    self._issue(
                        project_id,
                        code="unsafe_decision_path",
                        message=(
                            "Symbolic-link Processing Decision "
                            "entries are rejected."
                        ),
                        path=entry,
                    )
                )
                continue

            if entry.name.startswith("."):
                issues.append(
                    self._issue(
                        project_id,
                        code="unexpected_hidden_decision_entry",
                        message=(
                            "Unexpected hidden Processing Decision "
                            "entry."
                        ),
                        path=entry,
                    )
                )
                continue

            if not entry.is_file():
                issues.append(
                    self._issue(
                        project_id,
                        code="unexpected_decision_entry",
                        message=(
                            "Processing Decision entries must be "
                            "JSON files."
                        ),
                        path=entry,
                    )
                )
                continue

            if not entry.name.endswith(".json"):
                issues.append(
                    self._issue(
                        project_id,
                        code="invalid_decision_filename",
                        message=(
                            "Processing Decision filename must end "
                            "with .json."
                        ),
                        path=entry,
                    )
                )
                continue

            candidate_id = entry.name.removesuffix(".json")

            if not is_valid_processing_decision_id(candidate_id):
                issues.append(
                    self._issue(
                        project_id,
                        code="invalid_decision_filename",
                        message=(
                            "Processing Decision filename must "
                            "match ^PD-[0-9]{6}\\.json$."
                        ),
                        path=entry,
                    )
                )
                continue

            try:
                decisions.append(
                    self.load_decision(project_id, candidate_id)
                )
            except ProjectProcessingError as exc:
                issues.append(
                    self._issue(
                        project_id,
                        code=self._issue_code_for_exception(
                            exc,
                            default="invalid_processing_decision",
                        ),
                        message=str(exc),
                        path=entry,
                        processing_decision_id=candidate_id,
                    )
                )

    def _occupied_run_ids(self, root: Path) -> tuple[str, ...]:
        if not root.exists():
            return ()

        occupied: set[str] = set()

        try:
            entries = tuple(root.iterdir())
        except OSError as exc:
            raise ProcessingPersistenceError(
                "Unable to inspect Processing Run root "
                f"{root}: {exc}"
            ) from exc

        for entry in entries:
            if is_valid_processing_run_id(entry.name):
                occupied.add(entry.name)
                continue

            match = _TEMP_RUN_PATTERN.fullmatch(entry.name)
            if match is not None:
                occupied.add(match.group(1))

        return tuple(sorted(occupied))

    def _occupied_decision_ids(self, root: Path) -> tuple[str, ...]:
        if not root.exists():
            return ()

        occupied: set[str] = set()

        try:
            entries = tuple(root.iterdir())
        except OSError as exc:
            raise ProcessingPersistenceError(
                "Unable to inspect Processing Decision root "
                f"{root}: {exc}"
            ) from exc

        for entry in entries:
            if entry.name.endswith(".json"):
                candidate = entry.name.removesuffix(".json")
                if is_valid_processing_decision_id(candidate):
                    occupied.add(candidate)
                    continue

            match = _TEMP_DECISION_PATTERN.fullmatch(entry.name)
            if match is not None:
                occupied.add(
                    match.group(1).removesuffix(".json")
                )

        return tuple(sorted(occupied))

    def _ensure_directory(
        self,
        path: Path,
        *,
        parent: Path,
        label: str,
    ) -> None:
        self._assert_lexically_within(path, parent)

        if path.is_symlink():
            raise UnsafeProcessingPathError(
                f"Symbolic-link {label} is rejected: {path}."
            )

        if path.exists():
            if not path.is_dir():
                raise UnsafeProcessingPathError(
                    f"{label} is not a directory: {path}."
                )
            return

        if parent.is_symlink() or not parent.is_dir():
            raise UnsafeProcessingPathError(
                f"Parent directory is unsafe for {label}: {parent}."
            )

        try:
            path.mkdir()
        except OSError as exc:
            raise ProcessingPersistenceError(
                f"Unable to create {label} {path}: {exc}"
            ) from exc

    def _assert_optional_directory_safe(
        self,
        path: Path,
        *,
        label: str,
    ) -> None:
        if path.is_symlink():
            raise UnsafeProcessingPathError(
                f"Symbolic-link {label} is rejected: {path}."
            )

        if path.exists() and not path.is_dir():
            raise UnsafeProcessingPathError(
                f"{label} is not a directory: {path}."
            )

    def _assert_directory_safe(
        self,
        path: Path,
        *,
        label: str,
    ) -> None:
        if path.is_symlink():
            raise UnsafeProcessingPathError(
                f"Symbolic-link {label} is rejected: {path}."
            )

        if not path.exists() or not path.is_dir():
            raise ProcessingIntegrityError(
                f"Required {label} is missing or not a directory: "
                f"{path}."
            )

    def _assert_file_safe(
        self,
        path: Path,
        *,
        label: str,
    ) -> None:
        if path.is_symlink():
            raise UnsafeProcessingPathError(
                f"Symbolic-link {label} is rejected: {path}."
            )

        if not path.exists() or not path.is_file():
            raise ProcessingIntegrityError(
                f"Required {label} is missing or not a file: "
                f"{path}."
            )

    @staticmethod
    def _assert_lexically_within(
        path: Path,
        parent: Path,
    ) -> None:
        try:
            path.relative_to(parent)
        except ValueError as exc:
            raise UnsafeProcessingPathError(
                f"Processing path escapes its authority root: {path}."
            ) from exc

    @staticmethod
    def _write_new_text(
        path: Path,
        text: str,
        *,
        label: str,
    ) -> None:
        try:
            with path.open("x", encoding="utf-8") as stream:
                stream.write(text)
                stream.flush()
                os.fsync(stream.fileno())
        except FileExistsError as exc:
            raise ProcessingPersistenceError(
                f"{label} path already exists: {path}."
            ) from exc
        except OSError as exc:
            raise ProcessingPersistenceError(
                f"Unable to persist {label} {path}: {exc}"
            ) from exc

    @staticmethod
    def _read_text(
        path: Path,
        *,
        label: str,
    ) -> str:
        try:
            return path.read_text(encoding="utf-8")
        except OSError as exc:
            raise ProcessingPersistenceError(
                f"Unable to read {label} {path}: {exc}"
            ) from exc

    @staticmethod
    def _issue(
        project_id: str,
        *,
        code: str,
        message: str,
        path: Path,
        processing_run_id: str | None = None,
        event_id: str | None = None,
        processing_decision_id: str | None = None,
    ) -> ProcessingIssue:
        return ProcessingIssue(
            project_id=project_id,
            code=code,
            message=message,
            issue_level="blocking",
            path=path,
            processing_run_id=processing_run_id,
            event_id=event_id,
            processing_decision_id=processing_decision_id,
        )

    @staticmethod
    def _issue_code_for_exception(
        exc: Exception,
        *,
        default: str,
    ) -> str:
        if isinstance(exc, UnsafeProcessingPathError):
            return "unsafe_processing_path"
        if isinstance(exc, ProcessingRecoveryRequiredError):
            return "processing_recovery_required"
        if isinstance(exc, ProcessingReferenceError):
            return "invalid_processing_reference"
        if isinstance(exc, ProcessingEventChainError):
            return "invalid_event_history"
        if isinstance(exc, ProcessingIntegrityError):
            return "processing_integrity_error"
        return default