"""Immutable Human change proposals for Phase-L Final Model Review."""

from __future__ import annotations

from dataclasses import asdict, replace
import json
import re
from typing import Any

from .errors import FinalModelReviewIntegrityError, FinalModelReviewValidationError
from .fingerprints import calculate_json_fingerprint, validate_sha256_fingerprint
from .identifiers import (
    validate_final_model_review_change_proposal_id,
    validate_final_model_review_id,
    validate_final_model_review_revision_id,
)
from .types import (
    AGENT_REPROPOSAL_REQUEST_STATUSES,
    FINAL_MODEL_REVIEW_CHANGE_CLASSIFICATIONS,
    FINAL_MODEL_REVIEW_CHANGE_ROUTES,
    FINAL_MODEL_REVIEW_CHANGE_SURFACES,
    FinalModelReviewChangeProposal,
    FinalModelReviewChangeTarget,
)

CHANGE_PROPOSAL_SCHEMA_VERSION = "1.0.0"
_TIMESTAMP = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]+)?Z$"
)
_GSU = re.compile(r"^GSU-[0-9]{6}$")
_SYMBOL = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_IME = re.compile(r"^IME-[0-9]{6}$")
_IMR = re.compile(r"^IMR-[0-9]{6}$")

ROUTE_BY_CLASSIFICATION = {
    "engineering_semantics": "phase_h_candidate_review",
    "generated_representation": "phase_j_generation",
    "validation_policy_or_tool": "phase_k_validation",
    "review_presentation_only": "phase_l_presentation",
}


def create_final_model_review_change_proposal(
    *,
    project_id: str,
    final_model_review_id: str,
    final_model_review_revision_id: str,
    final_model_review_change_proposal_id: str,
    base_revision_content_fingerprint: str,
    base_review_subject_fingerprint: str,
    surface: str,
    classification: str,
    target: FinalModelReviewChangeTarget,
    original_text: str | None,
    proposed_text: str | None,
    reviewer_feedback: str,
    request_agent_reproposal: bool,
    requested_agent_personalities: tuple[str, ...] = (),
    created_by: str,
    created_at: str,
) -> FinalModelReviewChangeProposal:
    selected_surface = _choice(surface, FINAL_MODEL_REVIEW_CHANGE_SURFACES, "surface")
    selected_classification = _choice(
        classification,
        FINAL_MODEL_REVIEW_CHANGE_CLASSIFICATIONS,
        "classification",
    )
    route = ROUTE_BY_CLASSIFICATION[selected_classification]
    validated_target = _target(target)
    original = _optional_text(original_text, "original_text")
    proposed = _optional_text(proposed_text, "proposed_text")
    feedback = _text(reviewer_feedback, "reviewer_feedback")
    if selected_surface == "sysml_code":
        if validated_target.generated_unit_id is None:
            raise FinalModelReviewValidationError(
                "sysml_code change proposals require generated_unit_id."
            )
        if original is None or proposed is None or original == proposed:
            raise FinalModelReviewValidationError(
                "sysml_code change proposals require a material original/proposed text diff."
            )
        if selected_classification == "review_presentation_only":
            raise FinalModelReviewValidationError(
                "a material SysML-code change cannot be presentation-only."
            )
    personalities = _personalities(requested_agent_personalities)
    if not isinstance(request_agent_reproposal, bool):
        raise FinalModelReviewValidationError(
            "request_agent_reproposal must be a boolean."
        )
    if personalities and not request_agent_reproposal:
        raise FinalModelReviewValidationError(
            "requested_agent_personalities require request_agent_reproposal=true."
        )
    provisional = FinalModelReviewChangeProposal(
        schema_version=CHANGE_PROPOSAL_SCHEMA_VERSION,
        project_id=_project(project_id),
        final_model_review_id=validate_final_model_review_id(final_model_review_id),
        final_model_review_revision_id=validate_final_model_review_revision_id(
            final_model_review_revision_id
        ),
        final_model_review_change_proposal_id=(
            validate_final_model_review_change_proposal_id(
                final_model_review_change_proposal_id
            )
        ),
        base_revision_content_fingerprint=validate_sha256_fingerprint(
            base_revision_content_fingerprint,
            label="base_revision_content_fingerprint",
        ),
        base_review_subject_fingerprint=validate_sha256_fingerprint(
            base_review_subject_fingerprint,
            label="base_review_subject_fingerprint",
        ),
        surface=selected_surface,
        classification=selected_classification,
        authority_route=route,
        target=validated_target,
        original_text=original,
        proposed_text=proposed,
        reviewer_feedback=feedback,
        agent_reproposal_request_status=(
            "requested" if request_agent_reproposal else "not_requested"
        ),
        requested_agent_personalities=personalities,
        created_by=_text(created_by, "created_by"),
        created_at=_timestamp(created_at),
        content_fingerprint="0" * 64,
    )
    return replace(
        provisional,
        content_fingerprint=calculate_final_model_review_change_proposal_fingerprint(
            provisional
        ),
    )


