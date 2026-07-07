"""Central orchestrator for the first Turing Generator MVP workflow."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from core.pipeline_config import (
    ALLOWED_INGESTION_TASK_TYPE,
    REQUIRED_TASK_FIELDS,
)
from core.run_context import RunContext
from modules.extraction.basic_markdown_extractor import extract_basic_markdown_information
from modules.ingestion.artifact_reader import read_text_artifact
from modules.ingestion.report_builder import build_ingestion_report
from modules.mapping.derivation_assessor import detect_evidence_types, assess_derivation_support
from modules.review.feedback import build_feedback_placeholder
from modules.traceability.traceability import build_ingestion_traceability


class OrchestratorError(RuntimeError):
    """Raised when the orchestrator cannot complete a task."""


class TuringOrchestrator:
    def __init__(self, workspace_root: str | Path = ".") -> None:
        self.workspace_root = Path(workspace_root).resolve()

    def run_task(self, task_path: str | Path) -> dict[str, Any]:
        absolute_task_path = self._resolve(task_path)
        task = self._load_json(absolute_task_path)
        self._validate_task(task)

        recipe_path = self._resolve(task["recipe"]["recipe_path"])
        recipe_text = self._read_optional_text(recipe_path, required=True)

        required_context = self._load_context_files(task.get("required_context_files", []), required=True)
        optional_context = self._load_context_files(task.get("optional_context_files", []), required=False)
        agent_personalities = self._load_agent_personalities(task.get("agent_personalities", []))

        run_context = RunContext(
            workspace_root=self.workspace_root,
            task_path=absolute_task_path,
            task=task,
            recipe_text=recipe_text,
            required_context=required_context,
            optional_context=optional_context,
            agent_personalities=agent_personalities,
        )

        if task.get("task_type") != ALLOWED_INGESTION_TASK_TYPE:
            raise OrchestratorError(
                f"Unsupported task type for this MVP skeleton: {task.get('task_type')}"
            )

        return self._execute_ingestion_task(run_context)

    def _execute_ingestion_task(self, run_context: RunContext) -> dict[str, Any]:
        input_artifacts = run_context.task.get("input_artifacts", [])
        if not input_artifacts:
            raise OrchestratorError("Task does not define input_artifacts.")
        if len(input_artifacts) > 1:
            raise OrchestratorError("This first MVP skeleton supports exactly one input artifact per run.")

        input_artifact = input_artifacts[0]
        input_path = run_context.resolve(input_artifact["path"])
        raw_text = read_text_artifact(input_path)

        extraction = extract_basic_markdown_information(raw_text)
        detected_evidence_types = detect_evidence_types(raw_text)
        derivation_rules = self._load_derivation_rules(run_context)
        derivation_assessments = assess_derivation_support(derivation_rules, detected_evidence_types)

        report_text = build_ingestion_report(
            run_context=run_context,
            input_artifact=input_artifact,
            raw_text=raw_text,
            extraction=extraction,
            detected_evidence_types=detected_evidence_types,
            derivation_assessments=derivation_assessments,
        )

        output_map = self._expected_outputs_by_id(run_context.task)
        report_path = self._resolve_output_path(
            output_map,
            "INGESTION_REPORT_TASK_001",
            "data/ingestion_reports/task_001_ingestion_report.md",
        )
        feedback_path = self._resolve_output_path(
            output_map,
            "FEEDBACK_PLACEHOLDER_TASK_001",
            "data/feedback/task_001_ingestion_feedback.json",
        )
        traceability_path = self._resolve_output_path(
            output_map,
            "TRACEABILITY_PLACEHOLDER_TASK_001",
            "data/traceability/task_001_ingestion_traceability.json",
        )

        self._write_text(report_path, report_text)

        feedback = build_feedback_placeholder(
            run_context.task,
            self._relative(report_path),
        )
        self._write_json(feedback_path, feedback)

        traceability = build_ingestion_traceability(
            run_context=run_context,
            input_artifact=input_artifact,
            report_path=self._relative(report_path),
            feedback_path=self._relative(feedback_path),
        )
        self._write_json(traceability_path, traceability)

        return {
            "status": "completed_stopped_before_review_gate",
            "task_id": run_context.task_id,
            "recipe_id": run_context.recipe_id,
            "generated_artifacts": {
                "ingestion_report": self._relative(report_path),
                "feedback_placeholder": self._relative(feedback_path),
                "traceability_placeholder": self._relative(traceability_path),
            },
            "detected_evidence_types": detected_evidence_types,
            "message": "Ingestion report created. Human review is required before approved input promotion.",
        }

    def _validate_task(self, task: dict[str, Any]) -> None:
        missing = [field for field in REQUIRED_TASK_FIELDS if field not in task]
        if missing:
            raise OrchestratorError(f"Task is missing required fields: {missing}")

    def _load_context_files(self, paths: list[str], required: bool) -> dict[str, str]:
        context: dict[str, str] = {}
        for path in paths:
            absolute_path = self._resolve(path)
            text = self._read_optional_text(absolute_path, required=required)
            if text is not None:
                context[path] = text
        return context

    def _load_agent_personalities(self, agent_specs: list[dict[str, Any]]) -> dict[str, str]:
        agents: dict[str, str] = {}
        for agent in agent_specs:
            path = agent.get("path")
            if not path:
                continue
            absolute_path = self._resolve(path)
            text = self._read_optional_text(absolute_path, required=False)
            if text is not None:
                agents[path] = text
        return agents

    def _load_derivation_rules(self, run_context: RunContext) -> dict[str, Any]:
        path = "context/mapping/sysml_model_derivation_rules.json"
        absolute_path = self._resolve(path)
        if not absolute_path.exists():
            raise OrchestratorError(
                "Derivation rules file is required but missing: "
                "context/mapping/sysml_model_derivation_rules.json"
            )
        return self._load_json(absolute_path)

    def _expected_outputs_by_id(self, task: dict[str, Any]) -> dict[str, dict[str, Any]]:
        return {
            artifact["artifact_id"]: artifact
            for artifact in task.get("expected_output_artifacts", [])
            if "artifact_id" in artifact
        }

    def _resolve_output_path(
        self,
        output_map: dict[str, dict[str, Any]],
        artifact_id: str,
        fallback: str,
    ) -> Path:
        relative_path = output_map.get(artifact_id, {}).get("path", fallback)
        return self._resolve(relative_path)

    def _resolve(self, path: str | Path) -> Path:
        candidate = Path(path)
        if candidate.is_absolute():
            return candidate
        return self.workspace_root / candidate

    def _relative(self, path: Path) -> str:
        try:
            return str(path.relative_to(self.workspace_root))
        except ValueError:
            return str(path)

    def _read_optional_text(self, path: Path, required: bool) -> str | None:
        if not path.exists():
            if required:
                raise OrchestratorError(f"Required file does not exist: {path}")
            return None
        return path.read_text(encoding="utf-8")

    def _load_json(self, path: Path) -> dict[str, Any]:
        if not path.exists():
            raise OrchestratorError(f"JSON file does not exist: {path}")
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise OrchestratorError(f"Invalid JSON in {path}: {exc}") from exc

    def _write_text(self, path: Path, text: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def _write_json(self, path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
