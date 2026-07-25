"""Create, validate and serialize immutable Processing Decisions."""

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
    ProcessingIntegrityError,
    ProcessingValidationError,
)
from .identifiers import (
    validate_processing_decision_id,
)
from .types import (
    PROCESSING_DECISION_TYPES,
    SOURCE_PROCESSING_DISPOSITIONS,
    ProcessingDecision,
)


PROCESSING_DECISION_SCHEMA_VERSION = "1.0.0"

_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_SOURCE_ID_PATTERN = re.compile(r"^SRC-[0-9]{6}$")
_UTC_TIMESTAMP_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T"
    r"\d{2}:\d{2}:\d{2}"
    r"(?:\.\d+)?Z$"
)

_PROCESSING_DECISION_FIELDS = frozenset(
    {
        "schema_version",
        "project_id",
        "processing_decision_id",
        "decision_type",
        "source_id",
        "source_sha256",
        "disposition",
        "reviewer_identity",
        "rationale",
        "decided_at",
        "supersedes_processing_decision_id",
        "decision_fingerprint",
    }
)


def create_processing_decision(
    *,
    project_id: str,
    processing_decision_id: str,
    decision_type: str,
    source_id: str,
    source_sha256: str,
    disposition: str,
    reviewer_identity: str,
    rationale: str,
    timestamp: str,
    supersedes_processing_decision_id: (
        str | None
    ) = None,
) -> ProcessingDecision:
    """Create one fingerprinted immutable Processing Decision."""

    provisional_decision = ProcessingDecision(
        schema_version=PROCESSING_DECISION_SCHEMA_VERSION,
        project_id=project_id,
        processing_decision_id=processing_decision_id,
        decision_type=decision_type,
        source_id=source_id,
        source_sha256=source_sha256,
        disposition=disposition,
        reviewer_identity=reviewer_identity,
        rationale=rationale,
        decided_at=timestamp,
        supersedes_processing_decision_id=(
            supersedes_processing_decision_id
        ),
        decision_fingerprint="0" * 64,
    )

    _validate_processing_decision(
        provisional_decision,
        verify_fingerprint=False,
    )

    fingerprint = calculate_processing_decision_fingerprint(
        provisional_decision
    )

    decision = replace(
        provisional_decision,
        decision_fingerprint=fingerprint,
    )

    validate_processing_decision(decision)

    return decision


def parse_processing_decision(
    payload: object,
) -> ProcessingDecision:
    """Parse and validate one Processing Decision mapping."""

    if not isinstance(payload, dict):
        raise ProcessingValidationError(
            "Processing Decision must be a JSON object."
        )

    normalized_payload = dict(payload)
    normalized_payload.setdefault(
        "supersedes_processing_decision_id",
        None,
    )

    _require_exact_fields(
        normalized_payload,
        expected_fields=_PROCESSING_DECISION_FIELDS,
        label="Processing Decision",
    )

    decision = ProcessingDecision(
        schema_version=normalized_payload[
            "schema_version"
        ],
        project_id=normalized_payload["project_id"],
        processing_decision_id=normalized_payload[
            "processing_decision_id"
        ],
        decision_type=normalized_payload["decision_type"],
        source_id=normalized_payload["source_id"],
        source_sha256=normalized_payload["source_sha256"],
        disposition=normalized_payload["disposition"],
        reviewer_identity=normalized_payload[
            "reviewer_identity"
        ],
        rationale=normalized_payload["rationale"],
        decided_at=normalized_payload["decided_at"],
        supersedes_processing_decision_id=(
            normalized_payload[
                "supersedes_processing_decision_id"
            ]
        ),
        decision_fingerprint=normalized_payload[
            "decision_fingerprint"
        ],
    )

    validate_processing_decision(decision)

    return decision


def processing_decision_from_json(
    text: object,
) -> ProcessingDecision:
    """Parse one Processing Decision from strict JSON."""

    if not isinstance(text, str):
        raise ProcessingValidationError(
            "Processing Decision JSON must be a string."
        )

    try:
        payload = json.loads(
            text,
            object_pairs_hook=_object_without_duplicate_keys,
        )
    except ProcessingValidationError:
        raise
    except json.JSONDecodeError as exc:
        raise ProcessingValidationError(
            "Processing Decision is not valid JSON."
        ) from exc

    return parse_processing_decision(payload)