def calculate_final_model_review_change_proposal_fingerprint(
    proposal: FinalModelReviewChangeProposal,
) -> str:
    _validate(proposal, verify_fingerprint=False)
    payload = asdict(proposal)
    payload.pop("final_model_review_change_proposal_id")
    payload.pop("created_at")
    payload.pop("content_fingerprint")
    return calculate_json_fingerprint(payload)


def validate_final_model_review_change_proposal(
    proposal: FinalModelReviewChangeProposal,
) -> None:
    _validate(proposal, verify_fingerprint=True)


def final_model_review_change_proposal_to_json(
    proposal: FinalModelReviewChangeProposal,
) -> str:
    validate_final_model_review_change_proposal(proposal)
    return json.dumps(asdict(proposal), ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def final_model_review_change_proposal_from_json(
    text: object,
    *,
    expected_project_id: str | None = None,
    expected_review_id: str | None = None,
    expected_change_proposal_id: str | None = None,
) -> FinalModelReviewChangeProposal:
    if not isinstance(text, str):
        raise FinalModelReviewValidationError("change proposal JSON must be a string.")
    try:
        raw = json.loads(text, object_pairs_hook=_unique_pairs)
    except FinalModelReviewValidationError:
        raise
    except json.JSONDecodeError as exc:
        raise FinalModelReviewValidationError("change proposal contains invalid JSON.") from exc
    if not isinstance(raw, dict):
        raise FinalModelReviewValidationError("change proposal must be a JSON object.")
    expected = {
        "schema_version", "project_id", "final_model_review_id",
        "final_model_review_revision_id", "final_model_review_change_proposal_id",
        "base_revision_content_fingerprint", "base_review_subject_fingerprint",
        "surface", "classification", "authority_route", "target", "original_text",
        "proposed_text", "reviewer_feedback", "agent_reproposal_request_status",
        "requested_agent_personalities", "created_by", "created_at", "content_fingerprint",
    }
    if set(raw) != expected:
        raise FinalModelReviewValidationError("change proposal has invalid fields.")
    target_raw = raw["target"]
    if not isinstance(target_raw, dict):
        raise FinalModelReviewValidationError("change proposal target must be an object.")
    target = FinalModelReviewChangeTarget(**target_raw)
    request_status = raw["agent_reproposal_request_status"]
    proposal = create_final_model_review_change_proposal(
        project_id=raw["project_id"],
        final_model_review_id=raw["final_model_review_id"],
        final_model_review_revision_id=raw["final_model_review_revision_id"],
        final_model_review_change_proposal_id=raw["final_model_review_change_proposal_id"],
        base_revision_content_fingerprint=raw["base_revision_content_fingerprint"],
        base_review_subject_fingerprint=raw["base_review_subject_fingerprint"],
        surface=raw["surface"],
        classification=raw["classification"],
        target=target,
        original_text=raw["original_text"],
        proposed_text=raw["proposed_text"],
        reviewer_feedback=raw["reviewer_feedback"],
        request_agent_reproposal=(request_status == "requested"),
        requested_agent_personalities=tuple(raw["requested_agent_personalities"]),
        created_by=raw["created_by"],
        created_at=raw["created_at"],
    )
    if request_status not in AGENT_REPROPOSAL_REQUEST_STATUSES:
        raise FinalModelReviewValidationError("agent_reproposal_request_status is invalid.")
    if raw["authority_route"] not in FINAL_MODEL_REVIEW_CHANGE_ROUTES:
        raise FinalModelReviewValidationError("authority_route is invalid.")
    if raw["authority_route"] != proposal.authority_route:
        raise FinalModelReviewIntegrityError("stored change-proposal route is not deterministic.")
    if raw["schema_version"] != CHANGE_PROPOSAL_SCHEMA_VERSION:
        raise FinalModelReviewValidationError("unsupported change proposal schema_version.")
    if raw["content_fingerprint"] != proposal.content_fingerprint:
        raise FinalModelReviewIntegrityError("change proposal fingerprint mismatch.")
    if expected_project_id is not None and proposal.project_id != expected_project_id:
        raise FinalModelReviewIntegrityError("change proposal Project does not match path.")
    if expected_review_id is not None and proposal.final_model_review_id != expected_review_id:
        raise FinalModelReviewIntegrityError("change proposal review ID does not match path.")
    if (
        expected_change_proposal_id is not None
        and proposal.final_model_review_change_proposal_id != expected_change_proposal_id
    ):
        raise FinalModelReviewIntegrityError("change proposal ID does not match path.")
    return proposal


def _validate(proposal: FinalModelReviewChangeProposal, *, verify_fingerprint: bool) -> None:
    if not isinstance(proposal, FinalModelReviewChangeProposal):
        raise FinalModelReviewValidationError("proposal must be a FinalModelReviewChangeProposal.")
    if proposal.schema_version != CHANGE_PROPOSAL_SCHEMA_VERSION:
        raise FinalModelReviewValidationError("unsupported change proposal schema_version.")
    _project(proposal.project_id)
    validate_final_model_review_id(proposal.final_model_review_id)
    validate_final_model_review_revision_id(proposal.final_model_review_revision_id)
    validate_final_model_review_change_proposal_id(proposal.final_model_review_change_proposal_id)
    validate_sha256_fingerprint(proposal.base_revision_content_fingerprint, label="base_revision_content_fingerprint")
    validate_sha256_fingerprint(proposal.base_review_subject_fingerprint, label="base_review_subject_fingerprint")
    _choice(proposal.surface, FINAL_MODEL_REVIEW_CHANGE_SURFACES, "surface")
    _choice(proposal.classification, FINAL_MODEL_REVIEW_CHANGE_CLASSIFICATIONS, "classification")
    if proposal.authority_route != ROUTE_BY_CLASSIFICATION[proposal.classification]:
        raise FinalModelReviewIntegrityError("change proposal authority route does not match classification.")
    _target(proposal.target)
    _optional_text(proposal.original_text, "original_text")
    _optional_text(proposal.proposed_text, "proposed_text")
    _text(proposal.reviewer_feedback, "reviewer_feedback")
    _choice(proposal.agent_reproposal_request_status, AGENT_REPROPOSAL_REQUEST_STATUSES, "agent_reproposal_request_status")
    personalities = _personalities(proposal.requested_agent_personalities)
    if personalities and proposal.agent_reproposal_request_status != "requested":
        raise FinalModelReviewValidationError("agent personalities require a requested agent re-proposal.")
    _text(proposal.created_by, "created_by")
    _timestamp(proposal.created_at)
    validate_sha256_fingerprint(proposal.content_fingerprint, label="content_fingerprint")
    if verify_fingerprint:
        expected = calculate_final_model_review_change_proposal_fingerprint(
            replace(proposal, content_fingerprint="0" * 64)
        )
        if proposal.content_fingerprint != expected:
            raise FinalModelReviewIntegrityError("change proposal fingerprint mismatch.")


def _target(target: FinalModelReviewChangeTarget) -> FinalModelReviewChangeTarget:
    if not isinstance(target, FinalModelReviewChangeTarget):
        raise FinalModelReviewValidationError("target must be a FinalModelReviewChangeTarget.")
    if target.generated_unit_id is not None:
        if _GSU.fullmatch(target.generated_unit_id) is None or target.generated_unit_id == "GSU-000000":
            raise FinalModelReviewValidationError("generated_unit_id is invalid.")
        if target.generated_unit_content_fingerprint is None:
            raise FinalModelReviewValidationError("generated unit target requires its content fingerprint.")
        validate_sha256_fingerprint(target.generated_unit_content_fingerprint, label="generated_unit_content_fingerprint")
    elif target.generated_unit_content_fingerprint is not None:
        raise FinalModelReviewValidationError("generated_unit_content_fingerprint requires generated_unit_id.")
    if target.generated_symbol_id is not None:
        if target.generated_unit_id is None or _SYMBOL.fullmatch(target.generated_symbol_id) is None:
            raise FinalModelReviewValidationError("generated_symbol_id requires a valid generated unit target.")
    if target.internal_model_element_id is not None and _IME.fullmatch(target.internal_model_element_id) is None:
        raise FinalModelReviewValidationError("internal_model_element_id is invalid.")
    if target.internal_model_relationship_id is not None and _IMR.fullmatch(target.internal_model_relationship_id) is None:
        raise FinalModelReviewValidationError("internal_model_relationship_id is invalid.")
    if target.validation_finding_code is not None:
        _text(target.validation_finding_code, "validation_finding_code")
    if not any((
        target.generated_unit_id,
        target.generated_symbol_id,
        target.internal_model_element_id,
        target.internal_model_relationship_id,
        target.validation_finding_code,
    )):
        raise FinalModelReviewValidationError("change proposal target must identify at least one review subject.")
    return target


def _project(value: object) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[0-9]{6}", value) is None:
        raise FinalModelReviewValidationError("project_id must be a six-digit string.")
    return value


def _choice(value: object, allowed: tuple[str, ...], label: str) -> str:
    if not isinstance(value, str) or value not in allowed:
        raise FinalModelReviewValidationError(f"{label} must be one of {allowed}.")
    return value


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise FinalModelReviewValidationError(f"{label} must be a non-empty trimmed string.")
    return value


def _optional_text(value: object, label: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise FinalModelReviewValidationError(f"{label} must be a string or None.")
    return value


def _personalities(values: tuple[str, ...]) -> tuple[str, ...]:
    if not isinstance(values, tuple):
        raise FinalModelReviewValidationError("requested_agent_personalities must be a tuple.")
    selected = tuple(_text(value, "requested_agent_personality") for value in values)
    if len(selected) != len(set(selected)) or selected != tuple(sorted(selected)):
        raise FinalModelReviewValidationError("requested_agent_personalities must be unique and sorted.")
    return selected


def _timestamp(value: object) -> str:
    if not isinstance(value, str) or _TIMESTAMP.fullmatch(value) is None:
        raise FinalModelReviewValidationError("created_at must be a UTC timestamp ending in Z.")
    return value


def _unique_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise FinalModelReviewValidationError(f"duplicate JSON key: {key!r}.")
        result[key] = value
    return result
