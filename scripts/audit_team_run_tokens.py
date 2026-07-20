"""Audit prompt sizes and API usage of the latest team-ingestion run.

Usage:
python scripts/audit_team_run_tokens.py

Optional:
python scripts/audit_team_run_tokens.py /path/to/run_directory
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TASK_DIR = (
    PROJECT_ROOT
    / "data"
    / "team_runs"
    / "TASK_001_INGEST_EXAMPLE_MODEL"
)


def resolve_run_dir() -> Path:
    if len(sys.argv) > 1:
        run_dir = Path(sys.argv[1]).expanduser().resolve()

        if not run_dir.exists():
            raise RuntimeError(f"Run directory does not exist: {run_dir}")

        return run_dir

    run_dirs = sorted(
        (path for path in TASK_DIR.iterdir() if path.is_dir()),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )

    if not run_dirs:
        raise RuntimeError(f"No run directories found below {TASK_DIR}")

    return run_dirs[0]


def get_usage_value(
    usage: dict[str, Any],
    *keys: str,
) -> int | None:
    for key in keys:
        value = usage.get(key)

        if isinstance(value, int):
            return value

    return None


def stage_from_path(path: Path) -> str:
    parts = path.parts

    try:
        index = parts.index("agent_outputs")
        return parts[index + 1]
    except (ValueError, IndexError):
        return "unknown_stage"


def main() -> None:
    run_dir = resolve_run_dir()

    output_files = sorted(
        (run_dir / "agent_outputs").rglob("*.json")
    )

    if not output_files:
        raise RuntimeError(
            f"No agent output artifacts found in {run_dir}"
        )

    rows: list[dict[str, Any]] = []

    for path in output_files:
        payload = json.loads(path.read_text(encoding="utf-8"))
        metrics = payload.get("prompt_metrics", {})
        usage = payload.get("usage", {})

        rows.append(
            {
                "stage": stage_from_path(path),
                "agent_id": payload.get("agent_id", ""),
                "persona_id": payload.get("persona_id", ""),
                "estimated_input_tokens": metrics.get(
                    "estimated_input_tokens"
                ),
                "input_characters": metrics.get(
                    "input_characters"
                ),
                "instruction_characters": metrics.get(
                    "instruction_characters"
                ),
                "actual_input_tokens": get_usage_value(
                    usage,
                    "input_tokens",
                    "prompt_tokens",
                ),
                "actual_output_tokens": get_usage_value(
                    usage,
                    "output_tokens",
                    "completion_tokens",
                ),
                "total_tokens": get_usage_value(
                    usage,
                    "total_tokens",
                ),
                "artifact": str(path.relative_to(run_dir)),
            }
        )

    print("")
    print("Team Run Token Audit")
    print("=" * 120)
    print(f"Run directory: {run_dir}")
    print("")

    header = (
        f"{'Stage':34} "
        f"{'Agent':48} "
        f"{'Est. input':>12} "
        f"{'Actual input':>13} "
        f"{'Output':>9}"
    )

    print(header)
    print("-" * len(header))

    for row in rows:
        print(
            f"{str(row['stage'])[:33]:34} "
            f"{str(row['agent_id'])[:47]:48} "
            f"{str(row['estimated_input_tokens'] or ''):>12} "
            f"{str(row['actual_input_tokens'] or ''):>13} "
            f"{str(row['actual_output_tokens'] or ''):>9}"
        )

    estimated_total = sum(
        int(row["estimated_input_tokens"] or 0)
        for row in rows
    )

    actual_input_total = sum(
        int(row["actual_input_tokens"] or 0)
        for row in rows
    )

    actual_output_total = sum(
        int(row["actual_output_tokens"] or 0)
        for row in rows
    )

    print("")
    print("Totals")
    print("-" * 60)
    print(f"Agent runs:                  {len(rows)}")
    print(f"Estimated input tokens:      {estimated_total}")
    print(f"Reported actual input:       {actual_input_total}")
    print(f"Reported actual output:      {actual_output_total}")
    print("")

    stage_totals: dict[str, int] = {}

    for row in rows:
        stage = str(row["stage"])
        stage_totals[stage] = stage_totals.get(stage, 0) + int(
            row["actual_input_tokens"]
            or row["estimated_input_tokens"]
            or 0
        )

    print("Input by stage")
    print("-" * 60)

    for stage, total in sorted(stage_totals.items()):
        print(f"{stage:40} {total:>12}")

    print("")
    print("Interpretation:")
    print(
        "Later stages should remain compact rather than increasing "
        "dramatically with every prior agent output."
    )


if __name__ == "__main__":
    main()
