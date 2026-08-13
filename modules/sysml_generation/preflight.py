"""Deterministic Phase-J generation preflight for mapping completeness."""

from __future__ import annotations

from dataclasses import dataclass

from modules.internal_model.types import InternalEngineeringModelSnapshot

from .artifact_structure import (
    load_artifact_structure_profile,
    load_artifact_structure_reference,
    validate_artifact_structure_profile,
)
from .errors import SysMLGenerationBlockedError
from .generation_profile import (
    find_element_mapping,
    find_relationship_mapping,
    load_generation_profile,
    load_generation_profile_reference,
    validate_generation_profile,
)
from .identifiers import (
    generated_element_symbol,
    generated_relationship_symbol,
)
from .target_notation import (
    load_target_notation,
    load_target_notation_reference,
    validate_target_notation,
)
from .types import (
    SysMLArtifactStructureReference,
    SysMLGenerationFinding,
    SysMLGenerationProfileReference,
    TargetNotationReference,
)


@dataclass(frozen=True, slots=True)
class SysMLGenerationPreflightResult:
    """Deterministic preflight result before any Phase-J rendering."""

    target_notation_reference: TargetNotationReference
    generation_profile_reference: SysMLGenerationProfileReference
    artifact_structure_reference: SysMLArtifactStructureReference
    findings: tuple[SysMLGenerationFinding, ...]

    @property
    def blocking_findings(self) -> tuple[SysMLGenerationFinding, ...]:
        return tuple(item for item in self.findings if item.blocking)

    @property
    def ready(self) -> bool:
        return not self.blocking_findings


