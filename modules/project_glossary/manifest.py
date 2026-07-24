"""Validate, parse and serialize Project Glossary artifacts.

This module owns the immutable JSON contract and its cross-reference
validation. Filesystem persistence, identifier allocation and glossary
mutation belong to the Project Glossary repository implemented in P4/16.
"""

from __future__ import annotations

from datetime import datetime
import json
import re
from typing import Any
from urllib.parse import urlparse

from modules.project_sources.identifiers import validate_source_id
from modules.project_workspace.identifiers import is_valid_project_id
from modules.source_projection.identifiers import (
    validate_segment_id,
    validate_source_projection_id,
)

from .errors import (
    AmbiguousAlternativeLabelError,
    DuplicatePreferredLabelError,
    ProjectConceptRevisionError,
    ProjectGlossaryValidationError,
)
from .identifiers import (
    is_valid_ambiguity_group_id,
    is_valid_project_concept_id,
    is_valid_terminology_decision_id,
)
from .normalization import (
    localized_label_comparison_key,
    require_language_code,
    require_stored_glossary_text,
)
from .types import (
    AMBIGUITY_RESOLUTION_RULES,
    PROJECT_CONCEPT_LIFECYCLE_STATES,
    PROJECT_CONCEPT_MAPPING_RELATIONS,
    PROJECT_CONCEPT_PROVENANCE_TYPES,
    AmbiguityGroup,
    LocalizedGlossaryText,
    ProjectConcept,
    ProjectConceptProvenance,
    ProjectConceptRevision,
    ProjectExternalOntologyMapping,
    ProjectGlossary,
    TuringCoreConceptMapping,
)


PROJECT_GLOSSARY_SCHEMA_VERSION = "1.0.0"
PROJECT_GLOSSARY_FILENAME = "project_glossary.json"

TURING_CORE_VOCABULARY_ID = "TURING_CORE_VOCABULARY"

_SEMANTIC_VERSION_PATTERN = re.compile(
    r"^[0-9]+\.[0-9]+\.[0-9]+$"
)
_UTC_TIMESTAMP_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T"
    r"\d{2}:\d{2}:\d{2}"
    r"(?:\.\d+)?Z$"
)
_TURING_CORE_CONCEPT_ID_PATTERN = re.compile(
    r"^TC-[0-9]{6}$"
)
_REFERENCE_SYSTEM_ID_PATTERN = re.compile(
    r"^[A-Z][A-Z0-9_]*$"
)

_GLOSSARY_FIELDS = frozenset(
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
)
_PROJECT_CONCEPT_FIELDS = frozenset(
    {
        "project_concept_id",
        "latest_revision",
        "revisions",
    }
)
_REVISION_FIELDS = frozenset(
    {
        "revision",
        "lifecycle_status",
        "preferred_labels",
        "alternative_labels",
        "definitions",
        "broader_project_concept_ids",
        "related_project_concept_ids",
        "turing_core_mappings",
        "external_ontology_mappings",
        "provenance",
        "rationale",
        "created_at",
    }
)
_LOCALIZED_TEXT_FIELDS = frozenset(
    {
        "language",
        "text",
    }
)
_PROVENANCE_FIELDS = frozenset(
    {
        "provenance_type",
        "reference_id",
        "rationale",
        "reference_system_id",
        "reference_version",
        "source_projection_id",
        "segment_ids",
    }
)
_TURING_CORE_MAPPING_FIELDS = frozenset(
    {
        "vocabulary_id",
        "vocabulary_version",
        "turing_core_concept_id",
        "relation",
        "rationale",
    }
)
_EXTERNAL_MAPPING_FIELDS = frozenset(
    {
        "reference_system_id",
        "reference_system_version",
        "reference_concept_iri",
        "relation",
        "rationale",
    }
)
_AMBIGUITY_GROUP_FIELDS = frozenset(
    {
        "ambiguity_group_id",
        "label",
        "language",
        "candidate_project_concept_ids",
        "resolution_rule",
        "rationale",
        "created_at",
    }
)


def create_project_glossary(
    project_id: str,
    *,
    default_language: str,
    timestamp: str,
) -> ProjectGlossary:
    """Create an empty revision-one Project Glossary."""

    return parse_project_glossary(
        {
            "schema_version": PROJECT_GLOSSARY_SCHEMA_VERSION,
            "project_id": project_id,
            "glossary_revision": 1,
            "default_language": default_language,
            "created_at": timestamp,
            "updated_at": timestamp,
            "concepts": [],
            "ambiguity_groups": [],
        },
        expected_project_id=project_id,
    )


