"""Run the agentic ingestion pipeline for TASK_001.

Usage from project root:
python scripts/run_agentic_ingestion_task.py
"""

from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from modules.ingestion.agentic_ingestion import run_agentic_ingestion


def main() -> None:
    result = run_agentic_ingestion(
        project_root=PROJECT_ROOT,
        task_id="TASK_001_INGEST_EXAMPLE_MODEL",
        recipe_id="REC_INGESTION_001",
        raw_input_path=PROJECT_ROOT / "legacy" / "raw" / "example_legacy_model_description.md",
        report_output_path=PROJECT_ROOT / "data" / "ingestion_reports" / "task_001_ingestion_report_agentic.md",
        provider="openai",
        model="gpt-5.5",
        api_key=None,
        runs_per_agent=1,
    )

    print("Agentic ingestion finished.")
    print(f"Run ID: {result.run_id}")
    print(f"Run directory: {result.run_dir}")
    print(f"Report path: {result.report_path}")
    print("")
    print("Agent outputs:")

    for agent_result in result.agent_results:
        print(
            f"- {agent_result.agent_id} "
            f"run {agent_result.run_index}: "
            f"{agent_result.output_path}"
        )


if __name__ == "__main__":
    main()
