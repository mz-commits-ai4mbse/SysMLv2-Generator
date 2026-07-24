"""Load and validate the curated Turing Core Vocabulary.

Turing Core is a global, versioned semantic bridge. Loading this artifact
performs no LLM call, ontology inference, framework assignment, engineering
approval or model generation.
"""

from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any

from modules.framework import (
    FrameworkTemplateError,
    load_framework_template,
    mapping_target_ids,
)
from modules.semantics.errors import (
    OntologyRegistryError,
    SemanticReferenceError,
    TuringCoreVocabularyError,
)
from modules.semantics.registry import (
    DEFAULT_ONTOLOGY_REGISTRY_PATH,
    load_ontology_registry,
)
from modules.semantics.types import (
    ExternalOntologyMapping,
    SysMLRepresentationCandidate,
    TuringCoreAuthority,
    TuringCoreConcept,
    TuringCoreConceptRelationPolicy,
    TuringCoreExternalMappingPolicy,
    TuringCoreFrameworkMappingPolicy,
    TuringCoreIdentifierPolicy,
    TuringCoreLabelPolicy,
    TuringCoreSourceReference,
    TuringCoreSysMLMappingPolicy,
    TuringCoreVocabulary,
    TURING_CORE_CONCEPT_KINDS,
    TURING_CORE_CONCEPT_STATUSES,
    TURING_CORE_EXTERNAL_MAPPING_RELATIONS,
    TURING_CORE_EXTERNAL_MAPPING_STATUSES,
)
from modules.semantics.validation import (
    object_without_duplicate_keys,
    require_boolean,
    require_exact_object,
    require_http_url,
    require_identifier,
    require_list,
    require_positive_integer,
    require_repository_path,
    require_semantic_version,
    require_string,
    require_unique,
    resolve_repository_path,
)


DEFAULT_TURING_CORE_VOCABULARY_PATH = Path(
    "context/semantics/turing_core_vocabulary.json"
)

TURING_CORE_SCHEMA_VERSION = "1.0.0"
TURING_CORE_VOCABULARY_ID = "TURING_CORE_VOCABULARY"

_CONCEPT_ID_PATTERN = re.compile(r"^TC-[0-9]{6}$")
_LANGUAGE_PATTERN = re.compile(r"^[a-z]{2}$")
_VOCABULARY_STATUSES = frozenset(
    {
        "draft",
        "active",
        "retired",
    }
)
_INTERNAL_CONCEPT_RELATIONS = frozenset(
    {
        "broader_concept_ids",
        "related_concept_ids",
    }
)
_ALLOWED_SOURCE_ROOTS = frozenset(
    {
        "collaboration",
        "context",
    }
)


def _fields(text: str) -> frozenset[str]:
    return frozenset(text.split())


_TOP_LEVEL_FIELDS = _fields(
    """
    schema_version vocabulary_id vocabulary_version name status
    default_language authority source_references identifier_policy
    label_policy concept_relation_policy framework_mapping_policy
    sysml_v2_mapping_policy external_mapping_policy concepts
    """
)

_AUTHORITY_FIELDS = _fields(
    """
    role engineering_authority framework_authority
    target_model_semantics external_reference_systems
    project_terminology_authority
    automatic_project_mutation_allowed authority_rule
    """
)

_SOURCE_REFERENCE_REQUIRED_FIELDS = _fields(
    """
    source_reference_id path role
    """
)

_SOURCE_REFERENCE_OPTIONAL_FIELDS = _fields(
    """
    referenced_id referenced_version
    """
)

_IDENTIFIER_POLICY_FIELDS = _fields(
    """
    field pattern scope allocation reuse_allowed
    meaning_change_allowed
    """
)

_LABEL_POLICY_FIELDS = _fields(
    """
    preferred_label_required preferred_label_unique_casefolded
    alternative_labels_unique_within_concept_casefolded
    preferred_label_may_equal_alternative_label_casefolded
    automatic_synonym_generation_allowed
    """
)

_CONCEPT_RELATION_POLICY_FIELDS = _fields(
    """
    allowed_relations self_reference_allowed
    unknown_concept_reference_behavior
    """
)

_FRAMEWORK_MAPPING_POLICY_FIELDS = _fields(
    """
    framework_template_id framework_template_version
    candidate_target_field scope_reference_field
    candidate_target_must_be_mapping_target
    scope_reference_may_reference_level_node
    automatic_framework_assignment_allowed rule
    """
)

_SYSML_MAPPING_POLICY_FIELDS = _fields(
    """
    target_notation_id target_notation_version allowed_relation
    unknown_construct_behavior automatic_model_generation_allowed
    rule
    """
)

_EXTERNAL_MAPPING_POLICY_FIELDS = _fields(
    """
    registry_id allowed_reference_system_ids allowed_relations
    mapping_required review_required automatic_exact_match_allowed
    initial_mapping_status
    """
)

_CONCEPT_FIELDS = _fields(
    """
    concept_id preferred_label alternative_labels definition
    concept_kind broader_concept_ids related_concept_ids
    candidate_framework_node_ids framework_scope_node_ids
    sysml_v2_representation_candidates target_notation_note
    external_mapping_status external_mappings
    provenance_source_reference_ids status order
    """
)

_SYSML_CANDIDATE_FIELDS = _fields(
    """
    construct_id relation rationale
    """
)

_EXTERNAL_MAPPING_FIELDS = _fields(
    """
    reference_system_id reference_system_version
    reference_concept_iri relation rationale
    provenance_source_reference_ids
    """
)


