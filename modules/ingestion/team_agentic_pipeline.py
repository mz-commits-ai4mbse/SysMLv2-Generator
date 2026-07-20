"""Team-based agentic ingestion pipeline.

This module orchestrates team execution and consensus analysis.

It does not contain task instructions.
It does not build detailed input text itself.
It does not implement consensus logic itself.
It does not implement LLM provider logic itself.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from modules.agents.team_config import load_team_config
from modules.agents.team_runner import run_agent_team
from modules.agents.types import AgentRunResult
from modules.consensus.analyzer import (
    analyze_consensus,
    write_consensus_json,
    write_consensus_markdown,
)
from modules.ingestion.agent_inputs import (
    build_completeness_review_input,
    build_derivation_assessment_input,
    build_evidence_classification_input,
    build_initial_interpretation_input,
)
from modules.ingestion.agent_tasks import (
    get_completeness_checker_task_instructions,
    get_derivation_assessor_task_instructions,
    get_evidence_classifier_task_instructions,
    get_interpreter_task_instructions,
)
from modules.ingestion.run_summary import write_run_summaries
from modules.ingestion.review_report import write_ingestion_review_report


@dataclass
class TeamAgenticIngestionResult:
    """Final result of a team-based agentic ingestion run."""

    task_id: str
    run_id: str
    run_dir: Path
    report_path: Path
    agent_results: list[AgentRunResult]
    consensus_reports: list[dict[str, Any]]
    run_summary: dict[str, Any]


def run_team_agentic_ingestion(
    *,
    project_root: Path,
    task_id: str,
    recipe_id: str,
    raw_input_path: Path,
    report_output_path: Path,
    provider: str = "openai",
    model: str = "gpt-5.4-mini",
    api_key: str | None = None,
    runs_per_member: int = 1,
    max_members_per_team: int | None = 1,
    dry_run: bool = False,
) -> TeamAgenticIngestionResult:
    """Run the modular team-based agentic ingestion pipeline.

    By default max_members_per_team is 1 to avoid accidental high-cost runs.
    Set max_members_per_team=None to run all configured team members.
    """

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = project_root / "data" / "team_runs" / task_id / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    raw_text = raw_input_path.read_text(encoding="utf-8")

    recipe_text = read_optional_file(
        project_root / "recipes" / "ingestion" / "create_ingestion_artifact.recipe.md"
    )

    derivation_rules_text = read_optional_file(
        project_root / "context" / "mapping" / "sysml_model_derivation_rules.json"
    )

    global_principles_text = read_optional_file(
        project_root / "context" / "global" / "project_principles.md"
    )

    team_files = get_ingestion_team_files(project_root)

    all_agent_results: list[AgentRunResult] = []
    consensus_reports: list[dict[str, Any]] = []

    team_execution_mode = get_team_execution_mode(
        dry_run=dry_run,
        max_members_per_team=max_members_per_team,
    )

    interpretation_results, interpretation_consensus = run_stage_with_consensus(
        project_root=project_root,
        run_dir=run_dir,
        stage_name="01_legacy_interpretation",
        team_file=team_files["legacy_interpretation"],
        task_instructions=get_interpreter_task_instructions(),
        input_text=build_initial_interpretation_input(
            task_id=task_id,
            recipe_id=recipe_id,
            raw_input_path=raw_input_path,
            raw_text=raw_text,
            recipe_text=recipe_text,
            global_principles_text=global_principles_text,
        ),
        provider=provider,
        model=model,
        api_key=api_key,
        runs_per_member=runs_per_member,
        max_members_per_team=max_members_per_team,
        dry_run=dry_run,
    )
    all_agent_results.extend(interpretation_results)
    consensus_reports.append(interpretation_consensus)

    evidence_results, evidence_consensus = run_stage_with_consensus(
        project_root=project_root,
        run_dir=run_dir,
        stage_name="02_evidence_classification",
        team_file=team_files["evidence_classification"],
        task_instructions=get_evidence_classifier_task_instructions(),
        input_text=build_evidence_classification_input(
            task_id=task_id,
            raw_input_path=raw_input_path,
            raw_text=raw_text,
            interpretation_results=interpretation_results,
            interpretation_consensus=interpretation_consensus,
        ),
        provider=provider,
        model=model,
        api_key=api_key,
        runs_per_member=runs_per_member,
        max_members_per_team=max_members_per_team,
        dry_run=dry_run,
    )
    all_agent_results.extend(evidence_results)
    consensus_reports.append(evidence_consensus)

    derivation_results, derivation_consensus = run_stage_with_consensus(
        project_root=project_root,
        run_dir=run_dir,
        stage_name="03_derivation_assessment",
        team_file=team_files["derivation_assessment"],
        task_instructions=get_derivation_assessor_task_instructions(
            derivation_rules_text=derivation_rules_text
        ),
        input_text=build_derivation_assessment_input(
            task_id=task_id,
            raw_input_path=raw_input_path,
            raw_text=raw_text,
            evidence_results=evidence_results,
            evidence_consensus=evidence_consensus,
            derivation_rules_text=derivation_rules_text,
        ),
        provider=provider,
        model=model,
        api_key=api_key,
        runs_per_member=runs_per_member,
        max_members_per_team=max_members_per_team,
        dry_run=dry_run,
    )
    all_agent_results.extend(derivation_results)
    consensus_reports.append(derivation_consensus)

    completeness_results, completeness_consensus = run_stage_with_consensus(
        project_root=project_root,
        run_dir=run_dir,
        stage_name="04_completeness_review",
        team_file=team_files["completeness_review"],
        task_instructions=get_completeness_checker_task_instructions(),
        input_text=build_completeness_review_input(
            task_id=task_id,
            raw_input_path=raw_input_path,
            raw_text=raw_text,
            interpretation_results=interpretation_results,
            evidence_results=evidence_results,
            derivation_results=derivation_results,
            interpretation_consensus=interpretation_consensus,
            evidence_consensus=evidence_consensus,
            derivation_consensus=derivation_consensus,
        ),
        provider=provider,
        model=model,
        api_key=api_key,
        runs_per_member=runs_per_member,
        max_members_per_team=max_members_per_team,
        dry_run=dry_run,
    )
    all_agent_results.extend(completeness_results)
    consensus_reports.append(completeness_consensus)

    write_ingestion_review_report(
        task_id=task_id,
        recipe_id=recipe_id,
        raw_input_path=raw_input_path,
        run_id=run_id,
        run_dir=run_dir,
        report_output_path=report_output_path,
        derivation_results=derivation_results,
        completeness_results=completeness_results,
        consensus_reports=consensus_reports,
        narrative_report_path=None,
    )

    run_summary = write_run_summaries(
        task_id=task_id,
        recipe_id=recipe_id,
        raw_input_path=raw_input_path,
        report_output_path=report_output_path,
        run_id=run_id,
        run_dir=run_dir,
        provider=provider,
        model=model,
        team_execution_mode=team_execution_mode,
        agent_results=all_agent_results,
        consensus_reports=consensus_reports,
    )

    return TeamAgenticIngestionResult(
        task_id=task_id,
        run_id=run_id,
        run_dir=run_dir,
        report_path=report_output_path,
        agent_results=all_agent_results,
        consensus_reports=consensus_reports,
        run_summary=run_summary,
    )


def run_stage_with_consensus(
    *,
    project_root: Path,
    run_dir: Path,
    stage_name: str,
    team_file: Path,
    task_instructions: str,
    input_text: str,
    provider: str,
    model: str,
    api_key: str | None,
    runs_per_member: int,
    max_members_per_team: int | None,
    dry_run: bool,
) -> tuple[list[AgentRunResult], dict[str, Any]]:
    """Run one team stage and create consensus reports."""

    team_config = load_team_config(
        project_root=project_root,
        team_file=team_file,
    )

    stage_output_dir = run_dir / "agent_outputs" / stage_name

    agent_results = run_agent_team(
        project_root=project_root,
        team_file=team_file,
        task_instructions=task_instructions,
        input_text=input_text,
        output_dir=stage_output_dir,
        provider=provider,
        model=model,
        api_key=api_key,
        runs_per_member=runs_per_member,
        max_members=max_members_per_team,
        include_alternative_members=False,
        dry_run=dry_run,
    )

    agent_payloads = load_agent_payloads_from_results(agent_results)

    consensus_report = analyze_consensus(
        team_id=team_config.team_id,
        task_name=team_config.task_name,
        agent_payloads=agent_payloads,
    )

    write_stage_consensus_reports(
        run_dir=run_dir,
        stage_name=stage_name,
        team_id=team_config.team_id,
        consensus_report=consensus_report,
    )

    return agent_results, consensus_report


def load_agent_payloads_from_results(
    agent_results: list[AgentRunResult],
) -> list[dict[str, Any]]:
    """Load JSON payloads written by team member runs."""

    payloads: list[dict[str, Any]] = []

    for result in agent_results:
        with result.output_path.open("r", encoding="utf-8") as file:
            payload = json.load(file)

        payload["_artifact_path"] = str(result.output_path)
        payloads.append(payload)

    return payloads


def write_stage_consensus_reports(
    *,
    run_dir: Path,
    stage_name: str,
    team_id: str,
    consensus_report: dict[str, Any],
) -> None:
    """Write JSON and Markdown consensus reports for one stage."""

    consensus_dir = run_dir / "consensus_reports" / stage_name
    base_name = safe_filename(team_id)

    write_consensus_json(
        consensus_report,
        consensus_dir / f"{base_name}_consensus.json",
    )

    write_consensus_markdown(
        consensus_report,
        consensus_dir / f"{base_name}_consensus.md",
    )


def build_preliminary_run_summary_text(
    *,
    task_id: str,
    recipe_id: str,
    run_id: str,
    run_dir: Path,
    provider: str,
    model: str,
    team_execution_mode: str,
    agent_results: list[AgentRunResult],
    consensus_reports: list[dict[str, Any]],
) -> str:
    """Create a simple text summary before the final run summary is written."""

    lines: list[str] = []

    lines.append("# Preliminary Team Agentic Ingestion Run Summary")
    lines.append("")
    lines.append(f"- Task ID: {task_id}")
    lines.append(f"- Recipe ID: {recipe_id}")
    lines.append(f"- Run ID: {run_id}")
    lines.append(f"- Run Directory: {run_dir}")
    lines.append(f"- Provider: {provider}")
    lines.append(f"- Model: {model}")
    lines.append(f"- Team Execution Mode: {team_execution_mode}")
    lines.append(f"- Agent Results So Far: {len(agent_results)}")
    lines.append(f"- Consensus Reports So Far: {len(consensus_reports)}")
    lines.append("")
    lines.append("## Consensus Summary")
    lines.append("")

    for report in consensus_reports:
        summary = report.get("summary", {})
        lines.append(f"### {report.get('team_id')}")
        lines.append(f"- Task: {report.get('task_name')}")
        lines.append(f"- Total Agents: {report.get('total_agents')}")
        lines.append(f"- Full Agreement: {summary.get('full_agreement', 0)}")
        lines.append(f"- Majority Agreement: {summary.get('majority_agreement', 0)}")
        lines.append(f"- Review Required: {summary.get('review_required', 0)}")
        lines.append("")

    return "\n".join(lines)


def get_ingestion_team_files(project_root: Path) -> dict[str, Path]:
    """Return configured ingestion team files."""

    ingestion_team_dir = project_root / "teams" / "ingestion"

    return {
        "legacy_interpretation": ingestion_team_dir / "legacy_interpretation_team.json",
        "evidence_classification": ingestion_team_dir / "evidence_classification_team.json",
        "derivation_assessment": ingestion_team_dir / "derivation_assessment_team.json",
        "completeness_review": ingestion_team_dir / "completeness_review_team.json",
        "report_composition": ingestion_team_dir / "report_composition_team.json",
    }


def get_team_execution_mode(
    *,
    dry_run: bool,
    max_members_per_team: int | None,
) -> str:
    """Describe team execution mode for summaries."""

    if dry_run:
        prefix = "dry_run"
    else:
        prefix = "llm"

    if max_members_per_team == 1:
        return f"{prefix}_single_member_per_team"

    if max_members_per_team is None:
        return f"{prefix}_all_configured_team_members"

    return f"{prefix}_max_{max_members_per_team}_members_per_team"


def read_optional_file(path: Path) -> str:
    """Read a file if it exists, otherwise return a diagnostic string."""

    if not path.exists():
        return f"File not found: {path}"

    return path.read_text(encoding="utf-8")


def safe_filename(value: str) -> str:
    """Create a filesystem-safe lowercase filename fragment."""

    cleaned = value.lower().replace(" ", "_").replace("-", "_")
    return "".join(char for char in cleaned if char.isalnum() or char == "_")
