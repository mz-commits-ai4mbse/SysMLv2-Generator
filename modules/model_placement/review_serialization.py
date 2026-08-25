"""Canonical serialization for Model Placement comparison and Human decisions."""

from __future__ import annotations

from dataclasses import asdict
import hashlib
import json

from .errors import ModelPlacementContractError
from .review_identifiers import validate_model_placement_decision_id
from .review_types import (
    MODEL_PLACEMENT_REVIEW_DECISION_SCHEMA_VERSION,
    MODEL_PLACEMENT_REVIEW_OUTCOMES,
    ModelPlacementReviewDecision,
)
from .types import (
    MODEL_PLACEMENT_SCHEMA_VERSION,
    ModelPlacementBatchComparison,
    ModelPlacementPersonaProposal,
    ModelPlacementReviewItem,
    ModelPlacementRuleSupport,
)


def comparison_to_json(value: ModelPlacementBatchComparison) -> str:
    if not isinstance(value, ModelPlacementBatchComparison):
        raise ModelPlacementContractError(
            "comparison must be ModelPlacementBatchComparison."
        )
    return json.dumps(
        asdict(value),
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ) + "\n"


def comparison_from_json(text: str) -> ModelPlacementBatchComparison:
    try:
        payload = json.loads(text)
    except Exception as exc:
        raise ModelPlacementContractError(
            "Model Placement comparison JSON is invalid."
        ) from exc
    if not isinstance(payload, dict):
        raise ModelPlacementContractError(
            "Model Placement comparison JSON must contain an object."
        )
    if payload.get("schema_version") != MODEL_PLACEMENT_SCHEMA_VERSION:
        raise ModelPlacementContractError(
            "Model Placement comparison schema version is unsupported."
        )
    try:
        items = tuple(
            ModelPlacementReviewItem(
                approved_input_id=item["approved_input_id"],
                approved_input_kind=item["approved_input_kind"],
                stable_subject_key=item["stable_subject_key"],
                title=item["title"],
                primary_text=item["primary_text"],
                information_type=item["information_type"],
                deterministic_disposition=item["deterministic_disposition"],
                deterministic_candidate_rule_ids=tuple(
                    item["deterministic_candidate_rule_ids"]
                ),
                allowed_rule_ids=tuple(item["allowed_rule_ids"]),
                persona_proposals=tuple(
                    ModelPlacementPersonaProposal(
                        persona_id=proposal["persona_id"],
                        approved_input_id=proposal["approved_input_id"],
                        result=proposal["result"],
                        selected_rule_id=proposal["selected_rule_id"],
                        alternative_rule_ids=tuple(
                            proposal["alternative_rule_ids"]
                        ),
                        rationale=proposal["rationale"],
                        proposal_fingerprint=proposal[
                            "proposal_fingerprint"
                        ],
                    )
                    for proposal in item["persona_proposals"]
                ),
                rule_support=tuple(
                    ModelPlacementRuleSupport(
                        rule_id=support["rule_id"],
                        supporting_personas=tuple(
                            support["supporting_personas"]
                        ),
                    )
                    for support in item["rule_support"]
                ),
                agreement_level=item["agreement_level"],
                unanimous_rule_id=item["unanimous_rule_id"],
                review_attention_required=item[
                    "review_attention_required"
                ],
                content_fingerprint=item["content_fingerprint"],
            )
            for item in payload["items"]
        )
        result = ModelPlacementBatchComparison(
            schema_version=payload["schema_version"],
            project_id=payload["project_id"],
            profile_id=payload["profile_id"],
            profile_version=payload["profile_version"],
            profile_fingerprint=payload["profile_fingerprint"],
            request_fingerprint=payload["request_fingerprint"],
            persona_ids=tuple(payload["persona_ids"]),
            items=items,
            human_review_required=payload["human_review_required"],
            content_fingerprint=payload["content_fingerprint"],
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ModelPlacementContractError(
            "Model Placement comparison JSON violates the exact contract."
        ) from exc
    return result


def create_review_decision(
    *,
    project_id: str,
    decision_id: str,
    comparison: ModelPlacementBatchComparison,
    approved_input_id: str,
    outcome: str,
    selected_rule_id: str | None,
    reviewer_identity: str,
    rationale: str | None,
    supersedes_decision_id: str | None,
    reviewed_at: str,
) -> ModelPlacementReviewDecision:
    validate_model_placement_decision_id(decision_id)
    if outcome not in MODEL_PLACEMENT_REVIEW_OUTCOMES:
        raise ModelPlacementContractError(
            "Unsupported Model Placement review outcome."
        )
    if not isinstance(reviewer_identity, str) or not reviewer_identity.strip():
        raise ModelPlacementContractError(
            "reviewer_identity is required."
        )
    item = next(
        (
            item
            for item in comparison.items
            if item.approved_input_id == approved_input_id
        ),
        None,
    )
    if item is None:
        raise ModelPlacementContractError(
            "Model Placement decision references an input outside the comparison."
        )
    if outcome == "accepted":
        if selected_rule_id not in set(item.allowed_rule_ids):
            raise ModelPlacementContractError(
                "Accepted Model Placement must select one allowed profile rule."
            )
    elif selected_rule_id is not None:
        raise ModelPlacementContractError(
            "Only accepted Model Placement decisions may select a profile rule."
        )
    if outcome in {"rejected", "reopened"} and (
        not isinstance(rationale, str) or not rationale.strip()
    ):
        raise ModelPlacementContractError(
            f"{outcome} Model Placement decisions require a rationale."
        )
    if supersedes_decision_id is not None:
        validate_model_placement_decision_id(supersedes_decision_id)

    provisional = {
        "schema_version": MODEL_PLACEMENT_REVIEW_DECISION_SCHEMA_VERSION,
        "project_id": project_id,
        "decision_id": decision_id,
        "comparison_fingerprint": comparison.content_fingerprint,
        "review_item_fingerprint": item.content_fingerprint,
        "approved_input_id": approved_input_id,
        "outcome": outcome,
        "selected_rule_id": selected_rule_id,
        "reviewer_identity": reviewer_identity.strip(),
        "rationale": None if rationale is None else rationale.strip(),
        "supersedes_decision_id": supersedes_decision_id,
        "reviewed_at": reviewed_at,
    }
    fingerprint_payload = dict(provisional)
    fingerprint_payload.pop("decision_id")
    fingerprint_payload.pop("reviewed_at")
    return ModelPlacementReviewDecision(
        **provisional,
        decision_fingerprint=_fingerprint(fingerprint_payload),
    )


def decision_to_json(value: ModelPlacementReviewDecision) -> str:
    return json.dumps(
        asdict(value),
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ) + "\n"


def decision_from_json(text: str) -> ModelPlacementReviewDecision:
    try:
        payload = json.loads(text)
        value = ModelPlacementReviewDecision(**payload)
    except Exception as exc:
        raise ModelPlacementContractError(
            "Model Placement decision JSON violates the exact contract."
        ) from exc
    if value.schema_version != MODEL_PLACEMENT_REVIEW_DECISION_SCHEMA_VERSION:
        raise ModelPlacementContractError(
            "Model Placement decision schema version is unsupported."
        )
    validate_model_placement_decision_id(value.decision_id)
    if value.supersedes_decision_id is not None:
        validate_model_placement_decision_id(value.supersedes_decision_id)
    if value.outcome not in MODEL_PLACEMENT_REVIEW_OUTCOMES:
        raise ModelPlacementContractError(
            "Model Placement decision outcome is invalid."
        )
    fingerprint_payload = asdict(value)
    stored = fingerprint_payload.pop("decision_fingerprint")
    fingerprint_payload.pop("decision_id")
    fingerprint_payload.pop("reviewed_at")
    if _fingerprint(fingerprint_payload) != stored:
        raise ModelPlacementContractError(
            "Model Placement decision fingerprint is invalid."
        )
    return value


def _fingerprint(payload) -> str:
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
