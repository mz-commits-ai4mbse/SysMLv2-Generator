"""Tests for immutable Review Document Version manifests."""

from __future__ import annotations

from dataclasses import replace

import pytest

from modules.review_workspace.errors import (
    InvalidReviewVersionTransitionError,
    ReviewIntegrityError,
    ReviewValidationError,
)
from modules.review_workspace.version_manifest import (
    REVIEW_DOCUMENT_VERSION_SCHEMA_VERSION,
    calculate_review_document_version_fingerprint,
    create_review_document_version,
    finalize_review_document_version,
    parse_review_document_version,
    review_document_version_from_json,
    review_document_version_to_dict,
    review_document_version_to_json,
    validate_review_document_version,
)


def _draft():
    return create_review_document_version(
        project_id="000001",
        review_document_id="RVD-000001",
        review_document_version_id="RVV-000001",
        version_number=1,
        predecessor_version_id=None,
        reopen_reason=None,
        opened_by="reviewer@example.com",
        timestamp="2026-08-03T15:00:00Z",
        head_revision_id="RVR-000001",
    )


def _successor():
    return create_review_document_version(
        project_id="000001",
        review_document_id="RVD-000001",
        review_document_version_id="RVV-000002",
        version_number=2,
        predecessor_version_id="RVV-000001",
        reopen_reason=(
            "Framework assignment requires correction."
        ),
        opened_by="reviewer@example.com",
        timestamp="2026-08-04T15:00:00Z",
        head_revision_id="RVR-000002",
    )


def _finalized():
    return finalize_review_document_version(
        _draft(),
        finalized_revision_id="RVR-000001",
        finalization_decision_id="HRD-000001",
        timestamp="2026-08-03T16:00:00Z",
    )


def test_create_draft_version_is_fingerprinted() -> None:
    version = _draft()

    assert version.schema_version == (
        REVIEW_DOCUMENT_VERSION_SCHEMA_VERSION
    )
    assert version.version_state == "draft"
    assert version.finalized_revision_id is None
    assert version.finalized_at is None
    assert version.finalization_decision_id is None

    assert version.content_fingerprint == (
        calculate_review_document_version_fingerprint(
            version
        )
    )

    validate_review_document_version(version)


def test_finalize_version_returns_new_immutable_state() -> None:
    draft = _draft()

    finalized = finalize_review_document_version(
        draft,
        finalized_revision_id="RVR-000001",
        finalization_decision_id="HRD-000001",
        timestamp="2026-08-03T16:00:00Z",
    )

    assert draft.version_state == "draft"
    assert draft.finalized_revision_id is None

    assert finalized.version_state == "finalized"
    assert finalized.finalized_revision_id == (
        finalized.head_revision_id
    )
    assert finalized.finalization_decision_id == (
        "HRD-000001"
    )

    validate_review_document_version(finalized)


@pytest.mark.parametrize(
    "version",
    (
        _draft(),
        _successor(),
        _finalized(),
    ),
)
def test_version_round_trip_is_deterministic(
    version,
) -> None:
    serialized = review_document_version_to_json(
        version
    )

    assert serialized.endswith("\n")
    assert (
        review_document_version_from_json(serialized)
        == version
    )

    assert review_document_version_to_json(
        review_document_version_from_json(serialized)
    ) == serialized


def test_version_dict_has_exact_fields() -> None:
    payload = review_document_version_to_dict(_draft())

    assert set(payload) == {
        "schema_version",
        "project_id",
        "review_document_id",
        "review_document_version_id",
        "version_number",
        "predecessor_version_id",
        "reopen_reason",
        "opened_by",
        "opened_at",
        "version_state",
        "head_revision_id",
        "finalized_revision_id",
        "finalized_at",
        "finalization_decision_id",
        "content_fingerprint",
    }


def test_first_version_rejects_predecessor() -> None:
    version = _draft()

    modified = replace(
        version,
        predecessor_version_id="RVV-000001",
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="must not have a predecessor",
    ):
        validate_review_document_version(modified)


def test_first_version_rejects_reopen_reason() -> None:
    version = _draft()

    modified = replace(
        version,
        reopen_reason="Unexpected reason.",
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="must not have a reopen reason",
    ):
        validate_review_document_version(modified)


def test_successor_requires_predecessor() -> None:
    version = _successor()

    modified = replace(
        version,
        predecessor_version_id=None,
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="requires predecessor_version_id",
    ):
        validate_review_document_version(modified)


def test_successor_requires_reopen_reason() -> None:
    version = _successor()

    modified = replace(
        version,
        reopen_reason=None,
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="requires a reopen_reason",
    ):
        validate_review_document_version(modified)


