"""Evidence-memory construction.

This module consolidates outputs from the Evidence Classification Team into a
compact handover artifact for model-element and buildability assessment.

It does not call an LLM.
It does not assess SysML model buildability.
It does not approve evidence.
"""

from __future__ import annotations

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


def build_evidence_memory(
    *,
    task_id: str,
    run_id: str,
    raw_input_path: Path,
    evidence_results: list[AgentRunResult],
    evidence_consensus: dict[str, Any],
    output_path: Path,
) -> dict[str, Any]:
    """Build and write compact evidence memory."""

    agent_outputs = load_structured_agent_outputs(evidence_results)

    detected_evidence = collect_detected_evidence(agent_outputs)
    rejected_candidates = collect_rejected_candidates(agent_outputs)
    evidence_gaps = collect_evidence_gaps(agent_outputs)

    payload = {
        "detected_evidence": detected_evidence,
        "rejected_evidence_candidates": rejected_candidates,
        "evidence_gaps": evidence_gaps,
        "handover_summary": {
            "detected_evidence_count": len(detected_evidence),
            "rejected_candidate_count": len(rejected_candidates),
            "evidence_gap_count": len(evidence_gaps),
            "participating_agents": [
                {
                    "agent_id": item["agent_id"],
                    "persona_id": item["persona_id"],
                }
                for item in agent_outputs
            ],
            "consensus_summary": evidence_consensus.get("summary", {}),
        },
    }

    memory = create_memory_envelope(
        memory_type="evidence_memory",
        task_id=task_id,
        run_id=run_id,
        source_path=raw_input_path,
        producing_team_id="TEAM_EVIDENCE_CLASSIFICATION",
        payload=payload,
        source_agent_results=evidence_results,
        consensus_report=evidence_consensus,
    )

    write_memory_artifact(
        memory=memory,
        output_path=output_path,
    )

    return memory


def collect_detected_evidence(
    agent_outputs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Collect evidence records and preserve per-agent assessments."""

    grouped: dict[str, dict[str, Any]] = {}

    for agent_output in agent_outputs:
        agent_id = agent_output["agent_id"]
        persona_id = agent_output["persona_id"]

        entries = agent_output["output"].get("detected_evidence", [])

        for entry in entries:
            if not isinstance(entry, dict):
                continue

            evidence_type = str(entry.get("evidence_type", "")).strip()
            source_info_id = str(entry.get("source_info_id", "")).strip()
            source_excerpt = str(entry.get("source_excerpt", "")).strip()

            if not evidence_type:
                continue

            source_basis = source_info_id or source_excerpt

            group_key = (
                f"{normalize_text(evidence_type)}::"
                f"{normalize_text(source_basis)}"
            )

            item = grouped.setdefault(
                group_key,
                {
                    "memory_evidence_id": "",
                    "evidence_type": evidence_type,
                    "source_info_ids": [],
                    "source_excerpts": [],
                    "agent_assessments": [],
                    "confidence_values": [],
                    "requires_review": False,
                },
            )

            item["source_info_ids"].append(source_info_id)
            item["source_excerpts"].append(source_excerpt)
            item["confidence_values"].append(
                str(entry.get("confidence", "")).strip()
            )

            item["agent_assessments"].append(
                {
                    "agent_id": agent_id,
                    "persona_id": persona_id,
                    "original_evidence_id": entry.get("evidence_id", ""),
                    "interpretation": entry.get("interpretation", ""),
                    "confidence": entry.get("confidence", ""),
                    "rationale_summary": entry.get(
                        "rationale_summary",
                        "",
                    ),
                }
            )

    result: list[dict[str, Any]] = []

    for index, item in enumerate(grouped.values(), start=1):
        item["memory_evidence_id"] = f"MEM_EVIDENCE_{index:03d}"
        item["source_info_ids"] = unique_strings(
            item["source_info_ids"]
        )
        item["source_excerpts"] = unique_strings(
            item["source_excerpts"]
        )
        item["confidence_values"] = unique_strings(
            item["confidence_values"]
        )

        assessment_agents = {
            assessment["agent_id"]
            for assessment in item["agent_assessments"]
        }

        item["requires_review"] = (
            len(item["confidence_values"]) > 1
            or len(assessment_agents) < len(agent_outputs)
        )

        result.append(item)

    return result


def collect_rejected_candidates(
    agent_outputs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Collect rejected evidence candidates."""

    collected: list[dict[str, Any]] = []

    for agent_output in agent_outputs:
        for entry in agent_output["output"].get(
            "rejected_evidence_candidates",
            [],
        ):
            if not isinstance(entry, dict):
                continue

            collected.append(
                {
                    "agent_id": agent_output["agent_id"],
                    "persona_id": agent_output["persona_id"],
                    "source_info_id": entry.get("source_info_id", ""),
                    "rejected_evidence_type": entry.get(
                        "rejected_evidence_type",
                        "",
                    ),
                    "reason": entry.get("reason", ""),
                }
            )

    return unique_dicts(
        collected,
        key_fields=(
            "agent_id",
            "source_info_id",
            "rejected_evidence_type",
            "reason",
        ),
    )


def collect_evidence_gaps(
    agent_outputs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Collect evidence gaps returned by classifiers."""

    collected: list[dict[str, Any]] = []

    for agent_output in agent_outputs:
        for entry in agent_output["output"].get("evidence_gaps", []):
            if isinstance(entry, dict):
                collected.append(
                    {
                        "agent_id": agent_output["agent_id"],
                        "persona_id": agent_output["persona_id"],
                        "content": entry,
                    }
                )
            else:
                text = str(entry or "").strip()

                if text:
                    collected.append(
                        {
                            "agent_id": agent_output["agent_id"],
                            "persona_id": agent_output["persona_id"],
                            "content": text,
                        }
                    )

    return unique_dicts(
        collected,
        key_fields=("agent_id", "persona_id", "content"),
    )