def load_turing_core_vocabulary(
    path: Path = DEFAULT_TURING_CORE_VOCABULARY_PATH,
    *,
    repository_root: Path = Path("."),
    validate_references: bool = True,
) -> TuringCoreVocabulary:
    """Load Turing Core and optionally validate repository references."""

    root = repository_root.resolve()

    try:
        vocabulary_path = resolve_repository_path(
            root,
            path,
            "Turing Core Vocabulary path",
        )
    except SemanticReferenceError as exc:
        raise TuringCoreVocabularyError(str(exc)) from exc

    try:
        text = vocabulary_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise TuringCoreVocabularyError(
            "Unable to read Turing Core Vocabulary from "
            f"{vocabulary_path}: {exc}."
        ) from exc

    try:
        payload = json.loads(
            text,
            object_pairs_hook=object_without_duplicate_keys,
        )
    except OntologyRegistryError as exc:
        raise TuringCoreVocabularyError(str(exc)) from exc
    except json.JSONDecodeError as exc:
        raise TuringCoreVocabularyError(
            "Turing Core Vocabulary contains invalid JSON: "
            f"{exc}."
        ) from exc

    vocabulary = parse_turing_core_vocabulary(payload)

    if validate_references:
        validate_turing_core_references(
            vocabulary,
            repository_root=root,
        )

    return vocabulary


def parse_turing_core_vocabulary(
    payload: Any,
) -> TuringCoreVocabulary:
    """Parse and strictly validate one Turing Core payload."""

    try:
        vocabulary = _parse_turing_core_vocabulary(payload)
    except OntologyRegistryError as exc:
        raise TuringCoreVocabularyError(str(exc)) from exc

    _validate_internal_concept_references(vocabulary)
    _validate_concept_labels(vocabulary)
    _validate_concept_order(vocabulary)

    return vocabulary


def validate_turing_core_references(
    vocabulary: TuringCoreVocabulary,
    *,
    repository_root: Path = Path("."),
) -> None:
    """Validate repository, framework, SysML and ontology references."""

    root = repository_root.resolve()

    try:
        _validate_source_references(vocabulary, root)
        _validate_framework_references(vocabulary, root)
        _validate_sysml_references(vocabulary, root)
        _validate_ontology_references(vocabulary, root)
    except TuringCoreVocabularyError:
        raise
    except (
        FrameworkTemplateError,
        OntologyRegistryError,
        SemanticReferenceError,
        OSError,
        json.JSONDecodeError,
    ) as exc:
        raise TuringCoreVocabularyError(
            f"Turing Core reference validation failed: {exc}"
        ) from exc


def turing_core_concept_by_id(
    vocabulary: TuringCoreVocabulary,
    concept_id: str,
) -> TuringCoreConcept:
    """Return one concept by stable identifier."""

    for concept in vocabulary.concepts:
        if concept.concept_id == concept_id:
            return concept

    raise TuringCoreVocabularyError(
        f"Unknown Turing Core concept ID: {concept_id!r}."
    )


def turing_core_concepts_by_label(
    vocabulary: TuringCoreVocabulary,
    label: str,
) -> tuple[TuringCoreConcept, ...]:
    """Return exact case-insensitive preferred or alternative matches."""

    if not isinstance(label, str) or not label.strip():
        raise TuringCoreVocabularyError(
            "Turing Core label query must be a non-empty string."
        )

    if label != label.strip():
        raise TuringCoreVocabularyError(
            "Turing Core label query must not contain "
            "surrounding whitespace."
        )

    normalized = label.casefold()

    return tuple(
        concept
        for concept in vocabulary.concepts
        if normalized
        in {
            concept.preferred_label.casefold(),
            *(
                alternative.casefold()
                for alternative in concept.alternative_labels
            ),
        }
    )


def _parse_turing_core_vocabulary(
    payload: Any,
) -> TuringCoreVocabulary:
    data = require_exact_object(
        payload,
        _TOP_LEVEL_FIELDS,
        "Turing Core Vocabulary",
    )

    schema_version = require_semantic_version(
        data["schema_version"],
        "schema_version",
    )

    if schema_version != TURING_CORE_SCHEMA_VERSION:
        raise OntologyRegistryError(
            "Unsupported Turing Core schema_version: "
            f"{schema_version!r}."
        )

    vocabulary_id = require_identifier(
        data["vocabulary_id"],
        "vocabulary_id",
    )

    if vocabulary_id != TURING_CORE_VOCABULARY_ID:
        raise OntologyRegistryError(
            "vocabulary_id must be "
            f"{TURING_CORE_VOCABULARY_ID!r}."
        )

    vocabulary_version = require_semantic_version(
        data["vocabulary_version"],
        "vocabulary_version",
    )
    name = require_string(data["name"], "name")
    status = require_string(data["status"], "status")

    if status not in _VOCABULARY_STATUSES:
        raise OntologyRegistryError(
            "status must be one of: "
            + ", ".join(sorted(_VOCABULARY_STATUSES))
            + "."
        )

    default_language = require_string(
        data["default_language"],
        "default_language",
    )

    if not _LANGUAGE_PATTERN.fullmatch(default_language):
        raise OntologyRegistryError(
            "default_language must contain exactly two "
            "lowercase letters."
        )

    authority = _parse_authority(data["authority"])
    source_references = _parse_source_references(
        data["source_references"]
    )
    identifier_policy = _parse_identifier_policy(
        data["identifier_policy"]
    )
    label_policy = _parse_label_policy(data["label_policy"])
    concept_relation_policy = _parse_concept_relation_policy(
        data["concept_relation_policy"]
    )
    framework_mapping_policy = _parse_framework_mapping_policy(
        data["framework_mapping_policy"]
    )
    sysml_v2_mapping_policy = _parse_sysml_mapping_policy(
        data["sysml_v2_mapping_policy"]
    )
    external_mapping_policy = _parse_external_mapping_policy(
        data["external_mapping_policy"]
    )
    concepts = _parse_concepts(
        data["concepts"],
        sysml_relation=sysml_v2_mapping_policy.allowed_relation,
        external_relations=frozenset(
            external_mapping_policy.allowed_relations
        ),
    )

    source_reference_ids = {
        reference.source_reference_id
        for reference in source_references
    }

    for concept in concepts:
        unknown_provenance = (
            set(concept.provenance_source_reference_ids)
            - source_reference_ids
        )

        if unknown_provenance:
            raise OntologyRegistryError(
                f"{concept.concept_id} references unknown "
                "provenance source IDs: "
                + ", ".join(sorted(unknown_provenance))
                + "."
            )

        for mapping in concept.external_mappings:
            unknown_mapping_provenance = (
                set(mapping.provenance_source_reference_ids)
                - source_reference_ids
            )

            if unknown_mapping_provenance:
                raise OntologyRegistryError(
                    f"{concept.concept_id} external mapping "
                    "references unknown provenance source IDs: "
                    + ", ".join(
                        sorted(unknown_mapping_provenance)
                    )
                    + "."
                )

    if (
        set(authority.external_reference_systems)
        != set(
            external_mapping_policy.allowed_reference_system_ids
        )
    ):
        raise OntologyRegistryError(
            "authority.external_reference_systems must match "
            "external_mapping_policy.allowed_reference_system_ids."
        )

    return TuringCoreVocabulary(
        schema_version=schema_version,
        vocabulary_id=vocabulary_id,
        vocabulary_version=vocabulary_version,
        name=name,
        status=status,
        default_language=default_language,
        authority=authority,
        source_references=source_references,
        identifier_policy=identifier_policy,
        label_policy=label_policy,
        concept_relation_policy=concept_relation_policy,
        framework_mapping_policy=framework_mapping_policy,
        sysml_v2_mapping_policy=sysml_v2_mapping_policy,
        external_mapping_policy=external_mapping_policy,
        concepts=concepts,
    )