class SysMLGenerationPreflightService:
    """Evaluate whether one exact IEM is completely serializable under J2 policy."""

    def evaluate(
        self,
        snapshot: InternalEngineeringModelSnapshot,
        *,
        target_notation: dict | None = None,
        generation_profile: dict | None = None,
        artifact_structure: dict | None = None,
    ) -> SysMLGenerationPreflightResult:
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

        findings: list[SysMLGenerationFinding] = []
        allowed_constructs = {
            item["construct_id"]
            for item in target["allowed_constructs"]
            if item.get("allowed") is True
        }

        self._check_profile_references(
            snapshot,
            target,
            generation,
            structure_profile,
            findings,
        )
        package_membership = self._check_structure_projection(
            snapshot,
            structure_profile,
            findings,
        )
        generated_symbols, element_kinds, element_constructs = self._check_elements(
            snapshot,
            generation,
            allowed_constructs,
            package_membership,
            findings,
        )
        self._check_relationships(
            snapshot,
            generation,
            allowed_constructs,
            generated_symbols,
            element_kinds,
            element_constructs,
            findings,
        )

        ordered = tuple(
            sorted(
                findings,
                key=lambda item: (
                    0 if item.blocking else 1,
                    item.code,
                    item.target_type or "",
                    item.target_id or "",
                    item.profile_rule_id or "",
                    item.message,
                ),
            )
        )

        return SysMLGenerationPreflightResult(
            target_notation_reference=(
                load_target_notation_reference()
                if target_notation is None
                else TargetNotationReference(
                    context_id=target["context_id"],
                    version=target["version"],
                    content_fingerprint=self._fingerprint(target),
                )
            ),
            generation_profile_reference=(
                load_generation_profile_reference()
                if generation_profile is None
                else SysMLGenerationProfileReference(
                    profile_id=generation["profile_id"],
                    profile_version=generation["profile_version"],
                    profile_fingerprint=self._fingerprint(generation),
                )
            ),
            artifact_structure_reference=(
                load_artifact_structure_reference()
                if artifact_structure is None
                else SysMLArtifactStructureReference(
                    profile_id=structure_profile["profile_id"],
                    profile_version=structure_profile["profile_version"],
                    profile_fingerprint=self._fingerprint(structure_profile),
                )
            ),
            findings=ordered,
        )

    def require_ready(
        self,
        snapshot: InternalEngineeringModelSnapshot,
        **kwargs,
    ) -> SysMLGenerationPreflightResult:
        result = self.evaluate(snapshot, **kwargs)
        if not result.ready:
            error = SysMLGenerationBlockedError(
                "Phase-J generation preflight is blocked by "
                f"{len(result.blocking_findings)} finding(s)."
            )
            error.findings = result.blocking_findings
            raise error
        return result

    @staticmethod
    def _fingerprint(payload: object) -> str:
        from .fingerprints import calculate_json_fingerprint
        return calculate_json_fingerprint(payload)

    def _check_profile_references(
        self,
        snapshot,
        target,
        generation,
        artifact_structure,
        findings,
    ) -> None:
        if (
            generation["target_notation_context_id"] != target["context_id"]
            or generation["target_notation_version"] != target["version"]
        ):
            findings.append(
                self._finding(
                    "PROFILE_REFERENCE_MISMATCH",
                    "Generation Profile does not reference the selected "
                    "Target Notation context/version.",
                    target_type="generation_profile",
                    target_id=generation["profile_id"],
                )
            )

        framework_ref = snapshot.structure.framework_template_reference
        expected_template = (
            generation["framework_template_id"],
            generation["framework_template_version"],
        )
        actual_template = (
            framework_ref.template_id,
            framework_ref.template_version,
        )
        if actual_template != expected_template:
            findings.append(
                self._finding(
                    "PROFILE_REFERENCE_MISMATCH",
                    "IEM Framework Template does not match Generation Profile.",
                    target_type="internal_engineering_model",
                    target_id=snapshot.manifest.internal_engineering_model_id,
                )
            )

        artifact_template = (
            artifact_structure["framework_template_id"],
            artifact_structure["framework_template_version"],
        )
        if actual_template != artifact_template:
            findings.append(
                self._finding(
                    "PROFILE_REFERENCE_MISMATCH",
                    "IEM Framework Template does not match Artifact Structure "
                    "Profile.",
                    target_type="internal_engineering_model",
                    target_id=snapshot.manifest.internal_engineering_model_id,
                )
            )

    def _check_structure_projection(
        self,
        snapshot,
        artifact_structure,
        findings,
    ) -> dict[str, str]:
        mappings = {
            item["framework_node_id"]: item
            for item in artifact_structure["framework_package_mappings"]
        }
        snapshot_nodes = {
            item.framework_node_id: item
            for item in snapshot.structure.nodes
        }

        for node_id, node in snapshot_nodes.items():
            mapping = mappings.get(node_id)
            if mapping is None:
                findings.append(
                    self._finding(
                        "STRUCTURE_PROJECTION_ERROR",
                        "No package projection exists for Framework node.",
                        target_type="framework_node",
                        target_id=node_id,
                    )
                )
                continue
            mismatches = []
            if mapping["mapping_key"] != node.mapping_key:
                mismatches.append("mapping_key")
            if (
                mapping["parent_framework_node_id"]
                != node.parent_framework_node_id
            ):
                mismatches.append("parent_framework_node_id")
            if mapping["order"] != node.order:
                mismatches.append("order")
            if mismatches:
                findings.append(
                    self._finding(
                        "STRUCTURE_PROJECTION_ERROR",
                        "Artifact Structure disagrees with materialized IEM "
                        f"Framework node fields: {', '.join(mismatches)}.",
                        target_type="framework_node",
                        target_id=node_id,
                    )
                )

        extra = sorted(set(mappings) - set(snapshot_nodes))
        for node_id in extra:
            findings.append(
                self._finding(
                    "STRUCTURE_PROJECTION_ERROR",
                    "Artifact Structure contains a Framework node that is absent "
                    "from the materialized IEM structure.",
                    target_type="framework_node",
                    target_id=node_id,
                )
            )

        element_membership: dict[str, list[str]] = {}
        for node in snapshot.structure.nodes:
            for element_id in node.internal_model_element_ids:
                element_membership.setdefault(element_id, []).append(
                    node.framework_node_id
                )

        flattened: dict[str, str] = {}
        for element in snapshot.elements:
            memberships = element_membership.get(
                element.internal_model_element_id,
                [],
            )
            if len(memberships) != 1:
                findings.append(
                    self._finding(
                        "STRUCTURE_PROJECTION_ERROR",
                        "Each IEM element must belong to exactly one materialized "
                        "Framework node for package projection.",
                        target_type="internal_model_element",
                        target_id=element.internal_model_element_id,
                    )
                )
                continue
            flattened[element.internal_model_element_id] = memberships[0]
        return flattened

    def _check_elements(
        self,
        snapshot,
        generation,
        allowed_constructs,
        package_membership,
        findings,
    ) -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
        symbols: dict[str, str] = {}
        element_kinds: dict[str, str] = {}
        element_constructs: dict[str, str] = {}
        symbol_owner: dict[str, str] = {}

        node_by_id = {
            node.framework_node_id: node
            for node in snapshot.structure.nodes
        }

        for element in snapshot.elements:
            element_id = element.internal_model_element_id
            try:
                symbol = generated_element_symbol(element_id)
            except Exception:
                findings.append(
                    self._finding(
                        "UNRENDERABLE_IDENTIFIER",
                        "IEM element identity cannot be converted to the "
                        "configured generated symbol subset.",
                        target_type="internal_model_element",
                        target_id=element_id,
                    )
                )
                continue
            previous = symbol_owner.get(symbol)
            if previous is not None and previous != element_id:
                findings.append(
                    self._finding(
                        "DUPLICATE_GENERATED_SYMBOL",
                        f"Generated symbol {symbol!r} is already owned by "
                        f"{previous}.",
                        target_type="internal_model_element",
                        target_id=element_id,
                    )
                )
            symbol_owner[symbol] = element_id
            symbols[element_id] = symbol

            membership_node_id = package_membership.get(element_id)
            if membership_node_id is not None:
                node = node_by_id[membership_node_id]
                if node.mapping_key != element.model_area:
                    findings.append(
                        self._finding(
                            "STRUCTURE_PROJECTION_ERROR",
                            "IEM element model_area disagrees with its "
                            "materialized Framework package membership.",
                            target_type="internal_model_element",
                            target_id=element_id,
                        )
                    )
                if element.framework_assignment != membership_node_id:
                    findings.append(
                        self._finding(
                            "STRUCTURE_PROJECTION_ERROR",
                            "IEM element framework_assignment disagrees with "
                            "materialized Framework package membership.",
                            target_type="internal_model_element",
                            target_id=element_id,
                        )
                    )

            mapping = find_element_mapping(
                generation,
                model_area=element.model_area,
                element_type=element.element_type,
            )
            if mapping is None or mapping["mapping_status"] != "supported":
                findings.append(
                    self._finding(
                        "UNSUPPORTED_ELEMENT_MAPPING",
                        "No production-authorized SysML mapping exists for "
                        f"{element.model_area}/{element.element_type}.",
                        target_type="internal_model_element",
                        target_id=element_id,
                        profile_rule_id=(
                            None if mapping is None else mapping["rule_id"]
                        ),
                    )
                )
                continue

            construct_id = mapping["target_construct_id"]
            if construct_id not in allowed_constructs:
                findings.append(
                    self._finding(
                        "TARGET_CONSTRUCT_NOT_ALLOWED",
                        f"Generation rule requires non-allowed target construct "
                        f"{construct_id}.",
                        target_type="internal_model_element",
                        target_id=element_id,
                        profile_rule_id=mapping["rule_id"],
                    )
                )
            else:
                element_kinds[element_id] = mapping["target_element_kind"]
                element_constructs[element_id] = construct_id

        return symbols, element_kinds, element_constructs

    def _check_relationships(
        self,
        snapshot,
        generation,
        allowed_constructs,
        generated_symbols,
        element_kinds,
        element_constructs,
        findings,
    ) -> None:
        element_ids = {item.internal_model_element_id for item in snapshot.elements}
        relationship_symbols: dict[str, str] = {}

        for relation in snapshot.relationships:
            relation_id = relation.internal_model_relationship_id
            try:
                trace_symbol = generated_relationship_symbol(relation_id)
            except Exception:
                findings.append(
                    self._finding(
                        "UNRENDERABLE_IDENTIFIER",
                        "IEM relationship identity cannot be converted to the "
                        "configured generated trace symbol subset.",
                        target_type="internal_model_relationship",
                        target_id=relation_id,
                    )
                )
                trace_symbol = None
            if trace_symbol is not None:
                previous = relationship_symbols.get(trace_symbol)
                if previous is not None and previous != relation_id:
                    findings.append(
                        self._finding(
                            "DUPLICATE_GENERATED_SYMBOL",
                            f"Generated relationship trace symbol {trace_symbol!r} "
                            f"is already owned by {previous}.",
                            target_type="internal_model_relationship",
                            target_id=relation_id,
                        )
                    )
                relationship_symbols[trace_symbol] = relation_id

            endpoints_renderable = True
            for endpoint_label, endpoint_id in (
                ("source", relation.source_internal_model_element_id),
                ("target", relation.target_internal_model_element_id),
            ):
                if endpoint_id not in element_ids or endpoint_id not in generated_symbols:
                    endpoints_renderable = False
                    findings.append(
                        self._finding(
                            "UNRESOLVED_GENERATED_ENDPOINT",
                            f"Relationship {endpoint_label} endpoint "
                            f"{endpoint_id!r} has no renderable generated element.",
                            target_type="internal_model_relationship",
                            target_id=relation_id,
                        )
                    )

            mapping = find_relationship_mapping(
                generation,
                relationship_family=relation.relationship_family,
                semantic_intent=relation.semantic_intent,
                directionality=relation.directionality,
            )
            if mapping is None or mapping["mapping_status"] != "supported":
                findings.append(
                    self._finding(
                        "UNSUPPORTED_RELATIONSHIP_MAPPING",
                        "No production-authorized SysML relationship mapping "
                        "exists for exact IEM relationship semantics "
                        f"({relation.relationship_family}, "
                        f"{relation.semantic_intent}, "
                        f"{relation.directionality}).",
                        target_type="internal_model_relationship",
                        target_id=relation_id,
                        profile_rule_id=(
                            None if mapping is None else mapping["rule_id"]
                        ),
                    )
                )
                continue

            construct_id = mapping["target_construct_id"]
            if construct_id not in allowed_constructs:
                findings.append(
                    self._finding(
                        "TARGET_CONSTRUCT_NOT_ALLOWED",
                        f"Relationship generation rule requires non-allowed "
                        f"target construct {construct_id}.",
                        target_type="internal_model_relationship",
                        target_id=relation_id,
                        profile_rule_id=mapping["rule_id"],
                    )
                )
                continue

            if endpoints_renderable:
                self._check_endpoint_kind(
                    relation_id,
                    relation.source_internal_model_element_id,
                    "source",
                    element_kinds,
                    mapping["source_endpoint_kinds"],
                    mapping["rule_id"],
                    findings,
                )
                self._check_endpoint_kind(
                    relation_id,
                    relation.target_internal_model_element_id,
                    "target",
                    element_kinds,
                    mapping["target_endpoint_kinds"],
                    mapping["rule_id"],
                    findings,
                )
                self._check_endpoint_construct(
                    relation_id,
                    relation.source_internal_model_element_id,
                    "source",
                    element_constructs,
                    mapping["source_endpoint_construct_ids"],
                    mapping["rule_id"],
                    findings,
                )
                self._check_endpoint_construct(
                    relation_id,
                    relation.target_internal_model_element_id,
                    "target",
                    element_constructs,
                    mapping["target_endpoint_construct_ids"],
                    mapping["rule_id"],
                    findings,
                )

    def _check_endpoint_kind(
        self,
        relation_id: str,
        endpoint_id: str,
        endpoint_label: str,
        element_kinds: dict[str, str],
        allowed_kinds: list[str],
        rule_id: str,
        findings: list[SysMLGenerationFinding],
    ) -> None:
        actual_kind = element_kinds.get(endpoint_id)
        if actual_kind is None:
            return
        if actual_kind not in allowed_kinds:
            findings.append(
                self._finding(
                    "RELATIONSHIP_ENDPOINT_KIND_MISMATCH",
                    f"Relationship {endpoint_label} endpoint {endpoint_id} "
                    f"renders as {actual_kind!r}, but generation rule {rule_id} "
                    f"allows {allowed_kinds!r}.",
                    target_type="internal_model_relationship",
                    target_id=relation_id,
                    profile_rule_id=rule_id,
                )
            )

    def _check_endpoint_construct(
        self,
        relation_id: str,
        endpoint_id: str,
        endpoint_label: str,
        element_constructs: dict[str, str],
        allowed_constructs: list[str],
        rule_id: str,
        findings: list[SysMLGenerationFinding],
    ) -> None:
        actual_construct = element_constructs.get(endpoint_id)
        if actual_construct is None:
            return
        if actual_construct not in allowed_constructs:
            findings.append(
                self._finding(
                    "RELATIONSHIP_ENDPOINT_CONSTRUCT_MISMATCH",
                    f"Relationship {endpoint_label} endpoint {endpoint_id} "
                    f"renders as {actual_construct!r}, but generation rule "
                    f"{rule_id} allows {allowed_constructs!r}.",
                    target_type="internal_model_relationship",
                    target_id=relation_id,
                    profile_rule_id=rule_id,
                )
            )

    @staticmethod
    def _finding(
        code: str,
        message: str,
        *,
        target_type: str | None = None,
        target_id: str | None = None,
        profile_rule_id: str | None = None,
    ) -> SysMLGenerationFinding:
        return SysMLGenerationFinding(
            code=code,
            message=message,
            issue_level="error",
            blocking=True,
            target_type=target_type,
            target_id=target_id,
            profile_rule_id=profile_rule_id,
        )
