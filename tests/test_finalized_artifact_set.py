"""Tests for finalized Review Artifact Set integrity."""

from __future__ import annotations

from dataclasses import replace
import json

import pytest

from modules.review_workspace.effective_decisions_manifest import (
    effective_review_decision_set_to_json,
)
from modules.review_workspace.errors import (
    ReviewIntegrityError,
    ReviewValidationError,
)
from modules.review_workspace.finalized_artifact_set import (
    FINALIZED_REVIEW_ARTIFACT_ORDER,
    FINALIZED_REVIEW_ARTIFACT_SET_SCHEMA_VERSION,
    FinalizedReviewArtifact,
    FinalizedReviewArtifactSet,
    calculate_finalized_review_artifact_fingerprint,
    calculate_finalized_review_artifact_set_fingerprint,
    create_finalized_review_artifact_set,
    validate_finalized_review_artifact_set,
)
from modules.review_workspace.reviewed_document_manifest import (
    finalized_reviewed_document_from_json,
    finalized_reviewed_document_to_json,
)
from modules.review_workspace.reviewed_report_renderer import (
    calculate_reviewed_report_fingerprint,
    reviewed_report_to_markdown,
)

from tests.test_review_workspace_finalization_validation import (
    _element_item,
)
from tests.test_reviewed_report_renderer import (
    _report,
)


def _artifact_set(*items):
    (
        reviewed_document,
        _,
        effective_decisions,
        reviewed_report,
    ) = _report(*items)

    artifact_set = create_finalized_review_artifact_set(
        reviewed_document,
        effective_decisions,
        reviewed_report,
    )

    return (
        reviewed_document,
        effective_decisions,
        reviewed_report,
        artifact_set,
    )


def test_contract_constants() -> None:
    assert (
        FINALIZED_REVIEW_ARTIFACT_SET_SCHEMA_VERSION
        == "1.0.0"
    )
    assert FINALIZED_REVIEW_ARTIFACT_ORDER == (
        "reviewed_document.json",
        "effective_decisions.json",
        "reviewed_report.md",
    )


def test_create_binds_exact_finalized_sources() -> None:
    (
        reviewed_document,
        effective_decisions,
        reviewed_report,
        artifact_set,
    ) = _artifact_set()

    assert isinstance(
        artifact_set,
        FinalizedReviewArtifactSet,
    )
    assert (
        artifact_set.reviewed_document
        is reviewed_document
    )
    assert (
        artifact_set.effective_decisions
        is effective_decisions
    )
    assert artifact_set.reviewed_report is reviewed_report


def test_create_contains_exactly_three_ordered_artifacts() -> None:
    *_, artifact_set = _artifact_set()

    assert tuple(
        artifact.filename
        for artifact in artifact_set.artifacts
    ) == FINALIZED_REVIEW_ARTIFACT_ORDER
    assert len(artifact_set.artifacts) == 3
    assert all(
        artifact.filename != "artifact_set.json"
        for artifact in artifact_set.artifacts
    )


def test_artifact_bytes_match_exact_serializers() -> None:
    (
        reviewed_document,
        effective_decisions,
        reviewed_report,
        artifact_set,
    ) = _artifact_set()

    expected_contents = (
        finalized_reviewed_document_to_json(
            reviewed_document
        ).encode("utf-8"),
        effective_review_decision_set_to_json(
            effective_decisions
        ).encode("utf-8"),
        reviewed_report_to_markdown(
            reviewed_report
        ).encode("utf-8"),
    )

    assert tuple(
        artifact.content
        for artifact in artifact_set.artifacts
    ) == expected_contents


def test_each_artifact_binds_its_exact_bytes() -> None:
    *_, artifact_set = _artifact_set()

    for artifact in artifact_set.artifacts:
        assert (
            artifact.byte_fingerprint
            == calculate_finalized_review_artifact_fingerprint(
                artifact.content
            )
        )


def test_artifact_set_fingerprint_is_deterministic() -> None:
    *_, first = _artifact_set()
    *_, second = _artifact_set()

    assert (
        first.artifact_set_fingerprint
        == second.artifact_set_fingerprint
    )
    assert (
        calculate_finalized_review_artifact_set_fingerprint(
            first
        )
        == first.artifact_set_fingerprint
    )


def test_different_finalizations_have_different_set_fingerprints() -> None:
    *_, first = _artifact_set()
    *_, second = _artifact_set(
        _element_item(
            review_item_id="RIT-000002",
        )
    )

    assert (
        first.artifact_set_fingerprint
        != second.artifact_set_fingerprint
    )


def test_exact_artifact_set_is_valid() -> None:
    *_, artifact_set = _artifact_set()

    validate_finalized_review_artifact_set(
        artifact_set
    )


def test_mixed_effective_decisions_are_rejected() -> None:
    (
        reviewed_document,
        _,
        _,
        reviewed_report,
    ) = _report()

    (
        _,
        _,
        foreign_effective_decisions,
        _,
    ) = _report(
        _element_item(
            review_item_id="RIT-000002",
        )
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="exact Finalized Reviewed Document",
    ):
        create_finalized_review_artifact_set(
            reviewed_document,
            foreign_effective_decisions,
            reviewed_report,
        )


def test_mixed_reviewed_report_is_rejected() -> None:
    (
        reviewed_document,
        _,
        effective_decisions,
        _,
    ) = _report()

    *_, foreign_report = _report(
        _element_item(
            review_item_id="RIT-000002",
        )
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="exact deterministic rendering",
    ):
        create_finalized_review_artifact_set(
            reviewed_document,
            effective_decisions,
            foreign_report,
        )