def processing_decision_to_dict(
    decision: ProcessingDecision,
) -> dict[str, object]:
    """Serialize one validated Processing Decision."""

    validate_processing_decision(decision)

    return _processing_decision_payload(
        decision,
        include_fingerprint=True,
    )


def processing_decision_to_json(
    decision: ProcessingDecision,
) -> str:
    """Serialize one Processing Decision as deterministic JSON."""

    return (
        json.dumps(
            processing_decision_to_dict(decision),
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )


def processing_decision_filename(
    processing_decision_id: object,
) -> str:
    """Return the canonical filename for one Processing Decision."""

    validated_decision_id = (
        validate_processing_decision_id(
            processing_decision_id
        )
    )

    return f"{validated_decision_id}.json"


def calculate_processing_decision_fingerprint(
    decision: ProcessingDecision,
) -> str:
    """Calculate the deterministic Processing Decision fingerprint."""

    _validate_processing_decision(
        decision,
        verify_fingerprint=False,
    )

    payload = _processing_decision_payload(
        decision,
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


def validate_processing_decision(
    decision: object,
) -> ProcessingDecision:
    """Validate and return one immutable Processing Decision."""

    return _validate_processing_decision(
        decision,
        verify_fingerprint=True,
    )


def _validate_processing_decision(
    decision: object,
    *,
    verify_fingerprint: bool,
) -> ProcessingDecision:
    """Validate one decision with optional fingerprint checking."""

    if not isinstance(decision, ProcessingDecision):
        raise ProcessingValidationError(
            "decision must be a ProcessingDecision."
        )

    if (
        decision.schema_version
        != PROCESSING_DECISION_SCHEMA_VERSION
    ):
        raise ProcessingValidationError(
            "Unsupported Processing Decision schema_version: "
            f"{decision.schema_version!r}."
        )

    if not is_valid_project_id(decision.project_id):
        raise ProcessingValidationError(
            "project_id must match ^[0-9]{6}$."
        )

    try:
        validate_processing_decision_id(
            decision.processing_decision_id
        )
    except Exception as exc:
        raise ProcessingValidationError(
            "processing_decision_id is invalid."
        ) from exc

    if decision.decision_type not in PROCESSING_DECISION_TYPES:
        raise ProcessingValidationError(
            "decision_type is not supported."
        )

    _validate_source_id(decision.source_id)

    _validate_sha256(
        decision.source_sha256,
        label="source_sha256",
    )

    if (
        decision.disposition
        not in SOURCE_PROCESSING_DISPOSITIONS
    ):
        raise ProcessingValidationError(
            "disposition is not supported."
        )

    _validate_trimmed_string(
        decision.reviewer_identity,
        label="reviewer_identity",
        maximum_length=240,
    )

    _validate_trimmed_string(
        decision.rationale,
        label="rationale",
        maximum_length=4000,
    )

    _validate_utc_timestamp(
        decision.decided_at,
        label="decided_at",
    )

    supersedes_decision_id = (
        decision.supersedes_processing_decision_id
    )

    if supersedes_decision_id is not None:
        try:
            validate_processing_decision_id(
                supersedes_decision_id
            )
        except Exception as exc:
            raise ProcessingValidationError(
                "supersedes_processing_decision_id "
                "is invalid."
            ) from exc

        if (
            supersedes_decision_id
            == decision.processing_decision_id
        ):
            raise ProcessingValidationError(
                "A Processing Decision cannot supersede itself."
            )

    if verify_fingerprint:
        _validate_sha256(
            decision.decision_fingerprint,
            label="decision_fingerprint",
        )

        expected_fingerprint = (
            calculate_processing_decision_fingerprint(
                decision
            )
        )

        if (
            decision.decision_fingerprint
            != expected_fingerprint
        ):
            raise ProcessingIntegrityError(
                "decision_fingerprint does not match the "
                "Processing Decision content."
            )

    return decision


def _processing_decision_payload(
    decision: ProcessingDecision,
    *,
    include_fingerprint: bool,
) -> dict[str, object]:
    """Build the canonical serialized decision payload."""

    payload: dict[str, object] = {
        "schema_version": decision.schema_version,
        "project_id": decision.project_id,
        "processing_decision_id": (
            decision.processing_decision_id
        ),
        "decision_type": decision.decision_type,
        "source_id": decision.source_id,
        "source_sha256": decision.source_sha256,
        "disposition": decision.disposition,
        "reviewer_identity": decision.reviewer_identity,
        "rationale": decision.rationale,
        "decided_at": decision.decided_at,
    }

    if (
        decision.supersedes_processing_decision_id
        is not None
    ):
        payload["supersedes_processing_decision_id"] = (
            decision.supersedes_processing_decision_id
        )

    if include_fingerprint:
        payload["decision_fingerprint"] = (
            decision.decision_fingerprint
        )

    return payload


def _validate_source_id(value: object) -> None:
    """Validate one project-local Source ID."""

    if (
        not isinstance(value, str)
        or _SOURCE_ID_PATTERN.fullmatch(value) is None
        or value == "SRC-000000"
    ):
        raise ProcessingValidationError(
            "source_id must match ^SRC-[0-9]{6}$ and use "
            "a sequence from 000001 to 999999."
        )


def _validate_sha256(
    value: object,
    *,
    label: str,
) -> None:
    """Validate one lowercase SHA-256 value."""

    if (
        not isinstance(value, str)
        or _SHA256_PATTERN.fullmatch(value) is None
    ):
        raise ProcessingValidationError(
            f"{label} must be a lowercase 64-character "
            "SHA-256 value."
        )


def _validate_trimmed_string(
    value: object,
    *,
    label: str,
    maximum_length: int,
) -> None:
    """Validate one required trimmed string."""

    if not isinstance(value, str):
        raise ProcessingValidationError(
            f"{label} must be a string."
        )

    if not value:
        raise ProcessingValidationError(
            f"{label} must not be empty."
        )

    if value != value.strip():
        raise ProcessingValidationError(
            f"{label} must not contain surrounding whitespace."
        )

    if len(value) > maximum_length:
        raise ProcessingValidationError(
            f"{label} must contain at most "
            f"{maximum_length} characters."
        )


def _validate_utc_timestamp(
    value: object,
    *,
    label: str,
) -> None:
    """Validate one UTC ISO-8601 timestamp."""

    if (
        not isinstance(value, str)
        or _UTC_TIMESTAMP_PATTERN.fullmatch(value) is None
    ):
        raise ProcessingValidationError(
            f"{label} must be a UTC ISO-8601 timestamp "
            "ending in Z."
        )

    try:
        parsed = datetime.fromisoformat(
            value.removesuffix("Z") + "+00:00"
        )
    except ValueError as exc:
        raise ProcessingValidationError(
            f"{label} is not a valid timestamp."
        ) from exc

    if (
        parsed.utcoffset() is None
        or parsed.utcoffset().total_seconds() != 0
    ):
        raise ProcessingValidationError(
            f"{label} must use UTC."
        )


def _object_without_duplicate_keys(
    pairs: list[tuple[str, Any]],
) -> dict[str, Any]:
    """Reject duplicate JSON object keys."""

    payload: dict[str, Any] = {}

    for key, value in pairs:
        if key in payload:
            raise ProcessingValidationError(
                f"Duplicate JSON field: {key}."
            )

        payload[key] = value

    return payload


def _require_exact_fields(
    payload: dict[str, object],
    *,
    expected_fields: frozenset[str],
    label: str,
) -> None:
    """Require one exact closed field set."""

    actual_fields = frozenset(payload)

    missing_fields = expected_fields - actual_fields
    unknown_fields = actual_fields - expected_fields

    if missing_fields:
        raise ProcessingValidationError(
            f"{label} is missing fields: "
            f"{sorted(missing_fields)}."
        )

    if unknown_fields:
        raise ProcessingValidationError(
            f"{label} contains unknown fields: "
            f"{sorted(unknown_fields)}."
        )