"""Conservative profile-driven Phase-H Model Candidate derivation."""

from __future__ import annotations

import hashlib
import json

from modules.approved_input.types import (
    ApprovedInputManifest,
    ApprovedInputRelationshipRepresentation,
)

from .errors import (
    ModelCandidateDerivationError,
    ModelCandidateReferenceError,
)
from .structure_profile import (
    RELATIONSHIP_PRIORITY_CRITERIA,
    model_structure_profile_reference,
)
from .types import (
    ModelCandidateApprovedInputSelection,
    ModelCandidateAttribute,
    ModelCandidateDerivationPlan,
    ModelCandidateDerivationRequest,
    ModelDerivationRulesReference,
    ModelElementCandidateDraft,
    ModelElementDerivationRule,
    ModelRelationshipCandidateDraft,
    ModelRelationshipSemanticRule,
    ModelStructureAreaDefinition,
    ModelStructureProfile,
    RelationshipPriorityAssessment,
    RelationshipPriorityCriterionResult,
    StructuralComparabilityAssessment,
    StructuralProfileConformance,
)


class ProfileDrivenModelCandidateDeriver:
    """Derive only profile-supported content from reviewed Approved Inputs."""

    def __init__(
        self,
        *,
        profile: ModelStructureProfile,
        derivation_rules_reference: ModelDerivationRulesReference,
    ) -> None:
        self.profile = profile
        self.derivation_rules_reference = derivation_rules_reference
        self._areas = {
            item.model_area_id: item
            for item in profile.model_areas
        }
        self._relationship_rules = {
            item.semantic_intent: item
            for item in profile.relationship_semantics
        }

    def derive(
        self,
        request: ModelCandidateDerivationRequest,
    ) -> ModelCandidateDerivationPlan:
        """Interpret the complete active snapshot without inventing semantics."""

        self._validate_request_bindings(request)

        element_drafts = tuple(
            self._derive_element(item)
            for item in request.approved_inputs
            if item.approved_input_kind == "element_statement"
        )
        element_drafts = tuple(
            sorted(element_drafts, key=lambda item: item.draft_key)
        )

        relationships = tuple(
            item
            for item in request.approved_inputs
            if item.approved_input_kind == "relationship_statement"
        )
        relationship_drafts = self._derive_relationships(
            relationships,
            element_drafts,
        )

        # human_clarification remains available in request.approved_inputs as
        # reviewed context but is intentionally not auto-materialized.
        return ModelCandidateDerivationPlan(
            element_drafts=element_drafts,
            relationship_drafts=relationship_drafts,
        )

    def _validate_request_bindings(
        self,
        request: ModelCandidateDerivationRequest,
    ) -> None:
        expected_profile = model_structure_profile_reference(
            self.profile
        )
        if (
            request.model_structure_profile_reference
            != expected_profile
        ):
            raise ModelCandidateReferenceError(
                "Derivation request Model Structure Profile reference "
                "does not match the configured profile."
            )
        if (
            request.derivation_rules_reference
            != self.derivation_rules_reference
        ):
            raise ModelCandidateReferenceError(
                "Derivation request rules reference does not match "
                "the configured derivation rules."
            )
        if (
            request.framework_template_reference.template_id
            != self.profile.framework_template_id
            or request.framework_template_reference.template_version
            != self.profile.framework_template_version
        ):
            raise ModelCandidateReferenceError(
                "Derivation request Framework Template does not match "
                "the configured Model Structure Profile."
            )

    def _derive_element(
        self,
        approved_input: ApprovedInputManifest,
    ) -> ModelElementCandidateDraft:
        rule, support_level, findings, missing = (
            self._select_element_rule(approved_input)
        )
        area = self._areas[rule.model_area_id]
        attributes = self._element_attributes(approved_input)
        conformance = self._conformance(
            status=(
                "conformant"
                if support_level == "supported"
                else "review_required"
            ),
            finding_ids=findings,
            evidence={
                "approved_input_id": approved_input.approved_input_id,
                "rule_id": rule.rule_id,
                "model_area_id": rule.model_area_id,
                "element_type": rule.element_type,
            },
        )
        rationale = (
            "Approved Input maps to profile rule "
            f"{rule.rule_id} using reviewed classification/framework "
            "evidence."
            if support_level == "supported"
            else (
                "Approved Input maps provisionally to profile rule "
                f"{rule.rule_id}; explicit classification/framework "
                "evidence is incomplete."
            )
        )
        return ModelElementCandidateDraft(
            draft_key=f"element:{approved_input.approved_input_id}",
            candidate_subject_key=approved_input.stable_subject_key,
            comparison_anchor_id=(
                f"{area.comparison_anchor_prefix}:"
                f"{approved_input.stable_subject_key}"
            ),
            proposed_name=approved_input.canonical_content.title,
            description=approved_input.canonical_content.description,
            model_area=rule.model_area_id,
            element_type=rule.element_type,
            framework_assignment=area.framework_node_id,
            terminology_assignment=(
                approved_input.selected_terminology_assignment
            ),
            attributes=attributes,
            approved_input_selections=(
                ModelCandidateApprovedInputSelection(
                    approved_input_id=approved_input.approved_input_id,
                    provenance_role="direct_support",
                ),
            ),
            derivation_rationale=rationale,
            support_level=support_level,
            assumptions=(
                ()
                if support_level == "supported"
                else (
                    "Element shape uses a profile fallback because "
                    "reviewed mapping evidence is incomplete.",
                )
            ),
            missing_information=missing,
            structure_profile_conformance=conformance,
            predecessor_candidate_ids=(),
        )

    def _select_element_rule(
        self,
        approved_input: ApprovedInputManifest,
    ) -> tuple[
        ModelElementDerivationRule,
        str,
        tuple[str, ...],
        tuple[str, ...],
    ]:
        classification = approved_input.selected_classification
        framework = approved_input.selected_framework_assignment
        information_type = (
            approved_input.canonical_content.information_type
        )

        classification_matches = self._rules_matching(
            "classification_values",
            classification,
        )
        framework_matches = self._rules_matching(
            "framework_assignment_values",
            framework,
        )
        information_matches = self._rules_matching(
            "information_type_values",
            information_type,
        )

        selected = self._select_consistent_rule(
            classification_matches,
            framework_matches,
            information_matches,
            approved_input_id=approved_input.approved_input_id,
        )

        classification_exact = (
            classification is not None
            and selected in classification_matches
        )
        framework_exact = (
            framework is None or selected in framework_matches
        )

        if classification_exact and framework_exact:
            return selected, "supported", (), ()

        missing = []
        if not classification_exact:
            missing.append("explicit_profile_classification")
        if framework is None:
            missing.append("explicit_framework_assignment")
        findings = ("PROFILE_PARTIAL_ELEMENT_MAPPING",)
        return (
            selected,
            "partially_supported",
            findings,
            tuple(sorted(set(missing))),
        )

    def _rules_matching(
        self,
        field: str,
        value: str | None,
    ) -> tuple[ModelElementDerivationRule, ...]:
        if value is None:
            return ()
        return tuple(
            rule
            for rule in self.profile.element_derivation_rules
            if value in getattr(rule, field)
        )

    def _select_consistent_rule(
        self,
        classification_matches,
        framework_matches,
        information_matches,
        *,
        approved_input_id: str,
    ) -> ModelElementDerivationRule:
        # Prefer explicit reviewed classification; use framework to
        # disambiguate intentionally shared labels such as "Function".
        selected_pool = classification_matches
        if len(selected_pool) > 1 and framework_matches:
            selected_pool = tuple(
                rule
                for rule in selected_pool
                if rule in framework_matches
            )

        if not selected_pool:
            selected_pool = framework_matches
        if len(selected_pool) > 1 and information_matches:
            selected_pool = tuple(
                rule
                for rule in selected_pool
                if rule in information_matches
            )

        if not selected_pool:
            selected_pool = information_matches

        if len(selected_pool) != 1:
            if not selected_pool:
                raise ModelCandidateDerivationError(
                    "No profile-supported Element mapping exists for "
                    f"{approved_input_id}."
                )
            raise ModelCandidateDerivationError(
                "Element mapping is ambiguous for "
                f"{approved_input_id}: "
                f"{sorted(rule.rule_id for rule in selected_pool)}."
            )

        selected = selected_pool[0]

        # If an explicit framework assignment is recognized by the profile,
        # it must not contradict the selected classification rule.
        if (
            framework_matches
            and selected not in framework_matches
        ):
            raise ModelCandidateDerivationError(
                "Reviewed classification and framework assignment "
                f"conflict for {approved_input_id}."
            )
        return selected

    def _element_attributes(
        self,
        approved_input: ApprovedInputManifest,
    ) -> tuple[ModelCandidateAttribute, ...]:
        content = approved_input.canonical_content
        values = {
            "approved_input_kind": approved_input.approved_input_kind,
            "primary_text": content.primary_text,
        }
        optional = {
            "information_type": content.information_type,
            "modality": content.modality,
            "epistemic_status": content.epistemic_status,
            "source_classification": (
                approved_input.selected_classification
            ),
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

    def _derive_relationships(
        self,
        approved_inputs: tuple[ApprovedInputManifest, ...],
        element_drafts: tuple[ModelElementCandidateDraft, ...],
    ) -> tuple[ModelRelationshipCandidateDraft, ...]:
        grouped = {}
        for approved_input in approved_inputs:
            representation = (
                approved_input.selected_relationship_representation
            )
            if representation is None:
                raise ModelCandidateDerivationError(
                    "Approved relationship input has no exact relationship "
                    f"representation: {approved_input.approved_input_id}."
                )
            semantic_rule = self._relationship_rules.get(
                representation.semantic_intent
            )
            if semantic_rule is None:
                raise ModelCandidateDerivationError(
                    "Relationship semantic intent is not defined by the "
                    "Model Structure Profile: "
                    f"{representation.semantic_intent!r}."
                )
            key = self._relationship_group_key(
                representation
            )
            grouped.setdefault(
                key,
                {
                    "representation": representation,
                    "semantic_rule": semantic_rule,
                    "approved_inputs": [],
                },
            )["approved_inputs"].append(approved_input)

        endpoint_groups = {}
        for key, value in grouped.items():
            representation = value["representation"]
            endpoint_key = (
                representation.source_subject_key,
                representation.target_subject_key,
            )
            endpoint_groups.setdefault(endpoint_key, []).append(key)

        subject_index = {}
        for draft in element_drafts:
            subject_index.setdefault(
                draft.candidate_subject_key,
                [],
            ).append(draft)

        drafts = []
        for key in sorted(grouped):
            value = grouped[key]
            representation = value["representation"]
            semantic_rule = value["semantic_rule"]
            evidence = tuple(
                sorted(
                    value["approved_inputs"],
                    key=lambda item: item.approved_input_id,
                )
            )
            endpoint_key = (
                representation.source_subject_key,
                representation.target_subject_key,
            )
            alternatives = endpoint_groups[endpoint_key]
            choice_key = (
                None
                if len(alternatives) == 1
                else self._choice_key(endpoint_key)
            )
            endpoint_certainty = self._endpoint_certainty(
                representation,
                subject_index,
            )
            comparability = self._comparability(
                representation,
                semantic_rule,
                subject_index,
                endpoint_certainty,
            )
            conformance = self._relationship_conformance(
                semantic_rule,
                representation,
            )
            priority = self._priority(
                semantic_rule,
                endpoint_certainty,
                comparability,
                conformance,
            )
            drafts.append(
                ModelRelationshipCandidateDraft(
                    draft_key=(
                        "relationship:"
                        + hashlib.sha256(
                            key.encode("utf-8")
                        ).hexdigest()[:16]
                    ),
                    relationship_choice_key=choice_key,
                    source_subject_key=(
                        representation.source_subject_key
                    ),
                    target_subject_key=(
                        representation.target_subject_key
                    ),
                    relationship_family=(
                        semantic_rule.relationship_family
                    ),
                    semantic_intent=(
                        representation.semantic_intent
                    ),
                    directionality=semantic_rule.directionality,
                    approved_input_selections=tuple(
                        ModelCandidateApprovedInputSelection(
                            approved_input_id=item.approved_input_id,
                            provenance_role="explicit_relationship",
                        )
                        for item in evidence
                    ),
                    derivation_rationale=(
                        "Explicit Approved Input relationship preserved "
                        "without changing engineering semantic intent."
                    ),
                    supporting_evidence=tuple(
                        item.approved_input_id for item in evidence
                    ),
                    assumptions=(),
                    missing_information=(
                        ()
                        if endpoint_certainty == "resolved"
                        else (
                            "exact_relationship_endpoint_resolution",
                        )
                    ),
                    priority_assessment=priority,
                    comparability_assessment=comparability,
                    structure_profile_conformance=conformance,
                    upstream_relationship_representation=representation,
                    predecessor_candidate_ids=(),
                )
            )

        return tuple(sorted(drafts, key=lambda item: item.draft_key))

    def _relationship_group_key(
        self,
        representation: ApprovedInputRelationshipRepresentation,
    ) -> str:
        payload = {
            "source_subject_key": representation.source_subject_key,
            "target_subject_key": representation.target_subject_key,
            "semantic_intent": representation.semantic_intent,
            "sysml_v2_construct": representation.sysml_v2_construct,
            "construct_properties": [
                {"name": item.name, "value": item.value}
                for item in representation.construct_properties
            ],
            "target_notation_profile_id": (
                representation.target_notation_profile_id
            ),
            "target_notation_profile_version": (
                representation.target_notation_profile_version
            ),
            "textual_notation_preview": (
                representation.textual_notation_preview
            ),
            "profile_validation_status": (
                representation.profile_validation_status
            ),
            "profile_validation_fingerprint": (
                representation.profile_validation_fingerprint
            ),
        }
        return json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )

    def _choice_key(
        self,
        endpoint_key: tuple[str, str],
    ) -> str:
        value = "|".join(endpoint_key)
        return (
            "choice:"
            + hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]
        )

    def _endpoint_certainty(
        self,
        representation: ApprovedInputRelationshipRepresentation,
        subject_index,
    ) -> str:
        counts = (
            len(subject_index.get(
                representation.source_subject_key,
                (),
            )),
            len(subject_index.get(
                representation.target_subject_key,
                (),
            )),
        )
        if counts == (1, 1):
            return "resolved"
        if 0 in counts:
            return "unresolved"
        return "ambiguous"

    def _comparability(
        self,
        representation: ApprovedInputRelationshipRepresentation,
        semantic_rule: ModelRelationshipSemanticRule,
        subject_index,
        endpoint_certainty: str,
    ) -> StructuralComparabilityAssessment:
        anchor_ids = []
        for subject_key in (
            representation.source_subject_key,
            representation.target_subject_key,
        ):
            matches = subject_index.get(subject_key, ())
            if len(matches) == 1:
                anchor = matches[0].comparison_anchor_id
                if anchor is not None:
                    anchor_ids.append(anchor)

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
            ()
            if semantic_rule.deviation_id is None
            else (semantic_rule.deviation_id,)
        )
        return StructuralComparabilityAssessment(
            impact=impact,
            comparison_anchor_ids=tuple(sorted(set(anchor_ids))),
            canonical_pattern_match=canonical_match,
            deviation_ids=deviations,
            rationale=(
                "Relationship uses the profile-defined semantic rule; "
                f"endpoint certainty is {endpoint_certainty}."
            ),
        )

    def _relationship_conformance(
        self,
        semantic_rule: ModelRelationshipSemanticRule,
        representation: ApprovedInputRelationshipRepresentation,
    ) -> StructuralProfileConformance:
        if semantic_rule.canonical:
            status = "conformant"
            findings = ()
        else:
            status = "exception_required"
            findings = (
                semantic_rule.deviation_id,
            )
        return self._conformance(
            status=status,
            finding_ids=tuple(
                item for item in findings if item is not None
            ),
            evidence={
                "semantic_intent": representation.semantic_intent,
                "relationship_family": semantic_rule.relationship_family,
                "directionality": semantic_rule.directionality,
                "canonical": semantic_rule.canonical,
            },
        )

    def _priority(
        self,
        semantic_rule: ModelRelationshipSemanticRule,
        endpoint_certainty: str,
        comparability: StructuralComparabilityAssessment,
        conformance: StructuralProfileConformance,
    ) -> RelationshipPriorityAssessment:
        if not semantic_rule.canonical:
            priority_class = "exception_candidate"
        elif endpoint_certainty != "resolved":
            priority_class = "supported_alternative"
        else:
            priority_class = "preferred"

        result_by_criterion = {
            "evidence_directness": (
                "explicit",
                "Relationship is directly represented by Approved Input.",
            ),
            "semantic_fit": (
                "exact_profile_match",
                "Approved semantic intent has an exact profile rule.",
            ),
            "endpoint_certainty": (
                endpoint_certainty,
                "Endpoint certainty is calculated from Element drafts.",
            ),
            "structural_profile_preference": (
                "canonical"
                if semantic_rule.canonical
                else "noncanonical",
                "Preference follows the versioned structure profile.",
            ),
            "structural_comparability_impact": (
                comparability.impact,
                "Impact follows endpoint certainty and canonical profile use.",
            ),
            "assumption_burden": (
                "none",
                "No relationship semantics were inferred beyond Approved Input.",
            ),
            "conformance": (
                conformance.status,
                "Conformance is bound to the exact profile semantic rule.",
            ),
        }
        criteria = tuple(
            RelationshipPriorityCriterionResult(
                criterion=criterion,
                result=result_by_criterion[criterion][0],
                rationale=result_by_criterion[criterion][1],
            )
            for criterion in RELATIONSHIP_PRIORITY_CRITERIA
        )
        return RelationshipPriorityAssessment(
            priority_class=priority_class,
            criterion_results=criteria,
            rationale=(
                "Advisory priority only; Human Review remains the "
                "authorization boundary."
            ),
        )

    def _conformance(
        self,
        *,
        status: str,
        finding_ids: tuple[str, ...],
        evidence: dict[str, object],
    ) -> StructuralProfileConformance:
        payload = {
            "profile_id": self.profile.profile_id,
            "profile_version": self.profile.profile_version,
            "profile_fingerprint": self.profile.profile_fingerprint,
            "status": status,
            "finding_ids": sorted(finding_ids),
            "evidence": evidence,
        }
        canonical = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        return StructuralProfileConformance(
            status=status,
            finding_ids=tuple(sorted(finding_ids)),
            conformance_fingerprint=hashlib.sha256(
                canonical.encode("utf-8")
            ).hexdigest(),
        )
