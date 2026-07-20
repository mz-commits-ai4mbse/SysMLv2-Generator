"""Dry-run test for the team runner.

This script does not call an LLM.
It only checks team loading, role/persona loading and artifact writing.

Usage:
python scripts/test_team_runner_dry_run.py
"""

from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from modules.agents.team_runner import run_agent_team


def main() -> None:
    output_dir = (
        PROJECT_ROOT
        / "data"
        / "team_runs"
        / "dry_run_legacy_interpretation"
    )

    results = run_agent_team(
        project_root=PROJECT_ROOT,
        team_file=PROJECT_ROOT / "teams" / "ingestion" / "legacy_interpretation_team.json",
        task_instructions="Dry-run only. Do not call an LLM.",
        input_text="Dummy input for dry-run team runner test.",
        output_dir=output_dir,
        provider="openai",
        model="dry-run-model",
        api_key=None,
        runs_per_member=1,
        max_members=None,
        include_alternative_members=False,
        dry_run=True,
    )

    print("Team dry-run finished.")
    print(f"Output directory: {output_dir}")
    print("")
    print("Team member outputs:")

    for result in results:
        print(f"- {result.agent_id}: {result.output_path}")


if __name__ == "__main__":
    main()
