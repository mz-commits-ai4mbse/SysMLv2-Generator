"""Derivation-memory construction.

This module consolidates outputs from the Derivation Assessment Team into a
compact handover artifact for completeness review and deterministic reporting.

It does not call an LLM.
It does not approve model elements.
It does not generate SysML v2 code.
It does not add relationships that were not returned as source-supported.
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


def build_derivation_memory(
    *,
    task_id: str,
    run_id: str,
    raw_input_path: Path,
    derivation_results: list[AgentRunResult],
    derivation_consensus: dict[str, Any],
    output_path: Path,
) -> dict[str, Any]:
    """Build and write compact derivation memory."""

    agent_outputs = load_structured_agent_outputs(derivation_results)

    candidate_model_elements = collect_candidate_model_elements(
        agent_outputs
    )
    explicit_source_links = collect_explicit_source_links(
        agent_outputs
    )
    sysml_model_buildability = collect_sysml_model_buildability(
        agent_outputs
    )
    missing_information = collect_missing_information(
        agent_outputs
    )
    unsupported_interpretations = collect_unsupported_interpretations(
        agent_outputs
    )
    artifact_assessments = collect_artifact_assessments(
        agent_outputs
    )
    blocked_generation_tasks = collect_generic_list_entries(
        agent_outputs,
        field_name="blocked_generation_tasks",
    )
    cross_artifact_observations = collect_generic_list_entries(
        agent_outputs,
        field_name="cross_artifact_observations",
    )

    payload = {
        "candidate_model_elements": candidate_model_elements,
        "explicit_source_links": explicit_source_links,
        "sysml_model_buildability": sysml_model_buildability,
        "missing_information_for_model_building": missing_information,
        "possible_but_unsupported_interpretations": (
            unsupported_interpretations
        ),
        "model_artifact_assessments": artifact_assessments,
        "blocked_generation_tasks": blocked_generation_tasks,
        "cross_artifact_observations": cross_artifact_observations,
        "handover_summary": {
            "candidate_model_element_count": len(
                candidate_model_elements
            ),
            "explicit_source_link_count": len(
                explicit_source_links
            ),
            "assessed_model_type_count": len(
                sysml_model_buildability
            ),
            "missing_information_count": len(
                missing_information
            ),
            "unsupported_interpretation_count": len(
                unsupported_interpretations
            ),
            "participating_agents": [
                {
                    "agent_id": item["agent_id"],
                    "persona_id": item["persona_id"],
                }
                for item in agent_outputs
            ],
            "consensus_summary": derivation_consensus.get(
                "summary",
                {},
            ),
        },
    }

    memory = create_memory_envelope(
        memory_type="derivation_memory",
        task_id=task_id,
        run_id=run_id,
        source_path=raw_input_path,
        producing_team_id="TEAM_DERIVATION_ASSESSMENT",
        payload=payload,
        source_agent_results=derivation_results,
        consensus_report=derivation_consensus,
    )

    write_memory_artifact(
        memory=memory,
        output_path=output_path,
    )

    return memory


def collect_candidate_model_elements(
    agent_outputs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Collect candidate model elements with per-agent assessments."""

    grouped: dict[str, dict[str, Any]] = {}

    for agent_output in agent_outputs:
        agent_id = agent_output["agent_id"]
        persona_id = agent_output["persona_id"]

        for entry in agent_output["output"].get(
            "candidate_model_elements",
            [],
        ):
            if not isinstance(entry, dict):
                continue

            element_type = str(
                entry.get("element_type", "other")
            ).strip()
            candidate_name = str(
                entry.get("candidate_name", "")
            ).strip()

            if not candidate_name:
                continue

            group_key = (
                f"{normalize_text(element_type)}::"
                f"{normalize_text(candidate_name)}"
            )

            candidate = grouped.setdefault(
                group_key,
                {
                    "memory_candidate_id": "",
                    "element_type": element_type,
                    "candidate_name": candidate_name,
                    "descriptions": [],
                    "source_basis": [],
                    "assigned_source_information": [],
                    "agent_assessments": [],
                    "confidence_values": [],
                    "generation_readiness_values": [],
                    "missing_information": [],
                    "requires_review": False,
                },
            )

            candidate["descriptions"].append(
                entry.get("description", "")
            )
            candidate["source_basis"].extend(
                entry.get("source_basis", [])
            )
            candidate["confidence_values"].append(
                entry.get("confidence", "")
            )
            candidate["generation_readiness_values"].append(
                entry.get("generation_readiness", "")
            )
            candidate["missing_information"].extend(
                entry.get("missing_information", [])
            )

            candidate["agent_assessments"].append(
                {
                    "agent_id": agent_id,
                    "persona_id": persona_id,
                    "original_candidate_id": entry.get(
                        "candidate_id",
                        "",
                    ),
                    "description": entry.get("description", ""),
                    "confidence": entry.get("confidence", ""),
                    "generation_readiness": entry.get(
                        "generation_readiness",
                        "",
                    ),
                    "source_basis": entry.get(
                        "source_basis",
                        [],
                    ),
                    "missing_information": entry.get(
                        "missing_information",
                        [],
                    ),
                    "rationale_summary": entry.get(
                        "rationale_summary",
                        "",
                    ),
                }
            )

            for assignment in entry.get(
                "assigned_source_information",
                [],
            ):
                if not isinstance(assignment, dict):
                    continue

                candidate["assigned_source_information"].append(
                    {
                        "agent_id": agent_id,
                        "persona_id": persona_id,
                        "source_info_id": assignment.get(
                            "source_info_id",
                            "",
                        ),
                        "source_statement": assignment.get(
                            "source_statement",
                            "",
                        ),
                        "assignment_type": assignment.get(
                            "assignment_type",
                            "",
                        ),
                        "confidence": assignment.get(
                            "confidence",
                            "",
                        ),
                    }
                )

    result: list[dict[str, Any]] = []

    for index, candidate in enumerate(
        grouped.values(),
        start=1,
    ):
        candidate["memory_candidate_id"] = (
            f"MEM_CANDIDATE_{index:03d}"
        )
        candidate["descriptions"] = unique_strings(
            candidate["descriptions"]
        )
        candidate["source_basis"] = unique_strings(
            candidate["source_basis"]
        )
        candidate["confidence_values"] = unique_strings(
            candidate["confidence_values"]
        )
        candidate["generation_readiness_values"] = unique_strings(
            candidate["generation_readiness_values"]
        )
        candidate["missing_information"] = unique_strings(
            candidate["missing_information"]
        )
        candidate["assigned_source_information"] = unique_dicts(
            candidate["assigned_source_information"],
            key_fields=(
                "agent_id",
                "source_info_id",
                "source_statement",
                "assignment_type",
            ),
        )

        identifying_agents = {
            assessment["agent_id"]
            for assessment in candidate["agent_assessments"]
        }

        candidate["requires_review"] = (
            len(identifying_agents) < len(agent_outputs)
            or len(candidate["confidence_values"]) > 1
            or len(
                candidate["generation_readiness_values"]
            ) > 1
        )

        result.append(candidate)

    return result


