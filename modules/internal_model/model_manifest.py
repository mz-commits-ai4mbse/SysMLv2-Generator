"""Strict immutable manifest contract for complete Internal Engineering Models."""

from __future__ import annotations

from modules.model_candidates.identifiers import validate_model_candidate_set_id

from ._manifest_support import (
    assembly_provenance_payload,
    assembly_rules_reference_payload,
    canonical_fingerprint,
    derivation_rules_reference_payload,
    deterministic_json,
    exact_object,
    framework_template_reference_payload,
    model_structure_profile_reference_payload,
    parse_assembly_provenance,
    parse_assembly_rules_reference,
    parse_derivation_rules_reference,
    parse_framework_template_reference,
    parse_model_structure_profile_reference,
    parse_review_reference_tuple,
    review_reference_payload,
    sha256,
    strict_json_loads,
    timestamp,
    validate_project_id,
)
from .errors import InternalModelIntegrityError, InternalModelValidationError
from .identifiers import (
    validate_internal_engineering_model_id,
    validate_internal_model_element_id,
    validate_internal_model_relationship_id,
)
from .types import (
    InternalEngineeringModelManifest,
    InternalModelAssemblyContext,
)


INTERNAL_ENGINEERING_MODEL_SCHEMA_VERSION = "1.0.0"


def create_internal_engineering_model_manifest(
    *,
    project_id: str,
    internal_engineering_model_id: str,
    assembly_input_fingerprint: str,
    candidate_set_id: str,
    candidate_set_content_fingerprint: str,
    approved_input_snapshot_fingerprint: str,
    assembly_context: InternalModelAssemblyContext,
    assembly_provenance,
    structure_content_fingerprint: str,
    internal_model_element_ids,
    internal_model_relationship_ids,
    review_decision_references,
    accepted_exception_references,
    created_at: str,
) -> InternalEngineeringModelManifest:
    provisional = InternalEngineeringModelManifest(
        schema_version=INTERNAL_ENGINEERING_MODEL_SCHEMA_VERSION,
        project_id=project_id,
        internal_engineering_model_id=internal_engineering_model_id,
        assembly_input_fingerprint=assembly_input_fingerprint,
        candidate_set_id=candidate_set_id,
        candidate_set_content_fingerprint=candidate_set_content_fingerprint,
        approved_input_snapshot_fingerprint=(
            approved_input_snapshot_fingerprint
        ),
        assembly_context=assembly_context,
        assembly_provenance=assembly_provenance,
        structure_content_fingerprint=structure_content_fingerprint,
        internal_model_element_ids=tuple(internal_model_element_ids),
        internal_model_relationship_ids=tuple(
            internal_model_relationship_ids
        ),
        review_decision_references=tuple(review_decision_references),
        accepted_exception_references=tuple(
            accepted_exception_references
        ),
        created_at=created_at,
        content_fingerprint="0" * 64,
    )
    checked = _validated_without_fingerprint(provisional)
    result = InternalEngineeringModelManifest(
        schema_version=checked.schema_version,
        project_id=checked.project_id,
        internal_engineering_model_id=checked.internal_engineering_model_id,
        assembly_input_fingerprint=checked.assembly_input_fingerprint,
        candidate_set_id=checked.candidate_set_id,
        candidate_set_content_fingerprint=(
            checked.candidate_set_content_fingerprint
        ),
        approved_input_snapshot_fingerprint=(
            checked.approved_input_snapshot_fingerprint
        ),
        assembly_context=checked.assembly_context,
        assembly_provenance=checked.assembly_provenance,
        structure_content_fingerprint=(
            checked.structure_content_fingerprint
        ),
        internal_model_element_ids=checked.internal_model_element_ids,
        internal_model_relationship_ids=(
            checked.internal_model_relationship_ids
        ),
        review_decision_references=checked.review_decision_references,
        accepted_exception_references=(
            checked.accepted_exception_references
        ),
        created_at=checked.created_at,
        content_fingerprint=(
            calculate_internal_engineering_model_fingerprint(checked)
        ),
    )
    return validate_internal_engineering_model_manifest(result)


def calculate_internal_engineering_model_fingerprint(
    value: InternalEngineeringModelManifest,
) -> str:
    return canonical_fingerprint(_payload(value, include_fingerprint=False))


def validate_internal_engineering_model_manifest(
    value: InternalEngineeringModelManifest,
) -> InternalEngineeringModelManifest:
    checked = _validated_without_fingerprint(value)
    fingerprint = sha256(
        value.content_fingerprint,
        label="content_fingerprint",
    )
    if fingerprint != calculate_internal_engineering_model_fingerprint(
        checked
    ):
        raise InternalModelIntegrityError(
            "Internal Engineering Model content_fingerprint mismatch."
        )
    return value


def internal_engineering_model_manifest_to_dict(
    value: InternalEngineeringModelManifest,
) -> dict[str, object]:
    validate_internal_engineering_model_manifest(value)
    return _payload(value, include_fingerprint=True)


