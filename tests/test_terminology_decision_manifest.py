"""Tests for immutable human Terminology Decision records."""

from __future__ import annotations

from dataclasses import replace
import json

import pytest

from modules.project_glossary.decision_manifest import (
    TERMINOLOGY_DECISION_SCHEMA_VERSION,
    TERMINOLOGY_DECISIONS_DIRECTORY_NAME,
    create_terminology_decision,
    parse_terminology_decision,
    terminology_decision_filename,
    terminology_decision_from_json,
    terminology_decision_to_dict,
    terminology_decision_to_json,
    terminology_decision_transition,
    validate_terminology_decision,
)
from modules.project_glossary.errors import (
    InvalidTerminologyLifecycleTransitionError,
    TerminologyDecisionError,
)
from modules.project_glossary.types import (
    TerminologyDecision,
)


PROJECT_ID = "318604"
DECISION_ID = "TD-000001"
CONCEPT_ID = "PC-000001"
TIMESTAMP = "2026-07-23T12:00:00Z"


def decision_payload(
    *,
    decision: str = "accept",
    previous_status: str = "candidate",
    resulting_status: str = "accepted",
) -> dict[str, object]:
    """Return one valid Terminology Decision payload."""

    return {
        "schema_version": (
            TERMINOLOGY_DECISION_SCHEMA_VERSION
        ),
        "project_id": PROJECT_ID,
        "terminology_decision_id": DECISION_ID,
        "project_concept_id": CONCEPT_ID,
        "project_concept_revision": 1,
        "decision": decision,
        "previous_lifecycle_status": previous_status,
        "resulting_lifecycle_status": resulting_status,
        "reviewer_identity": "Moritz Diez",
        "decided_at": TIMESTAMP,
        "rationale": "Human terminology review.",
    }


def accepted_decision() -> TerminologyDecision:
    """Create one valid accepted terminology decision."""

    return create_terminology_decision(
        PROJECT_ID,
        DECISION_ID,
        CONCEPT_ID,
        1,
        decision="accept",
        previous_lifecycle_status="candidate",
        reviewer_identity="Moritz Diez",
        decided_at=TIMESTAMP,
        rationale="Human terminology review.",
    )


def test_decision_constants() -> None:
    assert TERMINOLOGY_DECISION_SCHEMA_VERSION == "1.0.0"
    assert (
        TERMINOLOGY_DECISIONS_DIRECTORY_NAME
        == "terminology_decisions"
    )


@pytest.mark.parametrize(
    ("decision", "expected"),
    [
        (
            "accept",
            ("candidate", "accepted"),
        ),
        (
            "reject",
            ("candidate", "rejected"),
        ),
        (
            "deprecate",
            ("accepted", "deprecated"),
        ),
    ],
)
def test_terminology_decision_transition(
    decision: str,
    expected: tuple[str, str],
) -> None:
    assert terminology_decision_transition(
        decision
    ) == expected


@pytest.mark.parametrize(
    "decision",
    [
        "",
        "approve",
        "accepted",
        "Accept",
        1,
        None,
    ],
)
def test_transition_rejects_unknown_decision(
    decision: object,
) -> None:
    with pytest.raises(TerminologyDecisionError):
        terminology_decision_transition(
            decision  # type: ignore[arg-type]
        )


@pytest.mark.parametrize(
    ("decision", "previous", "resulting"),
    [
        ("accept", "candidate", "accepted"),
        ("reject", "candidate", "rejected"),
        ("deprecate", "accepted", "deprecated"),
    ],
)
def test_create_terminology_decision(
    decision: str,
    previous: str,
    resulting: str,
) -> None:
    created = create_terminology_decision(
        PROJECT_ID,
        DECISION_ID,
        CONCEPT_ID,
        1,
        decision=decision,
        previous_lifecycle_status=previous,
        reviewer_identity="Moritz Diez",
        decided_at=TIMESTAMP,
        rationale="Human terminology review.",
    )

    assert created.decision == decision
    assert created.previous_lifecycle_status == previous
    assert created.resulting_lifecycle_status == resulting
    assert created.reviewer_identity == "Moritz Diez"


