"""Consensus data types for the Turing Generator."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ComparableItem:
    """One comparable item extracted from an agent output."""

    group_key: str
    value_key: str
    item_type: str
    display_value: str
    agent_id: str
    persona_id: str | None = None
    source_path: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ConsensusGroup:
    """Consensus result for one comparison group."""

    group_key: str
    item_type: str
    agreement_level: str
    total_agents: int
    supporting_agents: list[str]
    value_distribution: dict[str, list[str]]
    representative_value: str
    review_required: bool
    reason: str
    agent_values: dict[str, str] = field(default_factory=dict)
