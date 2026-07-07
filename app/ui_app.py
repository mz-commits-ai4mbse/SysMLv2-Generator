"""Streamlit UI for the first Turing Generator MVP workflow.

Current scope:
1. Run ingestion task.
2. Display generated ingestion report.
3. Edit ingestion report in browser.
4. Save reviewed report separately.
5. Save structured decision report.
6. Stop before approved input promotion.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any

import streamlit as st

# Allow running without installing the package.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.orchestrator import TuringOrchestrator, OrchestratorError


DEFAULT_TASK_FILE = "tasks/task_001_ingest_example_model.json"
DEFAULT_REPORT_FILE = "data/ingestion_reports/task_001_ingestion_report.md"


def resolve_path(workspace_root: Path, path_value: str | Path) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        return path
    return workspace_root / path


def relative_to_workspace(workspace_root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(workspace_root))
    except ValueError:
        return str(path)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def load_task_if_available(workspace_root: Path, task_file: str) -> dict[str, Any]:
    task_path = resolve_path(workspace_root, task_file)
    if not task_path.exists():
        return {}
    try:
        return json.loads(task_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def derive_review_paths(workspace_root: Path, report_path: Path) -> tuple[Path, Path]:
    reviewed_report_path = report_path.with_name(f"{report_path.stem}_reviewed.md")

    decision_name = report_path.name.replace(
        "ingestion_report.md",
        "ingestion_decision_report.json",
    )

    if decision_name == report_path.name:
        decision_name = f"{report_path.stem}_decision_report.json"

    decision_path = workspace_root / "data" / "decisions" / decision_name

    return reviewed_report_path, decision_path


def build_decision_report(
    workspace_root: Path,
    task_file: str,
    task: dict[str, Any],
    original_report_path: Path,
    reviewed_report_path: Path,
    decision_path: Path,
    decision: str,
    reviewer: str,
    review_comment: str,
    original_text: str,
    reviewed_text: str,
) -> dict[str, Any]:
    task_id = task.get("task_id", "UNKNOWN_TASK")
    recipe_id = task.get("recipe", {}).get("recipe_id", "UNKNOWN_RECIPE")

    approved_for_promotion = decision in {
        "approve",
        "approve_with_modifications",
    }

    return {
        "decision_report_id": f"{task_id}_INGESTION_DECISION",
        "task_id": task_id,
        "task_file": task_file,
        "recipe_id": recipe_id,
        "review_gate": {
            "gate_id": "RG_001_INGESTION_REVIEW",
            "name": "Ingestion Review Gate",
            "status": "decision_recorded"
        },
        "decision": decision,
        "approved_for_promotion": approved_for_promotion,
        "promotion_executed": False,
        "reviewer": reviewer,
        "review_comment": review_comment,
        "report_changed_by_human": original_text != reviewed_text,
        "artifacts": {
            "original_ingestion_report": relative_to_workspace(
                workspace_root,
                original_report_path,
            ),
            "reviewed_ingestion_report": relative_to_workspace(
                workspace_root,
                reviewed_report_path,
            ),
            "decision_report": relative_to_workspace(
                workspace_root,
                decision_path,
            )
        },
        "allowed_next_step": (
            "approved_input_promotion"
            if approved_for_promotion
            else "revise_or_reject_ingestion_artifact"
        ),
        "note": (
            "This decision report records the human review decision. "
            "The MVP still stops before approved input promotion."
        ),
        "created_at_utc": datetime.now(timezone.utc).isoformat()
    }


st.set_page_config(page_title="Turing Generator MVP", layout="wide")

st.title("Turing Generator MVP")
st.caption(
    "Current workflow: raw input → ingestion report → human review → decision report"
)

st.sidebar.header("Workspace")

workspace_root_input = st.sidebar.text_input("Workspace root", value=".")
task_file = st.sidebar.text_input("Task file", value=DEFAULT_TASK_FILE)

workspace_root = Path(workspace_root_input).expanduser().resolve()

st.sidebar.write("Resolved workspace:")
st.sidebar.code(str(workspace_root))

if "last_result" not in st.session_state:
    st.session_state["last_result"] = None

if "review_report_path" not in st.session_state:
    st.session_state["review_report_path"] = DEFAULT_REPORT_FILE

if "review_text" not in st.session_state:
    st.session_state["review_text"] = ""

if "original_report_text" not in st.session_state:
    st.session_state["original_report_text"] = ""

tab_run, tab_review = st.tabs(["1. Run Ingestion Task", "2. Review Report"])

with tab_run:
    st.subheader("Run ingestion task")

    st.write(
        "This creates the ingestion report, feedback placeholder and traceability placeholder. "
        "It stops before approved input promotion."
    )

    if st.button("Run ingestion task", type="primary"):
        orchestrator = TuringOrchestrator(workspace_root=workspace_root)

        try:
            result = orchestrator.run_task(task_file)
        except OrchestratorError as exc:
            st.error(str(exc))
        else:
            st.session_state["last_result"] = result

            report_path = result.get("generated_artifacts", {}).get("ingestion_report")
            if report_path:
                absolute_report_path = resolve_path(workspace_root, report_path)

                if absolute_report_path.exists():
                    report_text = read_text(absolute_report_path)
                    st.session_state["review_report_path"] = report_path
                    st.session_state["review_text"] = report_text
                    st.session_state["original_report_text"] = report_text

            st.success("Task completed and stopped before review gate.")
            st.json(result)

    if st.session_state["last_result"]:
        st.subheader("Last run result")
        st.json(st.session_state["last_result"])

with tab_review:
    st.subheader("Human review")

    report_file = st.text_input(
        "Ingestion report to review",
        value=st.session_state["review_report_path"],
    )

    report_path = resolve_path(workspace_root, report_file)

    col_load, col_status = st.columns([1, 3])

    with col_load:
        if st.button("Load report"):
            if not report_path.exists():
                st.error(f"Report does not exist: {report_path}")
            else:
                report_text = read_text(report_path)
                st.session_state["review_report_path"] = report_file
                st.session_state["review_text"] = report_text
                st.session_state["original_report_text"] = report_text
                st.success("Report loaded for review.")

    with col_status:
        if report_path.exists():
            st.info(f"Loaded report path: {report_path}")
        else:
            st.warning("Report file does not exist yet. Run the ingestion task first.")

    st.markdown("---")

    st.write("Edit the report below. The original generated report will not be overwritten.")

    st.text_area(
        "Editable ingestion report",
        key="review_text",
        height=600,
    )

    st.markdown("---")

    st.subheader("Review decision")

    decision = st.selectbox(
        "Decision",
        options=[
            "approve",
            "approve_with_modifications",
            "reject",
        ],
        index=1,
    )

    reviewer = st.text_input(
        "Reviewer",
        value="human_systems_engineer",
    )

    review_comment = st.text_area(
        "Review comment",
        value=(
            "Reviewed in browser. Decision recorded. "
            "Promotion to approved input is not executed in this MVP step."
        ),
        height=120,
    )

    if st.button("Save reviewed report and decision", type="primary"):
        if not report_path.exists():
            st.error("Cannot save review because the original report does not exist.")
        elif not st.session_state["review_text"].strip():
            st.error("Cannot save review because the edited report is empty.")
        else:
            task = load_task_if_available(workspace_root, task_file)
            reviewed_report_path, decision_path = derive_review_paths(
                workspace_root,
                report_path,
            )

            original_text = st.session_state.get("original_report_text", "")
            if not original_text:
                original_text = read_text(report_path)

            reviewed_text = st.session_state["review_text"]

            write_text(reviewed_report_path, reviewed_text)

            decision_report = build_decision_report(
                workspace_root=workspace_root,
                task_file=task_file,
                task=task,
                original_report_path=report_path,
                reviewed_report_path=reviewed_report_path,
                decision_path=decision_path,
                decision=decision,
                reviewer=reviewer,
                review_comment=review_comment,
                original_text=original_text,
                reviewed_text=reviewed_text,
            )

            write_json(decision_path, decision_report)

            st.success("Reviewed report and decision report saved.")

            st.write("Reviewed report:")
            st.code(relative_to_workspace(workspace_root, reviewed_report_path))

            st.write("Decision report:")
            st.code(relative_to_workspace(workspace_root, decision_path))

            st.json(decision_report)

    st.markdown("---")

    with st.expander("Preview edited report"):
        st.markdown(st.session_state["review_text"])