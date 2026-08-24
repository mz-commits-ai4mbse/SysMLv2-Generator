"""Contract tests for persona-independent source-grounded Evidence."""

from __future__ import annotations

import json

import pytest

from modules.source_evidence import (
    SourceEvidenceAnchor,
    SourceEvidenceAnchorError,
    SourceEvidenceValidationError,
    calculate_source_evidence_content_fingerprint,
    create_source_evidence,
    format_source_evidence_id,
    next_source_evidence_id,
    source_evidence_from_json,
    source_evidence_to_json,
)


PROJECT_ID = "318604"
SOURCE_ID = "SRC-000001"
SOURCE_PROJECTION_ID = "SP-000001"
PROJECTION_FINGERPRINT = "a" * 64
TIMESTAMP = "2026-08-21T10:00:00Z"


def evidence():
    return create_source_evidence(
        project_id=PROJECT_ID,
        source_id=SOURCE_ID,
        source_projection_id=SOURCE_PROJECTION_ID,
        source_evidence_id="EVD-000001",
        source_projection_fingerprint=PROJECTION_FINGERPRINT,
        source_anchors=(
            SourceEvidenceAnchor(
                segment_id="SEG-000001",
                start_offset=4,
                end_offset=18,
            ),
        ),
        source_excerpt="remote control",
        timestamp=TIMESTAMP,
    )


def test_identifier_format_and_allocation_are_sequential() -> None:
    assert format_source_evidence_id(1) == "EVD-000001"
    assert next_source_evidence_id(
        ("EVD-000001", "EVD-000003")
    ) == "EVD-000004"


def test_source_evidence_is_immutable_source_identity() -> None:
    item = evidence()

    assert item.project_id == PROJECT_ID
    assert item.source_id == SOURCE_ID
    assert item.source_projection_id == SOURCE_PROJECTION_ID
    assert item.source_evidence_id == "EVD-000001"
    assert item.source_excerpt == "remote control"
    assert len(item.source_anchors) == 1


def test_fingerprint_excludes_id_and_timestamp() -> None:
    item = evidence()

    expected = calculate_source_evidence_content_fingerprint(
        project_id=item.project_id,
        source_id=item.source_id,
        source_projection_id=item.source_projection_id,
        source_projection_fingerprint=(
            item.source_projection_fingerprint
        ),
        source_anchors=item.source_anchors,
        source_excerpt=item.source_excerpt,
    )

    second = create_source_evidence(
        project_id=item.project_id,
        source_id=item.source_id,
        source_projection_id=item.source_projection_id,
        source_evidence_id="EVD-000099",
        source_projection_fingerprint=(
            item.source_projection_fingerprint
        ),
        source_anchors=item.source_anchors,
        source_excerpt=item.source_excerpt,
        timestamp="2026-08-21T11:00:00Z",
    )

    assert item.content_fingerprint == expected
    assert second.content_fingerprint == expected


def test_json_round_trip_is_canonical() -> None:
    item = evidence()

    text = source_evidence_to_json(item)
    assert source_evidence_from_json(text) == item
    assert source_evidence_to_json(
        source_evidence_from_json(text)
    ) == text


def test_unknown_fields_fail_closed() -> None:
    payload = json.loads(source_evidence_to_json(evidence()))
    payload["interpretation"] = "must not exist here"

    with pytest.raises(SourceEvidenceValidationError):
        source_evidence_from_json(json.dumps(payload))


def test_empty_excerpt_is_rejected() -> None:
    with pytest.raises(SourceEvidenceValidationError):
        create_source_evidence(
            project_id=PROJECT_ID,
            source_id=SOURCE_ID,
            source_projection_id=SOURCE_PROJECTION_ID,
            source_evidence_id="EVD-000001",
            source_projection_fingerprint=PROJECTION_FINGERPRINT,
            source_anchors=(
                SourceEvidenceAnchor(
                    segment_id="SEG-000001",
                    start_offset=0,
                    end_offset=1,
                ),
            ),
            source_excerpt="",
            timestamp=TIMESTAMP,
        )


def test_anchor_order_and_duplicates_fail_closed() -> None:
    with pytest.raises(SourceEvidenceAnchorError):
        create_source_evidence(
            project_id=PROJECT_ID,
            source_id=SOURCE_ID,
            source_projection_id=SOURCE_PROJECTION_ID,
            source_evidence_id="EVD-000001",
            source_projection_fingerprint=PROJECTION_FINGERPRINT,
            source_anchors=(
                SourceEvidenceAnchor(
                    segment_id="SEG-000002",
                    start_offset=0,
                    end_offset=1,
                ),
                SourceEvidenceAnchor(
                    segment_id="SEG-000001",
                    start_offset=0,
                    end_offset=1,
                ),
            ),
            source_excerpt="ab",
            timestamp=TIMESTAMP,
        )
