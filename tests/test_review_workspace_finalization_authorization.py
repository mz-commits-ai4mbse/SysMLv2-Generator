"""Tests for exact Review Document finalization authorization."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

import pytest

from modules.human_review import (
    HumanReviewRepository,
    create_human_review_decision,
)
from modules.human_review.errors import (
    HumanReviewIntegrityError,
    HumanReviewReferenceError,
)
from modules.project_workspace import (
    ProjectWorkspace,
)
from modules.review_workspace.errors import (
    ReviewFinalizationBlockedError,
    ReviewIntegrityError,
    ReviewValidationError,
)
from modules.review_workspace.finalization_authorization import (
    authorize_persisted_review_document_finalization,
    authorize_review_document_finalization,
    validate_review_finalization_authorization,
)
from modules.review_workspace.finalization_validation import (
    assess_review_document_finalization,
    create_review_document_finalization_target,
)
from modules.review_workspace.version_manifest import (
    create_review_document_version,
)

from tests.test_review_workspace_finalization_validation import (
    _element_item,
    _revision,
)
from tests.test_review_workspace_repository_mutations import (
    _bundle,
)


DECISION_TIMESTAMP = "2026-08-05T19:05:00Z"
FINALIZATION_TIMESTAMP = "2026-08-05T19:10:00Z"


def _clock() -> datetime:
    return datetime(
        2026,
        8,
        5,
        19,
        5,
        tzinfo=timezone.utc,
    )


def _inputs():
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

    return (
        document,
        version,
        revision,
        assessment,
    )


def _decision(
    assessment,
    *,
    target=None,
    decision: str = "confirm",
    reviewer_identity: str = "moritz",
    rationale: str | None = None,
    decision_id: str = "HRD-000001",
):
    if target is None:
        target = (
            create_review_document_finalization_target(
                assessment
            )
        )

    return create_human_review_decision(
        project_id=assessment.project_id,
        human_review_decision_id=decision_id,
        target=target,
        review_mode="detailed_review",
        decision=decision,
        reviewer_identity=reviewer_identity,
        rationale=rationale,
        timestamp=DECISION_TIMESTAMP,
    )


def _repository(
    tmp_path: Path,
) -> HumanReviewRepository:
    root = tmp_path / "projects"

    workspace = ProjectWorkspace(
        root=root,
        id_generator=lambda: "000001",
        clock=_clock,
    )
    workspace.create_project(
        "Finalization Authorization Test"
    )

    return HumanReviewRepository(
        root=root,
        clock=_clock,
    )


def test_exact_decision_authorizes_finalization() -> None:
    (
        _,
        version,
        revision,
        assessment,
    ) = _inputs()

    result = authorize_review_document_finalization(
        version,
        revision,
        assessment,
        _decision(assessment),
        timestamp=FINALIZATION_TIMESTAMP,
    )

    assert (
        result.finalized_version.version_state
        == "finalized"
    )
    assert (
        result.finalized_version
        .finalized_revision_id
        == revision.review_revision_id
    )
    assert (
        result.finalized_version
        .finalization_decision_id
        == "HRD-000001"
    )


def test_authorization_binds_all_exact_fingerprints() -> None:
    (
        _,
        version,
        revision,
        assessment,
    ) = _inputs()
    decision = _decision(assessment)

    result = authorize_review_document_finalization(
        version,
        revision,
        assessment,
        decision,
        timestamp=FINALIZATION_TIMESTAMP,
    )

    authorization = result.authorization

    assert (
        authorization
        .draft_version_content_fingerprint
        == version.content_fingerprint
    )
    assert (
        authorization.review_revision_fingerprint
        == revision.revision_fingerprint
    )
    assert (
        authorization.validation_fingerprint
        == assessment.validation_fingerprint
    )
    assert (
        authorization
        .human_review_decision_fingerprint
        == decision.decision_fingerprint
    )
    assert (
        authorization
        .finalized_version_content_fingerprint
        == result.finalized_version
        .content_fingerprint
    )


def test_authorization_fingerprint_is_valid() -> None:
    _, version, revision, assessment = _inputs()

    result = authorize_review_document_finalization(
        version,
        revision,
        assessment,
        _decision(assessment),
        timestamp=FINALIZATION_TIMESTAMP,
    )

    assert (
        validate_review_finalization_authorization(
            result.authorization
        )
        is None
    )


def test_tampered_authorization_is_rejected() -> None:
    _, version, revision, assessment = _inputs()

    result = authorize_review_document_finalization(
        version,
        revision,
        assessment,
        _decision(assessment),
        timestamp=FINALIZATION_TIMESTAMP,
    )

    tampered = replace(
        result.authorization,
        reviewer_identity="other-reviewer",
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="fingerprint",
    ):
        validate_review_finalization_authorization(
            tampered
        )


def test_stale_decision_content_fingerprint_is_rejected() -> None:
    _, version, revision, assessment = _inputs()
    target = (
        create_review_document_finalization_target(
            assessment
        )
    )
    stale_target = replace(
        target,
        target_content_fingerprint="c" * 64,
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="target content fingerprint",
    ):
        authorize_review_document_finalization(
            version,
            revision,
            assessment,
            _decision(
                assessment,
                target=stale_target,
            ),
            timestamp=FINALIZATION_TIMESTAMP,
        )


def test_stale_validation_fingerprint_is_rejected() -> None:
    _, version, revision, assessment = _inputs()
    target = (
        create_review_document_finalization_target(
            assessment
        )
    )
    stale_target = replace(
        target,
        reference_validation_fingerprint=(
            "d" * 64
        ),
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="validation fingerprint",
    ):
        authorize_review_document_finalization(
            version,
            revision,
            assessment,
            _decision(
                assessment,
                target=stale_target,
            ),
            timestamp=FINALIZATION_TIMESTAMP,
        )


def test_wrong_version_target_is_rejected() -> None:
    _, version, revision, assessment = _inputs()
    target = (
        create_review_document_finalization_target(
            assessment
        )
    )
    foreign_target = replace(
        target,
        target_id="RVV-000002",
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="selected Review Document Version",
    ):
        authorize_review_document_finalization(
            version,
            revision,
            assessment,
            _decision(
                assessment,
                target=foreign_target,
            ),
            timestamp=FINALIZATION_TIMESTAMP,
        )


def test_non_confirming_decision_is_rejected() -> None:
    _, version, revision, assessment = _inputs()

    with pytest.raises(
        ReviewFinalizationBlockedError,
        match="confirm",
    ):
        authorize_review_document_finalization(
            version,
            revision,
            assessment,
            _decision(
                assessment,
                decision="request_changes",
                rationale=(
                    "Additional review is required."
                ),
            ),
            timestamp=FINALIZATION_TIMESTAMP,
        )


def test_blocked_assessment_cannot_be_authorized() -> None:
    document, version, _ = _bundle()
    revision = _revision(
        _element_item(outcome="open")
    )
    assessment = (
        assess_review_document_finalization(
            document,
            version,
            revision,
        )
    )
    target = (
        create_review_document_finalization_target(
            assessment
        )
    )

    with pytest.raises(
        ReviewFinalizationBlockedError,
        match="review_item_open",
    ):
        authorize_review_document_finalization(
            version,
            revision,
            assessment,
            _decision(
                assessment,
                target=target,
                decision="request_changes",
                rationale=(
                    "Open Review Items remain."
                ),
            ),
            timestamp=FINALIZATION_TIMESTAMP,
        )


def test_stale_version_assessment_is_rejected() -> None:
    _, version, revision, assessment = _inputs()

    changed_version = (
        create_review_document_version(
            project_id=version.project_id,
            review_document_id=(
                version.review_document_id
            ),
            review_document_version_id=(
                version.review_document_version_id
            ),
            version_number=version.version_number,
            predecessor_version_id=(
                version.predecessor_version_id
            ),
            reopen_reason=version.reopen_reason,
            opened_by="different-reviewer",
            timestamp=version.opened_at,
            head_revision_id=(
                version.head_revision_id
            ),
        )
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="content fingerprint is stale",
    ):
        authorize_review_document_finalization(
            changed_version,
            revision,
            assessment,
            _decision(assessment),
            timestamp=FINALIZATION_TIMESTAMP,
        )


def test_repository_accepts_finalization_target_filter(
    tmp_path: Path,
) -> None:
    repository = _repository(tmp_path)
    _, _, _, assessment = _inputs()
    target = (
        create_review_document_finalization_target(
            assessment
        )
    )

    decision = repository.record_decision(
        "000001",
        target,
        review_mode="detailed_review",
        decision="confirm",
        reviewer_identity="moritz",
    )

    assert repository.list_decisions(
        "000001",
        target_type=(
            "review_document_finalization"
        ),
        target_id="RVV-000001",
    ) == (
        decision,
    )


def test_persisted_exact_confirmation_authorizes(
    tmp_path: Path,
) -> None:
    repository = _repository(tmp_path)
    _, version, revision, assessment = _inputs()
    target = (
        create_review_document_finalization_target(
            assessment
        )
    )

    decision = repository.record_decision(
        "000001",
        target,
        review_mode="detailed_review",
        decision="confirm",
        reviewer_identity="moritz",
    )

    result = (
        authorize_persisted_review_document_finalization(
            version,
            revision,
            assessment,
            repository,
            timestamp=FINALIZATION_TIMESTAMP,
        )
    )

    assert (
        result.authorization
        .human_review_decision_id
        == decision.human_review_decision_id
    )


def test_missing_persisted_decision_blocks(
    tmp_path: Path,
) -> None:
    repository = _repository(tmp_path)
    _, version, revision, assessment = _inputs()

    with pytest.raises(
        HumanReviewReferenceError,
        match="No Human Review Decision",
    ):
        authorize_persisted_review_document_finalization(
            version,
            revision,
            assessment,
            repository,
            timestamp=FINALIZATION_TIMESTAMP,
        )


def test_latest_exact_rejection_blocks(
    tmp_path: Path,
) -> None:
    repository = _repository(tmp_path)
    _, version, revision, assessment = _inputs()
    target = (
        create_review_document_finalization_target(
            assessment
        )
    )

    repository.record_decision(
        "000001",
        target,
        review_mode="detailed_review",
        decision="confirm",
        reviewer_identity="moritz",
    )
    repository.record_decision(
        "000001",
        target,
        review_mode="detailed_review",
        decision="reject",
        reviewer_identity="moritz",
        rationale=(
            "Finalization has been withdrawn."
        ),
    )

    with pytest.raises(
        HumanReviewIntegrityError,
        match="does not confirm",
    ):
        authorize_persisted_review_document_finalization(
            version,
            revision,
            assessment,
            repository,
            timestamp=FINALIZATION_TIMESTAMP,
        )


def test_repository_argument_is_strict() -> None:
    _, version, revision, assessment = _inputs()

    with pytest.raises(
        ReviewValidationError,
        match="HumanReviewRepository",
    ):
        authorize_persisted_review_document_finalization(
            version,
            revision,
            assessment,
            object(),
            timestamp=FINALIZATION_TIMESTAMP,
        )
