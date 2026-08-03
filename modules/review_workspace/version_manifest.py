"""Create, finalize and serialize Review Document Versions."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime
import hashlib
import json
import re
from typing import Any

from modules.human_review.errors import (
    HumanReviewValidationError,
)
from modules.human_review.identifiers import (
    validate_human_review_decision_id,
)
from modules.project_workspace.identifiers import (
    is_valid_project_id,
)

from .errors import (
    InvalidReviewVersionTransitionError,
    ReviewIntegrityError,
    ReviewValidationError,
)
from .identifiers import (
    review_document_version_id_sequence,
    validate_review_document_id,
    validate_review_document_version_id,
    validate_review_revision_id,
)
from .types import (
    REVIEW_DOCUMENT_VERSION_STATES,
    ReviewDocumentVersion,
)


REVIEW_DOCUMENT_VERSION_SCHEMA_VERSION = "1.0.0"
REVIEW_DOCUMENT_VERSION_MANIFEST_FILENAME = (
    "review_version_manifest.json"
)

_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_UTC_TIMESTAMP_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T"
    r"\d{2}:\d{2}:\d{2}"
    r"(?:\.\d+)?Z$"
)

_REVIEW_DOCUMENT_VERSION_FIELDS = frozenset(
    {
        "schema_version",
        "project_id",
        "review_document_id",
        "review_document_version_id",
        "version_number",
        "predecessor_version_id",
        "reopen_reason",
        "opened_by",
        "opened_at",
        "version_state",
        "head_revision_id",
        "finalized_revision_id",
        "finalized_at",
        "finalization_decision_id",
        "content_fingerprint",
    }
)


def create_review_document_version(
    *,
    project_id: str,
    review_document_id: str,
    review_document_version_id: str,
    version_number: int,
    predecessor_version_id: str | None,
    reopen_reason: str | None,
    opened_by: str,
    timestamp: str,
    head_revision_id: str,
) -> ReviewDocumentVersion:
    """Create one fingerprinted draft Review Document Version."""

    provisional = ReviewDocumentVersion(
        schema_version=(
            REVIEW_DOCUMENT_VERSION_SCHEMA_VERSION
        ),
        project_id=project_id,
        review_document_id=review_document_id,
        review_document_version_id=(
            review_document_version_id
        ),
        version_number=version_number,
        predecessor_version_id=predecessor_version_id,
        reopen_reason=reopen_reason,
        opened_by=opened_by,
        opened_at=timestamp,
        version_state="draft",
        head_revision_id=head_revision_id,
        finalized_revision_id=None,
        finalized_at=None,
        finalization_decision_id=None,
        content_fingerprint="0" * 64,
    )

    _validate_review_document_version(
        provisional,
        verify_fingerprint=False,
    )

    version = replace(
        provisional,
        content_fingerprint=(
            calculate_review_document_version_fingerprint(
                provisional
            )
        ),
    )

    validate_review_document_version(version)

    return version


def finalize_review_document_version(
    version: ReviewDocumentVersion,
    *,
    finalized_revision_id: str,
    finalization_decision_id: str,
    timestamp: str,
) -> ReviewDocumentVersion:
    """Finalize one exact current Review Document Version."""

    validate_review_document_version(version)

    if version.version_state != "draft":
        raise InvalidReviewVersionTransitionError(
            "Only a draft Review Document Version can be "
            "finalized."
        )

    if finalized_revision_id != version.head_revision_id:
        raise InvalidReviewVersionTransitionError(
            "finalized_revision_id must equal the current "
            "head_revision_id."
        )

    provisional = replace(
        version,
        version_state="finalized",
        finalized_revision_id=finalized_revision_id,
        finalized_at=timestamp,
        finalization_decision_id=(
            finalization_decision_id
        ),
        content_fingerprint="0" * 64,
    )

    _validate_review_document_version(
        provisional,
        verify_fingerprint=False,
    )

    finalized = replace(
        provisional,
        content_fingerprint=(
            calculate_review_document_version_fingerprint(
                provisional
            )
        ),
    )

    validate_review_document_version(finalized)

    return finalized


def parse_review_document_version(
    payload: object,
) -> ReviewDocumentVersion:
    """Parse and validate one Review Document Version mapping."""

    data = _exact_object(
        payload,
        expected_fields=_REVIEW_DOCUMENT_VERSION_FIELDS,
        label="Review Document Version",
    )

    version = ReviewDocumentVersion(
        schema_version=data["schema_version"],
        project_id=data["project_id"],
        review_document_id=data["review_document_id"],
        review_document_version_id=(
            data["review_document_version_id"]
        ),
        version_number=data["version_number"],
        predecessor_version_id=(
            data["predecessor_version_id"]
        ),
        reopen_reason=data["reopen_reason"],
        opened_by=data["opened_by"],
        opened_at=data["opened_at"],
        version_state=data["version_state"],
        head_revision_id=data["head_revision_id"],
        finalized_revision_id=(
            data["finalized_revision_id"]
        ),
        finalized_at=data["finalized_at"],
        finalization_decision_id=(
            data["finalization_decision_id"]
        ),
        content_fingerprint=data["content_fingerprint"],
    )

    validate_review_document_version(version)

    return version


def review_document_version_from_json(
    text: object,
) -> ReviewDocumentVersion:
    """Parse one Review Document Version from strict JSON."""

    if not isinstance(text, str):
        raise ReviewValidationError(
            "Review Document Version JSON must be a string."
        )

    try:
        payload = json.loads(
            text,
            object_pairs_hook=_object_without_duplicate_keys,
        )
    except ReviewValidationError:
        raise
    except json.JSONDecodeError as exc:
        raise ReviewValidationError(
            "Review Document Version is not valid JSON."
        ) from exc

    return parse_review_document_version(payload)


def review_document_version_to_dict(
    version: ReviewDocumentVersion,
) -> dict[str, object]:
    """Serialize one validated Review Document Version."""

    validate_review_document_version(version)

    return _review_document_version_payload(
        version,
        include_fingerprint=True,
    )


def review_document_version_to_json(
    version: ReviewDocumentVersion,
) -> str:
    """Serialize a Review Document Version deterministically."""

    return (
        json.dumps(
            review_document_version_to_dict(version),
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )


def calculate_review_document_version_fingerprint(
    version: ReviewDocumentVersion,
) -> str:
    """Calculate the deterministic version fingerprint."""

    _validate_review_document_version(
        version,
        verify_fingerprint=False,
    )

    payload = _review_document_version_payload(
        version,
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


def validate_review_document_version(
    version: ReviewDocumentVersion,
) -> None:
    """Validate one complete Review Document Version."""

    _validate_review_document_version(
        version,
        verify_fingerprint=True,
    )


def _validate_review_document_version(
    version: ReviewDocumentVersion,
    *,
    verify_fingerprint: bool,
) -> None:
    if not isinstance(version, ReviewDocumentVersion):
        raise ReviewValidationError(
            "version must be a ReviewDocumentVersion."
        )

    if (
        version.schema_version
        != REVIEW_DOCUMENT_VERSION_SCHEMA_VERSION
    ):
        raise ReviewValidationError(
            "schema_version must be "
            f"{REVIEW_DOCUMENT_VERSION_SCHEMA_VERSION!r}."
        )

    if not is_valid_project_id(version.project_id):
        raise ReviewValidationError(
            "project_id must be a valid six-digit Project ID."
        )

    _adapt_review_validator(
        validate_review_document_id,
        version.review_document_id,
        "review_document_id",
    )

    _adapt_review_validator(
        validate_review_document_version_id,
        version.review_document_version_id,
        "review_document_version_id",
    )

    _positive_integer(
        version.version_number,
        "version_number",
    )

    _validate_predecessor_contract(version)

    _text(version.opened_by, "opened_by")
    opened_at = _utc_timestamp(
        version.opened_at,
        "opened_at",
    )

    if version.version_state not in (
        REVIEW_DOCUMENT_VERSION_STATES
    ):
        raise ReviewValidationError(
            "version_state must be one of "
            f"{sorted(REVIEW_DOCUMENT_VERSION_STATES)!r}."
        )

    _adapt_review_validator(
        validate_review_revision_id,
        version.head_revision_id,
        "head_revision_id",
    )

    if version.version_state == "draft":
        _validate_draft_contract(version)
    else:
        _validate_finalized_contract(
            version,
            opened_at=opened_at,
        )

    _sha256(
        version.content_fingerprint,
        "content_fingerprint",
    )

    if verify_fingerprint and (
        version.content_fingerprint
        != calculate_review_document_version_fingerprint(
            version
        )
    ):
        raise ReviewIntegrityError(
            "Review Document Version fingerprint does not "
            "match its content."
        )


def _validate_predecessor_contract(
    version: ReviewDocumentVersion,
) -> None:
    if version.version_number == 1:
        if version.predecessor_version_id is not None:
            raise ReviewIntegrityError(
                "The first Review Document Version must not "
                "have a predecessor."
            )

        if version.reopen_reason is not None:
            raise ReviewIntegrityError(
                "The first Review Document Version must not "
                "have a reopen reason."
            )

        return

    if version.predecessor_version_id is None:
        raise ReviewIntegrityError(
            "A successor Review Document Version requires "
            "predecessor_version_id."
        )

    if version.reopen_reason is None:
        raise ReviewIntegrityError(
            "A successor Review Document Version requires "
            "a reopen_reason."
        )

    _text(version.reopen_reason, "reopen_reason")

    _adapt_review_validator(
        validate_review_document_version_id,
        version.predecessor_version_id,
        "predecessor_version_id",
    )

    current_sequence = (
        review_document_version_id_sequence(
            version.review_document_version_id
        )
    )
    predecessor_sequence = (
        review_document_version_id_sequence(
            version.predecessor_version_id
        )
    )

    if predecessor_sequence >= current_sequence:
        raise ReviewIntegrityError(
            "predecessor_version_id must identify an earlier "
            "Review Document Version."
        )


def _validate_draft_contract(
    version: ReviewDocumentVersion,
) -> None:
    finalization_values = (
        version.finalized_revision_id,
        version.finalized_at,
        version.finalization_decision_id,
    )

    if any(value is not None for value in finalization_values):
        raise ReviewIntegrityError(
            "A draft Review Document Version must not contain "
            "finalization data."
        )


def _validate_finalized_contract(
    version: ReviewDocumentVersion,
    *,
    opened_at: datetime,
) -> None:
    if version.finalized_revision_id is None:
        raise ReviewIntegrityError(
            "A finalized Review Document Version requires "
            "finalized_revision_id."
        )

    if version.finalized_at is None:
        raise ReviewIntegrityError(
            "A finalized Review Document Version requires "
            "finalized_at."
        )

    if version.finalization_decision_id is None:
        raise ReviewIntegrityError(
            "A finalized Review Document Version requires "
            "finalization_decision_id."
        )

    _adapt_review_validator(
        validate_review_revision_id,
        version.finalized_revision_id,
        "finalized_revision_id",
    )

    if (
        version.finalized_revision_id
        != version.head_revision_id
    ):
        raise ReviewIntegrityError(
            "finalized_revision_id must equal "
            "head_revision_id."
        )

    finalized_at = _utc_timestamp(
        version.finalized_at,
        "finalized_at",
    )

    if finalized_at < opened_at:
        raise ReviewIntegrityError(
            "finalized_at must not be earlier than opened_at."
        )

    try:
        validate_human_review_decision_id(
            version.finalization_decision_id
        )
    except HumanReviewValidationError as exc:
        raise ReviewValidationError(
            "finalization_decision_id is invalid."
        ) from exc


def _review_document_version_payload(
    version: ReviewDocumentVersion,
    *,
    include_fingerprint: bool,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_version": version.schema_version,
        "project_id": version.project_id,
        "review_document_id": (
            version.review_document_id
        ),
        "review_document_version_id": (
            version.review_document_version_id
        ),
        "version_number": version.version_number,
        "predecessor_version_id": (
            version.predecessor_version_id
        ),
        "reopen_reason": version.reopen_reason,
        "opened_by": version.opened_by,
        "opened_at": version.opened_at,
        "version_state": version.version_state,
        "head_revision_id": version.head_revision_id,
        "finalized_revision_id": (
            version.finalized_revision_id
        ),
        "finalized_at": version.finalized_at,
        "finalization_decision_id": (
            version.finalization_decision_id
        ),
    }

    if include_fingerprint:
        payload["content_fingerprint"] = (
            version.content_fingerprint
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


def _adapt_review_validator(
    validator: Any,
    value: object,
    label: str,
) -> None:
    try:
        validator(value)
    except ReviewValidationError as exc:
        raise ReviewValidationError(
            f"{label} is invalid."
        ) from exc


def _positive_integer(
    value: object,
    label: str,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ReviewValidationError(
            f"{label} must be an integer."
        )

    if value < 1:
        raise ReviewValidationError(
            f"{label} must be at least 1."
        )

    return value


def _sha256(value: object, label: str) -> str:
    selected = _text(value, label)

    if _SHA256_PATTERN.fullmatch(selected) is None:
        raise ReviewValidationError(
            f"{label} must be a lowercase SHA-256 value."
        )

    return selected


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ReviewValidationError(
            f"{label} must be a non-empty string."
        )

    if value != value.strip():
        raise ReviewValidationError(
            f"{label} must not contain surrounding whitespace."
        )

    return value


def _utc_timestamp(
    value: object,
    label: str,
) -> datetime:
    selected = _text(value, label)

    if _UTC_TIMESTAMP_PATTERN.fullmatch(selected) is None:
        raise ReviewValidationError(
            f"{label} must be a UTC timestamp."
        )

    try:
        parsed = datetime.fromisoformat(
            selected.replace("Z", "+00:00")
        )
    except ValueError as exc:
        raise ReviewValidationError(
            f"{label} is not a valid UTC timestamp."
        ) from exc

    return parsed


def _object_without_duplicate_keys(
    pairs: list[tuple[str, Any]],
) -> dict[str, Any]:
    result: dict[str, Any] = {}

    for key, value in pairs:
        if key in result:
            raise ReviewValidationError(
                f"Duplicate JSON object key: {key!r}."
            )

        result[key] = value

    return result
