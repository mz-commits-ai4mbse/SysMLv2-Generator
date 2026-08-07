"""Repository-bound service for idempotent Approved Input promotion."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from modules.human_review import (
    HumanReviewError,
    HumanReviewRepository,
)
from modules.project_processing import (
    ProjectProcessingError,
    ProjectProcessingRepository,
)
from modules.project_sources import (
    ProjectSourceError,
    ProjectSourceRegistry,
)
from modules.review_workspace import (
    ReviewWorkspaceError,
    ReviewWorkspaceRepository,
)

from .eligibility import (
    ApprovedInputPromotionEligibilityAssessment,
    assess_approved_input_promotion_eligibility,
)
from .lifecycle import active_approved_input_manifests
from .lifecycle_service import ApprovedInputLifecycleService
from .errors import (
    ApprovedInputError,
    ApprovedInputPromotionBlockedError,
    ApprovedInputRecoveryRequiredError,
    ApprovedInputReferenceError,
    ApprovedInputValidationError,
)
from .promotion_plan import (
    ApprovedInputPromotionPlan,
    ApprovedInputPromotionPlanItem,
    create_approved_input_promotion_plan,
)
from .repository import (
    DEFAULT_PROJECTS_ROOT,
    ApprovedInputRepository,
)
from .types import ApprovedInputManifest


def _default_clock() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True, slots=True)
class ApprovedInputPromotionResult:
    """Completed G5.5 manifest-promotion result."""

    project_id: str
    review_document_id: str
    review_document_version_id: str
    finalized_artifact_set_fingerprint: str
    promoted_manifests: tuple[ApprovedInputManifest, ...]
    created_approved_input_ids: tuple[str, ...]
    reused_approved_input_ids: tuple[str, ...]
    skipped_review_item_ids: tuple[str, ...]
    lifecycle_event_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class _PromotionAuthoritySnapshots:
    document: object
    artifact_set: object
    source_manifest: object
    processing_history: object
    finalization_decision: object


class ApprovedInputPromotionService:
    """Promote one exact finalized Review Version idempotently."""

    def __init__(
        self,
        root: Path | str = DEFAULT_PROJECTS_ROOT,
        *,
        clock: Callable[[], datetime] = _default_clock,
        review_repository=None,
        source_registry=None,
        processing_repository=None,
        human_review_repository=None,
        approved_input_repository=None,
        lifecycle_service=None,
    ) -> None:
        if not callable(clock):
            raise ApprovedInputValidationError(
                "clock must be callable."
            )

        self.root = Path(root)
        self._clock = clock
        self._review_repository = (
            review_repository
            if review_repository is not None
            else ReviewWorkspaceRepository(root=self.root)
        )
        self._source_registry = (
            source_registry
            if source_registry is not None
            else ProjectSourceRegistry(root=self.root)
        )
        self._processing_repository = (
            processing_repository
            if processing_repository is not None
            else ProjectProcessingRepository(root=self.root)
        )
        self._human_review_repository = (
            human_review_repository
            if human_review_repository is not None
            else HumanReviewRepository(root=self.root)
        )
        self._approved_input_repository = (
            approved_input_repository
            if approved_input_repository is not None
            else ApprovedInputRepository(root=self.root)
        )
        self._lifecycle_service = (
            lifecycle_service
            if lifecycle_service is not None
            else ApprovedInputLifecycleService(
                root=self.root,
                clock=clock,
                approved_input_repository=(
                    self._approved_input_repository
                ),
                human_review_repository=(
                    self._human_review_repository
                ),
            )
        )

    def assess_eligibility(
        self,
        project_id: str,
        review_document_id: str,
        review_document_version_id: str,
    ) -> ApprovedInputPromotionEligibilityAssessment:
        """Load current authority snapshots and assess them read-only."""

        snapshots = self._load_current_authority(
            project_id,
            review_document_id,
            review_document_version_id,
        )

        return assess_approved_input_promotion_eligibility(
            snapshots.document,
            snapshots.artifact_set,
            snapshots.source_manifest,
            snapshots.processing_history,
            snapshots.finalization_decision,
        )

    def promote_finalized_version(
        self,
        project_id: str,
        review_document_id: str,
        review_document_version_id: str,
    ) -> ApprovedInputPromotionResult:
        """Promote all currently eligible items with idempotent recovery.

        Manifests are created or retained first; G5.6 lifecycle events
        reconcile changed or withdrawn successor subjects afterwards.
        """

        snapshots = self._load_current_authority(
            project_id,
            review_document_id,
            review_document_version_id,
        )
        assessment = assess_approved_input_promotion_eligibility(
            snapshots.document,
            snapshots.artifact_set,
            snapshots.source_manifest,
            snapshots.processing_history,
            snapshots.finalization_decision,
        )

        if not assessment.eligible_for_promotion:
            raise ApprovedInputPromotionBlockedError(
                "Approved Input promotion is blocked: "
                + ", ".join(assessment.blocking_issue_codes)
            )

        timestamp = self._timestamp()
        existing_manifests = (
            self._approved_input_repository.list_manifests(
                project_id
            )
        )
        active_manifests = active_approved_input_manifests(
            existing_manifests,
            self._approved_input_repository.list_events(project_id),
        )
        initial_plan = create_approved_input_promotion_plan(
            snapshots.document,
            snapshots.artifact_set,
            assessment,
            existing_manifests,
            active_manifests=active_manifests,
            timestamp=timestamp,
        )

        promoted: dict[str, ApprovedInputManifest] = {}
        created_ids: list[str] = []
        reused_ids: list[str] = []
        skipped_ids = list(initial_plan.skipped_item_ids)

        for planned_item in initial_plan.items:
            if planned_item.action == "skip":
                continue

            try:
                current_item = self._current_plan_item(
                    project_id,
                    review_document_id,
                    review_document_version_id,
                    planned_item.review_item_id,
                    expected_plan=initial_plan,
                    timestamp=timestamp,
                )

                if current_item.action == "skip":
                    raise ApprovedInputPromotionBlockedError(
                        "A previously promotable Review Item became "
                        "non-promotable during promotion: "
                        f"{current_item.review_item_id}."
                    )

                if current_item.manifest is None:
                    raise ApprovedInputRecoveryRequiredError(
                        "Promotion plan item lacks an Approved Input "
                        "manifest."
                    )

                if current_item.action == "reuse":
                    persisted = (
                        self._approved_input_repository.load_manifest(
                            project_id,
                            current_item.manifest.approved_input_id,
                        )
                    )
                    if persisted != current_item.manifest:
                        raise ApprovedInputRecoveryRequiredError(
                            "Reusable Approved Input changed during "
                            "promotion."
                        )
                    promoted[
                        current_item.review_item_id
                    ] = persisted
                    reused_ids.append(
                        persisted.approved_input_id
                    )
                    continue

                persisted = (
                    self._approved_input_repository.persist_manifest(
                        current_item.manifest
                    )
                )
                promoted[
                    current_item.review_item_id
                ] = persisted
                created_ids.append(
                    persisted.approved_input_id
                )
            except ApprovedInputPromotionBlockedError as exc:
                if created_ids:
                    raise ApprovedInputRecoveryRequiredError(
                        "Approved Input promotion became blocked after "
                        "partial publication; deterministic recovery is "
                        "required."
                    ) from exc
                raise
            except ApprovedInputRecoveryRequiredError:
                raise
            except ApprovedInputError as exc:
                raise ApprovedInputRecoveryRequiredError(
                    "Approved Input promotion did not complete; existing "
                    "published manifests remain traceable and the "
                    "operation must be resumed idempotently."
                ) from exc
            except Exception as exc:
                raise ApprovedInputRecoveryRequiredError(
                    "Approved Input promotion encountered an unexpected "
                    "repository failure; deterministic recovery is "
                    "required."
                ) from exc

        ordered_promoted = tuple(
            promoted[item.review_item_id]
            for item in initial_plan.items
            if item.review_item_id in promoted
        )

        try:
            final_snapshots = self._load_current_authority(
                project_id,
                review_document_id,
                review_document_version_id,
            )
            final_assessment = (
                assess_approved_input_promotion_eligibility(
                    final_snapshots.document,
                    final_snapshots.artifact_set,
                    final_snapshots.source_manifest,
                    final_snapshots.processing_history,
                    final_snapshots.finalization_decision,
                )
            )
            if not final_assessment.eligible_for_promotion:
                raise ApprovedInputPromotionBlockedError(
                    "Promotion authority became invalid before "
                    "lifecycle reconciliation."
                )
            if (
                final_snapshots.artifact_set.artifact_set_fingerprint
                != initial_plan.finalized_artifact_set_fingerprint
                or final_assessment.finalization_decision_fingerprint
                != initial_plan.finalization_decision_fingerprint
            ):
                raise ApprovedInputPromotionBlockedError(
                    "Promotion authority changed before lifecycle "
                    "reconciliation."
                )
            lifecycle_events = (
                self._lifecycle_service.reconcile_finalized_version(
                    final_snapshots.artifact_set,
                    ordered_promoted,
                )
            )
        except ApprovedInputRecoveryRequiredError:
            raise
        except Exception as exc:
            raise ApprovedInputRecoveryRequiredError(
                "Approved Input manifests were reconciled only "
                "partially; lifecycle recovery must resume "
                "idempotently."
            ) from exc

        return ApprovedInputPromotionResult(
            project_id=project_id,
            review_document_id=review_document_id,
            review_document_version_id=(
                review_document_version_id
            ),
            finalized_artifact_set_fingerprint=(
                initial_plan.finalized_artifact_set_fingerprint
            ),
            promoted_manifests=ordered_promoted,
            created_approved_input_ids=tuple(created_ids),
            reused_approved_input_ids=tuple(reused_ids),
            skipped_review_item_ids=tuple(skipped_ids),
            lifecycle_event_ids=tuple(
                event.approved_input_event_id
                for event in lifecycle_events
            ),
        )

    def _current_plan_item(
        self,
        project_id: str,
        review_document_id: str,
        review_document_version_id: str,
        review_item_id: str,
        *,
        expected_plan: ApprovedInputPromotionPlan,
        timestamp: str,
    ) -> ApprovedInputPromotionPlanItem:
        """Revalidate all authority immediately before one write/reuse."""

        snapshots = self._load_current_authority(
            project_id,
            review_document_id,
            review_document_version_id,
        )
        assessment = assess_approved_input_promotion_eligibility(
            snapshots.document,
            snapshots.artifact_set,
            snapshots.source_manifest,
            snapshots.processing_history,
            snapshots.finalization_decision,
        )

        if not assessment.eligible_for_promotion:
            raise ApprovedInputPromotionBlockedError(
                "Current promotion eligibility is blocked: "
                + ", ".join(assessment.blocking_issue_codes)
            )

        if (
            snapshots.artifact_set.artifact_set_fingerprint
            != expected_plan.finalized_artifact_set_fingerprint
            or assessment.finalization_decision_fingerprint
            != expected_plan.finalization_decision_fingerprint
        ):
            raise ApprovedInputPromotionBlockedError(
                "Promotion authority changed after plan creation."
            )

        existing_manifests = (
            self._approved_input_repository.list_manifests(
                project_id
            )
        )
        active_manifests = active_approved_input_manifests(
            existing_manifests,
            self._approved_input_repository.list_events(project_id),
        )
        current_plan = create_approved_input_promotion_plan(
            snapshots.document,
            snapshots.artifact_set,
            assessment,
            existing_manifests,
            active_manifests=active_manifests,
            timestamp=timestamp,
        )

        matches = tuple(
            item
            for item in current_plan.items
            if item.review_item_id == review_item_id
        )

        if len(matches) != 1:
            raise ApprovedInputRecoveryRequiredError(
                "Current promotion plan does not contain exactly one "
                f"Review Item {review_item_id}."
            )

        return matches[0]

    def _load_current_authority(
        self,
        project_id: str,
        review_document_id: str,
        review_document_version_id: str,
    ) -> _PromotionAuthoritySnapshots:
        try:
            document = self._review_repository.load_document(
                project_id,
                review_document_id,
            )
            artifact_set = (
                self._review_repository.load_finalized_artifact_set(
                    project_id,
                    review_document_id,
                    review_document_version_id,
                )
            )
            source_manifest = self._source_registry.load_source(
                project_id,
                document.source_id,
            )
            processing_history = (
                self._processing_repository.load_run(
                    project_id,
                    document.processing_run_id,
                )
            )
            finalization_decision = (
                self._human_review_repository.load_decision(
                    project_id,
                    artifact_set.reviewed_document
                    .finalization_decision_id,
                )
            )
        except (
            ReviewWorkspaceError,
            ProjectSourceError,
            ProjectProcessingError,
            HumanReviewError,
        ) as exc:
            raise ApprovedInputReferenceError(
                "Unable to load the exact current authority snapshots "
                "required for Approved Input promotion."
            ) from exc

        return _PromotionAuthoritySnapshots(
            document=document,
            artifact_set=artifact_set,
            source_manifest=source_manifest,
            processing_history=processing_history,
            finalization_decision=finalization_decision,
        )

    def _timestamp(self) -> str:
        value = self._clock()

        if not isinstance(value, datetime):
            raise ApprovedInputValidationError(
                "clock must return a datetime."
            )

        if value.tzinfo is None or value.utcoffset() is None:
            raise ApprovedInputValidationError(
                "clock must return a timezone-aware datetime."
            )

        return (
            value.astimezone(timezone.utc)
            .isoformat(timespec="seconds")
            .replace("+00:00", "Z")
        )
