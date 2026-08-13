"""Strict immutable manifest contract for Phase-H Element Candidates."""

from __future__ import annotations

from dataclasses import fields, replace

from ._manifest_support import (
    approved_input_reference_payload,
    attribute_payload,
    canonical_fingerprint,
    conformance_payload,
    deterministic_json,
    exact_object,
    normalize_approved_input_references,
    normalize_attributes,
    optional_identifier,
    optional_text,
    parse_approved_input_reference,
    parse_attribute,
    parse_conformance,
    sha256,
    stable_subject_key,
    strict_json_loads,
    text,
    timestamp,
    validate_project_id,
    sorted_unique_text_tuple,
)
from .errors import (
    ModelCandidateIntegrityError,
    ModelCandidateValidationError,
)
from .identifiers import (
    validate_model_candidate_set_id,
    validate_model_element_candidate_id,
)
from .types import (
    MODEL_CANDIDATE_SUPPORT_LEVELS,
    ModelCandidateApprovedInputReference,
    ModelCandidateAttribute,
    ModelElementCandidate,
    StructuralProfileConformance,
)


MODEL_ELEMENT_CANDIDATE_SCHEMA_VERSION = "1.0.0"

_FIELDS = frozenset(
    field.name for field in fields(ModelElementCandidate)
)


def create_model_element_candidate(
    *,
    project_id: str,
    candidate_set_id: str,
    model_element_candidate_id: str,
    candidate_subject_key: str,
    comparison_anchor_id: str | None,
    proposed_name: str,
    description: str | None,
    model_area: str,
    element_type: str,
    framework_assignment: str | None,
    terminology_assignment: str | None,
    attributes: tuple[ModelCandidateAttribute, ...],
    approved_input_references: tuple[
        ModelCandidateApprovedInputReference,
        ...,
    ],
    derivation_rationale: str,
    support_level: str,
    assumptions: tuple[str, ...],
    missing_information: tuple[str, ...],
    structure_profile_conformance: StructuralProfileConformance,
    predecessor_candidate_ids: tuple[str, ...],
    created_at: str,
) -> ModelElementCandidate:
    """Create one deterministic immutable Element Candidate."""

    provisional = ModelElementCandidate(
        schema_version=MODEL_ELEMENT_CANDIDATE_SCHEMA_VERSION,
        project_id=project_id,
        candidate_set_id=candidate_set_id,
        model_element_candidate_id=model_element_candidate_id,
        candidate_subject_key=candidate_subject_key,
        comparison_anchor_id=comparison_anchor_id,
        proposed_name=proposed_name,
        description=description,
        model_area=model_area,
        element_type=element_type,
        framework_assignment=framework_assignment,
        terminology_assignment=terminology_assignment,
        attributes=normalize_attributes(attributes),
        approved_input_references=normalize_approved_input_references(
            approved_input_references
        ),
        derivation_rationale=derivation_rationale,
        support_level=support_level,
        assumptions=tuple(sorted(assumptions)),
        missing_information=tuple(sorted(missing_information)),
        structure_profile_conformance=parse_conformance(
            conformance_payload(structure_profile_conformance)
        ),
        predecessor_candidate_ids=tuple(
            sorted(predecessor_candidate_ids)
        ),
        created_at=created_at,
        content_fingerprint="0" * 64,
    )
    candidate = replace(
        provisional,
        content_fingerprint=calculate_model_element_candidate_fingerprint(
            provisional
        ),
    )
    validate_model_element_candidate(candidate)
    return candidate


def calculate_model_element_candidate_fingerprint(
    candidate: ModelElementCandidate,
) -> str:
    _validate_candidate(candidate, verify_fingerprint=False)
    payload = _payload(candidate)
    payload.pop("model_element_candidate_id")
    payload.pop("content_fingerprint")
    payload.pop("created_at")
    return canonical_fingerprint(payload)


def validate_model_element_candidate(
    candidate: ModelElementCandidate,
) -> None:
    _validate_candidate(candidate, verify_fingerprint=True)


def model_element_candidate_to_dict(
    candidate: ModelElementCandidate,
) -> dict[str, object]:
    validate_model_element_candidate(candidate)
    return _payload(candidate)


