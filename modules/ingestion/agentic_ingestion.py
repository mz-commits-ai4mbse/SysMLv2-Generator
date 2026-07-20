"""Agentic ingestion pipeline for legacy engineering data.

This module coordinates multiple single-responsibility agents.

Architecture:
- Knowledge Layer: agents, context, recipes, mapping rules
- Process Layer: this pipeline and the agent runner
- Artifact Layer: raw input, intermediate agent outputs, ingestion report
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from modules.agents.runner import run_llm_agent
from modules.agents.types import AgentRunResult


@dataclass
class AgenticIngestionResult:
    """Final result of an agentic ingestion run."""

    task_id: str
    run_id: str
    report_path: Path
    run_dir: Path
    agent_results: list[AgentRunResult]


def run_agentic_ingestion(
    *,
    project_root: Path,
    task_id: str,
    recipe_id: str,
    raw_input_path: Path,
    report_output_path: Path,
    provider: str = "openai",
    model: str = "gpt-5.5",
    api_key: str | None = None,
    runs_per_agent: int = 1,
) -> AgenticIngestionResult:
    """Run the full agentic ingestion pipeline."""

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = project_root / "data" / "agent_runs" / task_id / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    raw_text = raw_input_path.read_text(encoding="utf-8")

    recipe_text = read_optional_file(
        project_root / "recipes" / "ingestion" / "create_ingestion_artifact.recipe.md"
    )

    derivation_rules_text = read_optional_file(
        project_root / "context" / "mapping" / "sysml_model_derivation_rules.json"
    )

    global_principles_text = read_optional_file(
        project_root / "context" / "global" / "project_principles.md"
    )

    all_results: list[AgentRunResult] = []

    interpreter_results = run_agent_group(
        run_dir=run_dir,
        agent_id="AGENT_LEGACY_DATA_INTERPRETER",
        personality_file=project_root / "agents" / "legacy_data_interpreter.md",
        task_name="Interpret raw legacy data",
        task_instructions=get_interpreter_task_instructions(),
        input_text=build_initial_input(
            task_id=task_id,
            recipe_id=recipe_id,
            raw_input_path=raw_input_path,
            raw_text=raw_text,
            recipe_text=recipe_text,
            global_principles_text=global_principles_text,
        ),
        provider=provider,
        model=model,
        api_key=api_key,
        runs_per_agent=runs_per_agent,
    )
    all_results.extend(interpreter_results)

    evidence_results = run_agent_group(
        run_dir=run_dir,
        agent_id="AGENT_EVIDENCE_CLASSIFIER",
        personality_file=project_root / "agents" / "evidence_classifier.md",
        task_name="Classify engineering evidence",
        task_instructions=get_evidence_classifier_task_instructions(),
        input_text=build_chained_input(
            task_id=task_id,
            raw_input_path=raw_input_path,
            raw_text=raw_text,
            previous_results=interpreter_results,
        ),
        provider=provider,
        model=model,
        api_key=api_key,
        runs_per_agent=runs_per_agent,
    )
    all_results.extend(evidence_results)

    derivation_results = run_agent_group(
        run_dir=run_dir,
        agent_id="AGENT_DERIVATION_ASSESSOR",
        personality_file=project_root / "agents" / "derivation_assessor.md",
        task_name="Assess downstream model derivation support",
        task_instructions=get_derivation_assessor_task_instructions(
            derivation_rules_text=derivation_rules_text
        ),
        input_text=build_chained_input(
            task_id=task_id,
            raw_input_path=raw_input_path,
            raw_text=raw_text,
            previous_results=evidence_results,
            additional_context={
                "interpreter_outputs": format_agent_outputs(interpreter_results),
                "derivation_rules": derivation_rules_text,
            },
        ),
        provider=provider,
        model=model,
        api_key=api_key,
        runs_per_agent=runs_per_agent,
    )
    all_results.extend(derivation_results)

    completeness_results = run_agent_group(
        run_dir=run_dir,
        agent_id="AGENT_COMPLETENESS_CHECKER",
        personality_file=project_root / "agents" / "completeness_checker_agentic.md",
        task_name="Check completeness, gaps, risks and review readiness",
        task_instructions=get_completeness_checker_task_instructions(),
        input_text=build_completeness_input(
            task_id=task_id,
            raw_input_path=raw_input_path,
            raw_text=raw_text,
            interpreter_results=interpreter_results,
            evidence_results=evidence_results,
            derivation_results=derivation_results,
        ),
        provider=provider,
        model=model,
        api_key=api_key,
        runs_per_agent=runs_per_agent,
    )
    all_results.extend(completeness_results)

    report_results = run_agent_group(
        run_dir=run_dir,
        agent_id="AGENT_REPORT_COMPOSER",
        personality_file=project_root / "agents" / "report_composer.md",
        task_name="Compose structured ingestion report",
        task_instructions=get_report_composer_task_instructions(
            task_id=task_id,
            recipe_id=recipe_id,
            raw_input_path=raw_input_path,
        ),
        input_text=build_report_composer_input(
            task_id=task_id,
            recipe_id=recipe_id,
            raw_input_path=raw_input_path,
            raw_text=raw_text,
            all_results=all_results,
        ),
        provider=provider,
        model=model,
        api_key=api_key,
        runs_per_agent=1,
    )
    all_results.extend(report_results)

    report_output_path.parent.mkdir(parents=True, exist_ok=True)
    report_output_path.write_text(report_results[0].output_text, encoding="utf-8")

    write_run_summary(
        run_dir=run_dir,
        task_id=task_id,
        recipe_id=recipe_id,
        raw_input_path=raw_input_path,
        report_output_path=report_output_path,
        provider=provider,
        model=model,
        runs_per_agent=runs_per_agent,
        agent_results=all_results,
    )

    return AgenticIngestionResult(
        task_id=task_id,
        run_id=run_id,
        report_path=report_output_path,
        run_dir=run_dir,
        agent_results=all_results,
    )


def run_agent_group(
    *,
    run_dir: Path,
    agent_id: str,
    personality_file: Path,
    task_name: str,
    task_instructions: str,
    input_text: str,
    provider: str,
    model: str,
    api_key: str | None,
    runs_per_agent: int,
) -> list[AgentRunResult]:
    """Run one agent task one or more times."""

    results: list[AgentRunResult] = []
    agent_output_dir = run_dir / safe_filename(agent_id)

    for index in range(1, runs_per_agent + 1):
        result = run_llm_agent(
            agent_id=agent_id,
            personality_file=personality_file,
            task_name=task_name,
            task_instructions=task_instructions,
            input_text=input_text,
            output_dir=agent_output_dir,
            provider=provider,
            model=model,
            api_key=api_key,
            run_index=index,
        )
        results.append(result)

    return results


def get_interpreter_task_instructions() -> str:
    return """
