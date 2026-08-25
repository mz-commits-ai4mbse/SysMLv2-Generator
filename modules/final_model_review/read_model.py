"""Deterministic read model for Phase-L Final Model Review UI projection."""

from __future__ import annotations

from modules.internal_model.authority_backed import (
    AuthorityBackedInternalModelRepository,
)

from dataclasses import asdict
from pathlib import Path
from typing import Protocol

from modules.internal_model.phase_j_read_service import InternalModelReadService
from modules.model_candidates.model_proposal import ModelProposalReadService
from modules.project_workspace.workspace import DEFAULT_PROJECTS_ROOT

from .errors import FinalModelReviewIntegrityError
from .repository import FinalModelReviewRepository
from .types import (
    FinalModelReviewAgentProposalView,
    FinalModelReviewCodeLocationView,
    FinalModelReviewCodeUnitView,
    FinalModelReviewDiagramEdgeView,
    FinalModelReviewDiagramNodeView,
    FinalModelReviewDiagramView,
    FinalModelReviewEvidenceReference,
    FinalModelReviewExternalValidatorView,
    FinalModelReviewTraceabilityView,
    FinalModelReviewValidationFindingView,
    FinalModelReviewView,
)


class FinalModelReviewAgentEvidenceResolver(Protocol):
    """Resolve optional agent/personality evidence without making it authority."""

    def resolve_agent_proposal(
        self,
        project_id: str,
        reference: FinalModelReviewEvidenceReference,
    ) -> FinalModelReviewAgentProposalView | None:
        ...


