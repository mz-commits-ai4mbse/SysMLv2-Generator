"""Build bounded placement requests from Approved Engineering Information."""

from __future__ import annotations

import hashlib
import json

from modules.model_candidates.llm_projection_contract import (
    LLMProjectionInputItem,
    LLMProjectionRequest,
    LLMProjectionTargetOption,
)
from modules.model_placement.errors import ModelPlacementContractError
from modules.model_candidates.project_authority_handoff import (
    phase_h_subject_key,
)
from modules.model_placement.types import (
    MODEL_PLACEMENT_SCHEMA_VERSION,
    ModelPlacementBatchComparison,
    ModelPlacementReviewItem,
    ModelPlacementRuleSupport,
)


def build_model_placement_request(
    *,
    request,
    coverage,
    profile,
) -> LLMProjectionRequest:
    """Build one coherent placement request for all element Approved Inputs."""

    coverage_by_id = {
        item.approved_input_id: item
        for item in coverage.entries
    }
    items = []
    for approved_input in request.approved_inputs:
        if approved_input.approved_input_kind != "element_statement":
            continue
        entry = coverage_by_id.get(approved_input.approved_input_id)
        if entry is None:
            raise ModelPlacementContractError(
                "Placement request lacks deterministic coverage for an "
                "Approved Input."
            )

        options = _placement_options(
            approved_input=approved_input,
            profile=profile,
        )
        if not options:
            raise ModelPlacementContractError(
                "Placement request requires at least one profile-controlled "
                "target option."
            )

        deterministic_rule_ids = set(entry.candidate_rule_ids)
        if entry.selected_rule_id is not None:
            deterministic_rule_ids.add(entry.selected_rule_id)

        content = approved_input.canonical_content
        resolved_subject_key = phase_h_subject_key(
            request,
            approved_input,
        )
        items.append(
            LLMProjectionInputItem(
                approved_input_id=approved_input.approved_input_id,
                approved_input_kind=approved_input.approved_input_kind,
                stable_subject_key=resolved_subject_key,
                title=content.title,
                primary_text=content.primary_text,
                description=content.description,
                information_type=content.information_type,
                reviewed_classification=(
                    approved_input.selected_classification
                ),
                reviewed_framework_assignment=(
                    approved_input.selected_framework_assignment
                ),
                deterministic_disposition=entry.disposition,
                deterministic_reason_code=entry.reason_code,
                deterministic_candidate_rule_ids=tuple(
                    sorted(deterministic_rule_ids)
                ),
                review_escalation=False,
                allowed_target_options=options,
            )
        )

    items = tuple(
        sorted(items, key=lambda item: item.approved_input_id)
    )
    if not items:
        raise ModelPlacementContractError(
            "Model Placement requires at least one element Approved Input."
        )

    payload = {
        "schema_version": MODEL_PLACEMENT_SCHEMA_VERSION,
        "project_id": request.project_id,
        "profile_id": profile.profile_id,
        "profile_version": profile.profile_version,
        "profile_fingerprint": profile.profile_fingerprint,
        "items": [_request_item_payload(item) for item in items],
    }
    return LLMProjectionRequest(
        project_id=request.project_id,
        profile_id=profile.profile_id,
        profile_version=profile.profile_version,
        profile_fingerprint=profile.profile_fingerprint,
        items=items,
        request_fingerprint=_fingerprint(payload),
    )


