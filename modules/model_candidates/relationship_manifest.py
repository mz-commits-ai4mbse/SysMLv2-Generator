"""Strict immutable manifest contract for Phase-H Relationship Candidates."""

from __future__ import annotations

from dataclasses import fields, replace

from modules.approved_input.types import (
    ApprovedInputRelationshipRepresentation,
)

from ._manifest_support import (
    approved_input_reference_payload,
    canonical_fingerprint,
    comparability_assessment_payload,
    conformance_payload,
    deterministic_json,
    endpoint_payload,
    exact_object,
    normalize_approved_input_references,
    optional_identifier,
    parse_approved_input_reference,
    parse_comparability_assessment,
    parse_conformance,
    parse_endpoint,
    parse_priority_assessment,
    parse_upstream_relationship,
    priority_assessment_payload,
    sha256,
    sorted_unique_text_tuple,
    strict_json_loads,
    text,
    timestamp,
    upstream_relationship_payload,
    validate_project_id,
)
from .errors import (
    ModelCandidateIntegrityError,
    ModelCandidateValidationError,
)
from .identifiers import (
    validate_model_candidate_set_id,
    validate_model_relationship_candidate_id,
)
from .types import (
    ModelCandidateApprovedInputReference,
    ModelRelationshipCandidate,
    ModelRelationshipEndpoint,
    RelationshipPriorityAssessment,
    StructuralComparabilityAssessment,
    StructuralProfileConformance,
)


MODEL_RELATIONSHIP_CANDIDATE_SCHEMA_VERSION = "1.0.0"

_FIELDS = frozenset(
    field.name for field in fields(ModelRelationshipCandidate)
)


def create_model_relationship_candidate(
    *,
    project_id: str,
    candidate_set_id: str,
    model_relationship_candidate_id: str,
    relationship_choice_key: str | None,
    source: ModelRelationshipEndpoint,
    target: ModelRelationshipEndpoint,
    relationship_family: str,
    semantic_intent: str,
    directionality: str,
    approved_input_references: tuple[
        ModelCandidateApprovedInputReference,
        ...,
    ],
    derivation_rationale: str,
    supporting_evidence: tuple[str, ...],
    assumptions: tuple[str, ...],
    missing_information: tuple[str, ...],
    priority_assessment: RelationshipPriorityAssessment,
    comparability_assessment: StructuralComparabilityAssessment,
    structure_profile_conformance: StructuralProfileConformance,
    upstream_relationship_representation: (
        ApprovedInputRelationshipRepresentation | None
    ),
    predecessor_candidate_ids: tuple[str, ...],
    created_at: str,
) -> ModelRelationshipCandidate:
    """Create one deterministic immutable Relationship Candidate."""

    provisional = ModelRelationshipCandidate(
        schema_version=MODEL_RELATIONSHIP_CANDIDATE_SCHEMA_VERSION,
        project_id=project_id,
        candidate_set_id=candidate_set_id,
        model_relationship_candidate_id=(
            model_relationship_candidate_id
        ),
        relationship_choice_key=relationship_choice_key,
        source=parse_endpoint(endpoint_payload(source)),
        target=parse_endpoint(endpoint_payload(target)),
        relationship_family=relationship_family,
        semantic_intent=semantic_intent,
        directionality=directionality,
        approved_input_references=normalize_approved_input_references(
            approved_input_references
        ),
        derivation_rationale=derivation_rationale,
        supporting_evidence=tuple(sorted(supporting_evidence)),
        assumptions=tuple(sorted(assumptions)),
        missing_information=tuple(sorted(missing_information)),
        priority_assessment=parse_priority_assessment(
            priority_assessment_payload(priority_assessment)
        ),
        comparability_assessment=parse_comparability_assessment(
            comparability_assessment_payload(
                comparability_assessment
            )
        ),
        structure_profile_conformance=parse_conformance(
            conformance_payload(structure_profile_conformance)
        ),
        upstream_relationship_representation=(
            None
            if upstream_relationship_representation is None
            else parse_upstream_relationship(
                upstream_relationship_payload(
                    upstream_relationship_representation
                )
            )
        ),
        predecessor_candidate_ids=tuple(
            sorted(predecessor_candidate_ids)
        ),
        created_at=created_at,
        content_fingerprint="0" * 64,
    )
    candidate = replace(
        provisional,
        content_fingerprint=(
            calculate_model_relationship_candidate_fingerprint(
                provisional
            )
        ),
    )
    validate_model_relationship_candidate(candidate)
    return candidate


