"""Public API tests for P9 evidence-reference construction."""

from __future__ import annotations

import modules.review_workspace as review_workspace


def test_p9_evidence_reference_adapter_is_publicly_importable() -> None:
    assert (
        review_workspace.P9SubjectEvidence
        is not None
    )
    assert (
        review_workspace.P9StructuredEvidenceSet
        is not None
    )
    assert callable(
        review_workspace
        .construct_p9_evidence_references
    )


def test_p9_evidence_reference_constants_are_public() -> None:
    assert (
        review_workspace.SOURCE_EVIDENCE_ROLE
        == "agent_source_evidence"
    )
    assert (
        review_workspace.CONSENSUS_EVIDENCE_ROLE
        == "agent_consensus"
    )


def test_p9_evidence_reference_exports_are_declared() -> None:
    required_exports = {
        "SOURCE_EVIDENCE_ROLE",
        "CONSENSUS_EVIDENCE_ROLE",
        "P9SubjectEvidence",
        "P9StructuredEvidenceSet",
        "construct_p9_evidence_references",
    }

    assert required_exports <= set(
        review_workspace.__all__
    )
