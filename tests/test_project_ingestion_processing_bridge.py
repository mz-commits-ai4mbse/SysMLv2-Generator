"""Tests for the P9 Phase-F to P5 Processing Run bridge."""

from __future__ import annotations

from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace

from pypdf import PdfWriter

from modules.project_ingestion import (
    ProjectBoundIngestionService,
    ProjectIngestionConfiguration,
    calculate_ingestion_configuration_fingerprint,
)
from modules.project_processing import (
    PROCESSING_STAGES,
    ProjectProcessingRepository,
)
from modules.project_processing.paths import (
    PROCESSING_ARTIFACT_KINDS,
)
from modules.project_sources import (
    ProjectSourceRegistry,
)
from modules.project_workspace import ProjectWorkspace


PROJECT_ID = "123456"


class FixedClock:
    """Deterministic timezone-aware clock."""

    def __init__(self) -> None:
        self._second = 0

    def __call__(self) -> datetime:
        self._second += 1
        return datetime(
            2026,
            7,
            27,
            12,
            0,
            self._second,
            tzinfo=timezone.utc,
        )


class FakePipelineRunner:
    """Capture project-bound execution and write minimal work output."""

    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.calls: list[dict[str, object]] = []
        self.raw_texts: list[str] = []

    def __call__(self, **kwargs):
        self.calls.append(dict(kwargs))

        if self.fail:
            raise RuntimeError("private pipeline failure")

        project_root = Path(kwargs["project_root"])
        raw_input_path = project_root / Path(
            kwargs["raw_input_path"]
        )
        execution_root = project_root / Path(
            kwargs["execution_root"]
        )
        report_output_path = project_root / Path(
            kwargs["report_output_path"]
        )

        self.raw_texts.append(
            raw_input_path.read_text(encoding="utf-8")
        )
        execution_root.mkdir(parents=True)
        (
            execution_root / "phase_f_marker.txt"
        ).write_text("executed", encoding="utf-8")
        report_output_path.parent.mkdir(parents=True, exist_ok=True)
        report_output_path.write_text(
            "# Unreviewed report\n",
            encoding="utf-8",
        )

        return SimpleNamespace(
            run_id="20260727T120000Z",
        )


def build_text_pdf(text: str) -> bytes:
    """Build a minimal one-page PDF with a machine-readable text layer."""

    escaped_text = (
        text.replace("\\", "\\\\")
        .replace("(", "\\(")
        .replace(")", "\\)")
    )
    content_stream = (
        "BT\n"
        "/F1 12 Tf\n"
        "72 720 Td\n"
        f"({escaped_text}) Tj\n"
        "ET\n"
    ).encode("latin-1")

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        (
            b"<< /Type /Pages /Kids [3 0 R] "
            b"/Count 1 >>"
        ),
        (
            b"<< /Type /Page /Parent 2 0 R "
            b"/MediaBox [0 0 612 792] "
            b"/Resources << /Font << "
            b"/F1 4 0 R >> >> "
            b"/Contents 5 0 R >>"
        ),
        (
            b"<< /Type /Font /Subtype /Type1 "
            b"/BaseFont /Helvetica >>"
        ),
        (
            b"<< /Length "
            + str(len(content_stream)).encode("ascii")
            + b" >>\nstream\n"
            + content_stream
            + b"endstream"
        ),
    ]

    result = bytearray(
        b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"
    )
    offsets = [0]

    for object_number, object_content in enumerate(
        objects,
        start=1,
    ):
        offsets.append(len(result))
        result.extend(
            f"{object_number} 0 obj\n".encode("ascii")
        )
        result.extend(object_content)
        result.extend(b"\nendobj\n")

    xref_offset = len(result)
    result.extend(
        f"xref\n0 {len(objects) + 1}\n".encode("ascii")
    )
    result.extend(b"0000000000 65535 f \n")

    for offset in offsets[1:]:
        result.extend(
            f"{offset:010d} 00000 n \n".encode("ascii")
        )

    result.extend(
        (
            "trailer\n"
            f"<< /Size {len(objects) + 1} "
            "/Root 1 0 R >>\n"
            "startxref\n"
            f"{xref_offset}\n"
            "%%EOF\n"
        ).encode("ascii")
    )

    return bytes(result)


def build_blank_pdf() -> bytes:
    stream = BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    writer.write(stream)
    return stream.getvalue()


def prepare_project(tmp_path: Path):
    repository_root = tmp_path / "repository"
    projects_root = repository_root / "data" / "projects"
    projects_root.parent.mkdir(parents=True)

    workspace = ProjectWorkspace(
        root=projects_root,
        id_generator=lambda: PROJECT_ID,
    )
    workspace.create_project("P9 Processing Bridge")

    return repository_root, projects_root


