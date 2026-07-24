"""Tests for read-only terminology-mapping reference validation."""

from __future__ import annotations

import builtins
from dataclasses import FrozenInstanceError, replace

import pytest

from modules.project_glossary.types import (
    AmbiguityGroup,
    LocalizedGlossaryText,
    ProjectConcept,
    ProjectConceptRevision,
    ProjectGlossary,
)
from modules.semantics.types import (
    LocalizedText,
    OntologyRegistry,
    ReferenceConcept,
    ReferenceConceptIndex,
    TuringCoreConcept,
    TuringCoreVocabulary,
)
from modules.terminology_mapping.errors import (
    TerminologyMappingReferenceError,
)
from modules.terminology_mapping.reference_validation import (
    TerminologyMappingReferenceValidationResult,
    validate_terminology_mapping_references,
)
from modules.terminology_mapping.types import (
    TerminologyMappingBasis,
    TerminologyMappingCandidate,
    TerminologyMappingProposal,
    TerminologyMappingTarget,
    TerminologyOccurrence,
)


PROJECT_ID = "318604"


def partial(data_type: type, **values: object) -> object:
    """Build a typed read-only fixture with only accessed slots populated."""

    value = object.__new__(data_type)
    for name, field_value in values.items():
        object.__setattr__(value, name, field_value)
    return value


def revision(
    *,
    number: int = 1,
    status: str = "accepted",
    preferred: str = "Pump",
    alternatives: tuple[str, ...] = ("Pumpe",),
) -> ProjectConceptRevision:
    return partial(
        ProjectConceptRevision,
        revision=number,
        lifecycle_status=status,
        preferred_labels=(
            LocalizedGlossaryText("en", preferred),
        ),
        alternative_labels=tuple(
            LocalizedGlossaryText("en", label)
            for label in alternatives
        ),
    )


def concept(
    *,
    concept_id: str = "PC-000001",
    selected_revision: ProjectConceptRevision | None = None,
) -> ProjectConcept:
    selected = revision() if selected_revision is None else selected_revision
    return ProjectConcept(
        project_concept_id=concept_id,
        latest_revision=selected.revision,
        revisions=(selected,),
    )


def glossary(
    *,
    concepts: tuple[ProjectConcept, ...] | None = None,
    ambiguity_groups: tuple[AmbiguityGroup, ...] = (),
    project_id: str = PROJECT_ID,
    glossary_revision: int = 1,
) -> ProjectGlossary:
    return partial(
        ProjectGlossary,
        project_id=project_id,
        glossary_revision=glossary_revision,
        default_language="en",
        concepts=(
            (concept(),)
            if concepts is None
            else concepts
        ),
        ambiguity_groups=ambiguity_groups,
    )


def turing_concept(
    *,
    concept_id: str = "TC-000001",
    status: str = "active",
) -> TuringCoreConcept:
    return partial(
        TuringCoreConcept,
        concept_id=concept_id,
        status=status,
        preferred_label="System Element",
        alternative_labels=("System Component",),
    )


def vocabulary(
    *,
    concepts: tuple[TuringCoreConcept, ...] | None = None,
    version: str = "1.0.0",
    registry_id: str = "TURING_ONTOLOGY_REGISTRY",
) -> TuringCoreVocabulary:
    policy = partial(
        builtins.type(
            "_ExternalMappingPolicy",
            (),
            {},
        ),
        registry_id=registry_id,
    )
    return partial(
        TuringCoreVocabulary,
        vocabulary_version=version,
        concepts=(
            (turing_concept(),)
            if concepts is None
            else concepts
        ),
        external_mapping_policy=policy,
    )


def registry(
    *,
    version: str = "1.0.0",
    registry_id: str = "TURING_ONTOLOGY_REGISTRY",
    reference_system_version: str = "202602",
) -> OntologyRegistry:
    system = partial(
        builtins.type("_ReferenceSystem", (), {}),
        reference_system_id="IOF_CORE_202602",
        version=reference_system_version,
    )
    return partial(
        OntologyRegistry,
        registry_id=registry_id,
        registry_version=version,
        reference_systems=(system,),
    )


