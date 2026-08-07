"""Tests for repository-bound G5.5 Approved Input promotion."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone

import pytest

from modules.approved_input.errors import (
    ApprovedInputPersistenceError,
    ApprovedInputPromotionBlockedError,
    ApprovedInputRecoveryRequiredError,
)
from modules.approved_input.promotion_service import (
    ApprovedInputPromotionResult,
    ApprovedInputPromotionService,
)

from tests.test_approved_input_promotion_eligibility import (
    _element_item,
    _inputs,
    _open_question_item,
)


class _ReviewRepository:
    def __init__(self, document, artifact_set) -> None:
        self.document = document
        self.artifact_set = artifact_set
        self.load_document_calls = 0
        self.load_artifact_calls = 0

    def load_document(self, project_id, review_document_id):
        self.load_document_calls += 1
        assert project_id == self.document.project_id
        assert review_document_id == self.document.review_document_id
        return self.document

    def load_finalized_artifact_set(
        self,
        project_id,
        review_document_id,
        review_document_version_id,
    ):
        self.load_artifact_calls += 1
        assert project_id == self.document.project_id
        assert review_document_id == self.document.review_document_id
        assert (
            review_document_version_id
            == self.artifact_set.reviewed_document.review_document_version_id
        )
        return self.artifact_set


class _SourceRegistry:
    def __init__(self, source, *, sequence=None) -> None:
        self.source = source
        self.sequence = list(sequence or ())
        self.calls = 0

    def load_source(self, project_id, source_id):
        self.calls += 1
        assert project_id == self.source.project_id
        assert source_id == self.source.source_id
        if self.sequence:
            return self.sequence.pop(0)
        return self.source


class _ProcessingRepository:
    def __init__(self, history) -> None:
        self.history = history
        self.calls = 0

    def load_run(self, project_id, processing_run_id):
        self.calls += 1
        assert project_id == self.history.manifest.project_id
        assert (
            processing_run_id
            == self.history.manifest.processing_run_id
        )
        return self.history


class _HumanReviewRepository:
    def __init__(self, decision) -> None:
        self.decision = decision
        self.calls = 0

    def load_decision(self, project_id, decision_id):
        self.calls += 1
        assert project_id == self.decision.project_id
        assert decision_id == self.decision.human_review_decision_id
        return self.decision


class _ApprovedRepository:
    def __init__(self) -> None:
        self.manifests = []
        self.events = []
        self.persist_calls = 0
        self.fail_on_persist_call = None

    def list_manifests(self, project_id):
        assert project_id == "000001"
        return tuple(self.manifests)

    def list_events(self, project_id, approved_input_id=None):
        assert project_id == "000001"
        if approved_input_id is None:
            return tuple(self.events)
        return tuple(
            event
            for event in self.events
            if event.approved_input_id == approved_input_id
        )

    def next_approved_input_event_id(self, project_id):
        assert project_id == "000001"
        return f"AIE-{len(self.events) + 1:06d}"

    def persist_event(self, event):
        self.events.append(event)
        return event

    def persist_manifest(self, manifest):
        self.persist_calls += 1
        if self.persist_calls == self.fail_on_persist_call:
            raise ApprovedInputPersistenceError(
                "simulated persistence failure"
            )
        self.manifests.append(manifest)
        return manifest

    def load_manifest(self, project_id, approved_input_id):
        assert project_id == "000001"
        return next(
            manifest
            for manifest in self.manifests
            if manifest.approved_input_id == approved_input_id
        )


def _clock() -> datetime:
    return datetime(
        2026,
        8,
        7,
        10,
        30,
        tzinfo=timezone.utc,
    )


def _service(*items, terminal_state="awaiting_review"):
    document, artifact_set, source, history, decision = _inputs(
        *items,
        terminal_state=terminal_state,
    )
    approved = _ApprovedRepository()
    service = ApprovedInputPromotionService(
        clock=_clock,
        review_repository=_ReviewRepository(
            document,
            artifact_set,
        ),
        source_registry=_SourceRegistry(source),
        processing_repository=_ProcessingRepository(history),
        human_review_repository=_HumanReviewRepository(decision),
        approved_input_repository=approved,
    )
    return service, approved


def _promote(service):
    return service.promote_finalized_version(
        "000001",
        "RVD-000001",
        "RVV-000001",
    )


def test_assess_eligibility_loads_fresh_authority_snapshots() -> None:
    service, _ = _service()

    assessment = service.assess_eligibility(
        "000001",
        "RVD-000001",
        "RVV-000001",
    )

    assert assessment.eligible_for_promotion is True
    assert assessment.promotable_item_ids == ("RIT-000001",)


def test_promote_creates_one_manifest() -> None:
    service, repository = _service()

    result = _promote(service)

    assert isinstance(result, ApprovedInputPromotionResult)
    assert result.created_approved_input_ids == ("AIN-000001",)
    assert result.reused_approved_input_ids == ()
    assert result.skipped_review_item_ids == ()
    assert len(result.promoted_manifests) == 1
    assert repository.persist_calls == 1
    assert len(repository.manifests) == 1


def test_duplicate_promotion_reuses_existing_manifest() -> None:
    service, repository = _service()

    first = _promote(service)
    second = _promote(service)

    assert first.created_approved_input_ids == ("AIN-000001",)
    assert second.created_approved_input_ids == ()
    assert second.reused_approved_input_ids == ("AIN-000001",)
    assert repository.persist_calls == 1
    assert len(repository.manifests) == 1


def test_legitimate_nonpromotable_item_is_skipped() -> None:
    service, repository = _service(
        _open_question_item(
            outcome="accepted_with_modification"
        )
    )

    result = _promote(service)

    assert result.promoted_manifests == ()
    assert result.created_approved_input_ids == ()
    assert result.skipped_review_item_ids == ("RIT-000002",)
    assert repository.persist_calls == 0


def test_document_level_eligibility_failure_blocks_before_write() -> None:
    service, repository = _service(terminal_state="blocked")

    with pytest.raises(ApprovedInputPromotionBlockedError):
        _promote(service)

    assert repository.persist_calls == 0
    assert repository.manifests == []


def test_authority_is_revalidated_immediately_before_write() -> None:
    document, artifact_set, source, history, decision = _inputs()
    changed_source = replace(
        source,
        source_role="context_only",
    )
    approved = _ApprovedRepository()
    service = ApprovedInputPromotionService(
        clock=_clock,
        review_repository=_ReviewRepository(
            document,
            artifact_set,
        ),
        source_registry=_SourceRegistry(
            source,
            sequence=(source, changed_source),
        ),
        processing_repository=_ProcessingRepository(history),
        human_review_repository=_HumanReviewRepository(decision),
        approved_input_repository=approved,
    )

    with pytest.raises(ApprovedInputPromotionBlockedError):
        _promote(service)

    assert approved.persist_calls == 0
    assert approved.manifests == []


def test_partial_failure_resumes_idempotently() -> None:
    first_item = _element_item(review_item_id="RIT-000001")
    second_item = _element_item(review_item_id="RIT-000002")
    service, repository = _service(first_item, second_item)
    repository.fail_on_persist_call = 2

    with pytest.raises(ApprovedInputRecoveryRequiredError):
        _promote(service)

    assert tuple(
        manifest.approved_input_id
        for manifest in repository.manifests
    ) == ("AIN-000001",)

    repository.fail_on_persist_call = None
    recovered = _promote(service)

    assert recovered.reused_approved_input_ids == ("AIN-000001",)
    assert recovered.created_approved_input_ids == ("AIN-000002",)
    assert tuple(
        manifest.approved_input_id
        for manifest in repository.manifests
    ) == (
        "AIN-000001",
        "AIN-000002",
    )
