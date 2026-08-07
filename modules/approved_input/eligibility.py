"""Deterministic eligibility assessment for Approved Input promotion."""

from __future__ import annotations

from dataclasses import dataclass

from modules.human_review import (
    HumanReviewDecision,
    validate_human_review_decision,
)
from modules.project_processing import (
    ProcessingRunHistory,
    derive_processing_artifact_lifecycles,
    derive_processing_run_state,
    validate_processing_run_history,
)
from modules.project_processing.errors import ProjectProcessingError
from modules.project_processing.types import ProcessingArtifactReference
from modules.project_sources.types import SourceManifest
from modules.review_workspace.document_manifest import (
    validate_review_document,
)
from modules.review_workspace.errors import ReviewWorkspaceError
from modules.review_workspace.finalized_artifact_set import (
    FinalizedReviewArtifactSet,
    validate_finalized_review_artifact_set,
)
from modules.review_workspace.types import ReviewDocument, ReviewItem

from .errors import (
    ApprovedInputIntegrityError,
    ApprovedInputValidationError,
)


PROMOTABLE_REVIEW_ITEM_OUTCOMES = frozenset(
    {
        "accepted_as_generated",
        "accepted_with_modification",
        "combined",
    }
)

PROMOTION_ALLOWED_RUN_STATES = frozenset(
    {
        "awaiting_review",
        "completed",
    }
)

_APPROVED_INPUT_KIND_BY_REVIEW_ITEM_KIND = {
    "element": "element_statement",
    "relationship": "relationship_statement",
}


@dataclass(frozen=True, slots=True)
class ApprovedInputPromotionItemAssessment:
    """Promotion eligibility of one finalized Review Item."""

    review_item_id: str
    stable_subject_key: str
    review_item_kind: str
    effective_review_outcome: str
    review_item_fingerprint: str
    approved_input_kind: str | None
    eligible_for_promotion: bool
    reason_codes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ApprovedInputPromotionEligibilityAssessment:
    """Exact advisory assessment of one finalized Review Version."""

    project_id: str
    review_document_id: str
    review_document_version_id: str
    review_revision_id: str
    finalized_artifact_set_fingerprint: str
    finalization_decision_id: str
    finalization_decision_fingerprint: str
    finalization_validation_fingerprint: str
    item_assessments: tuple[
        ApprovedInputPromotionItemAssessment,
        ...,
    ]
    blocking_issue_codes: tuple[str, ...]
    eligible_for_promotion: bool

    @property
    def promotable_item_ids(self) -> tuple[str, ...]:
        """Return promotable Review Item IDs in deterministic order."""

        return tuple(
            item.review_item_id
            for item in self.item_assessments
            if item.eligible_for_promotion
        )


