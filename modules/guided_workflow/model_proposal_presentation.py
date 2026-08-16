"""Deterministic engineer-facing Model Proposal presentation projection."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .errors import GuidedWorkflowValidationError


_ACTION_REQUIRED_STATES = frozenset({"pending", "deferred", "stale"})
_ACCEPTED_STATES = frozenset({"accepted", "accepted_exception"})
_TERMINAL_STATES = frozenset({"accepted", "accepted_exception", "rejected"})
_SUPPORTED_REVIEW_STATES = frozenset(
    {"pending", "deferred", "stale", "accepted", "accepted_exception", "rejected"}
)
_SUPPORTED_GATE_STATES = frozenset({"not_ready", "blocked", "ready"})


@dataclass(frozen=True, slots=True)
class GuidedModelArchitectureNodeView:
    """One proposed model element in engineer-readable form."""

    candidate_id: str
    name: str
    model_area: str
    element_type: str
    support_level: str
    conformance_status: str
    review_status: str
    decision_required: bool
    approved_input_ids: tuple[str, ...]
    assumptions: tuple[str, ...]
    missing_information: tuple[str, ...]
    rationale: str


@dataclass(frozen=True, slots=True)
class GuidedModelArchitectureEdgeView:
    """One proposed relationship with exact Candidate identity retained."""

    candidate_id: str
    source: str
    relationship: str
    target: str
    relationship_family: str
    priority_class: str
    comparability_impact: str
    resolution_status: str
    conformance_status: str
    review_status: str
    decision_required: bool
    relationship_choice_key: str | None
    approved_input_ids: tuple[str, ...]
    assumptions: tuple[str, ...]
    missing_information: tuple[str, ...]
    rationale: str


@dataclass(frozen=True, slots=True)
class GuidedModelRelationshipChoiceView:
    """One authoritative relationship-alternative group."""

    choice_key: str
    candidate_ids: tuple[str, ...]
    preferred_candidate_ids: tuple[str, ...]
    accepted_candidate_ids: tuple[str, ...]
    review_required: bool
    label: str
    semantic: str


@dataclass(frozen=True, slots=True)
class GuidedModelDecisionView:
    """One existing required Human Candidate decision."""

    decision_key: str
    target_type: str
    target_ids: tuple[str, ...]
    title: str
    reason: str
    recommended_action: str


@dataclass(frozen=True, slots=True)
class GuidedModelDeviationView:
    """One structure/profile deviation without changing its authority meaning."""

    target_type: str
    candidate_id: str
    title: str
    conformance_status: str
    review_status: str
    finding_ids: tuple[str, ...]
    deviation_ids: tuple[str, ...]
    rationale: str
    semantic: str


@dataclass(frozen=True, slots=True)
class GuidedModelComparabilityView:
    """Compact structural-comparability summary."""

    improves_count: int
    neutral_count: int
    reduces_count: int
    unknown_count: int
    label: str
    semantic: str
    comparison_anchor_ids: tuple[str, ...]
    deviation_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class GuidedModelReadinessView:
    """Human-review progress plus authoritative Phase-I gate projection."""

    phase_i_gate_status: str
    status_label: str
    semantic: str
    total_candidates: int
    reviewed_candidates: int
    accepted_candidates: int
    rejected_candidates: int
    pending_candidates: int
    deferred_candidates: int
    stale_candidates: int
    decisions_required: int
    blocking_issues: int
    can_assemble: bool


@dataclass(frozen=True, slots=True)
class GuidedModelProposalPresentation:
    """Complete deterministic Focused/Technical Model Proposal projection."""

    candidate_set_id: str
    candidate_set_content_fingerprint: str
    summary: str
    architecture_nodes: tuple[GuidedModelArchitectureNodeView, ...]
    architecture_edges: tuple[GuidedModelArchitectureEdgeView, ...]
    relationship_choices: tuple[GuidedModelRelationshipChoiceView, ...]
    required_decisions: tuple[GuidedModelDecisionView, ...]
    deviations: tuple[GuidedModelDeviationView, ...]
    comparability: GuidedModelComparabilityView
    readiness: GuidedModelReadinessView
    next_action: str
    generation_rationale_summary: str


def build_model_proposal_presentation(
    proposal: Any,
) -> GuidedModelProposalPresentation:
    """Project one exact ModelProposalView without introducing new authority."""

    candidate_set_id = _required_text(
        getattr(proposal, "candidate_set_id", None),
        "Candidate Set identity",
    )
    fingerprint = _required_text(
        getattr(proposal, "candidate_set_content_fingerprint", None),
        "Candidate Set fingerprint",
    )
    summary = _required_text(
        getattr(proposal, "summary", None),
        "Model Proposal summary",
    )
    next_action = _required_text(
        getattr(proposal, "next_action", None),
        "Model Proposal next action",
    )
    generation_rationale = _required_text(
        getattr(proposal, "generation_rationale_summary", None),
        "Model Proposal generation rationale",
    )

    elements = tuple(getattr(proposal, "proposed_elements", ()))
    relationships = tuple(getattr(proposal, "proposed_relationships", ()))

    nodes = tuple(_build_node(item) for item in elements)
    edges = tuple(_build_edge(item) for item in relationships)

    _validate_unique_ids(
        tuple(item.candidate_id for item in nodes),
        "element Candidate",
    )
    _validate_unique_ids(
        tuple(item.candidate_id for item in edges),
        "relationship Candidate",
    )
    _validate_structural_overview(proposal, nodes, edges)

    node_by_id = {item.candidate_id: item for item in nodes}
    edge_by_id = {item.candidate_id: item for item in edges}

    choices = tuple(
        _build_choice(item, edge_by_id)
        for item in tuple(getattr(proposal, "relationship_choice_groups", ()))
    )
    decisions = tuple(
        _build_decision(item, node_by_id, edge_by_id)
        for item in tuple(getattr(proposal, "required_human_decisions", ()))
    )
    deviations = tuple(
        _build_deviation(item, node_by_id, edge_by_id)
        for item in tuple(getattr(proposal, "profile_deviations", ()))
    )

    comparability = _build_comparability(
        getattr(proposal, "comparability_summary", None)
    )
    blocking = tuple(getattr(proposal, "blocking_issues", ()))
    readiness = _build_readiness(
        proposal,
        nodes,
        edges,
        decisions_required=len(decisions),
        blocking_issues=len(blocking),
    )

    return GuidedModelProposalPresentation(
        candidate_set_id=candidate_set_id,
        candidate_set_content_fingerprint=fingerprint,
        summary=summary,
        architecture_nodes=nodes,
        architecture_edges=edges,
        relationship_choices=choices,
        required_decisions=decisions,
        deviations=deviations,
        comparability=comparability,
        readiness=readiness,
        next_action=next_action,
        generation_rationale_summary=generation_rationale,
    )


def _build_node(item: Any) -> GuidedModelArchitectureNodeView:
    candidate_id = _required_text(
        getattr(item, "candidate_id", None),
        "element Candidate identity",
    )
    state = _review_status(item)
    return GuidedModelArchitectureNodeView(
        candidate_id=candidate_id,
        name=_required_text(
            getattr(item, "proposed_name", None),
            f"element Candidate {candidate_id} name",
        ),
        model_area=_required_text(
            getattr(item, "model_area", None),
            f"element Candidate {candidate_id} model area",
        ),
        element_type=_required_text(
            getattr(item, "element_type", None),
            f"element Candidate {candidate_id} type",
        ),
        support_level=_required_text(
            getattr(item, "support_level", None),
            f"element Candidate {candidate_id} support",
        ),
        conformance_status=_required_text(
            getattr(item, "conformance_status", None),
            f"element Candidate {candidate_id} conformance",
        ),
        review_status=state,
        decision_required=state in _ACTION_REQUIRED_STATES,
        approved_input_ids=_string_tuple(
            getattr(item, "approved_input_ids", ())
        ),
        assumptions=_string_tuple(getattr(item, "assumptions", ())),
        missing_information=_string_tuple(
            getattr(item, "missing_information", ())
        ),
        rationale=_optional_text(getattr(item, "rationale", None)),
    )


def _build_edge(item: Any) -> GuidedModelArchitectureEdgeView:
    candidate_id = _required_text(
        getattr(item, "candidate_id", None),
        "relationship Candidate identity",
    )
    state = _review_status(item)
    source_status = _required_text(
        getattr(item, "source_resolution_status", None),
        f"relationship Candidate {candidate_id} source resolution",
    )
    target_status = _required_text(
        getattr(item, "target_resolution_status", None),
        f"relationship Candidate {candidate_id} target resolution",
    )

    if source_status == "resolved" and target_status == "resolved":
        resolution = "resolved"
    elif "ambiguous" in {source_status, target_status}:
        resolution = "ambiguous"
    else:
        resolution = "unresolved"

    choice_key = getattr(item, "relationship_choice_key", None)
    if choice_key is not None:
        choice_key = _required_text(
            choice_key,
            f"relationship Candidate {candidate_id} choice key",
        )

    return GuidedModelArchitectureEdgeView(
        candidate_id=candidate_id,
        source=_required_text(
            getattr(item, "source_subject_key", None),
            f"relationship Candidate {candidate_id} source",
        ),
        relationship=_required_text(
            getattr(item, "semantic_intent", None),
            f"relationship Candidate {candidate_id} semantic intent",
        ),
        target=_required_text(
            getattr(item, "target_subject_key", None),
            f"relationship Candidate {candidate_id} target",
        ),
        relationship_family=_required_text(
            getattr(item, "relationship_family", None),
            f"relationship Candidate {candidate_id} family",
        ),
        priority_class=_required_text(
            getattr(item, "priority_class", None),
            f"relationship Candidate {candidate_id} priority",
        ),
        comparability_impact=_required_text(
            getattr(item, "comparability_impact", None),
            f"relationship Candidate {candidate_id} comparability",
        ),
        resolution_status=resolution,
        conformance_status=_required_text(
            getattr(item, "conformance_status", None),
            f"relationship Candidate {candidate_id} conformance",
        ),
        review_status=state,
        decision_required=state in _ACTION_REQUIRED_STATES,
        relationship_choice_key=choice_key,
        approved_input_ids=_string_tuple(
            getattr(item, "approved_input_ids", ())
        ),
        assumptions=_string_tuple(getattr(item, "assumptions", ())),
        missing_information=_string_tuple(
            getattr(item, "missing_information", ())
        ),
        rationale=_optional_text(getattr(item, "rationale", None)),
    )


def _build_choice(
    item: Any,
    edge_by_id: dict[str, GuidedModelArchitectureEdgeView],
) -> GuidedModelRelationshipChoiceView:
    key = _required_text(
        getattr(item, "relationship_choice_key", None),
        "relationship choice key",
    )
    candidate_ids = _string_tuple(getattr(item, "candidate_ids", ()))
    if len(candidate_ids) < 2:
        raise GuidedWorkflowValidationError(
            "Relationship choice presentation requires at least two alternatives."
        )
    if any(candidate_id not in edge_by_id for candidate_id in candidate_ids):
        raise GuidedWorkflowValidationError(
            "Relationship choice references a Candidate outside the exact Model Proposal."
        )

    preferred = _string_tuple(
        getattr(item, "preferred_candidate_ids", ())
    )
    accepted = _string_tuple(
        getattr(item, "accepted_candidate_ids", ())
    )
    if not set(preferred).issubset(candidate_ids):
        raise GuidedWorkflowValidationError(
            "Preferred relationship alternative is outside its choice group."
        )
    if not set(accepted).issubset(candidate_ids):
        raise GuidedWorkflowValidationError(
            "Accepted relationship alternative is outside its choice group."
        )

    review_required = bool(getattr(item, "review_required", False))
    if review_required:
        label = (
            f"{len(candidate_ids)} relationship alternatives · "
            "Human decision required"
        )
        semantic = "attention"
    elif len(accepted) == 1:
        label = (
            f"{len(candidate_ids)} relationship alternatives · "
            "choice resolved"
        )
        semantic = "positive"
    else:
        label = f"{len(candidate_ids)} relationship alternatives"
        semantic = "neutral"

    return GuidedModelRelationshipChoiceView(
        choice_key=key,
        candidate_ids=candidate_ids,
        preferred_candidate_ids=preferred,
        accepted_candidate_ids=accepted,
        review_required=review_required,
        label=label,
        semantic=semantic,
    )


def _build_decision(
    item: Any,
    node_by_id: dict[str, GuidedModelArchitectureNodeView],
    edge_by_id: dict[str, GuidedModelArchitectureEdgeView],
) -> GuidedModelDecisionView:
    key = _required_text(
        getattr(item, "decision_key", None),
        "Model Proposal decision key",
    )
    target_type = _required_text(
        getattr(item, "target_type", None),
        f"Model Proposal decision {key} target type",
    )
    target_ids = _string_tuple(getattr(item, "target_ids", ()))
    if not target_ids:
        raise GuidedWorkflowValidationError(
            "Model Proposal decision must reference at least one Candidate."
        )

    if target_type == "element_candidate":
        if len(target_ids) != 1 or target_ids[0] not in node_by_id:
            raise GuidedWorkflowValidationError(
                "Element decision does not bind one exact element Candidate."
            )
        title = node_by_id[target_ids[0]].name
    elif target_type == "relationship_candidate":
        if len(target_ids) != 1 or target_ids[0] not in edge_by_id:
            raise GuidedWorkflowValidationError(
                "Relationship decision does not bind one exact relationship Candidate."
            )
        edge = edge_by_id[target_ids[0]]
        title = f"{edge.source} → {edge.relationship} → {edge.target}"
    elif target_type == "relationship_choice_group":
        if any(target_id not in edge_by_id for target_id in target_ids):
            raise GuidedWorkflowValidationError(
                "Relationship choice decision references an unavailable Candidate."
            )
        title = "Choose relationship alternative"
    else:
        raise GuidedWorkflowValidationError(
            f"Unsupported Model Proposal decision target type: {target_type}."
        )

    return GuidedModelDecisionView(
        decision_key=key,
        target_type=target_type,
        target_ids=target_ids,
        title=title,
        reason=_required_text(
            getattr(item, "reason", None),
            f"Model Proposal decision {key} reason",
        ),
        recommended_action=_required_text(
            getattr(item, "recommended_action", None),
            f"Model Proposal decision {key} action",
        ),
    )


def _build_deviation(
    item: Any,
    node_by_id: dict[str, GuidedModelArchitectureNodeView],
    edge_by_id: dict[str, GuidedModelArchitectureEdgeView],
) -> GuidedModelDeviationView:
    target_type = _required_text(
        getattr(item, "target_type", None),
        "profile deviation target type",
    )
    candidate_id = _required_text(
        getattr(item, "candidate_id", None),
        "profile deviation Candidate identity",
    )
    review_status = _required_text(
        getattr(item, "review_status", None),
        f"profile deviation {candidate_id} review state",
    )
    _validate_review_state(review_status)

    if target_type == "element_candidate":
        if candidate_id not in node_by_id:
            raise GuidedWorkflowValidationError(
                "Element profile deviation references an unavailable Candidate."
            )
        title = node_by_id[candidate_id].name
    elif target_type == "relationship_candidate":
        if candidate_id not in edge_by_id:
            raise GuidedWorkflowValidationError(
                "Relationship profile deviation references an unavailable Candidate."
            )
        edge = edge_by_id[candidate_id]
        title = f"{edge.source} → {edge.relationship} → {edge.target}"
    else:
        raise GuidedWorkflowValidationError(
            f"Unsupported profile deviation target type: {target_type}."
        )

    return GuidedModelDeviationView(
        target_type=target_type,
        candidate_id=candidate_id,
        title=title,
        conformance_status=_required_text(
            getattr(item, "conformance_status", None),
            f"profile deviation {candidate_id} conformance",
        ),
        review_status=review_status,
        finding_ids=_string_tuple(getattr(item, "finding_ids", ())),
        deviation_ids=_string_tuple(getattr(item, "deviation_ids", ())),
        rationale=_optional_text(getattr(item, "rationale", None)),
        semantic=(
            "attention"
            if review_status in _ACTION_REQUIRED_STATES
            else "informational"
        ),
    )


def _build_comparability(item: Any) -> GuidedModelComparabilityView:
    if item is None:
        raise GuidedWorkflowValidationError(
            "Model Proposal comparability summary is unavailable."
        )

    improves = _nonnegative_int(
        getattr(item, "improves_count", None),
        "comparability improves count",
    )
    neutral = _nonnegative_int(
        getattr(item, "neutral_count", None),
        "comparability neutral count",
    )
    reduces = _nonnegative_int(
        getattr(item, "reduces_count", None),
        "comparability reduces count",
    )
    unknown = _nonnegative_int(
        getattr(item, "unknown_count", None),
        "comparability unknown count",
    )

    if reduces:
        label = f"{reduces} relationship(s) reduce structural comparability"
        semantic = "attention"
    elif unknown:
        label = f"{unknown} relationship comparison(s) remain unknown"
        semantic = "attention"
    elif improves:
        label = f"{improves} relationship(s) improve structural comparability"
        semantic = "positive"
    else:
        label = "No material structural comparability change"
        semantic = "neutral"

    return GuidedModelComparabilityView(
        improves_count=improves,
        neutral_count=neutral,
        reduces_count=reduces,
        unknown_count=unknown,
        label=label,
        semantic=semantic,
        comparison_anchor_ids=_string_tuple(
            getattr(item, "comparison_anchor_ids", ())
        ),
        deviation_ids=_string_tuple(getattr(item, "deviation_ids", ())),
    )


def _build_readiness(
    proposal: Any,
    nodes: tuple[GuidedModelArchitectureNodeView, ...],
    edges: tuple[GuidedModelArchitectureEdgeView, ...],
    *,
    decisions_required: int,
    blocking_issues: int,
) -> GuidedModelReadinessView:
    gate = _required_text(
        getattr(proposal, "phase_i_gate_status", None),
        "Phase-I gate status",
    )
    if gate not in _SUPPORTED_GATE_STATES:
        raise GuidedWorkflowValidationError(
            f"Unsupported Phase-I gate status: {gate}."
        )

    states = tuple(item.review_status for item in (*nodes, *edges))
    total = len(states)
    accepted = sum(state in _ACCEPTED_STATES for state in states)
    rejected = sum(state == "rejected" for state in states)
    pending = sum(state == "pending" for state in states)
    deferred = sum(state == "deferred" for state in states)
    stale = sum(state == "stale" for state in states)
    reviewed = sum(state in _TERMINAL_STATES for state in states)

    if blocking_issues or gate == "blocked":
        label = "Blocked from engineering-model assembly"
        semantic = "blocking"
    elif decisions_required or gate == "not_ready":
        label = "Human Candidate review required"
        semantic = "attention"
    else:
        label = "Ready for engineering-model assembly"
        semantic = "positive"

    can_assemble = (
        gate == "ready"
        and decisions_required == 0
        and blocking_issues == 0
    )

    return GuidedModelReadinessView(
        phase_i_gate_status=gate,
        status_label=label,
        semantic=semantic,
        total_candidates=total,
        reviewed_candidates=reviewed,
        accepted_candidates=accepted,
        rejected_candidates=rejected,
        pending_candidates=pending,
        deferred_candidates=deferred,
        stale_candidates=stale,
        decisions_required=decisions_required,
        blocking_issues=blocking_issues,
        can_assemble=can_assemble,
    )


def _validate_structural_overview(
    proposal: Any,
    nodes: tuple[GuidedModelArchitectureNodeView, ...],
    edges: tuple[GuidedModelArchitectureEdgeView, ...],
) -> None:
    overview = getattr(proposal, "structural_overview", None)
    if overview is None:
        raise GuidedWorkflowValidationError(
            "Model Proposal structural overview is unavailable."
        )

    overview_node_ids = tuple(
        _required_text(
            getattr(item, "candidate_id", None),
            "structural overview node Candidate identity",
        )
        for item in tuple(getattr(overview, "nodes", ()))
    )
    overview_edge_ids = tuple(
        _required_text(
            getattr(item, "candidate_id", None),
            "structural overview edge Candidate identity",
        )
        for item in tuple(getattr(overview, "edges", ()))
    )

    if set(overview_node_ids) != {item.candidate_id for item in nodes}:
        raise GuidedWorkflowValidationError(
            "Structural overview does not bind the exact proposed element Candidates."
        )
    if set(overview_edge_ids) != {item.candidate_id for item in edges}:
        raise GuidedWorkflowValidationError(
            "Structural overview does not bind the exact proposed relationship Candidates."
        )


def _review_status(item: Any) -> str:
    review_state = getattr(item, "review_state", None)
    if review_state is None:
        raise GuidedWorkflowValidationError(
            "Candidate Review state is unavailable."
        )
    state = _required_text(
        getattr(review_state, "status", None),
        "Candidate Review state",
    )
    _validate_review_state(state)
    return state


def _validate_review_state(state: str) -> None:
    if state not in _SUPPORTED_REVIEW_STATES:
        raise GuidedWorkflowValidationError(
            f"Unsupported Candidate Review state: {state}."
        )


def _required_text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise GuidedWorkflowValidationError(f"{label} is unavailable.")
    return value.strip()


def _optional_text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _string_tuple(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    try:
        items = tuple(value)
    except TypeError as exc:
        raise GuidedWorkflowValidationError(
            "Expected a sequence of presentation references."
        ) from exc
    result = []
    for item in items:
        if not isinstance(item, str) or not item.strip():
            raise GuidedWorkflowValidationError(
                "Presentation references must be non-empty strings."
            )
        result.append(item.strip())
    return tuple(result)


def _nonnegative_int(value: Any, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise GuidedWorkflowValidationError(
            f"{label} must be a non-negative integer."
        )
    return value


def _validate_unique_ids(values: tuple[str, ...], label: str) -> None:
    if len(set(values)) != len(values):
        raise GuidedWorkflowValidationError(
            f"Duplicate {label} identity in Model Proposal presentation."
        )
