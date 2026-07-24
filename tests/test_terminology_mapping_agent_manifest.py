"""Tests for persona-specific terminology mapping manifests."""

from __future__ import annotations

from dataclasses import fields, replace
from hashlib import sha256
import json

import pytest

from modules.information_units.types import (
    InformationUnit,
    InformationUnitExtractionProvenance,
    InformationUnitSourceAnchor,
)
from modules.terminology_mapping.agent_manifest import (
    TERMINOLOGY_MAPPING_AGENT_RESULT_SCHEMA_VERSION,
    create_terminology_mapping_agent_candidate,
    create_terminology_mapping_agent_result,
    create_terminology_mapping_basis,
    create_terminology_mapping_proposal,
    create_terminology_mapping_target,
    create_terminology_occurrence,
    parse_terminology_mapping_agent_result,
    terminology_mapping_agent_result_from_json,
    terminology_mapping_agent_result_to_dict,
    terminology_mapping_agent_result_to_json,
    validate_terminology_mapping_agent_result,
)
from modules.terminology_mapping.errors import (
    DuplicateTerminologyMappingAgentCandidateError,
    TerminologyMappingIntegrityError,
    TerminologyMappingReferenceError,
    TerminologyMappingValidationError,
)
from modules.terminology_mapping.types import (
    TerminologyMappingAgentCandidate,
    TerminologyMappingAgentResult,
)


PROJECT_ID = "318604"
SOURCE_ID = "SRC-000001"
SOURCE_PROJECTION_ID = "SP-000001"
INFORMATION_UNIT_ID = "IU-000001"
TIMESTAMP = "2026-07-24T13:00:00Z"


def information_unit(
    *,
    project_id: str = PROJECT_ID,
    source_id: str = SOURCE_ID,
    source_projection_id: str = SOURCE_PROJECTION_ID,
    information_unit_id: str = INFORMATION_UNIT_ID,
    source_excerpt: str = "The pump preserves pressure.",
    interpreted_statement: str = (
        "The pump shall preserve system pressure."
    ),
) -> InformationUnit:
    return InformationUnit(
        schema_version="1.0.0",
        project_id=project_id,
        information_unit_id=information_unit_id,
        source_id=source_id,
        source_projection_id=source_projection_id,
        source_anchors=(
            InformationUnitSourceAnchor(
                segment_id="SEG-000001",
                start_offset=0,
                end_offset=len(source_excerpt),
            ),
        ),
        source_excerpt=source_excerpt,
        interpreted_statement=interpreted_statement,
        information_type="requirement",
        statement_modality="normative",
        epistemic_class="explicit",
        supporting_information_unit_ids=(),
        derivation_rationale=None,
        missing_evidence=None,
        extraction_provenance=(
            InformationUnitExtractionProvenance(
                team_id="semantic-team",
                persona_ids=("persona-a", "persona-b"),
                llm_provider="test-provider",
                llm_model="test-model",
                prompt_schema_version="1.0.0",
                consensus_report_id="CONSENSUS-TEST-001",
            )
        ),
        confidence="high",
        confidence_rationale="Unanimous independent personas.",
        content_fingerprint="a" * 64,
        created_at="2026-07-24T12:00:00Z",
    )


def occurrence(
    *,
    unit: InformationUnit | None = None,
) -> object:
    selected_unit = information_unit() if unit is None else unit
    start = selected_unit.interpreted_statement.index("pump")
    return create_terminology_occurrence(
        selected_unit,
        text_field="interpreted_statement",
        start_offset=start,
        end_offset=start + len("pump"),
    )


def project_basis() -> object:
    return create_terminology_mapping_basis(
        basis_type="accepted_project_glossary",
        reference_id=f"{PROJECT_ID}/PC-000001/revision/1",
        reference_version="1",
        rationale="Accepted project meaning matches the term.",
    )


def turing_basis() -> object:
    return create_terminology_mapping_basis(
        basis_type="turing_core",
        reference_id="TC-000001",
        reference_version="1.0.0",
        rationale="Turing Core defines the controlled MBSE term.",
    )


def reference_basis() -> object:
    return create_terminology_mapping_basis(
        basis_type="reference_concept_index",
        reference_id=(
            "https://spec.industrialontologies.org/"
            "ontology/core/Pump"
        ),
        reference_version="1.0.0",
        rationale="The pinned reference index contains the concept.",
    )


