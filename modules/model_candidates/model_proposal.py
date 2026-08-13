"""Deterministic non-authoritative Model Proposal projection for Phase H."""

from __future__ import annotations

import json

from modules.project_workspace.workspace import DEFAULT_PROJECTS_ROOT

from .candidate_review_identifiers import (
    model_candidate_review_decision_id_sequence,
)
from .candidate_review_repository import (
    ModelCandidateReviewRepository,
)
from .errors import (
    ModelCandidateIntegrityError,
    ModelCandidatePhaseIGateError,
)
from .phase_i_read_service import ModelCandidateReadService
from .repository import ModelCandidateRepository
from .types import (
    ModelCandidateReviewDecision,
    ModelCandidateSetSnapshot,
    ModelProposalBlockingIssue,
    ModelProposalComparabilitySummary,
    ModelProposalElementView,
    ModelProposalProfileDeviation,
    ModelProposalRelationshipChoiceGroup,
    ModelProposalRelationshipView,
    ModelProposalRequiredDecision,
    ModelProposalReviewState,
    ModelProposalStructuralEdge,
    ModelProposalStructuralNode,
    ModelProposalStructuralOverview,
    ModelProposalView,
)


class ModelProposalReadService:
    """Build one coherent projection from an explicit immutable Candidate Set."""

    def __init__(
        self,
        root=DEFAULT_PROJECTS_ROOT,
        *,
        candidate_repository: ModelCandidateRepository | None = None,
        review_repository: ModelCandidateReviewRepository | None = None,
        phase_i_read_service: ModelCandidateReadService | None = None,
    ) -> None:
        self.root = root
        self._candidates = (
            ModelCandidateRepository(root=root)
            if candidate_repository is None
            else candidate_repository
        )
        self._reviews = (
            ModelCandidateReviewRepository(
                root=root,
                candidate_repository=self._candidates,
            )
            if review_repository is None
            else review_repository
        )
        self._phase_i = (
            ModelCandidateReadService(
                root=root,
                candidate_repository=self._candidates,
                review_repository=self._reviews,
            )
            if phase_i_read_service is None
            else phase_i_read_service
        )

    def load_model_proposal(
        self,
        project_id: str,
        candidate_set_id: str,
    ) -> ModelProposalView:
        """Load the proposal without changing Candidate or Review authority."""

        snapshot = self._candidates.load_candidate_set(
            project_id,
            candidate_set_id,
        )
        review_scan = self._reviews.scan_decisions(project_id)
        set_decisions = tuple(
            item
            for item in review_scan.decisions
            if item.target.candidate_set_id == candidate_set_id
        )

        review_by_target = self._latest_review_states(
            snapshot,
            set_decisions,
        )
        elements = tuple(
            self._element_view(
                item,
                review_by_target[
                    ("element_candidate", item.model_element_candidate_id)
                ],
            )
            for item in snapshot.element_candidates
        )
        relationships = tuple(
            self._relationship_view(
                item,
                review_by_target[
                    (
                        "relationship_candidate",
                        item.model_relationship_candidate_id,
                    )
                ],
            )
            for item in snapshot.relationship_candidates
        )

        choice_groups = self._relationship_choice_groups(
            snapshot,
            relationships,
        )
        deviations = self._profile_deviations(
            snapshot,
            review_by_target,
        )
        decisions = self._required_decisions(
            snapshot,
            review_by_target,
            choice_groups,
        )
        blocking = tuple(
            ModelProposalBlockingIssue(
                code=item.code,
                message=item.message,
            )
            for item in review_scan.issues
        )

        phase_i_gate_status, gate_block = self._phase_i_status(
            project_id,
            candidate_set_id,
            decisions=decisions,
            blocking=blocking,
        )
        if gate_block is not None:
            blocking = tuple(
                sorted(
                    {
                        (item.code, item.message)
                        for item in (
                            *blocking,
                            gate_block,
                        )
                    }
                )
            )
            blocking = tuple(
                ModelProposalBlockingIssue(code=code, message=message)
                for code, message in blocking
            )

        summary = self._summary(
            snapshot,
            elements,
            relationships,
            decisions,
            blocking,
        )
        next_action = self._next_action(
            decisions,
            blocking,
            phase_i_gate_status,
        )

        return ModelProposalView(
            project_id=project_id,
            candidate_set_id=candidate_set_id,
            candidate_set_content_fingerprint=(
                snapshot.manifest.content_fingerprint
            ),
            summary=summary,
            proposed_elements=elements,
            proposed_relationships=relationships,
            structural_overview=self._structural_overview(
                elements,
                relationships,
            ),
            relationship_choice_groups=choice_groups,
            comparability_summary=self._comparability_summary(
                snapshot
            ),
            profile_deviations=deviations,
            required_human_decisions=decisions,
            blocking_issues=blocking,
            generation_rationale_summary=(
                self._generation_rationale_summary(snapshot)
            ),
            phase_i_gate_status=phase_i_gate_status,
            next_action=next_action,
        )

    def _latest_review_states(
        self,
        snapshot: ModelCandidateSetSnapshot,
        decisions: tuple[ModelCandidateReviewDecision, ...],
    ) -> dict[tuple[str, str], ModelProposalReviewState]:
        result = {}
        for target_type, candidates, id_attr in (
            (
                "element_candidate",
                snapshot.element_candidates,
                "model_element_candidate_id",
            ),
            (
                "relationship_candidate",
                snapshot.relationship_candidates,
                "model_relationship_candidate_id",
            ),
        ):
            for candidate in candidates:
                candidate_id = getattr(candidate, id_attr)
                matching = tuple(
                    item
                    for item in decisions
                    if item.target.target_type == target_type
                    and item.target.candidate_id == candidate_id
                )
                latest = (
                    None
                    if not matching
                    else max(
                        matching,
                        key=lambda item: (
                            model_candidate_review_decision_id_sequence(
                                item.model_candidate_review_decision_id
                            )
                        ),
                    )
                )
                result[(target_type, candidate_id)] = (
                    self._review_state(
                        snapshot,
                        candidate,
                        latest,
                    )
                )
        return result

    def _review_state(
        self,
        snapshot: ModelCandidateSetSnapshot,
        candidate,
        decision: ModelCandidateReviewDecision | None,
    ) -> ModelProposalReviewState:
        if decision is None:
            return ModelProposalReviewState(
                status="pending",
                decision_id=None,
                decision_fingerprint=None,
                rationale=None,
            )
        target = decision.target
        exact = (
            target.candidate_set_id
            == snapshot.manifest.candidate_set_id
            and target.candidate_set_content_fingerprint
            == snapshot.manifest.content_fingerprint
            and target.candidate_content_fingerprint
            == candidate.content_fingerprint
            and target.model_structure_profile_reference
            == snapshot.manifest.model_structure_profile_reference
            and target.structure_profile_conformance_status
            == candidate.structure_profile_conformance.status
            and target.structure_profile_conformance_fingerprint
            == candidate.structure_profile_conformance.conformance_fingerprint
            and target.approved_input_snapshot_fingerprint
            == snapshot.manifest.approved_input_snapshot_fingerprint
        )
        return ModelProposalReviewState(
            status=decision.decision if exact else "stale",
            decision_id=decision.model_candidate_review_decision_id,
            decision_fingerprint=decision.decision_fingerprint,
            rationale=decision.rationale,
        )

    def _element_view(
        self,
        item,
        review_state: ModelProposalReviewState,
    ) -> ModelProposalElementView:
        return ModelProposalElementView(
            candidate_id=item.model_element_candidate_id,
            candidate_subject_key=item.candidate_subject_key,
            proposed_name=item.proposed_name,
            description=item.description,
            model_area=item.model_area,
            element_type=item.element_type,
            comparison_anchor_id=item.comparison_anchor_id,
            support_level=item.support_level,
            conformance_status=(
                item.structure_profile_conformance.status
            ),
            review_state=review_state,
            approved_input_ids=tuple(
                sorted(
                    reference.approved_input_id
                    for reference in item.approved_input_references
                )
            ),
            assumptions=item.assumptions,
            missing_information=item.missing_information,
            rationale=item.derivation_rationale,
        )

    def _relationship_view(
        self,
        item,
        review_state: ModelProposalReviewState,
    ) -> ModelProposalRelationshipView:
        return ModelProposalRelationshipView(
            candidate_id=item.model_relationship_candidate_id,
            relationship_choice_key=item.relationship_choice_key,
            source_subject_key=item.source.candidate_subject_key,
            target_subject_key=item.target.candidate_subject_key,
            source_resolution_status=item.source.resolution_status,
            target_resolution_status=item.target.resolution_status,
            relationship_family=item.relationship_family,
            semantic_intent=item.semantic_intent,
            directionality=item.directionality,
            priority_class=item.priority_assessment.priority_class,
            comparability_impact=item.comparability_assessment.impact,
            conformance_status=(
                item.structure_profile_conformance.status
            ),
            review_state=review_state,
            approved_input_ids=tuple(
                sorted(
                    reference.approved_input_id
                    for reference in item.approved_input_references
                )
            ),
            assumptions=item.assumptions,
            missing_information=item.missing_information,
            rationale=item.derivation_rationale,
        )

    def _structural_overview(
        self,
        elements: tuple[ModelProposalElementView, ...],
        relationships: tuple[ModelProposalRelationshipView, ...],
    ) -> ModelProposalStructuralOverview:
        nodes = tuple(
            ModelProposalStructuralNode(
                candidate_id=item.candidate_id,
                label=item.proposed_name,
                model_area=item.model_area,
                element_type=item.element_type,
                review_status=item.review_state.status,
            )
            for item in elements
        )
        edges = tuple(
            ModelProposalStructuralEdge(
                candidate_id=item.candidate_id,
                source_subject_key=item.source_subject_key,
                target_subject_key=item.target_subject_key,
                semantic_intent=item.semantic_intent,
                relationship_family=item.relationship_family,
                review_status=item.review_state.status,
                resolution_status=self._combined_resolution_status(item),
            )
            for item in relationships
        )
        return ModelProposalStructuralOverview(
            nodes=nodes,
            edges=edges,
            model_areas=tuple(
                sorted({item.model_area for item in elements})
            ),
        )

    def _combined_resolution_status(
        self,
        item: ModelProposalRelationshipView,
    ) -> str:
        statuses = {
            item.source_resolution_status,
            item.target_resolution_status,
        }
        if statuses == {"resolved"}:
            return "resolved"
        if "ambiguous" in statuses:
            return "ambiguous"
        return "unresolved"

    def _relationship_choice_groups(
        self,
        snapshot: ModelCandidateSetSnapshot,
        relationships: tuple[ModelProposalRelationshipView, ...],
    ) -> tuple[ModelProposalRelationshipChoiceGroup, ...]:
        by_id = {
            item.candidate_id: item for item in relationships
        }
        groups: dict[str, list[str]] = {}
        for item in snapshot.relationship_candidates:
            if item.relationship_choice_key is None:
                continue
            groups.setdefault(
                item.relationship_choice_key,
                [],
            ).append(item.model_relationship_candidate_id)

        result = []
        for choice_key in sorted(groups):
            candidate_ids = tuple(sorted(groups[choice_key]))
            preferred = tuple(
                candidate_id
                for candidate_id in candidate_ids
                if next(
                    item
                    for item in snapshot.relationship_candidates
                    if item.model_relationship_candidate_id == candidate_id
                ).priority_assessment.priority_class
                == "preferred"
            )
            accepted = tuple(
                candidate_id
                for candidate_id in candidate_ids
                if by_id[candidate_id].review_state.status
                in {"accepted", "accepted_exception"}
            )
            terminal = all(
                by_id[candidate_id].review_state.status
                in {
                    "accepted",
                    "accepted_exception",
                    "rejected",
                }
                for candidate_id in candidate_ids
            )
            result.append(
                ModelProposalRelationshipChoiceGroup(
                    relationship_choice_key=choice_key,
                    candidate_ids=candidate_ids,
                    preferred_candidate_ids=preferred,
                    accepted_candidate_ids=accepted,
                    review_required=(
                        not terminal or len(accepted) != 1
                    ),
                )
            )
        return tuple(result)

    def _comparability_summary(
        self,
        snapshot: ModelCandidateSetSnapshot,
    ) -> ModelProposalComparabilitySummary:
        assessments = tuple(
            item.comparability_assessment
            for item in snapshot.relationship_candidates
        )
        counts = {
            "improves": 0,
            "neutral": 0,
            "reduces": 0,
            "unknown": 0,
        }
        anchors = set()
        deviations = set()
        for item in assessments:
            counts[item.impact] += 1
            anchors.update(item.comparison_anchor_ids)
            deviations.update(item.deviation_ids)
        return ModelProposalComparabilitySummary(
            improves_count=counts["improves"],
            neutral_count=counts["neutral"],
            reduces_count=counts["reduces"],
            unknown_count=counts["unknown"],
            comparison_anchor_ids=tuple(sorted(anchors)),
            deviation_ids=tuple(sorted(deviations)),
        )

    def _profile_deviations(
        self,
        snapshot: ModelCandidateSetSnapshot,
        review_states: dict[tuple[str, str], ModelProposalReviewState],
    ) -> tuple[ModelProposalProfileDeviation, ...]:
        result = []
        for target_type, candidates, id_attr in (
            (
                "element_candidate",
                snapshot.element_candidates,
                "model_element_candidate_id",
            ),
            (
                "relationship_candidate",
                snapshot.relationship_candidates,
                "model_relationship_candidate_id",
            ),
        ):
            for item in candidates:
                candidate_id = getattr(item, id_attr)
                conformance = item.structure_profile_conformance
                deviation_ids = (
                    ()
                    if target_type == "element_candidate"
                    else item.comparability_assessment.deviation_ids
                )
                if (
                    conformance.status == "conformant"
                    and not conformance.finding_ids
                    and not deviation_ids
                ):
                    continue
                result.append(
                    ModelProposalProfileDeviation(
                        target_type=target_type,
                        candidate_id=candidate_id,
                        conformance_status=conformance.status,
                        finding_ids=conformance.finding_ids,
                        deviation_ids=deviation_ids,
                        review_status=review_states[
                            (target_type, candidate_id)
                        ].status,
                        rationale=(
                            item.derivation_rationale
                            if target_type == "element_candidate"
                            else item.comparability_assessment.rationale
                        ),
                    )
                )
        return tuple(
            sorted(
                result,
                key=lambda item: (
                    item.target_type,
                    item.candidate_id,
                ),
            )
        )

    def _required_decisions(
        self,
        snapshot: ModelCandidateSetSnapshot,
        review_states: dict[tuple[str, str], ModelProposalReviewState],
        choice_groups: tuple[ModelProposalRelationshipChoiceGroup, ...],
    ) -> tuple[ModelProposalRequiredDecision, ...]:
        result = []
        grouped_relationship_ids = {
            candidate_id
            for group in choice_groups
            for candidate_id in group.candidate_ids
        }

        for item in snapshot.element_candidates:
            candidate_id = item.model_element_candidate_id
            state = review_states[
                ("element_candidate", candidate_id)
            ].status
            if state in {"pending", "deferred", "stale"}:
                result.append(
                    ModelProposalRequiredDecision(
                        decision_key=f"element:{candidate_id}",
                        target_type="element_candidate",
                        target_ids=(candidate_id,),
                        reason=self._review_reason(state),
                        recommended_action=(
                            "Review this proposed model element."
                        ),
                    )
                )

        for group in choice_groups:
            if group.review_required:
                result.append(
                    ModelProposalRequiredDecision(
                        decision_key=(
                            "relationship_choice:"
                            + group.relationship_choice_key
                        ),
                        target_type="relationship_choice_group",
                        target_ids=group.candidate_ids,
                        reason=(
                            "Relationship alternatives require one "
                            "explicitly accepted choice and terminal "
                            "decisions for the remaining alternatives."
                        ),
                        recommended_action=(
                            "Select the intended relationship alternative."
                        ),
                    )
                )

        for item in snapshot.relationship_candidates:
            candidate_id = item.model_relationship_candidate_id
            if candidate_id in grouped_relationship_ids:
                continue
            state = review_states[
                ("relationship_candidate", candidate_id)
            ].status
            if state in {"pending", "deferred", "stale"}:
                result.append(
                    ModelProposalRequiredDecision(
                        decision_key=f"relationship:{candidate_id}",
                        target_type="relationship_candidate",
                        target_ids=(candidate_id,),
                        reason=self._review_reason(state),
                        recommended_action=(
                            "Review this proposed relationship."
                        ),
                    )
                )

        return tuple(
            sorted(result, key=lambda item: item.decision_key)
        )

    def _review_reason(self, state: str) -> str:
        if state == "pending":
            return "No Human Review Decision exists yet."
        if state == "deferred":
            return "The latest Human Review Decision is deferred."
        return (
            "The latest Human Review Decision does not bind the exact "
            "current Candidate snapshot."
        )

    def _phase_i_status(
        self,
        project_id: str,
        candidate_set_id: str,
        *,
        decisions: tuple[ModelProposalRequiredDecision, ...],
        blocking: tuple[ModelProposalBlockingIssue, ...],
    ) -> tuple[str, ModelProposalBlockingIssue | None]:
        if decisions:
            return "not_ready", None
        if blocking:
            return "blocked", None
        try:
            self._phase_i.load_phase_i_input(
                project_id,
                candidate_set_id,
            )
        except ModelCandidatePhaseIGateError as exc:
            return (
                "blocked",
                ModelProposalBlockingIssue(
                    code="phase_i_gate_blocked",
                    message=str(exc),
                ),
            )
        return "ready", None

    def _summary(
        self,
        snapshot: ModelCandidateSetSnapshot,
        elements: tuple[ModelProposalElementView, ...],
        relationships: tuple[ModelProposalRelationshipView, ...],
        decisions: tuple[ModelProposalRequiredDecision, ...],
        blocking: tuple[ModelProposalBlockingIssue, ...],
    ) -> str:
        area_count = len({item.model_area for item in elements})
        text = (
            f"Proposal {snapshot.manifest.candidate_set_id} contains "
            f"{len(elements)} model element(s) and "
            f"{len(relationships)} relationship(s) across "
            f"{area_count} model area(s)."
        )
        if decisions:
            return (
                text
                + f" {len(decisions)} human decision(s) remain."
            )
        if blocking:
            return (
                text
                + f" {len(blocking)} blocking integrity/gate issue(s) remain."
            )
        return text + " Human Review is terminal for all Candidates."

    def _generation_rationale_summary(
        self,
        snapshot: ModelCandidateSetSnapshot,
    ) -> str:
        provenance = snapshot.manifest.generation_provenance
        return (
            f"Generated by {provenance.method} from "
            f"{len(snapshot.manifest.approved_input_references)} "
            "Approved Input snapshot reference(s), using Model Structure "
            f"Profile "
            f"{snapshot.manifest.model_structure_profile_reference.profile_id} "
            f"{snapshot.manifest.model_structure_profile_reference.profile_version}."
        )

    def _next_action(
        self,
        decisions: tuple[ModelProposalRequiredDecision, ...],
        blocking: tuple[ModelProposalBlockingIssue, ...],
        phase_i_gate_status: str,
    ) -> str:
        if decisions:
            return (
                "Resolve the required Human Review decision(s) before "
                "attempting Phase-I assembly."
            )
        if blocking or phase_i_gate_status == "blocked":
            return (
                "Resolve the blocking integrity or authority issue before "
                "Phase-I assembly."
            )
        if phase_i_gate_status == "ready":
            return "Continue to Phase-I Internal Engineering Model assembly."
        raise ModelCandidateIntegrityError(
            "Model Proposal next-action state is internally inconsistent."
        )


