"""Tests for immutable Scoped Review Action manifests."""

from __future__ import annotations

from dataclasses import replace

import pytest

from modules.review_workspace.errors import (
    ReviewIntegrityError,
    ReviewValidationError,
)
from modules.review_workspace.scoped_action_manifest import (
    SCOPED_REVIEW_ACTION_SCHEMA_VERSION,
    calculate_scoped_review_action_fingerprint,
    create_scoped_review_action,
    parse_scoped_review_action,
    scoped_review_action_filename,
    scoped_review_action_from_json,
    scoped_review_action_to_dict,
    scoped_review_action_to_json,
    validate_scoped_review_action,
)
from modules.review_workspace.types import (
    MaterializedReviewItemReference,
)


def _materialized_item(
    *,
    review_item_id: str = "RIT-000001",
    fingerprint: str = "a" * 64,
) -> MaterializedReviewItemReference:
    return MaterializedReviewItemReference(
        review_item_id=review_item_id,
        item_content_fingerprint=fingerprint,
    )


def _document_default():
    return create_scoped_review_action(
        project_id="000001",
        review_document_id="RVD-000001",
        review_document_version_id="RVV-000001",
        scoped_review_action_id="SRA-000001",
        action_scope="document_default",
        decision_dimension="framework_assignment",
        selected_values=(
            "02_System/01_Requirements",
        ),
        filter_definition=None,
        materialized_items=(),
        created_by="reviewer@example.com",
        timestamp="2026-08-03T16:00:00Z",
        rationale=None,
    )


def _filtered_set():
    return create_scoped_review_action(
        project_id="000001",
        review_document_id="RVD-000001",
        review_document_version_id="RVV-000001",
        scoped_review_action_id="SRA-000002",
        action_scope="filtered_set",
        decision_dimension="classification",
        selected_values=("requirement",),
        filter_definition=(
            "review_item_kind=element;"
            "proposed_classification=requirement"
        ),
        materialized_items=(
            _materialized_item(),
            _materialized_item(
                review_item_id="RIT-000002",
                fingerprint="b" * 64,
            ),
        ),
        created_by="reviewer@example.com",
        timestamp="2026-08-03T16:05:00Z",
        rationale=None,
    )


def _explicit_selection(
    *,
    outcome: str = "deferred",
    rationale: str | None = None,
):
    return create_scoped_review_action(
        project_id="000001",
        review_document_id="RVD-000001",
        review_document_version_id="RVV-000001",
        scoped_review_action_id="SRA-000003",
        action_scope="explicit_selection",
        decision_dimension="review_outcome",
        selected_values=(outcome,),
        filter_definition=None,
        materialized_items=(
            _materialized_item(),
        ),
        created_by="reviewer@example.com",
        timestamp="2026-08-03T16:10:00Z",
        rationale=rationale,
    )


def test_create_scoped_action_is_fingerprinted() -> None:
    action = _filtered_set()

    assert action.schema_version == (
        SCOPED_REVIEW_ACTION_SCHEMA_VERSION
    )
    assert action.action_fingerprint == (
        calculate_scoped_review_action_fingerprint(
            action
        )
    )

    validate_scoped_review_action(action)


@pytest.mark.parametrize(
    "action",
    (
        _document_default(),
        _filtered_set(),
        _explicit_selection(),
    ),
)
def test_scoped_action_round_trip_is_deterministic(
    action,
) -> None:
    serialized = scoped_review_action_to_json(action)

    assert serialized.endswith("\n")
    assert (
        scoped_review_action_from_json(serialized)
        == action
    )
    assert scoped_review_action_to_json(
        scoped_review_action_from_json(serialized)
    ) == serialized


