from __future__ import annotations

from dataclasses import FrozenInstanceError
from types import SimpleNamespace

import pytest

from modules.guided_workflow import (
    GuidedWorkflowValidationError,
    build_processing_source_view,
    build_review_item_view,
    build_review_queue_item_view,
)


def _source():
    return SimpleNamespace(
        project_id="123456",
        source_id="SRC-000001",
        source_role="engineering_source",
        original_filename="requirements.md",
        media_type="text/markdown",
        size_bytes=240,
        sha256="a" * 64,
        registered_at="2026-08-16T08:00:00+00:00",
    )


def _execution(**overrides):
    values = {
        "project_id": "123456",
        "source_id": "SRC-000001",
        "processing_run_id": None,
        "attempt_id": None,
        "run_state": None,
        "processing_stage": None,
        "failure_reason": None,
        "blocked_reason": None,
        "pending_review": False,
        "configuration_fingerprint": None,
        "can_start_new": True,
        "can_retry": False,
        "recovery_required": False,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def _queue(**overrides):
    values = {
        "project_id": "123456",
        "source_id": "SRC-000001",
        "original_filename": "requirements.md",
        "processing_run_id": "PRN-000001",
        "attempt_id": "ATT-000001",
        "run_state": "awaiting_review",
        "pending_review": True,
        "is_current_processing_run": True,
        "review_document_ids": ("RVD-000001",),
        "review_document_id": "RVD-000001",
        "review_document_version_id": "RVV-000001",
        "version_number": 1,
        "version_state": "draft",
        "head_revision_id": "RVR-000001",
        "review_item_count": 4,
        "review_outcome_counts": (
            ("open", 1),
            ("deferred", 1),
            ("accepted", 2),
        ),
        "finalization_eligible": False,
        "finalization_blocking_issue_codes": (),
        "promotion_eligible": False,
        "promotion_blocking_issue_codes": (),
        "promotable_review_item_ids": (),
        "active_approved_input_ids": (),
        "inactive_approved_input_ids": (),
        "workflow_status": "draft_review",
        "issue_codes": (),
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def _content():
    return SimpleNamespace(
        title="Remote control",
        primary_text="The system shall support remote control.",
        description="Engineering statement derived from the source.",
    )


def _item(**overrides):
    values = {
        "review_item_id": "RIT-000001",
        "review_item_kind": "element",
        "current_content": _content(),
        "effective_review_outcome": "open",
        "lineage_operation": "initial",
        "item_content_fingerprint": "b" * 64,
        "source_evidence_references": (object(),),
        "consensus_evidence_references": (object(),),
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def _proposal(
    proposal_id,
    persona_id,
    *,
    agent_id=None,
    text="The system shall support remote control.",
):
    return SimpleNamespace(
        review_item_id="RIT-000001",
        stable_subject_key="remote_control",
        proposal_key=f"{persona_id}:{proposal_id}",
        proposal_kind="element",
        agent_id=agent_id or persona_id,
        persona_id=persona_id,
        proposal_id=proposal_id,
        review_state="proposed",
        proposed_title="Remote control",
        proposed_primary_text=text,
        proposed_description="Proposal description.",
        proposed_information_type="requirement",
        framework_assignment_values=(),
        source_assignments=(),
        rationale="Derived from source evidence.",
        confidence="high",
        generation_readiness="ready",
        supporting_evidence=("source-1",),
        missing_evidence=(),
        artifact_id=f"ART-{proposal_id}",
        artifact_content_fingerprint="c" * 64,
        proposal_content_fingerprint="d" * 64,
    )


def _fact(**overrides):
    values = {
        "review_item_id": "RIT-000001",
        "item_content_fingerprint": "b" * 64,
        "review_status": "open",
        "review_item_kind": "element",
        "proposed_classifications": ("requirement",),
        "effective_classifications": ("requirement",),
        "proposed_framework_assignments": (),
        "effective_framework_assignments": (),
        "agent_identities": ("a1", "a2", "a3"),
        "confidence_levels": ("high",),
        "consensus_states": ("full_agreement",),
        "agent_disagreement_state": "absent",
        "human_modification_state": "unmodified",
        "source_identities": ("SRC-000001",),
        "evidence_sufficiency_state": "sufficient",
        "relationship_validation_status": "not_applicable",
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_processing_view_is_filename_first_and_ready_without_run():
    view = build_processing_source_view(_source(), _execution())

    assert view.filename == "requirements.md"
    assert view.role_label == "Engineering source"
    assert view.status_label == "Ready to process"
    assert view.next_action == "Run processing"
    assert view.source_id == "SRC-000001"


def test_processing_view_routes_awaiting_review_to_human_review():
    view = build_processing_source_view(
        _source(),
        _execution(
            processing_run_id="PRN-000001",
            attempt_id="ATT-000001",
            run_state="awaiting_review",
            pending_review=True,
            can_start_new=False,
        ),
    )

    assert view.status_label == "Ready for Human Review"
    assert view.semantic == "attention"
    assert view.next_action == "Continue to Human Review"
    assert view.processing_run_id == "PRN-000001"


def test_processing_failure_keeps_retry_semantics_from_authoritative_state():
    view = build_processing_source_view(
        _source(),
        _execution(
            processing_run_id="PRN-000001",
            attempt_id="ATT-000002",
            run_state="failed",
            failure_reason="agentic_ingestion_failed",
            can_start_new=False,
            can_retry=True,
        ),
    )

    assert view.semantic == "blocking"
    assert view.next_action == "Retry processing"
    assert view.failure_reason == "agentic_ingestion_failed"


def test_processing_projection_rejects_cross_source_state():
    with pytest.raises(GuidedWorkflowValidationError):
        build_processing_source_view(
            _source(),
            _execution(source_id="SRC-999999"),
        )


def test_review_queue_counts_open_deferred_and_unresolved_as_human_work():
    view = build_review_queue_item_view(
        _queue(
            review_outcome_counts=(
                ("open", 1),
                ("deferred", 2),
                ("unresolved", 1),
                ("accepted", 3),
            ),
            review_item_count=7,
        )
    )

    assert view.decisions_required == 4
    assert view.status_label == "Human Review in progress"
    assert view.next_action == "Continue review"


def test_review_queue_exposes_approved_input_as_positive_result():
    view = build_review_queue_item_view(
        _queue(
            workflow_status="approved_input_available",
            review_outcome_counts=(("accepted", 4),),
            active_approved_input_ids=("AIN-000001", "AIN-000002"),
        )
    )

    assert view.decisions_required == 0
    assert view.semantic == "positive"
    assert view.status_label == "Approved Input available"
    assert view.active_approved_input_count == 2


def test_review_item_groups_multiple_runs_under_one_persona_column():
    view = build_review_item_view(
        _item(),
        proposal_details=(
            _proposal("P-001", "systems_engineer", agent_id="agent-run-1"),
            _proposal("P-002", "systems_engineer", agent_id="agent-run-2"),
            _proposal("P-003", "critical_reviewer"),
        ),
        filter_fact=_fact(),
    )

    assert len(view.persona_columns) == 2
    systems = next(
        column
        for column in view.persona_columns
        if column.persona_id == "systems_engineer"
    )
    assert len(systems.proposals) == 2
    assert systems.agent_ids == ("agent-run-1", "agent-run-2")


def test_full_agreement_is_positive_but_open_item_still_requires_human_decision():
    view = build_review_item_view(
        _item(effective_review_outcome="open"),
        proposal_details=(
            _proposal("P-001", "systems_engineer"),
            _proposal("P-002", "critical_reviewer"),
            _proposal("P-003", "completeness_reviewer"),
        ),
        filter_fact=_fact(
            consensus_states=("full_agreement",),
            agent_disagreement_state="absent",
        ),
    )

    assert view.variance.semantic == "positive"
    assert view.variance.label == "Unanimous · 3 Personas agree"
    assert view.decision_required is True
    assert view.decision_label == "Human decision required"


def test_majority_with_disagreement_is_visible_attention():
    view = build_review_item_view(
        _item(),
        proposal_details=(
            _proposal("P-001", "systems_engineer"),
            _proposal(
                "P-002",
                "critical_reviewer",
                text="Only an authorized consumer may control the system.",
            ),
            _proposal("P-003", "completeness_reviewer"),
        ),
        filter_fact=_fact(
            consensus_states=("majority_with_disagreement",),
            agent_disagreement_state="present",
        ),
    )

    assert view.variance.consensus_level == "majority"
    assert view.variance.variance_level == "medium"
    assert view.variance.semantic == "attention"
    assert view.variance.label == (
        "Majority with disagreement · 3 Personas compared"
    )


def test_missing_consensus_is_neutral_and_not_invented():
    view = build_review_item_view(
        _item(
            review_item_kind="relationship",
            consensus_evidence_references=(),
        ),
        proposal_details=(
            _proposal("P-001", "systems_engineer"),
            _proposal("P-002", "critical_reviewer"),
        ),
        filter_fact=_fact(
            review_item_kind="relationship",
            consensus_states=("not_available",),
            agent_disagreement_state="not_available",
            relationship_validation_status="valid",
        ),
    )

    assert view.variance.consensus_level == "incomplete"
    assert view.variance.semantic == "neutral"
    assert view.variance.label == "Consensus not available"


def test_review_item_preserves_exact_technical_binding_under_focused_projection():
    view = build_review_item_view(
        _item(),
        proposal_details=(_proposal("P-001", "systems_engineer"),),
        filter_fact=_fact(),
    )

    assert view.review_item_id == "RIT-000001"
    assert view.item_content_fingerprint == "b" * 64
    assert view.source_evidence_count == 1
    assert view.consensus_evidence_count == 1


def test_review_item_rejects_stale_filter_fact_binding():
    with pytest.raises(GuidedWorkflowValidationError):
        build_review_item_view(
            _item(),
            proposal_details=(_proposal("P-001", "systems_engineer"),),
            filter_fact=_fact(item_content_fingerprint="stale-fingerprint"),
        )


def test_processing_and_review_presentation_types_are_immutable():
    view = build_processing_source_view(_source(), _execution())

    with pytest.raises(FrozenInstanceError):
        view.filename = "changed.md"


def test_single_persona_does_not_claim_inter_persona_agreement():
    view = build_review_item_view(
        _item(effective_review_outcome="open"),
        proposal_details=(
            _proposal("P-001", "systems_engineer"),
        ),
        filter_fact=_fact(
            consensus_states=("full_agreement",),
            agent_disagreement_state="absent",
        ),
    )

    assert view.variance.consensus_level == "incomplete"
    assert view.variance.variance_level == "not_assessable"
    assert view.variance.semantic == "neutral"
    assert (
        view.variance.label
        == "Single Persona result · agreement cannot be assessed"
    )
    assert view.decision_required is True
