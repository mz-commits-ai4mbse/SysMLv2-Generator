"""Contract tests for interpretation of fixed Source Evidence."""

from __future__ import annotations

import json

import pytest

from modules.evidence_interpretation import (
    EvidenceInterpretationValidationError,
    materialize_information_unit_candidates,
    parse_evidence_interpretation_output,
)
from modules.source_evidence import (
    SourceEvidenceAnchor,
    create_source_evidence,
)


def evidence(
    evidence_id: str,
    *,
    segment_id: str,
    start: int,
    end: int,
    excerpt: str,
):
    return create_source_evidence(
        project_id="318604",
        source_id="SRC-000001",
        source_projection_id="SP-000001",
        source_evidence_id=evidence_id,
        source_projection_fingerprint="a" * 64,
        source_anchors=(
            SourceEvidenceAnchor(
                segment_id=segment_id,
                start_offset=start,
                end_offset=end,
            ),
        ),
        source_excerpt=excerpt,
        timestamp="2026-08-21T10:00:00Z",
    )


def valid_payload():
    return {
        "interpretations": [
            {
                "source_evidence_id": "EVD-000001",
                "interpreted_statement": (
                    "The remote expert may receive temporary control."
                ),
                "information_type": "function",
                "statement_modality": "descriptive",
                "epistemic_class": "explicit",
                "missing_evidence": None,
                "extraction_rationale": "Directly stated control behavior.",
                "uncertainties": [],
            },
            {
                "source_evidence_id": "EVD-000002",
                "interpreted_statement": (
                    "The operator permission gates remote control."
                ),
                "information_type": "constraint",
                "statement_modality": "descriptive",
                "epistemic_class": "interpretation",
                "missing_evidence": None,
                "extraction_rationale": "Permission condition is explicit.",
                "uncertainties": [
                    "The exact permission mechanism is unspecified."
                ],
            },
        ]
    }


def test_parser_requires_exact_evidence_identity_set() -> None:
    payload = valid_payload()
    parsed = parse_evidence_interpretation_output(
        json.dumps(payload),
        expected_source_evidence_ids=(
            "EVD-000001",
            "EVD-000002",
        ),
    )

    assert tuple(
        value.source_evidence_id for value in parsed
    ) == ("EVD-000001", "EVD-000002")

    payload["interpretations"].pop()
    with pytest.raises(EvidenceInterpretationValidationError):
        parse_evidence_interpretation_output(
            json.dumps(payload),
            expected_source_evidence_ids=(
                "EVD-000001",
                "EVD-000002",
            ),
        )


def test_pre_review_derivation_is_forbidden() -> None:
    payload = valid_payload()
    payload["interpretations"][0][
        "epistemic_class"
    ] = "derivation"

    with pytest.raises(EvidenceInterpretationValidationError):
        parse_evidence_interpretation_output(
            json.dumps(payload),
            expected_source_evidence_ids=(
                "EVD-000001",
                "EVD-000002",
            ),
        )


def test_candidate_grounding_is_taken_from_source_evidence() -> None:
    items = (
        evidence(
            "EVD-000001",
            segment_id="SEG-000001",
            start=4,
            end=18,
            excerpt="remote control",
        ),
        evidence(
            "EVD-000002",
            segment_id="SEG-000002",
            start=2,
            end=12,
            excerpt="permission",
        ),
    )
    parsed = parse_evidence_interpretation_output(
        json.dumps(valid_payload()),
        expected_source_evidence_ids=(
            "EVD-000001",
            "EVD-000002",
        ),
    )

    candidates = materialize_information_unit_candidates(
        evidence=items,
        interpretations=parsed,
    )

    assert candidates[0].candidate_id == "IUC-000001"
    assert candidates[0].source_excerpt == "remote control"
    assert candidates[0].source_anchors[0].segment_id == "SEG-000001"
    assert candidates[0].source_anchors[0].start_offset == 4
    assert candidates[0].source_anchors[0].end_offset == 18
    assert candidates[1].source_excerpt == "permission"