def semantic_basis() -> object:
    return create_terminology_mapping_basis(
        basis_type="semantic_interpretation",
        reference_id="IU-000001/interpreted_statement/4:8",
        reference_version=None,
        rationale="The surrounding statement establishes usage.",
    )


def project_target() -> object:
    return create_terminology_mapping_target(
        target_kind="project_concept",
        display_label="Pump",
        project_concept_id="PC-000001",
        project_concept_revision=1,
    )


def turing_target() -> object:
    return create_terminology_mapping_target(
        target_kind="turing_core_concept",
        display_label="System Element",
        turing_core_concept_id="TC-000001",
    )


def external_target() -> object:
    return create_terminology_mapping_target(
        target_kind="external_reference_concept",
        display_label="Pump",
        reference_system_id="IOF_CORE_202602",
        reference_system_version="202602",
        reference_concept_iri=(
            "https://spec.industrialontologies.org/"
            "ontology/core/Pump"
        ),
    )


def proposal(
    *,
    target: object | None = None,
    relation: str = "exact_match",
    bases: tuple[object, ...] | None = None,
) -> object:
    selected_target = (
        project_target() if target is None else target
    )
    selected_bases = (
        (project_basis(), semantic_basis())
        if bases is None
        else bases
    )
    return create_terminology_mapping_proposal(
        mapping_relation=relation,
        target=selected_target,
        mapping_bases=selected_bases,
        rationale="The contextual meaning matches the target.",
    )


def candidate(
    *,
    candidate_id: str = "TMAC-000001",
    selected_occurrence: object | None = None,
    status: str = "mapped",
    proposals: tuple[object, ...] | None = None,
) -> TerminologyMappingAgentCandidate:
    return create_terminology_mapping_agent_candidate(
        terminology_mapping_agent_candidate_id=candidate_id,
        occurrence=(
            occurrence()
            if selected_occurrence is None
            else selected_occurrence
        ),
        mapping_status=status,
        proposals=(
            (proposal(),)
            if proposals is None
            else proposals
        ),
        rationale="Persona proposes an explicit terminology mapping.",
        uncertainties=(),
    )


def result(
    *,
    unit: InformationUnit | None = None,
    candidates: tuple[TerminologyMappingAgentCandidate, ...]
    | None = None,
    no_candidate_rationale: str | None = None,
    **overrides: object,
) -> TerminologyMappingAgentResult:
    selected_unit = information_unit() if unit is None else unit
    selected_candidates = (
        (candidate(selected_occurrence=occurrence(unit=selected_unit)),)
        if candidates is None
        else candidates
    )
    values: dict[str, object] = {
        "information_unit": selected_unit,
        "team_id": "terminology-team",
        "agent_id": "terminology-agent-a",
        "persona_id": "persona-a",
        "persona_run_index": 1,
        "persona_configuration_fingerprint": (
            sha256(b"persona-a").hexdigest()
        ),
        "llm_provider": "test-provider",
        "llm_model": "test-model",
        "prompt_schema_version": "1.0.0",
        "ontology_registry_version": "1.0.0",
        "reference_concept_index_version": "1.0.0",
        "turing_core_version": "1.0.0",
        "project_glossary_revision": 1,
        "candidates": selected_candidates,
        "no_candidate_rationale": no_candidate_rationale,
        "timestamp": TIMESTAMP,
    }
    values.update(overrides)
    return create_terminology_mapping_agent_result(**values)


def payload() -> dict[str, object]:
    return terminology_mapping_agent_result_to_dict(result())


def test_schema_version_is_explicit() -> None:
    assert TERMINOLOGY_MAPPING_AGENT_RESULT_SCHEMA_VERSION == "1.0.0"


def test_round_trip_is_lossless_and_deterministic() -> None:
    original = result()
    first = terminology_mapping_agent_result_to_json(original)
    second = terminology_mapping_agent_result_to_json(original)
    reloaded = terminology_mapping_agent_result_from_json(first)

    assert first == second
    assert reloaded == original
    assert json.loads(first)["schema_version"] == "1.0.0"


def test_agent_candidate_has_no_authoritative_fields() -> None:
    field_names = {
        field.name
        for field in fields(TerminologyMappingAgentCandidate)
    }
    for forbidden in (
        "confidence",
        "consensus_level",
        "terminology_mapping_candidate_id",
        "reviewer_id",
        "decision",
        "accepted",
    ):
        assert forbidden not in field_names


