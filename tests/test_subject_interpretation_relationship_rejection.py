"""R4c.3d unsupported relationship hints are rejected, not admitted."""

from __future__ import annotations

import json

import pytest

from modules.engineering_subjects.types import (
    CanonicalEngineeringSubject,
    CanonicalSubjectSet,
    EngineeringMention,
)
from modules.subject_interpretation import (
    SubjectInterpretationValidationError,
    parse_subject_interpretation_output,
)

_SHA = "a" * 64


def _subject_set():
    return CanonicalSubjectSet(
        schema_version="1.0.0",
        project_id="396272",
        source_id="SRC-000001",
        source_projection_id="SP-000001",
        source_projection_fingerprint=_SHA,
        mentions=(
            EngineeringMention(
                mention_id="MNT-000001",
                source_span_id="SPAN-000001",
                segment_id="SEG-000001",
                start_offset=0,
                end_offset=1,
                exact_text="A",
                source_evidence_ids=("EVD-000001",),
                content_fingerprint="b" * 64,
            ),
            EngineeringMention(
                mention_id="MNT-000002",
                source_span_id="SPAN-000001",
                segment_id="SEG-000001",
                start_offset=2,
                end_offset=3,
                exact_text="B",
                source_evidence_ids=("EVD-000001",),
                content_fingerprint="c" * 64,
            ),
        ),
        subjects=(
            CanonicalEngineeringSubject(
                canonical_subject_id="SUBJ-000001",
                canonical_label="A",
                subject_form="entity",
                identity_status="resolved",
                mention_ids=("MNT-000001",),
                content_fingerprint="d" * 64,
            ),
            CanonicalEngineeringSubject(
                canonical_subject_id="SUBJ-000002",
                canonical_label="B",
                subject_form="entity",
                identity_status="resolved",
                mention_ids=("MNT-000002",),
                content_fingerprint="e" * 64,
            ),
        ),
        content_fingerprint="f" * 64,
    )


def _interpretation(subject_id):
    return {
        "canonical_subject_id": subject_id,
        "interpreted_statement": "Statement.",
        "information_type": "unclassified",
        "statement_modality": "descriptive",
        "epistemic_class": "explicit",
        "missing_evidence": None,
        "rationale": "Rationale.",
        "uncertainties": [],
    }


def _payload(relationship):
    return {
        "interpretations": [
            _interpretation("SUBJ-000001"),
            _interpretation("SUBJ-000002"),
        ],
        "relationships": [relationship],
    }


def test_unsupported_relationship_kind_is_rejected_not_accepted():
    parsed = parse_subject_interpretation_output(
        json.dumps(
            _payload(
                {
                    "source_subject_id": "SUBJ-000001",
                    "relationship_kind": "does_not_define",
                    "target_subject_id": "SUBJ-000002",
                    "statement": "Unsupported candidate relation.",
                }
            )
        ),
        subject_set=_subject_set(),
    )

    assert parsed.relationships == ()
    assert len(parsed.rejected_relationships) == 1
    rejected = parsed.rejected_relationships[0]
    assert rejected.relationship_kind == "does_not_define"
    assert rejected.reason_code == "unsupported_relationship_kind"


def test_unsupported_relationship_is_not_mapped_to_related_to():
    parsed = parse_subject_interpretation_output(
        json.dumps(
            _payload(
                {
                    "source_subject_id": "SUBJ-000001",
                    "relationship_kind": "does_not_define",
                    "target_subject_id": "SUBJ-000002",
                    "statement": "Unsupported candidate relation.",
                }
            )
        ),
        subject_set=_subject_set(),
    )

    assert all(
        relation.relationship_kind != "related_to"
        for relation in parsed.relationships
    )


def test_unknown_subject_endpoint_remains_hard_failure():
    with pytest.raises(SubjectInterpretationValidationError):
        parse_subject_interpretation_output(
            json.dumps(
                _payload(
                    {
                        "source_subject_id": "SUBJ-000001",
                        "relationship_kind": "does_not_define",
                        "target_subject_id": "SUBJ-999999",
                        "statement": "Bad endpoint.",
                    }
                )
            ),
            subject_set=_subject_set(),
        )


def test_self_relationship_remains_hard_failure():
    with pytest.raises(SubjectInterpretationValidationError):
        parse_subject_interpretation_output(
            json.dumps(
                _payload(
                    {
                        "source_subject_id": "SUBJ-000001",
                        "relationship_kind": "does_not_define",
                        "target_subject_id": "SUBJ-000001",
                        "statement": "Self relation.",
                    }
                )
            ),
            subject_set=_subject_set(),
        )
