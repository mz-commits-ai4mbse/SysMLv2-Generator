"""Create, validate and serialize immutable Scoped Review Actions."""

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
    validate_review_document_id,
    validate_review_document_version_id,
    validate_review_item_id,
    validate_scoped_review_action_id,
)
from .types import (
    REVIEW_ACTION_SCOPES,
    REVIEW_DECISION_DIMENSIONS,
    REVIEW_ITEM_OUTCOMES,
    MaterializedReviewItemReference,
    ScopedReviewAction,
)


SCOPED_REVIEW_ACTION_SCHEMA_VERSION = "1.0.0"

_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_UTC_TIMESTAMP_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T"
    r"\d{2}:\d{2}:\d{2}"
    r"(?:\.\d+)?Z$"
)

_SCOPED_REVIEW_ACTION_FIELDS = frozenset(
    {
        "schema_version",
        "project_id",
        "review_document_id",
        "review_document_version_id",
        "scoped_review_action_id",
        "action_scope",
        "decision_dimension",
        "selected_values",
        "filter_definition",
        "materialized_items",
        "created_by",
        "created_at",
        "rationale",
        "action_fingerprint",
    }
)

_MATERIALIZED_ITEM_FIELDS = frozenset(
    {
        "review_item_id",
        "item_content_fingerprint",
    }
)


def create_scoped_review_action(
    *,
    project_id: str,
    review_document_id: str,
    review_document_version_id: str,
    scoped_review_action_id: str,
    action_scope: str,
    decision_dimension: str,
    selected_values: tuple[str, ...],
    filter_definition: str | None,
    materialized_items: tuple[
        MaterializedReviewItemReference,
        ...,
    ],
    created_by: str,
    timestamp: str,
    rationale: str | None,
) -> ScopedReviewAction:
    """Create one fingerprinted immutable Scoped Review Action."""

    provisional = ScopedReviewAction(
        schema_version=(
            SCOPED_REVIEW_ACTION_SCHEMA_VERSION
        ),
        project_id=project_id,
        review_document_id=review_document_id,
        review_document_version_id=(
            review_document_version_id
        ),
        scoped_review_action_id=(
            scoped_review_action_id
        ),
        action_scope=action_scope,
        decision_dimension=decision_dimension,
        selected_values=selected_values,
        filter_definition=filter_definition,
        materialized_items=materialized_items,
        created_by=created_by,
        created_at=timestamp,
        rationale=rationale,
        action_fingerprint="0" * 64,
    )

    _validate_scoped_review_action(
        provisional,
        verify_fingerprint=False,
    )

    action = replace(
        provisional,
        action_fingerprint=(
            calculate_scoped_review_action_fingerprint(
                provisional
            )
        ),
    )

    validate_scoped_review_action(action)

    return action


def parse_scoped_review_action(
    payload: object,
) -> ScopedReviewAction:
    """Parse and validate one Scoped Review Action mapping."""

    data = _exact_object(
        payload,
        expected_fields=_SCOPED_REVIEW_ACTION_FIELDS,
        label="Scoped Review Action",
    )

    selected_value_payloads = data["selected_values"]

    if not isinstance(selected_value_payloads, list):
        raise ReviewValidationError(
            "selected_values must be a JSON array."
        )

    materialized_item_payloads = data[
        "materialized_items"
    ]

    if not isinstance(materialized_item_payloads, list):
        raise ReviewValidationError(
            "materialized_items must be a JSON array."
        )

    action = ScopedReviewAction(
        schema_version=data["schema_version"],
        project_id=data["project_id"],
        review_document_id=data["review_document_id"],
        review_document_version_id=(
            data["review_document_version_id"]
        ),
        scoped_review_action_id=(
            data["scoped_review_action_id"]
        ),
        action_scope=data["action_scope"],
        decision_dimension=data["decision_dimension"],
        selected_values=tuple(selected_value_payloads),
        filter_definition=data["filter_definition"],
        materialized_items=tuple(
            _parse_materialized_item(item)
            for item in materialized_item_payloads
        ),
        created_by=data["created_by"],
        created_at=data["created_at"],
        rationale=data["rationale"],
        action_fingerprint=data["action_fingerprint"],
    )

    validate_scoped_review_action(action)

    return action


