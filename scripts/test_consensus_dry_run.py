"""Dry-run test for consensus analysis.

This script does not call an LLM.
It compares the dry-run team artifacts created by test_team_runner_dry_run.py.

Usage:
python scripts/test_consensus_dry_run.py
"""

from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from modules.consensus.analyzer import (
    analyze_consensus,
    load_agent_payloads_from_directory,
    write_consensus_json,
    write_consensus_markdown,
)


def main() -> None:
    input_dir = (
        PROJECT_ROOT
        / "data"
        / "team_runs"
        / "dry_run_legacy_interpretation"
    )

    json_output_path = (
        PROJECT_ROOT
        / "data"
        / "consensus_reports"
        / "dry_run_legacy_interpretation_consensus.json"
    )

    markdown_output_path = (
        PROJECT_ROOT
        / "data"
        / "consensus_reports"
        / "dry_run_legacy_interpretation_consensus.md"
    )

    agent_payloads = load_agent_payloads_from_directory(input_dir)

    report = analyze_consensus(
        team_id="TEAM_LEGACY_INTERPRETATION",
        task_name="Interpret raw legacy data",
        agent_payloads=agent_payloads,
    )

    write_consensus_json(report, json_output_path)
    write_consensus_markdown(report, markdown_output_path)

    print("Consensus dry-run finished.")
    print(f"Input directory: {input_dir}")
    print(f"JSON report: {json_output_path}")
    print(f"Markdown report: {markdown_output_path}")
    print("")
    print("Summary:")

    for key, value in report["summary"].items():
        print(f"- {key}: {value}")


if __name__ == "__main__":
    main()
