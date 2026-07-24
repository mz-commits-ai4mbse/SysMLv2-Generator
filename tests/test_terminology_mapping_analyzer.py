"""Tests for deterministic terminology mapping consensus."""

from __future__ import annotations

from dataclasses import fields, replace
from hashlib import sha256
from itertools import permutations

import pytest

from modules.information_units.types import (
    InformationUnit,
    InformationUnitExtractionProvenance,
    InformationUnitSourceAnchor,
)
from modules.terminology_mapping.agent_manifest import (
    create_terminology_mapping_agent_candidate,
    create_terminology_mapping_agent_result,
    create_terminology_mapping_basis,
    create_terminology_mapping_proposal,
    create_terminology_mapping_target,
    create_terminology_occurrence,
)
from modules.terminology_mapping.analyzer import (
    TERMINOLOGY_MAPPING_CONSENSUS_SCHEMA_VERSION,
    TERMINOLOGY_MAPPING_NORMALIZATION_ID,
    TERMINOLOGY_MAPPING_NORMALIZATION_VERSION,
    TerminologyMappingConsensusResult,
    analyze_terminology_mapping_consensus,
    normalize_terminology_mapping_text,
    terminology_mapping_signature,
    terminology_occurrence_key,
)
from modules.terminology_mapping.errors import (
    DuplicateTerminologyMappingAgentResultError,
    TerminologyMappingComparisonError,
    TerminologyMappingConfigurationError,
    TerminologyMappingValidationError,
)
from modules.terminology_mapping.types import (
    TerminologyMappingAgentCandidate,
    TerminologyMappingAgentResult,
)


PROJECT_ID = "318604"
SOURCE_ID = "SRC-000001"
SOURCE_PROJECTION_ID = "SP-000001"
INFORMATION_UNIT_ID = "IU-000001"
TIMESTAMP = "2026-07-24T14:00:00Z"


def information_unit() -> InformationUnit:
    statement = "The pump shall preserve system pressure."
    return InformationUnit(
        schema_version="1.0.0",
        project_id=PROJECT_ID,
        information_unit_id=INFORMATION_UNIT_ID,
        source_id=SOURCE_ID,
        source_projection_id=SOURCE_PROJECTION_ID,
        source_anchors=(
            InformationUnitSourceAnchor(
                segment_id="SEG-000001",
                start_offset=0,
                end_offset=len(statement),
            ),
        ),
        source_excerpt=statement,
        interpreted_statement=statement,
        information_type="requirement",
        statement_modality="normative",
        epistemic_class="explicit",
        supporting_information_unit_ids=(),
        derivation_rationale=None,
        missing_evidence=None,
        extraction_provenance=(
            InformationUnitExtractionProvenance(
                team_id="semantic-team",
                persona_ids=("persona-a", "persona-b"),
                llm_provider="test-provider",
                llm_model="test-model",
                prompt_schema_version="1.0.0",
                consensus_report_id="CONSENSUS-TEST-001",
            )
        ),
        confidence="high",
        confidence_rationale="Unanimous semantic extraction.",
        content_fingerprint="a" * 64,
        created_at="2026-07-24T12:00:00Z",
    )


def mapping_basis(
    basis_type: str = "accepted_project_glossary",
) -> object:
    values = {
        "accepted_project_glossary": (
            f"{PROJECT_ID}/PC-000001/revision/1",
            "1",
        ),
        "turing_core": ("TC-000001", "1.0.0"),
        "reference_concept_index": (
            "https://example.org/ontology/Pump",
            "1.0.0",
        ),
        "semantic_interpretation": (
            "IU-000001/interpreted_statement/4:8",
            None,
        ),
    }
    reference_id, version = values[basis_type]
    return create_terminology_mapping_basis(
        basis_type=basis_type,
        reference_id=reference_id,
        reference_version=version,
        rationale="Deterministic test mapping basis.",
    )


def project_proposal(
    *,
    display_label: str = "Pump",
    rationale: str = "The accepted project meaning matches.",
) -> object:
    target = create_terminology_mapping_target(
        target_kind="project_concept",
        display_label=display_label,
        project_concept_id="PC-000001",
        project_concept_revision=1,
    )
    return create_terminology_mapping_proposal(
        mapping_relation="exact_match",
        target=target,
        mapping_bases=(
            mapping_basis(),
            mapping_basis("semantic_interpretation"),
        ),
        rationale=rationale,
    )


