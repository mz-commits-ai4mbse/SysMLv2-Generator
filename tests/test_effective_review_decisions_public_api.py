"""Public API tests for effective Review decisions."""

from __future__ import annotations

import modules.review_workspace as review_workspace


def test_effective_decision_set_type_is_public() -> None:
    assert (
        review_workspace.EffectiveReviewDecisionSet
        is not None
    )


def test_effective_decision_set_contract_is_public() -> None:
    assert (
        review_workspace
        .EFFECTIVE_REVIEW_DECISION_SET_SCHEMA_VERSION
        == "1.0.0"
    )

    functions = (
        review_workspace
        .calculate_effective_review_decision_set_fingerprint,
        review_workspace
        .create_effective_review_decision_set,
        review_workspace
        .effective_review_decision_set_from_json,
        review_workspace
        .effective_review_decision_set_to_dict,
        review_workspace
        .effective_review_decision_set_to_json,
        review_workspace
        .parse_effective_review_decision_set,
        review_workspace
        .validate_effective_review_decision_set,
        review_workspace
        .validate_effective_review_decision_set_binding,
    )

    assert all(callable(value) for value in functions)


def test_effective_decision_set_exports_are_declared() -> None:
    required_exports = {
        "EFFECTIVE_REVIEW_DECISION_SET_SCHEMA_VERSION",
        "EffectiveReviewDecisionSet",
        "calculate_effective_review_decision_set_fingerprint",
        "create_effective_review_decision_set",
        "effective_review_decision_set_from_json",
        "effective_review_decision_set_to_dict",
        "effective_review_decision_set_to_json",
        "parse_effective_review_decision_set",
        "validate_effective_review_decision_set",
        "validate_effective_review_decision_set_binding",
    }

    assert required_exports <= set(
        review_workspace.__all__
    )
