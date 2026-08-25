"""Human Review-2 authority for SEM-015 model-quality refinement."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re

from .errors import ModelQualityError
from .types import (
    ModelQualityAuthoritySet,
    ModelQualityDecision,
    ModelQualityRefinementBundle,
)


MODEL_QUALITY_DECISION_SCHEMA_VERSION = "1.0.0"
MODEL_QUALITY_AUTHORITY_SET_SCHEMA_VERSION = "1.0.0"
_DECISION_ID = re.compile(r"^MQD-[0-9]{6}$")
_AUTHORITY_ID = re.compile(r"^MQA-[0-9]{6}$")


def create_quality_decision(
    *,
    bundle: ModelQualityRefinementBundle,
    decision_id: str,
    internal_model_element_id: str,
    decision: str,
    reviewer_identity: str,
    rationale: str,
    decided_at: str,
    approved_name: str | None = None,
    approved_description: str | None = None,
    supersedes_decision_id: str | None = None,
) -> ModelQualityDecision:
    if _DECISION_ID.fullmatch(decision_id) is None:
        raise ModelQualityError("Model-quality decision ID is invalid.")
    if decision not in {"approved", "overridden", "rejected"}:
        raise ModelQualityError("Model-quality Human decision is invalid.")
    proposal = _proposal(bundle, internal_model_element_id)
    reviewer = _text(reviewer_identity, "reviewer_identity")
    reason = _text(rationale, "rationale")
    timestamp = _text(decided_at, "decided_at")

    if decision == "approved":
        if (
            not proposal.meaning_preserved
            or proposal.unsupported_information_added
        ):
            raise ModelQualityError(
                "Unsafe model-quality proposal cannot be approved unchanged."
            )
        name = proposal.refined_name
        description = proposal.refined_description
    elif decision == "overridden":
        name = _text(approved_name, "approved_name")
        description = _optional_text(approved_description)
    else:
        if approved_name is not None or approved_description is not None:
            raise ModelQualityError(
                "Rejected model-quality decision cannot approve target wording."
            )
        name = None
        description = None

    supersedes = None
    if supersedes_decision_id is not None:
        if _DECISION_ID.fullmatch(supersedes_decision_id) is None:
            raise ModelQualityError(
                "supersedes_decision_id is invalid."
            )
        supersedes = supersedes_decision_id

    body = {
        "schema_version": MODEL_QUALITY_DECISION_SCHEMA_VERSION,
        "project_id": bundle.project_id,
        "decision_id": decision_id,
        "review_id": bundle.review_id,
        "review_fingerprint": bundle.content_fingerprint,
        "internal_model_element_id": internal_model_element_id,
        "proposal_fingerprint": proposal.content_fingerprint,
        "decision": decision,
        "approved_name": name,
        "approved_description": description,
        "reviewer_identity": reviewer,
        "rationale": reason,
        "decided_at": timestamp,
        "supersedes_decision_id": supersedes,
    }
    return ModelQualityDecision(
        **body,
        content_fingerprint=_fingerprint(body),
    )


def create_quality_authority_set(
    *,
    bundle: ModelQualityRefinementBundle,
    authority_set_id: str,
    effective_decisions: tuple[ModelQualityDecision, ...],
    created_at: str,
) -> ModelQualityAuthoritySet:
    if _AUTHORITY_ID.fullmatch(authority_set_id) is None:
        raise ModelQualityError("Model-quality authority-set ID is invalid.")
    expected = {
        item.internal_model_element_id
        for item in bundle.proposals
    }
    received = {}
    for decision in effective_decisions:
        _validate_decision(bundle, decision)
        if decision.internal_model_element_id in received:
            raise ModelQualityError(
                "Model-quality authority set contains duplicate element decisions."
            )
        if decision.decision == "rejected":
            raise ModelQualityError(
                "Rejected model-quality proposal blocks final model authority."
            )
        received[decision.internal_model_element_id] = decision
    if set(received) != expected:
        raise ModelQualityError(
            "Model-quality authority set requires one effective Human decision "
            "for every refined model element."
        )
    ordered = tuple(
        received[item.internal_model_element_id]
        for item in bundle.proposals
    )
    body = {
        "schema_version": MODEL_QUALITY_AUTHORITY_SET_SCHEMA_VERSION,
        "project_id": bundle.project_id,
        "authority_set_id": authority_set_id,
        "review_id": bundle.review_id,
        "review_fingerprint": bundle.content_fingerprint,
        "source_internal_engineering_model_id": (
            bundle.source_internal_engineering_model_id
        ),
        "source_internal_engineering_model_fingerprint": (
            bundle.source_internal_engineering_model_fingerprint
        ),
        "effective_decisions": [_decision_payload(item) for item in ordered],
        "created_at": _text(created_at, "created_at"),
    }
    return ModelQualityAuthoritySet(
        schema_version=MODEL_QUALITY_AUTHORITY_SET_SCHEMA_VERSION,
        project_id=bundle.project_id,
        authority_set_id=authority_set_id,
        review_id=bundle.review_id,
        review_fingerprint=bundle.content_fingerprint,
        source_internal_engineering_model_id=(
            bundle.source_internal_engineering_model_id
        ),
        source_internal_engineering_model_fingerprint=(
            bundle.source_internal_engineering_model_fingerprint
        ),
        effective_decisions=ordered,
        created_at=body["created_at"],
        content_fingerprint=_fingerprint(body),
    )


def validate_quality_decision(bundle, decision) -> None:
    _validate_decision(bundle, decision)


def _validate_decision(bundle, decision) -> None:
    if (
        decision.project_id != bundle.project_id
        or decision.review_id != bundle.review_id
        or decision.review_fingerprint != bundle.content_fingerprint
    ):
        raise ModelQualityError(
            "Model-quality decision does not bind the exact refinement review."
        )
    proposal = _proposal(
        bundle,
        decision.internal_model_element_id,
    )
    if decision.proposal_fingerprint != proposal.content_fingerprint:
        raise ModelQualityError(
            "Model-quality decision proposal fingerprint differs."
        )


def _proposal(bundle, element_id):
    matches = tuple(
        item
        for item in bundle.proposals
        if item.internal_model_element_id == element_id
    )
    if len(matches) != 1:
        raise ModelQualityError(
            "Model-quality element is not uniquely present in the review."
        )
    return matches[0]


def _decision_payload(item):
    return {
        "schema_version": item.schema_version,
        "project_id": item.project_id,
        "decision_id": item.decision_id,
        "review_id": item.review_id,
        "review_fingerprint": item.review_fingerprint,
        "internal_model_element_id": item.internal_model_element_id,
        "proposal_fingerprint": item.proposal_fingerprint,
        "decision": item.decision,
        "approved_name": item.approved_name,
        "approved_description": item.approved_description,
        "reviewer_identity": item.reviewer_identity,
        "rationale": item.rationale,
        "decided_at": item.decided_at,
        "supersedes_decision_id": item.supersedes_decision_id,
        "content_fingerprint": item.content_fingerprint,
    }


def _text(value, field):
    if not isinstance(value, str) or not value.strip():
        raise ModelQualityError(f"{field} must be non-empty text.")
    return value.strip()


def _optional_text(value):
    if value is None:
        return None
    if not isinstance(value, str):
        raise ModelQualityError("Optional text must be text or null.")
    return value.strip() or None


def _fingerprint(payload):
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
