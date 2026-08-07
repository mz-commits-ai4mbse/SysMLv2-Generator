"""Repository-bound Approved Input lifecycle transitions and reconciliation."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path

from modules.human_review import (
    HumanReviewError,
    HumanReviewRepository,
    validate_human_review_decision,
)
from modules.review_workspace.finalized_artifact_set import (
    FinalizedReviewArtifactSet,
    validate_finalized_review_artifact_set,
)

from .errors import (
    ApprovedInputIntegrityError,
    ApprovedInputReferenceError,
    ApprovedInputValidationError,
)
from .event_manifest import create_approved_input_event
from .lifecycle import (
    active_approved_input_manifests,
    calculate_promotion_equivalence_fingerprint,
    derive_approved_input_authority_states,
)
from .repository import DEFAULT_PROJECTS_ROOT, ApprovedInputRepository
from .types import ApprovedInputEvent, ApprovedInputManifest


def _default_clock() -> datetime:
    return datetime.now(timezone.utc)


class ApprovedInputLifecycleService:
    """Append terminal lifecycle events without mutating manifests."""

    def __init__(
        self,
        root: Path | str = DEFAULT_PROJECTS_ROOT,
        *,
        clock: Callable[[], datetime] = _default_clock,
        approved_input_repository=None,
        human_review_repository=None,
    ) -> None:
        if not callable(clock):
            raise ApprovedInputValidationError(
                "clock must be callable."
            )
        self.root = Path(root)
        self._clock = clock
        self._approved_input_repository = (
            approved_input_repository
            if approved_input_repository is not None
            else ApprovedInputRepository(root=self.root)
        )
        self._human_review_repository = (
            human_review_repository
            if human_review_repository is not None
            else HumanReviewRepository(root=self.root)
        )

    def invalidate(
        self,
        project_id: str,
        approved_input_id: str,
        *,
        reason_code: str,
        actor_identity: str,
        rationale: str | None = None,
    ) -> ApprovedInputEvent:
        """Invalidate one active Approved Input for an integrity reason."""

        manifest = self._require_active(
            project_id,
            approved_input_id,
        )
        event = create_approved_input_event(
            project_id=project_id,
            approved_input_event_id=(
                self._approved_input_repository
                .next_approved_input_event_id(project_id)
            ),
            approved_input_id=manifest.approved_input_id,
            event_type="invalidated",
            reason_code=reason_code,
            rationale=rationale,
            actor_identity=actor_identity,
            successor_approved_input_id=None,
            causal_review_document_id=None,
            causal_review_document_version_id=None,
            causal_review_revision_id=None,
            causal_finalization_decision_id=None,
            causal_finalization_decision_fingerprint=None,
            occurred_at=self._timestamp(),
        )
        return self._approved_input_repository.persist_event(event)

    def revoke(
        self,
        project_id: str,
        approved_input_id: str,
        artifact_set: FinalizedReviewArtifactSet,
        *,
        rationale: str,
        reason_code: str = "successor_review_withdrawal",
    ) -> ApprovedInputEvent:
        """Revoke one active Approved Input by exact successor review."""

        manifest = self._require_active(
            project_id,
            approved_input_id,
        )
        reviewed, decision = self._confirmed_finalization(
            project_id,
            artifact_set,
        )
        if manifest.review_document_id != reviewed.review_document_id:
            raise ApprovedInputIntegrityError(
                "Revocation must remain within one Review Document."
            )
        event = create_approved_input_event(
            project_id=project_id,
            approved_input_event_id=(
                self._approved_input_repository
                .next_approved_input_event_id(project_id)
            ),
            approved_input_id=manifest.approved_input_id,
            event_type="revoked",
            reason_code=reason_code,
            rationale=rationale,
            actor_identity=decision.reviewer_identity,
            successor_approved_input_id=None,
            causal_review_document_id=reviewed.review_document_id,
            causal_review_document_version_id=(
                reviewed.review_document_version_id
            ),
            causal_review_revision_id=reviewed.review_revision_id,
            causal_finalization_decision_id=(
                reviewed.finalization_decision_id
            ),
            causal_finalization_decision_fingerprint=(
                reviewed.finalization_decision_fingerprint
            ),
            occurred_at=self._timestamp(),
        )
        return self._approved_input_repository.persist_event(event)

    def supersede(
        self,
        project_id: str,
        approved_input_id: str,
        successor_approved_input_id: str,
        artifact_set: FinalizedReviewArtifactSet,
        *,
        rationale: str | None = None,
        reason_code: str = "successor_review_item_changed",
    ) -> ApprovedInputEvent:
        """Supersede one active Approved Input with one active successor."""

        predecessor = self._require_active(
            project_id,
            approved_input_id,
        )
        successor = self._require_active(
            project_id,
            successor_approved_input_id,
        )
        reviewed, decision = self._confirmed_finalization(
            project_id,
            artifact_set,
        )

        if predecessor.approved_input_id == successor.approved_input_id:
            raise ApprovedInputIntegrityError(
                "Supersession requires distinct Approved Input IDs."
            )
        if (
            predecessor.stable_subject_key
            != successor.stable_subject_key
        ):
            raise ApprovedInputIntegrityError(
                "Supersession requires the same stable_subject_key."
            )
        if (
            successor.review_document_id
            != reviewed.review_document_id
            or successor.review_document_version_id
            != reviewed.review_document_version_id
            or successor.review_revision_id
            != reviewed.review_revision_id
            or successor.finalization_decision_id
            != reviewed.finalization_decision_id
            or successor.finalization_decision_fingerprint
            != reviewed.finalization_decision_fingerprint
        ):
            raise ApprovedInputIntegrityError(
                "Superseding Approved Input does not bind the exact "
                "successor finalization."
            )
        if (
            calculate_promotion_equivalence_fingerprint(predecessor)
            == calculate_promotion_equivalence_fingerprint(successor)
        ):
            raise ApprovedInputIntegrityError(
                "Equivalent successor content must retain the existing "
                "Approved Input instead of superseding it."
            )

        event = create_approved_input_event(
            project_id=project_id,
            approved_input_event_id=(
                self._approved_input_repository
                .next_approved_input_event_id(project_id)
            ),
            approved_input_id=predecessor.approved_input_id,
            event_type="superseded",
            reason_code=reason_code,
            rationale=rationale,
            actor_identity=decision.reviewer_identity,
            successor_approved_input_id=successor.approved_input_id,
            causal_review_document_id=reviewed.review_document_id,
            causal_review_document_version_id=(
                reviewed.review_document_version_id
            ),
            causal_review_revision_id=reviewed.review_revision_id,
            causal_finalization_decision_id=(
                reviewed.finalization_decision_id
            ),
            causal_finalization_decision_fingerprint=(
                reviewed.finalization_decision_fingerprint
            ),
            occurred_at=self._timestamp(),
        )
        return self._approved_input_repository.persist_event(event)

    def reconcile_finalized_version(
        self,
        artifact_set: FinalizedReviewArtifactSet,
        promoted_manifests: tuple[ApprovedInputManifest, ...],
    ) -> tuple[ApprovedInputEvent, ...]:
        """Reconcile one finalized successor version item by item."""

        validate_finalized_review_artifact_set(artifact_set)
        if not isinstance(promoted_manifests, tuple):
            raise ApprovedInputValidationError(
                "promoted_manifests must be a tuple."
            )
        reviewed = artifact_set.reviewed_document
        project_id = reviewed.project_id
        promoted_by_subject: dict[str, ApprovedInputManifest] = {}
        for manifest in promoted_manifests:
            if not isinstance(manifest, ApprovedInputManifest):
                raise ApprovedInputValidationError(
                    "promoted_manifests entries must be manifests."
                )
            if manifest.project_id != project_id:
                raise ApprovedInputIntegrityError(
                    "Promoted manifests must remain project-local."
                )
            if manifest.stable_subject_key in promoted_by_subject:
                raise ApprovedInputIntegrityError(
                    "Promoted stable_subject_key values must be unique."
                )
            promoted_by_subject[manifest.stable_subject_key] = manifest

        created_events: list[ApprovedInputEvent] = []
        items = artifact_set.effective_decisions.effective_decisions
        seen_subjects: set[str] = set()

        for item in items:
            subject = item.stable_subject_key
            if subject in seen_subjects:
                raise ApprovedInputIntegrityError(
                    "Finalized Review Items must have unique stable subjects "
                    "for lifecycle reconciliation."
                )
            seen_subjects.add(subject)

            active = self._active_for_subject(
                project_id,
                reviewed.review_document_id,
                subject,
            )
            outcome = item.effective_review_outcome

            if outcome in {
                "accepted_as_generated",
                "accepted_with_modification",
                "combined",
            }:
                current = promoted_by_subject.get(subject)
                if current is None:
                    # G5.4 option A: accepted open questions remain
                    # non-promotable until an explicit conversion exists.
                    continue
                predecessors = tuple(
                    manifest
                    for manifest in active
                    if manifest.approved_input_id
                    != current.approved_input_id
                )
                if len(predecessors) > 1:
                    raise ApprovedInputIntegrityError(
                        "Multiple active predecessor Approved Inputs exist "
                        "for one stable subject."
                    )
                if predecessors:
                    created_events.append(
                        self.supersede(
                            project_id,
                            predecessors[0].approved_input_id,
                            current.approved_input_id,
                            artifact_set,
                            rationale=item.current_content.human_rationale,
                        )
                    )
                continue

            if outcome in {"rejected", "out_of_scope"}:
                if len(active) > 1:
                    raise ApprovedInputIntegrityError(
                        "Multiple active Approved Inputs exist for one "
                        "withdrawn stable subject."
                    )
                if not active:
                    continue
                rationale = item.current_content.human_rationale
                if not isinstance(rationale, str) or not rationale.strip():
                    raise ApprovedInputIntegrityError(
                        "Revoking a previous Approved Input requires the "
                        "human rationale from the finalized Review Item."
                    )
                created_events.append(
                    self.revoke(
                        project_id,
                        active[0].approved_input_id,
                        artifact_set,
                        rationale=rationale,
                        reason_code=(
                            "successor_review_rejected"
                            if outcome == "rejected"
                            else "successor_review_out_of_scope"
                        ),
                    )
                )

            # deferred and non-promotable question outcomes deliberately
            # leave existing authority unchanged.

        return tuple(created_events)

    def _active_for_subject(
        self,
        project_id: str,
        review_document_id: str,
        stable_subject_key: str,
    ) -> tuple[ApprovedInputManifest, ...]:
        manifests = self._approved_input_repository.list_manifests(
            project_id
        )
        events = self._approved_input_repository.list_events(project_id)
        active = active_approved_input_manifests(manifests, events)
        return tuple(
            manifest
            for manifest in active
            if manifest.review_document_id == review_document_id
            and manifest.stable_subject_key == stable_subject_key
        )

    def _require_active(
        self,
        project_id: str,
        approved_input_id: str,
    ) -> ApprovedInputManifest:
        manifest = self._approved_input_repository.load_manifest(
            project_id,
            approved_input_id,
        )
        snapshots = derive_approved_input_authority_states(
            self._approved_input_repository.list_manifests(project_id),
            self._approved_input_repository.list_events(project_id),
        )
        matches = tuple(
            snapshot
            for snapshot in snapshots
            if snapshot.manifest.approved_input_id == approved_input_id
        )
        if len(matches) != 1:
            raise ApprovedInputIntegrityError(
                "Approved Input authority state cannot be derived exactly."
            )
        if matches[0].authority_state != "active":
            raise ApprovedInputIntegrityError(
                "Only an active Approved Input may receive a G5.6 "
                "lifecycle transition."
            )
        return manifest

    def _confirmed_finalization(
        self,
        project_id: str,
        artifact_set: FinalizedReviewArtifactSet,
    ):
        validate_finalized_review_artifact_set(artifact_set)
        reviewed = artifact_set.reviewed_document
        if reviewed.project_id != project_id:
            raise ApprovedInputIntegrityError(
                "Lifecycle finalization evidence crosses a Project boundary."
            )
        try:
            decision = self._human_review_repository.load_decision(
                project_id,
                reviewed.finalization_decision_id,
            )
            validate_human_review_decision(decision)
        except HumanReviewError as exc:
            raise ApprovedInputReferenceError(
                "Exact finalization Human Review Decision is unavailable."
            ) from exc

        bindings = (
            (
                decision.decision_fingerprint,
                reviewed.finalization_decision_fingerprint,
                "decision fingerprint",
            ),
            (
                decision.target.target_type,
                "review_document_finalization",
                "target type",
            ),
            (
                decision.target.target_id,
                reviewed.review_document_version_id,
                "target ID",
            ),
            (
                decision.target.target_content_fingerprint,
                reviewed.draft_version_content_fingerprint,
                "target content fingerprint",
            ),
            (
                decision.target.reference_validation_fingerprint,
                reviewed.finalization_validation_fingerprint,
                "validation fingerprint",
            ),
            (
                decision.reviewer_identity,
                reviewed.reviewer_identity,
                "reviewer identity",
            ),
        )
        for actual, expected, label in bindings:
            if actual != expected:
                raise ApprovedInputIntegrityError(
                    "Lifecycle finalization decision does not match exact "
                    f"{label}."
                )
        if (
            decision.decision != "confirm"
            or decision.review_mode != "detailed_review"
            or decision.target.reference_validation_status == "invalid"
        ):
            raise ApprovedInputIntegrityError(
                "Lifecycle requires the exact detailed finalization "
                "confirmation."
            )
        return reviewed, decision

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
