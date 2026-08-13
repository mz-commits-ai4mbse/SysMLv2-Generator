"""Resolve pinned Phase-I structure context and materialize template hierarchy."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from modules.framework import (
    DEFAULT_FRAMEWORK_TEMPLATE_PATH,
    FrameworkTemplateError,
    load_framework_template,
)
from modules.model_candidates.errors import ModelCandidateValidationError
from modules.model_candidates.structure_profile import (
    DEFAULT_MODEL_STRUCTURE_PROFILE_PATH,
    load_model_structure_profile,
)
from modules.model_candidates.types import (
    ModelCandidateAssemblyInput,
    ModelStructureProfile,
)

from .assembly_rules import (
    DEFAULT_INTERNAL_MODEL_ASSEMBLY_RULES_PATH,
    calculate_internal_model_assembly_rules_fingerprint,
    load_internal_model_assembly_rules,
)
from .errors import (
    InternalModelAssemblyBlockedError,
    InternalModelReferenceError,
    InternalModelValidationError,
)
from .identifiers import validate_internal_model_element_id
from .structure_manifest import create_internal_model_structure
from .types import (
    InternalModelAssemblyContext,
    InternalModelAssemblyRulesReference,
    InternalModelStructure,
    InternalModelStructureNode,
)


@dataclass(frozen=True, slots=True)
class ResolvedInternalModelStructureContext:
    """Exact locally resolved configuration matching the H→I handoff."""

    assembly_context: InternalModelAssemblyContext
    framework_template: dict[str, Any]
    model_structure_profile: ModelStructureProfile


class InternalModelStructureResolver:
    """Resolve and verify all pinned structure configuration for Phase I."""

    def __init__(
        self,
        *,
        framework_template_path: Path | str = DEFAULT_FRAMEWORK_TEMPLATE_PATH,
        model_structure_profile_path: (
            Path | str
        ) = DEFAULT_MODEL_STRUCTURE_PROFILE_PATH,
        assembly_rules_path: (
            Path | str
        ) = DEFAULT_INTERNAL_MODEL_ASSEMBLY_RULES_PATH,
    ) -> None:
        self.framework_template_path = Path(framework_template_path)
        self.model_structure_profile_path = Path(
            model_structure_profile_path
        )
        self.assembly_rules_path = Path(assembly_rules_path)

    def resolve(
        self,
        assembly_input: ModelCandidateAssemblyInput,
    ) -> ResolvedInternalModelStructureContext:
        """Fail closed unless local config exactly matches pinned H→I refs."""

        if not isinstance(assembly_input, ModelCandidateAssemblyInput):
            raise InternalModelValidationError(
                "assembly_input must be ModelCandidateAssemblyInput."
            )

        try:
            template = load_framework_template(
                self.framework_template_path
            )
        except FrameworkTemplateError as exc:
            raise InternalModelReferenceError(
                "Unable to resolve pinned Framework Template."
            ) from exc

        template_ref = assembly_input.framework_template_reference
        if (
            template["template_id"] != template_ref.template_id
            or template["template_version"] != template_ref.template_version
        ):
            raise InternalModelReferenceError(
                "Resolved Framework Template does not match the "
                "pinned H→I reference."
            )

        try:
            profile = load_model_structure_profile(
                self.model_structure_profile_path,
                framework_template=template,
            )
        except ModelCandidateValidationError as exc:
            raise InternalModelReferenceError(
                "Unable to resolve pinned Model Structure Profile."
            ) from exc
        profile_ref = assembly_input.model_structure_profile_reference
        if (
            profile.profile_id != profile_ref.profile_id
            or profile.profile_version != profile_ref.profile_version
            or profile.profile_fingerprint
            != profile_ref.profile_fingerprint
        ):
            raise InternalModelReferenceError(
                "Resolved Model Structure Profile does not match the "
                "pinned H→I reference."
            )

        rules = load_internal_model_assembly_rules(
            self.assembly_rules_path
        )
        if (
            rules["framework_template_id"] != template_ref.template_id
            or rules["framework_template_version"]
            != template_ref.template_version
            or rules["model_structure_profile_id"]
            != profile_ref.profile_id
            or rules["model_structure_profile_version"]
            != profile_ref.profile_version
        ):
            raise InternalModelReferenceError(
                "Internal Model assembly rules are not bound to the "
                "pinned Framework/Profile context."
            )

        rules_ref = InternalModelAssemblyRulesReference(
            rules_id=rules["rules_id"],
            rules_version=rules["rules_version"],
            rules_fingerprint=(
                calculate_internal_model_assembly_rules_fingerprint(rules)
            ),
        )

        return ResolvedInternalModelStructureContext(
            assembly_context=InternalModelAssemblyContext(
                framework_template_reference=template_ref,
                model_structure_profile_reference=profile_ref,
                derivation_rules_reference=(
                    assembly_input.derivation_rules_reference
                ),
                assembly_rules_reference=rules_ref,
            ),
            framework_template=template,
            model_structure_profile=profile,
        )


class InternalModelStructureMaterializer:
    """Materialize complete template hierarchy with exact IME membership."""

    def materialize(
        self,
        *,
        project_id: str,
        internal_engineering_model_id: str,
        assembly_input: ModelCandidateAssemblyInput,
        resolved_context: ResolvedInternalModelStructureContext,
        internal_element_id_by_candidate_id: Mapping[str, str],
    ) -> InternalModelStructure:
        """Build deterministic structure without reclassifying H Candidates."""

        self._validate_context_matches_input(
            assembly_input,
            resolved_context,
        )

        candidates = tuple(
            assembly_input.accepted_element_candidates
        )
        candidate_ids = {
            item.model_element_candidate_id for item in candidates
        }
        mapping_ids = set(internal_element_id_by_candidate_id)

        if mapping_ids != candidate_ids:
            missing = sorted(candidate_ids - mapping_ids)
            extra = sorted(mapping_ids - candidate_ids)
            raise InternalModelAssemblyBlockedError(
                "Structure materialization requires exactly one IME mapping "
                "for every accepted Element Candidate; "
                f"missing={missing}, extra={extra}."
            )

        ime_ids = tuple(
            validate_internal_model_element_id(
                internal_element_id_by_candidate_id[candidate_id]
            )
            for candidate_id in sorted(candidate_ids)
        )
        if len(ime_ids) != len(set(ime_ids)):
            raise InternalModelAssemblyBlockedError(
                "Multiple accepted Element Candidates map to the same IME."
            )

        profile = resolved_context.model_structure_profile
        area_by_id = {
            area.model_area_id: area for area in profile.model_areas
        }
        membership: dict[str, list[str]] = {}

        for candidate in candidates:
            area = area_by_id.get(candidate.model_area)
            if area is None:
                raise InternalModelAssemblyBlockedError(
                    "Accepted Element Candidate references an unknown "
                    f"model_area: {candidate.model_element_candidate_id}."
                )
            if candidate.framework_assignment != area.framework_node_id:
                raise InternalModelAssemblyBlockedError(
                    "Accepted Element Candidate framework_assignment does "
                    "not match its reviewed profile area: "
                    f"{candidate.model_element_candidate_id}."
                )
            if candidate.element_type not in area.permitted_element_types:
                raise InternalModelAssemblyBlockedError(
                    "Accepted Element Candidate element_type is not "
                    "permitted in its reviewed model_area: "
                    f"{candidate.model_element_candidate_id}."
                )

            ime_id = internal_element_id_by_candidate_id[
                candidate.model_element_candidate_id
            ]
            membership.setdefault(
                candidate.framework_assignment,
                [],
            ).append(ime_id)

        nodes = tuple(
            InternalModelStructureNode(
                framework_node_id=node["node_id"],
                mapping_key=node["mapping_key"],
                name=node["name"],
                node_type=node["node_type"],
                parent_framework_node_id=node["parent_node_id"],
                order=node["order"],
                internal_model_element_ids=tuple(
                    sorted(membership.get(node["node_id"], ()))
                ),
            )
            for node in self._ordered_template_nodes(
                resolved_context.framework_template
            )
        )

        return create_internal_model_structure(
            project_id=project_id,
            internal_engineering_model_id=internal_engineering_model_id,
            framework_template_reference=(
                assembly_input.framework_template_reference
            ),
            nodes=nodes,
        )

    def _ordered_template_nodes(
        self,
        template: dict[str, Any],
    ) -> tuple[dict[str, Any], ...]:
        roots = sorted(
            (
                node
                for node in template["nodes"]
                if node["parent_node_id"] is None
            ),
            key=lambda item: (item["order"], item["node_id"]),
        )
        children: dict[str, list[dict[str, Any]]] = {}
        for node in template["nodes"]:
            parent = node["parent_node_id"]
            if parent is None:
                continue
            children.setdefault(parent, []).append(node)

        ordered: list[dict[str, Any]] = []
        for root in roots:
            ordered.append(root)
            ordered.extend(
                sorted(
                    children.get(root["node_id"], ()),
                    key=lambda item: (
                        item["order"],
                        item["node_id"],
                    ),
                )
            )

        if len(ordered) != len(template["nodes"]):
            raise InternalModelAssemblyBlockedError(
                "Framework Template hierarchy cannot be deterministically "
                "materialized."
            )
        return tuple(ordered)

    def _validate_context_matches_input(
        self,
        assembly_input: ModelCandidateAssemblyInput,
        resolved_context: ResolvedInternalModelStructureContext,
    ) -> None:
        context = resolved_context.assembly_context
        if (
            context.framework_template_reference
            != assembly_input.framework_template_reference
            or context.model_structure_profile_reference
            != assembly_input.model_structure_profile_reference
            or context.derivation_rules_reference
            != assembly_input.derivation_rules_reference
        ):
            raise InternalModelReferenceError(
                "Resolved structure context does not match the exact H→I "
                "assembly input."
            )