def test_scoped_action_dict_has_exact_fields() -> None:
    payload = scoped_review_action_to_dict(
        _filtered_set()
    )

    assert set(payload) == {
        "schema_version",
        "project_id",
        "review_document_id",
        "review_document_version_id",
        "scoped_review_action_id",
        "action_scope",
        "decision_dimension",
        "selected_values",
        "filter_definition",
        "materialized_items",
        "created_by",
        "created_at",
        "rationale",
        "action_fingerprint",
    }


def test_scoped_action_filename_is_canonical() -> None:
    assert scoped_review_action_filename(
        "SRA-000042"
    ) == "SRA-000042.json"

    with pytest.raises(ReviewValidationError):
        scoped_review_action_filename("INVALID")


def test_scoped_action_rejects_modified_content() -> None:
    action = _filtered_set()

    modified = replace(
        action,
        created_by="other@example.com",
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="fingerprint",
    ):
        validate_scoped_review_action(modified)


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("project_id", "INVALID"),
        ("review_document_id", "INVALID"),
        ("review_document_version_id", "INVALID"),
        ("scoped_review_action_id", "INVALID"),
        ("action_scope", "dynamic_query"),
        ("decision_dimension", "approval"),
        ("created_by", ""),
        ("created_at", "invalid"),
        ("action_fingerprint", "invalid"),
    ),
)
def test_scoped_action_rejects_invalid_fields(
    field: str,
    value: object,
) -> None:
    action = _filtered_set()

    modified = replace(
        action,
        **{field: value},
    )

    with pytest.raises(
        (
            ReviewValidationError,
            ReviewIntegrityError,
        )
    ):
        validate_scoped_review_action(modified)


def test_document_default_has_no_dynamic_scope() -> None:
    action = _document_default()

    with pytest.raises(
        ReviewIntegrityError,
        match="filter_definition",
    ):
        validate_scoped_review_action(
            replace(
                action,
                filter_definition="review_item_kind=element",
            )
        )

    with pytest.raises(
        ReviewIntegrityError,
        match="materialized",
    ):
        validate_scoped_review_action(
            replace(
                action,
                materialized_items=(
                    _materialized_item(),
                ),
            )
        )


def test_document_default_cannot_set_review_outcome() -> None:
    action = _document_default()

    modified = replace(
        action,
        decision_dimension="review_outcome",
        selected_values=("accepted_as_generated",),
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="must not set review_outcome",
    ):
        validate_scoped_review_action(modified)


def test_filtered_set_requires_filter_definition() -> None:
    action = _filtered_set()

    modified = replace(
        action,
        filter_definition=None,
    )

    with pytest.raises(ReviewValidationError):
        validate_scoped_review_action(modified)


def test_filtered_set_requires_materialized_items() -> None:
    action = _filtered_set()

    modified = replace(
        action,
        materialized_items=(),
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="materialized",
    ):
        validate_scoped_review_action(modified)


def test_explicit_selection_rejects_filter_definition() -> None:
    action = _explicit_selection()

    modified = replace(
        action,
        filter_definition="review_item_id=RIT-000001",
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="must not contain",
    ):
        validate_scoped_review_action(modified)


def test_explicit_selection_requires_materialized_items() -> None:
    action = _explicit_selection()

    modified = replace(
        action,
        materialized_items=(),
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="materialized",
    ):
        validate_scoped_review_action(modified)


def test_materialized_item_ids_must_be_unique() -> None:
    action = _filtered_set()
    reference = action.materialized_items[0]

    modified = replace(
        action,
        materialized_items=(
            reference,
            replace(
                reference,
                item_content_fingerprint="c" * 64,
            ),
        ),
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="must be unique",
    ):
        validate_scoped_review_action(modified)


@pytest.mark.parametrize(
    ("review_item_id", "fingerprint"),
    (
        ("INVALID", "a" * 64),
        ("RIT-000001", "invalid"),
    ),
)
def test_materialized_items_are_strictly_validated(
    review_item_id: str,
    fingerprint: str,
) -> None:
    action = _filtered_set()

    modified = replace(
        action,
        materialized_items=(
            _materialized_item(
                review_item_id=review_item_id,
                fingerprint=fingerprint,
            ),
        ),
    )

    with pytest.raises(ReviewValidationError):
        validate_scoped_review_action(modified)


