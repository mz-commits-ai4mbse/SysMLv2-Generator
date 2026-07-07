"""Create traceability placeholders for the first MVP workflow."""

from __future__ import annotations

from typing import Any

from core.run_context import RunContext


def build_ingestion_traceability(
    run_context: RunContext,
    input_artifact: dict[str, Any],
    report_path: str,
    feedback_path: str,
) -> dict[str, Any]:
    return {
        "traceability_id": f"TRACE_{run_context.task_id}",
        "task_id": run_context.task_id,
        "recipe_id": run_context.recipe_id,
        "run_id": run_context.run_id,
        "generated_at": run_context.generated_at,
        "input_artifacts": [
            {
                "artifact_id": input_artifact.get("artifact_id"),
                "path": input_artifact.get("path"),
                "source_state": input_artifact.get("source_state", "raw_unreviewed"),
            }
        ],
        "context_files": list(run_context.required_context.keys()),
        "optional_context_files_loaded": list(run_context.optional_context.keys()),
        "agent_personalities_loaded": list(run_context.agent_personalities.keys()),
        "generated_artifacts": [
            {
                "artifact_type": "ingestion_report",
                "path": report_path,
                "state": "ready_for_review",
            },
            {
                "artifact_type": "feedback_placeholder",
                "path": feedback_path,
                "state": "pending_review",
            },
        ],
        "workflow_state": "stopped_before_approved_input_promotion",
        "forbidden_actions_confirmed": [
            "No approved input created.",
            "No approved model data created.",
            "No SysML v2 output generated.",
            "No protected architecture model files modified.",
        ],
    }
