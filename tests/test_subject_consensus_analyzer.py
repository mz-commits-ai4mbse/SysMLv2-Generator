"""R4c.4 deterministic field-level Subject consensus tests."""

from __future__ import annotations

from pathlib import Path

from modules.subject_consensus import analyze_subject_consensus
from modules.subject_interpretation.types import (
    PersonaSubjectInterpretation,
    PersonaSubjectRelationship,
    SharedSubjectInterpretationResult,
    SubjectInterpretationRunResult,
)


def _interpretation(
    subject_id: str,
    *,
    information_type: str,
    modality: str = "descriptive",
    epistemic: str = "explicit",
    statement: str = "Statement.",
    uncertainties=(),
    missing_evidence=None,
):
    return PersonaSubjectInterpretation(
        canonical_subject_id=subject_id,
        interpreted_statement=statement,
        information_type=information_type,
        statement_modality=modality,
        epistemic_class=epistemic,
        missing_evidence=missing_evidence,
        rationale="Rationale.",
        uncertainties=tuple(uncertainties),
        content_fingerprint="a" * 64,
    )


def _relationship(
    source: str,
    kind: str,
    target: str,
    statement: str = "Relationship.",
):
    return PersonaSubjectRelationship(
        source_subject_id=source,
        relationship_kind=kind,
        target_subject_id=target,
        statement=statement,
        content_fingerprint="b" * 64,
    )


def _run(
    persona_id: str,
    run_index: int,
    interpretations,
    relationships=(),
):
    return SubjectInterpretationRunResult(
        project_id="396272",
        source_id="SRC-000001",
        source_projection_id="SP-000001",
        team_id="TEAM",
        agent_id=f"AGENT_{persona_id}",
        persona_id=persona_id,
        persona_run_index=run_index,
        llm_provider="openai",
        llm_model="gpt-test",
        prompt_schema_version="1.3.0",
        interpretations=tuple(interpretations),
        relationships=tuple(relationships),
        content_fingerprint="c" * 64,
    )


def _shared(run_results, *, runs_per_persona=1):
    personas = tuple(
        sorted({run.persona_id for run in run_results})
    )
    return SharedSubjectInterpretationResult(
        project_id="396272",
        source_id="SRC-000001",
        source_projection_id="SP-000001",
        team_id="TEAM",
        canonical_subject_ids=("SUBJ-000001", "SUBJ-000002"),
        required_personas=personas,
        runs_per_persona=runs_per_persona,
        run_results=tuple(run_results),
        output_root=Path("/tmp/test"),
    )


def test_unanimous_structured_field_is_high_confidence():
    runs = [
        _run(
            persona,
            1,
            (
                _interpretation("SUBJ-000001", information_type="actor"),
                _interpretation(
                    "SUBJ-000002",
                    information_type="information_item",
                ),
            ),
        )
        for persona in ("P1", "P2", "P3")
    ]

    result = analyze_subject_consensus(_shared(runs))
    field = result.subject_outcomes[0].information_type

    assert field.consensus_level == "unanimous"
    assert field.confidence == "high"
    assert field.selected_value == "actor"
    assert field.supporting_personas == ("P1", "P2", "P3")
    assert field.review_attention_required is False
    assert result.human_review_required is True


def test_strict_majority_is_medium_and_preserves_dissent():
    runs = [
        _run(
            "P1",
            1,
            (
                _interpretation("SUBJ-000001", information_type="actor"),
                _interpretation("SUBJ-000002", information_type="gap"),
            ),
        ),
        _run(
            "P2",
            1,
            (
                _interpretation("SUBJ-000001", information_type="actor"),
                _interpretation("SUBJ-000002", information_type="gap"),
            ),
        ),
        _run(
            "P3",
            1,
            (
                _interpretation(
                    "SUBJ-000001",
                    information_type="stakeholder",
                ),
                _interpretation("SUBJ-000002", information_type="gap"),
            ),
        ),
    ]

    field = analyze_subject_consensus(
        _shared(runs)
    ).subject_outcomes[0].information_type

    assert field.consensus_level == "majority"
    assert field.confidence == "medium"
    assert field.selected_value == "actor"
    assert field.supporting_personas == ("P1", "P2")
    assert field.dissenting_personas == ("P3",)
    assert field.review_attention_required is True


