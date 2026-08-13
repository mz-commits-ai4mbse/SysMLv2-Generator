"""Production orchestration for idempotent Phase-I assembly and persistence."""

from __future__ import annotations

from pathlib import Path

from modules.model_candidates.types import ModelCandidateAssemblyInput
from modules.project_workspace.workspace import DEFAULT_PROJECTS_ROOT

from .assembly import InternalModelAssemblyService
from .assembly_input import (
    calculate_model_candidate_assembly_input_fingerprint,
)
from .repository import InternalModelRepository
from .structure_materialization import InternalModelStructureResolver
from .types import (
    InternalEngineeringModelSnapshot,
    InternalModelAssemblyProvenance,
)


class InternalModelPersistenceService:
    """Assemble once per exact authority state and atomically persist the IEM."""

    def __init__(
        self,
        *,
        root: Path | str = DEFAULT_PROJECTS_ROOT,
        repository: InternalModelRepository | None = None,
        structure_resolver: InternalModelStructureResolver | None = None,
    ) -> None:
        self._repository = (
            InternalModelRepository(root=root)
            if repository is None
            else repository
        )
        self._structure_resolver = (
            InternalModelStructureResolver()
            if structure_resolver is None
            else structure_resolver
        )
        self._assembly_service = InternalModelAssemblyService(
            structure_resolver=self._structure_resolver,
        )

    @property
    def repository(self) -> InternalModelRepository:
        return self._repository

    def assemble_and_persist(
        self,
        *,
        assembly_input: ModelCandidateAssemblyInput,
        assembly_provenance: InternalModelAssemblyProvenance,
        created_at: str,
    ) -> InternalEngineeringModelSnapshot:
        """Return prior exact assembly or create one new immutable snapshot."""

        input_fingerprint = (
            calculate_model_candidate_assembly_input_fingerprint(
                assembly_input
            )
        )
        resolved = self._structure_resolver.resolve(assembly_input)

        existing = self._repository.find_by_assembly_identity(
            assembly_input.project_id,
            assembly_input_fingerprint=input_fingerprint,
            assembly_rules_reference=(
                resolved.assembly_context.assembly_rules_reference
            ),
        )
        if existing is not None:
            return existing

        iem_id = self._repository.next_internal_engineering_model_id(
            assembly_input.project_id
        )
        occupied_elements = (
            self._repository.occupied_internal_model_element_ids(
                assembly_input.project_id
            )
        )
        occupied_relationships = (
            self._repository.occupied_internal_model_relationship_ids(
                assembly_input.project_id
            )
        )

        snapshot = self._assembly_service.assemble(
            project_id=assembly_input.project_id,
            internal_engineering_model_id=iem_id,
            assembly_input=assembly_input,
            assembly_provenance=assembly_provenance,
            created_at=created_at,
            occupied_internal_model_element_ids=occupied_elements,
            occupied_internal_model_relationship_ids=(
                occupied_relationships
            ),
        )
        return self._repository.persist_snapshot(snapshot)
