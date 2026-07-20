"""Team configuration loading for agentic workflows."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class TeamMemberConfig:
    """Configuration for one team member."""

    member_id: str
    agent_id: str
    persona_id: str
    persona_file: Path
    perspective: str


@dataclass
class AgentTeamConfig:
    """Configuration for one agent team."""

    team_id: str
    team_name: str
    task_name: str
    role_id: str
    role_file: Path
    description: str
    default_execution_mode: str
    members: list[TeamMemberConfig]
    alternative_members: list[TeamMemberConfig]
    consensus_required: bool
    consensus_focus: list[str]
    source_path: Path


def load_team_config(project_root: Path, team_file: Path) -> AgentTeamConfig:
    """Load a team configuration JSON file."""

    resolved_team_file = resolve_project_path(project_root, team_file)

    with resolved_team_file.open("r", encoding="utf-8") as file:
        payload = json.load(file)

    members = [
        parse_member(project_root, item)
        for item in payload.get("members", [])
    ]

    alternative_members = [
        parse_member(project_root, item)
        for item in payload.get("alternative_members", [])
    ]

    return AgentTeamConfig(
        team_id=payload["team_id"],
        team_name=payload["team_name"],
        task_name=payload["task_name"],
        role_id=payload["role_id"],
        role_file=resolve_project_path(project_root, Path(payload["role_file"])),
        description=payload.get("description", ""),
        default_execution_mode=payload.get("default_execution_mode", "multi_persona"),
        members=members,
        alternative_members=alternative_members,
        consensus_required=bool(payload.get("consensus_required", False)),
        consensus_focus=list(payload.get("consensus_focus", [])),
        source_path=resolved_team_file,
    )


def parse_member(project_root: Path, payload: dict[str, Any]) -> TeamMemberConfig:
    """Parse one team member from JSON payload."""

    return TeamMemberConfig(
        member_id=payload["member_id"],
        agent_id=payload["agent_id"],
        persona_id=payload["persona_id"],
        persona_file=resolve_project_path(project_root, Path(payload["persona_file"])),
        perspective=payload.get("perspective", ""),
    )


def resolve_project_path(project_root: Path, path: Path) -> Path:
    """Resolve project-relative paths."""

    if path.is_absolute():
        return path

    return project_root / path
