"""R4c.3e bounded classification-repair tests."""

import json

import pytest

from modules.engineering_subjects.types import (
    CanonicalEngineeringSubject,
    CanonicalSubjectSet,
    EngineeringMention,
)
from modules.subject_interpretation import (
    SubjectInterpretationValidationError,
    apply_classification_repair_response,
    find_classification_repair_needs,
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
        ),
        subjects=(
            CanonicalEngineeringSubject(
                canonical_subject_id="SUBJ-000001",
                canonical_label="A",
                subject_form="entity",
                identity_status="resolved",
                mention_ids=("MNT-000001",),
                content_fingerprint="c" * 64,
            ),
        ),
        content_fingerprint="d" * 64,
    )


def _raw(info_type="capability"):
    return json.dumps(
        {
            "interpretations": [
                {
                    "canonical_subject_id": "SUBJ-000001",
                    "interpreted_statement": "A statement.",
                    "information_type": info_type,
                    "statement_modality": "descriptive",
                    "epistemic_class": "explicit",
                    "missing_evidence": None,
                    "rationale": "Rationale.",
                    "uncertainties": [],
                }
            ],
            "relationships": [],
        }
    )


def test_invalid_required_enum_is_detected_without_mapping():
    needs = find_classification_repair_needs(
        _raw(),
        subject_set=_subject_set(),
    )

    assert len(needs) == 1
    assert needs[0].canonical_subject_id == "SUBJ-000001"
    assert needs[0].field_name == "information_type"
    assert needs[0].invalid_value == "capability"


def test_repair_patches_only_identified_field():
    raw = _raw()
    needs = find_classification_repair_needs(
        raw,
        subject_set=_subject_set(),
    )

    repaired, audit = apply_classification_repair_response(
        raw_output=raw,
        repair_output=json.dumps(
            {
                "repairs": [
                    {
                        "canonical_subject_id": "SUBJ-000001",
                        "field_name": "information_type",
                        "value": "unclassified",
                    }
                ]
            }
        ),
        needs=needs,
    )

    payload = json.loads(repaired)
    item = payload["interpretations"][0]
    assert item["information_type"] == "unclassified"
    assert item["interpreted_statement"] == "A statement."
    assert item["statement_modality"] == "descriptive"
    assert item["epistemic_class"] == "explicit"

    assert len(audit) == 1
    assert audit[0].original_value == "capability"
    assert audit[0].repaired_value == "unclassified"


def test_repair_cannot_modify_unidentified_field():
    raw = _raw()
    needs = find_classification_repair_needs(
        raw,
        subject_set=_subject_set(),
    )

    with pytest.raises(SubjectInterpretationValidationError):
        apply_classification_repair_response(
            raw_output=raw,
            repair_output=json.dumps(
                {
                    "repairs": [
                        {
                            "canonical_subject_id": "SUBJ-000001",
                            "field_name": "statement_modality",
                            "value": "normative",
                        }
                    ]
                }
            ),
            needs=needs,
        )


def test_valid_output_needs_no_repair():
    assert find_classification_repair_needs(
        _raw("actor"),
        subject_set=_subject_set(),
    ) == ()