Return only JSON. Do not wrap the JSON in Markdown fences.

Extract meaningful engineering information from the raw legacy input.

Required JSON shape:
{
  "source_information": [
    {
      "source_info_id": "SRC_INFO_001",
      "source_reference": "line or section reference",
      "extracted_information": "what the source says",
      "information_kind": "explicit | implied | assumption | uncertainty | negated | missing",
      "confidence": "high | medium | low",
      "notes": "concise rationale"
    }
  ],
  "assumptions": [],
  "ambiguities": [],
  "not_interpreted_as_positive_evidence": []
}

Focus only on interpretation and extraction.
Do not classify evidence types.
Do not assess downstream model derivation.
""".strip()


def get_evidence_classifier_task_instructions() -> str:
    return """
Return only JSON. Do not wrap the JSON in Markdown fences.

Classify the interpreted engineering information into evidence types.

Classify only positive evidence.
Do not classify missing, negated, absent or uncertain information as positive evidence.

Required JSON shape:
{
  "detected_evidence": [
    {
      "evidence_id": "EVDET_001",
      "evidence_type": "EV_FUNCTION_OR_CAPABILITY",
      "source_info_id": "SRC_INFO_001",
      "source_excerpt": "source statement",
      "interpretation": "why this is evidence",
      "confidence": "high | medium | low",
      "rationale_summary": "concise rationale"
    }
  ],
  "rejected_evidence_candidates": [
    {
      "source_info_id": "SRC_INFO_999",
      "rejected_evidence_type": "EV_VALIDATION_CRITERION",
      "reason": "why this is not positive evidence"
    }
  ],
  "evidence_gaps": []
}
""".strip()


def get_derivation_assessor_task_instructions(derivation_rules_text: str) -> str:
    return f"""
