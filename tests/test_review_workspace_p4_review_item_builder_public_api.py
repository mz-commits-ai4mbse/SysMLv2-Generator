"""Public API tests for initial P4 Review Item construction."""

from __future__ import annotations

import modules.review_workspace as review_workspace


def test_p4_review_item_builder_is_publicly_importable() -> None:
    assert (
        review_workspace.P4InitialReviewItemSet
        is not None
    )
    assert callable(
        review_workspace
        .construct_initial_p4_review_items
    )
    assert callable(
        review_workspace
        .create_p4_information_unit_stable_subject_key
    )


def test_p4_open_question_types_are_public() -> None:
    assert (
        review_workspace
        .P4_OPEN_QUESTION_INFORMATION_TYPES
        == frozenset(
            {
                "open_question",
                "gap",
                "ambiguity",
                "risk",
                "unclassified",
            }
        )
    )


def test_p4_review_item_builder_exports_are_declared() -> None:
    required_exports = {
        "P4_OPEN_QUESTION_INFORMATION_TYPES",
        "P4InitialReviewItemSet",
        "construct_initial_p4_review_items",
        "create_p4_information_unit_stable_subject_key",
    }

    assert required_exports <= set(
        review_workspace.__all__
    )