def model_element_candidate_to_json(
    candidate: ModelElementCandidate,
) -> str:
    return deterministic_json(model_element_candidate_to_dict(candidate))


def model_element_candidate_from_json(
    text_value: object,
    *,
    expected_project_id: str | None = None,
    expected_candidate_set_id: str | None = None,
    expected_model_element_candidate_id: str | None = None,
) -> ModelElementCandidate:
    return parse_model_element_candidate(
        strict_json_loads(
            text_value,
            label="Model Element Candidate",
        ),
        expected_project_id=expected_project_id,
        expected_candidate_set_id=expected_candidate_set_id,
        expected_model_element_candidate_id=(
            expected_model_element_candidate_id
        ),
    )


def parse_model_element_candidate(
    payload: object,
    *,
    expected_project_id: str | None = None,
    expected_candidate_set_id: str | None = None,
    expected_model_element_candidate_id: str | None = None,
) -> ModelElementCandidate:
    data = exact_object(
        payload,
        expected_fields=_FIELDS,
        label="Model Element Candidate",
    )
    for name in (
        "attributes",
        "approved_input_references",
        "assumptions",
        "missing_information",
        "predecessor_candidate_ids",
    ):
        if not isinstance(data[name], list):
            raise ModelCandidateValidationError(
                f"{name} must be a JSON array."
            )

    candidate = ModelElementCandidate(
        schema_version=data["schema_version"],
        project_id=data["project_id"],
        candidate_set_id=data["candidate_set_id"],
        model_element_candidate_id=data["model_element_candidate_id"],
        candidate_subject_key=data["candidate_subject_key"],
        comparison_anchor_id=data["comparison_anchor_id"],
        proposed_name=data["proposed_name"],
        description=data["description"],
        model_area=data["model_area"],
        element_type=data["element_type"],
        framework_assignment=data["framework_assignment"],
        terminology_assignment=data["terminology_assignment"],
        attributes=tuple(
            parse_attribute(item)
            for item in data["attributes"]
        ),
        approved_input_references=tuple(
            parse_approved_input_reference(item)
            for item in data["approved_input_references"]
        ),
        derivation_rationale=data["derivation_rationale"],
        support_level=data["support_level"],
        assumptions=tuple(data["assumptions"]),
        missing_information=tuple(data["missing_information"]),
        structure_profile_conformance=parse_conformance(
            data["structure_profile_conformance"]
        ),
        predecessor_candidate_ids=tuple(
            data["predecessor_candidate_ids"]
        ),
        created_at=data["created_at"],
        content_fingerprint=data["content_fingerprint"],
    )
    _validate_candidate(candidate, verify_fingerprint=True)

    if (
        expected_project_id is not None
        and candidate.project_id != expected_project_id
    ):
        raise ModelCandidateValidationError(
            "project_id does not match expected project."
        )
    if (
        expected_candidate_set_id is not None
        and candidate.candidate_set_id != expected_candidate_set_id
    ):
        raise ModelCandidateValidationError(
            "candidate_set_id does not match expected Candidate Set."
        )
    if (
        expected_model_element_candidate_id is not None
        and candidate.model_element_candidate_id
        != expected_model_element_candidate_id
    ):
        raise ModelCandidateValidationError(
            "model_element_candidate_id does not match expected candidate."
        )
    return candidate


