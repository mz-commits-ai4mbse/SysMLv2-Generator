"""J6 deterministic assembly of validation-ready GeneratedSysMLArtifactSet."""

from __future__ import annotations

from dataclasses import asdict, replace

from modules.internal_model.types import InternalEngineeringModelSnapshot

from .element_renderer import SysMLElementRenderer
from .errors import SysMLGenerationIntegrityError
from .fingerprints import (
    calculate_json_fingerprint,
    calculate_text_fingerprint,
    validate_sha256_fingerprint,
)
from .generator_rules import load_generator_rules, load_generator_rules_reference
from .projection import SysMLProjectionPlanService
from .projection_types import (
    SysMLElementProjection,
    SysMLPackageProjection,
    SysMLProjectionPlan,
)
from .relationship_renderer import SysMLRelationshipRenderer
from .types import (
    GeneratedSysMLArtifactSet,
    GeneratedSysMLLocation,
    GeneratedSysMLTraceabilityEntry,
    GeneratedSysMLUnit,
    SysMLGenerationContext,
    SysMLGenerationProvenance,
)


GENERATED_SYSML_ARTIFACT_SET_SCHEMA_VERSION = "1.0.0"
GENERATOR_IMPLEMENTATION_REFERENCE = (
    "modules.sysml_generation.artifact_builder:SysMLArtifactSetBuilder"
)


class _UnitComposer:
    def __init__(self) -> None:
        self.lines: list[str] = []
        self.locations: dict[tuple[str, str], GeneratedSysMLLocation] = {}

    @property
    def next_line(self) -> int:
        return len(self.lines) + 1

    def append_line(self, text: str) -> None:
        self.lines.append(text)

    def append_fragment(
        self,
        *,
        target_type: str,
        target_id: str,
        fragment: str,
        indent_level: int,
    ) -> None:
        prefix = "    " * indent_level
        start = self.next_line
        for line in fragment.split("\n"):
            self.append_line(prefix + line)
        self.locations[(target_type, target_id)] = GeneratedSysMLLocation(
            start_line=start,
            end_line=len(self.lines),
        )

    def content(self) -> str:
        return "\n".join(self.lines) + "\n"