def parse_project_glossary(
    payload: Any,
    *,
    expected_project_id: str | None = None,
) -> ProjectGlossary:
    """Parse and validate one Project Glossary payload."""

    glossary_object = _require_exact_object(
        payload,
        _GLOSSARY_FIELDS,
        "Project Glossary",
    )

    schema_version = glossary_object["schema_version"]

    if schema_version != PROJECT_GLOSSARY_SCHEMA_VERSION:
        raise ProjectGlossaryValidationError(
            "Unsupported Project Glossary schema_version: "
            f"{schema_version!r}."
        )

    project_id = _require_project_id(
        glossary_object["project_id"],
        "project_id",
    )

    if expected_project_id is not None:
        validated_expected_project_id = _require_project_id(
            expected_project_id,
            "expected_project_id",
        )

        if project_id != validated_expected_project_id:
            raise ProjectGlossaryValidationError(
                "Project Glossary project_id does not match its "
                f"project directory: {project_id!r} != "
                f"{validated_expected_project_id!r}."
            )

    glossary_revision = _require_positive_integer(
        glossary_object["glossary_revision"],
        "glossary_revision",
    )
    default_language = require_language_code(
        glossary_object["default_language"],
        "default_language",
    )
    created_at, created_datetime = _require_utc_timestamp(
        glossary_object["created_at"],
        "created_at",
    )
    updated_at, updated_datetime = _require_utc_timestamp(
        glossary_object["updated_at"],
        "updated_at",
    )

    if updated_datetime < created_datetime:
        raise ProjectGlossaryValidationError(
            "updated_at must not be earlier than created_at."
        )

    concepts = tuple(
        _parse_project_concept(
            value,
            default_language=default_language,
            label=f"concepts[{index}]",
        )
        for index, value in enumerate(
            _require_list(
                glossary_object["concepts"],
                "concepts",
            )
        )
    )
    ambiguity_groups = tuple(
        _parse_ambiguity_group(
            value,
            label=f"ambiguity_groups[{index}]",
        )
        for index, value in enumerate(
            _require_list(
                glossary_object["ambiguity_groups"],
                "ambiguity_groups",
            )
        )
    )

    glossary = ProjectGlossary(
        schema_version=schema_version,
        project_id=project_id,
        glossary_revision=glossary_revision,
        default_language=default_language,
        created_at=created_at,
        updated_at=updated_at,
        concepts=concepts,
        ambiguity_groups=ambiguity_groups,
    )

    _validate_glossary_cross_references(glossary)
    return glossary


def project_glossary_from_json(
    text: str,
    *,
    expected_project_id: str | None = None,
) -> ProjectGlossary:
    """Parse and validate Project Glossary JSON text."""

    if not isinstance(text, str):
        raise ProjectGlossaryValidationError(
            "Project Glossary JSON input must be a string."
        )

    try:
        payload = json.loads(
            text,
            object_pairs_hook=_object_without_duplicate_keys,
        )
    except ProjectGlossaryValidationError:
        raise
    except json.JSONDecodeError as exc:
        raise ProjectGlossaryValidationError(
            f"Project Glossary contains invalid JSON: {exc}."
        ) from exc

    return parse_project_glossary(
        payload,
        expected_project_id=expected_project_id,
    )


def validate_project_glossary(
    glossary: ProjectGlossary,
    *,
    expected_project_id: str | None = None,
) -> None:
    """Validate an immutable ProjectGlossary instance."""

    parse_project_glossary(
        _project_glossary_payload(glossary),
        expected_project_id=expected_project_id,
    )


def project_glossary_to_dict(
    glossary: ProjectGlossary,
) -> dict[str, Any]:
    """Return a validated JSON-compatible glossary dictionary."""

    payload = _project_glossary_payload(glossary)
    parse_project_glossary(payload)
    return payload


def project_glossary_to_json(
    glossary: ProjectGlossary,
) -> str:
    """Serialize a Project Glossary deterministically."""

    return json.dumps(
        project_glossary_to_dict(glossary),
        ensure_ascii=False,
        indent=2,
    ) + "\n"


def _parse_project_concept(
    value: Any,
    *,
    default_language: str,
    label: str,
) -> ProjectConcept:
    concept_object = _require_exact_object(
        value,
        _PROJECT_CONCEPT_FIELDS,
        label,
    )
    project_concept_id = _require_project_concept_id(
        concept_object["project_concept_id"],
        f"{label}.project_concept_id",
    )
    latest_revision = _require_positive_integer(
        concept_object["latest_revision"],
        f"{label}.latest_revision",
    )
    revision_values = _require_list(
        concept_object["revisions"],
        f"{label}.revisions",
    )

    if not revision_values:
        raise ProjectConceptRevisionError(
            f"{label}.revisions must not be empty."
        )

    revisions = tuple(
        _parse_project_concept_revision(
            revision_value,
            project_concept_id=project_concept_id,
            default_language=default_language,
            label=f"{label}.revisions[{index}]",
        )
        for index, revision_value in enumerate(revision_values)
    )
    revision_numbers = tuple(
        revision.revision
        for revision in revisions
    )
    expected_numbers = tuple(
        range(1, latest_revision + 1)
    )

    if revision_numbers != expected_numbers:
        raise ProjectConceptRevisionError(
            f"{label}.revisions must be ordered, contiguous and "
            f"cover 1 through latest_revision {latest_revision}."
        )

    return ProjectConcept(
        project_concept_id=project_concept_id,
        latest_revision=latest_revision,
        revisions=revisions,
    )


