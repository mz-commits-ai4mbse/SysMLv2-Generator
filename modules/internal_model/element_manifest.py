"""Strict immutable manifest contract for Internal Model Elements."""

from __future__ import annotations

from modules.model_candidates.identifiers import (
    validate_model_element_candidate_id,
)

from ._manifest_support import (
    approved_input_reference_payload,
    canonical_fingerprint,
    deterministic_json,
    exact_object,
    identifier,
    optional_identifier,
    optional_text,
    parse_approved_input_reference_tuple,
    parse_review_reference,
    review_reference_payload,
    sha256,
    stable_subject_key,
    strict_json_loads,
    text,
    validate_project_id,
)
from .errors import InternalModelIntegrityError, InternalModelValidationError
from .identifiers import (
    validate_internal_engineering_model_id,
    validate_internal_model_element_id,
)
from .types import InternalModelAttribute, InternalModelElement


INTERNAL_MODEL_ELEMENT_SCHEMA_VERSION = "1.0.0"


def create_internal_model_element(
    *,
    project_id: str,
    internal_engineering_model_id: str,
    internal_model_element_id: str,
    model_subject_key: str,
    source_model_element_candidate_id: str,
    source_model_element_candidate_fingerprint: str,
    name: str,
    description: str | None,
    model_area: str,
    element_type: str,
    framework_assignment: str,
    terminology_assignment: str | None,
    attributes: tuple[InternalModelAttribute, ...],
    comparison_anchor_id: str | None,
    approved_input_references,
    review_decision_reference,
    accepted_exception_reference,
) -> InternalModelElement:
    provisional = InternalModelElement(
        schema_version=INTERNAL_MODEL_ELEMENT_SCHEMA_VERSION,
        project_id=project_id,
        internal_engineering_model_id=internal_engineering_model_id,
        internal_model_element_id=internal_model_element_id,
        model_subject_key=model_subject_key,
        source_model_element_candidate_id=source_model_element_candidate_id,
        source_model_element_candidate_fingerprint=(
            source_model_element_candidate_fingerprint
        ),
        name=name,
        description=description,
        model_area=model_area,
        element_type=element_type,
        framework_assignment=framework_assignment,
        terminology_assignment=terminology_assignment,
        attributes=attributes,
        comparison_anchor_id=comparison_anchor_id,
        approved_input_references=tuple(approved_input_references),
        review_decision_reference=review_decision_reference,
        accepted_exception_reference=accepted_exception_reference,
        content_fingerprint="0" * 64,
    )
    checked = _validated_without_fingerprint(provisional)
    result = InternalModelElement(
        schema_version=checked.schema_version,
        project_id=checked.project_id,
        internal_engineering_model_id=checked.internal_engineering_model_id,
        internal_model_element_id=checked.internal_model_element_id,
        model_subject_key=checked.model_subject_key,
        source_model_element_candidate_id=(
            checked.source_model_element_candidate_id
        ),
        source_model_element_candidate_fingerprint=(
            checked.source_model_element_candidate_fingerprint
        ),
        name=checked.name,
        description=checked.description,
        model_area=checked.model_area,
        element_type=checked.element_type,
        framework_assignment=checked.framework_assignment,
        terminology_assignment=checked.terminology_assignment,
        attributes=checked.attributes,
        comparison_anchor_id=checked.comparison_anchor_id,
        approved_input_references=checked.approved_input_references,
        review_decision_reference=checked.review_decision_reference,
        accepted_exception_reference=checked.accepted_exception_reference,
        content_fingerprint=calculate_internal_model_element_fingerprint(
            checked
        ),
    )
    return validate_internal_model_element(result)


def calculate_internal_model_element_fingerprint(
    value: InternalModelElement,
) -> str:
    return canonical_fingerprint(_payload(value, include_fingerprint=False))


def validate_internal_model_element(
    value: InternalModelElement,
) -> InternalModelElement:
    checked = _validated_without_fingerprint(value)
    fingerprint = sha256(
        value.content_fingerprint,
        label="content_fingerprint",
    )
    if fingerprint != calculate_internal_model_element_fingerprint(checked):
        raise InternalModelIntegrityError(
            "Internal Model Element content_fingerprint mismatch."
        )
    return value


def internal_model_element_to_dict(
    value: InternalModelElement,
) -> dict[str, object]:
    validate_internal_model_element(value)
    return _payload(value, include_fingerprint=True)


def internal_model_element_to_json(value: InternalModelElement) -> str:
    return deterministic_json(internal_model_element_to_dict(value))


def internal_model_element_from_json(
    text_value: object,
) -> InternalModelElement:
    return parse_internal_model_element(
        strict_json_loads(text_value, label="Internal Model Element")
    )