def calculate_model_relationship_candidate_fingerprint(
    candidate: ModelRelationshipCandidate,
) -> str:
    _validate_candidate(candidate, verify_fingerprint=False)
    payload = _payload(candidate)
    payload.pop("model_relationship_candidate_id")
    payload.pop("content_fingerprint")
    payload.pop("created_at")
    return canonical_fingerprint(payload)


def validate_model_relationship_candidate(
    candidate: ModelRelationshipCandidate,
) -> None:
    _validate_candidate(candidate, verify_fingerprint=True)


def model_relationship_candidate_to_dict(
    candidate: ModelRelationshipCandidate,
) -> dict[str, object]:
    validate_model_relationship_candidate(candidate)
    return _payload(candidate)


def model_relationship_candidate_to_json(
    candidate: ModelRelationshipCandidate,
) -> str:
    return deterministic_json(
        model_relationship_candidate_to_dict(candidate)
    )


def model_relationship_candidate_from_json(
    text_value: object,
    *,
    expected_project_id: str | None = None,
    expected_candidate_set_id: str | None = None,
    expected_model_relationship_candidate_id: str | None = None,
) -> ModelRelationshipCandidate:
    return parse_model_relationship_candidate(
        strict_json_loads(
            text_value,
            label="Model Relationship Candidate",
        ),
        expected_project_id=expected_project_id,
        expected_candidate_set_id=expected_candidate_set_id,
        expected_model_relationship_candidate_id=(
            expected_model_relationship_candidate_id
        ),
    )


