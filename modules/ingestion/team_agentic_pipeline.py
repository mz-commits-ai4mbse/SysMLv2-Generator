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
    build_source_anchored_completeness_review_input,
    build_source_anchored_derivation_assessment_input,
    build_source_anchored_evidence_classification_input,
    build_source_anchored_initial_interpretation_input,
)
from modules.ingestion.agent_tasks import (
    get_completeness_checker_task_instructions,
    get_derivation_assessor_task_instructions,
    get_evidence_classifier_task_instructions,
    get_interpreter_task_instructions,
)
from modules.ingestion.run_summary import write_run_summaries
from modules.ingestion.review_report import write_ingestion_review_report
from modules.source_analysis_units.types import SourceAnalysisUnit


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
    source_analysis_unit_ids: tuple[str, ...] = ()


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
    execution_root: Path | None = None,
    source_analysis_units: tuple[SourceAnalysisUnit, ...] | None = None,
) -> TeamAgenticIngestionResult:
    """Run the modular team-based agentic ingestion pipeline.

    By default max_members_per_team is 1 to avoid accidental high-cost runs.
    Set max_members_per_team=None to run all configured team members.
    """

    project_root = Path(project_root).resolve()
    resolved_raw_input_path = _resolve_pipeline_path(
        project_root,
        raw_input_path,
    )
    resolved_report_output_path = _resolve_pipeline_path(
        project_root,
        report_output_path,
    )

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = _resolve_pipeline_run_directory(
        project_root=project_root,
        task_id=task_id,
        run_id=run_id,
        execution_root=execution_root,
    )
    run_dir.mkdir(parents=True, exist_ok=True)

    raw_text = resolved_raw_input_path.read_text(encoding="utf-8")

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

    if source_analysis_units is not None:
        return _run_source_anchored_ingestion(
            project_root=project_root,
            task_id=task_id,
            recipe_id=recipe_id,
            resolved_raw_input_path=resolved_raw_input_path,
            resolved_report_output_path=(
                resolved_report_output_path
            ),
            run_id=run_id,
            run_dir=run_dir,
            raw_text=raw_text,
            recipe_text=recipe_text,
            derivation_rules_text=derivation_rules_text,
            global_principles_text=global_principles_text,
            team_files=team_files,
            provider=provider,
            model=model,
            api_key=api_key,
            runs_per_member=runs_per_member,
            max_members_per_team=max_members_per_team,
            dry_run=dry_run,
            team_execution_mode=team_execution_mode,
            source_analysis_units=source_analysis_units,
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
            raw_input_path=resolved_raw_input_path,
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
            raw_input_path=resolved_raw_input_path,
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
            raw_input_path=resolved_raw_input_path,
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
            raw_input_path=resolved_raw_input_path,
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
        raw_input_path=resolved_raw_input_path,
        run_id=run_id,
        run_dir=run_dir,
        report_output_path=resolved_report_output_path,
        derivation_results=derivation_results,
        completeness_results=completeness_results,
        consensus_reports=consensus_reports,
        narrative_report_path=None,
    )

    run_summary = write_run_summaries(
        task_id=task_id,
        recipe_id=recipe_id,
        raw_input_path=resolved_raw_input_path,
        report_output_path=resolved_report_output_path,
        run_id=run_id,
        run_dir=run_dir,
        provider=provider,
        model=model,
        team_execution_mode=team_execution_mode,
        agent_results=all_agent_results,
        consensus_reports=consensus_reports,
        repository_root=project_root,
    )

    return TeamAgenticIngestionResult(
        task_id=task_id,
        run_id=run_id,
        run_dir=run_dir,
        report_path=resolved_report_output_path,
        agent_results=all_agent_results,
        consensus_reports=consensus_reports,
        run_summary=run_summary,
    )



