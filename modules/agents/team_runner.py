"""Team runner for executing multiple persona agents on the same task.

A team run means:

- same task
- same input
- same role
- different personas

This module does not perform consensus analysis.
Consensus and variance analysis are handled by modules/consensus/.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from collections.abc import Callable
from pathlib import Path
from typing import Any

from modules.agents.team_config import AgentTeamConfig, TeamMemberConfig, load_team_config
from modules.agents.types import AgentRunResult
from modules.llm.factory import create_llm_client
from modules.llm.types import LLMRequest
from modules.source_analysis_units.identifiers import (
    validate_source_analysis_unit_id,
)


def run_agent_team(
    *,
    project_root: Path,
    team_file: Path,
    task_instructions: str,
    input_text: str,
    output_dir: Path,
    provider: str,
    model: str,
    api_key: str | None = None,
    runs_per_member: int = 1,
    max_members: int | None = None,
    include_alternative_members: bool = False,
    dry_run: bool = False,
    source_analysis_unit_id: str | None = None,
    result_observer: Callable[[AgentRunResult], None] | None = None,
) -> list[AgentRunResult]:
    """Run all selected members of one team on the same task."""

    validated_source_analysis_unit_id = (
        _validate_optional_source_analysis_unit_id(
            source_analysis_unit_id
        )
    )

    team_config = load_team_config(
        project_root=project_root,
        team_file=team_file,
    )

    selected_members = select_team_members(
        team_config=team_config,
        max_members=max_members,
        include_alternative_members=include_alternative_members,
    )

    results: list[AgentRunResult] = []

    for member in selected_members:
        for run_index in range(1, runs_per_member + 1):
            result = run_team_member(
                team_config=team_config,
                member=member,
                task_instructions=task_instructions,
                input_text=input_text,
                output_dir=output_dir,
                provider=provider,
                model=model,
                api_key=api_key,
                run_index=run_index,
                dry_run=dry_run,
                source_analysis_unit_id=(
                    validated_source_analysis_unit_id
                ),
            )
            results.append(result)
            if result_observer is not None:
                result_observer(result)

    return results


def run_team_member(
    *,
    team_config: AgentTeamConfig,
    member: TeamMemberConfig,
    task_instructions: str,
    input_text: str,
    output_dir: Path,
    provider: str,
    model: str,
    api_key: str | None,
    run_index: int,
    dry_run: bool,
    source_analysis_unit_id: str | None = None,
) -> AgentRunResult:
    """Run one persona agent within a team."""

    validated_source_analysis_unit_id = (
        _validate_optional_source_analysis_unit_id(
            source_analysis_unit_id
        )
    )

    role_text = team_config.role_file.read_text(encoding="utf-8")
    persona_text = member.persona_file.read_text(encoding="utf-8")

    instructions = build_team_member_instructions(
        team_config=team_config,
        member=member,
        role_text=role_text,
        persona_text=persona_text,
        task_instructions=task_instructions,
    )

    member_output_dir = (
        output_dir
        / safe_filename(team_config.team_id)
        / safe_filename(member.agent_id)
    )
    member_output_dir.mkdir(parents=True, exist_ok=True)

    output_path = member_output_dir / f"{safe_filename(member.agent_id)}_run_{run_index:02d}.json"

    if dry_run:
        output_text = build_dry_run_output(
            team_config=team_config,
            member=member,
            model=model,
            run_index=run_index,
            source_analysis_unit_id=(
                validated_source_analysis_unit_id
            ),
        )
        response_id = None
        usage: dict[str, Any] = {}
        status = "dry_run"
    else:
        client = create_llm_client(provider)

        metadata = {
            "team_id": team_config.team_id,
            "team_name": team_config.team_name,
            "role_id": team_config.role_id,
            "member_id": member.member_id,
            "agent_id": member.agent_id,
            "persona_id": member.persona_id,
            "task_name": team_config.task_name,
            "run_index": run_index,
        }
        if validated_source_analysis_unit_id is not None:
            metadata["source_analysis_unit_id"] = (
                validated_source_analysis_unit_id
            )

        llm_result = client.generate(
            LLMRequest(
                provider=provider,
                model=model,
                api_key=api_key,
                instructions=instructions,
                input_text=input_text,
                metadata=metadata,
            )
        )

        output_text = llm_result.text
        response_id = llm_result.response_id
        usage = llm_result.usage
        status = llm_result.raw_status

    prompt_metrics = calculate_prompt_metrics(
        instructions=instructions,
        input_text=input_text,
    )

    payload = {
        "team_id": team_config.team_id,
        "team_name": team_config.team_name,
        "task_name": team_config.task_name,
        "role_id": team_config.role_id,
        "role_file": str(team_config.role_file),
        "member_id": member.member_id,
        "agent_id": member.agent_id,
        "persona_id": member.persona_id,
        "persona_file": str(member.persona_file),
        "perspective": member.perspective,
        "run_index": run_index,
        "provider": provider,
        "model": model,
        "response_id": response_id,
        "status": status,
        "usage": usage,
        "prompt_metrics": prompt_metrics,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "output_text": output_text,
    }
    if validated_source_analysis_unit_id is not None:
        payload["source_analysis_unit_id"] = (
            validated_source_analysis_unit_id
        )

    output_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return AgentRunResult(
        agent_id=member.agent_id,
        task_name=team_config.task_name,
        run_index=run_index,
        provider=provider,
        model=model,
        output_text=output_text,
        output_path=output_path,
        response_id=response_id,
        usage=usage,
        status=status,
        source_analysis_unit_id=(
            validated_source_analysis_unit_id
        ),
    )


def build_team_member_instructions(
    *,
    team_config: AgentTeamConfig,
    member: TeamMemberConfig,
    role_text: str,
    persona_text: str,
    task_instructions: str,
) -> str:
    """Build instructions for one team member."""

    return f"""