def reference_concept(
    *,
    iri: str = "https://example.test/iof/Pump",
    system_id: str = "IOF_CORE_202602",
    version: str = "202602",
) -> ReferenceConcept:
    return partial(
        ReferenceConcept,
        iri=iri,
        reference_system_id=system_id,
        version=version,
        preferred_labels=(LocalizedText("en", "Pump"),),
        alternative_labels=(),
    )


def reference_index(
    *,
    concepts: tuple[ReferenceConcept, ...] | None = None,
    version: str = "1.0.0",
    registry_id: str = "TURING_ONTOLOGY_REGISTRY",
    registry_version: str = "1.0.0",
) -> ReferenceConceptIndex:
    return partial(
        ReferenceConceptIndex,
        index_version=version,
        registry_id=registry_id,
        registry_version=registry_version,
        concepts=(
            (reference_concept(),)
            if concepts is None
            else concepts
        ),
    )


def project_proposal(
    *,
    concept_id: str = "PC-000001",
    revision_number: int = 1,
    display_label: str = "Pump",
    basis_id: str | None = None,
    basis_version: str = "1",
) -> TerminologyMappingProposal:
    selected_basis_id = (
        f"{PROJECT_ID}/{concept_id}/revision/{revision_number}"
        if basis_id is None
        else basis_id
    )
    return TerminologyMappingProposal(
        mapping_relation="exact_match",
        target=TerminologyMappingTarget(
            target_kind="project_concept",
            display_label=display_label,
            project_concept_id=concept_id,
            project_concept_revision=revision_number,
        ),
        mapping_bases=(
            TerminologyMappingBasis(
                basis_type="accepted_project_glossary",
                reference_id=selected_basis_id,
                reference_version=basis_version,
                rationale="Accepted project terminology.",
            ),
        ),
        rationale="Candidate mapping.",
    )


def turing_proposal(
    *,
    concept_id: str = "TC-000001",
    display_label: str = "System Element",
    basis_version: str = "1.0.0",
) -> TerminologyMappingProposal:
    return TerminologyMappingProposal(
        mapping_relation="related_to",
        target=TerminologyMappingTarget(
            target_kind="turing_core_concept",
            display_label=display_label,
            turing_core_concept_id=concept_id,
        ),
        mapping_bases=(
            TerminologyMappingBasis(
                basis_type="turing_core",
                reference_id=concept_id,
                reference_version=basis_version,
                rationale="Curated Turing Core reference.",
            ),
        ),
        rationale="Candidate mapping.",
    )


def external_proposal(
    *,
    iri: str = "https://example.test/iof/Pump",
    system_id: str = "IOF_CORE_202602",
    system_version: str = "202602",
    display_label: str = "Pump",
    basis_version: str = "1.0.0",
) -> TerminologyMappingProposal:
    return TerminologyMappingProposal(
        mapping_relation="related_to",
        target=TerminologyMappingTarget(
            target_kind="external_reference_concept",
            display_label=display_label,
            reference_system_id=system_id,
            reference_system_version=system_version,
            reference_concept_iri=iri,
        ),
        mapping_bases=(
            TerminologyMappingBasis(
                basis_type="reference_concept_index",
                reference_id=iri,
                reference_version=basis_version,
                rationale="Pinned local concept index.",
            ),
        ),
        rationale="Candidate mapping.",
    )


def candidate(
    *,
    proposals: tuple[TerminologyMappingProposal, ...] | None = None,
    term_text: str = "Pump",
    **overrides: object,
) -> TerminologyMappingCandidate:
    values: dict[str, object] = {
        "project_id": PROJECT_ID,
        "information_unit_id": "IU-000001",
        "terminology_mapping_candidate_id": "TMC-000001",
        "occurrence": TerminologyOccurrence(
            information_unit_id="IU-000001",
            text_field="interpreted_statement",
            start_offset=4,
            end_offset=4 + len(term_text),
            term_text=term_text,
        ),
        "proposals": (
            (project_proposal(),)
            if proposals is None
            else proposals
        ),
        "ontology_registry_version": "1.0.0",
        "reference_concept_index_version": "1.0.0",
        "turing_core_version": "1.0.0",
        "project_glossary_revision": 1,
    }
    values.update(overrides)
    return partial(TerminologyMappingCandidate, **values)


