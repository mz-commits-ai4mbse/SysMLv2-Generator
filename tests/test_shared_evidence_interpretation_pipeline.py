"""Integration tests for shared-Evidence persona interpretation."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

from modules.agents.types import AgentRunResult
from modules.evidence_interpretation import (
    SharedEvidenceInterpretationPipeline,
)
from modules.project_sources import (
    ENGINEERING_SOURCE_ROLE,
    ProjectSourceRegistry,
)
from modules.project_workspace import ProjectWorkspace
from modules.source_evidence import (
    SourceEvidenceAnchor,
    SourceEvidenceRepository,
)
from modules.source_projection.repository import (
    SourceProjectionRepository,
)


PROJECT_ID = "318604"


def fixed_clock() -> datetime:
    return datetime(
        2026,
        8,
        21,
        10,
        0,
        0,
        tzinfo=timezone.utc,
    )


def environment(tmp_path: Path):
    projects_root = tmp_path / "projects"
    inputs = tmp_path / "inputs"
    inputs.mkdir()

    workspace = ProjectWorkspace(
        root=projects_root,
        id_generator=lambda: PROJECT_ID,
        clock=fixed_clock,
    )
    workspace.create_project("Shared Evidence Test")

    source_path = inputs / "source.md"
    source_path.write_text(
        "# Demo\n\n"
        "The remote expert may take temporary control when the "
        "operator permits it.\n",
        encoding="utf-8",
    )

    registry = ProjectSourceRegistry(
        root=projects_root,
        clock=fixed_clock,
    )
    source = registry.register_source(
        PROJECT_ID,
        source_path,
        source_role=ENGINEERING_SOURCE_ROLE,
    )

    projection_repository = SourceProjectionRepository(
        root=projects_root,
        clock=fixed_clock,
    )
    projection = projection_repository.create_projection(
        PROJECT_ID,
        source.source_id,
    )

    evidence_repository = SourceEvidenceRepository(
        root=projects_root,
        clock=fixed_clock,
        source_projection_repository=projection_repository,
    )
    segment = next(
        segment
        for segment in projection.manifest.segments
        if "temporary control"
        in projection.content[
            segment.start_offset:segment.end_offset
        ]
    )
    segment_text = projection.content[
        segment.start_offset:segment.end_offset
    ]

    excerpts = (
        "temporary control",
        "operator permits it",
    )
    evidence = []
    for excerpt in excerpts:
        start = segment_text.index(excerpt)
        evidence.append(
            evidence_repository.create_or_reuse_evidence(
                PROJECT_ID,
                projection.manifest.source_projection_id,
                source_anchors=(
                    SourceEvidenceAnchor(
                        segment_id=segment.segment_id,
                        start_offset=start,
                        end_offset=start + len(excerpt),
                    ),
                ),
                source_excerpt=excerpt,
            )
        )

    return projection, tuple(evidence)


def test_dry_run_produces_one_consensus_subject_per_evidence(
    tmp_path: Path,
) -> None:
    projection, evidence = environment(tmp_path)

    pipeline = SharedEvidenceInterpretationPipeline(
        project_root=Path("."),
        clock=fixed_clock,
    )
    result = pipeline.run(
        source_projection=projection,
        source_evidence=evidence,
        execution_root=tmp_path / "run",
        provider="openai",
        model="gpt-test",
        runs_per_persona=1,
        max_members=None,
        dry_run=True,
    )

    assert len(result.required_personas) == 3
    assert len(result.agent_results) == 3
    assert len(result.consensus_result.outcomes) == 2
    assert result.source_evidence_ids == (
        "EVD-000001",
        "EVD-000002",
    )
    assert result.consensus_result_path.is_file()
    assert result.binding_summary_path.is_file()

    summary = json.loads(
        result.binding_summary_path.read_text(encoding="utf-8")
    )
    assert [
        item["source_evidence_id"]
        for item in summary["bindings"]
    ] == ["EVD-000001", "EVD-000002"]


def test_live_team_receives_same_fixed_evidence_and_cannot_change_grounding(
    tmp_path: Path,
) -> None:
    projection, evidence = environment(tmp_path)
    calls = []

    agent_ids = (
        "AGENT_LEGACY_LITERAL_INTERPRETER",
        "AGENT_LEGACY_SYSTEMS_ENGINEERING_INTERPRETER",
        "AGENT_LEGACY_SKEPTICAL_AMBIGUITY_INTERPRETER",
    )

    def fake_team_runner(**kwargs):
        calls.append(kwargs)
        results = []
        for index, agent_id in enumerate(agent_ids, start=1):
            payload = {
                "interpretations": [
                    {
                        "source_evidence_id": "EVD-000001",
                        "interpreted_statement": (
                            "Temporary remote control is described."
                        ),
                        "information_type": "function",
                        "statement_modality": "descriptive",
                        "epistemic_class": "explicit",
                        "missing_evidence": None,
                        "extraction_rationale": "Source-grounded.",
                        "uncertainties": [],
                    },
                    {
                        "source_evidence_id": "EVD-000002",
                        "interpreted_statement": (
                            "Operator permission constrains control."
                        ),
                        "information_type": "constraint",
                        "statement_modality": "descriptive",
                        "epistemic_class": "explicit",
                        "missing_evidence": None,
                        "extraction_rationale": "Source-grounded.",
                        "uncertainties": [],
                    },
                ]
            }
            results.append(
                AgentRunResult(
                    agent_id=agent_id,
                    task_name="Interpret fixed source-grounded Evidence",
                    run_index=1,
                    provider="openai",
                    model="gpt-test",
                    output_text=json.dumps(payload),
                    output_path=(
                        tmp_path / f"raw_{index}.json"
                    ),
                    response_id=f"resp_{index}",
                    status="completed",
                )
            )
        return results

    pipeline = SharedEvidenceInterpretationPipeline(
        project_root=Path("."),
        team_runner=fake_team_runner,
        clock=fixed_clock,
    )
    result = pipeline.run(
        source_projection=projection,
        source_evidence=evidence,
        execution_root=tmp_path / "live_run",
        provider="openai",
        model="gpt-test",
        runs_per_persona=1,
        max_members=None,
        dry_run=False,
    )

    assert len(calls) == 1
    common_input = calls[0]["input_text"]
    assert "EVD-000001" in common_input
    assert "EVD-000002" in common_input
    assert "temporary control" in common_input
    assert "operator permits it" in common_input

    for agent_result in result.agent_results:
        assert tuple(
            candidate.source_excerpt
            for candidate in agent_result.candidates
        ) == (
            "temporary control",
            "operator permits it",
        )

    assert len(result.consensus_result.outcomes) == 2
