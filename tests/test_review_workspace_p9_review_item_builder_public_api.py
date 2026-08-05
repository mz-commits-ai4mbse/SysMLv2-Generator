"""Public API tests for initial P9 Review Item construction."""

from __future__ import annotations

import modules.review_workspace as review_workspace


def test_p9_review_item_builder_is_publicly_importable() -> None:
    assert (
        review_workspace.P9InitialReviewItemSet
        is not None
    )
    assert callable(
        review_workspace
        .construct_initial_p9_review_items
    )


def test_p9_review_item_builder_defaults_are_public() -> None:
    assert (
        review_workspace
        .DEFAULT_TARGET_NOTATION_PROFILE_ID
        == "SYSML_V2_TARGET"
    )
    assert (
        review_workspace
        .DEFAULT_TARGET_NOTATION_PROFILE_VERSION
        == "1.0.0"
    )


def test_p9_review_item_builder_exports_are_declared() -> None:
    required_exports = {
        "DEFAULT_TARGET_NOTATION_PROFILE_ID",
        "DEFAULT_TARGET_NOTATION_PROFILE_VERSION",
        "P9InitialReviewItemSet",
        "construct_initial_p9_review_items",
    }

    assert required_exports <= set(
        review_workspace.__all__
    )
