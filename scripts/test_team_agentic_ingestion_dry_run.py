"""Dry-run test for the modular team-based agentic ingestion pipeline.

This script does not call an LLM.

It tests:
- team loading
- role/persona loading
- staged team execution
- consensus report writing
- run summary writing
- final report artifact writing

Usage:
python scripts/test_team_agentic_ingestion_dry_run.py
"""

from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from modules.ingestion.team_agentic_pipeline import run_team_agentic_ingestion


def main() -> None:
    result = run_team_agentic_ingestion(
        project_root=PROJECT_ROOT,
        task_id="TASK_001_INGEST_EXAMPLE_MODEL",
        recipe_id="REC_INGESTION_001",
        raw_input_path=PROJECT_ROOT / "legacy" / "raw" / "example_legacy_model_description.md",
        report_output_path=PROJECT_ROOT
        / "data"
        / "ingestion_reports"
        / "task_001_team_agentic_ingestion_report_dry_run.md",
        provider="openai",
        model="dry-run-model",
        api_key=None,
        runs_per_member=1,
        max_members_per_team=None,
        dry_run=True,
    )

    print("Team agentic ingestion dry-run finished.")
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
