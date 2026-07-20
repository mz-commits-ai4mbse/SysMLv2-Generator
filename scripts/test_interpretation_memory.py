"""Test interpretation-memory generation from an existing team run.

Usage:
python scripts/test_interpretation_memory.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from modules.agents.types import AgentRunResult
from modules.ingestion.interpretation_memory import (
    build_interpretation_memory,
)


def main() -> None:
    task_dir = (
        PROJECT_ROOT
        / "data"
        / "team_runs"
        / "TASK_001_INGEST_EXAMPLE_MODEL"
    )

    run_dirs = sorted(
        path
        for path in task_dir.iterdir()
        if path.is_dir()
    )

    if not run_dirs:
        raise RuntimeError("No existing team run found.")

    run_dir = run_dirs[-1]

    interpretation_dir = (
        run_dir
        / "agent_outputs"
        / "01_legacy_interpretation"
    )

    result_paths = sorted(
        interpretation_dir.rglob("*.json")
    )

    if not result_paths:
        raise RuntimeError(
            "No interpretation agent outputs found."
        )

    results: list[AgentRunResult] = []

    for index, result_path in enumerate(
        result_paths,
        start=1,
    ):
        wrapper = json.loads(
            result_path.read_text(encoding="utf-8")
        )

        results.append(
            AgentRunResult(
                agent_id=wrapper.get(
                    "agent_id",
                    f"UNKNOWN_AGENT_{index}",
                ),
                task_name=wrapper.get(
                    "task_name",
                    "Interpret raw legacy data",
                ),
                run_index=int(
                    wrapper.get("run_index", 1)
                ),
                provider=wrapper.get("provider", ""),
                model=wrapper.get("model", ""),
                output_text=wrapper.get("output_text", ""),
                output_path=result_path,
                response_id=wrapper.get("response_id"),
                usage=wrapper.get("usage", {}),
                status=wrapper.get("status", ""),
            )
        )

    consensus_paths = sorted(
        (
            run_dir
            / "consensus_reports"
            / "01_legacy_interpretation"
        ).glob("*_consensus.json")
    )

    if consensus_paths:
        consensus = json.loads(
            consensus_paths[0].read_text(
                encoding="utf-8"
            )
        )
    else:
        consensus = {
            "summary": {},
            "consensus_report_id": None,
        }

    output_path = (
        run_dir
        / "memory"
        / "01_interpretation_memory.json"
    )

    memory = build_interpretation_memory(
        task_id="TASK_001_INGEST_EXAMPLE_MODEL",
        run_id=run_dir.name,
        raw_input_path=(
            PROJECT_ROOT
            / "legacy"
            / "raw"
            / "example_legacy_model_description.md"
        ),
        interpretation_results=results,
        interpretation_consensus=consensus,
        output_path=output_path,
    )

    payload = memory["payload"]

    print("Interpretation memory created.")
    print(f"Run directory: {run_dir}")
    print(f"Output path: {output_path}")
    print(
        "Source information:",
        len(payload.get("source_information", [])),
    )
    print(
        "Assumptions:",
        len(payload.get("assumptions", [])),
    )
    print(
        "Ambiguities:",
        len(payload.get("ambiguities", [])),
    )


if __name__ == "__main__":
    main()
