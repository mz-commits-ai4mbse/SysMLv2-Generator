from __future__ import annotations

from dataclasses import FrozenInstanceError
from types import SimpleNamespace

import pytest

from modules.guided_workflow import (
    GuidedWorkflowValidationError,
    build_model_proposal_presentation,
)


def _review(status="pending"):
    return SimpleNamespace(status=status)


def _element(candidate_id="MCE-000001", *, status="pending", name="System"):
    return SimpleNamespace(
        candidate_id=candidate_id,
        proposed_name=name,
        model_area="system_logical",
        element_type="part_definition",
        support_level="supported",
        conformance_status="conformant",
        review_state=_review(status),
        approved_input_ids=("AIN-000001",),
        assumptions=(),
        missing_information=(),
        rationale="Derived from Approved Input.",
    )


def _relationship(
    candidate_id="MCR-000001",
    *,
    status="pending",
    source="system",
    target="component",
    choice_key=None,
    priority="preferred",
    comparability="neutral",
):
    return SimpleNamespace(
        candidate_id=candidate_id,
        relationship_choice_key=choice_key,
        source_subject_key=source,
        target_subject_key=target,
        source_resolution_status="resolved",
        target_resolution_status="resolved",
        relationship_family="dependency",
        semantic_intent="contains",
        directionality="directed",
        priority_class=priority,
        comparability_impact=comparability,
        conformance_status="conformant",
        review_state=_review(status),
        approved_input_ids=("AIN-000002",),
        assumptions=(),
        missing_information=(),
        rationale="Derived relationship.",
    )


def _structural(elements, relationships):
    return SimpleNamespace(
        nodes=tuple(
            SimpleNamespace(candidate_id=item.candidate_id)
            for item in elements
        ),
        edges=tuple(
            SimpleNamespace(candidate_id=item.candidate_id)
            for item in relationships
        ),
        model_areas=("system_logical",),
    )


