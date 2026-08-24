"""R4c.4 relationship consensus tests."""

from pathlib import Path

from modules.subject_consensus import analyze_subject_consensus
from modules.subject_interpretation.types import (
    PersonaSubjectInterpretation,
    PersonaSubjectRelationship,
    SharedSubjectInterpretationResult,
    SubjectInterpretationRunResult,
)


def _i(subject_id):
    return PersonaSubjectInterpretation(
        canonical_subject_id=subject_id,
        interpreted_statement="Statement.",
        information_type="unclassified",
        statement_modality="descriptive",
        epistemic_class="explicit",
        missing_evidence=None,
        rationale="Rationale.",
        uncertainties=(),
        content_fingerprint="a" * 64,
    )


def _r(statement="Uses."):
    return PersonaSubjectRelationship(
        source_subject_id="SUBJ-000001",
        relationship_kind="uses",
        target_subject_id="SUBJ-000002",
        statement=statement,
        content_fingerprint="b" * 64,
    )


def _run(persona, index, relationships):
    return SubjectInterpretationRunResult(
        project_id="396272",
        source_id="SRC-000001",
        source_projection_id="SP-000001",
        team_id="TEAM",
        agent_id=f"AGENT_{persona}",
        persona_id=persona,
        persona_run_index=index,
        llm_provider="openai",
        llm_model="gpt-test",
        prompt_schema_version="1.3.0",
        interpretations=(_i("SUBJ-000001"), _i("SUBJ-000002")),
        relationships=tuple(relationships),
        content_fingerprint="c" * 64,
    )


def _shared(runs, runs_per_persona=1):
    return SharedSubjectInterpretationResult(
        project_id="396272",
        source_id="SRC-000001",
        source_projection_id="SP-000001",
        team_id="TEAM",
        canonical_subject_ids=("SUBJ-000001", "SUBJ-000002"),
        required_personas=("P1", "P2", "P3"),
        runs_per_persona=runs_per_persona,
        run_results=tuple(runs),
        output_root=Path("/tmp/test"),
    )


def test_relationship_majority_counts_personas_not_statements():
    runs = (
        _run("P1", 1, (_r("P1 wording."),)),
        _run("P2", 1, (_r("P2 wording."),)),
        _run("P3", 1, ()),
    )

    outcome = analyze_subject_consensus(
        _shared(runs)
    ).relationship_outcomes[0]

    assert outcome.consensus_level == "majority"
    assert outcome.confidence == "medium"
    assert outcome.supporting_personas == ("P1", "P2")
    assert outcome.omitting_personas == ("P3",)
    assert len(outcome.statement_variants) == 2


def test_relationship_repeated_run_instability_does_not_vote():
    runs = (
        _run("P1", 1, (_r(),)),
        _run("P1", 2, ()),
        _run("P2", 1, (_r(),)),
        _run("P2", 2, (_r(),)),
        _run("P3", 1, ()),
        _run("P3", 2, ()),
    )

    outcome = analyze_subject_consensus(
        _shared(runs, runs_per_persona=2)
    ).relationship_outcomes[0]

    assert outcome.supporting_personas == ("P2",)
    assert outcome.omitting_personas == ("P3",)
    assert outcome.unstable_personas == ("P1",)
    assert outcome.consensus_level == "divergent"
    assert outcome.confidence == "low"
