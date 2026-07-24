"""Validate terminology-mapping candidates against semantic authorities.

This module performs deterministic, read-only reference validation. It does
not accept a mapping candidate, mutate a Project Glossary, alter Turing Core,
or infer additional ontology relations.
"""

from __future__ import annotations

from dataclasses import dataclass

from modules.project_glossary.normalization import (
    normalize_label_for_comparison,
)
from modules.project_glossary.types import (
    ProjectConcept,
    ProjectConceptRevision,
    ProjectGlossary,
)
from modules.semantics.types import (
    OntologyRegistry,
    ReferenceConcept,
    ReferenceConceptIndex,
    TuringCoreConcept,
    TuringCoreVocabulary,
)
from modules.terminology_mapping.errors import (
    TerminologyMappingReferenceError,
)
from modules.terminology_mapping.types import (
    TerminologyMappingBasis,
    TerminologyMappingCandidate,
    TerminologyMappingIssue,
    TerminologyMappingProposal,
    TerminologyMappingTarget,
)


@dataclass(frozen=True, slots=True)
class TerminologyMappingReferenceValidationResult:
    """Read-only validation result for one persisted mapping candidate."""

    project_id: str
    terminology_mapping_candidate_id: str
    checked_proposal_count: int
    references_valid: bool
    issues: tuple[TerminologyMappingIssue, ...]


def validate_terminology_mapping_references(
    candidate: TerminologyMappingCandidate,
    *,
    project_glossary: ProjectGlossary,
    turing_core_vocabulary: TuringCoreVocabulary,
    ontology_registry: OntologyRegistry,
    reference_concept_index: ReferenceConceptIndex,
) -> TerminologyMappingReferenceValidationResult:
    """Validate all versioned targets and bases without changing authority.

    The candidate and all supplied semantic resources are treated as immutable
    snapshots. Any stale, missing, non-accepted, ambiguous, or inconsistent
    reference produces a blocking issue rather than an inferred correction.
    """

    _require_supported_inputs(
        candidate,
        project_glossary,
        turing_core_vocabulary,
        ontology_registry,
        reference_concept_index,
    )

    issues: list[TerminologyMappingIssue] = []

    _validate_context_versions(
        candidate,
        project_glossary,
        turing_core_vocabulary,
        ontology_registry,
        reference_concept_index,
        issues,
    )

    project_concepts = {
        concept.project_concept_id: concept
        for concept in project_glossary.concepts
    }
    turing_concepts = {
        concept.concept_id: concept
        for concept in turing_core_vocabulary.concepts
    }
    reference_concepts = {
        concept.iri: concept
        for concept in reference_concept_index.concepts
    }
    reference_system_versions = {
        system.reference_system_id: system.version
        for system in ontology_registry.reference_systems
    }

    for proposal_index, proposal in enumerate(
        candidate.proposals,
        start=1,
    ):
        if proposal.target is None:
            continue

        target = proposal.target
        if target.target_kind == "project_concept":
            _validate_project_target(
                candidate,
                proposal,
                proposal_index,
                target,
                project_glossary,
                project_concepts,
                issues,
            )
        elif target.target_kind == "turing_core_concept":
            _validate_turing_target(
                candidate,
                proposal,
                proposal_index,
                target,
                turing_core_vocabulary,
                turing_concepts,
                issues,
            )
        elif target.target_kind == "external_reference_concept":
            _validate_external_target(
                candidate,
                proposal,
                proposal_index,
                target,
                reference_concept_index,
                reference_concepts,
                reference_system_versions,
                issues,
            )
        else:
            _issue(
                issues,
                candidate,
                "unsupported_target_kind",
                (
                    f"Proposal {proposal_index} has unsupported target "
                    f"kind {target.target_kind!r}."
                ),
            )

    ordered_issues = tuple(
        sorted(
            issues,
            key=lambda issue: (
                issue.issue_level,
                issue.code,
                issue.message,
            ),
        )
    )
    return TerminologyMappingReferenceValidationResult(
        project_id=candidate.project_id,
        terminology_mapping_candidate_id=(
            candidate.terminology_mapping_candidate_id
        ),
        checked_proposal_count=len(candidate.proposals),
        references_valid=not any(
            issue.issue_level == "blocking"
            for issue in ordered_issues
        ),
        issues=ordered_issues,
    )