def turing_proposal() -> object:
    target = create_terminology_mapping_target(
        target_kind="turing_core_concept",
        display_label="System Element",
        turing_core_concept_id="TC-000001",
    )
    return create_terminology_mapping_proposal(
        mapping_relation="related_to",
        target=target,
        mapping_bases=(mapping_basis("turing_core"),),
        rationale="Turing Core provides a related MBSE meaning.",
    )


def no_equivalent_proposal() -> object:
    return create_terminology_mapping_proposal(
        mapping_relation="no_equivalent",
        target=None,
        mapping_bases=(
            mapping_basis("semantic_interpretation"),
        ),
        rationale="No controlled equivalent was found.",
    )


def occurrence(
    *,
    term: str = "pump",
) -> object:
    unit = information_unit()
    start = unit.interpreted_statement.index(term)
    return create_terminology_occurrence(
        unit,
        text_field="interpreted_statement",
        start_offset=start,
        end_offset=start + len(term),
    )


def candidate(
    *,
    status: str = "mapped",
    proposals: tuple[object, ...] | None = None,
    selected_occurrence: object | None = None,
    rationale: str = "Persona mapping rationale.",
) -> TerminologyMappingAgentCandidate:
    selected_proposals = (
        (project_proposal(),)
        if proposals is None
        else proposals
    )
    return create_terminology_mapping_agent_candidate(
        terminology_mapping_agent_candidate_id="TMAC-000001",
        occurrence=(
            occurrence()
            if selected_occurrence is None
            else selected_occurrence
        ),
        mapping_status=status,
        proposals=selected_proposals,
        rationale=rationale,
        uncertainties=(),
    )


def agent_result(
    persona_id: str,
    *,
    run_index: int = 1,
    selected_candidate: TerminologyMappingAgentCandidate
    | None = None,
    omit_candidate: bool = False,
    fingerprint: str | None = None,
    **overrides: object,
) -> TerminologyMappingAgentResult:
    candidates = (
        ()
        if omit_candidate
        else (
            candidate()
            if selected_candidate is None
            else selected_candidate,
        )
    )
    values: dict[str, object] = {
        "information_unit": information_unit(),
        "team_id": "terminology-team",
        "agent_id": f"agent-{persona_id}",
        "persona_id": persona_id,
        "persona_run_index": run_index,
        "persona_configuration_fingerprint": (
            fingerprint
            or sha256(persona_id.encode("utf-8")).hexdigest()
        ),
        "llm_provider": "test-provider",
        "llm_model": "test-model",
        "prompt_schema_version": "1.0.0",
        "ontology_registry_version": "1.0.0",
        "reference_concept_index_version": "1.0.0",
        "turing_core_version": "1.0.0",
        "project_glossary_revision": 1,
        "candidates": candidates,
        "no_candidate_rationale": (
            "No mapping candidate for this persona run."
            if omit_candidate
            else None
        ),
        "timestamp": "2026-07-24T13:00:00Z",
    }
    values.update(overrides)
    return create_terminology_mapping_agent_result(**values)


def analyze(
    results: tuple[TerminologyMappingAgentResult, ...],
    *,
    personas: tuple[str, ...] = (
        "persona-a",
        "persona-b",
    ),
    expectations: dict[str, int] | None = None,
    timestamp: str = TIMESTAMP,
) -> TerminologyMappingConsensusResult:
    return analyze_terminology_mapping_consensus(
        agent_results=results,
        required_personas=personas,
        expected_runs_per_persona=(
            {persona_id: 1 for persona_id in personas}
            if expectations is None
            else expectations
        ),
        information_unit=information_unit(),
        timestamp=timestamp,
    )


def test_consensus_contract_is_explicit() -> None:
    assert TERMINOLOGY_MAPPING_CONSENSUS_SCHEMA_VERSION == "1.0.0"
    assert (
        TERMINOLOGY_MAPPING_NORMALIZATION_ID
        == "unicode_nfkc_whitespace_casefold"
    )
    assert TERMINOLOGY_MAPPING_NORMALIZATION_VERSION == "1.0.0"


def test_consensus_result_is_frozen_and_slotted() -> None:
    assert TerminologyMappingConsensusResult.__dataclass_params__.frozen
    assert TerminologyMappingConsensusResult.__slots__


def test_lexical_normalization_is_deterministic() -> None:
    assert normalize_terminology_mapping_text(
        "  ＰUMP\t "
    ) == "pump"


