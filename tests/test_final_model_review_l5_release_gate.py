from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone

import pytest

from modules.final_model_review import (
    FinalModelReviewIntegrityError,
    FinalModelReviewReleaseGateError,
    FinalModelReviewReleaseService,
    create_final_model_review_change_proposal,
    create_final_model_review_decision,
    create_final_model_review_decision_target,
    create_final_model_review_item,
    create_final_model_review_revision,
    create_generated_unit_reference,
    evaluate_final_model_review_release_gate,
    require_final_model_review_approved_for_publication,
)
from modules.final_model_review.types import (
    FinalModelReviewChangeTarget,
    FinalModelReviewRepositoryScanResult,
    FinalModelReviewRevisionBundle,
)


FP_A = "a" * 64
FP_B = "b" * 64
FP_C = "c" * 64
FP_D = "d" * 64


def _revision(
    revision_id="FRV-000001",
    *,
    predecessor=None,
    status="valid",
    gate="passed",
):
    return create_final_model_review_revision(
        project_id="000001",
        final_model_review_id="FMR-000001",
        final_model_review_revision_id=revision_id,
        predecessor_revision_id=predecessor,
        source_internal_engineering_model_id="IEM-000001",
        generated_artifact_set_fingerprint=FP_C,
        validation_result_fingerprint=FP_D,
        validation_status=status,
        publication_gate=gate,
        generated_units=(
            create_generated_unit_reference(
                generated_unit_id="GSU-000001",
                relative_path="generated_model.sysml",
                content_fingerprint=FP_A,
            ),
        ),
        created_at="2026-08-14T12:00:00Z",
    )


def _bundle(revision):
    return FinalModelReviewRevisionBundle(
        revision=revision,
        storage_manifest=None,
        artifact_set_snapshot={},
        validation_result_snapshot={},
        generated_units=(),
    )


def _item(revision_id="FRV-000001", *, mandatory=True, item_id="FRI-000001"):
    return create_final_model_review_item(
        project_id="000001",
        final_model_review_id="FMR-000001",
        final_model_review_revision_id=revision_id,
        final_model_review_item_id=item_id,
        item_kind="general",
        summary="Review this issue.",
        detail=None,
        mandatory=mandatory,
    )


def _proposal(revision):
    return create_final_model_review_change_proposal(
        project_id="000001",
        final_model_review_id="FMR-000001",
        final_model_review_revision_id=(
            revision.final_model_review_revision_id
        ),
        final_model_review_change_proposal_id="FCP-000001",
        base_revision_content_fingerprint=revision.content_fingerprint,
        base_review_subject_fingerprint=revision.review_subject_fingerprint,
        surface="diagram",
        classification="engineering_semantics",
        target=FinalModelReviewChangeTarget(
            generated_unit_id=None,
            generated_unit_content_fingerprint=None,
            generated_symbol_id=None,
            internal_model_element_id="IME-000001",
            internal_model_relationship_id=None,
            validation_finding_code=None,
        ),
        original_text=None,
        proposed_text=None,
        reviewer_feedback="Change the model semantics.",
        request_agent_reproposal=False,
        created_by="moritz",
        created_at="2026-08-14T12:01:00Z",
    )


def _decision(revision, decision, decision_id="FRD-000001"):
    return create_final_model_review_decision(
        project_id="000001",
        final_model_review_decision_id=decision_id,
        target=create_final_model_review_decision_target(revision),
        decision=decision,
        reviewer_identity="moritz",
        rationale="reviewed",
        reviewed_at="2026-08-14T12:02:00Z",
    )