def _parse_authority(payload: Any) -> TuringCoreAuthority:
    data = require_exact_object(
        payload,
        _AUTHORITY_FIELDS,
        "authority",
    )
    external_reference_systems = _string_tuple(
        data["external_reference_systems"],
        "authority.external_reference_systems",
        allow_empty=False,
    )

    authority = TuringCoreAuthority(
        role=require_string(data["role"], "authority.role"),
        engineering_authority=require_string(
            data["engineering_authority"],
            "authority.engineering_authority",
        ),
        framework_authority=require_string(
            data["framework_authority"],
            "authority.framework_authority",
        ),
        target_model_semantics=require_string(
            data["target_model_semantics"],
            "authority.target_model_semantics",
        ),
        external_reference_systems=external_reference_systems,
        project_terminology_authority=require_string(
            data["project_terminology_authority"],
            "authority.project_terminology_authority",
        ),
        automatic_project_mutation_allowed=require_boolean(
            data["automatic_project_mutation_allowed"],
            "authority.automatic_project_mutation_allowed",
        ),
        authority_rule=require_string(
            data["authority_rule"],
            "authority.authority_rule",
        ),
    )

    if authority.automatic_project_mutation_allowed:
        raise OntologyRegistryError(
            "authority.automatic_project_mutation_allowed "
            "must be false."
        )

    return authority


def _parse_source_references(
    payload: Any,
) -> tuple[TuringCoreSourceReference, ...]:
    items = require_list(payload, "source_references")

    if not items:
        raise OntologyRegistryError(
            "source_references must not be empty."
        )

    references: list[TuringCoreSourceReference] = []

    for index, item in enumerate(items):
        label = f"source_references[{index}]"
        data = require_exact_object(
            item,
            _SOURCE_REFERENCE_REQUIRED_FIELDS,
            label,
            optional_fields=_SOURCE_REFERENCE_OPTIONAL_FIELDS,
        )
        path = _require_curated_source_path(
            data["path"],
            f"{label}.path",
        )
        referenced_id = data.get("referenced_id")
        referenced_version = data.get("referenced_version")

        if (referenced_id is None) != (
            referenced_version is None
        ):
            raise OntologyRegistryError(
                f"{label}.referenced_id and referenced_version "
                "must either both be present or both be absent."
            )

        references.append(
            TuringCoreSourceReference(
                source_reference_id=require_identifier(
                    data["source_reference_id"],
                    f"{label}.source_reference_id",
                ),
                path=path,
                role=require_string(
                    data["role"],
                    f"{label}.role",
                ),
                referenced_id=(
                    require_identifier(
                        referenced_id,
                        f"{label}.referenced_id",
                    )
                    if referenced_id is not None
                    else None
                ),
                referenced_version=(
                    require_semantic_version(
                        referenced_version,
                        f"{label}.referenced_version",
                    )
                    if referenced_version is not None
                    else None
                ),
            )
        )

    require_unique(
        (
            reference.source_reference_id
            for reference in references
        ),
        "Turing Core source reference ID",
    )
    require_unique(
        (
            reference.path.as_posix()
            for reference in references
        ),
        "Turing Core source path",
    )

    return tuple(references)


def _parse_identifier_policy(
    payload: Any,
) -> TuringCoreIdentifierPolicy:
    data = require_exact_object(
        payload,
        _IDENTIFIER_POLICY_FIELDS,
        "identifier_policy",
    )
    policy = TuringCoreIdentifierPolicy(
        field=require_string(
            data["field"],
            "identifier_policy.field",
        ),
        pattern=require_string(
            data["pattern"],
            "identifier_policy.pattern",
        ),
        scope=require_string(
            data["scope"],
            "identifier_policy.scope",
        ),
        allocation=require_string(
            data["allocation"],
            "identifier_policy.allocation",
        ),
        reuse_allowed=require_boolean(
            data["reuse_allowed"],
            "identifier_policy.reuse_allowed",
        ),
        meaning_change_allowed=require_boolean(
            data["meaning_change_allowed"],
            "identifier_policy.meaning_change_allowed",
        ),
    )

    if policy.field != "concept_id":
        raise OntologyRegistryError(
            "identifier_policy.field must be 'concept_id'."
        )

    if policy.pattern != r"^TC-[0-9]{6}$":
        raise OntologyRegistryError(
            "identifier_policy.pattern must be "
            "'^TC-[0-9]{6}$'."
        )

    if policy.scope != "global_to_turing_generator":
        raise OntologyRegistryError(
            "identifier_policy.scope must be "
            "'global_to_turing_generator'."
        )

    if policy.allocation != "sequential":
        raise OntologyRegistryError(
            "identifier_policy.allocation must be 'sequential'."
        )

    if policy.reuse_allowed or policy.meaning_change_allowed:
        raise OntologyRegistryError(
            "Turing Core identifiers shall not be reused or "
            "silently assigned another meaning."
        )

    return policy