@pytest.mark.parametrize(
    "value",
    [None, 1, "", "   "],
)
def test_lexical_normalization_rejects_invalid_input(
    value: object,
) -> None:
    with pytest.raises(TerminologyMappingComparisonError):
        normalize_terminology_mapping_text(value)


def test_occurrence_key_preserves_exact_evidence() -> None:
    assert terminology_occurrence_key(occurrence()) == (
        "interpreted_statement",
        4,
        8,
        "pump",
    )


def test_signature_excludes_wording_only_rationale() -> None:
    first = candidate(
        proposals=(
            project_proposal(rationale="First rationale."),
        ),
        rationale="First candidate rationale.",
    )
    second = candidate(
        proposals=(
            project_proposal(rationale="Second rationale."),
        ),
        rationale="Second candidate rationale.",
    )

    assert terminology_mapping_signature(first) == (
        terminology_mapping_signature(second)
    )


def test_signature_uses_stable_target_not_display_label() -> None:
    first = candidate(
        proposals=(project_proposal(display_label="Pump"),),
    )
    second = candidate(
        proposals=(
            project_proposal(display_label="Pumpe"),
        ),
    )

    assert terminology_mapping_signature(first) == (
        terminology_mapping_signature(second)
    )


def test_different_target_changes_signature() -> None:
    first = candidate()
    second = candidate(proposals=(turing_proposal(),))

    assert terminology_mapping_signature(first) != (
        terminology_mapping_signature(second)
    )


def test_unanimous_mapping_is_high_but_requires_confirmation() -> None:
    outcome = analyze(
        (
            agent_result("persona-a"),
            agent_result("persona-b"),
        )
    ).outcomes[0]

    assert outcome.consensus_level == "unanimous"
    assert outcome.variance_level == "low"
    assert outcome.confidence == "high"
    assert outcome.mapping_status == "mapped"
    assert outcome.confirmation_required is True
    assert outcome.review_required is False
    assert outcome.recommended_review_mode == "quick_confirmation"
    assert outcome.persistence_eligible is True


def test_unanimous_wording_variation_remains_high() -> None:
    first = candidate(
        proposals=(
            project_proposal(
                display_label="Pump",
                rationale="First wording.",
            ),
        ),
    )
    second = candidate(
        proposals=(
            project_proposal(
                display_label="Pumpe",
                rationale="Second wording.",
            ),
        ),
    )
    outcome = analyze(
        (
            agent_result(
                "persona-a",
                selected_candidate=first,
            ),
            agent_result(
                "persona-b",
                selected_candidate=second,
            ),
        )
    ).outcomes[0]

    assert outcome.confidence == "high"
    assert outcome.supporting_personas == (
        "persona-a",
        "persona-b",
    )


def test_two_persona_disagreement_is_incomparable() -> None:
    outcome = analyze(
        (
            agent_result("persona-a"),
            agent_result(
                "persona-b",
                selected_candidate=candidate(
                    proposals=(turing_proposal(),)
                ),
            ),
        )
    ).outcomes[0]

    assert outcome.consensus_level == "incomparable"
    assert outcome.confidence == "low"
    assert outcome.persistence_eligible is False
    assert outcome.review_required is True


def test_three_persona_majority_is_medium() -> None:
    outcome = analyze(
        (
            agent_result("persona-a"),
            agent_result("persona-b"),
            agent_result(
                "persona-c",
                selected_candidate=candidate(
                    proposals=(turing_proposal(),)
                ),
            ),
        ),
        personas=(
            "persona-a",
            "persona-b",
            "persona-c",
        ),
    ).outcomes[0]

    assert outcome.consensus_level == "majority"
    assert outcome.variance_level == "medium"
    assert outcome.confidence == "medium"
    assert outcome.supporting_personas == (
        "persona-a",
        "persona-b",
    )
    assert outcome.dissenting_personas == ("persona-c",)
    assert outcome.review_required is True


def test_single_support_is_low() -> None:
    outcome = analyze(
        (
            agent_result("persona-a"),
            agent_result("persona-b", omit_candidate=True),
            agent_result("persona-c", omit_candidate=True),
        ),
        personas=(
            "persona-a",
            "persona-b",
            "persona-c",
        ),
    ).outcomes[0]

    assert outcome.consensus_level == "incomplete"
    assert outcome.confidence == "low"
    assert outcome.omitting_personas == (
        "persona-b",
        "persona-c",
    )


