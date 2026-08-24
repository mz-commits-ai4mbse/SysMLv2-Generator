"""Phase-H bridge from Approved Engineering Information to Model Candidates."""

from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path

from modules.approved_engineering_information import ApprovedEngineeringInformationSet
from modules.approved_input.types import ApprovedInputManifest

from .errors import ModelCandidateDerivationError, ModelCandidateReferenceError
from .types import (
    ModelCandidateApprovedInputSelection,
    ModelCandidateDerivationPlan,
    ModelCandidateDerivationRequest,
    ModelCandidateGenerationProvenance,
    ModelCandidateProjectionCoverage,
    ModelCandidateProjectionDisposition,
    ModelRelationshipCandidateDraft,
    ModelStructureProfile,
    StructuralComparabilityAssessment,
)

SEMANTIC_RELATIONSHIP_PROJECTION_KIND = "semantic_relationship"


def validate_approved_engineering_information_binding(
    *,
    project_id: str,
    approved_inputs: tuple[ApprovedInputManifest, ...],
    approved_engineering_information: ApprovedEngineeringInformationSet,
) -> None:
    """Require one exact AEI authority envelope for the Approved Input snapshot."""
    if not isinstance(approved_engineering_information, ApprovedEngineeringInformationSet):
        raise ModelCandidateReferenceError(
            "Approved Engineering Information has invalid type."
        )
    if approved_engineering_information.project_id != project_id:
        raise ModelCandidateReferenceError(
            "Approved Engineering Information belongs to another project."
        )
    if not isinstance(approved_inputs, tuple) or not all(
        isinstance(item, ApprovedInputManifest) for item in approved_inputs
    ):
        raise ModelCandidateReferenceError(
            "Approved Engineering Information binding requires Approved Inputs."
        )

    input_by_id = {item.approved_input_id: item for item in approved_inputs}
    if len(input_by_id) != len(approved_inputs):
        raise ModelCandidateReferenceError(
            "Approved Input snapshot contains duplicate identities."
        )

    subjects = approved_engineering_information.subjects
    subject_by_input = {item.approved_input_id: item for item in subjects}
    if len(subject_by_input) != len(subjects):
        raise ModelCandidateReferenceError(
            "Approved Engineering Information contains duplicate Subject bindings."
        )
    if set(subject_by_input) != set(input_by_id):
        raise ModelCandidateReferenceError(
            "Approved Engineering Information Subjects do not match the exact "
            "active Approved Input snapshot."
        )

    for approved_input_id, manifest in input_by_id.items():
        subject = subject_by_input[approved_input_id]
        if subject.stable_subject_key != manifest.stable_subject_key:
            raise ModelCandidateReferenceError(
                "Approved Engineering Subject stable key does not match "
                f"{approved_input_id}."
            )
        if subject.approved_input_fingerprint != manifest.content_fingerprint:
            raise ModelCandidateReferenceError(
                "Approved Engineering Subject fingerprint does not match "
                f"{approved_input_id}."
            )
        if subject.review_item_id != manifest.review_item_id:
            raise ModelCandidateReferenceError(
                "Approved Engineering Subject Review Item does not match "
                f"{approved_input_id}."
            )
        if subject.review_item_fingerprint != manifest.review_item_fingerprint:
            raise ModelCandidateReferenceError(
                "Approved Engineering Subject Review fingerprint does not match "
                f"{approved_input_id}."
            )
        if (
            manifest.review_document_id
            != approved_engineering_information.review_document_id
            or manifest.review_document_version_id
            != approved_engineering_information.review_document_version_id
            or manifest.review_revision_id
            != approved_engineering_information.review_revision_id
        ):
            raise ModelCandidateReferenceError(
                "Approved Input Review authority does not match the Approved "
                "Engineering Information envelope."
            )

    approved_subject_ids = {item.canonical_subject_id for item in subjects}
    decision_ids = tuple(
        item.relationship_decision_id
        for item in approved_engineering_information.relationships
    )
    if len(decision_ids) != len(set(decision_ids)):
        raise ModelCandidateReferenceError(
            "Approved Engineering Information contains duplicate Relationship "
            "decision identities."
        )

    non_promotable_subject_ids = (
        approved_engineering_information.non_promotable_subject_ids
    )
    if len(non_promotable_subject_ids) != len(
        set(non_promotable_subject_ids)
    ):
        raise ModelCandidateReferenceError(
            "Approved Engineering Information contains duplicate "
            "non-promotable Subject identities."
        )
    if set(non_promotable_subject_ids) & approved_subject_ids:
        raise ModelCandidateReferenceError(
            "A Subject cannot be both approved/model-promotable and "
            "non-promotable."
        )

    non_projectable_relationship_ids = (
        approved_engineering_information
        .non_projectable_relationship_decision_ids
    )
    if len(non_projectable_relationship_ids) != len(
        set(non_projectable_relationship_ids)
    ):
        raise ModelCandidateReferenceError(
            "Approved Engineering Information contains duplicate "
            "non-projectable Relationship decision identities."
        )
    if set(non_projectable_relationship_ids) & set(decision_ids):
        raise ModelCandidateReferenceError(
            "A Relationship decision cannot be both projectable and "
            "non-projectable."
        )

    for relationship in approved_engineering_information.relationships:
        if (
            relationship.source_subject_id not in approved_subject_ids
            or relationship.target_subject_id not in approved_subject_ids
        ):
            raise ModelCandidateReferenceError(
                "Approved Engineering Relationship endpoint is outside the "
                "approved Subject population."
            )


