"""Validate, parse and serialize Terminology Decision records.

Terminology Decisions document human review of Project Concept lifecycle
states. They approve terminology only and never constitute Engineering
Approval.
"""

from __future__ import annotations

from datetime import datetime
import json
import re
from typing import Any

from modules.project_workspace.identifiers import is_valid_project_id

from .errors import (
    InvalidTerminologyLifecycleTransitionError,
    ProjectGlossaryValidationError,
    TerminologyDecisionError,
)
from .identifiers import (
    is_valid_project_concept_id,
    is_valid_terminology_decision_id,
)
from .normalization import require_stored_glossary_text
from .types import (
    PROJECT_CONCEPT_LIFECYCLE_STATES,
    TERMINOLOGY_DECISION_ACTIONS,
    TerminologyDecision,
)


TERMINOLOGY_DECISION_SCHEMA_VERSION = "1.0.0"
TERMINOLOGY_DECISIONS_DIRECTORY_NAME = (
    "terminology_decisions"
)

_UTC_TIMESTAMP_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T"
    r"\d{2}:\d{2}:\d{2}"
    r"(?:\.\d+)?Z$"
)

_TERMINOLOGY_DECISION_FIELDS = frozenset(
    {
        "schema_version",
        "project_id",
        "terminology_decision_id",
        "project_concept_id",
        "project_concept_revision",
        "decision",
        "previous_lifecycle_status",
        "resulting_lifecycle_status",
        "reviewer_identity",
        "decided_at",
        "rationale",
    }
)

_DECISION_TRANSITIONS = {
    "accept": (
        "candidate",
        "accepted",
    ),
    "reject": (
        "candidate",
        "rejected",
    ),
    "deprecate": (
        "accepted",
        "deprecated",
    ),
}


def terminology_decision_filename(
    terminology_decision_id: str,
) -> str:
    """Return the canonical filename for one Decision ID."""

    validated_id = _require_terminology_decision_id(
        terminology_decision_id,
        "terminology_decision_id",
    )
    return f"{validated_id}.json"


def terminology_decision_transition(
    decision: str,
) -> tuple[str, str]:
    """Return the required previous and resulting lifecycle states."""

    validated_decision = _require_decision_action(
        decision,
        "decision",
    )
    return _DECISION_TRANSITIONS[validated_decision]


def create_terminology_decision(
    project_id: str,
    terminology_decision_id: str,
    project_concept_id: str,
    project_concept_revision: int,
    *,
    decision: str,
    previous_lifecycle_status: str,
    reviewer_identity: str,
    decided_at: str,
    rationale: str,
) -> TerminologyDecision:
    """Create one validated immutable human terminology decision."""

    required_previous_status, resulting_status = (
        terminology_decision_transition(decision)
    )

    if previous_lifecycle_status != required_previous_status:
        raise InvalidTerminologyLifecycleTransitionError(
            f"Decision {decision!r} requires previous lifecycle "
            f"status {required_previous_status!r}, not "
            f"{previous_lifecycle_status!r}."
        )

    return parse_terminology_decision(
        {
            "schema_version": (
                TERMINOLOGY_DECISION_SCHEMA_VERSION
            ),
            "project_id": project_id,
            "terminology_decision_id": (
                terminology_decision_id
            ),
            "project_concept_id": project_concept_id,
            "project_concept_revision": (
                project_concept_revision
            ),
            "decision": decision,
            "previous_lifecycle_status": (
                previous_lifecycle_status
            ),
            "resulting_lifecycle_status": resulting_status,
            "reviewer_identity": reviewer_identity,
            "decided_at": decided_at,
            "rationale": rationale,
        },
        expected_project_id=project_id,
        expected_terminology_decision_id=(
            terminology_decision_id
        ),
    )


