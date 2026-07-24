"""Generate the deterministic Reference Concept Index.

The generated index is derived and non-authoritative. Pinned local ontology
snapshots remain the auditable reference artifacts.
"""

from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlparse
from xml.etree import ElementTree

from modules.semantics.errors import (
    DuplicateReferenceConceptIriError,
    OntologyParseError,
    ReferenceConceptIndexError,
)
from modules.semantics.registry import (
    DEFAULT_ONTOLOGY_REGISTRY_PATH,
    load_ontology_registry,
    ontology_artifacts_for_index,
    verify_ontology_snapshots,
)
from modules.semantics.types import (
    LocalizedText,
    OntologyArtifact,
    OntologyReferenceSystem,
    OntologyRegistry,
    ReferenceConcept,
    ReferenceConceptIndex,
    ReferenceConceptSourceSnapshot,
)
from modules.semantics.validation import (
    resolve_repository_path,
)


REFERENCE_CONCEPT_INDEX_SCHEMA_VERSION = "1.0.0"
REFERENCE_CONCEPT_INDEX_ID = "TURING_REFERENCE_CONCEPT_INDEX"
REFERENCE_CONCEPT_INDEX_VERSION = "1.0.0"

REFERENCE_CONCEPT_INDEX_GENERATOR_ID = (
    "TURING_REFERENCE_CONCEPT_INDEX_GENERATOR"
)
REFERENCE_CONCEPT_INDEX_GENERATOR_VERSION = "1.0.0"

_RDF_NAMESPACE = (
    "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
)
_RDFS_NAMESPACE = (
    "http://www.w3.org/2000/01/rdf-schema#"
)
_OWL_NAMESPACE = "http://www.w3.org/2002/07/owl#"
_SKOS_NAMESPACE = (
    "http://www.w3.org/2004/02/skos/core#"
)
_IOF_ANNOTATION_NAMESPACE = (
    "https://spec.industrialontologies.org/ontology/annotation/"
)
_XML_NAMESPACE = "http://www.w3.org/XML/1998/namespace"

_RDF_ABOUT = f"{{{_RDF_NAMESPACE}}}about"
_RDF_RESOURCE = f"{{{_RDF_NAMESPACE}}}resource"
_XML_LANGUAGE = f"{{{_XML_NAMESPACE}}}lang"

_PREFERRED_LABEL_TAGS = (
    f"{{{_RDFS_NAMESPACE}}}label",
)

_ALTERNATIVE_LABEL_TAGS = (
    f"{{{_SKOS_NAMESPACE}}}altLabel",
    f"{{{_IOF_ANNOTATION_NAMESPACE}}}synonym",
    f"{{{_IOF_ANNOTATION_NAMESPACE}}}abbreviation",
)

_DEFINITION_TAGS = (
    f"{{{_SKOS_NAMESPACE}}}definition",
    (
        f"{{{_IOF_ANNOTATION_NAMESPACE}}}"
        "naturalLanguageDefinition"
    ),
)

_ENTITY_SPECIFICATIONS = (
    (
        "class",
        f"{{{_OWL_NAMESPACE}}}Class",
        f"{{{_RDFS_NAMESPACE}}}subClassOf",
    ),
    (
        "object_property",
        f"{{{_OWL_NAMESPACE}}}ObjectProperty",
        f"{{{_RDFS_NAMESPACE}}}subPropertyOf",
    ),
    (
        "datatype_property",
        f"{{{_OWL_NAMESPACE}}}DatatypeProperty",
        f"{{{_RDFS_NAMESPACE}}}subPropertyOf",
    ),
)

_ENTITY_ORDER = {
    entity_type: order
    for order, (entity_type, _, _) in enumerate(
        _ENTITY_SPECIFICATIONS
    )
}


