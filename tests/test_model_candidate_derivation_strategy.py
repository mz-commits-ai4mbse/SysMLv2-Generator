"""Tests for R5 derivation-mode recommendation and review escalation."""

from __future__ import annotations

from dataclasses import replace

import pytest

from modules.model_candidates import (
    ECO_DETERMINISTIC_MODE,
    LLM_ASSISTED_MODE,
    ModelCandidateApprovedInputReference,
    ModelCandidateProjectionCoverage,
    ModelCandidateProjectionDisposition,
    ModelCandidateReviewDecision,
    ModelCandidateReviewTargetSnapshot,
    ModelCandidateSetManifest,
    ModelCandidateSetSnapshot,
    ModelDerivationRulesReference,
    ModelElementCandidate,
    ModelStructureProfileReference,
    StructuralProfileConformance,
    assess_model_derivation_strategy,
    build_review_escalation_reason,
    validate_model_derivation_mode,
)
from modules.project_workspace.types import FrameworkTemplateReference


PROJECT_ID = "318604"
PROFILE = ModelStructureProfileReference(
    profile_id="MSP-001",
    profile_version="1.0.0",
    profile_fingerprint="a" * 64,
)


def disposition(
    approved_input_id: str,
    value: str,
) -> ModelCandidateProjectionDisposition:
    return ModelCandidateProjectionDisposition(
        approved_input_id=approved_input_id,
        approved_input_kind="element_statement",
        disposition=value,
        reason_code=f"reason_{value}",
        selected_rule_id=(
            "RULE-1" if value == "mapped" else None
        ),
        candidate_rule_ids=(),
        rationale=f"{value} rationale",
    )


def coverage(*values: str) -> ModelCandidateProjectionCoverage:
    return ModelCandidateProjectionCoverage(
        project_id=PROJECT_ID,
        model_structure_profile_reference=PROFILE,
        entries=tuple(
            disposition(
                f"AIN-{index:06d}",
                value,
            )
            for index, value in enumerate(values, start=1)
        ),
    )


def candidate_snapshot() -> ModelCandidateSetSnapshot:
    reference = ModelCandidateApprovedInputReference(
        approved_input_id="AIN-000001",
        content_fingerprint="b" * 64,
        stable_subject_key="evidence:evd-000001",
        provenance_role="direct_support",
    )
    conformance = StructuralProfileConformance(
        status="conformant",
        finding_ids=(),
        conformance_fingerprint="c" * 64,
    )
    element = ModelElementCandidate(
        schema_version="1.0.0",
        project_id=PROJECT_ID,
        candidate_set_id="MCS-000001",
        model_element_candidate_id="MCE-000001",
        candidate_subject_key="evidence:evd-000001",
        comparison_anchor_id="logical:evidence:evd-000001",
        proposed_name="Temporary remote control",
        description=None,
        model_area="logical",
        element_type="function",
        framework_assignment="LF",
        terminology_assignment=None,
        attributes=(),
        approved_input_references=(reference,),
        derivation_rationale="Deterministic mapping.",
        support_level="supported",
        assumptions=(),
        missing_information=(),
        structure_profile_conformance=conformance,
        predecessor_candidate_ids=(),
        created_at="2026-08-21T10:00:00Z",
        content_fingerprint="d" * 64,
    )
    manifest = ModelCandidateSetManifest(
        schema_version="1.0.0",
        project_id=PROJECT_ID,
        candidate_set_id="MCS-000001",
        predecessor_candidate_set_id=None,
        regeneration_reason=None,
        approved_input_references=(reference,),
        approved_input_snapshot_fingerprint="e" * 64,
        framework_template_reference=FrameworkTemplateReference(
            template_id="TURING_RFLP_FRAMEWORK",
            template_version="1.0.0",
        ),
        model_structure_profile_reference=PROFILE,
        derivation_rules_reference=ModelDerivationRulesReference(
            context_id="DERIVATION-CONTEXT",
            context_version="1.0.0",
            context_fingerprint="f" * 64,
        ),
        generation_provenance=__import__(
            "modules.model_candidates",
            fromlist=["ModelCandidateGenerationProvenance"],
        ).ModelCandidateGenerationProvenance(
            method="deterministic_profile_projection",
            recipe_reference="ADR-020:H9",
            agent_reference=None,
            model_reference=None,
            context_fingerprint="1" * 64,
        ),
        element_candidate_ids=("MCE-000001",),
        relationship_candidate_ids=(),
        created_at="2026-08-21T10:00:00Z",
        content_fingerprint="2" * 64,
    )
    return ModelCandidateSetSnapshot(
        manifest=manifest,
        element_candidates=(element,),
        relationship_candidates=(),
    )