def model_proposal_view_to_dict(
    view: ModelProposalView,
) -> dict[str, object]:
    """Return a deterministic JSON-compatible Level-1/2 proposal projection."""

    if not isinstance(view, ModelProposalView):
        raise ModelCandidateIntegrityError(
            "view must be a ModelProposalView."
        )
    return {
        "project_id": view.project_id,
        "candidate_set_id": view.candidate_set_id,
        "candidate_set_content_fingerprint": (
            view.candidate_set_content_fingerprint
        ),
        "summary": view.summary,
        "proposed_elements": [
            {
                "candidate_id": item.candidate_id,
                "candidate_subject_key": item.candidate_subject_key,
                "proposed_name": item.proposed_name,
                "description": item.description,
                "model_area": item.model_area,
                "element_type": item.element_type,
                "comparison_anchor_id": item.comparison_anchor_id,
                "support_level": item.support_level,
                "conformance_status": item.conformance_status,
                "review_state": {
                    "status": item.review_state.status,
                    "decision_id": item.review_state.decision_id,
                    "decision_fingerprint": (
                        item.review_state.decision_fingerprint
                    ),
                    "rationale": item.review_state.rationale,
                },
                "approved_input_ids": list(item.approved_input_ids),
                "assumptions": list(item.assumptions),
                "missing_information": list(item.missing_information),
                "rationale": item.rationale,
            }
            for item in view.proposed_elements
        ],
        "proposed_relationships": [
            {
                "candidate_id": item.candidate_id,
                "relationship_choice_key": (
                    item.relationship_choice_key
                ),
                "source_subject_key": item.source_subject_key,
                "target_subject_key": item.target_subject_key,
                "source_resolution_status": (
                    item.source_resolution_status
                ),
                "target_resolution_status": (
                    item.target_resolution_status
                ),
                "relationship_family": item.relationship_family,
                "semantic_intent": item.semantic_intent,
                "directionality": item.directionality,
                "priority_class": item.priority_class,
                "comparability_impact": item.comparability_impact,
                "conformance_status": item.conformance_status,
                "review_state": {
                    "status": item.review_state.status,
                    "decision_id": item.review_state.decision_id,
                    "decision_fingerprint": (
                        item.review_state.decision_fingerprint
                    ),
                    "rationale": item.review_state.rationale,
                },
                "approved_input_ids": list(item.approved_input_ids),
                "assumptions": list(item.assumptions),
                "missing_information": list(item.missing_information),
                "rationale": item.rationale,
            }
            for item in view.proposed_relationships
        ],
        "structural_overview": {
            "nodes": [
                {
                    "candidate_id": item.candidate_id,
                    "label": item.label,
                    "model_area": item.model_area,
                    "element_type": item.element_type,
                    "review_status": item.review_status,
                }
                for item in view.structural_overview.nodes
            ],
            "edges": [
                {
                    "candidate_id": item.candidate_id,
                    "source_subject_key": item.source_subject_key,
                    "target_subject_key": item.target_subject_key,
                    "semantic_intent": item.semantic_intent,
                    "relationship_family": item.relationship_family,
                    "review_status": item.review_status,
                    "resolution_status": item.resolution_status,
                }
                for item in view.structural_overview.edges
            ],
            "model_areas": list(view.structural_overview.model_areas),
        },
        "relationship_choice_groups": [
            {
                "relationship_choice_key": item.relationship_choice_key,
                "candidate_ids": list(item.candidate_ids),
                "preferred_candidate_ids": list(
                    item.preferred_candidate_ids
                ),
                "accepted_candidate_ids": list(
                    item.accepted_candidate_ids
                ),
                "review_required": item.review_required,
            }
            for item in view.relationship_choice_groups
        ],
        "comparability_summary": {
            "improves_count": view.comparability_summary.improves_count,
            "neutral_count": view.comparability_summary.neutral_count,
            "reduces_count": view.comparability_summary.reduces_count,
            "unknown_count": view.comparability_summary.unknown_count,
            "comparison_anchor_ids": list(
                view.comparability_summary.comparison_anchor_ids
            ),
            "deviation_ids": list(
                view.comparability_summary.deviation_ids
            ),
        },
        "profile_deviations": [
            {
                "target_type": item.target_type,
                "candidate_id": item.candidate_id,
                "conformance_status": item.conformance_status,
                "finding_ids": list(item.finding_ids),
                "deviation_ids": list(item.deviation_ids),
                "review_status": item.review_status,
                "rationale": item.rationale,
            }
            for item in view.profile_deviations
        ],
        "required_human_decisions": [
            {
                "decision_key": item.decision_key,
                "target_type": item.target_type,
                "target_ids": list(item.target_ids),
                "reason": item.reason,
                "recommended_action": item.recommended_action,
            }
            for item in view.required_human_decisions
        ],
        "blocking_issues": [
            {
                "code": item.code,
                "message": item.message,
            }
            for item in view.blocking_issues
        ],
        "generation_rationale_summary": (
            view.generation_rationale_summary
        ),
        "phase_i_gate_status": view.phase_i_gate_status,
        "next_action": view.next_action,
    }