def register_source(
    projects_root: Path,
    tmp_path: Path,
    *,
    filename: str,
    content: bytes,
    source_role: str = "engineering_source",
):
    input_path = tmp_path / filename
    input_path.write_bytes(content)
    registry = ProjectSourceRegistry(root=projects_root)
    return registry.register_source(
        PROJECT_ID,
        input_path,
        source_role=source_role,
    )


def create_service(
    repository_root: Path,
    projects_root: Path,
    pipeline: FakePipelineRunner,
) -> ProjectBoundIngestionService:
    return ProjectBoundIngestionService(
        root=projects_root,
        repository_root=repository_root,
        pipeline_runner=pipeline,
        clock=FixedClock(),
    )


def test_p9_extends_canonical_processing_vocabularies():
    assert "agentic_ingestion" in PROCESSING_STAGES
    assert {
        "agent_outputs",
        "consensus_reports",
        "review_reports",
        "run_summaries",
    } <= PROCESSING_ARTIFACT_KINDS


def test_configuration_fingerprint_is_deterministic_and_secret_free():
    configuration = ProjectIngestionConfiguration(
        dry_run=False,
        runs_per_member=2,
        max_members_per_team=None,
    )

    first = calculate_ingestion_configuration_fingerprint(
        configuration
    )
    second = calculate_ingestion_configuration_fingerprint(
        configuration
    )

    assert first == second
    assert len(first) == 64
    assert not hasattr(configuration, "api_key")


def test_execute_creates_run_and_started_attempt(tmp_path: Path):
    repository_root, projects_root = prepare_project(tmp_path)
    source = register_source(
        projects_root,
        tmp_path,
        filename="requirements.txt",
        content=b"The system shall preserve traceability.",
    )
    pipeline = FakePipelineRunner()
    service = create_service(
        repository_root,
        projects_root,
        pipeline,
    )

    result = service.execute_registered_source_to_work(
        PROJECT_ID,
        source.source_id,
        configuration=ProjectIngestionConfiguration(),
    )

    assert result.run_state == "running"
    assert result.processing_stage == "agentic_ingestion"
    assert result.processing_run_id == "RUN-000001"
    assert result.attempt_id == "ATT-000001"
    assert result.source_projection_id == "SP-000001"
    assert result.projection_result == "complete"
    assert result.phase_f_run_id == "20260727T120000Z"
    assert result.failure_reason is None

    history = ProjectProcessingRepository(
        root=projects_root
    ).load_run(
        PROJECT_ID,
        result.processing_run_id,
    )
    assert tuple(
        event.event_type
        for event in history.events
    ) == (
        "run_created",
        "stage_started",
    )
    assert history.events[-1].next_state == "running"
    assert history.events[-1].processing_stage == (
        "agentic_ingestion"
    )
    assert history.manifest.source_id == source.source_id
    assert history.manifest.source_sha256 == source.sha256
    assert history.manifest.framework_template_id == (
        "TURING_RFLP_FRAMEWORK"
    )
    assert history.manifest.framework_template_version == (
        "1.0.0"
    )


def test_execution_uses_repository_relative_projection_and_work_paths(
    tmp_path: Path,
):
    repository_root, projects_root = prepare_project(tmp_path)
    source = register_source(
        projects_root,
        tmp_path,
        filename="requirements.md",
        content=b"# Requirement\n\nThe system shall operate.",
    )
    pipeline = FakePipelineRunner()
    service = create_service(
        repository_root,
        projects_root,
        pipeline,
    )

    result = service.execute_registered_source_to_work(
        PROJECT_ID,
        source.source_id,
        configuration=ProjectIngestionConfiguration(),
        api_key="not-persisted-secret",
    )

    assert result.run_state == "running"
    assert len(pipeline.calls) == 1
    call = pipeline.calls[0]

    for field in (
        "raw_input_path",
        "report_output_path",
        "execution_root",
    ):
        value = Path(call[field])
        assert not value.is_absolute()
        assert ".." not in value.parts

    assert str(call["raw_input_path"]).startswith(
        f"data/projects/{PROJECT_ID}/semantics/"
    )
    assert str(call["execution_root"]).startswith(
        f"data/projects/{PROJECT_ID}/runs/RUN-000001/"
        "work/agentic_ingestion/ATT-000001/"
    )
    assert call["api_key"] == "not-persisted-secret"

    history = ProjectProcessingRepository(
        root=projects_root
    ).load_run(PROJECT_ID, "RUN-000001")
    assert "not-persisted-secret" not in repr(history)
    assert "not-persisted-secret" not in repr(result)


