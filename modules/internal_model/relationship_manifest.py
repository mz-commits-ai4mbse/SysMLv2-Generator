"""Strict immutable manifest contract for Internal Model Relationships."""

from __future__ import annotations

from modules.model_candidates.identifiers import (
    validate_model_relationship_candidate_id,
)

from ._manifest_support import (
    approved_input_reference_payload,
    canonical_fingerprint,
    deterministic_json,
    exact_object,
    identifier,
    parse_approved_input_reference_tuple,
    parse_review_reference,
    review_reference_payload,
    sha256,
    stable_subject_key,
    strict_json_loads,
    validate_project_id,
)
from .errors import InternalModelIntegrityError, InternalModelValidationError
from .identifiers import (
    validate_internal_engineering_model_id,
    validate_internal_model_element_id,
    validate_internal_model_relationship_id,
)
from .types import InternalModelRelationship


INTERNAL_MODEL_RELATIONSHIP_SCHEMA_VERSION = "1.0.0"


def create_internal_model_relationship(
    *,
    project_id: str,
    internal_engineering_model_id: str,
    internal_model_relationship_id: str,
    source_internal_model_element_id: str,
    target_internal_model_element_id: str,
    source_model_subject_key: str,
    target_model_subject_key: str,
    relationship_family: str,
    semantic_intent: str,
    directionality: str,
    source_model_relationship_candidate_id: str,
    source_model_relationship_candidate_fingerprint: str,
    approved_input_references,
    review_decision_reference,
    accepted_exception_reference,
) -> InternalModelRelationship:
    provisional = InternalModelRelationship(
        schema_version=INTERNAL_MODEL_RELATIONSHIP_SCHEMA_VERSION,
        project_id=project_id,
        internal_engineering_model_id=internal_engineering_model_id,
        internal_model_relationship_id=internal_model_relationship_id,
        source_internal_model_element_id=source_internal_model_element_id,
        target_internal_model_element_id=target_internal_model_element_id,
        source_model_subject_key=source_model_subject_key,
        target_model_subject_key=target_model_subject_key,
        relationship_family=relationship_family,
        semantic_intent=semantic_intent,
        directionality=directionality,
        source_model_relationship_candidate_id=(
            source_model_relationship_candidate_id
        ),
        source_model_relationship_candidate_fingerprint=(
            source_model_relationship_candidate_fingerprint
        ),
        approved_input_references=tuple(approved_input_references),
        review_decision_reference=review_decision_reference,
        accepted_exception_reference=accepted_exception_reference,
        content_fingerprint="0" * 64,
    )
    checked = _validated_without_fingerprint(provisional)
    result = InternalModelRelationship(
        schema_version=checked.schema_version,
        project_id=checked.project_id,
        internal_engineering_model_id=checked.internal_engineering_model_id,
        internal_model_relationship_id=(
            checked.internal_model_relationship_id
        ),
        source_internal_model_element_id=(
            checked.source_internal_model_element_id
        ),
        target_internal_model_element_id=(
            checked.target_internal_model_element_id
        ),
        source_model_subject_key=checked.source_model_subject_key,
        target_model_subject_key=checked.target_model_subject_key,
        relationship_family=checked.relationship_family,
        semantic_intent=checked.semantic_intent,
        directionality=checked.directionality,
        source_model_relationship_candidate_id=(
            checked.source_model_relationship_candidate_id
        ),
        source_model_relationship_candidate_fingerprint=(
            checked.source_model_relationship_candidate_fingerprint
        ),
        approved_input_references=checked.approved_input_references,
        review_decision_reference=checked.review_decision_reference,
        accepted_exception_reference=checked.accepted_exception_reference,
        content_fingerprint=(
            calculate_internal_model_relationship_fingerprint(checked)
        ),
    )
    return validate_internal_model_relationship(result)


def calculate_internal_model_relationship_fingerprint(
    value: InternalModelRelationship,
) -> str:
    return canonical_fingerprint(_payload(value, include_fingerprint=False))


def validate_internal_model_relationship(
    value: InternalModelRelationship,
) -> InternalModelRelationship:
    checked = _validated_without_fingerprint(value)
    fingerprint = sha256(
        value.content_fingerprint,
        label="content_fingerprint",
    )
    if fingerprint != calculate_internal_model_relationship_fingerprint(
        checked
    ):
        raise InternalModelIntegrityError(
            "Internal Model Relationship content_fingerprint mismatch."
        )
    return value


def internal_model_relationship_to_dict(
    value: InternalModelRelationship,
) -> dict[str, object]:
    validate_internal_model_relationship(value)
    return _payload(value, include_fingerprint=True)


def internal_model_relationship_to_json(
    value: InternalModelRelationship,
) -> str:
    return deterministic_json(internal_model_relationship_to_dict(value))


def internal_model_relationship_from_json(
    text_value: object,
) -> InternalModelRelationship:
    return parse_internal_model_relationship(
        strict_json_loads(
            text_value,
            label="Internal Model Relationship",
        )
    )