def _require_supported_inputs(
    candidate: object,
    project_glossary: object,
    turing_core_vocabulary: object,
    ontology_registry: object,
    reference_concept_index: object,
) -> None:
    expected = (
        (
            candidate,
            TerminologyMappingCandidate,
            "candidate",
        ),
        (
            project_glossary,
            ProjectGlossary,
            "project_glossary",
        ),
        (
            turing_core_vocabulary,
            TuringCoreVocabulary,
            "turing_core_vocabulary",
        ),
        (
            ontology_registry,
            OntologyRegistry,
            "ontology_registry",
        ),
        (
            reference_concept_index,
            ReferenceConceptIndex,
            "reference_concept_index",
        ),
    )
    for value, value_type, label in expected:
        if not isinstance(value, value_type):
            raise TerminologyMappingReferenceError(
                f"{label} must be a {value_type.__name__}."
            )


def _validate_context_versions(
    candidate: TerminologyMappingCandidate,
    glossary: ProjectGlossary,
    vocabulary: TuringCoreVocabulary,
    registry: OntologyRegistry,
    index: ReferenceConceptIndex,
    issues: list[TerminologyMappingIssue],
) -> None:
    if candidate.project_id != glossary.project_id:
        _issue(
            issues,
            candidate,
            "project_glossary_project_mismatch",
            (
                f"Candidate project {candidate.project_id!r} does not "
                f"match Project Glossary project {glossary.project_id!r}."
            ),
        )

    expected_versions: tuple[
        tuple[str, object, object],
        ...
    ] = (
        (
            "project_glossary_revision",
            candidate.project_glossary_revision,
            glossary.glossary_revision,
        ),
        (
            "turing_core_version",
            candidate.turing_core_version,
            vocabulary.vocabulary_version,
        ),
        (
            "ontology_registry_version",
            candidate.ontology_registry_version,
            registry.registry_version,
        ),
        (
            "reference_concept_index_version",
            candidate.reference_concept_index_version,
            index.index_version,
        ),
    )
    for field_name, candidate_value, current_value in expected_versions:
        if candidate_value != current_value:
            _issue(
                issues,
                candidate,
                f"{field_name}_mismatch",
                (
                    f"Candidate {field_name} {candidate_value!r} does "
                    f"not match supplied authority {current_value!r}."
                ),
            )

    if index.registry_id != registry.registry_id:
        _issue(
            issues,
            candidate,
            "reference_index_registry_id_mismatch",
            (
                f"Reference Concept Index registry ID "
                f"{index.registry_id!r} does not match Ontology Registry "
                f"ID {registry.registry_id!r}."
            ),
        )
    if index.registry_version != registry.registry_version:
        _issue(
            issues,
            candidate,
            "reference_index_registry_version_mismatch",
            (
                f"Reference Concept Index registry version "
                f"{index.registry_version!r} does not match Ontology "
                f"Registry version {registry.registry_version!r}."
            ),
        )
    if (
        vocabulary.external_mapping_policy.registry_id
        != registry.registry_id
    ):
        _issue(
            issues,
            candidate,
            "turing_core_registry_id_mismatch",
            (
                "Turing Core external mapping policy references registry "
                f"{vocabulary.external_mapping_policy.registry_id!r}, "
                f"not {registry.registry_id!r}."
            ),
        )