def _parse_project_concept_revision(
    value: Any,
    *,
    project_concept_id: str,
    default_language: str,
    label: str,
) -> ProjectConceptRevision:
    revision_object = _require_exact_object(
        value,
        _REVISION_FIELDS,
        label,
    )
    revision = _require_positive_integer(
        revision_object["revision"],
        f"{label}.revision",
    )
    lifecycle_status = _require_member(
        revision_object["lifecycle_status"],
        PROJECT_CONCEPT_LIFECYCLE_STATES,
        f"{label}.lifecycle_status",
    )
    preferred_labels = _parse_localized_texts(
        revision_object["preferred_labels"],
        label=f"{label}.preferred_labels",
        require_nonempty=True,
        unique_language=True,
    )
    alternative_labels = _parse_localized_texts(
        revision_object["alternative_labels"],
        label=f"{label}.alternative_labels",
        require_nonempty=False,
        unique_language=False,
    )
    definitions = _parse_localized_texts(
        revision_object["definitions"],
        label=f"{label}.definitions",
        require_nonempty=True,
        unique_language=True,
    )

    preferred_languages = {
        item.language
        for item in preferred_labels
    }
    definition_languages = {
        item.language
        for item in definitions
    }

    if default_language not in preferred_languages:
        raise ProjectGlossaryValidationError(
            f"{label}.preferred_labels must contain the Project "
            f"Glossary default language {default_language!r}."
        )

    if default_language not in definition_languages:
        raise ProjectGlossaryValidationError(
            f"{label}.definitions must contain the Project "
            f"Glossary default language {default_language!r}."
        )

    preferred_keys = {
        localized_label_comparison_key(
            item.language,
            item.text,
            label=f"{label}.preferred_labels",
        )
        for item in preferred_labels
    }
    alternative_keys = [
        localized_label_comparison_key(
            item.language,
            item.text,
            label=f"{label}.alternative_labels",
        )
        for item in alternative_labels
    ]

    if len(alternative_keys) != len(set(alternative_keys)):
        raise ProjectGlossaryValidationError(
            f"{label}.alternative_labels contains duplicate "
            "normalized labels."
        )

    overlap = preferred_keys.intersection(alternative_keys)

    if overlap:
        raise ProjectGlossaryValidationError(
            f"{label} must not repeat a preferred label as an "
            "alternative label in the same language."
        )

    broader_ids = _parse_project_concept_id_list(
        revision_object["broader_project_concept_ids"],
        f"{label}.broader_project_concept_ids",
    )
    related_ids = _parse_project_concept_id_list(
        revision_object["related_project_concept_ids"],
        f"{label}.related_project_concept_ids",
    )

    if project_concept_id in broader_ids:
        raise ProjectGlossaryValidationError(
            f"{label}.broader_project_concept_ids must not "
            "reference the owning concept."
        )

    if project_concept_id in related_ids:
        raise ProjectGlossaryValidationError(
            f"{label}.related_project_concept_ids must not "
            "reference the owning concept."
        )

    if set(broader_ids).intersection(related_ids):
        raise ProjectGlossaryValidationError(
            f"{label} must not classify the same Project Concept "
            "as both broader and related."
        )

    turing_core_mappings = tuple(
        _parse_turing_core_mapping(
            mapping,
            label=(
                f"{label}.turing_core_mappings"
                f"[{index}]"
            ),
        )
        for index, mapping in enumerate(
            _require_list(
                revision_object["turing_core_mappings"],
                f"{label}.turing_core_mappings",
            )
        )
    )
    external_mappings = tuple(
        _parse_external_mapping(
            mapping,
            label=(
                f"{label}.external_ontology_mappings"
                f"[{index}]"
            ),
        )
        for index, mapping in enumerate(
            _require_list(
                revision_object[
                    "external_ontology_mappings"
                ],
                f"{label}.external_ontology_mappings",
            )
        )
    )
    provenance = tuple(
        _parse_provenance(
            item,
            label=f"{label}.provenance[{index}]",
        )
        for index, item in enumerate(
            _require_list(
                revision_object["provenance"],
                f"{label}.provenance",
            )
        )
    )

    if not provenance:
        raise ProjectGlossaryValidationError(
            f"{label}.provenance must not be empty."
        )

    rationale = require_stored_glossary_text(
        revision_object["rationale"],
        f"{label}.rationale",
    )
    created_at, _ = _require_utc_timestamp(
        revision_object["created_at"],
        f"{label}.created_at",
    )

    return ProjectConceptRevision(
        revision=revision,
        lifecycle_status=lifecycle_status,
        preferred_labels=preferred_labels,
        alternative_labels=alternative_labels,
        definitions=definitions,
        broader_project_concept_ids=broader_ids,
        related_project_concept_ids=related_ids,
        turing_core_mappings=turing_core_mappings,
        external_ontology_mappings=external_mappings,
        provenance=provenance,
        rationale=rationale,
        created_at=created_at,
    )


def _parse_localized_texts(
    value: Any,
    *,
    label: str,
    require_nonempty: bool,
    unique_language: bool,
) -> tuple[LocalizedGlossaryText, ...]:
    items = _require_list(value, label)

    if require_nonempty and not items:
        raise ProjectGlossaryValidationError(
            f"{label} must not be empty."
        )

    parsed = tuple(
        _parse_localized_text(
            item,
            label=f"{label}[{index}]",
        )
        for index, item in enumerate(items)
    )

    if unique_language:
        languages = [
            item.language
            for item in parsed
        ]

        if len(languages) != len(set(languages)):
            raise ProjectGlossaryValidationError(
                f"{label} must contain at most one entry per "
                "language."
            )

    return parsed