Return only JSON. Do not wrap the JSON in Markdown fences.

Assess downstream model derivation support using the evidence classification and the derivation rules.

Support levels:
- supported
- partially_supported
- not_supported
- conflicting

Required JSON shape:
{{
  "model_artifact_assessments": [
    {{
      "model_artifact_type": "functional_model",
      "support_level": "supported | partially_supported | not_supported | conflicting",
      "evidence_basis": ["EV_FUNCTION_OR_CAPABILITY"],
      "reason": "concise rationale",
      "missing_information": ["missing item"],
      "recommended_action": "what should happen next"
    }}
  ],
  "cross_artifact_observations": [],
  "blocked_generation_tasks": []
}}

Derivation rules:
{derivation_rules_text}
""".strip()


def get_completeness_checker_task_instructions() -> str:
    return """
Return only JSON. Do not wrap the JSON in Markdown fences.

Check the consistency and review-readiness of the prior agent outputs.

Required JSON shape:
{
  "gaps": [
    {
      "gap_id": "GAP_001",
      "missing_information": "what is missing",
      "why_it_matters": "impact on downstream model generation",
      "suggested_human_action": "what reviewer should do"
    }
  ],
  "ambiguities_and_risks": [
    {
      "risk_id": "RISK_001",
      "topic": "topic",
      "description": "description",
      "potential_impact": "impact",
      "suggested_review_action": "action"
    }
  ],
  "review_questions": [
    {
      "question_id": "RQ_001",
      "question": "question",
      "related_artifact_or_candidate": "reference",
      "reason": "why this matters"
    }
  ],
  "recommended_review_decision": "review_required | suitable_for_review_with_minor_gaps | incomplete_but_reviewable | incomplete_and_blocking"
}
""".strip()


def get_report_composer_task_instructions(
    *,
    task_id: str,
    recipe_id: str,
    raw_input_path: Path,
) -> str:
    return f"""
Return only Markdown.

Compose a structured ingestion report from the prior agent outputs.

Do not introduce new engineering claims.
Use only the raw input and prior agent outputs.

Required report structure:

# Ingestion Report

## Report Metadata

Include:
- Report ID: IR_{task_id}
- Task ID: {task_id}
- Recipe ID: {recipe_id}
- Source Path: {raw_input_path}
- Generated By: LLM Agentic Ingestion
- Review Status: ready_for_review

## Agent Execution Summary

Include a table:
| Agent ID | Task | Runs | Provider | Model | Output Artifact | Status |
|---|---|---:|---|---|---|---|

## 1. Executive Summary

## 2. Source Artifacts Reviewed

## 3. Extracted Source Information

## 4. Interpreted Engineering Information

## 5. Candidate Downstream Elements

## 5a. Downstream Model Derivation Assessment

Use support levels only:
- supported
- partially_supported
- not_supported
- conflicting

## 6. Assumptions

## 7. Missing Information

## 8. Ambiguities and Risks

## 9. Review Questions

## 10. Recommended Review Decision

Do not use approved or rejected.

## 11. Traceability Notes

## Review Gate Rule

