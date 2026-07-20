"""Deterministic review-oriented ingestion report generation.

This module creates a stable human-review report from structured agent outputs.

It does not call an LLM.
It does not create new engineering claims.
It does not propose relationships.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from modules.agents.types import AgentRunResult


def write_ingestion_review_report(
    *,
    task_id: str,
    recipe_id: str,
    raw_input_path: Path,
    run_id: str,
    run_dir: Path,
    report_output_path: Path,
    derivation_results: list[AgentRunResult],
    completeness_results: list[AgentRunResult],
    consensus_reports: list[dict[str, Any]],
    narrative_report_path: Path | None = None,
) -> None:
    """Build and write the deterministic ingestion review report."""

    derivation_payloads = load_result_payloads(derivation_results)
    completeness_payloads = load_result_payloads(completeness_results)

    candidates = collect_candidate_elements(derivation_payloads)
    explicit_links = collect_explicit_links(derivation_payloads)
    buildability = collect_model_buildability(derivation_payloads)
    missing_information = collect_missing_information(
        derivation_payloads=derivation_payloads,
        completeness_payloads=completeness_payloads,
    )
    review_questions = collect_review_questions(
        derivation_payloads=derivation_payloads,
        completeness_payloads=completeness_payloads,
    )

    agent_ids = sorted(
        {
            payload.get("agent_id", "UNKNOWN_AGENT")
            for payload in derivation_payloads
        }
    )

    lines: list[str] = []

    lines.extend(
        build_header(
            task_id=task_id,
            recipe_id=recipe_id,
            raw_input_path=raw_input_path,
            run_id=run_id,
            run_dir=run_dir,
        )
    )

    lines.extend(
        build_review_dashboard(
            candidates=candidates,
            explicit_links=explicit_links,
            buildability=buildability,
            missing_information=missing_information,
        )
    )

    lines.extend(
        build_candidate_comparison_section(
            candidates=candidates,
            agent_ids=agent_ids,
        )
    )

    lines.extend(
        build_element_details_section(
            candidates=candidates,
        )
    )

    lines.extend(
        build_explicit_links_section(
            explicit_links=explicit_links,
            agent_ids=agent_ids,
        )
    )

    lines.extend(
        build_model_buildability_section(
            buildability=buildability,
            agent_ids=agent_ids,
        )
    )

    lines.extend(
        build_missing_information_section(
            missing_information=missing_information,
        )
    )

    lines.extend(
        build_review_questions_section(
            review_questions=review_questions,
        )
    )

    lines.extend(
        build_traceability_section(
            derivation_results=derivation_results,
            completeness_results=completeness_results,
            consensus_reports=consensus_reports,
            narrative_report_path=narrative_report_path,
        )
    )

    report_output_path.parent.mkdir(parents=True, exist_ok=True)
    report_output_path.write_text("\n".join(lines), encoding="utf-8")


def load_result_payloads(
    results: list[AgentRunResult],
) -> list[dict[str, Any]]:
    """Load structured output payloads from agent result artifacts."""

    payloads: list[dict[str, Any]] = []

    for result in results:
        wrapper = json.loads(result.output_path.read_text(encoding="utf-8"))
        parsed_output = parse_json_output(wrapper.get("output_text", ""))

        payloads.append(
            {
                "agent_id": wrapper.get("agent_id", result.agent_id),
                "persona_id": wrapper.get("persona_id", "UNKNOWN_PERSONA"),
                "output_path": str(result.output_path),
                "output": parsed_output if isinstance(parsed_output, dict) else {},
            }
        )

    return payloads


def parse_json_output(text: str) -> Any:
    """Parse agent JSON output, including Markdown-fenced JSON."""

    cleaned = str(text or "").strip()

    if cleaned.startswith("```"):
        lines = cleaned.splitlines()

        if lines and lines[0].startswith("```"):
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        cleaned = "\n".join(lines).strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return None


def collect_candidate_elements(
    payloads: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Collect candidate elements and preserve per-agent assessments."""

    candidates: dict[str, dict[str, Any]] = {}

    for payload in payloads:
        agent_id = str(payload["agent_id"])
        persona_id = str(payload["persona_id"])

        for entry in payload["output"].get("candidate_model_elements", []):
            if not isinstance(entry, dict):
                continue

            element_type = str(entry.get("element_type", "other")).strip()
            candidate_name = str(entry.get("candidate_name", "")).strip()

            if not candidate_name:
                continue

            key = candidate_key(element_type, candidate_name)

            candidate = candidates.setdefault(
                key,
                {
                    "element_type": element_type,
                    "candidate_name": candidate_name,
                    "agent_results": {},
                    "source_assignments": [],
                },
            )

            candidate["agent_results"][agent_id] = {
                "persona_id": persona_id,
                "description": entry.get("description", ""),
                "confidence": entry.get("confidence", ""),
                "generation_readiness": entry.get("generation_readiness", ""),
                "source_basis": entry.get("source_basis", []),
                "missing_information": entry.get("missing_information", []),
                "rationale_summary": entry.get("rationale_summary", ""),
            }

            for assignment in entry.get("assigned_source_information", []):
                if not isinstance(assignment, dict):
                    continue

                candidate["source_assignments"].append(
                    {
                        "agent_id": agent_id,
                        "persona_id": persona_id,
                        "source_info_id": assignment.get("source_info_id", ""),
                        "source_statement": assignment.get("source_statement", ""),
                        "assignment_type": assignment.get("assignment_type", ""),
                        "confidence": assignment.get("confidence", ""),
                    }
                )

    return candidates