def _parse_localized_text(
    value: Any,
    *,
    label: str,
) -> LocalizedGlossaryText:
    text_object = _require_exact_object(
        value,
        _LOCALIZED_TEXT_FIELDS,
        label,
    )

    return LocalizedGlossaryText(
        language=require_language_code(
            text_object["language"],
            f"{label}.language",
        ),
        text=require_stored_glossary_text(
            text_object["text"],
            f"{label}.text",
        ),
    )


def _parse_provenance(
    value: Any,
    *,
    label: str,
) -> ProjectConceptProvenance:
    provenance_object = _require_exact_object(
        value,
        _PROVENANCE_FIELDS,
        label,
    )
    provenance_type = _require_member(
        provenance_object["provenance_type"],
        PROJECT_CONCEPT_PROVENANCE_TYPES,
        f"{label}.provenance_type",
    )
    reference_id = require_stored_glossary_text(
        provenance_object["reference_id"],
        f"{label}.reference_id",
    )
    rationale = require_stored_glossary_text(
        provenance_object["rationale"],
        f"{label}.rationale",
    )
    reference_system_id = _require_optional_string(
        provenance_object["reference_system_id"],
        f"{label}.reference_system_id",
    )
    reference_version = _require_optional_string(
        provenance_object["reference_version"],
        f"{label}.reference_version",
    )
    source_projection_id = _require_optional_string(
        provenance_object["source_projection_id"],
        f"{label}.source_projection_id",
    )
    segment_ids = tuple(
        _validate_segment_reference(
            segment_id,
            f"{label}.segment_ids[{index}]",
        )
        for index, segment_id in enumerate(
            _require_list(
                provenance_object["segment_ids"],
                f"{label}.segment_ids",
            )
        )
    )

    if len(segment_ids) != len(set(segment_ids)):
        raise ProjectGlossaryValidationError(
            f"{label}.segment_ids must not contain duplicates."
        )

    if provenance_type in {
        "engineering_source",
        "context_only_source",
    }:
        _validate_source_reference(
            reference_id,
            f"{label}.reference_id",
        )

        if source_projection_id is None:
            raise ProjectGlossaryValidationError(
                f"{label}.source_projection_id is required for "
                f"{provenance_type!r} provenance."
            )

        _validate_source_projection_reference(
            source_projection_id,
            f"{label}.source_projection_id",
        )

        if not segment_ids:
            raise ProjectGlossaryValidationError(
                f"{label}.segment_ids must not be empty for "
                f"{provenance_type!r} provenance."
            )

        if (
            reference_system_id is not None
            or reference_version is not None
        ):
            raise ProjectGlossaryValidationError(
                f"{label} source provenance must not declare an "
                "external reference system."
            )
    elif provenance_type == "terminology_decision":
        if not is_valid_terminology_decision_id(reference_id):
            raise ProjectGlossaryValidationError(
                f"{label}.reference_id must be a valid "
                "Terminology Decision ID."
            )
        _require_no_projection_reference(
            source_projection_id,
            segment_ids,
            label,
        )

        if (
            reference_system_id is not None
            or reference_version is not None
        ):
            raise ProjectGlossaryValidationError(
                f"{label} terminology-decision provenance must "
                "not declare an external reference system."
            )
    elif provenance_type == "external_reference":
        _require_http_iri(
            reference_id,
            f"{label}.reference_id",
        )
        _require_reference_system(
            reference_system_id,
            reference_version,
            label,
        )
        _require_no_projection_reference(
            source_projection_id,
            segment_ids,
            label,
        )
    elif provenance_type == "turing_core":
        if (
            _TURING_CORE_CONCEPT_ID_PATTERN.fullmatch(
                reference_id
            )
            is None
            or reference_id == "TC-000000"
        ):
            raise ProjectGlossaryValidationError(
                f"{label}.reference_id must be a valid "
                "Turing Core Concept ID."
            )

        if reference_system_id != TURING_CORE_VOCABULARY_ID:
            raise ProjectGlossaryValidationError(
                f"{label}.reference_system_id must be "
                f"{TURING_CORE_VOCABULARY_ID!r}."
            )

        _require_semantic_version(
            reference_version,
            f"{label}.reference_version",
        )
        _require_no_projection_reference(
            source_projection_id,
            segment_ids,
            label,
        )

    return ProjectConceptProvenance(
        provenance_type=provenance_type,
        reference_id=reference_id,
        rationale=rationale,
        reference_system_id=reference_system_id,
        reference_version=reference_version,
        source_projection_id=source_projection_id,
        segment_ids=segment_ids,
    )


def _parse_turing_core_mapping(
    value: Any,
    *,
    label: str,
) -> TuringCoreConceptMapping:
    mapping_object = _require_exact_object(
        value,
        _TURING_CORE_MAPPING_FIELDS,
        label,
    )
    vocabulary_id = require_stored_glossary_text(
        mapping_object["vocabulary_id"],
        f"{label}.vocabulary_id",
    )

    if vocabulary_id != TURING_CORE_VOCABULARY_ID:
        raise ProjectGlossaryValidationError(
            f"{label}.vocabulary_id must be "
            f"{TURING_CORE_VOCABULARY_ID!r}."
        )

    vocabulary_version = _require_semantic_version(
        mapping_object["vocabulary_version"],
        f"{label}.vocabulary_version",
    )
    concept_id = require_stored_glossary_text(
        mapping_object["turing_core_concept_id"],
        f"{label}.turing_core_concept_id",
    )

    if (
        _TURING_CORE_CONCEPT_ID_PATTERN.fullmatch(concept_id)
        is None
        or concept_id == "TC-000000"
    ):
        raise ProjectGlossaryValidationError(
            f"{label}.turing_core_concept_id must match "
            "^TC-[0-9]{6}$ and must not use sequence 000000."
        )

    return TuringCoreConceptMapping(
        vocabulary_id=vocabulary_id,
        vocabulary_version=vocabulary_version,
        turing_core_concept_id=concept_id,
        relation=_require_member(
            mapping_object["relation"],
            PROJECT_CONCEPT_MAPPING_RELATIONS,
            f"{label}.relation",
        ),
        rationale=require_stored_glossary_text(
            mapping_object["rationale"],
            f"{label}.rationale",
        ),
    )


