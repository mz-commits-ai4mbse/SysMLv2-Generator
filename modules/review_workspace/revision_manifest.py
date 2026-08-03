"""Create, validate and serialize immutable Review Revisions."""

from __future__ import annotations

from dataclasses import replace
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
    review_revision_id_sequence,
    validate_review_document_id,
    validate_review_document_version_id,
    validate_review_revision_id,
    validate_scoped_review_action_id,
)
from .item_manifest import (
    parse_review_item,
    review_item_to_dict,
    validate_review_item,
)
from .types import (
    ReviewItem,
    ReviewRevision,
)


REVIEW_REVISION_SCHEMA_VERSION = "1.0.0"

_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_UTC_TIMESTAMP_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T"
    r"\d{2}:\d{2}:\d{2}"
    r"(?:\.\d+)?Z$"
)

_REVIEW_REVISION_FIELDS = frozenset(
    {
        "schema_version",
        "project_id",
        "review_document_id",
        "review_document_version_id",
        "review_revision_id",
        "revision_sequence",
        "predecessor_revision_id",
        "review_items",
        "scoped_review_action_ids",
        "created_by",
        "created_at",
        "revision_fingerprint",
    }
)


def create_review_revision(
    *,
    project_id: str,
    review_document_id: str,
    review_document_version_id: str,
    review_revision_id: str,
    revision_sequence: int,
    predecessor_revision_id: str | None,
    review_items: tuple[ReviewItem, ...],
    scoped_review_action_ids: tuple[str, ...],
    created_by: str,
    timestamp: str,
) -> ReviewRevision:
    """Create one fingerprinted immutable Review Revision."""

    provisional = ReviewRevision(
        schema_version=REVIEW_REVISION_SCHEMA_VERSION,
        project_id=project_id,
        review_document_id=review_document_id,
        review_document_version_id=(
            review_document_version_id
        ),
        review_revision_id=review_revision_id,
        revision_sequence=revision_sequence,
        predecessor_revision_id=predecessor_revision_id,
        review_items=review_items,
        scoped_review_action_ids=scoped_review_action_ids,
        created_by=created_by,
        created_at=timestamp,
        revision_fingerprint="0" * 64,
    )

    _validate_review_revision(
        provisional,
        verify_fingerprint=False,
    )

    revision = replace(
        provisional,
        revision_fingerprint=(
            calculate_review_revision_fingerprint(
                provisional
            )
        ),
    )

    validate_review_revision(revision)

    return revision


def parse_review_revision(
    payload: object,
) -> ReviewRevision:
    """Parse and validate one Review Revision mapping."""

    data = _exact_object(
        payload,
        expected_fields=_REVIEW_REVISION_FIELDS,
        label="Review Revision",
    )

    review_item_payloads = data["review_items"]

    if not isinstance(review_item_payloads, list):
        raise ReviewValidationError(
            "review_items must be a JSON array."
        )

    action_id_payloads = data[
        "scoped_review_action_ids"
    ]

    if not isinstance(action_id_payloads, list):
        raise ReviewValidationError(
            "scoped_review_action_ids must be a JSON array."
        )

    revision = ReviewRevision(
        schema_version=data["schema_version"],
        project_id=data["project_id"],
        review_document_id=data["review_document_id"],
        review_document_version_id=(
            data["review_document_version_id"]
        ),
        review_revision_id=data["review_revision_id"],
        revision_sequence=data["revision_sequence"],
        predecessor_revision_id=(
            data["predecessor_revision_id"]
        ),
        review_items=tuple(
            parse_review_item(item)
            for item in review_item_payloads
        ),
        scoped_review_action_ids=tuple(
            action_id_payloads
        ),
        created_by=data["created_by"],
        created_at=data["created_at"],
        revision_fingerprint=data["revision_fingerprint"],
    )

    validate_review_revision(revision)

    return revision


def review_revision_from_json(
    text: object,
) -> ReviewRevision:
    """Parse one Review Revision from strict JSON."""

    if not isinstance(text, str):
        raise ReviewValidationError(
            "Review Revision JSON must be a string."
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
            "Review Revision is not valid JSON."
        ) from exc

    return parse_review_revision(payload)


def review_revision_to_dict(
    revision: ReviewRevision,
) -> dict[str, object]:
    """Serialize one validated Review Revision."""

    validate_review_revision(revision)

    return _review_revision_payload(
        revision,
        include_fingerprint=True,
    )


