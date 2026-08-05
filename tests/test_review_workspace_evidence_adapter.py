"""Tests for exact P9 Review Evidence selection."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from modules.project_processing import (
    create_processing_artifact_reference,
    create_processing_event,
    create_processing_run_history,
    create_processing_run_manifest,
    create_semantic_reference_version,
)
from modules.review_workspace.errors import (
    ReviewIntegrityError,
    ReviewReferenceError,
)
from modules.review_workspace.evidence_adapter import (
    select_p9_review_evidence_set,
)


PROJECT_ID = "123456"
OTHER_PROJECT_ID = "654321"
SOURCE_ID = "SRC-000001"
RUN_ID = "RUN-000001"
ATTEMPT_ID = "ATT-000001"

SOURCE_SHA256 = "a" * 64
CONFIGURATION_FINGERPRINT = "b" * 64


_ARTIFACT_PREFIXES = {
    "agent_outputs": "AGOUT",
    "consensus_reports": "CONS",
    "review_reports": "REVIEW",
    "run_summaries": "SUMMARY",
}


def _create_reference(
    repository_root: Path,
    artifact_type: str,
    index: int,
    content: bytes,
    *,
    path_project_id: str = PROJECT_ID,
):
    filename = f"{artifact_type}-{index:04d}.dat"
    relative_path = (
        Path("data")
        / "projects"
        / path_project_id
        / "runs"
        / RUN_ID
        / "artifacts"
        / artifact_type
        / "agentic_ingestion"
        / ATTEMPT_ID
        / filename
    )
    target = repository_root / relative_path
    target.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    target.write_bytes(content)

    prefix = _ARTIFACT_PREFIXES.get(
        artifact_type,
        "OTHER",
    )

    return create_processing_artifact_reference(
        artifact_type=artifact_type,
        artifact_id=(
            f"{prefix}-{ATTEMPT_ID}-{index:04d}"
        ),
        content_fingerprint=hashlib.sha256(
            content
        ).hexdigest(),
        repository_relative_path=(
            relative_path.as_posix()
        ),
    )


def _complete_references(
    repository_root: Path,
):
    return (
        _create_reference(
            repository_root,
            "agent_outputs",
            1,
            b'{"agent":"one"}',
        ),
        _create_reference(
            repository_root,
            "agent_outputs",
            2,
            b'{"agent":"two"}',
        ),
        _create_reference(
            repository_root,
            "consensus_reports",
            1,
            b'{"consensus":"review"}',
        ),
        _create_reference(
            repository_root,
            "review_reports",
            1,
            b"# Ingestion Review\n",
        ),
        _create_reference(
            repository_root,
            "run_summaries",
            1,
            b'{"run":"summary"}',
        ),
        _create_reference(
            repository_root,
            "run_summaries",
            2,
            b"# Run Summary\n",
        ),
    )


def _history(
    references,
    *,
    awaiting_review: bool = True,
):
    semantic_reference = (
        create_semantic_reference_version(
            reference_system_id="BFO_2020",
            reference_version="1.0.0",
        )
    )

    manifest = create_processing_run_manifest(
        project_id=PROJECT_ID,
        processing_run_id=RUN_ID,
        source_id=SOURCE_ID,
        source_sha256=SOURCE_SHA256,
        source_role_snapshot="engineering_source",
        workflow_profile=(
            "engineering_source_processing"
        ),
        configuration_fingerprint=(
            CONFIGURATION_FINGERPRINT
        ),
        framework_template_id=(
            "TURING_RFLP_FRAMEWORK"
        ),
        framework_template_version="1.0.0",
        semantic_reference_versions=(
            semantic_reference,
        ),
        timestamp="2026-08-04T15:00:00Z",
    )

    created = create_processing_event(
        project_id=PROJECT_ID,
        processing_run_id=RUN_ID,
        event_id="EVT-000001",
        event_sequence=1,
        previous_state=None,
        next_state="created",
        processing_stage=None,
        event_type="run_created",
        attempt_id=None,
        reason_code="run_created",
        artifact_references=(),
        timestamp="2026-08-04T15:00:01Z",
        previous_event_fingerprint=None,
    )

    started = create_processing_event(
        project_id=PROJECT_ID,
        processing_run_id=RUN_ID,
        event_id="EVT-000002",
        event_sequence=2,
        previous_state="created",
        next_state="running",
        processing_stage="agentic_ingestion",
        event_type="stage_started",
        attempt_id=ATTEMPT_ID,
        reason_code="agentic_ingestion_started",
        artifact_references=(),
        timestamp="2026-08-04T15:00:02Z",
        previous_event_fingerprint=(
            created.event_fingerprint
        ),
    )

    published = create_processing_event(
        project_id=PROJECT_ID,
        processing_run_id=RUN_ID,
        event_id="EVT-000003",
        event_sequence=3,
        previous_state="running",
        next_state="running",
        processing_stage="agentic_ingestion",
        event_type="artifact_published",
        attempt_id=ATTEMPT_ID,
        reason_code=(
            "agentic_ingestion_artifacts_published"
        ),
        artifact_references=tuple(references),
        timestamp="2026-08-04T15:00:03Z",
        previous_event_fingerprint=(
            started.event_fingerprint
        ),
    )

    events = [
        created,
        started,
        published,
    ]

    if awaiting_review:
        requested = create_processing_event(
            project_id=PROJECT_ID,
            processing_run_id=RUN_ID,
            event_id="EVT-000004",
            event_sequence=4,
            previous_state="running",
            next_state="awaiting_review",
            processing_stage="agentic_ingestion",
            event_type="review_requested",
            attempt_id=ATTEMPT_ID,
            reason_code=(
                "agentic_ingestion_review_requested"
            ),
            artifact_references=(),
            timestamp="2026-08-04T15:00:04Z",
            previous_event_fingerprint=(
                published.event_fingerprint
            ),
        )
        events.append(requested)

    return create_processing_run_history(
        manifest=manifest,
        events=tuple(events),
    )


def test_selects_complete_active_p9_evidence(
    tmp_path: Path,
) -> None:
    repository_root = tmp_path / "repository"
    repository_root.mkdir()

    history = _history(
        _complete_references(repository_root)
    )

    selected = select_p9_review_evidence_set(
        history,
        repository_root=repository_root,
    )

    assert selected.project_id == PROJECT_ID
    assert selected.source_id == SOURCE_ID
    assert selected.processing_run_id == RUN_ID
    assert selected.attempt_id == ATTEMPT_ID

    assert (
        selected.primary_review_artifact_reference
        .artifact_type
        == "review_reports"
    )
    assert len(selected.agent_output_references) == 2
    assert len(
        selected.consensus_report_references
    ) == 1
    assert len(selected.run_summary_references) == 2
    assert len(
        selected.supporting_artifact_references
    ) == 5

    assert (
        selected.framework_template.template_id
        == "TURING_RFLP_FRAMEWORK"
    )
    assert (
        selected.framework_template.template_version
        == "1.0.0"
    )


def test_rejects_run_not_awaiting_review(
    tmp_path: Path,
) -> None:
    repository_root = tmp_path / "repository"
    repository_root.mkdir()

    history = _history(
        _complete_references(repository_root),
        awaiting_review=False,
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="currently awaiting review",
    ):
        select_p9_review_evidence_set(
            history,
            repository_root=repository_root,
        )


@pytest.mark.parametrize(
    ("missing_type", "message"),
    (
        (
            "agent_outputs",
            "at least one Agent Output",
        ),
        (
            "consensus_reports",
            "at least one Consensus Report",
        ),
        (
            "review_reports",
            "exactly one Review Report",
        ),
        (
            "run_summaries",
            "at least one Run Summary",
        ),
    ),
)
def test_rejects_incomplete_p9_evidence(
    tmp_path: Path,
    missing_type: str,
    message: str,
) -> None:
    repository_root = tmp_path / "repository"
    repository_root.mkdir()

    references = tuple(
        reference
        for reference in _complete_references(
            repository_root
        )
        if reference.artifact_type != missing_type
    )
    history = _history(references)

    with pytest.raises(
        ReviewIntegrityError,
        match=message,
    ):
        select_p9_review_evidence_set(
            history,
            repository_root=repository_root,
        )


def test_rejects_multiple_review_reports(
    tmp_path: Path,
) -> None:
    repository_root = tmp_path / "repository"
    repository_root.mkdir()

    references = (
        _complete_references(repository_root)
        + (
            _create_reference(
                repository_root,
                "review_reports",
                2,
                b"# Second Review\n",
            ),
        )
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="exactly one Review Report",
    ):
        select_p9_review_evidence_set(
            _history(references),
            repository_root=repository_root,
        )


def test_rejects_unsupported_artifact_type(
    tmp_path: Path,
) -> None:
    repository_root = tmp_path / "repository"
    repository_root.mkdir()

    references = (
        _complete_references(repository_root)
        + (
            _create_reference(
                repository_root,
                "other_evidence",
                1,
                b"other",
            ),
        )
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="unsupported artifact type",
    ):
        select_p9_review_evidence_set(
            _history(references),
            repository_root=repository_root,
        )


def test_rejects_cross_project_artifact_path(
    tmp_path: Path,
) -> None:
    repository_root = tmp_path / "repository"
    repository_root.mkdir()

    references = list(
        _complete_references(repository_root)
    )
    references[0] = _create_reference(
        repository_root,
        "agent_outputs",
        3,
        b'{"agent":"wrong-project"}',
        path_project_id=OTHER_PROJECT_ID,
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="does not match its Project",
    ):
        select_p9_review_evidence_set(
            _history(tuple(references)),
            repository_root=repository_root,
        )


def test_rejects_missing_artifact_file(
    tmp_path: Path,
) -> None:
    repository_root = tmp_path / "repository"
    repository_root.mkdir()

    references = _complete_references(
        repository_root
    )
    review_reference = next(
        reference
        for reference in references
        if reference.artifact_type
        == "review_reports"
    )

    (
        repository_root
        / review_reference.repository_relative_path
    ).unlink()

    with pytest.raises(
        ReviewReferenceError,
        match="does not exist",
    ):
        select_p9_review_evidence_set(
            _history(references),
            repository_root=repository_root,
        )


def test_rejects_artifact_fingerprint_mismatch(
    tmp_path: Path,
) -> None:
    repository_root = tmp_path / "repository"
    repository_root.mkdir()

    references = _complete_references(
        repository_root
    )
    agent_reference = next(
        reference
        for reference in references
        if reference.artifact_type
        == "agent_outputs"
    )

    target = (
        repository_root
        / agent_reference.repository_relative_path
    )
    target.write_bytes(b"changed after publication")

    with pytest.raises(
        ReviewIntegrityError,
        match="fingerprint does not match",
    ):
        select_p9_review_evidence_set(
            _history(references),
            repository_root=repository_root,
        )


def test_rejects_symbolic_link_artifact(
    tmp_path: Path,
) -> None:
    repository_root = tmp_path / "repository"
    repository_root.mkdir()

    references = _complete_references(
        repository_root
    )
    summary_reference = next(
        reference
        for reference in references
        if reference.artifact_type
        == "run_summaries"
    )

    target = (
        repository_root
        / summary_reference.repository_relative_path
    )
    outside = tmp_path / "outside-summary"
    outside.write_bytes(b"outside")

    target.unlink()

    try:
        target.symlink_to(outside)
    except OSError:
        pytest.skip(
            "Symbolic links are unavailable "
            "on this platform."
        )

    with pytest.raises(
        ReviewReferenceError,
        match="symbolic-link paths",
    ):
        select_p9_review_evidence_set(
            _history(references),
            repository_root=repository_root,
        )
