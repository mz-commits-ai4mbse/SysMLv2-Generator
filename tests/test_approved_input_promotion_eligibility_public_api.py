"""Tests for the Approved Input promotion eligibility public API."""

import modules.approved_input as approved_input


def test_promotion_eligibility_symbols_are_public() -> None:
    expected = {
        "PROMOTABLE_REVIEW_ITEM_OUTCOMES",
        "PROMOTION_ALLOWED_RUN_STATES",
        "ApprovedInputPromotionEligibilityAssessment",
        "ApprovedInputPromotionItemAssessment",
        "assess_approved_input_promotion_eligibility",
    }

    assert expected.issubset(set(approved_input.__all__))