def _run_source_anchored_ingestion(
    *,
    project_root: Path,
    task_id: str,
    recipe_id: str,
    resolved_raw_input_path: Path,
    resolved_report_output_path: Path,
    run_id: str,
    run_dir: Path,
    raw_text: str,
    recipe_text: str,
    derivation_rules_text: str,
    global_principles_text: str,
    team_files: dict[str, Path],
    provider: str,
    model: str,
    api_key: str | None,
    runs_per_member: int,
    max_members_per_team: int | None,
    dry_run: bool,
    team_execution_mode: str,
    source_analysis_units: tuple[SourceAnalysisUnit, ...],
) -> TeamAgenticIngestionResult:
    """Run semantic Phase-F stages with one immutable source scope at a time."""

    units = _validated_source_analysis_units(
        source_analysis_units
    )
    all_agent_results: list[AgentRunResult] = []
    consensus_reports: list[dict[str, Any]] = []
    interpretation_results: list[AgentRunResult] = []
    evidence_results: list[AgentRunResult] = []
    derivation_results: list[AgentRunResult] = []
    interpretation_consensus_by_unit: list[
        dict[str, Any]
    ] = []
    evidence_consensus_by_unit: list[
        dict[str, Any]
    ] = []
    derivation_consensus_by_unit: list[
        dict[str, Any]
    ] = []

    for unit in units:
        unit_id = unit.source_analysis_unit_id

        unit_interpretation_results, unit_interpretation_consensus = (
            run_stage_with_consensus(
                project_root=project_root,
                run_dir=run_dir,
                stage_name="01_legacy_interpretation",
                team_file=team_files["legacy_interpretation"],
                task_instructions=(
                    get_interpreter_task_instructions()
                ),
                input_text=(
                    build_source_anchored_initial_interpretation_input(
                        source_analysis_unit=unit,
                        task_id=task_id,
                        recipe_id=recipe_id,
                        raw_input_path=resolved_raw_input_path,
                        recipe_text=recipe_text,
                        global_principles_text=(
                            global_principles_text
                        ),
                    )
                ),
                provider=provider,
                model=model,
                api_key=api_key,
                runs_per_member=runs_per_member,
                max_members_per_team=max_members_per_team,
                dry_run=dry_run,
                source_analysis_unit_id=unit_id,
            )
        )
        interpretation_results.extend(
            unit_interpretation_results
        )
        all_agent_results.extend(unit_interpretation_results)
        interpretation_consensus_by_unit.append(
            unit_interpretation_consensus
        )
        consensus_reports.append(unit_interpretation_consensus)

        unit_evidence_results, unit_evidence_consensus = (
            run_stage_with_consensus(
                project_root=project_root,
                run_dir=run_dir,
                stage_name="02_evidence_classification",
                team_file=team_files["evidence_classification"],
                task_instructions=(
                    get_evidence_classifier_task_instructions()
                ),
                input_text=(
                    build_source_anchored_evidence_classification_input(
                        source_analysis_unit=unit,
                        task_id=task_id,
                        raw_input_path=resolved_raw_input_path,
                        interpretation_results=(
                            unit_interpretation_results
                        ),
                        interpretation_consensus=(
                            unit_interpretation_consensus
                        ),
                    )
                ),
                provider=provider,
                model=model,
                api_key=api_key,
                runs_per_member=runs_per_member,
                max_members_per_team=max_members_per_team,
                dry_run=dry_run,
                source_analysis_unit_id=unit_id,
            )
        )
        evidence_results.extend(unit_evidence_results)
        all_agent_results.extend(unit_evidence_results)
        evidence_consensus_by_unit.append(
            unit_evidence_consensus
        )
        consensus_reports.append(unit_evidence_consensus)

        unit_derivation_results, unit_derivation_consensus = (
            run_stage_with_consensus(
                project_root=project_root,
                run_dir=run_dir,
                stage_name="03_derivation_assessment",
                team_file=team_files["derivation_assessment"],
                task_instructions=(
                    get_derivation_assessor_task_instructions(
                        derivation_rules_text=(
                            derivation_rules_text
                        )
                    )
                ),
                input_text=(
                    build_source_anchored_derivation_assessment_input(
                        source_analysis_unit=unit,
                        task_id=task_id,
                        raw_input_path=resolved_raw_input_path,
                        evidence_results=unit_evidence_results,
                        evidence_consensus=unit_evidence_consensus,
                        derivation_rules_text=(
                            derivation_rules_text
                        ),
                    )
                ),
                provider=provider,
                model=model,
                api_key=api_key,
                runs_per_member=runs_per_member,
                max_members_per_team=max_members_per_team,
                dry_run=dry_run,
                source_analysis_unit_id=unit_id,
            )
        )
        derivation_results.extend(unit_derivation_results)
        all_agent_results.extend(unit_derivation_results)
        derivation_consensus_by_unit.append(
            unit_derivation_consensus
        )
        consensus_reports.append(unit_derivation_consensus)

    # Completeness review is intentionally compiled once after all source
    # analysis units. It does not create engineering proposals and therefore
    # remains a source-wide review step rather than a per-unit semantic vote.
    completeness_results, completeness_consensus = (
        run_stage_with_consensus(
            project_root=project_root,
            run_dir=run_dir,
            stage_name="04_completeness_review",
            team_file=team_files["completeness_review"],
            task_instructions=(
                get_completeness_checker_task_instructions()
            ),
            input_text=build_source_anchored_completeness_review_input(
                task_id=task_id,
                raw_input_path=resolved_raw_input_path,
                raw_text=raw_text,
                source_analysis_unit_count=len(
                    source_analysis_units
                ),
                interpretation_run_count=len(
                    interpretation_results
                ),
                evidence_run_count=len(evidence_results),
                derivation_run_count=len(derivation_results),
                interpretation_consensus=(
                    _source_anchored_consensus_bundle(
                        "01_legacy_interpretation",
                        interpretation_consensus_by_unit,
                    )
                ),
                evidence_consensus=(
                    _source_anchored_consensus_bundle(
                        "02_evidence_classification",
                        evidence_consensus_by_unit,
                    )
                ),
                derivation_consensus=(
                    _source_anchored_consensus_bundle(
                        "03_derivation_assessment",
                        derivation_consensus_by_unit,
                    )
                ),
            ),
            provider=provider,
            model=model,
            api_key=api_key,
            runs_per_member=runs_per_member,
            max_members_per_team=max_members_per_team,
            dry_run=dry_run,
        )
    )
    all_agent_results.extend(completeness_results)
    consensus_reports.append(completeness_consensus)

    write_ingestion_review_report(
        task_id=task_id,
        recipe_id=recipe_id,
        raw_input_path=resolved_raw_input_path,
        run_id=run_id,
        run_dir=run_dir,
        report_output_path=resolved_report_output_path,
        derivation_results=derivation_results,
        completeness_results=completeness_results,
        consensus_reports=consensus_reports,
        narrative_report_path=None,
    )

    run_summary = write_run_summaries(
        task_id=task_id,
        recipe_id=recipe_id,
        raw_input_path=resolved_raw_input_path,
        report_output_path=resolved_report_output_path,
        run_id=run_id,
        run_dir=run_dir,
        provider=provider,
        model=model,
        team_execution_mode=team_execution_mode,
        agent_results=all_agent_results,
        consensus_reports=consensus_reports,
        repository_root=project_root,
    )

    return TeamAgenticIngestionResult(
        task_id=task_id,
        run_id=run_id,
        run_dir=run_dir,
        report_path=resolved_report_output_path,
        agent_results=all_agent_results,
        consensus_reports=consensus_reports,
        run_summary=run_summary,
        source_analysis_unit_ids=tuple(
            unit.source_analysis_unit_id for unit in units
        ),
    )


