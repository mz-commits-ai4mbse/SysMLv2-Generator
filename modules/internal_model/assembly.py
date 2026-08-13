"""Deterministic Phase-I assembly of accepted H Candidates into one IEM snapshot."""

from __future__ import annotations

from collections.abc import Iterable

from modules.model_candidates.types import (
    ModelCandidateAssemblyInput,
    ModelCandidateReviewDecisionReference,
    ModelElementCandidate,
    ModelRelationshipCandidate,
)

from .assembly_input import (
    calculate_model_candidate_assembly_input_fingerprint,
)
from .element_manifest import create_internal_model_element
from .errors import (
    InternalModelAssemblyBlockedError,
    InternalModelIntegrityError,
    InternalModelValidationError,
)
from .identifiers import (
    next_internal_model_element_id,
    next_internal_model_relationship_id,
    validate_internal_engineering_model_id,
)
from .model_manifest import create_internal_engineering_model_manifest
from .relationship_manifest import create_internal_model_relationship
from .structure_materialization import (
    InternalModelStructureMaterializer,
    InternalModelStructureResolver,
)
from .types import (
    InternalEngineeringModelSnapshot,
    InternalModelAssemblyProvenance,
    InternalModelAttribute,
    InternalModelElement,
    InternalModelRelationship,
)