def _validate_project_target(
    candidate: TerminologyMappingCandidate,
    proposal: TerminologyMappingProposal,
    proposal_index: int,
    target: TerminologyMappingTarget,
    glossary: ProjectGlossary,
    project_concepts: dict[str, ProjectConcept],
    issues: list[TerminologyMappingIssue],
) -> None:
    concept_id = target.project_concept_id
    revision_number = target.project_concept_revision
    concept = project_concepts.get(concept_id or "")

    if concept is None:
        _issue(
            issues,
            candidate,
            "project_concept_not_found",
            (
                f"Proposal {proposal_index} references unknown Project "
                f"Concept {concept_id!r}."
            ),
        )
        return

    revision = _revision_by_number(
        concept,
        revision_number,
    )
    if revision is None:
        _issue(
            issues,
            candidate,
            "project_concept_revision_not_found",
            (
                f"Proposal {proposal_index} references unknown revision "
                f"{revision_number!r} of Project Concept {concept_id!r}."
            ),
        )
        return

    if revision.lifecycle_status != "accepted":
        _issue(
            issues,
            candidate,
            "project_concept_revision_not_accepted",
            (
                f"Proposal {proposal_index} references Project Concept "
                f"{concept_id!r} revision {revision_number}, whose "
                f"lifecycle status is {revision.lifecycle_status!r}."
            ),
        )

    expected_reference_id = (
        f"{candidate.project_id}/{concept_id}/"
        f"revision/{revision_number}"
    )
    _require_basis(
        candidate,
        proposal,
        proposal_index,
        basis_type="accepted_project_glossary",
        reference_id=expected_reference_id,
        reference_version=str(glossary.glossary_revision),
        issues=issues,
    )
    _validate_project_label_context(
        candidate,
        proposal_index,
        target,
        glossary,
        concept,
        revision,
        issues,
    )


def _validate_project_label_context(
    candidate: TerminologyMappingCandidate,
    proposal_index: int,
    target: TerminologyMappingTarget,
    glossary: ProjectGlossary,
    selected_concept: ProjectConcept,
    selected_revision: ProjectConceptRevision,
    issues: list[TerminologyMappingIssue],
) -> None:
    occurrence_key = normalize_label_for_comparison(
        candidate.occurrence.term_text,
        "candidate.occurrence.term_text",
    )
    selected_labels = _revision_label_keys(
        selected_revision,
        glossary.default_language,
    )

    if occurrence_key not in selected_labels:
        _issue(
            issues,
            candidate,
            "project_concept_label_not_matched",
            (
                f"Proposal {proposal_index} term "
                f"{candidate.occurrence.term_text!r} does not exactly "
                f"match an accepted {glossary.default_language!r} label "
                f"of Project Concept "
                f"{selected_concept.project_concept_id!r}. Semantic "
                "review is required; no synonym is inferred."
            ),
            issue_level="warning",
        )

    matching_concepts: set[str] = set()
    for concept in glossary.concepts:
        revision = _effective_accepted_revision(concept)
        if revision is None:
            continue
        if occurrence_key in _revision_label_keys(
            revision,
            glossary.default_language,
        ):
            matching_concepts.add(concept.project_concept_id)

    matching_groups = tuple(
        group
        for group in glossary.ambiguity_groups
        if group.language == glossary.default_language
        and normalize_label_for_comparison(
            group.label,
            "ambiguity_group.label",
        )
        == occurrence_key
    )
    if len(matching_concepts) > 1 or matching_groups:
        details = sorted(
            matching_concepts
            | {
                concept_id
                for group in matching_groups
                for concept_id in group.candidate_project_concept_ids
            }
        )
        _issue(
            issues,
            candidate,
            "ambiguous_project_glossary_label",
            (
                f"Proposal {proposal_index} term "
                f"{candidate.occurrence.term_text!r} is ambiguous across "
                f"Project Concepts {details!r}; it must not be "
                "auto-resolved."
            ),
        )
    elif (
        matching_concepts
        and selected_concept.project_concept_id
        not in matching_concepts
    ):
        _issue(
            issues,
            candidate,
            "project_glossary_label_conflict",
            (
                f"Proposal {proposal_index} selects Project Concept "
                f"{selected_concept.project_concept_id!r}, but the exact "
                f"accepted label points to "
                f"{sorted(matching_concepts)!r}."
            ),
        )

    preferred_labels = {
        label.text
        for label in selected_revision.preferred_labels
    }
    if target.display_label not in preferred_labels:
        _issue(
            issues,
            candidate,
            "project_target_display_label_differs",
            (
                f"Proposal {proposal_index} display label "
                f"{target.display_label!r} is not a preferred label of "
                f"Project Concept {selected_concept.project_concept_id!r}."
            ),
            issue_level="warning",
        )


