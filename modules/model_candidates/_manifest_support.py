"""Shared strict parsing and validation helpers for Phase-H manifests."""

from __future__ import annotations

from dataclasses import fields
import hashlib
import json
import re
from typing import Any

from modules.approved_input.identifiers import validate_approved_input_id
from modules.approved_input.types import (
    ApprovedInputRelationshipProperty,
    ApprovedInputRelationshipRepresentation,
)
from modules.project_workspace.identifiers import is_valid_project_id
from modules.project_workspace.types import FrameworkTemplateReference

from .errors import (
    ModelCandidateIntegrityError,
    ModelCandidateValidationError,
)
from .identifiers import validate_model_element_candidate_id
from .types import (
    MODEL_RELATIONSHIP_PRIORITY_CLASSES,
    RELATIONSHIP_ENDPOINT_RESOLUTION_STATUSES,
    STRUCTURAL_COMPARABILITY_IMPACTS,
    ModelCandidateApprovedInputReference,
    ModelCandidateAttribute,
    ModelCandidateGenerationProvenance,
    ModelDerivationRulesReference,
    ModelRelationshipEndpoint,
    ModelStructureProfileReference,
    RelationshipPriorityAssessment,
    RelationshipPriorityCriterionResult,
    StructuralComparabilityAssessment,
    StructuralProfileConformance,
)


SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
SEMVER_PATTERN = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
UTC_TIMESTAMP_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T"
    r"\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$"
)
STABLE_SUBJECT_KEY_PATTERN = re.compile(
    r"^[a-z0-9][a-z0-9._:-]{0,239}$"
)
GENERAL_IDENTIFIER_PATTERN = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9._:-]*$"
)
UPPER_IDENTIFIER_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]*$")


def strict_json_loads(text: object, *, label: str) -> Any:
    """Load strict JSON and reject duplicate object keys."""

    if not isinstance(text, str):
        raise ModelCandidateValidationError(
            f"{label} JSON must be a string."
        )
    try:
        return json.loads(
            text,
            object_pairs_hook=_object_without_duplicate_keys,
        )
    except ModelCandidateValidationError:
        raise
    except json.JSONDecodeError as exc:
        raise ModelCandidateValidationError(
            f"{label} is not valid JSON."
        ) from exc


def deterministic_json(payload: dict[str, object]) -> str:
    return (
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )


