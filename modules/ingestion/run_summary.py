"""Run summary writing for team-based agentic ingestion.

This module only writes run summaries.

It does not call LLMs.
It does not run agents.
It does not perform consensus analysis.
It does not compose the final ingestion report.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from modules.agents.types import AgentRunResult


def build_run_summary(
    *,
    task_id: str,
    recipe_id: str,
    raw_input_path: Path,
    report_output_path: Path,
    run_id: str,
    run_dir: Path,
    provider: str,
    model: str,
    team_execution_mode: str,
    agent_results: list[AgentRunResult],
    consensus_reports: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build a structured run summary dictionary."""

    return {
        "task_id": task_id,
        "recipe_id": recipe_id,
        "raw_input_path": str(raw_input_path),
        "report_output_path": str(report_output_path),
        "run_id": run_id,
        "run_dir": str(run_dir),
        "provider": provider,
        "model": model,
        "team_execution_mode": team_execution_mode,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "agent_results": [
            serialize_agent_result(result)
            for result in agent_results
        ],
        "consensus_reports": [
            serialize_consensus_report(report)
            for report in consensus_reports
        ],
    }


def serialize_agent_result(result: AgentRunResult) -> dict[str, Any]:
    """Serialize one agent result for the run summary."""

    return {
        "agent_id": result.agent_id,
        "task_name": result.task_name,
        "run_index": result.run_index,
        "provider": result.provider,
        "model": result.model,
        "response_id": result.response_id,
        "status": result.status,
        "output_path": str(result.output_path),
        "usage": result.usage,
    }


def serialize_consensus_report(report: dict[str, Any]) -> dict[str, Any]:
    """Serialize one consensus report for the run summary."""

    return {
        "consensus_report_id": report.get("consensus_report_id"),
        "team_id": report.get("team_id"),
        "task_name": report.get("task_name"),
        "created_at": report.get("created_at"),
        "total_agents": report.get("total_agents"),
        "summary": report.get("summary", {}),
    }


def write_run_summary_json(
    *,
    summary: dict[str, Any],
    output_path: Path,
) -> None:
    """Write run summary as JSON."""

    output_path.parent.mkdir(parents=True, exist_ok=True)

    output_path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def write_run_summary_markdown(
    *,
    summary: dict[str, Any],
    output_path: Path,
) -> None:
    """Write run summary as Markdown."""

    output_path.parent.mkdir(parents=True, exist_ok=True)

    lines: list[str] = []

    lines.append("# Team Agentic Ingestion Run Summary")
    lines.append("")
    lines.append("## Run Metadata")
    lines.append("")
    lines.append(f"- Task ID: `{summary.get('task_id')}`")
    lines.append(f"- Recipe ID: `{summary.get('recipe_id')}`")
    lines.append(f"- Run ID: `{summary.get('run_id')}`")
    lines.append(f"- Run Directory: `{summary.get('run_dir')}`")
    lines.append(f"- Raw Input Path: `{summary.get('raw_input_path')}`")
    lines.append(f"- Report Output Path: `{summary.get('report_output_path')}`")
    lines.append(f"- Provider: `{summary.get('provider')}`")
    lines.append(f"- Model: `{summary.get('model')}`")
    lines.append(f"- Team Execution Mode: `{summary.get('team_execution_mode')}`")
    lines.append(f"- Created At: `{summary.get('created_at')}`")
    lines.append("")
    lines.append("## Agent Results")
    lines.append("")
    lines.append("| Agent ID | Task | Run | Provider | Model | Status | Output Artifact |")
    lines.append("|---|---|---:|---|---|---|---|")

    for result in summary.get("agent_results", []):
        lines.append(
            "| "
            f"{safe_cell(result.get('agent_id'))} | "
            f"{safe_cell(result.get('task_name'))} | "
            f"{result.get('run_index')} | "
            f"{safe_cell(result.get('provider'))} | "
            f"{safe_cell(result.get('model'))} | "
            f"{safe_cell(result.get('status'))} | "
            f"`{result.get('output_path')}` |"
        )

    lines.append("")
    lines.append("## Consensus Reports")
    lines.append("")
    lines.append("| Team ID | Task | Total Agents | Review Required | Full Agreement | Majority Agreement | Disagreement |")
    lines.append("|---|---|---:|---:|---:|---:|---:|")

    for report in summary.get("consensus_reports", []):
        report_summary = report.get("summary", {})
        disagreement = (
            int(report_summary.get("majority_with_disagreement", 0))
            + int(report_summary.get("minority_interpretation", 0))
            + int(report_summary.get("conflict", 0))
        )

        lines.append(
            "| "
            f"{safe_cell(report.get('team_id'))} | "
            f"{safe_cell(report.get('task_name'))} | "
            f"{report.get('total_agents')} | "
            f"{report_summary.get('review_required', 0)} | "
            f"{report_summary.get('full_agreement', 0)} | "
            f"{report_summary.get('majority_agreement', 0)} | "
            f"{disagreement} |"
        )

    output_path.write_text("\n".join(lines), encoding="utf-8")


def write_run_summaries(
    *,
    task_id: str,
    recipe_id: str,
    raw_input_path: Path,
    report_output_path: Path,
    run_id: str,
    run_dir: Path,
    provider: str,
    model: str,
    team_execution_mode: str,
    agent_results: list[AgentRunResult],
    consensus_reports: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build and write JSON and Markdown run summaries."""

    summary = build_run_summary(
        task_id=task_id,
        recipe_id=recipe_id,
        raw_input_path=raw_input_path,
        report_output_path=report_output_path,
        run_id=run_id,
        run_dir=run_dir,
        provider=provider,
        model=model,
        team_execution_mode=team_execution_mode,
        agent_results=agent_results,
        consensus_reports=consensus_reports,
    )

    write_run_summary_json(
        summary=summary,
        output_path=run_dir / "team_agentic_ingestion_run_summary.json",
    )

    write_run_summary_markdown(
        summary=summary,
        output_path=run_dir / "team_agentic_ingestion_run_summary.md",
    )

    return summary


def safe_cell(value: Any) -> str:
    """Sanitize Markdown table cell content."""

    return str(value or "").replace("|", "\\|").replace("\n", " ").strip()
