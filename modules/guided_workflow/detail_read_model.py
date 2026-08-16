"""Read-only detail projections for Guided Engineering Workflow stages."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from modules.final_model_review.read_model import (
    FinalModelReviewReadService,
)
from modules.final_model_review.release_service import (
    FinalModelReviewReleaseService,
)
from modules.final_model_review.repository import (
    FinalModelReviewRepository,
)
from modules.model_candidates.model_proposal import (
    ModelProposalReadService,
)
from modules.model_candidates.repository import (
    ModelCandidateRepository,
)
from modules.output_publication.repository import (
    OutputPublicationRepository,
)

from .errors import GuidedWorkflowValidationError


GUIDED_DETAIL_STATUSES = (
    "not_available",
    "selection_required",
    "ready",
)


@dataclass(frozen=True, slots=True)
class GuidedDetailOption:
    """One explicit immutable artifact available for display."""

    entity_id: str
    label: str
    parent_entity_id: str | None = None


@dataclass(frozen=True, slots=True)
class GuidedModelProposalDetail:
    """Resolved read-only Model Proposal working context."""

    status: str
    options: tuple[GuidedDetailOption, ...]
    selected_entity_id: str | None
    proposal: Any | None


@dataclass(frozen=True, slots=True)
class GuidedFinalModelReviewDetail:
    """Resolved read-only Final Model Review working context."""

    status: str
    options: tuple[GuidedDetailOption, ...]
    selected_entity_id: str | None
    final_model_review_id: str | None
    review: Any | None
    release_gate: Any | None


@dataclass(frozen=True, slots=True)
class GuidedPublishedOutputDetail:
    """Resolved read-only Published Output working context."""

    status: str
    options: tuple[GuidedDetailOption, ...]
    selected_entity_id: str | None
    package: Any | None


class GuidedWorkflowDetailReadService:
    """Resolve exact domain read models for engineer-facing detail views.

    This service owns no engineering, review, release or publication
    authority. It only resolves existing immutable domain state for display.
    """

    def __init__(
        self,
        project_root: Path | str = Path("."),
        *,
        candidate_repository=None,
        model_proposal_service=None,
        final_review_repository=None,
        final_review_service=None,
        final_release_service=None,
        output_repository=None,
    ) -> None:
        self.project_root = Path(project_root)
        projects_root = self.project_root / "data" / "projects"

        self._candidates = (
            ModelCandidateRepository(root=projects_root)
            if candidate_repository is None
            else candidate_repository
        )
        self._model_proposals = (
            ModelProposalReadService(
                root=projects_root,
                candidate_repository=self._candidates,
            )
            if model_proposal_service is None
            else model_proposal_service
        )
        self._final_reviews = (
            FinalModelReviewRepository(root=projects_root)
            if final_review_repository is None
            else final_review_repository
        )
        self._final_review_read = (
            FinalModelReviewReadService(
                root=projects_root,
                repository=self._final_reviews,
            )
            if final_review_service is None
            else final_review_service
        )
        self._final_release = (
            FinalModelReviewReleaseService(
                root=projects_root,
                repository=self._final_reviews,
            )
            if final_release_service is None
            else final_release_service
        )
        self._outputs = (
            OutputPublicationRepository(
                output_root=self.project_root / "data" / "output"
            )
            if output_repository is None
            else output_repository
        )

    def load_model_proposal(
        self,
        project_id: str,
        candidate_set_id: str | None = None,
    ) -> GuidedModelProposalDetail:
        """Resolve one exact Candidate Set without implicit latest authority."""

        try:
            scan = self._candidates.scan_project(project_id)
        except Exception as exc:
            raise GuidedWorkflowValidationError(
                "Model Proposal state cannot be reconstructed safely."
            ) from exc

        if scan.issues:
            raise GuidedWorkflowValidationError(
                "Model Proposal repository contains blocking issues."
            )

        snapshots = tuple(scan.candidate_sets)

        if not snapshots:
            return GuidedModelProposalDetail(
                status="not_available",
                options=(),
                selected_entity_id=None,
                proposal=None,
            )

        by_id = {
            item.manifest.candidate_set_id: item
            for item in snapshots
        }

        if candidate_set_id is not None:
            if candidate_set_id not in by_id:
                raise GuidedWorkflowValidationError(
                    "Selected Candidate Set is not available in this Project."
                )
            return self._load_exact_model_proposal(
                project_id,
                candidate_set_id,
                options=self._candidate_options((by_id[candidate_set_id],)),
            )

        heads = self._candidate_heads(snapshots)
        options = self._candidate_options(heads)

        if len(heads) == 1:
            return self._load_exact_model_proposal(
                project_id,
                heads[0].manifest.candidate_set_id,
                options=options,
            )

        if len(heads) > 1:
            return GuidedModelProposalDetail(
                status="selection_required",
                options=options,
                selected_entity_id=None,
                proposal=None,
            )

        raise GuidedWorkflowValidationError(
            "Candidate lineage does not resolve a current Model Proposal."
        )

    def load_final_model_review(
        self,
        project_id: str,
        final_model_review_revision_id: str | None = None,
    ) -> GuidedFinalModelReviewDetail:
        """Resolve one exact Final Model Review revision."""

        try:
            scan = self._final_reviews.scan(project_id)
        except Exception as exc:
            raise GuidedWorkflowValidationError(
                "Final Model Review state cannot be reconstructed safely."
            ) from exc

        if scan.issues:
            raise GuidedWorkflowValidationError(
                "Final Model Review repository contains blocking issues."
            )

        revisions = tuple(scan.revisions)

        if not revisions:
            return GuidedFinalModelReviewDetail(
                status="not_available",
                options=(),
                selected_entity_id=None,
                final_model_review_id=None,
                review=None,
                release_gate=None,
            )

        if final_model_review_revision_id is not None:
            matching = tuple(
                bundle
                for bundle in revisions
                if (
                    bundle.revision.final_model_review_revision_id
                    == final_model_review_revision_id
                )
            )
            if len(matching) != 1:
                raise GuidedWorkflowValidationError(
                    "Selected Final Model Review revision is not uniquely "
                    "available in this Project."
                )
            return self._load_exact_final_review(
                project_id,
                matching[0],
                options=self._final_review_options(matching),
            )

        heads = self._final_review_heads(revisions)
        options = self._final_review_options(heads)

        if len(heads) == 1:
            return self._load_exact_final_review(
                project_id,
                heads[0],
                options=options,
            )

        if len(heads) > 1:
            return GuidedFinalModelReviewDetail(
                status="selection_required",
                options=options,
                selected_entity_id=None,
                final_model_review_id=None,
                review=None,
                release_gate=None,
            )

        raise GuidedWorkflowValidationError(
            "Final Model Review lineage does not resolve a current revision."
        )

    def load_published_output(
        self,
        project_id: str,
        output_package_id: str | None = None,
    ) -> GuidedPublishedOutputDetail:
        """Resolve one immutable Published Output package."""

        try:
            scan = self._outputs.scan_project(project_id)
        except Exception as exc:
            raise GuidedWorkflowValidationError(
                "Published Output state cannot be reconstructed safely."
            ) from exc

        if scan.issues:
            raise GuidedWorkflowValidationError(
                "Published Output repository contains blocking issues."
            )

        packages = tuple(scan.packages)

        if not packages:
            return GuidedPublishedOutputDetail(
                status="not_available",
                options=(),
                selected_entity_id=None,
                package=None,
            )

        by_id = {
            item.manifest.output_package_id: item
            for item in packages
        }

        if output_package_id is not None:
            if output_package_id not in by_id:
                raise GuidedWorkflowValidationError(
                    "Selected Published Output is not available in this Project."
                )
            package = self._outputs.load_output(
                project_id,
                output_package_id,
            )
            return GuidedPublishedOutputDetail(
                status="ready",
                options=self._output_options((package,)),
                selected_entity_id=output_package_id,
                package=package,
            )

        options = self._output_options(packages)

        if len(packages) == 1:
            package_id = packages[0].manifest.output_package_id
            package = self._outputs.load_output(
                project_id,
                package_id,
            )
            return GuidedPublishedOutputDetail(
                status="ready",
                options=options,
                selected_entity_id=package_id,
                package=package,
            )

        return GuidedPublishedOutputDetail(
            status="selection_required",
            options=options,
            selected_entity_id=None,
            package=None,
        )

    def read_published_output_file(
        self,
        project_id: str,
        output_package_id: str,
        relative_path: str,
    ) -> bytes:
        """Read only a manifest-authorized file from one exact OUT package."""

        try:
            return self._outputs.read_file(
                project_id,
                output_package_id,
                relative_path,
            )
        except Exception as exc:
            raise GuidedWorkflowValidationError(
                "Published Output file could not be read safely."
            ) from exc

    def _load_exact_model_proposal(
        self,
        project_id: str,
        candidate_set_id: str,
        *,
        options: tuple[GuidedDetailOption, ...],
    ) -> GuidedModelProposalDetail:
        try:
            proposal = self._model_proposals.load_model_proposal(
                project_id,
                candidate_set_id,
            )
        except Exception as exc:
            raise GuidedWorkflowValidationError(
                "Selected Model Proposal could not be reconstructed safely."
            ) from exc

        return GuidedModelProposalDetail(
            status="ready",
            options=options,
            selected_entity_id=candidate_set_id,
            proposal=proposal,
        )

    def _load_exact_final_review(
        self,
        project_id: str,
        bundle,
        *,
        options: tuple[GuidedDetailOption, ...],
    ) -> GuidedFinalModelReviewDetail:
        revision = bundle.revision

        try:
            view = self._final_review_read.load_view(
                project_id,
                revision.final_model_review_id,
                revision.final_model_review_revision_id,
            )
            gate = self._final_release.evaluate(
                project_id,
                revision.final_model_review_id,
                revision.final_model_review_revision_id,
            )
        except Exception as exc:
            raise GuidedWorkflowValidationError(
                "Selected Final Model Review could not be reconstructed safely."
            ) from exc

        return GuidedFinalModelReviewDetail(
            status="ready",
            options=options,
            selected_entity_id=(
                revision.final_model_review_revision_id
            ),
            final_model_review_id=revision.final_model_review_id,
            review=view,
            release_gate=gate,
        )

    @staticmethod
    def _candidate_heads(snapshots):
        predecessor_ids = {
            item.manifest.predecessor_candidate_set_id
            for item in snapshots
            if item.manifest.predecessor_candidate_set_id is not None
        }
        return tuple(
            sorted(
                (
                    item
                    for item in snapshots
                    if item.manifest.candidate_set_id
                    not in predecessor_ids
                ),
                key=lambda item: item.manifest.candidate_set_id,
            )
        )

    @staticmethod
    def _final_review_heads(revisions):
        by_review: dict[str, list[Any]] = {}

        for bundle in revisions:
            by_review.setdefault(
                bundle.revision.final_model_review_id,
                [],
            ).append(bundle)

        heads = []

        for review_id in sorted(by_review):
            bundles = tuple(by_review[review_id])
            predecessor_ids = {
                bundle.revision.predecessor_revision_id
                for bundle in bundles
                if bundle.revision.predecessor_revision_id is not None
            }
            heads.extend(
                bundle
                for bundle in bundles
                if (
                    bundle.revision.final_model_review_revision_id
                    not in predecessor_ids
                )
            )

        return tuple(
            sorted(
                heads,
                key=lambda bundle: (
                    bundle.revision.final_model_review_id,
                    bundle.revision.final_model_review_revision_id,
                ),
            )
        )

    @staticmethod
    def _candidate_options(snapshots):
        return tuple(
            GuidedDetailOption(
                entity_id=item.manifest.candidate_set_id,
                label=(
                    "Model Proposal — "
                    f"{len(item.element_candidates)} elements · "
                    f"{len(item.relationship_candidates)} relationships"
                ),
            )
            for item in snapshots
        )

    @staticmethod
    def _final_review_options(revisions):
        return tuple(
            GuidedDetailOption(
                entity_id=(
                    bundle.revision.final_model_review_revision_id
                ),
                parent_entity_id=(
                    bundle.revision.final_model_review_id
                ),
                label=(
                    "Final Model Review — "
                    f"{bundle.revision.validation_status} · "
                    f"{bundle.revision.created_at}"
                ),
            )
            for bundle in revisions
        )

    @staticmethod
    def _output_options(packages):
        return tuple(
            GuidedDetailOption(
                entity_id=item.manifest.output_package_id,
                label=(
                    "Published Output — "
                    f"{item.manifest.published_at}"
                ),
            )
            for item in sorted(
                packages,
                key=lambda package: (
                    package.manifest.output_package_id
                ),
            )
        )
