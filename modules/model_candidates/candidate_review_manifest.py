"""Strict immutable manifest for Phase-H Candidate Review Decisions."""

from __future__ import annotations

from dataclasses import fields, replace
import hashlib
import json
import re
from typing import Any

from .candidate_review_identifiers import (
    validate_model_candidate_review_decision_id,
)
from .errors import (
    ModelCandidateIntegrityError,
    ModelCandidateValidationError,
)
from .identifiers import (
    validate_model_candidate_set_id,
    validate_model_element_candidate_id,
    validate_model_relationship_candidate_id,
)
from .types import (
    MODEL_CANDIDATE_REVIEW_DECISIONS,
    MODEL_CANDIDATE_REVIEW_TARGET_TYPES,
    ModelCandidateReviewDecision,
    ModelCandidateReviewTargetSnapshot,
    ModelStructureProfileReference,
)


MODEL_CANDIDATE_REVIEW_DECISION_SCHEMA_VERSION = "1.0.0"

_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_TIMESTAMP = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T"
    r"[0-9]{2}:[0-9]{2}:[0-9]{2}Z$"
)
_TARGET_ID_PATTERNS = {
    "element_candidate": re.compile(r"^MCE-[0-9]{6}$"),
    "relationship_candidate": re.compile(r"^MCR-[0-9]{6}$"),
}
_FIELDS = frozenset(
    field.name for field in fields(ModelCandidateReviewDecision)
)
_TARGET_FIELDS = frozenset(
    field.name for field in fields(ModelCandidateReviewTargetSnapshot)
)
_PROFILE_FIELDS = frozenset(
    field.name for field in fields(ModelStructureProfileReference)
)


def create_model_candidate_review_target_snapshot(
    *,
    candidate_set_id: str,
    candidate_set_content_fingerprint: str,
    target_type: str,
    candidate_id: str,
    candidate_content_fingerprint: str,
    model_structure_profile_reference: ModelStructureProfileReference,
    structure_profile_conformance_status: str,
    structure_profile_conformance_fingerprint: str,
    approved_input_snapshot_fingerprint: str,
) -> ModelCandidateReviewTargetSnapshot:
    return _parse_target(
        {
            "candidate_set_id": candidate_set_id,
            "candidate_set_content_fingerprint": (
                candidate_set_content_fingerprint
            ),
            "target_type": target_type,
            "candidate_id": candidate_id,
            "candidate_content_fingerprint": (
                candidate_content_fingerprint
            ),
            "model_structure_profile_reference": {
                "profile_id": model_structure_profile_reference.profile_id,
                "profile_version": (
                    model_structure_profile_reference.profile_version
                ),
                "profile_fingerprint": (
                    model_structure_profile_reference.profile_fingerprint
                ),
            },
            "structure_profile_conformance_status": (
                structure_profile_conformance_status
            ),
            "structure_profile_conformance_fingerprint": (
                structure_profile_conformance_fingerprint
            ),
            "approved_input_snapshot_fingerprint": (
                approved_input_snapshot_fingerprint
            ),
        }
    )


def create_model_candidate_review_decision(
    *,
    project_id: str,
    model_candidate_review_decision_id: str,
    target: ModelCandidateReviewTargetSnapshot,
    decision: str,
    reviewer_identity: str,
    rationale: str | None,
    reviewed_at: str,
) -> ModelCandidateReviewDecision:
    if not isinstance(target, ModelCandidateReviewTargetSnapshot):
        raise ModelCandidateValidationError(
            "target must be a ModelCandidateReviewTargetSnapshot."
        )
    provisional = ModelCandidateReviewDecision(
        schema_version=MODEL_CANDIDATE_REVIEW_DECISION_SCHEMA_VERSION,
        project_id=_project_id(project_id),
        model_candidate_review_decision_id=(
            validate_model_candidate_review_decision_id(
                model_candidate_review_decision_id
            )
        ),
        target=target,
        decision=_decision(decision),
        reviewer_identity=_text(
            reviewer_identity,
            "reviewer_identity",
        ),
        rationale=_optional_text(rationale, "rationale"),
        reviewed_at=_timestamp(reviewed_at),
        decision_fingerprint="0" * 64,
    )
    _validate_gate(provisional)
    return replace(
        provisional,
        decision_fingerprint=(
            calculate_model_candidate_review_decision_fingerprint(
                provisional
            )
        ),
    )


