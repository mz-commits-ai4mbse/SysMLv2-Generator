"""Run the modular team-based agentic ingestion pipeline.

This script uses real LLM calls.

Cost-control default:
- one team member per team
- one run per member

Usage:
python scripts/run_team_agentic_ingestion_task.py

Optional:
python scripts/run_team_agentic_ingestion_task.py --model gpt-5-mini
python scripts/run_team_agentic_ingestion_task.py --model gpt-5.4-mini --max-members-per-team 1
python scripts/run_team_agentic_ingestion_task.py --model gpt-5.4-mini --max-members-per-team all
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from modules.ingestion.team_agentic_pipeline import run_team_agentic_ingestion


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run team-based agentic ingestion for TASK_001."
    )

    parser.add_argument(
        "--model",
        default="gpt-5.4-mini",
        help="OpenAI model to use. Example: gpt-5.4-mini, gpt-5-mini, gpt-4.1-mini",
    )

    parser.add_argument(
        "--max-members-per-team",
        default="1",
        help="Use 1 for cost-saving single-member mode, or all for all configured team members.",
    )

    parser.add_argument(
        "--runs-per-member",
        type=int,
        default=1,
        help="Number of runs per selected team member.",
    )

    return parser.parse_args()


def parse_max_members(value: str) -> int | None:
    normalized = value.strip().lower()

    if normalized == "all":
        return None

    return int(normalized)


def main() -> None:
    args = parse_args()

    max_members_per_team = parse_max_members(args.max_members_per_team)

    print("Starting team-based agentic ingestion.")
    print("")
    print("Configuration:")
    print(f"- Model: {args.model}")
    print(f"- Max members per team: {args.max_members_per_team}")
    print(f"- Runs per member: {args.runs_per_member}")
    print("")
    print("Note: This may take several minutes.")
    print("")

    result = run_team_agentic_ingestion(
        project_root=PROJECT_ROOT,
        task_id="TASK_001_INGEST_EXAMPLE_MODEL",
        recipe_id="REC_INGESTION_001",
        raw_input_path=PROJECT_ROOT / "legacy" / "raw" / "example_legacy_model_description.md",
        report_output_path=PROJECT_ROOT
        / "data"
        / "ingestion_reports"
        / "task_001_team_agentic_ingestion_report.md",
        provider="openai",
        model=args.model,
        api_key=None,
        runs_per_member=args.runs_per_member,
        max_members_per_team=max_members_per_team,
        dry_run=False,
    )

    print("Team agentic ingestion finished.")
    print("")
    print(f"Task ID: {result.task_id}")
    print(f"Run ID: {result.run_id}")
    print(f"Run directory: {result.run_dir}")
    print(f"Report path: {result.report_path}")
    print(f"Agent results: {len(result.agent_results)}")
    print(f"Consensus reports: {len(result.consensus_reports)}")
    print("")
    print("Agent outputs:")

    for agent_result in result.agent_results:
        print(
            f"- {agent_result.agent_id} | "
            f"{agent_result.task_name} | "
            f"run {agent_result.run_index} | "
            f"{agent_result.output_path}"
        )

    print("")
    print("Consensus summaries:")

    for consensus_report in result.consensus_reports:
        summary = consensus_report.get("summary", {})
        print(
            f"- {consensus_report.get('team_id')} | "
            f"groups={summary.get('total_groups', 0)} | "
            f"review_required={summary.get('review_required', 0)}"
        )


if __name__ == "__main__":
    main()