def review_revision_to_json(
    revision: ReviewRevision,
) -> str:
    """Serialize one Review Revision deterministically."""

    return (
        json.dumps(
            review_revision_to_dict(revision),
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )


def review_revision_filename(
    review_revision_id: object,
) -> str:
    """Return the canonical filename for one Review Revision."""

    validated = validate_review_revision_id(
        review_revision_id
    )

    return f"{validated}.json"


def calculate_review_revision_fingerprint(
    revision: ReviewRevision,
) -> str:
    """Calculate the deterministic Review Revision fingerprint."""

    _validate_review_revision(
        revision,
        verify_fingerprint=False,
    )

    payload = _review_revision_payload(
        revision,
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


def validate_review_revision(
    revision: ReviewRevision,
) -> None:
    """Validate one complete Review Revision."""

    _validate_review_revision(
        revision,
        verify_fingerprint=True,
    )


def _validate_review_revision(
    revision: ReviewRevision,
    *,
    verify_fingerprint: bool,
) -> None:
    if not isinstance(revision, ReviewRevision):
        raise ReviewValidationError(
            "revision must be a ReviewRevision."
        )

    if revision.schema_version != REVIEW_REVISION_SCHEMA_VERSION:
        raise ReviewValidationError(
            "schema_version must be "
            f"{REVIEW_REVISION_SCHEMA_VERSION!r}."
        )

    if not is_valid_project_id(revision.project_id):
        raise ReviewValidationError(
            "project_id must be a valid six-digit Project ID."
        )

    validate_review_document_id(
        revision.review_document_id
    )
    validate_review_document_version_id(
        revision.review_document_version_id
    )
    validate_review_revision_id(
        revision.review_revision_id
    )

    _positive_integer(
        revision.revision_sequence,
        "revision_sequence",
    )

    _validate_predecessor_contract(revision)
    _validate_review_items(revision)
    _validate_scoped_review_action_ids(
        revision.scoped_review_action_ids
    )

    _text(revision.created_by, "created_by")
    _utc_timestamp(revision.created_at, "created_at")
    _sha256(
        revision.revision_fingerprint,
        "revision_fingerprint",
    )

    if verify_fingerprint and (
        revision.revision_fingerprint
        != calculate_review_revision_fingerprint(revision)
    ):
        raise ReviewIntegrityError(
            "Review Revision fingerprint does not match "
            "its content."
        )


def _validate_predecessor_contract(
    revision: ReviewRevision,
) -> None:
    predecessor = revision.predecessor_revision_id

    if revision.revision_sequence == 1:
        if predecessor is not None:
            raise ReviewIntegrityError(
                "The first Review Revision must not have "
                "a predecessor."
            )

        return

    if predecessor is None:
        raise ReviewIntegrityError(
            "A successor Review Revision requires "
            "predecessor_revision_id."
        )

    validate_review_revision_id(predecessor)

    current_sequence = review_revision_id_sequence(
        revision.review_revision_id
    )
    predecessor_sequence = review_revision_id_sequence(
        predecessor
    )

    if predecessor_sequence >= current_sequence:
        raise ReviewIntegrityError(
            "predecessor_revision_id must identify an "
            "earlier Review Revision."
        )


def _validate_review_items(
    revision: ReviewRevision,
) -> None:
    if not isinstance(revision.review_items, tuple):
        raise ReviewValidationError(
            "review_items must be a tuple."
        )

    review_item_ids: set[str] = set()
    stable_subject_keys: set[str] = set()

    for item in revision.review_items:
        validate_review_item(item)

        if item.project_id != revision.project_id:
            raise ReviewIntegrityError(
                "Review Item project_id must match the "
                "Review Revision."
            )

        if (
            item.review_document_id
            != revision.review_document_id
        ):
            raise ReviewIntegrityError(
                "Review Item review_document_id must match "
                "the Review Revision."
            )

        if (
            item.review_document_version_id
            != revision.review_document_version_id
        ):
            raise ReviewIntegrityError(
                "Review Item review_document_version_id must "
                "match the Review Revision."
            )

        if item.review_item_id in review_item_ids:
            raise ReviewIntegrityError(
                "Review Item IDs must be unique within one "
                "Review Revision."
            )

        if item.stable_subject_key in stable_subject_keys:
            raise ReviewIntegrityError(
                "stable_subject_key values must be unique "
                "within one Review Revision."
            )

        review_item_ids.add(item.review_item_id)
        stable_subject_keys.add(item.stable_subject_key)


def _validate_scoped_review_action_ids(
    action_ids: tuple[str, ...],
) -> None:
    if not isinstance(action_ids, tuple):
        raise ReviewValidationError(
            "scoped_review_action_ids must be a tuple."
        )

    if len(action_ids) != len(set(action_ids)):
        raise ReviewIntegrityError(
            "scoped_review_action_ids must be unique."
        )

    for action_id in action_ids:
        validate_scoped_review_action_id(action_id)


def _review_revision_payload(
    revision: ReviewRevision,
    *,
    include_fingerprint: bool,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_version": revision.schema_version,
        "project_id": revision.project_id,
        "review_document_id": (
            revision.review_document_id
        ),
        "review_document_version_id": (
            revision.review_document_version_id
        ),
        "review_revision_id": revision.review_revision_id,
        "revision_sequence": revision.revision_sequence,
        "predecessor_revision_id": (
            revision.predecessor_revision_id
        ),
        "review_items": [
            review_item_to_dict(item)
            for item in revision.review_items
        ],
        "scoped_review_action_ids": list(
            revision.scoped_review_action_ids
        ),
        "created_by": revision.created_by,
        "created_at": revision.created_at,
    }

    if include_fingerprint:
        payload["revision_fingerprint"] = (
            revision.revision_fingerprint
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


def _utc_timestamp(value: object, label: str) -> str:
    selected = _text(value, label)

    if _UTC_TIMESTAMP_PATTERN.fullmatch(selected) is None:
        raise ReviewValidationError(
            f"{label} must be a UTC timestamp."
        )

    try:
        datetime.fromisoformat(
            selected.replace("Z", "+00:00")
        )
    except ValueError as exc:
        raise ReviewValidationError(
            f"{label} is not a valid UTC timestamp."
        ) from exc

    return selected


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
