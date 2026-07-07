"""Run context model for one Turing Generator task execution."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class RunContext:
    workspace_root: Path
    task_path: Path
    task: dict[str, Any]
    recipe_text: str
    required_context: dict[str, str]
    optional_context: dict[str, str]
    agent_personalities: dict[str, str]
    run_id: str = field(default_factory=lambda: f"run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}")
    generated_at: str = field(default_factory=utc_timestamp)

    @property
    def task_id(self) -> str:
        return self.task.get("task_id", "UNKNOWN_TASK")

    @property
    def recipe_id(self) -> str:
        return self.task.get("recipe", {}).get("recipe_id", "UNKNOWN_RECIPE")

    def resolve(self, relative_path: str | Path) -> Path:
        return self.workspace_root / Path(relative_path)