def parse_model_relationship_candidate(
    payload: object,
    *,
    expected_project_id: str | None = None,
    expected_candidate_set_id: str | None = None,
    expected_model_relationship_candidate_id: str | None = None,
) -> ModelRelationshipCandidate:
    data = exact_object(
        payload,
        expected_fields=_FIELDS,
        label="Model Relationship Candidate",
    )
    for name in (
        "approved_input_references",
        "supporting_evidence",
        "assumptions",
        "missing_information",
        "predecessor_candidate_ids",
    ):
        if not isinstance(data[name], list):
            raise ModelCandidateValidationError(
                f"{name} must be a JSON array."
            )

    upstream = data["upstream_relationship_representation"]
    candidate = ModelRelationshipCandidate(
        schema_version=data["schema_version"],
        project_id=data["project_id"],
        candidate_set_id=data["candidate_set_id"],
        model_relationship_candidate_id=data[
            "model_relationship_candidate_id"
        ],
        relationship_choice_key=data["relationship_choice_key"],
        source=parse_endpoint(data["source"]),
        target=parse_endpoint(data["target"]),
        relationship_family=data["relationship_family"],
        semantic_intent=data["semantic_intent"],
        directionality=data["directionality"],
        approved_input_references=tuple(
            parse_approved_input_reference(item)
            for item in data["approved_input_references"]
        ),
        derivation_rationale=data["derivation_rationale"],
        supporting_evidence=tuple(data["supporting_evidence"]),
        assumptions=tuple(data["assumptions"]),
        missing_information=tuple(data["missing_information"]),
        priority_assessment=parse_priority_assessment(
            data["priority_assessment"]
        ),
        comparability_assessment=parse_comparability_assessment(
            data["comparability_assessment"]
        ),
        structure_profile_conformance=parse_conformance(
            data["structure_profile_conformance"]
        ),
        upstream_relationship_representation=(
            None
            if upstream is None
            else parse_upstream_relationship(upstream)
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
        expected_model_relationship_candidate_id is not None
        and candidate.model_relationship_candidate_id
        != expected_model_relationship_candidate_id
    ):
        raise ModelCandidateValidationError(
            "model_relationship_candidate_id does not match expected candidate."
        )
    return candidate


def _validate_candidate(
    candidate: ModelRelationshipCandidate,
    *,
    verify_fingerprint: bool,
) -> None:
    if not isinstance(candidate, ModelRelationshipCandidate):
        raise ModelCandidateValidationError(
            "candidate must be a ModelRelationshipCandidate."
        )
    if (
        candidate.schema_version
        != MODEL_RELATIONSHIP_CANDIDATE_SCHEMA_VERSION
    ):
        raise ModelCandidateValidationError(
            "Invalid Model Relationship Candidate schema_version."
        )
    validate_project_id(candidate.project_id)
    validate_model_candidate_set_id(candidate.candidate_set_id)
    current_id = validate_model_relationship_candidate_id(
        candidate.model_relationship_candidate_id
    )
    optional_identifier(
        candidate.relationship_choice_key,
        label="relationship_choice_key",
    )
    parse_endpoint(endpoint_payload(candidate.source))
    parse_endpoint(endpoint_payload(candidate.target))

    text(candidate.relationship_family, label="relationship_family")
    text(candidate.semantic_intent, label="semantic_intent")
    text(candidate.directionality, label="directionality")

    normalized_inputs = normalize_approved_input_references(
        candidate.approved_input_references
    )
    if normalized_inputs != candidate.approved_input_references:
        raise ModelCandidateValidationError(
            "approved_input_references must use deterministic ID order."
        )

    text(candidate.derivation_rationale, label="derivation_rationale")
    supporting = sorted_unique_text_tuple(
        candidate.supporting_evidence,
        label="supporting_evidence",
    )
    assumptions = sorted_unique_text_tuple(
        candidate.assumptions,
        label="assumptions",
    )
    missing = sorted_unique_text_tuple(
        candidate.missing_information,
        label="missing_information",
    )
    if supporting != candidate.supporting_evidence:
        raise ModelCandidateValidationError(
            "supporting_evidence must use deterministic sorted order."
        )
    if assumptions != candidate.assumptions:
        raise ModelCandidateValidationError(
            "assumptions must use deterministic sorted order."
        )
    if missing != candidate.missing_information:
        raise ModelCandidateValidationError(
            "missing_information must use deterministic sorted order."
        )

    parse_priority_assessment(
        priority_assessment_payload(candidate.priority_assessment)
    )
    parse_comparability_assessment(
        comparability_assessment_payload(
            candidate.comparability_assessment
        )
    )
    parse_conformance(
        conformance_payload(candidate.structure_profile_conformance)
    )

    if candidate.upstream_relationship_representation is not None:
        parse_upstream_relationship(
            upstream_relationship_payload(
                candidate.upstream_relationship_representation
            )
        )

    if not isinstance(candidate.predecessor_candidate_ids, tuple):
        raise ModelCandidateValidationError(
            "predecessor_candidate_ids must be a tuple."
        )
    try:
        predecessors = tuple(
            validate_model_relationship_candidate_id(item)
            for item in candidate.predecessor_candidate_ids
        )
    except Exception as exc:
        raise ModelCandidateValidationError(
            "predecessor_candidate_ids contains an invalid MCR ID."
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
            "A Relationship Candidate must not reference itself as predecessor."
        )

    timestamp(candidate.created_at, label="created_at")
    sha256(candidate.content_fingerprint, label="content_fingerprint")
    if verify_fingerprint:
        expected = (
            calculate_model_relationship_candidate_fingerprint(candidate)
        )
        if candidate.content_fingerprint != expected:
            raise ModelCandidateIntegrityError(
                "Model Relationship Candidate content_fingerprint "
                "does not match."
            )


def _payload(
    candidate: ModelRelationshipCandidate,
) -> dict[str, object]:
    return {
        "schema_version": candidate.schema_version,
        "project_id": candidate.project_id,
        "candidate_set_id": candidate.candidate_set_id,
        "model_relationship_candidate_id": (
            candidate.model_relationship_candidate_id
        ),
        "relationship_choice_key": candidate.relationship_choice_key,
        "source": endpoint_payload(candidate.source),
        "target": endpoint_payload(candidate.target),
        "relationship_family": candidate.relationship_family,
        "semantic_intent": candidate.semantic_intent,
        "directionality": candidate.directionality,
        "approved_input_references": [
            approved_input_reference_payload(item)
            for item in candidate.approved_input_references
        ],
        "derivation_rationale": candidate.derivation_rationale,
        "supporting_evidence": list(candidate.supporting_evidence),
        "assumptions": list(candidate.assumptions),
        "missing_information": list(candidate.missing_information),
        "priority_assessment": priority_assessment_payload(
            candidate.priority_assessment
        ),
        "comparability_assessment": comparability_assessment_payload(
            candidate.comparability_assessment
        ),
        "structure_profile_conformance": conformance_payload(
            candidate.structure_profile_conformance
        ),
        "upstream_relationship_representation": (
            None
            if candidate.upstream_relationship_representation is None
            else upstream_relationship_payload(
                candidate.upstream_relationship_representation
            )
        ),
        "predecessor_candidate_ids": list(
            candidate.predecessor_candidate_ids
        ),
        "created_at": candidate.created_at,
        "content_fingerprint": candidate.content_fingerprint,
    }
