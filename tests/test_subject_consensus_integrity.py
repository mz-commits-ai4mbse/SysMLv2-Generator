"""R4c.4 fixed-population integrity tests."""

from pathlib import Path

import pytest

from modules.subject_consensus import (
    SubjectConsensusIntegrityError,
    analyze_subject_consensus,
)
from modules.subject_interpretation.types import (
    PersonaSubjectInterpretation,
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


def _run(persona, index, subjects):
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
        interpretations=tuple(_i(subject) for subject in subjects),
        relationships=(),
        content_fingerprint="b" * 64,
    )


def test_missing_persona_run_fails_closed():
    value = SharedSubjectInterpretationResult(
        project_id="396272",
        source_id="SRC-000001",
        source_projection_id="SP-000001",
        team_id="TEAM",
        canonical_subject_ids=("SUBJ-000001",),
        required_personas=("P1", "P2"),
        runs_per_persona=1,
        run_results=(
            _run("P1", 1, ("SUBJ-000001",)),
        ),
        output_root=Path("/tmp/test"),
    )

    with pytest.raises(SubjectConsensusIntegrityError):
        analyze_subject_consensus(value)


def test_subject_population_mismatch_fails_closed():
    value = SharedSubjectInterpretationResult(
        project_id="396272",
        source_id="SRC-000001",
        source_projection_id="SP-000001",
        team_id="TEAM",
        canonical_subject_ids=("SUBJ-000001", "SUBJ-000002"),
        required_personas=("P1",),
        runs_per_persona=1,
        run_results=(
            _run("P1", 1, ("SUBJ-000001",)),
        ),
        output_root=Path("/tmp/test"),
    )

    with pytest.raises(SubjectConsensusIntegrityError):
        analyze_subject_consensus(value)
