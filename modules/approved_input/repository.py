"""Project-isolated persistence for immutable Approved Input manifests."""

from __future__ import annotations

import os
from pathlib import Path

from modules.project_workspace import (
    ProjectWorkspace,
    ProjectWorkspaceError,
)

from .errors import (
    ApprovedInputEventNotFoundError,
    ApprovedInputIntegrityError,
    ApprovedInputNotFoundError,
    ApprovedInputPersistenceError,
    ApprovedInputRecoveryRequiredError,
    ApprovedInputReferenceError,
    UnsafeApprovedInputPathError,
)
from .event_manifest import (
    approved_input_event_from_json,
    approved_input_event_to_json,
    validate_approved_input_event,
)
from .identifiers import (
    next_approved_input_event_id as allocate_next_approved_input_event_id,
    next_approved_input_id as allocate_next_approved_input_id,
    validate_approved_input_event_id,
    validate_approved_input_id,
)
from .lifecycle import (
    active_approved_input_manifests,
    derive_approved_input_authority_states,
)
from .manifest import (
    approved_input_manifest_from_json,
    approved_input_manifest_to_json,
    validate_approved_input_manifest,
)
from .paths import (
    approved_input_event_directory_path,
    approved_input_event_filename,
    approved_input_event_path,
    approved_input_events_path,
    approved_input_manifest_filename,
    approved_input_manifest_path,
    approved_input_manifests_path,
    approved_inputs_path,
    project_path,
)
from .repository_scan import scan_approved_input_repository
from .types import (
    ApprovedInputEvent,
    ApprovedInputManifest,
    ApprovedInputRepositoryScanResult,
)


DEFAULT_PROJECTS_ROOT = Path("data/projects")