def assess_approved_input_promotion_eligibility(
    document: object,
    artifact_set: object,
    source_manifest: object,
    processing_history: object,
    finalization_decision: object,
) -> ApprovedInputPromotionEligibilityAssessment:
    """Assess exact current authority snapshots for promotion.

    This operation is read-only. It accepts validated authority snapshots
    and never persists Approved Input. G5.5 is responsible for loading these
    snapshots fresh immediately before promotion and for calling this
    assessment again before any write.
    """

    document = _validated_document(document)
    artifact_set = _validated_artifact_set(artifact_set)
    source_manifest = _validated_source_manifest(source_manifest)
    processing_history = _validated_processing_history(
        processing_history
    )
    finalization_decision = _validated_finalization_decision(
        finalization_decision
    )

    reviewed_document = artifact_set.reviewed_document
    issue_codes: set[str] = set()

    _collect_review_binding_issues(
        document,
        artifact_set,
        issue_codes,
    )
    _collect_source_binding_issues(
        document,
        source_manifest,
        issue_codes,
    )
    _collect_processing_binding_issues(
        document,
        processing_history,
        issue_codes,
    )
    _collect_finalization_decision_issues(
        reviewed_document,
        finalization_decision,
        issue_codes,
    )

    item_assessments = tuple(
        sorted(
            (
                _assess_review_item(item)
                for item in (
                    artifact_set
                    .effective_decisions
                    .effective_decisions
                )
            ),
            key=lambda item: item.review_item_id,
        )
    )

    for item in item_assessments:
        if (
            item.review_item_kind == "relationship"
            and item.effective_review_outcome
            in PROMOTABLE_REVIEW_ITEM_OUTCOMES
            and not item.eligible_for_promotion
        ):
            issue_codes.add(
                "accepted_relationship_not_promotable:"
                f"{item.review_item_id}"
            )

    blocking_issue_codes = tuple(sorted(issue_codes))

    return ApprovedInputPromotionEligibilityAssessment(
        project_id=reviewed_document.project_id,
        review_document_id=(
            reviewed_document.review_document_id
        ),
        review_document_version_id=(
            reviewed_document.review_document_version_id
        ),
        review_revision_id=(
            reviewed_document.review_revision_id
        ),
        finalized_artifact_set_fingerprint=(
            artifact_set.artifact_set_fingerprint
        ),
        finalization_decision_id=(
            reviewed_document.finalization_decision_id
        ),
        finalization_decision_fingerprint=(
            reviewed_document
            .finalization_decision_fingerprint
        ),
        finalization_validation_fingerprint=(
            reviewed_document
            .finalization_validation_fingerprint
        ),
        item_assessments=item_assessments,
        blocking_issue_codes=blocking_issue_codes,
        eligible_for_promotion=not blocking_issue_codes,
    )


def _validated_document(value: object) -> ReviewDocument:
    if not isinstance(value, ReviewDocument):
        raise ApprovedInputValidationError(
            "document must be a ReviewDocument."
        )

    try:
        validate_review_document(value)
    except ReviewWorkspaceError as exc:
        raise ApprovedInputValidationError(
            "document must satisfy the Review Document contract."
        ) from exc

    return value


def _validated_artifact_set(
    value: object,
) -> FinalizedReviewArtifactSet:
    if not isinstance(value, FinalizedReviewArtifactSet):
        raise ApprovedInputValidationError(
            "artifact_set must be a FinalizedReviewArtifactSet."
        )

    try:
        validate_finalized_review_artifact_set(value)
    except ReviewWorkspaceError as exc:
        raise ApprovedInputIntegrityError(
            "Finalized Review Artifact Set is invalid."
        ) from exc

    return value


def _validated_source_manifest(value: object) -> SourceManifest:
    if not isinstance(value, SourceManifest):
        raise ApprovedInputValidationError(
            "source_manifest must be a SourceManifest."
        )

    return value


def _validated_processing_history(
    value: object,
) -> ProcessingRunHistory:
    if not isinstance(value, ProcessingRunHistory):
        raise ApprovedInputValidationError(
            "processing_history must be a ProcessingRunHistory."
        )

    try:
        return validate_processing_run_history(value)
    except ProjectProcessingError as exc:
        raise ApprovedInputIntegrityError(
            "Processing Run history is invalid."
        ) from exc


def _validated_finalization_decision(
    value: object,
) -> HumanReviewDecision:
    if not isinstance(value, HumanReviewDecision):
        raise ApprovedInputValidationError(
            "finalization_decision must be a HumanReviewDecision."
        )

    try:
        validate_human_review_decision(value)
    except Exception as exc:
        raise ApprovedInputIntegrityError(
            "Human Review finalization decision is invalid."
        ) from exc

    return value


