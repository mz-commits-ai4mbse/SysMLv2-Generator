"""Hybrid deterministic-first Phase-H Model Candidate derivation."""

from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path

from modules.approved_input.types import (
    ApprovedInputManifest,
)

from .errors import ModelCandidateDerivationError
from .project_authority_handoff import phase_h_subject_key
from .llm_projection_executor import (
    LLMProjectionBatchExecutor,
    LLMProjectionInvocation,
)
from .profile_deriver import ProfileDrivenModelCandidateDeriver
from .types import (
    ModelCandidateApprovedInputSelection,
    ModelCandidateAttribute,
    ModelCandidateDerivationPlan,
    ModelCandidateGenerationProvenance,
    ModelCandidateDerivationRequest,
    ModelElementCandidateDraft,
    ModelRelationshipCandidateDraft,
    ModelStructureProfile,
    ModelDerivationRulesReference,
    RelationshipPriorityAssessment,
    RelationshipPriorityCriterionResult,
)



class HybridModelCandidateDeriver:
    """Use deterministic mapping first and LLM projection only when unresolved."""

    def __init__(
        self,
        *,
        profile: ModelStructureProfile,
        derivation_rules_reference: ModelDerivationRulesReference,
        executor: LLMProjectionBatchExecutor,
        output_dir: Path,
        review_escalation_approved_input_ids: tuple[str, ...] = (),
    ) -> None:
        if not isinstance(output_dir, Path):
            raise ModelCandidateDerivationError(
                "Hybrid derivation output_dir must be a pathlib.Path."
            )
        self.profile = profile
        self.derivation_rules_reference = derivation_rules_reference
        self.executor = executor
        self.output_dir = output_dir
        if not isinstance(
            review_escalation_approved_input_ids,
            tuple,
        ):
            raise ModelCandidateDerivationError(
                "review_escalation_approved_input_ids must be a tuple."
            )
        if len(review_escalation_approved_input_ids) != len(
            set(review_escalation_approved_input_ids)
        ):
            raise ModelCandidateDerivationError(
                "review_escalation_approved_input_ids must be unique."
            )
        self.review_escalation_approved_input_ids = tuple(
            sorted(review_escalation_approved_input_ids)
        )
        self._deterministic = ProfileDrivenModelCandidateDeriver(
            profile=profile,
            derivation_rules_reference=derivation_rules_reference,
        )
        self._areas = {
            item.model_area_id: item for item in profile.model_areas
        }
        self._element_rules = {
            item.rule_id: item for item in profile.element_derivation_rules
        }
        self._relationship_rules = {
            f"relationship:{item.semantic_intent}": item
            for item in profile.relationship_semantics
        }
        self.last_invocations: tuple[LLMProjectionInvocation, ...] = ()
        self._has_derived = False

    def derive(
        self,
        request: ModelCandidateDerivationRequest,
    ) -> ModelCandidateDerivationPlan:
        """Derive one complete Candidate proposal or fail on unresolved output."""

        coverage = self._deterministic.assess_projection_coverage(request)

        llm_target_ids = tuple(
            sorted(
                set(coverage.unresolved_approved_input_ids)
                | set(self.review_escalation_approved_input_ids)
            )
        )
        if not llm_target_ids:
            self.last_invocations = ()
            plan = self._deterministic.derive(request)
            self._has_derived = True
            return plan

        invocations = self.executor.execute(
            request=request,
            coverage=coverage,
            profile=self.profile,
            output_dir=self.output_dir,
            explicit_escalation_approved_input_ids=(
                self.review_escalation_approved_input_ids
            ),
        )
        self.last_invocations = invocations

        proposals = {
            proposal.approved_input_id: proposal
            for invocation in invocations
            for proposal in invocation.response.proposals
        }
        expected_ids = set(llm_target_ids)
        if set(proposals) != expected_ids:
            raise ModelCandidateDerivationError(
                "Hybrid target projection did not return exactly one validated "
                "proposal for every eligible Approved Input."
            )

        unresolved = tuple(
            sorted(
                approved_input_id
                for approved_input_id, proposal in proposals.items()
                if proposal.result != "proposed_mapping"
            )
        )
        if unresolved:
            raise ModelCandidateDerivationError(
                "Hybrid target projection preserved unresolved engineering "
                "information and therefore cannot generate a complete "
                f"Candidate Set: {list(unresolved)}."
            )

        coverage_by_id = {
            item.approved_input_id: item for item in coverage.entries
        }
        input_by_id = {
            item.approved_input_id: item for item in request.approved_inputs
        }

        element_drafts = []
        for approved_input in request.approved_inputs:
            entry = coverage_by_id[approved_input.approved_input_id]
            if approved_input.approved_input_kind == "human_clarification":
                continue
            if approved_input.approved_input_kind != "element_statement":
                continue

            if (
                entry.disposition == "mapped"
                and approved_input.approved_input_id
                not in self.review_escalation_approved_input_ids
            ):
                element_drafts.append(
                    self._deterministic._derive_element(
                        approved_input,
                        request=request,
                    )
                )
                continue

            proposal = proposals[approved_input.approved_input_id]
            element_drafts.append(
                self._derive_llm_element(
                    approved_input=approved_input,
                    selected_rule_id=proposal.selected_rule_id,
                    rationale=proposal.rationale,
                    deterministic_reason_code=entry.reason_code,
                    request=request,
                )
            )

        element_drafts = tuple(
            sorted(element_drafts, key=lambda item: item.draft_key)
        )

        relationship_inputs = []
        llm_relationship_ids = set()
        original_relationship_by_id = {}

        for approved_input in request.approved_inputs:
            if approved_input.approved_input_kind != "relationship_statement":
                continue

            entry = coverage_by_id[approved_input.approved_input_id]
            if (
                entry.disposition == "mapped"
                and approved_input.approved_input_id
                not in self.review_escalation_approved_input_ids
            ):
                relationship_inputs.append(approved_input)
                continue

            proposal = proposals[approved_input.approved_input_id]
            selected_rule_id = proposal.selected_rule_id
            if selected_rule_id not in self._relationship_rules:
                raise ModelCandidateDerivationError(
                    "LLM relationship proposal selected a rule outside the "
                    "pinned Model Structure Profile."
                )

            relationship = (
                approved_input.selected_relationship_representation
            )
            if relationship is None:
                raise ModelCandidateDerivationError(
                    "Hybrid projection received an invalid relationship "
                    "Approved Input."
                )

            semantic_rule = self._relationship_rules[selected_rule_id]
            proxy_relationship = replace(
                relationship,
                semantic_intent=semantic_rule.semantic_intent,
            )
            proxy_input = replace(
                approved_input,
                selected_relationship_representation=proxy_relationship,
            )
            relationship_inputs.append(proxy_input)
            llm_relationship_ids.add(approved_input.approved_input_id)
            original_relationship_by_id[
                approved_input.approved_input_id
            ] = relationship

        relationship_drafts = self._deterministic._derive_relationships(
            tuple(relationship_inputs),
            element_drafts,
            request=request,
        )
        relationship_drafts = tuple(
            self._mark_llm_relationship_draft(
                draft,
                proposals=proposals,
                llm_relationship_ids=llm_relationship_ids,
                original_relationship_by_id=original_relationship_by_id,
            )
            for draft in relationship_drafts
        )

        plan = ModelCandidateDerivationPlan(
            element_drafts=element_drafts,
            relationship_drafts=tuple(
                sorted(
                    relationship_drafts,
                    key=lambda item: item.draft_key,
                )
            ),
        )
        self._has_derived = True
        return plan

    def generation_provenance(
        self,
    ) -> ModelCandidateGenerationProvenance:
        """Describe the actual successful derivation path after derive()."""

        if not self._has_derived:
            raise ModelCandidateDerivationError(
                "Hybrid generation provenance is available only after a "
                "successful derive() call."
            )

        if not self.last_invocations:
            payload = {
                "method": "deterministic_profile_projection",
                "profile_id": self.profile.profile_id,
                "profile_version": self.profile.profile_version,
                "profile_fingerprint": self.profile.profile_fingerprint,
                "derivation_context_id": (
                    self.derivation_rules_reference.context_id
                ),
                "derivation_context_version": (
                    self.derivation_rules_reference.context_version
                ),
                "derivation_context_fingerprint": (
                    self.derivation_rules_reference.context_fingerprint
                ),
            }
            return ModelCandidateGenerationProvenance(
                method="deterministic_profile_projection",
                recipe_reference="ADR-020:H9",
                agent_reference=None,
                model_reference=None,
                context_fingerprint=self._provenance_fingerprint(payload),
            )

        providers = {item.provider for item in self.last_invocations}
        models = {item.model for item in self.last_invocations}
        if len(providers) != 1 or len(models) != 1:
            raise ModelCandidateDerivationError(
                "One hybrid Candidate Set must use one provider/model pair."
            )
        provider = next(iter(providers))
        model = next(iter(models))

        # Usage and provider response IDs are execution telemetry. They are
        # intentionally excluded so semantically identical request/response
        # content yields the same generation-context fingerprint.
        payload = {
            "method": "llm_assisted_profile_projection",
            "profile_id": self.profile.profile_id,
            "profile_version": self.profile.profile_version,
            "profile_fingerprint": self.profile.profile_fingerprint,
            "derivation_context_fingerprint": (
                self.derivation_rules_reference.context_fingerprint
            ),
            "provider": provider,
            "model": model,
            "invocations": [
                {
                    "request_fingerprint": (
                        item.request.request_fingerprint
                    ),
                    "response_fingerprint": (
                        item.response.response_fingerprint
                    ),
                    **(
                        {
                            "supporting_response_fingerprints": list(
                                item.supporting_response_fingerprints
                            ),
                            "supporting_agent_ids": list(
                                item.supporting_agent_ids
                            ),
                        }
                        if item.supporting_response_fingerprints
                        else {}
                    ),
                }
                for item in self.last_invocations
            ],
        }
        return ModelCandidateGenerationProvenance(
            method="llm_assisted_profile_projection",
            recipe_reference="ADR-020:H9",
            agent_reference=getattr(
                self.executor,
                "agent_reference",
                "agents/target_projection_mapper.md",
            ),
            model_reference=f"{provider}:{model}",
            context_fingerprint=self._provenance_fingerprint(payload),
        )

    def _provenance_fingerprint(self, payload: object) -> str:
        canonical = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(
            canonical.encode("utf-8")
        ).hexdigest()

    def _derive_llm_element(
        self,
        *,
        approved_input: ApprovedInputManifest,
        selected_rule_id: str | None,
        rationale: str,
        deterministic_reason_code: str,
        request: ModelCandidateDerivationRequest,
    ) -> ModelElementCandidateDraft:
        if selected_rule_id not in self._element_rules:
            raise ModelCandidateDerivationError(
                "LLM element proposal selected a rule outside the pinned "
                "Model Structure Profile."
            )
        rule = self._element_rules[selected_rule_id]
        area = self._areas[rule.model_area_id]

        conformance = self._deterministic._conformance(
            status="conformant",
            finding_ids=(),
            evidence={
                "approved_input_id": approved_input.approved_input_id,
                "rule_id": rule.rule_id,
                "model_area_id": rule.model_area_id,
                "element_type": rule.element_type,
                "projection_method": "llm_assisted",
                "deterministic_reason_code": deterministic_reason_code,
            },
        )

        resolved_subject_key = phase_h_subject_key(
            request,
            approved_input,
        )
        return ModelElementCandidateDraft(
            draft_key=f"element:{approved_input.approved_input_id}",
            candidate_subject_key=resolved_subject_key,
            comparison_anchor_id=(
                f"{area.comparison_anchor_prefix}:"
                f"{resolved_subject_key}"
            ),
            proposed_name=approved_input.canonical_content.title,
            description=approved_input.canonical_content.description,
            model_area=rule.model_area_id,
            element_type=rule.element_type,
            framework_assignment=area.framework_node_id,
            terminology_assignment=(
                approved_input.selected_terminology_assignment
            ),
            attributes=self._original_element_attributes(approved_input),
            approved_input_selections=(
                ModelCandidateApprovedInputSelection(
                    approved_input_id=approved_input.approved_input_id,
                    provenance_role="direct_support",
                ),
            ),
            derivation_rationale=(
                "LLM-assisted target projection selected profile rule "
                f"{rule.rule_id} after deterministic resolution returned "
                f"{deterministic_reason_code}. Rationale: {rationale}"
            ),
            support_level="partially_supported",
            assumptions=(
                "Target mapping was proposed by the LLM-assisted projection "
                "strategy within profile-controlled options and remains "
                "subject to Human Review.",
            ),
            missing_information=(),
            structure_profile_conformance=conformance,
            predecessor_candidate_ids=(),
        )

    def _original_element_attributes(
        self,
        approved_input: ApprovedInputManifest,
    ) -> tuple[ModelCandidateAttribute, ...]:
        """Preserve reviewed Approved-Input evidence without proxy rewriting."""

        content = approved_input.canonical_content
        values = {
            "approved_input_kind": approved_input.approved_input_kind,
            "primary_text": content.primary_text,
        }
        optional = {
            "information_type": content.information_type,
            "modality": content.modality,
            "epistemic_status": content.epistemic_status,
            "source_classification": approved_input.selected_classification,
            "source_framework_assignment": (
                approved_input.selected_framework_assignment
            ),
        }
        values.update(
            {
                key: value
                for key, value in optional.items()
                if value is not None
            }
        )
        return tuple(
            ModelCandidateAttribute(name=key, value=value)
            for key, value in sorted(values.items())
        )

    def _mark_llm_relationship_draft(
        self,
        draft: ModelRelationshipCandidateDraft,
        *,
        proposals,
        llm_relationship_ids: set[str],
        original_relationship_by_id,
    ) -> ModelRelationshipCandidateDraft:
        evidence_ids = tuple(
            item.approved_input_id
            for item in draft.approved_input_selections
        )
        assisted_ids = tuple(
            item for item in evidence_ids if item in llm_relationship_ids
        )
        if not assisted_ids:
            return draft

        rationales = tuple(
            proposals[item].rationale for item in assisted_ids
        )
        original_upstream = (
            original_relationship_by_id[assisted_ids[0]]
            if len(assisted_ids) == 1
            else None
        )

        # LLM assistance changes semantic support/provenance, not whether
        # the selected profile-controlled relationship shape is structurally
        # conformant. Preserve deterministic profile conformance; a genuinely
        # noncanonical profile rule remains exception_required.
        conformance = draft.structure_profile_conformance

        priority = self._llm_relationship_priority(
            draft.priority_assessment
        )

        return replace(
            draft,
            derivation_rationale=(
                "LLM-assisted target projection selected the profile "
                f"relationship semantic {draft.semantic_intent!r}. "
                "Rationale: "
                + " | ".join(rationales)
            ),
            assumptions=tuple(
                sorted(
                    set(
                        draft.assumptions
                        + (
                            "Relationship semantic mapping was proposed by "
                            "the LLM-assisted projection strategy and remains "
                            "subject to Human Review.",
                        )
                    )
                )
            ),
            priority_assessment=priority,
            structure_profile_conformance=conformance,
            upstream_relationship_representation=original_upstream,
        )

    def _llm_relationship_priority(
        self,
        priority: RelationshipPriorityAssessment,
    ) -> RelationshipPriorityAssessment:
        criteria = []
        for item in priority.criterion_results:
            if item.criterion == "semantic_fit":
                criteria.append(
                    RelationshipPriorityCriterionResult(
                        criterion=item.criterion,
                        result="llm_profile_proposal",
                        rationale=(
                            "Semantic fit was proposed by LLM-assisted target "
                            "projection within profile-controlled options."
                        ),
                    )
                )
            elif item.criterion == "assumption_burden":
                criteria.append(
                    RelationshipPriorityCriterionResult(
                        criterion=item.criterion,
                        result="llm_projection",
                        rationale=(
                            "The target relationship semantic remains an "
                            "LLM-assisted proposal until Human Review."
                        ),
                    )
                )
            else:
                criteria.append(item)

        priority_class = (
            "exception_candidate"
            if priority.priority_class == "exception_candidate"
            else "supported_alternative"
        )
        return RelationshipPriorityAssessment(
            priority_class=priority_class,
            criterion_results=tuple(criteria),
            rationale=(
                "LLM-assisted relationship projection is advisory; Human "
                "Review remains the authorization boundary."
            ),
        )
