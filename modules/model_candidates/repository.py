"""Atomic project-isolated persistence for Phase-H Candidate Sets."""

from __future__ import annotations

from collections.abc import Iterable
import os
from pathlib import Path
import re

from modules.project_workspace import ProjectWorkspace
from modules.project_workspace.workspace import DEFAULT_PROJECTS_ROOT

from .candidate_set_manifest import (
    model_candidate_set_manifest_from_json,
    model_candidate_set_manifest_to_json,
    validate_model_candidate_set_manifest,
)
from .element_manifest import (
    model_element_candidate_from_json,
    model_element_candidate_to_json,
    validate_model_element_candidate,
)
from .errors import (
    ModelCandidateIntegrityError,
    ModelCandidateNotFoundError,
    ModelCandidatePersistenceError,
    ModelCandidateRecoveryRequiredError,
    ModelCandidateReferenceError,
    ModelElementCandidateNotFoundError,
    ModelRelationshipCandidateNotFoundError,
    UnsafeModelCandidatePathError,
)
from .identifiers import (
    next_model_candidate_set_id as allocate_next_candidate_set_id,
    next_model_element_candidate_id as allocate_next_element_candidate_id,
    next_model_relationship_candidate_id as allocate_next_relationship_candidate_id,
    validate_model_candidate_set_id,
    validate_model_element_candidate_id,
    validate_model_relationship_candidate_id,
)
from .paths import (
    MODEL_CANDIDATE_ELEMENTS_DIRECTORY_NAME,
    MODEL_CANDIDATE_RELATIONSHIPS_DIRECTORY_NAME,
    MODEL_CANDIDATE_SET_MANIFEST_FILENAME,
    model_candidate_elements_path,
    model_candidate_relationships_path,
    model_candidate_set_manifest_path,
    model_candidate_set_path,
    model_candidate_sets_path,
    model_candidates_path,
    model_element_candidate_filename,
    model_relationship_candidate_filename,
    project_path,
)
from .relationship_manifest import (
    model_relationship_candidate_from_json,
    model_relationship_candidate_to_json,
    validate_model_relationship_candidate,
)
from .repository_scan import scan_model_candidate_repository
from .types import (
    ModelCandidateRepositoryScanResult,
    ModelCandidateSetManifest,
    ModelCandidateSetSnapshot,
    ModelElementCandidate,
    ModelRelationshipCandidate,
)


_ELEMENT_FILE_PATTERN = re.compile(r"^(MCE-[0-9]{6})\.json$")
_RELATIONSHIP_FILE_PATTERN = re.compile(r"^(MCR-[0-9]{6})\.json$")
_REQUIRED_SET_ENTRIES = frozenset(
    {
        MODEL_CANDIDATE_SET_MANIFEST_FILENAME,
        MODEL_CANDIDATE_ELEMENTS_DIRECTORY_NAME,
        MODEL_CANDIDATE_RELATIONSHIPS_DIRECTORY_NAME,
    }
)


