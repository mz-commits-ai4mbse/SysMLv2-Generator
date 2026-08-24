"""R4c.3b pipeline test using existing semantic dimensions."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

from modules.engineering_subjects.types import (
    CanonicalEngineeringSubject,
    CanonicalSubjectSet,
    EngineeringMention,
)
from modules.source_projection.types import (
    ProjectionSegment,
    SourceProjectionArtifact,
    SourceProjectionManifest,
)
from modules.subject_interpretation import SubjectInterpretationPipeline


_SHA = "a" * 64
_CONTENT = "The microscope operator collaborates with a remote expert."


@dataclass(frozen=True)
class _RawResult:
    agent_id: str
    run_index: int
    output_text: str


def _projection():
    segment = ProjectionSegment(
        segment_id="SEG-000001",
        segment_type="text",
        start_offset=0,
        end_offset=len(_CONTENT),
        text_sha256=_SHA,
        source_locators=(),
    )
    return SourceProjectionArtifact(
        manifest=SourceProjectionManifest(
            schema_version="1.0.0",
            project_id="396272",
            source_id="SRC-000001",
            source_projection_id="SP-000001",
            source_role="engineering_source",
            source_sha256=_SHA,
            adapter_id="test",
            adapter_version="1.0.0",
            adapter_configuration=(),
            projection_fingerprint=_SHA,
            projection_result="available",
            content_sha256=_SHA,
            content_length=len(_CONTENT),
            segments=(segment,),
            issues=(),
            created_at="2026-08-24T00:00:00Z",
        ),
        content=_CONTENT,
    )


def _subject_set():
    mentions = (
        EngineeringMention(
            mention_id="MNT-000001",
            source_span_id="SPAN-000001",
            segment_id="SEG-000001",
            start_offset=4,
            end_offset=23,
            exact_text="microscope operator",
            source_evidence_ids=("EVD-000001",),
            content_fingerprint="b" * 64,
        ),
        EngineeringMention(
            mention_id="MNT-000002",
            source_span_id="SPAN-000001",
            segment_id="SEG-000001",
            start_offset=44,
            end_offset=57,
            exact_text="remote expert",
            source_evidence_ids=("EVD-000001",),
            content_fingerprint="c" * 64,
        ),
    )
    return CanonicalSubjectSet(
        schema_version="1.0.0",
        project_id="396272",
        source_id="SRC-000001",
        source_projection_id="SP-000001",
        source_projection_fingerprint=_SHA,
        mentions=mentions,
        subjects=(
            CanonicalEngineeringSubject(
                canonical_subject_id="SUBJ-000001",
                canonical_label="Microscope Operator",
                subject_form="entity",
                identity_status="resolved",
                mention_ids=("MNT-000001",),
                content_fingerprint="d" * 64,
            ),
            CanonicalEngineeringSubject(
                canonical_subject_id="SUBJ-000002",
                canonical_label="Remote Expert",
                subject_form="entity",
                identity_status="resolved",
                mention_ids=("MNT-000002",),
                content_fingerprint="e" * 64,
            ),
        ),
        content_fingerprint="f" * 64,
    )


def _output():
    return json.dumps(
        {
            "interpretations": [
                {
                    "canonical_subject_id": "SUBJ-000001",
                    "interpreted_statement": "Local operating role.",
                    "information_type": "actor",
                    "statement_modality": "descriptive",
                    "epistemic_class": "explicit",
                    "missing_evidence": None,
                    "rationale": "The Source identifies the local role.",
                    "uncertainties": [],
                },
                {
                    "canonical_subject_id": "SUBJ-000002",
                    "interpreted_statement": "Remote consultation role.",
                    "information_type": "actor",
                    "statement_modality": "descriptive",
                    "epistemic_class": "explicit",
                    "missing_evidence": None,
                    "rationale": "The Source identifies the remote role.",
                    "uncertainties": [],
                },
            ],
            "relationships": [
                {
                    "source_subject_id": "SUBJ-000001",
                    "relationship_kind": "related_to",
                    "target_subject_id": "SUBJ-000002",
                    "statement": "The roles participate in the same context.",
                }
            ],
        }
    )


def test_pipeline_preserves_fixed_population_and_existing_dimensions(
    tmp_path: Path,
):
    def runner(**kwargs):
        from modules.agents.team_config import load_team_config
        from modules.agents.team_runner import select_team_members

        team = load_team_config(
            project_root=kwargs["project_root"],
            team_file=kwargs["team_file"],
        )
        members = tuple(
            select_team_members(
                team_config=team,
                max_members=kwargs["max_members"],
                include_alternative_members=False,
            )
        )
        return tuple(
            _RawResult(
                agent_id=member.agent_id,
                run_index=1,
                output_text=_output(),
            )
            for member in members
        )

    result = SubjectInterpretationPipeline(
        project_root=Path("."),
        team_runner=runner,
    ).run(
        source_projection=_projection(),
        subject_set=_subject_set(),
        execution_root=tmp_path,
        provider="openai",
        model="gpt-test",
        runs_per_persona=1,
    )

    assert result.canonical_subject_ids == (
        "SUBJ-000001",
        "SUBJ-000002",
    )
    assert len(result.run_results) == len(result.required_personas)

    for run_result in result.run_results:
        assert tuple(
            item.canonical_subject_id
            for item in run_result.interpretations
        ) == result.canonical_subject_ids
        assert all(
            item.information_type == "actor"
            for item in run_result.interpretations
        )
        assert len(run_result.relationships) == 1