def review_decision(
    *,
    decision_id: str,
    decision: str,
    reviewed_at: str,
) -> ModelCandidateReviewDecision:
    return ModelCandidateReviewDecision(
        schema_version="1.0.0",
        project_id=PROJECT_ID,
        model_candidate_review_decision_id=decision_id,
        target=ModelCandidateReviewTargetSnapshot(
            candidate_set_id="MCS-000001",
            candidate_set_content_fingerprint="2" * 64,
            target_type="element_candidate",
            candidate_id="MCE-000001",
            candidate_content_fingerprint="d" * 64,
            model_structure_profile_reference=PROFILE,
            structure_profile_conformance_status="conformant",
            structure_profile_conformance_fingerprint="c" * 64,
            approved_input_snapshot_fingerprint="e" * 64,
        ),
        decision=decision,
        reviewer_identity="reviewer",
        rationale=(
            "Needs a different model projection."
            if decision == "rejected"
            else None
        ),
        reviewed_at=reviewed_at,
        decision_fingerprint="3" * 64,
    )


def test_complete_deterministic_coverage_recommends_eco() -> None:
    assessment = assess_model_derivation_strategy(
        coverage=coverage(
            "mapped",
            "mapped",
            "intentionally_not_projected",
        )
    )

    assert assessment.recommended_mode == ECO_DETERMINISTIC_MODE
    assert assessment.eco_feasible is True
    assert assessment.unresolved_approved_input_ids == ()
    assert assessment.escalated_approved_input_ids == ()


def test_unresolved_projection_recommends_llm_without_forcing_mode() -> None:
    assessment = assess_model_derivation_strategy(
        coverage=coverage(
            "mapped",
            "ambiguous",
            "unmapped",
        )
    )

    assert assessment.recommended_mode == LLM_ASSISTED_MODE
    assert assessment.eco_feasible is False
    assert assessment.unresolved_approved_input_ids == (
        "AIN-000002",
        "AIN-000003",
    )

    # Recommendation is advisory: selecting Eco is syntactically valid.
    assert (
        validate_model_derivation_mode(
            ECO_DETERMINISTIC_MODE
        )
        == ECO_DETERMINISTIC_MODE
    )


def test_latest_rejected_review_escalates_mapped_approved_input() -> None:
    predecessor = candidate_snapshot()
    accepted = review_decision(
        decision_id="MCD-000001",
        decision="accepted",
        reviewed_at="2026-08-21T10:00:00Z",
    )
    rejected = review_decision(
        decision_id="MCD-000002",
        decision="rejected",
        reviewed_at="2026-08-21T11:00:00Z",
    )

    assessment = assess_model_derivation_strategy(
        coverage=coverage("mapped"),
        predecessor_candidate_set=predecessor,
        predecessor_review_decisions=(
            rejected,
            accepted,
        ),
    )

    assert assessment.eco_feasible is True
    assert assessment.recommended_mode == LLM_ASSISTED_MODE
    assert assessment.rejected_predecessor_candidate_ids == (
        "MCE-000001",
    )
    assert assessment.escalated_approved_input_ids == (
        "AIN-000001",
    )


def test_later_acceptance_removes_review_escalation() -> None:
    predecessor = candidate_snapshot()
    rejected = review_decision(
        decision_id="MCD-000001",
        decision="rejected",
        reviewed_at="2026-08-21T10:00:00Z",
    )
    accepted = review_decision(
        decision_id="MCD-000002",
        decision="accepted",
        reviewed_at="2026-08-21T11:00:00Z",
    )

    assessment = assess_model_derivation_strategy(
        coverage=coverage("mapped"),
        predecessor_candidate_set=predecessor,
        predecessor_review_decisions=(
            rejected,
            accepted,
        ),
    )

    assert assessment.recommended_mode == ECO_DETERMINISTIC_MODE
    assert assessment.rejected_predecessor_candidate_ids == ()
    assert assessment.escalated_approved_input_ids == ()


def test_review_escalation_reason_binds_predecessor_and_rejection() -> None:
    predecessor = candidate_snapshot()
    rejected = review_decision(
        decision_id="MCD-000001",
        decision="rejected",
        reviewed_at="2026-08-21T10:00:00Z",
    )
    assessment = assess_model_derivation_strategy(
        coverage=coverage("mapped"),
        predecessor_candidate_set=predecessor,
        predecessor_review_decisions=(rejected,),
    )

    reason = build_review_escalation_reason(
        assessment=assessment,
        human_reason="Architecture mapping should be reconsidered.",
    )

    assert "MCS-000001" in reason
    assert "MCE-000001" in reason
    assert "Architecture mapping should be reconsidered." in reason


def test_review_decision_from_other_candidate_set_fails_closed() -> None:
    predecessor = candidate_snapshot()
    decision = review_decision(
        decision_id="MCD-000001",
        decision="rejected",
        reviewed_at="2026-08-21T10:00:00Z",
    )
    wrong_target = replace(
        decision.target,
        candidate_set_id="MCS-000002",
    )
    wrong = replace(
        decision,
        target=wrong_target,
    )

    with pytest.raises(Exception):
        assess_model_derivation_strategy(
            coverage=coverage("mapped"),
            predecessor_candidate_set=predecessor,
            predecessor_review_decisions=(wrong,),
        )


def test_invalid_mode_fails_closed() -> None:
    with pytest.raises(Exception):
        validate_model_derivation_mode("automatic_magic")
