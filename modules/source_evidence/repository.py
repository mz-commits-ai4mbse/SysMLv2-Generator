"""Persistent source-grounded Evidence derived from Source Projections."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
import errno
import os
from pathlib import Path
import re

from modules.project_sources import ENGINEERING_SOURCE_ROLE
from modules.project_workspace import ProjectWorkspace
from modules.source_projection.repository import (
    SourceProjectionRepository,
)
from modules.source_projection.types import (
    SourceProjectionArtifact,
)

from .errors import (
    SourceEvidenceAnchorError,
    SourceEvidenceError,
    SourceEvidenceIntegrityError,
    SourceEvidenceNotFoundError,
    SourceEvidencePersistenceError,
    SourceEvidenceReferenceError,
    UnavailableSourceEvidenceProjectionError,
    UnsafeSourceEvidencePathError,
)
from .identifiers import (
    is_valid_source_evidence_id,
    next_source_evidence_id,
    validate_source_evidence_id,
)
from .manifest import (
    calculate_source_evidence_content_fingerprint,
    create_source_evidence,
    source_evidence_from_json,
    source_evidence_to_json,
)
from .types import (
    SourceEvidence,
    SourceEvidenceAnchor,
)


DEFAULT_PROJECTS_ROOT = Path("data/projects")
SEMANTICS_DIRECTORY_NAME = "semantics"
SOURCE_EVIDENCE_DIRECTORY_NAME = "source_evidence"

_SOURCE_EVIDENCE_FILE_PATTERN = re.compile(
    r"^(EVD-[0-9]{6})\.json$"
)


def _default_clock() -> datetime:
    return datetime.now(timezone.utc)


class SourceEvidenceRepository:
    """Create, reopen and validate source-grounded Evidence."""

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

    def create_or_reuse_evidence(
        self,
        project_id: str,
        source_projection_id: str,
        *,
        source_anchors: tuple[SourceEvidenceAnchor, ...],
        source_excerpt: str,
    ) -> SourceEvidence:
        """Create or reuse Evidence for one exact source-grounded span."""

        projection = self._load_projection(
            project_id,
            source_projection_id,
        )
        if projection.manifest.projection_result == "unavailable":
            raise UnavailableSourceEvidenceProjectionError(
                "An unavailable Source Projection cannot back "
                "Source Evidence."
            )

        expected_fingerprint = (
            calculate_source_evidence_content_fingerprint(
                project_id=project_id,
                source_id=projection.manifest.source_id,
                source_projection_id=source_projection_id,
                source_projection_fingerprint=(
                    projection.manifest.projection_fingerprint
                ),
                source_anchors=source_anchors,
                source_excerpt=source_excerpt,
            )
        )

        existing = self.list_source_evidence(
            project_id,
            source_id=projection.manifest.source_id,
            source_projection_id=source_projection_id,
        )
        matching = tuple(
            evidence
            for evidence in existing
            if evidence.content_fingerprint == expected_fingerprint
        )
        if len(matching) > 1:
            raise SourceEvidenceIntegrityError(
                "Source Evidence content fingerprint is not unique."
            )
        if matching:
            return matching[0]

        source_evidence_id = next_source_evidence_id(
            evidence.source_evidence_id
            for evidence in self.list_source_evidence(project_id)
        )

        evidence = create_source_evidence(
            project_id=project_id,
            source_id=projection.manifest.source_id,
            source_projection_id=source_projection_id,
            source_evidence_id=source_evidence_id,
            source_projection_fingerprint=(
                projection.manifest.projection_fingerprint
            ),
            source_anchors=source_anchors,
            source_excerpt=source_excerpt,
            timestamp=self._current_utc_timestamp(),
        )
        self._validate_references(evidence)
        self._publish_source_evidence(evidence)
        return self.load_source_evidence(
            project_id,
            source_evidence_id,
        )

    def load_source_evidence(
        self,
        project_id: str,
        source_evidence_id: str,
    ) -> SourceEvidence:
        """Load and fully validate one persisted Source Evidence object."""

        path = self.source_evidence_path(
            project_id,
            source_evidence_id,
        )
        self._require_regular_file(
            path,
            not_found_error=SourceEvidenceNotFoundError(
                f"Source Evidence was not found: {path}."
            ),
        )

        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise SourceEvidencePersistenceError(
                f"Unable to read Source Evidence {path}: {exc}"
            ) from exc

        try:
            evidence = source_evidence_from_json(
                text,
                expected_project_id=project_id,
                expected_source_evidence_id=source_evidence_id,
            )
        except SourceEvidenceError:
            raise
        except Exception as exc:
            raise SourceEvidenceIntegrityError(
                f"Unable to validate Source Evidence {path}: {exc}"
            ) from exc

        self._validate_references(evidence)
        return evidence

    def list_source_evidence(
        self,
        project_id: str,
        *,
        source_id: str | None = None,
        source_projection_id: str | None = None,
    ) -> tuple[SourceEvidence, ...]:
        """List valid Source Evidence in identifier order."""

        self._workspace.load_project(project_id)
        evidence_path = self.source_evidence_directory_path(project_id)

        if not evidence_path.exists():
            return ()

        self._require_safe_directory(evidence_path)

        try:
            entries = tuple(
                sorted(
                    evidence_path.iterdir(),
                    key=lambda path: path.name,
                )
            )
        except OSError as exc:
            raise SourceEvidencePersistenceError(
                "Unable to inspect Source Evidence directory "
                f"{evidence_path}: {exc}"
            ) from exc

        result: list[SourceEvidence] = []
        for entry in entries:
            if entry.is_symlink() or not entry.is_file():
                raise UnsafeSourceEvidencePathError(
                    "Source Evidence entries must be regular files: "
                    f"{entry}."
                )

            match = _SOURCE_EVIDENCE_FILE_PATTERN.fullmatch(entry.name)
            if (
                match is None
                or not is_valid_source_evidence_id(
                    match.group(1) if match else None
                )
            ):
                raise SourceEvidenceIntegrityError(
                    "Source Evidence directory contains an "
                    f"unexpected entry: {entry}."
                )

            result.append(
                self.load_source_evidence(
                    project_id,
                    match.group(1),
                )
            )

        self._require_unique_evidence(tuple(result))

        return tuple(
            evidence
            for evidence in result
            if (
                (
                    source_id is None
                    or evidence.source_id == source_id
                )
                and (
                    source_projection_id is None
                    or evidence.source_projection_id
                    == source_projection_id
                )
            )
        )

    def source_evidence_directory_path(
        self,
        project_id: str,
    ) -> Path:
        """Return the project-local Source Evidence directory."""

        self._workspace.load_project(project_id)
        project_path = self.root / project_id
        semantics_path = project_path / SEMANTICS_DIRECTORY_NAME
        evidence_path = semantics_path / SOURCE_EVIDENCE_DIRECTORY_NAME

        if semantics_path.is_symlink():
            raise UnsafeSourceEvidencePathError(
                "Semantic artifact directory must not be a "
                f"symbolic link: {semantics_path}."
            )
        if semantics_path.exists() and not semantics_path.is_dir():
            raise UnsafeSourceEvidencePathError(
                "Semantic artifact path must be a directory: "
                f"{semantics_path}."
            )
        if evidence_path.is_symlink():
            raise UnsafeSourceEvidencePathError(
                "Source Evidence directory must not be a "
                f"symbolic link: {evidence_path}."
            )

        return evidence_path

    def source_evidence_path(
        self,
        project_id: str,
        source_evidence_id: str,
    ) -> Path:
        """Return the validated path of one Source Evidence object."""

        validated_id = validate_source_evidence_id(source_evidence_id)
        return (
            self.source_evidence_directory_path(project_id)
            / f"{validated_id}.json"
        )

    def _validate_references(
        self,
        evidence: SourceEvidence,
    ) -> None:
        projection = self._load_projection(
            evidence.project_id,
            evidence.source_projection_id,
        )
        manifest = projection.manifest

        if manifest.project_id != evidence.project_id:
            raise SourceEvidenceReferenceError(
                "Source Projection belongs to a different project."
            )
        if manifest.source_role != ENGINEERING_SOURCE_ROLE:
            raise SourceEvidenceReferenceError(
                "Only engineering_source may provide positive Source Evidence."
            )
        if manifest.source_id != evidence.source_id:
            raise SourceEvidenceReferenceError(
                "Source Projection belongs to a different source."
            )
        if (
            manifest.projection_fingerprint
            != evidence.source_projection_fingerprint
        ):
            raise SourceEvidenceReferenceError(
                "Source Evidence is bound to a different "
                "Source Projection fingerprint."
            )
        if manifest.projection_result == "unavailable":
            raise UnavailableSourceEvidenceProjectionError(
                "An unavailable Source Projection cannot back "
                "Source Evidence."
            )

        self._validate_source_anchors(evidence, projection)

    def _validate_source_anchors(
        self,
        evidence: SourceEvidence,
        projection: SourceProjectionArtifact,
    ) -> None:
        segment_by_id = {
            segment.segment_id: segment
            for segment in projection.manifest.segments
        }
        selected_text: list[str] = []

        for anchor in evidence.source_anchors:
            segment = segment_by_id.get(anchor.segment_id)
            if segment is None:
                raise SourceEvidenceAnchorError(
                    "Source Evidence references unknown segment "
                    f"{anchor.segment_id}."
                )

            segment_text = projection.content[
                segment.start_offset:segment.end_offset
            ]
            if anchor.end_offset > len(segment_text):
                raise SourceEvidenceAnchorError(
                    "Source Evidence anchor exceeds segment "
                    f"{anchor.segment_id}."
                )

            selected_text.append(
                segment_text[
                    anchor.start_offset:anchor.end_offset
                ]
            )

        if evidence.source_excerpt != "".join(selected_text):
            raise SourceEvidenceAnchorError(
                "source_excerpt does not equal the unchanged "
                "concatenation of Source Projection anchors."
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
            raise SourceEvidenceReferenceError(
                "Unable to resolve Source Projection "
                f"{project_id}/{source_projection_id}: {exc}"
            ) from exc

        if not isinstance(projection, SourceProjectionArtifact):
            raise SourceEvidenceReferenceError(
                "Source Projection Repository returned an "
                "unexpected artifact type."
            )

        return projection

    def _publish_source_evidence(
        self,
        evidence: SourceEvidence,
    ) -> None:
        path = self.source_evidence_path(
            evidence.project_id,
            evidence.source_evidence_id,
        )
        self._ensure_evidence_directory(path.parent)

        if path.exists() or path.is_symlink():
            raise SourceEvidencePersistenceError(
                "Source Evidence already exists and must not be "
                f"overwritten: {path}."
            )

        temporary_path = path.with_name(f".{path.name}.tmp")
        if temporary_path.exists() or temporary_path.is_symlink():
            raise SourceEvidencePersistenceError(
                "Temporary Source Evidence path already exists: "
                f"{temporary_path}."
            )

        serialized = source_evidence_to_json(evidence)

        try:
            with temporary_path.open("x", encoding="utf-8") as handle:
                handle.write(serialized)

            persisted = source_evidence_from_json(
                temporary_path.read_text(encoding="utf-8"),
                expected_project_id=evidence.project_id,
                expected_source_evidence_id=evidence.source_evidence_id,
            )
            if persisted != evidence:
                raise SourceEvidenceIntegrityError(
                    "Persisted Source Evidence differs from "
                    "the validated artifact."
                )

            try:
                os.link(temporary_path, path)
            except OSError as exc:
                if exc.errno == errno.EEXIST:
                    raise SourceEvidencePersistenceError(
                        "Source Evidence appeared during publication "
                        f"and was not overwritten: {path}."
                    ) from exc
                raise SourceEvidencePersistenceError(
                    f"Unable to publish Source Evidence {path}: {exc}"
                ) from exc
        finally:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError as exc:
                raise SourceEvidencePersistenceError(
                    "Unable to remove temporary Source Evidence "
                    f"file {temporary_path}: {exc}"
                ) from exc

    def _ensure_evidence_directory(
        self,
        evidence_path: Path,
    ) -> None:
        project_path = evidence_path.parent.parent
        semantics_path = evidence_path.parent

        if project_path.is_symlink():
            raise UnsafeSourceEvidencePathError(
                f"Project path must not be a symbolic link: {project_path}."
            )
        if semantics_path.is_symlink():
            raise UnsafeSourceEvidencePathError(
                "Semantic artifact directory must not be a "
                f"symbolic link: {semantics_path}."
            )
        if semantics_path.exists() and not semantics_path.is_dir():
            raise UnsafeSourceEvidencePathError(
                "Semantic artifact path must be a directory: "
                f"{semantics_path}."
            )

        try:
            semantics_path.mkdir(exist_ok=True)
        except OSError as exc:
            raise SourceEvidencePersistenceError(
                "Unable to create semantic artifact directory "
                f"{semantics_path}: {exc}"
            ) from exc

        if evidence_path.is_symlink():
            raise UnsafeSourceEvidencePathError(
                "Source Evidence directory must not be a "
                f"symbolic link: {evidence_path}."
            )
        if evidence_path.exists() and not evidence_path.is_dir():
            raise UnsafeSourceEvidencePathError(
                "Source Evidence path must be a directory: "
                f"{evidence_path}."
            )

        try:
            evidence_path.mkdir(exist_ok=True)
        except OSError as exc:
            raise SourceEvidencePersistenceError(
                "Unable to create Source Evidence directory "
                f"{evidence_path}: {exc}"
            ) from exc

    def _require_safe_directory(
        self,
        path: Path,
    ) -> None:
        if path.is_symlink() or not path.is_dir():
            raise UnsafeSourceEvidencePathError(
                "Source Evidence path must be a regular directory: "
                f"{path}."
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
            raise UnsafeSourceEvidencePathError(
                "Source Evidence path must be a regular file: "
                f"{path}."
            )

    def _require_unique_evidence(
        self,
        evidence_items: tuple[SourceEvidence, ...],
    ) -> None:
        fingerprints: dict[str, str] = {}

        for evidence in evidence_items:
            existing_id = fingerprints.get(evidence.content_fingerprint)
            if existing_id is not None:
                raise SourceEvidenceIntegrityError(
                    "Source Evidence content fingerprint is shared "
                    f"by {existing_id} and {evidence.source_evidence_id}."
                )
            fingerprints[
                evidence.content_fingerprint
            ] = evidence.source_evidence_id

    def _current_utc_timestamp(self) -> str:
        value = self._clock()
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        value = value.astimezone(timezone.utc)
        return value.isoformat().replace("+00:00", "Z")
