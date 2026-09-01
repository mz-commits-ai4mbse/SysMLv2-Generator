"""Tests for source-level and project-level Processing State aggregation."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from modules.project_sources import (
    CONTEXT_ONLY_SOURCE_ROLE,
    ENGINEERING_SOURCE_ROLE,
    SourceIssue,
    SourceManifest,
    SourceScanResult,
)
from modules.project_processing.aggregation import (
    derive_project_processing_summary,
    derive_source_processing_summaries,
)
from modules.project_processing.artifact_lifecycle import (
    create_artifact_invalidation_event,
)
from modules.project_processing.decision_manifest import (
    create_processing_decision,
)
from modules.project_processing.errors import (
    ProcessingIntegrityError,
    ProcessingReferenceError,
    ProcessingValidationError,
)
from modules.project_processing.event_manifest import (
    create_processing_artifact_reference,
    create_processing_event,
)
from modules.project_processing.history import (
    create_processing_run_history,
)
from modules.project_processing.run_lifecycle import (
    create_run_superseded_event,
)
from modules.project_processing.run_manifest import (
    create_processing_run_manifest,
    create_semantic_reference_version,
)
from modules.project_processing.types import (
    ProcessingIssue,
    ProcessingScanResult,
)


PROJECT_ID = "318604"
OTHER_PROJECT_ID = "481516"
SHA_A = "a" * 64
SHA_B = "b" * 64


def source(
    source_id: str = "SRC-000001",
    *,
    project_id: str = PROJECT_ID,
    role: str = ENGINEERING_SOURCE_ROLE,
    sha256: str = SHA_A,
) -> SourceManifest:
    return SourceManifest(
        schema_version="1.0.0",
        project_id=project_id,
        source_id=source_id,
        source_role=role,
        original_filename=f"{source_id.lower()}.txt",
        stored_filename="content.txt",
        media_type="text/plain",
        size_bytes=1,
        sha256=sha256,
        registered_at="2026-07-25T09:00:00Z",
        updated_at="2026-07-25T09:00:00Z",
    )


def source_scan(*sources, issues=()) -> SourceScanResult:
    return SourceScanResult(
        valid_sources=tuple(sources),
        source_issues=tuple(issues),
    )


def manifest(
    run_id: str = "RUN-000001",
    *,
    source_id: str = "SRC-000001",
    project_id: str = PROJECT_ID,
    source_sha256: str = SHA_A,
    role: str = ENGINEERING_SOURCE_ROLE,
    workflow_profile: str = "engineering_source_processing",
    configuration: str = "c" * 64,
    supersedes_run_id: str | None = None,
    timestamp: str = "2026-07-25T10:00:00Z",
):
    return create_processing_run_manifest(
        project_id=project_id,
        processing_run_id=run_id,
        source_id=source_id,
        source_sha256=source_sha256,
        source_role_snapshot=role,
        workflow_profile=workflow_profile,
        configuration_fingerprint=configuration,
        framework_template_id="TURING_RFLP_FRAMEWORK",
        framework_template_version="1.0.0",
        semantic_reference_versions=(
            create_semantic_reference_version(
                reference_system_id="PROJECT_GLOSSARY",
                reference_version="1.0.0",
            ),
        ),
        timestamp=timestamp,
        supersedes_run_id=supersedes_run_id,
    )


def initial_history(run_manifest=None):
    run_manifest = run_manifest or manifest()
    event = create_processing_event(
        project_id=run_manifest.project_id,
        processing_run_id=run_manifest.processing_run_id,
        event_id="EVT-000001",
        event_sequence=1,
        previous_state=None,
        next_state="created",
        processing_stage=None,
        event_type="run_created",
        attempt_id=None,
        reason_code="run_created",
        artifact_references=(),
        timestamp="2026-07-25T10:00:00Z",
        previous_event_fingerprint=None,
    )
    return create_processing_run_history(
        manifest=run_manifest,
        events=(event,),
    )


def append_event(
    history,
    *,
    next_state: str,
    event_type: str,
    reason_code: str,
    timestamp: str,
    processing_stage: str | None = None,
    attempt_id: str | None = None,
    artifact_references=(),
):
    previous = history.events[-1]
    sequence = len(history.events) + 1
    event = create_processing_event(
        project_id=history.manifest.project_id,
        processing_run_id=history.manifest.processing_run_id,
        event_id=f"EVT-{sequence:06d}",
        event_sequence=sequence,
        previous_state=previous.next_state,
        next_state=next_state,
        processing_stage=processing_stage,
        event_type=event_type,
        attempt_id=attempt_id,
        reason_code=reason_code,
        artifact_references=tuple(artifact_references),
        timestamp=timestamp,
        previous_event_fingerprint=previous.event_fingerprint,
    )
    return create_processing_run_history(
        manifest=history.manifest,
        events=history.events + (event,),
    )


def history_in_state(
    state: str,
    *,
    run_manifest=None,
    reason_code: str | None = None,
):
    history = initial_history(run_manifest)
    if state == "created":
        return history
    if state == "running":
        return append_event(
            history,
            next_state="running",
            event_type="stage_started",
            reason_code=reason_code or "stage_started",
            timestamp="2026-07-25T10:01:00Z",
            processing_stage="semantic_extraction",
            attempt_id="ATT-000001",
        )
    if state == "blocked":
        return append_event(
            history,
            next_state="blocked",
            event_type="run_blocked",
            reason_code=reason_code or "missing_projection",
            timestamp="2026-07-25T10:01:00Z",
        )
    if state == "failed":
        return append_event(
            history,
            next_state="failed",
            event_type="run_failed",
            reason_code=reason_code or "provider_failure",
            timestamp="2026-07-25T10:01:00Z",
        )

    history = history_in_state("running", run_manifest=run_manifest)
    if state == "awaiting_review":
        return append_event(
            history,
            next_state="awaiting_review",
            event_type="review_requested",
            reason_code=reason_code or "human_review_required",
            timestamp="2026-07-25T10:02:00Z",
            processing_stage="human_review",
            attempt_id="ATT-000001",
        )
    if state == "completed":
        return append_event(
            history,
            next_state="completed",
            event_type="run_completed",
            reason_code=reason_code or "workflow_resolved",
            timestamp="2026-07-25T10:02:00Z",
        )
    raise AssertionError(f"unsupported fixture state: {state}")


def artifact(
    artifact_id: str = "IU-000001",
    *,
    fingerprint: str = "d" * 64,
    path: str | None = None,
):
    return create_processing_artifact_reference(
        artifact_type="information_unit",
        artifact_id=artifact_id,
        content_fingerprint=fingerprint,
        repository_relative_path=(
            path
            if path is not None
            else f"data/projects/{PROJECT_ID}/semantics/{artifact_id}.json"
        ),
    )


def history_with_invalidated_artifact():
    history = history_in_state("running")
    reference = artifact()
    history = append_event(
        history,
        next_state="running",
        event_type="artifact_published",
        reason_code="artifact_published",
        timestamp="2026-07-25T10:02:00Z",
        processing_stage="publication",
        attempt_id="ATT-000001",
        artifact_references=(reference,),
    )
    invalidated = create_artifact_invalidation_event(
        history,
        artifact_references=(reference,),
        next_state="running",
        processing_stage="publication",
        attempt_id="ATT-000001",
        reason_code="source_out_of_scope",
        timestamp="2026-07-25T10:03:00Z",
    )
    return create_processing_run_history(
        manifest=history.manifest,
        events=history.events + (invalidated,),
    )


def decision(
    disposition: str,
    *,
    decision_id: str = "PD-000001",
    source_id: str = "SRC-000001",
    project_id: str = PROJECT_ID,
    source_sha256: str = SHA_A,
    supersedes: str | None = None,
):
    return create_processing_decision(
        project_id=project_id,
        processing_decision_id=decision_id,
        decision_type="source_disposition",
        source_id=source_id,
        source_sha256=source_sha256,
        disposition=disposition,
        reviewer_identity="reviewer@example.com",
        rationale="Explicit source treatment.",
        timestamp=(
            "2026-07-25T12:00:00Z"
            if decision_id == "PD-000001"
            else "2026-07-25T13:00:00Z"
        ),
        supersedes_processing_decision_id=supersedes,
    )


def processing_scan(*histories, decisions=(), issues=()):
    return ProcessingScanResult(
        run_histories=tuple(histories),
        decisions=tuple(decisions),
        issues=tuple(issues),
    )


def project_summary(sources, scan=None):
    return derive_project_processing_summary(
        PROJECT_ID,
        sources,
        scan or ProcessingScanResult(),
    )


def test_empty_project_is_empty() -> None:
    summary = project_summary(SourceScanResult())
    assert summary.project_state == "empty"
    assert summary.total_sources == 0
    assert summary.source_summaries == ()


def test_engineering_source_defaults_to_in_scope() -> None:
    summary = project_summary(source_scan(source()))
    item = summary.source_summaries[0]
    assert item.processing_disposition == "in_scope"
    assert item.current_processing_run_id is None
    assert summary.project_state == "not_started"


def test_context_source_defaults_to_context_only() -> None:
    summary = project_summary(
        source_scan(source(role=CONTEXT_ONLY_SOURCE_ROLE))
    )
    assert summary.context_only_sources == 1
    assert summary.source_summaries[0].processing_disposition == "context_only"


def test_in_scope_decision_cannot_elevate_registered_context_role() -> None:
    summary = project_summary(
        source_scan(source(role=CONTEXT_ONLY_SOURCE_ROLE)),
        processing_scan(decisions=(decision("in_scope"),)),
    )
    assert summary.source_summaries[0].processing_disposition == "context_only"


def test_out_of_scope_source_does_not_prevent_processed_state() -> None:
    summary = project_summary(
        source_scan(source()),
        processing_scan(decisions=(decision("out_of_scope"),)),
    )
    assert summary.project_state == "processed"
    assert summary.out_of_scope_sources == 1
    assert summary.not_started_sources == 0


def test_created_run_is_counted_as_not_started() -> None:
    summary = project_summary(
        source_scan(source()),
        processing_scan(initial_history()),
    )
    assert summary.not_started_sources == 1
    assert summary.project_state == "not_started"


def test_running_run_makes_project_in_progress() -> None:
    summary = project_summary(
        source_scan(source()),
        processing_scan(history_in_state("running")),
    )
    item = summary.source_summaries[0]
    assert item.run_state == "running"
    assert item.processing_stage == "semantic_extraction"
    assert item.latest_attempt_id == "ATT-000001"
    assert summary.project_state == "in_progress"


def test_awaiting_review_has_precedence_over_running() -> None:
    second_source = source("SRC-000002", sha256=SHA_B)
    second_manifest = manifest(
        "RUN-000002",
        source_id="SRC-000002",
        source_sha256=SHA_B,
    )
    summary = project_summary(
        source_scan(source(), second_source),
        processing_scan(
            history_in_state("running"),
            history_in_state("awaiting_review", run_manifest=second_manifest),
        ),
    )
    assert summary.awaiting_review_sources == 1
    assert summary.running_sources == 1
    assert summary.project_state == "awaiting_review"


def test_blocked_run_creates_attention_and_reason_code() -> None:
    summary = project_summary(
        source_scan(source()),
        processing_scan(
            history_in_state("blocked", reason_code="missing_projection")
        ),
    )
    item = summary.source_summaries[0]
    assert item.blocking_issue_codes == ("missing_projection",)
    assert summary.blocked_sources == 1
    assert summary.project_state == "attention_required"


def test_failed_run_creates_failure_code_and_attention() -> None:
    summary = project_summary(
        source_scan(source()),
        processing_scan(
            history_in_state("failed", reason_code="provider_failure")
        ),
    )
    item = summary.source_summaries[0]
    assert item.failure_issue_codes == ("provider_failure",)
    assert summary.failed_sources == 1
    assert summary.project_state == "attention_required"


def test_completed_run_makes_project_processed() -> None:
    summary = project_summary(
        source_scan(source()),
        processing_scan(history_in_state("completed")),
    )
    assert summary.completed_sources == 1
    assert summary.project_state == "processed"


def test_completed_and_unstarted_sources_are_partially_processed() -> None:
    summary = project_summary(
        source_scan(source(), source("SRC-000002", sha256=SHA_B)),
        processing_scan(history_in_state("completed")),
    )
    assert summary.completed_sources == 1
    assert summary.not_started_sources == 1
    assert summary.project_state == "partially_processed"


def test_running_has_precedence_over_partial_completion() -> None:
    second_manifest = manifest(
        "RUN-000002",
        source_id="SRC-000002",
        source_sha256=SHA_B,
    )
    summary = project_summary(
        source_scan(source(), source("SRC-000002", sha256=SHA_B)),
        processing_scan(
            history_in_state("completed"),
            history_in_state("running", run_manifest=second_manifest),
        ),
    )
    assert summary.project_state == "in_progress"


def test_attention_has_precedence_over_awaiting_review() -> None:
    second_manifest = manifest(
        "RUN-000002",
        source_id="SRC-000002",
        source_sha256=SHA_B,
    )
    summary = project_summary(
        source_scan(source(), source("SRC-000002", sha256=SHA_B)),
        processing_scan(
            history_in_state("failed"),
            history_in_state("awaiting_review", run_manifest=second_manifest),
        ),
    )
    assert summary.project_state == "attention_required"


def test_project_level_blocking_issue_requires_attention() -> None:
    issue = ProcessingIssue(
        project_id=PROJECT_ID,
        code="recovery_required",
        message="Recovery is required.",
        issue_level="blocking",
    )
    summary = project_summary(
        source_scan(source()),
        processing_scan(issues=(issue,)),
    )
    assert summary.project_state == "attention_required"
    assert summary.issues == (issue,)


def test_warning_does_not_change_not_started_state() -> None:
    issue = ProcessingIssue(
        project_id=PROJECT_ID,
        code="diagnostic_warning",
        message="Non-blocking diagnostic.",
        issue_level="warning",
    )
    summary = project_summary(
        source_scan(source()),
        processing_scan(issues=(issue,)),
    )
    assert summary.project_state == "not_started"


def test_source_issue_is_converted_to_blocking_processing_issue() -> None:
    issue = SourceIssue(
        project_id=PROJECT_ID,
        source_id="SRC-000001",
        code="invalid_source_content",
        message="Source content is invalid.",
        path=Path("data/projects/318604/sources/SRC-000001"),
    )
    summary = project_summary(
        source_scan(source(), issues=(issue,))
    )
    assert summary.source_summaries[0].blocking_issue_codes == (
        "invalid_source_content",
    )
    assert summary.project_state == "attention_required"


def test_successor_is_current_and_predecessor_is_listed() -> None:
    predecessor = history_in_state("completed")
    successor_manifest = manifest(
        "RUN-000002",
        configuration="e" * 64,
        supersedes_run_id="RUN-000001",
        timestamp="2026-07-25T11:00:00Z",
    )
    superseded_event = create_run_superseded_event(
        predecessor,
        successor_manifest,
        reason_code="binding_changed",
        timestamp="2026-07-25T11:00:00Z",
    )
    predecessor = create_processing_run_history(
        manifest=predecessor.manifest,
        events=predecessor.events + (superseded_event,),
    )
    successor = initial_history(successor_manifest)
    summary = project_summary(
        source_scan(source()),
        processing_scan(predecessor, successor),
    )
    item = summary.source_summaries[0]
    assert item.current_processing_run_id == "RUN-000002"
    assert item.superseded_run_ids == ("RUN-000001",)
    assert summary.superseded_runs == 1


def test_multiple_current_runs_are_blocking_and_current_is_omitted() -> None:
    second = initial_history(
        manifest("RUN-000002", configuration="e" * 64)
    )
    summary = project_summary(
        source_scan(source()),
        processing_scan(initial_history(), second),
    )
    item = summary.source_summaries[0]
    assert item.current_processing_run_id is None
    assert "multiple_current_processing_runs" in item.blocking_issue_codes
    assert summary.project_state == "attention_required"


def test_invalidated_artifacts_are_counted_per_source() -> None:
    summary = project_summary(
        source_scan(source()),
        processing_scan(history_with_invalidated_artifact()),
    )
    assert summary.invalidated_artifacts == 1
    assert summary.source_summaries[0].invalidated_artifact_count == 1


def test_invalidated_counts_remain_source_bound_with_same_local_id() -> None:
    first = history_in_state("running")
    first_artifact = artifact(
        "IU-SHARED",
        fingerprint="d" * 64,
        path=(
            f"data/projects/{PROJECT_ID}/runs/RUN-000001/"
            "artifacts/IU-SHARED.json"
        ),
    )
    first = append_event(
        first,
        next_state="running",
        event_type="artifact_published",
        reason_code="artifact_published",
        timestamp="2026-07-25T10:02:00Z",
        processing_stage="publication",
        attempt_id="ATT-000001",
        artifact_references=(first_artifact,),
    )
    invalidated = create_artifact_invalidation_event(
        first,
        artifact_references=(first_artifact,),
        next_state="running",
        processing_stage="publication",
        attempt_id="ATT-000001",
        reason_code="source_out_of_scope",
        timestamp="2026-07-25T10:03:00Z",
    )
    first = create_processing_run_history(
        manifest=first.manifest,
        events=first.events + (invalidated,),
    )

    second_manifest = manifest(
        "RUN-000002",
        source_id="SRC-000002",
        source_sha256=SHA_B,
    )
    second = history_in_state("running", run_manifest=second_manifest)
    second_artifact = artifact(
        "IU-SHARED",
        fingerprint="e" * 64,
        path=(
            f"data/projects/{PROJECT_ID}/runs/RUN-000002/"
            "artifacts/IU-SHARED.json"
        ),
    )
    second = append_event(
        second,
        next_state="running",
        event_type="artifact_published",
        reason_code="artifact_published",
        timestamp="2026-07-25T10:02:30Z",
        processing_stage="publication",
        attempt_id="ATT-000001",
        artifact_references=(second_artifact,),
    )

    summary = project_summary(
        source_scan(source(), source("SRC-000002", sha256=SHA_B)),
        processing_scan(first, second),
    )
    by_source = {
        item.source_id: item
        for item in summary.source_summaries
    }

    assert summary.invalidated_artifacts == 1
    assert by_source["SRC-000001"].invalidated_artifact_count == 1
    assert by_source["SRC-000002"].invalidated_artifact_count == 0


def test_disposition_change_requires_active_artifact_invalidation() -> None:
    history = history_in_state("running")
    reference = artifact()
    history = append_event(
        history,
        next_state="running",
        event_type="artifact_published",
        reason_code="artifact_published",
        timestamp="2026-07-25T10:02:00Z",
        processing_stage="publication",
        attempt_id="ATT-000001",
        artifact_references=(reference,),
    )
    summary = project_summary(
        source_scan(source()),
        processing_scan(
            history,
            decisions=(decision("context_only"),),
        ),
    )
    item = summary.source_summaries[0]
    assert "source_disposition_invalidation_required" in (
        item.blocking_issue_codes
    )
    assert summary.project_state == "attention_required"


def test_completed_invalidation_removes_invalidation_required_issue() -> None:
    summary = project_summary(
        source_scan(source()),
        processing_scan(
            history_with_invalidated_artifact(),
            decisions=(decision("out_of_scope"),),
        ),
    )
    assert "source_disposition_invalidation_required" not in (
        summary.source_summaries[0].blocking_issue_codes
    )


def test_context_only_decision_blocks_mismatched_engineering_run() -> None:
    summary = project_summary(
        source_scan(source()),
        processing_scan(
            history_in_state("completed"),
            decisions=(decision("context_only"),),
        ),
    )
    assert "processing_disposition_run_mismatch" in (
        summary.source_summaries[0].blocking_issue_codes
    )


def test_context_only_profile_matches_effective_disposition() -> None:
    context_source = source(role=CONTEXT_ONLY_SOURCE_ROLE)
    context_manifest = manifest(
        role=CONTEXT_ONLY_SOURCE_ROLE,
        workflow_profile="context_only_processing",
    )
    summary = project_summary(
        source_scan(context_source),
        processing_scan(history_in_state("completed", run_manifest=context_manifest)),
    )
    assert summary.project_state == "processed"
    assert summary.source_summaries[0].blocking_issue_codes == ()


def test_latest_decision_in_chain_controls_disposition() -> None:
    first = decision("context_only")
    second = decision(
        "out_of_scope",
        decision_id="PD-000002",
        supersedes="PD-000001",
    )
    summary = project_summary(
        source_scan(source()),
        processing_scan(decisions=(second, first)),
    )
    assert summary.source_summaries[0].processing_disposition == "out_of_scope"


def test_source_summaries_are_sorted_by_source_id() -> None:
    summaries = derive_source_processing_summaries(
        PROJECT_ID,
        source_scan(
            source("SRC-000002", sha256=SHA_B),
            source("SRC-000001"),
        ),
        ProcessingScanResult(),
    )
    assert tuple(item.source_id for item in summaries) == (
        "SRC-000001",
        "SRC-000002",
    )


def test_processing_issue_bound_to_run_is_associated_with_source() -> None:
    issue = ProcessingIssue(
        project_id=PROJECT_ID,
        code="incomplete_publication",
        message="Publication is incomplete.",
        issue_level="blocking",
        processing_run_id="RUN-000001",
    )
    summary = project_summary(
        source_scan(source()),
        processing_scan(initial_history(), issues=(issue,)),
    )
    assert summary.source_summaries[0].blocking_issue_codes == (
        "incomplete_publication",
    )


def test_no_sources_with_blocking_processing_issue_requires_attention() -> None:
    issue = ProcessingIssue(
        project_id=PROJECT_ID,
        code="orphan_processing_record",
        message="Orphan record detected.",
        issue_level="blocking",
    )
    summary = project_summary(
        SourceScanResult(),
        processing_scan(issues=(issue,)),
    )
    assert summary.project_state == "attention_required"


def test_unknown_run_source_is_rejected() -> None:
    with pytest.raises(ProcessingReferenceError):
        project_summary(
            source_scan(source()),
            processing_scan(
                initial_history(manifest(source_id="SRC-000002"))
            ),
        )


def test_run_source_fingerprint_mismatch_is_rejected() -> None:
    with pytest.raises(ProcessingReferenceError):
        project_summary(
            source_scan(source()),
            processing_scan(
                initial_history(manifest(source_sha256=SHA_B))
            ),
        )


def test_unknown_decision_source_is_rejected() -> None:
    with pytest.raises(ProcessingReferenceError):
        project_summary(
            source_scan(source()),
            processing_scan(
                decisions=(decision("out_of_scope", source_id="SRC-000002"),)
            ),
        )


def test_decision_source_fingerprint_mismatch_is_rejected() -> None:
    with pytest.raises(ProcessingReferenceError):
        project_summary(
            source_scan(source()),
            processing_scan(
                decisions=(decision("out_of_scope", source_sha256=SHA_B),)
            ),
        )


def test_duplicate_source_identity_is_rejected() -> None:
    with pytest.raises(ProcessingIntegrityError):
        project_summary(source_scan(source(), source()))


def test_mixed_project_sources_are_rejected() -> None:
    with pytest.raises(ProcessingValidationError):
        project_summary(
            source_scan(source(project_id=OTHER_PROJECT_ID))
        )


def test_mixed_project_processing_issue_is_rejected() -> None:
    issue = ProcessingIssue(
        project_id=OTHER_PROJECT_ID,
        code="wrong_project",
        message="Wrong project.",
        issue_level="blocking",
    )
    with pytest.raises(ProcessingReferenceError):
        project_summary(
            source_scan(source()),
            processing_scan(issues=(issue,)),
        )


def test_invalid_project_id_is_rejected() -> None:
    with pytest.raises(ProcessingValidationError):
        derive_project_processing_summary(
            "42",
            SourceScanResult(),
            ProcessingScanResult(),
        )


@pytest.mark.parametrize(
    ("source_value", "processing_value"),
    [
        ((), ProcessingScanResult()),
        (SourceScanResult(), ()),
    ],
)
def test_scan_inputs_require_explicit_result_types(
    source_value,
    processing_value,
) -> None:
    with pytest.raises(ProcessingValidationError):
        derive_project_processing_summary(
            PROJECT_ID,
            source_value,
            processing_value,
        )


def test_same_local_artifact_identity_across_sources_is_not_blocking() -> None:
    first = history_in_state("running")
    first_artifact = artifact(
        "IU-SHARED",
        fingerprint="d" * 64,
        path=(
            f"data/projects/{PROJECT_ID}/runs/RUN-000001/"
            "artifacts/IU-SHARED.json"
        ),
    )
    first = append_event(
        first,
        next_state="running",
        event_type="artifact_published",
        reason_code="artifact_published",
        timestamp="2026-07-25T10:02:00Z",
        processing_stage="publication",
        attempt_id="ATT-000001",
        artifact_references=(first_artifact,),
    )

    second_manifest = manifest(
        "RUN-000002",
        source_id="SRC-000002",
        source_sha256=SHA_B,
    )
    second = history_in_state("running", run_manifest=second_manifest)
    second_artifact = artifact(
        "IU-SHARED",
        fingerprint="e" * 64,
        path=(
            f"data/projects/{PROJECT_ID}/runs/RUN-000002/"
            "artifacts/IU-SHARED.json"
        ),
    )
    second = append_event(
        second,
        next_state="running",
        event_type="artifact_published",
        reason_code="artifact_published",
        timestamp="2026-07-25T10:03:00Z",
        processing_stage="publication",
        attempt_id="ATT-000001",
        artifact_references=(second_artifact,),
    )

    summary = project_summary(
        source_scan(source(), source("SRC-000002", sha256=SHA_B)),
        processing_scan(first, second),
    )

    assert summary.project_state == "in_progress"
    assert not any(
        issue.code == "artifact_cross_source_reference"
        for issue in summary.issues
    )
    assert not any(
        issue.code == "artifact_lifecycle_derivation_failed"
        for issue in summary.issues
    )

def test_summary_counts_are_internally_consistent() -> None:
    second_manifest = manifest(
        "RUN-000002",
        source_id="SRC-000002",
        source_sha256=SHA_B,
    )
    summary = project_summary(
        source_scan(
            source(),
            source("SRC-000002", sha256=SHA_B),
            source("SRC-000003", sha256="f" * 64),
        ),
        processing_scan(
            history_in_state("completed"),
            history_in_state("running", run_manifest=second_manifest),
            decisions=(
                decision(
                    "out_of_scope",
                    source_id="SRC-000003",
                    source_sha256="f" * 64,
                ),
            ),
        ),
    )
    assert summary.total_sources == 3
    assert summary.in_scope_sources == 2
    assert summary.out_of_scope_sources == 1
    assert summary.completed_sources == 1
    assert summary.running_sources == 1
    assert summary.project_state == "in_progress"