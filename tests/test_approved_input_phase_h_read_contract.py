"""Tests for the stable active-only Approved Input contract used by Phase H."""

from pathlib import Path

import pytest

from modules.approved_input.errors import (
    ApprovedInputIntegrityError,
)
from modules.approved_input.lifecycle_service import (
    ApprovedInputLifecycleService,
)
from modules.approved_input.paths import (
    approved_input_event_directory_path,
)

from tests.test_approved_input_repository import (
    PROJECT_ID,
    _manifest,
    repository,
)


def test_phase_h_read_contract_returns_empty_tuple_for_no_inputs(
    repository,
) -> None:
    store, _ = repository

    result = store.list_active_approved_inputs(PROJECT_ID)

    assert result == ()
    assert isinstance(result, tuple)


def test_phase_h_read_contract_returns_active_manifest(
    repository,
) -> None:
    store, _ = repository
    manifest = _manifest()
    store.persist_manifest(manifest)

    result = store.list_active_approved_inputs(PROJECT_ID)

    assert result == (manifest,)


def test_phase_h_read_contract_excludes_invalidated_input(
    repository,
) -> None:
    store, root = repository
    manifest = _manifest()
    store.persist_manifest(manifest)
    lifecycle = ApprovedInputLifecycleService(
        root=root,
        approved_input_repository=store,
    )

    lifecycle.invalidate(
        PROJECT_ID,
        manifest.approved_input_id,
        reason_code="source_integrity_failure",
        actor_identity="integrity-checker",
    )

    assert store.list_active_approved_inputs(PROJECT_ID) == ()
    assert store.list_manifests(PROJECT_ID) == (manifest,)
    assert manifest.authority_state == "active"


def test_phase_h_read_contract_fails_closed_on_repository_issue(
    repository,
) -> None:
    store, root = repository
    manifest = _manifest()
    store.persist_manifest(manifest)
    directory = approved_input_event_directory_path(
        root,
        PROJECT_ID,
        manifest.approved_input_id,
    )
    directory.mkdir()
    (directory / "unexpected.txt").write_text(
        "not a lifecycle event\n",
        encoding="utf-8",
    )

    with pytest.raises(ApprovedInputIntegrityError):
        store.list_active_approved_inputs(PROJECT_ID)