class RepositoryStub:
    def __init__(
        self,
        revision,
        *,
        revisions=None,
        items=(),
        proposals=(),
        decisions=(),
        scan_issues=(),
    ):
        self.bundle = _bundle(revision)
        self.revisions = tuple(revisions or (self.bundle,))
        self.items = tuple(items)
        self.proposals = tuple(proposals)
        self.decisions = list(decisions)
        self.scan_issues = tuple(scan_issues)

    def load_revision(self, project_id, review_id, revision_id):
        for item in self.revisions:
            if item.revision.final_model_review_revision_id == revision_id:
                return item
        raise FinalModelReviewIntegrityError("missing revision")

    def list_revisions(self, project_id, review_id):
        return self.revisions

    def list_items(self, project_id, review_id, revision_id):
        return tuple(
            item for item in self.items
            if item.final_model_review_revision_id == revision_id
        )

    def list_change_proposals(self, project_id, review_id=None, revision_id=None):
        return tuple(
            item for item in self.proposals
            if revision_id is None
            or item.final_model_review_revision_id == revision_id
        )

    def list_decisions(self, project_id, review_id):
        return tuple(self.decisions)

    def scan(self, project_id):
        return FinalModelReviewRepositoryScanResult(
            decisions=tuple(self.decisions),
            issues=self.scan_issues,
        )

    def persist_decision(self, decision):
        # Mirror the L5 repository fail-closed release check.
        from modules.final_model_review import (
            require_final_model_review_ready_for_approval,
        )
        if decision.decision == "approved_for_publication":
            require_final_model_review_ready_for_approval(
                self,
                decision.project_id,
                decision.target.final_model_review_id,
                decision.target.final_model_review_revision_id,
            )
        self.decisions.append(decision)
        return decision


def _clock():
    return datetime(2026, 8, 14, 12, 10, 0, tzinfo=timezone.utc)


def test_l5_valid_passed_clean_revision_is_ready_for_approval():
    repo = RepositoryStub(_revision())
    gate = evaluate_final_model_review_release_gate(
        repo, "000001", "FMR-000001", "FRV-000001"
    )
    assert gate.release_status == "ready_for_approval"
    assert gate.blockers == ()
    assert len(gate.evaluation_fingerprint) == 64


@pytest.mark.parametrize(
    ("status", "gate"),
    [("invalid", "blocked"), ("incomplete", "blocked")],
)
def test_l5_k_blocked_revision_cannot_be_released(status, gate):
    repo = RepositoryStub(_revision(status=status, gate=gate))
    result = evaluate_final_model_review_release_gate(
        repo, "000001", "FMR-000001", "FRV-000001"
    )
    assert result.release_status == "blocked"
    assert result.blockers[0].code == "validation_not_passed"


def test_l5_mandatory_item_blocks_exact_revision():
    repo = RepositoryStub(_revision(), items=(_item(),))
    result = evaluate_final_model_review_release_gate(
        repo, "000001", "FMR-000001", "FRV-000001"
    )
    assert result.release_status == "blocked"
    assert any(
        item.code == "mandatory_review_items_unresolved"
        for item in result.blockers
    )


def test_l5_nonmandatory_item_does_not_block_release():
    repo = RepositoryStub(
        _revision(),
        items=(_item(mandatory=False),),
    )
    result = evaluate_final_model_review_release_gate(
        repo, "000001", "FMR-000001", "FRV-000001"
    )
    assert result.release_status == "ready_for_approval"


def test_l5_change_proposal_blocks_exact_revision():
    revision = _revision()
    repo = RepositoryStub(revision, proposals=(_proposal(revision),))
    result = evaluate_final_model_review_release_gate(
        repo, "000001", "FMR-000001", "FRV-000001"
    )
    assert result.release_status == "blocked"
    assert any(
        item.code == "change_proposals_unresolved"
        for item in result.blockers
    )


@pytest.mark.parametrize("decision", ["changes_requested", "rejected"])
def test_l5_nonapproval_decision_permanently_blocks_that_frv(decision):
    revision = _revision()
    repo = RepositoryStub(revision, decisions=(_decision(revision, decision),))
    result = evaluate_final_model_review_release_gate(
        repo, "000001", "FMR-000001", "FRV-000001"
    )
    assert result.release_status == "blocked"
    assert any(
        item.code == "prior_nonapproval_decision"
        for item in result.blockers
    )


def test_l5_successor_revision_supersedes_older_frv():
    first = _revision("FRV-000001")
    second = _revision("FRV-000002", predecessor="FRV-000001")
    repo = RepositoryStub(
        first,
        revisions=(_bundle(first), _bundle(second)),
    )
    result = evaluate_final_model_review_release_gate(
        repo, "000001", "FMR-000001", "FRV-000001"
    )
    assert result.release_status == "blocked"
    assert result.blockers[-1].code == "revision_superseded"
    assert result.blockers[-1].reference_ids == ("FRV-000002",)