@pytest.mark.parametrize(
    "values",
    (
        (),
        ("requirement", "requirement"),
    ),
)
def test_selected_values_must_be_nonempty_and_unique(
    values: tuple[str, ...],
) -> None:
    action = _filtered_set()

    modified = replace(
        action,
        selected_values=values,
    )

    with pytest.raises(
        (
            ReviewValidationError,
            ReviewIntegrityError,
        )
    ):
        validate_scoped_review_action(modified)


@pytest.mark.parametrize(
    "values",
    (
        ("accepted_as_generated", "rejected"),
        ("not_a_review_outcome",),
    ),
)
def test_review_outcome_requires_one_valid_value(
    values: tuple[str, ...],
) -> None:
    action = _explicit_selection()

    modified = replace(
        action,
        selected_values=values,
    )

    with pytest.raises(ReviewValidationError):
        validate_scoped_review_action(modified)


def test_rejection_requires_rationale() -> None:
    with pytest.raises(
        ReviewIntegrityError,
        match="requires a rationale",
    ):
        _explicit_selection(
            outcome="rejected",
            rationale=None,
        )


def test_rejection_with_rationale_is_valid() -> None:
    action = _explicit_selection(
        outcome="rejected",
        rationale=(
            "The selected statements are unsupported."
        ),
    )

    validate_scoped_review_action(action)


def test_optional_rationale_rejects_whitespace() -> None:
    action = _filtered_set()

    modified = replace(
        action,
        rationale="  invalid  ",
    )

    with pytest.raises(ReviewValidationError):
        validate_scoped_review_action(modified)


def test_parse_rejects_missing_and_unknown_fields() -> None:
    payload = scoped_review_action_to_dict(
        _filtered_set()
    )

    missing = dict(payload)
    missing.pop("created_by")

    with pytest.raises(
        ReviewValidationError,
        match="missing",
    ):
        parse_scoped_review_action(missing)

    unknown = {
        **payload,
        "unexpected": True,
    }

    with pytest.raises(
        ReviewValidationError,
        match="unknown",
    ):
        parse_scoped_review_action(unknown)


def test_parse_rejects_non_array_fields() -> None:
    payload = scoped_review_action_to_dict(
        _filtered_set()
    )
    payload["selected_values"] = {}

    with pytest.raises(
        ReviewValidationError,
        match="selected_values",
    ):
        parse_scoped_review_action(payload)

    payload = scoped_review_action_to_dict(
        _filtered_set()
    )
    payload["materialized_items"] = {}

    with pytest.raises(
        ReviewValidationError,
        match="materialized_items",
    ):
        parse_scoped_review_action(payload)


def test_parse_rejects_invalid_materialized_item() -> None:
    payload = scoped_review_action_to_dict(
        _filtered_set()
    )

    materialized = dict(
        payload["materialized_items"][0]
    )
    materialized["unexpected"] = True
    payload["materialized_items"][0] = materialized

    with pytest.raises(
        ReviewValidationError,
        match="unknown",
    ):
        parse_scoped_review_action(payload)


def test_json_rejects_duplicate_keys() -> None:
    text = scoped_review_action_to_json(
        _filtered_set()
    )

    duplicated = text.replace(
        '"project_id": "000001",',
        (
            '"project_id": "000001",\n'
            '  "project_id": "000001",'
        ),
        1,
    )

    with pytest.raises(
        ReviewValidationError,
        match="Duplicate JSON object key",
    ):
        scoped_review_action_from_json(duplicated)


def test_json_rejects_invalid_input() -> None:
    with pytest.raises(ReviewValidationError):
        scoped_review_action_from_json(None)

    with pytest.raises(ReviewValidationError):
        scoped_review_action_from_json("{invalid")

