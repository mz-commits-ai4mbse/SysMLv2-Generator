"""Tests for bounded source-wide completeness review after SAU execution."""

from __future__ import annotations

from pathlib import Path

from modules.agents.types import AgentRunResult
from modules.ingestion.agent_inputs import (
    build_source_anchored_completeness_review_input,
)
from modules.ingestion.team_agentic_pipeline import (
    run_team_agentic_ingestion,
)
from modules.source_analysis_units.types import (
    SourceAnalysisUnit,
    SourceAnalysisUnitAnchor,
)


def _consensus_bundle(stage_name: str) -> dict[str, object]:
    return {
        "source_anchored": True,
        "stage_name": stage_name,
        "source_analysis_unit_count": 2,
        "unit_consensus_reports": [
            {
                "source_analysis_unit_id": "SAU-000001",
                "team_id": f"team_{stage_name}",
                "task_name": stage_name,
                "total_agents": 3,
                "summary": {
                    "full_agreement": 1,
                    "review_required": 1,
                },
                "groups": [
                    {
                        "group_key": "candidate::one",
                        "item_type": "candidate_model_element",
                        "agreement_level": "full_agreement",
                        "total_agents": 3,
                        "supporting_agents": ["a", "b", "c"],
                        "value_distribution": {
                            "value": ["a", "b", "c"],
                        },
                        "representative_value": "Microscope operator",
                        "review_required": False,
                        "reason": "All agents agree.",
                        "agent_values": {
                            "a": "VERY_LARGE_RAW_AGENT_DETAIL_A",
                            "b": "VERY_LARGE_RAW_AGENT_DETAIL_B",
                            "c": "VERY_LARGE_RAW_AGENT_DETAIL_C",
                        },
                    }
                ],
            },
            {
                "source_analysis_unit_id": "SAU-000002",
                "team_id": f"team_{stage_name}",
                "task_name": stage_name,
                "total_agents": 3,
                "summary": {
                    "full_agreement": 0,
                    "review_required": 1,
                },
                "groups": [
                    {
                        "group_key": "candidate::two",
                        "item_type": "candidate_model_element",
                        "agreement_level": "minority_interpretation",
                        "representative_value": "Remote expert",
                        "review_required": True,
                        "reason": "Persona disagreement.",
                        "agent_values": {
                            "a": "VERY_LARGE_RAW_AGENT_DETAIL_D",
                        },
                    }
                ],
            },
        ],
    }


def _unit(
    unit_id: str,
    order: int,
    excerpt: str,
) -> SourceAnalysisUnit:
    return SourceAnalysisUnit(
        schema_version="1.0.0",
        project_id="123456",
        source_id="SRC-000001",
        source_projection_id="SP-000001",
        source_analysis_unit_id=unit_id,
        source_projection_fingerprint="a" * 64,
        source_anchors=(
            SourceAnalysisUnitAnchor(
                segment_id=f"SEG-{order:06d}",
                start_offset=0,
                end_offset=len(excerpt),
            ),
        ),
        source_excerpt=excerpt,
        source_order_index=order,
        segmentation_profile_id="source_projection_segments",
        segmentation_profile_version="1.0.0",
        content_fingerprint=str(order) * 64,
        created_at="2026-08-19T10:00:00Z",
    )


def test_source_anchored_completeness_input_is_compact() -> None:
    text = build_source_anchored_completeness_review_input(
        task_id="TASK_POST_D5",
        raw_input_path=Path("legacy/source.md"),
        raw_text="Original engineering source.",
        source_analysis_unit_count=2,
        interpretation_run_count=12,
        evidence_run_count=12,
        derivation_run_count=12,
        interpretation_consensus=_consensus_bundle(
            "01_legacy_interpretation"
        ),
        evidence_consensus=_consensus_bundle(
            "02_evidence_classification"
        ),
        derivation_consensus=_consensus_bundle(
            "03_derivation_assessment"
        ),
    )

    assert "Original engineering source." in text

    normalized_text = " ".join(text.split())
    assert (
        "processed as 2 canonical Source Analysis Units."
        in normalized_text
    )

    assert "Legacy Interpretation: 12" in text
    assert "Evidence Classification: 12" in text
    assert "Derivation Assessment: 12" in text
    assert "SAU-000001" in text
    assert "SAU-000002" in text
    assert "Microscope operator" in text
    assert "Remote expert" in text

    assert "VERY_LARGE_RAW_AGENT_DETAIL_A" not in text
    assert "VERY_LARGE_RAW_AGENT_DETAIL_D" not in text
    assert '"agent_values"' not in text
    assert '"value_distribution"' not in text
    assert '"supporting_agents"' not in text