def test_predecessor_must_be_earlier() -> None:
    version = _successor()

    modified = replace(
        version,
        predecessor_version_id="RVV-000003",
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="earlier",
    ):
        validate_review_document_version(modified)


@pytest.mark.parametrize(
    "field",
    (
        "finalized_revision_id",
        "finalized_at",
        "finalization_decision_id",
    ),
)
def test_draft_rejects_finalization_data(
    field: str,
) -> None:
    version = _draft()

    values = {
        "finalized_revision_id": "RVR-000001",
        "finalized_at": "2026-08-03T16:00:00Z",
        "finalization_decision_id": "HRD-000001",
    }

    modified = replace(
        version,
        **{field: values[field]},
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="must not contain finalization data",
    ):
        validate_review_document_version(modified)


def test_finalization_requires_current_head_revision() -> None:
    with pytest.raises(
        InvalidReviewVersionTransitionError,
        match="head_revision_id",
    ):
        finalize_review_document_version(
            _draft(),
            finalized_revision_id="RVR-000002",
            finalization_decision_id="HRD-000001",
            timestamp="2026-08-03T16:00:00Z",
        )


def test_finalized_version_cannot_be_finalized_again() -> None:
    with pytest.raises(
        InvalidReviewVersionTransitionError,
        match="Only a draft",
    ):
        finalize_review_document_version(
            _finalized(),
            finalized_revision_id="RVR-000001",
            finalization_decision_id="HRD-000002",
            timestamp="2026-08-03T17:00:00Z",
        )


def test_finalized_state_requires_all_finalization_fields() -> None:
    finalized = _finalized()

    for field in (
        "finalized_revision_id",
        "finalized_at",
        "finalization_decision_id",
    ):
        modified = replace(
            finalized,
            **{field: None},
        )

        with pytest.raises(ReviewIntegrityError):
            validate_review_document_version(modified)


def test_finalized_revision_must_equal_head() -> None:
    finalized = _finalized()

    modified = replace(
        finalized,
        head_revision_id="RVR-000002",
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="must equal",
    ):
        validate_review_document_version(modified)


def test_finalization_time_cannot_precede_opening() -> None:
    with pytest.raises(
        ReviewIntegrityError,
        match="earlier than opened_at",
    ):
        finalize_review_document_version(
            _draft(),
            finalized_revision_id="RVR-000001",
            finalization_decision_id="HRD-000001",
            timestamp="2026-08-03T14:59:59Z",
        )


def test_finalization_decision_id_is_strict() -> None:
    with pytest.raises(
        ReviewValidationError,
        match="finalization_decision_id",
    ):
        finalize_review_document_version(
            _draft(),
            finalized_revision_id="RVR-000001",
            finalization_decision_id="INVALID",
            timestamp="2026-08-03T16:00:00Z",
        )


def test_version_rejects_modified_content() -> None:
    version = _draft()

    modified = replace(
        version,
        opened_by="other@example.com",
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="fingerprint",
    ):
        validate_review_document_version(modified)


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("project_id", "INVALID"),
        ("review_document_id", "INVALID"),
        ("review_document_version_id", "INVALID"),
        ("head_revision_id", "INVALID"),
        ("version_number", 0),
        ("version_number", True),
        ("opened_by", ""),
        ("opened_at", "invalid"),
        ("version_state", "closed"),
        ("content_fingerprint", "invalid"),
    ),
)
def test_version_rejects_invalid_fields(
    field: str,
    value: object,
) -> None:
    version = _draft()

    modified = replace(
        version,
        **{field: value},
    )

    with pytest.raises(
        (
            ReviewValidationError,
            ReviewIntegrityError,
        )
    ):
        validate_review_document_version(modified)


def test_parse_rejects_missing_and_unknown_fields() -> None:
    payload = review_document_version_to_dict(_draft())

    missing = dict(payload)
    missing.pop("opened_by")

    with pytest.raises(
        ReviewValidationError,
        match="missing",
    ):
        parse_review_document_version(missing)

    unknown = {
        **payload,
        "unexpected": True,
    }

    with pytest.raises(
        ReviewValidationError,
        match="unknown",
    ):
        parse_review_document_version(unknown)


def test_json_rejects_duplicate_keys() -> None:
    text = review_document_version_to_json(_draft())

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
        review_document_version_from_json(
            duplicated
        )


def test_json_rejects_invalid_input() -> None:
    with pytest.raises(ReviewValidationError):
        review_document_version_from_json(None)

    with pytest.raises(ReviewValidationError):
        review_document_version_from_json("{invalid")