def _parse_label_policy(
    payload: Any,
) -> TuringCoreLabelPolicy:
    data = require_exact_object(
        payload,
        _LABEL_POLICY_FIELDS,
        "label_policy",
    )
    policy = TuringCoreLabelPolicy(
        preferred_label_required=require_boolean(
            data["preferred_label_required"],
            "label_policy.preferred_label_required",
        ),
        preferred_label_unique_casefolded=require_boolean(
            data["preferred_label_unique_casefolded"],
            "label_policy.preferred_label_unique_casefolded",
        ),
        alternative_labels_unique_within_concept_casefolded=(
            require_boolean(
                data[
                    "alternative_labels_unique_within_"
                    "concept_casefolded"
                ],
                "label_policy."
                "alternative_labels_unique_within_"
                "concept_casefolded",
            )
        ),
        preferred_label_may_equal_alternative_label_casefolded=(
            require_boolean(
                data[
                    "preferred_label_may_equal_"
                    "alternative_label_casefolded"
                ],
                "label_policy."
                "preferred_label_may_equal_"
                "alternative_label_casefolded",
            )
        ),
        automatic_synonym_generation_allowed=require_boolean(
            data["automatic_synonym_generation_allowed"],
            "label_policy.automatic_synonym_generation_allowed",
        ),
    )

    if (
        not policy.preferred_label_required
        or not policy.preferred_label_unique_casefolded
        or not (
            policy
            .alternative_labels_unique_within_concept_casefolded
        )
        or (
            policy
            .preferred_label_may_equal_alternative_label_casefolded
        )
        or policy.automatic_synonym_generation_allowed
    ):
        raise OntologyRegistryError(
            "label_policy violates the accepted Turing Core "
            "label boundary."
        )

    return policy


def _parse_concept_relation_policy(
    payload: Any,
) -> TuringCoreConceptRelationPolicy:
    data = require_exact_object(
        payload,
        _CONCEPT_RELATION_POLICY_FIELDS,
        "concept_relation_policy",
    )
    allowed_relations = _string_tuple(
        data["allowed_relations"],
        "concept_relation_policy.allowed_relations",
        allow_empty=False,
    )
    policy = TuringCoreConceptRelationPolicy(
        allowed_relations=allowed_relations,
        self_reference_allowed=require_boolean(
            data["self_reference_allowed"],
            "concept_relation_policy.self_reference_allowed",
        ),
        unknown_concept_reference_behavior=require_string(
            data["unknown_concept_reference_behavior"],
            "concept_relation_policy."
            "unknown_concept_reference_behavior",
        ),
    )

    if set(policy.allowed_relations) != set(
        _INTERNAL_CONCEPT_RELATIONS
    ):
        raise OntologyRegistryError(
            "concept_relation_policy.allowed_relations must "
            "declare broader_concept_ids and related_concept_ids."
        )

    if policy.self_reference_allowed:
        raise OntologyRegistryError(
            "concept_relation_policy.self_reference_allowed "
            "must be false."
        )

    if (
        policy.unknown_concept_reference_behavior
        != "reject"
    ):
        raise OntologyRegistryError(
            "Unknown Turing Core concept references must be "
            "rejected."
        )

    return policy


def _parse_framework_mapping_policy(
    payload: Any,
) -> TuringCoreFrameworkMappingPolicy:
    data = require_exact_object(
        payload,
        _FRAMEWORK_MAPPING_POLICY_FIELDS,
        "framework_mapping_policy",
    )
    policy = TuringCoreFrameworkMappingPolicy(
        framework_template_id=require_identifier(
            data["framework_template_id"],
            "framework_mapping_policy.framework_template_id",
        ),
        framework_template_version=require_semantic_version(
            data["framework_template_version"],
            "framework_mapping_policy.framework_template_version",
        ),
        candidate_target_field=require_string(
            data["candidate_target_field"],
            "framework_mapping_policy.candidate_target_field",
        ),
        scope_reference_field=require_string(
            data["scope_reference_field"],
            "framework_mapping_policy.scope_reference_field",
        ),
        candidate_target_must_be_mapping_target=(
            require_boolean(
                data[
                    "candidate_target_must_be_mapping_target"
                ],
                "framework_mapping_policy."
                "candidate_target_must_be_mapping_target",
            )
        ),
        scope_reference_may_reference_level_node=(
            require_boolean(
                data[
                    "scope_reference_may_reference_level_node"
                ],
                "framework_mapping_policy."
                "scope_reference_may_reference_level_node",
            )
        ),
        automatic_framework_assignment_allowed=(
            require_boolean(
                data[
                    "automatic_framework_assignment_allowed"
                ],
                "framework_mapping_policy."
                "automatic_framework_assignment_allowed",
            )
        ),
        rule=require_string(
            data["rule"],
            "framework_mapping_policy.rule",
        ),
    )

    if (
        policy.candidate_target_field
        != "candidate_framework_node_ids"
        or policy.scope_reference_field
        != "framework_scope_node_ids"
        or not policy.candidate_target_must_be_mapping_target
        or not policy.scope_reference_may_reference_level_node
        or policy.automatic_framework_assignment_allowed
    ):
        raise OntologyRegistryError(
            "framework_mapping_policy violates the accepted "
            "candidate-mapping boundary."
        )

    return policy