def _collect_review_binding_issues(
    document: ReviewDocument,
    artifact_set: FinalizedReviewArtifactSet,
    issues: set[str],
) -> None:
    reviewed_document = artifact_set.reviewed_document

    bindings = (
        (
            document.project_id,
            reviewed_document.project_id,
            "review_project_binding_mismatch",
        ),
        (
            document.review_document_id,
            reviewed_document.review_document_id,
            "review_document_binding_mismatch",
        ),
        (
            document.source_id,
            reviewed_document.source_id,
            "review_source_binding_mismatch",
        ),
        (
            document.source_sha256,
            reviewed_document.source_sha256,
            "review_source_fingerprint_mismatch",
        ),
        (
            document.processing_run_id,
            reviewed_document.processing_run_id,
            "review_processing_run_binding_mismatch",
        ),
        (
            document.attempt_id,
            reviewed_document.attempt_id,
            "review_processing_attempt_binding_mismatch",
        ),
        (
            document.content_fingerprint,
            reviewed_document.review_document_content_fingerprint,
            "review_document_fingerprint_mismatch",
        ),
    )

    for actual, expected, code in bindings:
        if actual != expected:
            issues.add(code)


def _collect_source_binding_issues(
    document: ReviewDocument,
    source_manifest: SourceManifest,
    issues: set[str],
) -> None:
    if source_manifest.project_id != document.project_id:
        issues.add("source_project_binding_mismatch")

    if source_manifest.source_id != document.source_id:
        issues.add("source_identity_mismatch")

    if source_manifest.sha256 != document.source_sha256:
        issues.add("source_fingerprint_mismatch")

    if source_manifest.source_role != "engineering_source":
        issues.add("source_not_engineering_source")


def _collect_processing_binding_issues(
    document: ReviewDocument,
    history: ProcessingRunHistory,
    issues: set[str],
) -> None:
    manifest = history.manifest

    if manifest.project_id != document.project_id:
        issues.add("processing_project_binding_mismatch")

    if manifest.processing_run_id != document.processing_run_id:
        issues.add("processing_run_identity_mismatch")

    if manifest.source_id != document.source_id:
        issues.add("processing_source_identity_mismatch")

    if manifest.source_sha256 != document.source_sha256:
        issues.add("processing_source_fingerprint_mismatch")

    if manifest.source_role_snapshot != "engineering_source":
        issues.add("processing_source_role_not_engineering")

    if (
        manifest.workflow_profile
        != "engineering_source_processing"
    ):
        issues.add("processing_workflow_not_engineering")

    if (
        manifest.framework_template_id
        != document.framework_template.template_id
        or manifest.framework_template_version
        != document.framework_template.template_version
    ):
        issues.add("framework_reference_mismatch")

    if (
        manifest.semantic_reference_versions
        != document.semantic_reference_versions
    ):
        issues.add("semantic_reference_versions_mismatch")

    state = derive_processing_run_state(history)

    if state.run_state not in PROMOTION_ALLOWED_RUN_STATES:
        issues.add(
            "processing_run_not_promotable:"
            f"{state.run_state}"
        )

    if state.latest_attempt_id != document.attempt_id:
        issues.add("processing_attempt_not_current")

    published_references = _published_references_for_attempt(
        history,
        document.attempt_id,
    )

    required_references = (
        document.primary_review_artifact_reference,
        *document.supporting_artifact_references,
    )

    for reference in required_references:
        if reference not in published_references:
            issues.add(
                "review_artifact_not_published_in_attempt:"
                f"{reference.artifact_id}"
            )

    try:
        lifecycles = derive_processing_artifact_lifecycles(
            (history,)
        )
    except ProjectProcessingError as exc:
        raise ApprovedInputIntegrityError(
            "Processing artifact lifecycle cannot be derived."
        ) from exc

    lifecycle_by_key = {
        _reference_identity(item.artifact_reference): item
        for item in lifecycles
    }

    for reference in required_references:
        lifecycle = lifecycle_by_key.get(
            _reference_identity(reference)
        )

        if lifecycle is None:
            issues.add(
                "review_artifact_lifecycle_missing:"
                f"{reference.artifact_id}"
            )
            continue

        if lifecycle.artifact_reference != reference:
            issues.add(
                "review_artifact_reference_changed:"
                f"{reference.artifact_id}"
            )
            continue

        if lifecycle.lifecycle_state != "active":
            issues.add(
                "review_artifact_not_active:"
                f"{reference.artifact_id}"
            )