def _parse_external_mapping(
    value: Any,
    *,
    label: str,
) -> ProjectExternalOntologyMapping:
    mapping_object = _require_exact_object(
        value,
        _EXTERNAL_MAPPING_FIELDS,
        label,
    )

    return ProjectExternalOntologyMapping(
        reference_system_id=_require_reference_system_id(
            mapping_object["reference_system_id"],
            f"{label}.reference_system_id",
        ),
        reference_system_version=require_stored_glossary_text(
            mapping_object["reference_system_version"],
            f"{label}.reference_system_version",
        ),
        reference_concept_iri=_require_http_iri(
            mapping_object["reference_concept_iri"],
            f"{label}.reference_concept_iri",
        ),
        relation=_require_member(
            mapping_object["relation"],
            PROJECT_CONCEPT_MAPPING_RELATIONS,
            f"{label}.relation",
        ),
        rationale=require_stored_glossary_text(
            mapping_object["rationale"],
            f"{label}.rationale",
        ),
    )


def _parse_ambiguity_group(
    value: Any,
    *,
    label: str,
) -> AmbiguityGroup:
    group_object = _require_exact_object(
        value,
        _AMBIGUITY_GROUP_FIELDS,
        label,
    )
    ambiguity_group_id = group_object["ambiguity_group_id"]

    if not is_valid_ambiguity_group_id(ambiguity_group_id):
        raise ProjectGlossaryValidationError(
            f"{label}.ambiguity_group_id must match "
            "^AG-[0-9]{6}$ and must not use sequence 000000."
        )

    candidate_ids = _parse_project_concept_id_list(
        group_object["candidate_project_concept_ids"],
        f"{label}.candidate_project_concept_ids",
    )

    if len(candidate_ids) < 2:
        raise ProjectGlossaryValidationError(
            f"{label}.candidate_project_concept_ids must contain "
            "at least two Project Concept IDs."
        )

    created_at, _ = _require_utc_timestamp(
        group_object["created_at"],
        f"{label}.created_at",
    )

    return AmbiguityGroup(
        ambiguity_group_id=ambiguity_group_id,
        label=require_stored_glossary_text(
            group_object["label"],
            f"{label}.label",
        ),
        language=require_language_code(
            group_object["language"],
            f"{label}.language",
        ),
        candidate_project_concept_ids=candidate_ids,
        resolution_rule=_require_member(
            group_object["resolution_rule"],
            AMBIGUITY_RESOLUTION_RULES,
            f"{label}.resolution_rule",
        ),
        rationale=require_stored_glossary_text(
            group_object["rationale"],
            f"{label}.rationale",
        ),
        created_at=created_at,
    )


