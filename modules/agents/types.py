"""Agent execution types for the Turing Generator."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class AgentRunResult:
    """Result of one agent execution."""

    agent_id: str
    task_name: str
    run_index: int
    provider: str
    model: str
    output_text: str
    output_path: Path
    response_id: str | None = None
    usage: dict[str, Any] = field(default_factory=dict)
    status: str | None = None
    source_analysis_unit_id: str | None = None