def test_three_way_split_is_low_without_selected_value():
    types = {
        "P1": "logical_element",
        "P2": "physical_element",
        "P3": "interface",
    }
    runs = [
        _run(
            persona,
            1,
            (
                _interpretation(
                    "SUBJ-000001",
                    information_type=info_type,
                ),
                _interpretation("SUBJ-000002", information_type="gap"),
            ),
        )
        for persona, info_type in types.items()
    ]

    field = analyze_subject_consensus(
        _shared(runs)
    ).subject_outcomes[0].information_type

    assert field.consensus_level == "divergent"
    assert field.confidence == "low"
    assert field.selected_value is None
    assert len(field.value_distribution) == 3


def test_repeated_runs_do_not_create_extra_persona_votes():
    runs = [
        _run(
            "P1",
            1,
            (
                _interpretation("SUBJ-000001", information_type="actor"),
                _interpretation("SUBJ-000002", information_type="gap"),
            ),
        ),
        _run(
            "P1",
            2,
            (
                _interpretation(
                    "SUBJ-000001",
                    information_type="stakeholder",
                ),
                _interpretation("SUBJ-000002", information_type="gap"),
            ),
        ),
        _run(
            "P2",
            1,
            (
                _interpretation("SUBJ-000001", information_type="actor"),
                _interpretation("SUBJ-000002", information_type="gap"),
            ),
        ),
        _run(
            "P2",
            2,
            (
                _interpretation("SUBJ-000001", information_type="actor"),
                _interpretation("SUBJ-000002", information_type="gap"),
            ),
        ),
        _run(
            "P3",
            1,
            (
                _interpretation(
                    "SUBJ-000001",
                    information_type="stakeholder",
                ),
                _interpretation("SUBJ-000002", information_type="gap"),
            ),
        ),
        _run(
            "P3",
            2,
            (
                _interpretation(
                    "SUBJ-000001",
                    information_type="stakeholder",
                ),
                _interpretation("SUBJ-000002", information_type="gap"),
            ),
        ),
    ]

    field = analyze_subject_consensus(
        _shared(runs, runs_per_persona=2)
    ).subject_outcomes[0].information_type

    assert field.unstable_personas == ("P1",)
    assert field.selected_value is None
    assert field.consensus_level == "divergent"
    assert field.confidence == "low"


def test_free_text_variants_are_preserved_not_string_voted():
    runs = [
        _run(
            "P1",
            1,
            (
                _interpretation(
                    "SUBJ-000001",
                    information_type="actor",
                    statement="The operator is a local role.",
                ),
                _interpretation("SUBJ-000002", information_type="gap"),
            ),
        ),
        _run(
            "P2",
            1,
            (
                _interpretation(
                    "SUBJ-000001",
                    information_type="actor",
                    statement="A local operator participates.",
                ),
                _interpretation("SUBJ-000002", information_type="gap"),
            ),
        ),
        _run(
            "P3",
            1,
            (
                _interpretation(
                    "SUBJ-000001",
                    information_type="actor",
                    statement="The local role is the operator.",
                ),
                _interpretation("SUBJ-000002", information_type="gap"),
            ),
        ),
    ]

    outcome = analyze_subject_consensus(_shared(runs)).subject_outcomes[0]

    assert outcome.information_type.confidence == "high"
    assert tuple(
        variant.statements[0]
        for variant in outcome.statement_variants
    ) == (
        "The operator is a local role.",
        "A local operator participates.",
        "The local role is the operator.",
    )


def test_uncertainty_forces_subject_review_attention():
    runs = [
        _run(
            persona,
            1,
            (
                _interpretation(
                    "SUBJ-000001",
                    information_type="actor",
                    uncertainties=(
                        ("Boundary unclear.",)
                        if persona == "P3"
                        else ()
                    ),
                ),
                _interpretation("SUBJ-000002", information_type="gap"),
            ),
        )
        for persona in ("P1", "P2", "P3")
    ]

    outcome = analyze_subject_consensus(_shared(runs)).subject_outcomes[0]

    assert outcome.information_type.confidence == "high"
    assert outcome.review_attention_required is True
