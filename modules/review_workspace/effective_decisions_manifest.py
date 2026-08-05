"""Create and serialize immutable effective Review decisions."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
import hashlib
import json
import re
from typing import Any

from modules.project_workspace.identifiers import (
    is_valid_project_id,
)

from .errors import (
    ReviewIntegrityError,
    ReviewValidationError,
)
from .identifiers import (
    validate_review_document_id,
    validate_review_document_version_id,
    validate_review_revision_id,
)
from .item_manifest import (
    parse_review_item,
    review_item_to_dict,
    validate_review_item,
)
from .reviewed_document_manifest import (
    FINALIZED_REVIEW_ITEM_OUTCOMES,
    FinalizedReviewedDocument,
    validate_finalized_reviewed_document,
)
from .revision_manifest import (
    validate_review_revision,
)
from .types import (
    ReviewItem,
    ReviewRevision,
)


EFFECTIVE_REVIEW_DECISION_SET_SCHEMA_VERSION = "1.0.0"

_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_UTC_TIMESTAMP_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T"
    r"\d{2}:\d{2}:\d{2}"
    r"(?:\.\d+)?Z$"
)

_EFFECTIVE_REVIEW_DECISION_SET_FIELDS = frozenset(
    {
        "schema_version",
        "project_id",
        "review_document_id",
        "review_document_version_id",
        "review_revision_id",
        "finalized_reviewed_document_fingerprint",
        "review_revision_fingerprint",
        "finalization_decision_id",
        "finalization_decision_fingerprint",
        "finalization_validation_fingerprint",
        "finalized_at",
        "effective_decisions",
        "content_fingerprint",
    }
)


@dataclass(frozen=True, slots=True)
class EffectiveReviewDecisionSet:
    """Immutable machine-readable result of one finalized review."""

    schema_version: str
    project_id: str
    review_document_id: str
    review_document_version_id: str
    review_revision_id: str
    finalized_reviewed_document_fingerprint: str
    review_revision_fingerprint: str
    finalization_decision_id: str
    finalization_decision_fingerprint: str
    finalization_validation_fingerprint: str
    finalized_at: str
    effective_decisions: tuple[ReviewItem, ...]
    content_fingerprint: str


def create_effective_review_decision_set(
    reviewed_document: FinalizedReviewedDocument,
    revision: ReviewRevision,
) -> EffectiveReviewDecisionSet:
    """Create the exact effective decision set for one final review."""

    validate_finalized_reviewed_document(
        reviewed_document
    )
    validate_review_revision(revision)

    effective_decisions = tuple(
        sorted(
            revision.review_items,
            key=lambda item: item.review_item_id,
        )
    )

    provisional = EffectiveReviewDecisionSet(
        schema_version=(
            EFFECTIVE_REVIEW_DECISION_SET_SCHEMA_VERSION
        ),
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
        finalized_reviewed_document_fingerprint=(
            reviewed_document.content_fingerprint
        ),
        review_revision_fingerprint=(
            revision.revision_fingerprint
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
        finalized_at=reviewed_document.finalized_at,
        effective_decisions=effective_decisions,
        content_fingerprint="0" * 64,
    )

    decision_set = replace(
        provisional,
        content_fingerprint=(
            calculate_effective_review_decision_set_fingerprint(
                provisional
            )
        ),
    )

    validate_effective_review_decision_set_binding(
        decision_set,
        reviewed_document,
        revision,
    )

    return decision_set


def parse_effective_review_decision_set(
    payload: object,
) -> EffectiveReviewDecisionSet:
    """Parse and validate one strict decision-set mapping."""

    data = _exact_object(
        payload,
        expected_fields=(
            _EFFECTIVE_REVIEW_DECISION_SET_FIELDS
        ),
        label="Effective Review Decision Set",
    )

    decision_payloads = data["effective_decisions"]

    if not isinstance(decision_payloads, list):
        raise ReviewValidationError(
            "effective_decisions must be a JSON array."
        )

    decision_set = EffectiveReviewDecisionSet(
        schema_version=data["schema_version"],
        project_id=data["project_id"],
        review_document_id=(
            data["review_document_id"]
        ),
        review_document_version_id=(
            data["review_document_version_id"]
        ),
        review_revision_id=(
            data["review_revision_id"]
        ),
        finalized_reviewed_document_fingerprint=(
            data[
                "finalized_reviewed_document_fingerprint"
            ]
        ),
        review_revision_fingerprint=(
            data["review_revision_fingerprint"]
        ),
        finalization_decision_id=(
            data["finalization_decision_id"]
        ),
        finalization_decision_fingerprint=(
            data[
                "finalization_decision_fingerprint"
            ]
        ),
        finalization_validation_fingerprint=(
            data[
                "finalization_validation_fingerprint"
            ]
        ),
        finalized_at=data["finalized_at"],
        effective_decisions=tuple(
            parse_review_item(value)
            for value in decision_payloads
        ),
        content_fingerprint=(
            data["content_fingerprint"]
        ),
    )

    validate_effective_review_decision_set(
        decision_set
    )

    return decision_set


def effective_review_decision_set_from_json(
    text: object,
) -> EffectiveReviewDecisionSet:
    """Parse one effective decision set from strict JSON."""

    if not isinstance(text, str):
        raise ReviewValidationError(
            "Effective Review Decision Set JSON "
            "must be a string."
        )

    try:
        payload = json.loads(
            text,
            object_pairs_hook=(
                _object_without_duplicate_keys
            ),
        )
    except ReviewValidationError:
        raise
    except json.JSONDecodeError as exc:
        raise ReviewValidationError(
            "Effective Review Decision Set is not "
            "valid JSON."
        ) from exc

    return parse_effective_review_decision_set(
        payload
    )


def effective_review_decision_set_to_dict(
    decision_set: EffectiveReviewDecisionSet,
) -> dict[str, object]:
    """Serialize one validated effective decision set."""

    validate_effective_review_decision_set(
        decision_set
    )

    return _decision_set_payload(
        decision_set,
        include_fingerprint=True,
    )


def effective_review_decision_set_to_json(
    decision_set: EffectiveReviewDecisionSet,
) -> str:
    """Serialize one effective decision set deterministically."""

    return (
        json.dumps(
            effective_review_decision_set_to_dict(
                decision_set
            ),
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )


def calculate_effective_review_decision_set_fingerprint(
    decision_set: EffectiveReviewDecisionSet,
) -> str:
    """Calculate the deterministic decision-set fingerprint."""

    _validate_decision_set(
        decision_set,
        verify_fingerprint=False,
    )

    payload = _decision_set_payload(
        decision_set,
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


def validate_effective_review_decision_set(
    decision_set: EffectiveReviewDecisionSet,
) -> None:
    """Validate one complete effective decision set."""

    _validate_decision_set(
        decision_set,
        verify_fingerprint=True,
    )


def validate_effective_review_decision_set_binding(
    decision_set: EffectiveReviewDecisionSet,
    reviewed_document: FinalizedReviewedDocument,
    revision: ReviewRevision,
) -> None:
    """Validate the exact finalized manifest and revision binding."""

    validate_effective_review_decision_set(
        decision_set
    )
    validate_finalized_reviewed_document(
        reviewed_document
    )
    validate_review_revision(revision)

    if (
        decision_set.project_id
        != reviewed_document.project_id
        or decision_set.project_id
        != revision.project_id
    ):
        raise ReviewIntegrityError(
            "Effective decisions do not belong "
            "to the same Project."
        )

    if (
        decision_set.review_document_id
        != reviewed_document.review_document_id
        or decision_set.review_document_id
        != revision.review_document_id
    ):
        raise ReviewIntegrityError(
            "Effective decisions do not belong "
            "to the same Review Document."
        )

    if (
        decision_set.review_document_version_id
        != reviewed_document
        .review_document_version_id
        or decision_set.review_document_version_id
        != revision.review_document_version_id
    ):
        raise ReviewIntegrityError(
            "Effective decisions do not belong "
            "to the same Review Document Version."
        )

    if (
        decision_set.review_revision_id
        != reviewed_document.review_revision_id
        or decision_set.review_revision_id
        != revision.review_revision_id
    ):
        raise ReviewIntegrityError(
            "Effective decisions do not bind "
            "the same Review Revision."
        )

    if (
        decision_set
        .finalized_reviewed_document_fingerprint
        != reviewed_document.content_fingerprint
    ):
        raise ReviewIntegrityError(
            "Effective decisions do not bind the exact "
            "Finalized Reviewed Document."
        )

    if (
        decision_set.review_revision_fingerprint
        != revision.revision_fingerprint
        or decision_set.review_revision_fingerprint
        != reviewed_document
        .review_revision_fingerprint
    ):
        raise ReviewIntegrityError(
            "Effective decisions do not bind the exact "
            "Review Revision fingerprint."
        )

    if (
        decision_set.finalization_decision_id
        != reviewed_document.finalization_decision_id
        or decision_set
        .finalization_decision_fingerprint
        != reviewed_document
        .finalization_decision_fingerprint
        or decision_set
        .finalization_validation_fingerprint
        != reviewed_document
        .finalization_validation_fingerprint
    ):
        raise ReviewIntegrityError(
            "Effective decisions do not bind the exact "
            "finalization decision and validation."
        )

    if (
        decision_set.finalized_at
        != reviewed_document.finalized_at
    ):
        raise ReviewIntegrityError(
            "Effective decision finalization timestamp "
            "does not match the reviewed document."
        )

    expected_references = tuple(
        (
            reference.review_item_id,
            reference.stable_subject_key,
            reference.review_item_kind,
            reference.section,
            reference.effective_review_outcome,
            reference.item_content_fingerprint,
        )
        for reference in reviewed_document.review_items
    )

    actual_references = tuple(
        (
            item.review_item_id,
            item.stable_subject_key,
            item.review_item_kind,
            item.section,
            item.effective_review_outcome,
            item.item_content_fingerprint,
        )
        for item in decision_set.effective_decisions
    )

    if actual_references != expected_references:
        raise ReviewIntegrityError(
            "Effective decisions do not match the exact "
            "finalized Review Item set."
        )

    revision_items = tuple(
        sorted(
            revision.review_items,
            key=lambda item: item.review_item_id,
        )
    )

    if decision_set.effective_decisions != revision_items:
        raise ReviewIntegrityError(
            "Effective decisions differ from the exact "
            "finalized Review Revision."
        )


def _validate_decision_set(
    decision_set: EffectiveReviewDecisionSet,
    *,
    verify_fingerprint: bool,
) -> None:
    if not isinstance(
        decision_set,
        EffectiveReviewDecisionSet,
    ):
        raise ReviewValidationError(
            "decision_set must be an "
            "EffectiveReviewDecisionSet."
        )

    if (
        decision_set.schema_version
        != EFFECTIVE_REVIEW_DECISION_SET_SCHEMA_VERSION
    ):
        raise ReviewValidationError(
            "Invalid Effective Review Decision Set "
            "schema_version."
        )

    if not is_valid_project_id(
        decision_set.project_id
    ):
        raise ReviewValidationError(
            "project_id must be a valid six-digit "
            "Project ID."
        )

    validate_review_document_id(
        decision_set.review_document_id
    )
    validate_review_document_version_id(
        decision_set.review_document_version_id
    )
    validate_review_revision_id(
        decision_set.review_revision_id
    )

    for label, value in (
        (
            "finalized_reviewed_document_fingerprint",
            decision_set
            .finalized_reviewed_document_fingerprint,
        ),
        (
            "review_revision_fingerprint",
            decision_set.review_revision_fingerprint,
        ),
        (
            "finalization_decision_fingerprint",
            decision_set
            .finalization_decision_fingerprint,
        ),
        (
            "finalization_validation_fingerprint",
            decision_set
            .finalization_validation_fingerprint,
        ),
        (
            "content_fingerprint",
            decision_set.content_fingerprint,
        ),
    ):
        _sha256(value, label)

    _text(
        decision_set.finalization_decision_id,
        "finalization_decision_id",
    )
    _utc_timestamp(
        decision_set.finalized_at,
        "finalized_at",
    )

    if not isinstance(
        decision_set.effective_decisions,
        tuple,
    ):
        raise ReviewValidationError(
            "effective_decisions must be a tuple."
        )

    for item in decision_set.effective_decisions:
        validate_review_item(item)

        if item.project_id != decision_set.project_id:
            raise ReviewIntegrityError(
                "Effective Review Item belongs "
                "to another Project."
            )

        if (
            item.review_document_id
            != decision_set.review_document_id
        ):
            raise ReviewIntegrityError(
                "Effective Review Item belongs "
                "to another Review Document."
            )

        if (
            item.review_document_version_id
            != decision_set
            .review_document_version_id
        ):
            raise ReviewIntegrityError(
                "Effective Review Item belongs "
                "to another Review Document Version."
            )

        if (
            item.effective_review_outcome
            not in FINALIZED_REVIEW_ITEM_OUTCOMES
        ):
            raise ReviewIntegrityError(
                "Effective Review Item must have "
                "a non-blocking final outcome."
            )

    item_ids = tuple(
        item.review_item_id
        for item in decision_set.effective_decisions
    )

    if len(item_ids) != len(set(item_ids)):
        raise ReviewIntegrityError(
            "effective_decisions must not contain "
            "duplicate Review Item IDs."
        )

    if item_ids != tuple(sorted(item_ids)):
        raise ReviewIntegrityError(
            "effective_decisions must be ordered by "
            "review_item_id."
        )

    if verify_fingerprint and (
        decision_set.content_fingerprint
        != calculate_effective_review_decision_set_fingerprint(
            decision_set
        )
    ):
        raise ReviewIntegrityError(
            "Effective Review Decision Set fingerprint "
            "does not match its content."
        )


def _decision_set_payload(
    decision_set: EffectiveReviewDecisionSet,
    *,
    include_fingerprint: bool,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_version": decision_set.schema_version,
        "project_id": decision_set.project_id,
        "review_document_id": (
            decision_set.review_document_id
        ),
        "review_document_version_id": (
            decision_set.review_document_version_id
        ),
        "review_revision_id": (
            decision_set.review_revision_id
        ),
        "finalized_reviewed_document_fingerprint": (
            decision_set
            .finalized_reviewed_document_fingerprint
        ),
        "review_revision_fingerprint": (
            decision_set.review_revision_fingerprint
        ),
        "finalization_decision_id": (
            decision_set.finalization_decision_id
        ),
        "finalization_decision_fingerprint": (
            decision_set
            .finalization_decision_fingerprint
        ),
        "finalization_validation_fingerprint": (
            decision_set
            .finalization_validation_fingerprint
        ),
        "finalized_at": decision_set.finalized_at,
        "effective_decisions": [
            review_item_to_dict(item)
            for item in decision_set.effective_decisions
        ],
    }

    if include_fingerprint:
        payload["content_fingerprint"] = (
            decision_set.content_fingerprint
        )

    return payload


def _exact_object(
    value: object,
    *,
    expected_fields: frozenset[str],
    label: str,
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ReviewValidationError(
            f"{label} must be a JSON object."
        )

    actual_fields = frozenset(value)

    if actual_fields != expected_fields:
        raise ReviewValidationError(
            f"{label} has invalid fields; "
            f"missing={sorted(expected_fields - actual_fields)}, "
            f"unknown={sorted(actual_fields - expected_fields)}."
        )

    return value


def _object_without_duplicate_keys(
    pairs: list[tuple[str, Any]],
) -> dict[str, Any]:
    result: dict[str, Any] = {}

    for key, value in pairs:
        if key in result:
            raise ReviewValidationError(
                f"Duplicate JSON key: {key!r}."
            )

        result[key] = value

    return result


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
