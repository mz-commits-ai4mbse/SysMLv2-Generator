from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from modules.guided_workflow import (
    GUIDED_WORKFLOW_STAGE_IDS,
    GuidedWorkflowValidationError,
    build_guided_workflow_view,
    create_comparison_view,
    create_decision_alternative_view,
    create_decision_view,
    create_engineering_content_view,
    create_persona_result_view,
    create_proposal_view,
    create_stage_view,
    create_variance_view,
)


def _proposal(proposal_id: str, text: str = "Requirement"):

    return create_proposal_view(
        proposal_id=proposal_id,
        title=text,
        primary_text=text,
        confidence="high",
        rationale="Derived from the supplied engineering evidence.",
    )


def _persona(
    persona_id: str,
    proposal_id: str,
    text: str = "Requirement",
    *,
    run_count: int = 1,
    stability_level: str = "stable",
):
    return create_persona_result_view(
        persona_id=persona_id,
        persona_label=persona_id.replace("_", " ").title(),
        stability_level=stability_level,
        run_count=run_count,
        proposals=(_proposal(proposal_id, text),),
    )


def _stage(
    stage_id: str,
    *,
    status: str = "not_started",
    semantic: str = "neutral",
    decisions: int = 0,
    variance: int = 0,
    blockers: int = 0,
    action: str | None = None,
):
    return create_stage_view(
        stage_id=stage_id,
        presentation_status=status,
        semantic=semantic,
        summary=f"{stage_id} summary",
        decision_count=decisions,
        variance_attention_count=variance,
        blocking_issue_count=blockers,
        action_label=action,
    )


def _canonical_stages():
    return tuple(_stage(stage_id) for stage_id in GUIDED_WORKFLOW_STAGE_IDS)


def test_stage_contract_contains_seven_canonical_engineering_stages():
    assert GUIDED_WORKFLOW_STAGE_IDS == (
        "project_sources",
        "processing",
        "human_review",
        "project_reconciliation",
        "model_proposal",
        "final_model_review",
        "published_output",
    )


def test_engineering_content_is_content_first_and_immutable():
    view = create_engineering_content_view(
        entity_id="SRC-000001",
        content_kind="source",
        title="Stakeholder Notes",
        primary_text="Remote review is required.",
        source_label="stakeholder_notes.md",
    )

    assert view.title == "Stakeholder Notes"
    assert view.primary_text == "Remote review is required."
    assert view.traceability_available is True

    with pytest.raises(FrozenInstanceError):
        view.title = "Changed"


@pytest.mark.parametrize(
    "unsafe",
    (
        "../SRC-000001",
        "data/projects/000001",
        "/tmp/source",
        "SRC 000001",
    ),
)
def test_engineering_content_rejects_path_like_or_unstable_entity_ids(unsafe):
    with pytest.raises(GuidedWorkflowValidationError):
        create_engineering_content_view(
            entity_id=unsafe,
            content_kind="source",
            title="Source",
            primary_text="Content",
        )


def test_persona_result_groups_repeated_runs_under_one_persona():
    result = create_persona_result_view(
        persona_id="systems_engineer",
        persona_label="Systems Engineer",
        stability_level="stable",
        run_count=3,
        proposals=(
            _proposal("P-001"),
            _proposal("P-002"),
            _proposal("P-003"),
        ),
    )

    assert result.persona_id == "systems_engineer"
    assert result.run_count == 3
    assert len(result.proposals) == 3


def test_persona_result_rejects_duplicate_proposal_identity():
    proposal = _proposal("P-001")

    with pytest.raises(GuidedWorkflowValidationError):
        create_persona_result_view(
            persona_id="systems_engineer",
            persona_label="Systems Engineer",
            stability_level="stable",
            run_count=2,
            proposals=(proposal, proposal),
        )


def test_unanimous_low_variance_is_positive_but_not_approval():
    variance = create_variance_view(
        consensus_level="unanimous",
        variance_level="low",
        total_personas=3,
        supporting_personas=("p1", "p2", "p3"),
        review_required=True,
    )

    assert variance.semantic == "positive"
    assert variance.label == "Unanimous · 3 / 3 Personas agree"
    assert variance.review_required is True
    assert "Human review is required" in variance.explanation


