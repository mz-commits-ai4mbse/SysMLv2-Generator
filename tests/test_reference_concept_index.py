"""Tests for deterministic Reference Concept Index generation."""

from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
from pathlib import Path

import pytest

from modules.semantics.reference_index import (
    REFERENCE_CONCEPT_INDEX_GENERATOR_ID,
    REFERENCE_CONCEPT_INDEX_GENERATOR_VERSION,
    REFERENCE_CONCEPT_INDEX_ID,
    REFERENCE_CONCEPT_INDEX_SCHEMA_VERSION,
    REFERENCE_CONCEPT_INDEX_VERSION,
    generate_reference_concept_index,
    reference_concept_index_to_dict,
    reference_concept_index_to_json,
    write_reference_concept_index,
)
from modules.semantics.types import (
    REFERENCE_ENTITY_TYPES,
    ReferenceConcept,
    ReferenceConceptIndex,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
GENERATED_INDEX_PATH = (
    REPOSITORY_ROOT
    / "context/semantics/reference_concept_index.json"
)

EXPECTED_INDEX_SHA256 = (
    "39a1ac2cb4f4261d721fe8bca43a42aa6f339edac30c4950c7b15f32013d1100"
)
EXPECTED_INDEX_SIZE = 204709


@pytest.fixture(scope="module")
def index() -> ReferenceConceptIndex:
    return generate_reference_concept_index(
        repository_root=REPOSITORY_ROOT,
    )


def concept_by_iri(
    index: ReferenceConceptIndex,
    iri: str,
) -> ReferenceConcept:
    return next(
        concept
        for concept in index.concepts
        if concept.iri == iri
    )


def localized_values(values) -> set[tuple[str, str]]:
    return {
        (value.language, value.text)
        for value in values
    }


def test_index_metadata(index: ReferenceConceptIndex) -> None:
    assert index.schema_version == (
        REFERENCE_CONCEPT_INDEX_SCHEMA_VERSION
    )
    assert index.index_id == REFERENCE_CONCEPT_INDEX_ID
    assert index.index_version == (
        REFERENCE_CONCEPT_INDEX_VERSION
    )
    assert index.status == "generated_read_only"
    assert index.authority == "derived_non_authoritative"
    assert index.generator_id == (
        REFERENCE_CONCEPT_INDEX_GENERATOR_ID
    )
    assert index.generator_version == (
        REFERENCE_CONCEPT_INDEX_GENERATOR_VERSION
    )
    assert index.registry_id == "TURING_ONTOLOGY_REGISTRY"
    assert index.registry_version == "1.0.0"


def test_index_contains_expected_concept_count(
    index: ReferenceConceptIndex,
) -> None:
    assert index.concept_count == 236
    assert len(index.concepts) == 236


@pytest.mark.parametrize(
    ("reference_system_id", "expected_count"),
    [
        ("BFO_2020", 76),
        ("IOF_CORE_202602", 160),
    ],
)
def test_reference_system_concept_counts(
    index: ReferenceConceptIndex,
    reference_system_id: str,
    expected_count: int,
) -> None:
    assert sum(
        concept.reference_system_id == reference_system_id
        for concept in index.concepts
    ) == expected_count


@pytest.mark.parametrize(
    (
        "reference_system_id",
        "entity_type",
        "expected_count",
    ),
    [
        ("BFO_2020", "class", 36),
        ("BFO_2020", "object_property", 40),
        ("BFO_2020", "datatype_property", 0),
        ("IOF_CORE_202602", "class", 85),
        ("IOF_CORE_202602", "object_property", 73),
        ("IOF_CORE_202602", "datatype_property", 2),
    ],
)
def test_entity_type_distribution(
    index: ReferenceConceptIndex,
    reference_system_id: str,
    entity_type: str,
    expected_count: int,
) -> None:
    counts = Counter(
        (
            concept.reference_system_id,
            concept.entity_type,
        )
        for concept in index.concepts
    )

    assert counts[
        (reference_system_id, entity_type)
    ] == expected_count


def test_only_accepted_entity_types_are_indexed(
    index: ReferenceConceptIndex,
) -> None:
    assert {
        concept.entity_type
        for concept in index.concepts
    } == REFERENCE_ENTITY_TYPES


def test_all_iris_are_globally_unique(
    index: ReferenceConceptIndex,
) -> None:
    iris = [concept.iri for concept in index.concepts]

    assert len(iris) == len(set(iris)) == 236


def test_anonymous_owl_nodes_are_excluded(
    index: ReferenceConceptIndex,
) -> None:
    assert all(concept.iri for concept in index.concepts)
    assert all(
        concept.source_concept_id
        for concept in index.concepts
    )


def test_every_concept_has_label_and_definition(
    index: ReferenceConceptIndex,
) -> None:
    assert all(
        concept.preferred_labels
        for concept in index.concepts
    )
    assert all(
        concept.definitions
        for concept in index.concepts
    )


def test_localized_text_is_trimmed_and_qualified(
    index: ReferenceConceptIndex,
) -> None:
    values = [
        value
        for concept in index.concepts
        for group in (
            concept.preferred_labels,
            concept.alternative_labels,
            concept.definitions,
        )
        for value in group
    ]

    assert values
    assert all(value.language for value in values)
    assert all(value.text for value in values)
    assert all(
        value.language == value.language.strip()
        for value in values
    )
    assert all(
        value.text == value.text.strip()
        for value in values
    )


def test_localized_text_collections_are_sorted(
    index: ReferenceConceptIndex,
) -> None:
    for concept in index.concepts:
        for values in (
            concept.preferred_labels,
            concept.alternative_labels,
            concept.definitions,
        ):
            assert list(values) == sorted(
                values,
                key=lambda value: (
                    value.language,
                    value.text,
                ),
            )


def test_parent_iris_collections_are_sorted(
    index: ReferenceConceptIndex,
) -> None:
    for concept in index.concepts:
        assert list(concept.parent_iris) == sorted(
            set(concept.parent_iris)
        )


def test_concepts_have_deterministic_global_order(
    index: ReferenceConceptIndex,
) -> None:
    entity_order = {
        "class": 0,
        "object_property": 1,
        "datatype_property": 2,
    }
    expected = sorted(
        index.concepts,
        key=lambda concept: (
            concept.reference_system_id,
            entity_order[concept.entity_type],
            concept.iri,
        ),
    )

    assert list(index.concepts) == expected


def test_bfo_entity_concept(index: ReferenceConceptIndex) -> None:
    concept = concept_by_iri(
        index,
        "http://purl.obolibrary.org/obo/BFO_0000001",
    )

    assert concept.reference_system_id == "BFO_2020"
    assert concept.artifact_id == "BFO_CORE_2020"
    assert concept.source_concept_id == "BFO_0000001"
    assert concept.entity_type == "class"
    assert ("en", "entity") in localized_values(
        concept.preferred_labels
    )
    assert concept.parent_iris == ()


def test_bfo_continuant_parent(index: ReferenceConceptIndex) -> None:
    concept = concept_by_iri(
        index,
        "http://purl.obolibrary.org/obo/BFO_0000002",
    )

    assert (
        "http://purl.obolibrary.org/obo/BFO_0000001"
        in concept.parent_iris
    )


def test_bfo_alternative_label(index: ReferenceConceptIndex) -> None:
    concept = concept_by_iri(
        index,
        "http://purl.obolibrary.org/obo/BFO_0000054",
    )

    assert ("en", "realized in") in localized_values(
        concept.alternative_labels
    )


def test_iof_agent_concept(index: ReferenceConceptIndex) -> None:
    concept = concept_by_iri(
        index,
        (
            "https://spec.industrialontologies.org/"
            "ontology/construct/Agent"
        ),
    )

    assert concept.reference_system_id == "IOF_CORE_202602"
    assert concept.artifact_id == "IOF_CORE_202602"
    assert concept.source_concept_id == "Agent"
    assert concept.entity_type == "class"
    assert ("en-US", "agent") in localized_values(
        concept.preferred_labels
    )
    assert (
        "en-US",
        (
            "person, group of persons, or engineered system "
            "with an agent role"
        ),
    ) in localized_values(concept.definitions)
    assert concept.parent_iris == (
        "http://purl.obolibrary.org/obo/BFO_0000040",
    )


def test_iof_synonym_is_alternative_label(
    index: ReferenceConceptIndex,
) -> None:
    concept = concept_by_iri(
        index,
        (
            "https://spec.industrialontologies.org/"
            "ontology/construct/ActionSpecification"
        ),
    )

    assert (
        "en-US",
        "actionable work instruction",
    ) in localized_values(concept.alternative_labels)


def test_iof_datatype_property(index: ReferenceConceptIndex) -> None:
    concept = concept_by_iri(
        index,
        (
            "https://spec.industrialontologies.org/ontology/"
            "construct/hasSimpleExpressionValue"
        ),
    )

    assert concept.entity_type == "datatype_property"
    assert concept.parent_iris == (
        "http://www.w3.org/2002/07/owl#topDataProperty",
    )


def test_source_snapshots_are_only_ontology_artifacts(
    index: ReferenceConceptIndex,
) -> None:
    assert [
        snapshot.artifact_id
        for snapshot in index.source_snapshots
    ] == [
        "BFO_CORE_2020",
        "IOF_CORE_202602",
    ]


def test_source_snapshot_checksums_are_pinned(
    index: ReferenceConceptIndex,
) -> None:
    checksums = {
        snapshot.artifact_id: snapshot.checksum.value
        for snapshot in index.source_snapshots
    }

    assert checksums == {
        "BFO_CORE_2020": (
            "b65c817a7a25501499d287981aea972f"
            "2ce33146dcfb855915a459f6a051718d"
        ),
        "IOF_CORE_202602": (
            "a653bcacef50a241aa1696d0d647b605"
            "27497cb1f32726f1891a05cbe5cb7638"
        ),
    }


def test_serialization_is_byte_deterministic(
    index: ReferenceConceptIndex,
) -> None:
    first = reference_concept_index_to_json(index)
    second = reference_concept_index_to_json(index)

    assert first == second
    assert first.endswith("\n")
    assert "generated_at" not in first


def test_serialized_shape_matches_count(
    index: ReferenceConceptIndex,
) -> None:
    payload = reference_concept_index_to_dict(index)

    assert payload["concept_count"] == 236
    assert len(payload["concepts"]) == 236
    assert payload["authority"] == "derived_non_authoritative"
    assert payload["generator"] == {
        "generator_id": (
            "TURING_REFERENCE_CONCEPT_INDEX_GENERATOR"
        ),
        "generator_version": "1.0.0",
    }


def test_serialized_json_is_valid(
    index: ReferenceConceptIndex,
) -> None:
    payload = json.loads(
        reference_concept_index_to_json(index)
    )

    assert payload["index_id"] == (
        "TURING_REFERENCE_CONCEPT_INDEX"
    )
    assert payload["concept_count"] == 236


def test_generated_file_matches_generator_exactly(
    index: ReferenceConceptIndex,
) -> None:
    assert GENERATED_INDEX_PATH.read_text(
        encoding="utf-8"
    ) == reference_concept_index_to_json(index)


def test_generated_file_has_pinned_checksum() -> None:
    content = GENERATED_INDEX_PATH.read_bytes()

    assert len(content) == EXPECTED_INDEX_SIZE
    assert sha256(content).hexdigest() == (
        EXPECTED_INDEX_SHA256
    )


def test_atomic_writer_preserves_deterministic_bytes(
    index: ReferenceConceptIndex,
    tmp_path: Path,
) -> None:
    relative_path = Path("generated/reference_index.json")
    target = write_reference_concept_index(
        index,
        relative_path,
        repository_root=tmp_path,
    )
    first = target.read_bytes()

    second_target = write_reference_concept_index(
        index,
        relative_path,
        repository_root=tmp_path,
    )
    second = second_target.read_bytes()

    assert target == second_target
    assert first == second
    assert not target.with_name(
        f".{target.name}.tmp"
    ).exists()