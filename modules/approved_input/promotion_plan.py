"""Build deterministic, write-free Approved Input promotion plans."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import re

from modules.review_workspace.document_manifest import (
    validate_review_document,
)
from modules.review_workspace.finalized_artifact_set import (
    FinalizedReviewArtifactSet,
    validate_finalized_review_artifact_set,
)
from modules.review_workspace.item_manifest import validate_review_item
from modules.review_workspace.types import ReviewDocument, ReviewItem

from .eligibility import (
    ApprovedInputPromotionEligibilityAssessment,
    ApprovedInputPromotionItemAssessment,
)
from .errors import (
    ApprovedInputIntegrityError,
    ApprovedInputPromotionBlockedError,
    ApprovedInputValidationError,
)
from .identifiers import next_approved_input_id
from .lifecycle import calculate_promotion_equivalence_fingerprint
from .manifest import validate_approved_input_manifest
from .promotion_materialization import (
    create_manifest_from_review_item,
)
from .types import ApprovedInputManifest


PROMOTION_PLAN_ACTIONS = frozenset(
    {
        "create",
        "reuse",
        "skip",
    }
)

_UTC_TIMESTAMP_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T"
    r"\d{2}:\d{2}:\d{2}"
    r"(?:\.\d+)?Z$"
)


@dataclass(frozen=True, slots=True)
class ApprovedInputPromotionPlanItem:
    """One deterministic item action in a promotion plan."""

    review_item_id: str
    stable_subject_key: str
    action: str
    approved_input_id: str | None
    manifest: ApprovedInputManifest | None
    reason_codes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ApprovedInputPromotionPlan:
    """Write-free plan for one exact finalized Review Version."""

    project_id: str
    review_document_id: str
    review_document_version_id: str
    review_revision_id: str
    finalized_artifact_set_fingerprint: str
    finalization_decision_fingerprint: str
    planned_at: str
    items: tuple[ApprovedInputPromotionPlanItem, ...]

    @property
    def create_item_ids(self) -> tuple[str, ...]:
        return _item_ids_for_action(self.items, "create")

    @property
    def reuse_item_ids(self) -> tuple[str, ...]:
        return _item_ids_for_action(self.items, "reuse")

    @property
    def skipped_item_ids(self) -> tuple[str, ...]:
        return _item_ids_for_action(self.items, "skip")


def create_approved_input_promotion_plan(
    document: object,
    artifact_set: object,
    assessment: object,
    existing_manifests: object,
    *,
    active_manifests: object | None = None,
    timestamp: str,
) -> ApprovedInputPromotionPlan:
    """Create one deterministic plan without persisting anything."""

    document, artifact_set, assessment = _validated_inputs(
        document,
        artifact_set,
        assessment,
        timestamp=timestamp,
    )

    if not assessment.eligible_for_promotion:
        raise ApprovedInputPromotionBlockedError(
            "Approved Input promotion is blocked: "
            + ", ".join(assessment.blocking_issue_codes)
        )

    _validate_assessment_binding(
        document,
        artifact_set,
        assessment,
    )
    manifests = _validated_existing_manifests(
        existing_manifests,
        project_id=document.project_id,
    )
    active = _validated_active_manifests(
        active_manifests,
        manifests=manifests,
        project_id=document.project_id,
    )
    review_items = _review_items_by_id(artifact_set)
    occupied_ids = [
        manifest.approved_input_id
        for manifest in manifests
    ]
    planned_items: list[ApprovedInputPromotionPlanItem] = []

    for item_assessment in assessment.item_assessments:
        review_item = review_items.get(
            item_assessment.review_item_id
        )

        if review_item is None:
            raise ApprovedInputIntegrityError(
                "Promotion assessment references a Review Item that "
                "is not in the finalized effective decision set: "
                f"{item_assessment.review_item_id}."
            )

        _validate_item_assessment_binding(
            review_item,
            item_assessment,
        )
        planned_items.append(
            _plan_review_item(
                document,
                artifact_set,
                item_assessment,
                review_item,
                manifests=manifests,
                active_manifests=active,
                occupied_ids=occupied_ids,
                timestamp=timestamp,
            )
        )

    if len(planned_items) != len(review_items):
        raise ApprovedInputIntegrityError(
            "Promotion assessment does not cover the exact finalized "
            "Review Item set."
        )

    return ApprovedInputPromotionPlan(
        project_id=document.project_id,
        review_document_id=document.review_document_id,
        review_document_version_id=(
            assessment.review_document_version_id
        ),
        review_revision_id=assessment.review_revision_id,
        finalized_artifact_set_fingerprint=(
            artifact_set.artifact_set_fingerprint
        ),
        finalization_decision_fingerprint=(
            assessment.finalization_decision_fingerprint
        ),
        planned_at=timestamp,
        items=tuple(planned_items),
    )


def _plan_review_item(
    document: ReviewDocument,
    artifact_set: FinalizedReviewArtifactSet,
    item_assessment: ApprovedInputPromotionItemAssessment,
    review_item: ReviewItem,
    *,
    manifests: tuple[ApprovedInputManifest, ...],
    active_manifests: tuple[ApprovedInputManifest, ...],
    occupied_ids: list[str],
    timestamp: str,
) -> ApprovedInputPromotionPlanItem:
    if not item_assessment.eligible_for_promotion:
        return ApprovedInputPromotionPlanItem(
            review_item_id=review_item.review_item_id,
            stable_subject_key=review_item.stable_subject_key,
            action="skip",
            approved_input_id=None,
            manifest=None,
            reason_codes=item_assessment.reason_codes,
        )

    matches = tuple(
        manifest
        for manifest in manifests
        if _idempotence_key_for_manifest(manifest)
        == _idempotence_key_for_item(
            document,
            artifact_set,
            review_item,
        )
    )

    if len(matches) > 1:
        raise ApprovedInputIntegrityError(
            "Equivalent Approved Input promotion is represented "
            "by more than one manifest: "
            f"{review_item.review_item_id}."
        )

    if matches:
        active_ids = {
            manifest.approved_input_id
            for manifest in active_manifests
        }
        if matches[0].approved_input_id not in active_ids:
            raise ApprovedInputPromotionBlockedError(
                "An equivalent Approved Input exists but a newer "
                "lifecycle event blocks its authority."
            )
        return _reuse_plan_item(
            document,
            artifact_set,
            item_assessment,
            review_item,
            matches[0],
        )

    continuity_matches = tuple(
        manifest
        for manifest in active_manifests
        if manifest.review_document_id == document.review_document_id
        and manifest.stable_subject_key == review_item.stable_subject_key
    )
    if len(continuity_matches) > 1:
        raise ApprovedInputIntegrityError(
            "More than one active Approved Input exists for the same "
            "stable Review subject."
        )
    if continuity_matches:
        existing = continuity_matches[0]
        candidate = create_manifest_from_review_item(
            document,
            artifact_set,
            item_assessment,
            review_item,
            approved_input_id=existing.approved_input_id,
            created_at=existing.created_at,
        )
        if (
            calculate_promotion_equivalence_fingerprint(candidate)
            == calculate_promotion_equivalence_fingerprint(existing)
        ):
            return ApprovedInputPromotionPlanItem(
                review_item_id=review_item.review_item_id,
                stable_subject_key=review_item.stable_subject_key,
                action="reuse",
                approved_input_id=existing.approved_input_id,
                manifest=existing,
                reason_codes=(
                    "unchanged_successor_subject",
                ),
            )

    approved_input_id = next_approved_input_id(
        tuple(occupied_ids)
    )
    occupied_ids.append(approved_input_id)
    manifest = create_manifest_from_review_item(
        document,
        artifact_set,
        item_assessment,
        review_item,
        approved_input_id=approved_input_id,
        created_at=timestamp,
    )

    return ApprovedInputPromotionPlanItem(
        review_item_id=review_item.review_item_id,
        stable_subject_key=review_item.stable_subject_key,
        action="create",
        approved_input_id=approved_input_id,
        manifest=manifest,
        reason_codes=(),
    )


def _reuse_plan_item(
    document: ReviewDocument,
    artifact_set: FinalizedReviewArtifactSet,
    item_assessment: ApprovedInputPromotionItemAssessment,
    review_item: ReviewItem,
    existing: ApprovedInputManifest,
) -> ApprovedInputPromotionPlanItem:
    expected = create_manifest_from_review_item(
        document,
        artifact_set,
        item_assessment,
        review_item,
        approved_input_id=existing.approved_input_id,
        created_at=existing.created_at,
    )

    if existing != expected:
        raise ApprovedInputIntegrityError(
            "Existing Approved Input matches the promotion "
            "idempotence key but not the exact reviewed content: "
            f"{existing.approved_input_id}."
        )

    return ApprovedInputPromotionPlanItem(
        review_item_id=review_item.review_item_id,
        stable_subject_key=review_item.stable_subject_key,
        action="reuse",
        approved_input_id=existing.approved_input_id,
        manifest=existing,
        reason_codes=(),
    )


def _validated_inputs(
    document: object,
    artifact_set: object,
    assessment: object,
    *,
    timestamp: str,
) -> tuple[
    ReviewDocument,
    FinalizedReviewArtifactSet,
    ApprovedInputPromotionEligibilityAssessment,
]:
    if not isinstance(document, ReviewDocument):
        raise ApprovedInputValidationError(
            "document must be a ReviewDocument."
        )
    if not isinstance(artifact_set, FinalizedReviewArtifactSet):
        raise ApprovedInputValidationError(
            "artifact_set must be a FinalizedReviewArtifactSet."
        )
    if not isinstance(
        assessment,
        ApprovedInputPromotionEligibilityAssessment,
    ):
        raise ApprovedInputValidationError(
            "assessment must be an "
            "ApprovedInputPromotionEligibilityAssessment."
        )

    _validate_timestamp(timestamp)

    try:
        validate_review_document(document)
        validate_finalized_review_artifact_set(artifact_set)
    except Exception as exc:
        raise ApprovedInputIntegrityError(
            "artifact_set must satisfy the finalized Review contract."
        ) from exc

    return document, artifact_set, assessment


def _validated_existing_manifests(
    values: object,
    *,
    project_id: str,
) -> tuple[ApprovedInputManifest, ...]:
    if not isinstance(values, tuple):
        raise ApprovedInputValidationError(
            "existing_manifests must be a tuple."
        )

    seen_ids: set[str] = set()
    manifests: list[ApprovedInputManifest] = []

    for manifest in values:
        if not isinstance(manifest, ApprovedInputManifest):
            raise ApprovedInputValidationError(
                "existing_manifests entries must be "
                "ApprovedInputManifest values."
            )
        validate_approved_input_manifest(manifest)

        if manifest.project_id != project_id:
            raise ApprovedInputIntegrityError(
                "Existing Approved Input manifests must remain "
                "project-local."
            )
        if manifest.approved_input_id in seen_ids:
            raise ApprovedInputIntegrityError(
                "Existing Approved Input IDs must be unique."
            )

        seen_ids.add(manifest.approved_input_id)
        manifests.append(manifest)

    return tuple(
        sorted(
            manifests,
            key=lambda manifest: manifest.approved_input_id,
        )
    )


def _validated_active_manifests(
    values: object | None,
    *,
    manifests: tuple[ApprovedInputManifest, ...],
    project_id: str,
) -> tuple[ApprovedInputManifest, ...]:
    if values is None:
        return manifests
    active = _validated_existing_manifests(
        values,
        project_id=project_id,
    )
    manifest_ids = {
        manifest.approved_input_id for manifest in manifests
    }
    for manifest in active:
        if manifest.approved_input_id not in manifest_ids:
            raise ApprovedInputIntegrityError(
                "active_manifests must be a subset of "
                "existing_manifests."
            )
    return active


def _review_items_by_id(
    artifact_set: FinalizedReviewArtifactSet,
) -> dict[str, ReviewItem]:
    items = artifact_set.effective_decisions.effective_decisions
    result = {item.review_item_id: item for item in items}

    if len(result) != len(items):
        raise ApprovedInputIntegrityError(
            "Finalized effective Review Items must have unique IDs."
        )

    return result


def _validate_assessment_binding(
    document: ReviewDocument,
    artifact_set: FinalizedReviewArtifactSet,
    assessment: ApprovedInputPromotionEligibilityAssessment,
) -> None:
    reviewed = artifact_set.reviewed_document
    bindings = (
        (assessment.project_id, document.project_id, "project_id"),
        (
            assessment.review_document_id,
            document.review_document_id,
            "review_document_id",
        ),
        (
            assessment.review_document_version_id,
            reviewed.review_document_version_id,
            "review_document_version_id",
        ),
        (
            assessment.review_revision_id,
            reviewed.review_revision_id,
            "review_revision_id",
        ),
        (
            assessment.finalized_artifact_set_fingerprint,
            artifact_set.artifact_set_fingerprint,
            "finalized_artifact_set_fingerprint",
        ),
        (
            assessment.finalization_decision_id,
            reviewed.finalization_decision_id,
            "finalization_decision_id",
        ),
        (
            assessment.finalization_decision_fingerprint,
            reviewed.finalization_decision_fingerprint,
            "finalization_decision_fingerprint",
        ),
        (
            assessment.finalization_validation_fingerprint,
            reviewed.finalization_validation_fingerprint,
            "finalization_validation_fingerprint",
        ),
    )

    for actual, expected, label in bindings:
        if actual != expected:
            raise ApprovedInputIntegrityError(
                "Promotion assessment does not bind the exact "
                f"finalized Review authority: {label}."
            )


def _validate_item_assessment_binding(
    item: ReviewItem,
    assessment: ApprovedInputPromotionItemAssessment,
) -> None:
    validate_review_item(item)
    bindings = (
        (assessment.review_item_id, item.review_item_id),
        (assessment.stable_subject_key, item.stable_subject_key),
        (assessment.review_item_kind, item.review_item_kind),
        (
            assessment.effective_review_outcome,
            item.effective_review_outcome,
        ),
        (
            assessment.review_item_fingerprint,
            item.item_content_fingerprint,
        ),
    )

    if any(actual != expected for actual, expected in bindings):
        raise ApprovedInputIntegrityError(
            "Promotion item assessment is stale or does not bind the "
            f"exact Review Item: {item.review_item_id}."
        )


def _idempotence_key_for_manifest(
    manifest: ApprovedInputManifest,
) -> tuple[str, str, str, str, str]:
    return (
        manifest.project_id,
        manifest.review_document_version_id,
        manifest.review_item_id,
        manifest.review_item_fingerprint,
        manifest.finalization_decision_fingerprint,
    )


def _idempotence_key_for_item(
    document: ReviewDocument,
    artifact_set: FinalizedReviewArtifactSet,
    item: ReviewItem,
) -> tuple[str, str, str, str, str]:
    return (
        document.project_id,
        artifact_set.reviewed_document.review_document_version_id,
        item.review_item_id,
        item.item_content_fingerprint,
        artifact_set.reviewed_document.finalization_decision_fingerprint,
    )


def _validate_timestamp(value: object) -> None:
    if (
        not isinstance(value, str)
        or _UTC_TIMESTAMP_PATTERN.fullmatch(value) is None
    ):
        raise ApprovedInputValidationError(
            "timestamp must use an ISO-8601 UTC Z timestamp."
        )

    try:
        datetime.fromisoformat(
            value.removesuffix("Z") + "+00:00"
        )
    except ValueError as exc:
        raise ApprovedInputValidationError(
            "timestamp must be a real UTC date and time."
        ) from exc


def _item_ids_for_action(
    items: tuple[ApprovedInputPromotionPlanItem, ...],
    action: str,
) -> tuple[str, ...]:
    return tuple(
        item.review_item_id
        for item in items
        if item.action == action
    )