class ModelCandidateRepository:
    """Persist and reopen complete immutable Candidate Set bundles."""

    def __init__(
        self,
        root: Path | str = DEFAULT_PROJECTS_ROOT,
    ) -> None:
        self.root = Path(root)
        self._workspace = ProjectWorkspace(root=self.root)

    def next_candidate_set_id(self, project_id: str) -> str:
        """Return next project-local MCS ID without reusing gaps."""

        result = self.scan_project(project_id)
        self._raise_for_scan_issues(result)
        return allocate_next_candidate_set_id(
            snapshot.manifest.candidate_set_id
            for snapshot in result.candidate_sets
        )

    def next_element_candidate_id(self, project_id: str) -> str:
        """Return next project-local MCE ID without reusing gaps."""

        result = self.scan_project(project_id)
        self._raise_for_scan_issues(result)
        return allocate_next_element_candidate_id(
            candidate.model_element_candidate_id
            for snapshot in result.candidate_sets
            for candidate in snapshot.element_candidates
        )

    def next_relationship_candidate_id(
        self,
        project_id: str,
    ) -> str:
        """Return next project-local MCR ID without reusing gaps."""

        result = self.scan_project(project_id)
        self._raise_for_scan_issues(result)
        return allocate_next_relationship_candidate_id(
            candidate.model_relationship_candidate_id
            for snapshot in result.candidate_sets
            for candidate in snapshot.relationship_candidates
        )

    def persist_candidate_set(
        self,
        manifest: ModelCandidateSetManifest,
        *,
        element_candidates: Iterable[ModelElementCandidate],
        relationship_candidates: Iterable[
            ModelRelationshipCandidate
        ],
    ) -> ModelCandidateSetSnapshot:
        """Atomically publish one complete immutable Candidate Set."""

        validate_model_candidate_set_manifest(manifest)
        elements = self._sorted_instances(
            element_candidates,
            ModelElementCandidate,
            key=lambda item: item.model_element_candidate_id,
            label="element_candidates",
        )
        relationships = self._sorted_instances(
            relationship_candidates,
            ModelRelationshipCandidate,
            key=lambda item: item.model_relationship_candidate_id,
            label="relationship_candidates",
        )
        for item in elements:
            validate_model_element_candidate(item)
        for item in relationships:
            validate_model_relationship_candidate(item)

        self._workspace.load_project(manifest.project_id)
        snapshot = ModelCandidateSetSnapshot(
            manifest=manifest,
            element_candidates=elements,
            relationship_candidates=relationships,
        )
        self._validate_snapshot(snapshot)

        current = self.scan_project(manifest.project_id)
        self._raise_for_scan_issues(current)
        self._reject_project_wide_id_reuse(snapshot, current)

        self._prepare_repository(manifest.project_id)
        sets_root = model_candidate_sets_path(
            self.root,
            manifest.project_id,
        )
        final_path = model_candidate_set_path(
            self.root,
            manifest.project_id,
            manifest.candidate_set_id,
        )
        temporary_path = sets_root / (
            f".create-{manifest.candidate_set_id}.tmp"
        )

        if final_path.exists() or final_path.is_symlink():
            raise ModelCandidatePersistenceError(
                "Candidate Set already exists and is immutable: "
                f"{final_path}."
            )
        if temporary_path.exists() or temporary_path.is_symlink():
            raise ModelCandidateRecoveryRequiredError(
                "Interrupted Candidate Set persistence requires "
                f"recovery: {temporary_path}."
            )

        try:
            temporary_path.mkdir()
            elements_path = (
                temporary_path
                / MODEL_CANDIDATE_ELEMENTS_DIRECTORY_NAME
            )
            relationships_path = (
                temporary_path
                / MODEL_CANDIDATE_RELATIONSHIPS_DIRECTORY_NAME
            )
            elements_path.mkdir()
            relationships_path.mkdir()
        except OSError as exc:
            raise ModelCandidatePersistenceError(
                "Unable to create temporary Candidate Set directory "
                f"{temporary_path}: {exc}"
            ) from exc

        try:
            self._write_new_text(
                temporary_path
                / MODEL_CANDIDATE_SET_MANIFEST_FILENAME,
                model_candidate_set_manifest_to_json(manifest),
                label="Candidate Set manifest",
            )
            for candidate in elements:
                self._write_new_text(
                    elements_path
                    / model_element_candidate_filename(
                        candidate.model_element_candidate_id
                    ),
                    model_element_candidate_to_json(candidate),
                    label="Model Element Candidate",
                )
            for candidate in relationships:
                self._write_new_text(
                    relationships_path
                    / model_relationship_candidate_filename(
                        candidate.model_relationship_candidate_id
                    ),
                    model_relationship_candidate_to_json(candidate),
                    label="Model Relationship Candidate",
                )

            persisted_temporary = (
                self._load_snapshot_from_directory(
                    manifest.project_id,
                    manifest.candidate_set_id,
                    temporary_path,
                )
            )
            if persisted_temporary != snapshot:
                raise ModelCandidateIntegrityError(
                    "Persisted temporary Candidate Set differs from "
                    "the validated snapshot."
                )

            if final_path.exists() or final_path.is_symlink():
                raise ModelCandidatePersistenceError(
                    "Candidate Set path appeared during publication: "
                    f"{final_path}."
                )

            temporary_path.rename(final_path)
        except (
            ModelCandidateIntegrityError,
            ModelCandidatePersistenceError,
        ):
            raise
        except OSError as exc:
            raise ModelCandidatePersistenceError(
                "Unable to finalize Candidate Set "
                f"{final_path}: {exc}"
            ) from exc

        persisted = self.load_candidate_set(
            manifest.project_id,
            manifest.candidate_set_id,
        )
        if persisted != snapshot:
            raise ModelCandidateRecoveryRequiredError(
                "Published Candidate Set differs from validated "
                "content; explicit recovery is required."
            )

        post_publish = self.scan_project(manifest.project_id)
        if post_publish.issues:
            raise ModelCandidateRecoveryRequiredError(
                "Candidate Set was published but repository integrity "
                "is no longer clean; explicit recovery is required."
            )
        return persisted

    def load_candidate_set(
        self,
        project_id: str,
        candidate_set_id: str,
    ) -> ModelCandidateSetSnapshot:
        """Load one complete Candidate Set and validate all references."""

        self._workspace.load_project(project_id)
        validated_id = validate_model_candidate_set_id(
            candidate_set_id
        )
        directory = model_candidate_set_path(
            self.root,
            project_id,
            validated_id,
        )
        if directory.is_symlink():
            raise UnsafeModelCandidatePathError(
                "Symbolic-link Candidate Set directories are rejected: "
                f"{directory}."
            )
        if not directory.exists() or not directory.is_dir():
            raise ModelCandidateNotFoundError(
                "Candidate Set was not found: "
                f"{project_id}/{validated_id}."
            )
        return self._load_snapshot_from_directory(
            project_id,
            validated_id,
            directory,
        )

    def load_element_candidate(
        self,
        project_id: str,
        candidate_set_id: str,
        model_element_candidate_id: str,
    ) -> ModelElementCandidate:
        """Load one Element Candidate from an explicit Candidate Set."""

        validated_id = validate_model_element_candidate_id(
            model_element_candidate_id
        )
        snapshot = self.load_candidate_set(
            project_id,
            candidate_set_id,
        )
        for candidate in snapshot.element_candidates:
            if candidate.model_element_candidate_id == validated_id:
                return candidate
        raise ModelElementCandidateNotFoundError(
            "Model Element Candidate was not found in Candidate Set: "
            f"{candidate_set_id}/{validated_id}."
        )

    def load_relationship_candidate(
        self,
        project_id: str,
        candidate_set_id: str,
        model_relationship_candidate_id: str,
    ) -> ModelRelationshipCandidate:
        """Load one Relationship Candidate from an explicit Candidate Set."""

        validated_id = validate_model_relationship_candidate_id(
            model_relationship_candidate_id
        )
        snapshot = self.load_candidate_set(
            project_id,
            candidate_set_id,
        )
        for candidate in snapshot.relationship_candidates:
            if (
                candidate.model_relationship_candidate_id
                == validated_id
            ):
                return candidate
        raise ModelRelationshipCandidateNotFoundError(
            "Model Relationship Candidate was not found in "
            f"Candidate Set: {candidate_set_id}/{validated_id}."
        )

    def list_candidate_sets(
        self,
        project_id: str,
    ) -> tuple[ModelCandidateSetSnapshot, ...]:
        """Return all complete Candidate Sets in MCS identifier order."""

        result = self.scan_project(project_id)
        self._raise_for_scan_issues(result)
        return result.candidate_sets

    def scan_project(
        self,
        project_id: str,
    ) -> ModelCandidateRepositoryScanResult:
        """Return valid Candidate Sets plus deterministic diagnostics."""

        self._workspace.load_project(project_id)
        return scan_model_candidate_repository(self, project_id)

    def _load_snapshot_from_directory(
        self,
        project_id: str,
        candidate_set_id: str,
        directory: Path,
    ) -> ModelCandidateSetSnapshot:
        self._reject_symlink(
            directory,
            label="Candidate Set directory",
        )
        if not directory.is_dir():
            raise ModelCandidateIntegrityError(
                "Candidate Set path is not a regular directory."
            )

        try:
            entries = tuple(
                sorted(directory.iterdir(), key=lambda item: item.name)
            )
        except OSError as exc:
            raise ModelCandidatePersistenceError(
                f"Unable to inspect Candidate Set {directory}: {exc}"
            ) from exc

        for entry in entries:
            if entry.is_symlink():
                raise UnsafeModelCandidatePathError(
                    "Symbolic-link Candidate Set entries are rejected: "
                    f"{entry}."
                )
        actual_names = frozenset(entry.name for entry in entries)
        if actual_names != _REQUIRED_SET_ENTRIES:
            raise ModelCandidateIntegrityError(
                "Candidate Set directory has invalid entries; "
                f"missing={sorted(_REQUIRED_SET_ENTRIES - actual_names)}, "
                f"unknown={sorted(actual_names - _REQUIRED_SET_ENTRIES)}."
            )

        manifest_path = (
            directory / MODEL_CANDIDATE_SET_MANIFEST_FILENAME
        )
        elements_path = (
            directory / MODEL_CANDIDATE_ELEMENTS_DIRECTORY_NAME
        )
        relationships_path = (
            directory
            / MODEL_CANDIDATE_RELATIONSHIPS_DIRECTORY_NAME
        )
        self._require_regular_file(
            manifest_path,
            label="Candidate Set manifest",
        )
        self._require_regular_directory(
            elements_path,
            label="Element Candidate directory",
        )
        self._require_regular_directory(
            relationships_path,
            label="Relationship Candidate directory",
        )

        manifest = model_candidate_set_manifest_from_json(
            self._read_text(
                manifest_path,
                label="Candidate Set manifest",
            ),
            expected_project_id=project_id,
            expected_candidate_set_id=candidate_set_id,
        )
        elements = self._load_elements(
            project_id,
            candidate_set_id,
            elements_path,
        )
        relationships = self._load_relationships(
            project_id,
            candidate_set_id,
            relationships_path,
        )
        snapshot = ModelCandidateSetSnapshot(
            manifest=manifest,
            element_candidates=elements,
            relationship_candidates=relationships,
        )
        self._validate_snapshot(snapshot)
        return snapshot

    def _load_elements(
        self,
        project_id: str,
        candidate_set_id: str,
        directory: Path,
    ) -> tuple[ModelElementCandidate, ...]:
        try:
            entries = tuple(
                sorted(directory.iterdir(), key=lambda item: item.name)
            )
        except OSError as exc:
            raise ModelCandidatePersistenceError(
                f"Unable to inspect Element Candidate directory: {exc}"
            ) from exc

        result = []
        for entry in entries:
            self._reject_symlink(
                entry,
                label="Element Candidate entry",
            )
            match = _ELEMENT_FILE_PATTERN.fullmatch(entry.name)
            if match is None or not entry.is_file():
                raise ModelCandidateIntegrityError(
                    "Element Candidate directory contains an "
                    f"unexpected entry: {entry}."
                )
            candidate_id = match.group(1)
            candidate = model_element_candidate_from_json(
                self._read_text(
                    entry,
                    label="Model Element Candidate",
                ),
                expected_project_id=project_id,
                expected_candidate_set_id=candidate_set_id,
                expected_model_element_candidate_id=candidate_id,
            )
            result.append(candidate)
        return tuple(result)

    def _load_relationships(
        self,
        project_id: str,
        candidate_set_id: str,
        directory: Path,
    ) -> tuple[ModelRelationshipCandidate, ...]:
        try:
            entries = tuple(
                sorted(directory.iterdir(), key=lambda item: item.name)
            )
        except OSError as exc:
            raise ModelCandidatePersistenceError(
                "Unable to inspect Relationship Candidate directory: "
                f"{exc}"
            ) from exc

        result = []
        for entry in entries:
            self._reject_symlink(
                entry,
                label="Relationship Candidate entry",
            )
            match = _RELATIONSHIP_FILE_PATTERN.fullmatch(entry.name)
            if match is None or not entry.is_file():
                raise ModelCandidateIntegrityError(
                    "Relationship Candidate directory contains an "
                    f"unexpected entry: {entry}."
                )
            candidate_id = match.group(1)
            candidate = model_relationship_candidate_from_json(
                self._read_text(
                    entry,
                    label="Model Relationship Candidate",
                ),
                expected_project_id=project_id,
                expected_candidate_set_id=candidate_set_id,
                expected_model_relationship_candidate_id=candidate_id,
            )
            result.append(candidate)
        return tuple(result)

    def _validate_snapshot(
        self,
        snapshot: ModelCandidateSetSnapshot,
    ) -> None:
        if not isinstance(snapshot, ModelCandidateSetSnapshot):
            raise ModelCandidateIntegrityError(
                "snapshot must be a ModelCandidateSetSnapshot."
            )

        manifest = snapshot.manifest
        validate_model_candidate_set_manifest(manifest)
        element_map = {
            item.model_element_candidate_id: item
            for item in snapshot.element_candidates
        }
        relationship_map = {
            item.model_relationship_candidate_id: item
            for item in snapshot.relationship_candidates
        }

        if len(element_map) != len(snapshot.element_candidates):
            raise ModelCandidateIntegrityError(
                "Candidate Set contains duplicate MCE IDs."
            )
        if len(relationship_map) != len(
            snapshot.relationship_candidates
        ):
            raise ModelCandidateIntegrityError(
                "Candidate Set contains duplicate MCR IDs."
            )

        if tuple(sorted(element_map)) != manifest.element_candidate_ids:
            raise ModelCandidateIntegrityError(
                "Candidate Set manifest element_candidate_ids do not "
                "match persisted Element Candidates."
            )
        if (
            tuple(sorted(relationship_map))
            != manifest.relationship_candidate_ids
        ):
            raise ModelCandidateIntegrityError(
                "Candidate Set manifest relationship_candidate_ids do "
                "not match persisted Relationship Candidates."
            )

        snapshot_input_map = {
            (
                ref.approved_input_id,
                ref.content_fingerprint,
                ref.stable_subject_key,
            )
            for ref in manifest.approved_input_references
        }

        for candidate in snapshot.element_candidates:
            validate_model_element_candidate(candidate)
            self._require_candidate_membership(
                manifest,
                candidate.project_id,
                candidate.candidate_set_id,
            )
            self._require_candidate_provenance_within_snapshot(
                candidate.approved_input_references,
                snapshot_input_map,
            )

        for candidate in snapshot.relationship_candidates:
            validate_model_relationship_candidate(candidate)
            self._require_candidate_membership(
                manifest,
                candidate.project_id,
                candidate.candidate_set_id,
            )
            self._require_candidate_provenance_within_snapshot(
                candidate.approved_input_references,
                snapshot_input_map,
            )
            self._validate_relationship_endpoints(
                candidate,
                element_map,
            )

    def _validate_relationship_endpoints(
        self,
        relationship: ModelRelationshipCandidate,
        element_map: dict[str, ModelElementCandidate],
    ) -> None:
        for label, endpoint in (
            ("source", relationship.source),
            ("target", relationship.target),
        ):
            for candidate_id in endpoint.candidate_model_element_ids:
                element = element_map.get(candidate_id)
                if element is None:
                    raise ModelCandidateReferenceError(
                        f"Relationship {label} endpoint references "
                        "an Element Candidate outside this Candidate Set: "
                        f"{candidate_id}."
                    )
                if (
                    element.candidate_subject_key
                    != endpoint.candidate_subject_key
                ):
                    raise ModelCandidateIntegrityError(
                        f"Relationship {label} endpoint subject key does "
                        f"not match {candidate_id}."
                    )

    def _require_candidate_membership(
        self,
        manifest: ModelCandidateSetManifest,
        project_id: str,
        candidate_set_id: str,
    ) -> None:
        if project_id != manifest.project_id:
            raise ModelCandidateReferenceError(
                "Candidate project_id does not match Candidate Set."
            )
        if candidate_set_id != manifest.candidate_set_id:
            raise ModelCandidateReferenceError(
                "Candidate candidate_set_id does not match "
                "Candidate Set."
            )

    def _require_candidate_provenance_within_snapshot(
        self,
        references,
        snapshot_input_map: set[tuple[str, str, str]],
    ) -> None:
        for ref in references:
            identity = (
                ref.approved_input_id,
                ref.content_fingerprint,
                ref.stable_subject_key,
            )
            if identity not in snapshot_input_map:
                raise ModelCandidateReferenceError(
                    "Candidate Approved Input provenance is outside "
                    "the Candidate Set snapshot."
                )

    def _reject_project_wide_id_reuse(
        self,
        snapshot: ModelCandidateSetSnapshot,
        current: ModelCandidateRepositoryScanResult,
    ) -> None:
        existing_set_ids = {
            item.manifest.candidate_set_id
            for item in current.candidate_sets
        }
        if snapshot.manifest.candidate_set_id in existing_set_ids:
            raise ModelCandidatePersistenceError(
                "Candidate Set ID is already occupied."
            )

        existing_element_ids = {
            candidate.model_element_candidate_id
            for item in current.candidate_sets
            for candidate in item.element_candidates
        }
        reused_elements = existing_element_ids.intersection(
            candidate.model_element_candidate_id
            for candidate in snapshot.element_candidates
        )
        if reused_elements:
            raise ModelCandidateIntegrityError(
                "Model Element Candidate IDs are project-local and "
                f"must not be reused: {sorted(reused_elements)}."
            )

        existing_relationship_ids = {
            candidate.model_relationship_candidate_id
            for item in current.candidate_sets
            for candidate in item.relationship_candidates
        }
        reused_relationships = existing_relationship_ids.intersection(
            candidate.model_relationship_candidate_id
            for candidate in snapshot.relationship_candidates
        )
        if reused_relationships:
            raise ModelCandidateIntegrityError(
                "Model Relationship Candidate IDs are project-local "
                "and must not be reused: "
                f"{sorted(reused_relationships)}."
            )

    def _prepare_repository(self, project_id: str) -> None:
        project_root = project_path(self.root, project_id)
        repository_root = model_candidates_path(
            self.root,
            project_id,
        )
        sets_root = model_candidate_sets_path(
            self.root,
            project_id,
        )
        self._ensure_directory(
            repository_root,
            parent=project_root,
            label="Model Candidate repository root",
        )
        self._ensure_directory(
            sets_root,
            parent=repository_root,
            label="Candidate Set root",
        )

    def _ensure_directory(
        self,
        path: Path,
        *,
        parent: Path,
        label: str,
    ) -> None:
        self._assert_lexically_within(path, parent)
        self._reject_symlink(path, label=label)
        self._reject_symlink(parent, label=f"{label} parent")
        try:
            path.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise ModelCandidatePersistenceError(
                f"Unable to create {label} {path}: {exc}"
            ) from exc
        self._reject_symlink(path, label=label)
        if not path.is_dir():
            raise ModelCandidatePersistenceError(
                f"{label} is not a directory: {path}."
            )

    def _write_new_text(
        self,
        path: Path,
        text: str,
        *,
        label: str,
    ) -> None:
        self._reject_symlink(path, label=label)
        if path.exists():
            raise ModelCandidatePersistenceError(
                f"{label} already exists: {path}."
            )
        try:
            with path.open(
                "x",
                encoding="utf-8",
                newline="\n",
            ) as handle:
                handle.write(text)
                handle.flush()
                os.fsync(handle.fileno())
        except OSError as exc:
            raise ModelCandidatePersistenceError(
                f"Unable to write {label} {path}: {exc}"
            ) from exc

    def _read_text(self, path: Path, *, label: str) -> str:
        self._reject_symlink(path, label=label)
        try:
            return path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            raise ModelCandidateIntegrityError(
                f"{label} is not valid UTF-8."
            ) from exc
        except OSError as exc:
            raise ModelCandidatePersistenceError(
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
            raise ModelCandidateIntegrityError(
                f"{label} is missing or not a regular file: {path}."
            )

    def _require_regular_directory(
        self,
        path: Path,
        *,
        label: str,
    ) -> None:
        self._reject_symlink(path, label=label)
        if not path.exists() or not path.is_dir():
            raise ModelCandidateIntegrityError(
                f"{label} is missing or not a regular directory: "
                f"{path}."
            )

    def _reject_symlink(self, path: Path, *, label: str) -> None:
        if path.is_symlink():
            raise UnsafeModelCandidatePathError(
                f"{label} must not be a symbolic link: {path}."
            )

    def _assert_lexically_within(
        self,
        path: Path,
        parent: Path,
    ) -> None:
        try:
            path.absolute().relative_to(parent.absolute())
        except ValueError as exc:
            raise UnsafeModelCandidatePathError(
                f"Unsafe Model Candidate path: {path}."
            ) from exc

    def _raise_for_scan_issues(
        self,
        result: ModelCandidateRepositoryScanResult,
    ) -> None:
        if result.issues:
            first = result.issues[0]
            raise ModelCandidateRecoveryRequiredError(
                "Model Candidate repository has blocking integrity "
                f"issues; first={first.code}: {first.message}"
            )

    def _sorted_instances(
        self,
        values: Iterable,
        expected_type: type,
        *,
        key,
        label: str,
    ) -> tuple:
        if isinstance(values, (str, bytes)):
            raise ModelCandidateIntegrityError(
                f"{label} must be an iterable of artifacts."
            )
        try:
            items = tuple(values)
        except TypeError as exc:
            raise ModelCandidateIntegrityError(
                f"{label} must be iterable."
            ) from exc
        if not all(isinstance(item, expected_type) for item in items):
            raise ModelCandidateIntegrityError(
                f"{label} contains an invalid artifact type."
            )
        return tuple(sorted(items, key=key))
