"""Human-authoritative Approved Model Placement Set before model assembly."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json

from modules.model_placement.errors import ModelPlacementContractError


APPROVED_MODEL_PLACEMENT_SET_SCHEMA_VERSION = "1.0.0"


@dataclass(frozen=True, slots=True)
class ApprovedModelPlacement:
    approved_input_id: str
    stable_subject_key: str
    selected_rule_id: str
    model_area: str
    element_type: str
    framework_assignment: str
    review_decision_id: str
    review_decision_fingerprint: str
    content_fingerprint: str


@dataclass(frozen=True, slots=True)
class ApprovedModelPlacementSet:
    schema_version: str
    project_id: str
    comparison_fingerprint: str
    profile_id: str
    profile_version: str
    profile_fingerprint: str
    placements: tuple[ApprovedModelPlacement, ...]
    explicitly_not_materialized_approved_input_ids: tuple[str, ...]
    decision_fingerprints: tuple[str, ...]
    content_fingerprint: str


def build_approved_model_placement_set(
    *,
    comparison,
    latest_decisions,
    profile,
) -> ApprovedModelPlacementSet:
    decision_by_input = {
        item.approved_input_id: item for item in latest_decisions
    }
    if len(decision_by_input) != len(latest_decisions):
        raise ModelPlacementContractError(
            "Latest Model Placement decisions contain duplicate Approved Inputs."
        )

    rules = {item.rule_id: item for item in profile.element_derivation_rules}
    areas = {item.model_area_id: item for item in profile.model_areas}

    placements = []
    explicitly_not_materialized = []
    decision_fingerprints = []

    for review_item in comparison.items:
        decision = decision_by_input.get(review_item.approved_input_id)
        if decision is None:
            raise ModelPlacementContractError(
                "Model Placement finalization requires a Human decision for "
                "every review item."
            )
        if decision.comparison_fingerprint != comparison.content_fingerprint:
            raise ModelPlacementContractError(
                "Model Placement decision does not bind the exact comparison."
            )
        if decision.review_item_fingerprint != review_item.content_fingerprint:
            raise ModelPlacementContractError(
                "Model Placement decision does not bind the exact review item."
            )
        decision_fingerprints.append(decision.decision_fingerprint)

        if decision.outcome == "reopened":
            raise ModelPlacementContractError(
                "Reopened Model Placement decisions block finalization."
            )
        if decision.outcome == "deferred":
            raise ModelPlacementContractError(
                "Deferred Model Placement decisions block model assembly."
            )
        if decision.outcome == "rejected":
            explicitly_not_materialized.append(review_item.approved_input_id)
            continue
        if decision.outcome != "accepted":
            raise ModelPlacementContractError(
                "Unsupported effective Model Placement decision."
            )

        selected_rule_id = decision.selected_rule_id
        if selected_rule_id not in set(review_item.allowed_rule_ids):
            raise ModelPlacementContractError(
                "Accepted placement selected a rule outside the exact review item."
            )
        rule = rules.get(selected_rule_id)
        if rule is None:
            raise ModelPlacementContractError(
                "Accepted placement selected a rule outside the pinned profile."
            )
        area = areas.get(rule.model_area_id)
        if area is None:
            raise ModelPlacementContractError(
                "Accepted placement rule references an unavailable model area."
            )

        payload = {
            "approved_input_id": review_item.approved_input_id,
            "stable_subject_key": review_item.stable_subject_key,
            "selected_rule_id": selected_rule_id,
            "model_area": rule.model_area_id,
            "element_type": rule.element_type,
            "framework_assignment": area.framework_node_id,
            "review_decision_id": decision.decision_id,
            "review_decision_fingerprint": decision.decision_fingerprint,
        }
        placements.append(
            ApprovedModelPlacement(
                **payload,
                content_fingerprint=_fingerprint(payload),
            )
        )

    placements = tuple(sorted(placements, key=lambda item: item.approved_input_id))
    explicitly_not_materialized = tuple(sorted(explicitly_not_materialized))
    decision_fingerprints = tuple(sorted(decision_fingerprints))

    payload = {
        "schema_version": APPROVED_MODEL_PLACEMENT_SET_SCHEMA_VERSION,
        "project_id": comparison.project_id,
        "comparison_fingerprint": comparison.content_fingerprint,
        "profile_id": comparison.profile_id,
        "profile_version": comparison.profile_version,
        "profile_fingerprint": comparison.profile_fingerprint,
        "placements": [_placement_payload(item) for item in placements],
        "explicitly_not_materialized_approved_input_ids": list(
            explicitly_not_materialized
        ),
        "decision_fingerprints": list(decision_fingerprints),
    }
    return ApprovedModelPlacementSet(
        schema_version=APPROVED_MODEL_PLACEMENT_SET_SCHEMA_VERSION,
        project_id=comparison.project_id,
        comparison_fingerprint=comparison.content_fingerprint,
        profile_id=comparison.profile_id,
        profile_version=comparison.profile_version,
        profile_fingerprint=comparison.profile_fingerprint,
        placements=placements,
        explicitly_not_materialized_approved_input_ids=explicitly_not_materialized,
        decision_fingerprints=decision_fingerprints,
        content_fingerprint=_fingerprint(payload),
    )


def approved_model_placement_set_to_json(value) -> str:
    payload = {
        "schema_version": value.schema_version,
        "project_id": value.project_id,
        "comparison_fingerprint": value.comparison_fingerprint,
        "profile_id": value.profile_id,
        "profile_version": value.profile_version,
        "profile_fingerprint": value.profile_fingerprint,
        "placements": [_placement_payload(item) for item in value.placements],
        "explicitly_not_materialized_approved_input_ids": list(
            value.explicitly_not_materialized_approved_input_ids
        ),
        "decision_fingerprints": list(value.decision_fingerprints),
        "content_fingerprint": value.content_fingerprint,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def approved_model_placement_set_from_json(text: str):
    try:
        payload = json.loads(text)
        value = ApprovedModelPlacementSet(
            schema_version=payload["schema_version"],
            project_id=payload["project_id"],
            comparison_fingerprint=payload["comparison_fingerprint"],
            profile_id=payload["profile_id"],
            profile_version=payload["profile_version"],
            profile_fingerprint=payload["profile_fingerprint"],
            placements=tuple(
                ApprovedModelPlacement(**item)
                for item in payload["placements"]
            ),
            explicitly_not_materialized_approved_input_ids=tuple(
                payload["explicitly_not_materialized_approved_input_ids"]
            ),
            decision_fingerprints=tuple(payload["decision_fingerprints"]),
            content_fingerprint=payload["content_fingerprint"],
        )
    except Exception as exc:
        raise ModelPlacementContractError(
            "Approved Model Placement Set JSON violates the exact contract."
        ) from exc

    if value.schema_version != APPROVED_MODEL_PLACEMENT_SET_SCHEMA_VERSION:
        raise ModelPlacementContractError(
            "Approved Model Placement Set schema version is unsupported."
        )

    check = {
        "schema_version": value.schema_version,
        "project_id": value.project_id,
        "comparison_fingerprint": value.comparison_fingerprint,
        "profile_id": value.profile_id,
        "profile_version": value.profile_version,
        "profile_fingerprint": value.profile_fingerprint,
        "placements": [_placement_payload(item) for item in value.placements],
        "explicitly_not_materialized_approved_input_ids": list(
            value.explicitly_not_materialized_approved_input_ids
        ),
        "decision_fingerprints": list(value.decision_fingerprints),
    }
    if _fingerprint(check) != value.content_fingerprint:
        raise ModelPlacementContractError(
            "Approved Model Placement Set fingerprint is invalid."
        )
    return value


def _placement_payload(item):
    return {
        "approved_input_id": item.approved_input_id,
        "stable_subject_key": item.stable_subject_key,
        "selected_rule_id": item.selected_rule_id,
        "model_area": item.model_area,
        "element_type": item.element_type,
        "framework_assignment": item.framework_assignment,
        "review_decision_id": item.review_decision_id,
        "review_decision_fingerprint": item.review_decision_fingerprint,
        "content_fingerprint": item.content_fingerprint,
    }


def _fingerprint(payload) -> str:
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
