"""Immutable Human Target-Model Formulation authority contracts."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re

from .errors import TargetModelFormulationError
from .types import (
    TargetModelFormulationCandidate,
    TargetModelFormulationReview,
    TargetModelFormulationReviewItem,
)


TARGET_MODEL_FORMULATION_DECISION_SCHEMA_VERSION = "1.0.0"
TARGET_MODEL_FORMULATION_AUTHORITY_SET_SCHEMA_VERSION = "1.0.0"

_DECISION_ID = re.compile(r"^TFD-[0-9]{6}$")
_AUTHORITY_SET_ID = re.compile(r"^TFA-[0-9]{6}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True, slots=True)
class TargetModelFormulationDecision:
    schema_version: str
    project_id: str
    decision_id: str
    review_id: str
    review_fingerprint: str
    subject_kind: str
    authority_subject_id: str
    review_item_fingerprint: str
    selected_candidate_id: str
    selected_candidate_fingerprint: str
    selected_relevance_outcome: str
    selected_target_model_pattern_id: str | None
    selected_target_notation_construct_id: str | None
    selected_formulation_text: str | None
    reviewer_identity: str
    rationale: str
    decided_at: str
    supersedes_decision_id: str | None
    content_fingerprint: str


@dataclass(frozen=True, slots=True)
class TargetModelFormulationAuthoritySet:
    schema_version: str
    project_id: str
    authority_set_id: str
    review_id: str
    review_fingerprint: str
    source_internal_engineering_model_id: str
    source_internal_engineering_model_fingerprint: str
    final_model_review_decision_id: str
    final_model_review_decision_fingerprint: str
    target_model_profile_id: str
    target_model_profile_version: str
    target_model_profile_fingerprint: str
    target_notation_fingerprint: str
    effective_decisions: tuple[TargetModelFormulationDecision, ...]
    created_at: str
    content_fingerprint: str


def create_formulation_decision(
    *,
    review: TargetModelFormulationReview,
    decision_id: str,
    authority_subject_id: str,
    selected_candidate_id: str,
    reviewer_identity: str,
    rationale: str,
    decided_at: str,
    supersedes_decision_id: str | None = None,
) -> TargetModelFormulationDecision:
    """Authorize exactly one candidate already present in one immutable review item."""

    _validate_review(review)
    if _DECISION_ID.fullmatch(decision_id) is None:
        raise TargetModelFormulationError(
            "Target-Model Formulation decision ID is invalid."
        )

    item = _review_item(review, authority_subject_id)
    candidate = _candidate(item, selected_candidate_id)
    if candidate.relevance_outcome == "unresolved_human_review":
        raise TargetModelFormulationError(
            "Unresolved Human Review candidates cannot be Human-authorized as final decisions."
        )

    reviewer = _text(reviewer_identity, "reviewer_identity")
    reason = _text(rationale, "rationale")
    timestamp = _text(decided_at, "decided_at")
    supersedes = _optional_decision_id(supersedes_decision_id)

    body = {
        "schema_version": TARGET_MODEL_FORMULATION_DECISION_SCHEMA_VERSION,
        "project_id": review.project_id,
        "decision_id": decision_id,
        "review_id": review.review_id,
        "review_fingerprint": review.content_fingerprint,
        "subject_kind": item.subject_kind,
        "authority_subject_id": item.authority_subject_id,
        "review_item_fingerprint": item.content_fingerprint,
        "selected_candidate_id": candidate.candidate_id,
        "selected_candidate_fingerprint": candidate.content_fingerprint,
        "selected_relevance_outcome": candidate.relevance_outcome,
        "selected_target_model_pattern_id": candidate.target_model_pattern_id,
        "selected_target_notation_construct_id": candidate.target_notation_construct_id,
        "selected_formulation_text": candidate.formulation_text,
        "reviewer_identity": reviewer,
        "rationale": reason,
        "decided_at": timestamp,
        "supersedes_decision_id": supersedes,
    }
    return TargetModelFormulationDecision(
        **body,
        content_fingerprint=_fingerprint(body),
    )


def create_formulation_authority_set(
    *,
    review: TargetModelFormulationReview,
    authority_set_id: str,
    effective_decisions: tuple[TargetModelFormulationDecision, ...],
    created_at: str,
) -> TargetModelFormulationAuthoritySet:
    """Create a complete authority snapshot only when every review item is decided."""

    _validate_review(review)
    if _AUTHORITY_SET_ID.fullmatch(authority_set_id) is None:
        raise TargetModelFormulationError(
            "Target-Model Formulation authority-set ID is invalid."
        )
    timestamp = _text(created_at, "created_at")
    decisions = tuple(effective_decisions)
    if not decisions:
        raise TargetModelFormulationError(
            "Target-Model Formulation authority set requires effective decisions."
        )

    expected = {
        (item.subject_kind, item.authority_subject_id): item
        for item in review.items
    }
    received: dict[tuple[str, str], TargetModelFormulationDecision] = {}
    for decision in decisions:
        _validate_decision_against_review(review, decision)
        key = (decision.subject_kind, decision.authority_subject_id)
        if key in received:
            raise TargetModelFormulationError(
                "Target-Model Formulation authority set contains duplicate subject decisions."
            )
        received[key] = decision

    missing = sorted(set(expected) - set(received))
    extra = sorted(set(received) - set(expected))
    if missing or extra:
        raise TargetModelFormulationError(
            "Target-Model Formulation authority set must cover every review item exactly once."
        )

    ordered = tuple(
        received[(item.subject_kind, item.authority_subject_id)]
        for item in review.items
    )
    body = {
        "schema_version": TARGET_MODEL_FORMULATION_AUTHORITY_SET_SCHEMA_VERSION,
        "project_id": review.project_id,
        "authority_set_id": authority_set_id,
        "review_id": review.review_id,
        "review_fingerprint": review.content_fingerprint,
        "source_internal_engineering_model_id": review.source_internal_engineering_model_id,
        "source_internal_engineering_model_fingerprint": (
            review.source_internal_engineering_model_fingerprint
        ),
        "final_model_review_decision_id": review.final_model_review_decision_id,
        "final_model_review_decision_fingerprint": (
            review.final_model_review_decision_fingerprint
        ),
        "target_model_profile_id": review.target_model_profile_id,
        "target_model_profile_version": review.target_model_profile_version,
        "target_model_profile_fingerprint": review.target_model_profile_fingerprint,
        "target_notation_fingerprint": review.target_notation_fingerprint,
        "effective_decisions": [_decision_payload(item) for item in ordered],
        "created_at": timestamp,
    }
    return TargetModelFormulationAuthoritySet(
        schema_version=body["schema_version"],
        project_id=review.project_id,
        authority_set_id=authority_set_id,
        review_id=review.review_id,
        review_fingerprint=review.content_fingerprint,
        source_internal_engineering_model_id=(
            review.source_internal_engineering_model_id
        ),
        source_internal_engineering_model_fingerprint=(
            review.source_internal_engineering_model_fingerprint
        ),
        final_model_review_decision_id=review.final_model_review_decision_id,
        final_model_review_decision_fingerprint=(
            review.final_model_review_decision_fingerprint
        ),
        target_model_profile_id=review.target_model_profile_id,
        target_model_profile_version=review.target_model_profile_version,
        target_model_profile_fingerprint=review.target_model_profile_fingerprint,
        target_notation_fingerprint=review.target_notation_fingerprint,
        effective_decisions=ordered,
        created_at=timestamp,
        content_fingerprint=_fingerprint(body),
    )


def validate_decision_against_review(
    review: TargetModelFormulationReview,
    decision: TargetModelFormulationDecision,
) -> None:
    """Public fail-closed validator used by persistence and later IEM materialization."""

    _validate_review(review)
    _validate_decision_against_review(review, decision)


def _validate_decision_against_review(
    review: TargetModelFormulationReview,
    decision: TargetModelFormulationDecision,
) -> None:
    if decision.project_id != review.project_id:
        raise TargetModelFormulationError(
            "Target-Model Formulation decision project does not match review."
        )
    if decision.review_id != review.review_id:
        raise TargetModelFormulationError(
            "Target-Model Formulation decision review ID does not match."
        )
    if decision.review_fingerprint != review.content_fingerprint:
        raise TargetModelFormulationError(
            "Target-Model Formulation decision review fingerprint does not match."
        )

    item = _review_item(review, decision.authority_subject_id)
    if decision.subject_kind != item.subject_kind:
        raise TargetModelFormulationError(
            "Target-Model Formulation decision subject kind does not match review item."
        )
    if decision.review_item_fingerprint != item.content_fingerprint:
        raise TargetModelFormulationError(
            "Target-Model Formulation decision review-item fingerprint does not match."
        )

    candidate = _candidate(item, decision.selected_candidate_id)
    expected = {
        "selected_candidate_fingerprint": candidate.content_fingerprint,
        "selected_relevance_outcome": candidate.relevance_outcome,
        "selected_target_model_pattern_id": candidate.target_model_pattern_id,
        "selected_target_notation_construct_id": candidate.target_notation_construct_id,
        "selected_formulation_text": candidate.formulation_text,
    }
    for field, value in expected.items():
        if getattr(decision, field) != value:
            raise TargetModelFormulationError(
                "Target-Model Formulation decision selected candidate payload does not match review."
            )
    if candidate.relevance_outcome == "unresolved_human_review":
        raise TargetModelFormulationError(
            "Unresolved Human Review candidates cannot enter effective authority."
        )

    payload = _decision_payload(decision)
    fingerprint = payload.pop("content_fingerprint")
    if _fingerprint(payload) != fingerprint:
        raise TargetModelFormulationError(
            "Target-Model Formulation decision fingerprint is invalid."
        )


def _validate_review(review: TargetModelFormulationReview) -> None:
    if not isinstance(review, TargetModelFormulationReview):
        raise TargetModelFormulationError(
            "Target-Model Formulation authority requires an immutable review snapshot."
        )
    if _SHA256.fullmatch(review.content_fingerprint) is None:
        raise TargetModelFormulationError(
            "Target-Model Formulation review fingerprint is invalid."
        )


def _review_item(
    review: TargetModelFormulationReview,
    authority_subject_id: str,
) -> TargetModelFormulationReviewItem:
    subject_id = _text(authority_subject_id, "authority_subject_id")
    matches = [
        item for item in review.items
        if item.authority_subject_id == subject_id
    ]
    if len(matches) != 1:
        raise TargetModelFormulationError(
            "Target-Model Formulation authority subject is not uniquely present in review."
        )
    return matches[0]


def _candidate(
    item: TargetModelFormulationReviewItem,
    candidate_id: str,
) -> TargetModelFormulationCandidate:
    selected_id = _text(candidate_id, "selected_candidate_id")
    matches = [
        candidate for candidate in item.candidates
        if candidate.candidate_id == selected_id
    ]
    if len(matches) != 1:
        raise TargetModelFormulationError(
            "Selected Target-Model candidate is not uniquely present in review item."
        )
    return matches[0]


def _optional_decision_id(value: str | None) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or _DECISION_ID.fullmatch(value) is None:
        raise TargetModelFormulationError(
            "supersedes_decision_id must be a valid TFD ID."
        )
    return value


def _decision_payload(value: TargetModelFormulationDecision) -> dict:
    return {
        "schema_version": value.schema_version,
        "project_id": value.project_id,
        "decision_id": value.decision_id,
        "review_id": value.review_id,
        "review_fingerprint": value.review_fingerprint,
        "subject_kind": value.subject_kind,
        "authority_subject_id": value.authority_subject_id,
        "review_item_fingerprint": value.review_item_fingerprint,
        "selected_candidate_id": value.selected_candidate_id,
        "selected_candidate_fingerprint": value.selected_candidate_fingerprint,
        "selected_relevance_outcome": value.selected_relevance_outcome,
        "selected_target_model_pattern_id": value.selected_target_model_pattern_id,
        "selected_target_notation_construct_id": value.selected_target_notation_construct_id,
        "selected_formulation_text": value.selected_formulation_text,
        "reviewer_identity": value.reviewer_identity,
        "rationale": value.rationale,
        "decided_at": value.decided_at,
        "supersedes_decision_id": value.supersedes_decision_id,
        "content_fingerprint": value.content_fingerprint,
    }


def _text(value: str, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise TargetModelFormulationError(f"{label} is required.")
    return value.strip()


def _fingerprint(payload: dict) -> str:
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