def model_proposal_view_to_json(
    view: ModelProposalView,
) -> str:
    """Serialize the reproducible proposal projection deterministically."""

    return (
        json.dumps(
            model_proposal_view_to_dict(view),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )


def model_proposal_view_to_markdown(
    view: ModelProposalView,
) -> str:
    """Render a concise deterministic report without creating new authority."""

    lines = [
        f"# Model Proposal — {view.candidate_set_id}",
        "",
        view.summary,
        "",
        "## Proposed Elements",
        "",
    ]
    if view.proposed_elements:
        for item in view.proposed_elements:
            lines.append(
                f"- **{item.proposed_name}** (`{item.candidate_id}`) — "
                f"{item.model_area} / {item.element_type}; "
                f"review: {item.review_state.status}"
            )
    else:
        lines.append("- None")

    lines.extend(
        [
            "",
            "## Proposed Relationships",
            "",
        ]
    )
    if view.proposed_relationships:
        for item in view.proposed_relationships:
            lines.append(
                f"- `{item.candidate_id}`: "
                f"{item.source_subject_key} "
                f"—[{item.semantic_intent}]→ "
                f"{item.target_subject_key}; "
                f"review: {item.review_state.status}"
            )
    else:
        lines.append("- None")

    lines.extend(
        [
            "",
            "## Required Human Decisions",
            "",
        ]
    )
    if view.required_human_decisions:
        for item in view.required_human_decisions:
            lines.append(
                f"- {item.recommended_action} "
                f"({', '.join(item.target_ids)}): {item.reason}"
            )
    else:
        lines.append("- None")

    lines.extend(
        [
            "",
            "## Comparability",
            "",
            (
                "- improves="
                f"{view.comparability_summary.improves_count}, "
                f"neutral={view.comparability_summary.neutral_count}, "
                f"reduces={view.comparability_summary.reduces_count}, "
                f"unknown={view.comparability_summary.unknown_count}"
            ),
            "",
            "## Next Action",
            "",
            view.next_action,
            "",
            "> This report is a deterministic presentation projection of "
            "immutable Model Candidate artifacts. It is not model authority.",
            "",
        ]
    )
    return "\n".join(lines)