def internal_engineering_model_manifest_to_json(
    value: InternalEngineeringModelManifest,
) -> str:
    return deterministic_json(
        internal_engineering_model_manifest_to_dict(value)
    )


def internal_engineering_model_manifest_from_json(
    text_value: object,
) -> InternalEngineeringModelManifest:
    return parse_internal_engineering_model_manifest(
        strict_json_loads(
            text_value,
            label="Internal Engineering Model Manifest",
        )
    )


def parse_internal_engineering_model_manifest(
    value: object,
) -> InternalEngineeringModelManifest:
    data = exact_object(
        value,
        expected_fields=frozenset(
            InternalEngineeringModelManifest.__dataclass_fields__
        ),
        label="Internal Engineering Model Manifest",
    )
    context_data = exact_object(
        data["assembly_context"],
        expected_fields=frozenset(
            {
                "framework_template_reference",
                "model_structure_profile_reference",
                "derivation_rules_reference",
                "assembly_rules_reference",
            }
        ),
        label="Internal Model Assembly Context",
    )
    context = InternalModelAssemblyContext(
        framework_template_reference=parse_framework_template_reference(
            context_data["framework_template_reference"]
        ),
        model_structure_profile_reference=(
            parse_model_structure_profile_reference(
                context_data["model_structure_profile_reference"]
            )
        ),
        derivation_rules_reference=parse_derivation_rules_reference(
            context_data["derivation_rules_reference"]
        ),
        assembly_rules_reference=parse_assembly_rules_reference(
            context_data["assembly_rules_reference"]
        ),
    )

    raw_element_ids = data["internal_model_element_ids"]
    raw_relationship_ids = data["internal_model_relationship_ids"]
    if not isinstance(raw_element_ids, list):
        raise InternalModelValidationError(
            "internal_model_element_ids must be a JSON array."
        )
    if not isinstance(raw_relationship_ids, list):
        raise InternalModelValidationError(
            "internal_model_relationship_ids must be a JSON array."
        )

    result = InternalEngineeringModelManifest(
        schema_version=data["schema_version"],
        project_id=data["project_id"],
        internal_engineering_model_id=data["internal_engineering_model_id"],
        assembly_input_fingerprint=data["assembly_input_fingerprint"],
        candidate_set_id=data["candidate_set_id"],
        candidate_set_content_fingerprint=(
            data["candidate_set_content_fingerprint"]
        ),
        approved_input_snapshot_fingerprint=(
            data["approved_input_snapshot_fingerprint"]
        ),
        assembly_context=context,
        assembly_provenance=parse_assembly_provenance(
            data["assembly_provenance"]
        ),
        structure_content_fingerprint=data["structure_content_fingerprint"],
        internal_model_element_ids=tuple(raw_element_ids),
        internal_model_relationship_ids=tuple(raw_relationship_ids),
        review_decision_references=parse_review_reference_tuple(
            data["review_decision_references"],
            label="review_decision_references",
        ),
        accepted_exception_references=parse_review_reference_tuple(
            data["accepted_exception_references"],
            label="accepted_exception_references",
        ),
        created_at=data["created_at"],
        content_fingerprint=data["content_fingerprint"],
    )
    return validate_internal_engineering_model_manifest(result)


