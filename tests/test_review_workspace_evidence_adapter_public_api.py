"""Public API tests for Review Workspace evidence selection."""

from __future__ import annotations

import modules.review_workspace as review_workspace


def test_p9_evidence_adapter_is_publicly_importable() -> None:
    assert (
        review_workspace.P9ReviewEvidenceSet
        is not None
    )
    assert callable(
        review_workspace.select_p9_review_evidence_set
    )


def test_p9_evidence_adapter_exports_are_declared() -> None:
    required_exports = {
        "AGENTIC_INGESTION_STAGE",
        "P9_REVIEW_ARTIFACT_TYPES",
        "P9ReviewEvidenceSet",
        "select_p9_review_evidence_set",
    }

    assert required_exports <= set(
        review_workspace.__all__
    )
