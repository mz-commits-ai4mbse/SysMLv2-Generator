"""Input builders for agentic ingestion.

This module only builds text inputs for agent and team execution.

It does not call LLMs.
It does not run agents.
It does not perform consensus analysis.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from modules.agents.types import AgentRunResult
from modules.source_analysis_units.types import (
    SourceAnalysisUnit,
)


def _source_analysis_unit_context(
    unit: SourceAnalysisUnit,
) -> str:
    """Render the immutable source scope shared by all Personas."""

    return f"""
# Canonical Source Analysis Unit

Source Analysis Unit ID: {unit.source_analysis_unit_id}
Source ID: {unit.source_id}
Source Projection ID: {unit.source_projection_id}
Source Order Index: {unit.source_order_index}
Segmentation Profile: {unit.segmentation_profile_id} {unit.segmentation_profile_version}

Interpret only the exact Source Analysis Unit excerpt supplied below as
positive source material. The Source Analysis Unit identity is fixed before
Persona interpretation and must not be renamed, replaced or re-segmented.
""".strip()


def build_source_anchored_initial_interpretation_input(
    *,
    source_analysis_unit: SourceAnalysisUnit,
    task_id: str,
    recipe_id: str,
    raw_input_path: Path,
    recipe_text: str,
    global_principles_text: str,
) -> str:
    """Build legacy interpretation input for one canonical source unit."""

    return (
        _source_analysis_unit_context(source_analysis_unit)
        + "\n\n"
        + build_initial_interpretation_input(
            task_id=task_id,
            recipe_id=recipe_id,
            raw_input_path=raw_input_path,
            raw_text=source_analysis_unit.source_excerpt,
            recipe_text=recipe_text,
            global_principles_text=global_principles_text,
        )
    )


def build_source_anchored_evidence_classification_input(
    *,
    source_analysis_unit: SourceAnalysisUnit,
    task_id: str,
    raw_input_path: Path,
    interpretation_results: list[AgentRunResult],
    interpretation_consensus: dict[str, Any],
) -> str:
    """Build evidence input for one canonical source unit."""

    return (
        _source_analysis_unit_context(source_analysis_unit)
        + "\n\n"
        + build_evidence_classification_input(
            task_id=task_id,
            raw_input_path=raw_input_path,
            raw_text=source_analysis_unit.source_excerpt,
            interpretation_results=interpretation_results,
            interpretation_consensus=interpretation_consensus,
        )
    )


def build_source_anchored_derivation_assessment_input(
    *,
    source_analysis_unit: SourceAnalysisUnit,
    task_id: str,
    raw_input_path: Path,
    evidence_results: list[AgentRunResult],
    evidence_consensus: dict[str, Any],
    derivation_rules_text: str,
) -> str:
    """Build derivation input for one canonical source unit."""

    return (
        _source_analysis_unit_context(source_analysis_unit)
        + "\n\n"
        + build_derivation_assessment_input(
            task_id=task_id,
            raw_input_path=raw_input_path,
            raw_text=source_analysis_unit.source_excerpt,
            evidence_results=evidence_results,
            evidence_consensus=evidence_consensus,
            derivation_rules_text=derivation_rules_text,
        )
    )


def build_initial_interpretation_input(
    *,
    task_id: str,
    recipe_id: str,
    raw_input_path: Path,
    raw_text: str,
    recipe_text: str,
    global_principles_text: str,
) -> str:
    """Build input for the legacy interpretation team."""

    return f"""
# Task

Task ID: {task_id}
Recipe ID: {recipe_id}

# Global Principles

{global_principles_text}

# Recipe

{recipe_text}

# Raw Input Artifact

Path: {raw_input_path}

{raw_text}
""".strip()


def build_evidence_classification_input(
    *,
    task_id: str,
    raw_input_path: Path,
    raw_text: str,
    interpretation_results: list[AgentRunResult],
    interpretation_consensus: dict[str, Any],
) -> str:
    """Build input for the evidence classification team."""

    return f"""
# Task

Task ID: {task_id}

# Raw Input Artifact

Path: {raw_input_path}

{raw_text}

# Legacy Interpretation Agent Outputs

{format_agent_outputs(interpretation_results)}

# Legacy Interpretation Consensus

{format_json_block(interpretation_consensus)}
""".strip()


def build_derivation_assessment_input(
    *,
    task_id: str,
    raw_input_path: Path,
    raw_text: str,
    evidence_results: list[AgentRunResult],
    evidence_consensus: dict[str, Any],
    derivation_rules_text: str,
) -> str:
    """Build input for the derivation assessment team."""

    return f"""
