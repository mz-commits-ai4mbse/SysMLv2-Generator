"""Integration tests for the public project-processing summary service."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

import modules.project_processing as public_api
from modules.project_processing import (
    ProcessingIssue,
    ProcessingReferenceError,
    ProcessingScanResult,
    ProcessingValidationError,
    ProjectProcessingOperations,
    ProjectProcessingSummaryService,
    ProjectProcessingRepository,
    create_processing_event,
    create_processing_run_history,
    create_processing_run_manifest,
    create_semantic_reference_version,
)
from modules.project_processing.errors import ProcessingRecoveryRequiredError
from modules.project_sources import (
    ENGINEERING_SOURCE_ROLE,
    ProjectSourceRegistry,
    SourceIssue,
    SourceManifest,
    SourceScanResult,
)


PROJECT_ID = "318604"
SOURCE_ID = "SRC-000001"
SOURCE_SHA = "a" * 64
TIMESTAMP = "2026-07-25T10:00:00Z"


class FakeSourceRegistry:
    def __init__(self, result: object) -> None:
        self.result = result
        self.calls: list[str] = []

    def scan_sources(self, project_id: str) -> object:
        self.calls.append(project_id)
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


class FakeProcessingOperations:
    def __init__(self, result: object) -> None:
        self.result = result
        self.calls: list[str] = []

    def scan_project(self, project_id: str) -> object:
        self.calls.append(project_id)
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


def source_manifest(
    source_id: str = SOURCE_ID,
    *,
    sha256: str = SOURCE_SHA,
) -> SourceManifest:
    return SourceManifest(
        schema_version="1.0.0",
        project_id=PROJECT_ID,
        source_id=source_id,
        source_role=ENGINEERING_SOURCE_ROLE,
        original_filename=f"{source_id.lower()}.txt",
        stored_filename="content.txt",
        media_type="text/plain",
        size_bytes=1,
        sha256=sha256,
        registered_at=TIMESTAMP,
        updated_at=TIMESTAMP,
    )


def run_history(state: str = "created"):
    manifest = create_processing_run_manifest(
        project_id=PROJECT_ID,
        processing_run_id="RUN-000001",
        source_id=SOURCE_ID,
        source_sha256=SOURCE_SHA,
        source_role_snapshot=ENGINEERING_SOURCE_ROLE,
        workflow_profile="engineering_source_processing",
        configuration_fingerprint="b" * 64,
        framework_template_id="TURING_RFLP_FRAMEWORK",
        framework_template_version="1.0.0",
        semantic_reference_versions=(
            create_semantic_reference_version(
                reference_system_id="TURING_SEMANTICS",
                reference_version="1.0.0",
            ),
        ),
        timestamp=TIMESTAMP,
    )
    first = create_processing_event(
        project_id=PROJECT_ID,
        processing_run_id="RUN-000001",
        event_id="EVT-000001",
        event_sequence=1,
        previous_state=None,
        next_state="created",
        processing_stage=None,
        event_type="run_created",
        attempt_id=None,
        reason_code="run_created",
        artifact_references=(),
        timestamp=TIMESTAMP,
        previous_event_fingerprint=None,
    )
    events = (first,)

    if state == "running":
        second = create_processing_event(
            project_id=PROJECT_ID,
            processing_run_id="RUN-000001",
            event_id="EVT-000002",
            event_sequence=2,
            previous_state="created",
            next_state="running",
            processing_stage="source_projection",
            event_type="stage_started",
            attempt_id="ATT-000001",
            reason_code="stage_started",
            artifact_references=(),
            timestamp="2026-07-25T10:01:00Z",
            previous_event_fingerprint=first.event_fingerprint,
        )
        events += (second,)

    if state == "completed":
        running = run_history("running")
        second = running.events[-1]
        third = create_processing_event(
            project_id=PROJECT_ID,
            processing_run_id="RUN-000001",
            event_id="EVT-000003",
            event_sequence=3,
            previous_state="running",
            next_state="completed",
            processing_stage="publication",
            event_type="run_completed",
            attempt_id=None,
            reason_code="workflow_resolved",
            artifact_references=(),
            timestamp="2026-07-25T10:02:00Z",
            previous_event_fingerprint=second.event_fingerprint,
        )
        return create_processing_run_history(
            manifest=manifest,
            events=running.events + (third,),
        )

    return create_processing_run_history(
        manifest=manifest,
        events=events,
    )


def service(
    source_scan: object,
    processing_scan: object = ProcessingScanResult(),
) -> tuple[
    ProjectProcessingSummaryService,
    FakeSourceRegistry,
    FakeProcessingOperations,
]:
    sources = FakeSourceRegistry(source_scan)
    processing = FakeProcessingOperations(processing_scan)
    return (
        ProjectProcessingSummaryService(
            root=Path("unused"),
            source_registry=sources,
            processing_operations=processing,
        ),
        sources,
        processing,
    )


def test_default_service_wires_project_local_dependencies(tmp_path: Path) -> None:
    summary_service = ProjectProcessingSummaryService(tmp_path / "projects")

    assert summary_service.root == tmp_path / "projects"
    assert isinstance(summary_service.source_registry, ProjectSourceRegistry)
    assert isinstance(
        summary_service.processing_operations,
        ProjectProcessingOperations,
    )
    assert summary_service.source_registry.root == tmp_path / "projects"
    assert summary_service.processing_operations.root == tmp_path / "projects"


def test_collect_scans_delegates_once_to_each_authority() -> None:
    source_scan = SourceScanResult()
    processing_scan = ProcessingScanResult()
    summary_service, sources, processing = service(
        source_scan,
        processing_scan,
    )

    collected = summary_service.collect_scans(PROJECT_ID)

    assert collected == (source_scan, processing_scan)
    assert sources.calls == [PROJECT_ID]
    assert processing.calls == [PROJECT_ID]


def test_empty_project_summary_is_derived() -> None:
    summary_service, _, _ = service(SourceScanResult())

    summary = summary_service.project_summary(PROJECT_ID)

    assert summary.project_state == "empty"
    assert summary.total_sources == 0
    assert summary.source_summaries == ()


def test_registered_source_without_run_is_not_started() -> None:
    summary_service, _, _ = service(
        SourceScanResult(valid_sources=(source_manifest(),))
    )

    summary = summary_service.project_summary(PROJECT_ID)

    assert summary.project_state == "not_started"
    assert summary.not_started_sources == 1
    assert summary.in_scope_sources == 1


def test_running_run_is_exposed_as_in_progress() -> None:
    summary_service, _, _ = service(
        SourceScanResult(valid_sources=(source_manifest(),)),
        ProcessingScanResult(run_histories=(run_history("running"),)),
    )

    summary = summary_service.project_summary(PROJECT_ID)

    assert summary.project_state == "in_progress"
    assert summary.running_sources == 1
    assert summary.source_summaries[0].latest_attempt_id == "ATT-000001"


def test_completed_run_is_exposed_as_processed() -> None:
    summary_service, _, _ = service(
        SourceScanResult(valid_sources=(source_manifest(),)),
        ProcessingScanResult(run_histories=(run_history("completed"),)),
    )

    summary = summary_service.project_summary(PROJECT_ID)

    assert summary.project_state == "processed"
    assert summary.completed_sources == 1


def test_source_summaries_are_returned_in_source_order() -> None:
    second = source_manifest("SRC-000002", sha256="c" * 64)
    first = source_manifest()
    summary_service, _, _ = service(
        SourceScanResult(valid_sources=(second, first))
    )

    summaries = summary_service.source_summaries(PROJECT_ID)

    assert tuple(summary.source_id for summary in summaries) == (
        "SRC-000001",
        "SRC-000002",
    )


def test_source_summary_returns_exact_registered_source() -> None:
    summary_service, _, _ = service(
        SourceScanResult(valid_sources=(source_manifest(),))
    )

    summary = summary_service.source_summary(PROJECT_ID, SOURCE_ID)

    assert summary.source_id == SOURCE_ID
    assert summary.processing_disposition == "in_scope"


def test_source_summary_rejects_unknown_registered_source() -> None:
    summary_service, _, _ = service(SourceScanResult())

    with pytest.raises(ProcessingReferenceError):
        summary_service.source_summary(PROJECT_ID, SOURCE_ID)


def test_source_summary_validates_source_identifier_before_scanning() -> None:
    summary_service, sources, processing = service(SourceScanResult())

    with pytest.raises(Exception):
        summary_service.source_summary(PROJECT_ID, "SRC-0")

    assert sources.calls == []
    assert processing.calls == []


def test_blocking_processing_issue_produces_attention_required() -> None:
    issue = ProcessingIssue(
        project_id=PROJECT_ID,
        code="recovery_required",
        message="Recovery is required.",
        issue_level="blocking",
    )
    summary_service, _, _ = service(
        SourceScanResult(valid_sources=(source_manifest(),)),
        ProcessingScanResult(issues=(issue,)),
    )

    summary = summary_service.project_summary(PROJECT_ID)

    assert summary.project_state == "attention_required"
    assert summary.issues == (issue,)


def test_source_issue_is_included_in_summary() -> None:
    issue = SourceIssue(
        project_id=PROJECT_ID,
        source_id=SOURCE_ID,
        code="invalid_source_content",
        message="Source content is invalid.",
        path=Path("data/projects/318604/sources/SRC-000001"),
    )
    summary_service, _, _ = service(
        SourceScanResult(
            valid_sources=(source_manifest(),),
            source_issues=(issue,),
        )
    )

    summary = summary_service.project_summary(PROJECT_ID)

    assert summary.project_state == "attention_required"
    assert summary.source_summaries[0].blocking_issue_codes == (
        "invalid_source_content",
    )


def test_source_registry_failure_is_not_hidden() -> None:
    expected = RuntimeError("source scan failed")
    summary_service, _, processing = service(expected)

    with pytest.raises(RuntimeError, match="source scan failed"):
        summary_service.project_summary(PROJECT_ID)

    assert processing.calls == []


def test_processing_scan_failure_is_not_hidden() -> None:
    expected = ProcessingRecoveryRequiredError("processing scan failed")
    summary_service, sources, _ = service(SourceScanResult(), expected)

    with pytest.raises(
        ProcessingRecoveryRequiredError,
        match="processing scan failed",
    ):
        summary_service.project_summary(PROJECT_ID)

    assert sources.calls == [PROJECT_ID]


def test_invalid_source_scan_contract_is_rejected() -> None:
    summary_service, _, _ = service(object())

    with pytest.raises(ProcessingValidationError):
        summary_service.project_summary(PROJECT_ID)


def test_invalid_processing_scan_contract_is_rejected() -> None:
    summary_service, _, _ = service(SourceScanResult(), object())

    with pytest.raises(ProcessingValidationError):
        summary_service.project_summary(PROJECT_ID)


def test_repeated_summary_derivation_is_deterministic() -> None:
    source_scan = SourceScanResult(valid_sources=(source_manifest(),))
    processing_scan = ProcessingScanResult(
        run_histories=(run_history("running"),)
    )
    summary_service, _, _ = service(source_scan, processing_scan)

    first = summary_service.project_summary(PROJECT_ID)
    second = summary_service.project_summary(PROJECT_ID)

    assert first == second
    assert source_scan.valid_sources == (source_manifest(),)
    assert processing_scan.run_histories == (run_history("running"),)


def test_service_does_not_create_independent_current_state() -> None:
    summary_service, _, _ = service(
        SourceScanResult(valid_sources=(source_manifest(),)),
        ProcessingScanResult(run_histories=(run_history("running"),)),
    )

    assert not hasattr(summary_service, "current_state")
    assert not hasattr(summary_service, "summary_cache")


def test_public_api_exports_integration_entrypoints() -> None:
    assert public_api.ProjectProcessingRepository is ProjectProcessingRepository
    assert public_api.ProjectProcessingOperations is ProjectProcessingOperations
    assert (
        public_api.ProjectProcessingSummaryService
        is ProjectProcessingSummaryService
    )
    assert callable(public_api.derive_project_processing_summary)
    assert callable(public_api.derive_source_processing_summaries)


def test_public_api_all_has_no_duplicates() -> None:
    assert len(public_api.__all__) == len(set(public_api.__all__))


def test_public_api_all_names_resolve() -> None:
    unresolved = tuple(
        name for name in public_api.__all__ if not hasattr(public_api, name)
    )

    assert unresolved == ()