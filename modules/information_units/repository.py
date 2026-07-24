"""Immutable, project-isolated Information Unit persistence."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from datetime import datetime, timezone
import errno
import os
from pathlib import Path
import re
from typing import Any

from modules.project_sources import (
    ENGINEERING_SOURCE_ROLE,
    ProjectSourceRegistry,
)
from modules.project_workspace import ProjectWorkspace
from modules.project_workspace.errors import (
    ProjectNotFoundError,
    ProjectWorkspaceError,
)
from modules.project_workspace.identifiers import (
    is_valid_project_id,
)
from modules.project_workspace.workspace import (
    DEFAULT_PROJECTS_ROOT,
)
from modules.source_projection.repository import (
    SourceProjectionRepository,
)
from modules.source_projection.types import (
    SourceProjectionArtifact,
)

from .errors import (
    DuplicateInformationUnitContentError,
    IneligibleInformationUnitSourceError,
    InformationUnitAnchorError,
    InformationUnitError,
    InformationUnitIdAllocationError,
    InformationUnitIntegrityError,
    InformationUnitNotFoundError,
    InformationUnitPersistenceError,
    InformationUnitReferenceError,
    InformationUnitValidationError,
    UnavailableSourceProjectionError,
    UnsafeInformationUnitPathError,
)
from .identifiers import (
    is_valid_information_unit_id,
    next_information_unit_id,
    validate_information_unit_id,
)
from .manifest import (
    create_information_unit,
    information_unit_from_json,
    information_unit_to_json,
)
from .types import (
    InformationUnit,
    InformationUnitExtractionProvenance,
    InformationUnitIssue,
    InformationUnitScanResult,
    InformationUnitSourceAnchor,
)


SEMANTICS_DIRECTORY_NAME = "semantics"
INFORMATION_UNITS_DIRECTORY_NAME = "information_units"

_INFORMATION_UNIT_FILE_PATTERN = re.compile(
    r"^(IU-[0-9]{6})\.json$"
)


def _default_clock() -> datetime:
    return datetime.now(timezone.utc)


class InformationUnitRepository:
    """Create, publish and inspect immutable Information Units."""

    def __init__(
        self,
        root: Path | str = DEFAULT_PROJECTS_ROOT,
        *,
        clock: Callable[[], datetime] = _default_clock,
        source_registry: ProjectSourceRegistry | None = None,
        source_projection_repository: (
            SourceProjectionRepository | None
        ) = None,
    ) -> None:
        self.root = Path(root)
        self._clock = clock
        self._workspace = ProjectWorkspace(
            root=self.root,
            clock=clock,
        )
        self._source_registry = (
            ProjectSourceRegistry(
                root=self.root,
                clock=clock,
            )
            if source_registry is None
            else source_registry
        )
        self._source_projection_repository = (
            SourceProjectionRepository(
                root=self.root,
                clock=clock,
            )
            if source_projection_repository is None
            else source_projection_repository
        )

    def create_information_unit(
        self,
        project_id: str,
        source_id: str,
        source_projection_id: str,
        *,
        source_anchors: Iterable[
            InformationUnitSourceAnchor
        ],
        source_excerpt: str,
        interpreted_statement: str,
        information_type: str,
        statement_modality: str,
        epistemic_class: str,
        extraction_provenance: (
            InformationUnitExtractionProvenance
        ),
        confidence: str,
        confidence_rationale: str,
        supporting_information_unit_ids: Iterable[str] = (),
        derivation_rationale: str | None = None,
        missing_evidence: str | None = None,
    ) -> InformationUnit:
        """Validate and atomically publish one new Information Unit."""

        project_path = self._project_path(project_id)
        units_path = self._information_units_path(
            project_id,
            project_path=project_path,
        )
        self._ensure_directory(
            units_path,
            label="Information Units directory",
        )

        anchors = self._tuple_of_instances(
            source_anchors,
            InformationUnitSourceAnchor,
            "source_anchors",
        )
        supporting_ids = self._sorted_information_unit_ids(
            supporting_information_unit_ids
        )
        existing_units = self.list_information_units(
            project_id
        )
        information_unit_id = next_information_unit_id(
            unit.information_unit_id
            for unit in existing_units
        )

        information_unit = create_information_unit(
            project_id=project_id,
            information_unit_id=information_unit_id,
            source_id=source_id,
            source_projection_id=source_projection_id,
            source_anchors=anchors,
            source_excerpt=source_excerpt,
            interpreted_statement=interpreted_statement,
            information_type=information_type,
            statement_modality=statement_modality,
            epistemic_class=epistemic_class,
            supporting_information_unit_ids=supporting_ids,
            derivation_rationale=derivation_rationale,
            missing_evidence=missing_evidence,
            extraction_provenance=extraction_provenance,
            confidence=confidence,
            confidence_rationale=confidence_rationale,
            timestamp=self._current_utc_timestamp(),
        )

        self._validate_information_unit_references(
            information_unit,
            known_units={
                unit.information_unit_id: unit
                for unit in existing_units
            },
        )
        self._reject_duplicate_content(
            information_unit,
            existing_units,
        )
        self._publish_information_unit(information_unit)

        return self.load_information_unit(
            project_id,
            information_unit_id,
        )

    def load_information_unit(
        self,
        project_id: str,
        information_unit_id: str,
    ) -> InformationUnit:
        """Load and fully validate one persisted Information Unit."""

        information_unit = self._load_information_unit_file(
            project_id,
            information_unit_id,
        )
        known_units = {
            unit.information_unit_id: unit
            for unit in self._load_all_manifest_valid_units(
                project_id
            )
        }
        self._validate_information_unit_references(
            information_unit,
            known_units=known_units,
        )
        return information_unit

    def list_information_units(
        self,
        project_id: str,
        *,
        source_id: str | None = None,
        source_projection_id: str | None = None,
    ) -> tuple[InformationUnit, ...]:
        """List fully valid Information Units in identifier order."""

        if source_id is not None:
            self._load_source(project_id, source_id)

        if source_projection_id is not None:
            self._load_projection(
                project_id,
                source_projection_id,
            )

        units = self._load_all_manifest_valid_units(project_id)
        known_units = {
            unit.information_unit_id: unit
            for unit in units
        }

        for information_unit in units:
            self._validate_information_unit_references(
                information_unit,
                known_units=known_units,
            )

        self._require_unique_fingerprints(units)

        return tuple(
            information_unit
            for information_unit in units
            if (
                source_id is None
                or information_unit.source_id == source_id
            )
            and (
                source_projection_id is None
                or information_unit.source_projection_id
                == source_projection_id
            )
        )

    def scan_information_units(
        self,
        project_id: str,
    ) -> InformationUnitScanResult:
        """Return valid Information Units and deterministic issues."""

        issues: list[InformationUnitIssue] = []

        try:
            units_path = self.information_units_path(project_id)
        except Exception as exc:
            return InformationUnitScanResult(
                issues=(
                    InformationUnitIssue(
                        project_id=project_id,
                        code="invalid_information_units_path",
                        message=str(exc),
                        path=self.root / project_id,
                    ),
                )
            )

        if not units_path.exists():
            return InformationUnitScanResult()

        if units_path.is_symlink() or not units_path.is_dir():
            return InformationUnitScanResult(
                issues=(
                    InformationUnitIssue(
                        project_id=project_id,
                        code="unsafe_information_units_path",
                        message=(
                            "Information Units path must be a "
                            "regular directory."
                        ),
                        path=units_path,
                    ),
                )
            )

        parsed_units: list[InformationUnit] = []
        parsed_paths: dict[str, Path] = {}

        try:
            entries = tuple(
                sorted(
                    units_path.iterdir(),
                    key=lambda path: path.name,
                )
            )
        except OSError as exc:
            return InformationUnitScanResult(
                issues=(
                    InformationUnitIssue(
                        project_id=project_id,
                        code="unreadable_information_units_path",
                        message=str(exc),
                        path=units_path,
                    ),
                )
            )

        for entry in entries:
            match = _INFORMATION_UNIT_FILE_PATTERN.fullmatch(
                entry.name
            )

            if (
                entry.is_symlink()
                or not entry.is_file()
                or match is None
                or not is_valid_information_unit_id(
                    match.group(1) if match else None
                )
            ):
                issues.append(
                    InformationUnitIssue(
                        project_id=project_id,
                        code="unexpected_information_unit_entry",
                        message=(
                            "Information Units directory contains "
                            "an unexpected or unsafe entry."
                        ),
                        path=entry,
                    )
                )
                continue

            information_unit_id = match.group(1)

            try:
                information_unit = (
                    self._load_information_unit_file(
                        project_id,
                        information_unit_id,
                    )
                )
            except Exception as exc:
                issues.append(
                    InformationUnitIssue(
                        project_id=project_id,
                        code="invalid_information_unit",
                        message=str(exc),
                        path=entry,
                        information_unit_id=(
                            information_unit_id
                        ),
                    )
                )
                continue

            parsed_units.append(information_unit)
            parsed_paths[information_unit_id] = entry

        known_units = {
            unit.information_unit_id: unit
            for unit in parsed_units
        }
        invalid_ids: set[str] = set()

        for information_unit in parsed_units:
            try:
                self._validate_information_unit_references(
                    information_unit,
                    known_units=known_units,
                )
            except Exception as exc:
                invalid_ids.add(
                    information_unit.information_unit_id
                )
                issues.append(
                    InformationUnitIssue(
                        project_id=project_id,
                        code="invalid_information_unit_reference",
                        message=str(exc),
                        path=parsed_paths[
                            information_unit.information_unit_id
                        ],
                        information_unit_id=(
                            information_unit.information_unit_id
                        ),
                        source_id=information_unit.source_id,
                        source_projection_id=(
                            information_unit
                            .source_projection_id
                        ),
                    )
                )

        fingerprints: dict[str, str] = {}

        for information_unit in parsed_units:
            existing_id = fingerprints.get(
                information_unit.content_fingerprint
            )

            if existing_id is None:
                fingerprints[
                    information_unit.content_fingerprint
                ] = information_unit.information_unit_id
                continue

            invalid_ids.add(existing_id)
            invalid_ids.add(
                information_unit.information_unit_id
            )
            issues.append(
                InformationUnitIssue(
                    project_id=project_id,
                    code="duplicate_information_unit_content",
                    message=(
                        "Content fingerprint is shared by "
                        f"{existing_id} and "
                        f"{information_unit.information_unit_id}."
                    ),
                    path=parsed_paths[
                        information_unit.information_unit_id
                    ],
                    information_unit_id=(
                        information_unit.information_unit_id
                    ),
                    source_id=information_unit.source_id,
                    source_projection_id=(
                        information_unit.source_projection_id
                    ),
                )
            )

        issues.sort(
            key=lambda issue: (
                str(issue.path),
                issue.code,
                issue.information_unit_id or "",
                issue.source_id or "",
                issue.source_projection_id or "",
            )
        )
        valid_units = tuple(
            unit
            for unit in parsed_units
            if unit.information_unit_id not in invalid_ids
        )

        return InformationUnitScanResult(
            information_units=valid_units,
            issues=tuple(issues),
        )

    def information_units_path(
        self,
        project_id: str,
    ) -> Path:
        """Return the validated project Information Units path."""

        project_path = self._project_path(project_id)
        return self._information_units_path(
            project_id,
            project_path=project_path,
        )

    def information_unit_path(
        self,
        project_id: str,
        information_unit_id: str,
    ) -> Path:
        """Return the validated path of one Information Unit."""

        project_path = self._project_path(project_id)
        return self._information_unit_path(
            project_id,
            information_unit_id,
            project_path=project_path,
        )

    def _load_all_manifest_valid_units(
        self,
        project_id: str,
    ) -> tuple[InformationUnit, ...]:
        units_path = self.information_units_path(project_id)

        if not units_path.exists():
            return ()

        self._reject_symlink(
            units_path,
            label="Information Units directory",
        )

        if not units_path.is_dir():
            raise UnsafeInformationUnitPathError(
                "Information Units path is not a directory: "
                f"{units_path}."
            )

        try:
            entries = tuple(
                sorted(
                    units_path.iterdir(),
                    key=lambda path: path.name,
                )
            )
        except OSError as exc:
            raise InformationUnitPersistenceError(
                "Unable to inspect Information Units directory "
                f"{units_path}: {exc}"
            ) from exc

        units: list[InformationUnit] = []

        for entry in entries:
            self._reject_symlink(
                entry,
                label="Information Unit entry",
            )
            match = _INFORMATION_UNIT_FILE_PATTERN.fullmatch(
                entry.name
            )

            if match is None or not entry.is_file():
                raise InformationUnitIntegrityError(
                    "Information Units directory contains an "
                    f"unexpected entry: {entry}."
                )

            units.append(
                self._load_information_unit_file(
                    project_id,
                    match.group(1),
                )
            )

        return tuple(units)

    def _load_information_unit_file(
        self,
        project_id: str,
        information_unit_id: str,
    ) -> InformationUnit:
        path = self.information_unit_path(
            project_id,
            information_unit_id,
        )
        self._require_regular_file(
            path,
            not_found_error=InformationUnitNotFoundError(
                f"Information Unit was not found: {path}."
            ),
            label="Information Unit",
        )

        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise InformationUnitPersistenceError(
                f"Unable to read Information Unit {path}: {exc}"
            ) from exc

        try:
            return information_unit_from_json(
                text,
                expected_project_id=project_id,
                expected_information_unit_id=(
                    information_unit_id
                ),
            )
        except InformationUnitError:
            raise
        except Exception as exc:
            raise InformationUnitIntegrityError(
                f"Unable to validate Information Unit "
                f"{path}: {exc}"
            ) from exc

    def _validate_information_unit_references(
        self,
        information_unit: InformationUnit,
        *,
        known_units: dict[str, InformationUnit],
    ) -> None:
        source = self._load_source(
            information_unit.project_id,
            information_unit.source_id,
        )

        if source.source_role != ENGINEERING_SOURCE_ROLE:
            raise IneligibleInformationUnitSourceError(
                "Only an engineering_source may create an "
                "engineering Information Unit."
            )

        projection = self._load_projection(
            information_unit.project_id,
            information_unit.source_projection_id,
        )
        manifest = projection.manifest

        if manifest.project_id != information_unit.project_id:
            raise InformationUnitReferenceError(
                "Source Projection belongs to a different project."
            )

        if manifest.source_id != information_unit.source_id:
            raise InformationUnitReferenceError(
                "Source Projection belongs to a different source."
            )

        if manifest.source_role != ENGINEERING_SOURCE_ROLE:
            raise IneligibleInformationUnitSourceError(
                "Source Projection was not created from an "
                "engineering_source."
            )

        if manifest.projection_result == "unavailable":
            raise UnavailableSourceProjectionError(
                "An unavailable Source Projection cannot create "
                "Information Units."
            )

        self._validate_source_anchors(
            information_unit,
            projection,
        )

        for supporting_id in (
            information_unit.supporting_information_unit_ids
        ):
            supporting_unit = known_units.get(supporting_id)

            if supporting_unit is None:
                raise InformationUnitReferenceError(
                    "Supporting Information Unit was not found "
                    f"in project {information_unit.project_id}: "
                    f"{supporting_id}."
                )

            if (
                supporting_unit.project_id
                != information_unit.project_id
            ):
                raise InformationUnitReferenceError(
                    "Supporting Information Unit belongs to a "
                    "different project."
                )

            if (
                supporting_unit.source_id
                != information_unit.source_id
            ):
                raise InformationUnitReferenceError(
                    "P4 derivation support must belong to the "
                    "same engineering source."
                )

    def _validate_source_anchors(
        self,
        information_unit: InformationUnit,
        projection: SourceProjectionArtifact,
    ) -> None:
        segment_by_id = {
            segment.segment_id: segment
            for segment in projection.manifest.segments
        }
        selected_text: list[str] = []

        for anchor in information_unit.source_anchors:
            segment = segment_by_id.get(anchor.segment_id)

            if segment is None:
                raise InformationUnitAnchorError(
                    "Source anchor references unknown segment "
                    f"{anchor.segment_id}."
                )

            segment_text = projection.content[
                segment.start_offset:segment.end_offset
            ]

            if anchor.end_offset > len(segment_text):
                raise InformationUnitAnchorError(
                    "Source anchor range exceeds segment "
                    f"{anchor.segment_id}."
                )

            selected_text.append(
                segment_text[
                    anchor.start_offset:anchor.end_offset
                ]
            )

        expected_excerpt = "".join(selected_text)

        if information_unit.source_excerpt != expected_excerpt:
            raise InformationUnitAnchorError(
                "source_excerpt does not equal the unchanged "
                "concatenation of its Source Projection anchors."
            )

    def _load_source(
        self,
        project_id: str,
        source_id: str,
    ) -> Any:
        try:
            return self._source_registry.load_source(
                project_id,
                source_id,
            )
        except Exception as exc:
            raise InformationUnitReferenceError(
                "Unable to resolve Information Unit source "
                f"{project_id}/{source_id}: {exc}"
            ) from exc

    def _load_projection(
        self,
        project_id: str,
        source_projection_id: str,
    ) -> SourceProjectionArtifact:
        try:
            artifact = (
                self._source_projection_repository
                .load_projection(
                    project_id,
                    source_projection_id,
                )
            )
        except Exception as exc:
            raise InformationUnitReferenceError(
                "Unable to resolve Source Projection "
                f"{project_id}/{source_projection_id}: {exc}"
            ) from exc

        if not isinstance(artifact, SourceProjectionArtifact):
            raise InformationUnitReferenceError(
                "Source Projection Repository returned an "
                "unexpected artifact type."
            )

        return artifact

    def _reject_duplicate_content(
        self,
        candidate: InformationUnit,
        existing_units: tuple[InformationUnit, ...],
    ) -> None:
        for existing in existing_units:
            if (
                existing.content_fingerprint
                == candidate.content_fingerprint
            ):
                raise DuplicateInformationUnitContentError(
                    "Information Unit professional content "
                    "already exists as "
                    f"{existing.information_unit_id}."
                )

    def _require_unique_fingerprints(
        self,
        information_units: tuple[InformationUnit, ...],
    ) -> None:
        fingerprints: dict[str, str] = {}

        for information_unit in information_units:
            existing_id = fingerprints.get(
                information_unit.content_fingerprint
            )

            if existing_id is not None:
                raise DuplicateInformationUnitContentError(
                    "Information Unit content fingerprint is "
                    f"shared by {existing_id} and "
                    f"{information_unit.information_unit_id}."
                )

            fingerprints[
                information_unit.content_fingerprint
            ] = information_unit.information_unit_id

    def _publish_information_unit(
        self,
        information_unit: InformationUnit,
    ) -> None:
        if not isinstance(information_unit, InformationUnit):
            raise InformationUnitValidationError(
                "information_unit must be an InformationUnit "
                "instance."
            )

        path = self.information_unit_path(
            information_unit.project_id,
            information_unit.information_unit_id,
        )
        self._ensure_directory(
            path.parent,
            label="Information Units directory",
        )
        serialized = information_unit_to_json(
            information_unit
        )
        self._publish_new_validated_file(
            path,
            serialized,
            expected_value=information_unit,
            parser=lambda text: information_unit_from_json(
                text,
                expected_project_id=information_unit.project_id,
                expected_information_unit_id=(
                    information_unit.information_unit_id
                ),
            ),
            label="Information Unit",
        )

    def _publish_new_validated_file(
        self,
        target_path: Path,
        serialized: str,
        *,
        expected_value: Any,
        parser: Callable[[str], Any],
        label: str,
    ) -> None:
        temporary_path = self._temporary_path(target_path)
        self._reject_existing_temporary_path(
            temporary_path,
            label=label,
        )

        if target_path.exists() or target_path.is_symlink():
            raise InformationUnitPersistenceError(
                f"{label} already exists and must not be "
                f"overwritten: {target_path}."
            )

        self._write_and_validate_temporary_file(
            temporary_path,
            serialized,
            expected_value=expected_value,
            parser=parser,
            label=label,
        )

        try:
            os.link(temporary_path, target_path)
        except OSError as exc:
            if exc.errno == errno.EEXIST:
                raise InformationUnitPersistenceError(
                    f"{label} appeared during publication and "
                    f"was not overwritten: {target_path}."
                ) from exc

            raise InformationUnitPersistenceError(
                f"Unable to publish {label} at "
                f"{target_path}: {exc}"
            ) from exc
        finally:
            self._remove_temporary_file(
                temporary_path,
                label=label,
            )

    def _write_and_validate_temporary_file(
        self,
        temporary_path: Path,
        serialized: str,
        *,
        expected_value: Any,
        parser: Callable[[str], Any],
        label: str,
    ) -> None:
        if not isinstance(serialized, str):
            raise InformationUnitPersistenceError(
                f"Serialized {label} content must be a string."
            )

        try:
            with temporary_path.open(
                "x",
                encoding="utf-8",
                newline="\n",
            ) as output:
                output.write(serialized)
                output.flush()
                os.fsync(output.fileno())

            persisted_text = temporary_path.read_text(
                encoding="utf-8"
            )
            persisted_value = parser(persisted_text)
        except (OSError, UnicodeError) as exc:
            self._remove_temporary_file(
                temporary_path,
                label=label,
                suppress_missing=True,
            )
            raise InformationUnitPersistenceError(
                f"Unable to prepare temporary {label} file "
                f"{temporary_path}: {exc}"
            ) from exc
        except Exception:
            self._remove_temporary_file(
                temporary_path,
                label=label,
                suppress_missing=True,
            )
            raise

        if persisted_value != expected_value:
            self._remove_temporary_file(
                temporary_path,
                label=label,
                suppress_missing=True,
            )
            raise InformationUnitIntegrityError(
                f"Persisted temporary {label} differs from its "
                "validated value."
            )

    def _project_path(
        self,
        project_id: str,
    ) -> Path:
        if not is_valid_project_id(project_id):
            raise UnsafeInformationUnitPathError(
                "project_id must contain exactly six digits."
            )

        try:
            project = self._workspace.load_project(project_id)
        except ProjectNotFoundError:
            raise
        except ProjectWorkspaceError as exc:
            raise InformationUnitPersistenceError(
                f"Unable to validate project {project_id!r}: "
                f"{exc}"
            ) from exc

        project_path = self.root / project.project_id
        self._assert_path_within(
            project_path,
            self.root,
        )

        if project_path.is_symlink():
            raise UnsafeInformationUnitPathError(
                "Symbolic-link project directories are "
                f"rejected: {project_path}."
            )

        return project_path

    def _information_units_path(
        self,
        project_id: str,
        *,
        project_path: Path | None = None,
    ) -> Path:
        validated_project_path = (
            self._project_path(project_id)
            if project_path is None
            else project_path
        )
        semantics_path = (
            validated_project_path
            / SEMANTICS_DIRECTORY_NAME
        )
        self._assert_path_within(
            semantics_path,
            validated_project_path,
        )
        self._reject_symlink(
            semantics_path,
            label="Project semantics directory",
        )
        units_path = (
            semantics_path
            / INFORMATION_UNITS_DIRECTORY_NAME
        )
        self._assert_path_within(
            units_path,
            semantics_path,
        )
        self._reject_symlink(
            units_path,
            label="Information Units directory",
        )
        return units_path

    def _information_unit_path(
        self,
        project_id: str,
        information_unit_id: str,
        *,
        project_path: Path | None = None,
    ) -> Path:
        try:
            validated_id = validate_information_unit_id(
                information_unit_id
            )
        except Exception as exc:
            raise UnsafeInformationUnitPathError(
                "information_unit_id must be a valid "
                "Information Unit ID."
            ) from exc

        units_path = self._information_units_path(
            project_id,
            project_path=project_path,
        )
        path = units_path / f"{validated_id}.json"
        self._assert_path_within(path, units_path)
        self._reject_symlink(
            path,
            label="Information Unit",
        )
        return path

    def _ensure_directory(
        self,
        path: Path,
        *,
        label: str,
    ) -> None:
        self._reject_symlink(path, label=label)

        if path.exists() and not path.is_dir():
            raise UnsafeInformationUnitPathError(
                f"{label} is not a directory: {path}."
            )

        try:
            path.mkdir(
                parents=True,
                exist_ok=True,
            )
        except OSError as exc:
            raise InformationUnitPersistenceError(
                f"Unable to create {label} {path}: {exc}"
            ) from exc

        self._reject_symlink(path, label=label)

    def _require_regular_file(
        self,
        path: Path,
        *,
        not_found_error: Exception,
        label: str,
    ) -> None:
        self._reject_symlink(path, label=label)

        if not path.exists():
            raise not_found_error

        if not path.is_file():
            raise UnsafeInformationUnitPathError(
                f"{label} is not a regular file: {path}."
            )

    def _reject_symlink(
        self,
        path: Path,
        *,
        label: str,
    ) -> None:
        if path.is_symlink():
            raise UnsafeInformationUnitPathError(
                f"Symbolic-link {label} paths are rejected: "
                f"{path}."
            )

    def _assert_path_within(
        self,
        path: Path,
        parent: Path,
    ) -> None:
        try:
            path.resolve(strict=False).relative_to(
                parent.resolve(strict=False)
            )
        except ValueError as exc:
            raise UnsafeInformationUnitPathError(
                f"Path escapes its permitted parent: {path}."
            ) from exc

    def _temporary_path(
        self,
        target_path: Path,
    ) -> Path:
        temporary_path = target_path.parent / (
            f".{target_path.name}.tmp"
        )
        self._assert_path_within(
            temporary_path,
            target_path.parent,
        )
        return temporary_path

    def _reject_existing_temporary_path(
        self,
        temporary_path: Path,
        *,
        label: str,
    ) -> None:
        if (
            temporary_path.exists()
            or temporary_path.is_symlink()
        ):
            raise InformationUnitPersistenceError(
                f"Temporary {label} path already exists: "
                f"{temporary_path}."
            )

    def _remove_temporary_file(
        self,
        temporary_path: Path,
        *,
        label: str,
        suppress_missing: bool = False,
    ) -> None:
        try:
            temporary_path.unlink(
                missing_ok=suppress_missing,
            )
        except OSError as exc:
            raise InformationUnitPersistenceError(
                f"Unable to remove temporary {label} file "
                f"{temporary_path}: {exc}"
            ) from exc

    def _tuple_of_instances(
        self,
        values: Iterable[Any],
        expected_type: type[Any],
        label: str,
    ) -> tuple[Any, ...]:
        if isinstance(values, (str, bytes)):
            raise InformationUnitValidationError(
                f"{label} must be an iterable of "
                f"{expected_type.__name__} instances."
            )

        try:
            result = tuple(values)
        except TypeError as exc:
            raise InformationUnitValidationError(
                f"{label} must be iterable."
            ) from exc

        if not all(
            isinstance(value, expected_type)
            for value in result
        ):
            raise InformationUnitValidationError(
                f"{label} must contain only "
                f"{expected_type.__name__} instances."
            )

        return result

    def _sorted_information_unit_ids(
        self,
        values: Iterable[str],
    ) -> tuple[str, ...]:
        identifiers = self._tuple_of_instances(
            values,
            str,
            "supporting_information_unit_ids",
        )

        for identifier in identifiers:
            try:
                validate_information_unit_id(identifier)
            except Exception as exc:
                raise InformationUnitValidationError(
                    "supporting_information_unit_ids contains "
                    f"an invalid ID: {identifier!r}."
                ) from exc

        if len(identifiers) != len(set(identifiers)):
            raise InformationUnitValidationError(
                "supporting_information_unit_ids must not "
                "contain duplicates."
            )

        return tuple(sorted(identifiers))

    def _current_utc_timestamp(self) -> str:
        value = self._clock()

        if not isinstance(value, datetime):
            raise InformationUnitPersistenceError(
                "Information Unit Repository clock must return "
                "a datetime."
            )

        if value.tzinfo is None or value.utcoffset() is None:
            raise InformationUnitPersistenceError(
                "Information Unit Repository clock must return "
                "a timezone-aware datetime."
            )

        utc_value = value.astimezone(timezone.utc)
        return (
            utc_value.isoformat(timespec="seconds")
            .replace("+00:00", "Z")
        )