def parse_terminology_decision(
    payload: Any,
    *,
    expected_project_id: str | None = None,
    expected_terminology_decision_id: str | None = None,
) -> TerminologyDecision:
    """Parse and validate one Terminology Decision payload."""

    decision_object = _require_exact_object(
        payload,
        _TERMINOLOGY_DECISION_FIELDS,
        "Terminology Decision",
    )

    schema_version = decision_object["schema_version"]

    if schema_version != TERMINOLOGY_DECISION_SCHEMA_VERSION:
        raise TerminologyDecisionError(
            "Unsupported Terminology Decision schema_version: "
            f"{schema_version!r}."
        )

    project_id = _require_project_id(
        decision_object["project_id"],
        "project_id",
    )

    if expected_project_id is not None:
        validated_expected_project_id = _require_project_id(
            expected_project_id,
            "expected_project_id",
        )

        if project_id != validated_expected_project_id:
            raise TerminologyDecisionError(
                "Terminology Decision project_id does not match "
                f"its project directory: {project_id!r} != "
                f"{validated_expected_project_id!r}."
            )

    terminology_decision_id = (
        _require_terminology_decision_id(
            decision_object["terminology_decision_id"],
            "terminology_decision_id",
        )
    )

    if expected_terminology_decision_id is not None:
        validated_expected_decision_id = (
            _require_terminology_decision_id(
                expected_terminology_decision_id,
                "expected_terminology_decision_id",
            )
        )

        if (
            terminology_decision_id
            != validated_expected_decision_id
        ):
            raise TerminologyDecisionError(
                "Terminology Decision ID does not match its "
                f"filename: {terminology_decision_id!r} != "
                f"{validated_expected_decision_id!r}."
            )

    project_concept_id = _require_project_concept_id(
        decision_object["project_concept_id"],
        "project_concept_id",
    )
    project_concept_revision = _require_positive_integer(
        decision_object["project_concept_revision"],
        "project_concept_revision",
    )
    decision = _require_decision_action(
        decision_object["decision"],
        "decision",
    )
    previous_lifecycle_status = _require_lifecycle_status(
        decision_object["previous_lifecycle_status"],
        "previous_lifecycle_status",
    )
    resulting_lifecycle_status = _require_lifecycle_status(
        decision_object["resulting_lifecycle_status"],
        "resulting_lifecycle_status",
    )

    required_previous_status, required_resulting_status = (
        terminology_decision_transition(decision)
    )

    if (
        previous_lifecycle_status
        != required_previous_status
        or resulting_lifecycle_status
        != required_resulting_status
    ):
        raise InvalidTerminologyLifecycleTransitionError(
            f"Decision {decision!r} requires lifecycle transition "
            f"{required_previous_status!r} -> "
            f"{required_resulting_status!r}; received "
            f"{previous_lifecycle_status!r} -> "
            f"{resulting_lifecycle_status!r}."
        )

    reviewer_identity = _require_stored_text(
        decision_object["reviewer_identity"],
        "reviewer_identity",
    )
    decided_at, _ = _require_utc_timestamp(
        decision_object["decided_at"],
        "decided_at",
    )
    rationale = _require_stored_text(
        decision_object["rationale"],
        "rationale",
    )

    return TerminologyDecision(
        schema_version=schema_version,
        project_id=project_id,
        terminology_decision_id=terminology_decision_id,
        project_concept_id=project_concept_id,
        project_concept_revision=project_concept_revision,
        decision=decision,
        previous_lifecycle_status=(
            previous_lifecycle_status
        ),
        resulting_lifecycle_status=(
            resulting_lifecycle_status
        ),
        reviewer_identity=reviewer_identity,
        decided_at=decided_at,
        rationale=rationale,
    )


def terminology_decision_from_json(
    text: str,
    *,
    expected_project_id: str | None = None,
    expected_terminology_decision_id: str | None = None,
) -> TerminologyDecision:
    """Parse and validate Terminology Decision JSON text."""

    if not isinstance(text, str):
        raise TerminologyDecisionError(
            "Terminology Decision JSON input must be a string."
        )

    try:
        payload = json.loads(
            text,
            object_pairs_hook=_object_without_duplicate_keys,
        )
    except TerminologyDecisionError:
        raise
    except json.JSONDecodeError as exc:
        raise TerminologyDecisionError(
            f"Terminology Decision contains invalid JSON: {exc}."
        ) from exc

    return parse_terminology_decision(
        payload,
        expected_project_id=expected_project_id,
        expected_terminology_decision_id=(
            expected_terminology_decision_id
        ),
    )


def validate_terminology_decision(
    terminology_decision: TerminologyDecision,
    *,
    expected_project_id: str | None = None,
    expected_terminology_decision_id: str | None = None,
) -> None:
    """Validate an immutable TerminologyDecision instance."""

    parse_terminology_decision(
        _terminology_decision_payload(
            terminology_decision
        ),
        expected_project_id=expected_project_id,
        expected_terminology_decision_id=(
            expected_terminology_decision_id
        ),
    )


def terminology_decision_to_dict(
    terminology_decision: TerminologyDecision,
) -> dict[str, Any]:
    """Return a validated JSON-compatible Decision dictionary."""

    payload = _terminology_decision_payload(
        terminology_decision
    )
    parse_terminology_decision(payload)
    return payload


def terminology_decision_to_json(
    terminology_decision: TerminologyDecision,
) -> str:
    """Serialize one Terminology Decision deterministically."""

    return json.dumps(
        terminology_decision_to_dict(
            terminology_decision
        ),
        ensure_ascii=False,
        indent=2,
    ) + "\n"