class SysMLArtifactSetBuilder:
    """Build one deterministic validation-ready Phase-J artifact set."""

    def build(
        self,
        snapshot: InternalEngineeringModelSnapshot,
    ) -> GeneratedSysMLArtifactSet:
        source_iem_fingerprint = validate_sha256_fingerprint(
            snapshot.manifest.content_fingerprint,
            label="source IEM content fingerprint",
        )
        plan = SysMLProjectionPlanService().build(snapshot)
        rules = load_generator_rules()
        generator_rules_reference = load_generator_rules_reference()

        generation_context = SysMLGenerationContext(
            target_notation_reference=plan.target_notation_reference,
            generation_profile_reference=plan.generation_profile_reference,
            artifact_structure_reference=plan.artifact_structure_reference,
            generator_rules_reference=generator_rules_reference,
        )
        context_fingerprint = calculate_json_fingerprint(asdict(generation_context))
        generation_input_fingerprint = calculate_generation_input_fingerprint(
            source_iem_content_fingerprint=source_iem_fingerprint,
            generation_context=generation_context,
        )

        unit_content, locations = self._assemble_unit(
            plan=plan,
            qualification_separator=rules["relationship_placement"][
                "qualification_separator"
            ],
        )
        unit_fingerprint = calculate_text_fingerprint(unit_content)

        element_ids = tuple(item.internal_model_element_id for item in plan.elements)
        relationship_ids = tuple(
            item.internal_model_relationship_id for item in plan.relationships
        )
        generated_symbols = tuple(
            [item.generated_symbol for item in plan.elements]
            + [item.generated_trace_symbol for item in plan.relationships]
        )

        unit = GeneratedSysMLUnit(
            unit_id=plan.generated_unit_id,
            relative_path=plan.relative_path,
            content=unit_content,
            content_fingerprint=unit_fingerprint,
            generated_symbol_ids=generated_symbols,
            source_internal_model_element_ids=element_ids,
            source_internal_model_relationship_ids=relationship_ids,
        )

        traceability = self._build_traceability(
            snapshot=snapshot,
            plan=plan,
            locations=locations,
        )
        provenance = SysMLGenerationProvenance(
            method="deterministic_serialization",
            implementation_reference=GENERATOR_IMPLEMENTATION_REFERENCE,
            context_fingerprint=context_fingerprint,
        )

        payload = {
            "schema_version": GENERATED_SYSML_ARTIFACT_SET_SCHEMA_VERSION,
            "project_id": snapshot.manifest.project_id,
            "source_internal_engineering_model_id": (
                snapshot.manifest.internal_engineering_model_id
            ),
            "source_iem_content_fingerprint": source_iem_fingerprint,
            "generation_context": asdict(generation_context),
            "generation_input_fingerprint": generation_input_fingerprint,
            "generation_provenance": asdict(provenance),
            "units": [asdict(unit)],
            "traceability_entries": [asdict(item) for item in traceability],
            "nonblocking_diagnostics": [],
        }
        content_fingerprint = calculate_json_fingerprint(payload)

        artifact_set = GeneratedSysMLArtifactSet(
            schema_version=GENERATED_SYSML_ARTIFACT_SET_SCHEMA_VERSION,
            project_id=snapshot.manifest.project_id,
            source_internal_engineering_model_id=(
                snapshot.manifest.internal_engineering_model_id
            ),
            source_iem_content_fingerprint=source_iem_fingerprint,
            generation_context=generation_context,
            generation_input_fingerprint=generation_input_fingerprint,
            generation_provenance=provenance,
            units=(unit,),
            traceability_entries=traceability,
            nonblocking_diagnostics=(),
            content_fingerprint=content_fingerprint,
        )
        validate_generated_artifact_set_integrity(artifact_set, snapshot=snapshot)
        return artifact_set

    def _assemble_unit(
        self,
        *,
        plan: SysMLProjectionPlan,
        qualification_separator: str,
    ) -> tuple[str, dict[tuple[str, str], GeneratedSysMLLocation]]:
        composer = _UnitComposer()
        element_renderer = SysMLElementRenderer()
        relationship_renderer = SysMLRelationshipRenderer()

        packages_by_parent: dict[str | None, list[SysMLPackageProjection]] = {}
        for package in plan.packages:
            packages_by_parent.setdefault(package.parent_framework_node_id, []).append(
                package
            )
        elements_by_node: dict[str, list[SysMLElementProjection]] = {}
        for element in plan.elements:
            elements_by_node.setdefault(element.framework_node_id, []).append(element)
        package_by_node = {item.framework_node_id: item for item in plan.packages}

        composer.append_line(f"package {plan.root_package_name} {{")

        def emit_package(package: SysMLPackageProjection, *, indent_level: int) -> None:
            prefix = "    " * indent_level
            composer.append_line(f"{prefix}package {package.package_name} {{")

            for element in elements_by_node.get(package.framework_node_id, ()):
                rendered = element_renderer.render(element)
                composer.append_fragment(
                    target_type="element",
                    target_id=element.internal_model_element_id,
                    fragment=rendered.content,
                    indent_level=indent_level + 1,
                )

            for child in packages_by_parent.get(package.framework_node_id, ()):
                emit_package(child, indent_level=indent_level + 1)

            composer.append_line(f"{prefix}}}")

        for top_level in packages_by_parent.get(None, ()):
            emit_package(top_level, indent_level=1)

        if plan.relationships:
            composer.append_line("")

        qualified_symbols = {
            element.internal_model_element_id: self._qualified_symbol(
                element=element,
                package_by_node=package_by_node,
                separator=qualification_separator,
            )
            for element in plan.elements
        }

        for relationship in plan.relationships:
            qualified_projection = replace(
                relationship,
                source_generated_symbol=qualified_symbols[
                    relationship.source_internal_model_element_id
                ],
                target_generated_symbol=qualified_symbols[
                    relationship.target_internal_model_element_id
                ],
            )
            rendered = relationship_renderer.render(qualified_projection)
            composer.append_fragment(
                target_type="relationship",
                target_id=relationship.internal_model_relationship_id,
                fragment=rendered.content,
                indent_level=1,
            )

        composer.append_line("}")
        return composer.content(), composer.locations

    @staticmethod
    def _qualified_symbol(
        *,
        element: SysMLElementProjection,
        package_by_node: dict[str, SysMLPackageProjection],
        separator: str,
    ) -> str:
        path: list[str] = [element.generated_symbol]
        node_id: str | None = element.framework_node_id
        while node_id is not None:
            package = package_by_node[node_id]
            path.append(package.package_name)
            node_id = package.parent_framework_node_id
        path.reverse()
        return separator.join(path)

    @staticmethod
    def _build_traceability(
        *,
        snapshot: InternalEngineeringModelSnapshot,
        plan: SysMLProjectionPlan,
        locations: dict[tuple[str, str], GeneratedSysMLLocation],
    ) -> tuple[GeneratedSysMLTraceabilityEntry, ...]:
        element_source = {
            item.internal_model_element_id: item for item in snapshot.elements
        }
        relationship_source = {
            item.internal_model_relationship_id: item
            for item in snapshot.relationships
        }

        result: list[GeneratedSysMLTraceabilityEntry] = []
        for projected in plan.elements:
            source = element_source[projected.internal_model_element_id]
            result.append(
                GeneratedSysMLTraceabilityEntry(
                    generated_unit_id=plan.generated_unit_id,
                    generated_symbol_id=projected.generated_symbol,
                    generated_location=locations[
                        ("element", projected.internal_model_element_id)
                    ],
                    source_internal_engineering_model_id=(
                        snapshot.manifest.internal_engineering_model_id
                    ),
                    source_internal_model_element_id=(
                        projected.internal_model_element_id
                    ),
                    source_internal_model_relationship_id=None,
                    source_model_candidate_id=(
                        source.source_model_element_candidate_id
                    ),
                    approved_input_references=source.approved_input_references,
                    review_decision_reference=source.review_decision_reference,
                    accepted_exception_reference=(
                        source.accepted_exception_reference
                    ),
                )
            )

        for projected in plan.relationships:
            source = relationship_source[projected.internal_model_relationship_id]
            result.append(
                GeneratedSysMLTraceabilityEntry(
                    generated_unit_id=plan.generated_unit_id,
                    generated_symbol_id=projected.generated_trace_symbol,
                    generated_location=locations[
                        ("relationship", projected.internal_model_relationship_id)
                    ],
                    source_internal_engineering_model_id=(
                        snapshot.manifest.internal_engineering_model_id
                    ),
                    source_internal_model_element_id=None,
                    source_internal_model_relationship_id=(
                        projected.internal_model_relationship_id
                    ),
                    source_model_candidate_id=(
                        source.source_model_relationship_candidate_id
                    ),
                    approved_input_references=source.approved_input_references,
                    review_decision_reference=source.review_decision_reference,
                    accepted_exception_reference=(
                        source.accepted_exception_reference
                    ),
                )
            )
        return tuple(result)


