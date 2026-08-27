"""Live Human Target-Model Formulation review service for bounded BLK-006 recovery."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path

from modules.internal_model.authority_backed import AuthorityBackedInternalModelRepository
from modules.model_assembly.final_review import ModelAssemblyFinalReviewRepository
from modules.sysml_generation.generation_profile import load_generation_profile

from .errors import TargetModelFormulationError
from .evidence import assess_local_references
from .proposals import build_blk006_formulation_review
from .repository import TargetModelFormulationAuthorityRepository


@dataclass(frozen=True, slots=True)
class TargetModelFormulationLiveState:
    review: object
    effective_decisions: tuple
    authority_set: object | None


class TargetModelFormulationLiveReviewService:
    """Prepare and execute explicit Human formulation review over one authority-backed IEM."""

    def __init__(
        self,
        *,
        projects_root: Path | str = Path("data/projects"),
        repo_root: Path | str = Path("."),
        authority_repository=None,
        internal_model_repository=None,
        final_model_review_repository=None,
        clock=None,
    ) -> None:
        self.projects_root = Path(projects_root)
        self.repo_root = Path(repo_root)
        self.authority_repository = (
            authority_repository
            if authority_repository is not None
            else TargetModelFormulationAuthorityRepository(self.projects_root)
        )
        self.internal_model_repository = (
            internal_model_repository
            if internal_model_repository is not None
            else AuthorityBackedInternalModelRepository(self.projects_root)
        )
        self.final_model_review_repository = (
            final_model_review_repository
            if final_model_review_repository is not None
            else ModelAssemblyFinalReviewRepository(self.projects_root)
        )
        self._clock = clock

    def prepare_review(
        self,
        *,
        project_id: str,
        internal_engineering_model_id: str,
        force_revision: bool = False,
    ):
        snapshot = self.internal_model_repository.load(
            project_id,
            internal_engineering_model_id,
        )
        self._validate_final_model_review_binding(snapshot)

        target_profile_path = (
            self.repo_root
            / "context/sysml/sysml_v2_target_model_profile.json"
        )
        target_notation_path = (
            self.repo_root
            / "context/sysml/sysml_v2_target_notation.json"
        )
        release_root = self.repo_root / "external/sysml-v2-release"

        try:
            profile = json.loads(
                target_profile_path.read_text(encoding="utf-8")
            )
        except Exception as exc:
            raise TargetModelFormulationError(
                "Target-Model Profile could not be loaded."
            ) from exc

        assessment = assess_local_references(
            sysml_release_root=release_root,
            target_notation_path=target_notation_path,
        )

        existing = self.authority_repository.find_review_for_source(
            project_id,
            internal_engineering_model_id,
            snapshot.content_fingerprint,
        )
        if existing is not None and not force_revision:
            self._validate_existing_review_context(
                existing,
                snapshot=snapshot,
                profile=profile,
                target_notation_fingerprint=(
                    assessment.target_notation_fingerprint
                ),
            )
            return existing

        generation_profile_path = (
            self.repo_root
            / "context/sysml/turing_sysml_v2_generation_profile.json"
        )
        try:
            generation_profile = load_generation_profile(
                generation_profile_path
            )
        except Exception as exc:
            raise TargetModelFormulationError(
                "SysML Generation Profile could not be loaded."
            ) from exc

        review = build_blk006_formulation_review(
            snapshot=snapshot,
            assessment=assessment,
            target_model_profile=profile,
            generation_profile=generation_profile,
            review_id=self.authority_repository.allocate_review_id(project_id),
            created_at=self._now(),
        )
        self.authority_repository.record_review(review)
        return review

    def state(self, review) -> TargetModelFormulationLiveState:
        effective = self.authority_repository.effective_decisions(review)
        authority = self.authority_repository.latest_authority_set_for_review(
            review.project_id,
            review.review_id,
        )
        return TargetModelFormulationLiveState(
            review=review,
            effective_decisions=effective,
            authority_set=authority,
        )

    def record_selection(
        self,
        *,
        review,
        authority_subject_id: str,
        selected_candidate_id: str,
        reviewer_identity: str,
        rationale: str,
    ):
        return self.authority_repository.record_selection(
            review=review,
            authority_subject_id=authority_subject_id,
            selected_candidate_id=selected_candidate_id,
            reviewer_identity=reviewer_identity,
            rationale=rationale,
            decided_at=self._now(),
        )

    def finalize(self, review):
        effective = self.authority_repository.effective_decisions(review)
        existing = self.authority_repository.latest_authority_set_for_review(
            review.project_id,
            review.review_id,
        )
        if existing is not None and tuple(
            item.content_fingerprint
            for item in existing.effective_decisions
        ) == tuple(
            item.content_fingerprint
            for item in effective
        ):
            return existing

        return self.authority_repository.finalize_authority_set(
            review=review,
            created_at=self._now(),
        )

    def _validate_final_model_review_binding(self, snapshot) -> None:
        decision = self.final_model_review_repository.latest_decision(
            snapshot.project_id,
            snapshot.comparison_fingerprint,
        )
        if decision is None:
            raise TargetModelFormulationError(
                "Authority-backed IEM has no persisted Final Model Review authority."
            )
        if decision.decision != "approved":
            raise TargetModelFormulationError(
                "Target-Model Formulation requires an approved Final Model Review."
            )
        if (
            decision.final_assembly_decision_id
            != snapshot.final_model_review_decision_id
            or decision.decision_fingerprint
            != snapshot.final_model_review_decision_fingerprint
        ):
            raise TargetModelFormulationError(
                "Authority-backed IEM and Final Model Review authority binding differ."
            )

    @staticmethod
    def _validate_existing_review_context(
        review,
        *,
        snapshot,
        profile: dict,
        target_notation_fingerprint: str,
    ) -> None:
        if (
            review.source_internal_engineering_model_id
            != snapshot.internal_engineering_model_id
            or review.source_internal_engineering_model_fingerprint
            != snapshot.content_fingerprint
            or review.final_model_review_decision_id
            != snapshot.final_model_review_decision_id
            or review.final_model_review_decision_fingerprint
            != snapshot.final_model_review_decision_fingerprint
        ):
            raise TargetModelFormulationError(
                "Persisted Target-Model Formulation review authority binding differs from the live IEM."
            )
        if (
            review.target_model_profile_id != profile.get("profile_id")
            or review.target_model_profile_version
            != profile.get("profile_version")
        ):
            raise TargetModelFormulationError(
                "Persisted Target-Model Formulation review uses a different Target-Model Profile."
            )
        if review.target_notation_fingerprint != target_notation_fingerprint:
            raise TargetModelFormulationError(
                "Persisted Target-Model Formulation review uses a different Target Notation."
            )

    def _now(self) -> str:
        if self._clock is None:
            value = datetime.now(timezone.utc)
        else:
            value = self._clock()
        return value.astimezone(timezone.utc).isoformat().replace(
            "+00:00",
            "Z",
        )