You are executing one specialized agent task in the Turing Generator.

Team ID:
{team_config.team_id}

Team Name:
{team_config.team_name}

Task Name:
{team_config.task_name}

Role ID:
{team_config.role_id}

Member ID:
{member.member_id}

Agent ID:
{member.agent_id}

Persona ID:
{member.persona_id}

Persona Perspective:
{member.perspective}

Architectural rules:
- You have exactly one responsibility in this step.
- All team members perform the same task independently.
- Do not coordinate with other team members.
- Do not perform consensus analysis.
- Do not perform the responsibilities of other roles.
- Do not approve data.
- Do not promote data into approved input.
- Do not generate SysML v2 model code.
- Preserve traceability to the given source material.
- Distinguish positive evidence from missing, negated, uncertain or merely mentioned information.
- Do not expose chain-of-thought. Provide concise rationale summaries only.

Role definition:
{role_text}

Persona definition:
{persona_text}

Task instructions:
{task_instructions}
""".strip()


def select_team_members(
    *,
    team_config: AgentTeamConfig,
    max_members: int | None,
    include_alternative_members: bool,
) -> list[TeamMemberConfig]:
    """Select team members for execution."""

    members = list(team_config.members)

    if include_alternative_members:
        members.extend(team_config.alternative_members)

    if max_members is not None:
        members = members[:max_members]

    return members


def calculate_prompt_metrics(
    *,
    instructions: str,
    input_text: str,
) -> dict[str, int]:
    """Calculate transparent approximate prompt-size metrics.

    The token estimate is intentionally approximate.
    Actual API token usage remains authoritative.
    """

    instruction_characters = len(instructions)
    input_characters = len(input_text)
    total_characters = instruction_characters + input_characters

    return {
        "instruction_characters": instruction_characters,
        "input_characters": input_characters,
        "total_characters": total_characters,
        "estimated_input_tokens": max(1, total_characters // 4),
    }


def build_dry_run_output(
    *,
    team_config: AgentTeamConfig,
    member: TeamMemberConfig,
    model: str,
    run_index: int,
    source_analysis_unit_id: str | None = None,
) -> str:
    """Create deterministic dry-run output without calling an LLM."""

    payload = {
        "dry_run": True,
        "message": "No LLM call was made.",
        "team_id": team_config.team_id,
        "team_name": team_config.team_name,
        "task_name": team_config.task_name,
        "role_id": team_config.role_id,
        "member_id": member.member_id,
        "agent_id": member.agent_id,
        "persona_id": member.persona_id,
        "perspective": member.perspective,
        "model": model,
        "run_index": run_index,
    }
    if source_analysis_unit_id is not None:
        payload["source_analysis_unit_id"] = (
            source_analysis_unit_id
        )

    return json.dumps(
        payload,
        indent=2,
        ensure_ascii=False,
    )


def _validate_optional_source_analysis_unit_id(
    value: str | None,
) -> str | None:
    if value is None:
        return None
    return validate_source_analysis_unit_id(value)


def safe_filename(value: str) -> str:
    """Create a filesystem-safe lowercase filename fragment."""

    cleaned = value.lower().replace(" ", "_").replace("-", "_")
    return "".join(char for char in cleaned if char.isalnum() or char == "_")