def test_text_layer_pdf_is_projected_before_phase_f(tmp_path: Path):
    repository_root, projects_root = prepare_project(tmp_path)
    source = register_source(
        projects_root,
        tmp_path,
        filename="requirements.pdf",
        content=build_text_pdf(
            "The system shall operate."
        ),
    )
    pipeline = FakePipelineRunner()
    service = create_service(
        repository_root,
        projects_root,
        pipeline,
    )

    result = service.execute_registered_source_to_work(
        PROJECT_ID,
        source.source_id,
        configuration=ProjectIngestionConfiguration(),
    )

    assert result.run_state == "running"
    assert result.projection_result == "complete"
    assert pipeline.raw_texts == [
        "The system shall operate."
    ]


def test_pdf_without_text_layer_fails_before_phase_f(tmp_path: Path):
    repository_root, projects_root = prepare_project(tmp_path)
    source = register_source(
        projects_root,
        tmp_path,
        filename="scanned.pdf",
        content=build_blank_pdf(),
    )
    pipeline = FakePipelineRunner()
    service = create_service(
        repository_root,
        projects_root,
        pipeline,
    )

    result = service.execute_registered_source_to_work(
        PROJECT_ID,
        source.source_id,
        configuration=ProjectIngestionConfiguration(),
    )

    assert result.run_state == "failed"
    assert result.projection_result == "unavailable"
    assert result.failure_reason == (
        "text_extraction_insufficient"
    )
    assert pipeline.calls == []

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
    assert history.events[-1].reason_code == (
        "text_extraction_insufficient"
    )


def test_phase_f_failure_becomes_p5_failed_state(tmp_path: Path):
    repository_root, projects_root = prepare_project(tmp_path)
    source = register_source(
        projects_root,
        tmp_path,
        filename="requirements.txt",
        content=b"Engineering source.",
    )
    pipeline = FakePipelineRunner(fail=True)
    service = create_service(
        repository_root,
        projects_root,
        pipeline,
    )

    result = service.execute_registered_source_to_work(
        PROJECT_ID,
        source.source_id,
        configuration=ProjectIngestionConfiguration(),
    )

    assert result.run_state == "failed"
    assert result.failure_reason == (
        "team_agentic_ingestion_failed"
    )

    history = ProjectProcessingRepository(
        root=projects_root
    ).load_run(PROJECT_ID, "RUN-000001")
    assert history.events[-1].event_type == "run_failed"
    assert history.events[-1].next_state == "failed"
    assert history.events[-1].reason_code == (
        "team_agentic_ingestion_failed"
    )


def test_context_source_uses_context_workflow_profile(
    tmp_path: Path,
):
    repository_root, projects_root = prepare_project(tmp_path)
    source = register_source(
        projects_root,
        tmp_path,
        filename="context.txt",
        content=b"Supporting context.",
        source_role="context_only",
    )
    pipeline = FakePipelineRunner()
    service = create_service(
        repository_root,
        projects_root,
        pipeline,
    )

    result = service.execute_registered_source_to_work(
        PROJECT_ID,
        source.source_id,
        configuration=ProjectIngestionConfiguration(),
    )

    history = ProjectProcessingRepository(
        root=projects_root
    ).load_run(
        PROJECT_ID,
        result.processing_run_id,
    )
    assert history.manifest.workflow_profile == (
        "context_only_processing"
    )


def test_new_artifact_kinds_accept_agentic_ingestion_attempt(
    tmp_path: Path,
):
    repository_root, projects_root = prepare_project(tmp_path)
    source = register_source(
        projects_root,
        tmp_path,
        filename="requirements.txt",
        content=b"Engineering source.",
    )
    pipeline = FakePipelineRunner()
    service = create_service(
        repository_root,
        projects_root,
        pipeline,
    )
    result = service.execute_registered_source_to_work(
        PROJECT_ID,
        source.source_id,
        configuration=ProjectIngestionConfiguration(),
    )

    processing = ProjectProcessingRepository(
        root=projects_root
    )
    review_directory = processing.prepare_attempt_directory(
        PROJECT_ID,
        result.processing_run_id,
        artifact_kind="review_reports",
        processing_stage="agentic_ingestion",
        attempt_id=result.attempt_id,
    )
    summary_directory = processing.prepare_attempt_directory(
        PROJECT_ID,
        result.processing_run_id,
        artifact_kind="run_summaries",
        processing_stage="agentic_ingestion",
        attempt_id=result.attempt_id,
    )

    assert review_directory.is_dir()
    assert summary_directory.is_dir()