def bind_generation_provenance_to_approved_engineering_information(
    provenance: ModelCandidateGenerationProvenance,
    approved_engineering_information: ApprovedEngineeringInformationSet | None,
) -> ModelCandidateGenerationProvenance:
    """Cryptographically bind Candidate generation context to AEI authority."""
    if approved_engineering_information is None:
        return provenance
    if not isinstance(provenance, ModelCandidateGenerationProvenance):
        raise ModelCandidateReferenceError("Generation provenance has invalid type.")
    payload = {
        "generation_method": provenance.method,
        "recipe_reference": provenance.recipe_reference,
        "agent_reference": provenance.agent_reference,
        "model_reference": provenance.model_reference,
        "base_context_fingerprint": provenance.context_fingerprint,
        "approved_engineering_information_fingerprint": (
            approved_engineering_information.content_fingerprint
        ),
    }
    return replace(provenance, context_fingerprint=_fingerprint(payload))


class ApprovedEngineeringInformationDeriver:
    """Add finalized semantic Relationship authority to an existing H deriver."""

    def __init__(
        self,
        *,
        base_deriver,
        profile: ModelStructureProfile,
        relationship_executor=None,
        output_dir: Path | None = None,
    ) -> None:
        self.base_deriver = base_deriver
        self.profile = profile
        self.relationship_executor = relationship_executor
        self.output_dir = output_dir
        self.last_relationship_invocations = ()
        self._derived = False

    def assess_projection_coverage(
        self,
        request: ModelCandidateDerivationRequest,
    ) -> ModelCandidateProjectionCoverage:
        base = self.base_deriver.assess_projection_coverage(request)
        authority = request.approved_engineering_information
        if authority is None:
            return base
        validate_approved_engineering_information_binding(
            project_id=request.project_id,
            approved_inputs=request.approved_inputs,
            approved_engineering_information=authority,
        )
        return ModelCandidateProjectionCoverage(
            project_id=base.project_id,
            model_structure_profile_reference=base.model_structure_profile_reference,
            entries=tuple(
                (
                    *base.entries,
                    *self._relationship_projection_entries(authority),
                    *self._non_projectable_relationship_entries(authority),
                )
            ),
        )

    def derive(
        self,
        request: ModelCandidateDerivationRequest,
    ) -> ModelCandidateDerivationPlan:
        base_plan = self.base_deriver.derive(request)
        authority = request.approved_engineering_information
        if authority is None or not authority.relationships:
            self.last_relationship_invocations = ()
            self._derived = True
            return base_plan

        validate_approved_engineering_information_binding(
            project_id=request.project_id,
            approved_inputs=request.approved_inputs,
            approved_engineering_information=authority,
        )
        entries = self._relationship_projection_entries(authority)
        selected_rules = {
            item.approved_input_id: item.selected_rule_id
            for item in entries
            if item.disposition == "mapped" and item.selected_rule_id is not None
        }
        unresolved = tuple(
            item
            for item in entries
            if item.disposition in {"ambiguous", "unmapped"}
        )

        self.last_relationship_invocations = ()
        if unresolved:
            if self.relationship_executor is None:
                raise ModelCandidateDerivationError(
                    "Accepted semantic Relationships contain unresolved target "
                    "mappings. Eco deterministic derivation fails closed."
                )
            if self.output_dir is None:
                raise ModelCandidateDerivationError(
                    "Semantic Relationship projection requires an output_dir."
                )
            execute = getattr(
                self.relationship_executor,
                "execute_semantic_relationships",
                None,
            )
            if execute is None or not callable(execute):
                raise ModelCandidateDerivationError(
                    "Relationship projection executor does not implement "
                    "execute_semantic_relationships()."
                )
            invocations = tuple(
                execute(
                    request=request,
                    relationship_entries=unresolved,
                    profile=self.profile,
                    output_dir=self.output_dir / "semantic_relationship_projection",
                )
            )
            self.last_relationship_invocations = invocations
            proposals = {
                proposal.relationship_decision_id: proposal
                for invocation in invocations
                for proposal in invocation.response.proposals
            }
            expected = {item.approved_input_id for item in unresolved}
            if set(proposals) != expected:
                raise ModelCandidateDerivationError(
                    "Semantic Relationship projection did not return exactly "
                    "one validated proposal for every unresolved Relationship."
                )
            still_unresolved = tuple(
                sorted(
                    relationship_id
                    for relationship_id, proposal in proposals.items()
                    if proposal.result != "proposed_mapping"
                    or proposal.selected_rule_id is None
                )
            )
            if still_unresolved:
                raise ModelCandidateDerivationError(
                    "Semantic Relationship target projection preserved "
                    "unresolved engineering meaning and cannot create a complete "
                    f"Candidate Set: {list(still_unresolved)}."
                )
            selected_rules.update(
                {
                    relationship_id: proposal.selected_rule_id
                    for relationship_id, proposal in proposals.items()
                }
            )

        relationship_drafts = self._relationship_drafts(
            authority=authority,
            element_drafts=base_plan.element_drafts,
            selected_rules=selected_rules,
        )
        self._derived = True
        return ModelCandidateDerivationPlan(
            element_drafts=base_plan.element_drafts,
            relationship_drafts=tuple(
                sorted(
                    (*base_plan.relationship_drafts, *relationship_drafts),
                    key=lambda item: item.draft_key,
                )
            ),
        )

    def generation_provenance(self) -> ModelCandidateGenerationProvenance:
        provider = getattr(self.base_deriver, "generation_provenance", None)
        if provider is None or not callable(provider):
            raise ModelCandidateDerivationError(
                "Wrapped deriver does not provide generation_provenance()."
            )
        base = provider()
        if not self._derived or not self.last_relationship_invocations:
            return base
        payload = {
            "base_context_fingerprint": base.context_fingerprint,
            "semantic_relationship_invocations": [
                {
                    "request_fingerprint": invocation.request.request_fingerprint,
                    "response_fingerprint": invocation.response.response_fingerprint,
                }
                for invocation in self.last_relationship_invocations
            ],
        }
        return replace(base, context_fingerprint=_fingerprint(payload))

    def _non_projectable_relationship_entries(
        self,
        authority: ApprovedEngineeringInformationSet,
    ) -> tuple[ModelCandidateProjectionDisposition, ...]:
        return tuple(
            ModelCandidateProjectionDisposition(
                approved_input_id=relationship_decision_id,
                approved_input_kind=SEMANTIC_RELATIONSHIP_PROJECTION_KIND,
                disposition="intentionally_not_projected",
                reason_code="non_promotable_relationship_endpoint",
                selected_rule_id=None,
                candidate_rule_ids=(),
                rationale=(
                    "Accepted Human-reviewed engineering Relationship "
                    "references at least one accepted Open Question that is "
                    "intentionally not promotable to an Approved Input. The "
                    "Relationship remains in Approved Engineering Information "
                    "authority but is not eligible for target-model projection "
                    "until both endpoints are model-promotable."
                ),
            )
            for relationship_decision_id in (
                authority.non_projectable_relationship_decision_ids
            )
        )

    def _relationship_projection_entries(
        self,
        authority: ApprovedEngineeringInformationSet,
    ) -> tuple[ModelCandidateProjectionDisposition, ...]:
        rules = {
            item.semantic_intent: item
            for item in self.profile.relationship_semantics
        }
        all_rule_ids = tuple(
            sorted(f"relationship:{value}" for value in rules)
        )
        result = []
        for relationship in authority.relationships:
            rule = rules.get(relationship.relationship_kind)
            if rule is None:
                result.append(
                    ModelCandidateProjectionDisposition(
                        approved_input_id=relationship.relationship_decision_id,
                        approved_input_kind=SEMANTIC_RELATIONSHIP_PROJECTION_KIND,
                        disposition="unmapped",
                        reason_code="semantic_relationship_requires_target_projection",
                        selected_rule_id=None,
                        candidate_rule_ids=all_rule_ids,
                        rationale=(
                            "Accepted engineering Relationship semantic is not "
                            "an exact Model Structure Profile semantic and must "
                            "be projected without changing Human authority."
                        ),
                    )
                )
                continue
            rule_id = f"relationship:{rule.semantic_intent}"
            result.append(
                ModelCandidateProjectionDisposition(
                    approved_input_id=relationship.relationship_decision_id,
                    approved_input_kind=SEMANTIC_RELATIONSHIP_PROJECTION_KIND,
                    disposition="mapped",
                    reason_code="exact_semantic_relationship_profile_mapping",
                    selected_rule_id=rule_id,
                    candidate_rule_ids=(rule_id,),
                    rationale=(
                        "Accepted engineering Relationship semantic exactly "
                        "matches one Model Structure Profile semantic."
                    ),
                )
            )
        return tuple(sorted(result, key=lambda item: item.approved_input_id))

    def _relationship_drafts(
        self,
        *,
        authority: ApprovedEngineeringInformationSet,
        element_drafts,
        selected_rules: dict[str, str],
    ) -> tuple[ModelRelationshipCandidateDraft, ...]:
        rule_by_id = {
            f"relationship:{item.semantic_intent}": item
            for item in self.profile.relationship_semantics
        }
        subject_by_id = {
            item.canonical_subject_id: item
            for item in authority.subjects
        }
        subject_index = {}
        for draft in element_drafts:
            subject_index.setdefault(draft.candidate_subject_key, []).append(draft)

        grouped = {}
        for relationship in authority.relationships:
            selected_rule_id = selected_rules.get(
                relationship.relationship_decision_id
            )
            if selected_rule_id not in rule_by_id:
                raise ModelCandidateDerivationError(
                    "Semantic Relationship projection selected a rule outside "
                    "the pinned Model Structure Profile."
                )
            source = subject_by_id[relationship.source_subject_id]
            target = subject_by_id[relationship.target_subject_id]
            key = (
                source.stable_subject_key,
                target.stable_subject_key,
                selected_rule_id,
            )
            grouped.setdefault(key, []).append(relationship)

        endpoint_groups = {}
        for key in grouped:
            endpoint_groups.setdefault(key[:2], []).append(key)

        profile_deriver = self._profile_deriver()
        drafts = []
        for key in sorted(grouped):
            source_key, target_key, selected_rule_id = key
            relationships = tuple(
                sorted(
                    grouped[key],
                    key=lambda item: item.relationship_decision_id,
                )
            )
            semantic_rule = rule_by_id[selected_rule_id]
            endpoint_key = (source_key, target_key)
            endpoint_certainty = self._endpoint_certainty(
                endpoint_key,
                subject_index,
            )
            comparability = self._comparability(
                endpoint_key=endpoint_key,
                semantic_rule=semantic_rule,
                subject_index=subject_index,
                endpoint_certainty=endpoint_certainty,
            )
            if semantic_rule.canonical:
                conformance_status = "conformant"
                findings = ()
            else:
                conformance_status = "exception_required"
                findings = tuple(
                    item
                    for item in (semantic_rule.deviation_id,)
                    if item is not None
                )
            conformance = profile_deriver._conformance(
                status=conformance_status,
                finding_ids=findings,
                evidence={
                    "approved_engineering_information_fingerprint": (
                        authority.content_fingerprint
                    ),
                    "relationship_decision_ids": [
                        item.relationship_decision_id for item in relationships
                    ],
                    "semantic_intent": semantic_rule.semantic_intent,
                    "relationship_family": semantic_rule.relationship_family,
                    "directionality": semantic_rule.directionality,
                    "canonical": semantic_rule.canonical,
                },
            )
            priority = profile_deriver._priority(
                semantic_rule,
                endpoint_certainty,
                comparability,
                conformance,
            )
            source_subject = next(
                item for item in authority.subjects
                if item.stable_subject_key == source_key
            )
            target_subject = next(
                item for item in authority.subjects
                if item.stable_subject_key == target_key
            )
            support_input_ids = tuple(
                sorted(
                    {
                        source_subject.approved_input_id,
                        target_subject.approved_input_id,
                    }
                )
            )
            exact = all(
                item.relationship_kind == semantic_rule.semantic_intent
                for item in relationships
            )
            assumptions = (
                ()
                if exact
                else (
                    "Target Relationship semantic was selected by LLM-assisted "
                    "profile-bounded projection and remains subject to Human "
                    "Model Candidate Review.",
                )
            )
            evidence = tuple(
                sorted(
                    f"{item.relationship_decision_id}:"
                    f"{item.relationship_decision_fingerprint}"
                    for item in relationships
                )
            )
            draft_payload = {
                "source_subject_key": source_key,
                "target_subject_key": target_key,
                "selected_rule_id": selected_rule_id,
                "relationship_decision_ids": [
                    item.relationship_decision_id for item in relationships
                ],
            }
            drafts.append(
                ModelRelationshipCandidateDraft(
                    draft_key="relationship:aei:" + _fingerprint(draft_payload)[:16],
                    relationship_choice_key=(
                        None
                        if len(endpoint_groups[endpoint_key]) == 1
                        else self._choice_key(endpoint_key)
                    ),
                    source_subject_key=source_key,
                    target_subject_key=target_key,
                    relationship_family=semantic_rule.relationship_family,
                    semantic_intent=semantic_rule.semantic_intent,
                    directionality=semantic_rule.directionality,
                    approved_input_selections=tuple(
                        ModelCandidateApprovedInputSelection(
                            approved_input_id=approved_input_id,
                            provenance_role="semantic_relationship_endpoint",
                        )
                        for approved_input_id in support_input_ids
                    ),
                    derivation_rationale=(
                        "Accepted Human-reviewed engineering Relationship "
                        + ("exactly matched" if exact else "was LLM-projected to")
                        + " profile rule "
                        + selected_rule_id
                        + "."
                    ),
                    supporting_evidence=evidence,
                    assumptions=assumptions,
                    missing_information=(
                        ()
                        if endpoint_certainty == "resolved"
                        else ("exact_relationship_endpoint_resolution",)
                    ),
                    priority_assessment=priority,
                    comparability_assessment=comparability,
                    structure_profile_conformance=conformance,
                    upstream_relationship_representation=None,
                    predecessor_candidate_ids=(),
                )
            )
        return tuple(sorted(drafts, key=lambda item: item.draft_key))

    def _profile_deriver(self):
        if (
            callable(getattr(self.base_deriver, "_conformance", None))
            and callable(getattr(self.base_deriver, "_priority", None))
        ):
            return self.base_deriver
        deterministic = getattr(self.base_deriver, "_deterministic", None)
        if (
            deterministic is not None
            and callable(getattr(deterministic, "_conformance", None))
            and callable(getattr(deterministic, "_priority", None))
        ):
            return deterministic
        raise ModelCandidateDerivationError(
            "Wrapped Phase-H deriver does not expose the profile-controlled "
            "relationship assessment helpers."
        )

    def _endpoint_certainty(self, endpoint_key, subject_index) -> str:
        counts = (
            len(subject_index.get(endpoint_key[0], ())),
            len(subject_index.get(endpoint_key[1], ())),
        )
        if counts == (1, 1):
            return "resolved"
        if 0 in counts:
            return "unresolved"
        return "ambiguous"

    def _comparability(
        self,
        *,
        endpoint_key,
        semantic_rule,
        subject_index,
        endpoint_certainty: str,
    ) -> StructuralComparabilityAssessment:
        anchors = []
        for subject_key in endpoint_key:
            matches = subject_index.get(subject_key, ())
            if len(matches) == 1:
                anchor = matches[0].comparison_anchor_id
                if anchor is not None:
                    anchors.append(anchor)
        if endpoint_certainty != "resolved":
            impact = "unknown"
            canonical_match = None
        elif semantic_rule.canonical:
            impact = "improves"
            canonical_match = True
        else:
            impact = "reduces"
            canonical_match = False
        deviations = (
            () if semantic_rule.deviation_id is None
            else (semantic_rule.deviation_id,)
        )
        return StructuralComparabilityAssessment(
            impact=impact,
            comparison_anchor_ids=tuple(sorted(set(anchors))),
            canonical_pattern_match=canonical_match,
            deviation_ids=deviations,
            rationale=(
                "Accepted engineering Relationship was projected through the "
                "pinned Model Structure Profile; endpoint certainty is "
                f"{endpoint_certainty}."
            ),
        )

    def _choice_key(self, endpoint_key) -> str:
        return (
            "choice:"
            + hashlib.sha256(
                "|".join(endpoint_key).encode("utf-8")
            ).hexdigest()[:16]
        )


def _fingerprint(payload: object) -> str:
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