def validate(
    selected_candidate: TerminologyMappingCandidate | None = None,
    *,
    selected_glossary: ProjectGlossary | None = None,
    selected_vocabulary: TuringCoreVocabulary | None = None,
    selected_registry: OntologyRegistry | None = None,
    selected_index: ReferenceConceptIndex | None = None,
) -> TerminologyMappingReferenceValidationResult:
    return validate_terminology_mapping_references(
        (
            candidate()
            if selected_candidate is None
            else selected_candidate
        ),
        project_glossary=(
            glossary()
            if selected_glossary is None
            else selected_glossary
        ),
        turing_core_vocabulary=(
            vocabulary()
            if selected_vocabulary is None
            else selected_vocabulary
        ),
        ontology_registry=(
            registry()
            if selected_registry is None
            else selected_registry
        ),
        reference_concept_index=(
            reference_index()
            if selected_index is None
            else selected_index
        ),
    )


def issue_codes(
    result: TerminologyMappingReferenceValidationResult,
) -> set[str]:
    return {issue.code for issue in result.issues}


def test_valid_project_mapping_is_reference_valid() -> None:
    result = validate()

    assert result.references_valid is True
    assert result.issues == ()
    assert result.checked_proposal_count == 1


def test_result_is_frozen_and_slotted() -> None:
    result = validate()

    assert result.__dataclass_params__.frozen
    assert result.__slots__
    with pytest.raises(FrozenInstanceError):
        result.references_valid = False


@pytest.mark.parametrize(
    ("candidate_field", "candidate_value", "expected_code"),
    (
        (
            "project_glossary_revision",
            2,
            "project_glossary_revision_mismatch",
        ),
        (
            "turing_core_version",
            "2.0.0",
            "turing_core_version_mismatch",
        ),
        (
            "ontology_registry_version",
            "2.0.0",
            "ontology_registry_version_mismatch",
        ),
        (
            "reference_concept_index_version",
            "2.0.0",
            "reference_concept_index_version_mismatch",
        ),
    ),
)
def test_candidate_context_version_mismatch_is_blocking(
    candidate_field: str,
    candidate_value: object,
    expected_code: str,
) -> None:
    result = validate(
        candidate(**{candidate_field: candidate_value})
    )

    assert result.references_valid is False
    assert expected_code in issue_codes(result)


def test_project_mismatch_is_blocking() -> None:
    result = validate(
        selected_glossary=glossary(project_id="999999")
    )

    assert "project_glossary_project_mismatch" in issue_codes(
        result
    )


def test_unknown_project_concept_is_blocking() -> None:
    result = validate(
        candidate(
            proposals=(
                project_proposal(concept_id="PC-999999"),
            )
        )
    )

    assert "project_concept_not_found" in issue_codes(result)


def test_unknown_project_revision_is_blocking() -> None:
    result = validate(
        candidate(
            proposals=(
                project_proposal(revision_number=2),
            )
        )
    )

    assert "project_concept_revision_not_found" in issue_codes(
        result
    )


def test_nonaccepted_project_revision_is_blocking() -> None:
    selected = concept(
        selected_revision=revision(status="candidate")
    )
    result = validate(
        selected_glossary=glossary(concepts=(selected,))
    )

    assert (
        "project_concept_revision_not_accepted"
        in issue_codes(result)
    )


def test_project_basis_must_bind_exact_reference() -> None:
    result = validate(
        candidate(
            proposals=(
                project_proposal(basis_id="wrong/reference"),
            )
        )
    )

    assert (
        "authoritative_mapping_basis_mismatch"
        in issue_codes(result)
    )