def calculate_generation_input_fingerprint(
    *,
    source_iem_content_fingerprint: str,
    generation_context: SysMLGenerationContext,
) -> str:
    validate_sha256_fingerprint(
        source_iem_content_fingerprint,
        label="source IEM content fingerprint",
    )
    return calculate_json_fingerprint(
        {
            "source_iem_content_fingerprint": source_iem_content_fingerprint,
            "target_notation_reference": asdict(
                generation_context.target_notation_reference
            ),
            "generation_profile_reference": asdict(
                generation_context.generation_profile_reference
            ),
            "artifact_structure_reference": asdict(
                generation_context.artifact_structure_reference
            ),
            "generator_rules_reference": asdict(
                generation_context.generator_rules_reference
            ),
        }
    )


def validate_generated_artifact_set_integrity(
    artifact_set: GeneratedSysMLArtifactSet,
    *,
    snapshot: InternalEngineeringModelSnapshot,
) -> None:
    if len(artifact_set.units) != 1:
        raise SysMLGenerationIntegrityError(
            "J6 MVP artifact set must contain exactly one generated unit."
        )
    unit = artifact_set.units[0]
    if calculate_text_fingerprint(unit.content) != unit.content_fingerprint:
        raise SysMLGenerationIntegrityError(
            "Generated unit content fingerprint mismatch."
        )
    if not unit.content.endswith("\n"):
        raise SysMLGenerationIntegrityError(
            "Generated unit must end with controlled LF output."
        )

    expected_ime = {
        item.internal_model_element_id for item in snapshot.elements
    }
    expected_imr = {
        item.internal_model_relationship_id for item in snapshot.relationships
    }
    if set(unit.source_internal_model_element_ids) != expected_ime:
        raise SysMLGenerationIntegrityError(
            "Generated unit does not cover every source IME."
        )
    if set(unit.source_internal_model_relationship_ids) != expected_imr:
        raise SysMLGenerationIntegrityError(
            "Generated unit does not cover every source IMR."
        )

    element_trace_ids = [
        item.source_internal_model_element_id
        for item in artifact_set.traceability_entries
        if item.source_internal_model_element_id is not None
    ]
    relationship_trace_ids = [
        item.source_internal_model_relationship_id
        for item in artifact_set.traceability_entries
        if item.source_internal_model_relationship_id is not None
    ]
    if len(element_trace_ids) != len(set(element_trace_ids)):
        raise SysMLGenerationIntegrityError(
            "Duplicate element traceability entries detected."
        )
    if len(relationship_trace_ids) != len(set(relationship_trace_ids)):
        raise SysMLGenerationIntegrityError(
            "Duplicate relationship traceability entries detected."
        )
    if set(element_trace_ids) != expected_ime:
        raise SysMLGenerationIntegrityError(
            "Traceability does not cover every source IME exactly once."
        )
    if set(relationship_trace_ids) != expected_imr:
        raise SysMLGenerationIntegrityError(
            "Traceability does not cover every source IMR exactly once."
        )

    line_count = len(unit.content.splitlines())
    for entry in artifact_set.traceability_entries:
        location = entry.generated_location
        if location is None:
            raise SysMLGenerationIntegrityError(
                "Every generated source artifact requires a line location."
            )
        if (
            location.start_line < 1
            or location.end_line < location.start_line
            or location.end_line > line_count
        ):
            raise SysMLGenerationIntegrityError(
                "Traceability line location is outside generated unit content."
            )

    expected_input = calculate_generation_input_fingerprint(
        source_iem_content_fingerprint=artifact_set.source_iem_content_fingerprint,
        generation_context=artifact_set.generation_context,
    )
    if expected_input != artifact_set.generation_input_fingerprint:
        raise SysMLGenerationIntegrityError(
            "generation_input_fingerprint mismatch."
        )

    recomputed = calculate_json_fingerprint(
        {
            "schema_version": artifact_set.schema_version,
            "project_id": artifact_set.project_id,
            "source_internal_engineering_model_id": (
                artifact_set.source_internal_engineering_model_id
            ),
            "source_iem_content_fingerprint": (
                artifact_set.source_iem_content_fingerprint
            ),
            "generation_context": asdict(artifact_set.generation_context),
            "generation_input_fingerprint": (
                artifact_set.generation_input_fingerprint
            ),
            "generation_provenance": asdict(
                artifact_set.generation_provenance
            ),
            "units": [asdict(item) for item in artifact_set.units],
            "traceability_entries": [
                asdict(item) for item in artifact_set.traceability_entries
            ],
            "nonblocking_diagnostics": [
                asdict(item)
                for item in artifact_set.nonblocking_diagnostics
            ],
        }
    )
    if recomputed != artifact_set.content_fingerprint:
        raise SysMLGenerationIntegrityError(
            "GeneratedSysMLArtifactSet content fingerprint mismatch."
        )