def test_l5_explicit_successor_itself_can_be_ready():
    first = _revision("FRV-000001")
    second = _revision("FRV-000002", predecessor="FRV-000001")
    repo = RepositoryStub(
        second,
        revisions=(_bundle(first), _bundle(second)),
    )
    result = evaluate_final_model_review_release_gate(
        repo, "000001", "FMR-000001", "FRV-000002"
    )
    assert result.release_status == "ready_for_approval"


def test_l5_release_service_records_exact_human_approval():
    revision = _revision()
    repo = RepositoryStub(revision)
    service = FinalModelReviewReleaseService(
        repository=repo,
        clock=_clock,
    )
    approval = service.approve_for_publication(
        "000001",
        "FMR-000001",
        "FRV-000001",
        reviewer_identity="moritz",
        rationale="Reviewed diagram, code, validation, and traceability.",
    )
    assert approval.decision.final_model_review_decision_id == "FRD-000001"
    assert approval.decision.decision == "approved_for_publication"
    assert approval.gate.release_status == "approved_for_publication"
    assert approval.gate.approval_decision_id == "FRD-000001"


def test_l5_release_service_is_idempotent_for_existing_approval():
    revision = _revision()
    approval = _decision(revision, "approved_for_publication")
    repo = RepositoryStub(revision, decisions=(approval,))
    service = FinalModelReviewReleaseService(repository=repo, clock=_clock)
    result = service.approve_for_publication(
        "000001",
        "FMR-000001",
        "FRV-000001",
        reviewer_identity="other",
        rationale="should not create another approval",
    )
    assert result.decision == approval
    assert len(repo.decisions) == 1


def test_l5_release_service_rejects_blocked_revision():
    repo = RepositoryStub(_revision(), items=(_item(),))
    service = FinalModelReviewReleaseService(repository=repo, clock=_clock)
    with pytest.raises(FinalModelReviewReleaseGateError):
        service.approve_for_publication(
            "000001",
            "FMR-000001",
            "FRV-000001",
            reviewer_identity="moritz",
        )


def test_l5_approval_becomes_stale_if_change_proposal_appears_afterwards():
    revision = _revision()
    approval = _decision(revision, "approved_for_publication")
    proposal = _proposal(revision)
    repo = RepositoryStub(
        revision,
        decisions=(approval,),
        proposals=(proposal,),
    )
    result = evaluate_final_model_review_release_gate(
        repo, "000001", "FMR-000001", "FRV-000001"
    )
    assert result.release_status == "blocked"
    assert result.approval_decision_id == "FRD-000001"
    with pytest.raises(FinalModelReviewReleaseGateError):
        require_final_model_review_approved_for_publication(
            repo, "000001", "FMR-000001", "FRV-000001"
        )


def test_l5_approval_becomes_stale_if_mandatory_item_appears_afterwards():
    revision = _revision()
    approval = _decision(revision, "approved_for_publication")
    repo = RepositoryStub(
        revision,
        decisions=(approval,),
        items=(_item(),),
    )
    result = evaluate_final_model_review_release_gate(
        repo, "000001", "FMR-000001", "FRV-000001"
    )
    assert result.release_status == "blocked"


def test_l5_multiple_approvals_for_same_revision_are_integrity_error():
    revision = _revision()
    first = _decision(revision, "approved_for_publication", "FRD-000001")
    second = create_final_model_review_decision(
        project_id="000001",
        final_model_review_decision_id="FRD-000002",
        target=create_final_model_review_decision_target(revision),
        decision="approved_for_publication",
        reviewer_identity="second-reviewer",
        rationale="different rationale",
        reviewed_at="2026-08-14T13:00:00Z",
    )
    repo = RepositoryStub(revision, decisions=(first, second))
    with pytest.raises(FinalModelReviewIntegrityError):
        evaluate_final_model_review_release_gate(
            repo, "000001", "FMR-000001", "FRV-000001"
        )


def test_l5_evaluation_fingerprint_changes_with_approval_relevant_evidence():
    revision = _revision()
    clean = evaluate_final_model_review_release_gate(
        RepositoryStub(revision),
        "000001",
        "FMR-000001",
        "FRV-000001",
    )
    with_item = evaluate_final_model_review_release_gate(
        RepositoryStub(revision, items=(_item(),)),
        "000001",
        "FMR-000001",
        "FRV-000001",
    )
    assert clean.evaluation_fingerprint != with_item.evaluation_fingerprint

