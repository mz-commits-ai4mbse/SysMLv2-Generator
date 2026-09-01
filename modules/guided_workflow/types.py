"""Immutable engineer-facing presentation types for the Guided Workflow."""

from __future__ import annotations

from dataclasses import dataclass


GUIDED_WORKFLOW_STAGE_IDS = (
    "project_sources",
    "processing",
    "human_review",
    "project_reconciliation",
    "model_proposal",
    "final_model_review",
    "published_output",
)

GUIDED_WORKFLOW_STAGE_LABELS = {
    "project_sources": "Project & Sources",
    "processing": "Processing",
    "human_review": "Human Review & Approved Input",
    "project_reconciliation": "Project Fit / Multi-Source Readiness",
    "model_proposal": "Model Proposal & Candidate Review",
    "final_model_review": "Final Model Review",
    "published_output": "Published Output",
}

GUIDED_WORKFLOW_PRESENTATION_STATUSES = frozenset(
    {
        "not_started",
        "in_progress",
        "action_required",
        "ready",
        "complete",
        "blocked",
        "unavailable",
    }
)

GUIDED_PRESENTATION_SEMANTICS = frozenset(
    {
        "positive",
        "attention",
        "blocking",
        "neutral",
        "informational",
    }
)

GUIDED_CONSENSUS_LEVELS = frozenset(
    {
        "unanimous",
        "majority",
        "single",
        "none",
        "incomparable",
        "incomplete",
    }
)

GUIDED_VARIANCE_LEVELS = frozenset(
    {
        "low",
        "medium",
        "high",
    }
)

GUIDED_PERSONA_STABILITY_LEVELS = frozenset(
    {
        "stable",
        "unstable",
        "indeterminate",
        "not_measured",
        "incomplete",
    }
)

GUIDED_DECISION_PRESENTATION_STATES = frozenset(
    {
        "required",
        "resolved",
        "blocked",
        "not_required",
    }
)


@dataclass(frozen=True, slots=True)
class GuidedEngineeringContentView:
    """One engineer-readable subject with technical detail intentionally hidden."""

    entity_id: str
    content_kind: str
    title: str
    primary_text: str
    secondary_text: str | None
    source_label: str | None
    traceability_available: bool


@dataclass(frozen=True, slots=True)
class GuidedProposalView:
    """One exact proposal prepared for Human comparison."""

    proposal_id: str
    title: str
    primary_text: str
    secondary_text: str | None
    confidence: str | None
    rationale: str | None
    supporting_evidence_count: int
    missing_evidence_count: int


@dataclass(frozen=True, slots=True)
class GuidedPersonaResultView:
    """One Persona column; repeated runs remain inside this Persona."""

    persona_id: str
    persona_label: str
    stability_level: str
    run_count: int
    proposals: tuple[GuidedProposalView, ...]


@dataclass(frozen=True, slots=True)
class GuidedVarianceView:
    """Human-readable consensus and variance without approval semantics."""

    consensus_level: str
    variance_level: str
    semantic: str
    label: str
    explanation: str
    total_personas: int
    supporting_personas: tuple[str, ...]
    dissenting_personas: tuple[str, ...]
    omitting_personas: tuple[str, ...]
    review_required: bool


@dataclass(frozen=True, slots=True)
class GuidedDecisionAlternativeView:
    """One Human-readable alternative; authority remains in the domain service."""

    alternative_key: str
    label: str
    summary: str | None
    source_entity_id: str | None


@dataclass(frozen=True, slots=True)
class GuidedDecisionView:
    """Presentation of one Human decision, never the decision authority itself."""

    decision_key: str
    subject: str
    prompt: str
    presentation_state: str
    authority_domain: str
    target_entity_id: str
    alternatives: tuple[GuidedDecisionAlternativeView, ...]


@dataclass(frozen=True, slots=True)
class GuidedComparisonView:
    """Side-by-side Persona comparison for one engineering subject."""

    subject: GuidedEngineeringContentView
    persona_results: tuple[GuidedPersonaResultView, ...]
    variance: GuidedVarianceView
    decision: GuidedDecisionView | None


@dataclass(frozen=True, slots=True)
class GuidedWorkflowStageView:
    """One non-authoritative stage projection for engineer navigation."""

    stage_id: str
    label: str
    presentation_status: str
    semantic: str
    summary: str
    decision_count: int
    variance_attention_count: int
    blocking_issue_count: int
    action_label: str | None
    target_entity_id: str | None


@dataclass(frozen=True, slots=True)
class EngineerWorkSummary:
    """Compact 'Your work' summary for the selected Project."""

    decisions_required: int
    variance_attention_count: int
    blocking_issue_count: int
    confirmed_result_count: int
    completed_stage_count: int


@dataclass(frozen=True, slots=True)
class GuidedWorkflowView:
    """Complete deterministic engineer-facing workflow projection."""

    project_id: str
    work_summary: EngineerWorkSummary
    stages: tuple[GuidedWorkflowStageView, ...]
    next_stage_id: str | None
    next_action: str | None
