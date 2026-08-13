"""Atomic project-isolated persistence for Internal Engineering Model snapshots."""

from __future__ import annotations

from pathlib import Path
import re

from modules.project_workspace import ProjectWorkspace
from modules.project_workspace.workspace import DEFAULT_PROJECTS_ROOT

from .element_manifest import (
    internal_model_element_from_json,
    internal_model_element_to_json,
)
from .errors import (
    InternalModelIntegrityError,
    InternalModelPersistenceError,
)
from .identifiers import (
    next_internal_engineering_model_id as allocate_next_iem_id,
    next_internal_model_element_id as allocate_next_ime_id,
    next_internal_model_relationship_id as allocate_next_imr_id,
    validate_internal_engineering_model_id,
)
from .model_manifest import (
    internal_engineering_model_manifest_from_json,
    internal_engineering_model_manifest_to_json,
)
from .paths import (
    INTERNAL_MODEL_ELEMENTS_DIRECTORY_NAME,
    INTERNAL_MODEL_MANIFEST_FILENAME,
    INTERNAL_MODEL_RELATIONSHIPS_DIRECTORY_NAME,
    INTERNAL_MODEL_STRUCTURE_FILENAME,
    internal_engineering_model_path,
    internal_model_element_filename,
    internal_model_relationship_filename,
    internal_models_path,
)
from .relationship_manifest import (
    internal_model_relationship_from_json,
    internal_model_relationship_to_json,
)
from .repository_errors import (
    InternalEngineeringModelNotFoundError,
    InternalModelRecoveryRequiredError,
    UnsafeInternalModelPathError,
)
from .repository_integrity import (
    validate_internal_engineering_model_snapshot,
)
from .repository_scan import scan_internal_model_repository
from .repository_types import InternalModelRepositoryScanResult
from .structure_manifest import (
    internal_model_structure_from_json,
    internal_model_structure_to_json,
)
from .types import (
    InternalEngineeringModelSnapshot,
    InternalModelElement,
    InternalModelRelationship,
)


_ELEMENT_FILE_PATTERN = re.compile(r"^(IME-[0-9]{6})\.json$")
_RELATIONSHIP_FILE_PATTERN = re.compile(r"^(IMR-[0-9]{6})\.json$")
_REQUIRED_IEM_ENTRIES = frozenset(
    {
        INTERNAL_MODEL_MANIFEST_FILENAME,
        INTERNAL_MODEL_STRUCTURE_FILENAME,
        INTERNAL_MODEL_ELEMENTS_DIRECTORY_NAME,
        INTERNAL_MODEL_RELATIONSHIPS_DIRECTORY_NAME,
    }
)


