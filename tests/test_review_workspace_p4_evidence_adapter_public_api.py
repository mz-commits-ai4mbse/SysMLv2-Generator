"""Public API tests for P4 Review Evidence association."""

from __future__ import annotations

import modules.review_workspace as review_workspace


def test_p4_evidence_adapter_is_publicly_importable() -> None:
    assert (
        review_workspace.P4ReviewEvidenceRecord
        is not None
    )
    assert (
        review_workspace.P4ReviewEvidenceSet
        is not None
    )
    assert callable(
        review_workspace.select_p4_review_evidence_set
    )


def test_p4_evidence_adapter_exports_are_declared() -> None:
    required_exports = {
        "P4ReviewEvidenceRecord",
        "P4ReviewEvidenceSet",
        "select_p4_review_evidence_set",
    }

    assert required_exports <= set(
        review_workspace.__all__
    )
