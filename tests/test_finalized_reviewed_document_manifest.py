"""Tests for the immutable Finalized Reviewed Document manifest."""

from __future__ import annotations

from dataclasses import replace
import json

import pytest

from modules.review_workspace.errors import (
    ReviewIntegrityError,
    ReviewValidationError,
)
from modules.review_workspace.finalization_authorization import (
    authorize_review_document_finalization,
)
from modules.review_workspace.finalization_validation import (
    assess_review_document_finalization,
)
from modules.review_workspace.reviewed_document_manifest import (
    FINALIZED_REVIEWED_DOCUMENT_SCHEMA_VERSION,
    FINALIZED_REVIEW_ITEM_OUTCOMES,
    calculate_finalized_reviewed_document_fingerprint,
    create_finalized_reviewed_document,
    finalized_reviewed_document_from_json,
    finalized_reviewed_document_to_dict,
    finalized_reviewed_document_to_json,
    parse_finalized_reviewed_document,
    validate_finalized_reviewed_document,
)

from tests.test_review_workspace_finalization_authorization import (
    FINALIZATION_TIMESTAMP,
    _decision,
)
from tests.test_review_workspace_finalization_validation import (
    _element_item,
    _revision,
)
from tests.test_review_workspace_repository_mutations import (
    _bundle,
)


def _manifest():
    document, version, _ = _bundle()
    revision = _revision(
        _element_item()
    )
    assessment = (
        assess_review_document_finalization(
            document,
            version,
            revision,
        )
    )
    authorized = (
        authorize_review_document_finalization(
            version,
            revision,
            assessment,
            _decision(assessment),
            timestamp=FINALIZATION_TIMESTAMP,
        )
    )

    manifest = create_finalized_reviewed_document(
        document,
        authorized.finalized_version,
        revision,
        authorized.authorization,
    )

    return (
        document,
        authorized.finalized_version,
        revision,
        authorized.authorization,
        manifest,
    )


def test_contract_constants() -> None:
    assert (
        FINALIZED_REVIEWED_DOCUMENT_SCHEMA_VERSION
        == "1.0.0"
    )
    assert FINALIZED_REVIEW_ITEM_OUTCOMES == frozenset(
        {
            "accepted_as_generated",
            "accepted_with_modification",
            "combined",
            "rejected",
            "deferred",
            "out_of_scope",
        }
    )


def test_create_manifest_binds_exact_review_chain() -> None:
    (
        document,
        version,
        revision,
        authorization,
        manifest,
    ) = _manifest()

    assert manifest.project_id == document.project_id
    assert (
        manifest.review_document_id
        == document.review_document_id
    )
    assert (
        manifest.review_document_version_id
        == version.review_document_version_id
    )
    assert (
        manifest.review_revision_id
        == revision.review_revision_id
    )
    assert (
        manifest.review_document_content_fingerprint
        == document.content_fingerprint
    )
    assert (
        manifest.finalized_version_content_fingerprint
        == version.content_fingerprint
    )
    assert (
        manifest.review_revision_fingerprint
        == revision.revision_fingerprint
    )
    assert (
        manifest.finalization_authorization_fingerprint
        == authorization.authorization_fingerprint
    )


def test_manifest_binds_decision_and_validation() -> None:
    _, _, _, authorization, manifest = _manifest()

    assert (
        manifest.finalization_decision_id
        == authorization.human_review_decision_id
    )
    assert (
        manifest.finalization_decision_fingerprint
        == authorization
        .human_review_decision_fingerprint
    )
    assert (
        manifest.finalization_validation_fingerprint
        == authorization.validation_fingerprint
    )
    assert (
        manifest.reviewer_identity
        == authorization.reviewer_identity
    )
    assert manifest.decision_at == authorization.decided_at
    assert (
        manifest.finalized_at
        == authorization.finalized_at
    )


def test_manifest_contains_exact_item_references() -> None:
    _, _, revision, _, manifest = _manifest()

    assert len(manifest.review_items) == 1

    reference = manifest.review_items[0]
    item = revision.review_items[0]

    assert reference.review_item_id == item.review_item_id
    assert (
        reference.stable_subject_key
        == item.stable_subject_key
    )
    assert (
        reference.effective_review_outcome
        == item.effective_review_outcome
    )
    assert (
        reference.item_content_fingerprint
        == item.item_content_fingerprint
    )


