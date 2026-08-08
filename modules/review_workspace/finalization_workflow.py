"""G6 finalization preview and finalized artifact orchestration."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import re

from modules.human_review import (
    HumanReviewDecision,
    validate_human_review_decision,
)

from .effective_decisions_manifest import (
    create_effective_review_decision_set,
)
from .errors import (
    ReviewIntegrityError,
    ReviewValidationError,
)
from .finalization_authorization import (
    AuthorizedReviewDocumentFinalization,
)
from .finalization_validation import (
    ReviewFinalizationValidationAssessment,
    assess_review_document_finalization,
)
from .finalized_artifact_set import (
    FinalizedReviewArtifactSet,
    create_finalized_review_artifact_set,
)
from .reviewed_document_manifest import (
    create_finalized_reviewed_document,
)
from .reviewed_report_renderer import (
    create_rendered_reviewed_report,
)
from .types import (
    ReviewDocument,
    ReviewDocumentVersion,
    ReviewRevision,
)


_ACCEPTED_REVIEW_OUTCOMES = frozenset(
    {
        "accepted_as_generated",
        "accepted_with_modification",
        "combined",
    }
)

_ISSUE_CODE_PATTERN = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,239}$"
)


@dataclass(frozen=True, slots=True)
class ReviewFinalizationWorkflowPreview:
    """Exact G6 finalization state for one current draft head."""

    assessment: ReviewFinalizationValidationAssessment
    latest_exact_decision_id: str | None
    latest_exact_decision: str | None
    exact_confirmation_decision_id: str | None
    exact_confirmation_decision_fingerprint: str | None

    @property
    def blocking_issue_codes(self) -> tuple[str, ...]:
        return self.assessment.blocking_issue_codes

    @property
    def eligible_for_confirmation(self) -> bool:
        return self.assessment.eligible_for_finalization

    @property
    def has_exact_confirmation(self) -> bool:
        return self.exact_confirmation_decision_id is not None

    @property
    def can_finalize(self) -> bool:
        return bool(
            self.assessment.eligible_for_finalization
            and self.has_exact_confirmation
        )


def create_review_finalization_workflow_preview(
    document: ReviewDocument,
    version: ReviewDocumentVersion,
    revision: ReviewRevision,
    decisions: tuple[HumanReviewDecision, ...],
    *,
    workflow_blocking_issue_codes: tuple[str, ...] = (),
) -> ReviewFinalizationWorkflowPreview:
    """Create one fresh finalization assessment plus exact HRD state."""

    if not isinstance(document, ReviewDocument):
        raise ReviewValidationError(
            "document must be a ReviewDocument."
        )
    if not isinstance(version, ReviewDocumentVersion):
        raise ReviewValidationError(
            "version must be a ReviewDocumentVersion."
        )
    if not isinstance(revision, ReviewRevision):
        raise ReviewValidationError(
            "revision must be a ReviewRevision."
        )
    if not isinstance(decisions, tuple):
        raise ReviewValidationError(
            "decisions must be a tuple."
        )

    issue_codes = {
        *_relationship_blocking_issue_codes(revision),
        *(
            _workflow_issue_code(value)
            for value in workflow_blocking_issue_codes
        ),
    }

    assessment = assess_review_document_finalization(
        document,
        version,
        revision,
        additional_blocking_issue_codes=tuple(
            sorted(issue_codes)
        ),
    )

    exact = []

    for decision in decisions:
        validate_human_review_decision(decision)

        if decision.project_id != document.project_id:
            raise ReviewIntegrityError(
                "Finalization decisions must belong to the selected Project."
            )

        target = decision.target

        if (
            target.target_type == "review_document_finalization"
            and target.target_id == version.review_document_version_id
            and target.target_content_fingerprint
            == assessment.review_document_version_content_fingerprint
            and target.reference_validation_fingerprint
            == assessment.validation_fingerprint
        ):
            exact.append(decision)

    exact = sorted(
        exact,
        key=lambda item: item.human_review_decision_id,
    )

    latest = exact[-1] if exact else None

    confirmation = (
        latest
        if (
            latest is not None
            and latest.decision == "confirm"
            and latest.review_mode == "detailed_review"
            and latest.target.reference_validation_status == "valid"
        )
        else None
    )

    return ReviewFinalizationWorkflowPreview(
        assessment=assessment,
        latest_exact_decision_id=(
            None
            if latest is None
            else latest.human_review_decision_id
        ),
        latest_exact_decision=(
            None
            if latest is None
            else latest.decision
        ),
        exact_confirmation_decision_id=(
            None
            if confirmation is None
            else confirmation.human_review_decision_id
        ),
        exact_confirmation_decision_fingerprint=(
            None
            if confirmation is None
            else confirmation.decision_fingerprint
        ),
    )


def build_finalized_review_artifact_set(
    document: ReviewDocument,
    revision: ReviewRevision,
    finalization: AuthorizedReviewDocumentFinalization,
) -> FinalizedReviewArtifactSet:
    """Build the exact three-artifact finalized set entirely in memory."""

    if not isinstance(
        finalization,
        AuthorizedReviewDocumentFinalization,
    ):
        raise ReviewValidationError(
            "finalization must be an AuthorizedReviewDocumentFinalization."
        )

    reviewed_document = create_finalized_reviewed_document(
        document,
        finalization.finalized_version,
        revision,
        finalization.authorization,
    )
    effective_decisions = (
        create_effective_review_decision_set(
            reviewed_document,
            revision,
        )
    )
    reviewed_report = create_rendered_reviewed_report(
        reviewed_document,
        effective_decisions,
    )

    return create_finalized_review_artifact_set(
        reviewed_document,
        effective_decisions,
        reviewed_report,
    )


def _relationship_blocking_issue_codes(
    revision: ReviewRevision,
) -> tuple[str, ...]:
    result = []

    for item in revision.review_items:
        if (
            item.review_item_kind != "relationship"
            or item.effective_review_outcome
            not in _ACCEPTED_REVIEW_OUTCOMES
        ):
            continue

        relationship = (
            item.current_content.relationship_representation
        )

        if (
            relationship is None
            or relationship.validation_status != "valid"
        ):
            result.append(
                "relationship_profile_not_valid:"
                f"{item.review_item_id}"
            )

    return tuple(sorted(result))


def _workflow_issue_code(
    value: object,
) -> str:
    if not isinstance(value, str) or not value:
        raise ReviewValidationError(
            "workflow blocking issue codes must be non-empty strings."
        )

    selected = f"workflow_blocking:{value}"

    if _ISSUE_CODE_PATTERN.fullmatch(selected) is not None:
        return selected

    digest = hashlib.sha256(
        value.encode("utf-8")
    ).hexdigest()[:24]

    return f"workflow_blocking:{digest}"