# Task

Task ID: {task_id}

# Raw Input Artifact

Path: {raw_input_path}

{raw_text}

# Evidence Classification Agent Outputs

{format_agent_outputs(evidence_results)}

# Evidence Classification Consensus

{format_json_block(evidence_consensus)}

# Derivation Rules

{derivation_rules_text}
""".strip()


def _compact_source_anchored_consensus_bundle(
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Reduce one SAU consensus bundle to completeness-review evidence."""

    compact_reports: list[dict[str, Any]] = []

    for report in payload.get("unit_consensus_reports", []):
        if not isinstance(report, dict):
            continue

        compact_groups: list[dict[str, Any]] = []

        for group in report.get("groups", []):
            if not isinstance(group, dict):
                continue

            compact_groups.append(
                {
                    "group_key": group.get("group_key"),
                    "item_type": group.get("item_type"),
                    "agreement_level": group.get("agreement_level"),
                    "representative_value": group.get(
                        "representative_value"
                    ),
                    "review_required": group.get("review_required"),
                    "reason": group.get("reason"),
                }
            )

        compact_reports.append(
            {
                "source_analysis_unit_id": report.get(
                    "source_analysis_unit_id"
                ),
                "team_id": report.get("team_id"),
                "task_name": report.get("task_name"),
                "total_agents": report.get("total_agents"),
                "summary": report.get("summary", {}),
                "groups": compact_groups,
            }
        )

    return {
        "source_anchored": bool(payload.get("source_anchored")),
        "stage_name": payload.get("stage_name"),
        "source_analysis_unit_count": payload.get(
            "source_analysis_unit_count"
        ),
        "unit_consensus_reports": compact_reports,
    }


def build_source_anchored_completeness_review_input(
    *,
    task_id: str,
    raw_input_path: Path,
    raw_text: str,
    source_analysis_unit_count: int,
    interpretation_run_count: int,
    evidence_run_count: int,
    derivation_run_count: int,
    interpretation_consensus: dict[str, Any],
    evidence_consensus: dict[str, Any],
    derivation_consensus: dict[str, Any],
) -> str:
    """Build bounded source-wide completeness input for SAU execution.

    Per-persona raw outputs are intentionally omitted. The completeness team
    reviews the original source together with compact deterministic per-unit
    consensus summaries. This prevents the source-wide step from re-embedding
    every successful LLM response into one oversized request.
    """

    compact_interpretation = (
        _compact_source_anchored_consensus_bundle(
            interpretation_consensus
        )
    )
    compact_evidence = _compact_source_anchored_consensus_bundle(
        evidence_consensus
    )
    compact_derivation = _compact_source_anchored_consensus_bundle(
        derivation_consensus
    )

    return f"""
# Task

Task ID: {task_id}

# Raw Input Artifact

Path: {raw_input_path}

{raw_text}

# Source-Anchored Execution Summary

The source was processed as {source_analysis_unit_count} canonical Source
Analysis Units.

Successful prior agent runs:
- Legacy Interpretation: {interpretation_run_count}
- Evidence Classification: {evidence_run_count}
- Derivation Assessment: {derivation_run_count}

For this source-wide completeness review, per-persona raw outputs are
intentionally omitted. Use the original source and the compact deterministic
per-unit consensus summaries below.

Do not treat orchestration metadata, task identifiers, file paths, Source
Analysis Unit identifiers, or these instructions as positive engineering
source evidence.

# Legacy Interpretation Consensus

{format_json_block(compact_interpretation)}

# Evidence Classification Consensus

{format_json_block(compact_evidence)}

# Derivation Assessment Consensus

{format_json_block(compact_derivation)}
""".strip()


def build_completeness_review_input(
    *,
    task_id: str,
    raw_input_path: Path,
    raw_text: str,
    interpretation_results: list[AgentRunResult],
    evidence_results: list[AgentRunResult],
    derivation_results: list[AgentRunResult],
    interpretation_consensus: dict[str, Any],
    evidence_consensus: dict[str, Any],
    derivation_consensus: dict[str, Any],
) -> str:
    """Build input for the completeness review team."""

    return f"""
# Task

Task ID: {task_id}

# Raw Input Artifact

Path: {raw_input_path}

{raw_text}

# Legacy Interpretation Outputs

{format_agent_outputs(interpretation_results)}

# Evidence Classification Outputs

{format_agent_outputs(evidence_results)}

# Derivation Assessment Outputs

{format_agent_outputs(derivation_results)}

# Legacy Interpretation Consensus

{format_json_block(interpretation_consensus)}

# Evidence Classification Consensus

{format_json_block(evidence_consensus)}

# Derivation Assessment Consensus

{format_json_block(derivation_consensus)}
""".strip()