def _validated_source_analysis_units(
    source_analysis_units: tuple[SourceAnalysisUnit, ...],
) -> tuple[SourceAnalysisUnit, ...]:
    if not isinstance(source_analysis_units, tuple):
        raise ValueError("source_analysis_units must be a tuple.")
    if not source_analysis_units:
        raise ValueError(
            "source_analysis_units must contain at least one unit."
        )
    if not all(
        isinstance(unit, SourceAnalysisUnit)
        for unit in source_analysis_units
    ):
        raise ValueError(
            "source_analysis_units must contain SourceAnalysisUnit instances."
        )

    ordered = tuple(
        sorted(
            source_analysis_units,
            key=lambda unit: unit.source_order_index,
        )
    )
    ids = tuple(
        unit.source_analysis_unit_id for unit in ordered
    )
    if len(ids) != len(set(ids)):
        raise ValueError(
            "source_analysis_unit_id values must be unique."
        )
    orders = tuple(unit.source_order_index for unit in ordered)
    if len(orders) != len(set(orders)):
        raise ValueError(
            "source_order_index values must be unique."
        )

    reference = ordered[0]
    for unit in ordered[1:]:
        if (
            unit.project_id != reference.project_id
            or unit.source_id != reference.source_id
            or unit.source_projection_id
            != reference.source_projection_id
            or unit.source_projection_fingerprint
            != reference.source_projection_fingerprint
        ):
            raise ValueError(
                "All Source Analysis Units in one Phase-F execution "
                "must belong to the same Project, Source and Source Projection."
            )

    return ordered


