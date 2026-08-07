"""Tests for the project-local Approved Input repository."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from pathlib import Path

import pytest

from modules.approved_input.errors import (
    ApprovedInputIntegrityError,
    ApprovedInputNotFoundError,
    ApprovedInputPersistenceError,
    ApprovedInputRecoveryRequiredError,
    UnsafeApprovedInputPathError,
)
from modules.approved_input.manifest import (
    approved_input_manifest_to_json,
    create_approved_input_manifest,
)
from modules.approved_input.paths import (
    approved_input_events_path,
    approved_input_manifest_path,
    approved_input_manifests_path,
    approved_inputs_path,
)
from modules.approved_input.repository import ApprovedInputRepository
from modules.approved_input.types import (
    APPROVED_INPUT_REPOSITORY_ISSUE_LEVELS,
    ApprovedInputCanonicalContent,
    ApprovedInputRepositoryIssue,
    ApprovedInputRepositoryScanResult,
)
from modules.project_processing.types import ProcessingArtifactReference
from modules.project_workspace import ProjectWorkspace


PROJECT_ID = "318604"
SHA_A = "a" * 64
SHA_B = "b" * 64
SHA_C = "c" * 64
SHA_D = "d" * 64
SHA_E = "e" * 64


def _clock() -> datetime:
    return datetime(
        2026,
        8,
        7,
        9,
        0,
        tzinfo=timezone.utc,
    )


def _create_project(
    root: Path,
    project_id: str = PROJECT_ID,
    display_name: str = "Approved Input Repository Test",
) -> None:
    workspace = ProjectWorkspace(
        root=root,
        id_generator=lambda: project_id,
        clock=_clock,
    )
    workspace.create_project(display_name)


def _artifact_reference(
    project_id: str,
) -> ProcessingArtifactReference:
    return ProcessingArtifactReference(
        artifact_type="information_unit",
        artifact_id="IU-000001",
        content_fingerprint=SHA_A,
        repository_relative_path=(
            f"data/projects/{project_id}/semantics/"
            "information_units/IU-000001.json"
        ),
    )


def _manifest(
    *,
    project_id: str = PROJECT_ID,
    approved_input_id: str = "AIN-000001",
):
    return create_approved_input_manifest(
        project_id=project_id,
        approved_input_id=approved_input_id,
        approved_input_kind="element_statement",
        canonical_content=ApprovedInputCanonicalContent(
            title="System shall preserve traceability",
            primary_text=(
                "The system shall preserve exact review traceability."
            ),
            description="Reviewed engineering statement.",
            information_type="requirement",
            modality="shall",
            epistemic_status="reviewed",
        ),
        selected_classification="System Requirement",
        selected_framework_assignment="System Requirements",
        selected_terminology_assignment="requirement",
        selected_source_assignments=("SRC-000001",),
        selected_relationship_representation=None,
        stable_subject_key="requirement.traceability",
        review_document_id="RVD-000001",
        review_document_version_id="RVV-000001",
        review_revision_id="RVR-000001",
        review_item_id="RIT-000001",
        review_item_kind="element",
        review_item_fingerprint=SHA_A,
        finalized_artifact_set_fingerprint=SHA_B,
        finalization_decision_id="HRD-000001",
        finalization_decision_fingerprint=SHA_C,
        finalization_validation_fingerprint=SHA_D,
        source_id="SRC-000001",
        source_sha256=SHA_E,
        processing_run_id="RUN-000001",
        attempt_id="ATT-000001",
        primary_artifact_reference=_artifact_reference(project_id),
        supporting_artifact_references=(),
        proposal_references=("proposal-a",),
        created_at="2026-08-07T09:00:00Z",
    )


@pytest.fixture
def repository(
    tmp_path: Path,
) -> tuple[ApprovedInputRepository, Path]:
    root = tmp_path / "projects"
    _create_project(root)
    return ApprovedInputRepository(root=root), root

def test_scan_empty_project_is_clean(repository) -> None:
    store, _ = repository

    result = store.scan_project(PROJECT_ID)

    assert result.manifests == ()
    assert result.issues == ()


def test_scan_returns_valid_manifests(repository) -> None:
    store, _ = repository
    manifest = store.persist_manifest(_manifest())

    result = store.scan_project(PROJECT_ID)

    assert result.manifests == (manifest,)
    assert result.issues == ()


def test_scan_reports_interrupted_manifest_persistence(repository) -> None:
    store, root = repository
    store.persist_manifest(_manifest())

    manifests_root = approved_input_manifests_path(
        root,
        PROJECT_ID,
    )
    temporary_path = manifests_root / ".AIN-000002.json.tmp"
    temporary_path.write_text(
        approved_input_manifest_to_json(
            _manifest(approved_input_id="AIN-000002")
        ),
        encoding="utf-8",
    )

    result = store.scan_project(PROJECT_ID)

    assert tuple(issue.code for issue in result.issues) == (
        "approved_input_persistence_interrupted",
    )
    assert result.issues[0].approved_input_id == "AIN-000002"

    with pytest.raises(ApprovedInputRecoveryRequiredError):
        store.next_approved_input_id(PROJECT_ID)


def test_scan_reports_incomplete_repository(repository) -> None:
    store, root = repository
    repository_root = approved_inputs_path(
        root,
        PROJECT_ID,
    )
    repository_root.mkdir()

    result = store.scan_project(PROJECT_ID)

    assert [issue.code for issue in result.issues] == [
        "approved_input_repository_incomplete",
        "approved_input_repository_incomplete",
    ]


def test_scan_reports_unexpected_repository_entry(repository) -> None:
    store, root = repository
    store.persist_manifest(_manifest())

    unexpected = approved_inputs_path(
        root,
        PROJECT_ID,
    ) / "current_state.json"
    unexpected.write_text("{}\n", encoding="utf-8")

    result = store.scan_project(PROJECT_ID)

    assert "unexpected_approved_input_repository_entry" in {
        issue.code for issue in result.issues
    }

    with pytest.raises(ApprovedInputIntegrityError):
        store.list_manifests(PROJECT_ID)


def test_scan_reports_invalid_manifest_content(repository) -> None:
    store, root = repository
    store.persist_manifest(_manifest())

    path = approved_input_manifest_path(
        root,
        PROJECT_ID,
        "AIN-000001",
    )
    path.write_text("{}\n", encoding="utf-8")

    result = store.scan_project(PROJECT_ID)

    assert tuple(issue.code for issue in result.issues) == (
        "invalid_approved_input_manifest",
    )
    assert result.manifests == ()


def test_scan_reports_unexpected_manifest_entry(repository) -> None:
    store, root = repository
    store.persist_manifest(_manifest())

    unexpected = approved_input_manifests_path(
        root,
        PROJECT_ID,
    ) / "current.json"
    unexpected.write_text("{}\n", encoding="utf-8")

    result = store.scan_project(PROJECT_ID)

    assert "unexpected_approved_input_manifest_entry" in {
        issue.code for issue in result.issues
    }


def test_scan_reports_unexpected_event_root_entry(repository) -> None:
    store, root = repository
    store.persist_manifest(_manifest())

    unexpected = approved_input_events_path(
        root,
        PROJECT_ID,
    ) / "current.json"
    unexpected.write_text("{}\n", encoding="utf-8")

    result = store.scan_project(PROJECT_ID)

    assert "unexpected_approved_input_event_entry" in {
        issue.code for issue in result.issues
    }