def generate_reference_concept_index(
    registry: OntologyRegistry | None = None,
    *,
    repository_root: Path = Path("."),
    registry_path: Path = DEFAULT_ONTOLOGY_REGISTRY_PATH,
) -> ReferenceConceptIndex:
    """Generate an in-memory index from verified local snapshots."""

    root = repository_root.resolve()

    if registry is None:
        registry = load_ontology_registry(
            registry_path,
            repository_root=root,
            verify_snapshots=True,
        )
    else:
        verify_ontology_snapshots(
            registry,
            repository_root=root,
        )

    concepts: list[ReferenceConcept] = []
    source_snapshots: list[
        ReferenceConceptSourceSnapshot
    ] = []

    for system, artifact in ontology_artifacts_for_index(
        registry
    ):
        concepts.extend(
            _parse_ontology_artifact(
                system,
                artifact,
                repository_root=root,
            )
        )
        source_snapshots.append(
            ReferenceConceptSourceSnapshot(
                reference_system_id=(
                    system.reference_system_id
                ),
                artifact_id=artifact.artifact_id,
                version=system.version,
                version_iri=(
                    artifact.version_iri
                    or system.version_iri
                ),
                checksum=artifact.checksum,
            )
        )

    _reject_duplicate_iris(concepts)

    ordered_concepts = tuple(
        sorted(
            concepts,
            key=lambda concept: (
                concept.reference_system_id,
                _ENTITY_ORDER[concept.entity_type],
                concept.iri,
            ),
        )
    )
    ordered_snapshots = tuple(
        sorted(
            source_snapshots,
            key=lambda snapshot: (
                snapshot.reference_system_id,
                snapshot.artifact_id,
            ),
        )
    )

    return ReferenceConceptIndex(
        schema_version=(
            REFERENCE_CONCEPT_INDEX_SCHEMA_VERSION
        ),
        index_id=REFERENCE_CONCEPT_INDEX_ID,
        index_version=REFERENCE_CONCEPT_INDEX_VERSION,
        status=registry.reference_concept_index.status,
        authority=registry.reference_concept_index.authority,
        generator_id=(
            REFERENCE_CONCEPT_INDEX_GENERATOR_ID
        ),
        generator_version=(
            REFERENCE_CONCEPT_INDEX_GENERATOR_VERSION
        ),
        registry_id=registry.registry_id,
        registry_version=registry.registry_version,
        source_snapshots=ordered_snapshots,
        concept_count=len(ordered_concepts),
        concepts=ordered_concepts,
    )


def generate_reference_concept_index_file(
    *,
    repository_root: Path = Path("."),
    registry_path: Path = DEFAULT_ONTOLOGY_REGISTRY_PATH,
) -> ReferenceConceptIndex:
    """Generate and atomically persist the configured index file."""

    root = repository_root.resolve()
    registry = load_ontology_registry(
        registry_path,
        repository_root=root,
        verify_snapshots=True,
    )
    index = generate_reference_concept_index(
        registry,
        repository_root=root,
    )
    write_reference_concept_index(
        index,
        registry.reference_concept_index.path,
        repository_root=root,
    )

    return index


def write_reference_concept_index(
    index: ReferenceConceptIndex,
    path: Path,
    *,
    repository_root: Path = Path("."),
) -> Path:
    """Atomically write one deterministic index JSON document."""

    root = repository_root.resolve()
    target = resolve_repository_path(
        root,
        path,
        "Reference Concept Index path",
    )
    temporary = target.with_name(
        f".{target.name}.tmp"
    )

    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary.write_text(
            reference_concept_index_to_json(index),
            encoding="utf-8",
        )
        temporary.replace(target)
    except OSError as exc:
        raise ReferenceConceptIndexError(
            "Unable to write Reference Concept Index to "
            f"{target}: {exc}."
        ) from exc

    return target