def build_deterministic_model_placement_comparison(
    *,
    placement_request: LLMProjectionRequest,
    coverage,
) -> ModelPlacementBatchComparison:
    """Build Human-reviewable Eco placement without any LLM invocation."""

    coverage_by_id = {
        item.approved_input_id: item
        for item in coverage.entries
    }
    review_items = []
    for item in placement_request.items:
        entry = coverage_by_id[item.approved_input_id]
        if entry.disposition != "mapped" or entry.selected_rule_id is None:
            raise ModelPlacementContractError(
                "Eco Model Placement requires every element Approved Input "
                "to have one deterministic mapping."
            )
        allowed = {
            option.rule_id
            for option in item.allowed_target_options
        }
        if entry.selected_rule_id not in allowed:
            raise ModelPlacementContractError(
                "Deterministic placement is outside the Human-review options."
            )

        item_payload = {
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
            "allowed_rule_ids": sorted(allowed),
            "persona_proposals": [],
            "rule_support": [
                {
                    "rule_id": entry.selected_rule_id,
                    "supporting_personas": ["DETERMINISTIC_PROFILE"],
                }
            ],
            "agreement_level": "unanimous_mapping",
            "unanimous_rule_id": entry.selected_rule_id,
            "review_attention_required": False,
        }
        review_items.append(
            ModelPlacementReviewItem(
                approved_input_id=item.approved_input_id,
                approved_input_kind=item.approved_input_kind,
                stable_subject_key=item.stable_subject_key,
                title=item.title,
                primary_text=item.primary_text,
                information_type=item.information_type,
                deterministic_disposition=item.deterministic_disposition,
                deterministic_candidate_rule_ids=tuple(
                    item.deterministic_candidate_rule_ids
                ),
                allowed_rule_ids=tuple(sorted(allowed)),
                persona_proposals=(),
                rule_support=(
                    ModelPlacementRuleSupport(
                        rule_id=entry.selected_rule_id,
                        supporting_personas=("DETERMINISTIC_PROFILE",),
                    ),
                ),
                agreement_level="unanimous_mapping",
                unanimous_rule_id=entry.selected_rule_id,
                review_attention_required=False,
                content_fingerprint=_fingerprint(item_payload),
            )
        )

    payload = {
        "schema_version": MODEL_PLACEMENT_SCHEMA_VERSION,
        "project_id": placement_request.project_id,
        "profile_id": placement_request.profile_id,
        "profile_version": placement_request.profile_version,
        "profile_fingerprint": placement_request.profile_fingerprint,
        "request_fingerprint": placement_request.request_fingerprint,
        "persona_ids": [],
        "items": [
            _review_item_payload(item)
            for item in review_items
        ],
        "human_review_required": True,
    }
    return ModelPlacementBatchComparison(
        schema_version=MODEL_PLACEMENT_SCHEMA_VERSION,
        project_id=placement_request.project_id,
        profile_id=placement_request.profile_id,
        profile_version=placement_request.profile_version,
        profile_fingerprint=placement_request.profile_fingerprint,
        request_fingerprint=placement_request.request_fingerprint,
        persona_ids=(),
        items=tuple(review_items),
        human_review_required=True,
        content_fingerprint=_fingerprint(payload),
    )


def _placement_options(*, approved_input, profile):
    information_type = approved_input.canonical_content.information_type
    normalized = (
        information_type.strip().lower()
        if isinstance(information_type, str)
        else None
    )

    matching = tuple(
        rule
        for rule in profile.element_derivation_rules
        if normalized is not None
        and normalized in {
            value.strip().lower()
            for value in rule.information_type_values
        }
    )
    rules = (
        matching
        if matching
        else tuple(profile.element_derivation_rules)
    )
    areas = {
        item.model_area_id: item
        for item in profile.model_areas
    }

    return tuple(
        sorted(
            (
                LLMProjectionTargetOption(
                    rule_id=rule.rule_id,
                    target_kind="element",
                    model_area=rule.model_area_id,
                    element_type=rule.element_type,
                    framework_assignment=(
                        areas[rule.model_area_id].framework_node_id
                    ),
                    relationship_family=None,
                    semantic_intent=None,
                    directionality=None,
                )
                for rule in rules
            ),
            key=lambda item: item.rule_id,
        )
    )


def _request_item_payload(item):
    return {
        "approved_input_id": item.approved_input_id,
        "approved_input_kind": item.approved_input_kind,
        "stable_subject_key": item.stable_subject_key,
        "title": item.title,
        "primary_text": item.primary_text,
        "description": item.description,
        "information_type": item.information_type,
        "reviewed_classification": item.reviewed_classification,
        "reviewed_framework_assignment": (
            item.reviewed_framework_assignment
        ),
        "deterministic_disposition": item.deterministic_disposition,
        "deterministic_reason_code": item.deterministic_reason_code,
        "deterministic_candidate_rule_ids": list(
            item.deterministic_candidate_rule_ids
        ),
        "allowed_target_options": [
            {
                "rule_id": option.rule_id,
                "target_kind": option.target_kind,
                "model_area": option.model_area,
                "element_type": option.element_type,
                "framework_assignment": option.framework_assignment,
            }
            for option in item.allowed_target_options
        ],
    }


def _review_item_payload(item):
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
        "persona_proposals": [],
        "rule_support": [
            {
                "rule_id": support.rule_id,
                "supporting_personas": list(
                    support.supporting_personas
                ),
            }
            for support in item.rule_support
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