def test_manifest_items_are_sorted_by_identifier() -> None:
    document, version, _ = _bundle()
    second = _element_item(
        review_item_id="RIT-000002",
    )
    first = _element_item()
    revision = _revision(second, first)

    assessment = (
        assess_review_document_finalization(
            document,
            version,
            revision,
        )
    )
    authorized = (
        authorize_review_document_finalization(
            version,
            revision,
            assessment,
            _decision(assessment),
            timestamp=FINALIZATION_TIMESTAMP,
        )
    )

    manifest = create_finalized_reviewed_document(
        document,
        authorized.finalized_version,
        revision,
        authorized.authorization,
    )

    assert tuple(
        item.review_item_id
        for item in manifest.review_items
    ) == (
        "RIT-000001",
        "RIT-000002",
    )


def test_json_round_trip_is_exact() -> None:
    *_, manifest = _manifest()

    text = finalized_reviewed_document_to_json(
        manifest
    )

    assert text.endswith("\n")
    assert (
        finalized_reviewed_document_from_json(text)
        == manifest
    )


def test_dictionary_round_trip_is_exact() -> None:
    *_, manifest = _manifest()

    payload = finalized_reviewed_document_to_dict(
        manifest
    )

    assert (
        parse_finalized_reviewed_document(payload)
        == manifest
    )


def test_serialization_is_deterministic() -> None:
    *_, manifest = _manifest()

    assert finalized_reviewed_document_to_json(
        manifest
    ) == finalized_reviewed_document_to_json(
        manifest
    )


def test_fingerprint_is_deterministic() -> None:
    *_, manifest = _manifest()

    assert (
        calculate_finalized_reviewed_document_fingerprint(
            manifest
        )
        == manifest.content_fingerprint
    )


def test_tampered_manifest_is_rejected() -> None:
    *_, manifest = _manifest()

    tampered = replace(
        manifest,
        reviewer_identity="other-reviewer",
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="fingerprint",
    ):
        validate_finalized_reviewed_document(
            tampered
        )


def test_draft_version_is_rejected() -> None:
    document, version, _ = _bundle()
    revision = _revision(
        _element_item()
    )
    assessment = (
        assess_review_document_finalization(
            document,
            version,
            revision,
        )
    )
    authorized = (
        authorize_review_document_finalization(
            version,
            revision,
            assessment,
            _decision(assessment),
            timestamp=FINALIZATION_TIMESTAMP,
        )
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="finalized Review Document Version",
    ):
        create_finalized_reviewed_document(
            document,
            version,
            revision,
            authorized.authorization,
        )


def test_foreign_revision_is_rejected() -> None:
    document, version, _ = _bundle()
    revision = _revision(
        _element_item()
    )
    assessment = (
        assess_review_document_finalization(
            document,
            version,
            revision,
        )
    )
    authorized = (
        authorize_review_document_finalization(
            version,
            revision,
            assessment,
            _decision(assessment),
            timestamp=FINALIZATION_TIMESTAMP,
        )
    )
    foreign_revision = _revision(
        _element_item(),
        revision_id="RVR-000002",
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="same Review Revision",
    ):
        create_finalized_reviewed_document(
            document,
            authorized.finalized_version,
            foreign_revision,
            authorized.authorization,
        )


def test_open_item_reference_is_rejected() -> None:
    *_, manifest = _manifest()
    reference = replace(
        manifest.review_items[0],
        effective_review_outcome="open",
    )
    provisional = replace(
        manifest,
        review_items=(reference,),
        content_fingerprint="0" * 64,
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="non-blocking effective outcome",
    ):
        calculate_finalized_reviewed_document_fingerprint(
            provisional
        )


def test_unknown_json_field_is_rejected() -> None:
    *_, manifest = _manifest()
    payload = finalized_reviewed_document_to_dict(
        manifest
    )
    payload["unknown"] = True

    with pytest.raises(
        ReviewValidationError,
        match="unknown",
    ):
        parse_finalized_reviewed_document(payload)


def test_duplicate_json_key_is_rejected() -> None:
    *_, manifest = _manifest()
    text = finalized_reviewed_document_to_json(
        manifest
    )
    payload = json.loads(text)
    encoded = json.dumps(payload)
    duplicate = encoded.replace(
        '{"schema_version":',
        '{"schema_version":"duplicate",'
        '"schema_version":',
        1,
    )

    with pytest.raises(
        ReviewValidationError,
        match="Duplicate JSON key",
    ):
        finalized_reviewed_document_from_json(
            duplicate
        )


def test_manifest_argument_is_strict() -> None:
    with pytest.raises(
        ReviewValidationError,
        match="FinalizedReviewedDocument",
    ):
        validate_finalized_reviewed_document(
            object()
        )
