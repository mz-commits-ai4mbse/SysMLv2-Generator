"""R4c.2 tests for system-owned mention anchors."""

from __future__ import annotations

import json

import pytest

from modules.engineering_subjects import (
    EngineeringSubjectIntegrityError,
    EngineeringSubjectValidationError,
)
from modules.engineering_subjects.contract import (
    materialize_canonical_subject_set,
    parse_subject_discovery_output,
)
from modules.engineering_subjects.types import (
    DiscoverySourceSpan,
    DiscoverySourceToken,
)


_SHA = "a" * 64


def _span():
    text = "make later\nreview possible"
    tokens = (
        DiscoverySourceToken(
            token_id="TOK-000001",
            source_span_id="SPAN-000001",
            segment_id="SEG-000001",
            start_offset=0,
            end_offset=4,
            exact_text="make",
        ),
        DiscoverySourceToken(
            token_id="TOK-000002",
            source_span_id="SPAN-000001",
            segment_id="SEG-000001",
            start_offset=5,
            end_offset=10,
            exact_text="later",
        ),
        DiscoverySourceToken(
            token_id="TOK-000003",
            source_span_id="SPAN-000001",
            segment_id="SEG-000001",
            start_offset=11,
            end_offset=17,
            exact_text="review",
        ),
        DiscoverySourceToken(
            token_id="TOK-000004",
            source_span_id="SPAN-000001",
            segment_id="SEG-000001",
            start_offset=18,
            end_offset=26,
            exact_text="possible",
        ),
    )
    return DiscoverySourceSpan(
        span_id="SPAN-000001",
        segment_id="SEG-000001",
        start_offset=0,
        end_offset=len(text),
        exact_text=text,
        source_evidence_ids=("EVD-000001",),
        source_tokens=tokens,
    )


def _materialize(start_token_id, end_token_id):
    proposals = parse_subject_discovery_output(
        json.dumps(
            {
                "subjects": [
                    {
                        "canonical_label": "Later Review",
                        "subject_form": "behavior",
                        "identity_status": "resolved",
                        "mentions": [
                            {
                                "source_span_id": "SPAN-000001",
                                "start_token_id": start_token_id,
                                "end_token_id": end_token_id,
                            }
                        ],
                    }
                ]
            }
        )
    )

    return materialize_canonical_subject_set(
        project_id="396272",
        source_id="SRC-000001",
        source_projection_id="SP-000001",
        source_projection_fingerprint=_SHA,
        source_spans=(_span(),),
        proposals=proposals,
    )


def test_system_reconstructs_exact_source_including_line_wrap():
    result = _materialize("TOK-000002", "TOK-000003")
    mention = result.mentions[0]

    assert mention.exact_text == "later\nreview"
    assert mention.start_offset == 5
    assert mention.end_offset == 17


def test_unknown_token_fails_closed():
    with pytest.raises(EngineeringSubjectIntegrityError):
        _materialize("TOK-000002", "TOK-999999")


def test_reversed_token_range_fails_closed():
    with pytest.raises(EngineeringSubjectIntegrityError):
        _materialize("TOK-000003", "TOK-000002")


def test_free_source_phrase_is_rejected_by_schema():
    with pytest.raises(EngineeringSubjectValidationError):
        parse_subject_discovery_output(
            json.dumps(
                {
                    "subjects": [
                        {
                            "canonical_label": "Later Review",
                            "subject_form": "behavior",
                            "identity_status": "resolved",
                            "mentions": [
                                {
                                    "source_span_id": "SPAN-000001",
                                    "source_phrase": "later review",
                                    "occurrence_index": 1,
                                }
                            ],
                        }
                    ]
                }
            )
        )