def test_result_has_no_authoritative_decision_fields() -> None:
    field_names = {
        field.name
        for field in fields(TerminologyMappingAgentResult)
    }
    for forbidden in (
        "confidence",
        "terminology_decision_id",
        "reviewer_id",
        "decision",
        "framework_assignment_id",
    ):
        assert forbidden not in field_names


def test_occurrence_uses_exact_information_unit_text() -> None:
    selected = occurrence()

    assert selected.information_unit_id == INFORMATION_UNIT_ID
    assert selected.text_field == "interpreted_statement"
    assert selected.term_text == "pump"
    assert selected.end_offset - selected.start_offset == 4


@pytest.mark.parametrize(
    ("text_field", "start_offset", "end_offset"),
    [
        ("unknown", 0, 1),
        ("interpreted_statement", -1, 1),
        ("interpreted_statement", 1, 1),
        ("interpreted_statement", 2, 1),
        ("interpreted_statement", 0, 999),
        ("interpreted_statement", True, 1),
        ("interpreted_statement", 0, False),
    ],
)
def test_occurrence_rejects_invalid_ranges(
    text_field: str,
    start_offset: object,
    end_offset: object,
) -> None:
    with pytest.raises(
        (
            TerminologyMappingValidationError,
            TerminologyMappingReferenceError,
        )
    ):
        create_terminology_occurrence(
            information_unit(),
            text_field=text_field,
            start_offset=start_offset,
            end_offset=end_offset,
        )


@pytest.mark.parametrize(
    "target_factory",
    [project_target, turing_target, external_target],
)
def test_all_accepted_target_kinds_are_explicit(
    target_factory: object,
) -> None:
    selected = target_factory()
    assert selected.display_label


@pytest.mark.parametrize(
    "values",
    [
        {
            "target_kind": "project_concept",
            "display_label": "Pump",
        },
        {
            "target_kind": "project_concept",
            "display_label": "Pump",
            "project_concept_id": "PC-000001",
        },
        {
            "target_kind": "project_concept",
            "display_label": "Pump",
            "project_concept_id": "PC-000001",
            "project_concept_revision": 1,
            "turing_core_concept_id": "TC-000001",
        },
        {
            "target_kind": "turing_core_concept",
            "display_label": "Pump",
        },
        {
            "target_kind": "turing_core_concept",
            "display_label": "Pump",
            "turing_core_concept_id": "TC-000001",
            "reference_system_id": "BFO_2020",
        },
        {
            "target_kind": "external_reference_concept",
            "display_label": "Pump",
            "reference_system_id": "IOF_CORE_202602",
            "reference_system_version": "202602",
        },
        {
            "target_kind": "external_reference_concept",
            "display_label": "Pump",
            "reference_system_id": "IOF_CORE_202602",
            "reference_system_version": "202602",
            "reference_concept_iri": "not-an-iri",
        },
        {
            "target_kind": "unknown",
            "display_label": "Pump",
        },
    ],
)
def test_target_rejects_incomplete_or_mixed_fields(
    values: dict[str, object],
) -> None:
    with pytest.raises(
        (
            TerminologyMappingValidationError,
            TerminologyMappingIntegrityError,
        )
    ):
        create_terminology_mapping_target(**values)


@pytest.mark.parametrize(
    ("basis_type", "reference_version"),
    [
        ("accepted_project_glossary", None),
        ("turing_core", None),
        ("reference_concept_index", None),
        ("unknown", "1.0.0"),
    ],
)
def test_versioned_basis_requires_version(
    basis_type: str,
    reference_version: str | None,
) -> None:
    with pytest.raises(
        (
            TerminologyMappingValidationError,
            TerminologyMappingIntegrityError,
        )
    ):
        create_terminology_mapping_basis(
            basis_type=basis_type,
            reference_id="reference",
            reference_version=reference_version,
            rationale="Test rationale.",
        )


def test_semantic_interpretation_basis_may_be_unversioned() -> None:
    assert semantic_basis().reference_version is None


