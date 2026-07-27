"""Tests for backward-compatible Phase-F execution-root support."""

from __future__ import annotations

from pathlib import Path

from modules.agents.types import AgentRunResult
from modules.ingestion.run_summary import build_run_summary
from modules.ingestion.team_agentic_pipeline import (
    run_team_agentic_ingestion,
)


def patch_pipeline(monkeypatch):
    def fake_stage(**kwargs):
        return [], {
            "team_id": kwargs["stage_name"],
            "summary": {},
        }

    def fake_report(**kwargs):
        output = kwargs["report_output_path"]
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text("# Report\n", encoding="utf-8")

    def fake_summaries(**kwargs):
        run_dir = kwargs["run_dir"]
        (
            run_dir / "team_agentic_ingestion_run_summary.json"
        ).write_text("{}", encoding="utf-8")
        (
            run_dir / "team_agentic_ingestion_run_summary.md"
        ).write_text("# Summary\n", encoding="utf-8")
        return {}

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
        fake_summaries,
    )


def test_default_phase_f_run_location_remains_unchanged(
    tmp_path: Path,
    monkeypatch,
):
    patch_pipeline(monkeypatch)
    raw_input = tmp_path / "input.txt"
    raw_input.write_text("Source text.", encoding="utf-8")
    report = tmp_path / "reports" / "report.md"

    result = run_team_agentic_ingestion(
        project_root=tmp_path,
        task_id="TASK_DEFAULT",
        recipe_id="REC_INGESTION_001",
        raw_input_path=raw_input,
        report_output_path=report,
        dry_run=True,
    )

    assert result.run_dir.parent == (
        tmp_path / "data" / "team_runs" / "TASK_DEFAULT"
    )
    assert result.report_path == report


def test_explicit_execution_root_is_used_exactly(
    tmp_path: Path,
    monkeypatch,
):
    patch_pipeline(monkeypatch)
    raw_relative = Path("data/source_projection/content.txt")
    raw_absolute = tmp_path / raw_relative
    raw_absolute.parent.mkdir(parents=True)
    raw_absolute.write_text(
        "Normalized source.",
        encoding="utf-8",
    )
    execution_relative = Path(
        "data/projects/123456/runs/RUN-000001/work/"
        "agentic_ingestion/ATT-000001/phase_f"
    )
    report_relative = Path(
        "data/projects/123456/runs/RUN-000001/work/"
        "agentic_ingestion/ATT-000001/review.md"
    )

    result = run_team_agentic_ingestion(
        project_root=tmp_path,
        task_id="P9_TASK",
        recipe_id="REC_INGESTION_001",
        raw_input_path=raw_relative,
        report_output_path=report_relative,
        execution_root=execution_relative,
        dry_run=True,
    )

    assert result.run_dir == tmp_path / execution_relative
    assert result.report_path == tmp_path / report_relative
    assert result.report_path.is_file()


def test_run_summary_can_render_repository_relative_paths(
    tmp_path: Path,
):
    output = (
        tmp_path / "data" / "runs" / "agent_outputs"
        / "agent.json"
    )
    output.parent.mkdir(parents=True)
    output.write_text("{}", encoding="utf-8")
    result = AgentRunResult(
        agent_id="AGENT_1",
        task_name="Task",
        run_index=1,
        provider="openai",
        model="model",
        output_text="{}",
        output_path=output,
    )

    summary = build_run_summary(
        task_id="TASK",
        recipe_id="REC",
        raw_input_path=tmp_path / "data" / "input.txt",
        report_output_path=tmp_path / "data" / "report.md",
        run_id="RUN",
        run_dir=tmp_path / "data" / "runs" / "RUN",
        provider="openai",
        model="model",
        team_execution_mode="dry_run",
        agent_results=[result],
        consensus_reports=[],
        repository_root=tmp_path,
    )

    assert summary["raw_input_path"] == "data/input.txt"
    assert summary["report_output_path"] == "data/report.md"
    assert summary["run_dir"] == "data/runs/RUN"
    assert summary["agent_results"][0]["output_path"] == (
        "data/runs/agent_outputs/agent.json"
    )