def test_all_personas_may_omit_candidates() -> None:
    selected = analyze(
        (
            agent_result("persona-a", omit_candidate=True),
            agent_result("persona-b", omit_candidate=True),
        )
    )

    assert selected.outcomes == ()
    assert any(
        issue.code == "no_terminology_mapping_candidates"
        for issue in selected.issues
    )


def test_stable_repeated_runs_do_not_create_more_votes() -> None:
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
    assert outcome.confidence == "high"
    assert len(outcome.candidate_references) == 4


def test_unstable_repeated_run_caps_confidence() -> None:
    results = (
        agent_result("persona-a", run_index=1),
        agent_result("persona-a", run_index=2),
        agent_result(
            "persona-a",
            run_index=3,
            selected_candidate=candidate(
                proposals=(turing_proposal(),)
            ),
        ),
        agent_result("persona-b", run_index=1),
        agent_result("persona-b", run_index=2),
        agent_result("persona-b", run_index=3),
    )
    selected = analyze(
        results,
        expectations={
            "persona-a": 3,
            "persona-b": 3,
        },
    )
    outcome = selected.outcomes[0]

    assert outcome.consensus_level == "unanimous"
    assert outcome.confidence == "medium"
    assert outcome.review_required is True
    assert any(
        issue.code == "unstable_persona_mapping"
        for issue in selected.issues
    )


def test_tied_repeated_runs_are_indeterminate() -> None:
    results = (
        agent_result("persona-a", run_index=1),
        agent_result(
            "persona-a",
            run_index=2,
            selected_candidate=candidate(
                proposals=(turing_proposal(),)
            ),
        ),
        agent_result("persona-b", run_index=1),
        agent_result("persona-b", run_index=2),
    )
    selected = analyze(
        results,
        expectations={
            "persona-a": 2,
            "persona-b": 2,
        },
    )

    assert selected.outcomes[0].confidence == "low"
    assert any(
        issue.code == "indeterminate_persona_mapping"
        for issue in selected.issues
    )