def _terminology_decision_payload(
    terminology_decision: TerminologyDecision,
) -> dict[str, Any]:
    if not isinstance(
        terminology_decision,
        TerminologyDecision,
    ):
        raise TerminologyDecisionError(
            "terminology_decision must be a "
            "TerminologyDecision instance."
        )

    return {
        "schema_version": terminology_decision.schema_version,
        "project_id": terminology_decision.project_id,
        "terminology_decision_id": (
            terminology_decision.terminology_decision_id
        ),
        "project_concept_id": (
            terminology_decision.project_concept_id
        ),
        "project_concept_revision": (
            terminology_decision.project_concept_revision
        ),
        "decision": terminology_decision.decision,
        "previous_lifecycle_status": (
            terminology_decision.previous_lifecycle_status
        ),
        "resulting_lifecycle_status": (
            terminology_decision.resulting_lifecycle_status
        ),
        "reviewer_identity": (
            terminology_decision.reviewer_identity
        ),
        "decided_at": terminology_decision.decided_at,
        "rationale": terminology_decision.rationale,
    }


def _require_project_id(
    value: Any,
    label: str,
) -> str:
    if not is_valid_project_id(value):
        raise TerminologyDecisionError(
            f"{label} must contain exactly six digits."
        )

    return value


def _require_terminology_decision_id(
    value: Any,
    label: str,
) -> str:
    if not is_valid_terminology_decision_id(value):
        raise TerminologyDecisionError(
            f"{label} must match ^TD-[0-9]{{6}}$ and must not "
            "use sequence 000000."
        )

    return value


def _require_project_concept_id(
    value: Any,
    label: str,
) -> str:
    if not is_valid_project_concept_id(value):
        raise TerminologyDecisionError(
            f"{label} must match ^PC-[0-9]{{6}}$ and must not "
            "use sequence 000000."
        )

    return value


def _require_decision_action(
    value: Any,
    label: str,
) -> str:
    action = _require_stored_text(value, label)

    if action not in TERMINOLOGY_DECISION_ACTIONS:
        raise TerminologyDecisionError(
            f"{label} must be one of: "
            f"{', '.join(sorted(TERMINOLOGY_DECISION_ACTIONS))}."
        )

    return action


def _require_lifecycle_status(
    value: Any,
    label: str,
) -> str:
    status = _require_stored_text(value, label)

    if status not in PROJECT_CONCEPT_LIFECYCLE_STATES:
        raise TerminologyDecisionError(
            f"{label} must be one of: "
            f"{', '.join(sorted(PROJECT_CONCEPT_LIFECYCLE_STATES))}."
        )

    return status


def _require_stored_text(
    value: Any,
    label: str,
) -> str:
    try:
        return require_stored_glossary_text(
            value,
            label,
        )
    except ProjectGlossaryValidationError as exc:
        raise TerminologyDecisionError(
            str(exc)
        ) from exc


def _require_positive_integer(
    value: Any,
    label: str,
) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value < 1
    ):
        raise TerminologyDecisionError(
            f"{label} must be a positive integer."
        )

    return value


def _require_utc_timestamp(
    value: Any,
    label: str,
) -> tuple[str, datetime]:
    if (
        not isinstance(value, str)
        or _UTC_TIMESTAMP_PATTERN.fullmatch(value) is None
    ):
        raise TerminologyDecisionError(
            f"{label} must be an ISO-8601 UTC timestamp ending in Z."
        )

    try:
        timestamp = datetime.fromisoformat(
            value.removesuffix("Z") + "+00:00"
        )
    except ValueError as exc:
        raise TerminologyDecisionError(
            f"{label} is not a valid UTC timestamp."
        ) from exc

    return value, timestamp


def _require_exact_object(
    value: Any,
    fields: frozenset[str],
    label: str,
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise TerminologyDecisionError(
            f"{label} must be a JSON object."
        )

    actual = set(value)
    missing = sorted(fields - actual)
    unknown = sorted(actual - fields)
    problems: list[str] = []

    if missing:
        problems.append(
            "missing " + ", ".join(missing)
        )

    if unknown:
        problems.append(
            "unknown " + ", ".join(unknown)
        )

    if problems:
        raise TerminologyDecisionError(
            f"{label} fields are invalid: "
            f"{'; '.join(problems)}."
        )

    return value


def _object_without_duplicate_keys(
    pairs: list[tuple[str, Any]],
) -> dict[str, Any]:
    result: dict[str, Any] = {}

    for key, value in pairs:
        if key in result:
            raise TerminologyDecisionError(
                f"Duplicate JSON field: {key!r}."
            )

        result[key] = value

    return result