def reference_concept_index_to_json(
    index: ReferenceConceptIndex,
) -> str:
    """Serialize an index into deterministic UTF-8 JSON text."""

    return (
        json.dumps(
            reference_concept_index_to_dict(index),
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )


def reference_concept_index_to_dict(
    index: ReferenceConceptIndex,
) -> dict[str, object]:
    """Convert an index into its stable JSON-compatible shape."""

    return {
        "schema_version": index.schema_version,
        "index_id": index.index_id,
        "index_version": index.index_version,
        "status": index.status,
        "authority": index.authority,
        "generator": {
            "generator_id": index.generator_id,
            "generator_version": index.generator_version,
        },
        "registry": {
            "registry_id": index.registry_id,
            "registry_version": index.registry_version,
        },
        "source_snapshots": [
            {
                "reference_system_id": (
                    snapshot.reference_system_id
                ),
                "artifact_id": snapshot.artifact_id,
                "version": snapshot.version,
                "version_iri": snapshot.version_iri,
                "checksum": {
                    "algorithm": (
                        snapshot.checksum.algorithm
                    ),
                    "value": snapshot.checksum.value,
                },
            }
            for snapshot in index.source_snapshots
        ],
        "concept_count": index.concept_count,
        "concepts": [
            _reference_concept_to_dict(concept)
            for concept in index.concepts
        ],
    }


def _parse_ontology_artifact(
    system: OntologyReferenceSystem,
    artifact: OntologyArtifact,
    *,
    repository_root: Path,
) -> tuple[ReferenceConcept, ...]:
    artifact_path = resolve_repository_path(
        repository_root,
        artifact.local_path,
        f"artifact path for {artifact.artifact_id}",
    )

    try:
        root = ElementTree.parse(artifact_path).getroot()
    except (OSError, ElementTree.ParseError) as exc:
        raise OntologyParseError(
            "Unable to parse verified ontology artifact "
            f"{artifact.artifact_id}: {exc}."
        ) from exc

    concepts: list[ReferenceConcept] = []
    version_iri = artifact.version_iri or system.version_iri

    for (
        entity_type,
        element_tag,
        parent_tag,
    ) in _ENTITY_SPECIFICATIONS:
        for element in root.findall(element_tag):
            iri = element.get(_RDF_ABOUT)

            if iri is None:
                continue

            iri = iri.strip()

            if not iri:
                raise OntologyParseError(
                    f"{artifact.artifact_id} contains an empty "
                    "rdf:about IRI."
                )

            preferred_labels = _localized_texts(
                element,
                _PREFERRED_LABEL_TAGS,
            )

            if not preferred_labels:
                raise OntologyParseError(
                    f"Named concept {iri!r} has no rdfs:label "
                    f"in {artifact.artifact_id}."
                )

            concepts.append(
                ReferenceConcept(
                    reference_system_id=(
                        system.reference_system_id
                    ),
                    artifact_id=artifact.artifact_id,
                    source_concept_id=(
                        _source_concept_id(iri)
                    ),
                    iri=iri,
                    entity_type=entity_type,
                    preferred_labels=preferred_labels,
                    alternative_labels=_localized_texts(
                        element,
                        _ALTERNATIVE_LABEL_TAGS,
                    ),
                    definitions=_localized_texts(
                        element,
                        _DEFINITION_TAGS,
                    ),
                    parent_iris=_parent_iris(
                        element,
                        parent_tag,
                    ),
                    version=system.version,
                    version_iri=version_iri,
                )
            )

    return tuple(concepts)


def _localized_texts(
    element: ElementTree.Element,
    tags: tuple[str, ...],
) -> tuple[LocalizedText, ...]:
    values: set[LocalizedText] = set()

    for tag in tags:
        for child in element.findall(tag):
            text = "".join(child.itertext()).strip()

            if not text:
                continue

            language = child.get(_XML_LANGUAGE, "und").strip()

            if not language:
                language = "und"

            values.add(
                LocalizedText(
                    language=language,
                    text=text,
                )
            )

    return tuple(
        sorted(
            values,
            key=lambda value: (
                value.language,
                value.text,
            ),
        )
    )


def _parent_iris(
    element: ElementTree.Element,
    parent_tag: str,
) -> tuple[str, ...]:
    values = {
        resource.strip()
        for child in element.findall(parent_tag)
        if (resource := child.get(_RDF_RESOURCE))
        and resource.strip()
    }

    return tuple(sorted(values))


def _source_concept_id(iri: str) -> str:
    parsed = urlparse(iri)

    if parsed.fragment:
        identifier = parsed.fragment
    else:
        identifier = parsed.path.rstrip("/").rsplit("/", 1)[-1]

    if not identifier:
        raise OntologyParseError(
            f"Unable to derive a source concept ID from IRI {iri!r}."
        )

    return identifier


def _reject_duplicate_iris(
    concepts: list[ReferenceConcept],
) -> None:
    seen: dict[str, ReferenceConcept] = {}

    for concept in concepts:
        previous = seen.get(concept.iri)

        if previous is not None:
            raise DuplicateReferenceConceptIriError(
                "Duplicate reference concept IRI "
                f"{concept.iri!r} in {previous.artifact_id} "
                f"and {concept.artifact_id}."
            )

        seen[concept.iri] = concept


def _reference_concept_to_dict(
    concept: ReferenceConcept,
) -> dict[str, object]:
    return {
        "reference_system_id": concept.reference_system_id,
        "artifact_id": concept.artifact_id,
        "source_concept_id": concept.source_concept_id,
        "iri": concept.iri,
        "entity_type": concept.entity_type,
        "preferred_labels": [
            _localized_text_to_dict(value)
            for value in concept.preferred_labels
        ],
        "alternative_labels": [
            _localized_text_to_dict(value)
            for value in concept.alternative_labels
        ],
        "definitions": [
            _localized_text_to_dict(value)
            for value in concept.definitions
        ],
        "parent_iris": list(concept.parent_iris),
        "version": concept.version,
        "version_iri": concept.version_iri,
    }


def _localized_text_to_dict(
    value: LocalizedText,
) -> dict[str, str]:
    return {
        "language": value.language,
        "text": value.text,
    }