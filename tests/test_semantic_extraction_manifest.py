"""Tests for the persona-specific Semantic Extraction result contract."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
import json

import pytest

from modules.information_units.types import (
    InformationUnit,
    InformationUnitExtractionProvenance,
    InformationUnitSourceAnchor,
)
from modules.semantic_extraction.errors import (
    DuplicateInformationUnitCandidateError,
    InformationUnitCandidateAnchorError,
    InformationUnitCandidateAssumptionError,
    InformationUnitCandidateDerivationError,
    NoCandidateRationaleError,
    SemanticExtractionReferenceError,
    SemanticExtractionValidationError,
)
from modules.semantic_extraction.manifest import (
    SEMANTIC_EXTRACTION_AGENT_RESULT_SCHEMA_VERSION,
    calculate_information_unit_candidate_fingerprint,
    create_information_unit_candidate,
    create_semantic_extraction_agent_result,
    parse_information_unit_candidate,
    parse_semantic_extraction_agent_result,
    semantic_extraction_agent_result_from_json,
    semantic_extraction_agent_result_to_dict,
    semantic_extraction_agent_result_to_json,
    validate_semantic_extraction_agent_result,
    validate_semantic_extraction_agent_result_context,
)
from modules.semantic_extraction.types import (
    InformationUnitCandidate,
    SemanticExtractionAgentResult,
)
from modules.source_projection.types import (
    ProjectionSegment,
    SourceProjectionArtifact,
    SourceProjectionManifest,
)


PROJECT_ID = "318604"
SOURCE_ID = "SRC-000001"
SOURCE_PROJECTION_ID = "SP-000001"
TIMESTAMP = "2026-07-24T10:00:00Z"


def candidate_payload(
    *,
    candidate_id: str = "IUC-000001",
    segment_id: str = "SEG-000001",
    start_offset: int = 0,
    end_offset: int = 5,
    source_excerpt: str = "Alpha",
    interpreted_statement: str = "Alpha is present.",
) -> dict[str, object]:
    return {
        "candidate_id": candidate_id,
        "source_anchors": [
            {
                "segment_id": segment_id,
                "start_offset": start_offset,
                "end_offset": end_offset,
            }
        ],
        "source_excerpt": source_excerpt,
        "interpreted_statement": interpreted_statement,
        "information_type": "unclassified",
        "statement_modality": "descriptive",
        "epistemic_class": "explicit",
        "supporting_information_unit_ids": [],
        "derivation_rationale": None,
        "missing_evidence": None,
        "extraction_rationale": (
            "The statement is explicit and independently "
            "reviewable."
        ),
        "uncertainties": [],
    }


def result_payload(
    *,
    candidates: list[dict[str, object]] | None = None,
    no_candidate_rationale: str | None = None,
) -> dict[str, object]:
    return {
        "schema_version": "1.0.0",
        "project_id": PROJECT_ID,
        "source_id": SOURCE_ID,
        "source_projection_id": SOURCE_PROJECTION_ID,
        "team_id": "semantic-extraction-team",
        "agent_id": "semantic-extractor-01",
        "persona_id": "systems-engineer",
        "persona_run_index": 1,
        "persona_configuration_fingerprint": "a" * 64,
        "llm_provider": "test-provider",
        "llm_model": "test-model",
        "prompt_schema_version": "1.0.0",
        "candidates": (
            [candidate_payload()]
            if candidates is None
            else candidates
        ),
        "no_candidate_rationale": no_candidate_rationale,
        "created_at": TIMESTAMP,
    }


def projection_artifact(
    *,
    project_id: str = PROJECT_ID,
    source_id: str = SOURCE_ID,
    source_projection_id: str = SOURCE_PROJECTION_ID,
    projection_result: str = "available",
) -> SourceProjectionArtifact:
    manifest = SourceProjectionManifest(
        schema_version="1.0.0",
        project_id=project_id,
        source_id=source_id,
        source_projection_id=source_projection_id,
        source_role="engineering_source",
        source_sha256="b" * 64,
        adapter_id="text",
        adapter_version="1.0.0",
        adapter_configuration=(),
        projection_fingerprint="c" * 64,
        projection_result=projection_result,
        content_sha256="d" * 64,
        content_length=9,
        segments=(
            ProjectionSegment(
                segment_id="SEG-000001",
                segment_type="text",
                start_offset=0,
                end_offset=5,
                text_sha256="e" * 64,
                source_locators=(),
            ),
            ProjectionSegment(
                segment_id="SEG-000002",
                segment_type="text",
                start_offset=5,
                end_offset=9,
                text_sha256="f" * 64,
                source_locators=(),
            ),
        ),
        issues=(),
        created_at=TIMESTAMP,
    )
    return SourceProjectionArtifact(
        manifest=manifest,
        content="AlphaBeta",
    )


def supporting_information_unit(
    *,
    project_id: str = PROJECT_ID,
    source_id: str = SOURCE_ID,
    information_unit_id: str = "IU-000001",
) -> InformationUnit:
    return InformationUnit(
        schema_version="1.0.0",
        project_id=project_id,
        information_unit_id=information_unit_id,
        source_id=source_id,
        source_projection_id=SOURCE_PROJECTION_ID,
        source_anchors=(
            InformationUnitSourceAnchor(
                segment_id="SEG-000001",
                start_offset=0,
                end_offset=5,
            ),
        ),
        source_excerpt="Alpha",
        interpreted_statement="Alpha is present.",
        information_type="unclassified",
        statement_modality="descriptive",
        epistemic_class="explicit",
        supporting_information_unit_ids=(),
        derivation_rationale=None,
        missing_evidence=None,
        extraction_provenance=(
            InformationUnitExtractionProvenance(
                team_id="semantic-extraction-team",
                persona_ids=("systems-engineer",),
                llm_provider="test-provider",
                llm_model="test-model",
                prompt_schema_version="1.0.0",
                consensus_report_id="CONSENSUS-000001",
            )
        ),
        confidence="medium",
        confidence_rationale="Test fixture.",
        content_fingerprint="0" * 64,
        created_at=TIMESTAMP,
    )


def derivation_candidate_payload() -> dict[str, object]:
    payload = candidate_payload()
    payload["epistemic_class"] = "derivation"
    payload["supporting_information_unit_ids"] = [
        "IU-000001"
    ]
    payload["derivation_rationale"] = (
        "The existing unit supports this consequence."
    )
    return payload


def test_schema_version_is_explicit() -> None:
    assert (
        SEMANTIC_EXTRACTION_AGENT_RESULT_SCHEMA_VERSION
        == "1.0.0"
    )


def test_parse_candidate_returns_immutable_type() -> None:
    candidate = parse_information_unit_candidate(
        candidate_payload()
    )

    assert isinstance(candidate, InformationUnitCandidate)
    assert candidate.candidate_id == "IUC-000001"
    assert candidate.source_anchors == (
        InformationUnitSourceAnchor(
            segment_id="SEG-000001",
            start_offset=0,
            end_offset=5,
        ),
    )


def test_create_candidate_validates_input() -> None:
    candidate = create_information_unit_candidate(
        candidate_id="IUC-000001",
        source_anchors=(
            InformationUnitSourceAnchor(
                segment_id="SEG-000001",
                start_offset=0,
                end_offset=5,
            ),
        ),
        source_excerpt="Alpha",
        interpreted_statement="Alpha is present.",
        information_type="unclassified",
        statement_modality="descriptive",
        epistemic_class="explicit",
        extraction_rationale="Direct source statement.",
    )

    assert candidate.candidate_id == "IUC-000001"


def test_parse_result_returns_immutable_type() -> None:
    result = parse_semantic_extraction_agent_result(
        result_payload()
    )

    assert isinstance(result, SemanticExtractionAgentResult)
    assert result.project_id == PROJECT_ID
    assert len(result.candidates) == 1


def test_create_result_validates_input() -> None:
    candidate = parse_information_unit_candidate(
        candidate_payload()
    )
    result = create_semantic_extraction_agent_result(
        project_id=PROJECT_ID,
        source_id=SOURCE_ID,
        source_projection_id=SOURCE_PROJECTION_ID,
        team_id="semantic-extraction-team",
        agent_id="semantic-extractor-01",
        persona_id="systems-engineer",
        persona_run_index=1,
        persona_configuration_fingerprint="a" * 64,
        llm_provider="test-provider",
        llm_model="test-model",
        prompt_schema_version="1.0.0",
        candidates=(candidate,),
        no_candidate_rationale=None,
        timestamp=TIMESTAMP,
    )

    assert result.candidates == (candidate,)


def test_result_json_round_trip_is_deterministic() -> None:
    result = parse_semantic_extraction_agent_result(
        result_payload()
    )
    first = semantic_extraction_agent_result_to_json(result)
    reloaded = semantic_extraction_agent_result_from_json(
        first
    )
    second = semantic_extraction_agent_result_to_json(reloaded)

    assert reloaded == result
    assert first == second
    assert first.endswith("\n")
    assert json.loads(first) == (
        semantic_extraction_agent_result_to_dict(result)
    )


def test_validate_result_accepts_valid_instance() -> None:
    result = parse_semantic_extraction_agent_result(
        result_payload()
    )

    assert validate_semantic_extraction_agent_result(result) is None


def test_zero_candidate_result_requires_rationale() -> None:
    result = parse_semantic_extraction_agent_result(
        result_payload(
            candidates=[],
            no_candidate_rationale=(
                "The projection contains no independently "
                "reviewable engineering statement."
            ),
        )
    )

    assert result.candidates == ()
    assert result.no_candidate_rationale is not None


def test_zero_candidate_result_rejects_missing_rationale() -> None:
    with pytest.raises(NoCandidateRationaleError):
        parse_semantic_extraction_agent_result(
            result_payload(candidates=[])
        )


def test_candidate_result_rejects_no_candidate_rationale() -> None:
    with pytest.raises(NoCandidateRationaleError):
        parse_semantic_extraction_agent_result(
            result_payload(
                no_candidate_rationale="Contradictory."
            )
        )


@pytest.mark.parametrize(
    "candidate_id",
    [
        "IUC-000000",
        "IUC-1",
        "IUC-1000000",
        "IU-000001",
        1,
    ],
)
def test_rejects_invalid_candidate_id(
    candidate_id: object,
) -> None:
    payload = candidate_payload()
    payload["candidate_id"] = candidate_id

    with pytest.raises(SemanticExtractionValidationError):
        parse_information_unit_candidate(payload)


@pytest.mark.parametrize(
    "candidate_ids",
    [
        ("IUC-000002",),
        ("IUC-000001", "IUC-000003"),
        ("IUC-000002", "IUC-000001"),
        ("IUC-000001", "IUC-000001"),
    ],
)
def test_result_requires_gapless_candidate_ids(
    candidate_ids: tuple[str, ...],
) -> None:
    candidates = []

    for index, candidate_id in enumerate(candidate_ids):
        candidates.append(
            candidate_payload(
                candidate_id=candidate_id,
                segment_id=(
                    "SEG-000001"
                    if index == 0
                    else "SEG-000002"
                ),
                start_offset=0,
                end_offset=(
                    5
                    if index == 0
                    else 4
                ),
                source_excerpt=(
                    "Alpha"
                    if index == 0
                    else "Beta"
                ),
                interpreted_statement=(
                    f"Statement {index}."
                ),
            )
        )

    with pytest.raises(SemanticExtractionValidationError):
        parse_semantic_extraction_agent_result(
            result_payload(candidates=candidates)
        )


def test_result_requires_candidate_source_order() -> None:
    candidates = [
        candidate_payload(
            candidate_id="IUC-000001",
            segment_id="SEG-000002",
            start_offset=0,
            end_offset=4,
            source_excerpt="Beta",
            interpreted_statement="Beta is present.",
        ),
        candidate_payload(
            candidate_id="IUC-000002",
            interpreted_statement="Alpha is present.",
        ),
    ]

    with pytest.raises(InformationUnitCandidateAnchorError):
        parse_semantic_extraction_agent_result(
            result_payload(candidates=candidates)
        )


def test_result_rejects_duplicate_professional_content() -> None:
    duplicate = candidate_payload(
        candidate_id="IUC-000002"
    )
    duplicate["extraction_rationale"] = (
        "A differently worded agent rationale."
    )
    duplicate["uncertainties"] = ["Minor wording doubt."]

    with pytest.raises(
        DuplicateInformationUnitCandidateError
    ):
        parse_semantic_extraction_agent_result(
            result_payload(
                candidates=[
                    candidate_payload(),
                    duplicate,
                ]
            )
        )


def test_distinct_professional_content_is_allowed() -> None:
    second = candidate_payload(
        candidate_id="IUC-000002",
        interpreted_statement="Alpha has a defined role.",
    )
    result = parse_semantic_extraction_agent_result(
        result_payload(
            candidates=[
                candidate_payload(),
                second,
            ]
        )
    )

    assert len(result.candidates) == 2


@pytest.mark.parametrize(
    ("expected_name", "expected_value"),
    [
        ("expected_project_id", "999999"),
        ("expected_source_id", "SRC-000002"),
        (
            "expected_source_projection_id",
            "SP-000002",
        ),
        ("expected_team_id", "other-team"),
        ("expected_agent_id", "other-agent"),
        ("expected_persona_id", "other-persona"),
        ("expected_persona_run_index", 2),
    ],
)
def test_expected_context_mismatch_is_rejected(
    expected_name: str,
    expected_value: object,
) -> None:
    with pytest.raises(SemanticExtractionValidationError):
        parse_semantic_extraction_agent_result(
            result_payload(),
            **{expected_name: expected_value},
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("schema_version", "2.0.0"),
        ("project_id", "12345"),
        ("source_id", "SRC-000000"),
        ("source_projection_id", "SP-000000"),
        ("team_id", ""),
        ("agent_id", " agent"),
        ("persona_id", "persona "),
        ("persona_configuration_fingerprint", "A" * 64),
        ("persona_configuration_fingerprint", "a" * 63),
        ("llm_provider", ""),
        ("llm_model", "\x00"),
        ("prompt_schema_version", "1.0"),
        ("created_at", "2026-07-24T10:00:00+00:00"),
        ("created_at", "2026-02-30T10:00:00Z"),
    ],
)
def test_rejects_invalid_result_scalar(
    field: str,
    value: object,
) -> None:
    payload = result_payload()
    payload[field] = value

    with pytest.raises(SemanticExtractionValidationError):
        parse_semantic_extraction_agent_result(payload)


@pytest.mark.parametrize(
    "persona_run_index",
    [0, -1, True, 1.0, "1"],
)
def test_rejects_invalid_persona_run_index(
    persona_run_index: object,
) -> None:
    payload = result_payload()
    payload["persona_run_index"] = persona_run_index

    with pytest.raises(SemanticExtractionValidationError):
        parse_semantic_extraction_agent_result(payload)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("information_type", "invented_type"),
        ("statement_modality", "mandatory"),
        ("epistemic_class", "guess"),
        ("interpreted_statement", ""),
        ("interpreted_statement", " statement"),
        ("extraction_rationale", ""),
        ("extraction_rationale", "rationale "),
    ],
)
def test_rejects_invalid_candidate_scalar(
    field: str,
    value: object,
) -> None:
    payload = candidate_payload()
    payload[field] = value

    with pytest.raises(SemanticExtractionValidationError):
        parse_information_unit_candidate(payload)


def test_source_excerpt_preserves_exact_whitespace() -> None:
    payload = candidate_payload(
        source_excerpt=" Alpha\n",
    )
    candidate = parse_information_unit_candidate(payload)

    assert candidate.source_excerpt == " Alpha\n"


@pytest.mark.parametrize(
    "source_excerpt",
    ["", "   ", "\x00", "\r\n"],
)
def test_rejects_unusable_source_excerpt(
    source_excerpt: str,
) -> None:
    payload = candidate_payload(
        source_excerpt=source_excerpt
    )

    with pytest.raises(SemanticExtractionValidationError):
        parse_information_unit_candidate(payload)


def test_rejects_missing_candidate_field() -> None:
    payload = candidate_payload()
    del payload["uncertainties"]

    with pytest.raises(SemanticExtractionValidationError):
        parse_information_unit_candidate(payload)


def test_rejects_unknown_candidate_field() -> None:
    payload = candidate_payload()
    payload["confidence"] = "high"

    with pytest.raises(SemanticExtractionValidationError):
        parse_information_unit_candidate(payload)


def test_rejects_missing_result_field() -> None:
    payload = result_payload()
    del payload["llm_model"]

    with pytest.raises(SemanticExtractionValidationError):
        parse_semantic_extraction_agent_result(payload)


@pytest.mark.parametrize(
    "forbidden_field",
    [
        "confidence",
        "consensus_level",
        "review_required",
        "framework_assignment",
        "ontology_mapping",
    ],
)
def test_rejects_forbidden_result_field(
    forbidden_field: str,
) -> None:
    payload = result_payload()
    payload[forbidden_field] = "not-allowed"

    with pytest.raises(SemanticExtractionValidationError):
        parse_semantic_extraction_agent_result(payload)


def test_json_input_must_be_string() -> None:
    with pytest.raises(SemanticExtractionValidationError):
        semantic_extraction_agent_result_from_json(  # type: ignore[arg-type]
            {}
        )


def test_rejects_invalid_json() -> None:
    with pytest.raises(SemanticExtractionValidationError):
        semantic_extraction_agent_result_from_json(
            "{invalid"
        )


def test_rejects_duplicate_json_fields() -> None:
    text = (
        '{"schema_version":"1.0.0",'
        '"schema_version":"1.0.0"}'
    )

    with pytest.raises(SemanticExtractionValidationError):
        semantic_extraction_agent_result_from_json(text)


def test_result_to_dict_requires_result_instance() -> None:
    with pytest.raises(SemanticExtractionValidationError):
        semantic_extraction_agent_result_to_dict(  # type: ignore[arg-type]
            {}
        )


def test_create_result_requires_candidate_tuple() -> None:
    with pytest.raises(SemanticExtractionValidationError):
        create_semantic_extraction_agent_result(
            project_id=PROJECT_ID,
            source_id=SOURCE_ID,
            source_projection_id=SOURCE_PROJECTION_ID,
            team_id="semantic-extraction-team",
            agent_id="semantic-extractor-01",
            persona_id="systems-engineer",
            persona_run_index=1,
            persona_configuration_fingerprint="a" * 64,
            llm_provider="test-provider",
            llm_model="test-model",
            prompt_schema_version="1.0.0",
            candidates=[],  # type: ignore[arg-type]
            no_candidate_rationale="No candidate.",
            timestamp=TIMESTAMP,
        )


def test_rejects_empty_source_anchor_collection() -> None:
    payload = candidate_payload()
    payload["source_anchors"] = []

    with pytest.raises(InformationUnitCandidateAnchorError):
        parse_information_unit_candidate(payload)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("segment_id", "SEG-000000"),
        ("start_offset", -1),
        ("start_offset", True),
        ("end_offset", 0),
        ("end_offset", 1.0),
    ],
)
def test_rejects_invalid_source_anchor_value(
    field: str,
    value: object,
) -> None:
    payload = candidate_payload()
    anchors = payload["source_anchors"]
    assert isinstance(anchors, list)
    anchors[0][field] = value

    with pytest.raises(InformationUnitCandidateAnchorError):
        parse_information_unit_candidate(payload)


def test_rejects_empty_source_anchor_range() -> None:
    payload = candidate_payload(
        start_offset=5,
        end_offset=5,
    )

    with pytest.raises(InformationUnitCandidateAnchorError):
        parse_information_unit_candidate(payload)


def test_rejects_unordered_source_anchors() -> None:
    payload = candidate_payload()
    payload["source_anchors"] = [
        {
            "segment_id": "SEG-000002",
            "start_offset": 0,
            "end_offset": 2,
        },
        {
            "segment_id": "SEG-000001",
            "start_offset": 0,
            "end_offset": 2,
        },
    ]

    with pytest.raises(InformationUnitCandidateAnchorError):
        parse_information_unit_candidate(payload)


def test_rejects_overlapping_source_anchors() -> None:
    payload = candidate_payload()
    payload["source_anchors"] = [
        {
            "segment_id": "SEG-000001",
            "start_offset": 0,
            "end_offset": 4,
        },
        {
            "segment_id": "SEG-000001",
            "start_offset": 3,
            "end_offset": 5,
        },
    ]

    with pytest.raises(InformationUnitCandidateAnchorError):
        parse_information_unit_candidate(payload)


def test_adjacent_source_anchors_are_allowed() -> None:
    payload = candidate_payload()
    payload["source_anchors"] = [
        {
            "segment_id": "SEG-000001",
            "start_offset": 0,
            "end_offset": 2,
        },
        {
            "segment_id": "SEG-000001",
            "start_offset": 2,
            "end_offset": 5,
        },
    ]

    candidate = parse_information_unit_candidate(payload)
    assert len(candidate.source_anchors) == 2


def test_derivation_candidate_is_valid() -> None:
    candidate = parse_information_unit_candidate(
        derivation_candidate_payload()
    )

    assert candidate.epistemic_class == "derivation"
    assert candidate.supporting_information_unit_ids == (
        "IU-000001",
    )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("supporting_information_unit_ids", []),
        ("derivation_rationale", None),
        ("missing_evidence", "Missing."),
    ],
)
def test_rejects_invalid_derivation_evidence(
    field: str,
    value: object,
) -> None:
    payload = derivation_candidate_payload()
    payload[field] = value

    with pytest.raises(
        InformationUnitCandidateDerivationError
    ):
        parse_information_unit_candidate(payload)


def test_assumption_candidate_is_valid() -> None:
    payload = candidate_payload()
    payload["epistemic_class"] = "assumption"
    payload["missing_evidence"] = (
        "The source does not define the operating context."
    )

    candidate = parse_information_unit_candidate(payload)
    assert candidate.epistemic_class == "assumption"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("missing_evidence", None),
        (
            "supporting_information_unit_ids",
            ["IU-000001"],
        ),
        ("derivation_rationale", "Derived."),
    ],
)
def test_rejects_invalid_assumption_evidence(
    field: str,
    value: object,
) -> None:
    payload = candidate_payload()
    payload["epistemic_class"] = "assumption"
    payload["missing_evidence"] = "Evidence is absent."
    payload[field] = value

    with pytest.raises(
        InformationUnitCandidateAssumptionError
    ):
        parse_information_unit_candidate(payload)


@pytest.mark.parametrize(
    ("field", "value", "error_type"),
    [
        (
            "supporting_information_unit_ids",
            ["IU-000001"],
            InformationUnitCandidateDerivationError,
        ),
        (
            "derivation_rationale",
            "Derived.",
            InformationUnitCandidateDerivationError,
        ),
        (
            "missing_evidence",
            "Missing.",
            InformationUnitCandidateAssumptionError,
        ),
    ],
)
def test_explicit_candidate_rejects_other_evidence(
    field: str,
    value: object,
    error_type: type[Exception],
) -> None:
    payload = candidate_payload()
    payload[field] = value

    with pytest.raises(error_type):
        parse_information_unit_candidate(payload)


@pytest.mark.parametrize(
    "supporting_ids",
    [
        ["IU-000001", "IU-000001"],
        ["IU-000002", "IU-000001"],
        ["IU-000000"],
    ],
)
def test_rejects_invalid_supporting_id_collection(
    supporting_ids: list[str],
) -> None:
    payload = derivation_candidate_payload()
    payload["supporting_information_unit_ids"] = (
        supporting_ids
    )

    with pytest.raises(
        InformationUnitCandidateDerivationError
    ):
        parse_information_unit_candidate(payload)


def test_uncertainties_preserve_agent_order() -> None:
    payload = candidate_payload()
    payload["uncertainties"] = [
        "First doubt.",
        "Second doubt.",
    ]
    candidate = parse_information_unit_candidate(payload)

    assert candidate.uncertainties == (
        "First doubt.",
        "Second doubt.",
    )


def test_rejects_duplicate_uncertainties() -> None:
    payload = candidate_payload()
    payload["uncertainties"] = [
        "Same doubt.",
        "Same doubt.",
    ]

    with pytest.raises(SemanticExtractionValidationError):
        parse_information_unit_candidate(payload)


@pytest.mark.parametrize(
    "uncertainties",
    [
        "not-a-list",
        [""],
        [" uncertainty"],
    ],
)
def test_rejects_invalid_uncertainties(
    uncertainties: object,
) -> None:
    payload = candidate_payload()
    payload["uncertainties"] = uncertainties

    with pytest.raises(SemanticExtractionValidationError):
        parse_information_unit_candidate(payload)


def test_candidate_fingerprint_excludes_run_local_analysis() -> None:
    first = parse_information_unit_candidate(
        candidate_payload()
    )
    second_payload = candidate_payload(
        candidate_id="IUC-000002"
    )
    second_payload["extraction_rationale"] = (
        "Different run-local explanation."
    )
    second_payload["uncertainties"] = [
        "Different run-local doubt."
    ]
    second = parse_information_unit_candidate(
        second_payload
    )

    assert (
        calculate_information_unit_candidate_fingerprint(
            first
        )
        == calculate_information_unit_candidate_fingerprint(
            second
        )
    )


def test_candidate_fingerprint_changes_with_professional_content() -> None:
    first = parse_information_unit_candidate(
        candidate_payload()
    )
    second = parse_information_unit_candidate(
        candidate_payload(
            interpreted_statement="Different statement."
        )
    )

    assert (
        calculate_information_unit_candidate_fingerprint(
            first
        )
        != calculate_information_unit_candidate_fingerprint(
            second
        )
    )


def test_context_validation_accepts_exact_projection_excerpt() -> None:
    result = parse_semantic_extraction_agent_result(
        result_payload()
    )

    assert (
        validate_semantic_extraction_agent_result_context(
            result,
            source_projection=projection_artifact(),
        )
        is None
    )


def test_context_validation_rejects_changed_excerpt() -> None:
    payload = candidate_payload(
        source_excerpt="alpha"
    )
    result = parse_semantic_extraction_agent_result(
        result_payload(candidates=[payload])
    )

    with pytest.raises(InformationUnitCandidateAnchorError):
        validate_semantic_extraction_agent_result_context(
            result,
            source_projection=projection_artifact(),
        )


def test_context_validation_rejects_unknown_segment() -> None:
    payload = candidate_payload(
        segment_id="SEG-000003"
    )
    result = parse_semantic_extraction_agent_result(
        result_payload(candidates=[payload])
    )

    with pytest.raises(InformationUnitCandidateAnchorError):
        validate_semantic_extraction_agent_result_context(
            result,
            source_projection=projection_artifact(),
        )


def test_context_validation_rejects_range_beyond_segment() -> None:
    payload = candidate_payload(
        end_offset=6,
        source_excerpt="AlphaB",
    )
    result = parse_semantic_extraction_agent_result(
        result_payload(candidates=[payload])
    )

    with pytest.raises(InformationUnitCandidateAnchorError):
        validate_semantic_extraction_agent_result_context(
            result,
            source_projection=projection_artifact(),
        )


@pytest.mark.parametrize(
    "projection",
    [
        projection_artifact(project_id="999999"),
        projection_artifact(source_id="SRC-000002"),
        projection_artifact(
            source_projection_id="SP-000002"
        ),
    ],
)
def test_context_validation_rejects_projection_identity(
    projection: SourceProjectionArtifact,
) -> None:
    result = parse_semantic_extraction_agent_result(
        result_payload()
    )

    with pytest.raises(SemanticExtractionReferenceError):
        validate_semantic_extraction_agent_result_context(
            result,
            source_projection=projection,
        )


def test_context_validation_rejects_unavailable_projection() -> None:
    result = parse_semantic_extraction_agent_result(
        result_payload()
    )

    with pytest.raises(SemanticExtractionReferenceError):
        validate_semantic_extraction_agent_result_context(
            result,
            source_projection=projection_artifact(
                projection_result="unavailable"
            ),
        )


def test_context_validation_requires_projection_artifact() -> None:
    result = parse_semantic_extraction_agent_result(
        result_payload()
    )

    with pytest.raises(SemanticExtractionReferenceError):
        validate_semantic_extraction_agent_result_context(
            result,
            source_projection={},  # type: ignore[arg-type]
        )


def test_context_validation_accepts_existing_same_source_support() -> None:
    result = parse_semantic_extraction_agent_result(
        result_payload(
            candidates=[derivation_candidate_payload()]
        )
    )

    assert (
        validate_semantic_extraction_agent_result_context(
            result,
            source_projection=projection_artifact(),
            supporting_information_units=(
                supporting_information_unit(),
            ),
        )
        is None
    )


def test_context_validation_rejects_missing_support() -> None:
    result = parse_semantic_extraction_agent_result(
        result_payload(
            candidates=[derivation_candidate_payload()]
        )
    )

    with pytest.raises(SemanticExtractionReferenceError):
        validate_semantic_extraction_agent_result_context(
            result,
            source_projection=projection_artifact(),
        )


@pytest.mark.parametrize(
    "supporting_unit",
    [
        supporting_information_unit(project_id="999999"),
        supporting_information_unit(source_id="SRC-000002"),
    ],
)
def test_context_validation_rejects_wrong_support_context(
    supporting_unit: InformationUnit,
) -> None:
    result = parse_semantic_extraction_agent_result(
        result_payload(
            candidates=[derivation_candidate_payload()]
        )
    )

    with pytest.raises(SemanticExtractionReferenceError):
        validate_semantic_extraction_agent_result_context(
            result,
            source_projection=projection_artifact(),
            supporting_information_units=(
                supporting_unit,
            ),
        )


def test_context_validation_rejects_duplicate_support_input() -> None:
    result = parse_semantic_extraction_agent_result(
        result_payload()
    )
    unit = supporting_information_unit()

    with pytest.raises(SemanticExtractionReferenceError):
        validate_semantic_extraction_agent_result_context(
            result,
            source_projection=projection_artifact(),
            supporting_information_units=(unit, unit),
        )


def test_context_validation_rejects_non_unit_support_input() -> None:
    result = parse_semantic_extraction_agent_result(
        result_payload()
    )

    with pytest.raises(SemanticExtractionReferenceError):
        validate_semantic_extraction_agent_result_context(
            result,
            source_projection=projection_artifact(),
            supporting_information_units=(
                "IU-000001",  # type: ignore[arg-type]
            ),
        )


def test_context_validation_rejects_string_as_support_collection() -> None:
    result = parse_semantic_extraction_agent_result(
        result_payload()
    )

    with pytest.raises(SemanticExtractionReferenceError):
        validate_semantic_extraction_agent_result_context(
            result,
            source_projection=projection_artifact(),
            supporting_information_units=(  # type: ignore[arg-type]
                "IU-000001"
            ),
        )


def test_zero_candidate_context_validation_is_valid() -> None:
    result = parse_semantic_extraction_agent_result(
        result_payload(
            candidates=[],
            no_candidate_rationale="No engineering claim.",
        )
    )

    assert (
        validate_semantic_extraction_agent_result_context(
            result,
            source_projection=projection_artifact(),
        )
        is None
    )


def test_directly_modified_result_is_revalidated() -> None:
    result = parse_semantic_extraction_agent_result(
        result_payload()
    )
    invalid = replace(
        result,
        persona_configuration_fingerprint="invalid",
    )

    with pytest.raises(SemanticExtractionValidationError):
        validate_semantic_extraction_agent_result(invalid)


def test_parsing_does_not_mutate_input_payload() -> None:
    payload = result_payload()
    before = deepcopy(payload)

    parse_semantic_extraction_agent_result(payload)

    assert payload == before