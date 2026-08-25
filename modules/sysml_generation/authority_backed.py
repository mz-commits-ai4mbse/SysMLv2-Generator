"""Authority-backed SysML v2 generation from Internal Model v2.

The generator reuses the validated Phase-J projection and rendering policy,
but carries Human authority references instead of legacy Candidate Review
references.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import uuid

from modules.project_workspace.types import FrameworkTemplateReference
from modules.sysml_generation.artifact_structure import (
    load_artifact_structure_profile,
)
from modules.sysml_generation.element_renderer import SysMLElementRenderer
from modules.sysml_generation.errors import SysMLGenerationBlockedError
from modules.sysml_generation.fingerprints import (
    calculate_json_fingerprint,
    calculate_text_fingerprint,
)
from modules.sysml_generation.generator_rules import (
    load_generator_rules,
    load_generator_rules_reference,
)
from modules.sysml_generation.projection import SysMLProjectionPlanService
from modules.sysml_generation.relationship_renderer import (
    SysMLRelationshipRenderer,
)
from modules.sysml_generation.types import (
    GeneratedSysMLLocation,
    GeneratedSysMLUnit,
    SysMLGenerationContext,
    SysMLGenerationProvenance,
)


AUTHORITY_BACKED_SYSML_ARTIFACT_SCHEMA_VERSION = "2.0.0"
AUTHORITY_BACKED_GENERATOR_IMPLEMENTATION_REFERENCE = (
    "modules.sysml_generation.authority_backed:"
    "AuthorityBackedSysMLArtifactBuilder"
)


@dataclass(frozen=True, slots=True)
class AuthorityBackedSysMLTraceabilityEntry:
    generated_unit_id: str
    generated_symbol_id: str
    generated_location: GeneratedSysMLLocation
    source_internal_engineering_model_id: str
    source_internal_model_element_id: str | None
    source_internal_model_relationship_id: str | None
    approved_input_id: str | None
    authority_references: tuple[object, ...]


@dataclass(frozen=True, slots=True)
class AuthorityBackedGeneratedSysMLArtifactSet:
    schema_version: str
    project_id: str
    source_internal_engineering_model_id: str
    source_iem_content_fingerprint: str
    generation_context: SysMLGenerationContext
    generation_input_fingerprint: str
    generation_provenance: SysMLGenerationProvenance
    units: tuple[GeneratedSysMLUnit, ...]
    traceability_entries: tuple[
        AuthorityBackedSysMLTraceabilityEntry, ...
    ]
    content_fingerprint: str


@dataclass(frozen=True, slots=True)
class _ManifestView:
    project_id: str
    internal_engineering_model_id: str
    content_fingerprint: str


@dataclass(frozen=True, slots=True)
class _StructureView:
    framework_template_reference: FrameworkTemplateReference
    nodes: tuple[object, ...]


@dataclass(frozen=True, slots=True)
class _GenerationSnapshotView:
    manifest: _ManifestView
    structure: _StructureView
    elements: tuple[object, ...]
    relationships: tuple[object, ...]


class _UnitComposer:
    def __init__(self):
        self.lines = []
        self.locations = {}

    @property
    def next_line(self):
        return len(self.lines) + 1

    def append_line(self, text):
        self.lines.append(text)

    def append_fragment(
        self,
        *,
        target_type,
        target_id,
        fragment,
        indent_level,
    ):
        prefix = "    " * indent_level
        start = self.next_line
        for line in fragment.split("\n"):
            self.append_line(prefix + line)
        self.locations[(target_type, target_id)] = GeneratedSysMLLocation(
            start_line=start,
            end_line=len(self.lines),
        )

    def content(self):
        return "\n".join(self.lines) + "\n"


class AuthorityBackedSysMLArtifactBuilder:
    """Generate SysML v2 without reintroducing Candidate Review authority."""

    def build(self, snapshot):
        view = _generation_view(snapshot)
        plan = SysMLProjectionPlanService().build(view)
        rules = load_generator_rules()
        generator_rules_reference = load_generator_rules_reference()

        generation_context = SysMLGenerationContext(
            target_notation_reference=plan.target_notation_reference,
            generation_profile_reference=plan.generation_profile_reference,
            artifact_structure_reference=plan.artifact_structure_reference,
            generator_rules_reference=generator_rules_reference,
        )
        context_fingerprint = calculate_json_fingerprint(
            asdict(generation_context)
        )
        generation_input_fingerprint = calculate_json_fingerprint(
            {
                "source_iem_content_fingerprint": (
                    snapshot.content_fingerprint
                ),
                "generation_context": asdict(generation_context),
            }
        )

        content, locations = self._assemble_unit(
            plan,
            qualification_separator=rules[
                "relationship_placement"
            ]["qualification_separator"],
        )
        unit = GeneratedSysMLUnit(
            unit_id=plan.generated_unit_id,
            relative_path=plan.relative_path,
            content=content,
            content_fingerprint=calculate_text_fingerprint(content),
            generated_symbol_ids=tuple(
                [item.generated_symbol for item in plan.elements]
                + [
                    item.generated_trace_symbol
                    for item in plan.relationships
                ]
            ),
            source_internal_model_element_ids=tuple(
                item.internal_model_element_id
                for item in plan.elements
            ),
            source_internal_model_relationship_ids=tuple(
                item.internal_model_relationship_id
                for item in plan.relationships
            ),
        )
        traceability = self._traceability(
            snapshot=snapshot,
            plan=plan,
            locations=locations,
        )
        provenance = SysMLGenerationProvenance(
            method="deterministic_authority_backed_serialization",
            implementation_reference=(
                AUTHORITY_BACKED_GENERATOR_IMPLEMENTATION_REFERENCE
            ),
            context_fingerprint=context_fingerprint,
        )
        body = {
            "schema_version": AUTHORITY_BACKED_SYSML_ARTIFACT_SCHEMA_VERSION,
            "project_id": snapshot.project_id,
            "source_internal_engineering_model_id": (
                snapshot.internal_engineering_model_id
            ),
            "source_iem_content_fingerprint": (
                snapshot.content_fingerprint
            ),
            "generation_context": asdict(generation_context),
            "generation_input_fingerprint": (
                generation_input_fingerprint
            ),
            "generation_provenance": asdict(provenance),
            "units": [asdict(unit)],
            "traceability_entries": [
                _trace_payload(item)
                for item in traceability
            ],
        }
        artifact = AuthorityBackedGeneratedSysMLArtifactSet(
            schema_version=AUTHORITY_BACKED_SYSML_ARTIFACT_SCHEMA_VERSION,
            project_id=snapshot.project_id,
            source_internal_engineering_model_id=(
                snapshot.internal_engineering_model_id
            ),
            source_iem_content_fingerprint=(
                snapshot.content_fingerprint
            ),
            generation_context=generation_context,
            generation_input_fingerprint=generation_input_fingerprint,
            generation_provenance=provenance,
            units=(unit,),
            traceability_entries=traceability,
            content_fingerprint=_fingerprint(body),
        )
        validate_authority_backed_artifact_set(
            artifact,
            snapshot=snapshot,
        )
        return artifact

    def _assemble_unit(self, plan, *, qualification_separator):
        composer = _UnitComposer()
        element_renderer = SysMLElementRenderer()
        relationship_renderer = SysMLRelationshipRenderer()

        packages_by_parent = {}
        for package in plan.packages:
            packages_by_parent.setdefault(
                package.parent_framework_node_id,
                [],
            ).append(package)
        elements_by_node = {}
        for element in plan.elements:
            elements_by_node.setdefault(
                element.framework_node_id,
                [],
            ).append(element)
        package_by_node = {
            item.framework_node_id: item
            for item in plan.packages
        }

        composer.append_line(f"package {plan.root_package_name} {{")

        def emit_package(package, *, indent_level):
            prefix = "    " * indent_level
            composer.append_line(
                f"{prefix}package {package.package_name} {{"
            )
            for element in elements_by_node.get(
                package.framework_node_id,
                (),
            ):
                rendered = element_renderer.render(element)
                composer.append_fragment(
                    target_type="element",
                    target_id=element.internal_model_element_id,
                    fragment=rendered.content,
                    indent_level=indent_level + 1,
                )
            for child in packages_by_parent.get(
                package.framework_node_id,
                (),
            ):
                emit_package(
                    child,
                    indent_level=indent_level + 1,
                )
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

        from dataclasses import replace

        for relationship in plan.relationships:
            qualified = replace(
                relationship,
                source_generated_symbol=qualified_symbols[
                    relationship.source_internal_model_element_id
                ],
                target_generated_symbol=qualified_symbols[
                    relationship.target_internal_model_element_id
                ],
            )
            rendered = relationship_renderer.render(qualified)
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
        element,
        package_by_node,
        separator,
    ):
        path = [element.generated_symbol]
        node_id = element.framework_node_id
        while node_id is not None:
            package = package_by_node[node_id]
            path.append(package.package_name)
            node_id = package.parent_framework_node_id
        path.reverse()
        return separator.join(path)

    @staticmethod
    def _traceability(*, snapshot, plan, locations):
        element_by_id = {
            item.internal_model_element_id: item
            for item in snapshot.elements
        }
        relationship_by_id = {
            item.internal_model_relationship_id: item
            for item in snapshot.relationships
        }
        result = []

        for projected in plan.elements:
            source = element_by_id[
                projected.internal_model_element_id
            ]
            result.append(
                AuthorityBackedSysMLTraceabilityEntry(
                    generated_unit_id=plan.generated_unit_id,
                    generated_symbol_id=projected.generated_symbol,
                    generated_location=locations[
                        (
                            "element",
                            projected.internal_model_element_id,
                        )
                    ],
                    source_internal_engineering_model_id=(
                        snapshot.internal_engineering_model_id
                    ),
                    source_internal_model_element_id=(
                        projected.internal_model_element_id
                    ),
                    source_internal_model_relationship_id=None,
                    approved_input_id=source.approved_input_id,
                    authority_references=(
                        source.placement_authority,
                    ),
                )
            )

        for projected in plan.relationships:
            source = relationship_by_id[
                projected.internal_model_relationship_id
            ]
            result.append(
                AuthorityBackedSysMLTraceabilityEntry(
                    generated_unit_id=plan.generated_unit_id,
                    generated_symbol_id=(
                        projected.generated_trace_symbol
                    ),
                    generated_location=locations[
                        (
                            "relationship",
                            projected.internal_model_relationship_id,
                        )
                    ],
                    source_internal_engineering_model_id=(
                        snapshot.internal_engineering_model_id
                    ),
                    source_internal_model_element_id=None,
                    source_internal_model_relationship_id=(
                        projected.internal_model_relationship_id
                    ),
                    approved_input_id=None,
                    authority_references=(
                        source.engineering_relationship_authority,
                        source.final_representation_authority,
                    ),
                )
            )
        return tuple(result)


class AuthorityBackedSysMLArtifactRepository:
    def __init__(self, root=Path("data/projects")):
        self.root = Path(root)

    def generate(self, snapshot):
        existing = self.load_if_available(
            snapshot.project_id,
            snapshot.internal_engineering_model_id,
        )
        if existing is not None:
            if (
                existing.source_iem_content_fingerprint
                != snapshot.content_fingerprint
            ):
                raise SysMLGenerationBlockedError(
                    "Existing authority-backed SysML artifact is stale."
                )
            return existing

        artifact = AuthorityBackedSysMLArtifactBuilder().build(snapshot)
        directory = (
            self.root
            / snapshot.project_id
            / "generated_sysml_v2"
            / snapshot.internal_engineering_model_id
        )
        directory.parent.mkdir(parents=True, exist_ok=True)
        if directory.exists() or directory.is_symlink():
            raise SysMLGenerationBlockedError(
                "Authority-backed SysML artifact path is occupied."
            )
        temp = directory.parent / (
            f".{snapshot.internal_engineering_model_id}."
            f"tmp-{uuid.uuid4().hex}"
        )
        temp.mkdir()
        (temp / "artifact_set.json").write_text(
            authority_backed_artifact_set_to_json(artifact),
            encoding="utf-8",
        )
        generated_dir = temp / "generated"
        generated_dir.mkdir()
        for unit in artifact.units:
            target = generated_dir.joinpath(
                *Path(unit.relative_path).parts
            )
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(unit.content, encoding="utf-8")
        temp.replace(directory)
        return self.load(
            snapshot.project_id,
            snapshot.internal_engineering_model_id,
        )

    def load_if_available(self, project_id, iem_id):
        path = (
            self.root
            / project_id
            / "generated_sysml_v2"
            / iem_id
            / "artifact_set.json"
        )
        if not path.exists():
            return None
        return self.load(project_id, iem_id)

    def load(self, project_id, iem_id):
        path = (
            self.root
            / project_id
            / "generated_sysml_v2"
            / iem_id
            / "artifact_set.json"
        )
        if path.is_symlink() or not path.is_file():
            raise SysMLGenerationBlockedError(
                "Authority-backed SysML artifact not found."
            )
        value = authority_backed_artifact_set_from_json(
            path.read_text(encoding="utf-8")
        )
        if (
            value.project_id != project_id
            or value.source_internal_engineering_model_id != iem_id
        ):
            raise SysMLGenerationBlockedError(
                "Authority-backed SysML artifact binding is invalid."
            )
        return value


def validate_authority_backed_artifact_set(artifact, *, snapshot):
    if artifact.schema_version != (
        AUTHORITY_BACKED_SYSML_ARTIFACT_SCHEMA_VERSION
    ):
        raise SysMLGenerationBlockedError(
            "Authority-backed SysML artifact schema is unsupported."
        )
    if (
        artifact.project_id != snapshot.project_id
        or artifact.source_internal_engineering_model_id
        != snapshot.internal_engineering_model_id
        or artifact.source_iem_content_fingerprint
        != snapshot.content_fingerprint
    ):
        raise SysMLGenerationBlockedError(
            "Authority-backed SysML artifact source binding is invalid."
        )
    if len(artifact.units) != 1:
        raise SysMLGenerationBlockedError(
            "Authority-backed SysML MVP requires exactly one unit."
        )

    unit = artifact.units[0]
    if calculate_text_fingerprint(
        unit.content
    ) != unit.content_fingerprint:
        raise SysMLGenerationBlockedError(
            "Generated SysML unit fingerprint mismatch."
        )
    expected_elements = {
        item.internal_model_element_id
        for item in snapshot.elements
    }
    expected_relationships = {
        item.internal_model_relationship_id
        for item in snapshot.relationships
    }
    if set(unit.source_internal_model_element_ids) != expected_elements:
        raise SysMLGenerationBlockedError(
            "Generated SysML does not cover every Internal Model element."
        )
    if (
        set(unit.source_internal_model_relationship_ids)
        != expected_relationships
    ):
        raise SysMLGenerationBlockedError(
            "Generated SysML does not cover every Internal Model relationship."
        )

    element_traces = {
        item.source_internal_model_element_id
        for item in artifact.traceability_entries
        if item.source_internal_model_element_id is not None
    }
    relationship_traces = {
        item.source_internal_model_relationship_id
        for item in artifact.traceability_entries
        if item.source_internal_model_relationship_id is not None
    }
    if element_traces != expected_elements:
        raise SysMLGenerationBlockedError(
            "Authority traceability does not cover every generated element."
        )
    if relationship_traces != expected_relationships:
        raise SysMLGenerationBlockedError(
            "Authority traceability does not cover every generated relationship."
        )

    body = _artifact_payload(
        artifact,
        include_fingerprint=False,
    )
    if _fingerprint(body) != artifact.content_fingerprint:
        raise SysMLGenerationBlockedError(
            "Authority-backed SysML artifact fingerprint mismatch."
        )


def authority_backed_artifact_set_to_json(value):
    return json.dumps(
        _artifact_payload(value, include_fingerprint=True),
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ) + "\n"


def authority_backed_artifact_set_from_json(text):
    from modules.internal_model.authority_backed import (
        InternalModelAuthorityReference,
    )
    from modules.sysml_generation.types import (
        SysMLArtifactStructureReference,
        SysMLGenerationProfileReference,
        SysMLGeneratorRulesReference,
        TargetNotationReference,
    )

    try:
        raw = json.loads(text)
        context_raw = raw["generation_context"]
        context = SysMLGenerationContext(
            target_notation_reference=TargetNotationReference(
                **context_raw["target_notation_reference"]
            ),
            generation_profile_reference=(
                SysMLGenerationProfileReference(
                    **context_raw["generation_profile_reference"]
                )
            ),
            artifact_structure_reference=(
                SysMLArtifactStructureReference(
                    **context_raw["artifact_structure_reference"]
                )
            ),
            generator_rules_reference=SysMLGeneratorRulesReference(
                **context_raw["generator_rules_reference"]
            ),
        )
        provenance = SysMLGenerationProvenance(
            **raw["generation_provenance"]
        )
        units = tuple(
            GeneratedSysMLUnit(
                **{
                    **item,
                    "generated_symbol_ids": tuple(
                        item["generated_symbol_ids"]
                    ),
                    "source_internal_model_element_ids": tuple(
                        item["source_internal_model_element_ids"]
                    ),
                    "source_internal_model_relationship_ids": tuple(
                        item[
                            "source_internal_model_relationship_ids"
                        ]
                    ),
                }
            )
            for item in raw["units"]
        )
        traces = []
        for item in raw["traceability_entries"]:
            location = GeneratedSysMLLocation(
                **item["generated_location"]
            )
            authorities = tuple(
                InternalModelAuthorityReference(**authority)
                for authority in item["authority_references"]
            )
            traces.append(
                AuthorityBackedSysMLTraceabilityEntry(
                    generated_unit_id=item["generated_unit_id"],
                    generated_symbol_id=item["generated_symbol_id"],
                    generated_location=location,
                    source_internal_engineering_model_id=item[
                        "source_internal_engineering_model_id"
                    ],
                    source_internal_model_element_id=item[
                        "source_internal_model_element_id"
                    ],
                    source_internal_model_relationship_id=item[
                        "source_internal_model_relationship_id"
                    ],
                    approved_input_id=item["approved_input_id"],
                    authority_references=authorities,
                )
            )
        return AuthorityBackedGeneratedSysMLArtifactSet(
            schema_version=raw["schema_version"],
            project_id=raw["project_id"],
            source_internal_engineering_model_id=raw[
                "source_internal_engineering_model_id"
            ],
            source_iem_content_fingerprint=raw[
                "source_iem_content_fingerprint"
            ],
            generation_context=context,
            generation_input_fingerprint=raw[
                "generation_input_fingerprint"
            ],
            generation_provenance=provenance,
            units=units,
            traceability_entries=tuple(traces),
            content_fingerprint=raw["content_fingerprint"],
        )
    except Exception as exc:
        raise SysMLGenerationBlockedError(
            "Authority-backed SysML artifact JSON violates the contract."
        ) from exc


def _generation_view(snapshot):
    return _GenerationSnapshotView(
        manifest=_ManifestView(
            project_id=snapshot.project_id,
            internal_engineering_model_id=(
                snapshot.internal_engineering_model_id
            ),
            content_fingerprint=snapshot.content_fingerprint,
        ),
        structure=_StructureView(
            framework_template_reference=FrameworkTemplateReference(
                template_id=snapshot.framework_template_id,
                template_version=snapshot.framework_template_version,
            ),
            nodes=snapshot.structure_nodes,
        ),
        elements=snapshot.elements,
        relationships=snapshot.relationships,
    )


def _trace_payload(item):
    return {
        "generated_unit_id": item.generated_unit_id,
        "generated_symbol_id": item.generated_symbol_id,
        "generated_location": asdict(item.generated_location),
        "source_internal_engineering_model_id": (
            item.source_internal_engineering_model_id
        ),
        "source_internal_model_element_id": (
            item.source_internal_model_element_id
        ),
        "source_internal_model_relationship_id": (
            item.source_internal_model_relationship_id
        ),
        "approved_input_id": item.approved_input_id,
        "authority_references": [
            asdict(authority)
            for authority in item.authority_references
        ],
    }


def _artifact_payload(value, *, include_fingerprint):
    payload = {
        "schema_version": value.schema_version,
        "project_id": value.project_id,
        "source_internal_engineering_model_id": (
            value.source_internal_engineering_model_id
        ),
        "source_iem_content_fingerprint": (
            value.source_iem_content_fingerprint
        ),
        "generation_context": asdict(value.generation_context),
        "generation_input_fingerprint": (
            value.generation_input_fingerprint
        ),
        "generation_provenance": asdict(
            value.generation_provenance
        ),
        "units": [asdict(item) for item in value.units],
        "traceability_entries": [
            _trace_payload(item)
            for item in value.traceability_entries
        ],
    }
    if include_fingerprint:
        payload["content_fingerprint"] = value.content_fingerprint
    return payload


def _fingerprint(payload):
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
