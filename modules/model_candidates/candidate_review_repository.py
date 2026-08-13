"""Atomic persistence and lookup for Phase-H Candidate Review Decisions."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
import errno
import os
from pathlib import Path
import re

from modules.project_workspace import ProjectWorkspace
from modules.project_workspace.workspace import DEFAULT_PROJECTS_ROOT

from .candidate_review_identifiers import (
    next_model_candidate_review_decision_id,
    validate_model_candidate_review_decision_id,
)
from .candidate_review_manifest import (
    create_model_candidate_review_decision,
    create_model_candidate_review_target_snapshot,
    model_candidate_review_decision_from_json,
    model_candidate_review_decision_to_json,
)
from .candidate_review_paths import (
    model_candidate_review_decision_path,
    model_candidate_reviews_path,
)
from .errors import (
    ModelCandidateIntegrityError,
    ModelCandidateReviewNotFoundError,
    ModelCandidateReviewPersistenceError,
    ModelCandidateValidationError,
)
from .repository import ModelCandidateRepository
from .types import (
    MODEL_CANDIDATE_REVIEW_TARGET_TYPES,
    ModelCandidateReviewDecision,
    ModelCandidateReviewIssue,
    ModelCandidateReviewScanResult,
)


_DECISION_FILE_PATTERN = re.compile(r"^(MCD-[0-9]{6})\.json$")


def _default_clock() -> datetime:
    return datetime.now(timezone.utc)


class ModelCandidateReviewRepository:
    """Persist immutable human decisions bound to exact Candidate snapshots."""

    def __init__(
        self,
        root: Path | str = DEFAULT_PROJECTS_ROOT,
        *,
        candidate_repository: ModelCandidateRepository | None = None,
        clock: Callable[[], datetime] = _default_clock,
    ) -> None:
        self.root = Path(root)
        self._clock = clock
        self._workspace = ProjectWorkspace(root=self.root, clock=clock)
        self._candidates = (
            ModelCandidateRepository(root=self.root)
            if candidate_repository is None
            else candidate_repository
        )

    def record_decision(
        self,
        project_id: str,
        candidate_set_id: str,
        *,
        target_type: str,
        candidate_id: str,
        decision: str,
        reviewer_identity: str,
        rationale: str | None = None,
    ) -> ModelCandidateReviewDecision:
        """Create one exact decision from persisted Candidate content."""

        snapshot = self._candidates.load_candidate_set(
            project_id,
            candidate_set_id,
        )
        candidate = self._candidate_for_target(
            snapshot,
            target_type,
            candidate_id,
        )
        existing = self.list_decisions(project_id)
        decision_id = next_model_candidate_review_decision_id(
            item.model_candidate_review_decision_id
            for item in existing
        )
        target = create_model_candidate_review_target_snapshot(
            candidate_set_id=snapshot.manifest.candidate_set_id,
            candidate_set_content_fingerprint=(
                snapshot.manifest.content_fingerprint
            ),
            target_type=target_type,
            candidate_id=candidate_id,
            candidate_content_fingerprint=candidate.content_fingerprint,
            model_structure_profile_reference=(
                snapshot.manifest.model_structure_profile_reference
            ),
            structure_profile_conformance_status=(
                candidate.structure_profile_conformance.status
            ),
            structure_profile_conformance_fingerprint=(
                candidate.structure_profile_conformance
                .conformance_fingerprint
            ),
            approved_input_snapshot_fingerprint=(
                snapshot.manifest.approved_input_snapshot_fingerprint
            ),
        )
        item = create_model_candidate_review_decision(
            project_id=project_id,
            model_candidate_review_decision_id=decision_id,
            target=target,
            decision=decision,
            reviewer_identity=reviewer_identity,
            rationale=rationale,
            reviewed_at=self._timestamp(),
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
            raise ModelCandidateIntegrityError(
                "Equivalent Model Candidate Review Decision already "
                f"exists as {duplicate.model_candidate_review_decision_id}."
            )
        self._publish(item)
        return self.load_decision(project_id, decision_id)

    def load_decision(
        self,
        project_id: str,
        decision_id: str,
    ) -> ModelCandidateReviewDecision:
        self._workspace.load_project(project_id)
        validated = validate_model_candidate_review_decision_id(
            decision_id
        )
        path = model_candidate_review_decision_path(
            self.root,
            project_id,
            validated,
        )
        self._reject_symlink(path, "Candidate Review Decision")
        if not path.exists() or not path.is_file():
            raise ModelCandidateReviewNotFoundError(
                f"Model Candidate Review Decision not found: {validated}."
            )
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise ModelCandidateReviewPersistenceError(
                f"Unable to read Model Candidate Review Decision: {path}."
            ) from exc
        return model_candidate_review_decision_from_json(
            text,
            expected_project_id=project_id,
            expected_decision_id=validated,
        )

    def list_decisions(
        self,
        project_id: str,
        *,
        candidate_set_id: str | None = None,
        target_type: str | None = None,
        candidate_id: str | None = None,
    ) -> tuple[ModelCandidateReviewDecision, ...]:
        self._workspace.load_project(project_id)
        if target_type is not None and (
            target_type not in MODEL_CANDIDATE_REVIEW_TARGET_TYPES
        ):
            raise ModelCandidateValidationError(
                "target_type filter is invalid."
            )
        if candidate_id is not None and target_type is None:
            raise ModelCandidateValidationError(
                "candidate_id filter requires target_type."
            )
        directory = model_candidate_reviews_path(
            self.root,
            project_id,
        )
        if not directory.exists():
            return ()
        self._reject_symlink(directory, "Candidate Review directory")
        if not directory.is_dir():
            raise ModelCandidateReviewPersistenceError(
                "Candidate Review path is not a directory."
            )
        decisions = []
        for path in sorted(directory.iterdir(), key=lambda item: item.name):
            match = _DECISION_FILE_PATTERN.fullmatch(path.name)
            if match is None:
                continue
            item = self.load_decision(project_id, match.group(1))
            if (
                candidate_set_id is not None
                and item.target.candidate_set_id != candidate_set_id
            ):
                continue
            if (
                target_type is not None
                and item.target.target_type != target_type
            ):
                continue
            if (
                candidate_id is not None
                and item.target.candidate_id != candidate_id
            ):
                continue
            decisions.append(item)
        return tuple(decisions)

    def scan_decisions(
        self,
        project_id: str,
    ) -> ModelCandidateReviewScanResult:
        try:
            self._workspace.load_project(project_id)
            directory = model_candidate_reviews_path(
                self.root,
                project_id,
            )
        except Exception as exc:
            return ModelCandidateReviewScanResult(
                issues=(
                    self._issue(
                        project_id,
                        code="unsafe_candidate_review_directory",
                        message=str(exc),
                        path=None,
                    ),
                )
            )
        if not directory.exists():
            return ModelCandidateReviewScanResult()
        if directory.is_symlink() or not directory.is_dir():
            return ModelCandidateReviewScanResult(
                issues=(
                    self._issue(
                        project_id,
                        code="unsafe_candidate_review_directory",
                        message=(
                            "Candidate Review path is not a safe directory."
                        ),
                        path=directory,
                    ),
                )
            )
        decisions = []
        issues = []
        for path in sorted(directory.iterdir(), key=lambda item: item.name):
            match = _DECISION_FILE_PATTERN.fullmatch(path.name)
            if match is None:
                issues.append(
                    self._issue(
                        project_id,
                        code="unexpected_candidate_review_entry",
                        message=(
                            "Unexpected entry in Candidate Review directory."
                        ),
                        path=path,
                    )
                )
                continue
            try:
                decisions.append(
                    self.load_decision(project_id, match.group(1))
                )
            except Exception as exc:
                issues.append(
                    self._issue(
                        project_id,
                        code="invalid_candidate_review_decision",
                        message=str(exc),
                        path=path,
                        decision_id=match.group(1),
                    )
                )
        return ModelCandidateReviewScanResult(
            decisions=tuple(decisions),
            issues=tuple(issues),
        )

    def latest_decision_for_target(
        self,
        project_id: str,
        candidate_set_id: str,
        *,
        target_type: str,
        candidate_id: str,
    ) -> ModelCandidateReviewDecision | None:
        decisions = self.list_decisions(
            project_id,
            candidate_set_id=candidate_set_id,
            target_type=target_type,
            candidate_id=candidate_id,
        )
        return decisions[-1] if decisions else None

    def _candidate_for_target(
        self,
        snapshot,
        target_type: str,
        candidate_id: str,
    ):
        if target_type == "element_candidate":
            candidates = snapshot.element_candidates
            attr = "model_element_candidate_id"
        elif target_type == "relationship_candidate":
            candidates = snapshot.relationship_candidates
            attr = "model_relationship_candidate_id"
        else:
            raise ModelCandidateValidationError(
                "target_type is invalid."
            )
        matches = tuple(
            item
            for item in candidates
            if getattr(item, attr) == candidate_id
        )
        if len(matches) != 1:
            raise ModelCandidateValidationError(
                "candidate_id does not resolve exactly once in "
                "the selected Candidate Set."
            )
        return matches[0]

    def _publish(
        self,
        item: ModelCandidateReviewDecision,
    ) -> None:
        directory = model_candidate_reviews_path(
            self.root,
            item.project_id,
        )
        self._ensure_directory(directory)
        path = model_candidate_review_decision_path(
            self.root,
            item.project_id,
            item.model_candidate_review_decision_id,
        )
        temporary = path.with_name(f".{path.name}.tmp")
        self._reject_symlink(path, "Candidate Review Decision")
        self._reject_symlink(temporary, "temporary Candidate Review Decision")
        if path.exists() or temporary.exists():
            raise ModelCandidateReviewPersistenceError(
                "Candidate Review Decision publication path is occupied."
            )
        serialized = model_candidate_review_decision_to_json(item)
        try:
            with temporary.open(
                "x",
                encoding="utf-8",
                newline="\n",
            ) as handle:
                handle.write(serialized)
                handle.flush()
                os.fsync(handle.fileno())
            reloaded = model_candidate_review_decision_from_json(
                temporary.read_text(encoding="utf-8"),
                expected_project_id=item.project_id,
                expected_decision_id=(
                    item.model_candidate_review_decision_id
                ),
            )
            if reloaded != item:
                raise ModelCandidateIntegrityError(
                    "Temporary Candidate Review Decision does not round-trip."
                )
            try:
                os.link(temporary, path)
            except OSError as exc:
                if exc.errno == errno.EEXIST:
                    raise ModelCandidateReviewPersistenceError(
                        "Candidate Review Decision appeared during publication."
                    ) from exc
                raise
        except (
            ModelCandidateIntegrityError,
            ModelCandidateReviewPersistenceError,
        ):
            raise
        except OSError as exc:
            raise ModelCandidateReviewPersistenceError(
                f"Unable to publish Candidate Review Decision: {path}."
            ) from exc
        finally:
            if temporary.exists() and not temporary.is_symlink():
                temporary.unlink()

    def _ensure_directory(self, path: Path) -> None:
        self._reject_symlink(path, "Candidate Review directory")
        try:
            path.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise ModelCandidateReviewPersistenceError(
                f"Unable to create Candidate Review directory: {path}."
            ) from exc
        self._reject_symlink(path, "Candidate Review directory")
        if not path.is_dir():
            raise ModelCandidateReviewPersistenceError(
                "Candidate Review path is not a directory."
            )

    def _reject_symlink(self, path: Path, label: str) -> None:
        if path.is_symlink():
            raise ModelCandidateReviewPersistenceError(
                f"{label} must not be a symbolic link: {path}."
            )

    def _timestamp(self) -> str:
        value = self._clock()
        if not isinstance(value, datetime):
            raise ModelCandidateReviewPersistenceError(
                "clock must return datetime."
            )
        if value.tzinfo is None or value.utcoffset() is None:
            raise ModelCandidateReviewPersistenceError(
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
        *,
        code: str,
        message: str,
        path: Path | None,
        decision_id: str | None = None,
    ) -> ModelCandidateReviewIssue:
        return ModelCandidateReviewIssue(
            project_id=project_id,
            code=code,
            message=message,
            issue_level="blocking",
            path=path,
            model_candidate_review_decision_id=decision_id,
        )