def calculate_model_candidate_review_decision_fingerprint(
    decision: ModelCandidateReviewDecision,
) -> str:
    _validate_decision(decision, verify_fingerprint=False)
    payload = _payload(decision)
    payload.pop("model_candidate_review_decision_id")
    payload.pop("reviewed_at")
    payload.pop("decision_fingerprint")
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def validate_model_candidate_review_decision(
    decision: ModelCandidateReviewDecision,
) -> None:
    _validate_decision(decision, verify_fingerprint=True)


def model_candidate_review_decision_to_dict(
    decision: ModelCandidateReviewDecision,
) -> dict[str, object]:
    validate_model_candidate_review_decision(decision)
    return _payload(decision)


def model_candidate_review_decision_to_json(
    decision: ModelCandidateReviewDecision,
) -> str:
    return (
        json.dumps(
            model_candidate_review_decision_to_dict(decision),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )


def model_candidate_review_decision_from_json(
    text: object,
    *,
    expected_project_id: str | None = None,
    expected_decision_id: str | None = None,
) -> ModelCandidateReviewDecision:
    if not isinstance(text, str):
        raise ModelCandidateValidationError(
            "Model Candidate Review Decision JSON must be a string."
        )
    try:
        payload = json.loads(
            text,
            object_pairs_hook=_without_duplicate_keys,
        )
    except ModelCandidateValidationError:
        raise
    except json.JSONDecodeError as exc:
        raise ModelCandidateValidationError(
            "Model Candidate Review Decision contains invalid JSON."
        ) from exc
    decision = parse_model_candidate_review_decision(payload)
    if (
        expected_project_id is not None
        and decision.project_id != expected_project_id
    ):
        raise ModelCandidateValidationError(
            "project_id does not match expected project."
        )
    if (
        expected_decision_id is not None
        and decision.model_candidate_review_decision_id
        != expected_decision_id
    ):
        raise ModelCandidateValidationError(
            "review decision ID does not match expected ID."
        )
    return decision


def parse_model_candidate_review_decision(
    payload: object,
) -> ModelCandidateReviewDecision:
    data = _exact_object(
        payload,
        _FIELDS,
        "Model Candidate Review Decision",
    )
    target = _parse_target(data["target"])
    decision = ModelCandidateReviewDecision(
        schema_version=_expected(
            data["schema_version"],
            MODEL_CANDIDATE_REVIEW_DECISION_SCHEMA_VERSION,
            "schema_version",
        ),
        project_id=_project_id(data["project_id"]),
        model_candidate_review_decision_id=(
            validate_model_candidate_review_decision_id(
                data["model_candidate_review_decision_id"]
            )
        ),
        target=target,
        decision=_decision(data["decision"]),
        reviewer_identity=_text(
            data["reviewer_identity"],
            "reviewer_identity",
        ),
        rationale=_optional_text(data["rationale"], "rationale"),
        reviewed_at=_timestamp(data["reviewed_at"]),
        decision_fingerprint=_sha256(
            data["decision_fingerprint"],
            "decision_fingerprint",
        ),
    )
    _validate_decision(decision, verify_fingerprint=True)
    return decision


def _parse_target(value: object) -> ModelCandidateReviewTargetSnapshot:
    data = _exact_object(
        value,
        _TARGET_FIELDS,
        "Model Candidate Review Target Snapshot",
    )
    target_type = _choice(
        data["target_type"],
        MODEL_CANDIDATE_REVIEW_TARGET_TYPES,
        "target_type",
    )
    candidate_id = _text(data["candidate_id"], "candidate_id")
    if _TARGET_ID_PATTERNS[target_type].fullmatch(candidate_id) is None:
        raise ModelCandidateValidationError(
            "candidate_id does not match target_type."
        )
    if target_type == "element_candidate":
        validate_model_element_candidate_id(candidate_id)
    else:
        validate_model_relationship_candidate_id(candidate_id)

    profile_data = _exact_object(
        data["model_structure_profile_reference"],
        _PROFILE_FIELDS,
        "Model Structure Profile Reference",
    )
    profile = ModelStructureProfileReference(
        profile_id=_text(profile_data["profile_id"], "profile_id"),
        profile_version=_text(
            profile_data["profile_version"],
            "profile_version",
        ),
        profile_fingerprint=_sha256(
            profile_data["profile_fingerprint"],
            "profile_fingerprint",
        ),
    )
    return ModelCandidateReviewTargetSnapshot(
        candidate_set_id=validate_model_candidate_set_id(
            data["candidate_set_id"]
        ),
        candidate_set_content_fingerprint=_sha256(
            data["candidate_set_content_fingerprint"],
            "candidate_set_content_fingerprint",
        ),
        target_type=target_type,
        candidate_id=candidate_id,
        candidate_content_fingerprint=_sha256(
            data["candidate_content_fingerprint"],
            "candidate_content_fingerprint",
        ),
        model_structure_profile_reference=profile,
        structure_profile_conformance_status=_text(
            data["structure_profile_conformance_status"],
            "structure_profile_conformance_status",
        ),
        structure_profile_conformance_fingerprint=_sha256(
            data["structure_profile_conformance_fingerprint"],
            "structure_profile_conformance_fingerprint",
        ),
        approved_input_snapshot_fingerprint=_sha256(
            data["approved_input_snapshot_fingerprint"],
            "approved_input_snapshot_fingerprint",
        ),
    )


def _validate_decision(
    decision: ModelCandidateReviewDecision,
    *,
    verify_fingerprint: bool,
) -> None:
    if not isinstance(decision, ModelCandidateReviewDecision):
        raise ModelCandidateValidationError(
            "decision must be a ModelCandidateReviewDecision."
        )
    if (
        decision.schema_version
        != MODEL_CANDIDATE_REVIEW_DECISION_SCHEMA_VERSION
    ):
        raise ModelCandidateValidationError(
            "Unsupported Model Candidate Review Decision schema_version."
        )
    _project_id(decision.project_id)
    validate_model_candidate_review_decision_id(
        decision.model_candidate_review_decision_id
    )
    _parse_target(_target_payload(decision.target))
    _decision(decision.decision)
    _text(decision.reviewer_identity, "reviewer_identity")
    _optional_text(decision.rationale, "rationale")
    _timestamp(decision.reviewed_at)
    _sha256(decision.decision_fingerprint, "decision_fingerprint")
    _validate_gate(decision)
    if verify_fingerprint:
        expected = (
            calculate_model_candidate_review_decision_fingerprint(
                decision
            )
        )
        if decision.decision_fingerprint != expected:
            raise ModelCandidateIntegrityError(
                "Model Candidate Review Decision fingerprint does not "
                "match content."
            )


def _validate_gate(decision: ModelCandidateReviewDecision) -> None:
    selected = decision.decision
    rationale = decision.rationale
    status = decision.target.structure_profile_conformance_status

    if selected in {
        "rejected",
        "deferred",
        "accepted_exception",
    } and rationale is None:
        raise ModelCandidateIntegrityError(
            f"{selected} requires an explicit reviewer rationale."
        )
    if selected == "accepted" and status != "conformant":
        raise ModelCandidateIntegrityError(
            "Non-conformant Candidate content requires "
            "accepted_exception rather than accepted."
        )
    if selected == "accepted_exception" and status == "conformant":
        raise ModelCandidateIntegrityError(
            "accepted_exception is reserved for Candidate content that "
            "is not profile-conformant."
        )


def _payload(
    decision: ModelCandidateReviewDecision,
) -> dict[str, object]:
    return {
        "schema_version": decision.schema_version,
        "project_id": decision.project_id,
        "model_candidate_review_decision_id": (
            decision.model_candidate_review_decision_id
        ),
        "target": _target_payload(decision.target),
        "decision": decision.decision,
        "reviewer_identity": decision.reviewer_identity,
        "rationale": decision.rationale,
        "reviewed_at": decision.reviewed_at,
        "decision_fingerprint": decision.decision_fingerprint,
    }


def _target_payload(
    target: ModelCandidateReviewTargetSnapshot,
) -> dict[str, object]:
    if not isinstance(target, ModelCandidateReviewTargetSnapshot):
        raise ModelCandidateValidationError(
            "target has invalid type."
        )
    return {
        "candidate_set_id": target.candidate_set_id,
        "candidate_set_content_fingerprint": (
            target.candidate_set_content_fingerprint
        ),
        "target_type": target.target_type,
        "candidate_id": target.candidate_id,
        "candidate_content_fingerprint": (
            target.candidate_content_fingerprint
        ),
        "model_structure_profile_reference": {
            "profile_id": (
                target.model_structure_profile_reference.profile_id
            ),
            "profile_version": (
                target.model_structure_profile_reference.profile_version
            ),
            "profile_fingerprint": (
                target.model_structure_profile_reference.profile_fingerprint
            ),
        },
        "structure_profile_conformance_status": (
            target.structure_profile_conformance_status
        ),
        "structure_profile_conformance_fingerprint": (
            target.structure_profile_conformance_fingerprint
        ),
        "approved_input_snapshot_fingerprint": (
            target.approved_input_snapshot_fingerprint
        ),
    }


def _exact_object(
    value: object,
    expected: frozenset[str],
    label: str,
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ModelCandidateValidationError(
            f"{label} must be a JSON object."
        )
    actual = frozenset(value)
    if actual != expected:
        raise ModelCandidateValidationError(
            f"{label} has invalid fields; "
            f"missing={sorted(expected - actual)}, "
            f"unknown={sorted(actual - expected)}."
        )
    return value


def _without_duplicate_keys(
    pairs: list[tuple[str, object]],
) -> dict[str, object]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ModelCandidateValidationError(
                f"Duplicate JSON key is not allowed: {key!r}."
            )
        result[key] = value
    return result


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ModelCandidateValidationError(
            f"{label} must be a non-empty string."
        )
    if value != value.strip():
        raise ModelCandidateValidationError(
            f"{label} must not contain surrounding whitespace."
        )
    return value


def _optional_text(value: object, label: str) -> str | None:
    return None if value is None else _text(value, label)


def _sha256(value: object, label: str) -> str:
    selected = _text(value, label)
    if _SHA256.fullmatch(selected) is None:
        raise ModelCandidateValidationError(
            f"{label} must be lowercase SHA-256."
        )
    return selected


def _timestamp(value: object) -> str:
    selected = _text(value, "reviewed_at")
    if _TIMESTAMP.fullmatch(selected) is None:
        raise ModelCandidateValidationError(
            "reviewed_at must be an ISO-8601 UTC timestamp ending in Z."
        )
    return selected


def _choice(
    value: object,
    choices: frozenset[str],
    label: str,
) -> str:
    selected = _text(value, label)
    if selected not in choices:
        raise ModelCandidateValidationError(
            f"{label} must be one of {sorted(choices)!r}."
        )
    return selected


def _decision(value: object) -> str:
    return _choice(
        value,
        MODEL_CANDIDATE_REVIEW_DECISIONS,
        "decision",
    )


def _project_id(value: object) -> str:
    selected = _text(value, "project_id")
    if len(selected) != 6 or not selected.isdigit():
        raise ModelCandidateValidationError(
            "project_id must contain exactly six digits."
        )
    return selected


def _expected(
    value: object,
    expected: str,
    label: str,
) -> str:
    if value != expected:
        raise ModelCandidateValidationError(
            f"{label} must be {expected!r}."
        )
    return expected
