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
    UnsafeApprovedInputPathError,
)
from modules.approved_input.manifest import (
    create_approved_input_manifest,
)
from modules.approved_input.paths import (
    approved_input_events_path,
    approved_input_manifest_path,
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


def test_repository_scan_types_are_frozen_and_slotted() -> None:
    issue = ApprovedInputRepositoryIssue(
        project_id=PROJECT_ID,
        code="example",
        message="Example issue.",
        issue_level="blocking",
        path=None,
        approved_input_id=None,
    )
    result = ApprovedInputRepositoryScanResult(
        issues=(issue,)
    )

    assert ApprovedInputRepositoryIssue.__dataclass_params__.frozen
    assert ApprovedInputRepositoryIssue.__slots__
    assert ApprovedInputRepositoryScanResult.__dataclass_params__.frozen
    assert ApprovedInputRepositoryScanResult.__slots__

    with pytest.raises(FrozenInstanceError):
        issue.code = "changed"

    assert APPROVED_INPUT_REPOSITORY_ISSUE_LEVELS == frozenset(
        {"warning", "blocking"}
    )
    assert result.issues == (issue,)


def test_next_approved_input_id_starts_at_one(repository) -> None:
    store, _ = repository

    assert store.next_approved_input_id(PROJECT_ID) == "AIN-000001"


def test_persist_and_load_manifest_round_trip(repository) -> None:
    store, root = repository
    manifest = _manifest()

    persisted = store.persist_manifest(manifest)

    assert persisted == manifest
    assert store.load_manifest(
        PROJECT_ID,
        "AIN-000001",
    ) == manifest

    path = approved_input_manifest_path(
        root,
        PROJECT_ID,
        "AIN-000001",
    )
    temporary_path = path.with_name(
        ".AIN-000001.json.tmp"
    )

    assert path.is_file()
    assert not temporary_path.exists()
    assert approved_input_events_path(
        root,
        PROJECT_ID,
    ).is_dir()


def test_persist_manifest_never_overwrites_existing_manifest(
    repository,
) -> None:
    store, root = repository
    manifest = _manifest()
    store.persist_manifest(manifest)

    path = approved_input_manifest_path(
        root,
        PROJECT_ID,
        "AIN-000001",
    )
    original_bytes = path.read_bytes()

    with pytest.raises(ApprovedInputPersistenceError):
        store.persist_manifest(manifest)

    assert path.read_bytes() == original_bytes


def test_next_id_uses_highest_persisted_identifier(repository) -> None:
    store, _ = repository

    store.persist_manifest(
        _manifest(approved_input_id="AIN-000001")
    )
    store.persist_manifest(
        _manifest(approved_input_id="AIN-000003")
    )

    assert store.next_approved_input_id(PROJECT_ID) == "AIN-000004"


def test_ids_are_project_isolated(repository) -> None:
    store, root = repository
    second_project_id = "318605"
    _create_project(
        root,
        second_project_id,
        "Second Approved Input Project",
    )

    store.persist_manifest(_manifest())

    assert store.next_approved_input_id(PROJECT_ID) == "AIN-000002"
    assert (
        store.next_approved_input_id(second_project_id)
        == "AIN-000001"
    )


def test_list_manifests_is_deterministic(repository) -> None:
    store, _ = repository

    store.persist_manifest(
        _manifest(approved_input_id="AIN-000002")
    )
    store.persist_manifest(
        _manifest(approved_input_id="AIN-000001")
    )

    assert tuple(
        manifest.approved_input_id
        for manifest in store.list_manifests(PROJECT_ID)
    ) == (
        "AIN-000001",
        "AIN-000002",
    )


def test_load_missing_manifest_fails_closed(repository) -> None:
    store, _ = repository

    with pytest.raises(ApprovedInputNotFoundError):
        store.load_manifest(PROJECT_ID, "AIN-000001")


def test_load_rejects_symbolic_link_manifest(repository) -> None:
    store, root = repository
    store.persist_manifest(_manifest())

    manifest_path = approved_input_manifest_path(
        root,
        PROJECT_ID,
        "AIN-000001",
    )
    target_path = manifest_path.with_name("target.json")
    manifest_path.rename(target_path)
    manifest_path.symlink_to(target_path.name)

    with pytest.raises(UnsafeApprovedInputPathError):
        store.load_manifest(PROJECT_ID, "AIN-000001")


def test_load_rejects_tampered_manifest(repository) -> None:
    store, root = repository
    store.persist_manifest(_manifest())

    path = approved_input_manifest_path(
        root,
        PROJECT_ID,
        "AIN-000001",
    )
    text = path.read_text(encoding="utf-8")
    path.write_text(
        text.replace(
            "The system shall preserve exact review traceability.",
            "Tampered reviewed content.",
        ),
        encoding="utf-8",
    )

    with pytest.raises(ApprovedInputIntegrityError):
        store.load_manifest(PROJECT_ID, "AIN-000001")
