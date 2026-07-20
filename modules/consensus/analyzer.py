"""Deterministic consensus and variance analysis.

This module compares outputs from multiple persona agents that performed
the same task.

It does not call an LLM.
It does not decide truth.
It only produces consensus and variance signals for human review.
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from modules.consensus.types import ComparableItem, ConsensusGroup


def load_agent_payloads_from_directory(directory: Path) -> list[dict[str, Any]]:
    """Load all agent JSON payloads below a directory."""

    payloads: list[dict[str, Any]] = []

    for path in sorted(directory.rglob("*.json")):
        with path.open("r", encoding="utf-8") as file:
            payload = json.load(file)

        payload["_artifact_path"] = str(path)
        payloads.append(payload)

    return payloads


def analyze_consensus(
    *,
    team_id: str,
    task_name: str,
    agent_payloads: list[dict[str, Any]],
) -> dict[str, Any]:
    """Analyze consensus and variance for one team task."""

    comparable_items: list[ComparableItem] = []

    for payload in agent_payloads:
        comparable_items.extend(extract_comparable_items(payload))

    agent_ids = sorted(
        {
            str(payload.get("agent_id", "UNKNOWN_AGENT"))
            for payload in agent_payloads
        }
    )

    agent_labels = {
        str(payload.get("agent_id", "UNKNOWN_AGENT")): str(payload.get("persona_id", "UNKNOWN_PERSONA"))
        for payload in agent_payloads
    }

    total_agents = len(agent_ids)

    grouped_items: dict[str, list[ComparableItem]] = defaultdict(list)

    for item in comparable_items:
        grouped_items[item.group_key].append(item)

    consensus_groups = [
        evaluate_group(
            group_key=group_key,
            items=items,
            total_agents=total_agents,
        )
        for group_key, items in grouped_items.items()
    ]

    summary = summarize_groups(consensus_groups)

    return {
        "consensus_report_id": f"CONSENSUS_{team_id}_{current_timestamp()}",
        "team_id": team_id,
        "task_name": task_name,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "total_agents": total_agents,
        "agent_ids": agent_ids,
        "agent_labels": agent_labels,
        "summary": summary,
        "groups": [
            {
                "group_key": group.group_key,
                "item_type": group.item_type,
                "agreement_level": group.agreement_level,
                "total_agents": group.total_agents,
                "supporting_agents": group.supporting_agents,
                "value_distribution": group.value_distribution,
                "representative_value": group.representative_value,
                "review_required": group.review_required,
                "reason": group.reason,
                "agent_values": group.agent_values,
            }
            for group in consensus_groups
        ],
    }


def extract_comparable_items(payload: dict[str, Any]) -> list[ComparableItem]:
    """Extract comparable items from one agent payload."""

    agent_id = str(payload.get("agent_id", "UNKNOWN_AGENT"))
    persona_id = payload.get("persona_id")
    source_path = payload.get("_artifact_path")

    output_text = str(payload.get("output_text", ""))
    parsed_output = parse_json_text(output_text)

    if not isinstance(parsed_output, dict):
        return [
            fallback_item(
                payload=payload,
                agent_id=agent_id,
                persona_id=persona_id,
                source_path=source_path,
            )
        ]

    items: list[ComparableItem] = []

    items.extend(
        extract_source_information_items(
            parsed_output=parsed_output,
            agent_id=agent_id,
            persona_id=persona_id,
            source_path=source_path,
        )
    )

    items.extend(
        extract_evidence_items(
            parsed_output=parsed_output,
            agent_id=agent_id,
            persona_id=persona_id,
            source_path=source_path,
        )
    )

    items.extend(
        extract_candidate_model_element_items(
            parsed_output=parsed_output,
            agent_id=agent_id,
            persona_id=persona_id,
            source_path=source_path,
        )
    )

    items.extend(
        extract_sysml_model_buildability_items(
            parsed_output=parsed_output,
            agent_id=agent_id,
            persona_id=persona_id,
            source_path=source_path,
        )
    )

    items.extend(
        extract_derivation_items(
            parsed_output=parsed_output,
            agent_id=agent_id,
            persona_id=persona_id,
            source_path=source_path,
        )
    )

    items.extend(
        extract_gap_items(
            parsed_output=parsed_output,
            agent_id=agent_id,
            persona_id=persona_id,
            source_path=source_path,
        )
    )

    items.extend(
        extract_review_decision_items(
            parsed_output=parsed_output,
            agent_id=agent_id,
            persona_id=persona_id,
            source_path=source_path,
        )
    )

    if not items:
        items.append(
            fallback_item(
                payload=payload,
                agent_id=agent_id,
                persona_id=persona_id,
                source_path=source_path,
            )
        )

    return items


def extract_source_information_items(
    *,
    parsed_output: dict[str, Any],
    agent_id: str,
    persona_id: str | None,
    source_path: str | None,
) -> list[ComparableItem]:
    items: list[ComparableItem] = []

    for entry in parsed_output.get("source_information", []):
        if not isinstance(entry, dict):
            continue

        extracted_information = str(entry.get("extracted_information", "")).strip()

        if not extracted_information:
            continue

        normalized = normalize_text(extracted_information)

        items.append(
            ComparableItem(
                group_key=f"source_information::{normalized}",
                value_key=normalized,
                item_type="source_information",
                display_value=extracted_information,
                agent_id=agent_id,
                persona_id=persona_id,
                source_path=source_path,
                metadata=entry,
            )
        )

    return items


def extract_evidence_items(
    *,
    parsed_output: dict[str, Any],
    agent_id: str,
    persona_id: str | None,
    source_path: str | None,
) -> list[ComparableItem]:
    items: list[ComparableItem] = []

    for entry in parsed_output.get("detected_evidence", []):
        if not isinstance(entry, dict):
            continue

        evidence_type = str(entry.get("evidence_type", "")).strip()
        source_excerpt = str(entry.get("source_excerpt", "")).strip()
        source_info_id = str(entry.get("source_info_id", "")).strip()

        if not evidence_type:
            continue

        basis = source_excerpt or source_info_id or "unknown_source"
        normalized_basis = normalize_text(basis)

        group_key = f"evidence::{evidence_type}::{normalized_basis}"

        items.append(
            ComparableItem(
                group_key=group_key,
                value_key=group_key,
                item_type="detected_evidence",
                display_value=f"{evidence_type}: {basis}",
                agent_id=agent_id,
                persona_id=persona_id,
                source_path=source_path,
                metadata=entry,
            )
        )

    return items


def extract_candidate_model_element_items(
    *,
    parsed_output: dict[str, Any],
    agent_id: str,
    persona_id: str | None,
    source_path: str | None,
) -> list[ComparableItem]:
    """Extract candidate SysML model element items."""

    items: list[ComparableItem] = []

    for entry in parsed_output.get("candidate_model_elements", []):
        if not isinstance(entry, dict):
            continue

        element_type = str(entry.get("element_type", "")).strip()
        candidate_name = str(entry.get("candidate_name", "")).strip()
        readiness = str(entry.get("generation_readiness", "")).strip()

        if not element_type or not candidate_name:
            continue

        group_key = f"candidate_model_element::{normalize_text(element_type)}::{normalize_text(candidate_name)}"
        value_key = normalize_text(readiness or candidate_name)

        display = f"{element_type}: {candidate_name}"

        if readiness:
            display = f"{display} [{readiness}]"

        items.append(
            ComparableItem(
                group_key=group_key,
                value_key=value_key,
                item_type="candidate_model_element",
                display_value=display,
                agent_id=agent_id,
                persona_id=persona_id,
                source_path=source_path,
                metadata=entry,
            )
        )

    return items


def extract_sysml_model_buildability_items(
    *,
    parsed_output: dict[str, Any],
    agent_id: str,
    persona_id: str | None,
    source_path: str | None,
) -> list[ComparableItem]:
    """Extract SysML model buildability items."""

    items: list[ComparableItem] = []

    for entry in parsed_output.get("sysml_model_buildability", []):
        if not isinstance(entry, dict):
            continue

        sysml_model_type = str(entry.get("sysml_model_type", "")).strip()
        support_level = str(entry.get("support_level", "")).strip()
        generation_scope = str(entry.get("generation_scope", "")).strip()
        can_be_generated_now = entry.get("can_be_generated_now")

        if not sysml_model_type or not support_level:
            continue

        group_key = f"sysml_model_buildability::{normalize_text(sysml_model_type)}"
        value_key = normalize_text(
            f"{support_level}::{generation_scope}::{can_be_generated_now}"
        )

        display = (
            f"{sysml_model_type}: {support_level}; "
            f"can_be_generated_now={can_be_generated_now}; "
            f"scope={generation_scope}"
        )

        missing_information = entry.get("missing_information", [])
        if missing_information:
            display += f"; missing={missing_information}"

        items.append(
            ComparableItem(
                group_key=group_key,
                value_key=value_key,
                item_type="sysml_model_buildability",
                display_value=display,
                agent_id=agent_id,
                persona_id=persona_id,
                source_path=source_path,
                metadata=entry,
            )
        )

    return items


def extract_derivation_items(
    *,
    parsed_output: dict[str, Any],
    agent_id: str,
    persona_id: str | None,
    source_path: str | None,
) -> list[ComparableItem]:
    items: list[ComparableItem] = []

    for entry in parsed_output.get("model_artifact_assessments", []):
        if not isinstance(entry, dict):
            continue

        model_artifact_type = str(entry.get("model_artifact_type", "")).strip()
        support_level = str(entry.get("support_level", "")).strip()

        if not model_artifact_type or not support_level:
            continue

        group_key = f"derivation::{normalize_text(model_artifact_type)}"
        value_key = normalize_text(support_level)

        items.append(
            ComparableItem(
                group_key=group_key,
                value_key=value_key,
                item_type="model_artifact_assessment",
                display_value=f"{model_artifact_type}: {support_level}",
                agent_id=agent_id,
                persona_id=persona_id,
                source_path=source_path,
                metadata=entry,
            )
        )

    return items


def extract_gap_items(
    *,
    parsed_output: dict[str, Any],
    agent_id: str,
    persona_id: str | None,
    source_path: str | None,
) -> list[ComparableItem]:
    items: list[ComparableItem] = []

    for entry in parsed_output.get("gaps", []):
        if not isinstance(entry, dict):
            continue

        missing_information = str(entry.get("missing_information", "")).strip()

        if not missing_information:
            continue

        normalized = normalize_text(missing_information)

        items.append(
            ComparableItem(
                group_key=f"gap::{normalized}",
                value_key=normalized,
                item_type="gap",
                display_value=missing_information,
                agent_id=agent_id,
                persona_id=persona_id,
                source_path=source_path,
                metadata=entry,
            )
        )

    return items


def extract_review_decision_items(
    *,
    parsed_output: dict[str, Any],
    agent_id: str,
    persona_id: str | None,
    source_path: str | None,
) -> list[ComparableItem]:
    decision = parsed_output.get("recommended_review_decision")

    if not decision:
        return []

    decision_text = str(decision).strip()

    return [
        ComparableItem(
            group_key="recommended_review_decision",
            value_key=normalize_text(decision_text),
            item_type="recommended_review_decision",
            display_value=decision_text,
            agent_id=agent_id,
            persona_id=persona_id,
            source_path=source_path,
            metadata={"recommended_review_decision": decision_text},
        )
    ]


def fallback_item(
    *,
    payload: dict[str, Any],
    agent_id: str,
    persona_id: str | None,
    source_path: str | None,
) -> ComparableItem:
    """Create a fallback item when no structured comparable content is found."""

    output_text = str(payload.get("output_text", "")).strip()
    preview = output_text[:200] if output_text else "No structured output found."

    return ComparableItem(
        group_key=f"unstructured_output::{normalize_text(agent_id)}",
        value_key=normalize_text(preview),
        item_type="unstructured_output",
        display_value=preview,
        agent_id=agent_id,
        persona_id=persona_id,
        source_path=source_path,
        metadata={"note": "No structured comparable fields found."},
    )


def evaluate_group(
    *,
    group_key: str,
    items: list[ComparableItem],
    total_agents: int,
) -> ConsensusGroup:
    """Evaluate agreement level for one comparison group."""

    value_distribution: dict[str, list[str]] = defaultdict(list)

    for item in items:
        value_distribution[item.value_key].append(item.agent_id)

    value_distribution_plain = {
        value_key: sorted(set(agent_ids))
        for value_key, agent_ids in value_distribution.items()
    }

    best_value_key, best_agents = max(
        value_distribution_plain.items(),
        key=lambda item: len(item[1]),
    )

    best_count = len(best_agents)
    unique_value_count = len(value_distribution_plain)
    representative = first_display_value(items, best_value_key)

    if unique_value_count == 1 and best_count == total_agents:
        agreement_level = "full_agreement"
        review_required = False
        reason = "All agents produced the same comparable item."
    elif unique_value_count == 1 and best_count > total_agents / 2:
        agreement_level = "majority_agreement"
        review_required = False
        reason = "A majority of agents produced the same comparable item."
    elif unique_value_count > 1 and best_count > total_agents / 2:
        agreement_level = "majority_with_disagreement"
        review_required = True
        reason = "A majority exists, but at least one agent disagrees."
    elif best_count == 1:
        agreement_level = "minority_interpretation"
        review_required = True
        reason = "Only one agent produced this interpretation."
    else:
        agreement_level = "conflict"
        review_required = True
        reason = "Agent outputs differ without a clear majority."

    agent_values = build_agent_values(items)

    return ConsensusGroup(
        group_key=group_key,
        item_type=items[0].item_type if items else "unknown",
        agreement_level=agreement_level,
        total_agents=total_agents,
        supporting_agents=best_agents,
        value_distribution=value_distribution_plain,
        representative_value=representative,
        review_required=review_required,
        reason=reason,
        agent_values=agent_values,
    )


def build_agent_values(items: list[ComparableItem]) -> dict[str, str]:
    """Build side-by-side display values per agent."""

    grouped: dict[str, list[str]] = defaultdict(list)

    for item in items:
        grouped[item.agent_id].append(item.display_value)

    return {
        agent_id: " ; ".join(values)
        for agent_id, values in sorted(grouped.items())
    }


def first_display_value(items: list[ComparableItem], value_key: str) -> str:
    for item in items:
        if item.value_key == value_key:
            return item.display_value
    return ""


def summarize_groups(groups: list[ConsensusGroup]) -> dict[str, Any]:
    summary = {
        "total_groups": len(groups),
        "full_agreement": 0,
        "majority_agreement": 0,
        "majority_with_disagreement": 0,
        "minority_interpretation": 0,
        "conflict": 0,
        "review_required": 0,
    }

    for group in groups:
        if group.agreement_level in summary:
            summary[group.agreement_level] += 1

        if group.review_required:
            summary["review_required"] += 1

    return summary


def write_consensus_json(report: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def write_consensus_markdown(report: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    lines: list[str] = []

    lines.append("# Consensus and Variance Report")
    lines.append("")
    lines.append("## Report Metadata")
    lines.append("")
    lines.append(f"- Consensus Report ID: `{report.get('consensus_report_id')}`")
    lines.append(f"- Team ID: `{report.get('team_id')}`")
    lines.append(f"- Task Name: {report.get('task_name')}")
    lines.append(f"- Created At: {report.get('created_at')}")
    lines.append(f"- Total Agents: {report.get('total_agents')}")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append("| Metric | Count |")
    lines.append("|---|---:|")

    for key, value in report.get("summary", {}).items():
        lines.append(f"| {key} | {value} |")

    lines.append("")
    lines.append("## Agent / Persona Mapping")
    lines.append("")
    lines.append("| Agent ID | Persona ID |")
    lines.append("|---|---|")
    for agent_id, persona_id in report.get("agent_labels", {}).items():
        lines.append(f"| {sanitize_markdown_cell(agent_id)} | {sanitize_markdown_cell(persona_id)} |")

    lines.append("")
    lines.append("## Agent Comparison Matrix")
    lines.append("")
    write_agent_comparison_matrix_lines(lines, report)

    lines.append("")
    lines.append("## Consensus Groups")
    lines.append("")
    lines.append(
        "| Agreement Level | Item Type | Representative Value | Supporting Agents | Review Required | Reason |"
    )
    lines.append("|---|---|---|---|---|---|")

    for group in report.get("groups", []):
        agents = ", ".join(group.get("supporting_agents", []))
        representative = sanitize_markdown_cell(group.get("representative_value", ""))
        reason = sanitize_markdown_cell(group.get("reason", ""))

        lines.append(
            f"| {group.get('agreement_level')} | "
            f"{group.get('item_type')} | "
            f"{representative} | "
            f"{agents} | "
            f"{group.get('review_required')} | "
            f"{reason} |"
        )

    output_path.write_text("\n".join(lines), encoding="utf-8")


def parse_json_text(text: str) -> Any:
    cleaned = text.strip()

    if not cleaned:
        return None

    if cleaned.startswith("```"):
        cleaned = remove_markdown_fence(cleaned)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return None


def remove_markdown_fence(text: str) -> str:
    cleaned = text.strip()

    cleaned = re.sub(r"^```[a-zA-Z0-9_-]*\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)

    return cleaned.strip()


def normalize_text(text: str) -> str:
    cleaned = text.strip().lower()
    cleaned = re.sub(r"[^a-z0-9äöüß]+", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def write_agent_comparison_matrix_lines(lines: list[str], report: dict[str, Any]) -> None:
    """Write side-by-side agent comparison matrix into Markdown lines."""

    agent_ids = list(report.get("agent_ids", []))

    if not agent_ids:
        lines.append("No agent comparison data available.")
        return

    header = ["Item Type", "Agreement", "Representative Value"]
    header.extend(agent_ids)
    header.append("Review Required")

    lines.append("| " + " | ".join(sanitize_markdown_cell(item) for item in header) + " |")
    lines.append("|" + "|".join("---" for _ in header) + "|")

    for group in report.get("groups", []):
        row = [
            group.get("item_type", ""),
            group.get("agreement_level", ""),
            group.get("representative_value", ""),
        ]

        agent_values = group.get("agent_values", {})

        for agent_id in agent_ids:
            row.append(agent_values.get(agent_id, ""))

        row.append(str(group.get("review_required", "")))

        lines.append("| " + " | ".join(sanitize_markdown_cell(item) for item in row) + " |")


def sanitize_markdown_cell(text: str) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ").strip()


def current_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
