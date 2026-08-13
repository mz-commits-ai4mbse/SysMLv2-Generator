"""Shared deterministic target-projection resolution for Phase H."""

from __future__ import annotations

from dataclasses import dataclass

from modules.approved_input.types import (
    ApprovedInputManifest,
    ApprovedInputRelationshipRepresentation,
)

from .errors import ModelCandidateDerivationError
from .structure_profile import model_structure_profile_reference
from .types import (
    MODEL_CANDIDATE_PROJECTION_DISPOSITIONS,
    ModelCandidateProjectionCoverage,
    ModelCandidateProjectionDisposition,
    ModelElementDerivationRule,
    ModelRelationshipSemanticRule,
    ModelStructureProfile,
)


@dataclass(frozen=True, slots=True)
class _ElementProjectionResolution:
    disposition: ModelCandidateProjectionDisposition
    selected_rule: ModelElementDerivationRule | None
    classification_rule_ids: tuple[str, ...]
    framework_rule_ids: tuple[str, ...]
    information_type_rule_ids: tuple[str, ...]


class ProfileProjectionResolver:
    """Resolve Approved Inputs against one pinned Model Structure Profile."""

    def __init__(self, *, profile: ModelStructureProfile) -> None:
        self.profile = profile
        self._relationship_rules = {
            item.semantic_intent: item
            for item in profile.relationship_semantics
        }

    def assess_snapshot(
        self,
        *,
        project_id: str,
        approved_inputs: tuple[ApprovedInputManifest, ...],
    ) -> ModelCandidateProjectionCoverage:
        """Return one explicit disposition for every supplied Approved Input."""

        if not isinstance(approved_inputs, tuple):
            raise ModelCandidateDerivationError(
                "Projection coverage requires Approved Inputs as a tuple."
            )
        if not all(
            isinstance(item, ApprovedInputManifest)
            for item in approved_inputs
        ):
            raise ModelCandidateDerivationError(
                "Projection coverage received an invalid Approved Input."
            )

        ordered = tuple(
            sorted(
                approved_inputs,
                key=lambda item: item.approved_input_id,
            )
        )
        ids = tuple(item.approved_input_id for item in ordered)
        if len(ids) != len(set(ids)):
            raise ModelCandidateDerivationError(
                "Projection coverage cannot contain duplicate Approved Input IDs."
            )
        for item in ordered:
            if item.project_id != project_id:
                raise ModelCandidateDerivationError(
                    "Projection coverage cannot cross project boundaries."
                )

        entries = tuple(self.resolve(item) for item in ordered)
        coverage = ModelCandidateProjectionCoverage(
            project_id=project_id,
            model_structure_profile_reference=(
                model_structure_profile_reference(self.profile)
            ),
            entries=entries,
        )
        self._validate_complete_coverage(coverage, expected_ids=ids)
        return coverage

    def resolve(
        self,
        approved_input: ApprovedInputManifest,
    ) -> ModelCandidateProjectionDisposition:
        """Resolve one Approved Input without raising for mapping limitations."""

        if approved_input.approved_input_kind == "element_statement":
            return self.resolve_element(approved_input).disposition

        if approved_input.approved_input_kind == "relationship_statement":
            return self._resolve_relationship(approved_input)[0]

        if approved_input.approved_input_kind == "human_clarification":
            return ModelCandidateProjectionDisposition(
                approved_input_id=approved_input.approved_input_id,
                approved_input_kind=approved_input.approved_input_kind,
                disposition="intentionally_not_projected",
                reason_code="context_only_human_clarification",
                selected_rule_id=None,
                candidate_rule_ids=(),
                rationale=(
                    "Human clarification remains reviewed context and is "
                    "intentionally not auto-materialized as a Model Candidate."
                ),
            )

        return ModelCandidateProjectionDisposition(
            approved_input_id=approved_input.approved_input_id,
            approved_input_kind=approved_input.approved_input_kind,
            disposition="unmapped",
            reason_code="unsupported_approved_input_kind",
            selected_rule_id=None,
            candidate_rule_ids=(),
            rationale=(
                "The Approved Input kind is not supported by the selected "
                "target-projection strategy."
            ),
        )

    def resolve_element(
        self,
        approved_input: ApprovedInputManifest,
    ) -> _ElementProjectionResolution:
        """Resolve one element statement and retain exact evidence matches."""

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

        classification_rule_ids = self._rule_ids(classification_matches)
        framework_rule_ids = self._rule_ids(framework_matches)
        information_rule_ids = self._rule_ids(information_matches)

        if not selected_pool:
            disposition = ModelCandidateProjectionDisposition(
                approved_input_id=approved_input.approved_input_id,
                approved_input_kind=approved_input.approved_input_kind,
                disposition="unmapped",
                reason_code="no_profile_element_mapping",
                selected_rule_id=None,
                candidate_rule_ids=(),
                rationale=(
                    "No Model Structure Profile element rule matches the "
                    "reviewed classification, framework assignment or "
                    "information type."
                ),
            )
            return _ElementProjectionResolution(
                disposition=disposition,
                selected_rule=None,
                classification_rule_ids=classification_rule_ids,
                framework_rule_ids=framework_rule_ids,
                information_type_rule_ids=information_rule_ids,
            )

        if len(selected_pool) != 1:
            candidate_rule_ids = self._rule_ids(selected_pool)
            disposition = ModelCandidateProjectionDisposition(
                approved_input_id=approved_input.approved_input_id,
                approved_input_kind=approved_input.approved_input_kind,
                disposition="ambiguous",
                reason_code="ambiguous_profile_element_mapping",
                selected_rule_id=None,
                candidate_rule_ids=candidate_rule_ids,
                rationale=(
                    "More than one Model Structure Profile element rule "
                    "remains applicable after deterministic disambiguation."
                ),
            )
            return _ElementProjectionResolution(
                disposition=disposition,
                selected_rule=None,
                classification_rule_ids=classification_rule_ids,
                framework_rule_ids=framework_rule_ids,
                information_type_rule_ids=information_rule_ids,
            )

        selected = selected_pool[0]
        if framework_matches and selected not in framework_matches:
            candidate_rule_ids = tuple(
                sorted(
                    {
                        selected.rule_id,
                        *(item.rule_id for item in framework_matches),
                    }
                )
            )
            disposition = ModelCandidateProjectionDisposition(
                approved_input_id=approved_input.approved_input_id,
                approved_input_kind=approved_input.approved_input_kind,
                disposition="ambiguous",
                reason_code="conflicting_profile_element_mapping",
                selected_rule_id=None,
                candidate_rule_ids=candidate_rule_ids,
                rationale=(
                    "Reviewed classification and framework assignment point "
                    "to conflicting Model Structure Profile rules."
                ),
            )
            return _ElementProjectionResolution(
                disposition=disposition,
                selected_rule=None,
                classification_rule_ids=classification_rule_ids,
                framework_rule_ids=framework_rule_ids,
                information_type_rule_ids=information_rule_ids,
            )

        disposition = ModelCandidateProjectionDisposition(
            approved_input_id=approved_input.approved_input_id,
            approved_input_kind=approved_input.approved_input_kind,
            disposition="mapped",
            reason_code="profile_element_mapping",
            selected_rule_id=selected.rule_id,
            candidate_rule_ids=(selected.rule_id,),
            rationale=(
                "Approved Input resolves to exactly one Model Structure "
                f"Profile rule: {selected.rule_id}."
            ),
        )
        return _ElementProjectionResolution(
            disposition=disposition,
            selected_rule=selected,
            classification_rule_ids=classification_rule_ids,
            framework_rule_ids=framework_rule_ids,
            information_type_rule_ids=information_rule_ids,
        )

    def require_element_mapping(
        self,
        approved_input: ApprovedInputManifest,
    ) -> _ElementProjectionResolution:
        """Return the exact element resolution or fail as strict mode."""

        resolution = self.resolve_element(approved_input)
        if (
            resolution.disposition.disposition != "mapped"
            or resolution.selected_rule is None
        ):
            self._raise_for_strict_entry(resolution.disposition)
        return resolution

    def require_relationship_mapping(
        self,
        approved_input: ApprovedInputManifest,
    ) -> tuple[
        ApprovedInputRelationshipRepresentation,
        ModelRelationshipSemanticRule,
    ]:
        """Return exact relationship mapping or fail as strict mode."""

        disposition, representation, semantic_rule = (
            self._resolve_relationship(approved_input)
        )
        if (
            disposition.disposition != "mapped"
            or representation is None
            or semantic_rule is None
        ):
            self._raise_for_strict_entry(disposition)
        return representation, semantic_rule

    def require_strict_coverage(
        self,
        coverage: ModelCandidateProjectionCoverage,
    ) -> None:
        """Fail when strict projection contains ambiguous/unmapped inputs."""

        for entry in coverage.entries:
            if entry.disposition in {
                "mapped",
                "intentionally_not_projected",
            }:
                continue
            self._raise_for_strict_entry(entry)

    def _resolve_relationship(
        self,
        approved_input: ApprovedInputManifest,
    ) -> tuple[
        ModelCandidateProjectionDisposition,
        ApprovedInputRelationshipRepresentation | None,
        ModelRelationshipSemanticRule | None,
    ]:
        representation = (
            approved_input.selected_relationship_representation
        )
        if representation is None:
            raise ModelCandidateDerivationError(
                "Approved relationship input violates the Approved Input "
                "contract: relationship_statement requires an exact "
                "selected_relationship_representation."
            )

        semantic_rule = self._relationship_rules.get(
            representation.semantic_intent
        )
        if semantic_rule is None:
            disposition = ModelCandidateProjectionDisposition(
                approved_input_id=approved_input.approved_input_id,
                approved_input_kind=approved_input.approved_input_kind,
                disposition="unmapped",
                reason_code="unsupported_relationship_semantic",
                selected_rule_id=None,
                candidate_rule_ids=(),
                rationale=(
                    "The reviewed relationship semantic intent is not "
                    "defined by the selected Model Structure Profile."
                ),
            )
            return disposition, representation, None

        rule_id = f"relationship:{semantic_rule.semantic_intent}"
        disposition = ModelCandidateProjectionDisposition(
            approved_input_id=approved_input.approved_input_id,
            approved_input_kind=approved_input.approved_input_kind,
            disposition="mapped",
            reason_code="profile_relationship_mapping",
            selected_rule_id=rule_id,
            candidate_rule_ids=(rule_id,),
            rationale=(
                "Approved relationship semantic intent has an exact "
                "Model Structure Profile rule."
            ),
        )
        return disposition, representation, semantic_rule

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

    def _rule_ids(
        self,
        rules: tuple[ModelElementDerivationRule, ...],
    ) -> tuple[str, ...]:
        return tuple(sorted(item.rule_id for item in rules))

    def _validate_complete_coverage(
        self,
        coverage: ModelCandidateProjectionCoverage,
        *,
        expected_ids: tuple[str, ...],
    ) -> None:
        actual_ids = tuple(
            item.approved_input_id for item in coverage.entries
        )
        if actual_ids != expected_ids:
            raise ModelCandidateDerivationError(
                "Projection coverage does not account for the complete "
                "Approved Input snapshot."
            )
        if any(
            item.disposition
            not in MODEL_CANDIDATE_PROJECTION_DISPOSITIONS
            for item in coverage.entries
        ):
            raise ModelCandidateDerivationError(
                "Projection coverage contains an invalid disposition."
            )
        if not coverage.is_complete:
            raise ModelCandidateDerivationError(
                "Projection coverage disposition counts are incomplete."
            )

    def _raise_for_strict_entry(
        self,
        entry: ModelCandidateProjectionDisposition,
    ) -> None:
        if entry.reason_code == "no_profile_element_mapping":
            raise ModelCandidateDerivationError(
                "No profile-supported Element mapping exists for "
                f"{entry.approved_input_id}."
            )

        if entry.reason_code == "ambiguous_profile_element_mapping":
            raise ModelCandidateDerivationError(
                "Element mapping is ambiguous for "
                f"{entry.approved_input_id}: "
                f"{list(entry.candidate_rule_ids)}."
            )

        if entry.reason_code == "conflicting_profile_element_mapping":
            raise ModelCandidateDerivationError(
                "Reviewed classification and framework assignment "
                f"conflict for {entry.approved_input_id}."
            )

        if entry.reason_code == "missing_relationship_representation":
            raise ModelCandidateDerivationError(
                "Approved relationship input has no exact relationship "
                f"representation: {entry.approved_input_id}."
            )

        if entry.reason_code == "unsupported_relationship_semantic":
            raise ModelCandidateDerivationError(
                "Relationship semantic intent is not defined by the "
                "Model Structure Profile for "
                f"{entry.approved_input_id}."
            )

        raise ModelCandidateDerivationError(
            "Strict target projection cannot resolve "
            f"{entry.approved_input_id}: {entry.reason_code}."
        )
