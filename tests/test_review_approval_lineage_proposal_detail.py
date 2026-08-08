"""Regression for Proposal Details after split/merge lineage."""

from dataclasses import replace

from modules.review_workspace.proposal_detail import (
    build_review_proposal_details,
)

from tests.test_review_approval_proposal_detail import (
    _item,
    _proposal,
)
from modules.review_workspace.p9_proposal_adapter import (
    P9StructuredProposalSet,
)


def test_split_child_keeps_access_to_original_proposal_detail():
    proposal = _proposal(
        "CAND-001",
        artifact_id="AGENT-001",
        text="Original proposal.",
        fingerprint="b" * 64,
    )
    original = _item((proposal,))
    split_child = replace(
        original,
        stable_subject_key="requirement:human-split-child",
        lineage_operation="split",
        derived_from_review_item_ids=("RIT-000099",),
    )

    details = build_review_proposal_details(
        split_child,
        P9StructuredProposalSet(
            project_id="123456",
            source_id="SRC-000001",
            processing_run_id="RUN-000001",
            attempt_id="ATT-000001",
            element_proposals=(proposal,),
            relationship_proposals=(),
        ),
    )

    assert details[0].proposal_id == "CAND-001"
