"""R4c.5a Subject Review projection tests."""

from pathlib import Path

from modules.engineering_subjects.types import (
    CanonicalEngineeringSubject,
    CanonicalSubjectSet,
    EngineeringMention,
)
from modules.subject_consensus.types import (
    ConsensusValueDistribution,
    FieldConsensusAssessment,
    SharedSubjectConsensusResult,
    SubjectConsensusOutcome,
)
from modules.subject_interpretation.types import (
    PersonaSubjectInterpretation,
    SharedSubjectInterpretationResult,
    SubjectInterpretationRunResult,
)
from modules.subject_review import build_subject_review_bundle

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
                end_offset=8,
                exact_text="operator",
                source_evidence_ids=("EVD-000001",),
                content_fingerprint="b" * 64,
            ),
        ),
        subjects=(
            CanonicalEngineeringSubject(
                canonical_subject_id="SUBJ-000001",
                canonical_label="Operator",
                subject_form="entity",
                identity_status="resolved",
                mention_ids=("MNT-000001",),
                content_fingerprint="c" * 64,
            ),
        ),
        content_fingerprint="d" * 64,
    )


def _field(name, value):
    return FieldConsensusAssessment(
        field_name=name,
        consensus_level="unanimous",
        confidence="high",
        selected_value=value,
        total_personas=2,
        supporting_personas=("P1", "P2"),
        dissenting_personas=(),
        unstable_personas=(),
        value_distribution=(
            ConsensusValueDistribution(
                value=value,
                supporting_personas=("P1", "P2"),
            ),
        ),
        review_attention_required=False,
    )


def _interpretation(persona, statement):
    item = PersonaSubjectInterpretation(
        canonical_subject_id="SUBJ-000001",
        interpreted_statement=statement,
        information_type="actor",
        statement_modality="descriptive",
        epistemic_class="explicit",
        missing_evidence=None,
        rationale="Rationale.",
        uncertainties=(),
        content_fingerprint="e" * 64,
    )
    return SubjectInterpretationRunResult(
        project_id="396272",
        source_id="SRC-000001",
        source_projection_id="SP-000001",
        team_id="TEAM",
        agent_id=f"AGENT_{persona}",
        persona_id=persona,
        persona_run_index=1,
        llm_provider="openai",
        llm_model="gpt-test",
        prompt_schema_version="1.3.0",
        interpretations=(item,),
        relationships=(),
        content_fingerprint="f" * 64,
    )


def _inputs():
    interpretations = SharedSubjectInterpretationResult(
        project_id="396272",
        source_id="SRC-000001",
        source_projection_id="SP-000001",
        team_id="TEAM",
        canonical_subject_ids=("SUBJ-000001",),
        required_personas=("P1", "P2"),
        runs_per_persona=1,
        run_results=(
            _interpretation("P1", "The operator is local."),
            _interpretation("P2", "A local operator participates."),
        ),
        output_root=Path("/tmp/test"),
    )
    consensus = SharedSubjectConsensusResult(
        schema_version="1.0.0",
        project_id="396272",
        source_id="SRC-000001",
        source_projection_id="SP-000001",
        team_id="TEAM",
        required_personas=("P1", "P2"),
        runs_per_persona=1,
        canonical_subject_ids=("SUBJ-000001",),
        subject_outcomes=(
            SubjectConsensusOutcome(
                canonical_subject_id="SUBJ-000001",
                information_type=_field("information_type", "actor"),
                statement_modality=_field("statement_modality", "descriptive"),
                epistemic_class=_field("epistemic_class", "explicit"),
                statement_variants=(),
                uncertainty_variants=(),
                missing_evidence_variants=(),
                review_attention_required=False,
            ),
        ),
        relationship_outcomes=(),
        human_review_required=True,
        content_fingerprint="1" * 64,
    )
    return interpretations, consensus


def test_review_bundle_contains_exact_subject_and_source_mentions():
    interpretations, consensus = _inputs()
    bundle = build_subject_review_bundle(
        subject_set=_subject_set(),
        interpretations=interpretations,
        consensus=consensus,
    )

    assert bundle.canonical_subject_ids == ("SUBJ-000001",)
    assert len(bundle.cards) == 1
    card = bundle.cards[0]
    assert card.canonical_label == "Operator"
    assert card.mentions[0].exact_text == "operator"
    assert card.mentions[0].source_evidence_ids == ("EVD-000001",)


def test_review_bundle_exposes_consensus_and_persona_variants():
    interpretations, consensus = _inputs()
    card = build_subject_review_bundle(
        subject_set=_subject_set(),
        interpretations=interpretations,
        consensus=consensus,
    ).cards[0]

    assert card.information_type.selected_value == "actor"
    assert card.information_type.confidence == "high"
    assert tuple(item.persona_id for item in card.persona_interpretations) == ("P1", "P2")
    assert card.persona_interpretations[0].interpreted_statements == (
        "The operator is local.",
    )