def build_report_composer_input(
    *,
    task_id: str,
    recipe_id: str,
    raw_input_path: Path,
    raw_text: str,
    all_agent_results: list[AgentRunResult],
    consensus_reports: list[dict[str, Any]],
    run_summary_text: str,
) -> str:
    """Build input for the report composition team."""

    return f"""
# Task

Task ID: {task_id}
Recipe ID: {recipe_id}

# Raw Input Artifact

Path: {raw_input_path}

{raw_text}

# Agent Outputs

{format_agent_outputs(all_agent_results)}

# Consensus Reports

{format_consensus_reports(consensus_reports)}

# Run Summary

{run_summary_text}
""".strip()


def format_agent_outputs(results: list[AgentRunResult]) -> str:
    """Format agent outputs for chained agent input."""

    blocks: list[str] = []

    for result in results:
        blocks.append(
            f"""
## {result.agent_id} / run {result.run_index}

Task: {result.task_name}
Provider: {result.provider}
Model: {result.model}
Output Artifact: {result.output_path}
Status: {result.status}

{result.output_text}
""".strip()
        )

    return "\n\n".join(blocks)


def format_consensus_reports(consensus_reports: list[dict[str, Any]]) -> str:
    """Format consensus reports for chained agent input."""

    blocks: list[str] = []

    for report in consensus_reports:
        blocks.append(
            f"""
## Consensus Report: {report.get("team_id", "UNKNOWN_TEAM")}

{format_json_block(report)}
""".strip()
        )

    return "\n\n".join(blocks)


def format_json_block(payload: dict[str, Any]) -> str:
    """Format a dictionary as JSON text."""

    return json.dumps(payload, indent=2, ensure_ascii=False)


def build_evidence_input_from_memory(
    *,
    task_id: str,
    interpretation_memory: dict[str, Any],
) -> str:
    """Build compact evidence-classification input from interpretation memory."""

    from modules.ingestion.memory import format_memory_for_prompt

    return f"""
# Task

Task ID: {task_id}

# Interpretation Memory

{format_memory_for_prompt(interpretation_memory)}

Classify evidence only from the source information contained in this memory.

Do not request or reconstruct the complete prior agent conversation.
Do not treat assumptions, ambiguities, negated statements or missing
information as positive evidence.
""".strip()


def build_derivation_input_from_memory(
    *,
    task_id: str,
    interpretation_memory: dict[str, Any],
    evidence_memory: dict[str, Any],
    derivation_rules_text: str,
) -> str:
    """Build compact derivation input from stage-memory artifacts."""

    from modules.ingestion.memory import format_memory_for_prompt

    return f"""
# Task

Task ID: {task_id}

# Interpretation Memory

{format_memory_for_prompt(interpretation_memory)}

# Evidence Memory

{format_memory_for_prompt(evidence_memory)}

# Derivation Rules

{derivation_rules_text}

Identify candidate model elements and assess SysML model buildability only
from the supplied memory artifacts and rules.

Do not reconstruct prior conversations.
Do not propose relationships.
Only include explicit_source_links when the supplied source information
directly supports the relationship.
""".strip()


def build_completeness_input_from_memory(
    *,
    task_id: str,
    interpretation_memory: dict[str, Any],
    evidence_memory: dict[str, Any],
    derivation_memory: dict[str, Any],
) -> str:
    """Build compact completeness-review input from stage memories."""

    from modules.ingestion.memory import format_memory_for_prompt

    return f"""
# Task

Task ID: {task_id}

# Interpretation Memory

{format_memory_for_prompt(interpretation_memory)}

# Evidence Memory

{format_memory_for_prompt(evidence_memory)}

# Derivation Memory

{format_memory_for_prompt(derivation_memory)}

Review only the supplied stage memories.

Check:
- whether candidate elements have sufficient source assignments
- whether explicit links are actually source-supported
- whether model-buildability assessments are internally consistent
- which information is still missing
- which conflicts require human review

Do not reconstruct prior agent conversations.
Do not propose new relationships.
Do not generate SysML v2 code.
Do not approve or promote data.
""".strip()