@pytest.mark.parametrize(
    ("target", "relation", "bases"),
    [
        (None, "exact_match", (project_basis(),)),
        (project_target(), "no_equivalent", (semantic_basis(),)),
        (project_target(), "exact_match", (semantic_basis(),)),
        (turing_target(), "related_to", (semantic_basis(),)),
        (external_target(), "broader_than", (semantic_basis(),)),
        (project_target(), "exact_match", ()),
    ],
)
def test_proposal_rejects_invalid_target_basis_combinations(
    target: object | None,
    relation: str,
    bases: tuple[object, ...],
) -> None:
    with pytest.raises(TerminologyMappingIntegrityError):
        create_terminology_mapping_proposal(
            mapping_relation=relation,
            target=target,
            mapping_bases=bases,
            rationale="Invalid test proposal.",
        )


def test_no_equivalent_is_explicit_and_targetless() -> None:
    selected = create_terminology_mapping_proposal(
        mapping_relation="no_equivalent",
        target=None,
        mapping_bases=(semantic_basis(),),
        rationale="No equivalent controlled concept was found.",
    )

    assert selected.target is None
    assert selected.mapping_relation == "no_equivalent"


@pytest.mark.parametrize(
    ("status", "proposals"),
    [
        ("unmapped", (proposal(),)),
        ("mapped", ()),
        (
            "mapped",
            (
                create_terminology_mapping_proposal(
                    mapping_relation="no_equivalent",
                    target=None,
                    mapping_bases=(semantic_basis(),),
                    rationale="No equivalent.",
                ),
            ),
        ),
        ("ambiguous", (proposal(),)),
        ("conflict", ()),
        ("no_equivalent", ()),
        ("no_equivalent", (proposal(),)),
    ],
)
def test_candidate_status_controls_proposals(
    status: str,
    proposals: tuple[object, ...],
) -> None:
    with pytest.raises(TerminologyMappingIntegrityError):
        candidate(
            status=status,
            proposals=proposals,
        )


def test_ambiguous_candidate_requires_multiple_targets() -> None:
    first = proposal()
    second = proposal(
        target=turing_target(),
        relation="related_to",
        bases=(turing_basis(), semantic_basis()),
    )
    selected = candidate(
        status="ambiguous",
        proposals=(first, second),
    )

    assert selected.mapping_status == "ambiguous"
    assert len(selected.proposals) == 2


def test_unmapped_candidate_is_valid_without_proposals() -> None:
    selected = candidate(
        status="unmapped",
        proposals=(),
    )

    assert selected.proposals == ()


def test_no_equivalent_candidate_is_valid() -> None:
    no_equivalent = create_terminology_mapping_proposal(
        mapping_relation="no_equivalent",
        target=None,
        mapping_bases=(semantic_basis(),),
        rationale="No controlled equivalent is available.",
    )
    selected = candidate(
        status="no_equivalent",
        proposals=(no_equivalent,),
    )

    assert selected.mapping_status == "no_equivalent"


def test_result_derives_source_identity_from_information_unit() -> None:
    selected = result()

    assert selected.project_id == PROJECT_ID
    assert selected.source_id == SOURCE_ID
    assert selected.source_projection_id == SOURCE_PROJECTION_ID
    assert selected.information_unit_id == INFORMATION_UNIT_ID


def test_result_preserves_all_reference_versions() -> None:
    selected = result()

    assert selected.ontology_registry_version == "1.0.0"
    assert selected.reference_concept_index_version == "1.0.0"
    assert selected.turing_core_version == "1.0.0"
    assert selected.project_glossary_revision == 1


def test_empty_result_requires_rationale() -> None:
    selected = result(
        candidates=(),
        no_candidate_rationale=(
            "No independently traceable term occurrence found."
        ),
    )

    assert selected.candidates == ()
    assert selected.no_candidate_rationale is not None


@pytest.mark.parametrize(
    ("candidates", "rationale"),
    [
        ((), None),
        ((candidate(),), "No candidates."),
    ],
)
def test_candidate_presence_controls_no_candidate_rationale(
    candidates: tuple[TerminologyMappingAgentCandidate, ...],
    rationale: str | None,
) -> None:
    with pytest.raises(TerminologyMappingIntegrityError):
        result(
            candidates=candidates,
            no_candidate_rationale=rationale,
        )


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("team_id", ""),
        ("team_id", " team "),
        ("agent_id", ""),
        ("persona_id", ""),
        ("persona_run_index", 0),
        ("persona_run_index", True),
        ("persona_configuration_fingerprint", "A" * 64),
        ("persona_configuration_fingerprint", "a" * 63),
        ("llm_provider", ""),
        ("llm_model", ""),
        ("prompt_schema_version", "1"),
        ("ontology_registry_version", "1"),
        ("reference_concept_index_version", "1.0"),
        ("turing_core_version", "v1"),
        ("project_glossary_revision", 0),
        ("timestamp", "2026-07-24"),
        ("timestamp", "2026-02-30T13:00:00Z"),
    ],
)
def test_result_rejects_invalid_metadata(
    field_name: str,
    value: object,
) -> None:
    with pytest.raises(TerminologyMappingValidationError):
        result(**{field_name: value})


