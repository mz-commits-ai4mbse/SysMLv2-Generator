"""Focused tests for ADR-033 concern-centric Case contracts."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from modules.project_semantic_reconciliation.case_contract import (
    create_project_reconciliation_case_assessment,
    create_project_semantic_index_artifact,
    derive_project_reconciliation_summary,
)
from modules.project_semantic_reconciliation.case_types import (
    ReconciliationClaimGroupProposal,
    SemanticIndexGroupProposal,
)
from modules.project_semantic_reconciliation.errors import (
    ProjectSemanticReconciliationIntegrityError,
    ProjectSemanticReconciliationValidationError,
)


PROJECT_ID = "308131"
INPUT_FP = "a" * 64


def subject(ref, source):
    return SimpleNamespace(
        subject_ref=ref,
        source_id=source,
    )


def refs():
    return (
        "project_subject:SRC-000001:SP-000001:CSUB-000001",
        "project_subject:SRC-000002:SP-000002:CSUB-000004",
        "project_subject:SRC-000003:SP-000003:CSUB-000002",
    )


def semantic_index():
    left, middle, right = refs()
    return create_project_semantic_index_artifact(
        project_id=PROJECT_ID,
        input_fingerprint=INPUT_FP,
        subjects=(
            subject(left, "SRC-000001"),
            subject(middle, "SRC-000002"),
            subject(right, "SRC-000003"),
        ),
        group_proposals=(
            SemanticIndexGroupProposal(
                group_label="Concurrent viewers",
                member_subject_refs=(left, middle),
            ),
            SemanticIndexGroupProposal(
                group_label="Audio channel",
                member_subject_refs=(right,),
            ),
        ),
    )


def test_semantic_index_assigns_every_subject_exactly_once():
    index = semantic_index()

    assert index.subject_refs == tuple(sorted(refs()))
    assert len(index.cases) == 2
    assert {
        ref
        for case in index.cases
        for ref in case.member_subject_refs
    } == set(refs())


def test_case_identity_is_deterministic_and_not_label_based():
    left, middle, right = refs()
    subjects = (
        subject(left, "SRC-000001"),
        subject(middle, "SRC-000002"),
        subject(right, "SRC-000003"),
    )

    first = create_project_semantic_index_artifact(
        project_id=PROJECT_ID,
        input_fingerprint=INPUT_FP,
        subjects=subjects,
        group_proposals=(
            SemanticIndexGroupProposal("Z label", (right,)),
            SemanticIndexGroupProposal("A label", (middle, left)),
        ),
    )
    second = create_project_semantic_index_artifact(
        project_id=PROJECT_ID,
        input_fingerprint=INPUT_FP,
        subjects=subjects,
        group_proposals=(
            SemanticIndexGroupProposal("Renamed singleton", (right,)),
            SemanticIndexGroupProposal("Renamed concern", (left, middle)),
        ),
    )

    assert [case.case_id for case in first.cases] == [
        "CASE-000001",
        "CASE-000002",
    ]
    assert [
        case.member_subject_refs for case in first.cases
    ] == [
        case.member_subject_refs for case in second.cases
    ]
    assert [
        case.case_fingerprint for case in first.cases
    ] == [
        case.case_fingerprint for case in second.cases
    ]


def test_unknown_subject_in_index_fails_closed():
    left, _, _ = refs()
    with pytest.raises(
        ProjectSemanticReconciliationIntegrityError,
        match="unknown Subject",
    ):
        create_project_semantic_index_artifact(
            project_id=PROJECT_ID,
            input_fingerprint=INPUT_FP,
            subjects=(subject(left, "SRC-000001"),),
            group_proposals=(
                SemanticIndexGroupProposal(
                    "bad",
                    ("project_subject:SRC-X:SP-X:CSUB-X",),
                ),
            ),
        )


def test_missing_subject_in_index_fails_closed():
    left, middle, _ = refs()
    with pytest.raises(
        ProjectSemanticReconciliationIntegrityError,
        match="cover every Subject",
    ):
        create_project_semantic_index_artifact(
            project_id=PROJECT_ID,
            input_fingerprint=INPUT_FP,
            subjects=(
                subject(left, "SRC-000001"),
                subject(middle, "SRC-000002"),
            ),
            group_proposals=(
                SemanticIndexGroupProposal("only one", (left,)),
            ),
        )


def test_subject_may_not_appear_in_two_cases():
    left, middle, _ = refs()
    with pytest.raises(
        ProjectSemanticReconciliationIntegrityError,
        match="exactly one Reconciliation Case",
    ):
        create_project_semantic_index_artifact(
            project_id=PROJECT_ID,
            input_fingerprint=INPUT_FP,
            subjects=(
                subject(left, "SRC-000001"),
                subject(middle, "SRC-000002"),
            ),
            group_proposals=(
                SemanticIndexGroupProposal("one", (left,)),
                SemanticIndexGroupProposal("two", (left, middle)),
            ),
        )


def test_multi_member_case_may_contain_subjects_from_one_source():
    left, middle, _ = refs()

    index = create_project_semantic_index_artifact(
        project_id=PROJECT_ID,
        input_fingerprint=INPUT_FP,
        subjects=(
            subject(left, "SRC-000001"),
            subject(middle, "SRC-000001"),
        ),
        group_proposals=(
            SemanticIndexGroupProposal(
                "shared engineering concern",
                (left, middle),
            ),
        ),
    )

    assert len(index.cases) == 1
    case = index.cases[0]
    assert case.singleton is False
    assert case.member_subject_refs == tuple(sorted((left, middle)))
    assert case.source_ids == ("SRC-000001",)
    assert index.human_review_required is True


def test_singleton_case_is_unique_without_llm_provenance():
    index = semantic_index()
    singleton = next(case for case in index.cases if case.singleton)

    assessment = create_project_reconciliation_case_assessment(
        semantic_index=index,
        case_id=singleton.case_id,
        shared_concern=singleton.group_label,
        outcome="unique",
        summary="No semantic counterpart was indexed.",
    )

    assert assessment.outcome == "unique"
    assert assessment.human_review_required is False
    assert assessment.llm_provider is None
    assert assessment.llm_model is None
    assert assessment.llm_response_id is None


def test_singleton_must_not_claim_llm_assessment():
    index = semantic_index()
    singleton = next(case for case in index.cases if case.singleton)

    with pytest.raises(
        ProjectSemanticReconciliationIntegrityError,
        match="must not claim LLM",
    ):
        create_project_reconciliation_case_assessment(
            semantic_index=index,
            case_id=singleton.case_id,
            shared_concern=singleton.group_label,
            outcome="unique",
            summary="Unique.",
            llm_provider="openai",
        )


def test_non_singleton_unique_is_rejected():
    index = semantic_index()
    case = next(case for case in index.cases if not case.singleton)

    with pytest.raises(
        ProjectSemanticReconciliationValidationError,
        match="reserved for Singleton",
    ):
        create_project_reconciliation_case_assessment(
            semantic_index=index,
            case_id=case.case_id,
            shared_concern=case.group_label,
            outcome="unique",
            summary="Invalid.",
            llm_provider="openai",
            llm_model="gpt-test",
        )


def test_potential_conflict_requires_partitioned_claim_groups():
    index = semantic_index()
    case = next(case for case in index.cases if not case.singleton)
    left, right = case.member_subject_refs

    assessment = create_project_reconciliation_case_assessment(
        semantic_index=index,
        case_id=case.case_id,
        shared_concern="Maximum concurrent viewers",
        outcome="potential_conflict",
        summary="Sources specify incompatible limits.",
        shared_concepts=("concurrent viewers",),
        material_differences=("maximum is 2 vs 5",),
        claim_group_proposals=(
            ReconciliationClaimGroupProposal(
                summary="maximum = 2",
                supported_by_subject_refs=(left,),
            ),
            ReconciliationClaimGroupProposal(
                summary="maximum = 5",
                supported_by_subject_refs=(right,),
            ),
        ),
        llm_provider="openai",
        llm_model="gpt-test",
        llm_response_id="resp-1",
    )

    assert assessment.outcome == "potential_conflict"
    assert [group.claim_group_id for group in assessment.claim_groups] == [
        "CLAIM-001",
        "CLAIM-002",
    ]
    assert assessment.human_review_required is True


def test_conflict_claim_groups_must_cover_all_case_members():
    index = semantic_index()
    case = next(case for case in index.cases if not case.singleton)
    left, _ = case.member_subject_refs

    with pytest.raises(
        ProjectSemanticReconciliationIntegrityError,
        match="partition all",
    ):
        create_project_reconciliation_case_assessment(
            semantic_index=index,
            case_id=case.case_id,
            shared_concern="Maximum concurrent viewers",
            outcome="potential_conflict",
            summary="Conflict.",
            shared_concepts=("viewer limit",),
            material_differences=("2 vs 5",),
            claim_group_proposals=(
                ReconciliationClaimGroupProposal(
                    summary="maximum = 2",
                    supported_by_subject_refs=(left,),
                ),
            ),
            llm_provider="openai",
            llm_model="gpt-test",
        )


def test_summary_requires_exactly_one_assessment_per_case():
    index = semantic_index()
    singleton = next(case for case in index.cases if case.singleton)

    unique = create_project_reconciliation_case_assessment(
        semantic_index=index,
        case_id=singleton.case_id,
        shared_concern=singleton.group_label,
        outcome="unique",
        summary="Unique.",
    )

    with pytest.raises(
        ProjectSemanticReconciliationIntegrityError,
        match="every Case",
    ):
        derive_project_reconciliation_summary(
            semantic_index=index,
            assessments=(unique,),
        )


def test_summary_derives_global_conflict_signal_without_llm():
    index = semantic_index()
    singleton = next(case for case in index.cases if case.singleton)
    multi = next(case for case in index.cases if not case.singleton)
    left, right = multi.member_subject_refs

    unique = create_project_reconciliation_case_assessment(
        semantic_index=index,
        case_id=singleton.case_id,
        shared_concern=singleton.group_label,
        outcome="unique",
        summary="Unique.",
    )
    conflict = create_project_reconciliation_case_assessment(
        semantic_index=index,
        case_id=multi.case_id,
        shared_concern="Maximum concurrent viewers",
        outcome="potential_conflict",
        summary="2 vs 5.",
        shared_concepts=("viewer limit",),
        material_differences=("2 vs 5",),
        claim_group_proposals=(
            ReconciliationClaimGroupProposal("2", (left,)),
            ReconciliationClaimGroupProposal("5", (right,)),
        ),
        llm_provider="openai",
        llm_model="gpt-test",
    )

    summary = derive_project_reconciliation_summary(
        semantic_index=index,
        assessments=(conflict, unique),
    )

    assert summary.case_count == 2
    assert summary.potential_conflicts_present is True
    assert summary.uncertainties_present is False
    assert summary.regrouping_required is False
    assert summary.human_project_authority_required is True
    assert dict(summary.outcome_counts) == {
        "potential_conflict": 1,
        "unique": 1,
    }


def test_distinct_case_sets_regrouping_required():
    index = semantic_index()
    singleton = next(case for case in index.cases if case.singleton)
    multi = next(case for case in index.cases if not case.singleton)

    unique = create_project_reconciliation_case_assessment(
        semantic_index=index,
        case_id=singleton.case_id,
        shared_concern=singleton.group_label,
        outcome="unique",
        summary="Unique.",
    )
    distinct = create_project_reconciliation_case_assessment(
        semantic_index=index,
        case_id=multi.case_id,
        shared_concern="Mis-grouped concern",
        outcome="distinct",
        summary="These Subjects should not share one Case.",
        material_differences=("different engineering concerns",),
        llm_provider="openai",
        llm_model="gpt-test",
    )

    summary = derive_project_reconciliation_summary(
        semantic_index=index,
        assessments=(unique, distinct),
    )

    assert summary.regrouping_required is True
    assert summary.potential_conflicts_present is False