def _parse_sysml_mapping_policy(
    payload: Any,
) -> TuringCoreSysMLMappingPolicy:
    data = require_exact_object(
        payload,
        _SYSML_MAPPING_POLICY_FIELDS,
        "sysml_v2_mapping_policy",
    )
    policy = TuringCoreSysMLMappingPolicy(
        target_notation_id=require_identifier(
            data["target_notation_id"],
            "sysml_v2_mapping_policy.target_notation_id",
        ),
        target_notation_version=require_semantic_version(
            data["target_notation_version"],
            "sysml_v2_mapping_policy.target_notation_version",
        ),
        allowed_relation=require_string(
            data["allowed_relation"],
            "sysml_v2_mapping_policy.allowed_relation",
        ),
        unknown_construct_behavior=require_string(
            data["unknown_construct_behavior"],
            "sysml_v2_mapping_policy.unknown_construct_behavior",
        ),
        automatic_model_generation_allowed=require_boolean(
            data["automatic_model_generation_allowed"],
            "sysml_v2_mapping_policy."
            "automatic_model_generation_allowed",
        ),
        rule=require_string(
            data["rule"],
            "sysml_v2_mapping_policy.rule",
        ),
    )

    if (
        policy.allowed_relation != "candidate_representation"
        or policy.unknown_construct_behavior != "reject"
        or policy.automatic_model_generation_allowed
    ):
        raise OntologyRegistryError(
            "sysml_v2_mapping_policy violates the accepted "
            "representation-candidate boundary."
        )

    return policy


def _parse_external_mapping_policy(
    payload: Any,
) -> TuringCoreExternalMappingPolicy:
    data = require_exact_object(
        payload,
        _EXTERNAL_MAPPING_POLICY_FIELDS,
        "external_mapping_policy",
    )
    allowed_reference_system_ids = _string_tuple(
        data["allowed_reference_system_ids"],
        "external_mapping_policy.allowed_reference_system_ids",
        allow_empty=False,
    )
    allowed_relations = _string_tuple(
        data["allowed_relations"],
        "external_mapping_policy.allowed_relations",
        allow_empty=False,
    )
    policy = TuringCoreExternalMappingPolicy(
        registry_id=require_identifier(
            data["registry_id"],
            "external_mapping_policy.registry_id",
        ),
        allowed_reference_system_ids=(
            allowed_reference_system_ids
        ),
        allowed_relations=allowed_relations,
        mapping_required=require_boolean(
            data["mapping_required"],
            "external_mapping_policy.mapping_required",
        ),
        review_required=require_boolean(
            data["review_required"],
            "external_mapping_policy.review_required",
        ),
        automatic_exact_match_allowed=require_boolean(
            data["automatic_exact_match_allowed"],
            "external_mapping_policy."
            "automatic_exact_match_allowed",
        ),
        initial_mapping_status=require_string(
            data["initial_mapping_status"],
            "external_mapping_policy.initial_mapping_status",
        ),
    )

    if set(policy.allowed_relations) != set(
        TURING_CORE_EXTERNAL_MAPPING_RELATIONS
    ):
        raise OntologyRegistryError(
            "external_mapping_policy.allowed_relations does "
            "not match the accepted relation set."
        )

    if (
        policy.mapping_required
        or not policy.review_required
        or policy.automatic_exact_match_allowed
        or policy.initial_mapping_status != "not_reviewed"
    ):
        raise OntologyRegistryError(
            "external_mapping_policy violates the accepted "
            "review boundary."
        )

    return policy


def _parse_concepts(
    payload: Any,
    *,
    sysml_relation: str,
    external_relations: frozenset[str],
) -> tuple[TuringCoreConcept, ...]:
    items = require_list(payload, "concepts")

    if not items:
        raise OntologyRegistryError(
            "concepts must not be empty."
        )

    concepts = tuple(
        _parse_concept(
            item,
            index=index,
            sysml_relation=sysml_relation,
            external_relations=external_relations,
        )
        for index, item in enumerate(items)
    )

    require_unique(
        (concept.concept_id for concept in concepts),
        "Turing Core concept ID",
    )
    require_unique(
        (str(concept.order) for concept in concepts),
        "Turing Core concept order",
    )

    return concepts


