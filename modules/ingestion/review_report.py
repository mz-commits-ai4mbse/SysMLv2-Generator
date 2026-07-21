"""Deterministic review-oriented ingestion report generation.

This module creates a stable human-review report from structured agent outputs.

It does not call an LLM.
It does not create new engineering claims.
It does not propose relationships.
"""

from __future__ import annotations

import json
import re
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

    project_root = determine_project_root(run_dir)

    derivation_payloads = load_result_payloads(derivation_results)
    completeness_payloads = load_result_payloads(completeness_results)

    candidates = collect_candidate_elements(derivation_payloads)
    explicit_links = collect_explicit_links(derivation_payloads)
    buildability = collect_model_buildability(derivation_payloads)
    missing_information = collect_missing_information(
        derivation_payloads=derivation_payloads,
        completeness_payloads=completeness_payloads,
    )
    risks = collect_ambiguities_and_risks(
        completeness_payloads=completeness_payloads,
    )
    review_questions = collect_review_questions(
        derivation_payloads=derivation_payloads,
        completeness_payloads=completeness_payloads,
        missing_information=missing_information,
        risks=risks,
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
            project_root=project_root,
        )
    )

    lines.extend(
        build_review_dashboard(
            candidates=candidates,
            explicit_links=explicit_links,
            buildability=buildability,
            missing_information=missing_information,
            risks=risks,
            review_questions=review_questions,
        )
    )

    lines.extend(
        build_candidate_comparison_section(
            candidates=candidates,
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
        build_risks_section(
            risks=risks,
        )
    )

    lines.extend(
        build_review_questions_section(
            review_questions=review_questions,
        )
    )

    lines.extend(
        build_explicit_links_section(
            explicit_links=explicit_links,
            agent_ids=agent_ids,
        )
    )

    lines.extend(
        build_element_details_section(
            candidates=candidates,
        )
    )

    lines.extend(
        build_traceability_section(
            derivation_results=derivation_results,
            completeness_results=completeness_results,
            consensus_reports=consensus_reports,
            narrative_report_path=narrative_report_path,
            project_root=project_root,
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
                    "candidate_ids": [],
                    "agent_results": {},
                    "source_assignments": [],
                },
            )

            extend_unique(
                candidate["candidate_ids"],
                [entry.get("candidate_id", "")],
            )

            candidate["agent_results"][agent_id] = {
                "candidate_id": entry.get("candidate_id", ""),
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
    """Collect and deterministically consolidate model-building gaps.

    Derivation and completeness agents often describe the same gap with
    different wording. Consolidation therefore uses normalized token overlap;
    it never asks an LLM and never creates a new engineering statement.
    """

    items: list[dict[str, Any]] = []

    for payload in derivation_payloads:
        for entry in payload["output"].get(
            "missing_information_for_model_building",
            [],
        ):
            if not isinstance(entry, dict):
                continue

            merge_missing_information_item(
                items=items,
                description=entry.get("missing_information", ""),
                limits_or_blocks=entry.get("limits_or_blocks", []),
                needed_for=entry.get("needed_for", []),
                rationales=[],
                review_questions=[entry.get("review_question", "")],
                suggested_actions=[],
                reported_by=[payload["agent_id"]],
                source_stages=["derivation_assessment"],
                source_ids=[entry.get("missing_info_id", "")],
            )

    for payload in completeness_payloads:
        for entry in payload["output"].get("gaps", []):
            if not isinstance(entry, dict):
                continue

            merge_missing_information_item(
                items=items,
                description=entry.get("missing_information", ""),
                limits_or_blocks=[],
                needed_for=[],
                rationales=[entry.get("why_it_matters", "")],
                review_questions=[],
                suggested_actions=[entry.get("suggested_human_action", "")],
                reported_by=[payload["agent_id"]],
                source_stages=["completeness_review"],
                source_ids=[entry.get("gap_id", "")],
            )

    for index, item in enumerate(items, start=1):
        item["report_gap_id"] = f"GAP-{index:03d}"

    return items


def collect_ambiguities_and_risks(
    *,
    completeness_payloads: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Collect ambiguity and risk statements without converting them to gaps."""

    risks: list[dict[str, Any]] = []

    for payload in completeness_payloads:
        for entry in payload["output"].get("ambiguities_and_risks", []):
            if not isinstance(entry, dict):
                continue

            topic = str(entry.get("topic", "")).strip()
            description = str(entry.get("description", "")).strip()

            if not topic and not description:
                continue

            existing = find_related_record(
                records=risks,
                candidate_text=f"{topic} {description}",
                text_fields=("topic", "description"),
            )

            if existing is None:
                existing = {
                    "topic": topic,
                    "description": description,
                    "potential_impacts": [],
                    "review_actions": [],
                    "reported_by": [],
                    "source_stages": [],
                    "source_ids": [],
                }
                risks.append(existing)

            extend_unique(
                existing["potential_impacts"],
                [entry.get("potential_impact", "")],
            )
            extend_unique(
                existing["review_actions"],
                [entry.get("suggested_review_action", "")],
            )
            extend_unique(existing["reported_by"], [payload["agent_id"]])
            extend_unique(existing["source_stages"], ["completeness_review"])
            extend_unique(existing["source_ids"], [entry.get("risk_id", "")])

    for index, risk in enumerate(risks, start=1):
        risk["report_risk_id"] = f"RISK-{index:03d}"

    return risks


def collect_review_questions(
    *,
    derivation_payloads: list[dict[str, Any]],
    completeness_payloads: list[dict[str, Any]],
    missing_information: list[dict[str, Any]],
    risks: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Collect review questions not already represented by a gap action."""

    questions: list[dict[str, Any]] = []

    for payload in derivation_payloads:
        for entry in payload["output"].get(
            "possible_but_unsupported_interpretations",
            [],
        ):
            if not isinstance(entry, dict):
                continue

            question = str(entry.get("review_question", "")).strip()

            if not question:
                continue

            merge_review_question(
                questions=questions,
                question=question,
                topics=[entry.get("topic", "")],
                reasons=[entry.get("reason_not_accepted", "")],
                reported_by=[payload["agent_id"]],
                source_stages=["derivation_assessment"],
                source_ids=[],
            )

    for payload in completeness_payloads:
        for entry in payload["output"].get("review_questions", []):
            if not isinstance(entry, dict):
                continue

            question = str(entry.get("question", "")).strip()

            if not question:
                continue

            merge_review_question(
                questions=questions,
                question=question,
                topics=[entry.get("related_artifact_or_candidate", "")],
                reasons=[entry.get("reason", "")],
                reported_by=[payload["agent_id"]],
                source_stages=["completeness_review"],
                source_ids=[entry.get("question_id", "")],
            )

    independent_questions = [
        question
        for question in questions
        if not question_is_covered_by_gap(
            question=question["question"],
            missing_information=missing_information,
        )
    ]

    for index, question in enumerate(independent_questions, start=1):
        question["report_question_id"] = f"RQ-{index:03d}"
        question["related_risk_ids"] = find_related_risk_ids(
            question=question["question"],
            risks=risks or [],
        )

    return independent_questions


def merge_missing_information_item(
    *,
    items: list[dict[str, Any]],
    description: Any,
    limits_or_blocks: Any,
    needed_for: Any,
    rationales: Any,
    review_questions: Any,
    suggested_actions: Any,
    reported_by: Any,
    source_stages: Any,
    source_ids: Any,
) -> None:
    """Merge one gap record while preserving all source-provided details."""

    description_text = str(description or "").strip()

    if not description_text:
        return

    existing = find_related_record(
        records=items,
        candidate_text=description_text,
        text_fields=("missing_information",),
    )

    if existing is None:
        existing = {
            "missing_information": description_text,
            "alternative_descriptions": [],
            "limits_or_blocks": [],
            "needed_for": [],
            "rationales": [],
            "review_questions": [],
            "suggested_actions": [],
            "reported_by": [],
            "source_stages": [],
            "source_ids": [],
        }
        items.append(existing)
    elif normalize(existing["missing_information"]) != normalize(description_text):
        extend_unique(existing["alternative_descriptions"], [description_text])

    extend_unique(existing["limits_or_blocks"], limits_or_blocks)
    extend_unique(existing["needed_for"], needed_for)
    extend_unique(existing["rationales"], rationales)
    extend_unique(existing["review_questions"], review_questions)
    extend_unique(existing["suggested_actions"], suggested_actions)
    extend_unique(existing["reported_by"], reported_by)
    extend_unique(existing["source_stages"], source_stages)
    extend_unique(existing["source_ids"], source_ids)


def merge_review_question(
    *,
    questions: list[dict[str, Any]],
    question: str,
    topics: Any,
    reasons: Any,
    reported_by: Any,
    source_stages: Any,
    source_ids: Any,
) -> None:
    """Merge repeated review questions without inventing a new formulation."""

    existing = find_related_record(
        records=questions,
        candidate_text=question,
        text_fields=("question",),
    )

    if existing is None:
        existing = {
            "question": question,
            "alternative_questions": [],
            "topics": [],
            "reasons": [],
            "reported_by": [],
            "source_stages": [],
            "source_ids": [],
        }
        questions.append(existing)
    elif normalize(existing["question"]) != normalize(question):
        extend_unique(existing["alternative_questions"], [question])

    extend_unique(existing["topics"], topics)
    extend_unique(existing["reasons"], reasons)
    extend_unique(existing["reported_by"], reported_by)
    extend_unique(existing["source_stages"], source_stages)
    extend_unique(existing["source_ids"], source_ids)


def question_is_covered_by_gap(
    *,
    question: str,
    missing_information: list[dict[str, Any]],
) -> bool:
    """Return True when a question already appears as a consolidated gap action."""

    for item in missing_information:
        descriptions = [item.get("missing_information", "")]
        descriptions.extend(item.get("alternative_descriptions", []))

        if any(texts_are_related(question, value) for value in descriptions):
            return True

        if any(
            texts_are_action_equivalent(question, value)
            for value in (
                item.get("review_questions", [])
                + item.get("suggested_actions", [])
            )
        ):
            return True

    return False


def find_related_risk_ids(
    *,
    question: str,
    risks: list[dict[str, Any]],
) -> list[str]:
    """Return report risk IDs that address the same review topic."""

    related_ids: list[str] = []

    for risk in risks:
        comparison_values = [
            risk.get("topic", ""),
            risk.get("description", ""),
        ]
        comparison_values.extend(risk.get("review_actions", []))

        if any(
            texts_are_related(question, value)
            or texts_are_action_equivalent(question, value)
            for value in comparison_values
        ):
            extend_unique(
                related_ids,
                [risk.get("report_risk_id", "")],
            )

    return related_ids


def find_related_record(
    *,
    records: list[dict[str, Any]],
    candidate_text: str,
    text_fields: tuple[str, ...],
) -> dict[str, Any] | None:
    """Find the first deterministically related record."""

    for record in records:
        record_text = " ".join(
            str(record.get(field, ""))
            for field in text_fields
        )

        if texts_are_related(candidate_text, record_text):
            return record

    return None


def texts_are_related(left: Any, right: Any) -> bool:
    """Compare two statements using deterministic significant-token overlap."""

    left_tokens = significant_tokens(left)
    right_tokens = significant_tokens(right)

    if not left_tokens or not right_tokens:
        return False

    if left_tokens == right_tokens:
        return True

    intersection_size = len(left_tokens & right_tokens)

    if intersection_size < 3:
        return False

    union_size = len(left_tokens | right_tokens)
    smaller_size = min(len(left_tokens), len(right_tokens))

    jaccard = intersection_size / union_size
    containment = intersection_size / smaller_size

    return (
        jaccard >= 0.45
        or containment >= 0.65
        or (intersection_size >= 4 and jaccard >= 0.33)
    )


def texts_are_action_equivalent(left: Any, right: Any) -> bool:
    """Use a slightly broader match for two review-action formulations."""

    left_tokens = significant_tokens(left)
    right_tokens = significant_tokens(right)

    if not left_tokens or not right_tokens:
        return False

    intersection_size = len(left_tokens & right_tokens)
    generic_entity_tokens = {
        "application",
        "client",
        "component",
        "element",
        "information",
        "microscope",
        "model",
        "session",
        "software",
        "system",
        "workstation",
    }
    action_specific_overlap = (
        left_tokens & right_tokens
    ) - generic_entity_tokens

    if intersection_size < 3 or not action_specific_overlap:
        return False

    union_size = len(left_tokens | right_tokens)
    smaller_size = min(len(left_tokens), len(right_tokens))

    jaccard = intersection_size / union_size
    containment = intersection_size / smaller_size

    return jaccard >= 0.30 or containment >= 0.50


def significant_tokens(value: Any) -> set[str]:
    """Return normalized content tokens for deterministic comparison."""

    aliases = {
        "acceptance": "accept",
        "activities": "activity",
        "boundaries": "boundary",
        "cases": "case",
        "components": "component",
        "criteria": "criterion",
        "definitions": "definition",
        "directionality": "direction",
        "directions": "direction",
        "distinct": "separate",
        "endpoints": "endpoint",
        "fields": "field",
        "formats": "format",
        "interfaces": "interface",
        "messages": "message",
        "models": "model",
        "postconditions": "postcondition",
        "preconditions": "precondition",
        "protocols": "protocol",
        "questions": "question",
        "requirements": "requirement",
        "represented": "representation",
        "transported": "transport",
        "scenarios": "scenario",
        "tests": "test",
        "thresholds": "threshold",
        "verification": "validation",
    }
    stopwords = {
        "a", "an", "and", "are", "as", "at", "be", "between", "by",
        "can", "for", "from", "how", "in", "is", "it", "of", "or",
        "such", "that", "the", "their", "this", "to", "used", "what",
        "when", "where", "which", "who", "with",
    }

    tokens = re.findall(r"[a-z0-9]+", str(value or "").lower())

    return {
        aliases.get(token, token)
        for token in tokens
        if token not in stopwords and len(token) > 1
    }


def extend_unique(target: list[str], values: Any) -> None:
    """Append non-empty values once while retaining original wording and order."""

    if isinstance(values, (list, tuple, set)):
        candidates = values
    else:
        candidates = [values]

    seen = {normalize(value) for value in target}

    for value in candidates:
        text = str(value or "").strip()
        key = normalize(text)

        if not text or key in seen:
            continue

        target.append(text)
        seen.add(key)


def build_header(
    *,
    task_id: str,
    recipe_id: str,
    raw_input_path: Path,
    run_id: str,
    run_dir: Path,
    project_root: Path,
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
        f"- Source: `{repository_relative_path(raw_input_path, project_root)}`",
        f"- Run Directory: `{repository_relative_path(run_dir, project_root)}`",
        "",
    ]


def build_review_dashboard(
    *,
    candidates: dict[str, dict[str, Any]],
    explicit_links: list[dict[str, Any]],
    buildability: dict[str, dict[str, Any]],
    missing_information: list[dict[str, Any]],
    risks: list[dict[str, Any]],
    review_questions: list[dict[str, Any]],
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
        f"| Consolidated missing-information items | {len(missing_information)} |",
        f"| Ambiguities and risks | {len(risks)} |",
        f"| Independent review questions | {len(review_questions)} |",
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

    if len(agent_ids) == 1:
        lines.extend(
            [
                "> Single-agent execution: candidate identification has not "
                "been cross-checked by another agent.",
                "",
            ]
        )

    header = ["Candidate ID", "Element Type", "Candidate"]
    header.extend(agent_ids)
    header.extend(["Agreement", "Review Required"])

    lines.append(markdown_row(header))
    lines.append(markdown_separator(len(header)))

    for candidate in candidates.values():
        row = [
            join_values(candidate.get("candidate_ids", [])),
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

        if len(agent_ids) == 1:
            agreement = "Single-agent observation — no cross-agent consensus"
        elif agent_ids and identified_count == len(agent_ids):
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
        "## 8. Element Details and Assigned Source Content",
        "",
    ]

    if not candidates:
        lines.extend(["No element details available.", ""])
        return lines

    for index, candidate in enumerate(candidates.values(), start=1):
        display_id = candidate_display_id(candidate, index)
        lines.extend(
            [
                f"### {display_id} — {candidate['candidate_name']}",
                "",
                f"- Candidate IDs: "
                f"{', '.join(candidate.get('candidate_ids', [])) or 'Not provided'}",
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
        "## 7. Explicit Source-Based Links",
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
            "| Link ID | Source Candidate | Link Type | Target Candidate | "
            "Source Statement | Confidence | Agent / Persona |",
            "|---|---|---|---|---|---|---|",
        ]
    )

    for link in explicit_links:
        lines.append(
            markdown_row(
                [
                    link.get("link_id", ""),
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
        "## 3. Buildable SysML Models",
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

    if len(agent_ids) == 1:
        lines.extend(
            [
                "> Single-agent execution: buildability assessments have not "
                "been cross-checked by another agent.",
                "",
            ]
        )

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

        if len(agent_ids) == 1:
            review_signal = "Single-agent assessment — no cross-agent consensus"
        elif len(signatures) <= 1:
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
        "## 4. Missing Information for Further Modeling",
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
            "| Gap ID | Missing Information | Limits or Blocks | Needed For | "
            "Why It Matters | Review Question | Suggested Action | Evidence Origin |",
            "|---|---|---|---|---|---|---|---|",
        ]
    )

    for item in missing_information:
        lines.append(
            markdown_row(
                [
                    item.get("report_gap_id", ""),
                    item.get("missing_information", ""),
                    join_values(item.get("limits_or_blocks", [])),
                    join_values(item.get("needed_for", [])),
                    join_values(item.get("rationales", [])),
                    join_values(item.get("review_questions", [])),
                    join_values(item.get("suggested_actions", [])),
                    format_evidence_origin(item),
                ]
            )
        )

    lines.append("")
    return lines


def build_risks_section(
    *,
    risks: list[dict[str, Any]],
) -> list[str]:
    lines = [
        "## 5. Ambiguities and Risks",
        "",
    ]

    if not risks:
        lines.extend(
            [
                "No structured ambiguity or risk items were returned.",
                "",
            ]
        )
        return lines

    lines.extend(
        [
            "| Risk ID | Topic | Description | Potential Impact | "
            "Review Action | Evidence Origin |",
            "|---|---|---|---|---|---|",
        ]
    )

    for risk in risks:
        lines.append(
            markdown_row(
                [
                    risk.get("report_risk_id", ""),
                    risk.get("topic", ""),
                    risk.get("description", ""),
                    join_values(risk.get("potential_impacts", [])),
                    join_values(risk.get("review_actions", [])),
                    format_evidence_origin(risk),
                ]
            )
        )

    lines.append("")
    return lines


def build_review_questions_section(
    *,
    review_questions: list[dict[str, Any]],
) -> list[str]:
    lines = [
        "## 6. Review Questions",
        "",
        "> Questions already represented by a consolidated gap action are not "
        "repeated in this section.",
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
            "| Question ID | Question | Related Topic / References | "
            "Related Risks | Why Review Is Required | Evidence Origin |",
            "|---|---|---|---|---|---|",
        ]
    )

    for item in review_questions:
        lines.append(
            markdown_row(
                [
                    item.get("report_question_id", ""),
                    item.get("question", ""),
                    join_values(item.get("topics", [])),
                    join_values(item.get("related_risk_ids", [])),
                    join_values(item.get("reasons", [])),
                    format_evidence_origin(item),
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
    project_root: Path,
) -> list[str]:
    lines = [
        "## 9. Technical Traceability",
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
                    repository_relative_path(result.output_path, project_root),
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
                    review_required_group_count(report),
                ]
            )
        )

    if narrative_report_path is not None:
        lines.extend(
            [
                "",
                "### Narrative Supplement",
                "",
                f"`{repository_relative_path(narrative_report_path, project_root)}`",
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


def format_evidence_origin(item: dict[str, Any]) -> str:
    """Format source stage, source identifiers and reporting agents."""

    parts: list[str] = []

    if item.get("source_stages"):
        parts.append(
            "Stages: " + ", ".join(item["source_stages"])
        )

    if item.get("source_ids"):
        parts.append(
            "Source IDs: " + ", ".join(item["source_ids"])
        )

    if item.get("reported_by"):
        parts.append(
            "Agents: " + ", ".join(item["reported_by"])
        )

    return "<br>".join(parts)


def candidate_display_id(
    candidate: dict[str, Any],
    fallback_index: int,
) -> str:
    """Return a source-provided candidate ID or a report-local fallback."""

    candidate_ids = candidate.get("candidate_ids", [])

    if len(candidate_ids) == 1:
        return str(candidate_ids[0])

    return f"REPORT_ELEM_{fallback_index:03d}"


def determine_project_root(run_dir: Path) -> Path:
    """Determine the repository root from a run directory."""

    resolved_run_dir = run_dir.resolve()

    for candidate in [resolved_run_dir, *resolved_run_dir.parents]:
        if (candidate / "modules").is_dir() and (candidate / "data").is_dir():
            return candidate

    if len(resolved_run_dir.parents) > 3:
        return resolved_run_dir.parents[3]

    return resolved_run_dir.parent


def repository_relative_path(path: Path, project_root: Path) -> str:
    """Render repository-owned paths without machine-specific prefixes."""

    try:
        return str(path.resolve().relative_to(project_root.resolve()))
    except ValueError:
        return str(path)


def review_required_group_count(report: dict[str, Any]) -> int:
    """Return a stable review-required count for old and new reports."""

    summary = report.get("summary", {})
    summary_value = summary.get("review_required")

    if isinstance(summary_value, int):
        return summary_value

    return sum(
        1
        for group in report.get("groups", [])
        if group.get("review_required") is True
    )


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
    text = "" if value is None else str(value)

    return (
        text
        .replace("|", "\\|")
        .replace("\n", " ")
        .strip()
    )


def markdown_row(values: list[Any]) -> str:
    return "| " + " | ".join(sanitize(value) for value in values) + " |"


def markdown_separator(column_count: int) -> str:
    return "|" + "|".join("---" for _ in range(column_count)) + "|"
