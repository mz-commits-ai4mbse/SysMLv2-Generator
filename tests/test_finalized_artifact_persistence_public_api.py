"""Public API test for finalized artifact persistence."""

from __future__ import annotations

from modules.review_workspace import (
    ReviewWorkspaceRepository,
)


def test_finalized_artifact_persistence_is_public() -> None:
    assert callable(
        ReviewWorkspaceRepository
        .persist_finalized_artifact_set
    )
