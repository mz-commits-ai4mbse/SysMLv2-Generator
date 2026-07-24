"""Tests for the curated Turing Core Vocabulary."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import FrozenInstanceError
import json
from pathlib import Path
from typing import Any

import pytest

from modules.semantics.errors import (
    TuringCoreVocabularyError,
)
from modules.semantics.turing_core import (
    DEFAULT_TURING_CORE_VOCABULARY_PATH,
    TURING_CORE_SCHEMA_VERSION,
    TURING_CORE_VOCABULARY_ID,
    load_turing_core_vocabulary,
    parse_turing_core_vocabulary,
    turing_core_concept_by_id,
    turing_core_concepts_by_label,
    validate_turing_core_references,
)
from modules.semantics.types import (
    TuringCoreConcept,
    TuringCoreVocabulary,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
VOCABULARY_PATH = (
    REPOSITORY_ROOT
    / DEFAULT_TURING_CORE_VOCABULARY_PATH
)


def vocabulary_payload() -> dict[str, Any]:
    """Return one independent copy of the accepted payload."""

    return json.loads(
        VOCABULARY_PATH.read_text(encoding="utf-8")
    )


def load_vocabulary() -> TuringCoreVocabulary:
    """Load the accepted vocabulary from the repository root."""

    return load_turing_core_vocabulary(
        repository_root=REPOSITORY_ROOT,
    )


def set_nested(
    payload: dict[str, Any],
    path: tuple[str | int, ...],
    value: Any,
) -> None:
    """Replace one nested payload value."""

    target: Any = payload

    for key in path[:-1]:
        target = target[key]

    target[path[-1]] = value


def delete_nested(
    payload: dict[str, Any],
    path: tuple[str | int, ...],
) -> None:
    """Delete one nested payload value."""

    target: Any = payload

    for key in path[:-1]:
        target = target[key]

    del target[path[-1]]


def external_mapping(
    *,
    reference_system_id: str = "BFO_2020",
    reference_system_version: str = "2020",
    relation: str = "related_to",
    iri: str = (
        "http://purl.obolibrary.org/obo/BFO_0000001"
    ),
) -> dict[str, Any]:
    """Return one structurally valid reviewed mapping."""

    return {
        "reference_system_id": reference_system_id,
        "reference_system_version": (
            reference_system_version
        ),
        "reference_concept_iri": iri,
        "relation": relation,
        "rationale": "Reviewed test mapping.",
        "provenance_source_reference_ids": [
            "SRC_TURING_CORE_ADR_011"
        ],
    }


def test_loads_accepted_vocabulary() -> None:
    vocabulary = load_vocabulary()

    assert vocabulary.schema_version == "1.0.0"
    assert vocabulary.vocabulary_id == (
        "TURING_CORE_VOCABULARY"
    )
    assert vocabulary.vocabulary_version == "1.0.0"
    assert vocabulary.name == "Turing Core Vocabulary"
    assert vocabulary.status == "active"
    assert vocabulary.default_language == "en"


def test_schema_constants_match_payload() -> None:
    payload = vocabulary_payload()

    assert TURING_CORE_SCHEMA_VERSION == "1.0.0"
    assert TURING_CORE_VOCABULARY_ID == (
        "TURING_CORE_VOCABULARY"
    )
    assert payload["schema_version"] == (
        TURING_CORE_SCHEMA_VERSION
    )
    assert payload["vocabulary_id"] == (
        TURING_CORE_VOCABULARY_ID
    )


def test_vocabulary_and_concepts_are_immutable() -> None:
    vocabulary = load_vocabulary()

    with pytest.raises(FrozenInstanceError):
        vocabulary.name = "Changed"  # type: ignore[misc]

    with pytest.raises(FrozenInstanceError):
        vocabulary.concepts[0].preferred_label = (  # type: ignore[misc]
            "Changed"
        )


def test_authority_boundary_is_preserved() -> None:
    authority = load_vocabulary().authority

    assert authority.role == "curated_semantic_bridge"
    assert authority.external_reference_systems == (
        "BFO_2020",
        "IOF_CORE_202602",
    )
    assert (
        authority.automatic_project_mutation_allowed
        is False
    )
    assert "does not create engineering facts" in (
        authority.authority_rule
    )


def test_mapping_boundaries_are_preserved() -> None:
    vocabulary = load_vocabulary()

    assert (
        vocabulary.framework_mapping_policy
        .automatic_framework_assignment_allowed
        is False
    )
    assert (
        vocabulary.sysml_v2_mapping_policy
        .automatic_model_generation_allowed
        is False
    )
    assert (
        vocabulary.external_mapping_policy
        .automatic_exact_match_allowed
        is False
    )
    assert (
        vocabulary.external_mapping_policy.review_required
        is True
    )
    assert (
        vocabulary.external_mapping_policy.mapping_required
        is False
    )


@pytest.mark.parametrize(
    ("concept_id", "label", "kind"),
    [
        ("TC-000001", "Stakeholder", "stakeholder_context"),
        ("TC-000002", "Actor", "stakeholder_context"),
        ("TC-000003", "User Need", "need"),
        (
            "TC-000004",
            "Stakeholder Requirement",
            "requirement",
        ),
        ("TC-000005", "Use Case", "stakeholder_behavior"),
        ("TC-000006", "Requirement", "requirement"),
        ("TC-000007", "Function", "behavior"),
        (
            "TC-000008",
            "Logical Architecture Element",
            "architecture_element",
        ),
        (
            "TC-000009",
            "Physical Architecture Element",
            "architecture_element",
        ),
        ("TC-000010", "System", "system_context"),
        ("TC-000011", "Subsystem", "system_context"),
    ],
)
def test_expected_concepts(
    concept_id: str,
    label: str,
    kind: str,
) -> None:
    concept = turing_core_concept_by_id(
        load_vocabulary(),
        concept_id,
    )

    assert isinstance(concept, TuringCoreConcept)
    assert concept.preferred_label == label
    assert concept.concept_kind == kind
    assert concept.status == "active"


def test_concept_ids_are_unique_and_ordered() -> None:
    concepts = load_vocabulary().concepts

    assert tuple(
        concept.concept_id
        for concept in concepts
    ) == tuple(
        f"TC-{number:06d}"
        for number in range(1, 12)
    )
    assert tuple(
        concept.order
        for concept in concepts
    ) == tuple(range(1, 12))


def test_preferred_labels_are_casefold_unique() -> None:
    labels = [
        concept.preferred_label.casefold()
        for concept in load_vocabulary().concepts
    ]

    assert len(labels) == len(set(labels)) == 11


def test_initial_external_mappings_are_unreviewed() -> None:
    concepts = load_vocabulary().concepts

    assert all(
        concept.external_mapping_status
        == "not_reviewed"
        for concept in concepts
    )
    assert all(
        concept.external_mappings == ()
        for concept in concepts
    )


@pytest.mark.parametrize(
    ("concept_id", "expected_targets", "expected_scopes"),
    [
        (
            "TC-000001",
            ("FW_STAKEHOLDER_STAKEHOLDERS",),
            ("FW_LEVEL_STAKEHOLDER",),
        ),
        (
            "TC-000002",
            ("FW_STAKEHOLDER_STAKEHOLDERS",),
            ("FW_LEVEL_STAKEHOLDER",),
        ),
        (
            "TC-000003",
            ("FW_STAKEHOLDER_USER_NEEDS",),
            ("FW_LEVEL_STAKEHOLDER",),
        ),
        (
            "TC-000004",
            (
                "FW_STAKEHOLDER_"
                "STAKEHOLDER_REQUIREMENTS",
            ),
            ("FW_LEVEL_STAKEHOLDER",),
        ),
        (
            "TC-000005",
            ("FW_STAKEHOLDER_USE_CASES",),
            ("FW_LEVEL_STAKEHOLDER",),
        ),
        (
            "TC-000006",
            (
                "FW_SYSTEM_REQUIREMENTS",
                "FW_SUBSYSTEM_REQUIREMENTS",
            ),
            (
                "FW_LEVEL_SYSTEM",
                "FW_LEVEL_SUBSYSTEM",
            ),
        ),
        (
            "TC-000007",
            (
                "FW_SYSTEM_FUNCTIONAL",
                "FW_SUBSYSTEM_FUNCTIONAL",
            ),
            (
                "FW_LEVEL_SYSTEM",
                "FW_LEVEL_SUBSYSTEM",
            ),
        ),
        (
            "TC-000008",
            (
                "FW_SYSTEM_LOGICAL",
                "FW_SUBSYSTEM_LOGICAL",
            ),
            (
                "FW_LEVEL_SYSTEM",
                "FW_LEVEL_SUBSYSTEM",
            ),
        ),
        (
            "TC-000009",
            (
                "FW_SYSTEM_PHYSICAL",
                "FW_SUBSYSTEM_PHYSICAL",
            ),
            (
                "FW_LEVEL_SYSTEM",
                "FW_LEVEL_SUBSYSTEM",
            ),
        ),
        (
            "TC-000010",
            (),
            ("FW_LEVEL_SYSTEM",),
        ),
        (
            "TC-000011",
            (),
            ("FW_LEVEL_SUBSYSTEM",),
        ),
    ],
)
def test_expected_framework_candidates(
    concept_id: str,
    expected_targets: tuple[str, ...],
    expected_scopes: tuple[str, ...],
) -> None:
    concept = turing_core_concept_by_id(
        load_vocabulary(),
        concept_id,
    )

    assert (
        concept.candidate_framework_node_ids
        == expected_targets
    )
    assert (
        concept.framework_scope_node_ids
        == expected_scopes
    )


@pytest.mark.parametrize(
    ("concept_id", "construct_ids"),
    [
        ("TC-000001", ()),
        ("TC-000002", ()),
        ("TC-000003", ()),
        ("TC-000004", ("TN_008",)),
        ("TC-000005", ()),
        ("TC-000006", ("TN_008",)),
        ("TC-000007", ("TN_005", "TN_006")),
        ("TC-000008", ("TN_003", "TN_004")),
        ("TC-000009", ("TN_003", "TN_004")),
        ("TC-000010", ("TN_003", "TN_004")),
        ("TC-000011", ("TN_003", "TN_004")),
    ],
)
def test_expected_sysml_representation_candidates(
    concept_id: str,
    construct_ids: tuple[str, ...],
) -> None:
    concept = turing_core_concept_by_id(
        load_vocabulary(),
        concept_id,
    )

    assert tuple(
        candidate.construct_id
        for candidate in (
            concept.sysml_v2_representation_candidates
        )
    ) == construct_ids
    assert all(
        candidate.relation == "candidate_representation"
        for candidate in (
            concept.sysml_v2_representation_candidates
        )
    )


def test_stakeholder_and_actor_remain_distinct() -> None:
    vocabulary = load_vocabulary()
    stakeholder = turing_core_concept_by_id(
        vocabulary,
        "TC-000001",
    )
    actor = turing_core_concept_by_id(
        vocabulary,
        "TC-000002",
    )

    assert stakeholder != actor
    assert stakeholder.concept_id in actor.related_concept_ids
    assert actor.concept_id in stakeholder.related_concept_ids


def test_use_case_and_function_remain_distinct() -> None:
    vocabulary = load_vocabulary()
    use_case = turing_core_concept_by_id(
        vocabulary,
        "TC-000005",
    )
    function = turing_core_concept_by_id(
        vocabulary,
        "TC-000007",
    )

    assert use_case.concept_kind == "stakeholder_behavior"
    assert function.concept_kind == "behavior"
    assert not use_case.sysml_v2_representation_candidates
    assert function.sysml_v2_representation_candidates


def test_subsystem_is_narrower_internal_concept() -> None:
    subsystem = turing_core_concept_by_id(
        load_vocabulary(),
        "TC-000011",
    )

    assert subsystem.broader_concept_ids == (
        "TC-000010",
    )


@pytest.mark.parametrize(
    ("query", "expected_id"),
    [
        ("Function", "TC-000007"),
        ("function", "TC-000007"),
        ("FUNCTION", "TC-000007"),
        ("Logical Component", "TC-000008"),
        ("Implementation Element", "TC-000009"),
        ("System of Interest", "TC-000010"),
    ],
)
def test_label_lookup(
    query: str,
    expected_id: str,
) -> None:
    matches = turing_core_concepts_by_label(
        load_vocabulary(),
        query,
    )

    assert tuple(
        concept.concept_id
        for concept in matches
    ) == (expected_id,)


def test_label_lookup_returns_empty_tuple_for_unknown_label() -> None:
    assert turing_core_concepts_by_label(
        load_vocabulary(),
        "Unknown Label",
    ) == ()


@pytest.mark.parametrize(
    "query",
    ["", " ", " Function ", None, 1, True],
)
def test_label_lookup_rejects_invalid_query(
    query: object,
) -> None:
    with pytest.raises(TuringCoreVocabularyError):
        turing_core_concepts_by_label(
            load_vocabulary(),
            query,  # type: ignore[arg-type]
        )


def test_concept_lookup_rejects_unknown_id() -> None:
    with pytest.raises(
        TuringCoreVocabularyError,
        match="Unknown Turing Core concept ID",
    ):
        turing_core_concept_by_id(
            load_vocabulary(),
            "TC-999999",
        )


@pytest.mark.parametrize(
    "payload",
    [None, [], "vocabulary", 1, True],
)
def test_rejects_non_object_payload(payload: object) -> None:
    with pytest.raises(TuringCoreVocabularyError):
        parse_turing_core_vocabulary(payload)


@pytest.mark.parametrize(
    "field",
    [
        "schema_version",
        "vocabulary_id",
        "vocabulary_version",
        "name",
        "status",
        "default_language",
        "authority",
        "source_references",
        "identifier_policy",
        "label_policy",
        "concept_relation_policy",
        "framework_mapping_policy",
        "sysml_v2_mapping_policy",
        "external_mapping_policy",
        "concepts",
    ],
)
def test_rejects_missing_top_level_field(field: str) -> None:
    payload = vocabulary_payload()
    del payload[field]

    with pytest.raises(
        TuringCoreVocabularyError,
        match="missing fields",
    ):
        parse_turing_core_vocabulary(payload)


def test_rejects_unknown_top_level_field() -> None:
    payload = vocabulary_payload()
    payload["unexpected"] = True

    with pytest.raises(
        TuringCoreVocabularyError,
        match="unknown fields",
    ):
        parse_turing_core_vocabulary(payload)


@pytest.mark.parametrize(
    "schema_version",
    ["1", "1.0", "2.0.0", 1, None, True],
)
def test_rejects_unsupported_schema_version(
    schema_version: object,
) -> None:
    payload = vocabulary_payload()
    payload["schema_version"] = schema_version

    with pytest.raises(TuringCoreVocabularyError):
        parse_turing_core_vocabulary(payload)


@pytest.mark.parametrize(
    "vocabulary_id",
    [
        "OTHER_VOCABULARY",
        "turing_core_vocabulary",
        "",
        None,
        True,
    ],
)
def test_rejects_invalid_vocabulary_id(
    vocabulary_id: object,
) -> None:
    payload = vocabulary_payload()
    payload["vocabulary_id"] = vocabulary_id

    with pytest.raises(TuringCoreVocabularyError):
        parse_turing_core_vocabulary(payload)


@pytest.mark.parametrize(
    "version",
    ["1", "1.0", "v1.0.0", "", None, True],
)
def test_rejects_invalid_vocabulary_version(
    version: object,
) -> None:
    payload = vocabulary_payload()
    payload["vocabulary_version"] = version

    with pytest.raises(TuringCoreVocabularyError):
        parse_turing_core_vocabulary(payload)


@pytest.mark.parametrize(
    "status",
    ["unknown", "", None, True],
)
def test_rejects_invalid_vocabulary_status(
    status: object,
) -> None:
    payload = vocabulary_payload()
    payload["status"] = status

    with pytest.raises(TuringCoreVocabularyError):
        parse_turing_core_vocabulary(payload)


@pytest.mark.parametrize(
    "language",
    ["EN", "eng", "e", "", None, True],
)
def test_rejects_invalid_default_language(
    language: object,
) -> None:
    payload = vocabulary_payload()
    payload["default_language"] = language

    with pytest.raises(TuringCoreVocabularyError):
        parse_turing_core_vocabulary(payload)


def test_rejects_automatic_project_mutation() -> None:
    payload = vocabulary_payload()
    payload["authority"][
        "automatic_project_mutation_allowed"
    ] = True

    with pytest.raises(TuringCoreVocabularyError):
        parse_turing_core_vocabulary(payload)


def test_rejects_mismatched_external_authorities() -> None:
    payload = vocabulary_payload()
    payload["authority"]["external_reference_systems"] = [
        "BFO_2020"
    ]

    with pytest.raises(
        TuringCoreVocabularyError,
        match="must match",
    ):
        parse_turing_core_vocabulary(payload)


def test_rejects_duplicate_source_reference_id() -> None:
    payload = vocabulary_payload()
    payload["source_references"][1][
        "source_reference_id"
    ] = payload["source_references"][0][
        "source_reference_id"
    ]

    with pytest.raises(TuringCoreVocabularyError):
        parse_turing_core_vocabulary(payload)


def test_rejects_duplicate_source_path() -> None:
    payload = vocabulary_payload()
    payload["source_references"][1]["path"] = (
        payload["source_references"][0]["path"]
    )

    with pytest.raises(TuringCoreVocabularyError):
        parse_turing_core_vocabulary(payload)


@pytest.mark.parametrize(
    "path",
    [
        "../outside.md",
        "/absolute/path.md",
        "external/source.md",
        r"context\source.md",
    ],
)
def test_rejects_unsafe_or_disallowed_source_path(
    path: str,
) -> None:
    payload = vocabulary_payload()
    payload["source_references"][0]["path"] = path

    with pytest.raises(TuringCoreVocabularyError):
        parse_turing_core_vocabulary(payload)


def test_rejects_partial_structured_source_reference() -> None:
    payload = vocabulary_payload()
    del payload["source_references"][1][
        "referenced_version"
    ]

    with pytest.raises(
        TuringCoreVocabularyError,
        match="must either both be present",
    ):
        parse_turing_core_vocabulary(payload)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("field", "id"),
        ("pattern", "^TC-.*$"),
        ("scope", "project_local"),
        ("allocation", "random"),
        ("reuse_allowed", True),
        ("meaning_change_allowed", True),
    ],
)
def test_rejects_invalid_identifier_policy(
    field: str,
    value: object,
) -> None:
    payload = vocabulary_payload()
    payload["identifier_policy"][field] = value

    with pytest.raises(TuringCoreVocabularyError):
        parse_turing_core_vocabulary(payload)


@pytest.mark.parametrize(
    "field",
    [
        "preferred_label_required",
        "preferred_label_unique_casefolded",
        (
            "alternative_labels_unique_within_"
            "concept_casefolded"
        ),
        (
            "preferred_label_may_equal_"
            "alternative_label_casefolded"
        ),
        "automatic_synonym_generation_allowed",
    ],
)
def test_rejects_reversed_label_policy(field: str) -> None:
    payload = vocabulary_payload()
    payload["label_policy"][field] = not (
        payload["label_policy"][field]
    )

    with pytest.raises(TuringCoreVocabularyError):
        parse_turing_core_vocabulary(payload)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("allowed_relations", ["broader_concept_ids"]),
        ("self_reference_allowed", True),
        (
            "unknown_concept_reference_behavior",
            "ignore",
        ),
    ],
)
def test_rejects_invalid_concept_relation_policy(
    field: str,
    value: object,
) -> None:
    payload = vocabulary_payload()
    payload["concept_relation_policy"][field] = value

    with pytest.raises(TuringCoreVocabularyError):
        parse_turing_core_vocabulary(payload)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("candidate_target_field", "target_ids"),
        ("scope_reference_field", "scope_ids"),
        (
            "candidate_target_must_be_mapping_target",
            False,
        ),
        (
            "scope_reference_may_reference_level_node",
            False,
        ),
        (
            "automatic_framework_assignment_allowed",
            True,
        ),
    ],
)
def test_rejects_invalid_framework_mapping_policy(
    field: str,
    value: object,
) -> None:
    payload = vocabulary_payload()
    payload["framework_mapping_policy"][field] = value

    with pytest.raises(TuringCoreVocabularyError):
        parse_turing_core_vocabulary(payload)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("allowed_relation", "exact_match"),
        ("unknown_construct_behavior", "ignore"),
        ("automatic_model_generation_allowed", True),
    ],
)
def test_rejects_invalid_sysml_mapping_policy(
    field: str,
    value: object,
) -> None:
    payload = vocabulary_payload()
    payload["sysml_v2_mapping_policy"][field] = value

    with pytest.raises(TuringCoreVocabularyError):
        parse_turing_core_vocabulary(payload)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("allowed_relations", ["exact_match"]),
        ("mapping_required", True),
        ("review_required", False),
        ("automatic_exact_match_allowed", True),
        ("initial_mapping_status", "reviewed"),
    ],
)
def test_rejects_invalid_external_mapping_policy(
    field: str,
    value: object,
) -> None:
    payload = vocabulary_payload()
    payload["external_mapping_policy"][field] = value

    with pytest.raises(TuringCoreVocabularyError):
        parse_turing_core_vocabulary(payload)


@pytest.mark.parametrize(
    "concept_id",
    [
        "TC-1",
        "TC-0000001",
        "tc-000001",
        "IU-000001",
        "",
        None,
        True,
    ],
)
def test_rejects_invalid_concept_id(
    concept_id: object,
) -> None:
    payload = vocabulary_payload()
    payload["concepts"][0]["concept_id"] = concept_id

    with pytest.raises(TuringCoreVocabularyError):
        parse_turing_core_vocabulary(payload)


def test_rejects_duplicate_concept_id() -> None:
    payload = vocabulary_payload()
    payload["concepts"][1]["concept_id"] = (
        payload["concepts"][0]["concept_id"]
    )

    with pytest.raises(TuringCoreVocabularyError):
        parse_turing_core_vocabulary(payload)


def test_rejects_duplicate_preferred_label_casefolded() -> None:
    payload = vocabulary_payload()
    payload["concepts"][1]["preferred_label"] = (
        payload["concepts"][0]["preferred_label"].upper()
    )

    with pytest.raises(
        TuringCoreVocabularyError,
        match="Duplicate case-insensitive preferred label",
    ):
        parse_turing_core_vocabulary(payload)


def test_rejects_preferred_label_as_alternative() -> None:
    payload = vocabulary_payload()
    concept = payload["concepts"][0]
    concept["alternative_labels"].append(
        concept["preferred_label"].upper()
    )

    with pytest.raises(
        TuringCoreVocabularyError,
        match="preferred label as an alternative",
    ):
        parse_turing_core_vocabulary(payload)


def test_rejects_duplicate_alternative_label_casefolded() -> None:
    payload = vocabulary_payload()
    payload["concepts"][0]["alternative_labels"] = [
        "Concern Holder",
        "CONCERN HOLDER",
    ]

    with pytest.raises(TuringCoreVocabularyError):
        parse_turing_core_vocabulary(payload)


@pytest.mark.parametrize(
    "kind",
    ["component", "", None, True],
)
def test_rejects_unknown_concept_kind(kind: object) -> None:
    payload = vocabulary_payload()
    payload["concepts"][0]["concept_kind"] = kind

    with pytest.raises(TuringCoreVocabularyError):
        parse_turing_core_vocabulary(payload)


@pytest.mark.parametrize(
    "status",
    ["candidate", "", None, True],
)
def test_rejects_unknown_concept_status(
    status: object,
) -> None:
    payload = vocabulary_payload()
    payload["concepts"][0]["status"] = status

    with pytest.raises(TuringCoreVocabularyError):
        parse_turing_core_vocabulary(payload)


def test_rejects_unknown_internal_concept_reference() -> None:
    payload = vocabulary_payload()
    payload["concepts"][0]["related_concept_ids"] = [
        "TC-999999"
    ]

    with pytest.raises(
        TuringCoreVocabularyError,
        match="unknown Turing Core concept IDs",
    ):
        parse_turing_core_vocabulary(payload)


def test_rejects_self_reference() -> None:
    payload = vocabulary_payload()
    payload["concepts"][0]["related_concept_ids"] = [
        "TC-000001"
    ]

    with pytest.raises(
        TuringCoreVocabularyError,
        match="must not reference itself",
    ):
        parse_turing_core_vocabulary(payload)


def test_rejects_relation_overlap() -> None:
    payload = vocabulary_payload()
    payload["concepts"][10]["related_concept_ids"].append(
        "TC-000010"
    )

    with pytest.raises(
        TuringCoreVocabularyError,
        match="across broader and related",
    ):
        parse_turing_core_vocabulary(payload)


def test_rejects_broader_concept_cycle() -> None:
    payload = vocabulary_payload()
    payload["concepts"][9]["broader_concept_ids"] = [
        "TC-000011"
    ]
    payload["concepts"][9]["related_concept_ids"].remove(
        "TC-000011"
    )

    with pytest.raises(
        TuringCoreVocabularyError,
        match="contain a cycle",
    ):
        parse_turing_core_vocabulary(payload)


def test_rejects_unknown_provenance_reference() -> None:
    payload = vocabulary_payload()
    payload["concepts"][0][
        "provenance_source_reference_ids"
    ] = ["UNKNOWN_SOURCE"]

    with pytest.raises(
        TuringCoreVocabularyError,
        match="unknown provenance",
    ):
        parse_turing_core_vocabulary(payload)


def test_rejects_non_contiguous_concept_order() -> None:
    payload = vocabulary_payload()
    payload["concepts"][10]["order"] = 12

    with pytest.raises(
        TuringCoreVocabularyError,
        match="contiguous order",
    ):
        parse_turing_core_vocabulary(payload)


def test_rejects_non_ascending_concept_id_order() -> None:
    payload = vocabulary_payload()
    replacements = {
        "TC-000001": "TC-000002",
        "TC-000002": "TC-000001",
    }

    for concept in payload["concepts"]:
        concept["concept_id"] = replacements.get(
            concept["concept_id"],
            concept["concept_id"],
        )

        for field in (
            "broader_concept_ids",
            "related_concept_ids",
        ):
            concept[field] = [
                replacements.get(concept_id, concept_id)
                for concept_id in concept[field]
            ]

    with pytest.raises(
        TuringCoreVocabularyError,
        match="ascending concept-ID order",
    ):
        parse_turing_core_vocabulary(payload)


def test_rejects_duplicate_sysml_construct_candidate() -> None:
    payload = vocabulary_payload()
    candidates = payload["concepts"][6][
        "sysml_v2_representation_candidates"
    ]
    candidates.append(deepcopy(candidates[0]))

    with pytest.raises(TuringCoreVocabularyError):
        parse_turing_core_vocabulary(payload)


def test_rejects_invalid_sysml_candidate_relation() -> None:
    payload = vocabulary_payload()
    payload["concepts"][6][
        "sysml_v2_representation_candidates"
    ][0]["relation"] = "exact_match"

    with pytest.raises(TuringCoreVocabularyError):
        parse_turing_core_vocabulary(payload)


def test_rejects_mapping_while_not_reviewed() -> None:
    payload = vocabulary_payload()
    payload["concepts"][0]["external_mappings"] = [
        external_mapping()
    ]

    with pytest.raises(
        TuringCoreVocabularyError,
        match="must be empty",
    ):
        parse_turing_core_vocabulary(payload)


def test_accepts_structurally_reviewed_external_mapping() -> None:
    payload = vocabulary_payload()
    payload["concepts"][0][
        "external_mapping_status"
    ] = "reviewed"
    payload["concepts"][0]["external_mappings"] = [
        external_mapping()
    ]

    vocabulary = parse_turing_core_vocabulary(payload)

    assert (
        vocabulary.concepts[0]
        .external_mappings[0]
        .reference_system_id
        == "BFO_2020"
    )


@pytest.mark.parametrize(
    ("relation", "iri"),
    [
        ("unsupported", "https://example.org/concept"),
        ("related_to", "not-an-iri"),
    ],
)
def test_rejects_invalid_external_mapping(
    relation: str,
    iri: str,
) -> None:
    payload = vocabulary_payload()
    payload["concepts"][0][
        "external_mapping_status"
    ] = "reviewed"
    payload["concepts"][0]["external_mappings"] = [
        external_mapping(
            relation=relation,
            iri=iri,
        )
    ]

    with pytest.raises(TuringCoreVocabularyError):
        parse_turing_core_vocabulary(payload)


def test_rejects_duplicate_external_mapping() -> None:
    payload = vocabulary_payload()
    payload["concepts"][0][
        "external_mapping_status"
    ] = "reviewed"
    mapping = external_mapping()
    payload["concepts"][0]["external_mappings"] = [
        mapping,
        deepcopy(mapping),
    ]

    with pytest.raises(
        TuringCoreVocabularyError,
        match="duplicate external mappings",
    ):
        parse_turing_core_vocabulary(payload)


def test_all_repository_references_validate() -> None:
    validate_turing_core_references(
        parse_turing_core_vocabulary(
            vocabulary_payload()
        ),
        repository_root=REPOSITORY_ROOT,
    )


def test_rejects_missing_repository_source() -> None:
    payload = vocabulary_payload()
    payload["source_references"][0]["path"] = (
        "collaboration/decisions/missing.md"
    )
    vocabulary = parse_turing_core_vocabulary(payload)

    with pytest.raises(
        TuringCoreVocabularyError,
        match="does not exist",
    ):
        validate_turing_core_references(
            vocabulary,
            repository_root=REPOSITORY_ROOT,
        )


def test_rejects_mismatched_source_artifact_id() -> None:
    payload = vocabulary_payload()
    payload["source_references"][1][
        "referenced_id"
    ] = "OTHER_FRAMEWORK"
    vocabulary = parse_turing_core_vocabulary(payload)

    with pytest.raises(
        TuringCoreVocabularyError,
        match="expected ID",
    ):
        validate_turing_core_references(
            vocabulary,
            repository_root=REPOSITORY_ROOT,
        )


def test_rejects_mismatched_source_artifact_version() -> None:
    payload = vocabulary_payload()
    payload["source_references"][1][
        "referenced_version"
    ] = "9.9.9"
    vocabulary = parse_turing_core_vocabulary(payload)

    with pytest.raises(
        TuringCoreVocabularyError,
        match="expected version",
    ):
        validate_turing_core_references(
            vocabulary,
            repository_root=REPOSITORY_ROOT,
        )


def test_rejects_unknown_framework_target() -> None:
    payload = vocabulary_payload()
    payload["concepts"][0][
        "candidate_framework_node_ids"
    ] = ["FW_UNKNOWN"]
    vocabulary = parse_turing_core_vocabulary(payload)

    with pytest.raises(
        TuringCoreVocabularyError,
        match="unknown or non-mapping framework targets",
    ):
        validate_turing_core_references(
            vocabulary,
            repository_root=REPOSITORY_ROOT,
        )


def test_rejects_level_as_framework_target() -> None:
    payload = vocabulary_payload()
    payload["concepts"][0][
        "candidate_framework_node_ids"
    ] = ["FW_LEVEL_STAKEHOLDER"]
    vocabulary = parse_turing_core_vocabulary(payload)

    with pytest.raises(
        TuringCoreVocabularyError,
        match="unknown or non-mapping framework targets",
    ):
        validate_turing_core_references(
            vocabulary,
            repository_root=REPOSITORY_ROOT,
        )


def test_rejects_mapping_target_as_framework_scope() -> None:
    payload = vocabulary_payload()
    payload["concepts"][0][
        "framework_scope_node_ids"
    ] = ["FW_STAKEHOLDER_STAKEHOLDERS"]
    vocabulary = parse_turing_core_vocabulary(payload)

    with pytest.raises(
        TuringCoreVocabularyError,
        match="unknown framework level nodes",
    ):
        validate_turing_core_references(
            vocabulary,
            repository_root=REPOSITORY_ROOT,
        )


def test_rejects_unknown_sysml_construct() -> None:
    payload = vocabulary_payload()
    payload["concepts"][0][
        "sysml_v2_representation_candidates"
    ] = [
        {
            "construct_id": "TN_999",
            "relation": "candidate_representation",
            "rationale": "Invalid test candidate.",
        }
    ]
    vocabulary = parse_turing_core_vocabulary(payload)

    with pytest.raises(
        TuringCoreVocabularyError,
        match="unknown or disallowed SysML v2 constructs",
    ):
        validate_turing_core_references(
            vocabulary,
            repository_root=REPOSITORY_ROOT,
        )


def test_rejects_restricted_sysml_construct() -> None:
    payload = vocabulary_payload()
    payload["concepts"][0][
        "sysml_v2_representation_candidates"
    ] = [
        {
            "construct_id": "TR_001",
            "relation": "candidate_representation",
            "rationale": "Restricted test candidate.",
        }
    ]
    vocabulary = parse_turing_core_vocabulary(payload)

    with pytest.raises(
        TuringCoreVocabularyError,
        match="unknown or disallowed SysML v2 constructs",
    ):
        validate_turing_core_references(
            vocabulary,
            repository_root=REPOSITORY_ROOT,
        )


def test_rejects_unknown_allowed_ontology_system() -> None:
    payload = vocabulary_payload()
    payload["authority"]["external_reference_systems"] = [
        "UNKNOWN_SYSTEM"
    ]
    payload["external_mapping_policy"][
        "allowed_reference_system_ids"
    ] = ["UNKNOWN_SYSTEM"]
    vocabulary = parse_turing_core_vocabulary(payload)

    with pytest.raises(
        TuringCoreVocabularyError,
        match="unknown ontology reference systems",
    ):
        validate_turing_core_references(
            vocabulary,
            repository_root=REPOSITORY_ROOT,
        )


def test_rejects_external_mapping_version_mismatch() -> None:
    payload = vocabulary_payload()
    payload["concepts"][0][
        "external_mapping_status"
    ] = "reviewed"
    payload["concepts"][0]["external_mappings"] = [
        external_mapping(
            reference_system_version="wrong-version"
        )
    ]
    vocabulary = parse_turing_core_vocabulary(payload)

    with pytest.raises(
        TuringCoreVocabularyError,
        match="but the registry provides",
    ):
        validate_turing_core_references(
            vocabulary,
            repository_root=REPOSITORY_ROOT,
        )


def test_rejects_external_mapping_to_disallowed_system() -> None:
    payload = vocabulary_payload()
    payload["concepts"][0][
        "external_mapping_status"
    ] = "reviewed"
    payload["concepts"][0]["external_mappings"] = [
        external_mapping(
            reference_system_id="UNREGISTERED_SYSTEM"
        )
    ]
    vocabulary = parse_turing_core_vocabulary(payload)

    with pytest.raises(
        TuringCoreVocabularyError,
        match="non-permitted reference system",
    ):
        validate_turing_core_references(
            vocabulary,
            repository_root=REPOSITORY_ROOT,
        )


def test_load_rejects_invalid_json(tmp_path: Path) -> None:
    path = (
        tmp_path
        / "context/semantics/turing_core_vocabulary.json"
    )
    path.parent.mkdir(parents=True)
    path.write_text("{invalid", encoding="utf-8")

    with pytest.raises(
        TuringCoreVocabularyError,
        match="invalid JSON",
    ):
        load_turing_core_vocabulary(
            repository_root=tmp_path,
            validate_references=False,
        )


def test_load_rejects_duplicate_json_key(
    tmp_path: Path,
) -> None:
    path = (
        tmp_path
        / "context/semantics/turing_core_vocabulary.json"
    )
    path.parent.mkdir(parents=True)
    path.write_text(
        (
            '{"schema_version":"1.0.0",'
            '"schema_version":"1.0.0"}'
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        TuringCoreVocabularyError,
        match="Duplicate JSON field",
    ):
        load_turing_core_vocabulary(
            repository_root=tmp_path,
            validate_references=False,
        )


def test_load_rejects_missing_file(tmp_path: Path) -> None:
    with pytest.raises(
        TuringCoreVocabularyError,
        match="Unable to read",
    ):
        load_turing_core_vocabulary(
            repository_root=tmp_path,
            validate_references=False,
        )


def test_load_rejects_repository_escape(
    tmp_path: Path,
) -> None:
    with pytest.raises(TuringCoreVocabularyError):
        load_turing_core_vocabulary(
            Path("../outside.json"),
            repository_root=tmp_path,
            validate_references=False,
        )