State clearly that this report stops before the ingestion review gate and requires human review before approved input promotion.
""".strip()


def build_initial_input(
    *,
    task_id: str,
    recipe_id: str,
    raw_input_path: Path,
    raw_text: str,
    recipe_text: str,
    global_principles_text: str,
) -> str:
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


def build_chained_input(
    *,
    task_id: str,
    raw_input_path: Path,
    raw_text: str,
    previous_results: list[AgentRunResult],
    additional_context: dict[str, str] | None = None,
) -> str:
    context = additional_context or {}

    context_block = "\n\n".join(
        f"# Additional Context: {key}\n\n{value}"
        for key, value in context.items()
    )

    return f"""
# Task

Task ID: {task_id}

# Raw Input Artifact

Path: {raw_input_path}

{raw_text}

# Previous Agent Outputs

{format_agent_outputs(previous_results)}

{context_block}
""".strip()


def build_completeness_input(
    *,
    task_id: str,
    raw_input_path: Path,
    raw_text: str,
    interpreter_results: list[AgentRunResult],
    evidence_results: list[AgentRunResult],
    derivation_results: list[AgentRunResult],
) -> str:
    return f"""
# Task

Task ID: {task_id}

# Raw Input Artifact

Path: {raw_input_path}

{raw_text}

# Legacy Data Interpreter Outputs

{format_agent_outputs(interpreter_results)}

# Evidence Classifier Outputs

{format_agent_outputs(evidence_results)}

# Derivation Assessor Outputs

{format_agent_outputs(derivation_results)}
""".strip()


def build_report_composer_input(
    *,
    task_id: str,
    recipe_id: str,
    raw_input_path: Path,
    raw_text: str,
    all_results: list[AgentRunResult],
) -> str:
    return f"""
# Task

Task ID: {task_id}
Recipe ID: {recipe_id}

# Raw Input Artifact

Path: {raw_input_path}

{raw_text}

# Agent Outputs

{format_agent_outputs(all_results)}

# Agent Output Artifacts

{format_agent_artifacts(all_results)}
""".strip()


def format_agent_outputs(results: list[AgentRunResult]) -> str:
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


def format_agent_artifacts(results: list[AgentRunResult]) -> str:
    rows = [
        "| Agent ID | Task | Run | Provider | Model | Output Artifact | Status |",
        "|---|---|---:|---|---|---|---|",
    ]

    for result in results:
        rows.append(
            f"| {result.agent_id} | {result.task_name} | {result.run_index} | "
            f"{result.provider} | {result.model} | {result.output_path} | {result.status or ''} |"
        )

    return "\n".join(rows)


def write_run_summary(
    *,
    run_dir: Path,
    task_id: str,
    recipe_id: str,
    raw_input_path: Path,
    report_output_path: Path,
    provider: str,
    model: str,
    runs_per_agent: int,
    agent_results: list[AgentRunResult],
) -> None:
    payload = {
        "task_id": task_id,
        "recipe_id": recipe_id,
        "raw_input_path": str(raw_input_path),
        "report_output_path": str(report_output_path),
        "provider": provider,
        "model": model,
        "runs_per_agent": runs_per_agent,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "agent_results": [
            {
                "agent_id": result.agent_id,
                "task_name": result.task_name,
                "run_index": result.run_index,
                "provider": result.provider,
                "model": result.model,
                "response_id": result.response_id,
                "status": result.status,
                "output_path": str(result.output_path),
                "usage": result.usage,
            }
            for result in agent_results
        ],
    }

    summary_path = run_dir / "agentic_ingestion_run_summary.json"
    summary_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def read_optional_file(path: Path) -> str:
    if not path.exists():
        return f"File not found: {path}"
    return path.read_text(encoding="utf-8")


def safe_filename(value: str) -> str:
    cleaned = value.lower().replace(" ", "_").replace("-", "_")
    return "".join(char for char in cleaned if char.isalnum() or char == "_")
