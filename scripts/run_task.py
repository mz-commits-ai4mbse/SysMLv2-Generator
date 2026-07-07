"""Run one Turing Generator task from the workspace root."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

# Allow running without installing the package.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.orchestrator import TuringOrchestrator, OrchestratorError


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a Turing Generator MVP task.")
    parser.add_argument("task_path", help="Path to the task JSON file, relative to workspace root.")
    parser.add_argument(
        "--workspace-root",
        default=".",
        help="Workspace root. Default: current directory.",
    )
    args = parser.parse_args()

    orchestrator = TuringOrchestrator(workspace_root=args.workspace_root)
    try:
        result = orchestrator.run_task(args.task_path)
    except OrchestratorError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
