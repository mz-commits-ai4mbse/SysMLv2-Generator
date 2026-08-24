"""R4c.5b.1 persisted Subject processing artifact tests."""

from pathlib import Path
from types import SimpleNamespace
import json

import pytest

from modules.subject_review.artifacts import (
    SUBJECT_PROCESSING_ARTIFACT_FILENAMES,
    write_subject_processing_artifacts,
)


def _inputs():
    subject = SimpleNamespace(
        canonical_subject_id="SUBJ-000001",
        canonical_label="Operator",
        subject_form="entity",
        identity_status="resolved",
        mention_ids=("MNT-000001",),
        content_fingerprint="1" * 64,
    )
    mention = SimpleNamespace(
        mention_id="MNT-000001",
        source_span_id="SPAN-000001",
        segment_id="SEG-000001",
        start_offset=0,
        end_offset=8,
        exact_text="operator",
        source_evidence_ids=("EVD-000001",),
        content_fingerprint="2" * 64,
    )
    subject_set = SimpleNamespace(
        schema_version="1.0.0",
        project_id="396272",
        source_id="SRC-000001",
        source_projection_id="SP-000001",
        source_projection_fingerprint="3" * 64,
        mentions=(mention,),
        subjects=(subject,),
        content_fingerprint="4" * 64,
    )

    interpretation_item = SimpleNamespace(
        canonical_subject_id="SUBJ-000001",
        interpreted_statement="The operator is a local actor.",
        information_type="actor",
        statement_modality="descriptive",
        epistemic_class="explicit",
        missing_evidence=None,
        rationale="Directly stated.",
        uncertainties=(),
        content_fingerprint="5" * 64,
    )
    run = SimpleNamespace(
        project_id="396272",
        source_id="SRC-000001",
        source_projection_id="SP-000001",
        team_id="TEAM",
        agent_id="AGENT",
        persona_id="PERSONA",
        persona_run_index=1,
        llm_provider="openai",
        llm_model="gpt-test",
        prompt_schema_version="1.3.0",
        interpretations=(interpretation_item,),
        relationships=(),
        rejected_relationships=(),
        classification_repairs=(),
        content_fingerprint="6" * 64,
    )
    interpretations = SimpleNamespace(
        project_id="396272",
        source_id="SRC-000001",
        source_projection_id="SP-000001",
        team_id="TEAM",
        canonical_subject_ids=("SUBJ-000001",),
        required_personas=("PERSONA",),
        runs_per_persona=1,
        run_results=(run,),
    )

    # The artifact writer intentionally delegates these two payloads to the
    # already accepted serializers, so small real objects are easiest here.
    from modules.subject_consensus.types import (
        ConsensusValueDistribution,
        FieldConsensusAssessment,
        SharedSubjectConsensusResult,
        SubjectConsensusOutcome,
    )
    from modules.subject_review.types import (
        SubjectReviewBundle,
        SubjectReviewCard,
        SubjectReviewField,
    )

    field = FieldConsensusAssessment(
        field_name="information_type",
        consensus_level="unanimous",
        confidence="high",
        selected_value="actor",
        total_personas=1,
        supporting_personas=("PERSONA",),
        dissenting_personas=(),
        unstable_personas=(),
        value_distribution=(
            ConsensusValueDistribution(
                value="actor",
                supporting_personas=("PERSONA",),
            ),
        ),
        review_attention_required=False,
    )
    modality = FieldConsensusAssessment(
        field_name="statement_modality",
        consensus_level="unanimous",
        confidence="high",
        selected_value="descriptive",
        total_personas=1,
        supporting_personas=("PERSONA",),
        dissenting_personas=(),
        unstable_personas=(),
        value_distribution=(
            ConsensusValueDistribution(
                value="descriptive",
                supporting_personas=("PERSONA",),
            ),
        ),
        review_attention_required=False,
    )
    epistemic = FieldConsensusAssessment(
        field_name="epistemic_class",
        consensus_level="unanimous",
        confidence="high",
        selected_value="explicit",
        total_personas=1,
        supporting_personas=("PERSONA",),
        dissenting_personas=(),
        unstable_personas=(),
        value_distribution=(
            ConsensusValueDistribution(
                value="explicit",
                supporting_personas=("PERSONA",),
            ),
        ),
        review_attention_required=False,
    )
    consensus = SharedSubjectConsensusResult(
        schema_version="1.0.0",
        project_id="396272",
        source_id="SRC-000001",
        source_projection_id="SP-000001",
        team_id="TEAM",
        required_personas=("PERSONA",),
        runs_per_persona=1,
        canonical_subject_ids=("SUBJ-000001",),
        subject_outcomes=(
            SubjectConsensusOutcome(
                canonical_subject_id="SUBJ-000001",
                information_type=field,
                statement_modality=modality,
                epistemic_class=epistemic,
                statement_variants=(),
                uncertainty_variants=(),
                missing_evidence_variants=(),
                review_attention_required=False,
            ),
        ),
        relationship_outcomes=(),
        human_review_required=True,
        content_fingerprint="7" * 64,
    )

    review_field = SubjectReviewField(
        field_name="information_type",
        selected_value="actor",
        consensus_level="unanimous",
        confidence="high",
        value_distribution=(),
        supporting_personas=("PERSONA",),
        dissenting_personas=(),
        unstable_personas=(),
        review_attention_required=False,
    )
    review_modality = SubjectReviewField(
        field_name="statement_modality",
        selected_value="descriptive",
        consensus_level="unanimous",
        confidence="high",
        value_distribution=(),
        supporting_personas=("PERSONA",),
        dissenting_personas=(),
        unstable_personas=(),
        review_attention_required=False,
    )
    review_epistemic = SubjectReviewField(
        field_name="epistemic_class",
        selected_value="explicit",
        consensus_level="unanimous",
        confidence="high",
        value_distribution=(),
        supporting_personas=("PERSONA",),
        dissenting_personas=(),
        unstable_personas=(),
        review_attention_required=False,
    )
    card = SubjectReviewCard(
        canonical_subject_id="SUBJ-000001",
        canonical_label="Operator",
        mentions=(),
        information_type=review_field,
        statement_modality=review_modality,
        epistemic_class=review_epistemic,
        persona_interpretations=(),
        relationships=(),
        classification_review_attention_required=False,
        relationship_review_attention_required=False,
        review_attention_required=False,
        content_fingerprint="8" * 64,
    )
    review_bundle = SubjectReviewBundle(
        schema_version="1.0.0",
        project_id="396272",
        source_id="SRC-000001",
        source_projection_id="SP-000001",
        canonical_subject_ids=("SUBJ-000001",),
        cards=(card,),
        human_review_required=True,
        content_fingerprint="9" * 64,
    )

    return subject_set, interpretations, consensus, review_bundle


