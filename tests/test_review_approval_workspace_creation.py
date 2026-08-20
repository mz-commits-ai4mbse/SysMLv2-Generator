"""Tests for G6.2 initial Human Review Workspace creation."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from modules.human_review import HumanReviewScanResult
from modules.review_workspace import (
    ReviewApprovalWorkflowService,
    ReviewIntegrityError,
    ReviewValidationError,
)


class FakeWorkspace:
    def load_project(self, project_id):
        return SimpleNamespace(project_id=project_id)


class FakeProcessingRepository:
    def __init__(self):
        self.calls = []

    def load_run(self, project_id, processing_run_id):
        self.calls.append((project_id, processing_run_id))
        return SimpleNamespace(
            manifest=SimpleNamespace(
                project_id=project_id,
                processing_run_id=processing_run_id,
            )
        )


class FakeProcessingSummaryService:
    def collect_scans(self, project_id):
        return (
            SimpleNamespace(
                valid_sources=(),
                source_issues=(),
            ),
            SimpleNamespace(
                run_histories=(),
                issues=(),
            ),
        )


class FakeP4Repository:
    def __init__(self, method_name):
        self.method_name = method_name
        self.calls = []

    def scan_information_units(self, project_id):
        assert self.method_name == "information"
        self.calls.append(project_id)
        return SimpleNamespace(
            information_units=(),
            issues=(),
        )

    def scan_candidates(self, project_id):
        assert self.method_name in {"terminology", "framework"}
        self.calls.append(project_id)
        return SimpleNamespace(
            candidates=(),
            issues=(),
        )


class FakeHumanReviewRepository:
    def __init__(self, scan):
        self.scan = scan
        self.calls = []

    def scan_decisions(self, project_id):
        self.calls.append(project_id)
        return self.scan


class FakeApprovedInputRepository:
    def scan_project(self, project_id):
        return SimpleNamespace(
            manifests=(),
            events=(),
            issues=(),
        )


class FakePromotionService:
    def assess_eligibility(self, *args):
        raise AssertionError(
            "Promotion eligibility is not part of initial draft creation."
        )


class FakeReviewRepository:
    def __init__(self, *, documents=()):
        self.documents = list(documents)
        self.versions = []
        self.revisions = []
        self.create_calls = []
        self.scan_calls = []
        self.next_document_calls = []

    def scan_project(self, project_id):
        self.scan_calls.append(project_id)
        return SimpleNamespace(
            documents=tuple(self.documents),
            versions=tuple(self.versions),
            revisions=tuple(self.revisions),
            scoped_actions=(),
            issues=(),
        )

    def next_document_id(self, project_id):
        self.next_document_calls.append(project_id)
        return "RVD-000001"

    def create_document_workspace(
        self,
        document,
        version,
        revision,
    ):
        self.create_calls.append(
            (document, version, revision)
        )
        self.documents.append(document)
        self.versions.append(version)
        self.revisions.append(revision)
        return document, version, revision

    def load_document(self, project_id, review_document_id):
        matches = [
            item
            for item in self.documents
            if item.review_document_id == review_document_id
        ]
        if len(matches) != 1:
            raise RuntimeError("document unavailable")
        return matches[0]

    def load_version(
        self,
        project_id,
        review_document_id,
        review_document_version_id,
    ):
        matches = [
            item
            for item in self.versions
            if (
                item.review_document_id == review_document_id
                and item.review_document_version_id
                == review_document_version_id
            )
        ]
        if len(matches) != 1:
            raise RuntimeError("version unavailable")
        return matches[0]

    def load_revision(
        self,
        project_id,
        review_document_id,
        review_document_version_id,
        review_revision_id,
    ):
        matches = [
            item
            for item in self.revisions
            if (
                item.review_document_id == review_document_id
                and item.review_document_version_id
                == review_document_version_id
                and item.review_revision_id == review_revision_id
            )
        ]
        if len(matches) != 1:
            raise RuntimeError("revision unavailable")
        return matches[0]


def _document(
    *,
    document_id="RVD-000001",
    run_id="PRN-000001",
):
    return SimpleNamespace(
        project_id="123456",
        review_document_id=document_id,
        source_id="SRC-000001",
        processing_run_id=run_id,
        attempt_id="ATT-000001",
    )


def _version():
    return SimpleNamespace(
        project_id="123456",
        review_document_id="RVD-000001",
        review_document_version_id="RVV-000001",
        version_number=1,
        version_state="draft",
        head_revision_id="RVR-000001",
        finalized_revision_id=None,
    )


def _revision():
    return SimpleNamespace(
        project_id="123456",
        review_document_id="RVD-000001",
        review_document_version_id="RVV-000001",
        review_revision_id="RVR-000001",
        review_items=(),
    )


def _human_decision(target_type):
    return SimpleNamespace(
        human_review_decision_id=(
            "HRD-000001"
            if target_type == "information_unit_publication"
            else "HRD-000002"
        ),
        target=SimpleNamespace(
            target_type=target_type,
            target_id=(
                "IU-000001"
                if target_type == "information_unit_publication"
                else "RVV-000099"
            ),
        ),
    )


def _service(
    *,
    review_repository=None,
    human_scan=None,
    captures=None,
):
    review_repository = (
        FakeReviewRepository()
        if review_repository is None
        else review_repository
    )
    human_scan = (
        HumanReviewScanResult()
        if human_scan is None
        else human_scan
    )
    captures = {} if captures is None else captures

    processing_repository = FakeProcessingRepository()
    information_repository = FakeP4Repository("information")
    terminology_repository = FakeP4Repository("terminology")
    framework_repository = FakeP4Repository("framework")

    document = _document()
    version = _version()
    revision = _revision()

    def p9_selector(history, *, repository_root):
        captures["p9_selector"] = (
            history,
            repository_root,
        )
        return SimpleNamespace(
            project_id="123456",
            source_id="SRC-000001",
        )

    def p9_proposal_adapter(evidence, *, repository_root):
        captures["p9_proposals"] = (
            evidence,
            repository_root,
        )
        return "p9-proposals"

    def p9_evidence_builder(
        evidence,
        proposals,
        *,
        repository_root,
    ):
        captures["p9_evidence"] = (
            evidence,
            proposals,
            repository_root,
        )
        return "p9-structured-evidence"

    def p9_source_evidence_builder(
        evidence,
        proposals,
        *,
        repository_root,
    ):
        captures["p9_source_evidence"] = (
            evidence,
            proposals,
            repository_root,
        )
        return "p9-source-evidence"

    def p9_review_input_projector(
        evidence,
        proposals,
        structured_evidence,
        *,
        repository_root,
    ):
        captures["p9_semantic_projection"] = (
            evidence,
            proposals,
            structured_evidence,
            repository_root,
        )
        return SimpleNamespace(
            proposals=proposals,
            evidence=structured_evidence,
            used_semantic_projection=False,
        )

    def p4_selector(evidence, **kwargs):
        captures["p4_human_scan"] = kwargs[
            "human_review_scan"
        ]
        captures["p4_inputs"] = kwargs
        return SimpleNamespace(
            project_id="123456",
            source_id="SRC-000001",
        )

    def p4_builder(evidence, *, repository_root):
        captures["p4_references"] = (
            evidence,
            repository_root,
        )
        return "p4-references"

    def assembler(**kwargs):
        captures["assembly"] = kwargs
        return SimpleNamespace(
            repository_bundle=(
                document,
                version,
                revision,
            ),
            eligibility=SimpleNamespace(
                eligible_for_workspace_creation=True,
            ),
        )

    service = ReviewApprovalWorkflowService(
        root="unused",
        repository_root="/repository",
        clock=lambda: datetime(
            2026,
            8,
            8,
            7,
            30,
            tzinfo=timezone.utc,
        ),
        workspace=FakeWorkspace(),
        source_registry=SimpleNamespace(),
        processing_summary_service=(
            FakeProcessingSummaryService()
        ),
        processing_repository=processing_repository,
        review_repository=review_repository,
        human_review_repository=(
            FakeHumanReviewRepository(human_scan)
        ),
        information_unit_repository=(
            information_repository
        ),
        terminology_mapping_repository=(
            terminology_repository
        ),
        framework_assignment_repository=(
            framework_repository
        ),
        approved_input_repository=(
            FakeApprovedInputRepository()
        ),
        promotion_service=FakePromotionService(),
        source_summary_deriver=(
            lambda project_id, source_scan, processing_scan: ()
        ),
        run_state_deriver=lambda history: None,
        finalization_assessor=(
            lambda document, version, revision: (
                SimpleNamespace(
                    eligible_for_finalization=False,
                    blocking_issue_codes=(),
                )
            )
        ),
        authority_deriver=lambda manifests, events: (),
        p9_evidence_selector=p9_selector,
        p9_proposal_adapter=p9_proposal_adapter,
        p9_evidence_builder=p9_evidence_builder,
        p9_source_evidence_builder=(
            p9_source_evidence_builder
        ),
        p9_review_input_projector=(
            p9_review_input_projector
        ),
        p4_evidence_selector=p4_selector,
        p4_evidence_builder=p4_builder,
        initial_review_assembler=assembler,
    )
    return (
        service,
        review_repository,
        processing_repository,
        captures,
    )


def test_open_or_create_review_constructs_exact_initial_bundle():
    p4_decision = _human_decision(
        "information_unit_publication"
    )
    finalization_decision = _human_decision(
        "review_document_finalization"
    )
    human_scan = HumanReviewScanResult(
        decisions=(
            p4_decision,
            finalization_decision,
        ),
        issues=(),
    )
    captures = {}
    (
        service,
        repository,
        processing_repository,
        _,
    ) = _service(
        human_scan=human_scan,
        captures=captures,
    )

    result = service.open_or_create_review(
        "123456",
        "PRN-000001",
        opened_by="Reviewer A",
    )

    assert result.created is True
    assert result.review_document_id == "RVD-000001"
    assert result.review_document_version_id == "RVV-000001"
    assert len(repository.create_calls) == 1
    assert processing_repository.calls == [
        ("123456", "PRN-000001")
    ]

    assembly = captures["assembly"]
    assert assembly["review_document_id"] == "RVD-000001"
    assert (
        assembly["review_document_version_id"]
        == "RVV-000001"
    )
    assert assembly["review_revision_id"] == "RVR-000001"
    assert assembly["opened_by"] == "Reviewer A"
    assert assembly["timestamp"] == "2026-08-08T07:30:00Z"

    source_evidence = captures[
        "p9_source_evidence"
    ]
    assert source_evidence[1] == "p9-proposals"
    assert source_evidence[2] == Path("/repository")

    semantic_projection = captures[
        "p9_semantic_projection"
    ]
    assert semantic_projection[1] == "p9-proposals"
    assert semantic_projection[2] == "p9-source-evidence"
    assert semantic_projection[3] == Path("/repository")

    p4_scan = captures["p4_human_scan"]
    assert p4_scan.decisions == (p4_decision,)


def test_equivalent_retry_opens_existing_workspace_without_new_write():
    service, repository, processing_repository, _ = _service()

    first = service.open_or_create_review(
        "123456",
        "PRN-000001",
        opened_by="Reviewer A",
    )
    second = service.open_or_create_review(
        "123456",
        "PRN-000001",
        opened_by="Reviewer A",
    )

    assert first.created is True
    assert second.created is False
    assert second.review_document_id == first.review_document_id
    assert len(repository.create_calls) == 1
    assert processing_repository.calls == [
        ("123456", "PRN-000001")
    ]


def test_multiple_existing_documents_for_run_block_creation():
    repository = FakeReviewRepository(
        documents=(
            _document(document_id="RVD-000001"),
            _document(document_id="RVD-000002"),
        )
    )
    service, repository, processing_repository, _ = _service(
        review_repository=repository
    )

    with pytest.raises(
        ReviewIntegrityError,
        match="Multiple Review Documents",
    ):
        service.open_or_create_review(
            "123456",
            "PRN-000001",
            opened_by="Reviewer A",
        )

    assert repository.create_calls == []
    assert processing_repository.calls == []


def test_invalid_reviewer_identity_blocks_before_evidence_or_write():
    service, repository, processing_repository, _ = _service()

    with pytest.raises(
        ReviewValidationError,
        match="reviewer identity",
    ):
        service.open_or_create_review(
            "123456",
            "PRN-000001",
            opened_by="   ",
        )

    assert repository.create_calls == []
    assert processing_repository.calls == []


def test_finalization_hrd_issue_is_not_misclassified_as_p4_evidence_issue():
    p4_issue = SimpleNamespace(
        target_type="information_unit_publication",
    )
    finalization_issue = SimpleNamespace(
        target_type="review_document_finalization",
    )
    scan = SimpleNamespace(
        decisions=(),
        issues=(p4_issue, finalization_issue),
    )

    filtered = ReviewApprovalWorkflowService._p4_human_review_scan(
        scan
    )

    assert filtered.issues == (p4_issue,)
