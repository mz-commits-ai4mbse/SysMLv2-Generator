"""LLM agent runner for the Turing Generator.

This module executes exactly one agent task per call.

It does not decide the full workflow.
It does not approve data.
It does not generate SysML v2 output.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from modules.agents.types import AgentRunResult
from modules.llm.factory import create_llm_client
from modules.llm.types import LLMRequest


def run_llm_agent(
    *,
    agent_id: str,
    personality_file: Path,
    task_name: str,
    task_instructions: str,
    input_text: str,
    output_dir: Path,
    provider: str,
    model: str,
    api_key: str | None = None,
    run_index: int = 1,
) -> AgentRunResult:
    """Run one LLM-backed agent and persist the result."""

    personality_text = personality_file.read_text(encoding="utf-8")

    instructions = build_agent_instructions(
        agent_id=agent_id,
        personality_file=personality_file,
        personality_text=personality_text,
        task_name=task_name,
        task_instructions=task_instructions,
    )

    client = create_llm_client(provider)

    llm_result = client.generate(
        LLMRequest(
            provider=provider,
            model=model,
            api_key=api_key,
            instructions=instructions,
            input_text=input_text,
            metadata={
                "agent_id": agent_id,
                "task_name": task_name,
                "run_index": run_index,
            },
        )
    )

    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / f"{safe_filename(agent_id)}_run_{run_index:02d}.json"

    payload = {
        "agent_id": agent_id,
        "personality_file": str(personality_file),
        "task_name": task_name,
        "run_index": run_index,
        "provider": llm_result.provider,
        "model": llm_result.model,
        "response_id": llm_result.response_id,
        "status": llm_result.raw_status,
        "usage": llm_result.usage,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "output_text": llm_result.text,
    }

    output_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return AgentRunResult(
        agent_id=agent_id,
        task_name=task_name,
        run_index=run_index,
        provider=llm_result.provider,
        model=llm_result.model,
        output_text=llm_result.text,
        output_path=output_path,
        response_id=llm_result.response_id,
        usage=llm_result.usage,
        status=llm_result.raw_status,
    )


def build_agent_instructions(
    *,
    agent_id: str,
    personality_file: Path,
    personality_text: str,
    task_name: str,
    task_instructions: str,
) -> str:
    """Build the instruction block for exactly one agent task."""

    return f"""
You are executing one specialized agent task in the Turing Generator.

Agent ID:
{agent_id}

Personality File:
{personality_file}

Task Name:
{task_name}

Architectural rules:
- You have exactly one responsibility in this step.
- Do not perform the responsibilities of other agents.
- Do not approve data.
- Do not promote data into approved input.
- Do not generate SysML v2 model code.
- Preserve traceability to the given source material.
- Be conservative when evidence is insufficient.
- Distinguish positive evidence from missing, negated, uncertain or merely mentioned information.
- Do not expose chain-of-thought. Provide concise rationale summaries only.

Agent personality:
{personality_text}

Task instructions:
{task_instructions}
""".strip()


def safe_filename(value: str) -> str:
    """Create a filesystem-safe lowercase filename fragment."""

    cleaned = value.lower().replace(" ", "_").replace("-", "_")
    return "".join(char for char in cleaned if char.isalnum() or char == "_")