def collect_explicit_links(
    payloads: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Collect only links explicitly returned as source-supported."""

    links: list[dict[str, Any]] = []

    for payload in payloads:
        for entry in payload["output"].get("explicit_source_links", []):
            if not isinstance(entry, dict):
                continue

            links.append(
                {
                    "agent_id": payload["agent_id"],
                    "persona_id": payload["persona_id"],
                    **entry,
                }
            )

    return links


def collect_model_buildability(
    payloads: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Collect per-agent SysML model buildability assessments."""

    buildability: dict[str, dict[str, Any]] = {}

    for payload in payloads:
        agent_id = str(payload["agent_id"])
        persona_id = str(payload["persona_id"])

        for entry in payload["output"].get("sysml_model_buildability", []):
            if not isinstance(entry, dict):
                continue

            model_type = str(entry.get("sysml_model_type", "")).strip()

            if not model_type:
                continue

            model = buildability.setdefault(
                model_type,
                {
                    "agent_results": {},
                },
            )

            model["agent_results"][agent_id] = {
                "persona_id": persona_id,
                "support_level": entry.get("support_level", ""),
                "can_be_generated_now": entry.get("can_be_generated_now"),
                "generation_scope": entry.get("generation_scope", ""),
                "available_information": entry.get("available_information", []),
                "evidence_basis": entry.get("evidence_basis", []),
                "missing_information": entry.get("missing_information", []),
                "reason": entry.get("reason", ""),
                "recommended_action": entry.get("recommended_action", ""),
            }

    return buildability


def collect_missing_information(
    *,
    derivation_payloads: list[dict[str, Any]],
    completeness_payloads: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Collect missing information from derivation and completeness stages."""

    items: list[dict[str, Any]] = []
    seen: set[str] = set()

    for payload in derivation_payloads:
        for entry in payload["output"].get(
            "missing_information_for_model_building",
            [],
        ):
            if not isinstance(entry, dict):
                continue

            description = str(entry.get("missing_information", "")).strip()
            key = normalize(description)

            if not description or key in seen:
                continue

            seen.add(key)
            items.append(
                {
                    "missing_information": description,
                    "limits_or_blocks": entry.get("limits_or_blocks", []),
                    "needed_for": entry.get("needed_for", []),
                    "review_question": entry.get("review_question", ""),
                    "reported_by": [payload["agent_id"]],
                }
            )

    for payload in completeness_payloads:
        for entry in payload["output"].get("gaps", []):
            if not isinstance(entry, dict):
                continue

            description = str(entry.get("missing_information", "")).strip()
            key = normalize(description)

            if not description:
                continue

            if key in seen:
                continue

            seen.add(key)
            items.append(
                {
                    "missing_information": description,
                    "limits_or_blocks": [entry.get("why_it_matters", "")],
                    "needed_for": [],
                    "review_question": entry.get("suggested_human_action", ""),
                    "reported_by": [payload["agent_id"]],
                }
            )

    return items


def collect_review_questions(
    *,
    derivation_payloads: list[dict[str, Any]],
    completeness_payloads: list[dict[str, Any]],
) -> list[dict[str, str]]:
    """Collect explicit human-review questions."""

    questions: list[dict[str, str]] = []
    seen: set[str] = set()

    for payload in derivation_payloads:
        for entry in payload["output"].get(
            "possible_but_unsupported_interpretations",
            [],
        ):
            if not isinstance(entry, dict):
                continue

            question = str(entry.get("review_question", "")).strip()

            if not question or normalize(question) in seen:
                continue

            seen.add(normalize(question))
            questions.append(
                {
                    "question": question,
                    "topic": str(entry.get("topic", "")),
                    "reason": str(entry.get("reason_not_accepted", "")),
                }
            )

    for payload in completeness_payloads:
        for entry in payload["output"].get("review_questions", []):
            if not isinstance(entry, dict):
                continue

            question = str(entry.get("question", "")).strip()

            if not question or normalize(question) in seen:
                continue

            seen.add(normalize(question))
            questions.append(
                {
                    "question": question,
                    "topic": str(
                        entry.get("related_artifact_or_candidate", "")
                    ),
                    "reason": str(entry.get("reason", "")),
                }
            )

    return questions


def build_header(
    *,
    task_id: str,
    recipe_id: str,
    raw_input_path: Path,
    run_id: str,
    run_dir: Path,
) -> list[str]:
    return [
        "# Ingestion Review Report",
        "",
        "> **Status: Unreviewed agentic output.** "
        "Human review is required before any information may be approved "
        "for model generation.",
        "",
        "## Report Metadata",
        "",
        f"- Task ID: `{task_id}`",
        f"- Recipe ID: `{recipe_id}`",
        f"- Run ID: `{run_id}`",
        f"- Source: `{raw_input_path}`",
        f"- Run Directory: `{run_dir}`",
        "",
    ]


def build_review_dashboard(
    *,
    candidates: dict[str, dict[str, Any]],
    explicit_links: list[dict[str, Any]],
    buildability: dict[str, dict[str, Any]],
    missing_information: list[dict[str, Any]],
) -> list[str]:
    ready_models = sum(
        1
        for model in buildability.values()
        if any(
            result.get("can_be_generated_now") is True
            for result in model["agent_results"].values()
        )
    )

    review_candidates = sum(
        1
        for candidate in candidates.values()
        if candidate_requires_review(candidate)
    )

    return [
        "## 1. Review Dashboard",
        "",
        "| Review Metric | Result |",
        "|---|---:|",
        f"| Recognized element candidates | {len(candidates)} |",
        f"| Element candidates requiring review | {review_candidates} |",
        f"| Explicit source-based links | {len(explicit_links)} |",
        f"| Assessed SysML model types | {len(buildability)} |",
        f"| Models considered preliminarily buildable by at least one agent | {ready_models} |",
        f"| Missing-information items | {len(missing_information)} |",
        "",
    ]


def build_candidate_comparison_section(
    *,
    candidates: dict[str, dict[str, Any]],
    agent_ids: list[str],
) -> list[str]:
    lines = [
        "## 2. Recognized Elements — Agent Comparison",
        "",
    ]

    if not candidates:
        lines.extend(
            [
                "No candidate model elements were identified.",
                "",
            ]
        )
        return lines

    header = ["Element Type", "Candidate"]
    header.extend(agent_ids)
    header.extend(["Agreement", "Review Required"])

    lines.append(markdown_row(header))
    lines.append(markdown_separator(len(header)))

    for candidate in candidates.values():
        row = [
            candidate["element_type"],
            candidate["candidate_name"],
        ]

        for agent_id in agent_ids:
            result = candidate["agent_results"].get(agent_id)

            if result is None:
                row.append("Not identified")
                continue

            row.append(
                "<br>".join(
                    [
                        f"Confidence: {result.get('confidence', '')}",
                        f"Readiness: {result.get('generation_readiness', '')}",
                        sanitize(result.get("description", "")),
                    ]
                )
            )

        identified_count = len(candidate["agent_results"])

        if agent_ids and identified_count == len(agent_ids):
            agreement = "All agents identified candidate"
        elif identified_count > len(agent_ids) / 2:
            agreement = "Majority identified candidate"
        else:
            agreement = "Minority identification"

        row.extend(
            [
                agreement,
                "Yes" if candidate_requires_review(candidate) else "No",
            ]
        )

        lines.append(markdown_row(row))

    lines.append("")
    lines.append(
        "Candidate grouping currently uses normalized element type and candidate name. "
        "Semantically equivalent names may therefore still appear as separate candidates "
        "and should be checked during review."
    )
    lines.append("")

    return lines


def build_element_details_section(
    *,
    candidates: dict[str, dict[str, Any]],
) -> list[str]:
    lines = [
        "## 3. Element Details and Assigned Source Content",
        "",
    ]

    if not candidates:
        lines.extend(["No element details available.", ""])
        return lines

    for index, candidate in enumerate(candidates.values(), start=1):
        lines.extend(
            [
                f"### ELEM-{index:03d} — {candidate['candidate_name']}",
                "",
                f"- Element Type: `{candidate['element_type']}`",
                f"- Agents Identifying Candidate: "
                f"{', '.join(candidate['agent_results'].keys())}",
                f"- Review Required: "
                f"{'Yes' if candidate_requires_review(candidate) else 'No'}",
                "",
                "#### Agent Assessments",
                "",
                "| Agent | Persona | Confidence | Readiness | Description | "
                "Source Basis | Missing Information |",
                "|---|---|---|---|---|---|---|",
            ]
        )

        for agent_id, result in candidate["agent_results"].items():
            lines.append(
                markdown_row(
                    [
                        agent_id,
                        result.get("persona_id", ""),
                        result.get("confidence", ""),
                        result.get("generation_readiness", ""),
                        result.get("description", ""),
                        join_values(result.get("source_basis", [])),
                        join_values(result.get("missing_information", [])),
                    ]
                )
            )

        lines.extend(
            [
                "",
                "#### Assigned Source Information",
                "",
            ]
        )

        assignments = deduplicate_assignments(
            candidate["source_assignments"]
        )

        if not assignments:
            lines.extend(
                [
                    "No structured source-to-element assignments were returned.",
                    "",
                ]
            )
            continue

        lines.extend(
            [
                "| Source Info ID | Source Statement | Assignment Type | "
                "Confidence | Reported By |",
                "|---|---|---|---|---|",
            ]
        )

        for assignment in assignments:
            lines.append(
                markdown_row(
                    [
                        assignment.get("source_info_id", ""),
                        assignment.get("source_statement", ""),
                        assignment.get("assignment_type", ""),
                        assignment.get("confidence", ""),
                        assignment.get("agent_id", ""),
                    ]
                )
            )

        lines.append("")

    return lines


def build_explicit_links_section(
    *,
    explicit_links: list[dict[str, Any]],
    agent_ids: list[str],
) -> list[str]:
    lines = [
        "## 4. Explicit Source-Based Links",
        "",
        "> No relationships are proposed in this ingestion stage. "
        "The table contains only links that an agent considered directly "
        "supported by source material.",
        "",
    ]

    if not explicit_links:
        lines.extend(
            [
                "No explicit source-based links were identified.",
                "",
            ]
        )
        return lines

    lines.extend(
        [
            "| Source Candidate | Link Type | Target Candidate | "
            "Source Statement | Confidence | Agent / Persona |",
            "|---|---|---|---|---|---|",
        ]
    )

    for link in explicit_links:
        lines.append(
            markdown_row(
                [
                    link.get("source_element_candidate", ""),
                    link.get("link_type", ""),
                    link.get("target_element_candidate", ""),
                    link.get("source_statement", ""),
                    link.get("confidence", ""),
                    (
                        f"{link.get('agent_id', '')} / "
                        f"{link.get('persona_id', '')}"
                    ),
                ]
            )
        )

    lines.append("")
    return lines


def build_model_buildability_section(
    *,
    buildability: dict[str, dict[str, Any]],
    agent_ids: list[str],
) -> list[str]:
    lines = [
        "## 5. Buildable SysML Models",
        "",
        "> `can_be_generated_now = true` means only that a preliminary "
        "model candidate may be generated for further human review.",
        "",
    ]

    if not buildability:
        lines.extend(
            [
                "No structured model-buildability assessment was returned.",
                "",
            ]
        )
        return lines

    header = ["SysML Model Type"]
    header.extend(agent_ids)
    header.extend(["Overall Review Signal", "Consolidated Missing Information"])

    lines.append(markdown_row(header))
    lines.append(markdown_separator(len(header)))

    for model_type, model in buildability.items():
        row = [model_type]

        for agent_id in agent_ids:
            result = model["agent_results"].get(agent_id)

            if result is None:
                row.append("No assessment")
                continue

            row.append(
                "<br>".join(
                    [
                        f"Support: {result.get('support_level', '')}",
                        f"Generate now: {result.get('can_be_generated_now')}",
                        f"Scope: {result.get('generation_scope', '')}",
                        f"Reason: {sanitize(result.get('reason', ''))}",
                    ]
                )
            )

        assessments = list(model["agent_results"].values())
        signatures = {
            (
                item.get("support_level"),
                item.get("can_be_generated_now"),
                item.get("generation_scope"),
            )
            for item in assessments
        }

        if len(signatures) <= 1:
            review_signal = "Assessments aligned"
        else:
            review_signal = "Conflicting assessments — review required"

        consolidated_missing = sorted(
            {
                str(missing)
                for item in assessments
                for missing in item.get("missing_information", [])
                if str(missing).strip()
            }
        )

        row.extend(
            [
                review_signal,
                join_values(consolidated_missing),
            ]
        )

        lines.append(markdown_row(row))

    lines.append("")
    return lines


def build_missing_information_section(
    *,
    missing_information: list[dict[str, Any]],
) -> list[str]:
    lines = [
        "## 6. Missing Information for Further Modeling",
        "",
    ]

    if not missing_information:
        lines.extend(
            [
                "No structured missing-information items were returned.",
                "",
            ]
        )
        return lines

    lines.extend(
        [
            "| Missing Information | Limits or Blocks | Needed For | "
            "Review Question / Action |",
            "|---|---|---|---|",
        ]
    )

    for item in missing_information:
        lines.append(
            markdown_row(
                [
                    item.get("missing_information", ""),
                    join_values(item.get("limits_or_blocks", [])),
                    join_values(item.get("needed_for", [])),
                    item.get("review_question", ""),
                ]
            )
        )

    lines.append("")
    return lines


def build_review_questions_section(
    *,
    review_questions: list[dict[str, str]],
) -> list[str]:
    lines = [
        "## 7. Review Questions",
        "",
    ]

    if not review_questions:
        lines.extend(
            [
                "No explicit review questions were returned.",
                "",
            ]
        )
        return lines

    lines.extend(
        [
            "| Question | Related Topic | Why Review Is Required |",
            "|---|---|---|",
        ]
    )

    for item in review_questions:
        lines.append(
            markdown_row(
                [
                    item.get("question", ""),
                    item.get("topic", ""),
                    item.get("reason", ""),
                ]
            )
        )

    lines.append("")
    return lines


def build_traceability_section(
    *,
    derivation_results: list[AgentRunResult],
    completeness_results: list[AgentRunResult],
    consensus_reports: list[dict[str, Any]],
    narrative_report_path: Path | None,
) -> list[str]:
    lines = [
        "## 8. Technical Traceability",
        "",
        "### Agent Output Artifacts",
        "",
        "| Agent | Task | Output Artifact |",
        "|---|---|---|",
    ]

    for result in derivation_results + completeness_results:
        lines.append(
            markdown_row(
                [
                    result.agent_id,
                    result.task_name,
                    str(result.output_path),
                ]
            )
        )

    lines.extend(
        [
            "",
            "### Consensus Reports",
            "",
            "| Team | Total Groups | Review-Required Groups |",
            "|---|---:|---:|",
        ]
    )

    for report in consensus_reports:
        summary = report.get("summary", {})
        lines.append(
            markdown_row(
                [
                    report.get("team_id", ""),
                    summary.get("total_groups", 0),
                    summary.get("review_required", 0),
                ]
            )
        )

    if narrative_report_path is not None:
        lines.extend(
            [
                "",
                "### Narrative Supplement",
                "",
                f"`{narrative_report_path}`",
            ]
        )

    lines.extend(
        [
            "",
            "## Review Gate Rule",
            "",
            "This report stops before the human ingestion review gate. "
            "No candidate element, source assignment, explicit link or model "
            "buildability decision may be treated as approved input until a "
            "human reviewer has accepted and promoted the relevant information.",
            "",
        ]
    )

    return lines


def candidate_requires_review(candidate: dict[str, Any]) -> bool:
    """Determine whether a candidate needs human attention."""

    results = list(candidate["agent_results"].values())

    if len(results) <= 1:
        return True

    signatures = {
        (
            result.get("confidence"),
            result.get("generation_readiness"),
            normalize(result.get("description", "")),
        )
        for result in results
    }

    return len(signatures) > 1


def deduplicate_assignments(
    assignments: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    unique: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str, str]] = set()

    for assignment in assignments:
        key = (
            normalize(assignment.get("source_info_id", "")),
            normalize(assignment.get("source_statement", "")),
            normalize(assignment.get("assignment_type", "")),
            normalize(assignment.get("agent_id", "")),
        )

        if key in seen:
            continue

        seen.add(key)
        unique.append(assignment)

    return unique


def candidate_key(element_type: str, candidate_name: str) -> str:
    return f"{normalize(element_type)}::{normalize(candidate_name)}"


def normalize(value: Any) -> str:
    return " ".join(str(value or "").strip().lower().split())


def join_values(values: Any) -> str:
    if isinstance(values, list):
        cleaned = [
            sanitize(value)
            for value in values
            if str(value).strip()
        ]
        return "<br>".join(cleaned)

    return sanitize(values)


def sanitize(value: Any) -> str:
    return (
        str(value or "")
        .replace("|", "\\|")
        .replace("\n", " ")
        .strip()
    )


def markdown_row(values: list[Any]) -> str:
    return "| " + " | ".join(sanitize(value) for value in values) + " |"


def markdown_separator(column_count: int) -> str:
    return "|" + "|".join("---" for _ in range(column_count)) + "|"
