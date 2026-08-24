"""Authority-preserving write delegation for Guided Engineering Workflow."""

from __future__ import annotations

from pathlib import Path

from modules.final_model_review.change_workflow import (
    FinalModelReviewChangeService,
)
from modules.final_model_review.release_service import (
    FinalModelReviewReleaseService,
)
from modules.final_model_review.repository import (
    FinalModelReviewRepository,
)
from modules.model_candidates.candidate_review_repository import (
    ModelCandidateReviewRepository,
)
from modules.model_candidates.derivation_workflow import (
    ModelDerivationWorkflowService,
)
from modules.output_publication.final_review_publication import (
    FinalReviewPublicationService,
)

from .errors import GuidedWorkflowWriteError


class GuidedWorkflowWriteService:
    """Delegate explicit Human actions to existing normative domain authority.

    This service owns no engineering, review, release or publication authority.
    It does not select implicit targets and does not maintain authoritative UI
    state.
    """

    def __init__(
        self,
        project_root: Path | str = Path("."),
        *,
        candidate_review_repository=None,
        model_derivation_service=None,
        final_review_repository=None,
        final_change_service=None,
        final_release_service=None,
        final_publication_service=None,
    ) -> None:
        self.project_root = Path(project_root)
        projects_root = self.project_root / "data" / "projects"

        self._candidate_reviews = (
            ModelCandidateReviewRepository(
                root=projects_root,
            )
            if candidate_review_repository is None
            else candidate_review_repository
        )
        self._model_derivation = (
            ModelDerivationWorkflowService(
                project_root=self.project_root,
            )
            if model_derivation_service is None
            else model_derivation_service
        )

        if final_review_repository is None:
            final_review_repository = FinalModelReviewRepository(
                root=projects_root,
            )

        self._final_reviews = final_review_repository

        self._final_changes = (
            FinalModelReviewChangeService(
                root=projects_root,
                repository=self._final_reviews,
            )
            if final_change_service is None
            else final_change_service
        )

        self._final_release = (
            FinalModelReviewReleaseService(
                root=projects_root,
                repository=self._final_reviews,
            )
            if final_release_service is None
            else final_release_service
        )

        self._final_publication = (
            FinalReviewPublicationService(
                self.project_root,
                final_review_repository=self._final_reviews,
            )
            if final_publication_service is None
            else final_publication_service
        )

    def assess_model_derivation(
        self,
        project_id: str,
        *,
        predecessor_candidate_set_id: str | None = None,
    ):
        """Return advisory Phase-H strategy without making a Human choice."""

        try:
            return self._model_derivation.assess(
                project_id,
                predecessor_candidate_set_id=predecessor_candidate_set_id,
            )
        except Exception as exc:
            raise GuidedWorkflowWriteError(
                "Model derivation strategy could not be assessed safely."
            ) from exc

    def generate_model_proposal(
        self,
        project_id: str,
        *,
        mode: str,
        provider: str = "openai",
        model: str = "gpt-5.4-mini",
        api_key: str | None = None,
        predecessor_candidate_set_id: str | None = None,
        human_regeneration_reason: str | None = None,
    ):
        """Generate one explicit Phase-H Candidate Set."""

        try:
            return self._model_derivation.generate(
                project_id,
                mode=mode,
                provider=provider,
                model=model,
                api_key=api_key,
                predecessor_candidate_set_id=predecessor_candidate_set_id,
                human_regeneration_reason=human_regeneration_reason,
            )
        except Exception as exc:
            raise GuidedWorkflowWriteError(
                "Model Proposal generation could not be completed safely."
            ) from exc

    def record_candidate_review_decision(
        self,
        project_id: str,
        candidate_set_id: str,
        *,
        target_type: str,
        candidate_id: str,
        decision: str,
        reviewer_identity: str,
        rationale: str | None = None,
    ):
        """Record one Human decision against one explicit Candidate snapshot."""

        try:
            return self._candidate_reviews.record_decision(
                project_id,
                candidate_set_id,
                target_type=target_type,
                candidate_id=candidate_id,
                decision=decision,
                reviewer_identity=reviewer_identity,
                rationale=rationale,
            )
        except Exception as exc:
            raise GuidedWorkflowWriteError(
                "Candidate Review decision could not be recorded safely."
            ) from exc

    def submit_final_model_change(
        self,
        project_id: str,
        final_model_review_id: str,
        final_model_review_revision_id: str,
        *,
        surface: str,
        classification: str,
        reviewer_feedback: str,
        created_by: str,
        generated_unit_id: str | None = None,
        generated_symbol_id: str | None = None,
        internal_model_element_id: str | None = None,
        internal_model_relationship_id: str | None = None,
        validation_finding_code: str | None = None,
        original_text: str | None = None,
        proposed_text: str | None = None,
        request_agent_reproposal: bool = False,
        requested_agent_personalities: tuple[str, ...] = (),
    ):
        """Submit one immutable Human change proposal for one exact FRV."""

        try:
            return self._final_changes.submit_change(
                project_id,
                final_model_review_id,
                final_model_review_revision_id,
                surface=surface,
                classification=classification,
                reviewer_feedback=reviewer_feedback,
                created_by=created_by,
                generated_unit_id=generated_unit_id,
                generated_symbol_id=generated_symbol_id,
                internal_model_element_id=internal_model_element_id,
                internal_model_relationship_id=(
                    internal_model_relationship_id
                ),
                validation_finding_code=validation_finding_code,
                original_text=original_text,
                proposed_text=proposed_text,
                request_agent_reproposal=request_agent_reproposal,
                requested_agent_personalities=(
                    requested_agent_personalities
                ),
            )
        except Exception as exc:
            raise GuidedWorkflowWriteError(
                "Final Model Review change request could not be recorded safely."
            ) from exc

    def approve_final_model_for_publication(
        self,
        project_id: str,
        final_model_review_id: str,
        final_model_review_revision_id: str,
        *,
        reviewer_identity: str,
        rationale: str | None = None,
    ):
        """Record Human publication approval for one exact validated FRV."""

        try:
            return self._final_release.approve_for_publication(
                project_id,
                final_model_review_id,
                final_model_review_revision_id,
                reviewer_identity=reviewer_identity,
                rationale=rationale,
            )
        except Exception as exc:
            raise GuidedWorkflowWriteError(
                "Final publication approval could not be recorded safely."
            ) from exc


    def publish_final_model_review_revision(
        self,
        project_id: str,
        final_model_review_id: str,
        final_model_review_revision_id: str,
    ):
        """Publish one explicit already-approved Final Model Review revision."""

        try:
            return self._final_publication.publish_revision(
                project_id,
                final_model_review_id,
                final_model_review_revision_id,
            )
        except Exception as exc:
            raise GuidedWorkflowWriteError(
                "Approved Final Model Review revision could not be "
                "published safely."
            ) from exc
