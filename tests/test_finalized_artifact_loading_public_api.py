"""Public API test for finalized artifact loading."""

from __future__ import annotations

from modules.review_workspace import (
    ReviewWorkspaceRepository,
)


def test_finalized_artifact_loading_is_public() -> None:
    assert callable(
        ReviewWorkspaceRepository
        .load_finalized_artifact_set
    )
