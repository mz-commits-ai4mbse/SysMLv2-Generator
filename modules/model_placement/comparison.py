"""Preserve multi-persona Model Placement variance without majority authority."""

from __future__ import annotations

import hashlib
import json

from modules.model_candidates.llm_projection_contract import (
    LLMProjectionRequest,
    LLMProjectionResponse,
)

from .errors import ModelPlacementContractError
from .types import (
    MODEL_PLACEMENT_AGREEMENT_LEVELS,
    MODEL_PLACEMENT_RESULTS,
    MODEL_PLACEMENT_SCHEMA_VERSION,
    ModelPlacementBatchComparison,
    ModelPlacementPersonaProposal,
    ModelPlacementReviewItem,
    ModelPlacementRuleSupport,
)


def compare_model_placement_personas(
    *,
    request: LLMProjectionRequest,
    persona_responses: tuple[tuple[str, LLMProjectionResponse], ...],
) -> ModelPlacementBatchComparison:
    """Compare independent persona placement proposals without selecting authority."""

    if not isinstance(request, LLMProjectionRequest):
        raise ModelPlacementContractError(
            "request must be an LLMProjectionRequest."
        )
    if (
        not isinstance(persona_responses, tuple)
        or len(persona_responses) < 2
    ):
        raise ModelPlacementContractError(
            "Model Placement comparison requires at least two persona responses."
        )

    persona_ids = tuple(item[0] for item in persona_responses)
    if (
        any(
            not isinstance(value, str)
            or not value.strip()
            or value != value.strip()
            for value in persona_ids
        )
        or len(persona_ids) != len(set(persona_ids))
    ):
        raise ModelPlacementContractError(
            "Model Placement persona IDs must be unique non-empty strings."
        )

    request_items = {
        item.approved_input_id: item
        for item in request.items
    }
    expected_ids = tuple(sorted(request_items))

    by_persona = {}
    for persona_id, response in persona_responses:
        if not isinstance(response, LLMProjectionResponse):
            raise ModelPlacementContractError(
                "Model Placement persona response has invalid type."
            )
        if response.request_fingerprint != request.request_fingerprint:
            raise ModelPlacementContractError(
                "Model Placement persona response does not bind the exact request."
            )
        proposals = {
            item.approved_input_id: item
            for item in response.proposals
        }
        if tuple(sorted(proposals)) != expected_ids:
            raise ModelPlacementContractError(
                "Every Model Placement persona must cover the exact request batch."
            )
        by_persona[persona_id] = proposals

    items = tuple(
        _compare_one(
            request_item=request_items[approved_input_id],
            by_persona=by_persona,
        )
        for approved_input_id in expected_ids
    )

    payload = {
        "schema_version": MODEL_PLACEMENT_SCHEMA_VERSION,
        "project_id": request.project_id,
        "profile_id": request.profile_id,
        "profile_version": request.profile_version,
        "profile_fingerprint": request.profile_fingerprint,
        "request_fingerprint": request.request_fingerprint,
        "persona_ids": sorted(persona_ids),
        "items": [_item_payload(item) for item in items],
        "human_review_required": True,
    }
    return ModelPlacementBatchComparison(
        schema_version=MODEL_PLACEMENT_SCHEMA_VERSION,
        project_id=request.project_id,
        profile_id=request.profile_id,
        profile_version=request.profile_version,
        profile_fingerprint=request.profile_fingerprint,
        request_fingerprint=request.request_fingerprint,
        persona_ids=tuple(sorted(persona_ids)),
        items=items,
        human_review_required=True,
        content_fingerprint=_fingerprint(payload),
    )


