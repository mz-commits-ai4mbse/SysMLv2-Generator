"""Public API tests for structured P9 proposal adaptation."""

from __future__ import annotations

import modules.review_workspace as review_workspace


def test_p9_proposal_adapter_is_publicly_importable() -> None:
    assert review_workspace.P9SourceAssignment is not None
    assert review_workspace.P9ElementProposal is not None
    assert review_workspace.P9RelationshipProposal is not None
    assert review_workspace.P9StructuredProposalSet is not None

    assert callable(
        review_workspace.adapt_p9_agent_proposals
    )
    assert callable(
        review_workspace.create_element_stable_subject_key
    )
    assert callable(
        review_workspace
        .create_relationship_stable_subject_key
    )


def test_p9_proposal_adapter_exports_are_declared() -> None:
    required_exports = {
        "P9SourceAssignment",
        "P9ElementProposal",
        "P9RelationshipProposal",
        "P9StructuredProposalSet",
        "adapt_p9_agent_proposals",
        "create_element_stable_subject_key",
        "create_relationship_stable_subject_key",
    }

    assert required_exports <= set(
        review_workspace.__all__
    )