def test_source_anchored_pipeline_uses_compact_completeness_input(
    tmp_path: Path,
    monkeypatch,
) -> None:
    calls: list[dict[str, object]] = []

    def fake_stage(**kwargs):
        calls.append(dict(kwargs))
        stage_name = str(kwargs["stage_name"])
        unit_id = kwargs.get("source_analysis_unit_id")

        result = AgentRunResult(
            agent_id=f"agent_{stage_name}",
            task_name=stage_name,
            run_index=1,
            provider="test",
            model="test-model",
            output_text=(
                "RAW_PER_PERSONA_OUTPUT_THAT_MUST_NOT_REACH_"
                "SOURCE_WIDE_COMPLETENESS"
            ),
            output_path=tmp_path / f"{stage_name}.json",
            status="completed",
            source_analysis_unit_id=(
                str(unit_id) if unit_id is not None else None
            ),
        )

        report: dict[str, object] = {
            "team_id": f"team_{stage_name}",
            "task_name": stage_name,
            "total_agents": 1,
            "summary": {"full_agreement": 1},
            "groups": [
                {
                    "group_key": f"group::{stage_name}",
                    "item_type": "test",
                    "agreement_level": "full_agreement",
                    "representative_value": f"summary::{stage_name}",
                    "review_required": False,
                    "reason": "Test consensus.",
                    "agent_values": {
                        "agent": (
                            "RAW_PER_PERSONA_OUTPUT_THAT_MUST_NOT_REACH_"
                            "SOURCE_WIDE_COMPLETENESS"
                        ),
                    },
                }
            ],
        }
        if unit_id is not None:
            report["source_analysis_unit_id"] = str(unit_id)

        return [result], report

    def fake_report(**kwargs):
        path = kwargs["report_output_path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# Report\n", encoding="utf-8")

    monkeypatch.setattr(
        "modules.ingestion.team_agentic_pipeline."
        "run_stage_with_consensus",
        fake_stage,
    )
    monkeypatch.setattr(
        "modules.ingestion.team_agentic_pipeline."
        "write_ingestion_review_report",
        fake_report,
    )
    monkeypatch.setattr(
        "modules.ingestion.team_agentic_pipeline."
        "write_run_summaries",
        lambda **kwargs: {},
    )

    raw_input = tmp_path / "source.md"
    raw_input.write_text(
        "First source unit.\n\nSecond source unit.",
        encoding="utf-8",
    )

    run_team_agentic_ingestion(
        project_root=tmp_path,
        task_id="TASK_POST_D5",
        recipe_id="REC_INGESTION_001",
        raw_input_path=raw_input,
        report_output_path=tmp_path / "report.md",
        source_analysis_units=(
            _unit("SAU-000001", 1, "First source unit."),
            _unit("SAU-000002", 2, "Second source unit."),
        ),
        dry_run=True,
    )

    completeness_call = calls[-1]
    assert completeness_call["stage_name"] == "04_completeness_review"
    assert completeness_call.get("source_analysis_unit_id") is None

    completeness_input = str(completeness_call["input_text"])
    assert "First source unit." in completeness_input
    assert "Second source unit." in completeness_input
    assert "Legacy Interpretation: 2" in completeness_input
    assert "Evidence Classification: 2" in completeness_input
    assert "Derivation Assessment: 2" in completeness_input
    assert "summary::03_derivation_assessment" in completeness_input
    assert (
        "RAW_PER_PERSONA_OUTPUT_THAT_MUST_NOT_REACH_"
        "SOURCE_WIDE_COMPLETENESS"
        not in completeness_input
    )
