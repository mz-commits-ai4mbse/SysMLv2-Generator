"""Tests for G6.5 promotion and immutable authority orchestration."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from modules.review_workspace.errors import (
    ReviewIntegrityError,
    ReviewValidationError,
)
from modules.review_workspace.workflow_service import (
    ReviewApprovalWorkflowService,
)


def _assessment(*, eligible=True):
    return SimpleNamespace(
        project_id="123456",
        review_document_id="RVD-000001",
        review_document_version_id="RVV-000001",
        review_revision_id="RVR-000001",
        finalized_artifact_set_fingerprint="a" * 64,
        eligible_for_promotion=eligible,
    )


class FakePromotionService:
    def __init__(
        self,
        *,
        assessment=None,
        result=None,
    ):
        self.assessment = (
            assessment
            if assessment is not None
            else _assessment()
        )
        self.result = result
        self.assess_calls = []
        self.promote_calls = []

    def assess_eligibility(self, *args):
        self.assess_calls.append(args)
        return self.assessment

    def promote_finalized_version(self, *args):
        self.promote_calls.append(args)
        return self.result


class FakeApprovedRepository:
    def __init__(
        self,
        *,
        scan=None,
        active=(),
    ):
        self.scan = scan
        self.active = tuple(active)

    def scan_project(self, project_id):
        return self.scan

    def list_active_approved_inputs(self, project_id):
        return self.active


def test_promotion_preview_requires_finalized_review_version():
    service = object.__new__(
        ReviewApprovalWorkflowService
    )
    service._review_repository = SimpleNamespace(
        load_version=lambda *args: SimpleNamespace(
            version_state="draft",
        )
    )
    service._promotion_service = FakePromotionService()

    with pytest.raises(
        ReviewValidationError,
        match="finalized",
    ):
        service.promotion_preview(
            "123456",
            "RVD-000001",
            "RVV-000001",
        )


def test_promotion_preview_delegates_fresh_g5_assessment_and_binds_revision():
    promotion = FakePromotionService()
    service = object.__new__(
        ReviewApprovalWorkflowService
    )
    service._review_repository = SimpleNamespace(
        load_version=lambda *args: SimpleNamespace(
            version_state="finalized",
            finalized_revision_id="RVR-000001",
        )
    )
    service._promotion_service = promotion

    result = service.promotion_preview(
        "123456",
        "RVD-000001",
        "RVV-000001",
    )

    assert result is promotion.assessment
    assert promotion.assess_calls == [
        (
            "123456",
            "RVD-000001",
            "RVV-000001",
        )
    ]


def test_traceability_derives_state_only_from_manifests_and_events():
    manifest = SimpleNamespace(
        approved_input_id="AIN-000001",
        approved_input_kind="element_statement",
        stable_subject_key="requirement:traceability",
        canonical_content=SimpleNamespace(
            title="Preserve traceability",
            primary_text="The system shall preserve traceability.",
        ),
        review_document_id="RVD-000001",
        review_document_version_id="RVV-000001",
        review_revision_id="RVR-000001",
        review_item_id="RIT-000001",
        review_item_kind="element",
        review_item_fingerprint="a" * 64,
        finalized_artifact_set_fingerprint="b" * 64,
        finalization_decision_id="HRD-000001",
        finalization_decision_fingerprint="c" * 64,
        finalization_validation_fingerprint="d" * 64,
        source_id="SRC-000001",
        source_sha256="e" * 64,
        processing_run_id="RUN-000001",
        attempt_id="ATT-000001",
        primary_artifact_reference=SimpleNamespace(
            artifact_id="ART-000001",
        ),
        supporting_artifact_references=(
            SimpleNamespace(
                artifact_id="ART-000002",
            ),
        ),
        proposal_references=("AGENT-001:CAND-001",),
        created_at="2026-08-08T13:00:00Z",
        content_fingerprint="f" * 64,
    )
    event = SimpleNamespace(
        approved_input_event_id="AIE-000001",
        approved_input_id="AIN-000001",
        event_type="revoked",
        previous_authority_state="active",
        next_authority_state="revoked",
        reason_code="review_item_withdrawn",
        rationale="Withdrawn in successor review.",
        actor_identity="promotion-service",
        successor_approved_input_id=None,
        causal_review_document_id="RVD-000001",
        causal_review_document_version_id="RVV-000002",
        causal_review_revision_id="RVR-000002",
        causal_finalization_decision_id="HRD-000002",
        causal_finalization_decision_fingerprint="1" * 64,
        occurred_at="2026-08-08T14:00:00Z",
        previous_event_fingerprint=None,
        event_fingerprint="2" * 64,
    )
    snapshot = SimpleNamespace(
        manifest=manifest,
        authority_state="revoked",
        latest_event_fingerprint="2" * 64,
    )

    service = object.__new__(
        ReviewApprovalWorkflowService
    )
    service._review_repository = SimpleNamespace(
        load_document=lambda *args: SimpleNamespace()
    )
    service._approved_input_repository = (
        FakeApprovedRepository(
            scan=SimpleNamespace(
                manifests=(manifest,),
                events=(event,),
                issues=(),
            )
        )
    )
    calls = []

    def derive(manifests, events):
        calls.append((manifests, events))
        return (snapshot,)

    service._authority_deriver = derive

    result = service.approved_input_traceability(
        "123456",
        "RVD-000001",
    )

    assert calls == [
        (
            (manifest,),
            (event,),
        )
    ]
    assert result[0].authority_state == "revoked"
    assert result[0].latest_event_fingerprint == "2" * 64
    assert (
        result[0].lifecycle_events[0]
        .approved_input_event_id
        == "AIE-000001"
    )


def test_traceability_fails_closed_on_repository_issues():
    service = object.__new__(
        ReviewApprovalWorkflowService
    )
    service._review_repository = SimpleNamespace(
        load_document=lambda *args: SimpleNamespace()
    )
    service._approved_input_repository = (
        FakeApprovedRepository(
            scan=SimpleNamespace(
                manifests=(),
                events=(),
                issues=(SimpleNamespace(code="broken"),),
            )
        )
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="integrity",
    ):
        service.approved_input_traceability(
            "123456",
            "RVD-000001",
        )


def test_promote_reloads_traceability_and_checks_phase_h_read_contract():
    promotion_result = SimpleNamespace(
        project_id="123456",
        review_document_id="RVD-000001",
        review_document_version_id="RVV-000001",
        finalized_artifact_set_fingerprint="a" * 64,
        created_approved_input_ids=("AIN-000001",),
        reused_approved_input_ids=(),
        skipped_review_item_ids=(),
        lifecycle_event_ids=(),
    )
    promotion = FakePromotionService(
        result=promotion_result
    )
    active_manifest = SimpleNamespace(
        approved_input_id="AIN-000001",
        review_document_id="RVD-000001",
    )
    service = object.__new__(
        ReviewApprovalWorkflowService
    )
    service._promotion_service = promotion
    service._review_repository = SimpleNamespace(
        load_version=lambda *args: SimpleNamespace(
            version_state="finalized",
            finalized_revision_id="RVR-000001",
        )
    )
    service.workspace_view = lambda *args: SimpleNamespace(
        marker="reloaded",
    )
    trace = SimpleNamespace(
        approved_input_id="AIN-000001",
        is_active=True,
        lifecycle_events=(),
    )
    service.approved_input_traceability = (
        lambda *args: (trace,)
    )
    service._approved_input_repository = (
        FakeApprovedRepository(
            active=(active_manifest,),
        )
    )

    result = service.promote_review_version(
        "123456",
        "RVD-000001",
        "RVV-000001",
    )

    assert promotion.promote_calls == [
        (
            "123456",
            "RVD-000001",
            "RVV-000001",
        )
    ]
    assert result.workspace.marker == "reloaded"
    assert result.created_approved_input_ids == (
        "AIN-000001",
    )
    assert result.traceability == (trace,)
