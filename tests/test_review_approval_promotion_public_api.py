"""Public API tests for G6.5 promotion traceability."""

def test_g65_promotion_symbols_are_public():
    import modules.review_workspace as review_workspace

    for name in (
        "ReviewApprovedInputEventTrace",
        "ReviewApprovedInputTrace",
        "ReviewApprovalPromotionResult",
    ):
        assert hasattr(
            review_workspace,
            name,
        ), name
