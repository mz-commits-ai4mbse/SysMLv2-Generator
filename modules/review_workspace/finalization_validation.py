"""Deterministic validation assessment for Review Version finalization."""

from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
import json
import re

from modules.human_review import (
    HumanReviewTargetSnapshot,
    create_human_review_target_snapshot,
)
from modules.project_workspace.identifiers import (
    is_valid_project_id,
)

from .document_manifest import (
    validate_review_document,
)
from .errors import (
    ReviewIntegrityError,
    ReviewValidationError,
)
from .identifiers import (
    validate_review_document_id,
    validate_review_document_version_id,
    validate_review_item_id,
    validate_review_revision_id,
)
from .revision_manifest import (
    validate_review_revision,
)
from .types import (
    RELATIONSHIP_PROFILE_VALIDATION_STATUSES,
    REVIEW_ITEM_OUTCOMES,
    ReviewDocument,
    ReviewDocumentVersion,
    ReviewRevision,
)
from .version_manifest import (
    validate_review_document_version,
)


REVIEW_FINALIZATION_VALIDATION_SCHEMA_VERSION = "1.0.0"

FINALIZATION_BLOCKING_OUTCOMES = frozenset(
    {
        "open",
        "unresolved",
    }
)

_BLOCKING_ISSUE_CODE_PATTERN = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,239}$"
)
_SHA256_PATTERN = re.compile(
    r"^[0-9a-f]{64}$"
)


@dataclass(frozen=True, slots=True)
class ReviewFinalizationItemSnapshot:
    """Exact Review Item state included in finalization validation."""

    review_item_id: str
    review_item_kind: str
    effective_review_outcome: str
    item_content_fingerprint: str
    relationship_validation_status: str | None


@dataclass(frozen=True, slots=True)
class ReviewFinalizationValidationAssessment:
    """Deterministic pre-finalization assessment of one draft version."""

    schema_version: str
    project_id: str
    review_document_id: str
    review_document_version_id: str
    review_revision_id: str
    review_document_content_fingerprint: str
    review_document_version_content_fingerprint: str
    review_revision_fingerprint: str
    item_snapshots: tuple[
        ReviewFinalizationItemSnapshot,
        ...,
    ]
    blocking_issue_codes: tuple[str, ...]
    eligible_for_finalization: bool
    validation_fingerprint: str


def assess_review_document_finalization(
    document: object,
    version: object,
    revision: object,
    *,
    additional_blocking_issue_codes: tuple[
        str,
        ...,
    ] = (),
) -> ReviewFinalizationValidationAssessment:
    """Assess one exact draft head for explicit finalization."""

    if not isinstance(document, ReviewDocument):
        raise ReviewValidationError(
            "document must be a ReviewDocument."
        )

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

    validate_review_document(document)
    validate_review_document_version(version)
    validate_review_revision(revision)

    _validate_identity_binding(
        document,
        version,
        revision,
    )

    issue_codes = set(
        _validate_additional_issue_codes(
            additional_blocking_issue_codes
        )
    )

    if version.version_state != "draft":
        issue_codes.add(
            "review_version_not_draft"
        )

    if (
        version.head_revision_id
        != revision.review_revision_id
    ):
        issue_codes.add(
            "review_revision_not_current_head"
        )

    item_snapshots = tuple(
        sorted(
            (
                _item_snapshot(item)
                for item in revision.review_items
            ),
            key=lambda item: item.review_item_id,
        )
    )

    for snapshot in item_snapshots:
        if snapshot.effective_review_outcome == "open":
            issue_codes.add(
                "review_item_open:"
                f"{snapshot.review_item_id}"
            )

        elif (
            snapshot.effective_review_outcome
            == "unresolved"
        ):
            issue_codes.add(
                "review_item_unresolved:"
                f"{snapshot.review_item_id}"
            )

    selected_issue_codes = tuple(
        sorted(issue_codes)
    )

    provisional = (
        ReviewFinalizationValidationAssessment(
            schema_version=(
                REVIEW_FINALIZATION_VALIDATION_SCHEMA_VERSION
            ),
            project_id=document.project_id,
            review_document_id=(
                document.review_document_id
            ),
            review_document_version_id=(
                version.review_document_version_id
            ),
            review_revision_id=(
                revision.review_revision_id
            ),
            review_document_content_fingerprint=(
                document.content_fingerprint
            ),
            review_document_version_content_fingerprint=(
                version.content_fingerprint
            ),
            review_revision_fingerprint=(
                revision.revision_fingerprint
            ),
            item_snapshots=item_snapshots,
            blocking_issue_codes=(
                selected_issue_codes
            ),
            eligible_for_finalization=(
                not selected_issue_codes
            ),
            validation_fingerprint="0" * 64,
        )
    )

    _validate_assessment(
        provisional,
        verify_fingerprint=False,
    )

    assessment = replace(
        provisional,
        validation_fingerprint=(
            calculate_review_finalization_validation_fingerprint(
                provisional
            )
        ),
    )

    validate_review_finalization_assessment(
        assessment
    )

    return assessment