def _validated_without_fingerprint(
    value: InternalEngineeringModelManifest,
) -> InternalEngineeringModelManifest:
    if not isinstance(value, InternalEngineeringModelManifest):
        raise InternalModelValidationError(
            "value must be InternalEngineeringModelManifest."
        )
    if value.schema_version != INTERNAL_ENGINEERING_MODEL_SCHEMA_VERSION:
        raise InternalModelValidationError(
            "Unsupported Internal Engineering Model schema_version."
        )

    validate_project_id(value.project_id)
    validate_internal_engineering_model_id(
        value.internal_engineering_model_id
    )
    sha256(
        value.assembly_input_fingerprint,
        label="assembly_input_fingerprint",
    )
    try:
        validate_model_candidate_set_id(value.candidate_set_id)
    except Exception as exc:
        raise InternalModelValidationError(
            "candidate_set_id is invalid."
        ) from exc
    sha256(
        value.candidate_set_content_fingerprint,
        label="candidate_set_content_fingerprint",
    )
    sha256(
        value.approved_input_snapshot_fingerprint,
        label="approved_input_snapshot_fingerprint",
    )

    context = _validated_context(value.assembly_context)
    provenance = parse_assembly_provenance(
        assembly_provenance_payload(value.assembly_provenance)
    )
    sha256(
        value.structure_content_fingerprint,
        label="structure_content_fingerprint",
    )

    element_ids = tuple(
        validate_internal_model_element_id(item)
        for item in value.internal_model_element_ids
    )
    relationship_ids = tuple(
        validate_internal_model_relationship_id(item)
        for item in value.internal_model_relationship_ids
    )
    if element_ids != tuple(sorted(element_ids)):
        raise InternalModelValidationError(
            "internal_model_element_ids must use deterministic sorted order."
        )
    if relationship_ids != tuple(sorted(relationship_ids)):
        raise InternalModelValidationError(
            "internal_model_relationship_ids must use deterministic sorted order."
        )
    if len(element_ids) != len(set(element_ids)):
        raise InternalModelIntegrityError(
            "internal_model_element_ids must be unique."
        )
    if len(relationship_ids) != len(set(relationship_ids)):
        raise InternalModelIntegrityError(
            "internal_model_relationship_ids must be unique."
        )

    reviews = parse_review_reference_tuple(
        [
            review_reference_payload(item)
            for item in value.review_decision_references
        ],
        label="review_decision_references",
    )
    exceptions = parse_review_reference_tuple(
        [
            review_reference_payload(item)
            for item in value.accepted_exception_references
        ],
        label="accepted_exception_references",
    )

    review_ids = {
        item.model_candidate_review_decision_id for item in reviews
    }
    for item in exceptions:
        if item.decision != "accepted_exception":
            raise InternalModelIntegrityError(
                "accepted_exception_references may contain only "
                "accepted_exception decisions."
            )
        if item.model_candidate_review_decision_id not in review_ids:
            raise InternalModelIntegrityError(
                "accepted_exception_references must be a subset of "
                "review_decision_references."
            )

    created = timestamp(value.created_at, label="created_at")

    return InternalEngineeringModelManifest(
        schema_version=value.schema_version,
        project_id=value.project_id,
        internal_engineering_model_id=value.internal_engineering_model_id,
        assembly_input_fingerprint=value.assembly_input_fingerprint,
        candidate_set_id=value.candidate_set_id,
        candidate_set_content_fingerprint=(
            value.candidate_set_content_fingerprint
        ),
        approved_input_snapshot_fingerprint=(
            value.approved_input_snapshot_fingerprint
        ),
        assembly_context=context,
        assembly_provenance=provenance,
        structure_content_fingerprint=value.structure_content_fingerprint,
        internal_model_element_ids=element_ids,
        internal_model_relationship_ids=relationship_ids,
        review_decision_references=reviews,
        accepted_exception_references=exceptions,
        created_at=created,
        content_fingerprint=value.content_fingerprint,
    )


def _validated_context(
    value: InternalModelAssemblyContext,
) -> InternalModelAssemblyContext:
    if not isinstance(value, InternalModelAssemblyContext):
        raise InternalModelValidationError(
            "assembly_context has invalid type."
        )
    return InternalModelAssemblyContext(
        framework_template_reference=parse_framework_template_reference(
            framework_template_reference_payload(
                value.framework_template_reference
            )
        ),
        model_structure_profile_reference=(
            parse_model_structure_profile_reference(
                model_structure_profile_reference_payload(
                    value.model_structure_profile_reference
                )
            )
        ),
        derivation_rules_reference=parse_derivation_rules_reference(
            derivation_rules_reference_payload(
                value.derivation_rules_reference
            )
        ),
        assembly_rules_reference=parse_assembly_rules_reference(
            assembly_rules_reference_payload(
                value.assembly_rules_reference
            )
        ),
    )


def _context_payload(
    value: InternalModelAssemblyContext,
) -> dict[str, object]:
    return {
        "framework_template_reference": framework_template_reference_payload(
            value.framework_template_reference
        ),
        "model_structure_profile_reference": (
            model_structure_profile_reference_payload(
                value.model_structure_profile_reference
            )
        ),
        "derivation_rules_reference": derivation_rules_reference_payload(
            value.derivation_rules_reference
        ),
        "assembly_rules_reference": assembly_rules_reference_payload(
            value.assembly_rules_reference
        ),
    }


def _payload(
    value: InternalEngineeringModelManifest,
    *,
    include_fingerprint: bool,
) -> dict[str, object]:
    payload = {
        "schema_version": value.schema_version,
        "project_id": value.project_id,
        "internal_engineering_model_id": value.internal_engineering_model_id,
        "assembly_input_fingerprint": value.assembly_input_fingerprint,
        "candidate_set_id": value.candidate_set_id,
        "candidate_set_content_fingerprint": (
            value.candidate_set_content_fingerprint
        ),
        "approved_input_snapshot_fingerprint": (
            value.approved_input_snapshot_fingerprint
        ),
        "assembly_context": _context_payload(value.assembly_context),
        "assembly_provenance": assembly_provenance_payload(
            value.assembly_provenance
        ),
        "structure_content_fingerprint": (
            value.structure_content_fingerprint
        ),
        "internal_model_element_ids": list(
            value.internal_model_element_ids
        ),
        "internal_model_relationship_ids": list(
            value.internal_model_relationship_ids
        ),
        "review_decision_references": [
            review_reference_payload(item)
            for item in value.review_decision_references
        ],
        "accepted_exception_references": [
            review_reference_payload(item)
            for item in value.accepted_exception_references
        ],
        "created_at": value.created_at,
    }
    if include_fingerprint:
        payload["content_fingerprint"] = value.content_fingerprint
    return payload
