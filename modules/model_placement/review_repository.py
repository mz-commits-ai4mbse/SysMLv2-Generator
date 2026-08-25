"""Atomic persistence for Human Model Placement Review."""

from __future__ import annotations

from datetime import datetime, timezone
import errno
import os
from pathlib import Path
import re

from .errors import ModelPlacementContractError
from .review_identifiers import next_model_placement_decision_id
from .review_serialization import (
    comparison_from_json,
    comparison_to_json,
    create_review_decision,
    decision_from_json,
    decision_to_json,
)
from .review_types import (
    ModelPlacementReviewDecision,
    ModelPlacementReviewState,
)
from .approved_set import (
    approved_model_placement_set_from_json,
    approved_model_placement_set_to_json,
    build_approved_model_placement_set,
)
from .types import ModelPlacementBatchComparison


_DECISION_PATTERN = re.compile(r"^(MPD-[0-9]{6})\.json$")


def _default_clock():
    return datetime.now(timezone.utc)


class ModelPlacementReviewRepository:
    """Persist one immutable comparison plus immutable Human decision history."""

    def __init__(self, root=Path("data/projects"), *, clock=_default_clock):
        self.root = Path(root)
        self._clock = clock

    def publish_comparison(
        self,
        comparison: ModelPlacementBatchComparison,
    ) -> ModelPlacementBatchComparison:
        if not isinstance(comparison, ModelPlacementBatchComparison):
            raise ModelPlacementContractError(
                "comparison must be ModelPlacementBatchComparison."
            )
        directory = self._comparison_dir(
            comparison.project_id,
            comparison.content_fingerprint,
        )
        self._ensure_directory(directory)
        path = directory / "comparison.json"
        if path.exists():
            loaded = self.load_comparison(
                comparison.project_id,
                comparison.content_fingerprint,
            )
            if loaded != comparison:
                raise ModelPlacementContractError(
                    "Existing Model Placement comparison differs from requested "
                    "content."
                )
            return loaded
        self._atomic_publish(
            path,
            comparison_to_json(comparison),
            label="Model Placement comparison",
        )
        return self.load_comparison(
            comparison.project_id,
            comparison.content_fingerprint,
        )

    def load_comparison(
        self,
        project_id: str,
        comparison_fingerprint: str,
    ) -> ModelPlacementBatchComparison:
        path = (
            self._comparison_dir(project_id, comparison_fingerprint)
            / "comparison.json"
        )
        self._reject_symlink(path, "Model Placement comparison")
        if not path.is_file():
            raise ModelPlacementContractError(
                "Model Placement comparison not found."
            )
        value = comparison_from_json(path.read_text(encoding="utf-8"))
        if (
            value.project_id != project_id
            or value.content_fingerprint != comparison_fingerprint
        ):
            raise ModelPlacementContractError(
                "Persisted Model Placement comparison binding is invalid."
            )
        return value

    def list_comparisons(
        self,
        project_id: str,
    ) -> tuple[ModelPlacementBatchComparison, ...]:
        """List persisted Model Placement comparisons for one Project."""

        base = self.root / project_id / "model_placement_reviews"
        if not base.exists():
            return ()
        self._reject_symlink(base, "Model Placement reviews directory")
        if not base.is_dir():
            raise ModelPlacementContractError(
                "Model Placement reviews path is not a directory."
            )

        result = []
        for path in sorted(base.iterdir(), key=lambda item: item.name):
            if (
                not path.is_dir()
                or len(path.name) != 64
                or any(
                    ch not in "0123456789abcdef"
                    for ch in path.name
                )
            ):
                raise ModelPlacementContractError(
                    "Unexpected entry in Model Placement reviews directory."
                )
            result.append(
                self.load_comparison(project_id, path.name)
            )
        return tuple(result)

    def finalize_approved_placement_set(
        self,
        project_id: str,
        comparison_fingerprint: str,
        *,
        profile,
    ):
        """Persist the exact Human-resolved placement authority for assembly."""

        comparison = self.load_comparison(
            project_id,
            comparison_fingerprint,
        )
        state = self.review_state(
            project_id,
            comparison_fingerprint,
        )
        value = build_approved_model_placement_set(
            comparison=comparison,
            latest_decisions=state.latest_decisions,
            profile=profile,
        )
        directory = self._comparison_dir(
            project_id,
            comparison_fingerprint,
        )
        path = directory / "approved_placement_set.json"
        if path.exists():
            loaded = self.load_approved_placement_set(
                project_id,
                comparison_fingerprint,
            )
            if loaded != value:
                raise ModelPlacementContractError(
                    "Existing Approved Model Placement Set differs from the "
                    "current Human decision authority."
                )
            return loaded

        self._atomic_publish(
            path,
            approved_model_placement_set_to_json(value),
            label="Approved Model Placement Set",
        )
        return self.load_approved_placement_set(
            project_id,
            comparison_fingerprint,
        )

    def load_approved_placement_set_if_available(
        self,
        project_id: str,
        comparison_fingerprint: str,
    ):
        """Return finalized placement authority when present, else None."""

        path = (
            self._comparison_dir(project_id, comparison_fingerprint)
            / "approved_placement_set.json"
        )
        self._reject_symlink(path, "Approved Model Placement Set")
        if not path.exists():
            return None
        return self.load_approved_placement_set(
            project_id,
            comparison_fingerprint,
        )

    def load_approved_placement_set(
        self,
        project_id: str,
        comparison_fingerprint: str,
    ):
        path = (
            self._comparison_dir(project_id, comparison_fingerprint)
            / "approved_placement_set.json"
        )
        self._reject_symlink(path, "Approved Model Placement Set")
        if not path.is_file():
            raise ModelPlacementContractError(
                "Approved Model Placement Set not found."
            )
        value = approved_model_placement_set_from_json(
            path.read_text(encoding="utf-8")
        )
        if (
            value.project_id != project_id
            or value.comparison_fingerprint != comparison_fingerprint
        ):
            raise ModelPlacementContractError(
                "Approved Model Placement Set binding is invalid."
            )
        return value

    def record_decision(
        self,
        project_id: str,
        comparison_fingerprint: str,
        *,
        approved_input_id: str,
        outcome: str,
        selected_rule_id: str | None,
        reviewer_identity: str,
        rationale: str | None = None,
    ) -> ModelPlacementReviewDecision:
        comparison = self.load_comparison(
            project_id,
            comparison_fingerprint,
        )
        existing = self.list_decisions(
            project_id,
            comparison_fingerprint,
        )
        latest = self.latest_decision_for_input(
            project_id,
            comparison_fingerprint,
            approved_input_id,
        )
        decision_id = next_model_placement_decision_id(
            item.decision_id for item in existing
        )
        item = create_review_decision(
            project_id=project_id,
            decision_id=decision_id,
            comparison=comparison,
            approved_input_id=approved_input_id,
            outcome=outcome,
            selected_rule_id=selected_rule_id,
            reviewer_identity=reviewer_identity,
            rationale=rationale,
            supersedes_decision_id=(
                None if latest is None else latest.decision_id
            ),
            reviewed_at=self._timestamp(),
        )
        self._publish_decision(item)
        return self.load_decision(
            project_id,
            comparison_fingerprint,
            decision_id,
        )

    def reopen_decision(
        self,
        project_id: str,
        comparison_fingerprint: str,
        *,
        approved_input_id: str,
        reviewer_identity: str,
        rationale: str,
    ) -> ModelPlacementReviewDecision:
        latest = self.latest_decision_for_input(
            project_id,
            comparison_fingerprint,
            approved_input_id,
        )
        if latest is None or latest.outcome == "reopened":
            raise ModelPlacementContractError(
                "Only a decided Model Placement item may be reopened."
            )
        return self.record_decision(
            project_id,
            comparison_fingerprint,
            approved_input_id=approved_input_id,
            outcome="reopened",
            selected_rule_id=None,
            reviewer_identity=reviewer_identity,
            rationale=rationale,
        )

    def load_decision(
        self,
        project_id: str,
        comparison_fingerprint: str,
        decision_id: str,
    ) -> ModelPlacementReviewDecision:
        path = (
            self._comparison_dir(project_id, comparison_fingerprint)
            / "decisions"
            / f"{decision_id}.json"
        )
        self._reject_symlink(path, "Model Placement decision")
        if not path.is_file():
            raise ModelPlacementContractError(
                "Model Placement decision not found."
            )
        value = decision_from_json(path.read_text(encoding="utf-8"))
        if (
            value.project_id != project_id
            or value.comparison_fingerprint != comparison_fingerprint
            or value.decision_id != decision_id
        ):
            raise ModelPlacementContractError(
                "Persisted Model Placement decision binding is invalid."
            )
        return value

    def list_decisions(
        self,
        project_id: str,
        comparison_fingerprint: str,
    ) -> tuple[ModelPlacementReviewDecision, ...]:
        directory = (
            self._comparison_dir(project_id, comparison_fingerprint)
            / "decisions"
        )
        if not directory.exists():
            return ()
        self._reject_symlink(directory, "Model Placement decisions directory")
        if not directory.is_dir():
            raise ModelPlacementContractError(
                "Model Placement decisions path is not a directory."
            )
        result = []
        for path in sorted(directory.iterdir(), key=lambda item: item.name):
            match = _DECISION_PATTERN.fullmatch(path.name)
            if match is None:
                raise ModelPlacementContractError(
                    "Unexpected entry in Model Placement decisions directory."
                )
            result.append(
                self.load_decision(
                    project_id,
                    comparison_fingerprint,
                    match.group(1),
                )
            )
        return tuple(result)

    def latest_decision_for_input(
        self,
        project_id: str,
        comparison_fingerprint: str,
        approved_input_id: str,
    ) -> ModelPlacementReviewDecision | None:
        values = tuple(
            item
            for item in self.list_decisions(
                project_id,
                comparison_fingerprint,
            )
            if item.approved_input_id == approved_input_id
        )
        return values[-1] if values else None

    def review_state(
        self,
        project_id: str,
        comparison_fingerprint: str,
    ) -> ModelPlacementReviewState:
        comparison = self.load_comparison(
            project_id,
            comparison_fingerprint,
        )
        latest = []
        counts = {
            "accepted": 0,
            "rejected": 0,
            "deferred": 0,
            "reopened": 0,
        }
        for review_item in comparison.items:
            decision = self.latest_decision_for_input(
                project_id,
                comparison_fingerprint,
                review_item.approved_input_id,
            )
            if decision is None:
                continue
            latest.append(decision)
            counts[decision.outcome] += 1

        decided_without_reopen = (
            counts["accepted"] + counts["rejected"] + counts["deferred"]
        )
        pending = len(comparison.items) - decided_without_reopen
        return ModelPlacementReviewState(
            project_id=project_id,
            comparison_fingerprint=comparison_fingerprint,
            total_count=len(comparison.items),
            pending_count=pending,
            accepted_count=counts["accepted"],
            rejected_count=counts["rejected"],
            deferred_count=counts["deferred"],
            reopened_count=counts["reopened"],
            latest_decisions=tuple(
                sorted(latest, key=lambda item: item.approved_input_id)
            ),
        )

    def _publish_decision(self, item: ModelPlacementReviewDecision) -> None:
        directory = (
            self._comparison_dir(
                item.project_id,
                item.comparison_fingerprint,
            )
            / "decisions"
        )
        self._ensure_directory(directory)
        path = directory / f"{item.decision_id}.json"
        self._atomic_publish(
            path,
            decision_to_json(item),
            label="Model Placement decision",
        )

    def _comparison_dir(self, project_id, comparison_fingerprint) -> Path:
        if (
            not isinstance(project_id, str)
            or not project_id.strip()
            or "/" in project_id
            or "\\" in project_id
        ):
            raise ModelPlacementContractError("project_id is invalid.")
        if (
            not isinstance(comparison_fingerprint, str)
            or len(comparison_fingerprint) != 64
            or any(ch not in "0123456789abcdef" for ch in comparison_fingerprint)
        ):
            raise ModelPlacementContractError(
                "comparison_fingerprint must be lowercase SHA-256."
            )
        return (
            self.root
            / project_id
            / "model_placement_reviews"
            / comparison_fingerprint
        )

    def _ensure_directory(self, path: Path) -> None:
        self._reject_symlink(path, "Model Placement directory")
        path.mkdir(parents=True, exist_ok=True)
        self._reject_symlink(path, "Model Placement directory")
        if not path.is_dir():
            raise ModelPlacementContractError(
                "Model Placement path is not a directory."
            )

    def _atomic_publish(self, path: Path, text: str, *, label: str) -> None:
        self._reject_symlink(path, label)
        temporary = path.with_name(f".{path.name}.tmp")
        self._reject_symlink(temporary, f"temporary {label}")
        if path.exists() or temporary.exists():
            raise ModelPlacementContractError(
                f"{label} publication path is occupied."
            )
        try:
            with temporary.open(
                "x",
                encoding="utf-8",
                newline="\n",
            ) as handle:
                handle.write(text)
                handle.flush()
                os.fsync(handle.fileno())
            try:
                os.link(temporary, path)
            except OSError as exc:
                if exc.errno == errno.EEXIST:
                    raise ModelPlacementContractError(
                        f"{label} appeared during publication."
                    ) from exc
                raise
        finally:
            if temporary.exists() and not temporary.is_symlink():
                temporary.unlink()

    def _reject_symlink(self, path: Path, label: str) -> None:
        if path.is_symlink():
            raise ModelPlacementContractError(
                f"{label} must not be a symbolic link."
            )

    def _timestamp(self) -> str:
        value = self._clock()
        if (
            not isinstance(value, datetime)
            or value.tzinfo is None
            or value.utcoffset() is None
        ):
            raise ModelPlacementContractError(
                "clock must return timezone-aware datetime."
            )
        return (
            value.astimezone(timezone.utc)
            .isoformat(timespec="seconds")
            .replace("+00:00", "Z")
        )
