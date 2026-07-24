"""Project-isolated persistence for framework-assignment candidates."""

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

from .analyzer import FrameworkAssignmentConsensusResult
from .candidate_manifest import (
    create_framework_assignment_candidate,
    framework_assignment_candidate_from_json,
    framework_assignment_candidate_to_json,
)
from .errors import (
    DuplicateFrameworkAssignmentCandidateError,
    FrameworkAssignmentIntegrityError,
    FrameworkAssignmentPersistenceError,
    FrameworkAssignmentReferenceError,
    FrameworkAssignmentValidationError,
)
from .identifiers import (
    next_framework_assignment_candidate_id,
    validate_framework_assignment_candidate_id,
)
from .types import (
    FrameworkAssignmentCandidate,
    FrameworkAssignmentConsensusOutcome,
    FrameworkAssignmentIssue,
    FrameworkAssignmentScanResult,
)


SEMANTICS_DIRECTORY_NAME = "semantics"
FRAMEWORK_ASSIGNMENTS_DIRECTORY_NAME = (
    "framework_assignments"
)

_CANDIDATE_FILE_PATTERN = re.compile(
    r"^(FAC-[0-9]{6})\.json$"
)


def _default_clock() -> datetime:
    return datetime.now(timezone.utc)


class FrameworkAssignmentRepository:
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
        consensus_result: FrameworkAssignmentConsensusResult,
        outcome: FrameworkAssignmentConsensusOutcome,
    ) -> FrameworkAssignmentCandidate:
        """Validate and atomically persist one consensus candidate."""

        if not isinstance(
            consensus_result,
            FrameworkAssignmentConsensusResult,
        ):
            raise FrameworkAssignmentValidationError(
                "consensus_result must be a "
                "FrameworkAssignmentConsensusResult."
            )
        if not isinstance(
            outcome,
            FrameworkAssignmentConsensusOutcome,
        ):
            raise FrameworkAssignmentValidationError(
                "outcome must be a "
                "FrameworkAssignmentConsensusOutcome."
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
        candidate_id = next_framework_assignment_candidate_id(
            candidate.framework_assignment_candidate_id
            for candidate in existing
        )
        candidate = create_framework_assignment_candidate(
            consensus_result=consensus_result,
            outcome=outcome,
            framework_assignment_candidate_id=candidate_id,
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
            raise DuplicateFrameworkAssignmentCandidateError(
                "Equivalent framework-assignment content already "
                "exists as "
                f"{duplicate.framework_assignment_candidate_id}."
            )

        self._publish(candidate)
        return self.load_candidate(
            candidate.project_id,
            candidate.framework_assignment_candidate_id,
        )

    def load_candidate(
        self,
        project_id: str,
        framework_assignment_candidate_id: str,
    ) -> FrameworkAssignmentCandidate:
        """Load and validate one persisted candidate."""

        path = self.candidate_path(
            project_id,
            framework_assignment_candidate_id,
        )
        if not path.is_file() or path.is_symlink():
            raise FrameworkAssignmentReferenceError(
                "Framework Assignment Candidate does not exist: "
                f"{framework_assignment_candidate_id!r}."
            )
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise FrameworkAssignmentPersistenceError(
                f"Unable to read mapping candidate: {path}."
            ) from exc
        candidate = framework_assignment_candidate_from_json(
            text,
            expected_project_id=project_id,
            expected_framework_assignment_candidate_id=(
                framework_assignment_candidate_id
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
    ) -> tuple[FrameworkAssignmentCandidate, ...]:
        """List fully valid candidates in identifier order."""

        directory = self._mapping_directory(project_id)
        if not directory.exists():
            return ()
        self._reject_symlink(
            directory,
            "Framework assignments directory",
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
    ) -> FrameworkAssignmentScanResult:
        """Return valid candidates and deterministic diagnostics."""

        try:
            directory = self._mapping_directory(project_id)
        except FrameworkAssignmentPersistenceError as exc:
            directory = (
                self.root
                / project_id
                / SEMANTICS_DIRECTORY_NAME
                / FRAMEWORK_ASSIGNMENTS_DIRECTORY_NAME
            )
            return FrameworkAssignmentScanResult(
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
            return FrameworkAssignmentScanResult()
        if directory.is_symlink() or not directory.is_dir():
            return FrameworkAssignmentScanResult(
                issues=(
                    self._issue(
                        project_id,
                        "unsafe_mapping_directory",
                        "Framework assignments path is not a safe "
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
                        "Unexpected entry in framework assignments "
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
        return FrameworkAssignmentScanResult(
            candidates=tuple(candidates),
            issues=tuple(issues),
        )

    def candidate_path(
        self,
        project_id: str,
        framework_assignment_candidate_id: str,
    ) -> Path:
        """Return the validated path for one candidate."""

        candidate_id = validate_framework_assignment_candidate_id(
            framework_assignment_candidate_id
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
            semantics / FRAMEWORK_ASSIGNMENTS_DIRECTORY_NAME
        )
        self._assert_within(directory, semantics)
        self._reject_symlink(
            directory,
            "Framework assignments directory",
        )
        return directory

    def _publish(
        self,
        candidate: FrameworkAssignmentCandidate,
    ) -> None:
        path = self.candidate_path(
            candidate.project_id,
            candidate.framework_assignment_candidate_id,
        )
        self._ensure_directory(path.parent)
        serialized = framework_assignment_candidate_to_json(
            candidate
        )
        temporary = path.with_name(f".{path.name}.tmp")
        if (
            path.exists()
            or path.is_symlink()
            or temporary.exists()
            or temporary.is_symlink()
        ):
            raise FrameworkAssignmentPersistenceError(
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
            reloaded = framework_assignment_candidate_from_json(
                temporary.read_text(encoding="utf-8"),
                expected_project_id=candidate.project_id,
                expected_framework_assignment_candidate_id=(
                    candidate.framework_assignment_candidate_id
                ),
            )
            if reloaded != candidate:
                raise FrameworkAssignmentIntegrityError(
                    "Temporary candidate does not round-trip."
                )
            try:
                os.link(temporary, path)
            except OSError as exc:
                if exc.errno == errno.EEXIST:
                    raise FrameworkAssignmentPersistenceError(
                        "Candidate appeared during publication."
                    ) from exc
                raise
        except FrameworkAssignmentPersistenceError:
            raise
        except Exception as exc:
            raise FrameworkAssignmentPersistenceError(
                f"Unable to publish mapping candidate: {path}."
            ) from exc
        finally:
            if temporary.exists() and not temporary.is_symlink():
                temporary.unlink()

    def _validate_consensus_information_unit(
        self,
        result: FrameworkAssignmentConsensusResult,
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
                raise FrameworkAssignmentReferenceError(
                    "Consensus result and Information Unit "
                    f"disagree on {field_name}."
                )

    def _validate_candidate_information_unit(
        self,
        candidate: FrameworkAssignmentCandidate,
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
                raise FrameworkAssignmentReferenceError(
                    "Framework Assignment Candidate and Information "
                    "Unit "
                    f"disagree on {field_name}."
                )
        for proposal in candidate.proposals:
            if not any(
                basis.basis_type == "information_unit"
                and basis.reference_id
                == information_unit.information_unit_id
                and basis.reference_version
                == information_unit.content_fingerprint
                for basis in proposal.assignment_bases
            ):
                raise FrameworkAssignmentReferenceError(
                    "Framework Assignment Candidate does not bind "
                    "the exact Information Unit content fingerprint."
                )

    def _ensure_directory(self, path: Path) -> None:
        self._reject_symlink(path, "Candidate directory")
        try:
            path.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise FrameworkAssignmentPersistenceError(
                f"Unable to create candidate directory: {path}."
            ) from exc
        self._reject_symlink(path, "Candidate directory")
        if not path.is_dir():
            raise FrameworkAssignmentPersistenceError(
                f"Candidate directory is not a directory: {path}."
            )

    def _assert_within(self, path: Path, parent: Path) -> None:
        try:
            path.absolute().relative_to(parent.absolute())
        except ValueError as exc:
            raise FrameworkAssignmentPersistenceError(
                f"Unsafe mapping path outside repository: {path}."
            ) from exc

    def _reject_symlink(self, path: Path, label: str) -> None:
        if path.is_symlink():
            raise FrameworkAssignmentPersistenceError(
                f"{label} must not be a symbolic link: {path}."
            )

    def _timestamp(self) -> str:
        value = self._clock()
        if not isinstance(value, datetime):
            raise FrameworkAssignmentPersistenceError(
                "clock must return datetime."
            )
        if value.tzinfo is None or value.utcoffset() is None:
            raise FrameworkAssignmentPersistenceError(
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
    ) -> FrameworkAssignmentIssue:
        return FrameworkAssignmentIssue(
            project_id=project_id,
            code=code,
            message=message,
            issue_level="blocking",
            path=path,
            framework_assignment_candidate_id=candidate_id,
        )