def _validate_glossary_cross_references(
    glossary: ProjectGlossary,
) -> None:
    concept_ids = tuple(
        concept.project_concept_id
        for concept in glossary.concepts
    )

    if len(concept_ids) != len(set(concept_ids)):
        raise ProjectGlossaryValidationError(
            "Project Glossary contains duplicate Project Concept IDs."
        )

    if concept_ids != tuple(sorted(concept_ids)):
        raise ProjectGlossaryValidationError(
            "Project Glossary concepts must be ordered by "
            "project_concept_id."
        )

    known_concept_ids = set(concept_ids)

    for concept in glossary.concepts:
        for revision in concept.revisions:
            referenced_ids = (
                revision.broader_project_concept_ids
                + revision.related_project_concept_ids
            )
            unknown_ids = sorted(
                set(referenced_ids) - known_concept_ids
            )

            if unknown_ids:
                raise ProjectGlossaryValidationError(
                    f"{concept.project_concept_id} revision "
                    f"{revision.revision} references unknown "
                    "Project Concept IDs: "
                    f"{', '.join(unknown_ids)}."
                )

    group_ids = tuple(
        group.ambiguity_group_id
        for group in glossary.ambiguity_groups
    )

    if len(group_ids) != len(set(group_ids)):
        raise ProjectGlossaryValidationError(
            "Project Glossary contains duplicate Ambiguity Group IDs."
        )

    if group_ids != tuple(sorted(group_ids)):
        raise ProjectGlossaryValidationError(
            "Project Glossary ambiguity_groups must be ordered by "
            "ambiguity_group_id."
        )

    group_keys: set[tuple[str, str]] = set()
    groups_by_key: dict[
        tuple[str, str],
        list[AmbiguityGroup],
    ] = {}

    for group in glossary.ambiguity_groups:
        unknown_ids = sorted(
            set(group.candidate_project_concept_ids)
            - known_concept_ids
        )

        if unknown_ids:
            raise ProjectGlossaryValidationError(
                f"{group.ambiguity_group_id} references unknown "
                "Project Concept IDs: "
                f"{', '.join(unknown_ids)}."
            )

        key = localized_label_comparison_key(
            group.language,
            group.label,
            label=group.ambiguity_group_id,
        )

        if key in group_keys:
            raise ProjectGlossaryValidationError(
                "Only one Ambiguity Group may exist for a "
                "normalized project-language label."
            )

        group_keys.add(key)
        groups_by_key.setdefault(key, []).append(group)

    accepted_labels = _accepted_label_index(
        glossary.concepts
    )
    reviewable_labels = _reviewable_label_index(
        glossary.concepts
    )

    for key, entries in accepted_labels.items():
        preferred_concept_ids = {
            concept_id
            for concept_id, label_kind in entries
            if label_kind == "preferred"
        }

        if len(preferred_concept_ids) > 1:
            raise DuplicatePreferredLabelError(
                "Accepted preferred labels must be unique within "
                "one project and language. Conflict for "
                f"{key!r}: "
                f"{', '.join(sorted(preferred_concept_ids))}."
            )

        involved_concept_ids = {
            concept_id
            for concept_id, _ in entries
        }

        if len(involved_concept_ids) <= 1:
            continue

        matching_groups = groups_by_key.get(key, [])

        if not matching_groups:
            raise AmbiguousAlternativeLabelError(
                "An accepted alternative-label ambiguity requires "
                f"an Ambiguity Group for {key!r}."
            )

        group_candidates = set(
            matching_groups[0].candidate_project_concept_ids
        )

        if not involved_concept_ids.issubset(group_candidates):
            raise AmbiguousAlternativeLabelError(
                f"{matching_groups[0].ambiguity_group_id} does not "
                "cover every accepted Project Concept using "
                f"label {key!r}."
            )

    for group in glossary.ambiguity_groups:
        key = localized_label_comparison_key(
            group.language,
            group.label,
            label=group.ambiguity_group_id,
        )
        label_concept_ids = {
            concept_id
            for concept_id, _ in reviewable_labels.get(key, [])
        }

        if not set(
            group.candidate_project_concept_ids
        ).issubset(label_concept_ids):
            raise ProjectGlossaryValidationError(
                f"{group.ambiguity_group_id} candidates must each "
                "use the ambiguity label in an accepted or "
                "reviewable candidate revision."
            )


def _accepted_label_index(
    concepts: tuple[ProjectConcept, ...],
) -> dict[
    tuple[str, str],
    list[tuple[str, str]],
]:
    result: dict[
        tuple[str, str],
        list[tuple[str, str]],
    ] = {}

    for concept in concepts:
        revision = _effective_accepted_revision(concept)

        if revision is None:
            continue

        for item in revision.preferred_labels:
            key = localized_label_comparison_key(
                item.language,
                item.text,
                label=concept.project_concept_id,
            )
            result.setdefault(key, []).append(
                (concept.project_concept_id, "preferred")
            )

        for item in revision.alternative_labels:
            key = localized_label_comparison_key(
                item.language,
                item.text,
                label=concept.project_concept_id,
            )
            result.setdefault(key, []).append(
                (concept.project_concept_id, "alternative")
            )

    return result


def _reviewable_label_index(
    concepts: tuple[ProjectConcept, ...],
) -> dict[
    tuple[str, str],
    list[tuple[str, str]],
]:
    result: dict[
        tuple[str, str],
        list[tuple[str, str]],
    ] = {}

    for concept in concepts:
        revisions: list[ProjectConceptRevision] = [
            concept.revisions[-1]
        ]
        accepted = _effective_accepted_revision(concept)

        if (
            accepted is not None
            and accepted.revision
            != concept.revisions[-1].revision
        ):
            revisions.append(accepted)

        for revision in revisions:
            for item in revision.preferred_labels:
                key = localized_label_comparison_key(
                    item.language,
                    item.text,
                    label=concept.project_concept_id,
                )
                result.setdefault(key, []).append(
                    (
                        concept.project_concept_id,
                        "preferred",
                    )
                )

            for item in revision.alternative_labels:
                key = localized_label_comparison_key(
                    item.language,
                    item.text,
                    label=concept.project_concept_id,
                )
                result.setdefault(key, []).append(
                    (
                        concept.project_concept_id,
                        "alternative",
                    )
                )

    return result


def _effective_accepted_revision(
    concept: ProjectConcept,
) -> ProjectConceptRevision | None:
    if (
        concept.revisions[-1].lifecycle_status
        == "deprecated"
    ):
        return None

    accepted = [
        revision
        for revision in concept.revisions
        if revision.lifecycle_status == "accepted"
    ]

    if not accepted:
        return None

    return accepted[-1]


def _project_glossary_payload(
    glossary: ProjectGlossary,
) -> dict[str, Any]:
    if not isinstance(glossary, ProjectGlossary):
        raise ProjectGlossaryValidationError(
            "glossary must be a ProjectGlossary instance."
        )

    return {
        "schema_version": glossary.schema_version,
        "project_id": glossary.project_id,
        "glossary_revision": glossary.glossary_revision,
        "default_language": glossary.default_language,
        "created_at": glossary.created_at,
        "updated_at": glossary.updated_at,
        "concepts": [
            _project_concept_payload(concept)
            for concept in glossary.concepts
        ],
        "ambiguity_groups": [
            _ambiguity_group_payload(group)
            for group in glossary.ambiguity_groups
        ],
    }


