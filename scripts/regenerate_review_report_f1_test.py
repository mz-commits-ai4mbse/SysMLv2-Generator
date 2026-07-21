import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


from modules.agents.types import AgentRunResult
from modules.ingestion.review_report import (
    write_ingestion_review_report,
)


TASK_ID = "TASK_001_INGEST_EXAMPLE_MODEL"
RUN_ID = "20260717T071127Z"
RECIPE_ID = "REC_INGESTION_001"


RUN_DIR = (
    PROJECT_ROOT
    / "data"
    / "team_runs"
    / TASK_ID
    / RUN_ID
)


RAW_INPUT_PATH = (
    PROJECT_ROOT
    / "legacy"
    / "raw"
    / "example_legacy_model_description.md"
)


REPORT_OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "ingestion_reports"
    / "task_001_team_agentic_ingestion_report_f1_test.md"
)


def load_agent_result(path: Path) -> AgentRunResult:
    payload = json.loads(path.read_text(encoding="utf-8"))

    return AgentRunResult(
        agent_id=str(payload.get("agent_id", "UNKNOWN_AGENT")),
        task_name=str(payload.get("task_name", "")),
        run_index=int(payload.get("run_index", 1)),
        provider=str(payload.get("provider", "")),
        model=str(payload.get("model", "")),
        output_text=str(payload.get("output_text", "")),
        output_path=path,
        response_id=payload.get("response_id"),
        usage=payload.get("usage", {}),
        status=payload.get("status"),
    )


def load_stage_results(stage_directory: Path) -> list[AgentRunResult]:
    paths = sorted(stage_directory.rglob("*.json"))

    if not paths:
        raise FileNotFoundError(
            f"No agent output files found in: {stage_directory}"
        )

    return [load_agent_result(path) for path in paths]


def load_consensus_reports(run_directory: Path) -> list[dict]:
    paths = sorted(
        (run_directory / "consensus_reports").rglob(
            "*_consensus.json"
        )
    )

    if not paths:
        raise FileNotFoundError(
            f"No consensus reports found in: {run_directory}"
        )

    return [
        json.loads(path.read_text(encoding="utf-8"))
        for path in paths
    ]


def count_report_rows(report_text: str, prefix: str) -> int:
    return sum(
        1
        for line in report_text.splitlines()
        if line.startswith(prefix)
    )


def main() -> None:
    if not RUN_DIR.exists():
        raise FileNotFoundError(
            f"Expected test run does not exist: {RUN_DIR}"
        )

    if not RAW_INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Expected raw input does not exist: {RAW_INPUT_PATH}"
        )

    derivation_results = load_stage_results(
        RUN_DIR
        / "agent_outputs"
        / "03_derivation_assessment"
    )

    completeness_results = load_stage_results(
        RUN_DIR
        / "agent_outputs"
        / "04_completeness_review"
    )

    consensus_reports = load_consensus_reports(RUN_DIR)

    narrative_report_path = (
        RUN_DIR / "narrative_ingestion_summary.md"
    )

    if not narrative_report_path.exists():
        narrative_report_path = None

    write_ingestion_review_report(
        task_id=TASK_ID,
        recipe_id=RECIPE_ID,
        raw_input_path=RAW_INPUT_PATH,
        run_id=RUN_ID,
        run_dir=RUN_DIR,
        report_output_path=REPORT_OUTPUT_PATH,
        derivation_results=derivation_results,
        completeness_results=completeness_results,
        consensus_reports=consensus_reports,
        narrative_report_path=narrative_report_path,
    )

    report_text = REPORT_OUTPUT_PATH.read_text(
        encoding="utf-8"
    )

    gap_count = count_report_rows(report_text, "| GAP-")
    risk_count = count_report_rows(report_text, "| RISK-")
    question_count = count_report_rows(report_text, "| RQ-")

    assert gap_count == 5, (
        f"Expected 5 consolidated gaps, found {gap_count}"
    )
    assert risk_count == 5, (
        f"Expected 5 risks, found {risk_count}"
    )
    assert question_count == 5, (
        f"Expected 5 independent review questions, "
        f"found {question_count}"
    )

    assert (
        "Single-agent observation — no cross-agent consensus"
        in report_text
    ), "Single-agent candidate wording is missing."

    assert (
        "Single-agent assessment — no cross-agent consensus"
        in report_text
    ), "Single-agent buildability wording is missing."

    print()
    print("F1 regression test passed.")
    print(f"Report: {REPORT_OUTPUT_PATH}")
    print(f"Consolidated gaps: {gap_count}")
    print(f"Ambiguities and risks: {risk_count}")
    print(f"Independent review questions: {question_count}")


if __name__ == "__main__":
    main()