"""Working-memory artifacts for the agentic ingestion pipeline.

A memory artifact is a compact, structured handover between pipeline stages.

It is not:
- a raw agent output
- a complete consensus report
- a narrative report
- an approved model input

Each stage receives only the memory required for its responsibility.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from modules.agents.types import AgentRunResult


MEMORY_SCHEMA_VERSION = "1.0"


def create_memory_envelope(
    *,
    memory_type: str,
    task_id: str,
    run_id: str,
    source_path: Path,
    producing_team_id: str,
    payload: dict[str, Any],
    source_agent_results: list[AgentRunResult],
    consensus_report: dict[str, Any] | None,
) -> dict[str, Any]:
    """Create a common envelope for one stage-memory artifact."""

    return {
        "memory_schema_version": MEMORY_SCHEMA_VERSION,
        "memory_type": memory_type,
        "task_id": task_id,
        "run_id": run_id,
        "source_path": str(source_path),
        "producing_team_id": producing_team_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "review_status": "unreviewed",
        "approved_for_modeling": False,
        "source_agent_artifacts": [
            {
                "agent_id": result.agent_id,
                "task_name": result.task_name,
                "run_index": result.run_index,
                "output_path": str(result.output_path),
                "status": result.status,
            }
            for result in source_agent_results
        ],
        "consensus_report_id": (
            consensus_report.get("consensus_report_id")
            if consensus_report
            else None
        ),
        "payload": payload,
    }


def load_structured_agent_outputs(
    results: list[AgentRunResult],
) -> list[dict[str, Any]]:
    """Load structured JSON content from agent-result wrapper files."""

    outputs: list[dict[str, Any]] = []

    for result in results:
        wrapper = json.loads(
            result.output_path.read_text(encoding="utf-8")
        )

        parsed_output = parse_json_text(
            str(wrapper.get("output_text", ""))
        )

        outputs.append(
            {
                "agent_id": str(
                    wrapper.get("agent_id", result.agent_id)
                ),
                "persona_id": str(
                    wrapper.get("persona_id", "UNKNOWN_PERSONA")
                ),
                "output_path": str(result.output_path),
                "output": (
                    parsed_output
                    if isinstance(parsed_output, dict)
                    else {}
                ),
            }
        )

    return outputs


def write_memory_artifact(
    *,
    memory: dict[str, Any],
    output_path: Path,
) -> None:
    """Write one memory artifact as formatted JSON."""

    output_path.parent.mkdir(parents=True, exist_ok=True)

    output_path.write_text(
        json.dumps(
            memory,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def format_memory_for_prompt(memory: dict[str, Any]) -> str:
    """Format only relevant memory content for a downstream prompt."""

    compact_memory = {
        "memory_type": memory.get("memory_type"),
        "review_status": memory.get("review_status"),
        "approved_for_modeling": memory.get(
            "approved_for_modeling",
            False,
        ),
        "payload": memory.get("payload", {}),
    }

    return json.dumps(
        compact_memory,
        indent=2,
        ensure_ascii=False,
    )


def parse_json_text(text: str) -> Any:
    """Parse JSON returned directly or inside a Markdown fence."""

    cleaned = text.strip()

    if not cleaned:
        return None

    if cleaned.startswith("```"):
        cleaned = re.sub(
            r"^```[a-zA-Z0-9_-]*\s*",
            "",
            cleaned,
        )
        cleaned = re.sub(
            r"\s*```$",
            "",
            cleaned,
        )
        cleaned = cleaned.strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return None


def normalize_text(value: Any) -> str:
    """Normalize text for conservative exact grouping."""

    cleaned = str(value or "").strip().lower()
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned


def unique_strings(values: list[Any]) -> list[str]:
    """Return unique non-empty strings while preserving order."""

    result: list[str] = []
    seen: set[str] = set()

    for value in values:
        text = str(value or "").strip()

        if not text:
            continue

        normalized = normalize_text(text)

        if normalized in seen:
            continue

        seen.add(normalized)
        result.append(text)

    return result


def unique_dicts(
    values: list[dict[str, Any]],
    *,
    key_fields: tuple[str, ...],
) -> list[dict[str, Any]]:
    """Deduplicate dictionaries using selected fields."""

    result: list[dict[str, Any]] = []
    seen: set[tuple[str, ...]] = set()

    for value in values:
        key = tuple(
            normalize_text(value.get(field))
            for field in key_fields
        )

        if key in seen:
            continue

        seen.add(key)
        result.append(value)

    return result
