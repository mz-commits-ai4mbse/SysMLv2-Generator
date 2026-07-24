"""Tests for the immutable Information Unit JSON contract."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
import json

import pytest

from modules.information_units.errors import (
    InformationUnitAnchorError,
    InformationUnitAssumptionError,
    InformationUnitDerivationError,
    InformationUnitValidationError,
)
from modules.information_units.manifest import (
    INFORMATION_UNIT_SCHEMA_VERSION,
    calculate_information_unit_content_fingerprint,
    create_information_unit,
    information_unit_from_json,
    information_unit_to_dict,
    information_unit_to_json,
    parse_information_unit,
    validate_information_unit,
)
from modules.information_units.types import (
    EPISTEMIC_CLASSES,
    INFORMATION_TYPES,
    SEMANTIC_CONFIDENCE_LEVELS,
    STATEMENT_MODALITIES,
    InformationUnit,
    InformationUnitExtractionProvenance,
    InformationUnitSourceAnchor,
)


PROJECT_ID = "318604"
INFORMATION_UNIT_ID = "IU-000001"
SOURCE_ID = "SRC-000001"
SOURCE_PROJECTION_ID = "SP-000001"
TIMESTAMP = "2026-07-23T12:00:00Z"


def valid_provenance(
    **changes: object,
) -> InformationUnitExtractionProvenance:
    values: dict[str, object] = {
        "team_id": "TEAM_SEMANTIC_EXTRACTION",
        "persona_ids": (
            "PERSONA_DOMAIN_EXPERT",
            "PERSONA_SYSTEMS_ENGINEER",
        ),
        "llm_provider": "openai",
        "llm_model": "gpt-test",
        "prompt_schema_version": "1.0.0",
        "consensus_report_id": (
            "CONSENSUS_TEAM_SEMANTIC_EXTRACTION_TEST"
        ),
    }
    values.update(changes)
    return InformationUnitExtractionProvenance(**values)


def create_valid_information_unit(
    **changes: object,
) -> InformationUnit:
    values: dict[str, object] = {
        "project_id": PROJECT_ID,
        "information_unit_id": INFORMATION_UNIT_ID,
        "source_id": SOURCE_ID,
        "source_projection_id": SOURCE_PROJECTION_ID,
        "source_anchors": (
            InformationUnitSourceAnchor(
                segment_id="SEG-000001",
                start_offset=0,
                end_offset=42,
            ),
        ),
        "source_excerpt": (
            "The system shall preserve source traceability."
        ),
        "interpreted_statement": (
            "The system shall preserve source traceability."
        ),
        "information_type": "requirement",
        "statement_modality": "normative",
        "epistemic_class": "explicit",
        "supporting_information_unit_ids": (),
        "derivation_rationale": None,
        "missing_evidence": None,
        "extraction_provenance": valid_provenance(),
        "confidence": "high",
        "confidence_rationale": (
            "All required personas agreed."
        ),
        "timestamp": TIMESTAMP,
    }
    values.update(changes)
    return create_information_unit(**values)


def valid_payload() -> dict[str, object]:
    return information_unit_to_dict(
        create_valid_information_unit()
    )


def recalculate_fingerprint(
    payload: dict[str, object],
) -> None:
    anchors = tuple(
        InformationUnitSourceAnchor(
            segment_id=anchor["segment_id"],
            start_offset=anchor["start_offset"],
            end_offset=anchor["end_offset"],
        )
        for anchor in payload["source_anchors"]
    )
    payload["content_fingerprint"] = (
        calculate_information_unit_content_fingerprint(
            project_id=payload["project_id"],
            source_id=payload["source_id"],
            source_projection_id=(
                payload["source_projection_id"]
            ),
            source_anchors=anchors,
            source_excerpt=payload["source_excerpt"],
            interpreted_statement=(
                payload["interpreted_statement"]
            ),
            information_type=payload["information_type"],
            statement_modality=payload["statement_modality"],
            epistemic_class=payload["epistemic_class"],
            supporting_information_unit_ids=tuple(
                payload["supporting_information_unit_ids"]
            ),
            derivation_rationale=(
                payload["derivation_rationale"]
            ),
            missing_evidence=payload["missing_evidence"],
        )
    )


def test_schema_version_is_explicit() -> None:
    assert INFORMATION_UNIT_SCHEMA_VERSION == "1.0.0"


def test_create_valid_information_unit() -> None:
    information_unit = create_valid_information_unit()

    assert information_unit.project_id == PROJECT_ID
    assert (
        information_unit.information_unit_id
        == INFORMATION_UNIT_ID
    )
    assert information_unit.source_id == SOURCE_ID
    assert (
        information_unit.source_projection_id
        == SOURCE_PROJECTION_ID
    )
    assert len(information_unit.content_fingerprint) == 64


def test_information_unit_is_immutable() -> None:
    information_unit = create_valid_information_unit()

    with pytest.raises(FrozenInstanceError):
        information_unit.confidence = "low"


def test_nested_types_are_immutable() -> None:
    information_unit = create_valid_information_unit()

    with pytest.raises(FrozenInstanceError):
        information_unit.source_anchors[0].end_offset = 1

    with pytest.raises(FrozenInstanceError):
        information_unit.extraction_provenance.team_id = "OTHER"


def test_json_round_trip_is_lossless() -> None:
    information_unit = create_valid_information_unit()
    serialized = information_unit_to_json(information_unit)

    reloaded = information_unit_from_json(serialized)

    assert reloaded == information_unit


def test_json_serialization_is_deterministic() -> None:
    information_unit = create_valid_information_unit()

    assert (
        information_unit_to_json(information_unit)
        == information_unit_to_json(information_unit)
    )
    assert information_unit_to_json(information_unit).endswith(
        "\n"
    )


def test_validate_information_unit_accepts_valid_instance() -> None:
    validate_information_unit(create_valid_information_unit())


def test_validate_information_unit_rejects_other_type() -> None:
    with pytest.raises(InformationUnitValidationError):
        validate_information_unit(object())


@pytest.mark.parametrize(
    "field",
    sorted(
        {
            "schema_version",
            "project_id",
            "information_unit_id",
            "source_id",
            "source_projection_id",
            "source_anchors",
            "source_excerpt",
            "interpreted_statement",
            "information_type",
            "statement_modality",
            "epistemic_class",
            "supporting_information_unit_ids",
            "derivation_rationale",
            "missing_evidence",
            "extraction_provenance",
            "confidence",
            "confidence_rationale",
            "content_fingerprint",
            "created_at",
        }
    ),
)
def test_missing_information_unit_field_is_rejected(
    field: str,
) -> None:
    payload = valid_payload()
    del payload[field]

    with pytest.raises(InformationUnitValidationError):
        parse_information_unit(payload)


def test_unknown_information_unit_field_is_rejected() -> None:
    payload = valid_payload()
    payload["unexpected"] = True

    with pytest.raises(InformationUnitValidationError):
        parse_information_unit(payload)


def test_non_object_payload_is_rejected() -> None:
    with pytest.raises(InformationUnitValidationError):
        parse_information_unit([])


@pytest.mark.parametrize(
    "version",
    ["", "1", "1.0", "2.0.0", None, 1],
)
def test_unsupported_schema_version_is_rejected(
    version: object,
) -> None:
    payload = valid_payload()
    payload["schema_version"] = version

    with pytest.raises(InformationUnitValidationError):
        parse_information_unit(payload)


@pytest.mark.parametrize(
    "project_id",
    ["31860", "3186040", "ABCDEF", 318604, None],
)
def test_invalid_project_id_is_rejected(
    project_id: object,
) -> None:
    payload = valid_payload()
    payload["project_id"] = project_id

    with pytest.raises(InformationUnitValidationError):
        parse_information_unit(payload)


@pytest.mark.parametrize(
    "information_unit_id",
    [
        "IU-000000",
        "IU-00001",
        "IU-1000000",
        "IU_000001",
        1,
        None,
    ],
)
def test_invalid_information_unit_id_is_rejected(
    information_unit_id: object,
) -> None:
    payload = valid_payload()
    payload["information_unit_id"] = information_unit_id

    with pytest.raises(InformationUnitValidationError):
        parse_information_unit(payload)


@pytest.mark.parametrize(
    "source_id",
    [
        "SRC-000000",
        "SRC-00001",
        "SOURCE-000001",
        1,
        None,
    ],
)
def test_invalid_source_id_is_rejected(
    source_id: object,
) -> None:
    payload = valid_payload()
    payload["source_id"] = source_id

    with pytest.raises(InformationUnitValidationError):
        parse_information_unit(payload)


@pytest.mark.parametrize(
    "source_projection_id",
    [
        "SP-000000",
        "SP-00001",
        "PROJECTION-000001",
        1,
        None,
    ],
)
def test_invalid_source_projection_id_is_rejected(
    source_projection_id: object,
) -> None:
    payload = valid_payload()
    payload["source_projection_id"] = (
        source_projection_id
    )

    with pytest.raises(InformationUnitValidationError):
        parse_information_unit(payload)


@pytest.mark.parametrize(
    ("expected_name", "expected_value"),
    [
        ("expected_project_id", "999999"),
        (
            "expected_information_unit_id",
            "IU-000002",
        ),
        ("expected_source_id", "SRC-000002"),
        (
            "expected_source_projection_id",
            "SP-000002",
        ),
    ],
)
def test_expected_context_mismatch_is_rejected(
    expected_name: str,
    expected_value: str,
) -> None:
    with pytest.raises(InformationUnitValidationError):
        parse_information_unit(
            valid_payload(),
            **{expected_name: expected_value},
        )


def test_matching_expected_context_is_accepted() -> None:
    information_unit = parse_information_unit(
        valid_payload(),
        expected_project_id=PROJECT_ID,
        expected_information_unit_id=INFORMATION_UNIT_ID,
        expected_source_id=SOURCE_ID,
        expected_source_projection_id=SOURCE_PROJECTION_ID,
    )

    assert information_unit.project_id == PROJECT_ID


@pytest.mark.parametrize(
    "source_anchors",
    [None, {}, "SEG-000001", ()],
)
def test_source_anchors_must_be_non_empty_list(
    source_anchors: object,
) -> None:
    payload = valid_payload()
    payload["source_anchors"] = source_anchors

    with pytest.raises(
        (
            InformationUnitValidationError,
            InformationUnitAnchorError,
        )
    ):
        parse_information_unit(payload)


def test_source_anchor_requires_exact_fields() -> None:
    payload = valid_payload()
    payload["source_anchors"][0]["unknown"] = True

    with pytest.raises(InformationUnitValidationError):
        parse_information_unit(payload)


@pytest.mark.parametrize(
    "segment_id",
    ["SEG-000000", "SEG-00001", "SP-000001", 1, None],
)
def test_invalid_anchor_segment_id_is_rejected(
    segment_id: object,
) -> None:
    payload = valid_payload()
    payload["source_anchors"][0]["segment_id"] = segment_id

    with pytest.raises(InformationUnitAnchorError):
        parse_information_unit(payload)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("start_offset", -1),
        ("start_offset", True),
        ("start_offset", 1.0),
        ("end_offset", 0),
        ("end_offset", -1),
        ("end_offset", True),
        ("end_offset", 1.0),
    ],
)
def test_invalid_anchor_offset_is_rejected(
    field: str,
    value: object,
) -> None:
    payload = valid_payload()
    payload["source_anchors"][0][field] = value

    with pytest.raises(InformationUnitAnchorError):
        parse_information_unit(payload)


@pytest.mark.parametrize(
    ("start_offset", "end_offset"),
    [(0, 0), (4, 4), (5, 4)],
)
def test_anchor_end_must_follow_start(
    start_offset: int,
    end_offset: int,
) -> None:
    payload = valid_payload()
    payload["source_anchors"][0].update(
        {
            "start_offset": start_offset,
            "end_offset": end_offset,
        }
    )

    with pytest.raises(InformationUnitAnchorError):
        parse_information_unit(payload)


def test_ordered_non_overlapping_anchors_are_accepted() -> None:
    payload = valid_payload()
    payload["source_anchors"] = [
        {
            "segment_id": "SEG-000001",
            "start_offset": 0,
            "end_offset": 5,
        },
        {
            "segment_id": "SEG-000001",
            "start_offset": 5,
            "end_offset": 10,
        },
        {
            "segment_id": "SEG-000002",
            "start_offset": 0,
            "end_offset": 7,
        },
    ]
    recalculate_fingerprint(payload)

    parsed = parse_information_unit(payload)

    assert len(parsed.source_anchors) == 3


def test_unordered_anchors_are_rejected() -> None:
    payload = valid_payload()
    payload["source_anchors"] = [
        {
            "segment_id": "SEG-000002",
            "start_offset": 0,
            "end_offset": 5,
        },
        {
            "segment_id": "SEG-000001",
            "start_offset": 0,
            "end_offset": 5,
        },
    ]

    with pytest.raises(InformationUnitAnchorError):
        parse_information_unit(payload)


def test_overlapping_anchors_are_rejected() -> None:
    payload = valid_payload()
    payload["source_anchors"] = [
        {
            "segment_id": "SEG-000001",
            "start_offset": 0,
            "end_offset": 7,
        },
        {
            "segment_id": "SEG-000001",
            "start_offset": 6,
            "end_offset": 10,
        },
    ]

    with pytest.raises(InformationUnitAnchorError):
        parse_information_unit(payload)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("source_excerpt", ""),
        ("source_excerpt", "   "),
        ("source_excerpt", None),
        ("source_excerpt", 1),
        ("source_excerpt", "text\r\n"),
        ("source_excerpt", "text\x00"),
        ("interpreted_statement", ""),
        ("interpreted_statement", "  "),
        ("interpreted_statement", None),
        ("interpreted_statement", " leading"),
        ("interpreted_statement", "trailing "),
        ("interpreted_statement", "text\r\n"),
    ],
)
def test_invalid_professional_text_is_rejected(
    field: str,
    value: object,
) -> None:
    payload = valid_payload()
    payload[field] = value

    with pytest.raises(InformationUnitValidationError):
        parse_information_unit(payload)


def test_source_excerpt_preserves_edge_whitespace() -> None:
    payload = valid_payload()
    payload["source_excerpt"] = "  exact source text\n"
    recalculate_fingerprint(payload)

    parsed = parse_information_unit(payload)

    assert parsed.source_excerpt == "  exact source text\n"


def test_atomicity_is_not_guessed_from_punctuation() -> None:
    information_unit = create_valid_information_unit(
        interpreted_statement=(
            "If the session starts, the system shall stream; "
            "the operator retains control."
        )
    )

    assert ";" in information_unit.interpreted_statement


@pytest.mark.parametrize(
    "information_type",
    sorted(INFORMATION_TYPES),
)
def test_every_information_type_is_accepted(
    information_type: str,
) -> None:
    information_unit = create_valid_information_unit(
        information_type=information_type
    )

    assert information_unit.information_type == information_type


def test_unknown_information_type_is_rejected() -> None:
    payload = valid_payload()
    payload["information_type"] = "subsystem"

    with pytest.raises(InformationUnitValidationError):
        parse_information_unit(payload)


@pytest.mark.parametrize(
    "statement_modality",
    sorted(STATEMENT_MODALITIES),
)
def test_every_statement_modality_is_accepted(
    statement_modality: str,
) -> None:
    information_unit = create_valid_information_unit(
        statement_modality=statement_modality
    )

    assert (
        information_unit.statement_modality
        == statement_modality
    )


def test_unknown_statement_modality_is_rejected() -> None:
    payload = valid_payload()
    payload["statement_modality"] = "mandatory"

    with pytest.raises(InformationUnitValidationError):
        parse_information_unit(payload)


@pytest.mark.parametrize(
    "confidence",
    sorted(SEMANTIC_CONFIDENCE_LEVELS),
)
def test_every_confidence_level_is_accepted(
    confidence: str,
) -> None:
    information_unit = create_valid_information_unit(
        confidence=confidence
    )

    assert information_unit.confidence == confidence


def test_unknown_confidence_is_rejected() -> None:
    payload = valid_payload()
    payload["confidence"] = "certain"

    with pytest.raises(InformationUnitValidationError):
        parse_information_unit(payload)


def test_derivation_with_support_is_accepted() -> None:
    information_unit = create_valid_information_unit(
        information_unit_id="IU-000003",
        epistemic_class="derivation",
        supporting_information_unit_ids=(
            "IU-000001",
            "IU-000002",
        ),
        derivation_rationale=(
            "The statement follows from both supporting units."
        ),
    )

    assert information_unit.epistemic_class == "derivation"


@pytest.mark.parametrize(
    ("supporting_ids", "rationale", "missing_evidence"),
    [
        ((), "A rationale.", None),
        (("IU-000001",), None, None),
        (
            ("IU-000001",),
            "A rationale.",
            "Unexpected missing evidence.",
        ),
    ],
)
def test_invalid_derivation_evidence_is_rejected(
    supporting_ids: tuple[str, ...],
    rationale: str | None,
    missing_evidence: str | None,
) -> None:
    with pytest.raises(InformationUnitDerivationError):
        create_valid_information_unit(
            information_unit_id="IU-000003",
            epistemic_class="derivation",
            supporting_information_unit_ids=supporting_ids,
            derivation_rationale=rationale,
            missing_evidence=missing_evidence,
        )


def test_assumption_with_missing_evidence_is_accepted() -> None:
    information_unit = create_valid_information_unit(
        epistemic_class="assumption",
        missing_evidence=(
            "The source does not identify the responsible actor."
        ),
    )

    assert information_unit.epistemic_class == "assumption"


@pytest.mark.parametrize(
    ("supporting_ids", "rationale", "missing_evidence"),
    [
        ((), None, None),
        (
            ("IU-000002",),
            None,
            "Evidence is missing.",
        ),
        (
            (),
            "Not a derivation.",
            "Evidence is missing.",
        ),
    ],
)
def test_invalid_assumption_evidence_is_rejected(
    supporting_ids: tuple[str, ...],
    rationale: str | None,
    missing_evidence: str | None,
) -> None:
    with pytest.raises(InformationUnitAssumptionError):
        create_valid_information_unit(
            epistemic_class="assumption",
            supporting_information_unit_ids=supporting_ids,
            derivation_rationale=rationale,
            missing_evidence=missing_evidence,
        )


@pytest.mark.parametrize(
    "epistemic_class",
    ["explicit", "interpretation"],
)
def test_source_grounded_class_has_no_auxiliary_evidence(
    epistemic_class: str,
) -> None:
    information_unit = create_valid_information_unit(
        epistemic_class=epistemic_class
    )

    assert not information_unit.supporting_information_unit_ids
    assert information_unit.derivation_rationale is None
    assert information_unit.missing_evidence is None


@pytest.mark.parametrize(
    "epistemic_class",
    sorted(EPISTEMIC_CLASSES),
)
def test_every_epistemic_class_has_valid_representation(
    epistemic_class: str,
) -> None:
    changes: dict[str, object] = {
        "epistemic_class": epistemic_class
    }

    if epistemic_class == "derivation":
        changes.update(
            {
                "information_unit_id": "IU-000002",
                "supporting_information_unit_ids": (
                    "IU-000001",
                ),
                "derivation_rationale": (
                    "The supporting unit entails this statement."
                ),
            }
        )
    elif epistemic_class == "assumption":
        changes["missing_evidence"] = (
            "The source omits the required confirmation."
        )

    information_unit = create_valid_information_unit(
        **changes
    )

    assert information_unit.epistemic_class == epistemic_class


def test_supporting_ids_must_be_ordered_and_unique() -> None:
    for identifiers in (
        ("IU-000001", "IU-000001"),
        ("IU-000002", "IU-000001"),
    ):
        with pytest.raises(InformationUnitDerivationError):
            create_valid_information_unit(
                information_unit_id="IU-000003",
                epistemic_class="derivation",
                supporting_information_unit_ids=identifiers,
                derivation_rationale="Valid rationale.",
            )


def test_self_support_is_rejected() -> None:
    with pytest.raises(InformationUnitDerivationError):
        create_valid_information_unit(
            epistemic_class="derivation",
            supporting_information_unit_ids=(
                INFORMATION_UNIT_ID,
            ),
            derivation_rationale="Circular rationale.",
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("team_id", ""),
        ("team_id", " TEAM"),
        ("llm_provider", ""),
        ("llm_model", ""),
        ("prompt_schema_version", "1.0"),
        ("prompt_schema_version", "latest"),
        ("consensus_report_id", ""),
    ],
)
def test_invalid_provenance_text_is_rejected(
    field: str,
    value: object,
) -> None:
    payload = valid_payload()
    payload["extraction_provenance"][field] = value

    with pytest.raises(InformationUnitValidationError):
        parse_information_unit(payload)


@pytest.mark.parametrize(
    "persona_ids",
    [
        [],
        "PERSONA_A",
        ["PERSONA_A", "PERSONA_A"],
        ["PERSONA_B", "PERSONA_A"],
        ["", "PERSONA_A"],
    ],
)
def test_invalid_persona_ids_are_rejected(
    persona_ids: object,
) -> None:
    payload = valid_payload()
    payload["extraction_provenance"]["persona_ids"] = (
        persona_ids
    )

    with pytest.raises(InformationUnitValidationError):
        parse_information_unit(payload)


def test_provenance_requires_exact_fields() -> None:
    payload = valid_payload()
    payload["extraction_provenance"]["unexpected"] = True

    with pytest.raises(InformationUnitValidationError):
        parse_information_unit(payload)


@pytest.mark.parametrize(
    "rationale",
    ["", " ", " leading", "trailing ", None, 1],
)
def test_invalid_confidence_rationale_is_rejected(
    rationale: object,
) -> None:
    payload = valid_payload()
    payload["confidence_rationale"] = rationale

    with pytest.raises(InformationUnitValidationError):
        parse_information_unit(payload)


@pytest.mark.parametrize(
    "fingerprint",
    [
        "",
        "a" * 63,
        "a" * 65,
        "A" * 64,
        "g" * 64,
        None,
    ],
)
def test_invalid_fingerprint_format_is_rejected(
    fingerprint: object,
) -> None:
    payload = valid_payload()
    payload["content_fingerprint"] = fingerprint

    with pytest.raises(InformationUnitValidationError):
        parse_information_unit(payload)


def test_fingerprint_mismatch_is_rejected() -> None:
    payload = valid_payload()
    payload["interpreted_statement"] = (
        "The statement was silently changed."
    )

    with pytest.raises(InformationUnitValidationError):
        parse_information_unit(payload)


def test_fingerprint_excludes_identity_and_run_metadata() -> None:
    first = create_valid_information_unit()
    second = create_valid_information_unit(
        information_unit_id="IU-000002",
        extraction_provenance=valid_provenance(
            llm_model="different-model",
            consensus_report_id="CONSENSUS_OTHER",
        ),
        confidence="low",
        confidence_rationale="The personas disagreed.",
        timestamp="2026-07-23T13:00:00Z",
    )

    assert (
        first.content_fingerprint
        == second.content_fingerprint
    )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        (
            "source_excerpt",
            "Different exact source evidence.",
        ),
        (
            "interpreted_statement",
            "A different semantic interpretation.",
        ),
        ("information_type", "constraint"),
        ("statement_modality", "descriptive"),
    ],
)
def test_professional_content_changes_fingerprint(
    field: str,
    value: object,
) -> None:
    first = create_valid_information_unit()
    second = create_valid_information_unit(
        information_unit_id="IU-000002",
        **{field: value},
    )

    assert (
        first.content_fingerprint
        != second.content_fingerprint
    )


@pytest.mark.parametrize(
    "timestamp",
    [
        "",
        "2026-07-23",
        "2026-07-23T12:00:00",
        "2026-07-23T12:00:00+00:00",
        "2026-02-30T12:00:00Z",
        None,
    ],
)
def test_invalid_timestamp_is_rejected(
    timestamp: object,
) -> None:
    payload = valid_payload()
    payload["created_at"] = timestamp

    with pytest.raises(InformationUnitValidationError):
        parse_information_unit(payload)


def test_invalid_json_is_rejected() -> None:
    with pytest.raises(InformationUnitValidationError):
        information_unit_from_json("{invalid")


def test_non_string_json_is_rejected() -> None:
    with pytest.raises(InformationUnitValidationError):
        information_unit_from_json({})


def test_duplicate_json_field_is_rejected() -> None:
    text = information_unit_to_json(
        create_valid_information_unit()
    )
    duplicated = text.replace(
        '"project_id": "318604",',
        (
            '"project_id": "318604",\n'
            '  "project_id": "318604",'
        ),
        1,
    )

    with pytest.raises(InformationUnitValidationError):
        information_unit_from_json(duplicated)


def test_serialization_revalidates_modified_instance() -> None:
    information_unit = create_valid_information_unit()
    invalid = replace(
        information_unit,
        confidence="certain",
    )

    with pytest.raises(InformationUnitValidationError):
        information_unit_to_dict(invalid)


def test_create_rejects_non_tuple_anchors() -> None:
    with pytest.raises(InformationUnitAnchorError):
        create_valid_information_unit(
            source_anchors=[
                InformationUnitSourceAnchor(
                    "SEG-000001",
                    0,
                    5,
                )
            ]
        )


def test_create_rejects_non_tuple_support_ids() -> None:
    with pytest.raises(InformationUnitValidationError):
        create_valid_information_unit(
            supporting_information_unit_ids=[]
        )


def test_fingerprint_is_deterministic() -> None:
    information_unit = create_valid_information_unit()

    recalculated = (
        calculate_information_unit_content_fingerprint(
            project_id=information_unit.project_id,
            source_id=information_unit.source_id,
            source_projection_id=(
                information_unit.source_projection_id
            ),
            source_anchors=information_unit.source_anchors,
            source_excerpt=information_unit.source_excerpt,
            interpreted_statement=(
                information_unit.interpreted_statement
            ),
            information_type=(
                information_unit.information_type
            ),
            statement_modality=(
                information_unit.statement_modality
            ),
            epistemic_class=(
                information_unit.epistemic_class
            ),
            supporting_information_unit_ids=(
                information_unit.supporting_information_unit_ids
            ),
            derivation_rationale=(
                information_unit.derivation_rationale
            ),
            missing_evidence=(
                information_unit.missing_evidence
            ),
        )
    )

    assert recalculated == information_unit.content_fingerprint


def test_json_payload_contains_no_review_or_mapping_state() -> None:
    payload = json.loads(
        information_unit_to_json(
            create_valid_information_unit()
        )
    )

    prohibited_fields = {
        "human_review",
        "engineering_approval",
        "framework_assignment",
        "terminology_mapping",
        "ontology_mapping",
        "approved",
    }

    assert prohibited_fields.isdisjoint(payload)