def test_missing_run_makes_consensus_incomplete() -> None:
    selected = analyze(
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

    assert selected.outcomes[0].consensus_level == "incomplete"
    assert selected.outcomes[0].confidence == "low"
    assert any(
        issue.code == "missing_persona_run"
        for issue in selected.issues
    )


def test_ambiguous_mapping_always_requires_detailed_review() -> None:
    ambiguous = candidate(
        status="ambiguous",
        proposals=(project_proposal(), turing_proposal()),
    )
    outcome = analyze(
        (
            agent_result(
                "persona-a",
                selected_candidate=ambiguous,
            ),
            agent_result(
                "persona-b",
                selected_candidate=ambiguous,
            ),
        )
    ).outcomes[0]

    assert outcome.confidence == "high"
    assert outcome.mapping_status == "ambiguous"
    assert outcome.review_required is True
    assert outcome.recommended_review_mode == "detailed_review"


def test_conflict_mapping_always_requires_detailed_review() -> None:
    conflict = candidate(
        status="conflict",
        proposals=(project_proposal(),),
    )
    outcome = analyze(
        (
            agent_result(
                "persona-a",
                selected_candidate=conflict,
            ),
            agent_result(
                "persona-b",
                selected_candidate=conflict,
            ),
        )
    ).outcomes[0]

    assert outcome.confidence == "high"
    assert outcome.mapping_status == "conflict"
    assert outcome.review_required is True


def test_no_equivalent_may_use_quick_confirmation() -> None:
    no_equivalent = candidate(
        status="no_equivalent",
        proposals=(no_equivalent_proposal(),),
    )
    outcome = analyze(
        (
            agent_result(
                "persona-a",
                selected_candidate=no_equivalent,
            ),
            agent_result(
                "persona-b",
                selected_candidate=no_equivalent,
            ),
        )
    ).outcomes[0]

    assert outcome.mapping_status == "no_equivalent"
    assert outcome.confidence == "high"
    assert outcome.review_required is False


def test_unmapped_may_use_quick_confirmation() -> None:
    unmapped = candidate(
        status="unmapped",
        proposals=(),
    )
    outcome = analyze(
        (
            agent_result(
                "persona-a",
                selected_candidate=unmapped,
            ),
            agent_result(
                "persona-b",
                selected_candidate=unmapped,
            ),
        )
    ).outcomes[0]

    assert outcome.mapping_status == "unmapped"
    assert outcome.confidence == "high"
    assert outcome.review_required is False


def test_input_order_does_not_change_result() -> None:
    results = (
        agent_result("persona-a"),
        agent_result("persona-b"),
        agent_result("persona-c"),
    )
    outputs = tuple(
        analyze(
            tuple(order),
            personas=(
                "persona-a",
                "persona-b",
                "persona-c",
            ),
        )
        for order in permutations(results)
    )

    assert all(output == outputs[0] for output in outputs)


def test_consensus_preserves_reproducibility_versions() -> None:
    selected = analyze(
        (
            agent_result("persona-a"),
            agent_result("persona-b"),
        )
    )

    assert selected.ontology_registry_version == "1.0.0"
    assert selected.reference_concept_index_version == "1.0.0"
    assert selected.turing_core_version == "1.0.0"
    assert selected.project_glossary_revision == 1


def test_consensus_has_no_human_decision() -> None:
    field_names = {
        field.name
        for field in fields(TerminologyMappingConsensusResult)
    }
    for forbidden in (
        "decision",
        "reviewer_id",
        "terminology_decision_id",
        "accepted",
    ):
        assert forbidden not in field_names


def test_duplicate_persona_run_is_rejected() -> None:
    duplicate = agent_result("persona-a")

    with pytest.raises(
        DuplicateTerminologyMappingAgentResultError
    ):
        analyze((duplicate, duplicate))


@pytest.mark.parametrize(
    "required_personas",
    [
        (),
        ("persona-a", "persona-a"),
        (" persona-a ", "persona-b"),
    ],
)
def test_invalid_required_personas_are_rejected(
    required_personas: tuple[str, ...],
) -> None:
    with pytest.raises(TerminologyMappingConfigurationError):
        analyze(
            (
                agent_result("persona-a"),
                agent_result("persona-b"),
            ),
            personas=required_personas,
        )


@pytest.mark.parametrize(
    "expectations",
    [
        {"persona-a": 1},
        {
            "persona-a": 1,
            "persona-b": 1,
            "persona-c": 1,
        },
        {"persona-a": 0, "persona-b": 1},
        {"persona-a": True, "persona-b": 1},
    ],
)
def test_invalid_run_expectations_are_rejected(
    expectations: dict[str, int],
) -> None:
    with pytest.raises(TerminologyMappingConfigurationError):
        analyze(
            (
                agent_result("persona-a"),
                agent_result("persona-b"),
            ),
            expectations=expectations,
        )


def test_unrequired_persona_is_rejected() -> None:
    with pytest.raises(TerminologyMappingConfigurationError):
        analyze(
            (
                agent_result("persona-a"),
                agent_result("persona-c"),
            )
        )


def test_run_index_above_expectation_is_rejected() -> None:
    with pytest.raises(TerminologyMappingConfigurationError):
        analyze(
            (
                agent_result("persona-a", run_index=2),
                agent_result("persona-b"),
            )
        )


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("team_id", "different-team"),
        ("llm_provider", "different-provider"),
        ("llm_model", "different-model"),
        ("prompt_schema_version", "2.0.0"),
        ("ontology_registry_version", "2.0.0"),
        ("reference_concept_index_version", "2.0.0"),
        ("turing_core_version", "2.0.0"),
        ("project_glossary_revision", 2),
    ],
)
def test_results_must_share_configuration(
    field_name: str,
    value: object,
) -> None:
    first = agent_result("persona-a")
    second = agent_result(
        "persona-b",
        **{field_name: value},
    )

    with pytest.raises(TerminologyMappingConfigurationError):
        analyze((first, second))


def test_persona_fingerprint_must_be_stable_across_runs() -> None:
    with pytest.raises(TerminologyMappingConfigurationError):
        analyze(
            (
                agent_result(
                    "persona-a",
                    run_index=1,
                    fingerprint="a" * 64,
                ),
                agent_result(
                    "persona-a",
                    run_index=2,
                    fingerprint="b" * 64,
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
    "timestamp",
    ["", " timestamp ", "2026-07-24"],
)
def test_invalid_consensus_timestamp_is_rejected(
    timestamp: str,
) -> None:
    with pytest.raises(TerminologyMappingValidationError):
        analyze(
            (
                agent_result("persona-a"),
                agent_result("persona-b"),
            ),
            timestamp=timestamp,
        )


def test_wrong_candidate_type_is_rejected_by_signature() -> None:
    with pytest.raises(TerminologyMappingComparisonError):
        terminology_mapping_signature(object())


def test_wrong_occurrence_type_is_rejected_by_key() -> None:
    with pytest.raises(TerminologyMappingComparisonError):
        terminology_occurrence_key(object())