def test_recomputed_tampered_report_is_rejected() -> None:
    (
        reviewed_document,
        effective_decisions,
        reviewed_report,
        _,
    ) = _artifact_set()

    markdown = reviewed_report.markdown.replace(
        "# Reviewed Report\n",
        "# Reviewed Report\n\nTampered presentation.\n",
        1,
    )
    tampered_report = replace(
        reviewed_report,
        markdown=markdown,
        content_fingerprint=(
            calculate_reviewed_report_fingerprint(
                markdown
            )
        ),
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="exact deterministic rendering",
    ):
        create_finalized_review_artifact_set(
            reviewed_document,
            effective_decisions,
            tampered_report,
        )


def test_wrong_artifact_order_is_rejected() -> None:
    *_, artifact_set = _artifact_set()

    tampered = replace(
        artifact_set,
        artifacts=(
            artifact_set.artifacts[1],
            artifact_set.artifacts[0],
            artifact_set.artifacts[2],
        ),
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="exact artifact order",
    ):
        validate_finalized_review_artifact_set(
            tampered
        )


def test_missing_artifact_is_rejected() -> None:
    *_, artifact_set = _artifact_set()

    tampered = replace(
        artifact_set,
        artifacts=artifact_set.artifacts[:-1],
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="exactly three artifacts",
    ):
        validate_finalized_review_artifact_set(
            tampered
        )


def test_extra_artifact_is_rejected() -> None:
    *_, artifact_set = _artifact_set()

    extra_content = b"not persisted by G4.2d\n"
    extra_artifact = FinalizedReviewArtifact(
        filename="artifact_set.json",
        content=extra_content,
        byte_fingerprint=(
            calculate_finalized_review_artifact_fingerprint(
                extra_content
            )
        ),
    )
    tampered = replace(
        artifact_set,
        artifacts=(
            *artifact_set.artifacts,
            extra_artifact,
        ),
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="exactly three artifacts",
    ):
        validate_finalized_review_artifact_set(
            tampered
        )


def test_duplicate_artifact_is_rejected() -> None:
    *_, artifact_set = _artifact_set()

    tampered = replace(
        artifact_set,
        artifacts=(
            artifact_set.artifacts[0],
            artifact_set.artifacts[0],
            artifact_set.artifacts[2],
        ),
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="exact artifact order",
    ):
        validate_finalized_review_artifact_set(
            tampered
        )


def test_tampered_artifact_bytes_are_rejected() -> None:
    *_, artifact_set = _artifact_set()

    first = artifact_set.artifacts[0]
    tampered_artifact = replace(
        first,
        content=first.content + b" ",
    )
    tampered = replace(
        artifact_set,
        artifacts=(
            tampered_artifact,
            *artifact_set.artifacts[1:],
        ),
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="byte fingerprint",
    ):
        validate_finalized_review_artifact_set(
            tampered
        )


def test_semantically_valid_reserialized_json_is_rejected() -> None:
    (
        reviewed_document,
        _,
        _,
        artifact_set,
    ) = _artifact_set()

    first = artifact_set.artifacts[0]
    payload = json.loads(
        first.content.decode("utf-8")
    )
    reserialized = (
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")

    assert reserialized != first.content
    assert (
        finalized_reviewed_document_from_json(
            reserialized.decode("utf-8")
        )
        == reviewed_document
    )

    tampered_artifact = replace(
        first,
        content=reserialized,
        byte_fingerprint=(
            calculate_finalized_review_artifact_fingerprint(
                reserialized
            )
        ),
    )
    tampered = replace(
        artifact_set,
        artifacts=(
            tampered_artifact,
            *artifact_set.artifacts[1:],
        ),
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="exact deterministic bytes",
    ):
        validate_finalized_review_artifact_set(
            tampered
        )


def test_tampered_artifact_set_fingerprint_is_rejected() -> None:
    *_, artifact_set = _artifact_set()

    tampered = replace(
        artifact_set,
        artifact_set_fingerprint="f" * 64,
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="Artifact-set fingerprint",
    ):
        validate_finalized_review_artifact_set(
            tampered
        )


def test_artifact_content_argument_is_strict() -> None:
    with pytest.raises(
        ReviewValidationError,
        match="must be bytes",
    ):
        calculate_finalized_review_artifact_fingerprint(
            bytearray()
        )


def test_artifact_set_argument_is_strict() -> None:
    with pytest.raises(
        ReviewValidationError,
        match="FinalizedReviewArtifactSet",
    ):
        validate_finalized_review_artifact_set(
            object()
        )


def test_artifacts_collection_must_be_a_tuple() -> None:
    *_, artifact_set = _artifact_set()

    tampered = replace(
        artifact_set,
        artifacts=list(artifact_set.artifacts),
    )

    with pytest.raises(
        ReviewValidationError,
        match="must be a tuple",
    ):
        validate_finalized_review_artifact_set(
            tampered
        )


def test_artifact_content_must_remain_bytes() -> None:
    *_, artifact_set = _artifact_set()

    first = replace(
        artifact_set.artifacts[0],
        content="not bytes",
    )
    tampered = replace(
        artifact_set,
        artifacts=(
            first,
            *artifact_set.artifacts[1:],
        ),
    )

    with pytest.raises(
        ReviewValidationError,
        match="must be bytes",
    ):
        validate_finalized_review_artifact_set(
            tampered
        )


def test_contract_types_are_immutable() -> None:
    *_, artifact_set = _artifact_set()
    artifact = artifact_set.artifacts[0]

    with pytest.raises(AttributeError):
        artifact.filename = "changed.json"

    with pytest.raises(AttributeError):
        artifact_set.artifact_set_fingerprint = "f" * 64