def _validate_turing_target(
    candidate: TerminologyMappingCandidate,
    proposal: TerminologyMappingProposal,
    proposal_index: int,
    target: TerminologyMappingTarget,
    vocabulary: TuringCoreVocabulary,
    concepts: dict[str, TuringCoreConcept],
    issues: list[TerminologyMappingIssue],
) -> None:
    concept_id = target.turing_core_concept_id
    concept = concepts.get(concept_id or "")
    if concept is None:
        _issue(
            issues,
            candidate,
            "turing_core_concept_not_found",
            (
                f"Proposal {proposal_index} references unknown Turing "
                f"Core Concept {concept_id!r}."
            ),
        )
        return
    if concept.status != "active":
        _issue(
            issues,
            candidate,
            "turing_core_concept_not_active",
            (
                f"Proposal {proposal_index} references Turing Core "
                f"Concept {concept_id!r} with status {concept.status!r}."
            ),
        )
    _require_basis(
        candidate,
        proposal,
        proposal_index,
        basis_type="turing_core",
        reference_id=concept_id or "",
        reference_version=vocabulary.vocabulary_version,
        issues=issues,
    )
    labels = {
        concept.preferred_label,
        *concept.alternative_labels,
    }
    if target.display_label not in labels:
        _issue(
            issues,
            candidate,
            "turing_core_display_label_differs",
            (
                f"Proposal {proposal_index} display label "
                f"{target.display_label!r} is not a curated label of "
                f"Turing Core Concept {concept_id!r}."
            ),
            issue_level="warning",
        )


def _validate_external_target(
    candidate: TerminologyMappingCandidate,
    proposal: TerminologyMappingProposal,
    proposal_index: int,
    target: TerminologyMappingTarget,
    index: ReferenceConceptIndex,
    concepts: dict[str, ReferenceConcept],
    reference_system_versions: dict[str, str],
    issues: list[TerminologyMappingIssue],
) -> None:
    iri = target.reference_concept_iri
    concept = concepts.get(iri or "")
    if concept is None:
        _issue(
            issues,
            candidate,
            "reference_concept_not_found",
            (
                f"Proposal {proposal_index} references unknown external "
                f"concept IRI {iri!r}."
            ),
        )
        return

    if concept.reference_system_id != target.reference_system_id:
        _issue(
            issues,
            candidate,
            "reference_concept_system_mismatch",
            (
                f"Proposal {proposal_index} declares reference system "
                f"{target.reference_system_id!r}, but concept {iri!r} "
                f"belongs to {concept.reference_system_id!r}."
            ),
        )
    registered_version = reference_system_versions.get(
        target.reference_system_id or ""
    )
    if registered_version is None:
        _issue(
            issues,
            candidate,
            "reference_system_not_registered",
            (
                f"Proposal {proposal_index} references unregistered "
                f"system {target.reference_system_id!r}."
            ),
        )
    elif target.reference_system_version != registered_version:
        _issue(
            issues,
            candidate,
            "reference_system_version_mismatch",
            (
                f"Proposal {proposal_index} declares reference-system "
                f"version {target.reference_system_version!r}, but the "
                f"pinned registry version is {registered_version!r}."
            ),
        )
    if (
        concept.version != target.reference_system_version
        or (
            registered_version is not None
            and concept.version != registered_version
        )
    ):
        _issue(
            issues,
            candidate,
            "reference_concept_version_mismatch",
            (
                f"Proposal {proposal_index} target version does not "
                f"match indexed concept version {concept.version!r}."
            ),
        )
    _require_basis(
        candidate,
        proposal,
        proposal_index,
        basis_type="reference_concept_index",
        reference_id=iri or "",
        reference_version=index.index_version,
        issues=issues,
    )
    labels = {
        label.text
        for label in (
            concept.preferred_labels
            + concept.alternative_labels
        )
    }
    if labels and target.display_label not in labels:
        _issue(
            issues,
            candidate,
            "reference_concept_display_label_differs",
            (
                f"Proposal {proposal_index} display label "
                f"{target.display_label!r} is not an indexed label of "
                f"external concept {iri!r}."
            ),
            issue_level="warning",
        )