def _project_concept_payload(
    concept: ProjectConcept,
) -> dict[str, Any]:
    if not isinstance(concept, ProjectConcept):
        raise ProjectGlossaryValidationError(
            "concepts must contain ProjectConcept instances."
        )

    return {
        "project_concept_id": concept.project_concept_id,
        "latest_revision": concept.latest_revision,
        "revisions": [
            _project_concept_revision_payload(revision)
            for revision in concept.revisions
        ],
    }


def _project_concept_revision_payload(
    revision: ProjectConceptRevision,
) -> dict[str, Any]:
    if not isinstance(revision, ProjectConceptRevision):
        raise ProjectGlossaryValidationError(
            "revisions must contain ProjectConceptRevision "
            "instances."
        )

    return {
        "revision": revision.revision,
        "lifecycle_status": revision.lifecycle_status,
        "preferred_labels": [
            _localized_text_payload(item)
            for item in revision.preferred_labels
        ],
        "alternative_labels": [
            _localized_text_payload(item)
            for item in revision.alternative_labels
        ],
        "definitions": [
            _localized_text_payload(item)
            for item in revision.definitions
        ],
        "broader_project_concept_ids": list(
            revision.broader_project_concept_ids
        ),
        "related_project_concept_ids": list(
            revision.related_project_concept_ids
        ),
        "turing_core_mappings": [
            _turing_core_mapping_payload(mapping)
            for mapping in revision.turing_core_mappings
        ],
        "external_ontology_mappings": [
            _external_mapping_payload(mapping)
            for mapping in revision.external_ontology_mappings
        ],
        "provenance": [
            _provenance_payload(item)
            for item in revision.provenance
        ],
        "rationale": revision.rationale,
        "created_at": revision.created_at,
    }


def _localized_text_payload(
    item: LocalizedGlossaryText,
) -> dict[str, Any]:
    if not isinstance(item, LocalizedGlossaryText):
        raise ProjectGlossaryValidationError(
            "Localized text collections must contain "
            "LocalizedGlossaryText instances."
        )

    return {
        "language": item.language,
        "text": item.text,
    }


def _provenance_payload(
    item: ProjectConceptProvenance,
) -> dict[str, Any]:
    if not isinstance(item, ProjectConceptProvenance):
        raise ProjectGlossaryValidationError(
            "provenance must contain ProjectConceptProvenance "
            "instances."
        )

    return {
        "provenance_type": item.provenance_type,
        "reference_id": item.reference_id,
        "rationale": item.rationale,
        "reference_system_id": item.reference_system_id,
        "reference_version": item.reference_version,
        "source_projection_id": item.source_projection_id,
        "segment_ids": list(item.segment_ids),
    }


def _turing_core_mapping_payload(
    mapping: TuringCoreConceptMapping,
) -> dict[str, Any]:
    if not isinstance(mapping, TuringCoreConceptMapping):
        raise ProjectGlossaryValidationError(
            "turing_core_mappings must contain "
            "TuringCoreConceptMapping instances."
        )

    return {
        "vocabulary_id": mapping.vocabulary_id,
        "vocabulary_version": mapping.vocabulary_version,
        "turing_core_concept_id": (
            mapping.turing_core_concept_id
        ),
        "relation": mapping.relation,
        "rationale": mapping.rationale,
    }


def _external_mapping_payload(
    mapping: ProjectExternalOntologyMapping,
) -> dict[str, Any]:
    if not isinstance(
        mapping,
        ProjectExternalOntologyMapping,
    ):
        raise ProjectGlossaryValidationError(
            "external_ontology_mappings must contain "
            "ProjectExternalOntologyMapping instances."
        )

    return {
        "reference_system_id": mapping.reference_system_id,
        "reference_system_version": (
            mapping.reference_system_version
        ),
        "reference_concept_iri": (
            mapping.reference_concept_iri
        ),
        "relation": mapping.relation,
        "rationale": mapping.rationale,
    }


def _ambiguity_group_payload(
    group: AmbiguityGroup,
) -> dict[str, Any]:
    if not isinstance(group, AmbiguityGroup):
        raise ProjectGlossaryValidationError(
            "ambiguity_groups must contain AmbiguityGroup "
            "instances."
        )

    return {
        "ambiguity_group_id": group.ambiguity_group_id,
        "label": group.label,
        "language": group.language,
        "candidate_project_concept_ids": list(
            group.candidate_project_concept_ids
        ),
        "resolution_rule": group.resolution_rule,
        "rationale": group.rationale,
        "created_at": group.created_at,
    }


def _parse_project_concept_id_list(
    value: Any,
    label: str,
) -> tuple[str, ...]:
    identifiers = tuple(
        _require_project_concept_id(
            item,
            f"{label}[{index}]",
        )
        for index, item in enumerate(
            _require_list(value, label)
        )
    )

    if len(identifiers) != len(set(identifiers)):
        raise ProjectGlossaryValidationError(
            f"{label} must not contain duplicates."
        )

    if identifiers != tuple(sorted(identifiers)):
        raise ProjectGlossaryValidationError(
            f"{label} must be ordered by Project Concept ID."
        )

    return identifiers