@pytest.mark.parametrize(
    ("decision", "previous"),
    [
        ("accept", "accepted"),
        ("accept", "rejected"),
        ("accept", "deprecated"),
        ("reject", "accepted"),
        ("reject", "rejected"),
        ("deprecate", "candidate"),
        ("deprecate", "rejected"),
        ("deprecate", "deprecated"),
    ],
)
def test_create_rejects_invalid_previous_status(
    decision: str,
    previous: str,
) -> None:
    with pytest.raises(
        InvalidTerminologyLifecycleTransitionError
    ):
        create_terminology_decision(
            PROJECT_ID,
            DECISION_ID,
            CONCEPT_ID,
            1,
            decision=decision,
            previous_lifecycle_status=previous,
            reviewer_identity="Moritz Diez",
            decided_at=TIMESTAMP,
            rationale="Invalid transition.",
        )


@pytest.mark.parametrize(
    ("decision_id", "filename"),
    [
        ("TD-000001", "TD-000001.json"),
        ("TD-000042", "TD-000042.json"),
        ("TD-999999", "TD-999999.json"),
    ],
)
def test_terminology_decision_filename(
    decision_id: str,
    filename: str,
) -> None:
    assert terminology_decision_filename(
        decision_id
    ) == filename


@pytest.mark.parametrize(
    "decision_id",
    [
        "TD-000000",
        "TD-1",
        "TD-1000000",
        "td-000001",
        "../TD-000001",
        "TD-000001.json",
        1,
        None,
    ],
)
def test_filename_rejects_invalid_decision_id(
    decision_id: object,
) -> None:
    with pytest.raises(TerminologyDecisionError):
        terminology_decision_filename(
            decision_id  # type: ignore[arg-type]
        )


def test_parse_accept_decision() -> None:
    parsed = parse_terminology_decision(
        decision_payload()
    )

    assert parsed == accepted_decision()


def test_parse_reject_decision() -> None:
    parsed = parse_terminology_decision(
        decision_payload(
            decision="reject",
            previous_status="candidate",
            resulting_status="rejected",
        )
    )

    assert parsed.decision == "reject"
    assert parsed.resulting_lifecycle_status == "rejected"


def test_parse_deprecate_decision() -> None:
    parsed = parse_terminology_decision(
        decision_payload(
            decision="deprecate",
            previous_status="accepted",
            resulting_status="deprecated",
        )
    )

    assert parsed.decision == "deprecate"
    assert parsed.resulting_lifecycle_status == "deprecated"


def test_round_trip_is_deterministic() -> None:
    decision = accepted_decision()
    first = terminology_decision_to_json(decision)
    second = terminology_decision_to_json(decision)
    reloaded = terminology_decision_from_json(
        first,
        expected_project_id=PROJECT_ID,
        expected_terminology_decision_id=DECISION_ID,
    )

    assert first == second
    assert first.endswith("\n")
    assert reloaded == decision
    assert terminology_decision_to_dict(
        decision
    ) == json.loads(first)


def test_unicode_round_trip() -> None:
    decision = replace(
        accepted_decision(),
        reviewer_identity="Mörïtz",
        rationale="Menschlich geprüft: Bedeutung bestätigt.",
    )
    serialized = terminology_decision_to_json(decision)

    assert "Mörïtz" in serialized
    assert "\\u00f6" not in serialized
    assert terminology_decision_from_json(
        serialized
    ) == decision


def test_validate_returns_none() -> None:
    assert validate_terminology_decision(
        accepted_decision(),
        expected_project_id=PROJECT_ID,
        expected_terminology_decision_id=DECISION_ID,
    ) is None


def test_validate_requires_decision_instance() -> None:
    with pytest.raises(TerminologyDecisionError):
        validate_terminology_decision(
            "invalid"  # type: ignore[arg-type]
        )


def test_serializer_revalidates_instance() -> None:
    invalid = replace(
        accepted_decision(),
        decision="approve",
    )

    with pytest.raises(TerminologyDecisionError):
        terminology_decision_to_json(invalid)


@pytest.mark.parametrize(
    "text",
    [
        "",
        "{invalid",
        "[]",
        "null",
        "42",
        '"text"',
    ],
)
def test_from_json_rejects_invalid_document(
    text: str,
) -> None:
    with pytest.raises(TerminologyDecisionError):
        terminology_decision_from_json(text)


def test_from_json_requires_string() -> None:
    with pytest.raises(TerminologyDecisionError):
        terminology_decision_from_json(
            42  # type: ignore[arg-type]
        )


