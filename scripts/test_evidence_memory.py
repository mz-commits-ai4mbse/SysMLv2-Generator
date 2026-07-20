"""Create evidence memory from the latest existing team run."""

from __future__ import annotations

import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from modules.agents.types import AgentRunResult
from modules.ingestion.evidence_memory import build_evidence_memory


def load_agent_results(directory: Path) -> list[AgentRunResult]:
    results: list[AgentRunResult] = []

    for result_path in sorted(directory.rglob("*.json")):
        wrapper = json.loads(result_path.read_text(encoding="utf-8"))

        results.append(
            AgentRunResult(
                agent_id=wrapper.get("agent_id", "UNKNOWN_AGENT"),
                task_name=wrapper.get(
                    "task_name",
                    "Classify engineering evidence",
                ),
                run_index=int(wrapper.get("run_index", 1)),
                provider=wrapper.get("provider", ""),
                model=wrapper.get("model", ""),
                output_text=wrapper.get("output_text", ""),
                output_path=result_path,
                response_id=wrapper.get("response_id"),
                usage=wrapper.get("usage", {}),
                status=wrapper.get("status", ""),
            )
        )

    return results


def main() -> None:
    task_dir = (
        PROJECT_ROOT
        / "data"
        / "team_runs"
        / "TASK_001_INGEST_EXAMPLE_MODEL"
    )

    run_dirs = sorted(path for path in task_dir.iterdir() if path.is_dir())

    if not run_dirs:
        raise RuntimeError("No existing team run found.")

    run_dir = run_dirs[-1]

    evidence_dir = (
        run_dir
        / "agent_outputs"
        / "02_evidence_classification"
    )

    results = load_agent_results(evidence_dir)

    if not results:
        raise RuntimeError("No evidence agent outputs found.")

    consensus_paths = sorted(
        (
            run_dir
            / "consensus_reports"
            / "02_evidence_classification"
        ).glob("*_consensus.json")
    )

    consensus = (
        json.loads(consensus_paths[0].read_text(encoding="utf-8"))
        if consensus_paths
        else {"summary": {}, "consensus_report_id": None}
    )

    output_path = (
        run_dir
        / "memory"
        / "02_evidence_memory.json"
    )

    memory = build_evidence_memory(
        task_id="TASK_001_INGEST_EXAMPLE_MODEL",
        run_id=run_dir.name,
        raw_input_path=(
            PROJECT_ROOT
            / "legacy"
            / "raw"
            / "example_legacy_model_description.md"
        ),
        evidence_results=results,
        evidence_consensus=consensus,
        output_path=output_path,
    )

    payload = memory["payload"]

    print("Evidence memory created.")
    print(f"Output path: {output_path}")
    print(
        "Detected evidence:",
        len(payload.get("detected_evidence", [])),
    )
    print(
        "Rejected candidates:",
        len(payload.get("rejected_evidence_candidates", [])),
    )
    print(
        "Evidence gaps:",
        len(payload.get("evidence_gaps", [])),
    )


if __name__ == "__main__":
    main()