# Repository integration: direct persistence cannot bypass the normative L5 gate.
@dataclass(frozen=True)
class _RepoFakeUnit:
    unit_id: str
    relative_path: str
    content: str
    content_fingerprint: str
    generated_symbol_ids: tuple[str, ...] = ("IME_000001",)


@dataclass(frozen=True)
class _RepoFakeArtifact:
    schema_version: str
    project_id: str
    source_internal_engineering_model_id: str
    content_fingerprint: str
    units: tuple[_RepoFakeUnit, ...]


@dataclass(frozen=True)
class _RepoFakeValidation:
    schema_version: str
    project_id: str
    source_internal_engineering_model_id: str
    source_artifact_set_fingerprint: str
    validation_status: str
    publication_gate: str
    content_fingerprint: str


class _RepoWorkspaceStub:
    def load_project(self, project_id):
        if project_id != "000001":
            raise RuntimeError("Project not found.")
        return object()


def _real_repo(tmp_path):
    from modules.final_model_review import FinalModelReviewRepository

    return FinalModelReviewRepository(
        root=tmp_path,
        workspace=_RepoWorkspaceStub(),
        clock=_clock,
        artifact_validator=lambda value: None,
        validation_result_validator=lambda value: None,
    )


def _repo_artifact():
    import hashlib

    content = "package X {}\n"
    unit = _RepoFakeUnit(
        unit_id="GSU-000001",
        relative_path="generated_model.sysml",
        content=content,
        content_fingerprint=hashlib.sha256(
            content.encode("utf-8")
        ).hexdigest(),
    )
    return _RepoFakeArtifact(
        schema_version="1.0.0",
        project_id="000001",
        source_internal_engineering_model_id="IEM-000001",
        content_fingerprint=FP_C,
        units=(unit,),
    )


def _repo_validation():
    return _RepoFakeValidation(
        schema_version="1.0.0",
        project_id="000001",
        source_internal_engineering_model_id="IEM-000001",
        source_artifact_set_fingerprint=FP_C,
        validation_status="valid",
        publication_gate="passed",
        content_fingerprint=FP_D,
    )


def _persist_clean_revision(repo):
    repo.create_review("000001")
    return repo.append_revision(
        "000001",
        "FMR-000001",
        artifact_set=_repo_artifact(),
        validation_result=_repo_validation(),
    )


def test_l5_repository_direct_approval_cannot_bypass_mandatory_item(tmp_path):
    repo = _real_repo(tmp_path)
    bundle = _persist_clean_revision(repo)
    item = create_final_model_review_item(
        project_id="000001",
        final_model_review_id="FMR-000001",
        final_model_review_revision_id="FRV-000001",
        final_model_review_item_id="FRI-000001",
        item_kind="general",
        summary="Must resolve.",
        detail=None,
        mandatory=True,
    )
    repo.persist_item(item)
    approval = _decision(
        bundle.revision,
        "approved_for_publication",
    )
    with pytest.raises(FinalModelReviewReleaseGateError):
        repo.persist_decision(approval)


def test_l5_repository_clean_direct_approval_is_gate_checked_and_persisted(tmp_path):
    repo = _real_repo(tmp_path)
    bundle = _persist_clean_revision(repo)
    approval = _decision(
        bundle.revision,
        "approved_for_publication",
    )
    saved = repo.persist_decision(approval)
    assert saved == approval
    gate = require_final_model_review_approved_for_publication(
        repo,
        "000001",
        "FMR-000001",
        "FRV-000001",
    )
    assert gate.approval_decision_id == "FRD-000001"


def test_l5_repository_list_items_is_explicit_revision_scoped_read(tmp_path):
    repo = _real_repo(tmp_path)
    _persist_clean_revision(repo)
    item = create_final_model_review_item(
        project_id="000001",
        final_model_review_id="FMR-000001",
        final_model_review_revision_id="FRV-000001",
        final_model_review_item_id="FRI-000001",
        item_kind="general",
        summary="Optional note.",
        detail=None,
        mandatory=False,
    )
    repo.persist_item(item)
    assert repo.list_items(
        "000001",
        "FMR-000001",
        "FRV-000001",
    ) == (item,)