class FinalModelReviewReadService:
    """Build one coherent UI projection from one explicit immutable revision."""

    def __init__(
        self,
        root: Path | str = DEFAULT_PROJECTS_ROOT,
        *,
        repository: FinalModelReviewRepository | None = None,
        internal_model_read_service: InternalModelReadService | None = None,
        authority_backed_internal_model_repository=None,
        model_proposal_read_service: ModelProposalReadService | None = None,
        agent_evidence_resolver: FinalModelReviewAgentEvidenceResolver | None = None,
    ) -> None:
        self.root = Path(root)
        self._repository = (
            FinalModelReviewRepository(root=self.root)
            if repository is None
            else repository
        )
        self._internal_models = (
            InternalModelReadService(root=self.root)
            if internal_model_read_service is None
            else internal_model_read_service
        )
        self._authority_backed_internal_models = (
            AuthorityBackedInternalModelRepository(root=self.root)
            if authority_backed_internal_model_repository is None
            else authority_backed_internal_model_repository
        )
        self._model_proposals = (
            ModelProposalReadService(root=self.root)
            if model_proposal_read_service is None
            else model_proposal_read_service
        )
        self._agent_evidence_resolver = agent_evidence_resolver

    def load_view(
        self,
        project_id: str,
        final_model_review_id: str,
        final_model_review_revision_id: str,
    ) -> FinalModelReviewView:
        """Load one exact Final Model Review revision for Human presentation."""

        bundle = self._repository.load_revision(
            project_id,
            final_model_review_id,
            final_model_review_revision_id,
        )
        revision = bundle.revision

        authority_backed = self._is_authority_backed_artifact_snapshot(
            bundle.artifact_set_snapshot
        )
        if authority_backed:
            snapshot = self._authority_backed_internal_models.load(
                project_id,
                revision.source_internal_engineering_model_id,
            )
            candidate_proposal = None
        else:
            snapshot = self._internal_models.load_phase_j_input(
                project_id,
                revision.source_internal_engineering_model_id,
            )
            candidate_proposal = self._model_proposals.load_model_proposal(
                project_id,
                snapshot.manifest.candidate_set_id,
            )
            if (
                candidate_proposal.candidate_set_content_fingerprint
                != snapshot.manifest.candidate_set_content_fingerprint
            ):
                raise FinalModelReviewIntegrityError(
                    "Candidate Proposal does not match the exact source "
                    "IEM Candidate Set."
                )

        self._validate_iem_binding(bundle, snapshot)

        traceability = self._traceability(bundle.artifact_set_snapshot)
        locations = {
            (item.generated_symbol_id): FinalModelReviewCodeLocationView(
                generated_unit_id=item.generated_unit_id,
                generated_symbol_id=item.generated_symbol_id,
                start_line=item.start_line,
                end_line=item.end_line,
            )
            for item in traceability
        }
        trace_by_element = {
            item.source_internal_model_element_id: item
            for item in traceability
            if item.source_internal_model_element_id is not None
        }
        trace_by_relationship = {
            item.source_internal_model_relationship_id: item
            for item in traceability
            if item.source_internal_model_relationship_id is not None
        }

        code_units = self._code_units(
            bundle,
            bundle.artifact_set_snapshot,
        )
        diagram = self._diagram(
            snapshot,
            trace_by_element=trace_by_element,
            trace_by_relationship=trace_by_relationship,
            locations=locations,
        )
        findings = self._validation_findings(
            bundle.validation_result_snapshot
        )
        items = self._items(
            project_id,
            final_model_review_id,
            final_model_review_revision_id,
        )
        decisions = tuple(
            item
            for item in self._repository.list_decisions(
                project_id,
                final_model_review_id,
            )
            if item.target.final_model_review_revision_id
            == final_model_review_revision_id
        )
        change_proposals = (
            self._repository.list_change_proposals(
                project_id,
                final_model_review_id,
                final_model_review_revision_id,
            )
            if hasattr(self._repository, "list_change_proposals")
            else ()
        )
        agent_proposals = self._agent_proposals(
            project_id,
            revision.evidence_references,
        )
        review_state = self._review_state(
            revision.validation_status,
            revision.publication_gate,
            items=items,
            decisions=decisions,
            change_proposals=change_proposals,
        )
        required_actions = self._required_actions(
            revision.validation_status,
            revision.publication_gate,
            items=items,
            decisions=decisions,
            change_proposals=change_proposals,
        )
        return FinalModelReviewView(
            project_id=project_id,
            final_model_review_id=final_model_review_id,
            final_model_review_revision_id=final_model_review_revision_id,
            source_internal_engineering_model_id=(
                revision.source_internal_engineering_model_id
            ),
            generated_artifact_set_fingerprint=(
                revision.generated_artifact_set_fingerprint
            ),
            validation_result_fingerprint=(
                revision.validation_result_fingerprint
            ),
            validation_status=revision.validation_status,
            publication_gate=revision.publication_gate,
            review_state=review_state,
            summary=self._summary(
                snapshot,
                findings,
                agent_proposals,
                review_state,
            ),
            code_units=code_units,
            diagram=diagram,
            validation_findings=findings,
            traceability=traceability,
            candidate_proposal=candidate_proposal,
            agent_proposals=agent_proposals,
            review_items=items,
            review_decisions=decisions,
            change_proposals=change_proposals,
            required_human_actions=required_actions,
            next_action=self._next_action(review_state, required_actions),
            external_validator_evidence=(
                self._external_validator_evidence(
                    bundle.validation_result_snapshot
                )
            ),
        )

    @staticmethod
    def _is_authority_backed_artifact_snapshot(snapshot) -> bool:
        if not isinstance(snapshot, dict):
            return False
        traces = snapshot.get("traceability_entries")
        if not isinstance(traces, (list, tuple)):
            return False
        return any(
            isinstance(item, dict)
            and "authority_references" in item
            for item in traces
        )

    def _validate_iem_binding(self, bundle, snapshot) -> None:
        revision = bundle.revision

        if hasattr(snapshot, "manifest"):
            project_id = snapshot.manifest.project_id
            iem_id = snapshot.manifest.internal_engineering_model_id
            iem_fingerprint = snapshot.manifest.content_fingerprint
        else:
            project_id = snapshot.project_id
            iem_id = snapshot.internal_engineering_model_id
            iem_fingerprint = snapshot.content_fingerprint

        if project_id != revision.project_id:
            raise FinalModelReviewIntegrityError(
                "Source IEM Project does not match Final Model Review revision."
            )
        if iem_id != revision.source_internal_engineering_model_id:
            raise FinalModelReviewIntegrityError(
                "Source IEM identity does not match Final Model Review revision."
            )

        expected_iem_fingerprint = bundle.artifact_set_snapshot.get(
            "source_iem_content_fingerprint"
        )
        if (
            expected_iem_fingerprint is None
            or iem_fingerprint != expected_iem_fingerprint
        ):
            raise FinalModelReviewIntegrityError(
                "Source IEM fingerprint does not match generated artifact evidence."
            )

    def _code_units(self, bundle, artifact_snapshot):
        units_raw = artifact_snapshot.get("units")
        if not isinstance(units_raw, list):
            raise FinalModelReviewIntegrityError(
                "Artifact-set snapshot units must be a JSON array."
            )
        by_id = {}
        for value in units_raw:
            if not isinstance(value, dict):
                raise FinalModelReviewIntegrityError(
                    "Artifact-set snapshot unit must be an object."
                )
            unit_id = value.get("unit_id")
            symbols = value.get("generated_symbol_ids")
            if not isinstance(unit_id, str) or not isinstance(symbols, list):
                raise FinalModelReviewIntegrityError(
                    "Artifact-set snapshot unit projection is malformed."
                )
            by_id[unit_id] = tuple(
                str(item) for item in symbols
            )
        result = []
        for stored in bundle.generated_units:
            if stored.generated_unit_id not in by_id:
                raise FinalModelReviewIntegrityError(
                    "Stored generated unit is missing from artifact-set snapshot."
                )
            result.append(
                FinalModelReviewCodeUnitView(
                    generated_unit_id=stored.generated_unit_id,
                    relative_path=stored.relative_path,
                    content=stored.content,
                    content_fingerprint=stored.content_fingerprint,
                    generated_symbol_ids=by_id[stored.generated_unit_id],
                )
            )
        return tuple(result)

    def _traceability(self, artifact_snapshot):
        values = artifact_snapshot.get("traceability_entries")
        if not isinstance(values, (list, tuple)):
            raise FinalModelReviewIntegrityError(
                "Artifact-set traceability_entries must be a JSON array."
            )

        result = []
        for raw in values:
            if not isinstance(raw, dict):
                raise FinalModelReviewIntegrityError(
                    "Traceability entry must be a JSON object."
                )

            location = raw.get("generated_location")
            if location is not None and not isinstance(location, dict):
                raise FinalModelReviewIntegrityError(
                    "Generated traceability location must be an object."
                )

            if "authority_references" in raw:
                authorities = raw.get("authority_references")
                if not isinstance(authorities, (list, tuple)):
                    raise FinalModelReviewIntegrityError(
                        "Authority-backed traceability references are malformed."
                    )

                authority_ids = []
                authority_types = []
                for authority in authorities:
                    if not isinstance(authority, dict):
                        raise FinalModelReviewIntegrityError(
                            "Authority-backed traceability reference must be "
                            "an object."
                        )
                    authority_ids.append(
                        self._required_string(authority, "authority_id")
                    )
                    authority_types.append(
                        self._required_string(authority, "authority_type")
                    )

                approved_input = raw.get("approved_input_id")
                approved_ids = (
                    ()
                    if approved_input is None
                    else (self._required_string(raw, "approved_input_id"),)
                )

                result.append(
                    FinalModelReviewTraceabilityView(
                        generated_unit_id=self._required_string(
                            raw, "generated_unit_id"
                        ),
                        generated_symbol_id=self._required_string(
                            raw, "generated_symbol_id"
                        ),
                        start_line=(
                            None
                            if location is None
                            else location.get("start_line")
                        ),
                        end_line=(
                            None
                            if location is None
                            else location.get("end_line")
                        ),
                        source_internal_model_element_id=raw.get(
                            "source_internal_model_element_id"
                        ),
                        source_internal_model_relationship_id=raw.get(
                            "source_internal_model_relationship_id"
                        ),
                        source_model_candidate_id=None,
                        approved_input_ids=approved_ids,
                        review_decision_id=(
                            None if not authority_ids else authority_ids[-1]
                        ),
                        accepted_exception_decision_id=None,
                        authority_ids=tuple(authority_ids),
                        authority_types=tuple(authority_types),
                    )
                )
                continue

            approved = raw.get("approved_input_references")
            review = raw.get("review_decision_reference")
            accepted = raw.get("accepted_exception_reference")
            if not isinstance(approved, (list, tuple)) or not isinstance(review, dict):
                raise FinalModelReviewIntegrityError(
                    "Traceability authority references are malformed."
                )

            result.append(
                FinalModelReviewTraceabilityView(
                    generated_unit_id=self._required_string(
                        raw, "generated_unit_id"
                    ),
                    generated_symbol_id=self._required_string(
                        raw, "generated_symbol_id"
                    ),
                    start_line=(
                        None if location is None else location.get("start_line")
                    ),
                    end_line=(
                        None if location is None else location.get("end_line")
                    ),
                    source_internal_model_element_id=raw.get(
                        "source_internal_model_element_id"
                    ),
                    source_internal_model_relationship_id=raw.get(
                        "source_internal_model_relationship_id"
                    ),
                    source_model_candidate_id=self._required_string(
                        raw, "source_model_candidate_id"
                    ),
                    approved_input_ids=tuple(
                        sorted(
                            self._required_string(item, "approved_input_id")
                            for item in approved
                            if isinstance(item, dict)
                        )
                    ),
                    review_decision_id=self._required_string(
                        review, "model_candidate_review_decision_id"
                    ),
                    accepted_exception_decision_id=(
                        None
                        if accepted is None
                        else self._required_string(
                            accepted,
                            "model_candidate_review_decision_id",
                        )
                    ),
                )
            )

        return tuple(
            sorted(
                result,
                key=lambda item: (
                    item.generated_unit_id,
                    item.start_line or 0,
                    item.generated_symbol_id,
                ),
            )
        )

    def _diagram(
        self,
        snapshot,
        *,
        trace_by_element,
        trace_by_relationship,
        locations,
    ):
        nodes = []
        for element in snapshot.elements:
            trace = trace_by_element.get(
                element.internal_model_element_id
            )
            generated_symbol = (
                None if trace is None else trace.generated_symbol_id
            )

            if hasattr(element, "placement_authority"):
                candidate_id = None
                review_id = element.placement_authority.authority_id
                authority_ids = (
                    element.placement_authority.authority_id,
                )
                authority_types = (
                    element.placement_authority.authority_type,
                )
            else:
                candidate_id = element.source_model_element_candidate_id
                review_id = (
                    element.review_decision_reference
                    .model_candidate_review_decision_id
                )
                authority_ids = ()
                authority_types = ()

            nodes.append(
                FinalModelReviewDiagramNodeView(
                    internal_model_element_id=(
                        element.internal_model_element_id
                    ),
                    generated_symbol_id=generated_symbol,
                    label=element.name,
                    description=element.description,
                    model_area=element.model_area,
                    element_type=element.element_type,
                    framework_assignment=element.framework_assignment,
                    source_model_candidate_id=candidate_id,
                    review_decision_id=review_id,
                    code_location=(
                        None
                        if generated_symbol is None
                        else locations.get(generated_symbol)
                    ),
                    authority_ids=authority_ids,
                    authority_types=authority_types,
                )
            )

        edges = []
        for relationship in snapshot.relationships:
            trace = trace_by_relationship.get(
                relationship.internal_model_relationship_id
            )
            generated_symbol = (
                None if trace is None else trace.generated_symbol_id
            )

            if hasattr(
                relationship,
                "engineering_relationship_authority",
            ):
                candidate_id = None
                review_id = (
                    relationship.final_representation_authority.authority_id
                )
                authority_ids = (
                    relationship.engineering_relationship_authority.authority_id,
                    relationship.final_representation_authority.authority_id,
                )
                authority_types = (
                    relationship.engineering_relationship_authority.authority_type,
                    relationship.final_representation_authority.authority_type,
                )
            else:
                candidate_id = (
                    relationship.source_model_relationship_candidate_id
                )
                review_id = (
                    relationship.review_decision_reference
                    .model_candidate_review_decision_id
                )
                authority_ids = ()
                authority_types = ()

            edges.append(
                FinalModelReviewDiagramEdgeView(
                    internal_model_relationship_id=(
                        relationship.internal_model_relationship_id
                    ),
                    generated_symbol_id=generated_symbol,
                    source_internal_model_element_id=(
                        relationship.source_internal_model_element_id
                    ),
                    target_internal_model_element_id=(
                        relationship.target_internal_model_element_id
                    ),
                    relationship_family=relationship.relationship_family,
                    semantic_intent=relationship.semantic_intent,
                    directionality=relationship.directionality,
                    source_model_candidate_id=candidate_id,
                    review_decision_id=review_id,
                    code_location=(
                        None
                        if generated_symbol is None
                        else locations.get(generated_symbol)
                    ),
                    authority_ids=authority_ids,
                    authority_types=authority_types,
                )
            )

        return FinalModelReviewDiagramView(
            nodes=tuple(
                sorted(
                    nodes,
                    key=lambda item: item.internal_model_element_id,
                )
            ),
            edges=tuple(
                sorted(
                    edges,
                    key=lambda item: item.internal_model_relationship_id,
                )
            ),
            model_areas=tuple(
                sorted({item.model_area for item in nodes})
            ),
        )

    def _external_validator_evidence(self, validation_snapshot):
        values = validation_snapshot.get(
            "external_validator_evidence"
        )
        if values is None:
            return ()
        if not isinstance(values, (list, tuple)):
            raise FinalModelReviewIntegrityError(
                "External validator evidence must be a JSON array."
            )

        result = []
        for raw in values:
            if not isinstance(raw, dict):
                raise FinalModelReviewIntegrityError(
                    "External validator evidence entry must be an object."
                )
            identity = raw.get("validator_identity")
            if not isinstance(identity, dict):
                raise FinalModelReviewIntegrityError(
                    "External validator identity is malformed."
                )
            diagnostics = raw.get("normalized_diagnostic_count")
            if type(diagnostics) is not int:
                raise FinalModelReviewIntegrityError(
                    "External validator diagnostic count is invalid."
                )
            exit_code = raw.get("exit_code")
            if exit_code is not None and type(exit_code) is not int:
                raise FinalModelReviewIntegrityError(
                    "External validator exit code is invalid."
                )

            result.append(
                FinalModelReviewExternalValidatorView(
                    tool_name=self._required_string(
                        identity, "tool_name"
                    ),
                    tool_version=(
                        None
                        if identity.get("tool_version") is None
                        else self._optional_tool_version(
                            identity.get("tool_version")
                        )
                    ),
                    execution_status=self._required_string(
                        raw, "execution_status"
                    ),
                    exit_code=exit_code,
                    normalized_diagnostic_count=diagnostics,
                )
            )
        return tuple(result)

    def _validation_findings(self, validation_snapshot):
        values = validation_snapshot.get("findings")
        if not isinstance(values, (list, tuple)):
            raise FinalModelReviewIntegrityError(
                "Validation-result findings must be a JSON array."
            )
        result = []
        for raw in values:
            if not isinstance(raw, dict):
                raise FinalModelReviewIntegrityError(
                    "Validation finding must be a JSON object."
                )
            location = raw.get("generated_location")
            if location is not None and not isinstance(location, dict):
                raise FinalModelReviewIntegrityError(
                    "Validation finding location must be an object."
                )
            result.append(
                FinalModelReviewValidationFindingView(
                    code=self._required_string(raw, "code"),
                    category=self._required_string(raw, "category"),
                    severity=self._required_string(raw, "severity"),
                    blocking=bool(raw.get("blocking")),
                    message=self._required_string(raw, "message"),
                    generated_unit_id=raw.get("generated_unit_id"),
                    generated_symbol_id=raw.get("generated_symbol_id"),
                    start_line=(
                        None if location is None else location.get("start_line")
                    ),
                    end_line=(
                        None if location is None else location.get("end_line")
                    ),
                    start_column=(
                        None if location is None else location.get("start_column")
                    ),
                    end_column=(
                        None if location is None else location.get("end_column")
                    ),
                    validator_id=raw.get("validator_id"),
                    validator_rule_id=raw.get("validator_rule_id"),
                )
            )
        return tuple(result)

    def _items(self, project_id, review_id, revision_id):
        scan = self._repository.scan(project_id)
        if scan.issues:
            raise FinalModelReviewIntegrityError(
                "Final Model Review repository contains blocking issues."
            )
        return tuple(
            item
            for item in scan.items
            if item.final_model_review_id == review_id
            and item.final_model_review_revision_id == revision_id
        )

    def _agent_proposals(self, project_id, evidence_references):
        result = []
        for reference in evidence_references:
            if reference.evidence_type != "agent_proposal":
                continue
            resolved = None
            if self._agent_evidence_resolver is not None:
                resolved = self._agent_evidence_resolver.resolve_agent_proposal(
                    project_id,
                    reference,
                )
            if resolved is not None:
                if (
                    resolved.reference_id != reference.reference_id
                    or resolved.content_fingerprint
                    != reference.content_fingerprint
                ):
                    raise FinalModelReviewIntegrityError(
                        "Resolved agent proposal does not match its review evidence reference."
                    )
                result.append(resolved)
            else:
                result.append(
                    FinalModelReviewAgentProposalView(
                        reference_id=reference.reference_id,
                        content_fingerprint=reference.content_fingerprint,
                        resolution_status="referenced_only",
                        agent_identity=None,
                        personality=None,
                        proposal_summary=None,
                        rationale=None,
                        confidence=None,
                        alternatives=(),
                    )
                )
        return tuple(sorted(result, key=lambda item: item.reference_id))

    def _review_state(
        self,
        status,
        gate,
        *,
        items,
        decisions,
        change_proposals,
    ):
        if change_proposals:
            if any(
                item.classification in {
                    "engineering_semantics",
                    "generated_representation",
                }
                for item in change_proposals
            ):
                return "regeneration_required"
            return "changes_requested"
        latest = decisions[-1] if decisions else None
        if status != "valid" or gate != "passed":
            return "validation_blocked"
        if any(item.mandatory for item in items):
            return "review_pending"
        if latest is not None:
            if latest.decision == "approved_for_publication":
                return "approved_for_publication"
            if latest.decision in {"changes_requested", "rejected"}:
                return "changes_requested"
        return "ready_for_approval"

    def _required_actions(
        self,
        status,
        gate,
        *,
        items,
        decisions,
        change_proposals,
    ):
        latest = decisions[-1] if decisions else None
        actions = []
        if status != "valid" or gate != "passed":
            actions.append(
                "Review blocking or incomplete validation evidence."
            )
        routes = tuple(
            sorted({item.authority_route for item in change_proposals})
        )
        if routes:
            actions.append(
                "Resolve recorded Human change proposal(s) through: "
                + ", ".join(routes)
                + "."
            )
        if latest is not None and latest.decision in {
            "changes_requested",
            "rejected",
        }:
            actions.append(
                "Resolve the Human-requested model changes and regenerate."
            )
        if any(item.mandatory for item in items):
            actions.append("Resolve mandatory Final Model Review items.")
        if not actions and (
            latest is None or latest.decision != "approved_for_publication"
        ):
            actions.append(
                "Approve the exact revision for publication or request changes."
            )
        return tuple(actions)

    def _summary(self, snapshot, findings, agent_proposals, review_state):
        return (
            f"Final model review contains {len(snapshot.elements)} model element(s), "
            f"{len(snapshot.relationships)} relationship(s), "
            f"{len(findings)} validation finding(s), and "
            f"{len(agent_proposals)} agent proposal reference(s). "
            f"Current review state: {review_state}."
        )

    def _next_action(self, review_state, actions):
        if review_state == "approved_for_publication":
            return "Continue to fingerprint-bound final output publication."
        if review_state == "regeneration_required":
            return "Route accepted changes upstream, regenerate deterministically, revalidate, and create a successor review revision."
        if review_state == "changes_requested":
            return "Resolve requested changes through the owning authority boundary; regenerate and revalidate when the routed change affects model authority."
        if actions:
            return actions[0]
        return "Continue Final Model Review."

    @staticmethod
    def _optional_tool_version(value):
        if not isinstance(value, str):
            raise FinalModelReviewIntegrityError(
                "External validator tool_version must be text or null."
            )
        normalized = value.strip()
        return normalized or None

    @staticmethod
    def _required_string(mapping, key):
        value = mapping.get(key)
        if not isinstance(value, str) or not value:
            raise FinalModelReviewIntegrityError(
                f"Review projection requires non-empty {key}."
            )
        return value


def final_model_review_view_to_dict(view: FinalModelReviewView) -> dict[str, object]:
    """Return a deterministic JSON-compatible UI projection."""

    if not isinstance(view, FinalModelReviewView):
        raise FinalModelReviewIntegrityError(
            "view must be a FinalModelReviewView."
        )
    payload = asdict(view)
    candidate = view.candidate_proposal
    try:
        payload["candidate_proposal"] = asdict(candidate)
    except TypeError:
        payload["candidate_proposal"] = candidate
    return payload