def test_unanimous_requires_support_from_every_persona():
    with pytest.raises(GuidedWorkflowValidationError):
        create_variance_view(
            consensus_level="unanimous",
            variance_level="low",
            total_personas=3,
            supporting_personas=("p1", "p2"),
            dissenting_personas=("p3",),
            review_required=True,
        )


def test_majority_medium_variance_is_attention():
    variance = create_variance_view(
        consensus_level="majority",
        variance_level="medium",
        total_personas=3,
        supporting_personas=("p1", "p2"),
        dissenting_personas=("p3",),
        review_required=True,
    )

    assert variance.semantic == "attention"
    assert variance.label == "Majority · 2 / 3 Personas agree"


def test_high_variance_is_blocking_presentation_semantic():
    variance = create_variance_view(
        consensus_level="none",
        variance_level="high",
        total_personas=3,
        dissenting_personas=("p1", "p2", "p3"),
        review_required=True,
    )

    assert variance.semantic == "blocking"
    assert variance.label == "No consensus"


@pytest.mark.parametrize("consensus", ("incomplete", "incomparable"))
def test_incomplete_or_incomparable_results_are_neutral(consensus):
    variance = create_variance_view(
        consensus_level=consensus,
        variance_level="high",
        total_personas=3,
        omitting_personas=("p1", "p2", "p3"),
        review_required=True,
    )

    assert variance.semantic == "neutral"


def test_persona_support_dissent_and_omission_must_be_disjoint():
    with pytest.raises(GuidedWorkflowValidationError):
        create_variance_view(
            consensus_level="majority",
            variance_level="medium",
            total_personas=3,
            supporting_personas=("p1", "p2"),
            dissenting_personas=("p2",),
            review_required=True,
        )


def test_comparison_uses_one_column_per_distinct_persona():
    subject = create_engineering_content_view(
        entity_id="IU-000001",
        content_kind="engineering_statement",
        title="Remote review",
        primary_text="Remote review shall be supported.",
    )
    personas = (
        _persona("systems_engineer", "P-001"),
        _persona("critical_reviewer", "P-002"),
        _persona("completeness_reviewer", "P-003"),
    )
    variance = create_variance_view(
        consensus_level="unanimous",
        variance_level="low",
        total_personas=3,
        supporting_personas=(
            "systems_engineer",
            "critical_reviewer",
            "completeness_reviewer",
        ),
        review_required=True,
    )

    comparison = create_comparison_view(
        subject=subject,
        persona_results=personas,
        variance=variance,
    )

    assert len(comparison.persona_results) == 3


def test_comparison_rejects_same_persona_as_multiple_independent_votes():
    subject = create_engineering_content_view(
        entity_id="IU-000001",
        content_kind="engineering_statement",
        title="Remote review",
        primary_text="Remote review shall be supported.",
    )
    personas = (
        _persona("systems_engineer", "P-001"),
        _persona("systems_engineer", "P-002"),
    )
    variance = create_variance_view(
        consensus_level="unanimous",
        variance_level="low",
        total_personas=2,
        supporting_personas=("systems_engineer", "other_persona"),
        review_required=True,
    )

    with pytest.raises(GuidedWorkflowValidationError):
        create_comparison_view(
            subject=subject,
            persona_results=personas,
            variance=variance,
        )


def test_comparison_requires_variance_total_to_match_distinct_personas():
    subject = create_engineering_content_view(
        entity_id="IU-000001",
        content_kind="engineering_statement",
        title="Remote review",
        primary_text="Remote review shall be supported.",
    )
    personas = (
        _persona("p1", "P-001"),
        _persona("p2", "P-002"),
    )
    variance = create_variance_view(
        consensus_level="majority",
        variance_level="medium",
        total_personas=3,
        supporting_personas=("p1", "p2"),
        dissenting_personas=("p3",),
        review_required=True,
    )

    with pytest.raises(GuidedWorkflowValidationError):
        create_comparison_view(
            subject=subject,
            persona_results=personas,
            variance=variance,
        )


def test_required_decision_exposes_human_readable_alternatives():
    alternatives = (
        create_decision_alternative_view(
            alternative_key="requirement",
            label="Requirement",
        ),
        create_decision_alternative_view(
            alternative_key="constraint",
            label="Constraint",
        ),
    )

    decision = create_decision_view(
        decision_key="decision-1",
        subject="Information classification",
        prompt="Select the engineering interpretation.",
        presentation_state="required",
        authority_domain="human_review",
        target_entity_id="RVI-000001",
        alternatives=alternatives,
    )

    assert decision.presentation_state == "required"
    assert [item.label for item in decision.alternatives] == [
        "Requirement",
        "Constraint",
    ]