def _parse_concept(
    payload: Any,
    *,
    index: int,
    sysml_relation: str,
    external_relations: frozenset[str],
) -> TuringCoreConcept:
    label = f"concepts[{index}]"
    data = require_exact_object(
        payload,
        _CONCEPT_FIELDS,
        label,
    )
    concept_id = require_string(
        data["concept_id"],
        f"{label}.concept_id",
    )

    if not _CONCEPT_ID_PATTERN.fullmatch(concept_id):
        raise OntologyRegistryError(
            f"{label}.concept_id must match "
            "'^TC-[0-9]{6}$'."
        )

    concept_kind = require_string(
        data["concept_kind"],
        f"{label}.concept_kind",
    )

    if concept_kind not in TURING_CORE_CONCEPT_KINDS:
        raise OntologyRegistryError(
            f"{label}.concept_kind is unsupported: "
            f"{concept_kind!r}."
        )

    status = require_string(
        data["status"],
        f"{label}.status",
    )

    if status not in TURING_CORE_CONCEPT_STATUSES:
        raise OntologyRegistryError(
            f"{label}.status is unsupported: {status!r}."
        )

    external_mapping_status = require_string(
        data["external_mapping_status"],
        f"{label}.external_mapping_status",
    )

    if (
        external_mapping_status
        not in TURING_CORE_EXTERNAL_MAPPING_STATUSES
    ):
        raise OntologyRegistryError(
            f"{label}.external_mapping_status is unsupported: "
            f"{external_mapping_status!r}."
        )

    sysml_candidates = _parse_sysml_candidates(
        data["sysml_v2_representation_candidates"],
        label=f"{label}.sysml_v2_representation_candidates",
        allowed_relation=sysml_relation,
    )
    external_mappings = _parse_external_mappings(
        data["external_mappings"],
        label=f"{label}.external_mappings",
        allowed_relations=external_relations,
    )

    if (
        external_mapping_status == "not_reviewed"
        and external_mappings
    ):
        raise OntologyRegistryError(
            f"{label}.external_mappings must be empty while "
            "external_mapping_status is 'not_reviewed'."
        )

    return TuringCoreConcept(
        concept_id=concept_id,
        preferred_label=require_string(
            data["preferred_label"],
            f"{label}.preferred_label",
        ),
        alternative_labels=_string_tuple(
            data["alternative_labels"],
            f"{label}.alternative_labels",
            allow_empty=True,
            casefold_unique=True,
        ),
        definition=require_string(
            data["definition"],
            f"{label}.definition",
        ),
        concept_kind=concept_kind,
        broader_concept_ids=_concept_id_tuple(
            data["broader_concept_ids"],
            f"{label}.broader_concept_ids",
        ),
        related_concept_ids=_concept_id_tuple(
            data["related_concept_ids"],
            f"{label}.related_concept_ids",
        ),
        candidate_framework_node_ids=_string_tuple(
            data["candidate_framework_node_ids"],
            f"{label}.candidate_framework_node_ids",
            allow_empty=True,
        ),
        framework_scope_node_ids=_string_tuple(
            data["framework_scope_node_ids"],
            f"{label}.framework_scope_node_ids",
            allow_empty=True,
        ),
        sysml_v2_representation_candidates=sysml_candidates,
        target_notation_note=require_string(
            data["target_notation_note"],
            f"{label}.target_notation_note",
        ),
        external_mapping_status=external_mapping_status,
        external_mappings=external_mappings,
        provenance_source_reference_ids=_string_tuple(
            data["provenance_source_reference_ids"],
            f"{label}.provenance_source_reference_ids",
            allow_empty=False,
        ),
        status=status,
        order=require_positive_integer(
            data["order"],
            f"{label}.order",
        ),
    )


def _parse_sysml_candidates(
    payload: Any,
    *,
    label: str,
    allowed_relation: str,
) -> tuple[SysMLRepresentationCandidate, ...]:
    items = require_list(payload, label)
    candidates: list[SysMLRepresentationCandidate] = []

    for index, item in enumerate(items):
        item_label = f"{label}[{index}]"
        data = require_exact_object(
            item,
            _SYSML_CANDIDATE_FIELDS,
            item_label,
        )
        relation = require_string(
            data["relation"],
            f"{item_label}.relation",
        )

        if relation != allowed_relation:
            raise OntologyRegistryError(
                f"{item_label}.relation must be "
                f"{allowed_relation!r}."
            )

        candidates.append(
            SysMLRepresentationCandidate(
                construct_id=require_identifier(
                    data["construct_id"],
                    f"{item_label}.construct_id",
                ),
                relation=relation,
                rationale=require_string(
                    data["rationale"],
                    f"{item_label}.rationale",
                ),
            )
        )

    require_unique(
        (
            candidate.construct_id
            for candidate in candidates
        ),
        f"{label} construct ID",
    )

    return tuple(candidates)


def _parse_external_mappings(
    payload: Any,
    *,
    label: str,
    allowed_relations: frozenset[str],
) -> tuple[ExternalOntologyMapping, ...]:
    items = require_list(payload, label)
    mappings: list[ExternalOntologyMapping] = []

    for index, item in enumerate(items):
        item_label = f"{label}[{index}]"
        data = require_exact_object(
            item,
            _EXTERNAL_MAPPING_FIELDS,
            item_label,
        )
        relation = require_string(
            data["relation"],
            f"{item_label}.relation",
        )

        if relation not in allowed_relations:
            raise OntologyRegistryError(
                f"{item_label}.relation is unsupported: "
                f"{relation!r}."
            )

        mappings.append(
            ExternalOntologyMapping(
                reference_system_id=require_identifier(
                    data["reference_system_id"],
                    f"{item_label}.reference_system_id",
                ),
                reference_system_version=(
                    require_string(
                        data["reference_system_version"],
                        f"{item_label}."
                        "reference_system_version",
                    )
                ),
                reference_concept_iri=require_http_url(
                    data["reference_concept_iri"],
                    f"{item_label}.reference_concept_iri",
                ),
                relation=relation,
                rationale=require_string(
                    data["rationale"],
                    f"{item_label}.rationale",
                ),
                provenance_source_reference_ids=(
                    _string_tuple(
                        data[
                            "provenance_source_reference_ids"
                        ],
                        f"{item_label}."
                        "provenance_source_reference_ids",
                        allow_empty=False,
                    )
                ),
            )
        )

    duplicate_keys = [
        (
            mapping.reference_system_id,
            mapping.reference_concept_iri,
            mapping.relation,
        )
        for mapping in mappings
    ]

    if len(duplicate_keys) != len(set(duplicate_keys)):
        raise OntologyRegistryError(
            f"{label} contains duplicate external mappings."
        )

    return tuple(mappings)


