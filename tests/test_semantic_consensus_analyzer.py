"""Tests for deterministic semantic consensus analysis."""

from __future__ import annotations

from hashlib import sha256
from itertools import permutations
import json

import pytest

from modules.information_units.types import (
    InformationUnitSourceAnchor,
)
from modules.semantic_consensus.analyzer import (
    analyze_semantic_consensus,
    candidate_evidence_key,
    candidate_professional_signature,
)
from modules.semantic_consensus.errors import (
    DuplicateSemanticAgentResultError,
    SemanticConsensusComparisonError,
    SemanticConsensusConfigurationError,
    SemanticConsensusReferenceError,
)
from modules.semantic_consensus.manifest import (
    semantic_consensus_result_to_json,
)
from modules.semantic_consensus.normalization import (
    CONSENSUS_TEXT_NORMALIZATION_ID,
    CONSENSUS_TEXT_NORMALIZATION_VERSION,
    canonical_consensus_json,
    normalize_consensus_text,
)
from modules.semantic_extraction.manifest import (
    create_information_unit_candidate,
    create_semantic_extraction_agent_result,
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
CONSENSUS_TIMESTAMP = "2026-07-24T11:00:00Z"


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


def candidate(
    *,
    candidate_id: str = "IUC-000001",
    statement: str = "Alpha is present.",
    segment_id: str = "SEG-000001",
    end_offset: int = 5,
    excerpt: str = "Alpha",
    information_type: str = "unclassified",
    epistemic_class: str = "explicit",
    supporting_ids: tuple[str, ...] = (),
    derivation_rationale: str | None = None,
    missing_evidence: str | None = None,
    uncertainties: tuple[str, ...] = (),
) -> InformationUnitCandidate:
    return create_information_unit_candidate(
        candidate_id=candidate_id,
        source_anchors=(
            InformationUnitSourceAnchor(
                segment_id=segment_id,
                start_offset=0,
                end_offset=end_offset,
            ),
        ),
        source_excerpt=excerpt,
        interpreted_statement=statement,
        information_type=information_type,
        statement_modality="descriptive",
        epistemic_class=epistemic_class,
        supporting_information_unit_ids=supporting_ids,
        derivation_rationale=derivation_rationale,
        missing_evidence=missing_evidence,
        extraction_rationale="Deterministic test candidate.",
        uncertainties=uncertainties,
    )


def agent_result(
    persona_id: str,
    *,
    run_index: int = 1,
    candidates: tuple[InformationUnitCandidate, ...] | None = None,
    agent_id: str | None = None,
    fingerprint: str | None = None,
    project_id: str = PROJECT_ID,
    source_id: str = SOURCE_ID,
    source_projection_id: str = SOURCE_PROJECTION_ID,
    team_id: str = "semantic-team",
    llm_provider: str = "test-provider",
    llm_model: str = "test-model",
    prompt_schema_version: str = "1.0.0",
) -> SemanticExtractionAgentResult:
    selected_candidates = (
        (candidate(),)
        if candidates is None
        else candidates
    )
    return create_semantic_extraction_agent_result(
        project_id=project_id,
        source_id=source_id,
        source_projection_id=source_projection_id,
        team_id=team_id,
        agent_id=agent_id or f"agent-{persona_id}",
        persona_id=persona_id,
        persona_run_index=run_index,
        persona_configuration_fingerprint=(
            fingerprint
            or sha256(persona_id.encode("utf-8")).hexdigest()
        ),
        llm_provider=llm_provider,
        llm_model=llm_model,
        prompt_schema_version=prompt_schema_version,
        candidates=selected_candidates,
        no_candidate_rationale=(
            None
            if selected_candidates
            else "No independently reviewable claim."
        ),
        timestamp=TIMESTAMP,
    )


def analyze(
    results: tuple[SemanticExtractionAgentResult, ...],
    *,
    personas: tuple[str, ...] = (
        "persona-a",
        "persona-b",
    ),
    expectations: dict[str, int] | None = None,
) -> object:
    return analyze_semantic_consensus(
        agent_results=results,
        required_personas=personas,
        expected_runs_per_persona=(
            {persona_id: 1 for persona_id in personas}
            if expectations is None
            else expectations
        ),
        source_projection=projection(),
        consensus_report_id="CONSENSUS-TEST-001",
        timestamp=CONSENSUS_TIMESTAMP,
    )


def test_normalization_contract_is_explicit() -> None:
    assert (
        CONSENSUS_TEXT_NORMALIZATION_ID
        == "unicode_nfkc_whitespace_casefold"
    )
    assert CONSENSUS_TEXT_NORMALIZATION_VERSION == "1.0.0"


def test_lexical_normalization_is_deterministic() -> None:
    assert normalize_consensus_text(
        "  ＡLPHA\t is\nPRESENT. "
    ) == "alpha is present."


@pytest.mark.parametrize(
    "value",
    [None, 1, "", "   "],
)
def test_lexical_normalization_rejects_invalid_input(
    value: object,
) -> None:
    with pytest.raises(SemanticConsensusComparisonError):
        normalize_consensus_text(value)


def test_canonical_json_is_order_independent() -> None:
    assert canonical_consensus_json(
        {"b": 2, "a": 1}
    ) == '{"a":1,"b":2}'


def test_evidence_key_uses_exact_anchors_and_excerpt() -> None:
    value = candidate()

    assert candidate_evidence_key(value) == (
        ((1, 0, 5),),
        "Alpha",
    )


def test_professional_signature_uses_lexical_statement() -> None:
    first = candidate(statement="Alpha is present.")
    second = candidate(statement="ALPHA  IS PRESENT.")

    assert (
        candidate_professional_signature(first)
        == candidate_professional_signature(second)
    )


def test_unanimous_consensus_requires_quick_human_confirmation() -> None:
    result = analyze(
        (
            agent_result("persona-a"),
            agent_result("persona-b"),
        )
    )
    outcome = result.outcomes[0]

    assert outcome.consensus_level == "unanimous"
    assert outcome.variance_level == "low"
    assert outcome.confidence == "high"
    assert outcome.confirmation_required is True
    assert outcome.review_required is False
    assert (
        outcome.recommended_review_mode
        == "quick_confirmation"
    )
    assert outcome.publication_eligible is True
    assert outcome.proposed_information_unit is not None
    payload = json.loads(
        semantic_consensus_result_to_json(result)
    )
    assert "information_unit_id" not in payload
    assert (
        "information_unit_id"
        not in payload["outcomes"][0]
    )
    assert (
        "information_unit_id"
        not in payload["outcomes"][0][
            "proposed_information_unit"
        ]
    )


def test_case_and_whitespace_variation_remains_unanimous() -> None:
    first = agent_result(
        "persona-a",
        candidates=(
            candidate(statement="Alpha is present."),
        ),
    )
    second = agent_result(
        "persona-b",
        candidates=(
            candidate(statement="ALPHA  IS PRESENT."),
        ),
    )
    outcome = analyze((second, first)).outcomes[0]

    assert outcome.confidence == "high"
    assert outcome.proposed_information_unit is not None
    assert (
        outcome.proposed_information_unit.interpreted_statement
        == "Alpha is present."
    )


def test_strict_majority_is_medium_and_requires_review() -> None:
    result = analyze(
        (
            agent_result("persona-a"),
            agent_result("persona-b"),
            agent_result(
                "persona-c",
                candidates=(
                    candidate(
                        statement="Alpha has another meaning."
                    ),
                ),
            ),
        ),
        personas=(
            "persona-a",
            "persona-b",
            "persona-c",
        ),
    )
    outcome = result.outcomes[0]

    assert outcome.consensus_level == "majority"
    assert outcome.confidence == "medium"
    assert outcome.review_required is True
    assert outcome.publication_eligible is False
    assert (
        outcome.recommended_review_mode
        == "detailed_review"
    )
    assert outcome.supporting_personas == (
        "persona-a",
        "persona-b",
    )
    assert outcome.dissenting_personas == (
        "persona-c",
    )


def test_two_persona_disagreement_is_incomparable() -> None:
    outcome = analyze(
        (
            agent_result("persona-a"),
            agent_result(
                "persona-b",
                candidates=(
                    candidate(statement="Different statement."),
                ),
            ),
        )
    ).outcomes[0]

    assert outcome.consensus_level == "incomparable"
    assert outcome.confidence == "low"
    assert outcome.proposed_information_unit is None
    assert outcome.review_required is True
    assert outcome.publication_eligible is False


def test_single_support_among_three_personas_is_low() -> None:
    outcome = analyze(
        (
            agent_result("persona-a"),
            agent_result("persona-b", candidates=()),
            agent_result("persona-c", candidates=()),
        ),
        personas=(
            "persona-a",
            "persona-b",
            "persona-c",
        ),
    ).outcomes[0]

    assert outcome.consensus_level == "single"
    assert outcome.confidence == "low"
    assert outcome.supporting_personas == ("persona-a",)
    assert outcome.omitting_personas == (
        "persona-b",
        "persona-c",
    )


def test_repeated_runs_do_not_create_additional_votes() -> None:
    results = tuple(
        agent_result(persona_id, run_index=run_index)
        for persona_id in ("persona-a", "persona-b")
        for run_index in (1, 2)
    )
    outcome = analyze(
        results,
        expectations={
            "persona-a": 2,
            "persona-b": 2,
        },
    ).outcomes[0]

    assert outcome.total_personas == 2
    assert outcome.supporting_personas == (
        "persona-a",
        "persona-b",
    )
    assert len(outcome.candidate_references) == 4
    assert outcome.confidence == "high"
    assert tuple(
        assessment.stability_level
        for assessment in outcome.persona_stability
    ) == ("stable", "stable")


def test_unique_modal_run_is_one_unstable_vote() -> None:
    results = (
        agent_result("persona-a", run_index=1),
        agent_result("persona-a", run_index=2),
        agent_result(
            "persona-a",
            run_index=3,
            candidates=(
                candidate(statement="Different statement."),
            ),
        ),
        agent_result("persona-b", run_index=1),
        agent_result("persona-b", run_index=2),
        agent_result("persona-b", run_index=3),
    )
    outcome = analyze(
        results,
        expectations={
            "persona-a": 3,
            "persona-b": 3,
        },
    ).outcomes[0]

    assert outcome.consensus_level == "unanimous"
    assert outcome.confidence == "medium"
    assert outcome.review_required is True
    assert outcome.publication_eligible is False
    assert (
        outcome.persona_stability[0].stability_level
        == "unstable"
    )
    assert any(
        issue.code == "unstable_persona_result"
        for issue in analyze(
            results,
            expectations={
                "persona-a": 3,
                "persona-b": 3,
            },
        ).issues
    )


def test_tied_repeated_runs_are_indeterminate() -> None:
    outcome = analyze(
        (
            agent_result("persona-a", run_index=1),
            agent_result(
                "persona-a",
                run_index=2,
                candidates=(
                    candidate(statement="Different statement."),
                ),
            ),
            agent_result("persona-b", run_index=1),
            agent_result("persona-b", run_index=2),
        ),
        expectations={
            "persona-a": 2,
            "persona-b": 2,
        },
    ).outcomes[0]

    assert outcome.consensus_level == "incomparable"
    assert outcome.confidence == "low"
    assert (
        outcome.persona_stability[0].stability_level
        == "indeterminate"
    )


def test_missing_run_makes_consensus_incomplete() -> None:
    result = analyze(
        (
            agent_result("persona-a", run_index=1),
            agent_result("persona-b", run_index=1),
            agent_result("persona-b", run_index=2),
        ),
        expectations={
            "persona-a": 2,
            "persona-b": 2,
        },
    )
    outcome = result.outcomes[0]

    assert outcome.consensus_level == "incomplete"
    assert outcome.confidence == "low"
    assert any(
        issue.code == "missing_persona_run"
        for issue in result.issues
    )


def test_missing_persona_result_makes_consensus_incomplete() -> None:
    result = analyze(
        (agent_result("persona-a"),)
    )

    assert result.outcomes[0].consensus_level == "incomplete"
    assert result.outcomes[0].confidence == "low"


def test_multiple_candidates_in_one_evidence_bucket_are_incomparable() -> None:
    first = candidate(
        candidate_id="IUC-000001",
        statement="First statement.",
    )
    second = candidate(
        candidate_id="IUC-000002",
        statement="Second statement.",
    )
    result = analyze(
        (
            agent_result(
                "persona-a",
                candidates=(first, second),
            ),
            agent_result("persona-b"),
        )
    )

    assert result.outcomes[0].consensus_level == "incomparable"
    assert result.outcomes[0].confidence == "low"
    assert any(
        issue.code
        == "ambiguous_persona_evidence_bucket"
        for issue in result.issues
    )


def test_explicit_uncertainty_caps_confidence() -> None:
    uncertain = candidate(
        uncertainties=("Interpretation may be incomplete.",)
    )
    outcome = analyze(
        (
            agent_result(
                "persona-a",
                candidates=(uncertain,),
            ),
            agent_result("persona-b"),
        )
    ).outcomes[0]

    assert outcome.consensus_level == "unanimous"
    assert outcome.confidence == "medium"
    assert outcome.review_required is True
    assert outcome.publication_eligible is False


def test_assumption_always_requires_detailed_review() -> None:
    assumed = candidate(
        epistemic_class="assumption",
        missing_evidence=(
            "The source does not state the operating context."
        ),
    )
    outcome = analyze(
        (
            agent_result(
                "persona-a",
                candidates=(assumed,),
            ),
            agent_result(
                "persona-b",
                candidates=(assumed,),
            ),
        )
    ).outcomes[0]

    assert outcome.confidence == "high"
    assert outcome.review_required is True
    assert outcome.publication_eligible is False
    assert (
        outcome.recommended_review_mode
        == "detailed_review"
    )


def test_all_personas_may_report_no_candidates() -> None:
    result = analyze(
        (
            agent_result("persona-a", candidates=()),
            agent_result("persona-b", candidates=()),
        )
    )

    assert result.outcomes == ()
    assert any(
        issue.code == "no_consensus_candidates"
        for issue in result.issues
    )


def test_outcomes_are_ordered_by_source_evidence() -> None:
    alpha = candidate(
        candidate_id="IUC-000001",
    )
    beta = candidate(
        candidate_id="IUC-000002",
        statement="Beta is present.",
        segment_id="SEG-000002",
        end_offset=4,
        excerpt="Beta",
    )
    result = analyze(
        (
            agent_result(
                "persona-b",
                candidates=(alpha, beta),
            ),
            agent_result(
                "persona-a",
                candidates=(alpha, beta),
            ),
        )
    )

    assert tuple(
        outcome.consensus_candidate_id
        for outcome in result.outcomes
    ) == ("SCC-000001", "SCC-000002")
    assert tuple(
        outcome.source_excerpt
        for outcome in result.outcomes
    ) == ("Alpha", "Beta")


def test_result_is_independent_of_input_order() -> None:
    source_results = (
        agent_result("persona-a"),
        agent_result("persona-b"),
        agent_result("persona-c"),
    )
    serialized = {
        semantic_consensus_result_to_json(
            analyze(
                tuple(order),
                personas=(
                    "persona-a",
                    "persona-b",
                    "persona-c",
                ),
            )
        )
        for order in permutations(source_results)
    }

    assert len(serialized) == 1


def test_duplicate_persona_run_is_rejected() -> None:
    duplicate = agent_result("persona-a")

    with pytest.raises(DuplicateSemanticAgentResultError):
        analyze_semantic_consensus(
            agent_results=(duplicate, duplicate),
            required_personas=("persona-a", "persona-b"),
            expected_runs_per_persona={
                "persona-a": 1,
                "persona-b": 1,
            },
            source_projection=projection(),
            consensus_report_id="CONSENSUS-TEST-001",
            timestamp=CONSENSUS_TIMESTAMP,
        )


@pytest.mark.parametrize(
    "personas",
    [
        ("persona-a",),
        ("persona-a", "persona-a"),
        (" persona-a", "persona-b"),
    ],
)
def test_invalid_required_personas_are_rejected(
    personas: tuple[str, ...],
) -> None:
    with pytest.raises(SemanticConsensusConfigurationError):
        analyze_semantic_consensus(
            agent_results=(agent_result("persona-a"),),
            required_personas=personas,
            expected_runs_per_persona={
                persona_id: 1
                for persona_id in set(personas)
            },
            source_projection=projection(),
            consensus_report_id="CONSENSUS-TEST-001",
            timestamp=CONSENSUS_TIMESTAMP,
        )


@pytest.mark.parametrize(
    "expectations",
    [
        {"persona-a": 1},
        {"persona-a": 1, "persona-b": 0},
        {"persona-a": 1, "persona-b": True},
    ],
)
def test_invalid_run_expectations_are_rejected(
    expectations: dict[str, object],
) -> None:
    with pytest.raises(SemanticConsensusConfigurationError):
        analyze_semantic_consensus(
            agent_results=(
                agent_result("persona-a"),
                agent_result("persona-b"),
            ),
            required_personas=("persona-a", "persona-b"),
            expected_runs_per_persona=expectations,  # type: ignore[arg-type]
            source_projection=projection(),
            consensus_report_id="CONSENSUS-TEST-001",
            timestamp=CONSENSUS_TIMESTAMP,
        )


def test_unconfigured_persona_is_rejected() -> None:
    with pytest.raises(SemanticConsensusConfigurationError):
        analyze(
            (
                agent_result("persona-a"),
                agent_result("persona-c"),
            )
        )


def test_run_index_above_expectation_is_rejected() -> None:
    with pytest.raises(SemanticConsensusConfigurationError):
        analyze(
            (
                agent_result("persona-a", run_index=2),
                agent_result("persona-b"),
            )
        )


def test_agent_id_must_remain_stable_across_runs() -> None:
    with pytest.raises(SemanticConsensusConfigurationError):
        analyze(
            (
                agent_result(
                    "persona-a",
                    run_index=1,
                    agent_id="agent-one",
                ),
                agent_result(
                    "persona-a",
                    run_index=2,
                    agent_id="agent-two",
                ),
                agent_result("persona-b", run_index=1),
                agent_result("persona-b", run_index=2),
            ),
            expectations={
                "persona-a": 2,
                "persona-b": 2,
            },
        )


def test_fingerprint_must_remain_stable_across_runs() -> None:
    with pytest.raises(SemanticConsensusConfigurationError):
        analyze(
            (
                agent_result(
                    "persona-a",
                    run_index=1,
                    fingerprint="1" * 64,
                ),
                agent_result(
                    "persona-a",
                    run_index=2,
                    fingerprint="2" * 64,
                ),
                agent_result("persona-b", run_index=1),
                agent_result("persona-b", run_index=2),
            ),
            expectations={
                "persona-a": 2,
                "persona-b": 2,
            },
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("project_id", "999999"),
        ("source_id", "SRC-000002"),
        ("source_projection_id", "SP-000002"),
        ("team_id", "other-team"),
        ("llm_provider", "other-provider"),
        ("llm_model", "other-model"),
        ("prompt_schema_version", "2.0.0"),
    ],
)
def test_result_configuration_mismatch_is_rejected(
    field: str,
    value: str,
) -> None:
    kwargs = {field: value}
    changed = agent_result("persona-b", **kwargs)

    with pytest.raises(
        (
            SemanticConsensusConfigurationError,
            SemanticConsensusReferenceError,
        )
    ):
        analyze(
            (
                agent_result("persona-a"),
                changed,
            )
        )


def test_changed_source_excerpt_is_rejected_by_context() -> None:
    changed = candidate(excerpt="alpha")

    with pytest.raises(SemanticConsensusReferenceError):
        analyze(
            (
                agent_result(
                    "persona-a",
                    candidates=(changed,),
                ),
                agent_result("persona-b"),
            )
        )