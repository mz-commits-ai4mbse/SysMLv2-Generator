"""Public API tests for G5.5 Approved Input promotion."""

import modules.approved_input as approved_input


def test_g5_5_promotion_symbols_are_public() -> None:
    expected = {
        "PROMOTION_PLAN_ACTIONS",
        "ApprovedInputPromotionBlockedError",
        "ApprovedInputPromotionPlan",
        "ApprovedInputPromotionPlanItem",
        "ApprovedInputPromotionResult",
        "ApprovedInputPromotionService",
        "create_approved_input_promotion_plan",
    }

    assert expected.issubset(set(approved_input.__all__))