def test_writes_exact_four_attempt_bound_artifacts(tmp_path):
    values = _inputs()
    paths = write_subject_processing_artifacts(
        output_root=tmp_path,
        source_sha256="a" * 64,
        processing_run_id="RUN-000001",
        attempt_id="ATT-000003",
        subject_set=values[0],
        interpretations=values[1],
        consensus=values[2],
        review_bundle=values[3],
    )

    assert tuple(path.name for path in paths) == (
        SUBJECT_PROCESSING_ARTIFACT_FILENAMES
    )

    for path in paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload["authority"]["project_id"] == "396272"
        assert payload["authority"]["source_id"] == "SRC-000001"
        assert payload["authority"]["processing_run_id"] == "RUN-000001"
        assert payload["authority"]["attempt_id"] == "ATT-000003"
        assert len(payload["content_fingerprint"]) == 64


def test_refuses_overwrite_of_attempt_work_artifact(tmp_path):
    values = _inputs()
    kwargs = dict(
        output_root=tmp_path,
        source_sha256="a" * 64,
        processing_run_id="RUN-000001",
        attempt_id="ATT-000003",
        subject_set=values[0],
        interpretations=values[1],
        consensus=values[2],
        review_bundle=values[3],
    )
    write_subject_processing_artifacts(**kwargs)

    with pytest.raises(FileExistsError):
        write_subject_processing_artifacts(**kwargs)
