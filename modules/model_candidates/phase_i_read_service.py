"""Validated sole Phase-H → Phase-I read boundary."""

from __future__ import annotations

from modules.approved_input import ApprovedInputRepository
from modules.approved_input.types import ApprovedInputManifest
from modules.project_workspace.workspace import DEFAULT_PROJECTS_ROOT

from .candidate_review_identifiers import (
    model_candidate_review_decision_id_sequence,
)
from .candidate_review_repository import (
    ModelCandidateReviewRepository,
)
from .errors import ModelCandidatePhaseIGateError
from .repository import ModelCandidateRepository
from .types import (
    ModelCandidateAssemblyInput,
    ModelCandidateReviewDecision,
    ModelCandidateReviewDecisionReference,
    ModelCandidateSetSnapshot,
)


class ModelCandidateReadService:
    """Expose only explicitly authorized Candidate content to Phase I."""

    def __init__(
        self,
        root=DEFAULT_PROJECTS_ROOT,
        *,
        candidate_repository: ModelCandidateRepository | None = None,
        review_repository: ModelCandidateReviewRepository | None = None,
        approved_input_repository: ApprovedInputRepository | None = None,
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
        self._approved_inputs = (
            ApprovedInputRepository(root=root)
            if approved_input_repository is None
            else approved_input_repository
        )

    def load_phase_i_input(
        self,
        project_id: str,
        candidate_set_id: str,
    ) -> ModelCandidateAssemblyInput:
        """Validate current authority, review selection and relationship integrity."""

        snapshot = self._candidates.load_candidate_set(
            project_id,
            candidate_set_id,
        )
        self._require_current_approved_inputs(snapshot)

        scan = self._reviews.scan_decisions(project_id)
        if scan.issues:
            first = scan.issues[0]
            raise ModelCandidatePhaseIGateError(
                "Candidate Review repository has blocking issues; "
                f"first={first.code}: {first.message}"
            )

        set_decisions = tuple(
            item
            for item in scan.decisions
            if item.target.candidate_set_id == candidate_set_id
        )
        self._reject_orphan_decisions(snapshot, set_decisions)

        selected_elements = []
        selected_relationships = []
        decision_refs = []
        exception_refs = []
        element_decisions = {}

        for candidate in snapshot.element_candidates:
            decision = self._require_terminal_exact_decision(
                snapshot,
                set_decisions,
                target_type="element_candidate",
                candidate_id=candidate.model_element_candidate_id,
                content_fingerprint=candidate.content_fingerprint,
                conformance_status=(
                    candidate.structure_profile_conformance.status
                ),
                conformance_fingerprint=(
                    candidate.structure_profile_conformance
                    .conformance_fingerprint
                ),
            )
            element_decisions[
                candidate.model_element_candidate_id
            ] = decision
            reference = self._decision_reference(decision)
            decision_refs.append(reference)
            if decision.decision in {
                "accepted",
                "accepted_exception",
            }:
                selected_elements.append(candidate)
                if decision.decision == "accepted_exception":
                    exception_refs.append(reference)

        for candidate in snapshot.relationship_candidates:
            decision = self._require_terminal_exact_decision(
                snapshot,
                set_decisions,
                target_type="relationship_candidate",
                candidate_id=(
                    candidate.model_relationship_candidate_id
                ),
                content_fingerprint=candidate.content_fingerprint,
                conformance_status=(
                    candidate.structure_profile_conformance.status
                ),
                conformance_fingerprint=(
                    candidate.structure_profile_conformance
                    .conformance_fingerprint
                ),
            )
            reference = self._decision_reference(decision)
            decision_refs.append(reference)
            if decision.decision in {
                "accepted",
                "accepted_exception",
            }:
                self._validate_selected_relationship(
                    candidate,
                    element_decisions,
                )
                selected_relationships.append(candidate)
                if decision.decision == "accepted_exception":
                    exception_refs.append(reference)

        self._validate_relationship_choices(
            tuple(selected_relationships)
        )

        decision_refs.sort(
            key=lambda item: model_candidate_review_decision_id_sequence(
                item.model_candidate_review_decision_id
            )
        )
        exception_refs.sort(
            key=lambda item: model_candidate_review_decision_id_sequence(
                item.model_candidate_review_decision_id
            )
        )

        manifest = snapshot.manifest
        return ModelCandidateAssemblyInput(
            project_id=project_id,
            candidate_set_id=manifest.candidate_set_id,
            candidate_set_content_fingerprint=(
                manifest.content_fingerprint
            ),
            approved_input_snapshot_fingerprint=(
                manifest.approved_input_snapshot_fingerprint
            ),
            approved_input_references=(
                manifest.approved_input_references
            ),
            model_structure_profile_reference=(
                manifest.model_structure_profile_reference
            ),
            generation_provenance=manifest.generation_provenance,
            accepted_element_candidates=tuple(selected_elements),
            accepted_relationship_candidates=tuple(
                selected_relationships
            ),
            accepted_exception_decisions=tuple(exception_refs),
            review_decision_references=tuple(decision_refs),
        )

    def _require_current_approved_inputs(
        self,
        snapshot: ModelCandidateSetSnapshot,
    ) -> None:
        active = tuple(
            self._approved_inputs.list_active_approved_inputs(
                snapshot.manifest.project_id
            )
        )
        if not all(isinstance(item, ApprovedInputManifest) for item in active):
            raise ModelCandidatePhaseIGateError(
                "Approved Input repository returned an invalid manifest type."
            )
        active_by_id = {
            item.approved_input_id: item for item in active
        }
        for reference in snapshot.manifest.approved_input_references:
            current = active_by_id.get(reference.approved_input_id)
            if current is None:
                raise ModelCandidatePhaseIGateError(
                    "Candidate Set references an Approved Input that is "
                    f"no longer active: {reference.approved_input_id}."
                )
            if (
                current.content_fingerprint
                != reference.content_fingerprint
                or current.stable_subject_key
                != reference.stable_subject_key
            ):
                raise ModelCandidatePhaseIGateError(
                    "Current Approved Input no longer matches the exact "
                    f"Candidate Set snapshot: {reference.approved_input_id}."
                )

    def _reject_orphan_decisions(
        self,
        snapshot: ModelCandidateSetSnapshot,
        decisions: tuple[ModelCandidateReviewDecision, ...],
    ) -> None:
        valid_targets = {
            (
                "element_candidate",
                item.model_element_candidate_id,
            )
            for item in snapshot.element_candidates
        } | {
            (
                "relationship_candidate",
                item.model_relationship_candidate_id,
            )
            for item in snapshot.relationship_candidates
        }
        for decision in decisions:
            key = (
                decision.target.target_type,
                decision.target.candidate_id,
            )
            if key not in valid_targets:
                raise ModelCandidatePhaseIGateError(
                    "Candidate Set has an orphan/stale Review Decision: "
                    f"{decision.model_candidate_review_decision_id}."
                )

    def _require_terminal_exact_decision(
        self,
        snapshot: ModelCandidateSetSnapshot,
        decisions: tuple[ModelCandidateReviewDecision, ...],
        *,
        target_type: str,
        candidate_id: str,
        content_fingerprint: str,
        conformance_status: str,
        conformance_fingerprint: str,
    ) -> ModelCandidateReviewDecision:
        matches = tuple(
            item
            for item in decisions
            if item.target.target_type == target_type
            and item.target.candidate_id == candidate_id
        )
        if not matches:
            raise ModelCandidatePhaseIGateError(
                "Every Candidate requires an explicit Human Review "
                f"Decision before Phase I: {candidate_id}."
            )
        latest = max(
            matches,
            key=lambda item: (
                model_candidate_review_decision_id_sequence(
                    item.model_candidate_review_decision_id
                )
            ),
        )
        target = latest.target
        manifest = snapshot.manifest
        exact = (
            target.candidate_set_id == manifest.candidate_set_id
            and target.candidate_set_content_fingerprint
            == manifest.content_fingerprint
            and target.candidate_content_fingerprint
            == content_fingerprint
            and target.model_structure_profile_reference
            == manifest.model_structure_profile_reference
            and target.structure_profile_conformance_status
            == conformance_status
            and target.structure_profile_conformance_fingerprint
            == conformance_fingerprint
            and target.approved_input_snapshot_fingerprint
            == manifest.approved_input_snapshot_fingerprint
        )
        if not exact:
            raise ModelCandidatePhaseIGateError(
                "Latest Candidate Review Decision is stale or does not "
                f"bind the exact Candidate snapshot: {candidate_id}."
            )
        if latest.decision == "deferred":
            raise ModelCandidatePhaseIGateError(
                f"Deferred Candidate decision blocks Phase I: {candidate_id}."
            )
        if (
            conformance_status != "conformant"
            and latest.decision == "accepted"
        ):
            raise ModelCandidatePhaseIGateError(
                "Non-conformant Candidate requires an explicitly "
                f"accepted exception: {candidate_id}."
            )
        return latest

    def _validate_selected_relationship(
        self,
        relationship,
        element_decisions: dict[str, ModelCandidateReviewDecision],
    ) -> None:
        for label, endpoint in (
            ("source", relationship.source),
            ("target", relationship.target),
        ):
            if (
                endpoint.resolution_status != "resolved"
                or endpoint.resolved_model_element_candidate_id is None
                or endpoint.candidate_model_element_ids
                != (endpoint.resolved_model_element_candidate_id,)
            ):
                raise ModelCandidatePhaseIGateError(
                    "Accepted Relationship has an unresolved or ambiguous "
                    f"{label} endpoint: "
                    f"{relationship.model_relationship_candidate_id}."
                )
            element_decision = element_decisions.get(
                endpoint.resolved_model_element_candidate_id
            )
            if (
                element_decision is None
                or element_decision.decision
                not in {"accepted", "accepted_exception"}
            ):
                raise ModelCandidatePhaseIGateError(
                    "Accepted Relationship endpoint is not authorized "
                    f"for Phase I: {endpoint.resolved_model_element_candidate_id}."
                )

    def _validate_relationship_choices(
        self,
        relationships,
    ) -> None:
        groups = {}
        for item in relationships:
            if item.relationship_choice_key is None:
                continue
            groups.setdefault(
                item.relationship_choice_key,
                [],
            ).append(item.model_relationship_candidate_id)
        conflicts = {
            key: ids
            for key, ids in groups.items()
            if len(ids) > 1
        }
        if conflicts:
            key = sorted(conflicts)[0]
            raise ModelCandidatePhaseIGateError(
                "More than one Relationship alternative is accepted for "
                f"choice group {key}: {sorted(conflicts[key])}."
            )

    def _decision_reference(
        self,
        decision: ModelCandidateReviewDecision,
    ) -> ModelCandidateReviewDecisionReference:
        return ModelCandidateReviewDecisionReference(
            model_candidate_review_decision_id=(
                decision.model_candidate_review_decision_id
            ),
            target_type=decision.target.target_type,
            candidate_id=decision.target.candidate_id,
            decision=decision.decision,
            decision_fingerprint=decision.decision_fingerprint,
        )