class InternalModelRepository:
    """Persist and reopen complete immutable IEM snapshot bundles."""

    def __init__(
        self,
        root: Path | str = DEFAULT_PROJECTS_ROOT,
    ) -> None:
        self.root = Path(root)
        self._workspace = ProjectWorkspace(root=self.root)

    def next_internal_engineering_model_id(
        self,
        project_id: str,
    ) -> str:
        result = self.scan_project(project_id)
        self._raise_for_scan_issues(result)
        return allocate_next_iem_id(
            item.manifest.internal_engineering_model_id
            for item in result.snapshots
        )

    def next_internal_model_element_id(
        self,
        project_id: str,
    ) -> str:
        result = self.scan_project(project_id)
        self._raise_for_scan_issues(result)
        return allocate_next_ime_id(
            element.internal_model_element_id
            for snapshot in result.snapshots
            for element in snapshot.elements
        )

    def next_internal_model_relationship_id(
        self,
        project_id: str,
    ) -> str:
        result = self.scan_project(project_id)
        self._raise_for_scan_issues(result)
        return allocate_next_imr_id(
            relationship.internal_model_relationship_id
            for snapshot in result.snapshots
            for relationship in snapshot.relationships
        )

    def occupied_internal_model_element_ids(
        self,
        project_id: str,
    ) -> tuple[str, ...]:
        result = self.scan_project(project_id)
        self._raise_for_scan_issues(result)
        return tuple(
            element.internal_model_element_id
            for snapshot in result.snapshots
            for element in snapshot.elements
        )

    def occupied_internal_model_relationship_ids(
        self,
        project_id: str,
    ) -> tuple[str, ...]:
        result = self.scan_project(project_id)
        self._raise_for_scan_issues(result)
        return tuple(
            relationship.internal_model_relationship_id
            for snapshot in result.snapshots
            for relationship in snapshot.relationships
        )

    def find_by_assembly_identity(
        self,
        project_id: str,
        *,
        assembly_input_fingerprint: str,
        assembly_rules_reference,
    ) -> InternalEngineeringModelSnapshot | None:
        """Return an exact prior assembly, never an implicit latest snapshot."""

        result = self.scan_project(project_id)
        self._raise_for_scan_issues(result)
        matches = tuple(
            snapshot
            for snapshot in result.snapshots
            if (
                snapshot.manifest.assembly_input_fingerprint
                == assembly_input_fingerprint
                and snapshot.manifest.assembly_context.assembly_rules_reference
                == assembly_rules_reference
            )
        )
        if len(matches) > 1:
            raise InternalModelRecoveryRequiredError(
                "Multiple IEM snapshots share one exact assembly identity."
            )
        return matches[0] if matches else None

    def persist_snapshot(
        self,
        snapshot: InternalEngineeringModelSnapshot,
    ) -> InternalEngineeringModelSnapshot:
        """Atomically publish one complete immutable IEM snapshot."""

        validate_internal_engineering_model_snapshot(snapshot)
        manifest = snapshot.manifest
        self._workspace.load_project(manifest.project_id)

        current = self.scan_project(manifest.project_id)
        self._raise_for_scan_issues(current)

        same_identity = tuple(
            item
            for item in current.snapshots
            if (
                item.manifest.assembly_input_fingerprint
                == manifest.assembly_input_fingerprint
                and item.manifest.assembly_context.assembly_rules_reference
                == manifest.assembly_context.assembly_rules_reference
            )
        )
        if len(same_identity) > 1:
            raise InternalModelRecoveryRequiredError(
                "Repository contains duplicate exact assembly identities."
            )
        if same_identity:
            return same_identity[0]

        self._reject_project_wide_id_reuse(snapshot, current)
        self._prepare_repository(manifest.project_id)

        repository_root = internal_models_path(
            self.root,
            manifest.project_id,
        )
        final_path = internal_engineering_model_path(
            self.root,
            manifest.project_id,
            manifest.internal_engineering_model_id,
        )
        temporary_path = repository_root / (
            f".create-{manifest.internal_engineering_model_id}.tmp"
        )

        if final_path.exists() or final_path.is_symlink():
            raise InternalModelPersistenceError(
                "Internal Engineering Model already exists and is immutable: "
                f"{final_path}."
            )
        if temporary_path.exists() or temporary_path.is_symlink():
            raise InternalModelRecoveryRequiredError(
                "Interrupted IEM persistence requires recovery: "
                f"{temporary_path}."
            )

        try:
            temporary_path.mkdir()
            elements_path = (
                temporary_path / INTERNAL_MODEL_ELEMENTS_DIRECTORY_NAME
            )
            relationships_path = (
                temporary_path
                / INTERNAL_MODEL_RELATIONSHIPS_DIRECTORY_NAME
            )
            elements_path.mkdir()
            relationships_path.mkdir()
        except OSError as exc:
            raise InternalModelPersistenceError(
                "Unable to create temporary IEM directory "
                f"{temporary_path}: {exc}"
            ) from exc

        try:
            self._write_new_text(
                temporary_path / INTERNAL_MODEL_MANIFEST_FILENAME,
                internal_engineering_model_manifest_to_json(
                    snapshot.manifest
                ),
                label="Internal Engineering Model manifest",
            )
            self._write_new_text(
                temporary_path / INTERNAL_MODEL_STRUCTURE_FILENAME,
                internal_model_structure_to_json(snapshot.structure),
                label="Internal Model structure",
            )
            for element in snapshot.elements:
                self._write_new_text(
                    elements_path
                    / internal_model_element_filename(
                        element.internal_model_element_id
                    ),
                    internal_model_element_to_json(element),
                    label="Internal Model Element",
                )
            for relationship in snapshot.relationships:
                self._write_new_text(
                    relationships_path
                    / internal_model_relationship_filename(
                        relationship.internal_model_relationship_id
                    ),
                    internal_model_relationship_to_json(relationship),
                    label="Internal Model Relationship",
                )

            temporary_snapshot = self._load_snapshot_from_directory(
                manifest.project_id,
                manifest.internal_engineering_model_id,
                temporary_path,
            )
            if temporary_snapshot != snapshot:
                raise InternalModelIntegrityError(
                    "Persisted temporary IEM differs from validated snapshot."
                )

            if final_path.exists() or final_path.is_symlink():
                raise InternalModelPersistenceError(
                    "IEM path appeared during publication: "
                    f"{final_path}."
                )

            temporary_path.rename(final_path)
        except (
            InternalModelIntegrityError,
            InternalModelPersistenceError,
        ):
            raise
        except OSError as exc:
            raise InternalModelPersistenceError(
                f"Unable to finalize IEM {final_path}: {exc}"
            ) from exc

        persisted = self.load_snapshot(
            manifest.project_id,
            manifest.internal_engineering_model_id,
        )
        if persisted != snapshot:
            raise InternalModelRecoveryRequiredError(
                "Published IEM differs from validated content; "
                "explicit recovery is required."
            )

        post_publish = self.scan_project(manifest.project_id)
        if post_publish.issues:
            raise InternalModelRecoveryRequiredError(
                "IEM was published but repository integrity is no longer "
                "clean; explicit recovery is required."
            )
        return persisted

    def load_snapshot(
        self,
        project_id: str,
        internal_engineering_model_id: str,
    ) -> InternalEngineeringModelSnapshot:
        self._workspace.load_project(project_id)
        validated_id = validate_internal_engineering_model_id(
            internal_engineering_model_id
        )
        directory = internal_engineering_model_path(
            self.root,
            project_id,
            validated_id,
        )
        if directory.is_symlink():
            raise UnsafeInternalModelPathError(
                "Symbolic-link IEM directories are rejected: "
                f"{directory}."
            )
        if not directory.exists() or not directory.is_dir():
            raise InternalEngineeringModelNotFoundError(
                "Internal Engineering Model was not found: "
                f"{project_id}/{validated_id}."
            )
        return self._load_snapshot_from_directory(
            project_id,
            validated_id,
            directory,
        )

    def list_snapshots(
        self,
        project_id: str,
    ) -> tuple[InternalEngineeringModelSnapshot, ...]:
        result = self.scan_project(project_id)
        self._raise_for_scan_issues(result)
        return result.snapshots

    def scan_project(
        self,
        project_id: str,
    ) -> InternalModelRepositoryScanResult:
        self._workspace.load_project(project_id)
        return scan_internal_model_repository(self, project_id)

    def _load_snapshot_from_directory(
        self,
        project_id: str,
        internal_engineering_model_id: str,
        directory: Path,
    ) -> InternalEngineeringModelSnapshot:
        self._reject_symlink(directory, label="IEM directory")
        if not directory.is_dir():
            raise InternalModelIntegrityError(
                "IEM path is not a regular directory."
            )

        try:
            entries = tuple(
                sorted(directory.iterdir(), key=lambda item: item.name)
            )
        except OSError as exc:
            raise InternalModelPersistenceError(
                f"Unable to inspect IEM directory {directory}: {exc}"
            ) from exc

        for entry in entries:
            self._reject_symlink(entry, label="IEM entry")
        actual_names = frozenset(entry.name for entry in entries)
        if actual_names != _REQUIRED_IEM_ENTRIES:
            raise InternalModelIntegrityError(
                "IEM directory has invalid entries; "
                f"missing={sorted(_REQUIRED_IEM_ENTRIES - actual_names)}, "
                f"unknown={sorted(actual_names - _REQUIRED_IEM_ENTRIES)}."
            )

        manifest_path = directory / INTERNAL_MODEL_MANIFEST_FILENAME
        structure_path = directory / INTERNAL_MODEL_STRUCTURE_FILENAME
        elements_path = (
            directory / INTERNAL_MODEL_ELEMENTS_DIRECTORY_NAME
        )
        relationships_path = (
            directory / INTERNAL_MODEL_RELATIONSHIPS_DIRECTORY_NAME
        )

        self._require_regular_file(
            manifest_path,
            label="IEM manifest",
        )
        self._require_regular_file(
            structure_path,
            label="Internal Model structure",
        )
        self._require_regular_directory(
            elements_path,
            label="IME directory",
        )
        self._require_regular_directory(
            relationships_path,
            label="IMR directory",
        )

        manifest = internal_engineering_model_manifest_from_json(
            self._read_text(
                manifest_path,
                label="IEM manifest",
            )
        )
        if (
            manifest.project_id != project_id
            or manifest.internal_engineering_model_id
            != internal_engineering_model_id
        ):
            raise InternalModelIntegrityError(
                "IEM manifest path identity does not match its contents."
            )

        structure = internal_model_structure_from_json(
            self._read_text(
                structure_path,
                label="Internal Model structure",
            )
        )
        elements = self._load_elements(
            project_id,
            internal_engineering_model_id,
            elements_path,
        )
        relationships = self._load_relationships(
            project_id,
            internal_engineering_model_id,
            relationships_path,
        )

        snapshot = InternalEngineeringModelSnapshot(
            manifest=manifest,
            structure=structure,
            elements=elements,
            relationships=relationships,
        )
        return validate_internal_engineering_model_snapshot(snapshot)

    def _load_elements(
        self,
        project_id: str,
        internal_engineering_model_id: str,
        directory: Path,
    ) -> tuple[InternalModelElement, ...]:
        entries = self._regular_json_entries(
            directory,
            pattern=_ELEMENT_FILE_PATTERN,
            label="IME directory",
        )
        result = []
        for entry, match in entries:
            internal_id = match.group(1)
            element = internal_model_element_from_json(
                self._read_text(entry, label="Internal Model Element")
            )
            if (
                element.project_id != project_id
                or element.internal_engineering_model_id
                != internal_engineering_model_id
                or element.internal_model_element_id != internal_id
            ):
                raise InternalModelIntegrityError(
                    "IME path identity does not match its contents."
                )
            result.append(element)
        return tuple(result)

    def _load_relationships(
        self,
        project_id: str,
        internal_engineering_model_id: str,
        directory: Path,
    ) -> tuple[InternalModelRelationship, ...]:
        entries = self._regular_json_entries(
            directory,
            pattern=_RELATIONSHIP_FILE_PATTERN,
            label="IMR directory",
        )
        result = []
        for entry, match in entries:
            internal_id = match.group(1)
            relationship = internal_model_relationship_from_json(
                self._read_text(
                    entry,
                    label="Internal Model Relationship",
                )
            )
            if (
                relationship.project_id != project_id
                or relationship.internal_engineering_model_id
                != internal_engineering_model_id
                or relationship.internal_model_relationship_id
                != internal_id
            ):
                raise InternalModelIntegrityError(
                    "IMR path identity does not match its contents."
                )
            result.append(relationship)
        return tuple(result)

    def _regular_json_entries(
        self,
        directory: Path,
        *,
        pattern,
        label: str,
    ):
        try:
            entries = tuple(
                sorted(directory.iterdir(), key=lambda item: item.name)
            )
        except OSError as exc:
            raise InternalModelPersistenceError(
                f"Unable to inspect {label}: {exc}"
            ) from exc

        result = []
        for entry in entries:
            self._reject_symlink(entry, label=f"{label} entry")
            match = pattern.fullmatch(entry.name)
            if match is None or not entry.is_file():
                raise InternalModelIntegrityError(
                    f"{label} contains unexpected entry: {entry}."
                )
            result.append((entry, match))
        return tuple(result)

    def _reject_project_wide_id_reuse(
        self,
        snapshot: InternalEngineeringModelSnapshot,
        current: InternalModelRepositoryScanResult,
    ) -> None:
        existing_iem_ids = {
            item.manifest.internal_engineering_model_id
            for item in current.snapshots
        }
        if snapshot.manifest.internal_engineering_model_id in existing_iem_ids:
            raise InternalModelPersistenceError(
                "IEM ID reuse is not allowed."
            )

        existing_element_ids = {
            element.internal_model_element_id
            for item in current.snapshots
            for element in item.elements
        }
        incoming_element_ids = {
            element.internal_model_element_id
            for element in snapshot.elements
        }
        reused_elements = sorted(
            existing_element_ids & incoming_element_ids
        )
        if reused_elements:
            raise InternalModelPersistenceError(
                "Project-local IME ID reuse is not allowed: "
                f"{reused_elements}."
            )

        existing_relationship_ids = {
            relationship.internal_model_relationship_id
            for item in current.snapshots
            for relationship in item.relationships
        }
        incoming_relationship_ids = {
            relationship.internal_model_relationship_id
            for relationship in snapshot.relationships
        }
        reused_relationships = sorted(
            existing_relationship_ids & incoming_relationship_ids
        )
        if reused_relationships:
            raise InternalModelPersistenceError(
                "Project-local IMR ID reuse is not allowed: "
                f"{reused_relationships}."
            )

    def _prepare_repository(self, project_id: str) -> None:
        repository_root = internal_models_path(self.root, project_id)
        if repository_root.is_symlink():
            raise UnsafeInternalModelPathError(
                "Symbolic-link Internal Model repository root is rejected."
            )
        if repository_root.exists():
            if not repository_root.is_dir():
                raise UnsafeInternalModelPathError(
                    "Internal Model repository root must be a directory."
                )
            return
        try:
            repository_root.mkdir()
        except OSError as exc:
            raise InternalModelPersistenceError(
                "Unable to create Internal Model repository root: "
                f"{repository_root}: {exc}"
            ) from exc

    def _write_new_text(
        self,
        path: Path,
        content: str,
        *,
        label: str,
    ) -> None:
        if path.exists() or path.is_symlink():
            raise InternalModelPersistenceError(
                f"{label} already exists: {path}."
            )
        try:
            with path.open("x", encoding="utf-8", newline="\n") as handle:
                handle.write(content)
        except OSError as exc:
            raise InternalModelPersistenceError(
                f"Unable to write {label} {path}: {exc}"
            ) from exc

    def _read_text(
        self,
        path: Path,
        *,
        label: str,
    ) -> str:
        self._require_regular_file(path, label=label)
        try:
            return path.read_text(encoding="utf-8")
        except OSError as exc:
            raise InternalModelPersistenceError(
                f"Unable to read {label} {path}: {exc}"
            ) from exc

    def _require_regular_file(
        self,
        path: Path,
        *,
        label: str,
    ) -> None:
        self._reject_symlink(path, label=label)
        if not path.exists() or not path.is_file():
            raise InternalModelIntegrityError(
                f"{label} must be a regular file: {path}."
            )

    def _require_regular_directory(
        self,
        path: Path,
        *,
        label: str,
    ) -> None:
        self._reject_symlink(path, label=label)
        if not path.exists() or not path.is_dir():
            raise InternalModelIntegrityError(
                f"{label} must be a regular directory: {path}."
            )

    def _reject_symlink(
        self,
        path: Path,
        *,
        label: str,
    ) -> None:
        if path.is_symlink():
            raise UnsafeInternalModelPathError(
                f"Symbolic-link {label} is rejected: {path}."
            )

    def _raise_for_scan_issues(
        self,
        result: InternalModelRepositoryScanResult,
    ) -> None:
        if result.issues:
            first = result.issues[0]
            raise InternalModelRecoveryRequiredError(
                "Internal Model repository has blocking integrity issues: "
                f"{first.code}: {first.message}"
            )
