"""Streamlit UI for team-based agentic ingestion.

Current scope:
- select existing legacy input file
- upload new Markdown/Text/JSON/CSV input file
- preview selected input
- configure pipeline parameters
- validate execution configuration
- start team-based agentic ingestion pipeline
- browse generated reports and technical artifacts
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import streamlit as st

from modules.ingestion.team_agentic_pipeline import run_team_agentic_ingestion


SUPPORTED_INPUT_SUFFIXES = {
    ".md",
    ".txt",
    ".json",
    ".csv",
}


@dataclass
class PipelineConfig:
    """Configuration prepared by the UI for team-based agentic ingestion."""

    selected_input_path: str
    report_output_path: str
    task_id: str
    recipe_id: str
    provider: str
    model: str
    max_members_per_team_label: str
    max_members_per_team_value: int | None
    runs_per_member: int
    dry_run: bool
    api_key: str | None
    api_key_source: str


def render_team_agentic_ingestion_ui(project_root: Path) -> None:
    """Render the Team Agentic Ingestion UI."""

    st.header("Team Agentic Ingestion")
    st.caption(
        "Run the multi-stage agentic ingestion pipeline on legacy engineering data. "
        "Current outputs are unreviewed and must not be treated as approved model generation input."
    )

    render_status_warning()

    legacy_raw_dir = project_root / "legacy" / "raw"
    upload_dir = legacy_raw_dir / "user_uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)

    st.subheader("1. Input Data")

    uploaded_path = render_upload_section(
        upload_dir=upload_dir,
        project_root=project_root,
    )

    available_files = list_legacy_input_files(legacy_raw_dir)

    selected_existing_path = render_existing_file_selector(
        project_root=project_root,
        available_files=available_files,
    )

    selected_input_path = uploaded_path or selected_existing_path

    if selected_input_path is None:
        st.info("Select or upload a legacy input file to continue.")
        return

    render_selected_file_preview(
        path=selected_input_path,
        project_root=project_root,
    )

    st.subheader("2. Pipeline Configuration")

    config = render_pipeline_configuration(
        project_root=project_root,
        selected_input_path=selected_input_path,
    )

    st.subheader("3. Execution Readiness")

    validation_messages = validate_pipeline_config(config)
    render_execution_readiness(
        config=config,
        validation_messages=validation_messages,
    )

    st.subheader("4. Prepared Configuration")

    render_prepared_configuration(
        config=config,
        project_root=project_root,
    )

    st.subheader("5. Run Pipeline")

    render_pipeline_execution_section(
        project_root=project_root,
        config=config,
        validation_messages=validation_messages,
    )


def render_status_warning() -> None:
    """Render review status warning."""

    st.warning(
        "Review gate pending: generated artifacts are unreviewed. "
        "Browsing an artifact does not approve or promote it."
    )


def render_upload_section(
    *,
    upload_dir: Path,
    project_root: Path,
) -> Path | None:
    """Render file upload section and return uploaded file path if available."""

    uploaded_file = st.file_uploader(
        "Upload legacy input file",
        type=["md", "txt", "json", "csv"],
        help="Uploaded files are stored in legacy/raw/user_uploads/.",
    )

    if uploaded_file is None:
        return None

    safe_name = make_safe_filename(uploaded_file.name)
    output_path = upload_dir / safe_name

    output_path.write_bytes(uploaded_file.getbuffer())

    st.success(
        "Uploaded file saved: "
        f"{format_display_path(output_path, project_root)}"
    )

    return output_path


def render_existing_file_selector(
    *,
    project_root: Path,
    available_files: list[Path],
) -> Path | None:
    """Render selector for existing legacy input files."""

    if not available_files:
        st.info("No existing legacy input files found.")
        return None

    options = [""] + [
        str(path.relative_to(project_root))
        for path in available_files
    ]

    selected = st.selectbox(
        "Or select existing legacy input file",
        options=options,
        index=0,
    )

    if not selected:
        return None

    return project_root / selected


def render_selected_file_preview(
    *,
    path: Path,
    project_root: Path,
) -> None:
    """Render selected file metadata and preview."""

    st.subheader("Selected Input Preview")

    st.caption(
        f"{format_display_path(path, project_root)} · "
        f"{format_file_size(path.stat().st_size)} · "
        f"{path.suffix.lower().lstrip('.').upper()}"
    )

    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        st.error("Could not preview file as UTF-8 text.")
        return

    preview_length = st.slider(
        "Preview length",
        min_value=500,
        max_value=10000,
        value=3000,
        step=500,
    )

    st.text_area(
        "Input preview",
        value=text[:preview_length],
        height=320,
    )


def render_pipeline_configuration(
    *,
    project_root: Path,
    selected_input_path: Path,
) -> PipelineConfig:
    """Render pipeline configuration widgets and return normalized config."""

    task_id = st.text_input(
        "Task ID",
        value=build_default_task_id(selected_input_path),
        help="Used for run directories and traceability.",
    )

    recipe_id = st.text_input(
        "Recipe ID",
        value="REC_INGESTION_001",
    )

    provider = st.selectbox(
        "LLM Provider",
        options=["openai"],
        index=0,
    )

    model = st.selectbox(
        "Model",
        options=[
            "gpt-5.4-mini",
            "gpt-5-mini",
            "gpt-4.1-mini",
            "gpt-4o-mini",
            "dry-run-model",
        ],
        index=0,
    )

    max_members_choice = st.selectbox(
        "Max members per team",
        options=[
            "1",
            "all",
        ],
        index=0,
        help="Use 1 for cost-saving demo mode. Use all for all configured personas.",
    )

    runs_per_member = st.number_input(
        "Runs per member",
        min_value=1,
        max_value=5,
        value=1,
        step=1,
    )

    dry_run = st.checkbox(
        "Dry run",
        value=True,
        help="Dry run does not call the LLM and costs no tokens.",
    )

    api_key, api_key_source = render_api_key_configuration(
        dry_run=dry_run,
        provider=provider,
    )

    report_output_path = render_report_output_path_configuration(
        project_root=project_root,
        task_id=task_id,
        dry_run=dry_run,
    )

    return PipelineConfig(
        selected_input_path=str(selected_input_path),
        report_output_path=str(report_output_path),
        task_id=task_id.strip(),
        recipe_id=recipe_id.strip(),
        provider=provider,
        model=model,
        max_members_per_team_label=max_members_choice,
        max_members_per_team_value=parse_max_members_per_team(max_members_choice),
        runs_per_member=int(runs_per_member),
        dry_run=bool(dry_run),
        api_key=api_key,
        api_key_source=api_key_source,
    )


def render_api_key_configuration(
    *,
    dry_run: bool,
    provider: str,
) -> tuple[str | None, str]:
    """Render API key input when real LLM execution is enabled."""

    if dry_run:
        st.info("API key not required because dry run is enabled.")
        return None, "not_required_dry_run"

    if provider != "openai":
        return None, "not_required_for_provider"

    if os.getenv("OPENAI_API_KEY"):
        st.success("OPENAI_API_KEY found in the Streamlit process environment.")
        return None, "environment_variable"

    st.warning(
        "OPENAI_API_KEY was not found in the Streamlit process environment. "
        "Enter an API key below to use it for this run only."
    )

    api_key = st.text_input(
        "OpenAI API key for this run",
        value="",
        type="password",
        help=(
            "Used only for this Streamlit session/run. "
            "The key is not shown in the prepared configuration and is not written to output artifacts."
        ),
    ).strip()

    if api_key:
        st.success("API key provided for this UI session.")
        return api_key, "ui_session_input"

    return None, "missing"


def render_prepared_configuration(
    *,
    config: PipelineConfig,
    project_root: Path,
) -> None:
    """Render a concise, secret-free configuration summary."""

    execution_mode = (
        "Dry run — no LLM calls"
        if config.dry_run
        else "Live LLM execution"
    )
    model = "Not used in dry run" if config.dry_run else config.model
    team_scope = (
        "All configured members"
        if config.max_members_per_team_value is None
        else f"Maximum {config.max_members_per_team_value} member(s) per team"
    )

    rows = [
        {
            "Setting": "Input",
            "Value": format_display_path(
                Path(config.selected_input_path),
                project_root,
            ),
        },
        {
            "Setting": "Report",
            "Value": format_display_path(
                Path(config.report_output_path),
                project_root,
            ),
        },
        {"Setting": "Task", "Value": config.task_id},
        {"Setting": "Recipe", "Value": config.recipe_id},
        {"Setting": "Execution", "Value": execution_mode},
        {"Setting": "Model", "Value": model},
        {"Setting": "Team scope", "Value": team_scope},
        {"Setting": "Runs per member", "Value": config.runs_per_member},
    ]

    with st.expander("Show technical configuration", expanded=False):
        st.dataframe(
            rows,
            hide_index=True,
            use_container_width=True,
        )


def render_report_output_path_configuration(
    *,
    project_root: Path,
    task_id: str,
    dry_run: bool,
) -> Path:
    """Render report output path configuration."""

    reports_dir = project_root / "data" / "ingestion_reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    default_filename = build_default_report_filename(
        task_id=task_id,
        dry_run=dry_run,
    )

    filename = st.text_input(
        "Report output filename",
        value=default_filename,
        help="The final ingestion report will be written to data/ingestion_reports/.",
    )

    safe_filename = make_safe_filename(filename)

    if not safe_filename.endswith(".md"):
        safe_filename = f"{safe_filename}.md"

    return reports_dir / safe_filename


def render_execution_readiness(
    *,
    config: PipelineConfig,
    validation_messages: list[str],
) -> None:
    """Render validation and execution readiness information."""

    estimated_agent_runs = estimate_agent_runs(config)

    mode_column, runs_column, team_column = st.columns(3)

    mode_column.metric(
        "Execution mode",
        "Dry run" if config.dry_run else "Live LLM",
    )
    runs_column.metric("Estimated agent runs", estimated_agent_runs)
    team_column.metric(
        "Team scope",
        (
            "All members"
            if config.max_members_per_team_value is None
            else f"{config.max_members_per_team_value} per team"
        ),
    )

    if config.dry_run:
        st.info(
            "Structural dry run: validates execution, persistence and artifact "
            "browsing without producing an engineering assessment or calling an LLM."
        )
    else:
        st.warning(
            "Dry run is disabled. This configuration will call the selected LLM provider."
        )

    if config.max_members_per_team_value is None:
        st.warning(
            "Full team mode is selected. This will run all configured personas per team "
            "and may be slower and more expensive."
        )
    else:
        st.info(
            f"Cost-saving mode: maximum {config.max_members_per_team_value} member(s) per team."
        )

    if validation_messages:
        for message in validation_messages:
            st.error(message)
    else:
        st.success("Configuration is valid and ready for pipeline execution.")


def render_pipeline_execution_section(
    *,
    project_root: Path,
    config: PipelineConfig,
    validation_messages: list[str],
) -> None:
    """Render pipeline execution button and result summary."""

    if validation_messages:
        st.button(
            "Run Team Agentic Ingestion",
            disabled=True,
            help="Fix configuration errors before running the pipeline.",
        )
        return

    if not config.dry_run:
        st.error(
            "Real LLM execution is enabled. Confirm that this input does not contain "
            "confidential information unless your API project/data-sharing settings allow it."
        )

        confirmation = st.checkbox(
            "I confirm that I want to run real LLM calls for this input.",
            value=False,
        )
    else:
        confirmation = True

    run_disabled = not confirmation

    if st.button(
        "Run Team Agentic Ingestion",
        type="primary",
        disabled=run_disabled,
    ):
        execute_pipeline_from_ui(
            project_root=project_root,
            config=config,
        )

    render_last_run_result(project_root=project_root)


def execute_pipeline_from_ui(
    *,
    project_root: Path,
    config: PipelineConfig,
) -> None:
    """Execute team agentic ingestion pipeline from UI."""

    with st.spinner("Running team-based agentic ingestion pipeline..."):
        try:
            result = run_team_agentic_ingestion(
                project_root=project_root,
                task_id=config.task_id,
                recipe_id=config.recipe_id,
                raw_input_path=Path(config.selected_input_path),
                report_output_path=Path(config.report_output_path),
                provider=config.provider,
                model=config.model,
                api_key=config.api_key,
                runs_per_member=config.runs_per_member,
                max_members_per_team=config.max_members_per_team_value,
                dry_run=config.dry_run,
            )

            st.session_state["team_agentic_last_run"] = {
                "success": True,
                "task_id": result.task_id,
                "run_id": result.run_id,
                "run_dir": str(result.run_dir),
                "report_path": str(result.report_path),
                "dry_run": config.dry_run,
                "agent_results_count": len(result.agent_results),
                "consensus_reports_count": len(result.consensus_reports),
                "agent_outputs": [
                    {
                        "agent_id": item.agent_id,
                        "task_name": item.task_name,
                        "run_index": item.run_index,
                        "status": item.status,
                        "output_path": str(item.output_path),
                    }
                    for item in result.agent_results
                ],
                "consensus_summaries": [
                    {
                        "team_id": report.get("team_id"),
                        "task_name": report.get("task_name"),
                        "summary": report.get("summary", {}),
                    }
                    for report in result.consensus_reports
                ],
            }

            st.success("Team agentic ingestion finished.")

        except Exception as exc:
            st.session_state["team_agentic_last_run"] = {
                "success": False,
                "error_type": type(exc).__name__,
                "error_message": str(exc),
            }
            st.error("Pipeline execution failed.")
            st.exception(exc)


def render_last_run_result(*, project_root: Path) -> None:
    """Render last run result stored in session state."""

    last_run = st.session_state.get("team_agentic_last_run")

    if not last_run:
        return

    st.subheader("Last Pipeline Run")

    if not last_run.get("success"):
        st.error("Last run failed.")
        st.json(last_run)
        return

    st.success("Last run finished successfully.")

    agents_column, consensus_column, run_column = st.columns(3)
    agents_column.metric(
        "Agent outputs",
        last_run.get("agent_results_count", 0),
    )
    consensus_column.metric(
        "Consensus reports",
        last_run.get("consensus_reports_count", 0),
    )
    run_column.metric("Run ID", last_run.get("run_id", "Unknown"))

    st.caption(f"Task: {last_run.get('task_id', 'Unknown')}")

    if last_run.get("dry_run"):
        st.info(
            "Dry-run result: the artifacts verify the workflow structure and "
            "do not contain an engineering assessment."
        )

    with st.expander("Show run locations", expanded=False):
        st.code(
            "\n".join(
                [
                    "Run directory: "
                    + format_display_path(
                        Path(str(last_run.get("run_dir", ""))),
                        project_root,
                    ),
                    "Final report: "
                    + format_display_path(
                        Path(str(last_run.get("report_path", ""))),
                        project_root,
                    ),
                ]
            ),
            language="text",
        )

    render_result_artifacts(
        last_run=last_run,
        project_root=project_root,
    )

    st.warning(
        "Review status: unreviewed. Artifact browsing does not record a human "
        "decision or promote information to approved input."
    )


def render_result_artifacts(
    *,
    last_run: dict[str, Any],
    project_root: Path,
) -> None:
    """Render final report, run summary, consensus reports and agent outputs."""

    run_dir = Path(str(last_run.get("run_dir", "")))
    report_path = Path(str(last_run.get("report_path", "")))

    tab_report, tab_summary, tab_consensus, tab_agents, tab_paths = st.tabs(
        [
            "Final Ingestion Report",
            "Run Summary",
            "Consensus Reports",
            "Agent Outputs",
            "Artifact Paths",
        ]
    )

    with tab_report:
        render_markdown_file(
            title="Final Ingestion Report",
            path=report_path,
            project_root=project_root,
        )

    with tab_summary:
        render_markdown_file(
            title="Run Summary",
            path=run_dir / "team_agentic_ingestion_run_summary.md",
            project_root=project_root,
        )

    with tab_consensus:
        render_consensus_report_browser(
            run_dir=run_dir,
            project_root=project_root,
        )

    with tab_agents:
        render_agent_output_browser(
            run_dir=run_dir,
            project_root=project_root,
        )

    with tab_paths:
        render_artifact_paths(
            run_dir=run_dir,
            report_path=report_path,
            project_root=project_root,
        )


def render_markdown_file(
    *,
    title: str,
    path: Path,
    project_root: Path,
) -> None:
    """Render a Markdown file if it exists."""

    st.markdown(f"### {title}")

    if not path.exists():
        st.warning(f"File not found: {path}")
        return

    text = path.read_text(encoding="utf-8")

    st.caption(format_display_path(path, project_root))
    st.markdown(text)


def render_consensus_report_browser(
    *,
    run_dir: Path,
    project_root: Path,
) -> None:
    """Render selectable consensus Markdown reports."""

    st.markdown("### Consensus Reports")

    consensus_files = sorted(
        (run_dir / "consensus_reports").rglob("*_consensus.md")
    )

    if not consensus_files:
        st.warning("No consensus reports found.")
        return

    labels = [
        str(path.relative_to(run_dir))
        for path in consensus_files
    ]

    selected_label = st.selectbox(
        "Select consensus report",
        options=labels,
    )

    selected_path = run_dir / selected_label

    render_markdown_file(
        title=selected_label,
        path=selected_path,
        project_root=project_root,
    )


def render_agent_output_browser(
    *,
    run_dir: Path,
    project_root: Path,
) -> None:
    """Render selectable raw agent JSON outputs."""

    st.markdown("### Agent Outputs")

    output_files = sorted(
        (run_dir / "agent_outputs").rglob("*.json")
    )

    if not output_files:
        st.warning("No agent output files found.")
        return

    labels = [
        str(path.relative_to(run_dir))
        for path in output_files
    ]

    selected_label = st.selectbox(
        "Select agent output",
        options=labels,
    )

    selected_path = run_dir / selected_label

    st.caption(format_display_path(selected_path, project_root))

    try:
        import json

        payload = json.loads(selected_path.read_text(encoding="utf-8"))
        st.json(payload)
    except Exception:
        st.text_area(
            "Agent output",
            value=selected_path.read_text(encoding="utf-8"),
            height=500,
        )


def render_artifact_paths(
    *,
    run_dir: Path,
    report_path: Path,
    project_root: Path,
) -> None:
    """Render artifact path overview."""

    st.markdown("### Artifact Paths")

    path_overview = chr(10).join(
        [
            "Run directory:",
            format_display_path(run_dir, project_root),
            "",
            "Final report:",
            format_display_path(report_path, project_root),
        ]
    )

    st.code(path_overview, language="text")

    if not run_dir.exists():
        st.warning("Run directory not found.")
        return

    artifact_files = sorted(
        path for path in run_dir.rglob("*") if path.is_file()
    )

    st.markdown("### Files in Run Directory")

    st.code(
        "\n".join(
            format_display_path(path, project_root)
            for path in artifact_files
        ),
        language="text",
    )


def format_display_path(path: Path, project_root: Path) -> str:
    """Return a repository-relative path when the path belongs to the project."""

    candidate = path if path.is_absolute() else project_root / path

    try:
        return str(candidate.resolve().relative_to(project_root.resolve()))
    except ValueError:
        return str(path)


def format_file_size(size_bytes: int) -> str:
    """Format a byte count for compact display in the UI."""

    if size_bytes < 1024:
        return f"{size_bytes} B"

    size_kib = size_bytes / 1024

    if size_kib < 1024:
        return f"{size_kib:.1f} KiB"

    return f"{size_kib / 1024:.1f} MiB"


def validate_pipeline_config(config: PipelineConfig) -> list[str]:
    """Validate prepared pipeline configuration."""

    messages: list[str] = []

    if not config.task_id:
        messages.append("Task ID must not be empty.")

    if not config.recipe_id:
        messages.append("Recipe ID must not be empty.")

    if not Path(config.selected_input_path).exists():
        messages.append("Selected input file does not exist.")

    if Path(config.selected_input_path).suffix.lower() not in SUPPORTED_INPUT_SUFFIXES:
        messages.append("Selected input file type is not supported.")

    if not config.report_output_path.endswith(".md"):
        messages.append("Report output path must end with .md.")

    if config.runs_per_member < 1:
        messages.append("Runs per member must be at least 1.")

    if not config.dry_run and config.model == "dry-run-model":
        messages.append("dry-run-model cannot be used when dry run is disabled.")

    if not config.dry_run and config.provider == "openai":
        if not os.getenv("OPENAI_API_KEY") and not config.api_key:
            messages.append(
                "No OpenAI API key available. Set OPENAI_API_KEY or enter an API key in the UI."
            )

    return messages


def estimate_agent_runs(config: PipelineConfig) -> int:
    """Estimate number of agent executions for the current pipeline."""

    if config.max_members_per_team_value is None:
        ingestion_team_agents = 3 + 3 + 3 + 3
    else:
        ingestion_team_agents = 4 * config.max_members_per_team_value

    return ingestion_team_agents * config.runs_per_member


def parse_max_members_per_team(value: str) -> int | None:
    """Parse max members per team UI value."""

    normalized = value.strip().lower()

    if normalized == "all":
        return None

    return int(normalized)


def build_default_task_id(selected_input_path: Path) -> str:
    """Build a default task ID from the selected input file."""

    stem = selected_input_path.stem.upper()
    safe_stem = "".join(
        char if char.isalnum() else "_"
        for char in stem
    )

    return f"TASK_INGEST_{safe_stem}"


def build_default_report_filename(
    *,
    task_id: str,
    dry_run: bool,
) -> str:
    """Build default report filename."""

    safe_task_id = make_safe_filename(task_id.lower())

    if dry_run:
        return f"{safe_task_id}_team_agentic_ingestion_report_dry_run.md"

    return f"{safe_task_id}_team_agentic_ingestion_report.md"


def list_legacy_input_files(legacy_raw_dir: Path) -> list[Path]:
    """List supported legacy input files."""

    if not legacy_raw_dir.exists():
        return []

    files: list[Path] = []

    for path in legacy_raw_dir.rglob("*"):
        if not path.is_file():
            continue

        if path.suffix.lower() not in SUPPORTED_INPUT_SUFFIXES:
            continue

        files.append(path)

    return sorted(files)


def make_safe_filename(filename: str) -> str:
    """Create a simple safe filename."""

    cleaned = filename.strip().replace(" ", "_")

    allowed = []
    for char in cleaned:
        if char.isalnum() or char in {".", "_", "-"}:
            allowed.append(char)
        else:
            allowed.append("_")

    safe = "".join(allowed).strip("._")

    if not safe:
        safe = "unnamed_file.md"

    return safe
