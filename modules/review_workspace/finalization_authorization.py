"""Authorize one exact Review Document Version finalization."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
import hashlib
import json
import re

from modules.human_review import (
    HumanReviewDecision,
    HumanReviewRepository,
    validate_human_review_decision,
    validate_human_review_decision_id,
)
from modules.project_workspace.identifiers import (
    is_valid_project_id,
)

from .errors import (
    ReviewFinalizationBlockedError,
    ReviewIntegrityError,
    ReviewValidationError,
)
from .finalization_validation import (
    ReviewFinalizationValidationAssessment,
    validate_review_finalization_assessment,
)
from .identifiers import (
    validate_review_document_id,
    validate_review_document_version_id,
    validate_review_revision_id,
)
from .revision_manifest import (
    validate_review_revision,
)
from .types import (
    ReviewDocumentVersion,
    ReviewRevision,
)
from .version_manifest import (
    finalize_review_document_version,
    validate_review_document_version,
)


REVIEW_FINALIZATION_AUTHORIZATION_SCHEMA_VERSION = (
    "1.0.0"
)

_SHA256_PATTERN = re.compile(
    r"^[0-9a-f]{64}$"
)
_UTC_TIMESTAMP_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T"
    r"\d{2}:\d{2}:\d{2}"
    r"(?:\.\d+)?Z$"
)


@dataclass(frozen=True, slots=True)
class ReviewFinalizationAuthorization:
    """Exact immutable authorization for one finalization transition."""

    schema_version: str
    project_id: str
    review_document_id: str
    review_document_version_id: str
    review_revision_id: str
    draft_version_content_fingerprint: str
    review_revision_fingerprint: str
    validation_fingerprint: str
    human_review_decision_id: str
    human_review_decision_fingerprint: str
    reviewer_identity: str
    decided_at: str
    finalized_at: str
    finalized_version_content_fingerprint: str
    authorization_fingerprint: str


@dataclass(frozen=True, slots=True)
class AuthorizedReviewDocumentFinalization:
    """One authorized in-memory Review Version transition."""

    finalized_version: ReviewDocumentVersion
    authorization: ReviewFinalizationAuthorization


def authorize_review_document_finalization(
    version: object,
    revision: object,
    assessment: object,
    decision: object,
    *,
    timestamp: str,
) -> AuthorizedReviewDocumentFinalization:
    """Authorize and construct one exact finalized version.

    This function performs no persistence. It verifies an exact Human
    Review Decision and returns the immutable authorized transition.
    """

    if not isinstance(
        version,
        ReviewDocumentVersion,
    ):
        raise ReviewValidationError(
            "version must be a ReviewDocumentVersion."
        )

    if not isinstance(revision, ReviewRevision):
        raise ReviewValidationError(
            "revision must be a ReviewRevision."
        )

    if not isinstance(
        assessment,
        ReviewFinalizationValidationAssessment,
    ):
        raise ReviewValidationError(
            "assessment must be a "
            "ReviewFinalizationValidationAssessment."
        )

    if not isinstance(
        decision,
        HumanReviewDecision,
    ):
        raise ReviewValidationError(
            "decision must be a HumanReviewDecision."
        )

    validate_review_document_version(version)
    validate_review_revision(revision)
    validate_review_finalization_assessment(
        assessment
    )
    validate_human_review_decision(decision)

    if not assessment.eligible_for_finalization:
        issue_text = ", ".join(
            assessment.blocking_issue_codes
        )

        raise ReviewFinalizationBlockedError(
            "Review Document Version finalization "
            "is blocked"
            + (
                f": {issue_text}."
                if issue_text
                else "."
            )
        )

    _validate_exact_review_binding(
        version,
        revision,
        assessment,
    )
    _validate_exact_decision_binding(
        version,
        assessment,
        decision,
    )

    finalized_version = (
        finalize_review_document_version(
            version,
            finalized_revision_id=(
                revision.review_revision_id
            ),
            finalization_decision_id=(
                decision.human_review_decision_id
            ),
            timestamp=timestamp,
        )
    )

    provisional_authorization = (
        ReviewFinalizationAuthorization(
            schema_version=(
                REVIEW_FINALIZATION_AUTHORIZATION_SCHEMA_VERSION
            ),
            project_id=version.project_id,
            review_document_id=(
                version.review_document_id
            ),
            review_document_version_id=(
                version.review_document_version_id
            ),
            review_revision_id=(
                revision.review_revision_id
            ),
            draft_version_content_fingerprint=(
                version.content_fingerprint
            ),
            review_revision_fingerprint=(
                revision.revision_fingerprint
            ),
            validation_fingerprint=(
                assessment.validation_fingerprint
            ),
            human_review_decision_id=(
                decision.human_review_decision_id
            ),
            human_review_decision_fingerprint=(
                decision.decision_fingerprint
            ),
            reviewer_identity=(
                decision.reviewer_identity
            ),
            decided_at=decision.decided_at,
            finalized_at=timestamp,
            finalized_version_content_fingerprint=(
                finalized_version.content_fingerprint
            ),
            authorization_fingerprint="0" * 64,
        )
    )

    authorization = replace(
        provisional_authorization,
        authorization_fingerprint=(
            calculate_review_finalization_authorization_fingerprint(
                provisional_authorization
            )
        ),
    )

    validate_review_finalization_authorization(
        authorization
    )

    return AuthorizedReviewDocumentFinalization(
        finalized_version=finalized_version,
        authorization=authorization,
    )


def authorize_persisted_review_document_finalization(
    version: object,
    revision: object,
    assessment: object,
    human_review_repository: object,
    *,
    timestamp: str,
) -> AuthorizedReviewDocumentFinalization:
    """Require the latest exact persisted confirmation and finalize."""

    if not isinstance(
        human_review_repository,
        HumanReviewRepository,
    ):
        raise ReviewValidationError(
            "human_review_repository must be a "
            "HumanReviewRepository."
        )

    if not isinstance(
        assessment,
        ReviewFinalizationValidationAssessment,
    ):
        raise ReviewValidationError(
            "assessment must be a "
            "ReviewFinalizationValidationAssessment."
        )

    validate_review_finalization_assessment(
        assessment
    )

    decision = (
        human_review_repository.require_confirmation(
            assessment.project_id,
            target_type=(
                "review_document_finalization"
            ),
            target_id=(
                assessment
                .review_document_version_id
            ),
            target_content_fingerprint=(
                assessment
                .review_document_version_content_fingerprint
            ),
            reference_validation_fingerprint=(
                assessment.validation_fingerprint
            ),
        )
    )

    return authorize_review_document_finalization(
        version,
        revision,
        assessment,
        decision,
        timestamp=timestamp,
    )


def calculate_review_finalization_authorization_fingerprint(
    authorization: ReviewFinalizationAuthorization,
) -> str:
    """Calculate one deterministic authorization fingerprint."""

    _validate_authorization(
        authorization,
        verify_fingerprint=False,
    )

    payload = _authorization_payload(
        authorization,
        include_fingerprint=False,
    )

    canonical_json = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )

    return hashlib.sha256(
        canonical_json.encode("utf-8")
    ).hexdigest()


def validate_review_finalization_authorization(
    authorization: ReviewFinalizationAuthorization,
) -> None:
    """Validate one complete finalization authorization."""

    _validate_authorization(
        authorization,
        verify_fingerprint=True,
    )


def _validate_exact_review_binding(
    version: ReviewDocumentVersion,
    revision: ReviewRevision,
    assessment: ReviewFinalizationValidationAssessment,
) -> None:
    if assessment.project_id != version.project_id:
        raise ReviewIntegrityError(
            "Finalization assessment project_id "
            "does not match the Review Version."
        )

    if revision.project_id != version.project_id:
        raise ReviewIntegrityError(
            "Review Revision project_id does not "
            "match the Review Version."
        )

    if (
        assessment.review_document_id
        != version.review_document_id
    ):
        raise ReviewIntegrityError(
            "Finalization assessment does not belong "
            "to the Review Document."
        )

    if (
        revision.review_document_id
        != version.review_document_id
    ):
        raise ReviewIntegrityError(
            "Review Revision does not belong to the "
            "Review Document."
        )

    if (
        assessment.review_document_version_id
        != version.review_document_version_id
    ):
        raise ReviewIntegrityError(
            "Finalization assessment does not belong "
            "to the Review Document Version."
        )

    if (
        revision.review_document_version_id
        != version.review_document_version_id
    ):
        raise ReviewIntegrityError(
            "Review Revision does not belong to the "
            "Review Document Version."
        )

    if (
        assessment.review_revision_id
        != revision.review_revision_id
    ):
        raise ReviewIntegrityError(
            "Finalization assessment does not bind "
            "the selected Review Revision."
        )

    if (
        version.head_revision_id
        != revision.review_revision_id
    ):
        raise ReviewIntegrityError(
            "Finalization requires the current "
            "Review Version head revision."
        )

    if (
        assessment
        .review_document_version_content_fingerprint
        != version.content_fingerprint
    ):
        raise ReviewIntegrityError(
            "Finalization assessment Review Version "
            "content fingerprint is stale."
        )

    if (
        assessment.review_revision_fingerprint
        != revision.revision_fingerprint
    ):
        raise ReviewIntegrityError(
            "Finalization assessment Review Revision "
            "fingerprint is stale."
        )


def _validate_exact_decision_binding(
    version: ReviewDocumentVersion,
    assessment: ReviewFinalizationValidationAssessment,
    decision: HumanReviewDecision,
) -> None:
    if decision.project_id != version.project_id:
        raise ReviewIntegrityError(
            "Human Review Decision project_id does "
            "not match the Review Version."
        )

    target = decision.target

    if (
        target.target_type
        != "review_document_finalization"
    ):
        raise ReviewIntegrityError(
            "Human Review Decision does not target "
            "Review Document finalization."
        )

    if (
        target.target_id
        != version.review_document_version_id
    ):
        raise ReviewIntegrityError(
            "Human Review Decision does not target "
            "the selected Review Document Version."
        )

    if (
        target.target_content_fingerprint
        != assessment
        .review_document_version_content_fingerprint
    ):
        raise ReviewIntegrityError(
            "Human Review Decision target content "
            "fingerprint does not match the "
            "Finalization Assessment."
        )

    if (
        target.reference_validation_fingerprint
        != assessment.validation_fingerprint
    ):
        raise ReviewIntegrityError(
            "Human Review Decision validation "
            "fingerprint does not match the "
            "Finalization Assessment."
        )

    if (
        target.reference_validation_status
        != "valid"
    ):
        raise ReviewFinalizationBlockedError(
            "Review Document finalization requires "
            "a validation-valid Human Review target."
        )

    if (
        target.recommended_review_mode
        != "detailed_review"
        or decision.review_mode
        != "detailed_review"
    ):
        raise ReviewFinalizationBlockedError(
            "Review Document finalization requires "
            "detailed_review."
        )

    if decision.decision != "confirm":
        raise ReviewFinalizationBlockedError(
            "Review Document finalization requires "
            "an exact confirm decision."
        )


def _validate_authorization(
    authorization: ReviewFinalizationAuthorization,
    *,
    verify_fingerprint: bool,
) -> None:
    if not isinstance(
        authorization,
        ReviewFinalizationAuthorization,
    ):
        raise ReviewValidationError(
            "authorization must be a "
            "ReviewFinalizationAuthorization."
        )

    if (
        authorization.schema_version
        != REVIEW_FINALIZATION_AUTHORIZATION_SCHEMA_VERSION
    ):
        raise ReviewValidationError(
            "Invalid Review Finalization "
            "Authorization schema_version."
        )

    if not is_valid_project_id(
        authorization.project_id
    ):
        raise ReviewValidationError(
            "project_id must be a valid "
            "six-digit Project ID."
        )

    validate_review_document_id(
        authorization.review_document_id
    )
    validate_review_document_version_id(
        authorization.review_document_version_id
    )
    validate_review_revision_id(
        authorization.review_revision_id
    )
    validate_human_review_decision_id(
        authorization.human_review_decision_id
    )

    for label, value in (
        (
            "draft_version_content_fingerprint",
            authorization
            .draft_version_content_fingerprint,
        ),
        (
            "review_revision_fingerprint",
            authorization
            .review_revision_fingerprint,
        ),
        (
            "validation_fingerprint",
            authorization.validation_fingerprint,
        ),
        (
            "human_review_decision_fingerprint",
            authorization
            .human_review_decision_fingerprint,
        ),
        (
            "finalized_version_content_fingerprint",
            authorization
            .finalized_version_content_fingerprint,
        ),
        (
            "authorization_fingerprint",
            authorization.authorization_fingerprint,
        ),
    ):
        _sha256(value, label)

    _text(
        authorization.reviewer_identity,
        "reviewer_identity",
    )

    decided_at = _utc_timestamp(
        authorization.decided_at,
        "decided_at",
    )
    finalized_at = _utc_timestamp(
        authorization.finalized_at,
        "finalized_at",
    )

    if finalized_at < decided_at:
        raise ReviewIntegrityError(
            "finalized_at must not be earlier "
            "than decided_at."
        )

    if verify_fingerprint and (
        authorization.authorization_fingerprint
        != calculate_review_finalization_authorization_fingerprint(
            authorization
        )
    ):
        raise ReviewIntegrityError(
            "Review Finalization Authorization "
            "fingerprint does not match its content."
        )


def _authorization_payload(
    authorization: ReviewFinalizationAuthorization,
    *,
    include_fingerprint: bool,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_version": authorization.schema_version,
        "project_id": authorization.project_id,
        "review_document_id": (
            authorization.review_document_id
        ),
        "review_document_version_id": (
            authorization.review_document_version_id
        ),
        "review_revision_id": (
            authorization.review_revision_id
        ),
        "draft_version_content_fingerprint": (
            authorization
            .draft_version_content_fingerprint
        ),
        "review_revision_fingerprint": (
            authorization.review_revision_fingerprint
        ),
        "validation_fingerprint": (
            authorization.validation_fingerprint
        ),
        "human_review_decision_id": (
            authorization.human_review_decision_id
        ),
        "human_review_decision_fingerprint": (
            authorization
            .human_review_decision_fingerprint
        ),
        "reviewer_identity": (
            authorization.reviewer_identity
        ),
        "decided_at": authorization.decided_at,
        "finalized_at": authorization.finalized_at,
        "finalized_version_content_fingerprint": (
            authorization
            .finalized_version_content_fingerprint
        ),
    }

    if include_fingerprint:
        payload["authorization_fingerprint"] = (
            authorization.authorization_fingerprint
        )

    return payload


def _sha256(
    value: object,
    label: str,
) -> str:
    if (
        not isinstance(value, str)
        or _SHA256_PATTERN.fullmatch(value)
        is None
    ):
        raise ReviewValidationError(
            f"{label} must be a lowercase SHA-256."
        )

    return value


def _text(
    value: object,
    label: str,
) -> str:
    if (
        not isinstance(value, str)
        or not value.strip()
        or value != value.strip()
    ):
        raise ReviewValidationError(
            f"{label} must be non-empty text "
            "without surrounding whitespace."
        )

    return value


def _utc_timestamp(
    value: object,
    label: str,
) -> datetime:
    if (
        not isinstance(value, str)
        or _UTC_TIMESTAMP_PATTERN.fullmatch(value)
        is None
    ):
        raise ReviewValidationError(
            f"{label} must be a UTC timestamp."
        )

    return datetime.fromisoformat(
        value.replace("Z", "+00:00")
    )