def test_project_basis_uses_glossary_revision() -> None:
    result = validate(
        candidate(
            proposals=(
                project_proposal(basis_version="2"),
            )
        )
    )

    assert (
        "authoritative_mapping_basis_mismatch"
        in issue_codes(result)
    )


def test_project_display_label_difference_is_warning_only() -> None:
    result = validate(
        candidate(
            proposals=(
                project_proposal(display_label="Different"),
            )
        )
    )

    assert result.references_valid is True
    assert "project_target_display_label_differs" in issue_codes(
        result
    )


def test_unmatched_project_term_requires_semantic_review_warning() -> None:
    result = validate(candidate(term_text="Device"))

    assert result.references_valid is True
    assert "project_concept_label_not_matched" in issue_codes(
        result
    )


def test_conflicting_exact_project_label_is_blocking() -> None:
    other = concept(
        concept_id="PC-000002",
        selected_revision=revision(
            preferred="Pump",
            alternatives=(),
        ),
    )
    selected = concept(
        selected_revision=revision(
            preferred="Actuator",
            alternatives=(),
        )
    )
    result = validate(
        candidate(term_text="Pump"),
        selected_glossary=glossary(
            concepts=(selected, other)
        ),
    )

    assert "project_glossary_label_conflict" in issue_codes(
        result
    )
    assert result.references_valid is False


def test_multiple_accepted_exact_labels_are_ambiguous() -> None:
    second = concept(
        concept_id="PC-000002",
        selected_revision=revision(
            preferred="Pump",
            alternatives=(),
        ),
    )
    result = validate(
        selected_glossary=glossary(
            concepts=(concept(), second)
        )
    )

    assert "ambiguous_project_glossary_label" in issue_codes(
        result
    )
    assert result.references_valid is False


def test_explicit_ambiguity_group_prevents_auto_resolution() -> None:
    group = partial(
        AmbiguityGroup,
        ambiguity_group_id="AG-000001",
        label="Pump",
        language="en",
        candidate_project_concept_ids=(
            "PC-000001",
            "PC-000002",
        ),
    )
    result = validate(
        selected_glossary=glossary(
            ambiguity_groups=(group,)
        )
    )

    assert "ambiguous_project_glossary_label" in issue_codes(
        result
    )


def test_valid_turing_core_mapping() -> None:
    result = validate(
        candidate(proposals=(turing_proposal(),))
    )

    assert result.references_valid is True
    assert result.issues == ()


def test_unknown_turing_core_concept_is_blocking() -> None:
    result = validate(
        candidate(
            proposals=(
                turing_proposal(concept_id="TC-999999"),
            )
        )
    )

    assert "turing_core_concept_not_found" in issue_codes(result)


def test_inactive_turing_core_concept_is_blocking() -> None:
    result = validate(
        candidate(proposals=(turing_proposal(),)),
        selected_vocabulary=vocabulary(
            concepts=(turing_concept(status="deprecated"),)
        ),
    )

    assert "turing_core_concept_not_active" in issue_codes(result)


def test_turing_basis_version_must_match_vocabulary() -> None:
    result = validate(
        candidate(
            proposals=(
                turing_proposal(basis_version="2.0.0"),
            )
        )
    )

    assert (
        "authoritative_mapping_basis_mismatch"
        in issue_codes(result)
    )


def test_turing_display_label_difference_is_warning_only() -> None:
    result = validate(
        candidate(
            proposals=(
                turing_proposal(display_label="Different"),
            )
        )
    )

    assert result.references_valid is True
    assert "turing_core_display_label_differs" in issue_codes(
        result
    )


def test_valid_external_reference_mapping() -> None:
    result = validate(
        candidate(proposals=(external_proposal(),))
    )

    assert result.references_valid is True
    assert result.issues == ()


def test_unknown_external_iri_is_blocking() -> None:
    result = validate(
        candidate(
            proposals=(
                external_proposal(
                    iri="https://example.test/iof/Unknown"
                ),
            )
        )
    )

    assert "reference_concept_not_found" in issue_codes(result)