def parse_internal_model_relationship(
    value: object,
) -> InternalModelRelationship:
    data = exact_object(
        value,
        expected_fields=frozenset(
            InternalModelRelationship.__dataclass_fields__
        ),
        label="Internal Model Relationship",
    )
    result = InternalModelRelationship(
        schema_version=data["schema_version"],
        project_id=data["project_id"],
        internal_engineering_model_id=data["internal_engineering_model_id"],
        internal_model_relationship_id=(
            data["internal_model_relationship_id"]
        ),
        source_internal_model_element_id=(
            data["source_internal_model_element_id"]
        ),
        target_internal_model_element_id=(
            data["target_internal_model_element_id"]
        ),
        source_model_subject_key=data["source_model_subject_key"],
        target_model_subject_key=data["target_model_subject_key"],
        relationship_family=data["relationship_family"],
        semantic_intent=data["semantic_intent"],
        directionality=data["directionality"],
        source_model_relationship_candidate_id=(
            data["source_model_relationship_candidate_id"]
        ),
        source_model_relationship_candidate_fingerprint=(
            data["source_model_relationship_candidate_fingerprint"]
        ),
        approved_input_references=parse_approved_input_reference_tuple(
            data["approved_input_references"],
            label="approved_input_references",
        ),
        review_decision_reference=parse_review_reference(
            data["review_decision_reference"]
        ),
        accepted_exception_reference=(
            None
            if data["accepted_exception_reference"] is None
            else parse_review_reference(
                data["accepted_exception_reference"]
            )
        ),
        content_fingerprint=data["content_fingerprint"],
    )
    return validate_internal_model_relationship(result)


def _validated_without_fingerprint(
    value: InternalModelRelationship,
) -> InternalModelRelationship:
    if not isinstance(value, InternalModelRelationship):
        raise InternalModelValidationError(
            "value must be InternalModelRelationship."
        )
    if value.schema_version != INTERNAL_MODEL_RELATIONSHIP_SCHEMA_VERSION:
        raise InternalModelValidationError(
            "Unsupported Internal Model Relationship schema_version."
        )
    validate_project_id(value.project_id)
    validate_internal_engineering_model_id(
        value.internal_engineering_model_id
    )
    validate_internal_model_relationship_id(
        value.internal_model_relationship_id
    )
    validate_internal_model_element_id(
        value.source_internal_model_element_id
    )
    validate_internal_model_element_id(
        value.target_internal_model_element_id
    )
    stable_subject_key(
        value.source_model_subject_key,
        label="source_model_subject_key",
    )
    stable_subject_key(
        value.target_model_subject_key,
        label="target_model_subject_key",
    )
    identifier(value.relationship_family, label="relationship_family")
    identifier(value.semantic_intent, label="semantic_intent")
    identifier(value.directionality, label="directionality")

    try:
        validate_model_relationship_candidate_id(
            value.source_model_relationship_candidate_id
        )
    except Exception as exc:
        raise InternalModelValidationError(
            "source_model_relationship_candidate_id is invalid."
        ) from exc

    sha256(
        value.source_model_relationship_candidate_fingerprint,
        label="source_model_relationship_candidate_fingerprint",
    )
    approved = parse_approved_input_reference_tuple(
        [
            approved_input_reference_payload(item)
            for item in value.approved_input_references
        ],
        label="approved_input_references",
    )
    review = parse_review_reference(
        review_reference_payload(value.review_decision_reference)
    )
    if (
        review.target_type != "relationship_candidate"
        or review.candidate_id
        != value.source_model_relationship_candidate_id
        or review.decision not in {"accepted", "accepted_exception"}
    ):
        raise InternalModelIntegrityError(
            "Relationship review reference must authorize the exact source MCR."
        )

    exception = value.accepted_exception_reference
    if review.decision == "accepted_exception":
        if exception != review:
            raise InternalModelIntegrityError(
                "accepted_exception must preserve the exact review reference."
            )
    elif exception is not None:
        raise InternalModelIntegrityError(
            "accepted_exception_reference is only valid for accepted_exception."
        )

    return InternalModelRelationship(
        schema_version=value.schema_version,
        project_id=value.project_id,
        internal_engineering_model_id=value.internal_engineering_model_id,
        internal_model_relationship_id=value.internal_model_relationship_id,
        source_internal_model_element_id=(
            value.source_internal_model_element_id
        ),
        target_internal_model_element_id=(
            value.target_internal_model_element_id
        ),
        source_model_subject_key=value.source_model_subject_key,
        target_model_subject_key=value.target_model_subject_key,
        relationship_family=value.relationship_family,
        semantic_intent=value.semantic_intent,
        directionality=value.directionality,
        source_model_relationship_candidate_id=(
            value.source_model_relationship_candidate_id
        ),
        source_model_relationship_candidate_fingerprint=(
            value.source_model_relationship_candidate_fingerprint
        ),
        approved_input_references=approved,
        review_decision_reference=review,
        accepted_exception_reference=exception,
        content_fingerprint=value.content_fingerprint,
    )


def _payload(
    value: InternalModelRelationship,
    *,
    include_fingerprint: bool,
) -> dict[str, object]:
    payload = {
        "schema_version": value.schema_version,
        "project_id": value.project_id,
        "internal_engineering_model_id": value.internal_engineering_model_id,
        "internal_model_relationship_id": (
            value.internal_model_relationship_id
        ),
        "source_internal_model_element_id": (
            value.source_internal_model_element_id
        ),
        "target_internal_model_element_id": (
            value.target_internal_model_element_id
        ),
        "source_model_subject_key": value.source_model_subject_key,
        "target_model_subject_key": value.target_model_subject_key,
        "relationship_family": value.relationship_family,
        "semantic_intent": value.semantic_intent,
        "directionality": value.directionality,
        "source_model_relationship_candidate_id": (
            value.source_model_relationship_candidate_id
        ),
        "source_model_relationship_candidate_fingerprint": (
            value.source_model_relationship_candidate_fingerprint
        ),
        "approved_input_references": [
            approved_input_reference_payload(item)
            for item in value.approved_input_references
        ],
        "review_decision_reference": review_reference_payload(
            value.review_decision_reference
        ),
        "accepted_exception_reference": (
            None
            if value.accepted_exception_reference is None
            else review_reference_payload(
                value.accepted_exception_reference
            )
        ),
    }
    if include_fingerprint:
        payload["content_fingerprint"] = value.content_fingerprint
    return payload
