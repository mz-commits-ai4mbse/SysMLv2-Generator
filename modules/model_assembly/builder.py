"""Assemble a reviewable model draft without creating new authority."""

from __future__ import annotations

import hashlib
import json

from modules.model_candidates.types import (
    ModelCandidateProjectionDisposition,
)
from modules.model_assembly.types import (
    MODEL_ASSEMBLY_DRAFT_SCHEMA_VERSION,
    ModelAssemblyDraft,
    ModelAssemblyElement,
    ModelAssemblyRelationship,
)
from modules.model_placement.errors import ModelPlacementContractError


def build_model_assembly_draft(
    *,
    request,
    approved_placement_set,
    profile,
    relationship_executor=None,
    output_dir=None,
    provider: str | None = None,
    model: str | None = None,
) -> ModelAssemblyDraft:
    """Assemble Human-placed elements and preserve relationship variance."""

    authority = request.approved_engineering_information
    if authority is None:
        raise ModelPlacementContractError(
            "Model Assembly requires Approved Engineering Information."
        )
    if approved_placement_set.project_id != request.project_id:
        raise ModelPlacementContractError(
            "Approved Model Placement Set belongs to another Project."
        )
    if (
        approved_placement_set.profile_id != profile.profile_id
        or approved_placement_set.profile_version != profile.profile_version
        or approved_placement_set.profile_fingerprint
        != profile.profile_fingerprint
    ):
        raise ModelPlacementContractError(
            "Approved Model Placement Set does not bind the pinned profile."
        )
    if authority.project_id != request.project_id:
        raise ModelPlacementContractError(
            "Approved Engineering Information belongs to another Project."
        )

    active_by_id = {
        item.approved_input_id: item
        for item in request.approved_inputs
    }
    subject_by_input = {
        item.approved_input_id: item
        for item in authority.subjects
    }
    subject_by_id = {
        item.canonical_subject_id: item
        for item in authority.subjects
    }

    expected_element_ids = {
        item.approved_input_id
        for item in request.approved_inputs
        if item.approved_input_kind == "element_statement"
    }
    resolved_ids = {
        item.approved_input_id
        for item in approved_placement_set.placements
    }
    rejected_ids = set(
        approved_placement_set
        .explicitly_not_materialized_approved_input_ids
    )
    if resolved_ids & rejected_ids:
        raise ModelPlacementContractError(
            "An Approved Input cannot be both placed and not materialized."
        )
    if resolved_ids | rejected_ids != expected_element_ids:
        raise ModelPlacementContractError(
            "Approved Model Placement Set does not cover the exact element "
            "Approved Input population."
        )

    elements = []
    for placement in approved_placement_set.placements:
        manifest = active_by_id.get(placement.approved_input_id)
        subject = subject_by_input.get(placement.approved_input_id)
        if manifest is None or subject is None:
            raise ModelPlacementContractError(
                "Approved placement is outside the active engineering authority."
            )
        if placement.stable_subject_key != manifest.stable_subject_key:
            raise ModelPlacementContractError(
                "Approved placement stable Subject binding is invalid."
            )
        payload = {
            "approved_input_id": placement.approved_input_id,
            "stable_subject_key": placement.stable_subject_key,
            "title": manifest.canonical_content.title,
            "primary_text": manifest.canonical_content.primary_text,
            "selected_rule_id": placement.selected_rule_id,
            "model_area": placement.model_area,
            "element_type": placement.element_type,
            "framework_assignment": placement.framework_assignment,
            "placement_decision_id": placement.review_decision_id,
            "placement_decision_fingerprint": (
                placement.review_decision_fingerprint
            ),
        }
        elements.append(
            ModelAssemblyElement(
                **payload,
                content_fingerprint=_fingerprint(payload),
            )
        )
    elements = tuple(
        sorted(elements, key=lambda item: item.approved_input_id)
    )

    rule_by_semantic = {
        item.semantic_intent: item
        for item in profile.relationship_semantics
    }
    all_rule_ids = tuple(
        sorted(
            f"relationship:{item.semantic_intent}"
            for item in profile.relationship_semantics
        )
    )

    exact_rule_by_decision = {}
    unresolved_entries = []
    for relationship in authority.relationships:
        semantic_rule = rule_by_semantic.get(
            relationship.relationship_kind
        )
        if semantic_rule is not None:
            exact_rule_by_decision[
                relationship.relationship_decision_id
            ] = f"relationship:{semantic_rule.semantic_intent}"
        else:
            unresolved_entries.append(
                ModelCandidateProjectionDisposition(
                    approved_input_id=(
                        relationship.relationship_decision_id
                    ),
                    approved_input_kind="semantic_relationship",
                    disposition="unmapped",
                    reason_code=(
                        "semantic_relationship_requires_target_projection"
                    ),
                    selected_rule_id=None,
                    candidate_rule_ids=all_rule_ids,
                    rationale=(
                        "Accepted engineering Relationship semantic is not "
                        "an exact Model Structure Profile semantic."
                    ),
                )
            )

    proposals = {}
    response_fingerprints = []
    if unresolved_entries and relationship_executor is not None:
        if output_dir is None:
            raise ModelPlacementContractError(
                "Relationship projection requires an output directory."
            )
        invocations = tuple(
            relationship_executor.execute_semantic_relationships(
                request=request,
                relationship_entries=tuple(unresolved_entries),
                profile=profile,
                output_dir=output_dir,
            )
        )
        for invocation in invocations:
            response = invocation.response
            response_fingerprints.append(
                response.response_fingerprint
            )
            for proposal in response.proposals:
                if proposal.relationship_decision_id in proposals:
                    raise ModelPlacementContractError(
                        "Relationship projection returned a duplicate decision."
                    )
                proposals[
                    proposal.relationship_decision_id
                ] = proposal
        expected = {
            item.approved_input_id
            for item in unresolved_entries
        }
        if set(proposals) != expected:
            raise ModelPlacementContractError(
                "Relationship projection did not cover the exact unresolved "
                "Relationship population."
            )

    relationships = []
    element_subject_keys = {
        item.stable_subject_key for item in elements
    }
    for relationship in authority.relationships:
        source = subject_by_id[relationship.source_subject_id]
        target = subject_by_id[relationship.target_subject_id]
        if (
            source.stable_subject_key not in element_subject_keys
            or target.stable_subject_key not in element_subject_keys
        ):
            continue

        relationship_id = relationship.relationship_decision_id
        if relationship_id in exact_rule_by_decision:
            status = "exact_profile_match"
            candidate_rule_ids = (
                exact_rule_by_decision[relationship_id],
            )
            projection_rationale = (
                "Accepted engineering Relationship semantic exactly matches "
                "one pinned profile rule."
            )
        else:
            proposal = proposals.get(relationship_id)
            if proposal is None:
                status = "unmapped"
                candidate_rule_ids = ()
                projection_rationale = (
                    "No target-relationship projection was executed. "
                    "Final Model Review must resolve representation."
                )
            elif proposal.result == "proposed_mapping":
                status = "persona_unanimous_proposal"
                candidate_rule_ids = (
                    proposal.selected_rule_id,
                )
                projection_rationale = proposal.rationale
            elif proposal.result == "ambiguous":
                status = "persona_variance"
                candidate_rule_ids = tuple(
                    sorted(proposal.alternative_rule_ids)
                )
                projection_rationale = proposal.rationale
            else:
                status = "unmapped"
                candidate_rule_ids = ()
                projection_rationale = proposal.rationale

        payload = {
            "relationship_decision_id": relationship_id,
            "relationship_decision_fingerprint": (
                relationship.relationship_decision_fingerprint
            ),
            "source_subject_id": relationship.source_subject_id,
            "source_subject_key": source.stable_subject_key,
            "relationship_kind": relationship.relationship_kind,
            "target_subject_id": relationship.target_subject_id,
            "target_subject_key": target.stable_subject_key,
            "representation_status": status,
            "candidate_rule_ids": list(candidate_rule_ids),
            "human_rationale": relationship.rationale,
            "projection_rationale": projection_rationale,
        }
        relationships.append(
            ModelAssemblyRelationship(
                relationship_decision_id=relationship_id,
                relationship_decision_fingerprint=(
                    relationship.relationship_decision_fingerprint
                ),
                source_subject_id=relationship.source_subject_id,
                source_subject_key=source.stable_subject_key,
                relationship_kind=relationship.relationship_kind,
                target_subject_id=relationship.target_subject_id,
                target_subject_key=target.stable_subject_key,
                representation_status=status,
                candidate_rule_ids=candidate_rule_ids,
                human_rationale=relationship.rationale,
                projection_rationale=projection_rationale,
                content_fingerprint=_fingerprint(payload),
            )
        )
    relationships = tuple(
        sorted(
            relationships,
            key=lambda item: item.relationship_decision_id,
        )
    )

    body = {
        "schema_version": MODEL_ASSEMBLY_DRAFT_SCHEMA_VERSION,
        "project_id": request.project_id,
        "comparison_fingerprint": (
            approved_placement_set.comparison_fingerprint
        ),
        "approved_placement_set_fingerprint": (
            approved_placement_set.content_fingerprint
        ),
        "approved_engineering_information_fingerprint": (
            authority.content_fingerprint
        ),
        "profile_id": profile.profile_id,
        "profile_version": profile.profile_version,
        "profile_fingerprint": profile.profile_fingerprint,
        "elements": [_element_payload(item) for item in elements],
        "relationships": [
            _relationship_payload(item)
            for item in relationships
        ],
        "intentionally_not_projected_relationship_decision_ids": list(
            authority.non_projectable_relationship_decision_ids
        ),
        "relationship_projection_provider": (
            provider if unresolved_entries and relationship_executor else None
        ),
        "relationship_projection_model": (
            model if unresolved_entries and relationship_executor else None
        ),
        "relationship_projection_response_fingerprints": sorted(
            response_fingerprints
        ),
    }
    return ModelAssemblyDraft(
        schema_version=MODEL_ASSEMBLY_DRAFT_SCHEMA_VERSION,
        project_id=request.project_id,
        comparison_fingerprint=(
            approved_placement_set.comparison_fingerprint
        ),
        approved_placement_set_fingerprint=(
            approved_placement_set.content_fingerprint
        ),
        approved_engineering_information_fingerprint=(
            authority.content_fingerprint
        ),
        profile_id=profile.profile_id,
        profile_version=profile.profile_version,
        profile_fingerprint=profile.profile_fingerprint,
        elements=elements,
        relationships=relationships,
        intentionally_not_projected_relationship_decision_ids=tuple(
            sorted(
                authority.non_projectable_relationship_decision_ids
            )
        ),
        relationship_projection_provider=(
            provider if unresolved_entries and relationship_executor else None
        ),
        relationship_projection_model=(
            model if unresolved_entries and relationship_executor else None
        ),
        relationship_projection_response_fingerprints=tuple(
            sorted(response_fingerprints)
        ),
        content_fingerprint=_fingerprint(body),
    )


