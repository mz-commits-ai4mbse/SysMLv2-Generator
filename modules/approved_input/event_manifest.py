"""Create and serialize immutable Approved Input lifecycle events."""

from __future__ import annotations

from dataclasses import fields, replace
import hashlib
import json
import re
from typing import Any

from modules.human_review.identifiers import (
    is_valid_human_review_decision_id,
)
from modules.project_workspace.identifiers import is_valid_project_id
from modules.review_workspace.identifiers import (
    is_valid_review_document_id,
    is_valid_review_document_version_id,
    is_valid_review_revision_id,
)

from .errors import (
    ApprovedInputIntegrityError,
    ApprovedInputValidationError,
)
from .identifiers import (
    validate_approved_input_event_id,
    validate_approved_input_id,
)
from .types import (
    APPROVED_INPUT_EVENT_TYPES,
    ApprovedInputEvent,
)


APPROVED_INPUT_EVENT_SCHEMA_VERSION = "1.0.0"

_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_REASON_CODE_PATTERN = re.compile(
    r"^[a-z][a-z0-9._:-]{0,239}$"
)
_UTC_TIMESTAMP_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T"
    r"\d{2}:\d{2}:\d{2}"
    r"(?:\.\d+)?Z$"
)
_EVENT_FIELDS = frozenset(
    field.name for field in fields(ApprovedInputEvent)
)


def create_approved_input_event(
    *,
    project_id: str,
    approved_input_event_id: str,
    approved_input_id: str,
    event_type: str,
    reason_code: str,
    rationale: str | None,
    actor_identity: str,
    successor_approved_input_id: str | None,
    causal_review_document_id: str | None,
    causal_review_document_version_id: str | None,
    causal_review_revision_id: str | None,
    causal_finalization_decision_id: str | None,
    causal_finalization_decision_fingerprint: str | None,
    occurred_at: str,
    previous_event_fingerprint: str | None = None,
) -> ApprovedInputEvent:
    """Create one immutable terminal Approved Input lifecycle event."""

    provisional = ApprovedInputEvent(
        schema_version=APPROVED_INPUT_EVENT_SCHEMA_VERSION,
        project_id=project_id,
        approved_input_event_id=approved_input_event_id,
        approved_input_id=approved_input_id,
        event_type=event_type,
        previous_authority_state="active",
        next_authority_state=event_type,
        reason_code=reason_code,
        rationale=rationale,
        actor_identity=actor_identity,
        successor_approved_input_id=successor_approved_input_id,
        causal_review_document_id=causal_review_document_id,
        causal_review_document_version_id=(
            causal_review_document_version_id
        ),
        causal_review_revision_id=causal_review_revision_id,
        causal_finalization_decision_id=(
            causal_finalization_decision_id
        ),
        causal_finalization_decision_fingerprint=(
            causal_finalization_decision_fingerprint
        ),
        occurred_at=occurred_at,
        previous_event_fingerprint=previous_event_fingerprint,
        event_fingerprint="0" * 64,
    )

    event = replace(
        provisional,
        event_fingerprint=(
            calculate_approved_input_event_fingerprint(
                provisional
            )
        ),
    )
    validate_approved_input_event(event)
    return event