def _source_anchored_consensus_bundle(
    stage_name: str,
    reports: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "source_anchored": True,
        "stage_name": stage_name,
        "source_analysis_unit_count": len(reports),
        "unit_consensus_reports": reports,
    }

def _resolve_pipeline_path(
    project_root: Path,
    path: Path,
) -> Path:
    """Resolve one absolute or repository-relative pipeline path."""

    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = project_root / candidate

    return candidate.resolve()


def _resolve_pipeline_run_directory(
    *,
    project_root: Path,
    task_id: str,
    run_id: str,
    execution_root: Path | None,
) -> Path:
    """Resolve default Phase-F or explicit project-bound execution."""

    if execution_root is None:
        return (
            project_root
            / "data"
            / "team_runs"
            / task_id
            / run_id
        )

    resolved = _resolve_pipeline_path(
        project_root,
        execution_root,
    )

    try:
        resolved.relative_to(project_root)
    except ValueError as exc:
        raise ValueError(
            "execution_root must remain inside project_root."
        ) from exc

    if resolved.is_symlink():
        raise ValueError(
            "Symbolic-link execution roots are rejected."
        )

    if resolved.exists() and not resolved.is_dir():
        raise ValueError(
            "execution_root must be a directory path."
        )

    return resolved


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
    source_analysis_unit_id: str | None = None,
) -> tuple[list[AgentRunResult], dict[str, Any]]:
    """Run one team stage and create consensus reports."""

    team_config = load_team_config(
        project_root=project_root,
        team_file=team_file,
    )

    stage_output_dir = run_dir / "agent_outputs" / stage_name
    if source_analysis_unit_id is not None:
        stage_output_dir = (
            stage_output_dir / source_analysis_unit_id
        )

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
        source_analysis_unit_id=source_analysis_unit_id,
    )

    agent_payloads = load_agent_payloads_from_results(agent_results)

    consensus_report = analyze_consensus(
        team_id=team_config.team_id,
        task_name=team_config.task_name,
        agent_payloads=agent_payloads,
    )
    if source_analysis_unit_id is not None:
        consensus_report = dict(consensus_report)
        consensus_report["source_analysis_unit_id"] = (
            source_analysis_unit_id
        )

    write_stage_consensus_reports(
        run_dir=run_dir,
        stage_name=stage_name,
        team_id=team_config.team_id,
        consensus_report=consensus_report,
        source_analysis_unit_id=source_analysis_unit_id,
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
    source_analysis_unit_id: str | None = None,
) -> None:
    """Write JSON and Markdown consensus reports for one stage."""

    consensus_dir = run_dir / "consensus_reports" / stage_name
    if source_analysis_unit_id is not None:
        consensus_dir = (
            consensus_dir / source_analysis_unit_id
        )
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