def test_candidate_identifiers_must_be_sequential() -> None:
    second = candidate(candidate_id="TMAC-000002")

    with pytest.raises(TerminologyMappingIntegrityError):
        result(candidates=(second,))


def test_duplicate_occurrence_is_rejected() -> None:
    selected_occurrence = occurrence()
    first = candidate(
        candidate_id="TMAC-000001",
        selected_occurrence=selected_occurrence,
    )
    second = candidate(
        candidate_id="TMAC-000002",
        selected_occurrence=selected_occurrence,
    )

    with pytest.raises(
        DuplicateTerminologyMappingAgentCandidateError
    ):
        result(candidates=(first, second))


def test_occurrence_text_is_checked_against_information_unit() -> None:
    selected = result()
    changed_unit = replace(
        information_unit(),
        interpreted_statement=(
            "The valve shall preserve system pressure."
        ),
    )

    with pytest.raises(TerminologyMappingReferenceError):
        validate_terminology_mapping_agent_result(
            selected,
            information_unit=changed_unit,
        )


@pytest.mark.parametrize(
    ("expected_name", "expected_value"),
    [
        ("expected_project_id", "318605"),
        ("expected_source_id", "SRC-000002"),
        ("expected_source_projection_id", "SP-000002"),
        ("expected_information_unit_id", "IU-000002"),
        ("expected_team_id", "another-team"),
        ("expected_agent_id", "another-agent"),
        ("expected_persona_id", "another-persona"),
    ],
)
def test_expected_reference_mismatch_is_rejected(
    expected_name: str,
    expected_value: str,
) -> None:
    with pytest.raises(TerminologyMappingReferenceError):
        parse_terminology_mapping_agent_result(
            payload(),
            **{expected_name: expected_value},
        )


@pytest.mark.parametrize(
    "field_name",
    [
        "schema_version",
        "project_id",
        "source_id",
        "source_projection_id",
        "information_unit_id",
        "team_id",
        "agent_id",
        "persona_id",
        "persona_run_index",
        "persona_configuration_fingerprint",
        "llm_provider",
        "llm_model",
        "prompt_schema_version",
        "ontology_registry_version",
        "reference_concept_index_version",
        "turing_core_version",
        "project_glossary_revision",
        "candidates",
        "no_candidate_rationale",
        "created_at",
    ],
)
def test_missing_result_field_is_rejected(
    field_name: str,
) -> None:
    data = payload()
    del data[field_name]

    with pytest.raises(TerminologyMappingValidationError):
        parse_terminology_mapping_agent_result(data)


def test_unknown_result_field_is_rejected() -> None:
    data = payload()
    data["unexpected"] = True

    with pytest.raises(TerminologyMappingValidationError):
        parse_terminology_mapping_agent_result(data)


def test_invalid_json_is_rejected() -> None:
    with pytest.raises(TerminologyMappingValidationError):
        terminology_mapping_agent_result_from_json("{invalid")


def test_duplicate_json_key_is_rejected() -> None:
    text = terminology_mapping_agent_result_to_json(result())
    duplicate = text.replace(
        '"schema_version": "1.0.0",',
        (
            '"schema_version": "1.0.0",\n'
            '  "schema_version": "1.0.0",'
        ),
        1,
    )

    with pytest.raises(TerminologyMappingValidationError):
        terminology_mapping_agent_result_from_json(duplicate)


def test_unsupported_schema_version_is_rejected() -> None:
    data = payload()
    data["schema_version"] = "2.0.0"

    with pytest.raises(TerminologyMappingValidationError):
        parse_terminology_mapping_agent_result(data)


def test_serialization_rejects_wrong_type() -> None:
    with pytest.raises(TerminologyMappingValidationError):
        terminology_mapping_agent_result_to_dict(object())