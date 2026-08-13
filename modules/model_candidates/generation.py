"""Approved-Input-only orchestration for Phase-H Candidate generation."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
from typing import Protocol, runtime_checkable

from modules.approved_input import ApprovedInputRepository
from modules.approved_input.types import ApprovedInputManifest
from modules.project_workspace import ProjectWorkspace
from modules.project_workspace.workspace import DEFAULT_PROJECTS_ROOT

from .candidate_set_manifest import (
    create_model_candidate_set_manifest,
)
from .element_manifest import create_model_element_candidate
from .errors import (
    ModelCandidateDerivationError,
    ModelCandidateGenerationBlockedError,
    ModelCandidateIntegrityError,
    ModelCandidateReferenceError,
    ModelCandidateValidationError,
)
from .identifiers import (
    next_model_element_candidate_id,
    next_model_relationship_candidate_id,
)
from .relationship_manifest import (
    create_model_relationship_candidate,
)
from .repository import ModelCandidateRepository
from .types import (
    ModelCandidateApprovedInputReference,
    ModelCandidateApprovedInputSelection,
    ModelCandidateDerivationPlan,
    ModelCandidateDerivationRequest,
    ModelCandidateGenerationProvenance,
    ModelCandidateSetSnapshot,
    ModelDerivationRulesReference,
    ModelElementCandidate,
    ModelElementCandidateDraft,
    ModelRelationshipCandidate,
    ModelRelationshipCandidateDraft,
    ModelRelationshipEndpoint,
    ModelStructureProfileReference,
)


def _default_clock() -> datetime:
    return datetime.now(timezone.utc)


@runtime_checkable
class ModelCandidateDeriver(Protocol):
    """Profile-aware derivation strategy consumed by the H5 orchestrator."""

    def derive(
        self,
        request: ModelCandidateDerivationRequest,
    ) -> ModelCandidateDerivationPlan:
        """Derive one deterministic proposal from the complete active snapshot."""


class ModelCandidateGenerationService:
    """Create and persist one Candidate Set from active Approved Inputs only."""

    def __init__(
        self,
        root=DEFAULT_PROJECTS_ROOT,
        *,
        approved_input_repository: ApprovedInputRepository | None = None,
        candidate_repository: ModelCandidateRepository | None = None,
        workspace: ProjectWorkspace | None = None,
        clock: Callable[[], datetime] = _default_clock,
    ) -> None:
        self.root = root
        self._approved_inputs = (
            ApprovedInputRepository(root=root)
            if approved_input_repository is None
            else approved_input_repository
        )
        self._candidates = (
            ModelCandidateRepository(root=root)
            if candidate_repository is None
            else candidate_repository
        )
        self._workspace = (
            ProjectWorkspace(root=root)
            if workspace is None
            else workspace
        )
        self._clock = clock

    def generate_candidate_set(
        self,
        project_id: str,
        *,
        deriver: ModelCandidateDeriver,
        model_structure_profile_reference: (
            ModelStructureProfileReference
        ),
        derivation_rules_reference: ModelDerivationRulesReference,
        generation_provenance: ModelCandidateGenerationProvenance | None = None,
        predecessor_candidate_set_id: str | None = None,
        regeneration_reason: str | None = None,
    ) -> ModelCandidateSetSnapshot:
        """Derive, bind and atomically persist one complete Candidate Set."""

        project = self._workspace.load_project(project_id)
        active_inputs = tuple(
            self._approved_inputs.list_active_approved_inputs(project_id)
        )
        active_inputs = self._validate_active_snapshot(
            project_id,
            active_inputs,
        )
        if not active_inputs:
            raise ModelCandidateGenerationBlockedError(
                "Phase-H Candidate generation requires at least one "
                "active Approved Input."
            )

        predecessor = self._load_predecessor(
            project_id,
            predecessor_candidate_set_id,
            regeneration_reason,
        )
        request = ModelCandidateDerivationRequest(
            project_id=project_id,
            approved_inputs=active_inputs,
            framework_template_reference=project.framework_template,
            model_structure_profile_reference=(
                model_structure_profile_reference
            ),
            derivation_rules_reference=derivation_rules_reference,
            predecessor_candidate_set=predecessor,
        )
        plan = self._derive(deriver, request)
        resolved_generation_provenance = self._resolve_generation_provenance(
            deriver,
            generation_provenance,
        )
        element_drafts = self._validate_element_drafts(
            plan.element_drafts,
            predecessor,
        )
        relationship_drafts = self._validate_relationship_drafts(
            plan.relationship_drafts,
            predecessor,
        )

        existing = self._candidates.list_candidate_sets(project_id)
        candidate_set_id = self._candidates.next_candidate_set_id(
            project_id
        )
        element_ids = self._allocate_element_ids(
            existing,
            len(element_drafts),
        )
        relationship_ids = self._allocate_relationship_ids(
            existing,
            len(relationship_drafts),
        )
        timestamp = self._timestamp()

        active_by_id = {
            item.approved_input_id: item
            for item in active_inputs
        }
        elements = tuple(
            self._materialize_element(
                project_id=project_id,
                candidate_set_id=candidate_set_id,
                candidate_id=candidate_id,
                draft=draft,
                active_by_id=active_by_id,
                timestamp=timestamp,
            )
            for candidate_id, draft in zip(
                element_ids,
                element_drafts,
                strict=True,
            )
        )
        subject_index = self._build_subject_index(elements)

        relationships = tuple(
            self._materialize_relationship(
                project_id=project_id,
                candidate_set_id=candidate_set_id,
                candidate_id=candidate_id,
                draft=draft,
                active_by_id=active_by_id,
                subject_index=subject_index,
                timestamp=timestamp,
            )
            for candidate_id, draft in zip(
                relationship_ids,
                relationship_drafts,
                strict=True,
            )
        )

        snapshot_refs = tuple(
            ModelCandidateApprovedInputReference(
                approved_input_id=item.approved_input_id,
                content_fingerprint=item.content_fingerprint,
                stable_subject_key=item.stable_subject_key,
                provenance_role="active_snapshot",
            )
            for item in active_inputs
        )
        manifest = create_model_candidate_set_manifest(
            project_id=project_id,
            candidate_set_id=candidate_set_id,
            predecessor_candidate_set_id=(
                predecessor_candidate_set_id
            ),
            regeneration_reason=regeneration_reason,
            approved_input_references=snapshot_refs,
            framework_template_reference=project.framework_template,
            model_structure_profile_reference=(
                model_structure_profile_reference
            ),
            derivation_rules_reference=derivation_rules_reference,
            generation_provenance=resolved_generation_provenance,
            element_candidate_ids=tuple(
                item.model_element_candidate_id
                for item in elements
            ),
            relationship_candidate_ids=tuple(
                item.model_relationship_candidate_id
                for item in relationships
            ),
            created_at=timestamp,
        )

        return self._candidates.persist_candidate_set(
            manifest,
            element_candidates=elements,
            relationship_candidates=relationships,
        )

    def _resolve_generation_provenance(
        self,
        deriver: ModelCandidateDeriver,
        explicit: ModelCandidateGenerationProvenance | None,
    ) -> ModelCandidateGenerationProvenance:
        """Resolve explicit or post-derivation strategy provenance."""

        if explicit is not None:
            if not isinstance(
                explicit,
                ModelCandidateGenerationProvenance,
            ):
                raise ModelCandidateValidationError(
                    "generation_provenance has invalid type."
                )
            return explicit

        provider = getattr(deriver, "generation_provenance", None)
        if provider is None or not callable(provider):
            raise ModelCandidateValidationError(
                "generation_provenance is required unless the deriver "
                "provides callable generation_provenance()."
            )
        try:
            value = provider()
        except ModelCandidateDerivationError:
            raise
        except Exception as exc:
            raise ModelCandidateDerivationError(
                "Deriver generation provenance resolution failed."
            ) from exc
        if not isinstance(value, ModelCandidateGenerationProvenance):
            raise ModelCandidateValidationError(
                "deriver generation_provenance() must return "
                "ModelCandidateGenerationProvenance."
            )
        return value

    def _derive(
        self,
        deriver: ModelCandidateDeriver,
        request: ModelCandidateDerivationRequest,
    ) -> ModelCandidateDerivationPlan:
        derive = getattr(deriver, "derive", None)
        if derive is None or not callable(derive):
            raise ModelCandidateValidationError(
                "deriver must provide callable derive(request)."
            )
        try:
            plan = derive(request)
        except ModelCandidateDerivationError:
            raise
        except Exception as exc:
            raise ModelCandidateDerivationError(
                "Model Candidate derivation failed."
            ) from exc
        if not isinstance(plan, ModelCandidateDerivationPlan):
            raise ModelCandidateDerivationError(
                "deriver must return ModelCandidateDerivationPlan."
            )
        return plan

    def _validate_active_snapshot(
        self,
        project_id: str,
        values: tuple[ApprovedInputManifest, ...],
    ) -> tuple[ApprovedInputManifest, ...]:
        if not all(isinstance(item, ApprovedInputManifest) for item in values):
            raise ModelCandidateGenerationBlockedError(
                "Approved Input repository returned an invalid manifest type."
            )
        ordered = tuple(
            sorted(values, key=lambda item: item.approved_input_id)
        )
        ids = tuple(item.approved_input_id for item in ordered)
        if len(ids) != len(set(ids)):
            raise ModelCandidateGenerationBlockedError(
                "Active Approved Input snapshot contains duplicate AIN IDs."
            )
        for item in ordered:
            if item.project_id != project_id:
                raise ModelCandidateGenerationBlockedError(
                    "Active Approved Input belongs to another project."
                )
        return ordered

    def _load_predecessor(
        self,
        project_id: str,
        predecessor_candidate_set_id: str | None,
        regeneration_reason: str | None,
    ) -> ModelCandidateSetSnapshot | None:
        if predecessor_candidate_set_id is None:
            if regeneration_reason is not None:
                raise ModelCandidateGenerationBlockedError(
                    "regeneration_reason requires predecessor_candidate_set_id."
                )
            return None
        if regeneration_reason is None or not regeneration_reason.strip():
            raise ModelCandidateGenerationBlockedError(
                "Regeneration requires a non-empty regeneration_reason."
            )
        return self._candidates.load_candidate_set(
            project_id,
            predecessor_candidate_set_id,
        )

    def _validate_element_drafts(
        self,
        drafts,
        predecessor: ModelCandidateSetSnapshot | None,
    ) -> tuple[ModelElementCandidateDraft, ...]:
        if not isinstance(drafts, tuple):
            raise ModelCandidateDerivationError(
                "element_drafts must be a tuple."
            )
        if not all(
            isinstance(item, ModelElementCandidateDraft)
            for item in drafts
        ):
            raise ModelCandidateDerivationError(
                "element_drafts contains an invalid draft type."
            )
        ordered = tuple(sorted(drafts, key=lambda item: item.draft_key))
        self._require_unique_draft_keys(
            ordered,
            label="Element",
        )
        predecessor_ids = (
            set()
            if predecessor is None
            else {
                item.model_element_candidate_id
                for item in predecessor.element_candidates
            }
        )
        for item in ordered:
            self._validate_draft_key(item.draft_key, label="Element")
            self._validate_predecessor_ids(
                item.predecessor_candidate_ids,
                predecessor_ids,
                label="Element",
                predecessor_present=predecessor is not None,
            )
        return ordered

    def _validate_relationship_drafts(
        self,
        drafts,
        predecessor: ModelCandidateSetSnapshot | None,
    ) -> tuple[ModelRelationshipCandidateDraft, ...]:
        if not isinstance(drafts, tuple):
            raise ModelCandidateDerivationError(
                "relationship_drafts must be a tuple."
            )
        if not all(
            isinstance(item, ModelRelationshipCandidateDraft)
            for item in drafts
        ):
            raise ModelCandidateDerivationError(
                "relationship_drafts contains an invalid draft type."
            )
        ordered = tuple(sorted(drafts, key=lambda item: item.draft_key))
        self._require_unique_draft_keys(
            ordered,
            label="Relationship",
        )
        predecessor_ids = (
            set()
            if predecessor is None
            else {
                item.model_relationship_candidate_id
                for item in predecessor.relationship_candidates
            }
        )
        for item in ordered:
            self._validate_draft_key(
                item.draft_key,
                label="Relationship",
            )
            self._validate_predecessor_ids(
                item.predecessor_candidate_ids,
                predecessor_ids,
                label="Relationship",
                predecessor_present=predecessor is not None,
            )
        return ordered

    def _validate_draft_key(self, value: str, *, label: str) -> None:
        if (
            not isinstance(value, str)
            or not value.strip()
            or value != value.strip()
        ):
            raise ModelCandidateDerivationError(
                f"{label} draft_key must be a non-empty trimmed string."
            )

    def _require_unique_draft_keys(self, drafts, *, label: str) -> None:
        keys = tuple(item.draft_key for item in drafts)
        if len(keys) != len(set(keys)):
            raise ModelCandidateDerivationError(
                f"{label} draft_key values must be unique."
            )

    def _validate_predecessor_ids(
        self,
        values: tuple[str, ...],
        allowed: set[str],
        *,
        label: str,
        predecessor_present: bool,
    ) -> None:
        if not isinstance(values, tuple):
            raise ModelCandidateDerivationError(
                f"{label} predecessor_candidate_ids must be a tuple."
            )
        if values and not predecessor_present:
            raise ModelCandidateReferenceError(
                f"{label} predecessor references require a predecessor "
                "Candidate Set."
            )
        if len(values) != len(set(values)):
            raise ModelCandidateDerivationError(
                f"{label} predecessor_candidate_ids must be unique."
            )
        outside = set(values) - allowed
        if outside:
            raise ModelCandidateReferenceError(
                f"{label} predecessor references are outside the "
                f"selected predecessor Candidate Set: {sorted(outside)}."
            )

    def _allocate_element_ids(
        self,
        existing: tuple[ModelCandidateSetSnapshot, ...],
        count: int,
    ) -> tuple[str, ...]:
        occupied = [
            item.model_element_candidate_id
            for snapshot in existing
            for item in snapshot.element_candidates
        ]
        allocated = []
        for _ in range(count):
            candidate_id = next_model_element_candidate_id(occupied)
            allocated.append(candidate_id)
            occupied.append(candidate_id)
        return tuple(allocated)

    def _allocate_relationship_ids(
        self,
        existing: tuple[ModelCandidateSetSnapshot, ...],
        count: int,
    ) -> tuple[str, ...]:
        occupied = [
            item.model_relationship_candidate_id
            for snapshot in existing
            for item in snapshot.relationship_candidates
        ]
        allocated = []
        for _ in range(count):
            candidate_id = next_model_relationship_candidate_id(occupied)
            allocated.append(candidate_id)
            occupied.append(candidate_id)
        return tuple(allocated)

    def _materialize_element(
        self,
        *,
        project_id: str,
        candidate_set_id: str,
        candidate_id: str,
        draft: ModelElementCandidateDraft,
        active_by_id: dict[str, ApprovedInputManifest],
        timestamp: str,
    ) -> ModelElementCandidate:
        references = self._resolve_provenance(
            draft.approved_input_selections,
            active_by_id,
        )
        return create_model_element_candidate(
            project_id=project_id,
            candidate_set_id=candidate_set_id,
            model_element_candidate_id=candidate_id,
            candidate_subject_key=draft.candidate_subject_key,
            comparison_anchor_id=draft.comparison_anchor_id,
            proposed_name=draft.proposed_name,
            description=draft.description,
            model_area=draft.model_area,
            element_type=draft.element_type,
            framework_assignment=draft.framework_assignment,
            terminology_assignment=draft.terminology_assignment,
            attributes=draft.attributes,
            approved_input_references=references,
            derivation_rationale=draft.derivation_rationale,
            support_level=draft.support_level,
            assumptions=draft.assumptions,
            missing_information=draft.missing_information,
            structure_profile_conformance=(
                draft.structure_profile_conformance
            ),
            predecessor_candidate_ids=(
                draft.predecessor_candidate_ids
            ),
            created_at=timestamp,
        )

    def _materialize_relationship(
        self,
        *,
        project_id: str,
        candidate_set_id: str,
        candidate_id: str,
        draft: ModelRelationshipCandidateDraft,
        active_by_id: dict[str, ApprovedInputManifest],
        subject_index: dict[str, tuple[str, ...]],
        timestamp: str,
    ) -> ModelRelationshipCandidate:
        references = self._resolve_provenance(
            draft.approved_input_selections,
            active_by_id,
        )
        return create_model_relationship_candidate(
            project_id=project_id,
            candidate_set_id=candidate_set_id,
            model_relationship_candidate_id=candidate_id,
            relationship_choice_key=draft.relationship_choice_key,
            source=self._resolve_endpoint(
                draft.source_subject_key,
                subject_index,
            ),
            target=self._resolve_endpoint(
                draft.target_subject_key,
                subject_index,
            ),
            relationship_family=draft.relationship_family,
            semantic_intent=draft.semantic_intent,
            directionality=draft.directionality,
            approved_input_references=references,
            derivation_rationale=draft.derivation_rationale,
            supporting_evidence=draft.supporting_evidence,
            assumptions=draft.assumptions,
            missing_information=draft.missing_information,
            priority_assessment=draft.priority_assessment,
            comparability_assessment=draft.comparability_assessment,
            structure_profile_conformance=(
                draft.structure_profile_conformance
            ),
            upstream_relationship_representation=(
                draft.upstream_relationship_representation
            ),
            predecessor_candidate_ids=(
                draft.predecessor_candidate_ids
            ),
            created_at=timestamp,
        )

    def _resolve_provenance(
        self,
        selections: tuple[ModelCandidateApprovedInputSelection, ...],
        active_by_id: dict[str, ApprovedInputManifest],
    ) -> tuple[ModelCandidateApprovedInputReference, ...]:
        if not isinstance(selections, tuple) or not selections:
            raise ModelCandidateDerivationError(
                "Candidate draft requires at least one Approved Input "
                "selection."
            )
        ids = tuple(item.approved_input_id for item in selections)
        if len(ids) != len(set(ids)):
            raise ModelCandidateDerivationError(
                "Candidate draft must not select the same Approved "
                "Input more than once."
            )

        references = []
        for selection in sorted(
            selections,
            key=lambda item: item.approved_input_id,
        ):
            if not isinstance(
                selection,
                ModelCandidateApprovedInputSelection,
            ):
                raise ModelCandidateDerivationError(
                    "approved_input_selections contains invalid type."
                )
            if (
                not isinstance(selection.provenance_role, str)
                or not selection.provenance_role.strip()
                or selection.provenance_role
                != selection.provenance_role.strip()
            ):
                raise ModelCandidateDerivationError(
                    "provenance_role must be a non-empty trimmed string."
                )
            manifest = active_by_id.get(selection.approved_input_id)
            if manifest is None:
                raise ModelCandidateReferenceError(
                    "Candidate draft references an Approved Input "
                    "outside the active snapshot: "
                    f"{selection.approved_input_id}."
                )
            references.append(
                ModelCandidateApprovedInputReference(
                    approved_input_id=manifest.approved_input_id,
                    content_fingerprint=manifest.content_fingerprint,
                    stable_subject_key=manifest.stable_subject_key,
                    provenance_role=selection.provenance_role,
                )
            )
        return tuple(references)

    def _build_subject_index(
        self,
        elements: tuple[ModelElementCandidate, ...],
    ) -> dict[str, tuple[str, ...]]:
        index: dict[str, list[str]] = {}
        for item in elements:
            index.setdefault(
                item.candidate_subject_key,
                [],
            ).append(item.model_element_candidate_id)
        return {
            key: tuple(sorted(values))
            for key, values in sorted(index.items())
        }

    def _resolve_endpoint(
        self,
        subject_key: str,
        subject_index: dict[str, tuple[str, ...]],
    ) -> ModelRelationshipEndpoint:
        candidate_ids = subject_index.get(subject_key, ())
        if not candidate_ids:
            return ModelRelationshipEndpoint(
                candidate_subject_key=subject_key,
                resolution_status="unresolved",
                resolved_model_element_candidate_id=None,
                candidate_model_element_ids=(),
            )
        if len(candidate_ids) == 1:
            return ModelRelationshipEndpoint(
                candidate_subject_key=subject_key,
                resolution_status="resolved",
                resolved_model_element_candidate_id=candidate_ids[0],
                candidate_model_element_ids=candidate_ids,
            )
        return ModelRelationshipEndpoint(
            candidate_subject_key=subject_key,
            resolution_status="ambiguous",
            resolved_model_element_candidate_id=None,
            candidate_model_element_ids=candidate_ids,
        )

    def _timestamp(self) -> str:
        value = self._clock()
        if not isinstance(value, datetime):
            raise ModelCandidateGenerationBlockedError(
                "clock must return datetime."
            )
        if value.tzinfo is None or value.utcoffset() is None:
            raise ModelCandidateGenerationBlockedError(
                "clock must return timezone-aware datetime."
            )
        return (
            value.astimezone(timezone.utc)
            .isoformat(timespec="seconds")
            .replace("+00:00", "Z")
        )