def _require_project_concept_id(
    value: Any,
    label: str,
) -> str:
    if not is_valid_project_concept_id(value):
        raise ProjectGlossaryValidationError(
            f"{label} must match ^PC-[0-9]{{6}}$ and must not "
            "use sequence 000000."
        )

    return value


def _require_project_id(
    value: Any,
    label: str,
) -> str:
    if not is_valid_project_id(value):
        raise ProjectGlossaryValidationError(
            f"{label} must contain exactly six digits."
        )

    return value


def _validate_source_reference(
    value: Any,
    label: str,
) -> str:
    try:
        return validate_source_id(value)
    except Exception as exc:
        raise ProjectGlossaryValidationError(
            f"{label} must be a valid Source ID."
        ) from exc


def _validate_source_projection_reference(
    value: Any,
    label: str,
) -> str:
    try:
        return validate_source_projection_id(value)
    except Exception as exc:
        raise ProjectGlossaryValidationError(
            f"{label} must be a valid Source Projection ID."
        ) from exc


def _validate_segment_reference(
    value: Any,
    label: str,
) -> str:
    try:
        return validate_segment_id(value)
    except Exception as exc:
        raise ProjectGlossaryValidationError(
            f"{label} must be a valid Segment ID."
        ) from exc


def _require_no_projection_reference(
    source_projection_id: str | None,
    segment_ids: tuple[str, ...],
    label: str,
) -> None:
    if source_projection_id is not None or segment_ids:
        raise ProjectGlossaryValidationError(
            f"{label} must not declare Source Projection or "
            "Segment references for this provenance type."
        )


def _require_reference_system(
    reference_system_id: str | None,
    reference_version: str | None,
    label: str,
) -> None:
    _require_reference_system_id(
        reference_system_id,
        f"{label}.reference_system_id",
    )
    require_stored_glossary_text(
        reference_version,
        f"{label}.reference_version",
    )


def _require_reference_system_id(
    value: Any,
    label: str,
) -> str:
    text = require_stored_glossary_text(value, label)

    if _REFERENCE_SYSTEM_ID_PATTERN.fullmatch(text) is None:
        raise ProjectGlossaryValidationError(
            f"{label} must be a stable uppercase identifier."
        )

    return text


def _require_semantic_version(
    value: Any,
    label: str,
) -> str:
    text = require_stored_glossary_text(value, label)

    if _SEMANTIC_VERSION_PATTERN.fullmatch(text) is None:
        raise ProjectGlossaryValidationError(
            f"{label} must use MAJOR.MINOR.PATCH versioning."
        )

    return text


def _require_http_iri(
    value: Any,
    label: str,
) -> str:
    text = require_stored_glossary_text(value, label)
    parsed = urlparse(text)

    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.netloc
    ):
        raise ProjectGlossaryValidationError(
            f"{label} must be an absolute HTTP(S) IRI."
        )

    return text


def _require_optional_string(
    value: Any,
    label: str,
) -> str | None:
    if value is None:
        return None

    return require_stored_glossary_text(value, label)


def _require_member(
    value: Any,
    allowed: frozenset[str],
    label: str,
) -> str:
    text = require_stored_glossary_text(value, label)

    if text not in allowed:
        raise ProjectGlossaryValidationError(
            f"{label} must be one of: "
            f"{', '.join(sorted(allowed))}."
        )

    return text


def _require_positive_integer(
    value: Any,
    label: str,
) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value < 1
    ):
        raise ProjectGlossaryValidationError(
            f"{label} must be a positive integer."
        )

    return value


def _require_utc_timestamp(
    value: Any,
    label: str,
) -> tuple[str, datetime]:
    if (
        not isinstance(value, str)
        or _UTC_TIMESTAMP_PATTERN.fullmatch(value) is None
    ):
        raise ProjectGlossaryValidationError(
            f"{label} must be an ISO-8601 UTC timestamp ending in Z."
        )

    try:
        timestamp = datetime.fromisoformat(
            value.removesuffix("Z") + "+00:00"
        )
    except ValueError as exc:
        raise ProjectGlossaryValidationError(
            f"{label} is not a valid UTC timestamp."
        ) from exc

    return value, timestamp


def _require_exact_object(
    value: Any,
    fields: frozenset[str],
    label: str,
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ProjectGlossaryValidationError(
            f"{label} must be a JSON object."
        )

    actual = set(value)
    missing = sorted(fields - actual)
    unknown = sorted(actual - fields)
    problems: list[str] = []

    if missing:
        problems.append(
            "missing " + ", ".join(missing)
        )

    if unknown:
        problems.append(
            "unknown " + ", ".join(unknown)
        )

    if problems:
        raise ProjectGlossaryValidationError(
            f"{label} fields are invalid: "
            f"{'; '.join(problems)}."
        )

    return value


def _require_list(
    value: Any,
    label: str,
) -> list[Any]:
    if not isinstance(value, list):
        raise ProjectGlossaryValidationError(
            f"{label} must be a JSON list."
        )

    return value


def _object_without_duplicate_keys(
    pairs: list[tuple[str, Any]],
) -> dict[str, Any]:
    result: dict[str, Any] = {}

    for key, value in pairs:
        if key in result:
            raise ProjectGlossaryValidationError(
                f"Duplicate JSON field: {key!r}."
            )

        result[key] = value

    return result