def test_required_decision_without_alternative_is_rejected():
    with pytest.raises(GuidedWorkflowValidationError):
        create_decision_view(
            decision_key="decision-1",
            subject="Classification",
            prompt="Choose.",
            presentation_state="required",
            authority_domain="human_review",
            target_entity_id="RVI-000001",
        )


def test_stage_uses_canonical_human_readable_label():
    stage = _stage(
        "human_review",
        status="action_required",
        semantic="attention",
        decisions=4,
        action="Continue review",
    )

    assert stage.label == "Human Review & Approved Input"
    assert stage.decision_count == 4


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("decision_count", -1),
        ("variance_attention_count", -1),
        ("blocking_issue_count", -1),
    ),
)
def test_stage_rejects_negative_counts(field, value):
    kwargs = {
        "stage_id": "processing",
        "presentation_status": "in_progress",
        "semantic": "informational",
        "summary": "Processing",
        field: value,
    }

    with pytest.raises(GuidedWorkflowValidationError):
        create_stage_view(**kwargs)


def test_workflow_requires_all_stages_in_canonical_order():
    stages = list(_canonical_stages())
    stages[0], stages[1] = stages[1], stages[0]

    with pytest.raises(GuidedWorkflowValidationError):
        build_guided_workflow_view(
            project_id="000001",
            stages=stages,
        )


def test_workflow_rejects_invalid_project_identity():
    with pytest.raises(GuidedWorkflowValidationError):
        build_guided_workflow_view(
            project_id="PROJECT-1",
            stages=_canonical_stages(),
        )


def test_your_work_summary_aggregates_engineer_relevant_counts():
    stages = (
        _stage("project_sources", status="complete"),
        _stage("processing", status="complete"),
        _stage(
            "human_review",
            status="action_required",
            semantic="attention",
            decisions=4,
            variance=2,
            action="Continue Human Review",
        ),
        _stage("project_reconciliation"),
        _stage("model_proposal"),
        _stage("final_model_review"),
        _stage("published_output"),
    )

    view = build_guided_workflow_view(
        project_id="000001",
        stages=stages,
        confirmed_result_count=11,
    )

    assert view.work_summary.decisions_required == 4
    assert view.work_summary.variance_attention_count == 2
    assert view.work_summary.confirmed_result_count == 11
    assert view.work_summary.completed_stage_count == 2


def test_next_action_prioritizes_open_human_decision():
    stages = (
        _stage(
            "project_sources",
            status="in_progress",
            semantic="informational",
            action="Inspect sources",
        ),
        _stage("processing"),
        _stage(
            "human_review",
            status="action_required",
            semantic="attention",
            decisions=2,
            action="Resolve 2 Human decisions",
        ),
        _stage("project_reconciliation"),
        _stage("model_proposal"),
        _stage("final_model_review"),
        _stage("published_output"),
    )

    view = build_guided_workflow_view(
        project_id="000001",
        stages=stages,
    )

    assert view.next_stage_id == "human_review"
    assert view.next_action == "Resolve 2 Human decisions"


def test_next_action_uses_blocker_when_no_human_decision_is_open():
    stages = (
        _stage("project_sources", status="complete"),
        _stage(
            "processing",
            status="blocked",
            semantic="blocking",
            blockers=1,
            action="Inspect processing issue",
        ),
        _stage("human_review"),
        _stage("project_reconciliation"),
        _stage("model_proposal"),
        _stage("final_model_review"),
        _stage("published_output"),
    )

    view = build_guided_workflow_view(
        project_id="000001",
        stages=stages,
    )

    assert view.next_stage_id == "processing"
    assert view.next_action == "Inspect processing issue"


def test_fully_complete_workflow_has_no_next_action():
    stages = tuple(
        _stage(
            stage_id,
            status="complete",
            semantic="positive",
        )
        for stage_id in GUIDED_WORKFLOW_STAGE_IDS
    )

    view = build_guided_workflow_view(
        project_id="000001",
        stages=stages,
        confirmed_result_count=12,
    )

    assert view.next_stage_id is None
    assert view.next_action is None
    assert view.work_summary.completed_stage_count == 7