def calculate_approved_input_event_fingerprint(
    event: ApprovedInputEvent,
) -> str:
    """Calculate the deterministic fingerprint of one lifecycle event."""

    _validate_event(event, verify_fingerprint=False)
    canonical_json = json.dumps(
        _event_payload(event, include_fingerprint=False),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(
        canonical_json.encode("utf-8")
    ).hexdigest()


def validate_approved_input_event(
    event: object,
) -> None:
    """Validate one complete immutable Approved Input Event."""

    _validate_event(event, verify_fingerprint=True)


def approved_input_event_to_dict(
    event: ApprovedInputEvent,
) -> dict[str, object]:
    """Serialize one validated event to a JSON-compatible mapping."""

    validate_approved_input_event(event)
    return _event_payload(event, include_fingerprint=True)


def approved_input_event_to_json(
    event: ApprovedInputEvent,
) -> str:
    """Serialize one lifecycle event deterministically."""

    return (
        json.dumps(
            approved_input_event_to_dict(event),
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )


def parse_approved_input_event(
    payload: object,
) -> ApprovedInputEvent:
    """Parse one strict Approved Input Event mapping."""

    data = _exact_object(
        payload,
        expected_fields=_EVENT_FIELDS,
        label="Approved Input Event",
    )
    event = ApprovedInputEvent(
        schema_version=data["schema_version"],
        project_id=data["project_id"],
        approved_input_event_id=data["approved_input_event_id"],
        approved_input_id=data["approved_input_id"],
        event_type=data["event_type"],
        previous_authority_state=data["previous_authority_state"],
        next_authority_state=data["next_authority_state"],
        reason_code=data["reason_code"],
        rationale=data["rationale"],
        actor_identity=data["actor_identity"],
        successor_approved_input_id=data[
            "successor_approved_input_id"
        ],
        causal_review_document_id=data[
            "causal_review_document_id"
        ],
        causal_review_document_version_id=data[
            "causal_review_document_version_id"
        ],
        causal_review_revision_id=data[
            "causal_review_revision_id"
        ],
        causal_finalization_decision_id=data[
            "causal_finalization_decision_id"
        ],
        causal_finalization_decision_fingerprint=data[
            "causal_finalization_decision_fingerprint"
        ],
        occurred_at=data["occurred_at"],
        previous_event_fingerprint=data[
            "previous_event_fingerprint"
        ],
        event_fingerprint=data["event_fingerprint"],
    )
    validate_approved_input_event(event)
    return event


def approved_input_event_from_json(text: object) -> ApprovedInputEvent:
    """Parse one lifecycle event from strict JSON."""

    if not isinstance(text, str):
        raise ApprovedInputValidationError(
            "Approved Input Event JSON must be a string."
        )
    try:
        payload = json.loads(
            text,
            object_pairs_hook=_object_without_duplicate_keys,
        )
    except ApprovedInputValidationError:
        raise
    except json.JSONDecodeError as exc:
        raise ApprovedInputValidationError(
            "Approved Input Event is not valid JSON."
        ) from exc
    return parse_approved_input_event(payload)


def _validate_event(
    event: object,
    *,
    verify_fingerprint: bool,
) -> None:
    if not isinstance(event, ApprovedInputEvent):
        raise ApprovedInputValidationError(
            "event must be an ApprovedInputEvent."
        )
    if event.schema_version != APPROVED_INPUT_EVENT_SCHEMA_VERSION:
        raise ApprovedInputValidationError(
            "Unsupported Approved Input Event schema_version."
        )
    if not is_valid_project_id(event.project_id):
        raise ApprovedInputValidationError(
            "project_id must match ^[0-9]{6}$."
        )
    validate_approved_input_event_id(event.approved_input_event_id)
    validate_approved_input_id(event.approved_input_id)

    if event.event_type not in APPROVED_INPUT_EVENT_TYPES:
        raise ApprovedInputValidationError(
            "event_type is not supported."
        )
    if event.previous_authority_state != "active":
        raise ApprovedInputIntegrityError(
            "G5.6 lifecycle transitions must originate from active."
        )
    if event.next_authority_state != event.event_type:
        raise ApprovedInputIntegrityError(
            "next_authority_state must equal the lifecycle event type."
        )

    _identifier_text(event.actor_identity, "actor_identity")
    if (
        not isinstance(event.reason_code, str)
        or _REASON_CODE_PATTERN.fullmatch(event.reason_code) is None
    ):
        raise ApprovedInputValidationError(
            "reason_code must be one stable lowercase identifier."
        )
    _optional_text(event.rationale, "rationale")
    _utc_timestamp(event.occurred_at)
    _optional_sha256(
        event.previous_event_fingerprint,
        "previous_event_fingerprint",
    )

    if event.event_type == "invalidated":
        _require_none(
            event.successor_approved_input_id,
            "successor_approved_input_id",
        )
        _require_no_causal_review(event)
    elif event.event_type == "revoked":
        _require_none(
            event.successor_approved_input_id,
            "successor_approved_input_id",
        )
        _required_text(event.rationale, "rationale")
        _validate_causal_review(event)
    elif event.event_type == "superseded":
        successor = validate_approved_input_id(
            event.successor_approved_input_id
        )
        if successor == event.approved_input_id:
            raise ApprovedInputIntegrityError(
                "An Approved Input cannot supersede itself."
            )
        _validate_causal_review(event)

    _sha256(event.event_fingerprint, "event_fingerprint")
    if verify_fingerprint and (
        event.event_fingerprint
        != calculate_approved_input_event_fingerprint(event)
    ):
        raise ApprovedInputIntegrityError(
            "Approved Input Event fingerprint does not match content."
        )


def _validate_causal_review(event: ApprovedInputEvent) -> None:
    if not is_valid_review_document_id(
        event.causal_review_document_id
    ):
        raise ApprovedInputValidationError(
            "causal_review_document_id is invalid."
        )
    if not is_valid_review_document_version_id(
        event.causal_review_document_version_id
    ):
        raise ApprovedInputValidationError(
            "causal_review_document_version_id is invalid."
        )
    if not is_valid_review_revision_id(
        event.causal_review_revision_id
    ):
        raise ApprovedInputValidationError(
            "causal_review_revision_id is invalid."
        )
    if not is_valid_human_review_decision_id(
        event.causal_finalization_decision_id
    ):
        raise ApprovedInputValidationError(
            "causal_finalization_decision_id is invalid."
        )
    _sha256(
        event.causal_finalization_decision_fingerprint,
        "causal_finalization_decision_fingerprint",
    )


def _require_no_causal_review(event: ApprovedInputEvent) -> None:
    for label, value in (
        (
            "causal_review_document_id",
            event.causal_review_document_id,
        ),
        (
            "causal_review_document_version_id",
            event.causal_review_document_version_id,
        ),
        (
            "causal_review_revision_id",
            event.causal_review_revision_id,
        ),
        (
            "causal_finalization_decision_id",
            event.causal_finalization_decision_id,
        ),
        (
            "causal_finalization_decision_fingerprint",
            event.causal_finalization_decision_fingerprint,
        ),
    ):
        _require_none(value, label)


def _event_payload(
    event: ApprovedInputEvent,
    *,
    include_fingerprint: bool,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_version": event.schema_version,
        "project_id": event.project_id,
        "approved_input_event_id": event.approved_input_event_id,
        "approved_input_id": event.approved_input_id,
        "event_type": event.event_type,
        "previous_authority_state": event.previous_authority_state,
        "next_authority_state": event.next_authority_state,
        "reason_code": event.reason_code,
        "rationale": event.rationale,
        "actor_identity": event.actor_identity,
        "successor_approved_input_id": (
            event.successor_approved_input_id
        ),
        "causal_review_document_id": (
            event.causal_review_document_id
        ),
        "causal_review_document_version_id": (
            event.causal_review_document_version_id
        ),
        "causal_review_revision_id": (
            event.causal_review_revision_id
        ),
        "causal_finalization_decision_id": (
            event.causal_finalization_decision_id
        ),
        "causal_finalization_decision_fingerprint": (
            event.causal_finalization_decision_fingerprint
        ),
        "occurred_at": event.occurred_at,
        "previous_event_fingerprint": event.previous_event_fingerprint,
    }
    if include_fingerprint:
        payload["event_fingerprint"] = event.event_fingerprint
    return payload


def _exact_object(
    payload: object,
    *,
    expected_fields: frozenset[str],
    label: str,
) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ApprovedInputValidationError(
            f"{label} must be a JSON object."
        )
    actual = frozenset(payload)
    if actual != expected_fields:
        missing = sorted(expected_fields - actual)
        unexpected = sorted(actual - expected_fields)
        raise ApprovedInputValidationError(
            f"{label} fields are not exact; "
            f"missing={missing!r}, unexpected={unexpected!r}."
        )
    return payload


def _object_without_duplicate_keys(
    pairs: list[tuple[str, Any]],
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ApprovedInputValidationError(
                f"Duplicate JSON key is not permitted: {key!r}."
            )
        result[key] = value
    return result


def _required_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ApprovedInputValidationError(
            f"{label} must be a non-empty string."
        )
    return value


def _identifier_text(value: object, label: str) -> str:
    return _required_text(value, label)


def _optional_text(value: object, label: str) -> None:
    if value is None:
        return
    _required_text(value, label)


def _require_none(value: object, label: str) -> None:
    if value is not None:
        raise ApprovedInputIntegrityError(
            f"{label} must be null for this lifecycle event."
        )


def _sha256(value: object, label: str) -> str:
    if not isinstance(value, str) or _SHA256_PATTERN.fullmatch(value) is None:
        raise ApprovedInputValidationError(
            f"{label} must be a lowercase SHA-256 fingerprint."
        )
    return value


def _optional_sha256(value: object, label: str) -> None:
    if value is None:
        return
    _sha256(value, label)


def _utc_timestamp(value: object) -> str:
    if not isinstance(value, str) or _UTC_TIMESTAMP_PATTERN.fullmatch(value) is None:
        raise ApprovedInputValidationError(
            "occurred_at must be one UTC timestamp ending in Z."
        )
    return value
