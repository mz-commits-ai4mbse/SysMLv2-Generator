"""R4c.3b tests for existing semantic-dimension reuse."""

from __future__ import annotations

import json

import pytest

from modules.engineering_subjects.types import (
    CanonicalEngineeringSubject,
    CanonicalSubjectSet,
    EngineeringMention,
)
from modules.semantic_extraction import (
    INFORMATION_TYPES,
)
from modules.subject_interpretation import (
    SubjectInterpretationValidationError,
    parse_subject_interpretation_output,
)


_SHA = "a" * 64


def _subject_set():
    mentions = (
        EngineeringMention(
            mention_id="MNT-000001",
            source_span_id="SPAN-000001",
            segment_id="SEG-000001",
            start_offset=0,
            end_offset=19,
            exact_text="microscope operator",
            source_evidence_ids=("EVD-000001",),
            content_fingerprint="b" * 64,
        ),
        EngineeringMention(
            mention_id="MNT-000002",
            source_span_id="SPAN-000002",
            segment_id="SEG-000001",
            start_offset=20,
            end_offset=33,
            exact_text="remote expert",
            source_evidence_ids=("EVD-000002",),
            content_fingerprint="c" * 64,
        ),
    )
    return CanonicalSubjectSet(
        schema_version="1.0.0",
        project_id="396272",
        source_id="SRC-000001",
        source_projection_id="SP-000001",
        source_projection_fingerprint=_SHA,
        mentions=mentions,
        subjects=(
            CanonicalEngineeringSubject(
                canonical_subject_id="SUBJ-000001",
                canonical_label="Microscope Operator",
                subject_form="entity",
                identity_status="resolved",
                mention_ids=("MNT-000001",),
                content_fingerprint="d" * 64,
            ),
            CanonicalEngineeringSubject(
                canonical_subject_id="SUBJ-000002",
                canonical_label="Remote Expert",
                subject_form="entity",
                identity_status="resolved",
                mention_ids=("MNT-000002",),
                content_fingerprint="e" * 64,
            ),
        ),
        content_fingerprint="f" * 64,
    )


def _item(subject_id, information_type):
    return {
        "canonical_subject_id": subject_id,
        "interpreted_statement": "Professional interpretation.",
        "information_type": information_type,
        "statement_modality": "descriptive",
        "epistemic_class": "explicit",
        "missing_evidence": None,
        "rationale": "The Source supports this interpretation.",
        "uncertainties": [],
    }


def _payload(relationships=None):
    return {
        "interpretations": [
            _item("SUBJ-000001", "actor"),
            _item("SUBJ-000002", "actor"),
        ],
        "relationships": relationships or [],
    }


def test_existing_information_types_are_reused():
    result = parse_subject_interpretation_output(
        json.dumps(_payload()),
        subject_set=_subject_set(),
    )
    assert all(
        item.information_type in INFORMATION_TYPES
        for item in result.interpretations
    )


@pytest.mark.parametrize("invalid_type", ["entity", "responsibility"])
def test_parallel_semantic_kind_values_are_not_accepted_as_information_types(
    invalid_type,
):
    payload = _payload()
    payload["interpretations"][0] = _item(
        "SUBJ-000001",
        invalid_type,
    )
    with pytest.raises(SubjectInterpretationValidationError):
        parse_subject_interpretation_output(
            json.dumps(payload),
            subject_set=_subject_set(),
        )


def test_unclassified_remains_valid_fail_open_semantic_result():
    payload = _payload()
    payload["interpretations"][0] = _item(
        "SUBJ-000001",
        "unclassified",
    )
    result = parse_subject_interpretation_output(
        json.dumps(payload),
        subject_set=_subject_set(),
    )
    assert result.interpretations[0].information_type == "unclassified"


def test_assumption_requires_missing_evidence():
    payload = _payload()
    payload["interpretations"][0]["epistemic_class"] = "assumption"
    with pytest.raises(SubjectInterpretationValidationError):
        parse_subject_interpretation_output(
            json.dumps(payload),
            subject_set=_subject_set(),
        )

    payload["interpretations"][0]["missing_evidence"] = (
        "The Source does not establish the system boundary."
    )
    result = parse_subject_interpretation_output(
        json.dumps(payload),
        subject_set=_subject_set(),
    )
    assert result.interpretations[0].epistemic_class == "assumption"


def test_derivation_is_not_allowed_in_pre_review_subject_interpretation():
    payload = _payload()
    payload["interpretations"][0]["epistemic_class"] = "derivation"
    with pytest.raises(SubjectInterpretationValidationError):
        parse_subject_interpretation_output(
            json.dumps(payload),
            subject_set=_subject_set(),
        )


def test_explicit_relationship_endpoints_remain_separate():
    payload = _payload(
        [
            {
                "source_subject_id": "SUBJ-000001",
                "relationship_kind": "related_to",
                "target_subject_id": "SUBJ-000002",
                "statement": "The two roles participate in the same context.",
            }
        ]
    )
    result = parse_subject_interpretation_output(
        json.dumps(payload),
        subject_set=_subject_set(),
    )
    assert result.relationships[0].source_subject_id == "SUBJ-000001"
    assert result.relationships[0].target_subject_id == "SUBJ-000002"
