"""Tests for immutable Processing Decision manifests."""

import json
import re

import pytest

from modules.project_processing.decision_manifest import (
    PROCESSING_DECISION_SCHEMA_VERSION,
    create_processing_decision,
    parse_processing_decision,
    processing_decision_filename,
    processing_decision_from_json,
    processing_decision_to_dict,
    processing_decision_to_json,
    validate_processing_decision,
)
from modules.project_processing.errors import (
    ProcessingIntegrityError,
    ProcessingValidationError,
)


SOURCE_SHA256 = "a" * 64
TIMESTAMP = "2026-07-25T10:00:00Z"


def _processing_decision(**overrides):
    values = {
        "project_id": "318604",
        "processing_decision_id": "PD-000001",
        "decision_type": "source_disposition",
        "source_id": "SRC-000001",
        "source_sha256": SOURCE_SHA256,
        "disposition": "in_scope",
        "reviewer_identity": "Moritz Diez",
        "rationale": (
            "The source contains engineering information "
            "relevant to the project."
        ),
        "timestamp": TIMESTAMP,
        "supersedes_processing_decision_id": None,
    }
    values.update(overrides)
    return create_processing_decision(**values)


def test_processing_decision_schema_version_is_stable():
    assert PROCESSING_DECISION_SCHEMA_VERSION == "1.0.0"


def test_create_processing_decision_builds_valid_manifest():
    decision = _processing_decision()

    assert decision.schema_version == "1.0.0"
    assert decision.project_id == "318604"
    assert decision.processing_decision_id == "PD-000001"
    assert decision.decision_type == "source_disposition"
    assert decision.source_id == "SRC-000001"
    assert decision.source_sha256 == SOURCE_SHA256
    assert decision.disposition == "in_scope"
    assert decision.reviewer_identity == "Moritz Diez"
    assert decision.decided_at == TIMESTAMP
    assert decision.supersedes_processing_decision_id is None

    assert re.fullmatch(
        r"[0-9a-f]{64}",
        decision.decision_fingerprint,
    )

    validate_processing_decision(decision)


@pytest.mark.parametrize(
    "disposition",
    [
        "in_scope",
        "context_only",
        "out_of_scope",
    ],
)
def test_processing_decision_accepts_supported_dispositions(
    disposition,
):
    decision = _processing_decision(
        disposition=disposition,
    )

    assert decision.disposition == disposition


def test_processing_decision_dict_round_trip():
    original = _processing_decision()

    payload = processing_decision_to_dict(original)
    restored = parse_processing_decision(payload)

    assert restored == original


def test_processing_decision_json_round_trip():
    original = _processing_decision()

    serialized = processing_decision_to_json(original)
    restored = processing_decision_from_json(serialized)

    assert restored == original
    assert serialized.endswith("\n")
    assert json.loads(serialized) == (
        processing_decision_to_dict(original)
    )


def test_processing_decision_json_is_pretty_printed():
    serialized = processing_decision_to_json(
        _processing_decision()
    )

    assert serialized.startswith("{\n")
    assert '  "schema_version": "1.0.0"' in serialized


def test_processing_decision_omits_null_supersession():
    decision = _processing_decision()

    payload = processing_decision_to_dict(decision)
    serialized = processing_decision_to_json(decision)

    assert "supersedes_processing_decision_id" not in payload
    assert "supersedes_processing_decision_id" not in serialized

    restored = parse_processing_decision(payload)

    assert restored.supersedes_processing_decision_id is None


def test_processing_decision_preserves_supersession():
    decision = _processing_decision(
        processing_decision_id="PD-000002",
        supersedes_processing_decision_id="PD-000001",
    )

    payload = processing_decision_to_dict(decision)
    restored = parse_processing_decision(payload)

    assert (
        payload["supersedes_processing_decision_id"]
        == "PD-000001"
    )
    assert (
        restored.supersedes_processing_decision_id
        == "PD-000001"
    )


def test_processing_decision_fingerprint_is_deterministic():
    first = _processing_decision()
    second = _processing_decision()

    assert (
        first.decision_fingerprint
        == second.decision_fingerprint
    )


def test_processing_decision_fingerprint_changes_with_content():
    first = _processing_decision(
        disposition="in_scope",
    )
    second = _processing_decision(
        disposition="out_of_scope",
    )

    assert (
        first.decision_fingerprint
        != second.decision_fingerprint
    )


def test_processing_decision_filename_uses_validated_identifier():
    assert (
        processing_decision_filename("PD-000042")
        == "PD-000042.json"
    )


@pytest.mark.parametrize(
    ("field_name", "invalid_value"),
    [
        ("project_id", "12345"),
        ("project_id", "1234567"),
        ("processing_decision_id", "PD-000000"),
        ("processing_decision_id", "PD-1"),
        ("decision_type", "engineering_approval"),
        ("source_id", "SRC-000000"),
        ("source_id", "SOURCE-000001"),
        ("source_sha256", "a" * 63),
        ("source_sha256", "A" * 64),
        ("disposition", "approved"),
        ("reviewer_identity", ""),
        ("reviewer_identity", " Moritz Diez"),
        ("reviewer_identity", "Moritz Diez "),
        ("rationale", ""),
        ("rationale", " Untrimmed rationale"),
        ("rationale", "Untrimmed rationale "),
        ("timestamp", "2026-07-25T10:00:00"),
        ("timestamp", "2026-07-25T12:00:00+02:00"),
        (
            "supersedes_processing_decision_id",
            "PD-000000",
        ),
    ],
)
def test_create_processing_decision_rejects_invalid_values(
    field_name,
    invalid_value,
):
    with pytest.raises(ProcessingValidationError):
        _processing_decision(
            **{field_name: invalid_value},
        )


def test_processing_decision_rejects_self_supersession():
    with pytest.raises(ProcessingValidationError):
        _processing_decision(
            processing_decision_id="PD-000001",
            supersedes_processing_decision_id="PD-000001",
        )


def test_processing_decision_filename_rejects_invalid_identifier():
    with pytest.raises(ProcessingValidationError):
        processing_decision_filename("PD-1")


@pytest.mark.parametrize(
    "missing_field",
    [
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
        "decision_fingerprint",
    ],
)
def test_parse_processing_decision_rejects_missing_fields(
    missing_field,
):
    payload = processing_decision_to_dict(
        _processing_decision()
    )
    payload.pop(missing_field)

    with pytest.raises(ProcessingValidationError):
        parse_processing_decision(payload)


def test_parse_processing_decision_rejects_unknown_fields():
    payload = processing_decision_to_dict(
        _processing_decision()
    )
    payload["unexpected"] = "value"

    with pytest.raises(ProcessingValidationError):
        parse_processing_decision(payload)


def test_processing_decision_json_rejects_duplicate_keys():
    serialized = processing_decision_to_json(
        _processing_decision()
    )

    duplicate_json = serialized.replace(
        '"project_id": "318604",',
        (
            '"project_id": "318604",\n'
            '  "project_id": "318604",'
        ),
    )

    with pytest.raises(ProcessingValidationError):
        processing_decision_from_json(duplicate_json)


def test_processing_decision_detects_content_tampering():
    payload = processing_decision_to_dict(
        _processing_decision()
    )
    payload["disposition"] = "out_of_scope"

    with pytest.raises(ProcessingIntegrityError):
        parse_processing_decision(payload)


def test_processing_decision_detects_fingerprint_tampering():
    payload = processing_decision_to_dict(
        _processing_decision()
    )
    payload["decision_fingerprint"] = "b" * 64

    with pytest.raises(ProcessingIntegrityError):
        parse_processing_decision(payload)