def _validate_internal_concept_references(
    vocabulary: TuringCoreVocabulary,
) -> None:
    concept_ids = {
        concept.concept_id
        for concept in vocabulary.concepts
    }
    broader_graph: dict[str, tuple[str, ...]] = {}

    for concept in vocabulary.concepts:
        references = (
            concept.broader_concept_ids
            + concept.related_concept_ids
        )

        if concept.concept_id in references:
            raise TuringCoreVocabularyError(
                f"{concept.concept_id} must not reference itself."
            )

        unknown = set(references) - concept_ids

        if unknown:
            raise TuringCoreVocabularyError(
                f"{concept.concept_id} references unknown "
                "Turing Core concept IDs: "
                + ", ".join(sorted(unknown))
                + "."
            )

        overlap = set(concept.broader_concept_ids) & set(
            concept.related_concept_ids
        )

        if overlap:
            raise TuringCoreVocabularyError(
                f"{concept.concept_id} repeats concept IDs "
                "across broader and related relations: "
                + ", ".join(sorted(overlap))
                + "."
            )

        broader_graph[concept.concept_id] = (
            concept.broader_concept_ids
        )

    _reject_broader_concept_cycles(broader_graph)


def _reject_broader_concept_cycles(
    graph: dict[str, tuple[str, ...]],
) -> None:
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(concept_id: str) -> None:
        if concept_id in visiting:
            raise TuringCoreVocabularyError(
                "Turing Core broader-concept relations "
                f"contain a cycle at {concept_id}."
            )

        if concept_id in visited:
            return

        visiting.add(concept_id)

        for broader_id in graph[concept_id]:
            visit(broader_id)

        visiting.remove(concept_id)
        visited.add(concept_id)

    for concept_id in graph:
        visit(concept_id)


def _validate_concept_labels(
    vocabulary: TuringCoreVocabulary,
) -> None:
    preferred: dict[str, str] = {}

    for concept in vocabulary.concepts:
        normalized_preferred = (
            concept.preferred_label.casefold()
        )

        if normalized_preferred in preferred:
            raise TuringCoreVocabularyError(
                "Duplicate case-insensitive preferred label "
                f"{concept.preferred_label!r} for "
                f"{preferred[normalized_preferred]} and "
                f"{concept.concept_id}."
            )

        preferred[normalized_preferred] = concept.concept_id
        normalized_alternatives = {
            label.casefold()
            for label in concept.alternative_labels
        }

        if normalized_preferred in normalized_alternatives:
            raise TuringCoreVocabularyError(
                f"{concept.concept_id} repeats its preferred "
                "label as an alternative label."
            )


def _validate_concept_order(
    vocabulary: TuringCoreVocabulary,
) -> None:
    expected = tuple(range(1, len(vocabulary.concepts) + 1))
    actual = tuple(
        concept.order
        for concept in vocabulary.concepts
    )

    if actual != expected:
        raise TuringCoreVocabularyError(
            "Turing Core concepts must use contiguous order "
            f"values starting at 1; received {actual}."
        )

    numeric_ids = tuple(
        int(concept.concept_id.removeprefix("TC-"))
        for concept in vocabulary.concepts
    )

    if numeric_ids != tuple(sorted(numeric_ids)):
        raise TuringCoreVocabularyError(
            "Turing Core concepts must be stored in ascending "
            "concept-ID order."
        )


def _validate_source_references(
    vocabulary: TuringCoreVocabulary,
    root: Path,
) -> None:
    for reference in vocabulary.source_references:
        path = resolve_repository_path(
            root,
            reference.path,
            f"Source reference {reference.source_reference_id}",
        )

        if not path.is_file():
            raise TuringCoreVocabularyError(
                "Turing Core source reference does not exist: "
                f"{reference.path.as_posix()}."
            )

        if reference.referenced_id is None:
            continue

        try:
            payload = json.loads(
                path.read_text(encoding="utf-8"),
                object_pairs_hook=object_without_duplicate_keys,
            )
        except (
            OSError,
            json.JSONDecodeError,
            OntologyRegistryError,
        ) as exc:
            raise TuringCoreVocabularyError(
                "Unable to validate structured source "
                f"{reference.path.as_posix()}: {exc}."
            ) from exc

        if not isinstance(payload, dict):
            raise TuringCoreVocabularyError(
                "Structured Turing Core source must be a JSON "
                f"object: {reference.path.as_posix()}."
            )

        actual_id = _first_present(
            payload,
            (
                "context_id",
                "template_id",
                "registry_id",
            ),
        )
        actual_version = _first_present(
            payload,
            (
                "version",
                "template_version",
                "registry_version",
            ),
        )

        if actual_id != reference.referenced_id:
            raise TuringCoreVocabularyError(
                f"{reference.source_reference_id} expected ID "
                f"{reference.referenced_id!r}, received "
                f"{actual_id!r}."
            )

        if actual_version != reference.referenced_version:
            raise TuringCoreVocabularyError(
                f"{reference.source_reference_id} expected "
                f"version {reference.referenced_version!r}, "
                f"received {actual_version!r}."
            )


def _validate_framework_references(
    vocabulary: TuringCoreVocabulary,
    root: Path,
) -> None:
    framework_reference = _source_reference_by_role(
        vocabulary,
        "accepted_framework_template",
    )
    template = load_framework_template(
        root / framework_reference.path
    )
    policy = vocabulary.framework_mapping_policy

    if template["template_id"] != policy.framework_template_id:
        raise TuringCoreVocabularyError(
            "Turing Core framework-template ID does not match "
            "the loaded framework."
        )

    if (
        template["template_version"]
        != policy.framework_template_version
    ):
        raise TuringCoreVocabularyError(
            "Turing Core framework-template version does not "
            "match the loaded framework."
        )

    target_ids = mapping_target_ids(template)
    level_ids = {
        node["node_id"]
        for node in template["nodes"]
        if node["node_type"] == "level"
    }

    for concept in vocabulary.concepts:
        unknown_targets = (
            set(concept.candidate_framework_node_ids)
            - target_ids
        )

        if unknown_targets:
            raise TuringCoreVocabularyError(
                f"{concept.concept_id} references unknown or "
                "non-mapping framework targets: "
                + ", ".join(sorted(unknown_targets))
                + "."
            )

        unknown_scopes = (
            set(concept.framework_scope_node_ids)
            - level_ids
        )

        if unknown_scopes:
            raise TuringCoreVocabularyError(
                f"{concept.concept_id} references unknown "
                "framework level nodes: "
                + ", ".join(sorted(unknown_scopes))
                + "."
            )