def parse_internal_model_element(value: object) -> InternalModelElement:
    data = exact_object(
        value,
        expected_fields=frozenset(
            InternalModelElement.__dataclass_fields__
        ),
        label="Internal Model Element",
    )
    raw_attributes = data["attributes"]
    if not isinstance(raw_attributes, list):
        raise InternalModelValidationError(
            "attributes must be a JSON array."
        )
    result = InternalModelElement(
        schema_version=data["schema_version"],
        project_id=data["project_id"],
        internal_engineering_model_id=data["internal_engineering_model_id"],
        internal_model_element_id=data["internal_model_element_id"],
        model_subject_key=data["model_subject_key"],
        source_model_element_candidate_id=(
            data["source_model_element_candidate_id"]
        ),
        source_model_element_candidate_fingerprint=(
            data["source_model_element_candidate_fingerprint"]
        ),
        name=data["name"],
        description=data["description"],
        model_area=data["model_area"],
        element_type=data["element_type"],
        framework_assignment=data["framework_assignment"],
        terminology_assignment=data["terminology_assignment"],
        attributes=tuple(_parse_attribute(item) for item in raw_attributes),
        comparison_anchor_id=data["comparison_anchor_id"],
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
    return validate_internal_model_element(result)


def _validated_without_fingerprint(
    value: InternalModelElement,
) -> InternalModelElement:
    if not isinstance(value, InternalModelElement):
        raise InternalModelValidationError(
            "value must be InternalModelElement."
        )
    if value.schema_version != INTERNAL_MODEL_ELEMENT_SCHEMA_VERSION:
        raise InternalModelValidationError(
            "Unsupported Internal Model Element schema_version."
        )
    validate_project_id(value.project_id)
    validate_internal_engineering_model_id(
        value.internal_engineering_model_id
    )
    validate_internal_model_element_id(value.internal_model_element_id)
    stable_subject_key(value.model_subject_key, label="model_subject_key")

    try:
        validate_model_element_candidate_id(
            value.source_model_element_candidate_id
        )
    except Exception as exc:
        raise InternalModelValidationError(
            "source_model_element_candidate_id is invalid."
        ) from exc

    sha256(
        value.source_model_element_candidate_fingerprint,
        label="source_model_element_candidate_fingerprint",
    )
    text(value.name, label="name")
    optional_text(value.description, label="description")
    identifier(value.model_area, label="model_area")
    identifier(value.element_type, label="element_type")
    identifier(value.framework_assignment, label="framework_assignment")
    optional_text(
        value.terminology_assignment,
        label="terminology_assignment",
    )
    optional_identifier(
        value.comparison_anchor_id,
        label="comparison_anchor_id",
    )

    attribute_keys = tuple(
        (
            identifier(item.name, label="attribute name"),
            text(item.value, label="attribute value"),
        )
        for item in value.attributes
    )
    if attribute_keys != tuple(sorted(attribute_keys)):
        raise InternalModelValidationError(
            "attributes must use deterministic sorted order."
        )
    if len(attribute_keys) != len({name for name, _ in attribute_keys}):
        raise InternalModelIntegrityError(
            "attribute names must be unique."
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
        review.target_type != "element_candidate"
        or review.candidate_id
        != value.source_model_element_candidate_id
        or review.decision not in {"accepted", "accepted_exception"}
    ):
        raise InternalModelIntegrityError(
            "Element review reference must authorize the exact source MCE."
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

    return InternalModelElement(
        schema_version=value.schema_version,
        project_id=value.project_id,
        internal_engineering_model_id=value.internal_engineering_model_id,
        internal_model_element_id=value.internal_model_element_id,
        model_subject_key=value.model_subject_key,
        source_model_element_candidate_id=(
            value.source_model_element_candidate_id
        ),
        source_model_element_candidate_fingerprint=(
            value.source_model_element_candidate_fingerprint
        ),
        name=value.name,
        description=value.description,
        model_area=value.model_area,
        element_type=value.element_type,
        framework_assignment=value.framework_assignment,
        terminology_assignment=value.terminology_assignment,
        attributes=value.attributes,
        comparison_anchor_id=value.comparison_anchor_id,
        approved_input_references=approved,
        review_decision_reference=review,
        accepted_exception_reference=exception,
        content_fingerprint=value.content_fingerprint,
    )


def _attribute_payload(
    value: InternalModelAttribute,
) -> dict[str, object]:
    return {"name": value.name, "value": value.value}


def _parse_attribute(value: object) -> InternalModelAttribute:
    data = exact_object(
        value,
        expected_fields=frozenset({"name", "value"}),
        label="Internal Model Attribute",
    )
    return InternalModelAttribute(
        name=identifier(data["name"], label="attribute name"),
        value=text(data["value"], label="attribute value"),
    )


def _payload(
    value: InternalModelElement,
    *,
    include_fingerprint: bool,
) -> dict[str, object]:
    payload = {
        "schema_version": value.schema_version,
        "project_id": value.project_id,
        "internal_engineering_model_id": value.internal_engineering_model_id,
        "internal_model_element_id": value.internal_model_element_id,
        "model_subject_key": value.model_subject_key,
        "source_model_element_candidate_id": (
            value.source_model_element_candidate_id
        ),
        "source_model_element_candidate_fingerprint": (
            value.source_model_element_candidate_fingerprint
        ),
        "name": value.name,
        "description": value.description,
        "model_area": value.model_area,
        "element_type": value.element_type,
        "framework_assignment": value.framework_assignment,
        "terminology_assignment": value.terminology_assignment,
        "attributes": [
            _attribute_payload(item) for item in value.attributes
        ],
        "comparison_anchor_id": value.comparison_anchor_id,
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
