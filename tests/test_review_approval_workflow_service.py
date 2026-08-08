"""Tests for the G6.1 Review Approval read-only workflow service."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from modules.review_workspace import (
    ReviewApprovalWorkflowService,
    ReviewIntegrityError,
    ReviewReferenceError,
)


class FakeWorkspace:
    def __init__(self, error=None):
        self.error = error

    def load_project(self, project_id):
        if self.error is not None:
            raise self.error
        return SimpleNamespace(project_id=project_id)


class FakeProcessingSummaryService:
    def __init__(self, source_scan, processing_scan):
        self.source_scan = source_scan
        self.processing_scan = processing_scan

    def collect_scans(self, project_id):
        return self.source_scan, self.processing_scan


class FakeReviewRepository:
    def __init__(self, scan):
        self.scan = scan
        self.calls = []

    def scan_project(self, project_id):
        return self.scan

    def load_document(self, project_id, document_id):
        matches = [
            item for item in self.scan.documents
            if item.review_document_id == document_id
        ]
        if len(matches) != 1:
            raise RuntimeError("document unavailable")
        return matches[0]

    def load_version(self, project_id, document_id, version_id):
        matches = [
            item for item in self.scan.versions
            if item.review_document_id == document_id
            and item.review_document_version_id == version_id
        ]
        if len(matches) != 1:
            raise RuntimeError("version unavailable")
        return matches[0]

    def load_revision(self, project_id, document_id, version_id, revision_id):
        self.calls.append((document_id, version_id, revision_id))
        matches = [
            item for item in self.scan.revisions
            if item.review_document_id == document_id
            and item.review_document_version_id == version_id
            and item.review_revision_id == revision_id
        ]
        if len(matches) != 1:
            raise RuntimeError("revision unavailable")
        return matches[0]


class FakeHumanReviewRepository:
    def __init__(self, scan):
        self.scan = scan

    def scan_decisions(self, project_id):
        return self.scan


class FakeApprovedInputRepository:
    def __init__(self, scan):
        self.scan = scan

    def scan_project(self, project_id):
        return self.scan


class FakePromotionService:
    def __init__(self, assessment=None):
        self.assessment = assessment
        self.calls = []

    def assess_eligibility(self, project_id, document_id, version_id):
        self.calls.append((project_id, document_id, version_id))
        return self.assessment


def source():
    return SimpleNamespace(
        source_id="SRC-000001",
        original_filename="requirements.md",
    )


def summary(pending_review=True):
    return SimpleNamespace(
        source_id="SRC-000001",
        current_processing_run_id="PRN-000001",
        pending_review=pending_review,
        run_state="awaiting_review",
        latest_attempt_id="ATT-000001",
    )


def history():
    return SimpleNamespace(
        manifest=SimpleNamespace(
            source_id="SRC-000001",
            processing_run_id="PRN-000001",
        )
    )


def document(document_id="RVD-000001"):
    return SimpleNamespace(
        project_id="123456",
        review_document_id=document_id,
        processing_run_id="PRN-000001",
        source_id="SRC-000001",
        attempt_id="ATT-000001",
    )


def version(
    version_id="RVV-000001",
    version_number=1,
    state="draft",
    revision_id="RVR-000001",
):
    return SimpleNamespace(
        project_id="123456",
        review_document_id="RVD-000001",
        review_document_version_id=version_id,
        version_number=version_number,
        version_state=state,
        head_revision_id=revision_id,
        finalized_revision_id=(revision_id if state == "finalized" else None),
    )


def revision(
    version_id="RVV-000001",
    revision_id="RVR-000001",
    outcome="open",
):
    return SimpleNamespace(
        project_id="123456",
        review_document_id="RVD-000001",
        review_document_version_id=version_id,
        review_revision_id=revision_id,
        review_items=(
            SimpleNamespace(
                review_item_id="RIT-000001",
                effective_review_outcome=outcome,
            ),
        ),
    )


def scan_sources(sources=(), issues=()):
    return SimpleNamespace(
        valid_sources=tuple(sources),
        source_issues=tuple(issues),
    )


def scan_processing(histories=(), issues=()):
    return SimpleNamespace(
        run_histories=tuple(histories),
        issues=tuple(issues),
    )


def scan_review(documents=(), versions=(), revisions=(), actions=(), issues=()):
    return SimpleNamespace(
        documents=tuple(documents),
        versions=tuple(versions),
        revisions=tuple(revisions),
        scoped_actions=tuple(actions),
        issues=tuple(issues),
    )


def scan_human(decisions=(), issues=()):
    return SimpleNamespace(decisions=tuple(decisions), issues=tuple(issues))


def scan_approved(manifests=(), events=(), issues=()):
    return SimpleNamespace(
        manifests=tuple(manifests),
        events=tuple(events),
        issues=tuple(issues),
    )


def finalization_assessment(eligible=False):
    return SimpleNamespace(
        eligible_for_finalization=eligible,
        blocking_issue_codes=(
            () if eligible else ("review_item_open:RIT-000001",)
        ),
    )


def promotion_assessment(eligible=True):
    return SimpleNamespace(
        eligible_for_promotion=eligible,
        blocking_issue_codes=(() if eligible else ("blocked",)),
        promotable_item_ids=("RIT-000001",) if eligible else (),
    )


def make_service(
    *,
    source_scan=None,
    processing_scan=None,
    source_summaries=(),
    review_scan=None,
    human_scan=None,
    approved_scan=None,
    finalization=None,
    promotion=None,
    authority=(),
):
    source_scan = source_scan or scan_sources()
    processing_scan = processing_scan or scan_processing()
    review_scan = review_scan or scan_review()
    human_scan = human_scan or scan_human()
    approved_scan = approved_scan or scan_approved()
    promotion_service = FakePromotionService(promotion)
    repository = FakeReviewRepository(review_scan)
    service = ReviewApprovalWorkflowService(
        root="unused",
        workspace=FakeWorkspace(),
        source_registry=SimpleNamespace(),
        processing_summary_service=FakeProcessingSummaryService(
            source_scan,
            processing_scan,
        ),
        review_repository=repository,
        human_review_repository=FakeHumanReviewRepository(human_scan),
        approved_input_repository=FakeApprovedInputRepository(approved_scan),
        promotion_service=promotion_service,
        source_summary_deriver=(
            lambda project_id, sources, processing: tuple(source_summaries)
        ),
        run_state_deriver=(
            lambda item: SimpleNamespace(
                pending_review=True,
                run_state="awaiting_review",
                latest_attempt_id="ATT-000001",
            )
        ),
        finalization_assessor=(
            lambda doc, ver, rev: (
                finalization
                if finalization is not None
                else finalization_assessment(False)
            )
        ),
        authority_deriver=lambda manifests, events: tuple(authority),
    )
    return service, repository, promotion_service


def test_pending_review_without_workspace_is_queued_for_creation():
    service, _, _ = make_service(
        source_scan=scan_sources((source(),)),
        processing_scan=scan_processing((history(),)),
        source_summaries=(summary(),),
    )
    view = service.project_view("123456")
    assert len(view.items) == 1
    item = view.items[0]
    assert item.original_filename == "requirements.md"
    assert item.review_document_id is None
    assert item.workflow_status == "awaiting_workspace"
    assert item.pending_review is True


def test_draft_review_projects_finalization_state_without_promotion_call():
    service, _, promotion_service = make_service(
        source_scan=scan_sources((source(),)),
        processing_scan=scan_processing((history(),)),
        source_summaries=(summary(),),
        review_scan=scan_review(
            (document(),),
            (version(),),
            (revision(),),
        ),
        finalization=finalization_assessment(False),
    )
    item = service.project_view("123456").items[0]
    assert item.review_item_count == 1
    assert item.review_outcome_count("open") == 1
    assert item.finalization_eligible is False
    assert item.workflow_status == "draft_review"
    assert promotion_service.calls == []


def test_eligible_draft_is_ready_to_finalize():
    service, _, _ = make_service(
        source_scan=scan_sources((source(),)),
        processing_scan=scan_processing((history(),)),
        source_summaries=(summary(),),
        review_scan=scan_review(
            (document(),),
            (version(),),
            (revision(outcome="accepted_as_generated"),),
        ),
        finalization=finalization_assessment(True),
    )
    item = service.project_view("123456").items[0]
    assert item.finalization_eligible is True
    assert item.workflow_status == "ready_to_finalize"


def test_multiple_review_documents_for_same_run_fail_closed():
    service, _, _ = make_service(
        source_scan=scan_sources((source(),)),
        processing_scan=scan_processing((history(),)),
        source_summaries=(summary(),),
        review_scan=scan_review(
            (document("RVD-000001"), document("RVD-000002")),
        ),
    )
    view = service.project_view("123456")
    assert view.items[0].workflow_status == "attention_required"
    assert "workflow.multiple_review_documents_for_run" in view.items[0].issue_codes


def test_finalized_review_projects_promotion_and_current_active_input():
    manifest = SimpleNamespace(
        approved_input_id="AIN-000001",
        review_document_id="RVD-000001",
        review_document_version_id="RVV-000001",
    )
    snapshot = SimpleNamespace(manifest=manifest, authority_state="active")
    service, _, promotion_service = make_service(
        source_scan=scan_sources((source(),)),
        processing_scan=scan_processing((history(),)),
        source_summaries=(summary(False),),
        review_scan=scan_review(
            (document(),),
            (version(state="finalized"),),
            (revision(),),
        ),
        approved_scan=scan_approved((manifest,)),
        promotion=promotion_assessment(True),
        authority=(snapshot,),
    )
    item = service.project_view("123456").items[0]
    assert item.promotion_eligible is True
    assert item.active_approved_input_ids == ("AIN-000001",)
    assert item.workflow_status == "approved_input_available"
    assert promotion_service.calls == [
        ("123456", "RVD-000001", "RVV-000001")
    ]


def test_scan_issue_is_safe_and_blocks_queue_without_exposing_path():
    source_issue = SimpleNamespace(
        code="source_integrity_error",
        source_id="SRC-000001",
        message="/Users/private/secret",
        path="/Users/private/secret",
    )
    service, _, _ = make_service(
        source_scan=scan_sources((source(),), (source_issue,)),
        processing_scan=scan_processing((history(),)),
        source_summaries=(summary(),),
    )
    view = service.project_view("123456")
    assert view.has_blocking_issues is True
    assert view.items[0].workflow_status == "attention_required"
    assert all("/Users/private" not in issue.message for issue in view.issues)


def test_workspace_view_selects_latest_version_and_exact_revision():
    version_1 = version()
    version_2 = version(
        version_id="RVV-000002",
        version_number=2,
        revision_id="RVR-000002",
    )
    revision_1 = revision()
    revision_2 = revision(
        version_id="RVV-000002",
        revision_id="RVR-000002",
    )
    action = SimpleNamespace(
        review_document_id="RVD-000001",
        review_document_version_id="RVV-000002",
        scoped_review_action_id="SRA-000001",
    )
    decision = SimpleNamespace(
        human_review_decision_id="HRD-000001",
        target=SimpleNamespace(
            target_type="review_document_finalization",
            target_id="RVV-000002",
        ),
    )
    service, repository, _ = make_service(
        source_scan=scan_sources((source(),)),
        processing_scan=scan_processing((history(),)),
        review_scan=scan_review(
            (document(),),
            (version_1, version_2),
            (revision_1, revision_2),
            (action,),
        ),
        human_scan=scan_human((decision,)),
        finalization=finalization_assessment(True),
    )
    view = service.workspace_view("123456", "RVD-000001")
    assert view.version.review_document_version_id == "RVV-000002"
    assert view.revision.review_revision_id == "RVR-000002"
    assert view.scoped_actions == (action,)
    assert view.finalization_decisions == (decision,)
    assert view.can_finalize is True
    assert ("RVD-000001", "RVV-000002", "RVR-000002") in repository.calls


def test_workspace_view_rejects_missing_requested_version():
    service, _, _ = make_service(
        source_scan=scan_sources((source(),)),
        processing_scan=scan_processing((history(),)),
        review_scan=scan_review(
            (document(),),
            (version(),),
            (revision(),),
        ),
    )
    with pytest.raises(ReviewReferenceError, match="requested Review Document Version"):
        service.workspace_view(
            "123456",
            "RVD-000001",
            "RVV-999999",
        )


def test_workspace_view_rejects_ambiguous_latest_version():
    service, _, _ = make_service(
        source_scan=scan_sources((source(),)),
        processing_scan=scan_processing((history(),)),
        review_scan=scan_review(
            (document(),),
            (
                version(version_id="RVV-000001", version_number=2),
                version(
                    version_id="RVV-000002",
                    version_number=2,
                    revision_id="RVR-000002",
                ),
            ),
            (),
        ),
    )
    with pytest.raises(ReviewIntegrityError, match="exactly one latest"):
        service.workspace_view("123456", "RVD-000001")