def _validate_candidate(
    candidate: ModelElementCandidate,
    *,
    verify_fingerprint: bool,
) -> None:
    if not isinstance(candidate, ModelElementCandidate):
        raise ModelCandidateValidationError(
            "candidate must be a ModelElementCandidate."
        )
    if candidate.schema_version != MODEL_ELEMENT_CANDIDATE_SCHEMA_VERSION:
        raise ModelCandidateValidationError(
            "Invalid Model Element Candidate schema_version."
        )
    validate_project_id(candidate.project_id)
    validate_model_candidate_set_id(candidate.candidate_set_id)
    current_id = validate_model_element_candidate_id(
        candidate.model_element_candidate_id
    )
    stable_subject_key(
        candidate.candidate_subject_key,
        label="candidate_subject_key",
    )
    optional_identifier(
        candidate.comparison_anchor_id,
        label="comparison_anchor_id",
    )
    text(candidate.proposed_name, label="proposed_name")
    optional_text(candidate.description, label="description")
    text(candidate.model_area, label="model_area")
    text(candidate.element_type, label="element_type")
    optional_text(
        candidate.framework_assignment,
        label="framework_assignment",
    )
    optional_text(
        candidate.terminology_assignment,
        label="terminology_assignment",
    )

    normalized_attributes = normalize_attributes(candidate.attributes)
    if normalized_attributes != candidate.attributes:
        raise ModelCandidateValidationError(
            "attributes must use deterministic name order."
        )

    normalized_inputs = normalize_approved_input_references(
        candidate.approved_input_references
    )
    if normalized_inputs != candidate.approved_input_references:
        raise ModelCandidateValidationError(
            "approved_input_references must use deterministic ID order."
        )

    text(candidate.derivation_rationale, label="derivation_rationale")
    if candidate.support_level not in MODEL_CANDIDATE_SUPPORT_LEVELS:
        raise ModelCandidateValidationError(
            "support_level is invalid."
        )
    assumptions = sorted_unique_text_tuple(
        candidate.assumptions,
        label="assumptions",
    )
    missing = sorted_unique_text_tuple(
        candidate.missing_information,
        label="missing_information",
    )
    if assumptions != candidate.assumptions:
        raise ModelCandidateValidationError(
            "assumptions must use deterministic sorted order."
        )
    if missing != candidate.missing_information:
        raise ModelCandidateValidationError(
            "missing_information must use deterministic sorted order."
        )

    parse_conformance(
        conformance_payload(candidate.structure_profile_conformance)
    )

    if not isinstance(candidate.predecessor_candidate_ids, tuple):
        raise ModelCandidateValidationError(
            "predecessor_candidate_ids must be a tuple."
        )
    try:
        predecessors = tuple(
            validate_model_element_candidate_id(item)
            for item in candidate.predecessor_candidate_ids
        )
    except Exception as exc:
        raise ModelCandidateValidationError(
            "predecessor_candidate_ids contains an invalid MCE ID."
        ) from exc
    if predecessors != tuple(sorted(predecessors)):
        raise ModelCandidateValidationError(
            "predecessor_candidate_ids must use deterministic sorted order."
        )
    if len(predecessors) != len(set(predecessors)):
        raise ModelCandidateIntegrityError(
            "predecessor_candidate_ids must be unique."
        )
    if current_id in predecessors:
        raise ModelCandidateIntegrityError(
            "An Element Candidate must not reference itself as predecessor."
        )

    timestamp(candidate.created_at, label="created_at")
    sha256(candidate.content_fingerprint, label="content_fingerprint")
    if verify_fingerprint:
        expected = calculate_model_element_candidate_fingerprint(candidate)
        if candidate.content_fingerprint != expected:
            raise ModelCandidateIntegrityError(
                "Model Element Candidate content_fingerprint does not match."
            )


def _payload(candidate: ModelElementCandidate) -> dict[str, object]:
    return {
        "schema_version": candidate.schema_version,
        "project_id": candidate.project_id,
        "candidate_set_id": candidate.candidate_set_id,
        "model_element_candidate_id": (
            candidate.model_element_candidate_id
        ),
        "candidate_subject_key": candidate.candidate_subject_key,
        "comparison_anchor_id": candidate.comparison_anchor_id,
        "proposed_name": candidate.proposed_name,
        "description": candidate.description,
        "model_area": candidate.model_area,
        "element_type": candidate.element_type,
        "framework_assignment": candidate.framework_assignment,
        "terminology_assignment": candidate.terminology_assignment,
        "attributes": [
            attribute_payload(item) for item in candidate.attributes
        ],
        "approved_input_references": [
            approved_input_reference_payload(item)
            for item in candidate.approved_input_references
        ],
        "derivation_rationale": candidate.derivation_rationale,
        "support_level": candidate.support_level,
        "assumptions": list(candidate.assumptions),
        "missing_information": list(candidate.missing_information),
        "structure_profile_conformance": conformance_payload(
            candidate.structure_profile_conformance
        ),
        "predecessor_candidate_ids": list(
            candidate.predecessor_candidate_ids
        ),
        "created_at": candidate.created_at,
        "content_fingerprint": candidate.content_fingerprint,
    }
