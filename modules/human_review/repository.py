"""Project-isolated persistence and gates for Human Review Decisions."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
import errno
import os
from pathlib import Path
import re

from modules.project_workspace import ProjectWorkspace
from modules.project_workspace.workspace import DEFAULT_PROJECTS_ROOT

from .errors import (
    DuplicateHumanReviewDecisionError,
    HumanReviewIntegrityError,
    HumanReviewPersistenceError,
    HumanReviewReferenceError,
    HumanReviewValidationError,
)
from .identifiers import (
    next_human_review_decision_id,
    validate_human_review_decision_id,
)
from .manifest import (
    create_human_review_decision,
    human_review_decision_from_json,
    human_review_decision_to_json,
)
from .types import (
    HUMAN_REVIEW_TARGET_TYPES,
    HumanReviewDecision,
    HumanReviewIssue,
    HumanReviewScanResult,
    HumanReviewTargetSnapshot,
)


SEMANTICS_DIRECTORY_NAME = "semantics"
HUMAN_REVIEWS_DIRECTORY_NAME = "human_reviews"

_DECISION_FILE_PATTERN = re.compile(r"^(HRD-[0-9]{6})\.json$")
_TARGET_ID_PATTERNS = {
    "information_unit_publication": re.compile(r"^IU-[0-9]{6}$"),
    "terminology_mapping_candidate": re.compile(r"^TMC-[0-9]{6}$"),
    "framework_assignment_candidate": re.compile(r"^FAC-[0-9]{6}$"),
    "review_document_finalization": re.compile(r"^RVV-[0-9]{6}$"),
}
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def _default_clock() -> datetime:
    return datetime.now(timezone.utc)


class HumanReviewRepository:
    """Persist immutable decisions and enforce exact confirmation gates."""

    def __init__(
        self,
        root: Path | str = DEFAULT_PROJECTS_ROOT,
        *,
        clock: Callable[[], datetime] = _default_clock,
    ) -> None:
        self.root = Path(root)
        self._clock = clock
        self._workspace = ProjectWorkspace(root=self.root, clock=clock)

    def record_decision(
        self,
        project_id: str,
        target: HumanReviewTargetSnapshot,
        *,
        review_mode: str,
        decision: str,
        reviewer_identity: str,
        rationale: str | None = None,
    ) -> HumanReviewDecision:
        """Create and atomically persist one immutable human decision."""

        if not isinstance(target, HumanReviewTargetSnapshot):
            raise HumanReviewValidationError(
                "target must be a HumanReviewTargetSnapshot."
            )
        existing = self.list_decisions(project_id)
        decision_id = next_human_review_decision_id(
            item.human_review_decision_id for item in existing
        )
        item = create_human_review_decision(
            project_id=project_id,
            human_review_decision_id=decision_id,
            target=target,
            review_mode=review_mode,
            decision=decision,
            reviewer_identity=reviewer_identity,
            rationale=rationale,
            timestamp=self._timestamp(),
        )
        duplicate = next(
            (
                saved
                for saved in existing
                if saved.decision_fingerprint
                == item.decision_fingerprint
            ),
            None,
        )
        if duplicate is not None:
            raise DuplicateHumanReviewDecisionError(
                "Equivalent Human Review Decision already exists as "
                f"{duplicate.human_review_decision_id}."
            )
        self._publish(item)
        return self.load_decision(project_id, decision_id)

    def load_decision(
        self,
        project_id: str,
        human_review_decision_id: str,
    ) -> HumanReviewDecision:
        """Load and strictly validate one persisted decision."""

        path = self.decision_path(
            project_id,
            human_review_decision_id,
        )
        if not path.is_file() or path.is_symlink():
            raise HumanReviewReferenceError(
                "Human Review Decision does not exist: "
                f"{human_review_decision_id!r}."
            )
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise HumanReviewPersistenceError(
                f"Unable to read Human Review Decision: {path}."
            ) from exc
        return human_review_decision_from_json(
            text,
            expected_project_id=project_id,
            expected_human_review_decision_id=(
                human_review_decision_id
            ),
        )

    def list_decisions(
        self,
        project_id: str,
        *,
        target_type: str | None = None,
        target_id: str | None = None,
    ) -> tuple[HumanReviewDecision, ...]:
        """List valid decisions in identifier order with optional filters."""

        self._validate_filters(target_type, target_id)
        directory = self._review_directory(project_id)
        if not directory.exists():
            return ()
        self._reject_symlink(directory, "Human reviews directory")
        if not directory.is_dir():
            raise HumanReviewPersistenceError(
                "Human reviews path is not a directory."
            )
        decisions = []
        for path in sorted(directory.iterdir()):
            match = _DECISION_FILE_PATTERN.fullmatch(path.name)
            if match is None:
                continue
            item = self.load_decision(project_id, match.group(1))
            if (
                target_type is not None
                and item.target.target_type != target_type
            ):
                continue
            if (
                target_id is not None
                and item.target.target_id != target_id
            ):
                continue
            decisions.append(item)
        return tuple(decisions)

    def scan_decisions(
        self,
        project_id: str,
    ) -> HumanReviewScanResult:
        """Return valid decisions and deterministic blocking diagnostics."""

        try:
            directory = self._review_directory(project_id)
        except Exception as exc:
            directory = (
                self.root
                / project_id
                / SEMANTICS_DIRECTORY_NAME
                / HUMAN_REVIEWS_DIRECTORY_NAME
            )
            return HumanReviewScanResult(
                issues=(
                    self._issue(
                        project_id,
                        "unsafe_review_directory",
                        str(exc),
                        directory,
                    ),
                )
            )
        if not directory.exists():
            return HumanReviewScanResult()
        if directory.is_symlink() or not directory.is_dir():
            return HumanReviewScanResult(
                issues=(
                    self._issue(
                        project_id,
                        "unsafe_review_directory",
                        "Human reviews path is not a safe directory.",
                        directory,
                    ),
                )
            )
        decisions = []
        issues = []
        for path in sorted(directory.iterdir()):
            match = _DECISION_FILE_PATTERN.fullmatch(path.name)
            if match is None:
                issues.append(
                    self._issue(
                        project_id,
                        "unexpected_review_entry",
                        "Unexpected entry in human reviews directory.",
                        path,
                    )
                )
                continue
            decision_id = match.group(1)
            try:
                decisions.append(
                    self.load_decision(project_id, decision_id)
                )
            except Exception as exc:
                issues.append(
                    self._issue(
                        project_id,
                        "invalid_review_decision",
                        str(exc),
                        path,
                        decision_id,
                    )
                )
        return HumanReviewScanResult(
            decisions=tuple(decisions),
            issues=tuple(issues),
        )

    def require_confirmation(
        self,
        project_id: str,
        *,
        target_type: str,
        target_id: str,
        target_content_fingerprint: str,
        reference_validation_fingerprint: str | None,
    ) -> HumanReviewDecision:
        """Return the latest exact confirmation or block publication."""

        self._validate_target_reference(
            target_type,
            target_id,
            target_content_fingerprint,
            reference_validation_fingerprint,
        )
        candidates = self.list_decisions(
            project_id,
            target_type=target_type,
            target_id=target_id,
        )
        exact = tuple(
            item
            for item in candidates
            if item.target.target_content_fingerprint
            == target_content_fingerprint
            and item.target.reference_validation_fingerprint
            == reference_validation_fingerprint
        )
        if not exact:
            raise HumanReviewReferenceError(
                "No Human Review Decision binds the exact target and "
                "reference-validation fingerprints."
            )
        latest = exact[-1]
        if latest.decision != "confirm":
            raise HumanReviewIntegrityError(
                "The latest exact Human Review Decision does not "
                "confirm publication."
            )
        if latest.target.reference_validation_status == "invalid":
            raise HumanReviewIntegrityError(
                "A reference-invalid target cannot pass publication."
            )
        return latest

    def decision_path(
        self,
        project_id: str,
        human_review_decision_id: str,
    ) -> Path:
        """Return the safe path for one decision."""

        decision_id = validate_human_review_decision_id(
            human_review_decision_id
        )
        directory = self._review_directory(project_id)
        path = directory / f"{decision_id}.json"
        self._assert_within(path, directory)
        self._reject_symlink(path, "Human Review Decision file")
        return path

    def _review_directory(self, project_id: str) -> Path:
        project = self._workspace.load_project(project_id)
        project_path = self.root / project.project_id
        self._assert_within(project_path, self.root)
        self._reject_symlink(project_path, "Project directory")
        semantics = project_path / SEMANTICS_DIRECTORY_NAME
        self._assert_within(semantics, project_path)
        self._reject_symlink(semantics, "Semantics directory")
        directory = semantics / HUMAN_REVIEWS_DIRECTORY_NAME
        self._assert_within(directory, semantics)
        self._reject_symlink(directory, "Human reviews directory")
        return directory

    def _publish(self, item: HumanReviewDecision) -> None:
        path = self.decision_path(
            item.project_id,
            item.human_review_decision_id,
        )
        self._ensure_directory(path.parent)
        serialized = human_review_decision_to_json(item)
        temporary = path.with_name(f".{path.name}.tmp")
        if (
            path.exists()
            or path.is_symlink()
            or temporary.exists()
            or temporary.is_symlink()
        ):
            raise HumanReviewPersistenceError(
                "Decision or temporary publication path already exists."
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
            reloaded = human_review_decision_from_json(
                temporary.read_text(encoding="utf-8"),
                expected_project_id=item.project_id,
                expected_human_review_decision_id=(
                    item.human_review_decision_id
                ),
            )
            if reloaded != item:
                raise HumanReviewIntegrityError(
                    "Temporary Human Review Decision does not "
                    "round-trip."
                )
            try:
                os.link(temporary, path)
            except OSError as exc:
                if exc.errno == errno.EEXIST:
                    raise HumanReviewPersistenceError(
                        "Decision appeared during publication."
                    ) from exc
                raise
        except HumanReviewPersistenceError:
            raise
        except Exception as exc:
            raise HumanReviewPersistenceError(
                f"Unable to publish Human Review Decision: {path}."
            ) from exc
        finally:
            if temporary.exists() and not temporary.is_symlink():
                temporary.unlink()

    def _validate_filters(
        self,
        target_type: str | None,
        target_id: str | None,
    ) -> None:
        if target_type is None:
            if target_id is not None:
                raise HumanReviewValidationError(
                    "target_id filter requires target_type."
                )
            return
        if target_type not in HUMAN_REVIEW_TARGET_TYPES:
            raise HumanReviewValidationError(
                "target_type filter is invalid."
            )
        if target_id is not None and (
            not isinstance(target_id, str)
            or _TARGET_ID_PATTERNS[target_type].fullmatch(target_id)
            is None
        ):
            raise HumanReviewValidationError(
                "target_id filter does not match target_type."
            )

    def _validate_target_reference(
        self,
        target_type: str,
        target_id: str,
        content_fingerprint: str,
        validation_fingerprint: str | None,
    ) -> None:
        self._validate_filters(target_type, target_id)
        if (
            not isinstance(content_fingerprint, str)
            or _SHA256.fullmatch(content_fingerprint) is None
        ):
            raise HumanReviewValidationError(
                "target_content_fingerprint must be SHA-256."
            )
        if validation_fingerprint is not None and (
            not isinstance(validation_fingerprint, str)
            or _SHA256.fullmatch(validation_fingerprint) is None
        ):
            raise HumanReviewValidationError(
                "reference_validation_fingerprint must be SHA-256 "
                "or None."
            )

    def _ensure_directory(self, path: Path) -> None:
        self._reject_symlink(path, "Human reviews directory")
        try:
            path.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise HumanReviewPersistenceError(
                f"Unable to create Human reviews directory: {path}."
            ) from exc
        self._reject_symlink(path, "Human reviews directory")
        if not path.is_dir():
            raise HumanReviewPersistenceError(
                "Human reviews path is not a directory."
            )

    def _assert_within(self, path: Path, parent: Path) -> None:
        try:
            path.absolute().relative_to(parent.absolute())
        except ValueError as exc:
            raise HumanReviewPersistenceError(
                f"Unsafe Human Review path: {path}."
            ) from exc

    def _reject_symlink(self, path: Path, label: str) -> None:
        if path.is_symlink():
            raise HumanReviewPersistenceError(
                f"{label} must not be a symbolic link: {path}."
            )

    def _timestamp(self) -> str:
        value = self._clock()
        if not isinstance(value, datetime):
            raise HumanReviewPersistenceError(
                "clock must return datetime."
            )
        if value.tzinfo is None or value.utcoffset() is None:
            raise HumanReviewPersistenceError(
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
        decision_id: str | None = None,
    ) -> HumanReviewIssue:
        return HumanReviewIssue(
            project_id=project_id,
            code=code,
            message=message,
            issue_level="blocking",
            path=path,
            human_review_decision_id=decision_id,
        )