def canonical_fingerprint(payload: dict[str, object]) -> str:
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def exact_object(
    value: object,
    *,
    expected_fields: frozenset[str],
    label: str,
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ModelCandidateValidationError(
            f"{label} must be a JSON object."
        )
    actual = frozenset(value)
    if actual != expected_fields:
        raise ModelCandidateValidationError(
            f"{label} has invalid fields; "
            f"missing={sorted(expected_fields - actual)}, "
            f"unknown={sorted(actual - expected_fields)}."
        )
    return value


def text(value: object, *, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ModelCandidateValidationError(
            f"{label} must be a non-empty string."
        )
    if value != value.strip():
        raise ModelCandidateValidationError(
            f"{label} must not contain surrounding whitespace."
        )
    return value


def optional_text(value: object, *, label: str) -> str | None:
    return None if value is None else text(value, label=label)


def identifier(value: object, *, label: str) -> str:
    value = text(value, label=label)
    if GENERAL_IDENTIFIER_PATTERN.fullmatch(value) is None:
        raise ModelCandidateValidationError(
            f"{label} has invalid identifier syntax."
        )
    return value


def optional_identifier(value: object, *, label: str) -> str | None:
    return None if value is None else identifier(value, label=label)


def upper_identifier(value: object, *, label: str) -> str:
    value = text(value, label=label)
    if UPPER_IDENTIFIER_PATTERN.fullmatch(value) is None:
        raise ModelCandidateValidationError(
            f"{label} must use uppercase identifier syntax."
        )
    return value


def semver(value: object, *, label: str) -> str:
    value = text(value, label=label)
    if SEMVER_PATTERN.fullmatch(value) is None:
        raise ModelCandidateValidationError(
            f"{label} must be a semantic version."
        )
    return value


def sha256(value: object, *, label: str) -> str:
    value = text(value, label=label)
    if SHA256_PATTERN.fullmatch(value) is None:
        raise ModelCandidateValidationError(
            f"{label} must be a lowercase SHA-256 value."
        )
    return value


def optional_sha256(value: object, *, label: str) -> str | None:
    return None if value is None else sha256(value, label=label)


def timestamp(value: object, *, label: str) -> str:
    value = text(value, label=label)
    if UTC_TIMESTAMP_PATTERN.fullmatch(value) is None:
        raise ModelCandidateValidationError(
            f"{label} must be an ISO-8601 UTC timestamp ending in Z."
        )
    return value


def stable_subject_key(value: object, *, label: str) -> str:
    value = text(value, label=label)
    if STABLE_SUBJECT_KEY_PATTERN.fullmatch(value) is None:
        raise ModelCandidateValidationError(
            f"{label} has invalid stable-subject-key syntax."
        )
    return value


def validate_project_id(value: object) -> str:
    if not is_valid_project_id(value):
        raise ModelCandidateValidationError(
            "project_id must be a valid six-digit Project ID."
        )
    return value


def sorted_unique_text_tuple(
    value: object,
    *,
    label: str,
) -> tuple[str, ...]:
    if not isinstance(value, (tuple, list)):
        raise ModelCandidateValidationError(
            f"{label} must be a tuple or JSON array."
        )
    checked = tuple(text(item, label=label) for item in value)
    if checked != tuple(sorted(checked)):
        raise ModelCandidateValidationError(
            f"{label} must use deterministic sorted order."
        )
    if len(checked) != len(set(checked)):
        raise ModelCandidateIntegrityError(
            f"{label} must contain unique values."
        )
    return checked


def approved_input_reference_payload(
    value: ModelCandidateApprovedInputReference,
) -> dict[str, object]:
    if not isinstance(value, ModelCandidateApprovedInputReference):
        raise ModelCandidateValidationError(
            "approved_input_reference has invalid type."
        )
    return {
        "approved_input_id": value.approved_input_id,
        "content_fingerprint": value.content_fingerprint,
        "stable_subject_key": value.stable_subject_key,
        "provenance_role": value.provenance_role,
    }


def parse_approved_input_reference(
    value: object,
) -> ModelCandidateApprovedInputReference:
    expected = frozenset(
        field.name
        for field in fields(ModelCandidateApprovedInputReference)
    )
    data = exact_object(
        value,
        expected_fields=expected,
        label="Model Candidate Approved Input Reference",
    )
    try:
        approved_input_id = validate_approved_input_id(
            data["approved_input_id"]
        )
    except Exception as exc:
        raise ModelCandidateValidationError(
            "approved_input_id is invalid."
        ) from exc
    return ModelCandidateApprovedInputReference(
        approved_input_id=approved_input_id,
        content_fingerprint=sha256(
            data["content_fingerprint"],
            label="Approved Input content_fingerprint",
        ),
        stable_subject_key=stable_subject_key(
            data["stable_subject_key"],
            label="Approved Input stable_subject_key",
        ),
        provenance_role=identifier(
            data["provenance_role"],
            label="provenance_role",
        ),
    )


def normalize_approved_input_references(
    values: tuple[ModelCandidateApprovedInputReference, ...],
) -> tuple[ModelCandidateApprovedInputReference, ...]:
    if not isinstance(values, tuple):
        raise ModelCandidateValidationError(
            "approved_input_references must be a tuple."
        )
    parsed = tuple(
        parse_approved_input_reference(
            approved_input_reference_payload(value)
        )
        for value in values
    )
    if not parsed:
        raise ModelCandidateIntegrityError(
            "A Model Candidate artifact requires Approved Input provenance."
        )
    ids = tuple(item.approved_input_id for item in parsed)
    if len(ids) != len(set(ids)):
        raise ModelCandidateIntegrityError(
            "approved_input_references must not repeat an Approved Input ID."
        )
    return tuple(sorted(parsed, key=lambda item: item.approved_input_id))


def calculate_approved_input_snapshot_fingerprint(
    values: tuple[ModelCandidateApprovedInputReference, ...],
) -> str:
    """Fingerprint the exact Approved-Input snapshot, independent of role."""

    normalized = normalize_approved_input_references(values)
    payload = [
        {
            "approved_input_id": item.approved_input_id,
            "content_fingerprint": item.content_fingerprint,
            "stable_subject_key": item.stable_subject_key,
        }
        for item in normalized
    ]
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def framework_template_reference_payload(
    value: FrameworkTemplateReference,
) -> dict[str, object]:
    if not isinstance(value, FrameworkTemplateReference):
        raise ModelCandidateValidationError(
            "framework_template_reference has invalid type."
        )
    return {
        "template_id": value.template_id,
        "template_version": value.template_version,
    }


def parse_framework_template_reference(
    value: object,
) -> FrameworkTemplateReference:
    expected = frozenset(
        field.name for field in fields(FrameworkTemplateReference)
    )
    data = exact_object(
        value,
        expected_fields=expected,
        label="Framework Template Reference",
    )
    return FrameworkTemplateReference(
        template_id=upper_identifier(
            data["template_id"],
            label="framework template_id",
        ),
        template_version=semver(
            data["template_version"],
            label="framework template_version",
        ),
    )


def model_structure_profile_reference_payload(
    value: ModelStructureProfileReference,
) -> dict[str, object]:
    if not isinstance(value, ModelStructureProfileReference):
        raise ModelCandidateValidationError(
            "model_structure_profile_reference has invalid type."
        )
    return {
        "profile_id": value.profile_id,
        "profile_version": value.profile_version,
        "profile_fingerprint": value.profile_fingerprint,
    }


def parse_model_structure_profile_reference(
    value: object,
) -> ModelStructureProfileReference:
    expected = frozenset(
        field.name for field in fields(ModelStructureProfileReference)
    )
    data = exact_object(
        value,
        expected_fields=expected,
        label="Model Structure Profile Reference",
    )
    return ModelStructureProfileReference(
        profile_id=upper_identifier(
            data["profile_id"],
            label="profile_id",
        ),
        profile_version=semver(
            data["profile_version"],
            label="profile_version",
        ),
        profile_fingerprint=sha256(
            data["profile_fingerprint"],
            label="profile_fingerprint",
        ),
    )


def derivation_rules_reference_payload(
    value: ModelDerivationRulesReference,
) -> dict[str, object]:
    if not isinstance(value, ModelDerivationRulesReference):
        raise ModelCandidateValidationError(
            "derivation_rules_reference has invalid type."
        )
    return {
        "context_id": value.context_id,
        "context_version": value.context_version,
        "context_fingerprint": value.context_fingerprint,
    }


def parse_derivation_rules_reference(
    value: object,
) -> ModelDerivationRulesReference:
    expected = frozenset(
        field.name for field in fields(ModelDerivationRulesReference)
    )
    data = exact_object(
        value,
        expected_fields=expected,
        label="Model Derivation Rules Reference",
    )
    return ModelDerivationRulesReference(
        context_id=upper_identifier(
            data["context_id"],
            label="derivation context_id",
        ),
        context_version=semver(
            data["context_version"],
            label="derivation context_version",
        ),
        context_fingerprint=sha256(
            data["context_fingerprint"],
            label="derivation context_fingerprint",
        ),
    )


def generation_provenance_payload(
    value: ModelCandidateGenerationProvenance,
) -> dict[str, object]:
    if not isinstance(value, ModelCandidateGenerationProvenance):
        raise ModelCandidateValidationError(
            "generation_provenance has invalid type."
        )
    return {
        "method": value.method,
        "recipe_reference": value.recipe_reference,
        "agent_reference": value.agent_reference,
        "model_reference": value.model_reference,
        "context_fingerprint": value.context_fingerprint,
    }


def parse_generation_provenance(
    value: object,
) -> ModelCandidateGenerationProvenance:
    expected = frozenset(
        field.name for field in fields(ModelCandidateGenerationProvenance)
    )
    data = exact_object(
        value,
        expected_fields=expected,
        label="Model Candidate Generation Provenance",
    )
    return ModelCandidateGenerationProvenance(
        method=identifier(data["method"], label="generation method"),
        recipe_reference=optional_text(
            data["recipe_reference"],
            label="recipe_reference",
        ),
        agent_reference=optional_text(
            data["agent_reference"],
            label="agent_reference",
        ),
        model_reference=optional_text(
            data["model_reference"],
            label="model_reference",
        ),
        context_fingerprint=optional_sha256(
            data["context_fingerprint"],
            label="generation context_fingerprint",
        ),
    )


def attribute_payload(value: ModelCandidateAttribute) -> dict[str, object]:
    if not isinstance(value, ModelCandidateAttribute):
        raise ModelCandidateValidationError("attribute has invalid type.")
    return {"name": value.name, "value": value.value}


def parse_attribute(value: object) -> ModelCandidateAttribute:
    expected = frozenset(
        field.name for field in fields(ModelCandidateAttribute)
    )
    data = exact_object(
        value,
        expected_fields=expected,
        label="Model Candidate Attribute",
    )
    return ModelCandidateAttribute(
        name=identifier(data["name"], label="attribute name"),
        value=text(data["value"], label="attribute value"),
    )


def normalize_attributes(
    values: tuple[ModelCandidateAttribute, ...],
) -> tuple[ModelCandidateAttribute, ...]:
    if not isinstance(values, tuple):
        raise ModelCandidateValidationError("attributes must be a tuple.")
    parsed = tuple(
        parse_attribute(attribute_payload(value))
        for value in values
    )
    names = tuple(item.name for item in parsed)
    if len(names) != len(set(names)):
        raise ModelCandidateIntegrityError(
            "attributes must not repeat an attribute name."
        )
    return tuple(sorted(parsed, key=lambda item: item.name))


def conformance_payload(
    value: StructuralProfileConformance,
) -> dict[str, object]:
    if not isinstance(value, StructuralProfileConformance):
        raise ModelCandidateValidationError(
            "structure_profile_conformance has invalid type."
        )
    return {
        "status": value.status,
        "finding_ids": list(value.finding_ids),
        "conformance_fingerprint": value.conformance_fingerprint,
    }


def parse_conformance(value: object) -> StructuralProfileConformance:
    expected = frozenset(
        field.name for field in fields(StructuralProfileConformance)
    )
    data = exact_object(
        value,
        expected_fields=expected,
        label="Structural Profile Conformance",
    )
    return StructuralProfileConformance(
        status=identifier(
            data["status"],
            label="structure profile conformance status",
        ),
        finding_ids=sorted_unique_text_tuple(
            data["finding_ids"],
            label="finding_ids",
        ),
        conformance_fingerprint=sha256(
            data["conformance_fingerprint"],
            label="conformance_fingerprint",
        ),
    )


def endpoint_payload(value: ModelRelationshipEndpoint) -> dict[str, object]:
    if not isinstance(value, ModelRelationshipEndpoint):
        raise ModelCandidateValidationError(
            "relationship endpoint has invalid type."
        )
    return {
        "candidate_subject_key": value.candidate_subject_key,
        "resolution_status": value.resolution_status,
        "resolved_model_element_candidate_id": (
            value.resolved_model_element_candidate_id
        ),
        "candidate_model_element_ids": list(
            value.candidate_model_element_ids
        ),
    }


def parse_endpoint(value: object) -> ModelRelationshipEndpoint:
    expected = frozenset(
        field.name for field in fields(ModelRelationshipEndpoint)
    )
    data = exact_object(
        value,
        expected_fields=expected,
        label="Model Relationship Endpoint",
    )
    status = text(data["resolution_status"], label="resolution_status")
    if status not in RELATIONSHIP_ENDPOINT_RESOLUTION_STATUSES:
        raise ModelCandidateValidationError(
            "resolution_status is invalid."
        )

    raw_ids = data["candidate_model_element_ids"]
    if not isinstance(raw_ids, (tuple, list)):
        raise ModelCandidateValidationError(
            "candidate_model_element_ids must be a tuple or JSON array."
        )
    try:
        candidate_ids = tuple(
            validate_model_element_candidate_id(item)
            for item in raw_ids
        )
    except Exception as exc:
        raise ModelCandidateValidationError(
            "candidate_model_element_ids contains an invalid MCE ID."
        ) from exc
    if candidate_ids != tuple(sorted(candidate_ids)):
        raise ModelCandidateValidationError(
            "candidate_model_element_ids must use deterministic sorted order."
        )
    if len(candidate_ids) != len(set(candidate_ids)):
        raise ModelCandidateIntegrityError(
            "candidate_model_element_ids must be unique."
        )

    resolved = data["resolved_model_element_candidate_id"]
    if resolved is not None:
        try:
            resolved = validate_model_element_candidate_id(resolved)
        except Exception as exc:
            raise ModelCandidateValidationError(
                "resolved_model_element_candidate_id is invalid."
            ) from exc

    if status == "resolved":
        if resolved is None or candidate_ids != (resolved,):
            raise ModelCandidateIntegrityError(
                "A resolved endpoint requires exactly its resolved MCE ID "
                "as the sole candidate."
            )
    elif status == "unresolved":
        if resolved is not None or candidate_ids:
            raise ModelCandidateIntegrityError(
                "An unresolved endpoint must not claim an MCE candidate."
            )
    elif status == "ambiguous":
        if resolved is not None or len(candidate_ids) < 2:
            raise ModelCandidateIntegrityError(
                "An ambiguous endpoint requires at least two candidate MCE "
                "IDs and no resolved MCE ID."
            )

    return ModelRelationshipEndpoint(
        candidate_subject_key=stable_subject_key(
            data["candidate_subject_key"],
            label="endpoint candidate_subject_key",
        ),
        resolution_status=status,
        resolved_model_element_candidate_id=resolved,
        candidate_model_element_ids=candidate_ids,
    )


def priority_criterion_payload(
    value: RelationshipPriorityCriterionResult,
) -> dict[str, object]:
    if not isinstance(value, RelationshipPriorityCriterionResult):
        raise ModelCandidateValidationError(
            "priority criterion has invalid type."
        )
    return {
        "criterion": value.criterion,
        "result": value.result,
        "rationale": value.rationale,
    }


def parse_priority_criterion(
    value: object,
) -> RelationshipPriorityCriterionResult:
    expected = frozenset(
        field.name
        for field in fields(RelationshipPriorityCriterionResult)
    )
    data = exact_object(
        value,
        expected_fields=expected,
        label="Relationship Priority Criterion Result",
    )
    return RelationshipPriorityCriterionResult(
        criterion=identifier(
            data["criterion"],
            label="priority criterion",
        ),
        result=identifier(
            data["result"],
            label="priority result",
        ),
        rationale=text(
            data["rationale"],
            label="priority criterion rationale",
        ),
    )


def priority_assessment_payload(
    value: RelationshipPriorityAssessment,
) -> dict[str, object]:
    if not isinstance(value, RelationshipPriorityAssessment):
        raise ModelCandidateValidationError(
            "priority_assessment has invalid type."
        )
    return {
        "priority_class": value.priority_class,
        "criterion_results": [
            priority_criterion_payload(item)
            for item in value.criterion_results
        ],
        "rationale": value.rationale,
    }


def parse_priority_assessment(
    value: object,
) -> RelationshipPriorityAssessment:
    expected = frozenset(
        field.name for field in fields(RelationshipPriorityAssessment)
    )
    data = exact_object(
        value,
        expected_fields=expected,
        label="Relationship Priority Assessment",
    )
    priority_class = text(
        data["priority_class"],
        label="priority_class",
    )
    if priority_class not in MODEL_RELATIONSHIP_PRIORITY_CLASSES:
        raise ModelCandidateValidationError(
            "priority_class is invalid."
        )
    raw = data["criterion_results"]
    if not isinstance(raw, (tuple, list)):
        raise ModelCandidateValidationError(
            "criterion_results must be a tuple or JSON array."
        )
    criteria = tuple(parse_priority_criterion(item) for item in raw)
    if not criteria:
        raise ModelCandidateIntegrityError(
            "Relationship priority assessment requires criterion results."
        )
    names = tuple(item.criterion for item in criteria)
    if len(names) != len(set(names)):
        raise ModelCandidateIntegrityError(
            "Relationship priority criteria must be unique."
        )
    return RelationshipPriorityAssessment(
        priority_class=priority_class,
        criterion_results=criteria,
        rationale=text(
            data["rationale"],
            label="priority assessment rationale",
        ),
    )


def comparability_assessment_payload(
    value: StructuralComparabilityAssessment,
) -> dict[str, object]:
    if not isinstance(value, StructuralComparabilityAssessment):
        raise ModelCandidateValidationError(
            "comparability_assessment has invalid type."
        )
    return {
        "impact": value.impact,
        "comparison_anchor_ids": list(value.comparison_anchor_ids),
        "canonical_pattern_match": value.canonical_pattern_match,
        "deviation_ids": list(value.deviation_ids),
        "rationale": value.rationale,
    }


def parse_comparability_assessment(
    value: object,
) -> StructuralComparabilityAssessment:
    expected = frozenset(
        field.name for field in fields(StructuralComparabilityAssessment)
    )
    data = exact_object(
        value,
        expected_fields=expected,
        label="Structural Comparability Assessment",
    )
    impact = text(data["impact"], label="comparability impact")
    if impact not in STRUCTURAL_COMPARABILITY_IMPACTS:
        raise ModelCandidateValidationError(
            "comparability impact is invalid."
        )
    pattern_match = data["canonical_pattern_match"]
    if pattern_match is not None and not isinstance(pattern_match, bool):
        raise ModelCandidateValidationError(
            "canonical_pattern_match must be boolean or null."
        )
    return StructuralComparabilityAssessment(
        impact=impact,
        comparison_anchor_ids=sorted_unique_text_tuple(
            data["comparison_anchor_ids"],
            label="comparison_anchor_ids",
        ),
        canonical_pattern_match=pattern_match,
        deviation_ids=sorted_unique_text_tuple(
            data["deviation_ids"],
            label="deviation_ids",
        ),
        rationale=text(
            data["rationale"],
            label="comparability rationale",
        ),
    )


def upstream_relationship_payload(
    value: ApprovedInputRelationshipRepresentation,
) -> dict[str, object]:
    if not isinstance(value, ApprovedInputRelationshipRepresentation):
        raise ModelCandidateValidationError(
            "upstream_relationship_representation has invalid type."
        )
    return {
        "source_subject_key": value.source_subject_key,
        "target_subject_key": value.target_subject_key,
        "semantic_intent": value.semantic_intent,
        "sysml_v2_construct": value.sysml_v2_construct,
        "construct_properties": [
            {"name": item.name, "value": item.value}
            for item in value.construct_properties
        ],
        "target_notation_profile_id": value.target_notation_profile_id,
        "target_notation_profile_version": (
            value.target_notation_profile_version
        ),
        "textual_notation_preview": value.textual_notation_preview,
        "profile_validation_status": value.profile_validation_status,
        "profile_validation_fingerprint": (
            value.profile_validation_fingerprint
        ),
    }


def parse_upstream_relationship(
    value: object,
) -> ApprovedInputRelationshipRepresentation:
    """Reconstruct upstream evidence without re-validating its semantics.

    Phase H deliberately does not duplicate the Approved Input semantic
    validator. H5 will bind this carried-forward representation back to the
    exact authoritative Approved Input manifest.
    """

    expected = frozenset(
        field.name
        for field in fields(ApprovedInputRelationshipRepresentation)
    )
    data = exact_object(
        value,
        expected_fields=expected,
        label="Upstream Approved Input Relationship Representation",
    )
    raw_properties = data["construct_properties"]
    if not isinstance(raw_properties, (tuple, list)):
        raise ModelCandidateValidationError(
            "construct_properties must be a tuple or JSON array."
        )

    property_fields = frozenset(
        field.name
        for field in fields(ApprovedInputRelationshipProperty)
    )
    properties = []
    for raw in raw_properties:
        item = exact_object(
            raw,
            expected_fields=property_fields,
            label="Upstream Relationship Property",
        )
        properties.append(
            ApprovedInputRelationshipProperty(
                name=text(
                    item["name"],
                    label="relationship property name",
                ),
                value=text(
                    item["value"],
                    label="relationship property value",
                ),
            )
        )

    return ApprovedInputRelationshipRepresentation(
        source_subject_key=text(
            data["source_subject_key"],
            label="upstream source_subject_key",
        ),
        target_subject_key=text(
            data["target_subject_key"],
            label="upstream target_subject_key",
        ),
        semantic_intent=text(
            data["semantic_intent"],
            label="upstream semantic_intent",
        ),
        sysml_v2_construct=text(
            data["sysml_v2_construct"],
            label="upstream sysml_v2_construct",
        ),
        construct_properties=tuple(properties),
        target_notation_profile_id=text(
            data["target_notation_profile_id"],
            label="upstream target_notation_profile_id",
        ),
        target_notation_profile_version=text(
            data["target_notation_profile_version"],
            label="upstream target_notation_profile_version",
        ),
        textual_notation_preview=text(
            data["textual_notation_preview"],
            label="upstream textual_notation_preview",
        ),
        profile_validation_status=text(
            data["profile_validation_status"],
            label="upstream profile_validation_status",
        ),
        profile_validation_fingerprint=text(
            data["profile_validation_fingerprint"],
            label="upstream profile_validation_fingerprint",
        ),
    )


def _object_without_duplicate_keys(
    pairs: list[tuple[str, object]],
) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ModelCandidateValidationError(
                f"Duplicate JSON key is not allowed: {key!r}."
            )
        result[key] = value
    return result
