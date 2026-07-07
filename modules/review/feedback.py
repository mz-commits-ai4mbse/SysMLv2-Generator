"""Create placeholder human feedback records."""

from __future__ import annotations

from typing import Any


def build_feedback_placeholder(task: dict[str, Any], report_path: str) -> dict[str, Any]:
    return {
        "task_id": task.get("task_id"),
        "review_artifact": report_path,
        "review_gate": task.get("review_gate", {}).get("gate_id", "RG_001_INGESTION_REVIEW"),
        "reviewer": "human_reviewer",
        "status": "pending_review",
        "decision": None,
        "allowed_decisions": ["approve", "approve_with_modifications", "reject"],
        "feedback_items": [],
        "approved_for_promotion": False,
        "notes": "Placeholder created by MVP ingestion workflow. Human review still required.",
    }
