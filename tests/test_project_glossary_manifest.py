"""Tests for the strict Project Glossary JSON contract."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
import json

import pytest

from modules.project_glossary.errors import (
    AmbiguousAlternativeLabelError,
    DuplicatePreferredLabelError,
    ProjectConceptRevisionError,
    ProjectGlossaryValidationError,
)
from modules.project_glossary.manifest import (
    PROJECT_GLOSSARY_FILENAME,
    PROJECT_GLOSSARY_SCHEMA_VERSION,
    create_project_glossary,
    parse_project_glossary,
    project_glossary_from_json,
    project_glossary_to_dict,
    project_glossary_to_json,
    validate_project_glossary,
)
from modules.project_glossary.types import ProjectGlossary


PROJECT_ID = "318604"
TIMESTAMP = "2026-07-23T10:00:00Z"


def source_provenance() -> dict[str, object]:
    """Return one valid engineering-source provenance record."""

    return {
        "provenance_type": "engineering_source",
        "reference_id": "SRC-000001",
        "rationale": "The source segment contains the term.",
        "reference_system_id": None,
        "reference_version": None,
        "source_projection_id": "SP-000001",
        "segment_ids": ["SEG-000001"],
    }


def concept_payload(
    concept_id: str = "PC-000001",
    *,
    preferred_label: str = "Antrieb",
    alternative_labels: list[str] | None = None,
    lifecycle_status: str = "candidate",
) -> dict[str, object]:
    """Return one valid Project Concept payload."""

    alternatives = (
        []
        if alternative_labels is None
        else [
            {
                "language": "de",
                "text": label,
            }
            for label in alternative_labels
        ]
    )

    return {
        "project_concept_id": concept_id,
        "latest_revision": 1,
        "revisions": [
            {
                "revision": 1,
                "lifecycle_status": lifecycle_status,
                "preferred_labels": [
                    {
                        "language": "de",
                        "text": preferred_label,
                    }
                ],
                "alternative_labels": alternatives,
                "definitions": [
                    {
                        "language": "de",
                        "text": (
                            "A project-specific concept definition."
                        ),
                    }
                ],
                "broader_project_concept_ids": [],
                "related_project_concept_ids": [],
                "turing_core_mappings": [],
                "external_ontology_mappings": [],
                "provenance": [
                    source_provenance()
                ],
                "rationale": "Initial glossary candidate.",
                "created_at": TIMESTAMP,
            }
        ],
    }


def glossary_payload(
    *,
    concepts: list[dict[str, object]] | None = None,
    ambiguity_groups: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    """Return one valid Project Glossary payload."""

    return {
        "schema_version": PROJECT_GLOSSARY_SCHEMA_VERSION,
        "project_id": PROJECT_ID,
        "glossary_revision": 1,
        "default_language": "de",
        "created_at": TIMESTAMP,
        "updated_at": TIMESTAMP,
        "concepts": (
            []
            if concepts is None
            else concepts
        ),
        "ambiguity_groups": (
            []
            if ambiguity_groups is None
            else ambiguity_groups
        ),
    }


def ambiguity_group_payload(
    *,
    label: str = "Port",
) -> dict[str, object]:
    """Return one valid Ambiguity Group payload."""

    return {
        "ambiguity_group_id": "AG-000001",
        "label": label,
        "language": "de",
        "candidate_project_concept_ids": [
            "PC-000001",
            "PC-000002",
        ],
        "resolution_rule": "context_required",
        "rationale": "The project uses two context-specific meanings.",
        "created_at": TIMESTAMP,
    }


def two_accepted_ambiguous_concepts() -> list[
    dict[str, object]
]:
    """Return two accepted concepts sharing one alternative label."""

    return [
        concept_payload(
            "PC-000001",
            preferred_label="Netzwerkanschluss",
            alternative_labels=["Port"],
            lifecycle_status="accepted",
        ),
        concept_payload(
            "PC-000002",
            preferred_label="Software-Schnittstelle",
            alternative_labels=["PORT"],
            lifecycle_status="accepted",
        ),
    ]


def revision(
    concept: dict[str, object],
) -> dict[str, object]:
    """Return the first revision from a concept fixture."""

    revisions = concept["revisions"]
    assert isinstance(revisions, list)
    result = revisions[0]
    assert isinstance(result, dict)
    return result


def test_manifest_constants() -> None:
    assert PROJECT_GLOSSARY_SCHEMA_VERSION == "1.0.0"
    assert PROJECT_GLOSSARY_FILENAME == "project_glossary.json"


def test_create_empty_project_glossary() -> None:
    glossary = create_project_glossary(
        PROJECT_ID,
        default_language="de",
        timestamp=TIMESTAMP,
    )

    assert glossary == ProjectGlossary(
        schema_version="1.0.0",
        project_id=PROJECT_ID,
        glossary_revision=1,
        default_language="de",
        created_at=TIMESTAMP,
        updated_at=TIMESTAMP,
        concepts=(),
        ambiguity_groups=(),
    )


def test_create_rejects_invalid_project_id() -> None:
    with pytest.raises(ProjectGlossaryValidationError):
        create_project_glossary(
            "12345",
            default_language="de",
            timestamp=TIMESTAMP,
        )


def test_create_rejects_invalid_default_language() -> None:
    with pytest.raises(ProjectGlossaryValidationError):
        create_project_glossary(
            PROJECT_ID,
            default_language="DE",
            timestamp=TIMESTAMP,
        )


def test_empty_glossary_round_trip_is_deterministic() -> None:
    glossary = create_project_glossary(
        PROJECT_ID,
        default_language="de",
        timestamp=TIMESTAMP,
    )

    first = project_glossary_to_json(glossary)
    second = project_glossary_to_json(glossary)
    reloaded = project_glossary_from_json(
        first,
        expected_project_id=PROJECT_ID,
    )

    assert first == second
    assert first.endswith("\n")
    assert reloaded == glossary


def test_populated_glossary_round_trip() -> None:
    parsed = parse_project_glossary(
        glossary_payload(
            concepts=[concept_payload()]
        )
    )
    serialized = project_glossary_to_json(parsed)

    assert project_glossary_from_json(serialized) == parsed
    assert project_glossary_to_dict(parsed) == json.loads(
        serialized
    )


def test_validate_project_glossary_returns_none() -> None:
    glossary = parse_project_glossary(
        glossary_payload(
            concepts=[concept_payload()]
        )
    )

    assert validate_project_glossary(
        glossary,
        expected_project_id=PROJECT_ID,
    ) is None


def test_validate_rejects_wrong_instance() -> None:
    with pytest.raises(ProjectGlossaryValidationError):
        validate_project_glossary("not a glossary")  # type: ignore[arg-type]


def test_serializer_rejects_invalid_nested_instance() -> None:
    glossary = create_project_glossary(
        PROJECT_ID,
        default_language="de",
        timestamp=TIMESTAMP,
    )
    invalid = replace(
        glossary,
        concepts=("not a concept",),  # type: ignore[arg-type]
    )

    with pytest.raises(ProjectGlossaryValidationError):
        project_glossary_to_json(invalid)


@pytest.mark.parametrize(
    "text",
    [
        "",
        "{invalid",
        "[]",
        "null",
    ],
)
def test_from_json_rejects_invalid_documents(
    text: str,
) -> None:
    with pytest.raises(ProjectGlossaryValidationError):
        project_glossary_from_json(text)


def test_from_json_requires_string() -> None:
    with pytest.raises(ProjectGlossaryValidationError):
        project_glossary_from_json(42)  # type: ignore[arg-type]


def test_from_json_rejects_duplicate_fields() -> None:
    text = json.dumps(glossary_payload())
    duplicate = text.replace(
        '"schema_version": "1.0.0"',
        (
            '"schema_version": "1.0.0", '
            '"schema_version": "1.0.0"'
        ),
        1,
    )

    with pytest.raises(
        ProjectGlossaryValidationError,
        match="Duplicate JSON field",
    ):
        project_glossary_from_json(duplicate)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("schema_version", "2.0.0"),
        ("project_id", "12345"),
        ("project_id", 318604),
        ("glossary_revision", 0),
        ("glossary_revision", True),
        ("glossary_revision", "1"),
        ("default_language", "DE"),
        ("default_language", "de-DE"),
        ("default_language", 1),
        ("created_at", "2026-07-23"),
        ("created_at", "2026-07-23T10:00:00+00:00"),
        ("updated_at", "invalid"),
        ("concepts", {}),
        ("ambiguity_groups", {}),
    ],
)
def test_root_field_validation(
    field: str,
    value: object,
) -> None:
    payload = glossary_payload()
    payload[field] = value

    with pytest.raises(ProjectGlossaryValidationError):
        parse_project_glossary(payload)


@pytest.mark.parametrize(
    "field",
    sorted(
        {
            "schema_version",
            "project_id",
            "glossary_revision",
            "default_language",
            "created_at",
            "updated_at",
            "concepts",
            "ambiguity_groups",
        }
    ),
)
def test_root_rejects_missing_fields(field: str) -> None:
    payload = glossary_payload()
    del payload[field]

    with pytest.raises(ProjectGlossaryValidationError):
        parse_project_glossary(payload)


def test_root_rejects_unknown_field() -> None:
    payload = glossary_payload()
    payload["unexpected"] = True

    with pytest.raises(
        ProjectGlossaryValidationError,
        match="unknown unexpected",
    ):
        parse_project_glossary(payload)


def test_expected_project_id_must_be_valid() -> None:
    with pytest.raises(ProjectGlossaryValidationError):
        parse_project_glossary(
            glossary_payload(),
            expected_project_id="invalid",
        )


def test_expected_project_id_must_match() -> None:
    with pytest.raises(
        ProjectGlossaryValidationError,
        match="does not match",
    ):
        parse_project_glossary(
            glossary_payload(),
            expected_project_id="318605",
        )


def test_updated_at_must_not_precede_created_at() -> None:
    payload = glossary_payload()
    payload["updated_at"] = "2026-07-23T09:59:59Z"

    with pytest.raises(ProjectGlossaryValidationError):
        parse_project_glossary(payload)


def test_fractional_utc_timestamp_is_supported() -> None:
    payload = glossary_payload()
    payload["created_at"] = "2026-07-23T10:00:00.123456Z"
    payload["updated_at"] = "2026-07-23T10:00:00.123456Z"

    result = parse_project_glossary(payload)

    assert result.created_at.endswith(".123456Z")


@pytest.mark.parametrize(
    "concept_id",
    [
        "PC-000000",
        "PC-1",
        "PC-1000000",
        "pc-000001",
        1,
    ],
)
def test_rejects_invalid_project_concept_id(
    concept_id: object,
) -> None:
    concept = concept_payload()
    concept["project_concept_id"] = concept_id

    with pytest.raises(ProjectGlossaryValidationError):
        parse_project_glossary(
            glossary_payload(concepts=[concept])
        )


def test_rejects_duplicate_project_concept_ids() -> None:
    concepts = [
        concept_payload("PC-000001"),
        concept_payload("PC-000001"),
    ]

    with pytest.raises(ProjectGlossaryValidationError):
        parse_project_glossary(
            glossary_payload(concepts=concepts)
        )


def test_concepts_must_be_sorted() -> None:
    concepts = [
        concept_payload("PC-000002"),
        concept_payload("PC-000001"),
    ]

    with pytest.raises(
        ProjectGlossaryValidationError,
        match="ordered",
    ):
        parse_project_glossary(
            glossary_payload(concepts=concepts)
        )


@pytest.mark.parametrize(
    "latest_revision",
    [
        0,
        True,
        "1",
    ],
)
def test_latest_revision_must_be_positive_integer(
    latest_revision: object,
) -> None:
    concept = concept_payload()
    concept["latest_revision"] = latest_revision

    with pytest.raises(ProjectGlossaryValidationError):
        parse_project_glossary(
            glossary_payload(concepts=[concept])
        )


def test_concept_requires_at_least_one_revision() -> None:
    concept = concept_payload()
    concept["revisions"] = []

    with pytest.raises(ProjectConceptRevisionError):
        parse_project_glossary(
            glossary_payload(concepts=[concept])
        )


@pytest.mark.parametrize(
    "revision_numbers",
    [
        [2],
        [1, 3],
        [2, 1],
    ],
)
def test_revisions_must_be_ordered_and_contiguous(
    revision_numbers: list[int],
) -> None:
    concept = concept_payload()
    template = revision(concept)
    revisions = []

    for number in revision_numbers:
        item = deepcopy(template)
        item["revision"] = number
        revisions.append(item)

    concept["latest_revision"] = max(revision_numbers)
    concept["revisions"] = revisions

    with pytest.raises(ProjectConceptRevisionError):
        parse_project_glossary(
            glossary_payload(concepts=[concept])
        )


@pytest.mark.parametrize(
    "status",
    [
        "",
        "approved",
        "Accepted",
        1,
    ],
)
def test_rejects_invalid_lifecycle_status(
    status: object,
) -> None:
    concept = concept_payload()
    revision(concept)["lifecycle_status"] = status

    with pytest.raises(ProjectGlossaryValidationError):
        parse_project_glossary(
            glossary_payload(concepts=[concept])
        )


@pytest.mark.parametrize(
    "field",
    [
        "preferred_labels",
        "definitions",
    ],
)
def test_required_localized_collections_must_not_be_empty(
    field: str,
) -> None:
    concept = concept_payload()
    revision(concept)[field] = []

    with pytest.raises(ProjectGlossaryValidationError):
        parse_project_glossary(
            glossary_payload(concepts=[concept])
        )


@pytest.mark.parametrize(
    "field",
    [
        "preferred_labels",
        "definitions",
    ],
)
def test_default_language_is_required(
    field: str,
) -> None:
    concept = concept_payload()
    revision(concept)[field] = [
        {
            "language": "en",
            "text": "Drive",
        }
    ]

    with pytest.raises(
        ProjectGlossaryValidationError,
        match="default language",
    ):
        parse_project_glossary(
            glossary_payload(concepts=[concept])
        )


@pytest.mark.parametrize(
    "field",
    [
        "preferred_labels",
        "definitions",
    ],
)
def test_one_entry_per_language_for_primary_texts(
    field: str,
) -> None:
    concept = concept_payload()
    revision(concept)[field] = [
        {
            "language": "de",
            "text": "Erster Text",
        },
        {
            "language": "de",
            "text": "Zweiter Text",
        },
    ]

    with pytest.raises(ProjectGlossaryValidationError):
        parse_project_glossary(
            glossary_payload(concepts=[concept])
        )


@pytest.mark.parametrize(
    "value",
    [
        "",
        " ",
        " Antrieb",
        "Antrieb ",
        42,
    ],
)
def test_localized_text_must_be_stored_cleanly(
    value: object,
) -> None:
    concept = concept_payload()
    preferred_labels = revision(
        concept
    )["preferred_labels"]
    assert isinstance(preferred_labels, list)
    preferred_labels[0]["text"] = value

    with pytest.raises(ProjectGlossaryValidationError):
        parse_project_glossary(
            glossary_payload(concepts=[concept])
        )


def test_alternative_labels_allow_multiple_per_language() -> None:
    concept = concept_payload(
        alternative_labels=[
            "Antriebssystem",
            "Drive Unit",
        ]
    )

    result = parse_project_glossary(
        glossary_payload(concepts=[concept])
    )

    assert len(
        result.concepts[0]
        .revisions[0]
        .alternative_labels
    ) == 2


def test_alternative_labels_reject_normalized_duplicates() -> None:
    concept = concept_payload(
        alternative_labels=[
            "Straße",
            "STRASSE",
        ]
    )

    with pytest.raises(
        ProjectGlossaryValidationError,
        match="duplicate normalized",
    ):
        parse_project_glossary(
            glossary_payload(concepts=[concept])
        )


def test_alternative_must_not_repeat_preferred_label() -> None:
    concept = concept_payload(
        preferred_label="Antrieb",
        alternative_labels=["ANTRIEB"],
    )

    with pytest.raises(
        ProjectGlossaryValidationError,
        match="preferred label",
    ):
        parse_project_glossary(
            glossary_payload(concepts=[concept])
        )


def test_inner_whitespace_is_not_collapsed() -> None:
    concept = concept_payload(
        preferred_label="A  B",
        alternative_labels=["A B"],
    )

    parse_project_glossary(
        glossary_payload(concepts=[concept])
    )


def test_fullwidth_and_ascii_labels_compare_equally() -> None:
    concept = concept_payload(
        preferred_label="Ｐｏｒｔ",
        alternative_labels=["port"],
    )

    with pytest.raises(ProjectGlossaryValidationError):
        parse_project_glossary(
            glossary_payload(concepts=[concept])
        )


@pytest.mark.parametrize(
    "field",
    [
        "broader_project_concept_ids",
        "related_project_concept_ids",
    ],
)
def test_concept_must_not_reference_itself(
    field: str,
) -> None:
    concept = concept_payload()
    revision(concept)[field] = ["PC-000001"]

    with pytest.raises(ProjectGlossaryValidationError):
        parse_project_glossary(
            glossary_payload(concepts=[concept])
        )


def test_same_concept_cannot_be_broader_and_related() -> None:
    first = concept_payload("PC-000001")
    second = concept_payload("PC-000002")
    revision(first)["broader_project_concept_ids"] = [
        "PC-000002"
    ]
    revision(first)["related_project_concept_ids"] = [
        "PC-000002"
    ]

    with pytest.raises(ProjectGlossaryValidationError):
        parse_project_glossary(
            glossary_payload(
                concepts=[first, second]
            )
        )


def test_rejects_unknown_concept_relation_target() -> None:
    concept = concept_payload()
    revision(concept)["related_project_concept_ids"] = [
        "PC-000002"
    ]

    with pytest.raises(
        ProjectGlossaryValidationError,
        match="unknown",
    ):
        parse_project_glossary(
            glossary_payload(concepts=[concept])
        )


def test_relation_targets_must_be_sorted_and_unique() -> None:
    first = concept_payload("PC-000001")
    second = concept_payload("PC-000002")
    third = concept_payload("PC-000003")
    revision(first)["related_project_concept_ids"] = [
        "PC-000003",
        "PC-000002",
    ]

    with pytest.raises(
        ProjectGlossaryValidationError,
        match="ordered",
    ):
        parse_project_glossary(
            glossary_payload(
                concepts=[first, second, third]
            )
        )


def test_revision_requires_provenance() -> None:
    concept = concept_payload()
    revision(concept)["provenance"] = []

    with pytest.raises(ProjectGlossaryValidationError):
        parse_project_glossary(
            glossary_payload(concepts=[concept])
        )


@pytest.mark.parametrize(
    "provenance",
    [
        {
            "provenance_type": "engineering_source",
            "reference_id": "SRC-000001",
            "rationale": "Engineering evidence.",
            "reference_system_id": None,
            "reference_version": None,
            "source_projection_id": "SP-000001",
            "segment_ids": ["SEG-000001"],
        },
        {
            "provenance_type": "context_only_source",
            "reference_id": "SRC-000001",
            "rationale": "Context evidence.",
            "reference_system_id": None,
            "reference_version": None,
            "source_projection_id": "SP-000001",
            "segment_ids": ["SEG-000001"],
        },
        {
            "provenance_type": "terminology_decision",
            "reference_id": "TD-000001",
            "rationale": "Human terminology decision.",
            "reference_system_id": None,
            "reference_version": None,
            "source_projection_id": None,
            "segment_ids": [],
        },
        {
            "provenance_type": "external_reference",
            "reference_id": "https://example.org/concept",
            "rationale": "External semantic reference.",
            "reference_system_id": "IOF_CORE_202602",
            "reference_version": "202602",
            "source_projection_id": None,
            "segment_ids": [],
        },
        {
            "provenance_type": "turing_core",
            "reference_id": "TC-000010",
            "rationale": "Turing Core bridge.",
            "reference_system_id": (
                "TURING_CORE_VOCABULARY"
            ),
            "reference_version": "1.0.0",
            "source_projection_id": None,
            "segment_ids": [],
        },
    ],
)
def test_accepts_typed_provenance(
    provenance: dict[str, object],
) -> None:
    concept = concept_payload()
    revision(concept)["provenance"] = [provenance]

    result = parse_project_glossary(
        glossary_payload(concepts=[concept])
    )

    assert (
        result.concepts[0]
        .revisions[0]
        .provenance[0]
        .provenance_type
        == provenance["provenance_type"]
    )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("reference_id", "SRC-000000"),
        ("source_projection_id", None),
        ("source_projection_id", "SP-000000"),
        ("segment_ids", []),
        ("segment_ids", ["SEG-000000"]),
        (
            "segment_ids",
            ["SEG-000001", "SEG-000001"],
        ),
        ("reference_system_id", "BFO_2020"),
        ("reference_version", "2020"),
    ],
)
def test_source_provenance_contract(
    field: str,
    value: object,
) -> None:
    concept = concept_payload()
    provenance = source_provenance()
    provenance[field] = value
    revision(concept)["provenance"] = [provenance]

    with pytest.raises(ProjectGlossaryValidationError):
        parse_project_glossary(
            glossary_payload(concepts=[concept])
        )


def test_terminology_decision_requires_valid_td_id() -> None:
    concept = concept_payload()
    provenance = {
        "provenance_type": "terminology_decision",
        "reference_id": "TD-000000",
        "rationale": "Human terminology decision.",
        "reference_system_id": None,
        "reference_version": None,
        "source_projection_id": None,
        "segment_ids": [],
    }
    revision(concept)["provenance"] = [provenance]

    with pytest.raises(ProjectGlossaryValidationError):
        parse_project_glossary(
            glossary_payload(concepts=[concept])
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("reference_id", "not-an-iri"),
        ("reference_system_id", None),
        ("reference_system_id", "iof"),
        ("reference_version", None),
        ("source_projection_id", "SP-000001"),
        ("segment_ids", ["SEG-000001"]),
    ],
)
def test_external_reference_provenance_contract(
    field: str,
    value: object,
) -> None:
    concept = concept_payload()
    provenance = {
        "provenance_type": "external_reference",
        "reference_id": "https://example.org/concept",
        "rationale": "External semantic reference.",
        "reference_system_id": "IOF_CORE_202602",
        "reference_version": "202602",
        "source_projection_id": None,
        "segment_ids": [],
    }
    provenance[field] = value
    revision(concept)["provenance"] = [provenance]

    with pytest.raises(ProjectGlossaryValidationError):
        parse_project_glossary(
            glossary_payload(concepts=[concept])
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("reference_id", "TC-000000"),
        ("reference_system_id", "TURING_CORE"),
        ("reference_version", "1"),
        ("source_projection_id", "SP-000001"),
        ("segment_ids", ["SEG-000001"]),
    ],
)
def test_turing_core_provenance_contract(
    field: str,
    value: object,
) -> None:
    concept = concept_payload()
    provenance = {
        "provenance_type": "turing_core",
        "reference_id": "TC-000010",
        "rationale": "Turing Core bridge.",
        "reference_system_id": (
            "TURING_CORE_VOCABULARY"
        ),
        "reference_version": "1.0.0",
        "source_projection_id": None,
        "segment_ids": [],
    }
    provenance[field] = value
    revision(concept)["provenance"] = [provenance]

    with pytest.raises(ProjectGlossaryValidationError):
        parse_project_glossary(
            glossary_payload(concepts=[concept])
        )


def test_accepts_turing_core_mapping() -> None:
    concept = concept_payload()
    revision(concept)["turing_core_mappings"] = [
        {
            "vocabulary_id": "TURING_CORE_VOCABULARY",
            "vocabulary_version": "1.0.0",
            "turing_core_concept_id": "TC-000010",
            "relation": "narrower_than",
            "rationale": "Candidate semantic bridge.",
        }
    ]

    result = parse_project_glossary(
        glossary_payload(concepts=[concept])
    )

    assert (
        result.concepts[0]
        .revisions[0]
        .turing_core_mappings[0]
        .turing_core_concept_id
        == "TC-000010"
    )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("vocabulary_id", "OTHER"),
        ("vocabulary_version", "1"),
        ("turing_core_concept_id", "TC-000000"),
        ("relation", "same_as"),
        ("rationale", ""),
    ],
)
def test_turing_core_mapping_contract(
    field: str,
    value: object,
) -> None:
    concept = concept_payload()
    mapping = {
        "vocabulary_id": "TURING_CORE_VOCABULARY",
        "vocabulary_version": "1.0.0",
        "turing_core_concept_id": "TC-000010",
        "relation": "narrower_than",
        "rationale": "Candidate semantic bridge.",
    }
    mapping[field] = value
    revision(concept)["turing_core_mappings"] = [
        mapping
    ]

    with pytest.raises(ProjectGlossaryValidationError):
        parse_project_glossary(
            glossary_payload(concepts=[concept])
        )


def test_accepts_external_mapping_release_version() -> None:
    concept = concept_payload()
    revision(concept)["external_ontology_mappings"] = [
        {
            "reference_system_id": "IOF_CORE_202602",
            "reference_system_version": "202602",
            "reference_concept_iri": (
                "https://example.org/concept"
            ),
            "relation": "related_to",
            "rationale": "Candidate external mapping.",
        }
    ]

    result = parse_project_glossary(
        glossary_payload(concepts=[concept])
    )

    assert (
        result.concepts[0]
        .revisions[0]
        .external_ontology_mappings[0]
        .reference_system_version
        == "202602"
    )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("reference_system_id", "iof"),
        ("reference_system_version", ""),
        ("reference_concept_iri", "not-an-iri"),
        ("relation", "same_as"),
        ("rationale", ""),
    ],
)
def test_external_mapping_contract(
    field: str,
    value: object,
) -> None:
    concept = concept_payload()
    mapping = {
        "reference_system_id": "IOF_CORE_202602",
        "reference_system_version": "202602",
        "reference_concept_iri": (
            "https://example.org/concept"
        ),
        "relation": "related_to",
        "rationale": "Candidate external mapping.",
    }
    mapping[field] = value
    revision(concept)["external_ontology_mappings"] = [
        mapping
    ]

    with pytest.raises(ProjectGlossaryValidationError):
        parse_project_glossary(
            glossary_payload(concepts=[concept])
        )


def test_candidate_label_conflicts_are_reviewable() -> None:
    concepts = [
        concept_payload(
            "PC-000001",
            preferred_label="Port",
        ),
        concept_payload(
            "PC-000002",
            preferred_label="PORT",
        ),
    ]

    parse_project_glossary(
        glossary_payload(concepts=concepts)
    )


def test_accepted_preferred_labels_must_be_unique() -> None:
    concepts = [
        concept_payload(
            "PC-000001",
            preferred_label="Port",
            lifecycle_status="accepted",
        ),
        concept_payload(
            "PC-000002",
            preferred_label="PORT",
            lifecycle_status="accepted",
        ),
    ]

    with pytest.raises(DuplicatePreferredLabelError):
        parse_project_glossary(
            glossary_payload(
                concepts=concepts,
                ambiguity_groups=[
                    ambiguity_group_payload()
                ],
            )
        )


def test_accepted_alternative_ambiguity_requires_group() -> None:
    with pytest.raises(AmbiguousAlternativeLabelError):
        parse_project_glossary(
            glossary_payload(
                concepts=two_accepted_ambiguous_concepts()
            )
        )


def test_accepted_alternative_ambiguity_with_group() -> None:
    result = parse_project_glossary(
        glossary_payload(
            concepts=two_accepted_ambiguous_concepts(),
            ambiguity_groups=[
                ambiguity_group_payload()
            ],
        )
    )

    assert (
        result.ambiguity_groups[0]
        .resolution_rule
        == "context_required"
    )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("ambiguity_group_id", "AG-000000"),
        ("label", ""),
        ("language", "DE"),
        (
            "candidate_project_concept_ids",
            ["PC-000001"],
        ),
        (
            "candidate_project_concept_ids",
            ["PC-000001", "PC-000001"],
        ),
        ("resolution_rule", "automatic"),
        ("rationale", ""),
        ("created_at", "invalid"),
    ],
)
def test_ambiguity_group_contract(
    field: str,
    value: object,
) -> None:
    group = ambiguity_group_payload()
    group[field] = value

    with pytest.raises(ProjectGlossaryValidationError):
        parse_project_glossary(
            glossary_payload(
                concepts=two_accepted_ambiguous_concepts(),
                ambiguity_groups=[group],
            )
        )


def test_ambiguity_group_rejects_unknown_candidate() -> None:
    group = ambiguity_group_payload()
    group["candidate_project_concept_ids"] = [
        "PC-000001",
        "PC-000003",
    ]

    with pytest.raises(
        ProjectGlossaryValidationError,
        match="unknown",
    ):
        parse_project_glossary(
            glossary_payload(
                concepts=two_accepted_ambiguous_concepts(),
                ambiguity_groups=[group],
            )
        )


def test_ambiguity_group_label_must_match_candidates() -> None:
    group = ambiguity_group_payload(
        label="Unrelated label"
    )

    with pytest.raises(AmbiguousAlternativeLabelError):
        parse_project_glossary(
            glossary_payload(
                concepts=two_accepted_ambiguous_concepts(),
                ambiguity_groups=[group],
            )
        )


def test_duplicate_ambiguity_group_ids_are_rejected() -> None:
    first = ambiguity_group_payload()
    second = ambiguity_group_payload()

    with pytest.raises(ProjectGlossaryValidationError):
        parse_project_glossary(
            glossary_payload(
                concepts=two_accepted_ambiguous_concepts(),
                ambiguity_groups=[first, second],
            )
        )


def test_duplicate_normalized_ambiguity_group_key_rejected() -> None:
    first = ambiguity_group_payload(label="Port")
    second = ambiguity_group_payload(label="PORT")
    second["ambiguity_group_id"] = "AG-000002"

    with pytest.raises(ProjectGlossaryValidationError):
        parse_project_glossary(
            glossary_payload(
                concepts=two_accepted_ambiguous_concepts(),
                ambiguity_groups=[first, second],
            )
        )


def test_ambiguity_groups_must_be_sorted() -> None:
    concepts = [
        concept_payload(
            "PC-000001",
            preferred_label="First A",
            alternative_labels=["Alpha"],
            lifecycle_status="accepted",
        ),
        concept_payload(
            "PC-000002",
            preferred_label="First B",
            alternative_labels=["Alpha"],
            lifecycle_status="accepted",
        ),
        concept_payload(
            "PC-000003",
            preferred_label="Second A",
            alternative_labels=["Beta"],
            lifecycle_status="accepted",
        ),
        concept_payload(
            "PC-000004",
            preferred_label="Second B",
            alternative_labels=["Beta"],
            lifecycle_status="accepted",
        ),
    ]
    alpha = {
        **ambiguity_group_payload(label="Alpha"),
        "ambiguity_group_id": "AG-000001",
    }
    beta = {
        **ambiguity_group_payload(label="Beta"),
        "ambiguity_group_id": "AG-000002",
        "candidate_project_concept_ids": [
            "PC-000003",
            "PC-000004",
        ],
    }

    with pytest.raises(
        ProjectGlossaryValidationError,
        match="ordered",
    ):
        parse_project_glossary(
            glossary_payload(
                concepts=concepts,
                ambiguity_groups=[beta, alpha],
            )
        )


def test_deprecated_latest_revision_removes_accepted_labels() -> None:
    concepts = [
        concept_payload(
            "PC-000001",
            preferred_label="Port",
            lifecycle_status="accepted",
        ),
        concept_payload(
            "PC-000002",
            preferred_label="PORT",
            lifecycle_status="accepted",
        ),
    ]

    for concept in concepts:
        first_revision = revision(concept)
        deprecated_revision = deepcopy(first_revision)
        deprecated_revision["revision"] = 2
        deprecated_revision["lifecycle_status"] = "deprecated"
        concept["latest_revision"] = 2
        concept["revisions"] = [
            first_revision,
            deprecated_revision,
        ]

    parse_project_glossary(
        glossary_payload(concepts=concepts)
    )


def test_new_candidate_preserves_previous_accepted_authority() -> None:
    first = concept_payload(
        "PC-000001",
        preferred_label="Port",
        lifecycle_status="accepted",
    )
    second = concept_payload(
        "PC-000002",
        preferred_label="PORT",
        lifecycle_status="accepted",
    )
    first_revision = revision(first)
    candidate_revision = deepcopy(first_revision)
    candidate_revision["revision"] = 2
    candidate_revision["lifecycle_status"] = "candidate"
    candidate_revision["preferred_labels"] = [
        {
            "language": "de",
            "text": "New candidate",
        }
    ]
    first["latest_revision"] = 2
    first["revisions"] = [
        first_revision,
        candidate_revision,
    ]

    with pytest.raises(DuplicatePreferredLabelError):
        parse_project_glossary(
            glossary_payload(
                concepts=[first, second]
            )
        )