def scoped_review_action_from_json(
    text: object,
) -> ScopedReviewAction:
    """Parse one Scoped Review Action from strict JSON."""

    if not isinstance(text, str):
        raise ReviewValidationError(
            "Scoped Review Action JSON must be a string."
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
            "Scoped Review Action is not valid JSON."
        ) from exc

    return parse_scoped_review_action(payload)


def scoped_review_action_to_dict(
    action: ScopedReviewAction,
) -> dict[str, object]:
    """Serialize one validated Scoped Review Action."""

    validate_scoped_review_action(action)

    return _scoped_review_action_payload(
        action,
        include_fingerprint=True,
    )


def scoped_review_action_to_json(
    action: ScopedReviewAction,
) -> str:
    """Serialize one Scoped Review Action deterministically."""

    return (
        json.dumps(
            scoped_review_action_to_dict(action),
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )


def scoped_review_action_filename(
    scoped_review_action_id: object,
) -> str:
    """Return the canonical filename for one scoped action."""

    validated = validate_scoped_review_action_id(
        scoped_review_action_id
    )

    return f"{validated}.json"


def calculate_scoped_review_action_fingerprint(
    action: ScopedReviewAction,
) -> str:
    """Calculate the deterministic scoped-action fingerprint."""

    _validate_scoped_review_action(
        action,
        verify_fingerprint=False,
    )

    payload = _scoped_review_action_payload(
        action,
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


def validate_scoped_review_action(
    action: ScopedReviewAction,
) -> None:
    """Validate one complete Scoped Review Action."""

    _validate_scoped_review_action(
        action,
        verify_fingerprint=True,
    )


def _validate_scoped_review_action(
    action: ScopedReviewAction,
    *,
    verify_fingerprint: bool,
) -> None:
    if not isinstance(action, ScopedReviewAction):
        raise ReviewValidationError(
            "action must be a ScopedReviewAction."
        )

    if (
        action.schema_version
        != SCOPED_REVIEW_ACTION_SCHEMA_VERSION
    ):
        raise ReviewValidationError(
            "schema_version must be "
            f"{SCOPED_REVIEW_ACTION_SCHEMA_VERSION!r}."
        )

    if not is_valid_project_id(action.project_id):
        raise ReviewValidationError(
            "project_id must be a valid six-digit Project ID."
        )

    validate_review_document_id(
        action.review_document_id
    )
    validate_review_document_version_id(
        action.review_document_version_id
    )
    validate_scoped_review_action_id(
        action.scoped_review_action_id
    )

    if action.action_scope not in REVIEW_ACTION_SCOPES:
        raise ReviewValidationError(
            "action_scope must be one of "
            f"{sorted(REVIEW_ACTION_SCOPES)!r}."
        )

    if (
        action.decision_dimension
        not in REVIEW_DECISION_DIMENSIONS
    ):
        raise ReviewValidationError(
            "decision_dimension must be one of "
            f"{sorted(REVIEW_DECISION_DIMENSIONS)!r}."
        )

    _validate_selected_values(action)
    _validate_scope_contract(action)
    _validate_materialized_items(
        action.materialized_items
    )
    _validate_rejection_contract(action)

    _text(action.created_by, "created_by")
    _utc_timestamp(action.created_at, "created_at")
    _optional_text(action.rationale, "rationale")
    _sha256(
        action.action_fingerprint,
        "action_fingerprint",
    )

    if verify_fingerprint and (
        action.action_fingerprint
        != calculate_scoped_review_action_fingerprint(
            action
        )
    ):
        raise ReviewIntegrityError(
            "Scoped Review Action fingerprint does not "
            "match its content."
        )


def _validate_selected_values(
    action: ScopedReviewAction,
) -> None:
    values = action.selected_values

    if not isinstance(values, tuple):
        raise ReviewValidationError(
            "selected_values must be a tuple."
        )

    if not values:
        raise ReviewValidationError(
            "selected_values must not be empty."
        )

    for value in values:
        _text(value, "selected_values entry")

    if len(values) != len(set(values)):
        raise ReviewIntegrityError(
            "selected_values must contain unique values."
        )

    if action.decision_dimension == "review_outcome":
        if (
            len(values) != 1
            or values[0] not in REVIEW_ITEM_OUTCOMES
        ):
            raise ReviewValidationError(
                "A review_outcome action requires exactly "
                "one valid Review Item outcome."
            )


def _validate_scope_contract(
    action: ScopedReviewAction,
) -> None:
    if action.action_scope == "document_default":
        if action.filter_definition is not None:
            raise ReviewIntegrityError(
                "A document_default action must not contain "
                "a filter_definition."
            )

        if action.materialized_items:
            raise ReviewIntegrityError(
                "A document_default action must not contain "
                "materialized Review Items."
            )

        if action.decision_dimension == "review_outcome":
            raise ReviewIntegrityError(
                "A document_default action must not set "
                "review_outcome."
            )

        return

    if action.action_scope == "filtered_set":
        _text(
            action.filter_definition,
            "filter_definition",
        )

        if not action.materialized_items:
            raise ReviewIntegrityError(
                "A filtered_set action requires exact "
                "materialized Review Items."
            )

        return

    if action.filter_definition is not None:
        raise ReviewIntegrityError(
            "An explicit_selection action must not contain "
            "a filter_definition."
        )

    if not action.materialized_items:
        raise ReviewIntegrityError(
            "An explicit_selection action requires exact "
            "materialized Review Items."
        )


def _validate_materialized_items(
    references: tuple[
        MaterializedReviewItemReference,
        ...,
    ],
) -> None:
    if not isinstance(references, tuple):
        raise ReviewValidationError(
            "materialized_items must be a tuple."
        )

    review_item_ids: set[str] = set()

    for reference in references:
        if not isinstance(
            reference,
            MaterializedReviewItemReference,
        ):
            raise ReviewValidationError(
                "materialized_items entries must be "
                "MaterializedReviewItemReference values."
            )

        validate_review_item_id(
            reference.review_item_id
        )
        _sha256(
            reference.item_content_fingerprint,
            "item_content_fingerprint",
        )

        if reference.review_item_id in review_item_ids:
            raise ReviewIntegrityError(
                "materialized Review Item IDs must be unique."
            )

        review_item_ids.add(reference.review_item_id)


def _validate_rejection_contract(
    action: ScopedReviewAction,
) -> None:
    if (
        action.decision_dimension != "review_outcome"
        or action.selected_values != ("rejected",)
    ):
        return

    if action.rationale is None:
        raise ReviewIntegrityError(
            "A rejection action requires a rationale."
        )

    _text(action.rationale, "rationale")


def _scoped_review_action_payload(
    action: ScopedReviewAction,
    *,
    include_fingerprint: bool,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_version": action.schema_version,
        "project_id": action.project_id,
        "review_document_id": (
            action.review_document_id
        ),
        "review_document_version_id": (
            action.review_document_version_id
        ),
        "scoped_review_action_id": (
            action.scoped_review_action_id
        ),
        "action_scope": action.action_scope,
        "decision_dimension": (
            action.decision_dimension
        ),
        "selected_values": list(
            action.selected_values
        ),
        "filter_definition": (
            action.filter_definition
        ),
        "materialized_items": [
            {
                "review_item_id": (
                    reference.review_item_id
                ),
                "item_content_fingerprint": (
                    reference.item_content_fingerprint
                ),
            }
            for reference in action.materialized_items
        ],
        "created_by": action.created_by,
        "created_at": action.created_at,
        "rationale": action.rationale,
    }

    if include_fingerprint:
        payload["action_fingerprint"] = (
            action.action_fingerprint
        )

    return payload


def _parse_materialized_item(
    payload: object,
) -> MaterializedReviewItemReference:
    data = _exact_object(
        payload,
        expected_fields=_MATERIALIZED_ITEM_FIELDS,
        label="Materialized Review Item Reference",
    )

    return MaterializedReviewItemReference(
        review_item_id=data["review_item_id"],
        item_content_fingerprint=(
            data["item_content_fingerprint"]
        ),
    )


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


def _optional_text(
    value: object,
    label: str,
) -> str | None:
    if value is None:
        return None

    return _text(value, label)


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