def _collect_finalization_decision_issues(
    reviewed_document,
    decision: HumanReviewDecision,
    issues: set[str],
) -> None:
    if decision.project_id != reviewed_document.project_id:
        issues.add("finalization_decision_project_mismatch")

    if (
        decision.human_review_decision_id
        != reviewed_document.finalization_decision_id
    ):
        issues.add("finalization_decision_identity_mismatch")

    if (
        decision.decision_fingerprint
        != reviewed_document.finalization_decision_fingerprint
    ):
        issues.add("finalization_decision_fingerprint_mismatch")

    target = decision.target

    if target.target_type != "review_document_finalization":
        issues.add("finalization_decision_target_type_mismatch")

    if (
        target.target_id
        != reviewed_document.review_document_version_id
    ):
        issues.add("finalization_decision_target_id_mismatch")

    if (
        target.target_content_fingerprint
        != reviewed_document.draft_version_content_fingerprint
    ):
        issues.add("finalization_decision_target_fingerprint_mismatch")

    if (
        target.reference_validation_fingerprint
        != reviewed_document.finalization_validation_fingerprint
    ):
        issues.add("finalization_validation_fingerprint_mismatch")

    if target.reference_validation_status != "valid":
        issues.add("finalization_reference_validation_not_valid")

    if decision.decision != "confirm":
        issues.add("finalization_decision_not_confirmed")

    if decision.review_mode != "detailed_review":
        issues.add("finalization_review_mode_not_detailed")

    if decision.reviewer_identity != reviewed_document.reviewer_identity:
        issues.add("finalization_reviewer_identity_mismatch")

    if decision.decided_at != reviewed_document.decision_at:
        issues.add("finalization_decision_time_mismatch")


def _assess_review_item(
    item: ReviewItem,
) -> ApprovedInputPromotionItemAssessment:
    reason_codes: list[str] = []

    if (
        item.effective_review_outcome
        not in PROMOTABLE_REVIEW_ITEM_OUTCOMES
    ):
        reason_codes.append(
            "review_outcome_not_promotable:"
            f"{item.effective_review_outcome}"
        )

    if item.review_item_kind == "open_question":
        reason_codes.append(
            "open_question_conversion_not_supported"
        )

    if (
        item.review_item_kind == "relationship"
        and item.effective_review_outcome
        in PROMOTABLE_REVIEW_ITEM_OUTCOMES
    ):
        relationship = (
            item.current_content.relationship_representation
        )

        if relationship is None:
            reason_codes.append(
                "relationship_representation_missing"
            )
        elif relationship.validation_status != "valid":
            reason_codes.append(
                "relationship_profile_not_valid"
            )

    eligible = not reason_codes

    return ApprovedInputPromotionItemAssessment(
        review_item_id=item.review_item_id,
        stable_subject_key=item.stable_subject_key,
        review_item_kind=item.review_item_kind,
        effective_review_outcome=(
            item.effective_review_outcome
        ),
        review_item_fingerprint=(
            item.item_content_fingerprint
        ),
        approved_input_kind=(
            _APPROVED_INPUT_KIND_BY_REVIEW_ITEM_KIND.get(
                item.review_item_kind
            )
            if eligible
            else None
        ),
        eligible_for_promotion=eligible,
        reason_codes=tuple(sorted(reason_codes)),
    )


def _published_references_for_attempt(
    history: ProcessingRunHistory,
    attempt_id: str,
) -> tuple[ProcessingArtifactReference, ...]:
    references: list[ProcessingArtifactReference] = []

    for event in history.events:
        if (
            event.event_type == "artifact_published"
            and event.attempt_id == attempt_id
        ):
            references.extend(event.artifact_references)

    return tuple(references)


def _reference_identity(
    reference: ProcessingArtifactReference,
) -> tuple[str, str]:
    return (
        reference.artifact_type,
        reference.artifact_id,
    )