class ApprovedInputRepository:
    """Persist, load and scan project-local Approved Input manifests."""

    def __init__(
        self,
        root: Path | str = DEFAULT_PROJECTS_ROOT,
    ) -> None:
        self.root = Path(root)
        self._workspace = ProjectWorkspace(root=self.root)

    def next_approved_input_id(
        self,
        project_id: str,
    ) -> str:
        """Return the next safe project-local Approved Input ID."""

        result = self.scan_project(project_id)
        self._raise_for_scan_issues(result)

        return allocate_next_approved_input_id(
            manifest.approved_input_id
            for manifest in result.manifests
        )

    def next_approved_input_event_id(
        self,
        project_id: str,
    ) -> str:
        """Return the next project-wide Approved Input Event ID."""

        result = self.scan_project(project_id)
        self._raise_for_scan_issues(result)
        return allocate_next_approved_input_event_id(
            event.approved_input_event_id
            for event in result.events
        )

    def persist_event(
        self,
        event: ApprovedInputEvent,
    ) -> ApprovedInputEvent:
        """Atomically append one immutable Approved Input Event."""

        validate_approved_input_event(event)
        self._load_project(event.project_id)
        self._prepare_repository(event.project_id)
        self.load_manifest(
            event.project_id,
            event.approved_input_id,
        )

        current = self.scan_project(event.project_id)
        self._raise_for_scan_issues(current)

        if any(
            item.approved_input_event_id
            == event.approved_input_event_id
            for item in current.events
        ):
            raise ApprovedInputPersistenceError(
                "Approved Input Event ID is already occupied: "
                f"{event.approved_input_event_id}."
            )

        # Validate the complete candidate lifecycle before publishing
        # any new immutable event bytes.
        derive_approved_input_authority_states(
            current.manifests,
            current.events + (event,),
        )

        directory = approved_input_event_directory_path(
            self.root,
            event.project_id,
            event.approved_input_id,
        )
        self._ensure_directory(
            directory,
            parent=approved_input_events_path(
                self.root,
                event.project_id,
            ),
            label="Approved Input event directory",
        )

        final_path = approved_input_event_path(
            self.root,
            event.project_id,
            event.approved_input_id,
            event.approved_input_event_id,
        )
        filename = approved_input_event_filename(
            event.approved_input_event_id
        )
        temporary_path = final_path.with_name(
            f".{filename}.tmp"
        )

        if final_path.exists() or final_path.is_symlink():
            raise ApprovedInputPersistenceError(
                "Approved Input Event already exists and is immutable: "
                f"{final_path}."
            )
        if temporary_path.exists() or temporary_path.is_symlink():
            raise ApprovedInputRecoveryRequiredError(
                "Interrupted Approved Input Event persistence requires "
                f"recovery: {temporary_path}."
            )

        self._write_new_text(
            temporary_path,
            approved_input_event_to_json(event),
            label="temporary Approved Input Event",
        )
        persisted_temporary = self._load_event_file(
            temporary_path,
            expected_project_id=event.project_id,
            expected_approved_input_id=event.approved_input_id,
            expected_event_id=event.approved_input_event_id,
        )
        if persisted_temporary != event:
            raise ApprovedInputIntegrityError(
                "Persisted temporary Approved Input Event differs "
                "from the validated event."
            )

        try:
            os.link(temporary_path, final_path)
        except FileExistsError as exc:
            raise ApprovedInputPersistenceError(
                "Approved Input Event publication target exists: "
                f"{final_path}."
            ) from exc
        except OSError as exc:
            raise ApprovedInputPersistenceError(
                "Unable to publish Approved Input Event "
                f"{final_path}: {exc}"
            ) from exc

        try:
            temporary_path.unlink()
        except OSError as exc:
            raise ApprovedInputRecoveryRequiredError(
                "Approved Input Event was published but temporary "
                "state remains; recovery is required: "
                f"{temporary_path}."
            ) from exc

        persisted = self.load_event(
            event.project_id,
            event.approved_input_id,
            event.approved_input_event_id,
        )
        if persisted != event:
            raise ApprovedInputIntegrityError(
                "Published Approved Input Event differs from the "
                "validated event."
            )
        post_publish = self.scan_project(event.project_id)
        if post_publish.issues:
            raise ApprovedInputRecoveryRequiredError(
                "Approved Input Event was published but the repository "
                "no longer satisfies the lifecycle integrity contract; "
                "explicit recovery is required."
            )
        matches = tuple(
            item
            for item in post_publish.events
            if item.approved_input_event_id
            == event.approved_input_event_id
        )
        if matches != (event,):
            raise ApprovedInputRecoveryRequiredError(
                "Published Approved Input Event is not globally unique; "
                "explicit recovery is required."
            )
        return persisted

    def load_event(
        self,
        project_id: str,
        approved_input_id: str,
        approved_input_event_id: str,
    ) -> ApprovedInputEvent:
        """Load and validate one immutable Approved Input Event."""

        self.load_manifest(project_id, approved_input_id)
        validated_event_id = validate_approved_input_event_id(
            approved_input_event_id
        )
        path = approved_input_event_path(
            self.root,
            project_id,
            approved_input_id,
            validated_event_id,
        )
        if path.is_symlink():
            raise UnsafeApprovedInputPathError(
                "Symbolic-link Approved Input Event paths are rejected: "
                f"{path}."
            )
        if not path.exists() or not path.is_file():
            raise ApprovedInputEventNotFoundError(
                "Approved Input Event was not found: "
                f"{project_id}/{approved_input_id}/{validated_event_id}."
            )
        return self._load_event_file(
            path,
            expected_project_id=project_id,
            expected_approved_input_id=approved_input_id,
            expected_event_id=validated_event_id,
        )

    def list_events(
        self,
        project_id: str,
        approved_input_id: str | None = None,
    ) -> tuple[ApprovedInputEvent, ...]:
        """Return lifecycle events in global AIE identifier order."""

        result = self.scan_project(project_id)
        self._raise_for_scan_issues(result)
        if approved_input_id is None:
            return result.events
        validated_id = validate_approved_input_id(approved_input_id)
        self.load_manifest(project_id, validated_id)
        return tuple(
            event
            for event in result.events
            if event.approved_input_id == validated_id
        )

    def persist_manifest(
        self,
        manifest: ApprovedInputManifest,
    ) -> ApprovedInputManifest:
        """Atomically publish one new immutable Approved Input Manifest."""

        validate_approved_input_manifest(manifest)
        self._load_project(manifest.project_id)
        self._prepare_repository(manifest.project_id)

        current = self.scan_project(manifest.project_id)
        self._raise_for_scan_issues(current)

        final_path = approved_input_manifest_path(
            self.root,
            manifest.project_id,
            manifest.approved_input_id,
        )
        filename = approved_input_manifest_filename(
            manifest.approved_input_id
        )
        temporary_path = final_path.with_name(
            f".{filename}.tmp"
        )

        self._assert_lexically_within(
            final_path,
            approved_input_manifests_path(
                self.root,
                manifest.project_id,
            ),
        )

        if final_path.is_symlink():
            raise UnsafeApprovedInputPathError(
                "Symbolic-link Approved Input Manifest paths are "
                f"rejected: {final_path}."
            )

        if final_path.exists():
            raise ApprovedInputPersistenceError(
                "Approved Input Manifest already exists and is "
                f"immutable: {final_path}."
            )

        if temporary_path.is_symlink():
            raise UnsafeApprovedInputPathError(
                "Symbolic-link temporary Approved Input paths are "
                f"rejected: {temporary_path}."
            )

        if temporary_path.exists():
            raise ApprovedInputRecoveryRequiredError(
                "Interrupted Approved Input persistence requires "
                f"recovery before publication: {temporary_path}."
            )

        serialized = approved_input_manifest_to_json(manifest)

        self._write_new_text(
            temporary_path,
            serialized,
            label="temporary Approved Input Manifest",
        )

        persisted_temporary = self._load_manifest_file(
            temporary_path,
            expected_project_id=manifest.project_id,
            expected_approved_input_id=manifest.approved_input_id,
        )

        if persisted_temporary != manifest:
            raise ApprovedInputIntegrityError(
                "Persisted temporary Approved Input Manifest differs "
                "from the validated manifest."
            )

        if final_path.exists() or final_path.is_symlink():
            raise ApprovedInputPersistenceError(
                "Approved Input Manifest publication target became "
                f"occupied: {final_path}."
            )

        try:
            os.link(temporary_path, final_path)
        except FileExistsError as exc:
            raise ApprovedInputPersistenceError(
                "Approved Input Manifest publication target already "
                f"exists: {final_path}."
            ) from exc
        except OSError as exc:
            raise ApprovedInputPersistenceError(
                "Unable to atomically publish Approved Input Manifest "
                f"{final_path}: {exc}"
            ) from exc

        try:
            temporary_path.unlink()
        except OSError as exc:
            raise ApprovedInputRecoveryRequiredError(
                "Approved Input Manifest was published but temporary "
                "state could not be removed; recovery is required: "
                f"{temporary_path}."
            ) from exc

        persisted = self.load_manifest(
            manifest.project_id,
            manifest.approved_input_id,
        )

        if persisted != manifest:
            raise ApprovedInputIntegrityError(
                "Published Approved Input Manifest differs from the "
                "validated manifest."
            )

        return persisted

    def load_manifest(
        self,
        project_id: str,
        approved_input_id: str,
    ) -> ApprovedInputManifest:
        """Load and fully validate one immutable Approved Input Manifest."""

        self._load_project(project_id)
        validated_id = validate_approved_input_id(
            approved_input_id
        )
        path = approved_input_manifest_path(
            self.root,
            project_id,
            validated_id,
        )

        if path.is_symlink():
            raise UnsafeApprovedInputPathError(
                "Symbolic-link Approved Input Manifest paths are "
                f"rejected: {path}."
            )

        if not path.exists() or not path.is_file():
            raise ApprovedInputNotFoundError(
                "Approved Input Manifest was not found: "
                f"{project_id}/{validated_id}."
            )

        return self._load_manifest_file(
            path,
            expected_project_id=project_id,
            expected_approved_input_id=validated_id,
        )

    def list_manifests(
        self,
        project_id: str,
    ) -> tuple[ApprovedInputManifest, ...]:
        """Return all valid immutable manifests in identifier order."""

        result = self.scan_project(project_id)
        self._raise_for_scan_issues(result)
        return result.manifests

    def list_active_approved_inputs(
        self,
        project_id: str,
    ) -> tuple[ApprovedInputManifest, ...]:
        """Return only currently authoritative inputs for Phase H.

        Authority is derived exclusively from immutable manifests and
        lifecycle events. Inactive manifests remain persisted and
        traceable but are never exposed through this stable read contract.
        """

        result = self.scan_project(project_id)
        self._raise_for_scan_issues(result)
        return active_approved_input_manifests(
            result.manifests,
            result.events,
        )

    def scan_project(
        self,
        project_id: str,
    ) -> ApprovedInputRepositoryScanResult:
        """Discover valid manifests and explicit repository issues."""

        self._load_project(project_id)
        return scan_approved_input_repository(
            self.root,
            project_id,
        )

    def _prepare_repository(
        self,
        project_id: str,
    ) -> None:
        project_root = project_path(self.root, project_id)
        repository_root = approved_inputs_path(
            self.root,
            project_id,
        )
        manifests_root = approved_input_manifests_path(
            self.root,
            project_id,
        )
        events_root = approved_input_events_path(
            self.root,
            project_id,
        )

        self._ensure_directory(
            repository_root,
            parent=project_root,
            label="Approved Input repository root",
        )
        self._ensure_directory(
            manifests_root,
            parent=repository_root,
            label="Approved Input manifests directory",
        )
        self._ensure_directory(
            events_root,
            parent=repository_root,
            label="Approved Input events directory",
        )

    def _load_manifest_file(
        self,
        path: Path,
        *,
        expected_project_id: str,
        expected_approved_input_id: str,
    ) -> ApprovedInputManifest:
        if path.is_symlink():
            raise UnsafeApprovedInputPathError(
                "Symbolic-link Approved Input Manifest paths are "
                f"rejected: {path}."
            )

        if not path.exists() or not path.is_file():
            raise ApprovedInputIntegrityError(
                "Required Approved Input Manifest is missing or not "
                f"a regular file: {path}."
            )

        expected_filename = approved_input_manifest_filename(
            expected_approved_input_id
        )
        allowed_names = {
            expected_filename,
            f".{expected_filename}.tmp",
        }

        if path.name not in allowed_names:
            raise ApprovedInputIntegrityError(
                "Approved Input Manifest filename does not match its "
                "identifier."
            )

        manifest = approved_input_manifest_from_json(
            self._read_text(
                path,
                label="Approved Input Manifest",
            )
        )

        if manifest.project_id != expected_project_id:
            raise ApprovedInputIntegrityError(
                "Approved Input Manifest project_id does not match "
                "its Project directory."
            )

        if manifest.approved_input_id != expected_approved_input_id:
            raise ApprovedInputIntegrityError(
                "Approved Input Manifest ID does not match its filename."
            )

        return manifest

    def _load_event_file(
        self,
        path: Path,
        *,
        expected_project_id: str,
        expected_approved_input_id: str,
        expected_event_id: str,
    ) -> ApprovedInputEvent:
        if path.is_symlink():
            raise UnsafeApprovedInputPathError(
                "Symbolic-link Approved Input Event paths are rejected: "
                f"{path}."
            )
        if not path.exists() or not path.is_file():
            raise ApprovedInputIntegrityError(
                "Required Approved Input Event is missing or not a "
                f"regular file: {path}."
            )
        expected_filename = approved_input_event_filename(
            expected_event_id
        )
        if path.name not in {
            expected_filename,
            f".{expected_filename}.tmp",
        }:
            raise ApprovedInputIntegrityError(
                "Approved Input Event filename does not match its ID."
            )
        event = approved_input_event_from_json(
            self._read_text(
                path,
                label="Approved Input Event",
            )
        )
        if event.project_id != expected_project_id:
            raise ApprovedInputIntegrityError(
                "Approved Input Event project_id does not match path."
            )
        if event.approved_input_id != expected_approved_input_id:
            raise ApprovedInputIntegrityError(
                "Approved Input Event does not belong to its AIN directory."
            )
        if event.approved_input_event_id != expected_event_id:
            raise ApprovedInputIntegrityError(
                "Approved Input Event ID does not match its filename."
            )
        return event

    def _load_project(self, project_id: str) -> None:
        try:
            self._workspace.load_project(project_id)
        except ProjectWorkspaceError as exc:
            raise ApprovedInputReferenceError(
                "Approved Input repository references an unavailable "
                f"Project: {project_id!r}."
            ) from exc

    def _ensure_directory(
        self,
        path: Path,
        *,
        parent: Path,
        label: str,
    ) -> None:
        self._assert_lexically_within(path, parent)

        if path.is_symlink():
            raise UnsafeApprovedInputPathError(
                f"Symbolic-link {label} is rejected: {path}."
            )

        if path.exists():
            if not path.is_dir():
                raise UnsafeApprovedInputPathError(
                    f"{label} is not a directory: {path}."
                )
            return

        if parent.is_symlink() or not parent.is_dir():
            raise UnsafeApprovedInputPathError(
                f"Parent directory is unsafe for {label}: {parent}."
            )

        try:
            path.mkdir()
        except OSError as exc:
            raise ApprovedInputPersistenceError(
                f"Unable to create {label} {path}: {exc}"
            ) from exc

    @staticmethod
    def _raise_for_scan_issues(
        result: ApprovedInputRepositoryScanResult,
    ) -> None:
        if not result.issues:
            return

        if any(
            issue.code in {
                "approved_input_persistence_interrupted",
                "approved_input_event_persistence_interrupted",
            }
            for issue in result.issues
        ):
            raise ApprovedInputRecoveryRequiredError(
                "Approved Input repository contains interrupted "
                "persistence state and requires recovery."
            )

        raise ApprovedInputIntegrityError(
            "Approved Input repository contains blocking integrity "
            "issues."
        )

    @staticmethod
    def _assert_lexically_within(
        path: Path,
        parent: Path,
    ) -> None:
        try:
            path.relative_to(parent)
        except ValueError as exc:
            raise UnsafeApprovedInputPathError(
                "Approved Input path escapes its authority root: "
                f"{path}."
            ) from exc

    @staticmethod
    def _write_new_text(
        path: Path,
        text: str,
        *,
        label: str,
    ) -> None:
        try:
            with path.open(
                "x",
                encoding="utf-8",
                newline="\n",
            ) as stream:
                stream.write(text)
                stream.flush()
                os.fsync(stream.fileno())
        except FileExistsError as exc:
            raise ApprovedInputPersistenceError(
                f"{label} path already exists: {path}."
            ) from exc
        except OSError as exc:
            raise ApprovedInputPersistenceError(
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
        except UnicodeDecodeError as exc:
            raise ApprovedInputIntegrityError(
                f"{label} is not valid UTF-8."
            ) from exc
        except OSError as exc:
            raise ApprovedInputPersistenceError(
                f"Unable to read {label} {path}: {exc}"
            ) from exc
