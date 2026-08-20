"""Persistent canonical Source Analysis Units derived from Source Projections."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
import errno
import os
from pathlib import Path
import re
from typing import Any

from modules.project_workspace import ProjectWorkspace
from modules.source_projection.identifiers import (
    segment_id_sequence,
)
from modules.source_projection.repository import (
    SourceProjectionRepository,
)
from modules.source_projection.types import (
    SourceProjectionArtifact,
)

from .errors import (
    SourceAnalysisUnitAnchorError,
    SourceAnalysisUnitError,
    SourceAnalysisUnitIntegrityError,
    SourceAnalysisUnitNotFoundError,
    SourceAnalysisUnitPersistenceError,
    SourceAnalysisUnitReferenceError,
    SourceAnalysisUnitValidationError,
    UnavailableSourceAnalysisProjectionError,
    UnsafeSourceAnalysisUnitPathError,
)
from .identifiers import (
    is_valid_source_analysis_unit_id,
    next_source_analysis_unit_id,
    validate_source_analysis_unit_id,
)
from .manifest import (
    calculate_source_analysis_unit_content_fingerprint,
    create_source_analysis_unit,
    source_analysis_unit_from_json,
    source_analysis_unit_to_json,
)
from .types import (
    SourceAnalysisUnit,
    SourceAnalysisUnitAnchor,
)


DEFAULT_PROJECTS_ROOT = Path("data/projects")
SEMANTICS_DIRECTORY_NAME = "semantics"
SOURCE_ANALYSIS_UNITS_DIRECTORY_NAME = (
    "source_analysis_units"
)

DEFAULT_SEGMENTATION_PROFILE_ID = (
    "source_projection_segments"
)
DEFAULT_SEGMENTATION_PROFILE_VERSION = "1.0.0"

_SOURCE_ANALYSIS_UNIT_FILE_PATTERN = re.compile(
    r"^(SAU-[0-9]{6})\.json$"
)


def _default_clock() -> datetime:
    return datetime.now(timezone.utc)


class SourceAnalysisUnitRepository:
    """Create, reopen and validate canonical source analysis scopes."""

    def __init__(
        self,
        root: Path | str = DEFAULT_PROJECTS_ROOT,
        *,
        clock: Callable[[], datetime] = _default_clock,
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
        self._source_projection_repository = (
            SourceProjectionRepository(
                root=self.root,
                clock=clock,
            )
            if source_projection_repository is None
            else source_projection_repository
        )

    def ensure_projection_units(
        self,
        project_id: str,
        source_projection_id: str,
        *,
        segmentation_profile_id: str = (
            DEFAULT_SEGMENTATION_PROFILE_ID
        ),
        segmentation_profile_version: str = (
            DEFAULT_SEGMENTATION_PROFILE_VERSION
        ),
    ) -> tuple[SourceAnalysisUnit, ...]:
        """Create or reuse one canonical unit per projection segment."""

        self._require_default_profile(
            segmentation_profile_id,
            segmentation_profile_version,
        )
        projection = self._load_projection(
            project_id,
            source_projection_id,
        )

        if projection.manifest.projection_result == "unavailable":
            raise UnavailableSourceAnalysisProjectionError(
                "An unavailable Source Projection cannot create "
                "Source Analysis Units."
            )

        existing = list(
            self.list_source_analysis_units(project_id)
        )
        result: list[SourceAnalysisUnit] = []

        for segment in projection.manifest.segments:
            segment_text = projection.content[
                segment.start_offset:segment.end_offset
            ]
            source_order_index = segment_id_sequence(
                segment.segment_id
            )
            anchor = SourceAnalysisUnitAnchor(
                segment_id=segment.segment_id,
                start_offset=0,
                end_offset=len(segment_text),
            )
            expected_fingerprint = (
                calculate_source_analysis_unit_content_fingerprint(
                    project_id=project_id,
                    source_id=projection.manifest.source_id,
                    source_projection_id=(
                        source_projection_id
                    ),
                    source_projection_fingerprint=(
                        projection.manifest
                        .projection_fingerprint
                    ),
                    source_anchors=(anchor,),
                    source_excerpt=segment_text,
                    source_order_index=source_order_index,
                    segmentation_profile_id=(
                        segmentation_profile_id
                    ),
                    segmentation_profile_version=(
                        segmentation_profile_version
                    ),
                )
            )

            matching = tuple(
                unit
                for unit in existing
                if unit.content_fingerprint
                == expected_fingerprint
            )
            if len(matching) > 1:
                raise SourceAnalysisUnitIntegrityError(
                    "Source Analysis Unit content fingerprint "
                    "is not unique."
                )
            if matching:
                result.append(matching[0])
                continue

            conflicting = tuple(
                unit
                for unit in existing
                if (
                    unit.source_projection_id
                    == source_projection_id
                    and unit.segmentation_profile_id
                    == segmentation_profile_id
                    and unit.segmentation_profile_version
                    == segmentation_profile_version
                    and unit.source_order_index
                    == source_order_index
                )
            )
            if conflicting:
                raise SourceAnalysisUnitIntegrityError(
                    "Canonical Source Analysis Unit position "
                    "already exists with different content."
                )

            source_analysis_unit_id = (
                next_source_analysis_unit_id(
                    unit.source_analysis_unit_id
                    for unit in existing
                )
            )
            unit = create_source_analysis_unit(
                project_id=project_id,
                source_id=projection.manifest.source_id,
                source_projection_id=source_projection_id,
                source_analysis_unit_id=(
                    source_analysis_unit_id
                ),
                source_projection_fingerprint=(
                    projection.manifest.projection_fingerprint
                ),
                source_anchors=(anchor,),
                source_excerpt=segment_text,
                source_order_index=source_order_index,
                segmentation_profile_id=(
                    segmentation_profile_id
                ),
                segmentation_profile_version=(
                    segmentation_profile_version
                ),
                timestamp=self._current_utc_timestamp(),
            )
            self._publish_source_analysis_unit(unit)
            persisted = self.load_source_analysis_unit(
                project_id,
                unit.source_analysis_unit_id,
            )
            existing.append(persisted)
            result.append(persisted)

        return tuple(
            sorted(
                result,
                key=lambda unit: unit.source_order_index,
            )
        )

    def load_source_analysis_unit(
        self,
        project_id: str,
        source_analysis_unit_id: str,
    ) -> SourceAnalysisUnit:
        """Load and fully validate one persisted Source Analysis Unit."""

        path = self.source_analysis_unit_path(
            project_id,
            source_analysis_unit_id,
        )
        self._require_regular_file(
            path,
            not_found_error=SourceAnalysisUnitNotFoundError(
                "Source Analysis Unit was not found: "
                f"{path}."
            ),
        )

        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise SourceAnalysisUnitPersistenceError(
                "Unable to read Source Analysis Unit "
                f"{path}: {exc}"
            ) from exc

        try:
            unit = source_analysis_unit_from_json(
                text,
                expected_project_id=project_id,
                expected_source_analysis_unit_id=(
                    source_analysis_unit_id
                ),
            )
        except SourceAnalysisUnitError:
            raise
        except Exception as exc:
            raise SourceAnalysisUnitIntegrityError(
                "Unable to validate Source Analysis Unit "
                f"{path}: {exc}"
            ) from exc

        self._validate_references(unit)
        return unit

    def list_source_analysis_units(
        self,
        project_id: str,
        *,
        source_id: str | None = None,
        source_projection_id: str | None = None,
    ) -> tuple[SourceAnalysisUnit, ...]:
        """List valid Source Analysis Units in identifier order."""

        self._workspace.load_project(project_id)
        units_path = self.source_analysis_units_path(
            project_id
        )

        if not units_path.exists():
            return ()

        self._require_safe_directory(units_path)

        try:
            entries = tuple(
                sorted(
                    units_path.iterdir(),
                    key=lambda path: path.name,
                )
            )
        except OSError as exc:
            raise SourceAnalysisUnitPersistenceError(
                "Unable to inspect Source Analysis Units "
                f"directory {units_path}: {exc}"
            ) from exc

        units: list[SourceAnalysisUnit] = []
        for entry in entries:
            if entry.is_symlink() or not entry.is_file():
                raise UnsafeSourceAnalysisUnitPathError(
                    "Source Analysis Unit entries must be "
                    f"regular files: {entry}."
                )

            match = _SOURCE_ANALYSIS_UNIT_FILE_PATTERN.fullmatch(
                entry.name
            )
            if (
                match is None
                or not is_valid_source_analysis_unit_id(
                    match.group(1) if match else None
                )
            ):
                raise SourceAnalysisUnitIntegrityError(
                    "Source Analysis Units directory contains "
                    f"an unexpected entry: {entry}."
                )

            units.append(
                self.load_source_analysis_unit(
                    project_id,
                    match.group(1),
                )
            )

        self._require_unique_units(tuple(units))

        return tuple(
            unit
            for unit in units
            if (
                source_id is None
                or unit.source_id == source_id
            )
            and (
                source_projection_id is None
                or unit.source_projection_id
                == source_projection_id
            )
        )

    def source_analysis_units_path(
        self,
        project_id: str,
    ) -> Path:
        """Return the project-local Source Analysis Unit directory."""

        self._workspace.load_project(project_id)
        project_path = self.root / project_id
        semantics_path = (
            project_path / SEMANTICS_DIRECTORY_NAME
        )
        units_path = (
            semantics_path
            / SOURCE_ANALYSIS_UNITS_DIRECTORY_NAME
        )

        if semantics_path.is_symlink():
            raise UnsafeSourceAnalysisUnitPathError(
                "Semantic artifact directory must not be a "
                f"symbolic link: {semantics_path}."
            )
        if (
            semantics_path.exists()
            and not semantics_path.is_dir()
        ):
            raise UnsafeSourceAnalysisUnitPathError(
                "Semantic artifact path must be a directory: "
                f"{semantics_path}."
            )
        if units_path.is_symlink():
            raise UnsafeSourceAnalysisUnitPathError(
                "Source Analysis Units directory must not be "
                f"a symbolic link: {units_path}."
            )

        return units_path

    def source_analysis_unit_path(
        self,
        project_id: str,
        source_analysis_unit_id: str,
    ) -> Path:
        """Return the validated path of one Source Analysis Unit."""

        validated_id = validate_source_analysis_unit_id(
            source_analysis_unit_id
        )
        path = (
            self.source_analysis_units_path(project_id)
            / f"{validated_id}.json"
        )
        return path

    def _validate_references(
        self,
        unit: SourceAnalysisUnit,
    ) -> None:
        projection = self._load_projection(
            unit.project_id,
            unit.source_projection_id,
        )
        manifest = projection.manifest

        if manifest.project_id != unit.project_id:
            raise SourceAnalysisUnitReferenceError(
                "Source Projection belongs to a different project."
            )
        if manifest.source_id != unit.source_id:
            raise SourceAnalysisUnitReferenceError(
                "Source Projection belongs to a different source."
            )
        if (
            manifest.projection_fingerprint
            != unit.source_projection_fingerprint
        ):
            raise SourceAnalysisUnitReferenceError(
                "Source Analysis Unit is bound to a different "
                "Source Projection fingerprint."
            )
        if manifest.projection_result == "unavailable":
            raise UnavailableSourceAnalysisProjectionError(
                "An unavailable Source Projection cannot back "
                "a Source Analysis Unit."
            )

        self._require_default_profile(
            unit.segmentation_profile_id,
            unit.segmentation_profile_version,
        )
        self._validate_source_anchors(
            unit,
            projection,
        )
        self._validate_default_profile_contract(
            unit,
            projection,
        )

    def _validate_source_anchors(
        self,
        unit: SourceAnalysisUnit,
        projection: SourceProjectionArtifact,
    ) -> None:
        segment_by_id = {
            segment.segment_id: segment
            for segment in projection.manifest.segments
        }
        selected_text: list[str] = []

        for anchor in unit.source_anchors:
            segment = segment_by_id.get(anchor.segment_id)
            if segment is None:
                raise SourceAnalysisUnitAnchorError(
                    "Source Analysis Unit references unknown "
                    f"segment {anchor.segment_id}."
                )

            segment_text = projection.content[
                segment.start_offset:segment.end_offset
            ]
            if anchor.end_offset > len(segment_text):
                raise SourceAnalysisUnitAnchorError(
                    "Source Analysis Unit anchor exceeds segment "
                    f"{anchor.segment_id}."
                )

            selected_text.append(
                segment_text[
                    anchor.start_offset:anchor.end_offset
                ]
            )

        if unit.source_excerpt != "".join(selected_text):
            raise SourceAnalysisUnitAnchorError(
                "source_excerpt does not equal the unchanged "
                "concatenation of Source Projection anchors."
            )

    def _validate_default_profile_contract(
        self,
        unit: SourceAnalysisUnit,
        projection: SourceProjectionArtifact,
    ) -> None:
        if len(unit.source_anchors) != 1:
            raise SourceAnalysisUnitIntegrityError(
                "Default segmentation requires exactly one "
                "full Source Projection segment per unit."
            )

        anchor = unit.source_anchors[0]
        segment_by_id = {
            segment.segment_id: segment
            for segment in projection.manifest.segments
        }
        segment = segment_by_id[anchor.segment_id]
        segment_text = projection.content[
            segment.start_offset:segment.end_offset
        ]
        expected_order = segment_id_sequence(
            segment.segment_id
        )

        if unit.source_order_index != expected_order:
            raise SourceAnalysisUnitIntegrityError(
                "source_order_index does not match the "
                "Source Projection segment sequence."
            )
        if (
            anchor.start_offset != 0
            or anchor.end_offset != len(segment_text)
        ):
            raise SourceAnalysisUnitIntegrityError(
                "Default segmentation must anchor the complete "
                "Source Projection segment."
            )

    def _load_projection(
        self,
        project_id: str,
        source_projection_id: str,
    ) -> SourceProjectionArtifact:
        try:
            projection = (
                self._source_projection_repository.load_projection(
                    project_id,
                    source_projection_id,
                )
            )
        except Exception as exc:
            raise SourceAnalysisUnitReferenceError(
                "Unable to resolve Source Projection "
                f"{project_id}/{source_projection_id}: {exc}"
            ) from exc

        if not isinstance(
            projection,
            SourceProjectionArtifact,
        ):
            raise SourceAnalysisUnitReferenceError(
                "Source Projection Repository returned an "
                "unexpected artifact type."
            )

        return projection

    def _publish_source_analysis_unit(
        self,
        unit: SourceAnalysisUnit,
    ) -> None:
        path = self.source_analysis_unit_path(
            unit.project_id,
            unit.source_analysis_unit_id,
        )
        self._ensure_units_directory(path.parent)

        if path.exists() or path.is_symlink():
            raise SourceAnalysisUnitPersistenceError(
                "Source Analysis Unit already exists and must "
                f"not be overwritten: {path}."
            )

        temporary_path = path.with_name(
            f".{path.name}.tmp"
        )
        if (
            temporary_path.exists()
            or temporary_path.is_symlink()
        ):
            raise SourceAnalysisUnitPersistenceError(
                "Temporary Source Analysis Unit path already "
                f"exists: {temporary_path}."
            )

        serialized = source_analysis_unit_to_json(unit)

        try:
            with temporary_path.open(
                "x",
                encoding="utf-8",
            ) as handle:
                handle.write(serialized)

            persisted = source_analysis_unit_from_json(
                temporary_path.read_text(encoding="utf-8"),
                expected_project_id=unit.project_id,
                expected_source_analysis_unit_id=(
                    unit.source_analysis_unit_id
                ),
            )
            if persisted != unit:
                raise SourceAnalysisUnitIntegrityError(
                    "Persisted Source Analysis Unit differs "
                    "from the validated artifact."
                )

            try:
                os.link(temporary_path, path)
            except OSError as exc:
                if exc.errno == errno.EEXIST:
                    raise SourceAnalysisUnitPersistenceError(
                        "Source Analysis Unit appeared during "
                        f"publication and was not overwritten: {path}."
                    ) from exc
                raise SourceAnalysisUnitPersistenceError(
                    "Unable to publish Source Analysis Unit "
                    f"{path}: {exc}"
                ) from exc
        finally:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError as exc:
                raise SourceAnalysisUnitPersistenceError(
                    "Unable to remove temporary Source Analysis "
                    f"Unit file {temporary_path}: {exc}"
                ) from exc

    def _ensure_units_directory(
        self,
        units_path: Path,
    ) -> None:
        project_path = units_path.parent.parent
        semantics_path = units_path.parent

        if project_path.is_symlink():
            raise UnsafeSourceAnalysisUnitPathError(
                f"Project path must not be a symbolic link: {project_path}."
            )
        if semantics_path.is_symlink():
            raise UnsafeSourceAnalysisUnitPathError(
                "Semantic artifact directory must not be a "
                f"symbolic link: {semantics_path}."
            )
        if (
            semantics_path.exists()
            and not semantics_path.is_dir()
        ):
            raise UnsafeSourceAnalysisUnitPathError(
                "Semantic artifact path must be a directory: "
                f"{semantics_path}."
            )

        try:
            semantics_path.mkdir(exist_ok=True)
        except OSError as exc:
            raise SourceAnalysisUnitPersistenceError(
                "Unable to create semantic artifact directory "
                f"{semantics_path}: {exc}"
            ) from exc

        if units_path.is_symlink():
            raise UnsafeSourceAnalysisUnitPathError(
                "Source Analysis Units directory must not be "
                f"a symbolic link: {units_path}."
            )
        if units_path.exists() and not units_path.is_dir():
            raise UnsafeSourceAnalysisUnitPathError(
                "Source Analysis Units path must be a directory: "
                f"{units_path}."
            )

        try:
            units_path.mkdir(exist_ok=True)
        except OSError as exc:
            raise SourceAnalysisUnitPersistenceError(
                "Unable to create Source Analysis Units directory "
                f"{units_path}: {exc}"
            ) from exc

    def _require_safe_directory(
        self,
        path: Path,
    ) -> None:
        if path.is_symlink() or not path.is_dir():
            raise UnsafeSourceAnalysisUnitPathError(
                "Source Analysis Units path must be a regular "
                f"directory: {path}."
            )

    def _require_regular_file(
        self,
        path: Path,
        *,
        not_found_error: Exception,
    ) -> None:
        if not path.exists():
            raise not_found_error
        if path.is_symlink() or not path.is_file():
            raise UnsafeSourceAnalysisUnitPathError(
                "Source Analysis Unit path must be a regular "
                f"file: {path}."
            )

    def _require_unique_units(
        self,
        units: tuple[SourceAnalysisUnit, ...],
    ) -> None:
        fingerprints: dict[str, str] = {}
        positions: dict[
            tuple[str, str, str, int],
            str,
        ] = {}

        for unit in units:
            existing_id = fingerprints.get(
                unit.content_fingerprint
            )
            if existing_id is not None:
                raise SourceAnalysisUnitIntegrityError(
                    "Source Analysis Unit content fingerprint "
                    f"is shared by {existing_id} and "
                    f"{unit.source_analysis_unit_id}."
                )
            fingerprints[
                unit.content_fingerprint
            ] = unit.source_analysis_unit_id

            position_key = (
                unit.source_projection_id,
                unit.segmentation_profile_id,
                unit.segmentation_profile_version,
                unit.source_order_index,
            )
            existing_position = positions.get(position_key)
            if existing_position is not None:
                raise SourceAnalysisUnitIntegrityError(
                    "Source Analysis Unit canonical position is "
                    f"shared by {existing_position} and "
                    f"{unit.source_analysis_unit_id}."
                )
            positions[
                position_key
            ] = unit.source_analysis_unit_id

    def _require_default_profile(
        self,
        profile_id: str,
        profile_version: str,
    ) -> None:
        if (
            profile_id != DEFAULT_SEGMENTATION_PROFILE_ID
            or profile_version
            != DEFAULT_SEGMENTATION_PROFILE_VERSION
        ):
            raise SourceAnalysisUnitValidationError(
                "D1 supports only segmentation profile "
                f"{DEFAULT_SEGMENTATION_PROFILE_ID} "
                f"{DEFAULT_SEGMENTATION_PROFILE_VERSION}."
            )

    def _current_utc_timestamp(self) -> str:
        value = self._clock()
        if not isinstance(value, datetime):
            raise SourceAnalysisUnitPersistenceError(
                "clock must return a datetime."
            )
        if value.tzinfo is None or value.utcoffset() is None:
            raise SourceAnalysisUnitPersistenceError(
                "clock must return a timezone-aware UTC datetime."
            )
        if value.utcoffset().total_seconds() != 0:
            raise SourceAnalysisUnitPersistenceError(
                "clock must return a UTC datetime."
            )
        return value.isoformat().replace("+00:00", "Z")
