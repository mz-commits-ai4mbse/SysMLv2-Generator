"""Assemble a reviewable model draft without creating new authority."""

from __future__ import annotations

import hashlib
import json

from modules.model_candidates.types import (
    ModelCandidateProjectionDisposition,
)
from modules.model_candidates.project_authority_handoff import (
    phase_h_subject_key,
    validate_project_authority_phase_h_request,
)
from modules.model_assembly.types import (
    MODEL_ASSEMBLY_DRAFT_SCHEMA_VERSION,
    MODEL_ASSEMBLY_PROJECT_AUTHORITY_SCHEMA_VERSION,
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
    handoff = getattr(request, "project_authority_handoff", None)
    if (authority is None) == (handoff is None):
        raise ModelPlacementContractError(
            "Model Assembly requires exactly one engineering authority mode: "
            "one source-local Approved Engineering Information envelope or "
            "one Project Engineering Authority handoff."
        )
    if handoff is not None:
        validate_project_authority_phase_h_request(request)
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
    if authority is not None and authority.project_id != request.project_id:
        raise ModelPlacementContractError(
            "Approved Engineering Information belongs to another Project."
        )

    active_by_id = {
        item.approved_input_id: item
        for item in request.approved_inputs
    }
    if handoff is None:
        subject_by_input = {
            item.approved_input_id: item
            for item in authority.subjects
        }
        subject_by_id = {
            item.canonical_subject_id: item
            for item in authority.subjects
        }
        relationship_records = tuple(
            _relationship_record_from_aei(
                item,
                subject_by_id=subject_by_id,
            )
            for item in authority.relationships
        )
        non_projectable_relationship_ids = tuple(
            authority.non_projectable_relationship_decision_ids
        )
        schema_version = MODEL_ASSEMBLY_DRAFT_SCHEMA_VERSION
        authority_binding = {
            "approved_engineering_information_fingerprint": (
                authority.content_fingerprint
            ),
            "project_authority_handoff_fingerprint": None,
            "project_engineering_authority_fingerprint": None,
            "model_impact_reconciliation_fingerprint": None,
            "source_approved_engineering_information_fingerprints": (),
        }
    else:
        subject_by_input = {
            item.approved_input_id: item
            for item in handoff.subjects
            if item.project_authority_state == "active"
        }
        relationship_records = tuple(
            _relationship_record_from_handoff(item)
            for item in handoff.relationships
        )
        non_projectable_relationship_ids = tuple(
            item.relationship_ref
            for item in handoff.non_projectable_relationships
        )
        schema_version = MODEL_ASSEMBLY_PROJECT_AUTHORITY_SCHEMA_VERSION
        authority_binding = {
            "approved_engineering_information_fingerprint": None,
            "project_authority_handoff_fingerprint": (
                handoff.content_fingerprint
            ),
            "project_engineering_authority_fingerprint": (
                handoff.project_authority_fingerprint
            ),
            "model_impact_reconciliation_fingerprint": (
                handoff.model_impact_fingerprint
            ),
            "source_approved_engineering_information_fingerprints": tuple(
                sorted(
                    item.content_fingerprint
                    for item in handoff.source_aei_references
                )
            ),
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
        if placement.stable_subject_key != phase_h_subject_key(
            request,
            manifest,
        ):
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
    for relationship in relationship_records:
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
    if (
        handoff is not None
        and unresolved_entries
        and relationship_executor is not None
    ):
        raise ModelPlacementContractError(
            "Project-authority Relationship projection must not synthesize "
            "a single-AEI LLM authority context. Preserve the Relationship "
            "for Human Final Model Review."
        )
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
    for relationship in relationship_records:
        if (
            relationship.source_subject_key not in element_subject_keys
            or relationship.target_subject_key not in element_subject_keys
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
            "source_subject_key": relationship.source_subject_key,
            "relationship_kind": relationship.relationship_kind,
            "target_subject_id": relationship.target_subject_id,
            "target_subject_key": relationship.target_subject_key,
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
                source_subject_key=relationship.source_subject_key,
                relationship_kind=relationship.relationship_kind,
                target_subject_id=relationship.target_subject_id,
                target_subject_key=relationship.target_subject_key,
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
        "schema_version": schema_version,
        "project_id": request.project_id,
        "comparison_fingerprint": (
            approved_placement_set.comparison_fingerprint
        ),
        "approved_placement_set_fingerprint": (
            approved_placement_set.content_fingerprint
        ),
        "approved_engineering_information_fingerprint": (
            authority_binding[
                "approved_engineering_information_fingerprint"
            ]
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
            non_projectable_relationship_ids
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
    _add_project_authority_binding_to_payload(
        body,
        authority_binding,
    )
    return ModelAssemblyDraft(
        schema_version=schema_version,
        project_id=request.project_id,
        comparison_fingerprint=(
            approved_placement_set.comparison_fingerprint
        ),
        approved_placement_set_fingerprint=(
            approved_placement_set.content_fingerprint
        ),
        approved_engineering_information_fingerprint=(
            authority_binding[
                "approved_engineering_information_fingerprint"
            ]
        ),
        profile_id=profile.profile_id,
        profile_version=profile.profile_version,
        profile_fingerprint=profile.profile_fingerprint,
        elements=elements,
        relationships=relationships,
        intentionally_not_projected_relationship_decision_ids=tuple(
            sorted(
                non_projectable_relationship_ids
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
        project_authority_handoff_fingerprint=(
            authority_binding[
                "project_authority_handoff_fingerprint"
            ]
        ),
        project_engineering_authority_fingerprint=(
            authority_binding[
                "project_engineering_authority_fingerprint"
            ]
        ),
        model_impact_reconciliation_fingerprint=(
            authority_binding[
                "model_impact_reconciliation_fingerprint"
            ]
        ),
        source_approved_engineering_information_fingerprints=(
            authority_binding[
                "source_approved_engineering_information_fingerprints"
            ]
        ),
    )


def model_assembly_draft_to_json(value: ModelAssemblyDraft) -> str:
    _validate_model_assembly_authority_shape(value)
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
    _add_project_authority_binding_to_payload(
        payload,
        _authority_binding_from_value(value),
    )
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
            project_authority_handoff_fingerprint=payload.get(
                "project_authority_handoff_fingerprint"
            ),
            project_engineering_authority_fingerprint=payload.get(
                "project_engineering_authority_fingerprint"
            ),
            model_impact_reconciliation_fingerprint=payload.get(
                "model_impact_reconciliation_fingerprint"
            ),
            source_approved_engineering_information_fingerprints=tuple(
                payload.get(
                    "source_approved_engineering_information_fingerprints",
                    (),
                )
            ),
        )
    except Exception as exc:
        raise ModelPlacementContractError(
            "Model Assembly Draft JSON violates the exact contract."
        ) from exc

    _validate_model_assembly_authority_shape(value)
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
    _add_project_authority_binding_to_payload(
        body,
        _authority_binding_from_value(value),
    )
    if _fingerprint(body) != value.content_fingerprint:
        raise ModelPlacementContractError(
            "Model Assembly Draft fingerprint is invalid."
        )
    return value



def _relationship_record_from_aei(item, *, subject_by_id):
    from types import SimpleNamespace

    source = subject_by_id[item.source_subject_id]
    target = subject_by_id[item.target_subject_id]
    return SimpleNamespace(
        relationship_decision_id=item.relationship_decision_id,
        relationship_decision_fingerprint=(
            item.relationship_decision_fingerprint
        ),
        source_subject_id=item.source_subject_id,
        source_subject_key=source.stable_subject_key,
        relationship_kind=item.relationship_kind,
        target_subject_id=item.target_subject_id,
        target_subject_key=target.stable_subject_key,
        rationale=item.rationale,
    )


def _relationship_record_from_handoff(item):
    from types import SimpleNamespace

    return SimpleNamespace(
        relationship_decision_id=item.relationship_ref,
        relationship_decision_fingerprint=(
            item.relationship_decision_fingerprint
        ),
        source_subject_id=item.source_subject_ref,
        source_subject_key=item.source_phase_h_subject_key,
        relationship_kind=item.relationship_kind,
        target_subject_id=item.target_subject_ref,
        target_subject_key=item.target_phase_h_subject_key,
        rationale=item.rationale,
    )


def _authority_binding_from_value(value):
    return {
        "approved_engineering_information_fingerprint": (
            value.approved_engineering_information_fingerprint
        ),
        "project_authority_handoff_fingerprint": (
            value.project_authority_handoff_fingerprint
        ),
        "project_engineering_authority_fingerprint": (
            value.project_engineering_authority_fingerprint
        ),
        "model_impact_reconciliation_fingerprint": (
            value.model_impact_reconciliation_fingerprint
        ),
        "source_approved_engineering_information_fingerprints": (
            value.source_approved_engineering_information_fingerprints
        ),
    }


def _add_project_authority_binding_to_payload(payload, binding):
    handoff_fingerprint = binding[
        "project_authority_handoff_fingerprint"
    ]
    if handoff_fingerprint is None:
        return
    payload["project_authority_handoff_fingerprint"] = handoff_fingerprint
    payload["project_engineering_authority_fingerprint"] = binding[
        "project_engineering_authority_fingerprint"
    ]
    payload["model_impact_reconciliation_fingerprint"] = binding[
        "model_impact_reconciliation_fingerprint"
    ]
    payload["source_approved_engineering_information_fingerprints"] = list(
        binding[
            "source_approved_engineering_information_fingerprints"
        ]
    )


def _validate_model_assembly_authority_shape(value):
    if value.schema_version == MODEL_ASSEMBLY_DRAFT_SCHEMA_VERSION:
        if value.approved_engineering_information_fingerprint is None:
            raise ModelPlacementContractError(
                "Legacy Model Assembly requires one AEI fingerprint."
            )
        if any(
            item is not None
            for item in (
                value.project_authority_handoff_fingerprint,
                value.project_engineering_authority_fingerprint,
                value.model_impact_reconciliation_fingerprint,
            )
        ) or value.source_approved_engineering_information_fingerprints:
            raise ModelPlacementContractError(
                "Legacy Model Assembly must not contain Project Authority "
                "binding."
            )
        return

    if (
        value.schema_version
        != MODEL_ASSEMBLY_PROJECT_AUTHORITY_SCHEMA_VERSION
    ):
        raise ModelPlacementContractError(
            "Model Assembly Draft schema version is unsupported."
        )
    if value.approved_engineering_information_fingerprint is not None:
        raise ModelPlacementContractError(
            "Project-authority Model Assembly must not claim one AEI "
            "fingerprint."
        )
    required = (
        value.project_authority_handoff_fingerprint,
        value.project_engineering_authority_fingerprint,
        value.model_impact_reconciliation_fingerprint,
    )
    if any(
        not isinstance(item, str) or len(item) != 64
        for item in required
    ):
        raise ModelPlacementContractError(
            "Project-authority Model Assembly binding is incomplete."
        )
    values = value.source_approved_engineering_information_fingerprints
    if (
        not values
        or values != tuple(sorted(values))
        or len(values) != len(set(values))
        or any(not isinstance(item, str) or len(item) != 64 for item in values)
    ):
        raise ModelPlacementContractError(
            "Source-local AEI fingerprint set is invalid."
        )

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