def test_from_json_rejects_duplicate_fields() -> None:
    serialized = json.dumps(decision_payload())
    duplicate = serialized.replace(
        '"decision": "accept"',
        (
            '"decision": "accept", '
            '"decision": "accept"'
        ),
        1,
    )

    with pytest.raises(
        TerminologyDecisionError,
        match="Duplicate JSON field",
    ):
        terminology_decision_from_json(duplicate)


@pytest.mark.parametrize(
    "field",
    sorted(
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
    ),
)
def test_rejects_missing_field(field: str) -> None:
    payload = decision_payload()
    del payload[field]

    with pytest.raises(TerminologyDecisionError):
        parse_terminology_decision(payload)


def test_rejects_unknown_field() -> None:
    payload = decision_payload()
    payload["engineering_approval"] = True

    with pytest.raises(
        TerminologyDecisionError,
        match="unknown engineering_approval",
    ):
        parse_terminology_decision(payload)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("schema_version", "2.0.0"),
        ("schema_version", 1),
        ("project_id", "31860"),
        ("project_id", 318604),
        ("terminology_decision_id", "TD-000000"),
        ("terminology_decision_id", "TD-1"),
        ("project_concept_id", "PC-000000"),
        ("project_concept_id", "PC-1"),
        ("project_concept_revision", 0),
        ("project_concept_revision", True),
        ("project_concept_revision", "1"),
        ("decision", "approve"),
        ("decision", ""),
        ("previous_lifecycle_status", "approved"),
        ("resulting_lifecycle_status", "approved"),
        ("reviewer_identity", ""),
        ("reviewer_identity", " Moritz"),
        ("reviewer_identity", 1),
        ("decided_at", "2026-07-23"),
        ("decided_at", "2026-07-23T12:00:00+00:00"),
        ("decided_at", "invalid"),
        ("rationale", ""),
        ("rationale", " Human review"),
        ("rationale", 1),
    ],
)
def test_field_validation(
    field: str,
    value: object,
) -> None:
    payload = decision_payload()
    payload[field] = value

    with pytest.raises(TerminologyDecisionError):
        parse_terminology_decision(payload)


@pytest.mark.parametrize(
    ("decision", "previous", "resulting"),
    [
        ("accept", "accepted", "accepted"),
        ("accept", "candidate", "rejected"),
        ("reject", "accepted", "rejected"),
        ("reject", "candidate", "accepted"),
        ("deprecate", "candidate", "deprecated"),
        ("deprecate", "accepted", "accepted"),
    ],
)
def test_parse_rejects_invalid_transition(
    decision: str,
    previous: str,
    resulting: str,
) -> None:
    payload = decision_payload(
        decision=decision,
        previous_status=previous,
        resulting_status=resulting,
    )

    with pytest.raises(
        InvalidTerminologyLifecycleTransitionError
    ):
        parse_terminology_decision(payload)


def test_expected_project_id_must_match() -> None:
    with pytest.raises(
        TerminologyDecisionError,
        match="does not match",
    ):
        parse_terminology_decision(
            decision_payload(),
            expected_project_id="318605",
        )


def test_expected_project_id_must_be_valid() -> None:
    with pytest.raises(TerminologyDecisionError):
        parse_terminology_decision(
            decision_payload(),
            expected_project_id="invalid",
        )


def test_expected_decision_id_must_match() -> None:
    with pytest.raises(
        TerminologyDecisionError,
        match="does not match",
    ):
        parse_terminology_decision(
            decision_payload(),
            expected_terminology_decision_id="TD-000002",
        )


def test_expected_decision_id_must_be_valid() -> None:
    with pytest.raises(TerminologyDecisionError):
        parse_terminology_decision(
            decision_payload(),
            expected_terminology_decision_id="invalid",
        )


def test_fractional_utc_timestamp_is_supported() -> None:
    payload = decision_payload()
    payload["decided_at"] = (
        "2026-07-23T12:00:00.123456Z"
    )

    result = parse_terminology_decision(payload)

    assert result.decided_at.endswith(".123456Z")


def test_impossible_calendar_timestamp_is_rejected() -> None:
    payload = decision_payload()
    payload["decided_at"] = "2026-02-30T12:00:00Z"

    with pytest.raises(TerminologyDecisionError):
        parse_terminology_decision(payload)


def test_record_has_no_engineering_approval_field() -> None:
    payload = terminology_decision_to_dict(
        accepted_decision()
    )

    assert "engineering_approval" not in payload
    assert "approved_information_unit_id" not in payload
    assert set(payload) == {
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