def _comparability(**overrides):
    values = {
        "improves_count": 0,
        "neutral_count": 1,
        "reduces_count": 0,
        "unknown_count": 0,
        "comparison_anchor_ids": (),
        "deviation_ids": (),
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def _proposal(
    *,
    elements=None,
    relationships=None,
    choices=(),
    decisions=None,
    deviations=(),
    blocking=(),
    gate="not_ready",
):
    elements = tuple(elements or (_element(),))
    relationships = tuple(relationships or (_relationship(),))
    if decisions is None:
        decisions = (
            SimpleNamespace(
                decision_key="element:MCE-000001",
                target_type="element_candidate",
                target_ids=("MCE-000001",),
                reason="No Human Review Decision exists yet.",
                recommended_action="Review this proposed model element.",
            ),
        )
    return SimpleNamespace(
        candidate_set_id="MCS-000001",
        candidate_set_content_fingerprint="a" * 64,
        summary="Proposed engineering model.",
        proposed_elements=elements,
        proposed_relationships=relationships,
        structural_overview=_structural(elements, relationships),
        relationship_choice_groups=tuple(choices),
        comparability_summary=_comparability(),
        profile_deviations=tuple(deviations),
        required_human_decisions=tuple(decisions),
        blocking_issues=tuple(blocking),
        generation_rationale_summary="Derived from exact Approved Input.",
        phase_i_gate_status=gate,
        next_action="Review remaining Candidates.",
    )


def test_architecture_projection_is_content_first_but_retains_exact_ids():
    view = build_model_proposal_presentation(_proposal())

    assert view.architecture_nodes[0].name == "System"
    assert view.architecture_nodes[0].model_area == "system_logical"
    assert view.architecture_nodes[0].candidate_id == "MCE-000001"
    assert view.architecture_edges[0].source == "system"
    assert view.architecture_edges[0].relationship == "contains"
    assert view.architecture_edges[0].target == "component"
    assert view.candidate_set_id == "MCS-000001"
    assert view.candidate_set_content_fingerprint == "a" * 64


def test_required_human_decision_uses_engineering_title_not_candidate_id():
    view = build_model_proposal_presentation(_proposal())

    assert view.required_decisions[0].title == "System"
    assert view.required_decisions[0].target_ids == ("MCE-000001",)
    assert view.readiness.decisions_required == 1
    assert view.readiness.status_label == "Human Candidate review required"
    assert view.readiness.semantic == "attention"
    assert view.readiness.can_assemble is False


def test_relationship_choice_is_presented_as_alternatives_not_votes():
    relationships = (
        _relationship(
            "MCR-000001",
            choice_key="control",
            priority="preferred",
        ),
        _relationship(
            "MCR-000002",
            choice_key="control",
            source="consumer",
            target="device",
            priority="alternative",
        ),
    )
    choice = SimpleNamespace(
        relationship_choice_key="control",
        candidate_ids=("MCR-000001", "MCR-000002"),
        preferred_candidate_ids=("MCR-000001",),
        accepted_candidate_ids=(),
        review_required=True,
    )
    decision = SimpleNamespace(
        decision_key="relationship_choice:control",
        target_type="relationship_choice_group",
        target_ids=("MCR-000001", "MCR-000002"),
        reason="Select one relationship alternative.",
        recommended_action="Select the intended relationship alternative.",
    )

    view = build_model_proposal_presentation(
        _proposal(
            relationships=relationships,
            choices=(choice,),
            decisions=(decision,),
        )
    )

    group = view.relationship_choices[0]
    assert group.label == "2 relationship alternatives · Human decision required"
    assert group.semantic == "attention"
    assert group.preferred_candidate_ids == ("MCR-000001",)
    assert view.required_decisions[0].title == "Choose relationship alternative"


def test_ready_gate_is_positive_only_without_decisions_or_blockers():
    view = build_model_proposal_presentation(
        _proposal(
            elements=(_element(status="accepted"),),
            relationships=(_relationship(status="rejected"),),
            decisions=(),
            gate="ready",
        )
    )

    assert view.readiness.total_candidates == 2
    assert view.readiness.reviewed_candidates == 2
    assert view.readiness.accepted_candidates == 1
    assert view.readiness.rejected_candidates == 1
    assert view.readiness.status_label == "Ready for engineering-model assembly"
    assert view.readiness.semantic == "positive"
    assert view.readiness.can_assemble is True


def test_blocking_issue_overrides_ready_visual_semantics():
    blocking = (
        SimpleNamespace(
            code="repository_issue",
            message="Repository integrity issue.",
        ),
    )
    view = build_model_proposal_presentation(
        _proposal(
            elements=(_element(status="accepted"),),
            relationships=(_relationship(status="accepted"),),
            decisions=(),
            blocking=blocking,
            gate="blocked",
        )
    )

    assert view.readiness.blocking_issues == 1
    assert view.readiness.semantic == "blocking"
    assert view.readiness.can_assemble is False


def test_structural_deviation_preserves_exact_target_and_review_state():
    deviation = SimpleNamespace(
        target_type="relationship_candidate",
        candidate_id="MCR-000001",
        conformance_status="deviation",
        finding_ids=("FND-001",),
        deviation_ids=("DEV-001",),
        review_status="pending",
        rationale="Relationship differs from the structural profile.",
    )
    view = build_model_proposal_presentation(
        _proposal(deviations=(deviation,))
    )

    projected = view.deviations[0]
    assert projected.candidate_id == "MCR-000001"
    assert projected.title == "system → contains → component"
    assert projected.semantic == "attention"
    assert projected.deviation_ids == ("DEV-001",)


def test_comparability_reduction_is_attention_not_approval():
    proposal = _proposal()
    proposal.comparability_summary = _comparability(
        neutral_count=0,
        reduces_count=1,
        deviation_ids=("DEV-001",),
    )

    view = build_model_proposal_presentation(proposal)

    assert view.comparability.semantic == "attention"
    assert "reduce structural comparability" in view.comparability.label
    assert view.comparability.deviation_ids == ("DEV-001",)


def test_projection_fails_closed_when_structural_overview_mismatches_candidates():
    proposal = _proposal()
    proposal.structural_overview = SimpleNamespace(
        nodes=(SimpleNamespace(candidate_id="MCE-999999"),),
        edges=(SimpleNamespace(candidate_id="MCR-000001"),),
        model_areas=("system_logical",),
    )

    with pytest.raises(GuidedWorkflowValidationError):
        build_model_proposal_presentation(proposal)


def test_projection_fails_closed_when_decision_targets_unknown_candidate():
    decision = SimpleNamespace(
        decision_key="element:MCE-999999",
        target_type="element_candidate",
        target_ids=("MCE-999999",),
        reason="No decision.",
        recommended_action="Review.",
    )

    with pytest.raises(GuidedWorkflowValidationError):
        build_model_proposal_presentation(
            _proposal(decisions=(decision,))
        )


def test_presentation_types_are_immutable():
    view = build_model_proposal_presentation(_proposal())

    with pytest.raises(FrozenInstanceError):
        view.readiness.status_label = "changed"