def collect_explicit_source_links(
    agent_outputs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Collect only source-supported explicit links."""

    collected: list[dict[str, Any]] = []

    for agent_output in agent_outputs:
        for entry in agent_output["output"].get(
            "explicit_source_links",
            [],
        ):
            if not isinstance(entry, dict):
                continue

            collected.append(
                {
                    "agent_id": agent_output["agent_id"],
                    "persona_id": agent_output["persona_id"],
                    "original_link_id": entry.get(
                        "link_id",
                        "",
                    ),
                    "source_element_candidate": entry.get(
                        "source_element_candidate",
                        "",
                    ),
                    "link_type": entry.get("link_type", ""),
                    "target_element_candidate": entry.get(
                        "target_element_candidate",
                        "",
                    ),
                    "source_basis": entry.get(
                        "source_basis",
                        [],
                    ),
                    "source_statement": entry.get(
                        "source_statement",
                        "",
                    ),
                    "confidence": entry.get("confidence", ""),
                    "rationale_summary": entry.get(
                        "rationale_summary",
                        "",
                    ),
                }
            )

    return unique_dicts(
        collected,
        key_fields=(
            "agent_id",
            "source_element_candidate",
            "link_type",
            "target_element_candidate",
            "source_statement",
        ),
    )


def collect_sysml_model_buildability(
    agent_outputs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Collect per-agent buildability assessments."""

    grouped: dict[str, dict[str, Any]] = {}

    for agent_output in agent_outputs:
        agent_id = agent_output["agent_id"]
        persona_id = agent_output["persona_id"]

        for entry in agent_output["output"].get(
            "sysml_model_buildability",
            [],
        ):
            if not isinstance(entry, dict):
                continue

            model_type = str(
                entry.get("sysml_model_type", "")
            ).strip()

            if not model_type:
                continue

            item = grouped.setdefault(
                normalize_text(model_type),
                {
                    "sysml_model_type": model_type,
                    "agent_assessments": [],
                    "support_levels": [],
                    "generation_scopes": [],
                    "can_be_generated_values": [],
                    "available_information": [],
                    "evidence_basis": [],
                    "missing_information": [],
                    "recommended_actions": [],
                    "requires_review": False,
                },
            )

            item["support_levels"].append(
                entry.get("support_level", "")
            )
            item["generation_scopes"].append(
                entry.get("generation_scope", "")
            )
            item["can_be_generated_values"].append(
                entry.get("can_be_generated_now")
            )
            item["available_information"].extend(
                entry.get("available_information", [])
            )
            item["evidence_basis"].extend(
                entry.get("evidence_basis", [])
            )
            item["missing_information"].extend(
                entry.get("missing_information", [])
            )
            item["recommended_actions"].append(
                entry.get("recommended_action", "")
            )

            item["agent_assessments"].append(
                {
                    "agent_id": agent_id,
                    "persona_id": persona_id,
                    "support_level": entry.get(
                        "support_level",
                        "",
                    ),
                    "can_be_generated_now": entry.get(
                        "can_be_generated_now"
                    ),
                    "generation_scope": entry.get(
                        "generation_scope",
                        "",
                    ),
                    "available_information": entry.get(
                        "available_information",
                        [],
                    ),
                    "evidence_basis": entry.get(
                        "evidence_basis",
                        [],
                    ),
                    "missing_information": entry.get(
                        "missing_information",
                        [],
                    ),
                    "reason": entry.get("reason", ""),
                    "recommended_action": entry.get(
                        "recommended_action",
                        "",
                    ),
                }
            )

    result: list[dict[str, Any]] = []

    for item in grouped.values():
        item["support_levels"] = unique_strings(
            item["support_levels"]
        )
        item["generation_scopes"] = unique_strings(
            item["generation_scopes"]
        )
        item["can_be_generated_values"] = list(
            dict.fromkeys(item["can_be_generated_values"])
        )
        item["available_information"] = unique_strings(
            item["available_information"]
        )
        item["evidence_basis"] = unique_strings(
            item["evidence_basis"]
        )
        item["missing_information"] = unique_strings(
            item["missing_information"]
        )
        item["recommended_actions"] = unique_strings(
            item["recommended_actions"]
        )

        item["requires_review"] = (
            len(item["agent_assessments"]) < len(agent_outputs)
            or len(item["support_levels"]) > 1
            or len(item["generation_scopes"]) > 1
            or len(item["can_be_generated_values"]) > 1
        )

        result.append(item)

    return result


def collect_missing_information(
    agent_outputs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Collect missing information for further model building."""

    collected: list[dict[str, Any]] = []

    for agent_output in agent_outputs:
        for entry in agent_output["output"].get(
            "missing_information_for_model_building",
            [],
        ):
            if not isinstance(entry, dict):
                continue

            collected.append(
                {
                    "agent_id": agent_output["agent_id"],
                    "persona_id": agent_output["persona_id"],
                    "original_missing_info_id": entry.get(
                        "missing_info_id",
                        "",
                    ),
                    "missing_information": entry.get(
                        "missing_information",
                        "",
                    ),
                    "limits_or_blocks": entry.get(
                        "limits_or_blocks",
                        [],
                    ),
                    "needed_for": entry.get(
                        "needed_for",
                        [],
                    ),
                    "review_question": entry.get(
                        "review_question",
                        "",
                    ),
                }
            )

    return unique_dicts(
        collected,
        key_fields=(
            "agent_id",
            "missing_information",
            "review_question",
        ),
    )


def collect_unsupported_interpretations(
    agent_outputs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Collect possible but unsupported interpretations."""

    collected: list[dict[str, Any]] = []

    for agent_output in agent_outputs:
        for entry in agent_output["output"].get(
            "possible_but_unsupported_interpretations",
            [],
        ):
            if not isinstance(entry, dict):
                continue

            collected.append(
                {
                    "agent_id": agent_output["agent_id"],
                    "persona_id": agent_output["persona_id"],
                    "topic": entry.get("topic", ""),
                    "reason_not_accepted": entry.get(
                        "reason_not_accepted",
                        "",
                    ),
                    "review_question": entry.get(
                        "review_question",
                        "",
                    ),
                }
            )

    return unique_dicts(
        collected,
        key_fields=(
            "agent_id",
            "topic",
            "review_question",
        ),
    )


def collect_artifact_assessments(
    agent_outputs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Collect generic model-artifact assessments."""

    collected: list[dict[str, Any]] = []

    for agent_output in agent_outputs:
        for entry in agent_output["output"].get(
            "model_artifact_assessments",
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
        key_fields=(
            "agent_id",
            "model_artifact_type",
            "support_level",
        ),
    )


def collect_generic_list_entries(
    agent_outputs: list[dict[str, Any]],
    *,
    field_name: str,
) -> list[dict[str, Any]]:
    """Collect generic structured or text list entries."""

    collected: list[dict[str, Any]] = []

    for agent_output in agent_outputs:
        for entry in agent_output["output"].get(
            field_name,
            [],
        ):
            collected.append(
                {
                    "agent_id": agent_output["agent_id"],
                    "persona_id": agent_output["persona_id"],
                    "content": entry,
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
