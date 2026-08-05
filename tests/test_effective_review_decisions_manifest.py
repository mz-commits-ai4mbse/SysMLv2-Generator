"""Tests for immutable effective Review decisions."""

from __future__ import annotations

from dataclasses import replace
import json

import pytest

from modules.review_workspace.effective_decisions_manifest import (
    EFFECTIVE_REVIEW_DECISION_SET_SCHEMA_VERSION,
    EffectiveReviewDecisionSet,
    calculate_effective_review_decision_set_fingerprint,
    create_effective_review_decision_set,
    effective_review_decision_set_from_json,
    effective_review_decision_set_to_dict,
    effective_review_decision_set_to_json,
    parse_effective_review_decision_set,
    validate_effective_review_decision_set,
    validate_effective_review_decision_set_binding,
)
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
    create_finalized_reviewed_document,
)

from tests.test_review_workspace_finalization_authorization import (
    FINALIZATION_TIMESTAMP,
    _decision,
)
from tests.test_review_workspace_finalization_validation import (
    _element_item,
    _open_question_item,
    _revision,
)
from tests.test_review_workspace_repository_mutations import (
    _bundle,
)


def _decision_set(*items):
    document, version, _ = _bundle()

    revision = _revision(
        *(
            items
            if items
            else (_element_item(),)
        )
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

    reviewed_document = (
        create_finalized_reviewed_document(
            document,
            authorized.finalized_version,
            revision,
            authorized.authorization,
        )
    )

    decision_set = (
        create_effective_review_decision_set(
            reviewed_document,
            revision,
        )
    )

    return reviewed_document, revision, decision_set


def test_schema_constant() -> None:
    assert (
        EFFECTIVE_REVIEW_DECISION_SET_SCHEMA_VERSION
        == "1.0.0"
    )


def test_create_binds_exact_finalized_review() -> None:
    reviewed_document, revision, decision_set = (
        _decision_set()
    )

    assert (
        decision_set.project_id
        == reviewed_document.project_id
    )
    assert (
        decision_set.review_document_id
        == reviewed_document.review_document_id
    )
    assert (
        decision_set.review_document_version_id
        == reviewed_document
        .review_document_version_id
    )
    assert (
        decision_set.review_revision_id
        == revision.review_revision_id
    )
    assert (
        decision_set
        .finalized_reviewed_document_fingerprint
        == reviewed_document.content_fingerprint
    )
    assert (
        decision_set.review_revision_fingerprint
        == revision.revision_fingerprint
    )


def test_finalization_evidence_is_bound() -> None:
    reviewed_document, _, decision_set = (
        _decision_set()
    )

    assert (
        decision_set.finalization_decision_id
        == reviewed_document.finalization_decision_id
    )
    assert (
        decision_set.finalization_decision_fingerprint
        == reviewed_document
        .finalization_decision_fingerprint
    )
    assert (
        decision_set
        .finalization_validation_fingerprint
        == reviewed_document
        .finalization_validation_fingerprint
    )
    assert (
        decision_set.finalized_at
        == reviewed_document.finalized_at
    )


def test_complete_review_items_are_preserved() -> None:
    _, revision, decision_set = _decision_set()

    assert decision_set.effective_decisions == tuple(
        sorted(
            revision.review_items,
            key=lambda item: item.review_item_id,
        )
    )

    item = decision_set.effective_decisions[0]

    assert item.current_content.primary_text == (
        "The system shall preserve source "
        "traceability."
    )
    assert (
        item.effective_review_outcome
        == "accepted_with_modification"
    )


def test_decisions_are_sorted_by_review_item_id() -> None:
    second = _open_question_item(
        review_item_id="RIT-000002",
    )
    first = _element_item(
        review_item_id="RIT-000001",
    )

    _, _, decision_set = _decision_set(
        second,
        first,
    )

    assert tuple(
        item.review_item_id
        for item in decision_set.effective_decisions
    ) == (
        "RIT-000001",
        "RIT-000002",
    )


def test_binding_validator_accepts_exact_chain() -> None:
    reviewed_document, revision, decision_set = (
        _decision_set()
    )

    validate_effective_review_decision_set_binding(
        decision_set,
        reviewed_document,
        revision,
    )


def test_json_round_trip_is_exact() -> None:
    _, _, decision_set = _decision_set()

    text = effective_review_decision_set_to_json(
        decision_set
    )

    assert text.endswith("\n")
    assert (
        effective_review_decision_set_from_json(text)
        == decision_set
    )


def test_dictionary_round_trip_is_exact() -> None:
    _, _, decision_set = _decision_set()

    payload = effective_review_decision_set_to_dict(
        decision_set
    )

    assert (
        parse_effective_review_decision_set(payload)
        == decision_set
    )


def test_serialization_is_deterministic() -> None:
    _, _, decision_set = _decision_set()

    assert effective_review_decision_set_to_json(
        decision_set
    ) == effective_review_decision_set_to_json(
        decision_set
    )


def test_fingerprint_is_deterministic() -> None:
    _, _, decision_set = _decision_set()

    assert (
        calculate_effective_review_decision_set_fingerprint(
            decision_set
        )
        == decision_set.content_fingerprint
    )


def test_tampered_decision_set_is_rejected() -> None:
    _, _, decision_set = _decision_set()

    tampered = replace(
        decision_set,
        finalized_at="2026-08-05T21:00:00Z",
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="fingerprint",
    ):
        validate_effective_review_decision_set(
            tampered
        )


def test_foreign_revision_is_rejected() -> None:
    reviewed_document, _, decision_set = (
        _decision_set()
    )

    foreign_revision = _revision(
        _element_item(),
        revision_id="RVR-000002",
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="same Review Revision",
    ):
        validate_effective_review_decision_set_binding(
            decision_set,
            reviewed_document,
            foreign_revision,
        )


def test_open_effective_decision_is_rejected() -> None:
    _, _, decision_set = _decision_set()

    open_item = _element_item(
        outcome="open",
    )

    provisional = replace(
        decision_set,
        effective_decisions=(open_item,),
        content_fingerprint="0" * 64,
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="non-blocking final outcome",
    ):
        calculate_effective_review_decision_set_fingerprint(
            provisional
        )


def test_duplicate_review_item_ids_are_rejected() -> None:
    _, _, decision_set = _decision_set()

    item = decision_set.effective_decisions[0]

    provisional = replace(
        decision_set,
        effective_decisions=(item, item),
        content_fingerprint="0" * 64,
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="duplicate Review Item IDs",
    ):
        calculate_effective_review_decision_set_fingerprint(
            provisional
        )


def test_unknown_json_field_is_rejected() -> None:
    _, _, decision_set = _decision_set()

    payload = effective_review_decision_set_to_dict(
        decision_set
    )
    payload["unknown"] = True

    with pytest.raises(
        ReviewValidationError,
        match="unknown",
    ):
        parse_effective_review_decision_set(payload)


def test_duplicate_json_key_is_rejected() -> None:
    _, _, decision_set = _decision_set()

    payload = effective_review_decision_set_to_dict(
        decision_set
    )
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
        effective_review_decision_set_from_json(
            duplicate
        )


def test_argument_is_strict() -> None:
    with pytest.raises(
        ReviewValidationError,
        match="EffectiveReviewDecisionSet",
    ):
        validate_effective_review_decision_set(
            object()
        )


def test_type_is_immutable_dataclass() -> None:
    _, _, decision_set = _decision_set()

    assert isinstance(
        decision_set,
        EffectiveReviewDecisionSet,
    )

    with pytest.raises(
        AttributeError,
    ):
        decision_set.project_id = "000002"
