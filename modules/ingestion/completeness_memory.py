"""Completeness-memory construction.

This module consolidates outputs from the Completeness Review Team into the
final compact handover artifact for deterministic review reporting.

It does not call an LLM.
It does not approve information.
It does not generate models.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from modules.agents.types import AgentRunResult
from modules.ingestion.memory import (
    create_memory_envelope,
    load_structured_agent_outputs,
    unique_dicts,
    write_memory_artifact,
)


def build_completeness_memory(
    *,
    task_id: str,
    run_id: str,
    raw_input_path: Path,
    completeness_results: list[AgentRunResult],
    completeness_consensus: dict[str, Any],
    output_path: Path,
) -> dict[str, Any]:
    """Build and write compact completeness memory."""

    agent_outputs = load_structured_agent_outputs(
        completeness_results
    )

    gaps = collect_entries(
        agent_outputs,
        field_name="gaps",
        key_fields=(
            "agent_id",
            "missing_information",
            "suggested_human_action",
        ),
    )

    ambiguities_and_risks = collect_entries(
        agent_outputs,
        field_name="ambiguities_and_risks",
        key_fields=(
            "agent_id",
            "topic",
            "description",
        ),
    )

    review_questions = collect_entries(
        agent_outputs,
        field_name="review_questions",
        key_fields=(
            "agent_id",
            "question",
            "related_artifact_or_candidate",
        ),
    )

    review_decisions = collect_review_decisions(
        agent_outputs
    )

    payload = {
        "gaps": gaps,
        "ambiguities_and_risks": ambiguities_and_risks,
        "review_questions": review_questions,
        "recommended_review_decisions": review_decisions,
        "handover_summary": {
            "gap_count": len(gaps),
            "risk_count": len(ambiguities_and_risks),
            "review_question_count": len(review_questions),
            "participating_agents": [
                {
                    "agent_id": item["agent_id"],
                    "persona_id": item["persona_id"],
                }
                for item in agent_outputs
            ],
            "consensus_summary": completeness_consensus.get(
                "summary",
                {},
            ),
        },
    }

    memory = create_memory_envelope(
        memory_type="completeness_memory",
        task_id=task_id,
        run_id=run_id,
        source_path=raw_input_path,
        producing_team_id="TEAM_COMPLETENESS_REVIEW",
        payload=payload,
        source_agent_results=completeness_results,
        consensus_report=completeness_consensus,
    )

    write_memory_artifact(
        memory=memory,
        output_path=output_path,
    )

    return memory


def collect_entries(
    agent_outputs: list[dict[str, Any]],
    *,
    field_name: str,
    key_fields: tuple[str, ...],
) -> list[dict[str, Any]]:
    """Collect structured entries from all completeness agents."""

    collected: list[dict[str, Any]] = []

    for agent_output in agent_outputs:
        for entry in agent_output["output"].get(
            field_name,
            [],
        ):
            if not isinstance(entry, dict):
                continue

            collected.append(
                {
                    "agent_id": agent_output["agent_id"],
                    "persona_id": agent_output["persona_id"],
                    **entry,
                }
            )

    return unique_dicts(
        collected,
        key_fields=key_fields,
    )


def collect_review_decisions(
    agent_outputs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Collect recommended review decisions per agent."""

    decisions: list[dict[str, Any]] = []

    for agent_output in agent_outputs:
        decision = agent_output["output"].get(
            "recommended_review_decision"
        )

        if not decision:
            continue

        decisions.append(
            {
                "agent_id": agent_output["agent_id"],
                "persona_id": agent_output["persona_id"],
                "recommended_review_decision": decision,
            }
        )

    return unique_dicts(
        decisions,
        key_fields=(
            "agent_id",
            "recommended_review_decision",
        ),
    )