def model_assembly_draft_to_json(value: ModelAssemblyDraft) -> str:
    payload = {
        "schema_version": value.schema_version,
        "project_id": value.project_id,
        "comparison_fingerprint": value.comparison_fingerprint,
        "approved_placement_set_fingerprint": (
            value.approved_placement_set_fingerprint
        ),
        "approved_engineering_information_fingerprint": (
            value.approved_engineering_information_fingerprint
        ),
        "profile_id": value.profile_id,
        "profile_version": value.profile_version,
        "profile_fingerprint": value.profile_fingerprint,
        "elements": [_element_payload(item) for item in value.elements],
        "relationships": [
            _relationship_payload(item)
            for item in value.relationships
        ],
        "intentionally_not_projected_relationship_decision_ids": list(
            value.intentionally_not_projected_relationship_decision_ids
        ),
        "relationship_projection_provider": (
            value.relationship_projection_provider
        ),
        "relationship_projection_model": value.relationship_projection_model,
        "relationship_projection_response_fingerprints": list(
            value.relationship_projection_response_fingerprints
        ),
        "content_fingerprint": value.content_fingerprint,
    }
    return json.dumps(
        payload,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ) + "\n"


def model_assembly_draft_from_json(text: str) -> ModelAssemblyDraft:
    try:
        payload = json.loads(text)
        elements = tuple(
            ModelAssemblyElement(**item)
            for item in payload["elements"]
        )
        relationships = tuple(
            ModelAssemblyRelationship(
                **{
                    **item,
                    "candidate_rule_ids": tuple(
                        item["candidate_rule_ids"]
                    ),
                }
            )
            for item in payload["relationships"]
        )
        value = ModelAssemblyDraft(
            schema_version=payload["schema_version"],
            project_id=payload["project_id"],
            comparison_fingerprint=payload["comparison_fingerprint"],
            approved_placement_set_fingerprint=(
                payload["approved_placement_set_fingerprint"]
            ),
            approved_engineering_information_fingerprint=(
                payload[
                    "approved_engineering_information_fingerprint"
                ]
            ),
            profile_id=payload["profile_id"],
            profile_version=payload["profile_version"],
            profile_fingerprint=payload["profile_fingerprint"],
            elements=elements,
            relationships=relationships,
            intentionally_not_projected_relationship_decision_ids=tuple(
                payload[
                    "intentionally_not_projected_relationship_decision_ids"
                ]
            ),
            relationship_projection_provider=(
                payload["relationship_projection_provider"]
            ),
            relationship_projection_model=(
                payload["relationship_projection_model"]
            ),
            relationship_projection_response_fingerprints=tuple(
                payload[
                    "relationship_projection_response_fingerprints"
                ]
            ),
            content_fingerprint=payload["content_fingerprint"],
        )
    except Exception as exc:
        raise ModelPlacementContractError(
            "Model Assembly Draft JSON violates the exact contract."
        ) from exc

    body = {
        "schema_version": value.schema_version,
        "project_id": value.project_id,
        "comparison_fingerprint": value.comparison_fingerprint,
        "approved_placement_set_fingerprint": (
            value.approved_placement_set_fingerprint
        ),
        "approved_engineering_information_fingerprint": (
            value.approved_engineering_information_fingerprint
        ),
        "profile_id": value.profile_id,
        "profile_version": value.profile_version,
        "profile_fingerprint": value.profile_fingerprint,
        "elements": [_element_payload(item) for item in value.elements],
        "relationships": [
            _relationship_payload(item)
            for item in value.relationships
        ],
        "intentionally_not_projected_relationship_decision_ids": list(
            value.intentionally_not_projected_relationship_decision_ids
        ),
        "relationship_projection_provider": (
            value.relationship_projection_provider
        ),
        "relationship_projection_model": value.relationship_projection_model,
        "relationship_projection_response_fingerprints": list(
            value.relationship_projection_response_fingerprints
        ),
    }
    if _fingerprint(body) != value.content_fingerprint:
        raise ModelPlacementContractError(
            "Model Assembly Draft fingerprint is invalid."
        )
    return value


def _element_payload(item):
    return {
        "approved_input_id": item.approved_input_id,
        "stable_subject_key": item.stable_subject_key,
        "title": item.title,
        "primary_text": item.primary_text,
        "selected_rule_id": item.selected_rule_id,
        "model_area": item.model_area,
        "element_type": item.element_type,
        "framework_assignment": item.framework_assignment,
        "placement_decision_id": item.placement_decision_id,
        "placement_decision_fingerprint": (
            item.placement_decision_fingerprint
        ),
        "content_fingerprint": item.content_fingerprint,
    }


def _relationship_payload(item):
    return {
        "relationship_decision_id": item.relationship_decision_id,
        "relationship_decision_fingerprint": (
            item.relationship_decision_fingerprint
        ),
        "source_subject_id": item.source_subject_id,
        "source_subject_key": item.source_subject_key,
        "relationship_kind": item.relationship_kind,
        "target_subject_id": item.target_subject_id,
        "target_subject_key": item.target_subject_key,
        "representation_status": item.representation_status,
        "candidate_rule_ids": list(item.candidate_rule_ids),
        "human_rationale": item.human_rationale,
        "projection_rationale": item.projection_rationale,
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
