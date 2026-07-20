"""Interpretation-memory construction.

This module consolidates outputs from the Legacy Interpretation Team into a
compact handover artifact for evidence classification.

It does not call an LLM.
It does not approve information.
It does not classify evidence types.
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

from modules.agents.types import AgentRunResult
from modules.ingestion.memory import (
    create_memory_envelope,
    load_structured_agent_outputs,
    normalize_text,
    unique_dicts,
    unique_strings,
    write_memory_artifact,
)


def build_interpretation_memory(
    *,
    task_id: str,
    run_id: str,
    raw_input_path: Path,
    interpretation_results: list[AgentRunResult],
    interpretation_consensus: dict[str, Any],
    output_path: Path,
) -> dict[str, Any]:
    """Build and write compact interpretation memory."""

    agent_outputs = load_structured_agent_outputs(
        interpretation_results
    )

    source_information = collect_source_information(
        agent_outputs
    )
    assumptions = collect_list_items(
        agent_outputs,
        field_name="assumptions",
    )
    ambiguities = collect_list_items(
        agent_outputs,
        field_name="ambiguities",
    )
    excluded_positive_evidence = collect_list_items(
        agent_outputs,
        field_name="not_interpreted_as_positive_evidence",
    )

    payload = {
        "source_information": source_information,
        "assumptions": assumptions,
        "ambiguities": ambiguities,
        "not_interpreted_as_positive_evidence": (
            excluded_positive_evidence
        ),
        "handover_summary": {
            "source_information_count": len(source_information),
            "assumption_count": len(assumptions),
            "ambiguity_count": len(ambiguities),
            "excluded_positive_evidence_count": len(
                excluded_positive_evidence
            ),
            "participating_agents": [
                {
                    "agent_id": item["agent_id"],
                    "persona_id": item["persona_id"],
                }
                for item in agent_outputs
            ],
            "consensus_summary": interpretation_consensus.get(
                "summary",
                {},
            ),
        },
    }

    memory = create_memory_envelope(
        memory_type="interpretation_memory",
        task_id=task_id,
        run_id=run_id,
        source_path=raw_input_path,
        producing_team_id="TEAM_LEGACY_INTERPRETATION",
        payload=payload,
        source_agent_results=interpretation_results,
        consensus_report=interpretation_consensus,
    )

    write_memory_artifact(
        memory=memory,
        output_path=output_path,
    )

    return memory


def collect_source_information(
    agent_outputs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Collect source-information records with per-agent observations."""

    grouped: dict[str, dict[str, Any]] = {}

    for agent_output in agent_outputs:
        agent_id = agent_output["agent_id"]
        persona_id = agent_output["persona_id"]

        entries = agent_output["output"].get(
            "source_information",
            [],
        )

        for entry in entries:
            if not isinstance(entry, dict):
                continue

            statement = str(
                entry.get("extracted_information", "")
            ).strip()

            if not statement:
                continue

            source_reference = str(
                entry.get("source_reference", "")
            ).strip()

            group_key = (
                f"{normalize_text(source_reference)}::"
                f"{normalize_text(statement)}"
            )

            item = grouped.setdefault(
                group_key,
                {
                    "memory_source_info_id": "",
                    "source_references": [],
                    "source_statements": [],
                    "agent_observations": [],
                    "information_kinds": [],
                    "confidence_values": [],
                    "requires_review": False,
                },
            )

            item["source_references"].append(source_reference)
            item["source_statements"].append(statement)
            item["information_kinds"].append(
                str(entry.get("information_kind", "")).strip()
            )
            item["confidence_values"].append(
                str(entry.get("confidence", "")).strip()
            )
            item["agent_observations"].append(
                {
                    "agent_id": agent_id,
                    "persona_id": persona_id,
                    "original_source_info_id": entry.get(
                        "source_info_id",
                        "",
                    ),
                    "source_reference": source_reference,
                    "extracted_information": statement,
                    "information_kind": entry.get(
                        "information_kind",
                        "",
                    ),
                    "confidence": entry.get("confidence", ""),
                    "notes": entry.get("notes", ""),
                }
            )

    result: list[dict[str, Any]] = []

    for index, item in enumerate(
        grouped.values(),
        start=1,
    ):
        information_kinds = unique_strings(
            item["information_kinds"]
        )
        confidence_values = unique_strings(
            item["confidence_values"]
        )

        item["memory_source_info_id"] = (
            f"MEM_SRC_INFO_{index:03d}"
        )
        item["source_references"] = unique_strings(
            item["source_references"]
        )
        item["source_statements"] = unique_strings(
            item["source_statements"]
        )
        item["information_kinds"] = information_kinds
        item["confidence_values"] = confidence_values
        item["requires_review"] = (
            len(information_kinds) > 1
            or len(confidence_values) > 1
            or any(
                kind
                in {
                    "assumption",
                    "uncertainty",
                    "negated",
                    "missing",
                }
                for kind in information_kinds
            )
        )

        result.append(item)

    return result


def collect_list_items(
    agent_outputs: list[dict[str, Any]],
    *,
    field_name: str,
) -> list[dict[str, Any]]:
    """Collect simple or structured list items from all agents."""

    collected: list[dict[str, Any]] = []

    for agent_output in agent_outputs:
        agent_id = agent_output["agent_id"]
        persona_id = agent_output["persona_id"]

        entries = agent_output["output"].get(
            field_name,
            [],
        )

        for entry in entries:
            if isinstance(entry, dict):
                collected.append(
                    {
                        "agent_id": agent_id,
                        "persona_id": persona_id,
                        "content": entry,
                    }
                )
            else:
                text = str(entry or "").strip()

                if text:
                    collected.append(
                        {
                            "agent_id": agent_id,
                            "persona_id": persona_id,
                            "content": text,
                        }
                    )

    return unique_dicts(
        collected,
        key_fields=(
            "agent_id",
            "persona_id",
            "content",
        ),
    )