def test_external_reference_system_must_match_index() -> None:
    result = validate(
        candidate(
            proposals=(
                external_proposal(system_id="BFO_2020"),
            )
        )
    )

    codes = issue_codes(result)
    assert "reference_concept_system_mismatch" in codes
    assert "reference_system_not_registered" in codes


def test_external_reference_version_must_match_registry() -> None:
    result = validate(
        candidate(
            proposals=(
                external_proposal(system_version="202501"),
            )
        )
    )

    codes = issue_codes(result)
    assert "reference_system_version_mismatch" in codes
    assert "reference_concept_version_mismatch" in codes


def test_external_basis_version_must_match_index() -> None:
    result = validate(
        candidate(
            proposals=(
                external_proposal(basis_version="2.0.0"),
            )
        )
    )

    assert (
        "authoritative_mapping_basis_mismatch"
        in issue_codes(result)
    )


def test_external_display_label_difference_is_warning_only() -> None:
    result = validate(
        candidate(
            proposals=(
                external_proposal(display_label="Different"),
            )
        )
    )

    assert result.references_valid is True
    assert "reference_concept_display_label_differs" in issue_codes(
        result
    )


def test_registry_binding_of_reference_index_is_checked() -> None:
    result = validate(
        selected_index=reference_index(
            registry_id="OTHER_REGISTRY",
            registry_version="2.0.0",
        )
    )

    codes = issue_codes(result)
    assert "reference_index_registry_id_mismatch" in codes
    assert "reference_index_registry_version_mismatch" in codes


def test_turing_core_registry_binding_is_checked() -> None:
    result = validate(
        selected_vocabulary=vocabulary(
            registry_id="OTHER_REGISTRY"
        )
    )

    assert "turing_core_registry_id_mismatch" in issue_codes(
        result
    )


def test_targetless_no_equivalent_needs_no_reference() -> None:
    proposal = TerminologyMappingProposal(
        mapping_relation="no_equivalent",
        target=None,
        mapping_bases=(
            TerminologyMappingBasis(
                basis_type="semantic_interpretation",
                reference_id=(
                    "IU-000001/interpreted_statement/4:8"
                ),
                reference_version=None,
                rationale="No controlled equivalent was found.",
            ),
        ),
        rationale="No equivalent.",
    )

    result = validate(candidate(proposals=(proposal,)))

    assert result.references_valid is True
    assert result.issues == ()


@pytest.mark.parametrize(
    ("argument_name", "bad_value"),
    (
        ("candidate", object()),
        ("project_glossary", object()),
        ("turing_core_vocabulary", object()),
        ("ontology_registry", object()),
        ("reference_concept_index", object()),
    ),
)
def test_wrong_input_types_are_rejected(
    argument_name: str,
    bad_value: object,
) -> None:
    arguments: dict[str, object] = {
        "candidate": candidate(),
        "project_glossary": glossary(),
        "turing_core_vocabulary": vocabulary(),
        "ontology_registry": registry(),
        "reference_concept_index": reference_index(),
    }
    arguments[argument_name] = bad_value

    with pytest.raises(TerminologyMappingReferenceError):
        validate_terminology_mapping_references(**arguments)


def test_validation_does_not_mutate_inputs() -> None:
    selected_candidate = candidate()
    selected_glossary = glossary()
    selected_vocabulary = vocabulary()
    selected_registry = registry()
    selected_index = reference_index()
    before = (
        selected_candidate.proposals,
        selected_glossary.concepts,
        selected_vocabulary.concepts,
        selected_registry.reference_systems,
        selected_index.concepts,
    )

    validate_terminology_mapping_references(
        selected_candidate,
        project_glossary=selected_glossary,
        turing_core_vocabulary=selected_vocabulary,
        ontology_registry=selected_registry,
        reference_concept_index=selected_index,
    )

    after = (
        selected_candidate.proposals,
        selected_glossary.concepts,
        selected_vocabulary.concepts,
        selected_registry.reference_systems,
        selected_index.concepts,
    )
    assert before == after