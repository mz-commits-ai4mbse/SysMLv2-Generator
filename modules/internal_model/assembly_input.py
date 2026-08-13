"""Deterministic fingerprinting of the authorized Phase-H → Phase-I input."""

from __future__ import annotations

from modules.model_candidates.types import ModelCandidateAssemblyInput

from ._manifest_support import (
    approved_input_reference_payload,
    candidate_generation_provenance_payload,
    canonical_fingerprint,
    derivation_rules_reference_payload,
    framework_template_reference_payload,
    model_structure_profile_reference_payload,
    review_reference_payload,
)
from .errors import InternalModelValidationError


def model_candidate_assembly_input_to_fingerprint_payload(
    value: ModelCandidateAssemblyInput,
) -> dict[str, object]:
    """Project exact authority-bearing H→I state into canonical fingerprint data."""

    if not isinstance(value, ModelCandidateAssemblyInput):
        raise InternalModelValidationError(
            "value must be ModelCandidateAssemblyInput."
        )

    return {
        "project_id": value.project_id,
        "candidate_set_id": value.candidate_set_id,
        "candidate_set_content_fingerprint": (
            value.candidate_set_content_fingerprint
        ),
        "approved_input_snapshot_fingerprint": (
            value.approved_input_snapshot_fingerprint
        ),
        "approved_input_references": sorted(
            (
                approved_input_reference_payload(item)
                for item in value.approved_input_references
            ),
            key=lambda item: item["approved_input_id"],
        ),
        "framework_template_reference": (
            framework_template_reference_payload(
                value.framework_template_reference
            )
        ),
        "model_structure_profile_reference": (
            model_structure_profile_reference_payload(
                value.model_structure_profile_reference
            )
        ),
        "derivation_rules_reference": derivation_rules_reference_payload(
            value.derivation_rules_reference
        ),
        "generation_provenance": candidate_generation_provenance_payload(
            value.generation_provenance
        ),
        "accepted_element_candidates": sorted(
            (
                {
                    "candidate_id": item.model_element_candidate_id,
                    "content_fingerprint": item.content_fingerprint,
                }
                for item in value.accepted_element_candidates
            ),
            key=lambda item: item["candidate_id"],
        ),
        "accepted_relationship_candidates": sorted(
            (
                {
                    "candidate_id": item.model_relationship_candidate_id,
                    "content_fingerprint": item.content_fingerprint,
                }
                for item in value.accepted_relationship_candidates
            ),
            key=lambda item: item["candidate_id"],
        ),
        "accepted_exception_decisions": sorted(
            (
                review_reference_payload(item)
                for item in value.accepted_exception_decisions
            ),
            key=lambda item: item["model_candidate_review_decision_id"],
        ),
        "review_decision_references": sorted(
            (
                review_reference_payload(item)
                for item in value.review_decision_references
            ),
            key=lambda item: item["model_candidate_review_decision_id"],
        ),
    }


def calculate_model_candidate_assembly_input_fingerprint(
    value: ModelCandidateAssemblyInput,
) -> str:
    """Return deterministic exact H→I authority fingerprint."""

    return canonical_fingerprint(
        model_candidate_assembly_input_to_fingerprint_payload(value)
    )
