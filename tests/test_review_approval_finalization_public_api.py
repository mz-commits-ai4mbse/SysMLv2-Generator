"""Public API tests for G6.4a finalization workflow."""

def test_g64a_finalization_symbols_are_public():
    import modules.review_workspace as review_workspace

    for name in (
        "ReviewFinalizationWorkflowPreview",
        "build_finalized_review_artifact_set",
        "create_review_finalization_workflow_preview",
        "ReviewApprovalFinalizationResult",
    ):
        assert hasattr(
            review_workspace,
            name,
        ), name
