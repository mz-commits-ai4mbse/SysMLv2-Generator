"""Deterministic package, symbol and ordering projection for Phase-J J3."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from modules.internal_model.types import InternalEngineeringModelSnapshot

from .artifact_structure import (
    load_artifact_structure_profile,
    validate_artifact_structure_profile,
)
from .errors import (
    SysMLGenerationBlockedError,
    SysMLGenerationValidationError,
)
from .generation_profile import (
    find_element_mapping,
    find_relationship_mapping,
    load_generation_profile,
    validate_generation_profile,
)
from .identifiers import (
    generated_element_symbol,
    generated_relationship_symbol,
)
from .preflight import SysMLGenerationPreflightService
from .projection_types import (
    SysMLElementProjection,
    SysMLPackageProjection,
    SysMLProjectionPlan,
    SysMLRelationshipProjection,
)
from .target_notation import (
    load_target_notation,
    validate_target_notation,
)
from .text_safety import (
    normalize_engineering_text,
    normalize_optional_engineering_text,
)
from .types import SysMLGenerationFinding


class SysMLProjectionPlanService:
    """Create one canonical renderer-neutral projection plan from a ready IEM."""

    def build(
        self,
        snapshot: InternalEngineeringModelSnapshot,
        *,
        target_notation: dict[str, Any] | None = None,
        generation_profile: dict[str, Any] | None = None,
        artifact_structure: dict[str, Any] | None = None,
    ) -> SysMLProjectionPlan:
        target = (
            load_target_notation()
            if target_notation is None
            else validate_target_notation(target_notation)
        )
        generation = (
            load_generation_profile()
            if generation_profile is None
            else validate_generation_profile(generation_profile)
        )
        structure_profile = (
            load_artifact_structure_profile()
            if artifact_structure is None
            else validate_artifact_structure_profile(artifact_structure)
        )

        preflight = SysMLGenerationPreflightService().require_ready(
            snapshot,
            target_notation=target,
            generation_profile=generation,
            artifact_structure=structure_profile,
        )

        packages = self._project_packages(snapshot, structure_profile)
        package_by_node = {
            item.framework_node_id: item
            for item in packages
        }

        element_membership = self._element_membership(snapshot)
        elements = self._project_elements(
            snapshot,
            generation,
            package_by_node,
            element_membership,
        )
        element_by_id = {
            item.internal_model_element_id: item
            for item in elements
        }
        relationships = self._project_relationships(
            snapshot,
            generation,
            element_by_id,
        )

        unit = structure_profile["output_units"][0]

        project_id = getattr(snapshot.manifest, "project_id", None)
        if project_id is None and snapshot.elements:
            project_id = snapshot.elements[0].project_id
        if project_id is None:
            project_id = snapshot.structure.project_id
        if not isinstance(project_id, str) or not project_id:
            self._block(
                "PROJECTION_CONTEXT_ERROR",
                "Unable to resolve project_id from the validated IEM snapshot.",
                target_type="internal_engineering_model",
                target_id=snapshot.manifest.internal_engineering_model_id,
            )

        return SysMLProjectionPlan(
            project_id=project_id,
            internal_engineering_model_id=(
                snapshot.manifest.internal_engineering_model_id
            ),
            target_notation_reference=preflight.target_notation_reference,
            generation_profile_reference=preflight.generation_profile_reference,
            artifact_structure_reference=preflight.artifact_structure_reference,
            generated_unit_id=unit["unit_id"],
            relative_path=unit["relative_path"],
            root_package_name=structure_profile["root_package"]["package_name"],
            packages=packages,
            elements=elements,
            relationships=relationships,
        )

    def _project_packages(
        self,
        snapshot: InternalEngineeringModelSnapshot,
        structure_profile: dict[str, Any],
    ) -> tuple[SysMLPackageProjection, ...]:
        config = {
            item["framework_node_id"]: item
            for item in structure_profile["framework_package_mappings"]
        }
        nodes = {
            item.framework_node_id: item
            for item in snapshot.structure.nodes
        }

        children: dict[str | None, list[str]] = defaultdict(list)
        for node_id, node in nodes.items():
            children[node.parent_framework_node_id].append(node_id)

        def sibling_key(node_id: str) -> tuple[int, str]:
            return (nodes[node_id].order, node_id)

        result: list[SysMLPackageProjection] = []

        def visit(
            node_id: str,
            *,
            depth: int,
            parent_package_name: str | None,
            parent_order_path: tuple[int, ...],
        ) -> None:
            node = nodes[node_id]
            mapping = config[node_id]
            order_path = parent_order_path + (node.order,)
            result.append(
                SysMLPackageProjection(
                    framework_node_id=node_id,
                    mapping_key=node.mapping_key,
                    package_name=mapping["package_name"],
                    parent_framework_node_id=node.parent_framework_node_id,
                    parent_package_name=parent_package_name,
                    order=node.order,
                    depth=depth,
                    order_path=order_path,
                    include_empty=mapping["include_empty"],
                )
            )
            for child_id in sorted(children.get(node_id, ()), key=sibling_key):
                visit(
                    child_id,
                    depth=depth + 1,
                    parent_package_name=mapping["package_name"],
                    parent_order_path=order_path,
                )

        for root_id in sorted(children.get(None, ()), key=sibling_key):
            visit(
                root_id,
                depth=1,
                parent_package_name=structure_profile["root_package"][
                    "package_name"
                ],
                parent_order_path=(),
            )

        if len(result) != len(nodes):
            self._block(
                "STRUCTURE_PROJECTION_ERROR",
                "Canonical Framework traversal did not visit every IEM node.",
                target_type="internal_engineering_model",
                target_id=snapshot.manifest.internal_engineering_model_id,
            )

        return tuple(result)

    def _element_membership(
        self,
        snapshot: InternalEngineeringModelSnapshot,
    ) -> dict[str, str]:
        memberships: dict[str, list[str]] = defaultdict(list)
        for node in snapshot.structure.nodes:
            for element_id in node.internal_model_element_ids:
                memberships[element_id].append(node.framework_node_id)

        result: dict[str, str] = {}
        for element in snapshot.elements:
            element_id = element.internal_model_element_id
            found = memberships.get(element_id, [])
            if len(found) != 1:
                self._block(
                    "STRUCTURE_PROJECTION_ERROR",
                    "Projection requires exactly one Framework package "
                    "membership per IEM element.",
                    target_type="internal_model_element",
                    target_id=element_id,
                )
            result[element_id] = found[0]
        return result

    def _project_elements(
        self,
        snapshot: InternalEngineeringModelSnapshot,
        generation_profile: dict[str, Any],
        package_by_node: dict[str, SysMLPackageProjection],
        membership: dict[str, str],
    ) -> tuple[SysMLElementProjection, ...]:
        package_rank = {
            package.framework_node_id: index
            for index, package in enumerate(package_by_node.values())
        }

        projected: list[SysMLElementProjection] = []
        for element in snapshot.elements:
            element_id = element.internal_model_element_id
            node_id = membership[element_id]
            package = package_by_node[node_id]
            mapping = find_element_mapping(
                generation_profile,
                model_area=element.model_area,
                element_type=element.element_type,
            )
            if mapping is None or mapping["mapping_status"] != "supported":
                self._block(
                    "UNSUPPORTED_ELEMENT_MAPPING",
                    "Element became unsupported after successful preflight.",
                    target_type="internal_model_element",
                    target_id=element_id,
                    profile_rule_id=(
                        None if mapping is None else mapping["rule_id"]
                    ),
                )

            try:
                engineering_name = normalize_engineering_text(
                    element.name,
                    label=f"{element_id} engineering name",
                    allow_empty=False,
                )
                description = normalize_optional_engineering_text(
                    element.description,
                    label=f"{element_id} engineering description",
                )
            except SysMLGenerationValidationError as exc:
                self._block(
                    "UNSAFE_DOCUMENTATION_CONTENT",
                    str(exc),
                    target_type="internal_model_element",
                    target_id=element_id,
                    profile_rule_id=mapping["rule_id"],
                )

            projected.append(
                SysMLElementProjection(
                    internal_model_element_id=element_id,
                    generated_symbol=generated_element_symbol(element_id),
                    framework_node_id=node_id,
                    package_name=package.package_name,
                    model_area=element.model_area,
                    element_type=element.element_type,
                    engineering_name=engineering_name,
                    engineering_description=description,
                    generation_rule_id=mapping["rule_id"],
                    target_construct_id=mapping["target_construct_id"],
                )
            )

        projected.sort(
            key=lambda item: (
                package_rank[item.framework_node_id],
                item.internal_model_element_id,
            )
        )
        return tuple(projected)

    def _project_relationships(
        self,
        snapshot: InternalEngineeringModelSnapshot,
        generation_profile: dict[str, Any],
        element_by_id: dict[str, SysMLElementProjection],
    ) -> tuple[SysMLRelationshipProjection, ...]:
        projected: list[SysMLRelationshipProjection] = []

        for relation in snapshot.relationships:
            relation_id = relation.internal_model_relationship_id
            mapping = find_relationship_mapping(
                generation_profile,
                relationship_family=relation.relationship_family,
                semantic_intent=relation.semantic_intent,
                directionality=relation.directionality,
            )
            if mapping is None or mapping["mapping_status"] != "supported":
                self._block(
                    "UNSUPPORTED_RELATIONSHIP_MAPPING",
                    "Relationship became unsupported after successful preflight.",
                    target_type="internal_model_relationship",
                    target_id=relation_id,
                    profile_rule_id=(
                        None if mapping is None else mapping["rule_id"]
                    ),
                )

            source = element_by_id.get(
                relation.source_internal_model_element_id
            )
            target = element_by_id.get(
                relation.target_internal_model_element_id
            )
            if source is None or target is None:
                self._block(
                    "UNRESOLVED_GENERATED_ENDPOINT",
                    "Relationship endpoint has no element projection.",
                    target_type="internal_model_relationship",
                    target_id=relation_id,
                    profile_rule_id=mapping["rule_id"],
                )

            projected.append(
                SysMLRelationshipProjection(
                    internal_model_relationship_id=relation_id,
                    generated_trace_symbol=generated_relationship_symbol(
                        relation_id
                    ),
                    source_internal_model_element_id=(
                        relation.source_internal_model_element_id
                    ),
                    target_internal_model_element_id=(
                        relation.target_internal_model_element_id
                    ),
                    source_generated_symbol=source.generated_symbol,
                    target_generated_symbol=target.generated_symbol,
                    relationship_family=relation.relationship_family,
                    semantic_intent=relation.semantic_intent,
                    directionality=relation.directionality,
                    generation_rule_id=mapping["rule_id"],
                    target_construct_id=mapping["target_construct_id"],
                    endpoint_rendering=mapping["endpoint_rendering"],
                )
            )

        projected.sort(
            key=lambda item: item.internal_model_relationship_id
        )
        return tuple(projected)

    @staticmethod
    def _block(
        code: str,
        message: str,
        *,
        target_type: str | None = None,
        target_id: str | None = None,
        profile_rule_id: str | None = None,
    ) -> None:
        finding = SysMLGenerationFinding(
            code=code,
            message=message,
            issue_level="error",
            blocking=True,
            target_type=target_type,
            target_id=target_id,
            profile_rule_id=profile_rule_id,
        )
        error = SysMLGenerationBlockedError(message)
        error.findings = (finding,)
        raise error
