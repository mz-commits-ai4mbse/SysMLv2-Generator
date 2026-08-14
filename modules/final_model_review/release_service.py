"""Explicit Human approval service for the Phase-L final release boundary."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from collections.abc import Callable

from modules.project_workspace.workspace import DEFAULT_PROJECTS_ROOT

from .contracts import (
    create_final_model_review_decision,
    create_final_model_review_decision_target,
)
from .errors import (
    FinalModelReviewIntegrityError,
    FinalModelReviewReleaseGateError,
    FinalModelReviewValidationError,
)
from .identifiers import next_final_model_review_decision_id
from .release_gate import (
    evaluate_final_model_review_release_gate,
    require_final_model_review_ready_for_approval,
)
from .repository import FinalModelReviewRepository
from .types import FinalModelReviewReleaseApproval


def _default_clock() -> datetime:
    return datetime.now(timezone.utc)


class FinalModelReviewReleaseService:
    """Record Human publication approval only through the normative L5 gate."""

    def __init__(
        self,
        root: Path | str = DEFAULT_PROJECTS_ROOT,
        *,
        repository: FinalModelReviewRepository | None = None,
        clock: Callable[[], datetime] = _default_clock,
    ) -> None:
        self.root = Path(root)
        self._repository = repository or FinalModelReviewRepository(
            root=self.root,
            clock=clock,
        )
        self._clock = clock

    def evaluate(
        self,
        project_id: str,
        final_model_review_id: str,
        final_model_review_revision_id: str,
    ):
        return evaluate_final_model_review_release_gate(
            self._repository,
            project_id,
            final_model_review_id,
            final_model_review_revision_id,
        )

    def approve_for_publication(
        self,
        project_id: str,
        final_model_review_id: str,
        final_model_review_revision_id: str,
        *,
        reviewer_identity: str,
        rationale: str | None = None,
    ) -> FinalModelReviewReleaseApproval:
        current = self.evaluate(
            project_id,
            final_model_review_id,
            final_model_review_revision_id,
        )
        if current.release_status == "approved_for_publication":
            decisions = tuple(
                item
                for item in self._repository.list_decisions(
                    project_id,
                    final_model_review_id,
                )
                if item.target.final_model_review_revision_id
                == final_model_review_revision_id
                and item.decision == "approved_for_publication"
            )
            if len(decisions) != 1:
                raise FinalModelReviewIntegrityError(
                    "Approved release gate does not resolve exactly one Human "
                    "publication decision."
                )
            return FinalModelReviewReleaseApproval(
                gate=current,
                decision=decisions[0],
            )

        gate = require_final_model_review_ready_for_approval(
            self._repository,
            project_id,
            final_model_review_id,
            final_model_review_revision_id,
        )
        scan = self._repository.scan(project_id)
        if scan.issues:
            first = scan.issues[0]
            raise FinalModelReviewIntegrityError(
                "Final Model Review decision ID allocation is blocked by "
                f"repository issue {first.code}: {first.message}"
            )
        decision_id = next_final_model_review_decision_id(
            item.final_model_review_decision_id
            for item in scan.decisions
        )
        bundle = self._repository.load_revision(
            project_id,
            final_model_review_id,
            final_model_review_revision_id,
        )
        decision = create_final_model_review_decision(
            project_id=project_id,
            final_model_review_decision_id=decision_id,
            target=create_final_model_review_decision_target(bundle.revision),
            decision="approved_for_publication",
            reviewer_identity=reviewer_identity,
            rationale=rationale,
            reviewed_at=self._timestamp(),
        )
        saved = self._repository.persist_decision(decision)
        approved = self.evaluate(
            project_id,
            final_model_review_id,
            final_model_review_revision_id,
        )
        if (
            approved.release_status != "approved_for_publication"
            or approved.approval_decision_id
            != saved.final_model_review_decision_id
        ):
            raise FinalModelReviewIntegrityError(
                "Persisted Human approval did not produce an approved release gate."
            )
        return FinalModelReviewReleaseApproval(
            gate=approved,
            decision=saved,
        )

    def _timestamp(self) -> str:
        value = self._clock()
        if not isinstance(value, datetime):
            raise FinalModelReviewValidationError(
                "clock must return datetime."
            )
        if value.tzinfo is None or value.utcoffset() is None:
            raise FinalModelReviewValidationError(
                "clock must return a timezone-aware datetime."
            )
        return (
            value.astimezone(timezone.utc)
            .isoformat(timespec="seconds")
            .replace("+00:00", "Z")
        )