class InternalModelAssemblyService:
    """Assemble the exact authorized H→I input without semantic reinterpretation."""

    def __init__(
        self,
        *,
        structure_resolver: InternalModelStructureResolver | None = None,
        structure_materializer: InternalModelStructureMaterializer | None = None,
    ) -> None:
        self._structure_resolver = (
            InternalModelStructureResolver()
            if structure_resolver is None
            else structure_resolver
        )
        self._structure_materializer = (
            InternalModelStructureMaterializer()
            if structure_materializer is None
            else structure_materializer
        )

    def assemble(
        self,
        *,
        project_id: str,
        internal_engineering_model_id: str,
        assembly_input: ModelCandidateAssemblyInput,
        assembly_provenance: InternalModelAssemblyProvenance,
        created_at: str,
        occupied_internal_model_element_ids: Iterable[str] = (),
        occupied_internal_model_relationship_ids: Iterable[str] = (),
    ) -> InternalEngineeringModelSnapshot:
        """Build one complete immutable in-memory IEM snapshot."""

        if not isinstance(assembly_input, ModelCandidateAssemblyInput):
            raise InternalModelValidationError(
                "assembly_input must be ModelCandidateAssemblyInput."
            )
        if project_id != assembly_input.project_id:
            raise InternalModelAssemblyBlockedError(
                "Phase-I project_id must match the H→I assembly input."
            )
        validate_internal_engineering_model_id(
            internal_engineering_model_id
        )
        if not isinstance(
            assembly_provenance,
            InternalModelAssemblyProvenance,
        ):
            raise InternalModelValidationError(
                "assembly_provenance has invalid type."
            )

        self._validate_candidate_scope(assembly_input)
        resolved_context = self._structure_resolver.resolve(
            assembly_input
        )

        element_id_by_candidate_id = self._allocate_element_ids(
            assembly_input.accepted_element_candidates,
            occupied_internal_model_element_ids,
        )
        elements = self._assemble_elements(
            internal_engineering_model_id=internal_engineering_model_id,
            assembly_input=assembly_input,
            element_id_by_candidate_id=element_id_by_candidate_id,
        )

        relationship_id_by_candidate_id = (
            self._allocate_relationship_ids(
                assembly_input.accepted_relationship_candidates,
                occupied_internal_model_relationship_ids,
            )
        )
        relationships = self._assemble_relationships(
            internal_engineering_model_id=internal_engineering_model_id,
            assembly_input=assembly_input,
            element_id_by_candidate_id=element_id_by_candidate_id,
            relationship_id_by_candidate_id=(
                relationship_id_by_candidate_id
            ),
        )

        structure = self._structure_materializer.materialize(
            project_id=project_id,
            internal_engineering_model_id=internal_engineering_model_id,
            assembly_input=assembly_input,
            resolved_context=resolved_context,
            internal_element_id_by_candidate_id=(
                element_id_by_candidate_id
            ),
        )

        manifest = create_internal_engineering_model_manifest(
            project_id=project_id,
            internal_engineering_model_id=internal_engineering_model_id,
            assembly_input_fingerprint=(
                calculate_model_candidate_assembly_input_fingerprint(
                    assembly_input
                )
            ),
            candidate_set_id=assembly_input.candidate_set_id,
            candidate_set_content_fingerprint=(
                assembly_input.candidate_set_content_fingerprint
            ),
            approved_input_snapshot_fingerprint=(
                assembly_input.approved_input_snapshot_fingerprint
            ),
            assembly_context=resolved_context.assembly_context,
            assembly_provenance=assembly_provenance,
            structure_content_fingerprint=structure.content_fingerprint,
            internal_model_element_ids=tuple(
                item.internal_model_element_id
                for item in elements
            ),
            internal_model_relationship_ids=tuple(
                item.internal_model_relationship_id
                for item in relationships
            ),
            review_decision_references=tuple(
                sorted(
                    assembly_input.review_decision_references,
                    key=lambda item: (
                        item.model_candidate_review_decision_id
                    ),
                )
            ),
            accepted_exception_references=tuple(
                sorted(
                    assembly_input.accepted_exception_decisions,
                    key=lambda item: (
                        item.model_candidate_review_decision_id
                    ),
                )
            ),
            created_at=created_at,
        )

        return InternalEngineeringModelSnapshot(
            manifest=manifest,
            structure=structure,
            elements=elements,
            relationships=relationships,
        )

    def _validate_candidate_scope(
        self,
        assembly_input: ModelCandidateAssemblyInput,
    ) -> None:
        seen_element_ids: set[str] = set()
        seen_subject_keys: set[str] = set()

        for candidate in assembly_input.accepted_element_candidates:
            if (
                candidate.project_id != assembly_input.project_id
                or candidate.candidate_set_id
                != assembly_input.candidate_set_id
            ):
                raise InternalModelAssemblyBlockedError(
                    "Accepted Element Candidate is outside the exact "
                    "H→I project/Candidate-Set scope."
                )
            if candidate.model_element_candidate_id in seen_element_ids:
                raise InternalModelIntegrityError(
                    "Accepted Element Candidate IDs must be unique."
                )
            if candidate.candidate_subject_key in seen_subject_keys:
                raise InternalModelAssemblyBlockedError(
                    "Accepted Element Candidates must have unique semantic "
                    "subject identities for deterministic assembly."
                )
            seen_element_ids.add(candidate.model_element_candidate_id)
            seen_subject_keys.add(candidate.candidate_subject_key)

        seen_relationship_ids: set[str] = set()
        for candidate in assembly_input.accepted_relationship_candidates:
            if (
                candidate.project_id != assembly_input.project_id
                or candidate.candidate_set_id
                != assembly_input.candidate_set_id
            ):
                raise InternalModelAssemblyBlockedError(
                    "Accepted Relationship Candidate is outside the exact "
                    "H→I project/Candidate-Set scope."
                )
            if (
                candidate.model_relationship_candidate_id
                in seen_relationship_ids
            ):
                raise InternalModelIntegrityError(
                    "Accepted Relationship Candidate IDs must be unique."
                )
            seen_relationship_ids.add(
                candidate.model_relationship_candidate_id
            )

    def _allocate_element_ids(
        self,
        candidates: tuple[ModelElementCandidate, ...],
        occupied_ids: Iterable[str],
    ) -> dict[str, str]:
        occupied = list(occupied_ids)
        result: dict[str, str] = {}

        for candidate in sorted(
            candidates,
            key=lambda item: item.model_element_candidate_id,
        ):
            internal_id = next_internal_model_element_id(occupied)
            occupied.append(internal_id)
            result[candidate.model_element_candidate_id] = internal_id

        return result

    def _allocate_relationship_ids(
        self,
        candidates: tuple[ModelRelationshipCandidate, ...],
        occupied_ids: Iterable[str],
    ) -> dict[str, str]:
        occupied = list(occupied_ids)
        result: dict[str, str] = {}

        for candidate in sorted(
            candidates,
            key=lambda item: item.model_relationship_candidate_id,
        ):
            internal_id = next_internal_model_relationship_id(occupied)
            occupied.append(internal_id)
            result[
                candidate.model_relationship_candidate_id
            ] = internal_id

        return result

    def _assemble_elements(
        self,
        *,
        internal_engineering_model_id: str,
        assembly_input: ModelCandidateAssemblyInput,
        element_id_by_candidate_id: dict[str, str],
    ) -> tuple[InternalModelElement, ...]:
        assembled: list[InternalModelElement] = []

        for candidate in sorted(
            assembly_input.accepted_element_candidates,
            key=lambda item: item.model_element_candidate_id,
        ):
            if candidate.framework_assignment is None:
                raise InternalModelAssemblyBlockedError(
                    "Accepted Element Candidate has no reviewed "
                    "framework_assignment: "
                    f"{candidate.model_element_candidate_id}."
                )

            review, exception = self._authorization_for(
                assembly_input,
                target_type="element_candidate",
                candidate_id=candidate.model_element_candidate_id,
            )

            attributes = tuple(
                InternalModelAttribute(
                    name=item.name,
                    value=item.value,
                )
                for item in sorted(
                    candidate.attributes,
                    key=lambda item: (item.name, item.value),
                )
            )
            approved_inputs = tuple(
                sorted(
                    candidate.approved_input_references,
                    key=lambda item: item.approved_input_id,
                )
            )

            assembled.append(
                create_internal_model_element(
                    project_id=assembly_input.project_id,
                    internal_engineering_model_id=(
                        internal_engineering_model_id
                    ),
                    internal_model_element_id=(
                        element_id_by_candidate_id[
                            candidate.model_element_candidate_id
                        ]
                    ),
                    model_subject_key=candidate.candidate_subject_key,
                    source_model_element_candidate_id=(
                        candidate.model_element_candidate_id
                    ),
                    source_model_element_candidate_fingerprint=(
                        candidate.content_fingerprint
                    ),
                    name=candidate.proposed_name,
                    description=candidate.description,
                    model_area=candidate.model_area,
                    element_type=candidate.element_type,
                    framework_assignment=(
                        candidate.framework_assignment
                    ),
                    terminology_assignment=(
                        candidate.terminology_assignment
                    ),
                    attributes=attributes,
                    comparison_anchor_id=(
                        candidate.comparison_anchor_id
                    ),
                    approved_input_references=approved_inputs,
                    review_decision_reference=review,
                    accepted_exception_reference=exception,
                )
            )

        return tuple(
            sorted(
                assembled,
                key=lambda item: item.internal_model_element_id,
            )
        )

    def _assemble_relationships(
        self,
        *,
        internal_engineering_model_id: str,
        assembly_input: ModelCandidateAssemblyInput,
        element_id_by_candidate_id: dict[str, str],
        relationship_id_by_candidate_id: dict[str, str],
    ) -> tuple[InternalModelRelationship, ...]:
        element_by_candidate_id = {
            item.model_element_candidate_id: item
            for item in assembly_input.accepted_element_candidates
        }
        assembled: list[InternalModelRelationship] = []

        for candidate in sorted(
            assembly_input.accepted_relationship_candidates,
            key=lambda item: item.model_relationship_candidate_id,
        ):
            source_candidate_id = self._resolved_endpoint_candidate_id(
                candidate,
                endpoint_name="source",
            )
            target_candidate_id = self._resolved_endpoint_candidate_id(
                candidate,
                endpoint_name="target",
            )

            source_candidate = element_by_candidate_id.get(
                source_candidate_id
            )
            target_candidate = element_by_candidate_id.get(
                target_candidate_id
            )
            if source_candidate is None or target_candidate is None:
                raise InternalModelAssemblyBlockedError(
                    "Accepted Relationship endpoint does not resolve to an "
                    "accepted Element Candidate: "
                    f"{candidate.model_relationship_candidate_id}."
                )

            if (
                candidate.source.candidate_subject_key
                != source_candidate.candidate_subject_key
                or candidate.target.candidate_subject_key
                != target_candidate.candidate_subject_key
            ):
                raise InternalModelAssemblyBlockedError(
                    "Accepted Relationship endpoint subject identity does "
                    "not match the resolved Element Candidate: "
                    f"{candidate.model_relationship_candidate_id}."
                )

            review, exception = self._authorization_for(
                assembly_input,
                target_type="relationship_candidate",
                candidate_id=(
                    candidate.model_relationship_candidate_id
                ),
            )

            assembled.append(
                create_internal_model_relationship(
                    project_id=assembly_input.project_id,
                    internal_engineering_model_id=(
                        internal_engineering_model_id
                    ),
                    internal_model_relationship_id=(
                        relationship_id_by_candidate_id[
                            candidate.model_relationship_candidate_id
                        ]
                    ),
                    source_internal_model_element_id=(
                        element_id_by_candidate_id[source_candidate_id]
                    ),
                    target_internal_model_element_id=(
                        element_id_by_candidate_id[target_candidate_id]
                    ),
                    source_model_subject_key=(
                        source_candidate.candidate_subject_key
                    ),
                    target_model_subject_key=(
                        target_candidate.candidate_subject_key
                    ),
                    relationship_family=candidate.relationship_family,
                    semantic_intent=candidate.semantic_intent,
                    directionality=candidate.directionality,
                    source_model_relationship_candidate_id=(
                        candidate.model_relationship_candidate_id
                    ),
                    source_model_relationship_candidate_fingerprint=(
                        candidate.content_fingerprint
                    ),
                    approved_input_references=tuple(
                        sorted(
                            candidate.approved_input_references,
                            key=lambda item: item.approved_input_id,
                        )
                    ),
                    review_decision_reference=review,
                    accepted_exception_reference=exception,
                )
            )

        return tuple(
            sorted(
                assembled,
                key=lambda item: item.internal_model_relationship_id,
            )
        )

    def _resolved_endpoint_candidate_id(
        self,
        candidate: ModelRelationshipCandidate,
        *,
        endpoint_name: str,
    ) -> str:
        endpoint = getattr(candidate, endpoint_name)

        if (
            endpoint.resolution_status != "resolved"
            or endpoint.resolved_model_element_candidate_id is None
            or endpoint.candidate_model_element_ids
            != (endpoint.resolved_model_element_candidate_id,)
        ):
            raise InternalModelAssemblyBlockedError(
                "Accepted Relationship has a non-exact "
                f"{endpoint_name} endpoint: "
                f"{candidate.model_relationship_candidate_id}."
            )

        return endpoint.resolved_model_element_candidate_id

    def _authorization_for(
        self,
        assembly_input: ModelCandidateAssemblyInput,
        *,
        target_type: str,
        candidate_id: str,
    ) -> tuple[
        ModelCandidateReviewDecisionReference,
        ModelCandidateReviewDecisionReference | None,
    ]:
        matches = tuple(
            item
            for item in assembly_input.review_decision_references
            if item.target_type == target_type
            and item.candidate_id == candidate_id
        )
        if len(matches) != 1:
            raise InternalModelAssemblyBlockedError(
                "Accepted Candidate requires exactly one authoritative "
                f"Review Decision reference: {candidate_id}."
            )

        review = matches[0]
        if review.decision not in {"accepted", "accepted_exception"}:
            raise InternalModelAssemblyBlockedError(
                "Accepted Candidate is not authorized by its Review "
                f"Decision reference: {candidate_id}."
            )

        exceptions = tuple(
            item
            for item in assembly_input.accepted_exception_decisions
            if item.target_type == target_type
            and item.candidate_id == candidate_id
        )

        if review.decision == "accepted_exception":
            if len(exceptions) != 1 or exceptions[0] != review:
                raise InternalModelAssemblyBlockedError(
                    "accepted_exception Candidate must preserve the exact "
                    f"exception Review reference: {candidate_id}."
                )
            return review, review

        if exceptions:
            raise InternalModelAssemblyBlockedError(
                "Normally accepted Candidate must not carry an exception "
                f"Review reference: {candidate_id}."
            )
        return review, None
