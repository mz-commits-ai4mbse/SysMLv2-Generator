"""Tests for project-bound publication, review request and dashboard state."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
from pathlib import Path
from types import SimpleNamespace

import pytest

from modules.project_dashboard.service import ProjectDashboardService
from modules.project_ingestion import (
    ProjectBoundIngestionService,
    ProjectIngestionConfiguration,
    ProjectIngestionExecutionError,
)
from modules.project_processing import ProjectProcessingRepository
from modules.project_sources import ProjectSourceRegistry
from modules.semantic_consolidation.errors import (
    SemanticConsolidationIntegrityError,
)
from modules.project_workspace import ProjectWorkspace


PROJECT_ID = "123456"


class FixedClock:
    """Return deterministic increasing UTC timestamps."""

    def __init__(self) -> None:
        self.second = 0

    def __call__(self) -> datetime:
        self.second += 1
        return datetime(
            2026,
            7,
            27,
            18,
            0,
            self.second,
            tzinfo=timezone.utc,
        )


class CompletePipeline:
    """Write the complete Phase-F work contract or one controlled defect."""

    def __init__(
        self,
        *,
        omit_summary: bool = False,
        symlink_agent_output: bool = False,
    ) -> None:
        self.omit_summary = omit_summary
        self.symlink_agent_output = symlink_agent_output
        self.calls: list[dict[str, object]] = []

    def __call__(self, **kwargs):
        self.calls.append(dict(kwargs))
        project_root = Path(kwargs["project_root"])
        execution_root = (
            project_root / Path(kwargs["execution_root"])
        )
        report_path = (
            project_root / Path(kwargs["report_output_path"])
        )

        agent_dir = (
            execution_root
            / "agent_outputs"
            / "01_legacy_interpretation"
        )
        consensus_dir = (
            execution_root
            / "consensus_reports"
            / "01_legacy_interpretation"
        )
        agent_dir.mkdir(parents=True)
        consensus_dir.mkdir(parents=True)
        report_path.parent.mkdir(parents=True, exist_ok=True)

        if self.symlink_agent_output:
            outside = project_root / "outside-agent.json"
            outside.write_text("{}", encoding="utf-8")
            (
                agent_dir / "agent.json"
            ).symlink_to(outside)
        else:
            (
                agent_dir / "agent.json"
            ).write_text(
                '{"status":"dry_run"}',
                encoding="utf-8",
            )

        (
            consensus_dir / "consensus.json"
        ).write_text(
            '{"summary":{"review_required":1}}',
            encoding="utf-8",
        )
        report_path.write_text(
            "# Unreviewed Ingestion Review\n",
            encoding="utf-8",
        )

        if not self.omit_summary:
            (
                execution_root
                / "team_agentic_ingestion_run_summary.json"
            ).write_text(
                '{"run_id":"20260727T180000Z"}',
                encoding="utf-8",
            )
            (
                execution_root
                / "team_agentic_ingestion_run_summary.md"
            ).write_text(
                "# Run Summary\n",
                encoding="utf-8",
            )

        return SimpleNamespace(
            run_id="20260727T180000Z",
        )


class RecordingSemanticConsolidator:
    """Record the C2.2 service call or raise a controlled error."""

    def __init__(self, *, error: Exception | None = None) -> None:
        self.error = error
        self.calls: list[dict[str, object]] = []
        self.processing_root: Path | None = None
        self.event_types_at_call: tuple[str, ...] | None = None

    def __call__(self, **kwargs):
        self.calls.append(dict(kwargs))
        if self.processing_root is not None:
            history = ProjectProcessingRepository(
                root=self.processing_root
            ).load_run(
                kwargs["project_id"],
                kwargs["processing_run_id"],
            )
            self.event_types_at_call = tuple(
                event.event_type
                for event in history.events
            )
        if self.error is not None:
            raise self.error
        return None


def _noop_semantic_consolidator(**kwargs):
    """Keep legacy publication tests focused on publication behavior."""
    return None


def prepare_service(
    tmp_path: Path,
    pipeline: CompletePipeline,
    *,
    semantic_consolidator=_noop_semantic_consolidator,
):
    repository_root = tmp_path / "repository"
    projects_root = repository_root / "data" / "projects"
    projects_root.parent.mkdir(parents=True)

    workspace = ProjectWorkspace(
        root=projects_root,
        id_generator=lambda: PROJECT_ID,
    )
    workspace.create_project("P9 Publication")

    source_path = tmp_path / "requirements.txt"
    source_path.write_text(
        "The system shall preserve traceability.",
        encoding="utf-8",
    )
    source = ProjectSourceRegistry(
        root=projects_root
    ).register_source(
        PROJECT_ID,
        source_path,
        source_role="engineering_source",
    )

    service = ProjectBoundIngestionService(
        root=projects_root,
        repository_root=repository_root,
        pipeline_runner=pipeline,
        semantic_consolidator=semantic_consolidator,
        clock=FixedClock(),
    )
    return service, projects_root, repository_root, source


def test_successful_execution_publishes_and_requests_review(
    tmp_path: Path,
) -> None:
    pipeline = CompletePipeline()
    service, projects_root, repository_root, source = (
        prepare_service(tmp_path, pipeline)
    )

    result = service.execute_registered_source(
        PROJECT_ID,
        source.source_id,
        configuration=ProjectIngestionConfiguration(),
    )

    assert result.run_state == "awaiting_review"
    assert result.processing_stage == "agentic_ingestion"
    assert result.processing_run_id == "RUN-000001"
    assert result.attempt_id == "ATT-000001"
    assert result.recovery_required is False
    assert {
        reference.artifact_type
        for reference in result.artifact_references
    } == {
        "agent_outputs",
        "consensus_reports",
        "review_reports",
        "run_summaries",
    }
    assert len(result.artifact_references) == 5

    history = ProjectProcessingRepository(
        root=projects_root
    ).load_run(PROJECT_ID, "RUN-000001")
    assert tuple(
        event.event_type
        for event in history.events
    ) == (
        "run_created",
        "stage_started",
        "artifact_published",
        "review_requested",
    )
    assert history.events[-1].next_state == "awaiting_review"

    published_event = history.events[-2]
    assert published_event.artifact_references == (
        result.artifact_references
    )

    for reference in result.artifact_references:
        path = (
            repository_root
            / reference.repository_relative_path
        )
        assert path.is_file()
        assert hashlib.sha256(
            path.read_bytes()
        ).hexdigest() == reference.content_fingerprint

    dashboard = ProjectDashboardService(
        root=projects_root,
        repository_root=repository_root,
    ).source_processing_view(PROJECT_ID)
    row = next(
        item
        for item in dashboard.sources
        if item.source_id == source.source_id
    )
    assert row.current_processing_run_id == "RUN-000001"
    assert row.latest_attempt_id == "ATT-000001"
    assert row.run_state == "awaiting_review"
    assert row.processing_stage == "agentic_ingestion"
    assert row.pending_review is True


def test_missing_required_output_fails_without_publication(
    tmp_path: Path,
) -> None:
    pipeline = CompletePipeline(omit_summary=True)
    service, projects_root, _, source = prepare_service(
        tmp_path,
        pipeline,
    )

    result = service.execute_registered_source(
        PROJECT_ID,
        source.source_id,
        configuration=ProjectIngestionConfiguration(),
    )

    assert result.run_state == "failed"
    assert result.failure_reason == (
        "ingestion_output_validation_failed"
    )
    assert result.artifact_references == ()

    history = ProjectProcessingRepository(
        root=projects_root
    ).load_run(PROJECT_ID, "RUN-000001")
    assert tuple(
        event.event_type
        for event in history.events
    ) == (
        "run_created",
        "stage_started",
        "run_failed",
    )
    assert not (
        projects_root
        / PROJECT_ID
        / "runs"
        / "RUN-000001"
        / "artifacts"
    ).exists()


def test_symbolic_link_output_is_not_published(
    tmp_path: Path,
) -> None:
    pipeline = CompletePipeline(
        symlink_agent_output=True
    )
    service, projects_root, _, source = prepare_service(
        tmp_path,
        pipeline,
    )

    try:
        result = service.execute_registered_source(
            PROJECT_ID,
            source.source_id,
            configuration=ProjectIngestionConfiguration(),
        )
    except OSError:
        pytest.skip("Symbolic links are unavailable on this platform.")

    assert result.run_state == "failed"
    assert result.failure_reason == (
        "ingestion_output_validation_failed"
    )
    assert not (
        projects_root
        / PROJECT_ID
        / "runs"
        / "RUN-000001"
        / "artifacts"
    ).exists()


def test_api_key_is_not_persisted_in_result_or_history(
    tmp_path: Path,
) -> None:
    pipeline = CompletePipeline()
    service, projects_root, _, source = prepare_service(
        tmp_path,
        pipeline,
    )
    secret = "sk-private-test-secret"

    result = service.execute_registered_source(
        PROJECT_ID,
        source.source_id,
        configuration=ProjectIngestionConfiguration(
            dry_run=False,
        ),
        api_key=secret,
    )

    history = ProjectProcessingRepository(
        root=projects_root
    ).load_run(PROJECT_ID, "RUN-000001")

    assert secret not in repr(result)
    assert secret not in repr(history)
    assert pipeline.calls[0]["api_key"] == secret


def test_published_paths_are_repository_relative_and_project_bound(
    tmp_path: Path,
) -> None:
    pipeline = CompletePipeline()
    service, _, _, source = prepare_service(
        tmp_path,
        pipeline,
    )

    result = service.execute_registered_source(
        PROJECT_ID,
        source.source_id,
        configuration=ProjectIngestionConfiguration(),
    )

    for reference in result.artifact_references:
        path = Path(reference.repository_relative_path)
        assert not path.is_absolute()
        assert ".." not in path.parts
        assert path.parts[:3] == (
            "data",
            "projects",
            PROJECT_ID,
        )
        assert result.processing_run_id in path.parts
        assert result.attempt_id in path.parts


def test_second_current_run_for_same_source_is_rejected(
    tmp_path: Path,
) -> None:
    pipeline = CompletePipeline()
    service, projects_root, _, source = prepare_service(
        tmp_path,
        pipeline,
    )

    first = service.execute_registered_source(
        PROJECT_ID,
        source.source_id,
        configuration=ProjectIngestionConfiguration(),
    )
    assert first.run_state == "awaiting_review"

    with pytest.raises(ProjectIngestionExecutionError):
        service.execute_registered_source(
            PROJECT_ID,
            source.source_id,
            configuration=ProjectIngestionConfiguration(),
        )

    scan = ProjectProcessingRepository(
        root=projects_root
    ).scan_project(PROJECT_ID)
    assert tuple(
        history.manifest.processing_run_id
        for history in scan.run_histories
    ) == ("RUN-000001",)

def test_semantic_consolidator_runs_before_review_publication(
    tmp_path: Path,
) -> None:
    pipeline = CompletePipeline()
    semantic = RecordingSemanticConsolidator()
    service, projects_root, repository_root, source = prepare_service(
        tmp_path,
        pipeline,
        semantic_consolidator=semantic,
    )
    semantic.processing_root = projects_root
    secret = "sk-semantic-integration-test"
    configuration = ProjectIngestionConfiguration(
        provider="openai",
        model="gpt-test",
        dry_run=False,
    )

    result = service.execute_registered_source(
        PROJECT_ID,
        source.source_id,
        configuration=configuration,
        api_key=secret,
    )

    assert result.run_state == "awaiting_review"
    assert len(pipeline.calls) == 1
    assert len(semantic.calls) == 1
    assert semantic.event_types_at_call == (
        "run_created",
        "stage_started",
    )

    call = semantic.calls[0]
    assert call["project_id"] == PROJECT_ID
    assert call["processing_run_id"] == "RUN-000001"
    assert getattr(call["phase_f_result"], "run_id") == (
        "20260727T180000Z"
    )
    assert Path(call["phase_f_root"]).is_dir()
    assert call["repository_root"] == repository_root
    assert call["provider"] == "openai"
    assert call["model"] == "gpt-test"
    assert call["api_key"] == secret
    assert call["dry_run"] is False
    assert (
        Path(call["phase_f_root"])
        / "team_agentic_ingestion_run_summary.json"
    ).is_file()

    history = ProjectProcessingRepository(
        root=projects_root
    ).load_run(PROJECT_ID, "RUN-000001")
    assert tuple(
        event.event_type
        for event in history.events
    ) == (
        "run_created",
        "stage_started",
        "artifact_published",
        "review_requested",
    )
    assert history.events[-1].next_state == "awaiting_review"
    assert secret not in repr(result)
    assert secret not in repr(history)


def test_semantic_integrity_failure_blocks_publication_and_review(
    tmp_path: Path,
) -> None:
    pipeline = CompletePipeline()
    semantic = RecordingSemanticConsolidator(
        error=SemanticConsolidationIntegrityError(
            "controlled semantic integrity failure"
        )
    )
    service, projects_root, _, source = prepare_service(
        tmp_path,
        pipeline,
        semantic_consolidator=semantic,
    )
    semantic.processing_root = projects_root

    result = service.execute_registered_source(
        PROJECT_ID,
        source.source_id,
        configuration=ProjectIngestionConfiguration(),
    )

    assert len(semantic.calls) == 1
    assert semantic.event_types_at_call == (
        "run_created",
        "stage_started",
    )
    assert result.run_state == "failed"
    assert result.failure_reason == (
        "semantic_consolidation_integrity_failed"
    )
    assert result.artifact_references == ()

    history = ProjectProcessingRepository(
        root=projects_root
    ).load_run(PROJECT_ID, "RUN-000001")
    assert tuple(
        event.event_type
        for event in history.events
    ) == (
        "run_created",
        "stage_started",
        "run_failed",
    )
    assert not (
        projects_root
        / PROJECT_ID
        / "runs"
        / "RUN-000001"
        / "artifacts"
    ).exists()


def test_semantic_execution_failure_blocks_publication_and_review(
    tmp_path: Path,
) -> None:
    pipeline = CompletePipeline()
    semantic = RecordingSemanticConsolidator(
        error=RuntimeError(
            "controlled semantic execution failure"
        )
    )
    service, projects_root, _, source = prepare_service(
        tmp_path,
        pipeline,
        semantic_consolidator=semantic,
    )
    semantic.processing_root = projects_root

    result = service.execute_registered_source(
        PROJECT_ID,
        source.source_id,
        configuration=ProjectIngestionConfiguration(),
    )

    assert len(semantic.calls) == 1
    assert semantic.event_types_at_call == (
        "run_created",
        "stage_started",
    )
    assert result.run_state == "failed"
    assert result.failure_reason == (
        "semantic_consolidation_execution_failed"
    )
    assert result.artifact_references == ()

    history = ProjectProcessingRepository(
        root=projects_root
    ).load_run(PROJECT_ID, "RUN-000001")
    assert tuple(
        event.event_type
        for event in history.events
    ) == (
        "run_created",
        "stage_started",
        "run_failed",
    )
    assert not (
        projects_root
        / PROJECT_ID
        / "runs"
        / "RUN-000001"
        / "artifacts"
    ).exists()