def _validate_sysml_references(
    vocabulary: TuringCoreVocabulary,
    root: Path,
) -> None:
    target_reference = _source_reference_by_role(
        vocabulary,
        "allowed_sysml_v2_target_notation",
    )
    target_path = resolve_repository_path(
        root,
        target_reference.path,
        "SysML v2 target notation",
    )
    payload = json.loads(
        target_path.read_text(encoding="utf-8"),
        object_pairs_hook=object_without_duplicate_keys,
    )

    if not isinstance(payload, dict):
        raise TuringCoreVocabularyError(
            "SysML v2 target notation must be a JSON object."
        )

    policy = vocabulary.sysml_v2_mapping_policy

    if payload.get("context_id") != policy.target_notation_id:
        raise TuringCoreVocabularyError(
            "Turing Core target-notation ID does not match "
            "the loaded SysML v2 target notation."
        )

    if payload.get("version") != policy.target_notation_version:
        raise TuringCoreVocabularyError(
            "Turing Core target-notation version does not "
            "match the loaded SysML v2 target notation."
        )

    allowed_constructs = payload.get("allowed_constructs")

    if not isinstance(allowed_constructs, list):
        raise TuringCoreVocabularyError(
            "SysML v2 target notation allowed_constructs "
            "must be a list."
        )

    construct_ids = {
        construct.get("construct_id")
        for construct in allowed_constructs
        if (
            isinstance(construct, dict)
            and construct.get("allowed") is True
            and isinstance(
                construct.get("construct_id"),
                str,
            )
        )
    }

    for concept in vocabulary.concepts:
        unknown_constructs = {
            candidate.construct_id
            for candidate in (
                concept.sysml_v2_representation_candidates
            )
        } - construct_ids

        if unknown_constructs:
            raise TuringCoreVocabularyError(
                f"{concept.concept_id} references unknown or "
                "disallowed SysML v2 constructs: "
                + ", ".join(sorted(unknown_constructs))
                + "."
            )


def _validate_ontology_references(
    vocabulary: TuringCoreVocabulary,
    root: Path,
) -> None:
    registry = load_ontology_registry(
        root / DEFAULT_ONTOLOGY_REGISTRY_PATH,
        repository_root=root,
        verify_snapshots=False,
    )
    policy = vocabulary.external_mapping_policy

    if registry.registry_id != policy.registry_id:
        raise TuringCoreVocabularyError(
            "Turing Core Ontology Registry ID does not match "
            "the loaded registry."
        )

    systems = {
        system.reference_system_id: system
        for system in registry.reference_systems
    }
    unknown_allowed_systems = (
        set(policy.allowed_reference_system_ids)
        - systems.keys()
    )

    if unknown_allowed_systems:
        raise TuringCoreVocabularyError(
            "Turing Core permits unknown ontology reference "
            "systems: "
            + ", ".join(sorted(unknown_allowed_systems))
            + "."
        )

    for concept in vocabulary.concepts:
        for mapping in concept.external_mappings:
            if (
                mapping.reference_system_id
                not in policy.allowed_reference_system_ids
            ):
                raise TuringCoreVocabularyError(
                    f"{concept.concept_id} mapping uses "
                    "non-permitted reference system "
                    f"{mapping.reference_system_id!r}."
                )

            system = systems[mapping.reference_system_id]

            if (
                mapping.reference_system_version
                != system.version
            ):
                raise TuringCoreVocabularyError(
                    f"{concept.concept_id} mapping expects "
                    f"{mapping.reference_system_id} version "
                    f"{mapping.reference_system_version!r}, "
                    f"but the registry provides "
                    f"{system.version!r}."
                )


def _source_reference_by_role(
    vocabulary: TuringCoreVocabulary,
    role: str,
) -> TuringCoreSourceReference:
    matches = tuple(
        reference
        for reference in vocabulary.source_references
        if reference.role == role
    )

    if len(matches) != 1:
        raise TuringCoreVocabularyError(
            "Turing Core must declare exactly one source "
            f"reference with role {role!r}; found "
            f"{len(matches)}."
        )

    return matches[0]


def _require_curated_source_path(
    value: Any,
    label: str,
) -> Path:
    text = require_string(value, label)
    root = text.split("/", 1)[0]

    if root not in _ALLOWED_SOURCE_ROOTS:
        raise OntologyRegistryError(
            f"{label} must be below collaboration/ or context/."
        )

    return require_repository_path(
        text,
        label,
        required_prefix=(root,),
    )


def _concept_id_tuple(
    value: Any,
    label: str,
) -> tuple[str, ...]:
    values = _string_tuple(
        value,
        label,
        allow_empty=True,
    )

    for concept_id in values:
        if not _CONCEPT_ID_PATTERN.fullmatch(concept_id):
            raise OntologyRegistryError(
                f"{label} contains invalid concept ID "
                f"{concept_id!r}."
            )

    return values


def _string_tuple(
    value: Any,
    label: str,
    *,
    allow_empty: bool,
    casefold_unique: bool = False,
) -> tuple[str, ...]:
    items = require_list(value, label)

    if not allow_empty and not items:
        raise OntologyRegistryError(
            f"{label} must not be empty."
        )

    values = tuple(
        require_string(item, f"{label}[{index}]")
        for index, item in enumerate(items)
    )
    uniqueness_values = (
        tuple(item.casefold() for item in values)
        if casefold_unique
        else values
    )
    require_unique(uniqueness_values, label)

    return values


def _first_present(
    payload: dict[str, Any],
    fields: tuple[str, ...],
) -> Any:
    for field in fields:
        if field in payload:
            return payload[field]

    return None
