"""Tests for the strict Semantic Consensus Result manifest."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
import json

import pytest

from modules.information_units.types import (
    InformationUnitSourceAnchor,
)
from modules.semantic_consensus.analyzer import (
    analyze_semantic_consensus,
)
from modules.semantic_consensus.errors import (
    DuplicateAgentCandidateReferenceError,
    SemanticConsensusIntegrityError,
    SemanticConsensusValidationError,
)
from modules.semantic_consensus.manifest import (
    SEMANTIC_CONSENSUS_SCHEMA_VERSION,
    parse_semantic_consensus_result,
    semantic_consensus_result_from_json,
    semantic_consensus_result_to_dict,
    semantic_consensus_result_to_json,
    validate_semantic_consensus_result,
)
from modules.semantic_consensus.types import (
    SemanticConsensusResult,
)
from modules.semantic_extraction.manifest import (
    create_information_unit_candidate,
    create_semantic_extraction_agent_result,
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


def projection() -> SourceProjectionArtifact:
    return SourceProjectionArtifact(
        manifest=SourceProjectionManifest(
            schema_version="1.0.0",
            project_id=PROJECT_ID,
            source_id=SOURCE_ID,
            source_projection_id=SOURCE_PROJECTION_ID,
            source_role="engineering_source",
            source_sha256="a" * 64,
            adapter_id="text",
            adapter_version="1.0.0",
            adapter_configuration=(),
            projection_fingerprint="b" * 64,
            projection_result="available",
            content_sha256="c" * 64,
            content_length=9,
            segments=(
                ProjectionSegment(
                    segment_id="SEG-000001",
                    segment_type="text",
                    start_offset=0,
                    end_offset=5,
                    text_sha256="d" * 64,
                    source_locators=(),
                ),
                ProjectionSegment(
                    segment_id="SEG-000002",
                    segment_type="text",
                    start_offset=5,
                    end_offset=9,
                    text_sha256="e" * 64,
                    source_locators=(),
                ),
            ),
            issues=(),
            created_at=TIMESTAMP,
        ),
        content="AlphaBeta",
    )


def extraction_result(
    persona_id: str,
    *,
    two_candidates: bool = False,
) -> object:
    alpha = create_information_unit_candidate(
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
    candidates = [alpha]

    if two_candidates:
        candidates.append(
            create_information_unit_candidate(
                candidate_id="IUC-000002",
                source_anchors=(
                    InformationUnitSourceAnchor(
                        segment_id="SEG-000002",
                        start_offset=0,
                        end_offset=4,
                    ),
                ),
                source_excerpt="Beta",
                interpreted_statement="Beta is present.",
                information_type="unclassified",
                statement_modality="descriptive",
                epistemic_class="explicit",
                extraction_rationale=(
                    "Direct source statement."
                ),
            )
        )

    return create_semantic_extraction_agent_result(
        project_id=PROJECT_ID,
        source_id=SOURCE_ID,
        source_projection_id=SOURCE_PROJECTION_ID,
        team_id="semantic-team",
        agent_id=f"agent-{persona_id}",
        persona_id=persona_id,
        persona_run_index=1,
        persona_configuration_fingerprint=sha256(
            persona_id.encode("utf-8")
        ).hexdigest(),
        llm_provider="test-provider",
        llm_model="test-model",
        prompt_schema_version="1.0.0",
        candidates=tuple(candidates),
        no_candidate_rationale=None,
        timestamp=TIMESTAMP,
    )


def valid_result(
    *,
    two_outcomes: bool = False,
) -> SemanticConsensusResult:
    return analyze_semantic_consensus(
        agent_results=(
            extraction_result(
                "persona-a",
                two_candidates=two_outcomes,
            ),
            extraction_result(
                "persona-b",
                two_candidates=two_outcomes,
            ),
        ),
        required_personas=("persona-a", "persona-b"),
        expected_runs_per_persona={
            "persona-a": 1,
            "persona-b": 1,
        },
        source_projection=projection(),
        consensus_report_id="CONSENSUS-TEST-001",
        timestamp="2026-07-24T11:00:00Z",
    )


def valid_payload(
    *,
    two_outcomes: bool = False,
) -> dict[str, object]:
    return semantic_consensus_result_to_dict(
        valid_result(two_outcomes=two_outcomes)
    )


def test_schema_version_is_explicit() -> None:
    assert SEMANTIC_CONSENSUS_SCHEMA_VERSION == "1.0.0"


def test_valid_result_round_trip_is_deterministic() -> None:
    result = valid_result()
    first = semantic_consensus_result_to_json(result)
    reloaded = semantic_consensus_result_from_json(first)
    second = semantic_consensus_result_to_json(reloaded)

    assert reloaded == result
    assert first == second
    assert first.endswith("\n")
    assert json.loads(first) == (
        semantic_consensus_result_to_dict(result)
    )


def test_validate_accepts_valid_result() -> None:
    result = valid_result()

    assert validate_semantic_consensus_result(result) is None


def test_parse_returns_immutable_result() -> None:
    parsed = parse_semantic_consensus_result(
        valid_payload()
    )

    assert isinstance(parsed, SemanticConsensusResult)
    assert parsed.outcomes[0].confirmation_required is True
    assert parsed.outcomes[0].publication_eligible is True


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
        (
            "expected_consensus_report_id",
            "OTHER-REPORT",
        ),
    ],
)
def test_expected_context_mismatch_is_rejected(
    expected_name: str,
    expected_value: str,
) -> None:
    with pytest.raises(SemanticConsensusValidationError):
        parse_semantic_consensus_result(
            valid_payload(),
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
        ("consensus_report_id", " report"),
        ("llm_provider", ""),
        ("llm_model", "model "),
        ("prompt_schema_version", "1.0"),
        ("created_at", "2026-07-24T11:00:00+00:00"),
        ("created_at", "2026-02-30T11:00:00Z"),
    ],
)
def test_rejects_invalid_result_scalar(
    field: str,
    value: object,
) -> None:
    payload = valid_payload()
    payload[field] = value

    with pytest.raises(SemanticConsensusValidationError):
        parse_semantic_consensus_result(payload)


def test_rejects_missing_result_field() -> None:
    payload = valid_payload()
    del payload["issues"]

    with pytest.raises(SemanticConsensusValidationError):
        parse_semantic_consensus_result(payload)


@pytest.mark.parametrize(
    "forbidden_field",
    [
        "confirmation_state",
        "human_decision",
        "reviewer_id",
        "confirmed_at",
        "information_unit_id",
    ],
)
def test_rejects_human_decision_or_final_id_field(
    forbidden_field: str,
) -> None:
    payload = valid_payload()
    payload[forbidden_field] = "not-allowed"

    with pytest.raises(SemanticConsensusValidationError):
        parse_semantic_consensus_result(payload)


def test_required_personas_must_be_sorted() -> None:
    payload = valid_payload()
    payload["required_personas"] = [
        "persona-b",
        "persona-a",
    ]

    with pytest.raises(SemanticConsensusValidationError):
        parse_semantic_consensus_result(payload)


def test_required_personas_must_be_distinct() -> None:
    payload = valid_payload()
    payload["required_personas"] = [
        "persona-a",
        "persona-a",
    ]

    with pytest.raises(SemanticConsensusValidationError):
        parse_semantic_consensus_result(payload)


def test_run_expectations_must_match_personas() -> None:
    payload = valid_payload()
    payload["persona_run_expectations"] = [
        {
            "persona_id": "persona-a",
            "expected_run_count": 1,
        }
    ]

    with pytest.raises(SemanticConsensusValidationError):
        parse_semantic_consensus_result(payload)


def test_confirmation_is_always_required() -> None:
    payload = valid_payload()
    payload["outcomes"][0]["confirmation_required"] = False

    with pytest.raises(SemanticConsensusValidationError):
        parse_semantic_consensus_result(payload)


def test_quick_confirmation_requires_no_detailed_review() -> None:
    payload = valid_payload()
    payload["outcomes"][0]["review_required"] = True

    with pytest.raises(SemanticConsensusValidationError):
        parse_semantic_consensus_result(payload)


def test_detailed_review_mode_requires_review_flag() -> None:
    payload = valid_payload()
    payload["outcomes"][0][
        "recommended_review_mode"
    ] = "detailed_review"

    with pytest.raises(SemanticConsensusValidationError):
        parse_semantic_consensus_result(payload)


@pytest.mark.parametrize(
    ("confidence", "variance"),
    [
        ("high", "medium"),
        ("medium", "low"),
        ("low", "medium"),
    ],
)
def test_confidence_and_variance_must_correspond(
    confidence: str,
    variance: str,
) -> None:
    payload = valid_payload()
    outcome = payload["outcomes"][0]
    outcome["confidence"] = confidence
    outcome["variance_level"] = variance

    with pytest.raises(SemanticConsensusValidationError):
        parse_semantic_consensus_result(payload)


def test_high_confidence_requires_unanimous_consensus() -> None:
    payload = valid_payload()
    payload["outcomes"][0]["consensus_level"] = "majority"

    with pytest.raises(SemanticConsensusValidationError):
        parse_semantic_consensus_result(payload)


def test_publication_eligibility_requires_proposed_unit() -> None:
    payload = valid_payload()
    payload["outcomes"][0][
        "proposed_information_unit"
    ] = None

    with pytest.raises(SemanticConsensusValidationError):
        parse_semantic_consensus_result(payload)


def test_publication_eligibility_requires_high_confidence() -> None:
    payload = valid_payload()
    outcome = payload["outcomes"][0]
    outcome["confidence"] = "medium"
    outcome["variance_level"] = "medium"

    with pytest.raises(SemanticConsensusValidationError):
        parse_semantic_consensus_result(payload)


def test_publication_eligibility_requires_quick_confirmation() -> None:
    payload = valid_payload()
    outcome = payload["outcomes"][0]
    outcome["review_required"] = True
    outcome["recommended_review_mode"] = "detailed_review"

    with pytest.raises(SemanticConsensusValidationError):
        parse_semantic_consensus_result(payload)


def test_proposed_unit_evidence_must_match_outcome() -> None:
    payload = valid_payload()
    payload["outcomes"][0][
        "proposed_information_unit"
    ]["source_excerpt"] = "Different"

    with pytest.raises(SemanticConsensusIntegrityError):
        parse_semantic_consensus_result(payload)


def test_assumption_cannot_use_quick_confirmation() -> None:
    payload = valid_payload()
    draft = payload["outcomes"][0][
        "proposed_information_unit"
    ]
    draft["epistemic_class"] = "assumption"
    draft["missing_evidence"] = "Evidence is absent."

    with pytest.raises(SemanticConsensusValidationError):
        parse_semantic_consensus_result(payload)


def test_outcome_persona_groups_must_be_disjoint() -> None:
    payload = valid_payload()
    payload["outcomes"][0]["dissenting_personas"] = [
        "persona-a"
    ]

    with pytest.raises(SemanticConsensusIntegrityError):
        parse_semantic_consensus_result(payload)


def test_outcome_persona_groups_must_cover_team() -> None:
    payload = valid_payload()
    payload["outcomes"][0]["supporting_personas"] = [
        "persona-a"
    ]

    with pytest.raises(SemanticConsensusIntegrityError):
        parse_semantic_consensus_result(payload)


def test_field_persona_groups_must_partition_team() -> None:
    payload = valid_payload()
    assessment = payload["outcomes"][0][
        "field_assessments"
    ][0]
    assessment["supporting_personas"] = ["persona-a"]

    with pytest.raises(SemanticConsensusIntegrityError):
        parse_semantic_consensus_result(payload)


def test_total_personas_must_equal_required_team_size() -> None:
    payload = valid_payload()
    payload["outcomes"][0]["total_personas"] = 3

    with pytest.raises(SemanticConsensusValidationError):
        parse_semantic_consensus_result(payload)


def test_field_assessment_order_is_fixed() -> None:
    payload = valid_payload()
    assessments = payload["outcomes"][0][
        "field_assessments"
    ]
    assessments[0], assessments[1] = (
        assessments[1],
        assessments[0],
    )

    with pytest.raises(SemanticConsensusValidationError):
        parse_semantic_consensus_result(payload)


def test_selected_field_value_must_exist_in_distribution() -> None:
    payload = valid_payload()
    payload["outcomes"][0]["field_assessments"][1][
        "selected_value"
    ] = "absent-value"

    with pytest.raises(SemanticConsensusIntegrityError):
        parse_semantic_consensus_result(payload)


def test_distribution_values_must_be_unique() -> None:
    payload = valid_payload()
    assessment = payload["outcomes"][0][
        "field_assessments"
    ][1]
    assessment["value_distribution"].append(
        deepcopy(assessment["value_distribution"][0])
    )

    with pytest.raises(SemanticConsensusIntegrityError):
        parse_semantic_consensus_result(payload)


def test_distribution_must_be_sorted() -> None:
    payload = valid_payload()
    assessment = payload["outcomes"][0][
        "field_assessments"
    ][1]
    second = deepcopy(assessment["value_distribution"][0])
    second["canonical_value"] = "aaa"
    second["display_value"] = "aaa"
    second["supporting_personas"] = []
    second["candidate_references"] = []
    assessment["value_distribution"].append(second)

    with pytest.raises(SemanticConsensusValidationError):
        parse_semantic_consensus_result(payload)


def test_persona_stability_must_cover_required_personas() -> None:
    payload = valid_payload()
    payload["outcomes"][0]["persona_stability"].pop()

    with pytest.raises(SemanticConsensusValidationError):
        parse_semantic_consensus_result(payload)


def test_omitted_runs_must_be_observed() -> None:
    payload = valid_payload()
    assessment = payload["outcomes"][0][
        "persona_stability"
    ][0]
    assessment["omitted_run_indices"] = [1]
    assessment["observed_run_indices"] = []

    with pytest.raises(SemanticConsensusValidationError):
        parse_semantic_consensus_result(payload)


def test_candidate_references_must_be_sorted() -> None:
    payload = valid_payload()
    payload["outcomes"][0][
        "candidate_references"
    ].reverse()

    with pytest.raises(SemanticConsensusValidationError):
        parse_semantic_consensus_result(payload)


def test_candidate_references_must_be_unique() -> None:
    payload = valid_payload()
    references = payload["outcomes"][0][
        "candidate_references"
    ]
    references.append(deepcopy(references[0]))

    with pytest.raises(
        DuplicateAgentCandidateReferenceError
    ):
        parse_semantic_consensus_result(payload)


def test_candidate_reference_must_use_required_persona() -> None:
    payload = valid_payload()
    payload["outcomes"][0]["candidate_references"][0][
        "persona_id"
    ] = "persona-c"

    with pytest.raises(SemanticConsensusValidationError):
        parse_semantic_consensus_result(payload)


def test_candidate_reference_run_must_not_exceed_expectation() -> None:
    payload = valid_payload()
    payload["outcomes"][0]["candidate_references"][0][
        "persona_run_index"
    ] = 2

    with pytest.raises(SemanticConsensusValidationError):
        parse_semantic_consensus_result(payload)


def test_consensus_candidate_ids_are_gapless() -> None:
    payload = valid_payload()
    payload["outcomes"][0][
        "consensus_candidate_id"
    ] = "SCC-000002"

    with pytest.raises(SemanticConsensusValidationError):
        parse_semantic_consensus_result(payload)


def test_outcomes_must_follow_source_order() -> None:
    payload = valid_payload(two_outcomes=True)
    payload["outcomes"].reverse()
    payload["outcomes"][0][
        "consensus_candidate_id"
    ] = "SCC-000001"
    payload["outcomes"][1][
        "consensus_candidate_id"
    ] = "SCC-000002"

    with pytest.raises(SemanticConsensusValidationError):
        parse_semantic_consensus_result(payload)


def test_agent_candidate_cannot_belong_to_two_outcomes() -> None:
    payload = valid_payload(two_outcomes=True)
    payload["outcomes"][1]["candidate_references"] = (
        deepcopy(
            payload["outcomes"][0][
                "candidate_references"
            ]
        )
    )

    with pytest.raises(
        DuplicateAgentCandidateReferenceError
    ):
        parse_semantic_consensus_result(payload)


def test_issues_must_be_sorted() -> None:
    payload = valid_payload()
    payload["issues"] = [
        {
            "code": "second_issue",
            "message": "Second.",
            "issue_level": "warning",
            "persona_id": "persona-b",
            "agent_id": None,
            "persona_run_index": None,
        },
        {
            "code": "first_issue",
            "message": "First.",
            "issue_level": "warning",
            "persona_id": "persona-a",
            "agent_id": None,
            "persona_run_index": None,
        },
    ]

    with pytest.raises(SemanticConsensusValidationError):
        parse_semantic_consensus_result(payload)


def test_duplicate_issues_are_rejected() -> None:
    payload = valid_payload()
    issue = {
        "code": "same_issue",
        "message": "Same.",
        "issue_level": "warning",
        "persona_id": None,
        "agent_id": None,
        "persona_run_index": None,
    }
    payload["issues"] = [deepcopy(issue), deepcopy(issue)]

    with pytest.raises(SemanticConsensusIntegrityError):
        parse_semantic_consensus_result(payload)


def test_issue_agent_requires_persona() -> None:
    payload = valid_payload()
    payload["issues"] = [
        {
            "code": "test_issue",
            "message": "Test.",
            "issue_level": "warning",
            "persona_id": None,
            "agent_id": "agent-a",
            "persona_run_index": None,
        }
    ]

    with pytest.raises(SemanticConsensusValidationError):
        parse_semantic_consensus_result(payload)


def test_json_input_must_be_string() -> None:
    with pytest.raises(SemanticConsensusValidationError):
        semantic_consensus_result_from_json(  # type: ignore[arg-type]
            {}
        )


def test_invalid_json_is_rejected() -> None:
    with pytest.raises(SemanticConsensusValidationError):
        semantic_consensus_result_from_json("{invalid")


def test_duplicate_json_field_is_rejected() -> None:
    with pytest.raises(SemanticConsensusValidationError):
        semantic_consensus_result_from_json(
            '{"schema_version":"1.0.0",'
            '"schema_version":"1.0.0"}'
        )


def test_to_dict_requires_result_instance() -> None:
    with pytest.raises(SemanticConsensusValidationError):
        semantic_consensus_result_to_dict(  # type: ignore[arg-type]
            {}
        )


def test_modified_dataclass_is_revalidated() -> None:
    result = valid_result()
    invalid = replace(
        result,
        consensus_report_id=" invalid",
    )

    with pytest.raises(SemanticConsensusValidationError):
        validate_semantic_consensus_result(invalid)


def test_parsing_does_not_mutate_payload() -> None:
    payload = valid_payload()
    before = deepcopy(payload)

    parse_semantic_consensus_result(payload)

    assert payload == before