def create_review_document_finalization_target(
    assessment: object,
) -> HumanReviewTargetSnapshot:
    """Create the exact Human Review target for one assessment."""

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

    return create_human_review_target_snapshot(
        target_type="review_document_finalization",
        target_id=(
            assessment.review_document_version_id
        ),
        target_content_fingerprint=(
            assessment
            .review_document_version_content_fingerprint
        ),
        recommended_review_mode="detailed_review",
        confirmation_required=True,
        reference_validation_status=(
            "valid"
            if assessment.eligible_for_finalization
            else "invalid"
        ),
        reference_validation_fingerprint=(
            assessment.validation_fingerprint
        ),
    )


def calculate_review_finalization_validation_fingerprint(
    assessment: ReviewFinalizationValidationAssessment,
) -> str:
    """Calculate the exact deterministic validation fingerprint."""

    _validate_assessment(
        assessment,
        verify_fingerprint=False,
    )

    payload = _assessment_payload(
        assessment,
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


def validate_review_finalization_assessment(
    assessment: ReviewFinalizationValidationAssessment,
) -> None:
    """Validate one complete finalization assessment."""

    _validate_assessment(
        assessment,
        verify_fingerprint=True,
    )


def _validate_identity_binding(
    document: ReviewDocument,
    version: ReviewDocumentVersion,
    revision: ReviewRevision,
) -> None:
    if version.project_id != document.project_id:
        raise ReviewIntegrityError(
            "Review Document Version project_id "
            "does not match the Review Document."
        )

    if revision.project_id != document.project_id:
        raise ReviewIntegrityError(
            "Review Revision project_id does not "
            "match the Review Document."
        )

    if (
        version.review_document_id
        != document.review_document_id
    ):
        raise ReviewIntegrityError(
            "Review Document Version does not belong "
            "to the selected Review Document."
        )

    if (
        revision.review_document_id
        != document.review_document_id
    ):
        raise ReviewIntegrityError(
            "Review Revision does not belong to the "
            "selected Review Document."
        )

    if (
        revision.review_document_version_id
        != version.review_document_version_id
    ):
        raise ReviewIntegrityError(
            "Review Revision does not belong to the "
            "selected Review Document Version."
        )


def _item_snapshot(
    item,
) -> ReviewFinalizationItemSnapshot:
    relationship = (
        item.current_content
        .relationship_representation
    )

    relationship_validation_status = (
        None
        if relationship is None
        else relationship.validation_status
    )

    return ReviewFinalizationItemSnapshot(
        review_item_id=item.review_item_id,
        review_item_kind=item.review_item_kind,
        effective_review_outcome=(
            item.effective_review_outcome
        ),
        item_content_fingerprint=(
            item.item_content_fingerprint
        ),
        relationship_validation_status=(
            relationship_validation_status
        ),
    )


def _validate_additional_issue_codes(
    values: object,
) -> tuple[str, ...]:
    if not isinstance(values, tuple):
        raise ReviewValidationError(
            "additional_blocking_issue_codes "
            "must be a tuple."
        )

    selected: list[str] = []

    for value in values:
        if (
            not isinstance(value, str)
            or _BLOCKING_ISSUE_CODE_PATTERN
            .fullmatch(value)
            is None
        ):
            raise ReviewValidationError(
                "Blocking issue codes must be "
                "non-empty stable identifiers."
            )

        selected.append(value)

    if len(selected) != len(set(selected)):
        raise ReviewIntegrityError(
            "additional_blocking_issue_codes "
            "must be unique."
        )

    return tuple(selected)


def _validate_assessment(
    assessment: ReviewFinalizationValidationAssessment,
    *,
    verify_fingerprint: bool,
) -> None:
    if not isinstance(
        assessment,
        ReviewFinalizationValidationAssessment,
    ):
        raise ReviewValidationError(
            "assessment must be a "
            "ReviewFinalizationValidationAssessment."
        )

    if (
        assessment.schema_version
        != REVIEW_FINALIZATION_VALIDATION_SCHEMA_VERSION
    ):
        raise ReviewValidationError(
            "Invalid finalization validation "
            "schema_version."
        )

    if not is_valid_project_id(
        assessment.project_id
    ):
        raise ReviewValidationError(
            "project_id must be a valid "
            "six-digit Project ID."
        )

    validate_review_document_id(
        assessment.review_document_id
    )
    validate_review_document_version_id(
        assessment.review_document_version_id
    )
    validate_review_revision_id(
        assessment.review_revision_id
    )

    _sha256(
        assessment
        .review_document_content_fingerprint,
        "review_document_content_fingerprint",
    )
    _sha256(
        assessment
        .review_document_version_content_fingerprint,
        "review_document_version_content_fingerprint",
    )
    _sha256(
        assessment.review_revision_fingerprint,
        "review_revision_fingerprint",
    )

    if not isinstance(
        assessment.item_snapshots,
        tuple,
    ):
        raise ReviewValidationError(
            "item_snapshots must be a tuple."
        )

    item_ids: list[str] = []

    for snapshot in assessment.item_snapshots:
        _validate_item_snapshot(snapshot)
        item_ids.append(
            snapshot.review_item_id
        )

    if len(item_ids) != len(set(item_ids)):
        raise ReviewIntegrityError(
            "Finalization item snapshots must "
            "have unique Review Item IDs."
        )

    if item_ids != sorted(item_ids):
        raise ReviewIntegrityError(
            "Finalization item snapshots must "
            "use deterministic Review Item order."
        )

    if not isinstance(
        assessment.blocking_issue_codes,
        tuple,
    ):
        raise ReviewValidationError(
            "blocking_issue_codes must be a tuple."
        )

    issue_codes = (
        assessment.blocking_issue_codes
    )

    if len(issue_codes) != len(
        set(issue_codes)
    ):
        raise ReviewIntegrityError(
            "blocking_issue_codes must be unique."
        )

    if issue_codes != tuple(
        sorted(issue_codes)
    ):
        raise ReviewIntegrityError(
            "blocking_issue_codes must use "
            "deterministic order."
        )

    for issue_code in issue_codes:
        if (
            _BLOCKING_ISSUE_CODE_PATTERN
            .fullmatch(issue_code)
            is None
        ):
            raise ReviewValidationError(
                "blocking_issue_codes contains "
                "an invalid identifier."
            )

    if not isinstance(
        assessment.eligible_for_finalization,
        bool,
    ):
        raise ReviewValidationError(
            "eligible_for_finalization must be "
            "a boolean."
        )

    if (
        assessment.eligible_for_finalization
        != (not issue_codes)
    ):
        raise ReviewIntegrityError(
            "eligible_for_finalization does not "
            "match blocking_issue_codes."
        )

    _sha256(
        assessment.validation_fingerprint,
        "validation_fingerprint",
    )

    if verify_fingerprint and (
        assessment.validation_fingerprint
        != calculate_review_finalization_validation_fingerprint(
            assessment
        )
    ):
        raise ReviewIntegrityError(
            "Finalization validation fingerprint "
            "does not match its content."
        )


def _validate_item_snapshot(
    snapshot: object,
) -> None:
    if not isinstance(
        snapshot,
        ReviewFinalizationItemSnapshot,
    ):
        raise ReviewValidationError(
            "item_snapshots entries must be "
            "ReviewFinalizationItemSnapshot values."
        )

    validate_review_item_id(
        snapshot.review_item_id
    )

    if snapshot.review_item_kind not in {
        "element",
        "relationship",
        "open_question",
    }:
        raise ReviewValidationError(
            "Invalid finalization Review Item kind."
        )

    if (
        snapshot.effective_review_outcome
        not in REVIEW_ITEM_OUTCOMES
    ):
        raise ReviewValidationError(
            "Invalid finalization Review Item outcome."
        )

    _sha256(
        snapshot.item_content_fingerprint,
        "item_content_fingerprint",
    )

    status = (
        snapshot.relationship_validation_status
    )

    if snapshot.review_item_kind == "relationship":
        if (
            status
            not in RELATIONSHIP_PROFILE_VALIDATION_STATUSES
        ):
            raise ReviewValidationError(
                "Relationship finalization snapshots "
                "require a valid validation status."
            )

    elif status is not None:
        raise ReviewIntegrityError(
            "Only relationship item snapshots may "
            "contain a relationship validation status."
        )


def _assessment_payload(
    assessment: ReviewFinalizationValidationAssessment,
    *,
    include_fingerprint: bool,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_version": (
            assessment.schema_version
        ),
        "project_id": assessment.project_id,
        "review_document_id": (
            assessment.review_document_id
        ),
        "review_document_version_id": (
            assessment.review_document_version_id
        ),
        "review_revision_id": (
            assessment.review_revision_id
        ),
        "review_document_content_fingerprint": (
            assessment
            .review_document_content_fingerprint
        ),
        "review_document_version_content_fingerprint": (
            assessment
            .review_document_version_content_fingerprint
        ),
        "review_revision_fingerprint": (
            assessment.review_revision_fingerprint
        ),
        "item_snapshots": [
            {
                "review_item_id": (
                    snapshot.review_item_id
                ),
                "review_item_kind": (
                    snapshot.review_item_kind
                ),
                "effective_review_outcome": (
                    snapshot
                    .effective_review_outcome
                ),
                "item_content_fingerprint": (
                    snapshot
                    .item_content_fingerprint
                ),
                "relationship_validation_status": (
                    snapshot
                    .relationship_validation_status
                ),
            }
            for snapshot in assessment.item_snapshots
        ],
        "blocking_issue_codes": list(
            assessment.blocking_issue_codes
        ),
        "eligible_for_finalization": (
            assessment.eligible_for_finalization
        ),
    }

    if include_fingerprint:
        payload["validation_fingerprint"] = (
            assessment.validation_fingerprint
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
