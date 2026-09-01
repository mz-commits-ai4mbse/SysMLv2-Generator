"""Focused tests for I2D.5D2B concern-centric V2 readers."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from modules.project_reconciliation.workflow_service import (
    ProjectAuthorityWorkflowService,
    ProjectReconciliationWorkflowError,
)


class V2Repository:
    def __init__(
        self,
        *,
        regrouping_required=False,
        conflicts=True,
        uncertainties=False,
    ):
        self.cycle = SimpleNamespace(
            schema_version="2.0.0",
            reconciliation_mode="concern_centric_cases",
            project_id="308131",
            reconciliation_cycle_id="PRC-000001",
            source_ids=("SRC-000001", "SRC-000002", "SRC-000003"),
        )
        self.index = SimpleNamespace(
            project_id="308131",
            source_ids=("SRC-000001", "SRC-000002", "SRC-000003"),
            cases=(
                SimpleNamespace(
                    case_id="CASE-000001",
                    group_label="Remote client",
                    member_subject_refs=(
                        "project_subject:SRC-000001:SP-1:CSUB-1",
                        "project_subject:SRC-000002:SP-2:CSUB-2",
                    ),
                    source_ids=("SRC-000001", "SRC-000002"),
                    singleton=False,
                ),
                SimpleNamespace(
                    case_id="CASE-000002",
                    group_label="Audio",
                    member_subject_refs=(
                        "project_subject:SRC-000003:SP-3:CSUB-3",
                    ),
                    source_ids=("SRC-000003",),
                    singleton=True,
                ),
            ),
        )
        self.assessments = (
            SimpleNamespace(
                case_id="CASE-000001",
                outcome=(
                    "distinct"
                    if regrouping_required
                    else "potential_conflict"
                ),
                summary=(
                    "Subjects do not belong to one concern."
                    if regrouping_required
                    else "Remote client is classified differently."
                ),
                shared_concepts=(
                    ()
                    if regrouping_required
                    else ("remote client",)
                ),
                material_differences=(
                    ("different engineering concerns",)
                    if regrouping_required
                    else ("actor versus logical element",)
                ),
                claim_groups=(
                    ()
                    if regrouping_required
                    else (
                        SimpleNamespace(
                            claim_group_id="CLAIM-001",
                            summary="actor",
                            supported_by_subject_refs=(
                                "project_subject:SRC-000001:SP-1:CSUB-1",
                            ),
                        ),
                        SimpleNamespace(
                            claim_group_id="CLAIM-002",
                            summary="logical element",
                            supported_by_subject_refs=(
                                "project_subject:SRC-000002:SP-2:CSUB-2",
                            ),
                        ),
                    )
                ),
                human_review_required=True,
            ),
            SimpleNamespace(
                case_id="CASE-000002",
                outcome="unique",
                summary="No cross-source counterpart.",
                shared_concepts=(),
                material_differences=(),
                claim_groups=(),
                human_review_required=False,
            ),
        )
        self.summary = SimpleNamespace(
            case_count=2,
            potential_conflicts_present=conflicts,
            uncertainties_present=uncertainties,
            regrouping_required=regrouping_required,
        )
        self.legacy_semantic_loads = 0
        self.authority_binding_reads = 0

    def latest_cycle(self, project_id):
        return self.cycle

    def load_cycle(self, project_id, cycle_id):
        return self.cycle

    def load_semantic_index(self, project_id, cycle_id):
        return self.index

    def load_case_assessments(self, project_id, cycle_id):
        return self.assessments

    def load_reconciliation_summary(self, project_id, cycle_id):
        return self.summary

    def load_semantic_reconciliation(self, project_id, cycle_id):
        self.legacy_semantic_loads += 1
        raise AssertionError("V2 reader must not load legacy S3")

    def load_authority_bindings_if_available(self, project_id, cycle_id):
        self.authority_binding_reads += 1
        raise AssertionError("V2 read-only path must not enter legacy S4")


def service(repo):
    return ProjectAuthorityWorkflowService(
        reconciliation_repository=repo,
        approved_input_repository=SimpleNamespace(),
        accepted_model_loader=lambda project_id: None,
    )


def test_v2_review_projects_cases_without_legacy_s3_or_s4_reads():
    repo = V2Repository()
    view = service(repo).load_review("308131")

    assert view.reconciliation_mode == "concern_centric_cases"
    assert view.cycle_id == "PRC-000001"
    assert view.case_count == 2
    assert view.unique_case_count == 1
    assert len(view.case_reviews) == 2
    assert view.relation_reviews == ()
    assert view.required_decision_count == 0
    assert view.decision_count == 0
    assert view.bindings_ready is False
    assert view.case_authority_ready is False
    assert view.workflow_status == "case_review_ready"
    assert view.potential_conflicts_present is True
    assert repo.legacy_semantic_loads == 0
    assert repo.authority_binding_reads == 0


def test_v2_case_projection_preserves_claim_evidence_read_only():
    repo = V2Repository()
    view = service(repo).load_review("308131")

    case = next(
        item
        for item in view.case_reviews
        if item.case_id == "CASE-000001"
    )
    assert case.group_label == "Remote client"
    assert case.outcome == "potential_conflict"
    assert case.source_ids == ("SRC-000001", "SRC-000002")
    assert case.human_review_required is True
    assert [group.claim_group_id for group in case.claim_groups] == [
        "CLAIM-001",
        "CLAIM-002",
    ]


def test_v2_distinct_case_is_exposed_as_regrouping_required():
    repo = V2Repository(
        regrouping_required=True,
        conflicts=False,
    )
    view = service(repo).load_review("308131")

    assert view.regrouping_required is True
    assert view.workflow_status == "regrouping_required"
    assert "regroup" in view.blocking_reason.lower()
    assert view.case_authority_ready is False


def test_v2_uncertainty_is_signal_not_legacy_integrity_failure():
    repo = V2Repository(
        conflicts=False,
        uncertainties=True,
    )
    view = service(repo).load_review("308131")

    assert view.uncertainties_present is True
    assert view.workflow_status == "case_review_ready"
    assert repo.legacy_semantic_loads == 0


def test_prepare_legacy_authority_bindings_is_blocked_for_v2():
    repo = V2Repository()

    with pytest.raises(
        ProjectReconciliationWorkflowError,
        match="case-aware Human Project Authority",
    ):
        service(repo).prepare_authority_bindings(
            "308131",
            "PRC-000001",
        )

    assert repo.authority_binding_reads == 0


def test_record_legacy_pairwise_decision_is_blocked_for_v2():
    repo = V2Repository()

    with pytest.raises(
        ProjectReconciliationWorkflowError,
        match="case-aware Human Project Authority",
    ):
        service(repo).record_authority_decision(
            "308131",
            "PRC-000001",
            left_subject_ref="left",
            right_subject_ref="right",
            outcome="remain_independent",
            reviewer_identity="MZ",
            rationale="Must never reach legacy relation authority.",
        )


def test_finalize_legacy_relation_authority_is_blocked_for_v2():
    repo = V2Repository()

    with pytest.raises(
        ProjectReconciliationWorkflowError,
        match="case-aware Human Project Authority",
    ):
        service(repo).finalize_authority(
            "308131",
            "PRC-000001",
        )