def _require_basis(
    candidate: TerminologyMappingCandidate,
    proposal: TerminologyMappingProposal,
    proposal_index: int,
    *,
    basis_type: str,
    reference_id: str,
    reference_version: str,
    issues: list[TerminologyMappingIssue],
) -> None:
    matching_type = tuple(
        basis
        for basis in proposal.mapping_bases
        if basis.basis_type == basis_type
    )
    if not matching_type:
        _issue(
            issues,
            candidate,
            "authoritative_mapping_basis_missing",
            (
                f"Proposal {proposal_index} has no {basis_type!r} basis "
                f"for target {reference_id!r}."
            ),
        )
        return

    if not any(
        _basis_matches(
            basis,
            reference_id,
            reference_version,
        )
        for basis in matching_type
    ):
        supplied = sorted(
            (
                basis.reference_id,
                basis.reference_version,
            )
            for basis in matching_type
        )
        _issue(
            issues,
            candidate,
            "authoritative_mapping_basis_mismatch",
            (
                f"Proposal {proposal_index} requires {basis_type!r} "
                f"basis ({reference_id!r}, {reference_version!r}), but "
                f"supplies {supplied!r}."
            ),
        )


def _basis_matches(
    basis: TerminologyMappingBasis,
    reference_id: str,
    reference_version: str,
) -> bool:
    return (
        basis.reference_id == reference_id
        and basis.reference_version == reference_version
    )


def _revision_by_number(
    concept: ProjectConcept,
    revision_number: int | None,
) -> ProjectConceptRevision | None:
    return next(
        (
            revision
            for revision in concept.revisions
            if revision.revision == revision_number
        ),
        None,
    )


def _effective_accepted_revision(
    concept: ProjectConcept,
) -> ProjectConceptRevision | None:
    accepted = tuple(
        revision
        for revision in concept.revisions
        if revision.lifecycle_status == "accepted"
    )
    if not accepted:
        return None
    return max(
        accepted,
        key=lambda revision: revision.revision,
    )


def _revision_label_keys(
    revision: ProjectConceptRevision,
    language: str,
) -> frozenset[str]:
    return frozenset(
        normalize_label_for_comparison(
            label.text,
            "Project Concept label",
        )
        for label in (
            revision.preferred_labels
            + revision.alternative_labels
        )
        if label.language == language
    )


def _issue(
    issues: list[TerminologyMappingIssue],
    candidate: TerminologyMappingCandidate,
    code: str,
    message: str,
    *,
    issue_level: str = "blocking",
) -> None:
    issues.append(
        TerminologyMappingIssue(
            project_id=candidate.project_id,
            code=code,
            message=message,
            issue_level=issue_level,
            information_unit_id=candidate.information_unit_id,
            terminology_mapping_candidate_id=(
                candidate.terminology_mapping_candidate_id
            ),
        )
    )
