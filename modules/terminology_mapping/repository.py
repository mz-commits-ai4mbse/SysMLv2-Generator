"""Project-isolated persistence for terminology mapping candidates."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
import errno
import os
from pathlib import Path
import re
from typing import Any

from modules.information_units.repository import (
    InformationUnitRepository,
)
from modules.project_workspace import ProjectWorkspace
from modules.project_workspace.workspace import (
    DEFAULT_PROJECTS_ROOT,
)

from .analyzer import TerminologyMappingConsensusResult
from .candidate_manifest import (
    create_terminology_mapping_candidate,
    terminology_mapping_candidate_from_json,
    terminology_mapping_candidate_to_json,
)
from .errors import (
    DuplicateTerminologyMappingCandidateError,
    TerminologyMappingIntegrityError,
    TerminologyMappingPersistenceError,
    TerminologyMappingReferenceError,
    TerminologyMappingValidationError,
)
from .identifiers import (
    next_terminology_mapping_candidate_id,
    validate_terminology_mapping_candidate_id,
)
from .types import (
    TerminologyMappingCandidate,
    TerminologyMappingConsensusOutcome,
    TerminologyMappingIssue,
    TerminologyMappingScanResult,
)


SEMANTICS_DIRECTORY_NAME = "semantics"
TERMINOLOGY_MAPPINGS_DIRECTORY_NAME = (
    "terminology_mappings"
)

_CANDIDATE_FILE_PATTERN = re.compile(
    r"^(TMC-[0-9]{6})\.json$"
)


def _default_clock() -> datetime:
    return datetime.now(timezone.utc)


class TerminologyMappingRepository:
    """Create and inspect immutable non-authoritative candidates."""

    def __init__(
        self,
        root: Path | str = DEFAULT_PROJECTS_ROOT,
        *,
        clock: Callable[[], datetime] = _default_clock,
        information_unit_repository: (
            InformationUnitRepository | None
        ) = None,
    ) -> None:
        self.root = Path(root)
        self._clock = clock
        self._workspace = ProjectWorkspace(
            root=self.root,
            clock=clock,
        )
        self._information_units = (
            InformationUnitRepository(
                root=self.root,
                clock=clock,
            )
            if information_unit_repository is None
            else information_unit_repository
        )

    def create_candidate(
        self,
        consensus_result: TerminologyMappingConsensusResult,
        outcome: TerminologyMappingConsensusOutcome,
    ) -> TerminologyMappingCandidate:
        """Validate and atomically persist one consensus candidate."""

        if not isinstance(
            consensus_result,
            TerminologyMappingConsensusResult,
        ):
            raise TerminologyMappingValidationError(
                "consensus_result must be a "
                "TerminologyMappingConsensusResult."
            )
        if not isinstance(
            outcome,
            TerminologyMappingConsensusOutcome,
        ):
            raise TerminologyMappingValidationError(
                "outcome must be a "
                "TerminologyMappingConsensusOutcome."
            )
        information_unit = self._information_units.load_information_unit(
            consensus_result.project_id,
            consensus_result.information_unit_id,
        )
        self._validate_consensus_information_unit(
            consensus_result,
            information_unit,
        )

        existing = self.list_candidates(
            consensus_result.project_id
        )
        candidate_id = next_terminology_mapping_candidate_id(
            candidate.terminology_mapping_candidate_id
            for candidate in existing
        )
        candidate = create_terminology_mapping_candidate(
            consensus_result=consensus_result,
            outcome=outcome,
            terminology_mapping_candidate_id=candidate_id,
            timestamp=self._timestamp(),
        )
        self._validate_candidate_information_unit(
            candidate,
            information_unit,
        )

        duplicate = next(
            (
                existing_candidate
                for existing_candidate in existing
                if existing_candidate.content_fingerprint
                == candidate.content_fingerprint
            ),
            None,
        )
        if duplicate is not None:
            raise DuplicateTerminologyMappingCandidateError(
                "Equivalent terminology mapping content already "
                "exists as "
                f"{duplicate.terminology_mapping_candidate_id}."
            )

        self._publish(candidate)
        return self.load_candidate(
            candidate.project_id,
            candidate.terminology_mapping_candidate_id,
        )

    def load_candidate(
        self,
        project_id: str,
        terminology_mapping_candidate_id: str,
    ) -> TerminologyMappingCandidate:
        """Load and validate one persisted candidate."""

        path = self.candidate_path(
            project_id,
            terminology_mapping_candidate_id,
        )
        if not path.is_file() or path.is_symlink():
            raise TerminologyMappingReferenceError(
                "Terminology Mapping Candidate does not exist: "
                f"{terminology_mapping_candidate_id!r}."
            )
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise TerminologyMappingPersistenceError(
                f"Unable to read mapping candidate: {path}."
            ) from exc
        candidate = terminology_mapping_candidate_from_json(
            text,
            expected_project_id=project_id,
            expected_terminology_mapping_candidate_id=(
                terminology_mapping_candidate_id
            ),
        )
        information_unit = self._information_units.load_information_unit(
            project_id,
            candidate.information_unit_id,
        )
        self._validate_candidate_information_unit(
            candidate,
            information_unit,
        )
        return candidate

    def list_candidates(
        self,
        project_id: str,
        *,
        information_unit_id: str | None = None,
    ) -> tuple[TerminologyMappingCandidate, ...]:
        """List fully valid candidates in identifier order."""

        directory = self._mapping_directory(project_id)
        if not directory.exists():
            return ()
        self._reject_symlink(
            directory,
            "Terminology mappings directory",
        )
        candidates = []
        for path in sorted(directory.iterdir()):
            match = _CANDIDATE_FILE_PATTERN.fullmatch(path.name)
            if match is None:
                continue
            candidate = self.load_candidate(
                project_id,
                match.group(1),
            )
            if (
                information_unit_id is None
                or candidate.information_unit_id
                == information_unit_id
            ):
                candidates.append(candidate)
        return tuple(candidates)

    def scan_candidates(
        self,
        project_id: str,
    ) -> TerminologyMappingScanResult:
        """Return valid candidates and deterministic diagnostics."""

        try:
            directory = self._mapping_directory(project_id)
        except TerminologyMappingPersistenceError as exc:
            directory = (
                self.root
                / project_id
                / SEMANTICS_DIRECTORY_NAME
                / TERMINOLOGY_MAPPINGS_DIRECTORY_NAME
            )
            return TerminologyMappingScanResult(
                issues=(
                    self._issue(
                        project_id,
                        "unsafe_mapping_directory",
                        str(exc),
                        directory,
                    ),
                )
            )
        if not directory.exists():
            return TerminologyMappingScanResult()
        if directory.is_symlink() or not directory.is_dir():
            return TerminologyMappingScanResult(
                issues=(
                    self._issue(
                        project_id,
                        "unsafe_mapping_directory",
                        "Terminology mappings path is not a safe "
                        "directory.",
                        directory,
                    ),
                )
            )

        candidates = []
        issues = []
        for path in sorted(directory.iterdir()):
            match = _CANDIDATE_FILE_PATTERN.fullmatch(path.name)
            if match is None:
                issues.append(
                    self._issue(
                        project_id,
                        "unexpected_mapping_entry",
                        "Unexpected entry in terminology mappings "
                        "directory.",
                        path,
                    )
                )
                continue
            candidate_id = match.group(1)
            try:
                candidates.append(
                    self.load_candidate(
                        project_id,
                        candidate_id,
                    )
                )
            except Exception as exc:
                issues.append(
                    self._issue(
                        project_id,
                        "invalid_mapping_candidate",
                        str(exc),
                        path,
                        candidate_id,
                    )
                )
        return TerminologyMappingScanResult(
            candidates=tuple(candidates),
            issues=tuple(issues),
        )

    def candidate_path(
        self,
        project_id: str,
        terminology_mapping_candidate_id: str,
    ) -> Path:
        """Return the validated path for one candidate."""

        candidate_id = validate_terminology_mapping_candidate_id(
            terminology_mapping_candidate_id
        )
        directory = self._mapping_directory(project_id)
        path = directory / f"{candidate_id}.json"
        self._assert_within(path, directory)
        self._reject_symlink(path, "Mapping candidate file")
        return path

    def _mapping_directory(self, project_id: str) -> Path:
        project = self._workspace.load_project(project_id)
        project_path = self.root / project.project_id
        self._assert_within(project_path, self.root)
        self._reject_symlink(project_path, "Project directory")
        semantics = project_path / SEMANTICS_DIRECTORY_NAME
        self._assert_within(semantics, project_path)
        self._reject_symlink(semantics, "Semantics directory")
        directory = (
            semantics / TERMINOLOGY_MAPPINGS_DIRECTORY_NAME
        )
        self._assert_within(directory, semantics)
        self._reject_symlink(
            directory,
            "Terminology mappings directory",
        )
        return directory

    def _publish(
        self,
        candidate: TerminologyMappingCandidate,
    ) -> None:
        path = self.candidate_path(
            candidate.project_id,
            candidate.terminology_mapping_candidate_id,
        )
        self._ensure_directory(path.parent)
        serialized = terminology_mapping_candidate_to_json(
            candidate
        )
        temporary = path.with_name(f".{path.name}.tmp")
        if (
            path.exists()
            or path.is_symlink()
            or temporary.exists()
            or temporary.is_symlink()
        ):
            raise TerminologyMappingPersistenceError(
                "Candidate or temporary publication path already "
                "exists."
            )
        try:
            with temporary.open(
                "x",
                encoding="utf-8",
                newline="\n",
            ) as handle:
                handle.write(serialized)
                handle.flush()
                os.fsync(handle.fileno())
            reloaded = terminology_mapping_candidate_from_json(
                temporary.read_text(encoding="utf-8"),
                expected_project_id=candidate.project_id,
                expected_terminology_mapping_candidate_id=(
                    candidate.terminology_mapping_candidate_id
                ),
            )
            if reloaded != candidate:
                raise TerminologyMappingIntegrityError(
                    "Temporary candidate does not round-trip."
                )
            try:
                os.link(temporary, path)
            except OSError as exc:
                if exc.errno == errno.EEXIST:
                    raise TerminologyMappingPersistenceError(
                        "Candidate appeared during publication."
                    ) from exc
                raise
        except TerminologyMappingPersistenceError:
            raise
        except Exception as exc:
            raise TerminologyMappingPersistenceError(
                f"Unable to publish mapping candidate: {path}."
            ) from exc
        finally:
            if temporary.exists() and not temporary.is_symlink():
                temporary.unlink()

    def _validate_consensus_information_unit(
        self,
        result: TerminologyMappingConsensusResult,
        information_unit: Any,
    ) -> None:
        for field_name in (
            "project_id",
            "source_id",
            "source_projection_id",
            "information_unit_id",
        ):
            if getattr(result, field_name) != getattr(
                information_unit,
                field_name,
            ):
                raise TerminologyMappingReferenceError(
                    "Consensus result and Information Unit "
                    f"disagree on {field_name}."
                )

    def _validate_candidate_information_unit(
        self,
        candidate: TerminologyMappingCandidate,
        information_unit: Any,
    ) -> None:
        for field_name in (
            "project_id",
            "source_id",
            "source_projection_id",
            "information_unit_id",
        ):
            if getattr(candidate, field_name) != getattr(
                information_unit,
                field_name,
            ):
                raise TerminologyMappingReferenceError(
                    "Mapping candidate and Information Unit "
                    f"disagree on {field_name}."
                )
        occurrence = candidate.occurrence
        text = getattr(
            information_unit,
            occurrence.text_field,
        )
        if (
            occurrence.end_offset > len(text)
            or text[
                occurrence.start_offset : occurrence.end_offset
            ]
            != occurrence.term_text
        ):
            raise TerminologyMappingReferenceError(
                "Candidate occurrence does not match Information "
                "Unit content."
            )

    def _ensure_directory(self, path: Path) -> None:
        self._reject_symlink(path, "Candidate directory")
        try:
            path.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise TerminologyMappingPersistenceError(
                f"Unable to create candidate directory: {path}."
            ) from exc
        self._reject_symlink(path, "Candidate directory")
        if not path.is_dir():
            raise TerminologyMappingPersistenceError(
                f"Candidate directory is not a directory: {path}."
            )

    def _assert_within(self, path: Path, parent: Path) -> None:
        try:
            path.absolute().relative_to(parent.absolute())
        except ValueError as exc:
            raise TerminologyMappingPersistenceError(
                f"Unsafe mapping path outside repository: {path}."
            ) from exc

    def _reject_symlink(self, path: Path, label: str) -> None:
        if path.is_symlink():
            raise TerminologyMappingPersistenceError(
                f"{label} must not be a symbolic link: {path}."
            )

    def _timestamp(self) -> str:
        value = self._clock()
        if not isinstance(value, datetime):
            raise TerminologyMappingPersistenceError(
                "clock must return datetime."
            )
        if value.tzinfo is None or value.utcoffset() is None:
            raise TerminologyMappingPersistenceError(
                "clock must return timezone-aware datetime."
            )
        return (
            value.astimezone(timezone.utc)
            .isoformat(timespec="seconds")
            .replace("+00:00", "Z")
        )

    def _issue(
        self,
        project_id: str,
        code: str,
        message: str,
        path: Path,
        candidate_id: str | None = None,
    ) -> TerminologyMappingIssue:
        return TerminologyMappingIssue(
            project_id=project_id,
            code=code,
            message=message,
            issue_level="blocking",
            path=path,
            terminology_mapping_candidate_id=candidate_id,
        )