"""Strict immutable manifest for Human Review Decisions."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from .errors import (
    HumanReviewIntegrityError,
    HumanReviewReferenceError,
    HumanReviewValidationError,
)
from .identifiers import validate_human_review_decision_id
from .types import (
    HUMAN_REVIEW_DECISIONS,
    HUMAN_REVIEW_MODES,
    HUMAN_REVIEW_TARGET_TYPES,
    REFERENCE_VALIDATION_STATUSES,
    HumanReviewDecision,
    HumanReviewTargetSnapshot,
)


HUMAN_REVIEW_DECISION_SCHEMA_VERSION = "1.0.0"

_TARGET_ID_PATTERNS = {
    "information_unit_publication": re.compile(
        r"^IU-[0-9]{6}$"
    ),
    "terminology_mapping_candidate": re.compile(
        r"^TMC-[0-9]{6}$"
    ),
    "framework_assignment_candidate": re.compile(
        r"^FAC-[0-9]{6}$"
    ),
    "review_document_finalization": re.compile(
        r"^RVV-[0-9]{6}$"
    ),
}
_GENERAL_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_TIMESTAMP = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T"
    r"[0-9]{2}:[0-9]{2}:[0-9]{2}Z$"
)
_FIELDS = frozenset(
    {
        "schema_version",
        "project_id",
        "human_review_decision_id",
        "target",
        "review_mode",
        "decision",
        "reviewer_identity",
        "rationale",
        "decided_at",
        "decision_fingerprint",
    }
)
_TARGET_FIELDS = frozenset(
    {
        "target_type",
        "target_id",
        "target_content_fingerprint",
        "recommended_review_mode",
        "confirmation_required",
        "reference_validation_status",
        "reference_validation_fingerprint",
    }
)


def create_human_review_target_snapshot(
    *,
    target_type: str,
    target_id: str,
    target_content_fingerprint: str,
    recommended_review_mode: str,
    confirmation_required: bool,
    reference_validation_status: str,
    reference_validation_fingerprint: str | None,
) -> HumanReviewTargetSnapshot:
    """Create one exact immutable target snapshot."""

    return _parse_target(
        {
            "target_type": target_type,
            "target_id": target_id,
            "target_content_fingerprint": (
                target_content_fingerprint
            ),
            "recommended_review_mode": recommended_review_mode,
            "confirmation_required": confirmation_required,
            "reference_validation_status": (
                reference_validation_status
            ),
            "reference_validation_fingerprint": (
                reference_validation_fingerprint
            ),
        }
    )


def create_human_review_decision(
    *,
    project_id: str,
    human_review_decision_id: str,
    target: HumanReviewTargetSnapshot,
    review_mode: str,
    decision: str,
    reviewer_identity: str,
    rationale: str | None,
    timestamp: str,
) -> HumanReviewDecision:
    """Create one immutable human decision without mutating its target."""

    if not isinstance(target, HumanReviewTargetSnapshot):
        raise HumanReviewValidationError(
            "target must be a HumanReviewTargetSnapshot."
        )
    provisional = HumanReviewDecision(
        schema_version=HUMAN_REVIEW_DECISION_SCHEMA_VERSION,
        project_id=project_id,
        human_review_decision_id=human_review_decision_id,
        target=target,
        review_mode=review_mode,
        decision=decision,
        reviewer_identity=reviewer_identity,
        rationale=rationale,
        decided_at=timestamp,
        decision_fingerprint="0" * 64,
    )
    fingerprint = calculate_human_review_decision_fingerprint(
        provisional
    )
    return parse_human_review_decision(
        {
            **_payload(provisional),
            "decision_fingerprint": fingerprint,
        },
        expected_project_id=project_id,
        expected_human_review_decision_id=(
            human_review_decision_id
        ),
    )


def calculate_human_review_decision_fingerprint(
    decision: HumanReviewDecision,
) -> str:
    """Calculate the identity-independent decision fingerprint."""

    data = _payload(decision)
    data.pop("human_review_decision_id")
    data.pop("decision_fingerprint")
    data.pop("decided_at")
    canonical = json.dumps(
        data,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(
        canonical.encode("utf-8")
    ).hexdigest()


def validate_human_review_decision(
    decision: HumanReviewDecision,
) -> None:
    """Validate one in-memory decision."""

    human_review_decision_to_dict(decision)


def human_review_decision_to_dict(
    decision: HumanReviewDecision,
) -> dict[str, Any]:
    """Return one validated JSON-compatible decision object."""

    parsed = parse_human_review_decision(_payload(decision))
    return _payload(parsed)


def human_review_decision_to_json(
    decision: HumanReviewDecision,
) -> str:
    """Serialize one decision deterministically."""

    return (
        json.dumps(
            human_review_decision_to_dict(decision),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )


def human_review_decision_from_json(
    text: str,
    *,
    expected_project_id: str | None = None,
    expected_human_review_decision_id: str | None = None,
) -> HumanReviewDecision:
    """Parse strict JSON into one Human Review Decision."""

    if not isinstance(text, str):
        raise HumanReviewValidationError(
            "Human Review Decision JSON must be a string."
        )
    try:
        payload = json.loads(
            text,
            object_pairs_hook=_without_duplicate_keys,
        )
    except HumanReviewValidationError:
        raise
    except json.JSONDecodeError as exc:
        raise HumanReviewValidationError(
            f"Human Review Decision contains invalid JSON: {exc}."
        ) from exc
    return parse_human_review_decision(
        payload,
        expected_project_id=expected_project_id,
        expected_human_review_decision_id=(
            expected_human_review_decision_id
        ),
    )


def parse_human_review_decision(
    payload: Any,
    *,
    expected_project_id: str | None = None,
    expected_human_review_decision_id: str | None = None,
) -> HumanReviewDecision:
    """Parse and strictly validate one decision object."""

    data = _exact_object(
        payload,
        _FIELDS,
        "Human Review Decision",
    )
    project_id = _identifier(
        data["project_id"],
        _GENERAL_ID,
        "project_id",
    )
    decision_id = validate_human_review_decision_id(
        data["human_review_decision_id"]
    )
    _expected_optional(
        project_id,
        expected_project_id,
        "project_id",
    )
    _expected_optional(
        decision_id,
        expected_human_review_decision_id,
        "human_review_decision_id",
    )
    target = _parse_target(data["target"])
    review_mode = _choice(
        data["review_mode"],
        HUMAN_REVIEW_MODES,
        "review_mode",
    )
    selected_decision = _choice(
        data["decision"],
        HUMAN_REVIEW_DECISIONS,
        "decision",
    )
    rationale = _optional_text(data["rationale"], "rationale")
    _validate_gate(
        target,
        review_mode,
        selected_decision,
        rationale,
    )
    decision = HumanReviewDecision(
        schema_version=_expected(
            data["schema_version"],
            HUMAN_REVIEW_DECISION_SCHEMA_VERSION,
            "schema_version",
        ),
        project_id=project_id,
        human_review_decision_id=decision_id,
        target=target,
        review_mode=review_mode,
        decision=selected_decision,
        reviewer_identity=_text(
            data["reviewer_identity"],
            "reviewer_identity",
        ),
        rationale=rationale,
        decided_at=_identifier(
            data["decided_at"],
            _TIMESTAMP,
            "decided_at",
        ),
        decision_fingerprint=_identifier(
            data["decision_fingerprint"],
            _SHA256,
            "decision_fingerprint",
        ),
    )
    if decision.decision_fingerprint != (
        calculate_human_review_decision_fingerprint(decision)
    ):
        raise HumanReviewIntegrityError(
            "Human Review Decision fingerprint does not match "
            "its content."
        )
    return decision


def _parse_target(value: Any) -> HumanReviewTargetSnapshot:
    data = _exact_object(
        value,
        _TARGET_FIELDS,
        "Human Review Target Snapshot",
    )
    target_type = _choice(
        data["target_type"],
        HUMAN_REVIEW_TARGET_TYPES,
        "target_type",
    )
    target_id = _identifier(
        data["target_id"],
        _TARGET_ID_PATTERNS[target_type],
        "target_id",
    )
    recommended_review_mode = _choice(
        data["recommended_review_mode"],
        HUMAN_REVIEW_MODES,
        "recommended_review_mode",
    )

    if (
        target_type
        == "review_document_finalization"
        and recommended_review_mode
        != "detailed_review"
    ):
        raise HumanReviewIntegrityError(
            "Review Document finalization must "
            "recommend detailed_review."
        )

    confirmation_required = _boolean(
        data["confirmation_required"],
        "confirmation_required",
    )
    if confirmation_required is not True:
        raise HumanReviewIntegrityError(
            "Every review target must require explicit confirmation."
        )
    validation_status = _choice(
        data["reference_validation_status"],
        REFERENCE_VALIDATION_STATUSES,
        "reference_validation_status",
    )
    validation_fingerprint = _optional_sha256(
        data["reference_validation_fingerprint"],
        "reference_validation_fingerprint",
    )
    if validation_status == "not_applicable":
        if (
            target_type != "information_unit_publication"
            or validation_fingerprint is not None
        ):
            raise HumanReviewIntegrityError(
                "not_applicable validation is reserved for Information "
                "Unit publication without a validation fingerprint."
            )
    elif validation_fingerprint is None:
        raise HumanReviewIntegrityError(
            "Candidate targets require a reference-validation "
            "fingerprint."
        )
    return HumanReviewTargetSnapshot(
        target_type=target_type,
        target_id=target_id,
        target_content_fingerprint=_identifier(
            data["target_content_fingerprint"],
            _SHA256,
            "target_content_fingerprint",
        ),
        recommended_review_mode=(
            recommended_review_mode
        ),
        confirmation_required=True,
        reference_validation_status=validation_status,
        reference_validation_fingerprint=validation_fingerprint,
    )


def _validate_gate(
    target: HumanReviewTargetSnapshot,
    review_mode: str,
    decision: str,
    rationale: str | None,
) -> None:
    if (
        target.target_type
        == "review_document_finalization"
        and review_mode != "detailed_review"
    ):
        raise HumanReviewIntegrityError(
            "Review Document finalization requires "
            "detailed_review."
        )

    if review_mode == "quick_confirmation" and (
        target.recommended_review_mode != "quick_confirmation"
        or target.reference_validation_status == "invalid"
    ):
        raise HumanReviewIntegrityError(
            "quick_confirmation is not permitted for this target."
        )
    if decision == "confirm":
        if target.reference_validation_status == "invalid":
            raise HumanReviewIntegrityError(
                "A reference-invalid target must not be confirmed."
            )
    elif rationale is None:
        raise HumanReviewIntegrityError(
            f"{decision} requires a reviewer rationale."
        )


def _payload(decision: HumanReviewDecision) -> dict[str, Any]:
    if not isinstance(decision, HumanReviewDecision):
        raise HumanReviewValidationError(
            "decision must be a HumanReviewDecision."
        )
    return {
        "schema_version": decision.schema_version,
        "project_id": decision.project_id,
        "human_review_decision_id": (
            decision.human_review_decision_id
        ),
        "target": {
            "target_type": decision.target.target_type,
            "target_id": decision.target.target_id,
            "target_content_fingerprint": (
                decision.target.target_content_fingerprint
            ),
            "recommended_review_mode": (
                decision.target.recommended_review_mode
            ),
            "confirmation_required": (
                decision.target.confirmation_required
            ),
            "reference_validation_status": (
                decision.target.reference_validation_status
            ),
            "reference_validation_fingerprint": (
                decision.target.reference_validation_fingerprint
            ),
        },
        "review_mode": decision.review_mode,
        "decision": decision.decision,
        "reviewer_identity": decision.reviewer_identity,
        "rationale": decision.rationale,
        "decided_at": decision.decided_at,
        "decision_fingerprint": decision.decision_fingerprint,
    }


def _exact_object(
    value: Any,
    expected: frozenset[str],
    label: str,
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise HumanReviewValidationError(
            f"{label} must be an object."
        )
    actual = frozenset(value)
    if actual != expected:
        raise HumanReviewValidationError(
            f"{label} has invalid fields; "
            f"missing={sorted(expected - actual)}, "
            f"unknown={sorted(actual - expected)}."
        )
    return value


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise HumanReviewValidationError(
            f"{label} must be a non-empty string."
        )
    if value != value.strip():
        raise HumanReviewValidationError(
            f"{label} must not contain surrounding whitespace."
        )
    return value


def _identifier(
    value: Any,
    pattern: re.Pattern[str],
    label: str,
) -> str:
    selected = _text(value, label)
    if pattern.fullmatch(selected) is None:
        raise HumanReviewValidationError(
            f"{label} has invalid syntax."
        )
    return selected


def _choice(
    value: Any,
    choices: frozenset[str],
    label: str,
) -> str:
    selected = _text(value, label)
    if selected not in choices:
        raise HumanReviewValidationError(
            f"{label} must be one of {sorted(choices)!r}."
        )
    return selected


def _optional_text(value: Any, label: str) -> str | None:
    return None if value is None else _text(value, label)


def _optional_sha256(value: Any, label: str) -> str | None:
    return (
        None
        if value is None
        else _identifier(value, _SHA256, label)
    )


def _boolean(value: Any, label: str) -> bool:
    if not isinstance(value, bool):
        raise HumanReviewValidationError(
            f"{label} must be a boolean."
        )
    return value


def _expected(value: Any, expected: str, label: str) -> str:
    if value != expected:
        raise HumanReviewValidationError(
            f"{label} must be {expected!r}."
        )
    return expected


def _expected_optional(
    actual: str,
    expected: str | None,
    label: str,
) -> None:
    if expected is not None and actual != expected:
        raise HumanReviewReferenceError(
            f"{label} must be {expected!r}, got {actual!r}."
        )


def _without_duplicate_keys(
    pairs: list[tuple[str, Any]],
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise HumanReviewValidationError(
                f"Duplicate JSON object key: {key!r}."
            )
        result[key] = value
    return result