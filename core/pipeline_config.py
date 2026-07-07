"""Pipeline configuration constants for the Turing Generator MVP."""

from pathlib import Path


INGESTION_REPORTS_DIR = Path("data/ingestion_reports")
FEEDBACK_DIR = Path("data/feedback")
TRACEABILITY_DIR = Path("data/traceability")
RUNS_DIR = Path("data/runs")

PROTECTED_ARCHITECTURE_DIR = Path("model/architecture")
GENERATED_OUTPUT_DIR = Path("data/output")

REQUIRED_TASK_FIELDS = [
    "task_id",
    "task_type",
    "recipe",
    "input_artifacts",
    "required_context_files",
    "expected_output_artifacts",
]

ALLOWED_INGESTION_TASK_TYPE = "create_ingestion_artifact"
