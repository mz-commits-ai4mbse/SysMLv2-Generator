"""Tests for immutable Approved Input lifecycle event persistence."""

from pathlib import Path

import pytest

from modules.approved_input.event_manifest import (
    approved_input_event_to_json,
    create_approved_input_event,
)
from modules.approved_input.errors import (
    ApprovedInputIntegrityError,
    ApprovedInputRecoveryRequiredError,
)
from modules.approved_input.paths import (
    approved_input_event_directory_path,
    approved_input_event_path,
)

from tests.test_approved_input_repository import (
    PROJECT_ID,
    _manifest,
    repository,
)


SHA_A = "a" * 64


def _event(event_id="AIE-000001", approved_input_id="AIN-000001"):
    return create_approved_input_event(
        project_id=PROJECT_ID,
        approved_input_event_id=event_id,
        approved_input_id=approved_input_id,
        event_type="invalidated",
        reason_code="source_integrity_failure",
        rationale="Source fingerprint changed.",
        actor_identity="integrity-checker",
        successor_approved_input_id=None,
        causal_review_document_id=None,
        causal_review_document_version_id=None,
        causal_review_revision_id=None,
        causal_finalization_decision_id=None,
        causal_finalization_decision_fingerprint=None,
        occurred_at="2026-08-07T11:30:00Z",
    )


def test_event_ids_are_project_wide_and_sequential(repository) -> None:
    store, _ = repository
    store.persist_manifest(_manifest(approved_input_id="AIN-000001"))
    store.persist_manifest(_manifest(approved_input_id="AIN-000002"))

    assert store.next_approved_input_event_id(PROJECT_ID) == "AIE-000001"
    store.persist_event(_event())
    assert store.next_approved_input_event_id(PROJECT_ID) == "AIE-000002"


def test_persist_load_and_list_event_round_trip(repository) -> None:
    store, root = repository
    store.persist_manifest(_manifest())
    event = _event()

    persisted = store.persist_event(event)

    assert persisted == event
    assert store.load_event(
        PROJECT_ID,
        "AIN-000001",
        "AIE-000001",
    ) == event
    assert store.list_events(PROJECT_ID) == (event,)
    assert store.list_events(
        PROJECT_ID,
        "AIN-000001",
    ) == (event,)
    assert approved_input_event_path(
        root,
        PROJECT_ID,
        "AIN-000001",
        "AIE-000001",
    ).is_file()


def test_scan_rejects_duplicate_global_event_id(repository) -> None:
    store, root = repository
    store.persist_manifest(_manifest(approved_input_id="AIN-000001"))
    store.persist_manifest(_manifest(approved_input_id="AIN-000002"))
    event = _event()
    store.persist_event(event)

    other_dir = approved_input_event_directory_path(
        root,
        PROJECT_ID,
        "AIN-000002",
    )
    other_dir.mkdir()
    duplicate = create_approved_input_event(
        project_id=PROJECT_ID,
        approved_input_event_id="AIE-000001",
        approved_input_id="AIN-000002",
        event_type="invalidated",
        reason_code="other_failure",
        rationale=None,
        actor_identity="integrity-checker",
        successor_approved_input_id=None,
        causal_review_document_id=None,
        causal_review_document_version_id=None,
        causal_review_revision_id=None,
        causal_finalization_decision_id=None,
        causal_finalization_decision_fingerprint=None,
        occurred_at="2026-08-07T11:31:00Z",
    )
    (other_dir / "AIE-000001.json").write_text(
        approved_input_event_to_json(duplicate),
        encoding="utf-8",
    )

    result = store.scan_project(PROJECT_ID)

    assert "duplicate_approved_input_event_id" in {
        issue.code for issue in result.issues
    }
    with pytest.raises(ApprovedInputIntegrityError):
        store.list_events(PROJECT_ID)


def test_scan_reports_interrupted_event_persistence(repository) -> None:
    store, root = repository
    store.persist_manifest(_manifest())
    directory = approved_input_event_directory_path(
        root,
        PROJECT_ID,
        "AIN-000001",
    )
    directory.mkdir()
    temporary = directory / ".AIE-000001.json.tmp"
    temporary.write_text(
        approved_input_event_to_json(_event()),
        encoding="utf-8",
    )

    result = store.scan_project(PROJECT_ID)

    assert "approved_input_event_persistence_interrupted" in {
        issue.code for issue in result.issues
    }
    with pytest.raises(ApprovedInputRecoveryRequiredError):
        store.next_approved_input_event_id(PROJECT_ID)


def test_scan_rejects_orphan_event_directory(repository) -> None:
    store, root = repository
    store.persist_manifest(_manifest())
    orphan = approved_input_event_directory_path(
        root,
        PROJECT_ID,
        "AIN-000002",
    )
    orphan.mkdir()

    result = store.scan_project(PROJECT_ID)

    assert "orphan_approved_input_event_directory" in {
        issue.code for issue in result.issues
    }