def _compare_one(*, request_item, by_persona) -> ModelPlacementReviewItem:
    persona_proposals = tuple(
        _normalize_proposal(
            persona_id=persona_id,
            proposal=by_persona[persona_id][request_item.approved_input_id],
        )
        for persona_id in sorted(by_persona)
    )

    allowed_rule_ids = tuple(
        sorted(option.rule_id for option in request_item.allowed_target_options)
    )
    allowed = set(allowed_rule_ids)

    referenced_by_rule: dict[str, set[str]] = {}
    for proposal in persona_proposals:
        referenced = set(proposal.alternative_rule_ids)
        if proposal.selected_rule_id is not None:
            referenced.add(proposal.selected_rule_id)
        outside = referenced - allowed
        if outside:
            raise ModelPlacementContractError(
                "Model Placement persona proposal references a rule outside "
                f"the exact request: {sorted(outside)}."
            )
        for rule_id in referenced:
            referenced_by_rule.setdefault(rule_id, set()).add(
                proposal.persona_id
            )

    rule_support = tuple(
        ModelPlacementRuleSupport(
            rule_id=rule_id,
            supporting_personas=tuple(sorted(personas)),
        )
        for rule_id, personas in sorted(referenced_by_rule.items())
    )

    agreement_level, unanimous_rule_id = _agreement(persona_proposals)
    if agreement_level not in MODEL_PLACEMENT_AGREEMENT_LEVELS:
        raise AssertionError("internal agreement level is invalid")

    review_attention_required = agreement_level != "unanimous_mapping"

    payload = {
        "approved_input_id": request_item.approved_input_id,
        "approved_input_kind": request_item.approved_input_kind,
        "stable_subject_key": request_item.stable_subject_key,
        "title": request_item.title,
        "primary_text": request_item.primary_text,
        "information_type": request_item.information_type,
        "deterministic_disposition": request_item.deterministic_disposition,
        "deterministic_candidate_rule_ids": list(
            request_item.deterministic_candidate_rule_ids
        ),
        "allowed_rule_ids": list(allowed_rule_ids),
        "persona_proposals": [
            _proposal_payload(item) for item in persona_proposals
        ],
        "rule_support": [
            {
                "rule_id": item.rule_id,
                "supporting_personas": list(item.supporting_personas),
            }
            for item in rule_support
        ],
        "agreement_level": agreement_level,
        "unanimous_rule_id": unanimous_rule_id,
        "review_attention_required": review_attention_required,
    }

    return ModelPlacementReviewItem(
        approved_input_id=request_item.approved_input_id,
        approved_input_kind=request_item.approved_input_kind,
        stable_subject_key=request_item.stable_subject_key,
        title=request_item.title,
        primary_text=request_item.primary_text,
        information_type=request_item.information_type,
        deterministic_disposition=request_item.deterministic_disposition,
        deterministic_candidate_rule_ids=tuple(
            request_item.deterministic_candidate_rule_ids
        ),
        allowed_rule_ids=allowed_rule_ids,
        persona_proposals=persona_proposals,
        rule_support=rule_support,
        agreement_level=agreement_level,
        unanimous_rule_id=unanimous_rule_id,
        review_attention_required=review_attention_required,
        content_fingerprint=_fingerprint(payload),
    )


def _normalize_proposal(*, persona_id, proposal):
    if proposal.result not in MODEL_PLACEMENT_RESULTS:
        raise ModelPlacementContractError(
            f"Unsupported Model Placement result: {proposal.result!r}."
        )
    payload = {
        "persona_id": persona_id,
        "approved_input_id": proposal.approved_input_id,
        "result": proposal.result,
        "selected_rule_id": proposal.selected_rule_id,
        "alternative_rule_ids": list(proposal.alternative_rule_ids),
        "rationale": proposal.rationale,
    }
    return ModelPlacementPersonaProposal(
        persona_id=persona_id,
        approved_input_id=proposal.approved_input_id,
        result=proposal.result,
        selected_rule_id=proposal.selected_rule_id,
        alternative_rule_ids=tuple(proposal.alternative_rule_ids),
        rationale=proposal.rationale,
        proposal_fingerprint=_fingerprint(payload),
    )


def _agreement(proposals):
    selected = tuple(
        item.selected_rule_id
        for item in proposals
        if item.result == "proposed_mapping"
        and item.selected_rule_id is not None
    )

    if (
        len(selected) == len(proposals)
        and len(set(selected)) == 1
    ):
        return "unanimous_mapping", selected[0]

    referenced_rules = set()
    for item in proposals:
        if item.selected_rule_id is not None:
            referenced_rules.add(item.selected_rule_id)
        referenced_rules.update(item.alternative_rule_ids)

    # Any explicitly preserved alternative across the persona population is
    # real placement variance. A 2:1 or "one mapping + one ambiguous + one
    # unmapped" result must never be collapsed into partial agreement merely
    # because all explicit single-rule selections happen to match.
    if len(referenced_rules) >= 2:
        return "placement_variance", None

    if selected and len(set(selected)) == 1:
        return "partial_mapping_agreement", None

    return "unresolved", None


def _proposal_payload(item):
    return {
        "persona_id": item.persona_id,
        "approved_input_id": item.approved_input_id,
        "result": item.result,
        "selected_rule_id": item.selected_rule_id,
        "alternative_rule_ids": list(item.alternative_rule_ids),
        "rationale": item.rationale,
        "proposal_fingerprint": item.proposal_fingerprint,
    }


def _item_payload(item):
    return {
        "approved_input_id": item.approved_input_id,
        "approved_input_kind": item.approved_input_kind,
        "stable_subject_key": item.stable_subject_key,
        "title": item.title,
        "primary_text": item.primary_text,
        "information_type": item.information_type,
        "deterministic_disposition": item.deterministic_disposition,
        "deterministic_candidate_rule_ids": list(
            item.deterministic_candidate_rule_ids
        ),
        "allowed_rule_ids": list(item.allowed_rule_ids),
        "persona_proposals": [
            _proposal_payload(value) for value in item.persona_proposals
        ],
        "rule_support": [
            {
                "rule_id": value.rule_id,
                "supporting_personas": list(value.supporting_personas),
            }
            for value in item.rule_support
        ],
        "agreement_level": item.agreement_level,
        "unanimous_rule_id": item.unanimous_rule_id,
        "review_attention_required": item.review_attention_required,
        "content_fingerprint": item.content_fingerprint,
    }


def _fingerprint(payload):
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
